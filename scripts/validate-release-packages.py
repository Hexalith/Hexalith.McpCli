#!/usr/bin/env python3
"""Validate exact staged IDs, versions, and bootstrap dependency closure."""

import argparse
import json
import re
import importlib.util
import struct
from paired_release import digest, run, write_new
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("staging", type=Path)
    parser.add_argument("version")
    parser.add_argument("phase")
    parser.add_argument("--source-sha")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    staging, version, phase = args.staging, args.version, args.phase
    request_spec = importlib.util.spec_from_file_location("release_request", Path(__file__).with_name("release-request.py"))
    request_module = importlib.util.module_from_spec(request_spec)
    request_spec.loader.exec_module(request_module)
    request_module.validate_version(version)
    packages = json.loads(Path("tools/release-packages.json").read_text())["packages"]
    expected_ids = [package["id"] for package in packages]
    if expected_ids != ["Hexalith.McpCli.Abstractions", "Hexalith.McpCli"]:
        raise ValueError("The release manifest must declare exactly the paired package IDs")
    if phase not in {"bootstrap", "paired"}:
        raise ValueError(f"Unknown release phase: {phase}")

    active_ids = expected_ids[:1] if phase == "bootstrap" else expected_ids
    expected_names = {f"{package_id}.{version}.nupkg" for package_id in active_ids}
    if not staging.is_dir() or staging.is_symlink():
        raise ValueError("Staging must be a real directory")
    actual_names = {path.name for path in staging.iterdir()}
    if actual_names != expected_names:
        raise ValueError(f"Expected {sorted(expected_names)}, found {sorted(actual_names)}")

    for package_id in active_ids:
        path = staging / f"{package_id}.{version}.nupkg"
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"{path} must be a regular package file")
        with ZipFile(path) as archive:
            names = set(archive.namelist())
            if len(names) != len(archive.namelist()):
                raise ValueError(f"{path} contains duplicate archive entries")
            if package_id.endswith(".Abstractions") and (
                "lib/net10.0/Hexalith.McpCli.Abstractions.dll" not in names
            ):
                raise ValueError("Abstractions package is missing its net10.0 compile DLL")
            if package_id.endswith(".Abstractions") and (
                "analyzers/dotnet/cs/Hexalith.McpCli.Analyzers.dll" not in names
            ):
                raise ValueError("Abstractions package is missing its C# analyzer DLL")
            nuspec_names = [name for name in names if name.endswith(".nuspec")]
            if len(nuspec_names) != 1:
                raise ValueError(f"{path} must contain one nuspec")
            root = ElementTree.fromstring(archive.read(nuspec_names[0]))
            metadata = root.find("{*}metadata")
            if metadata is None or metadata.findtext("{*}id") != package_id:
                raise ValueError(f"Unexpected package ID in {path}")
            if metadata.findtext("{*}version") != version:
                raise ValueError(f"Unexpected package version in {path}")
            if package_id.endswith(".Abstractions") and metadata.findall(".//{*}dependency"):
                raise ValueError("Abstractions must have no consumer-visible package dependencies")
            if package_id == "Hexalith.McpCli":
                validate_tool_package(archive, names, metadata)
            if phase == 'paired':
                for name in names:
                    if name.startswith('/') or '\\' in name or '..' in Path(name).parts:
                        raise ValueError('Unsafe archive entry.')
                if args.source_sha:
                    repository = metadata.find('{*}repository')
                    if repository is None or repository.get('commit') != args.source_sha:
                        raise ValueError('Package repository commit differs from the staged source.')

    if phase == 'paired':
        validate_effective_properties(packages, version)
    if args.output:
        write_new(args.output, {'version': version, 'phase': phase, 'source_sha': args.source_sha,
                               'packages': {name: digest(staging / name) for name in sorted(expected_names)}})

    print(f"Validated {phase} packages at version {version}")
    return 0


