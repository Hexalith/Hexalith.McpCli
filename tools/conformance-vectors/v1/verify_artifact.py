#!/usr/bin/env python3
"""Verify an exact Contracts artifact in an isolated generic host, including every vector step."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile

from validate import _load_json, package_identity, validate_vectors


def check_lint(findings: list[dict], accepted: list[dict]) -> None:
    if not isinstance(accepted, list):
        raise RuntimeError('Accepted lint must be an array of objects.')
    expected = set()
    for row in accepted:
        if not isinstance(row, dict) or set(row) != {'operation', 'code', 'property', 'approvalReference'} or any(not isinstance(value, str) or not value.strip() for value in row.values()):
            raise RuntimeError('Accepted lint requires exact operation, code, property and approvalReference.')
        key = (row['operation'], row['code'], row['property'])
        if key in expected:
            raise RuntimeError('Duplicate accepted lint exception.')
        expected.add(key)
    actual = {(row['operation'], row['code'], row.get('property')) for row in findings}
    if actual != expected:
        raise RuntimeError(f'Description lint differs from exact approvals: unapproved={sorted(actual - expected)!r}, stale={sorted(expected - actual)!r}')


def restored_package(assets: dict, identity: str, library: dict) -> tuple[Path, dict]:
    """Distinguish NuGet's restore content hash from the hash of exact signed archive bytes."""
    package_id, version = identity.rsplit('/', 1)
    candidates = [Path(folder) / library['path'] / f'{package_id.lower()}.{version.lower()}.nupkg'
                  for folder in assets['packageFolders']]
    artifact = next((path for path in candidates if path.is_file()), None)
    if artifact is None:
        raise RuntimeError(f'{identity}: exact restored .nupkg is unavailable.')
    normalize = lambda value: value if value.startswith('sha512-') else 'sha512-' + value
    digest = 'sha512-' + base64.b64encode(hashlib.sha512(artifact.read_bytes()).digest()).decode('ascii')
    assets_hash = normalize(library.get('sha512', ''))
    metadata = artifact.parent / '.nupkg.metadata'
    # Repository signatures can change raw archive bytes while retaining NuGet's restore content hash.
    content_hash = normalize(_load_json(metadata)['contentHash']) if metadata.exists() else digest
    if content_hash != assets_hash:
        raise RuntimeError(f'{identity}: restored bytes differ from the assets content hash.')
    sidecar = artifact.with_suffix('.nupkg.sha512')
    if sidecar.exists() and normalize(sidecar.read_text().strip()) != digest:
        raise RuntimeError(f'{identity}: restored bytes differ from the cached archive hash.')
    return artifact, {'id': package_id, 'version': version, 'artifactHash': digest,
                      'assetsHash': assets_hash, 'cacheContentHash': content_hash}


def resolved_packages(assets: dict) -> list[dict]:
    """Retain actual restored identities, archive hashes and independently matched restore content hashes."""
    return [restored_package(assets, identity, library)[1]
            for identity, library in sorted(assets['libraries'].items()) if library['type'] == 'package']