def validate_tool_package(archive: ZipFile, names: set[str], metadata: ElementTree.Element) -> None:
    prefix = "tools/net10.0/any/"
    required = {
        "README.md",
        prefix + "DotnetToolSettings.xml",
        prefix + "Hexalith.McpCli.dll",
        prefix + "Hexalith.McpCli.deps.json",
        prefix + "Hexalith.McpCli.runtimeconfig.json",
    }
    missing = required - names
    if missing:
        raise ValueError(f"McpCli tool package is missing {sorted(missing)}")
    if metadata.find(".//{*}packageType[@name='DotnetTool']") is None:
        raise ValueError("McpCli package is not marked as a .NET tool")
    command = ElementTree.fromstring(archive.read(prefix + "DotnetToolSettings.xml")).find(".//Command")
    if command is None or command.attrib != {
        "Name": "hexalith", "EntryPoint": "Hexalith.McpCli.dll", "Runner": "dotnet"
    }:
        raise ValueError("McpCli tool command is not hexalith")

    manifest = Path("src/Hexalith.McpCli/obj/Release/net10.0/ModuleAssemblyManifest.g.cs")
    if not manifest.is_file():
        raise ValueError("The generated Contracts assembly manifest is missing")
    entries = re.findall(r'\("([^"]+)", "([^"]+)"\)', manifest.read_text(encoding="utf-8"))
    if not entries:
        raise ValueError("The paired tool release has no enrolled Contracts assemblies")
    for package_id, assembly_name in entries:
        if not package_id.endswith('.Contracts') or not assembly_name.endswith('.Contracts'):
            raise ValueError(f'Invalid Contracts assembly manifest entry: {package_id}, {assembly_name}')
        if prefix + assembly_name + '.dll' not in names:
            raise ValueError(f'McpCli tool package is missing {assembly_name}.dll')
    project = ElementTree.parse('src/Hexalith.McpCli/Hexalith.McpCli.csproj')
    flagged = {item.get('Include') for item in project.findall('.//PackageReference')
               if item.get('HexalithContracts') == 'true'}
    policy = json.loads(Path('tools/dependency-policy.json').read_text())['modules']
    if len(entries) != len(set(entries)) or {item[0] for item in entries} != flagged or flagged != set(policy):
        raise ValueError('Generated manifest, flagged Contracts references and approved modules differ.')
    assets = json.loads(Path('src/Hexalith.McpCli/obj/project.assets.json').read_text())
    restored = {name.split('/')[0]: name.split('/')[1] for name in assets['libraries']}
    if any(restored.get(name) != version for name, version in policy.items()):
        raise ValueError('Restored Contracts versions differ from the approved enrollment.')
    dependencies = json.loads(archive.read(prefix + 'Hexalith.McpCli.deps.json'))
    if dependencies['runtimeTarget']['name'] != '.NETCoreApp,Version=v10.0':
        raise ValueError('The tool must target portable .NET 10 without a runtime identifier.')
    if any(f'{name}/{version}' not in dependencies['libraries'] for name, version in policy.items()):
        raise ValueError('Packaged Contracts versions differ from the approved enrollment.')
    runtime = json.loads(archive.read(prefix + 'Hexalith.McpCli.runtimeconfig.json'))['runtimeOptions']
    frameworks = runtime.get('frameworks', [runtime.get('framework', {})])
    if (runtime.get('tfm') != 'net10.0' or runtime.get('includedFrameworks')
            or not any(item.get('name') == 'Microsoft.NETCore.App' and item.get('version', '').startswith('10.') for item in frameworks)):
        raise ValueError('The tool must be framework-dependent on .NET 10.')
    if any(name.startswith(prefix + executable) for name in names for executable in ('hexalith.exe', 'Hexalith.McpCli.exe', 'coreclr', 'hostfxr')):
        raise ValueError('A native apphost or runtime payload is not allowed.')
    validate_tool_payload(archive, names, dependencies, prefix)
    for package_id, assembly_name in entries:
        if not package_id.endswith(".Contracts") or not assembly_name.endswith(".Contracts"):
            raise ValueError(f"Invalid Contracts assembly manifest entry: {package_id}, {assembly_name}")
        if prefix + assembly_name + ".dll" not in names:
            raise ValueError(f"McpCli tool package is missing {assembly_name}.dll")