def verify(repo: Path, artifact: Path, vectors: list[Path], output: Path,
           inventory: Path | None = None, expected_hash: str | None = None, accepted_lint: Path | None = None, align_candidate_dependencies: bool = True) -> dict:
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    # Invalidate stale success before even resolving the new artifact or reading inputs.
    (output / 'artifact.sha512').unlink(missing_ok=True)
    receipt = {'result': 'pending', 'checks': [],
               'approvalInputs': {'inventory': None, 'acceptedLint': None},
               'evidenceLimit': 'Scripted Gateway replay proves head routing and result parity; it does not prove live authorization or domain effects.'}

    def save():
        (output / 'verification.json').write_text(json.dumps(receipt, indent=2) + '\n')

    save()

    def run(command, cwd, env, label, expected_exit_codes=(0,)):
        result = subprocess.run(list(map(str, command)), cwd=cwd, env=env, capture_output=True, text=True)
        (output / (label + '.stdout.txt')).write_text(result.stdout)
        (output / (label + '.stderr.txt')).write_text(result.stderr)
        receipt['checks'].append({'label': label, 'command': list(map(str, command)), 'exitCode': result.returncode})
        save()
        if result.returncode not in expected_exit_codes:
            for channel, captured in [('stdout', result.stdout), ('stderr', result.stderr)]:
                if captured:
                    print(f'{label} {channel} (full output retained in {output / (label + "." + channel + ".txt")}):', file=sys.stderr)
                    print(captured[-16000:], end='' if captured.endswith('\n') else '\n', file=sys.stderr)
            raise RuntimeError(f'{label} failed with exit {result.returncode}; see {output}.')
        return result.stdout

    try:
        artifact = artifact.resolve(strict=True)
        package_id, version = package_identity(artifact)
        digest = 'sha512-' + base64.b64encode(hashlib.sha512(artifact.read_bytes()).digest()).decode('ascii')
        receipt.update(packageId=package_id, version=version, artifactHash=digest,
                       vectors={str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in vectors})
        save()
        if expected_hash is not None and digest != expected_hash:
            raise RuntimeError('Artifact hash differs from the approved receipt.')
        frozen_inputs = {}
        for key, source in [('inventory', inventory), ('acceptedLint', accepted_lint)]:
            if source is not None:
                data = source.read_bytes()
                frozen = output / (key + '.input.json')
                frozen.write_bytes(data)
                frozen_inputs[key] = frozen
                receipt['approvalInputs'][key] = {'path': str(source.resolve()), 'sha256': hashlib.sha256(data).hexdigest(), 'retainedInput': frozen.name}
        save()
        with tempfile.TemporaryDirectory(prefix='mcpcli-artifact-') as temporary:
            scratch = Path(temporary)
            env = {k: v for k, v in os.environ.items() if not k.startswith(('MCPCLI_', 'EVENTSTORE_'))}
            env['MCPCLI_CONFORMANCE_PROFILE_PATH'] = str(scratch / 'profile.json')
            env['NUGET_PACKAGES'] = str(scratch / 'packages')
            for name in ['src', 'references/Hexalith.Builds/Props']:
                shutil.copytree(repo / name, scratch / name, ignore=shutil.ignore_patterns('bin', 'obj', '.git'))
            for name in ['Directory.Build.props', 'Directory.Build.targets', 'Directory.Packages.props', 'global.json', '.editorconfig']:
                if (repo / name).exists():
                    shutil.copy2(repo / name, scratch / name)
            # Select the exact candidate dependency versions; record them so this cannot masquerade as shipped enrollment.
            with zipfile.ZipFile(artifact) as archive:
                nuspec = ET.fromstring(archive.read(next(n for n in archive.namelist() if n.endswith('.nuspec'))))
            dependencies = {d.attrib['id']: d.attrib['version'] for d in nuspec.iter() if d.tag.endswith('dependency')}
            receipt['artifactDependencies'] = dependencies
            common = []
            for name, prop in [('Hexalith.EventStore.Contracts', 'HexalithEventStoreVersion'),
                               ('Hexalith.Commons.UniqueIds', 'HexalithCommonsVersion')]:
                if align_candidate_dependencies and name in dependencies:
                    common.append(f'-p:{prop}={dependencies[name]}')
            receipt['candidateDependencyOverrides'] = common
            props = scratch / 'Directory.Packages.props'
            tree = ET.parse(props)
            ET.SubElement(ET.SubElement(tree.getroot(), 'ItemGroup'), 'PackageVersion', Update=package_id, Version=version)
            tree.write(props, encoding='unicode')
            host = scratch / 'host'
            host.mkdir()
            shutil.copy2(repo / 'tests/Hexalith.McpCli.ConformanceHost/Program.cs', host / 'Program.cs')
            for source in (repo / 'tests/Hexalith.McpCli.Core.Tests').glob('InventoryCoverage*.cs'):
                if source.name not in ('InventoryCoverageTests.cs', 'InventoryCoverageContractsAssembly.cs'):
                    shutil.copy2(source, host / source.name)
            project = ET.Element('Project', Sdk='Microsoft.NET.Sdk')
            group = ET.SubElement(project, 'PropertyGroup')
            for key, value in [('OutputType', 'Exe'), ('IsPackable', 'false'), ('RequireContractsFlag', 'true')]:
                ET.SubElement(group, key).text = value
            group = ET.SubElement(project, 'ItemGroup')
            ET.SubElement(group, 'ProjectReference', Include='../src/Hexalith.McpCli/Hexalith.McpCli.csproj')
            ET.SubElement(group, 'PackageReference', Include=package_id, HexalithContracts='true')
            ET.SubElement(project, 'Import', Project='../src/Hexalith.McpCli/Build/ModuleAssemblyManifest.targets')
            ET.ElementTree(project).write(host / 'ArtifactHost.csproj', encoding='unicode')
            run(['dotnet', 'restore', 'host/ArtifactHost.csproj', *common, f'-p:RestoreAdditionalProjectSources={artifact.parent}'], scratch, env, 'restore')
            receipt['resolvedPackages'] = resolved_packages(_load_json(host / 'obj/project.assets.json'))
            save()
            run(['dotnet', 'build', 'host/ArtifactHost.csproj', '--no-restore', '-c', 'Release', '-m:1', '-warnaserror', *common], scratch, env, 'build')
            cached = scratch / 'packages' / package_id.lower() / version.lower() / (package_id.lower() + '.' + version.lower() + '.nupkg')
            if not cached.exists() or hashlib.sha512(cached.read_bytes()).digest() != hashlib.sha512(artifact.read_bytes()).digest():
                raise RuntimeError('Restored package bytes do not match the supplied artifact.')
            command = ['dotnet', host / 'bin/Release/net10.0/ArtifactHost.dll']
            snapshot = json.loads(run([*command, '--full-catalog'], scratch, env, 'catalog'))
            if snapshot['diagnostics']:
                raise RuntimeError('Catalog diagnostics are not empty.')
            operations = sorted(o['name'] for m in snapshot['modules'] for o in m['operations'])
            receipt['operations'] = operations
            for module in snapshot['modules']:
                run([*command, 'operations', module['name'], '--strict'], scratch, env, 'operations-' + module['name'])
            run([*command, 'modules', '--strict'], scratch, env, 'modules')
            findings = []
            for operation in operations:
                description = json.loads(run([*command, 'describe', operation, '--lint', '--strict'], scratch, env, operation, (0, 1)))
                findings.extend(dict(finding, operation=operation) for finding in description['lintFindings'])
            check_lint(findings, _load_json(frozen_inputs['acceptedLint']) if accepted_lint is not None else [])
            receipt['acceptedLint'] = str(accepted_lint) if accepted_lint is not None else None
            findings = validate_vectors(vectors, artifact, (package_id, version), operations)
            if findings:
                raise RuntimeError('\n'.join(findings))
            if inventory is not None:
                run([*command, '--inventory', frozen_inputs['inventory']], scratch, env, 'inventory')
            run([sys.executable, repo / 'tools/conformance-vectors/v1/run_loopback.py', '--host', command[1],
                 '--artifact', artifact, '--expected-package-id', package_id, '--expected-package-version', version, *vectors], repo, env, 'replay')
        receipt['result'] = 'passed'
        save()
        (output / 'artifact.sha512').write_text(digest + '  ' + artifact.name + '\n')
        print(f'Verified {package_id}@{version}: {len(operations)} operations; complete vector replay passed.')
        return receipt
    except Exception as error:
        (output / 'artifact.sha512').unlink(missing_ok=True)
        receipt['result'] = 'failed'
        receipt['error'] = f'{type(error).__name__}: {error}'
        save()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--inventory', type=Path)
    parser.add_argument('--expected-hash')
    parser.add_argument('--accepted-lint', type=Path)
    parser.add_argument('vectors', nargs='+', type=Path)
    args = parser.parse_args()
    try:
        verify(Path(__file__).resolve().parents[3], args.artifact, [p.resolve() for p in args.vectors],
               args.output.resolve(), args.inventory, args.expected_hash, args.accepted_lint)
    except (RuntimeError, OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