def validate_tool_payload(archive, names, dependencies, prefix):
    native_magic = (b'\x7fELF', b'\xfe\xed\xfa\xce', b'\xce\xfa\xed\xfe', b'\xfe\xed\xfa\xcf',
                    b'\xcf\xfa\xed\xfe', b'\xca\xfe\xba\xbe', b'\xbe\xba\xfe\xca',
                    b'\xca\xfe\xba\xbf', b'\xbf\xba\xfe\xca', b'\0asm', b'!<arch>\n')
    for name in sorted(names):
        if not name.startswith(prefix) or name.endswith('/'):
            continue
        lowered = name.lower()
        payload = archive.read(name)
        if (re.search(r'\.so(?:\.[0-9]+)*\Z', lowered)
                or Path(lowered).suffix in {'.dylib', '.exe', '.a', '.lib', '.o', '.obj', '.node', '.wasm'}
                or payload.startswith(native_magic)):
            raise ValueError(f'Native payload is not allowed in the portable managed tool: {name}')
        if lowered.endswith('.dll'):
            validate_managed(payload)
        elif payload.startswith(b'MZ'):
            raise ValueError(f'An executable payload must be a managed DLL: {name}')
    targets = dependencies.get('targets', {})
    if dependencies['runtimeTarget']['name'] not in targets:
        raise ValueError('The tool dependency document is missing its portable runtime target.')
    for target in targets.values():
        for library in target.values():
            if library.get('native'):
                raise ValueError('Native dependency assets are not allowed in the portable managed tool.')
            for asset in library.get('runtimeTargets', {}).values():
                if asset.get('assetType', '').lower() == 'native':
                    raise ValueError('Native runtime-target dependency assets are not allowed in the portable managed tool.')


def validate_managed(payload):
    try:
        offset = struct.unpack_from('<I', payload, 0x3c)[0]
        optional = offset + 24
        magic = struct.unpack_from('<H', payload, optional)[0]
        directories = optional + (96 if magic == 0x10b else 112 if magic == 0x20b else 0)
        if payload[:2] != b'MZ' or payload[offset:offset + 4] != b'PE\0\0' or not directories:
            raise ValueError('The tool payload is not a managed PE assembly.')
        cli_rva, cli_size = struct.unpack_from('<II', payload, directories + 14 * 8)
        if not cli_rva or cli_size < 72:
            raise ValueError('The tool payload has no managed CLR header.')
        section_count = struct.unpack_from('<H', payload, offset + 6)[0]
        optional_size = struct.unpack_from('<H', payload, offset + 20)[0]
        cli_offset = None
        for index in range(section_count):
            section = optional + optional_size + index * 40
            virtual_size, virtual_address, raw_size, raw_pointer = struct.unpack_from('<IIII', payload, section + 8)
            if virtual_address <= cli_rva < virtual_address + max(virtual_size, raw_size):
                cli_offset = raw_pointer + cli_rva - virtual_address
                break
        if cli_offset is None or cli_offset + 72 > len(payload):
            raise ValueError('The tool payload has an invalid managed CLR header.')
        flags = struct.unpack_from('<I', payload, cli_offset + 16)[0]
        native_header = struct.unpack_from('<II', payload, cli_offset + 64)
        if not flags & 1 or flags & 2 or any(native_header):
            raise ValueError('The tool payload must contain portable managed IL, without mixed/native or precompiled code.')
    except (struct.error, IndexError):
        raise ValueError('The tool payload is not a managed PE assembly.') from None


def validate_effective_properties(packages, version):
    names = ['TargetFramework', 'TargetFrameworks', 'PackAsTool', 'ToolCommandName', 'UseAppHost',
             'PublishTrimmed', 'PublishAot', 'PublishReadyToRun', 'SelfContained', 'RuntimeIdentifier', 'RuntimeIdentifiers',
             'CreateRidSpecificToolPackages', 'PackageId', 'Version']
    for package in packages:
        result = run(['dotnet', 'msbuild', package['project'], '-nologo', '-p:Configuration=Release',
                      f'-p:Version={version}', '-getProperty:' + ','.join(names)], text=True)
        properties = json.loads(result.stdout)['Properties']
        if properties['TargetFramework'] != 'net10.0' or properties['TargetFrameworks']:
            raise ValueError('Release packages must target only net10.0.')
        if properties['PackageId'] != package['id'] or properties['Version'] != version:
            raise ValueError('Effective package identity/version differs from the release manifest.')
        if package['id'] == 'Hexalith.McpCli':
            if properties['PackAsTool'] != 'true' or properties['ToolCommandName'] != 'hexalith':
                raise ValueError('Effective tool packaging properties are invalid.')
            for name in ('UseAppHost', 'PublishTrimmed', 'PublishAot', 'PublishReadyToRun', 'SelfContained', 'CreateRidSpecificToolPackages'):
                if properties[name].lower() not in ('', 'false'):
                    raise ValueError(f'The portable tool cannot enable {name}.')
            if properties['RuntimeIdentifier'] or properties['RuntimeIdentifiers']:
                raise ValueError('The portable tool cannot specify a runtime identifier.')


if __name__ == "__main__":
    raise SystemExit(main())
