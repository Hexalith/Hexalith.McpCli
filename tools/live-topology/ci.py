#!/usr/bin/env python3
"""Bounded CI preparation and acceptance for the existing isolated semantic lane."""
from __future__ import annotations

import ctypes
import ctypes.util
import base64
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import time
import uuid
import xml.etree.ElementTree as ET
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import native_cohort
import native_audit
import native_sources

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from evidence_redaction import sanitized, sanitized_values, sanitized_xml
PROJECT = 'tests/Hexalith.McpCli.Integration.Tests'
TESTS = ROOT / PROJECT / 'bin/Release/net11.0/Hexalith.McpCli.Integration.Tests.dll'
MODULES = native_cohort.MODULES
# Published Testing.Integration remains independent of these test-owned launched SDK hosts.
EVENTSTORE_COHORT = native_cohort.COHORT
NATIVE_SELECTION = ROOT / 'tools/live-topology/native-runtime-current.json'
PACKAGE_GATEWAY = 'tests/Hexalith.McpCli.EventStoreGateway.TestHost/Hexalith.McpCli.EventStoreGateway.TestHost.csproj'
MODULE_AUDIT_PROJECTS = (PACKAGE_GATEWAY,
    'tests/Hexalith.McpCli.AppHost/Hexalith.McpCli.AppHost.csproj',
    'tests/Hexalith.McpCli.ConformanceHost/Hexalith.McpCli.ConformanceHost.csproj',
    PROJECT + '/Hexalith.McpCli.Integration.Tests.csproj')
SERVICES = {'sentry', 'redis', 'placement', 'scheduler'}
NAMESPACES = {'user', 'pid', 'net', 'mnt'}
OWNER_FILE = '.mcpcli-ci-owner'
ASPIRE_CLI_URL = 'https://github.com/microsoft/aspire/releases/download/v17.0.0/aspire-cli-linux-x64-17.0.0.tar.gz'
ASPIRE_CLI_SHA256 = '74a6d6418fcddb117770ccd235e2de4a96a02e36ebcfd0b0e2a0e69d6e85fc18'
# Exact root selections are a closed policy; owner projects use their native net11 graph.
SOURCE_PACKAGE_VERSIONS = {
    'Google.Protobuf': ('Include', '3.36.2'),
    'Grpc.Core.Api': ('Include', '2.85.0'),
    'Grpc.Net.Client': ('Include', '2.85.0'),
    'Grpc.Net.Common': ('Include', '2.85.0'),
    'Grpc.Reflection': ('Include', '2.85.0'),
    'Microsoft.Extensions.AI.Abstractions': ('Include', '11.0.0'),
    'Microsoft.Extensions.Caching.Abstractions': ('Include', '11.0.0'),
    'Hexalith.Commons.UniqueIds': ('Update', '3.0.2'),
    'Microsoft.CodeAnalysis.Analyzers': ('Update', '5.12.0'),
    'Microsoft.CodeAnalysis.Common': ('Update', '5.12.0'),
    'Microsoft.CodeAnalysis.CSharp': ('Update', '5.12.0'),
    'StackExchange.Redis': ('Update', '3.4.35'),
}


def current_runtime_profile() -> dict:
    """Load only the finite current toolchain and its exact pinned native binary map."""
    path = ROOT / 'tools/live-topology/runtime-profile-current.json'
    value = json.loads(path.read_text())
    expected = {'aspire': '17.0.0', 'dapr': '1.19.1', 'daprd': '1.19.2'}
    if value.get('schemaVersion') != 1 or value.get('profile') != 'current-sdk51-aspire1700-dapr1192' \
            or set(value.get('tools', {})) != set(expected):
        raise ValueError('The exact finite current runtime profile is required.')
    if value.get('managedTestHosts') != {'runtime': '11.0.0', 'targetFramework': 'net11.0',
            'projects': ['Hexalith.McpCli.AppHost', 'Hexalith.McpCli.Integration.Tests'],
            'resourceLaunch': {'rollForward': 'Disable', 'highestInstalledRuntime': '11.0.0',
                               'resources': ['eventstore', 'tenants', 'parties']}}:
        raise ValueError('The exact current owned managed test-host runtime is required.')
    for name, version in expected.items():
        item = value['tools'][name]
        if item.get('version') != version or any(not re.fullmatch('[0-9a-f]{64}', item.get(key, ''))
                for key in ('archiveSha256', 'binarySha256')):
            raise ValueError('Current runtime tool identity or checksum is invalid: ' + name)
    if value['tools']['aspire'].get('url') != ASPIRE_CLI_URL or value['tools']['aspire']['archiveSha256'] != ASPIRE_CLI_SHA256:
        raise ValueError('Current Aspire archive differs from its pinned official release.')
    binaries = value.get('binaries', {})
    if binaries.get('file') != 'binaries-current.json' or binaries.get('sha256') != hashlib.sha256(
            (path.parent / 'binaries-current.json').read_bytes()).hexdigest():
        raise ValueError('The current runtime binary manifest changed or is unbound.')
    return value


def current_managed_runtime_selection(output: str) -> dict:
    """Refuse any missing or newer framework than the exact current runtime image."""
    names = {'Microsoft.NETCore.App', 'Microsoft.AspNetCore.App'}
    found = {name: [] for name in names}
    for line in output.splitlines():
        parts = line.split()
        if parts and parts[0] in names:
            if len(parts) < 3 or not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', parts[1]):
                raise ValueError('Current native resources require a stable, measured managed runtime inventory.')
            found[parts[0]].append(tuple(map(int, parts[1].split('.'))))
    if any(not versions or max(versions) != (11, 0, 0) for versions in found.values()):
        raise ValueError('Current native resources require highest installed Core and ASP.NET runtime 11.0.0.')
    return {name: '11.0.0' for name in sorted(names)}


def verify_current_tool_bytes(profile: dict, paths: dict) -> None:
    """A version string alone cannot authenticate an installed executable."""
    if set(paths) != {'aspire', 'dapr', 'daprd'}:
        raise ValueError('The complete exact current executable set is required.')
    for name, path in paths.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != profile['tools'][name]['binarySha256']:
            raise ValueError('Current runtime executable hash mismatch: ' + name)


def require_current_runtime_profile(prepared: dict) -> dict:
    profile = current_runtime_profile()
    path = ROOT / 'tools/live-topology/runtime-profile-current.json'
    if prepared.get('runtimeProfile') != {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                                         'binariesSha256': profile['binaries']['sha256']}:
        raise ValueError('The prepared current runtime profile changed or is missing.')
    managed = current_managed_runtime_selection(subprocess.check_output(
        [prepared['tools']['executables']['dotnet']['path'], '--list-runtimes'], timeout=30, text=True))
    if prepared['tools'].get('managedResourceRuntimes') != managed:
        raise ValueError('The prepared managed resource runtime selection changed or is missing.')
    verify_current_tool_bytes(profile, {name: prepared['tools']['executables'][name]['path'] for name in ('aspire', 'dapr')}
                              | {'daprd': str(Path.home() / '.dapr/bin/daprd')})
    return profile


def save(path: Path, value, *, environment=None) -> None:
    path.write_text(sanitized(json.dumps(value, indent=2), environment=environment) + '\n')


def bounded(command: list[str], seconds: int, output: Path, *, cwd=ROOT, environment=None) -> str:
    """Enforce a process bound, retain both sanitized channels, and propagate failures."""
    output.parent.mkdir(parents=True, exist_ok=True)
    argv = list(map(str, command))
    actual = ['timeout', '--signal=TERM', '--kill-after=30s', str(seconds), *argv]
    display = ' '.join(sanitized_values(argv, environment=environment))
    print(sanitized(f'Running ({seconds}s): {display}', environment=environment), flush=True)
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        child = subprocess.Popen(actual, cwd=cwd, env=environment, stdout=stdout, stderr=stderr, start_new_session=True)
        interrupted = False
        try:
            code = child.wait(timeout=seconds + 40)
        except BaseException:
            interrupted = True
            raise
        finally:
            cleanup_deadline = time.monotonic() + 25
            if child.poll() is None:
                try:
                    os.kill(child.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass  # The child can exit between poll and the supervisor signal.
                try:
                    # The vector runner allows its detached child 20 seconds
                    # to clean up. Leave it that grace inside our 30-second bound.
                    child.wait(timeout=25)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(child.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    child.wait(timeout=1)
            # GNU timeout itself can exit on TERM before its command's
            # cleanup completes. Allow that owned group the same total grace.
            if interrupted or child.returncode != 0:
                while time.monotonic() < cleanup_deadline:
                    try:
                        os.killpg(child.pid, 0)
                    except ProcessLookupError:
                        break
                    time.sleep(.05)
            # A supervisor can exit before a TERM-resistant descendant.
            # Its session is task-owned even after the supervisor is reaped.
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            stdout.seek(0)
            stderr.seek(0)
            content = sanitized(stdout.read().decode(errors='replace'), environment=environment)
            error = sanitized(stderr.read().decode(errors='replace'), environment=environment)
            output.parent.joinpath(output.name + '.stdout.txt').write_text(content)
            output.parent.joinpath(output.name + '.stderr.txt').write_text(error)
            save(output.parent / (output.name + '.command.json'), {'command': argv, 'cwd': str(cwd),
                 'timeoutSeconds': seconds, 'exitCode': child.returncode}, environment=environment)
    if code != 0:
        raise RuntimeError(sanitized(f'{display} exited {code}; '
                           f'stdout: {output.parent / (output.name + ".stdout.txt")}; '
                           f'stderr: {output.parent / (output.name + ".stderr.txt")}', environment=environment))
    return content.strip()


def evidence_directory(*, preparing: bool) -> Path:
    value = os.environ.get('ASPIRE_EVIDENCE_PATH', 'TestResults/live-ci')
    if not re.fullmatch(r'[A-Za-z0-9_./-]+', value) or value.startswith('/') or any(part in ('', '.', '..') for part in value.split('/')):
        raise ValueError('ASPIRE_EVIDENCE_PATH must be a repository-relative directory without traversal.')
    path = ROOT / value
    if any(item.is_symlink() for item in [path, *path.parents] if ROOT in item.parents):
        raise ValueError('ASPIRE_EVIDENCE_PATH must not traverse symbolic links.')
    if preparing:
        path.mkdir(parents=True, exist_ok=True)
        if any(path.iterdir()):
            raise ValueError('Preparation requires a fresh empty evidence directory; existing files were left unchanged.')
        (path / OWNER_FILE).write_text(uuid.uuid4().hex + '\n')
    elif not path.is_dir() or not (path / OWNER_FILE).is_file() \
            or re.fullmatch(r'[0-9a-f]{32}\n', (path / OWNER_FILE).read_text()) is None:
        raise ValueError('A task-owned prepared evidence directory is required.')
    return path


def require_contract() -> None:
    if os.environ.get('ASPIRE_TEST_PROJECT', PROJECT) != PROJECT:
        raise ValueError(f'ASPIRE_TEST_PROJECT must be {PROJECT}.')
    if os.environ.get('TEST_PLATFORM', 'microsoft-testing-platform') != 'microsoft-testing-platform':
        raise ValueError('TEST_PLATFORM must be microsoft-testing-platform.')


def restored_cohort(project: Path, required: str, *, deployed_required: bool = True, apphost_required: bool = False) -> dict:
    """Verify restored EventStore archives and any assemblies copied to the project output."""
    assets = json.loads((project.parent / 'obj/project.assets.json').read_text())
    libraries = {name: item for name, item in assets['libraries'].items()
                 if name.lower().startswith('hexalith.eventstore.')}
    if required + '/' + EVENTSTORE_COHORT not in libraries or any(
            not name.endswith('/' + EVENTSTORE_COHORT) or item.get('type') != 'package'
            for name, item in libraries.items()):
        raise ValueError(f'{project}: restored assets must contain only the exact published EventStore package cohort.')
    target = assets['targets']['net11.0']
    output = project.parent / 'bin/Release/net11.0'
    packages = {}
    for identity in sorted(libraries):
        name, version = identity.split('/')
        archive_name = name.lower() + '.' + version + '.nupkg'
        folder = next((Path(root) / identity.lower() for root in assets['packageFolders']
                       if (Path(root) / identity.lower() / archive_name).is_file()), None)
        if folder is None:
            raise ValueError(f'The restored package archive is unavailable: {identity}.')
        archive_path = folder / archive_name
        with ZipFile(archive_path) as archive:
            nuspecs = [entry for entry in archive.namelist() if entry.endswith('.nuspec')]
            if len(nuspecs) != 1:
                raise ValueError(f'Package archive must contain one nuspec: {identity}.')
            nuspec = archive.read(nuspecs[0])
            if (folder / (name.lower() + '.nuspec')).read_bytes() != nuspec:
                raise ValueError(f'Extracted package metadata differs from its archive: {identity}.')
            metadata = ET.fromstring(nuspec).find('{*}metadata')
            repository = metadata.find('{*}repository') if metadata is not None else None
            commit = repository.get('commit', '') if repository is not None else ''
            if metadata is None or metadata.findtext('{*}id') != name or metadata.findtext('{*}version') != version \
                    or not re.fullmatch('[0-9a-f]{40}', commit):
                raise ValueError(f'Package archive must identify its exact published identity and source: {identity}.')
            native_cohort.require_restored_archive(archive_path, native_cohort.manifest(NATIVE_SELECTION), identity)
            binaries = {}
            for asset in sorted(target[identity].get('runtime', {})):
                if not asset.lower().endswith('.dll'):
                    continue
                expected = archive.read(asset)
                if (folder / asset).read_bytes() != expected:
                    raise ValueError(f'Extracted package binary differs from its archive: {identity}/{asset}.')
                deployed = output / Path(asset).name
                if deployed.is_file() and deployed.read_bytes() != expected:
                    raise ValueError(f'Deployed EventStore binary differs from its archive: {deployed}.')
                if deployed_required and not deployed.is_file():
                    raise ValueError(f'Launched host is missing its restored EventStore binary: {deployed}.')
                binaries[Path(asset).name] = hashlib.sha256(expected).hexdigest()
            packages[identity] = {'sourceCommit': commit, 'sha256': hashlib.sha256(archive_path.read_bytes()).hexdigest(),
                                  'binaries': binaries}
    owned = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
             for path in sorted(output.iterdir()) if path.is_file() and path.suffix in ('.dll', '.json')}
    if apphost_required:
        # Native qualification runs on Linux, where the SDK apphost has no extension.
        executable = output / project.stem
        if executable.is_symlink() or not executable.is_file() or not os.access(executable, os.X_OK):
            raise ValueError(f'Launched host is missing its regular executable apphost: {executable}.')
        owned[executable.name] = hashlib.sha256(executable.read_bytes()).hexdigest()
    return {'packages': packages, 'output': owned, 'deploymentRequired': deployed_required}


def gateway_package_provenance(source_root: Path | None = None) -> dict:
    """Bind every launched host, the restored archives and actual configuration to one receipt."""
    source_root = source_root or ROOT / 'references'
    selection = native_cohort.manifest(NATIVE_SELECTION)
    gateway = restored_cohort(ROOT / PACKAGE_GATEWAY, 'Hexalith.EventStore.Gateway', apphost_required=True)
    identity = 'Hexalith.EventStore.Gateway/' + EVENTSTORE_COHORT
    package = gateway['packages'][identity]
    domains = {module: restored_cohort(source_root / module / 'src' / module / (module + '.csproj'),
                                      'Hexalith.EventStore.DomainService')
               for module in ('Hexalith.Tenants', 'Hexalith.Parties')}
    adapter = restored_cohort(source_root / 'Hexalith.Parties/src/Hexalith.Parties.EventStoreExtensions/Hexalith.Parties.EventStoreExtensions.csproj',
                              'Hexalith.EventStore.DomainService', deployed_required=True)
    tenant = native_cohort.TENANT_COHORTS[EVENTSTORE_COHORT]
    composition = native_cohort.verify_runtime_assets(ROOT / 'tests/Hexalith.McpCli.AppHost/Hexalith.McpCli.AppHost.csproj',
                                                      selection, 'Hexalith.Tenants.Aspire/' + tenant)
    client = native_cohort.verify_runtime_assets(ROOT / 'tests/Hexalith.McpCli.ConformanceHost/Hexalith.McpCli.ConformanceHost.csproj',
                                                 selection, 'Hexalith.Tenants.Contracts/' + tenant)
    source = ROOT / 'references/Hexalith.EventStore'
    host = (ROOT / PACKAGE_GATEWAY).parent
    manifest = host / 'Configuration/provenance-current.json'
    configuration_source = json.loads(manifest.read_text())
    commit = configuration_source.get('sourceCommit', '')
    expected_files = {
        'Configuration/appsettings.gateway.json': 'src/Hexalith.EventStore/appsettings.json',
        'Properties/launchSettings.json': 'src/Hexalith.EventStore/Properties/launchSettings.json',
    }
    if configuration_source.get('profile') != 'published' \
            or configuration_source.get('eventStoreVersion') != EVENTSTORE_COHORT \
            or configuration_source.get('sourceRepository') != 'https://github.com/Hexalith/Hexalith.EventStore.git' \
            or commit != selection['sources']['Hexalith.EventStore']['commit'] \
            or set(configuration_source.get('files', {})) != set(expected_files):
        raise ValueError('The package configuration snapshot must declare its exact published cohort and native source identity.')
    for relative, original in expected_files.items():
        entry = configuration_source['files'][relative]
        snapshot = (host / relative).read_bytes()
        if entry.get('sourcePath') != original or entry.get('sha256') != hashlib.sha256(snapshot).hexdigest():
            raise ValueError('The package configuration snapshot differs from its declared native source provenance.')
        # Source is needed only by actual live qualification. Builds-only conformance
        # compiles and exercises the same required, owned snapshot without a runtime checkout.
        native = subprocess.check_output(['git', 'show', commit + ':' + original], cwd=source, timeout=10)
        if native != snapshot:
            raise ValueError('The package configuration snapshot differs from its exact native source blob.')
    deployed = host / 'bin/Release/net11.0/appsettings.gateway.json'
    if (host / 'Configuration/appsettings.gateway.json').read_bytes() != deployed.read_bytes():
        raise ValueError('The published gateway configuration differs from its source-bound snapshot.')
    paths = [manifest, *(host / relative for relative in expected_files), deployed,
             ROOT / 'tests/Hexalith.McpCli.AppHost/appsettings.json']
    paths.extend(sorted((ROOT / 'tests/Hexalith.McpCli.AppHost/DaprComponents').glob('*.yaml')))
    for module in ('Hexalith.Tenants', 'Hexalith.Parties'):
        directory = source_root / module / 'src' / module
        paths.extend(sorted(directory.glob('appsettings*.json')))
        paths.extend(sorted((directory / 'bin/Release/net11.0').glob('appsettings*.json')))
    configuration = {str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else 'source-fixtures/' + str(path.relative_to(source_root)):
                     hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    return {'profile': 'published', 'version': EVENTSTORE_COHORT, 'sourceCommit': package['sourceCommit'],
            'sha256': package['sha256'], 'gatewayHost': gateway, 'domainHosts': domains, 'partiesAdapter': adapter,
            'compositionHost': composition, 'clientHost': client,
            'configurationSourceCommit': commit, 'configuration': configuration}


def source_package_versions(own_versions: ET.Element) -> dict[str, str]:
    """Validate the finite unconditional current package selections without legacy injections."""
    rows = own_versions.findall('./ItemGroup/PackageVersion')
    expected = {name: {mode: name, 'Version': version}
                for name, (mode, version) in SOURCE_PACKAGE_VERSIONS.items()}
    if len(rows) != len(expected) or len(list(own_versions.iter('PackageVersion'))) != len(rows) \
            or any(group.attrib for group in own_versions.findall('ItemGroup') if group.findall('PackageVersion')) \
            or any(item.attrib != expected.get(item.get('Update') or item.get('Include')) or len(item) for item in rows) \
            or {item.get('Update') or item.get('Include') for item in rows} != set(expected):
        raise ValueError('The source package selections require the exact finite unconditional root package overrides.')
    return {name: version for name, (_, version) in SOURCE_PACKAGE_VERSIONS.items()}


def msbuild_path_literal(path: Path) -> str:
    """Escape a literal path before embedding it in MSBuild expressions or imports."""
    return re.sub(r"[%$@'();?*]", lambda match: f'%{ord(match[0]):02X}', str(path))


def require_source_catalog(prepared: dict) -> Path:
    """Recheck the pinned source catalog and exact private override before any child rebuild."""
    require_current_runtime_profile(prepared)
    native_cohort.reject_nested_catalogs(ROOT)
    private = Path(prepared['privateDirectory'])
    catalog = ROOT / 'references/Hexalith.Builds/Props/Directory.Packages.props'
    expected = prepared.get('sourcePackageCatalog', {})
    declared = subprocess.check_output(['git', 'rev-parse', 'HEAD:references/Hexalith.Builds'], cwd=ROOT, timeout=10, text=True).strip()
    checkout = catalog.parent.parent
    actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=checkout, timeout=10, text=True).strip()
    status = subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=normal', '--ignore-submodules=all'], cwd=checkout, timeout=10, text=True).strip()
    if actual != declared or actual != expected.get('buildsCommit') or status or checkout.is_symlink() \
            or hashlib.sha256(catalog.read_bytes()).hexdigest() != expected.get('catalogSha256'):
        raise ValueError('The prepared root-declared source package catalog identity or bytes changed.')
    files = {'source-runtime-packages.props': 'overlaySha256', 'source-runtime-overrides.targets': 'overridesSha256',
             'source-runtime-after-directory.targets': 'afterDirectorySha256'}
    for name, key in files.items():
        path = private / name
        if path.is_symlink() or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected.get(key):
            raise ValueError('The prepared private source package override changed or is missing.')
    nested_catalog = private / 'Hexalith.Builds' / 'Props' / 'Directory.Packages.props'
    nested_provenance = private / 'Hexalith.Builds' / 'Props' / 'ContainerProvenance.targets'
    provenance = ROOT / 'references/Hexalith.Builds/Props/ContainerProvenance.targets'
    if (private / 'Hexalith.Builds' / '.git').exists() or nested_catalog.is_symlink() or nested_provenance.is_symlink() \
            or not nested_catalog.is_file() or not nested_provenance.is_file() \
            or hashlib.sha256(nested_catalog.read_bytes()).hexdigest() != expected.get('overlaySha256') \
            or hashlib.sha256(nested_provenance.read_bytes()).hexdigest() != expected.get('nestedProvenanceSha256') \
            or not provenance.is_file() or hashlib.sha256(provenance.read_bytes()).hexdigest() != expected.get('nestedProvenanceSha256'):
        raise ValueError('The prepared private source package override changed or is missing.')
    own_versions = ET.parse(ROOT / 'Directory.Build.props').getroot()
    redis = [item.get('Version') for item in own_versions.iter('PackageVersion')
             if item.get('Update') == 'StackExchange.Redis']
    if redis != ['3.4.35']:
        raise ValueError('The prepared source package override differs from the exact root Redis pin.')
    source_package_versions(own_versions)
    return private / 'source-runtime-overrides.targets'


def reader_audit_provenance(prepared: dict | None = None) -> dict:
    """Retain exact package-byte coverage from successful online all-dependency audits."""
    projects = [PACKAGE_GATEWAY, 'tests/Hexalith.McpCli.AppHost/Hexalith.McpCli.AppHost.csproj',
                'tests/Hexalith.McpCli.ConformanceHost/Hexalith.McpCli.ConformanceHost.csproj',
                *(f'references/Hexalith.{name}/src/Hexalith.{name}/Hexalith.{name}.csproj' for name in ('Tenants', 'Parties')),
                'references/Hexalith.Parties/src/Hexalith.Parties.EventStoreExtensions/Hexalith.Parties.EventStoreExtensions.csproj']
    if prepared is not None:
        projects = [*MODULE_AUDIT_PROJECTS, *projects[3:]]
    packages, archives, sources = {}, {}, {}
    for relative in projects:
        project = ROOT / relative
        if prepared is not None and relative in prepared['nativeAudits']:
            receipt = prepared['nativeAudits'][relative]
            native_audit.require_audit(receipt, project)
            project = Path(receipt['privateDirectory']) / 'audit.csproj'
        elif prepared is not None and relative.startswith('references/'):
            project = Path(prepared['sourceFixtureRoot']) / relative.removeprefix('references/')
        assets = json.loads(project.parent.joinpath('obj/project.assets.json').read_text())
        audit = assets.get('project', {}).get('restore', {}).get('restoreAuditProperties', {})
        warning_policy = assets.get('project', {}).get('restore', {}).get('warningProperties', {})
        dependency_warnings = {framework + '/' + name: item.get('noWarn', [])
                               for framework, data in assets.get('project', {}).get('frameworks', {}).items()
                               for name, item in data.get('dependencies', {}).items() if item.get('noWarn')}
        suppressed = [*warning_policy.get('noWarn', []), *warning_policy.get('warnNotAsError', []),
                      *(code for codes in dependency_warnings.values() for code in codes)]
        if any(audit.get(name) != value for name, value in
               {'enableAudit': 'true', 'auditLevel': 'low', 'auditMode': 'all'}.items()) \
                or audit.get('suppressedAdvisories') or warning_policy.get('allWarningsAsErrors') is not True \
                or any(re.fullmatch(r'NU19\d{2}', code, re.IGNORECASE) for code in suppressed) \
                or any(item.get('level', '').lower() in ('warning', 'error') for item in assets.get('logs', [])):
            raise ValueError('The native reader requires unsuppressed low-level online all-dependency vulnerability audits with all warnings as errors.')
        graph = {}
        for identity, item in assets['libraries'].items():
            if item.get('type') != 'package':
                continue
            digest = item.get('sha512', '')
            if not re.fullmatch(r'[A-Za-z0-9+/]{86}==', digest) or identity in packages and packages[identity] != digest:
                raise ValueError('The audited package graph has missing or disagreeing package content hashes.')
            filename = identity.lower().replace('/', '.') + '.nupkg'
            archive = next((Path(folder) / identity.lower() / filename for folder in assets['packageFolders']
                            if (Path(folder) / identity.lower() / filename).is_file()), None)
            if archive is None:
                raise ValueError('An online audited package archive is missing: ' + identity)
            archive_hash = base64.b64encode(hashlib.sha512(archive.read_bytes()).digest()).decode()
            if identity in archives and archives[identity] != archive_hash:
                raise ValueError('Online audited archive bytes disagree: ' + identity)
            archives[identity] = archive_hash
            graph[identity] = packages[identity] = digest
        if not graph:
            raise ValueError('The online audited package graph is empty.')
        sources[relative] = {'packages': graph, 'policy': {'audit': audit, 'warnings': warning_policy,
                                                         'dependencyNoWarn': dependency_warnings}}
    builder = ROOT / 'references/Hexalith.Platform/src/Hexalith.Platform.CatalogBuilder'
    program = 'references/Hexalith.Platform/src/Hexalith.Platform.CatalogBuilder/Program.cs'
    extras = sorted(path.relative_to(ROOT).as_posix() for path in builder.glob('*.cs')
                    if path.is_file() and not path.is_symlink()
                    and path.name != 'Program.cs')
    inputs = ['global.json', 'Directory.Build.props', 'Directory.Packages.props',
              'references/Hexalith.Builds/Props/Directory.Packages.props',
              'references/Hexalith.Platform/src/Hexalith.Platform.CatalogBuilder/Hexalith.Platform.CatalogBuilder.csproj',
              program, *extras]
    return {'schemaVersion': 1, 'result': 'audited', 'sdkVersion': EVENTSTORE_COHORT,
            'sources': sources, 'packages': packages, 'archives': archives,
            'inputs': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in inputs},
            **({'nativeAudits': prepared['nativeAudits'], 'sourceAdvisories': prepared['sourceAdvisories']} if prepared is not None else {})}


def prove_source_advisories(private: Path, package_cache: Path, tools: dict, bounded, evidence: Path,
                            receipt: dict, *, required: bool = False) -> None:
    """Prove restore advisories as soon as the HTTP cache exists; reuse that snapshot for module audits."""
    source_http = private / 'source-http'
    snapshot = private / 'source-advisories'
    try:
        native_audit.advisory_cache_index(source_http)
    except ValueError:
        if required:
            raise
        return
    if 'sourceAdvisories' not in receipt:
        receipt['sourceAdvisories'] = native_audit.online_advisories(source_http, snapshot, bounded)
    elif not native_audit.snapshot_matches_cache(source_http, snapshot):
        shutil.rmtree(snapshot)
        receipt['sourceAdvisories'] = native_audit.online_advisories(source_http, snapshot, bounded)
    if 'nativeAudits' in receipt:
        return
    receipt['nativeAudits'] = {}
    for index, relative in enumerate(MODULE_AUDIT_PROJECTS):
        audit = native_audit.audit_project(ROOT / relative, private / ('module-audit-' + str(index)),
                                           evidence / ('module-audit-' + str(index)), tools['sdkPolicy'], bounded,
                                           proven_advisories=snapshot)
        receipt['nativeAudits'][relative] = audit
        # The isolated metadata reader has no external network. Seed its private cache
        # only from these freshly audited package bytes; never change the module cache.
        for package in (Path(audit['privateDirectory']) / 'packages').iterdir():
            if not package.is_dir():
                continue
            for version in package.iterdir():
                if not version.is_dir():
                    continue
                target = package_cache / package.name / version.name
                if target.exists():
                    for archive in version.glob('*.nupkg'):
                        if (target / archive.name).read_bytes() != archive.read_bytes():
                            raise ValueError('Private source/reader caches disagree on audited archive bytes.')
                else:
                    shutil.copytree(version, target)


def require_reader_audit(prepared: dict) -> Path:
    """Refuse drift in the retained audit proof or its current online audited graphs."""
    expected = prepared.get('readerAudit', {})
    path = Path(expected.get('path', ''))
    if path.is_symlink() or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected.get('sha256') \
            or json.loads(path.read_text()) != reader_audit_provenance(prepared if 'nativeAudits' in prepared else None):
        raise ValueError('The native reader online audit proof changed or is missing.')
    return path


def require_head_catalog(prepared: dict) -> Path:
    """Require the sealed capture bytes and exact prepared head DLL inventory."""
    expected = prepared.get('headCatalog', {})
    path = Path(expected.get('path', ''))
    if path.is_symlink() or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected.get('sha256'):
        raise ValueError('The prepared head Catalog capture changed or is missing.')
    capture = json.loads(path.read_text())
    binaries = {name: value for name, value in prepared['gateway']['clientHost']['output'].items()
                if name.endswith('.dll')}
    if not binaries or capture.get('result') != 'passed' or capture.get('binariesSha256') != binaries:
        raise ValueError('The head Catalog capture DLL inventory differs from preparation.')
    return path


def require_prepared_provenance(prepared: dict) -> dict:
    selection = native_cohort.manifest(NATIVE_SELECTION)
    if prepared.get('selection') != selection:
        raise ValueError('The authenticated native source/package selection changed after preparation.')
    require_source_catalog(prepared)
    discovery = prepared.get('discovery')
    if discovery is not None:
        discovered_path = Path(discovery['path'])
        if hashlib.sha256(discovered_path.read_bytes()).hexdigest() != discovery['sha256']:
            raise ValueError('Prepared Integration test discovery changed after preparation.')
        discovered = json.loads(discovered_path.read_text())
        if discovered['tests'] != expected_discovery() or discovered['binarySha256'] != hashlib.sha256(TESTS.read_bytes()).hexdigest():
            raise ValueError('Prepared Integration test discovery or binary changed after preparation.')
    if 'sourceAdvisories' in prepared:
        for name, page in prepared['sourceAdvisories']['pages'].items():
            path = Path(prepared['privateDirectory']) / 'source-advisories' / (name + '.json')
            if hashlib.sha256(path.read_bytes()).hexdigest() != page['sha256']:
                raise ValueError('The native source fixture advisory proof changed after preparation.')
    for source in prepared['sources']:
        checkout = ROOT / source['path']
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=checkout, timeout=10, text=True).strip()
        status = subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=normal', '--ignore-submodules=all'], cwd=checkout, timeout=10, text=True).strip()
        remote = subprocess.check_output(['git', 'remote', 'get-url', 'origin'], cwd=checkout, timeout=10, text=True).strip()
        if commit != source['selectedCommit'] or status or remote != source['repository']:
            raise ValueError('The prepared qualified source identity or clean owned files changed before execution.')
    if 'sourceFixtures' in prepared:
        source_proof = prepared['sourceFixtures']
        source_path = Path(source_proof['path'])
        if hashlib.sha256(source_path.read_bytes()).hexdigest() != source_proof['sha256']:
            raise ValueError('The private source fixture receipt changed after preparation.')
        native_sources.require(json.loads(source_path.read_text()))
    actual = gateway_package_provenance(Path(prepared['sourceFixtureRoot']) if 'sourceFixtureRoot' in prepared else None)
    if prepared.get('gateway') != actual:
        def first_difference(expected: object, observed: object, path: str = 'gateway') -> str:
            if isinstance(expected, dict) and isinstance(observed, dict):
                for key in sorted(expected.keys() | observed.keys()):
                    if key not in expected or key not in observed:
                        return path + '.' + key
                    if expected[key] != observed[key]:
                        return first_difference(expected[key], observed[key], path + '.' + key)
            return path
        changed = first_difference(prepared.get('gateway'), actual)
        raise ValueError('The prepared gateway package identity or bytes changed before isolated execution: ' + changed + '.')
    require_reader_audit(prepared)
    require_head_catalog(prepared)
    return actual


def expected_discovery() -> list[str]:
    plans = ROOT / 'tools/live-topology/plans-current'
    operations = sorted(json.loads(path.read_text())['operation'] for path in
                        (ROOT / 'tools/conformance-vectors/v1/current/modules').rglob('*.vector.json')
                        if (plans / (json.loads(path.read_text())['operation'] + '.json')).is_file())
    if not operations or len(set(operations)) != len(operations):
        raise ValueError('Live discovery requires unique approved vectors with companion plans.')
    return sorted([class_name + '.' + method for _, class_name, method in INDEPENDENT_CASES] +
                  ['Hexalith.McpCli.Integration.Tests.LiveVectorTests.ApprovedVectorHasPersistentSemantics(operation: "' + operation + '")'
                   for operation in operations])


def discover_integration(evidence: Path) -> dict:
    output = bounded(['dotnet', str(TESTS), '-preEnumerateTheories', '-list', 'tests'], 60, evidence / 'integration-discovery')
    found = sorted(line for line in output.splitlines() if line.startswith('Hexalith.McpCli.Integration.Tests.'))
    expected = expected_discovery()
    if found != expected:
        raise ValueError('Integration test discovery must equal every approved companion-plan vector and the exact independent smoke/boundary cases; extra, duplicate or missing tests refuse delegation.')
    path = evidence / 'integration-discovery.json'
    save(path, {'tests': found, 'binarySha256': hashlib.sha256(TESTS.read_bytes()).hexdigest()})
    return {'path': str(path.resolve()), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def prepare(evidence: Path) -> None:
    receipt = {'result': 'preparing', 'runId': uuid.uuid4().hex, 'sources': [], 'tools': {},
               'ownershipId': (evidence / OWNER_FILE).read_text().strip()}
    save(evidence / 'preparation.json', receipt)
    save(evidence / 'ci-live.json', {'result': 'not-run', 'fullLiveAccepted': False})
    try:
        require_contract()
        if sys.version_info < (3, 11, 4) or platform.system() != 'Linux' or platform.machine() != 'x86_64':
            raise RuntimeError('Live CI requires Linux amd64 and Python 3.11.4 or later.')
        for tool in ('timeout', 'git', 'dotnet', 'docker', 'dapr', 'aspire', 'unshare', 'ip', 'curl', 'bash'):
            if not shutil.which(tool):
                raise RuntimeError(f'Missing prerequisite: {tool}')
        for library in ('libssl.so.3', 'libcrypto.so.3'):
            try:
                ctypes.CDLL(library)
            except OSError as error:
                raise RuntimeError(f'Missing prerequisite shared library: {library}') from error
        for library in ('z', 'zstd'):
            if not ctypes.util.find_library(library):
                raise RuntimeError(f'Missing prerequisite shared library: {library}')
        tools = receipt['tools']
        receipt['discovery'] = discover_integration(evidence)
        tools['sdkPolicy'] = json.loads((ROOT / 'global.json').read_text())['sdk']
        # This command runs at ROOT, so the SDK resolver enforces global.json,
        # including its explicitly permitted patch roll-forward policy.
        tools['dotnet'] = bounded(['dotnet', '--version'], 30, evidence / 'dotnet-version')
        tools['managedResourceRuntimes'] = current_managed_runtime_selection(
            bounded(['dotnet', '--list-runtimes'], 30, evidence / 'dotnet-shared-runtimes'))
        profile = current_runtime_profile()
        cli_version = profile['tools']['dapr']['version']
        runtime_version = profile['tools']['daprd']['version']
        tools['dapr'] = bounded(['dapr', '--version'], 30, evidence / 'dapr-version')
        versions = {line.strip() for line in tools['dapr'].splitlines()}
        if not {f'CLI version: {cli_version}', f'Runtime version: {runtime_version}'} <= versions:
            raise RuntimeError(f'Dapr CLI {cli_version} and initialized runtime {runtime_version} are required; '
                               'initialize Dapr in the reusable workflow.')
        daprd = Path.home() / '.dapr/bin/daprd'
        if not daprd.is_file():
            raise RuntimeError(f'Missing initialized Dapr runtime: {daprd}')
        bounded(['docker', 'info', '--format', '{{.ServerVersion}}'], 30, evidence / 'docker-info')
        namespace_probe = ['unshare', '--user', '--map-root-user', '--net', '--pid', '--mount', '--fork', '--mount-proc', 'true']
        bounded(namespace_probe, 30, evidence / 'namespace-probe')
        temporary_root = Path(os.environ.get('RUNNER_TEMP') or tempfile.gettempdir()).resolve()
        if temporary_root.is_relative_to(evidence.resolve()):
            raise RuntimeError('RUNNER_TEMP must be outside the evidence upload directory; no private directory was created.')
        private = Path(tempfile.mkdtemp(prefix='mcpcli-live-ci-', dir=temporary_root)).resolve()
        receipt['privateDirectory'] = str(private)
        save(evidence / 'preparation.json', receipt)
        tools['aspire'] = bounded(['aspire', '--version'], 30, evidence / 'aspire-version')
        if tools['aspire'].split('+')[0] != '17.0.0':
            raise RuntimeError('Aspire CLI 17.0.0 is required.')
        tools['hostPython'] = sys.version
        tools['executables'] = {name: {'path': shutil.which(name), 'sha256': hashlib.sha256(Path(shutil.which(name)).read_bytes()).hexdigest()}
                                for name in ('aspire', 'dapr', 'dotnet')}
        tools['daprdSha256'] = hashlib.sha256(daprd.read_bytes()).hexdigest()
        verify_current_tool_bytes(profile, {name: tools['executables'][name]['path'] for name in ('aspire', 'dapr')} | {'daprd': str(daprd)})
        receipt['runtimeProfile'] = {'sha256': hashlib.sha256((ROOT / 'tools/live-topology/runtime-profile-current.json').read_bytes()).hexdigest(),
                                     'binariesSha256': profile['binaries']['sha256']}
        bundle = Path.home() / '.aspire'
        qualified = os.environ.get('HEXALITH_CI_ASPIRE_QUALIFIED_BUNDLE')
        if not qualified or not Path(qualified).is_dir():
            raise RuntimeError('The shared environment must supply its authenticated Aspire comparison bundle.')
        fresh_bundle = Path(qualified)
        expected_bundle = {str(path.relative_to(fresh_bundle)): hashlib.sha256(path.read_bytes()).hexdigest()
                           for path in fresh_bundle.rglob('*') if path.is_file()}
        if not {'dcp/dcp', 'dashboard/Aspire.Dashboard'} <= set(expected_bundle):
            raise RuntimeError('Selected qualified Aspire CLI did not extract its required embedded bundle files.')
        for relative, expected_hash in expected_bundle.items():
            installed = bundle / 'bundle' / relative
            if not installed.is_file() or hashlib.sha256(installed.read_bytes()).hexdigest() != expected_hash:
                raise RuntimeError(f'Qualified Aspire bundle mismatch: {relative}; installed bytes differ from the selected CLI embedded bundle.')
        if any(path.is_symlink() for path in fresh_bundle.rglob('*')) or any(path.is_symlink() for path in (bundle / 'bundle').rglob('*')):
            raise RuntimeError('The qualified Aspire bundle must not contain symbolic links.')
        actual_bundle = {str(path.relative_to(bundle / 'bundle')): hashlib.sha256(path.read_bytes()).hexdigest()
                         for path in (bundle / 'bundle').rglob('*') if path.is_file()}
        if actual_bundle != expected_bundle:
            raise RuntimeError('The installed Aspire bundle differs from the complete shared comparison tree.')
        tools['aspireBundle'] = expected_bundle
        save(evidence / 'aspire-bundle-hashes.json', expected_bundle)
        for relative in ('dcp/dcp', 'dashboard/Aspire.Dashboard'):
            binary = Path.home() / '.aspire/bundle' / relative
            tools[relative] = {'path': str(binary), 'sha256': hashlib.sha256(binary.read_bytes()).hexdigest()}
        selection = native_cohort.manifest(NATIVE_SELECTION)
        receipt['selection'] = selection
        # Source fixtures have their own cache; the shared module assets and outputs remain untouched.
        package_cache = private / 'packages'
        package_cache.mkdir()
        receipt['nugetPackages'] = str(package_cache)
        archives = private / 'public-archives'
        archives.mkdir()
        for package in selection['packages']:
            name = package['id'].lower() + '.' + package['version'] + '.nupkg'
            archive = archives / name
            url = f'https://api.nuget.org/v3-flatcontainer/{package["id"].lower()}/{package["version"]}/{name}'
            bounded(['curl', '--fail', '--silent', '--show-error', '--location', '--connect-timeout', '15', '--max-time', '120',
                     url, '-o', str(archive)], 130, evidence / ('public-' + package['id']))
            native_cohort.verify_archive(archive, package)
        # Source checkouts do not initialize their nested Builds gitlinks. Use the pinned root
        # catalog, container provenance targets, and current package policy for source hosts,
        # retaining each owner's native net11 graph.
        builds_root = ROOT / 'references/Hexalith.Builds'
        declared_builds = bounded(['git', 'rev-parse', 'HEAD:references/Hexalith.Builds'],
                                  10, evidence / 'builds-declared', cwd=ROOT)
        actual_builds = bounded(['git', 'rev-parse', 'HEAD'], 10, evidence / 'builds-actual', cwd=builds_root)
        builds_status = bounded(['git', 'status', '--porcelain', '--untracked-files=normal', '--ignore-submodules=all'],
                                10, evidence / 'builds-status', cwd=builds_root)
        if actual_builds != declared_builds or builds_status or builds_root.is_symlink():
            raise ValueError('The root-declared Builds catalog must match its pinned clean direct checkout.')
        catalog = builds_root / 'Props/Directory.Packages.props'
        provenance = builds_root / 'Props/ContainerProvenance.targets'
        if not provenance.is_file():
            raise ValueError('The qualified source catalog requires the pinned Builds ContainerProvenance.targets.')
        own_versions = ET.parse(ROOT / 'Directory.Build.props').getroot()
        redis = [item.get('Version') for item in own_versions.iter('PackageVersion')
                 if item.get('Update') == 'StackExchange.Redis']
        if not catalog.is_file() or redis != ['3.4.35']:
            raise ValueError('The qualified source catalog requires the exact root Redis 3.4.35 override.')
        mcpcli = [item.text for item in own_versions.iter('HexalithMcpCliVersion')]
        if mcpcli != ['3.0.0']:
            raise ValueError('The qualified source catalog requires the exact root McpCli 3.0.0 pin.')
        selections = source_package_versions(own_versions)
        overlay = private / 'source-runtime-packages.props'
        project_xml = ET.Element('Project')
        ET.SubElement(project_xml, 'Import', {'Project': msbuild_path_literal(catalog)})
        versions = ET.SubElement(project_xml, 'ItemGroup')
        for package, version in selections.items():
            ET.SubElement(versions, 'PackageVersion',
                          {SOURCE_PACKAGE_VERSIONS[package][0]: package, 'Version': version})
        ET.ElementTree(project_xml).write(overlay, encoding='utf-8', xml_declaration=True)
        # Standard post-import configuration reaches only the separate source fixtures
        # and SDK metadata preparation, preserving the shared module outputs.
        overrides = private / 'source-runtime-overrides.targets'
        overrides_xml = ET.Element('Project')
        # Keep fixture SDK preparation on the same compiler warning policy as
        # source compilation. Owner props can append exemptions even when the inherited
        # TreatWarningsAsErrors is true, changing deterministic assembly bytes.
        ET.SubElement(ET.SubElement(overrides_xml, 'PropertyGroup'), 'WarningsNotAsErrors')
        versions = ET.SubElement(overrides_xml, 'ItemGroup')
        for package, version in selections.items():
            # Owner metadata preparation can import the bare catalog, which lacks some root Include rows.
            ET.SubElement(versions, 'PackageVersion',
                          {'Include': package, 'Exclude': '@(PackageVersion)', 'Version': version})
            ET.SubElement(versions, 'PackageVersion', {'Update': package, 'Version': version})
        # The AppHost loads the root's Abstractions assembly. Source owners must
        # compile against that same version in their private fixture graph.
        ET.SubElement(ET.SubElement(overrides_xml, 'ItemGroup'), 'PackageVersion',
                      {'Update': 'Hexalith.McpCli.Abstractions', 'Version': mcpcli[0]})
        # Frozen owner props carry a separate legacy test harness pin. These private
        # runtime builds use the selected package cohort for every EventStore row.
        ET.SubElement(ET.SubElement(overrides_xml, 'ItemGroup'), 'PackageVersion',
                      {'Update': 'Hexalith.EventStore.Testing.Integration', 'Version': '$(HexalithEventStoreVersion)'})
        # Telemetry 11's replacement logging generator orders two nested Log types
        # nondeterministically. Keep the actual current Tenant source/runtime packages,
        # but select the standard LoggerMessage generator consistently before sealing.
        tenant_condition = "'$(MSBuildProjectName)' == 'Hexalith.Tenants'"
        ET.SubElement(ET.SubElement(overrides_xml, 'PropertyGroup', {'Condition': tenant_condition}),
                      'DisableMicrosoftExtensionsLoggingSourceGenerator').text = 'false'
        logging = ET.SubElement(overrides_xml, 'Target', {
            'Name': 'McpCliRequireDeterministicLoggingGenerator', 'BeforeTargets': 'CoreCompile',
            'Condition': tenant_condition})
        for item, filename, package in (
                ('_McpCliTelemetryLoggingGenerator', 'Microsoft.Gen.Logging', 'Microsoft.Extensions.Telemetry.Abstractions'),
                ('_McpCliStandardLoggingGenerator', 'Microsoft.Extensions.Logging.Generators', 'Microsoft.NETCore.App.Ref')):
            ET.SubElement(ET.SubElement(logging, 'ItemGroup'), item, {
                'Include': '@(Analyzer)', 'Condition': "'%(Analyzer.Filename)' == '" + filename + "'"})
            ET.SubElement(logging, 'Error', {'Condition': "'@(" + item + "->Count())' != '1'",
                'Text': 'The current Tenant fixture requires exactly one ' + filename + ' generator.'})
            identity = "'%(" + item + ".NuGetPackageId)' == '" + package \
                + "' And '%(" + item + ".NuGetPackageVersion)' == '11.0.0'"
            if package == 'Microsoft.NETCore.App.Ref':
                identity += " And '%(" + item + ".FrameworkReferenceName)' == 'Microsoft.NETCore.App'" \
                    + " And '%(" + item + ".FrameworkReferenceVersion)' == '11.0.0'"
            ET.SubElement(ET.SubElement(logging, 'ItemGroup'), item + 'Expected', {
                'Include': '@(' + item + ')', 'Condition': identity})
            ET.SubElement(logging, 'Error', {'Condition': "'@(" + item + "Expected->Count())' != '1'",
                'Text': 'The current Tenant fixture requires the exact ' + package + ' 11.0.0 generator identity.'})
        ET.SubElement(ET.SubElement(logging, 'ItemGroup'), 'Analyzer', {
            'Remove': '@(_McpCliTelemetryLoggingGenerator)'})
        ET.ElementTree(overrides_xml).write(overrides, encoding='utf-8', xml_declaration=True)
        # Microsoft.Common.targets imports CustomAfterMicrosoftCommonTargets inside
        # CurrentVersion.targets, then Directory.Build.targets. The published Tenants
        # 8.0.2 source qualifies EventStore only through 5.3.1; this late import
        # replaces those Error targets after the owner file and enables the 5.5.1
        # catalog constants without rewriting the frozen checkout.
        after_directory = private / 'source-runtime-after-directory.targets'
        after_xml = ET.Element('Project')
        tenants_projects = ("'$(MSBuildProjectName)' == 'Hexalith.Tenants' or "
                            "$(MSBuildProjectName.StartsWith('Hexalith.Tenants.'))")
        catalog_properties = ET.SubElement(after_xml, 'PropertyGroup', {'Condition': tenants_projects})
        ET.SubElement(catalog_properties, 'HexalithTenantsCatalogArtifactsAvailable').text = 'true'
        ET.SubElement(catalog_properties, 'DefineConstants').text = (
            '$(DefineConstants);HEXALITH_DEVELOPMENT_CATALOG_COHORT;HEXALITH_DEVELOPMENT_CATALOG_SOURCE;'
            'HEXALITH_TECHNICAL_HTTP_CATALOG_BINDING;HEXALITH_CHECKPOINTED_TENANT_PROJECTION')
        # Published Parties 4.0.0 source qualifies the catalog API only through EventStore 5.3.1.
        parties_projects = ("'$(MSBuildProjectName)' == 'Hexalith.Parties' or "
                            "$(MSBuildProjectName.StartsWith('Hexalith.Parties.'))")
        parties_properties = ET.SubElement(after_xml, 'PropertyGroup', {'Condition': parties_projects})
        ET.SubElement(parties_properties, 'DefineConstants').text = (
            '$(DefineConstants);HEXALITH_EVENTSTORE_CATALOG_API;HEXALITH_EVENTSTORE_CATALOG_HOSTS;'
            'HEXALITH_EVENTSTORE_QUERY_SELECTOR_BINDINGS;HES_CANCELLABLE_PROJECTIONS')
        ET.SubElement(after_xml, 'Target', {'Name': 'ValidateCatalogSdkSelection'})
        ET.SubElement(after_xml, 'Target', {'Name': 'ValidateCanonicalBoundaryPackageCohort'})
        ET.ElementTree(after_xml).write(after_directory, encoding='utf-8', xml_declaration=True)
        # SDK PrepareEventStoreDevelopmentOwnerAsync runs `dotnet build` without -p: overlays.
        # Tenants/Parties Directory.Packages.props import Hexalith3 from
        # ../../Hexalith.Builds (two levels above the fixture root). Place the
        # overlay catalog and provenance there, outside the sealed Git copy.
        nested_props = private / 'Hexalith.Builds' / 'Props'
        if nested_props.exists() or (private / 'Hexalith.Builds').is_symlink():
            raise ValueError('The private Hexalith.Builds overlay path is occupied.')
        nested_props.mkdir(parents=True)
        shutil.copyfile(overlay, nested_props / 'Directory.Packages.props')
        shutil.copyfile(provenance, nested_props / 'ContainerProvenance.targets')
        source_environment = dict(os.environ, NUGET_PACKAGES=str(package_cache),
                                  NUGET_HTTP_CACHE_PATH=str(private / 'source-http'),
                                  CustomAfterMicrosoftCommonTargets=str(overrides),
                                  CustomAfterDirectoryBuildTargets=str(after_directory))
        receipt['sourcePackageCatalog'] = {'buildsCommit': actual_builds,
                                           'catalogSha256': hashlib.sha256(catalog.read_bytes()).hexdigest(),
                                           'overlaySha256': hashlib.sha256(overlay.read_bytes()).hexdigest(),
                                           'overridesSha256': hashlib.sha256(overrides.read_bytes()).hexdigest(),
                                           'afterDirectorySha256': hashlib.sha256(after_directory.read_bytes()).hexdigest(),
                                           'nestedProvenanceSha256': hashlib.sha256(provenance.read_bytes()).hexdigest()}
        receipt['sources'] = native_cohort.select_sources(ROOT, selection, evidence, bounded)
        fixture_root = private / 'source-fixtures'
        source_proof = native_sources.create(ROOT, fixture_root, selection, evidence, bounded)
        receipt['sourceFixtureRoot'] = str(fixture_root)

        def source_properties(module: str) -> list[str]:
            properties = ['-p:NuGetAudit=true', '-p:NuGetAuditMode=all', '-p:NuGetAuditLevel=low', '-p:TreatWarningsAsErrors=true',
                          '-p:WarningsNotAsErrors=',
                          '-p:UseHexalithProjectReferences=false', '-p:UseNuGetDeps=true',
                          '-p:HexalithEventStoreFromSource=false', '-p:HexalithEventStoreVersion=' + EVENTSTORE_COHORT,
                          '-p:HexalithMcpCliVersion=' + mcpcli[0]]
            if module in ('Hexalith.Tenants', 'Hexalith.Parties'):
                properties.append('-p:HexalithBuildPackageVersions1=' + str(overlay))
                # Parties Directory.Packages.props imports Hexalith3BuildPackageProps
                # without Exists(); the isolated fixture has no nested Builds checkout.
                properties.append('-p:Hexalith1BuildPackageProps=' + str(overlay))
                properties.append('-p:Hexalith2BuildPackageProps=' + str(overlay))
                properties.append('-p:Hexalith3BuildPackageProps=' + str(overlay))
                properties.append('-p:HexalithContainerProvenanceTargets=' + str(provenance))
            return properties

        # Restore every source owner first, then prove the advisory HTTP cache before the long
        # compiles. Later builds use --no-restore so nuget.org cannot rotate that snapshot.
        for source in receipt['sources']:
            module = source['module']
            if module not in native_sources.MODULES:
                continue
            properties = source_properties(module)
            working = fixture_root / module
            project = f'src/{module}/{module}.csproj'
            bounded(['dotnet', 'restore', project, '-p:Configuration=Release', '-warnaserror', *properties],
                    300, evidence / (module + '-restore'), cwd=working, environment=source_environment)
            if module == 'Hexalith.Parties':
                bounded(['dotnet', 'restore', 'src/Hexalith.Parties.EventStoreExtensions/Hexalith.Parties.EventStoreExtensions.csproj',
                         '-p:Configuration=Release', '-warnaserror', '-p:CopyLocalLockFileAssemblies=true', *properties],
                        300, evidence / 'parties-adapter-restore', cwd=working, environment=source_environment)
        prove_source_advisories(private, package_cache, tools, bounded, evidence, receipt, required=True)
        for source in receipt['sources']:
            module = source['module']
            if module not in native_sources.MODULES:
                continue
            properties = source_properties(module)
            working = fixture_root / module
            project = f'src/{module}/{module}.csproj'
            source['HexalithEventStoreVersion'] = bounded(
                ['dotnet', 'msbuild', project, '-restore:false', '-getProperty:HexalithEventStoreVersion', *properties],
                30, evidence / (module + '-eventstore-version'), cwd=working, environment=source_environment)
            if source['HexalithEventStoreVersion'] != EVENTSTORE_COHORT:
                raise ValueError(f'{module} did not select the exact published EventStore cohort.')
            bounded(['dotnet', 'build', project, '--no-restore', '--configuration', 'Release', '-warnaserror', '-m:1',
                     *properties], 300, evidence / (module + '-build'), cwd=working, environment=source_environment)
            if module == 'Hexalith.Parties':
                bounded(['dotnet', 'build', 'src/Hexalith.Parties.EventStoreExtensions/Hexalith.Parties.EventStoreExtensions.csproj',
                         '--no-restore', '--configuration', 'Release', '-warnaserror', '-m:1', '-p:CopyLocalLockFileAssemblies=true', *properties],
                        300, evidence / 'parties-adapter-build', cwd=working, environment=source_environment)
            prove_source_advisories(private, package_cache, tools, bounded, evidence, receipt)
        source_path = evidence / 'native-source-fixtures.json'
        save(source_path, native_sources.seal(source_proof))
        receipt['sourceFixtures'] = {'path': str(source_path.resolve()), 'sha256': hashlib.sha256(source_path.read_bytes()).hexdigest()}
        receipt['gateway'] = gateway_package_provenance(fixture_root)
        audit_path = evidence / 'native-reader-audit.json'
        save(audit_path, reader_audit_provenance(receipt))
        receipt['readerAudit'] = {'path': str(audit_path.resolve()), 'sha256': hashlib.sha256(audit_path.read_bytes()).hexdigest()}
        python = Path(os.environ.get('HEXALITH_CI_PYTHON', ''))
        if not python.is_file():
            raise RuntimeError('The shared environment must supply its prepared Python interpreter.')
        tools['python'] = bounded([str(python), '--version'], 30, evidence / 'python-version')
        tools['jsonschema'] = bounded([str(python), '-c', 'import importlib.metadata; print(importlib.metadata.version("jsonschema"))'],
                                     30, evidence / 'jsonschema-version')
        if tools['jsonschema'] != '4.26.0':
            raise RuntimeError('The native product lane requires prepared jsonschema 4.26.0.')
        catalog_path = evidence / 'head-catalog.json'
        bounded([str(python), str(ROOT / 'tools/live-topology/capture_heads.py'), '--host',
                 str(ROOT / 'tests/Hexalith.McpCli.ConformanceHost/bin/Release/net11.0/Hexalith.McpCli.ConformanceHost.dll'),
                 '--output', str(catalog_path)], 180, evidence / 'head-catalog-capture')
        receipt['headCatalog'] = {'path': str(catalog_path.resolve()), 'sha256': hashlib.sha256(catalog_path.read_bytes()).hexdigest()}
        runtime = private / 'runtime'
        bounded([str(python), str(ROOT / 'tools/live-topology/bootstrap-runtime.py'), str(runtime)], 900, evidence / 'runtime-bootstrap')
        binaries = json.loads((ROOT / 'tools/live-topology/binaries-current.json').read_text())
        for row in binaries:
            path = runtime / 'bin' / Path(row['source']).name
            if hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
                raise RuntimeError(f'Private runtime binary hash mismatch: {path.name}')
        receipt.update(result='prepared', python=str(python), runtime=str(runtime),
                       path=str(python.parent) + os.pathsep + os.environ['PATH'])
        save(evidence / 'preparation.json', receipt)
        if os.environ.get('GITHUB_ENV'):
            with Path(os.environ['GITHUB_ENV']).open('a') as output:
                output.write(f'MCPCLI_CI_PREPARATION={evidence / "preparation.json"}\n')
        print(f'Prepared live CI: {evidence / "preparation.json"}', flush=True)
    except BaseException as error:
        receipt.update(result='failed', error=f'{type(error).__name__}: {error}')
        save(evidence / 'preparation.json', receipt)
        raise


def require_owned(path: Path, runtime: Path) -> dict:
    path = path.resolve()
    if path.name != 'result.json' or path.parent.parent != (runtime / 'runs').resolve():
        raise ValueError('Isolated receipt is outside the prepared runtime.')
    owned = json.loads(path.read_text())
    stopped = owned.get('ownedInfrastructureStopped', {})
    namespaces = owned.get('namespaces', {})
    outside = json.loads((path.parent / 'outside.json').read_text())['namespaces']
    def native_namespaces(value):
        return isinstance(value, dict) and set(value) == NAMESPACES and all(
            isinstance(identity, str) and re.fullmatch(name + r':\[[1-9][0-9]*\]', identity)
            for name, identity in value.items())
    if type(owned.get('commandExitCode')) is not int or owned['commandExitCode'] != 0 \
            or type(owned.get('supervisorPid')) is not int or owned['supervisorPid'] != 1 \
            or owned.get('prerequisitesReady') is not True \
            or not isinstance(stopped, dict) or set(stopped) != SERVICES \
            or any(type(value) is not int or not -signal.NSIG < value <= 255 for value in stopped.values()) \
            or not native_namespaces(namespaces) or not native_namespaces(outside) \
            or any(namespaces[key] == outside[key] for key in namespaces):
        raise ValueError('Private runtime did not prove prerequisites, private namespaces and owned cleanup.')
    return owned


def copy_diagnostics(runtime: Path, output: Path) -> None:
    """Copy an explicit allowlist, excluding state stores, issuer credentials and keys."""
    names = {'result.json', 'outside.json', 'command.stdout.txt', 'command.stderr.txt',
             'sentry.log', 'redis.log', 'placement.log', 'scheduler.log', 'initial-redis-backup.json', 'native-catalog.json'}
    for run in sorted((runtime / 'runs').glob('*')):
        if run.is_dir() and not run.is_symlink():
            for name in names:
                path = run / name
                if path.is_file() and not path.is_symlink():
                    target = output / run.name / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(sanitized(path.read_text(errors='replace')))


INDEPENDENT_CASE_TIMEOUT = 960
RUN_TIMEOUT_SECONDS = 13800
CLEANUP_HEADROOM_SECONDS = 600
PRE_VECTOR_CASES = (
    ('boundary', 'Hexalith.McpCli.Integration.Tests.SharedHeadBoundaryTests', 'SharedHeadsPreserveAuthorizationAndDeactivationSafety'),
)
POST_VECTOR_CASES = (
    ('smoke', 'Hexalith.McpCli.Integration.Tests.GatewaySmokeTests', 'AuthenticatedQueryReturnsSuccessfulDocument'),
)
INDEPENDENT_CASES = (*PRE_VECTOR_CASES, *POST_VECTOR_CASES)


def require_independent_case(path: Path, class_name: str, method: str) -> None:
    """Reject skipped, replaced, duplicate or runner-error cases even after a zero process exit."""
    xml = ET.parse(path).getroot()
    assemblies, cases = xml.findall('assembly'), xml.findall('.//test')
    if len(assemblies) != 1 or len(cases) != 1 or any(assemblies[0].get(key) != value for key, value in
            [('total', '1'), ('passed', '1'), ('failed', '0'), ('skipped', '0'), ('errors', '0')]) \
            or cases[0].get('result') != 'Pass' or cases[0].get('method') != method or cases[0].get('type') != class_name:
        raise ValueError(f'Independent case must contain exactly one passing, unskipped {class_name}.{method}.')


def run(evidence: Path) -> None:
    report = {'result': 'running', 'fullLiveAccepted': False, 'runId': uuid.uuid4().hex}
    save(evidence / 'ci-live.json', report)
    runtime = None
    try:
        require_contract()
        source = Path(os.environ.get('MCPCLI_CI_PREPARATION', str(evidence / 'preparation.json')))
        if source.resolve() != (evidence / 'preparation.json').resolve():
            raise ValueError('Preparation must come from the current evidence directory.')
        prepared = json.loads(source.read_text())
        if prepared.get('result') != 'prepared' or prepared.get('ownershipId') != (evidence / OWNER_FILE).read_text().strip():
            raise ValueError('Current successful preparation receipt is required.')
        gateway = require_prepared_provenance(prepared)
        source_overrides = require_source_catalog(prepared)
        reader_audit = require_reader_audit(prepared)
        prepared_runtime = Path(prepared['runtime']).resolve()
        python = Path(prepared['python'])
        if not prepared_runtime.is_dir() or not python.is_file() or not TESTS.is_file():
            raise ValueError('Prepared private runtime, Python and built Release integration tests are required.')
        for row in json.loads((ROOT / 'tools/live-topology/binaries-current.json').read_text()):
            binary = prepared_runtime / 'bin' / Path(row['source']).name
            if hashlib.sha256(binary.read_bytes()).hexdigest() != row['sha256']:
                raise ValueError(f'Prepared runtime binary hash mismatch: {binary.name}')
        if (prepared_runtime / 'runs').exists():
            raise ValueError('CI requires a fresh prepared runtime with no previous runs.')
        runtime = prepared_runtime
        environment = os.environ.copy()
        for key in list(environment):
            if key.startswith(('MCPCLI_LIVE_', 'EVENTSTORE_')):
                del environment[key]
        environment.update(McpCliCurrentNativeProfile='true', MCPCLI_ISOLATED_RUNTIME_DIR=str(runtime),
                           NUGET_PACKAGES=prepared['nugetPackages'],
                           MCPCLI_NATIVE_SOURCE_FIXTURES=prepared['sourceFixtures']['path'],
                           MCPCLI_NATIVE_SOURCE_FIXTURES_SHA256=prepared['sourceFixtures']['sha256'],
                           CustomAfterMicrosoftCommonTargets=str(source_overrides),
                           CustomAfterDirectoryBuildTargets=str(source_overrides.with_name('source-runtime-after-directory.targets')),
                           UseHexalithProjectReferences='false', UseNuGetDeps='true',
                           HexalithEventStoreFromSource='false', HexalithEventStoreVersion=EVENTSTORE_COHORT,
                           Topology__UsePackagedGateway='true',
                           MCPCLI_EVENTSTORE_PACKAGE_SOURCE_COMMIT=gateway['sourceCommit'],
                           MCPCLI_NATIVE_READER_AUDIT_PATH=str(reader_audit),
                           MCPCLI_NATIVE_READER_AUDIT_SHA256=prepared['readerAudit']['sha256'],
                           PATH=str(python.parent) + os.pathsep + prepared['path'])
        generation = evidence / report['runId']
        generation.mkdir()
        vectors = generation / 'vectors'
        report.update(preparationRunId=prepared['runId'], output=str(generation))
        report['vectors'] = {'result': 'not-run', 'reason': 'Pre-vector safety and provenance checks have not passed.'}
        independent_errors = []
        independent_receipts = []

        def run_independent(cases):
            """Run each registered independent case once with fresh state and current provenance."""
            for name, class_name, method in cases:
                case = generation / name
                case.mkdir()
                try:
                    require_prepared_provenance(prepared)
                    bounded([str(python), str(ROOT / 'tools/live-topology/run-isolated.py'), '--', 'dotnet', str(TESTS),
                             '-class', class_name, '-failSkips', '-result-xml', str(case / 'tests.xml')],
                            INDEPENDENT_CASE_TIMEOUT, case / 'process', environment={**environment, 'MCPCLI_LIVE_OUTPUT': str(case)})
                    require_independent_case(case / 'tests.xml', class_name, method)
                    lines = (case / 'process.stdout.txt').read_text().splitlines()
                    runs = [Path(line.removeprefix('Isolated run: ')) for line in lines if line.startswith('Isolated run: ')]
                    if len(runs) != 1:
                        raise ValueError(f'Independent {name} omitted its isolated runtime receipt.')
                    receipt = runs[0] / 'result.json'
                    require_owned(receipt, runtime)
                    if receipt in independent_receipts:
                        raise ValueError('Independent cases reused an isolated runtime receipt.')
                    independent_receipts.append(receipt)
                    report[name] = {'result': 'passed', 'receipt': str(receipt)}
                except Exception as error:
                    report[name] = {'result': 'failed', 'error': f'{type(error).__name__}: {error}'}
                    independent_errors.append(f'independent {name} failed: {error}')

        run_independent(PRE_VECTOR_CASES)
        if independent_errors:
            report['vectors'] = {'result': 'not-run', 'reason': 'Independent safety cases failed before vector execution.'}
            raise RuntimeError('; '.join(independent_errors))
        # Recheck all sealed module and private fixture inputs before any vector executes.
        require_prepared_provenance(prepared)
        vector_error = None
        try:
            bounded([str(python), str(ROOT / 'tools/live-topology/run-vectors.py'), '--output', str(vectors)],
                    RUN_TIMEOUT_SECONDS - len(INDEPENDENT_CASES) * INDEPENDENT_CASE_TIMEOUT - CLEANUP_HEADROOM_SECONDS,
                    generation / 'vectors-process', environment=environment)
            lane = json.loads((vectors / 'live-lane.json').read_text())
            # The live set is every approved vector with a companion plan; a vector without one is loopback-only.
            expected = sorted(operation for operation in (json.loads(path.read_text())['operation'] for path in
                              (ROOT / 'tools/conformance-vectors/v1/current/modules').rglob('*.vector.json'))
                              if (ROOT / 'tools/live-topology/plans-current' / (operation + '.json')).is_file())
            outcomes = lane.get('vectors', [])
            if not expected or len(set(expected)) != len(expected) or lane.get('coverage') != expected \
                    or lane.get('result') != 'passed' or lane.get('fullLiveAccepted') is not True \
                    or lane.get('passed') != len(expected) or lane.get('failed') != 0 \
                    or sorted(item.get('operation', '') for item in outcomes) != expected \
                    or len({item.get('isolatedReceipt') for item in outcomes}) != len(expected) \
                    or any(item.get('result') != 'passed' or item.get('exitCode') != 0 for item in outcomes):
                raise ValueError('Complete current passing evidence for every approved live vector is required; partial/preflight/skipped evidence is refused.')
            for item in outcomes:
                require_owned(Path(item['isolatedReceipt']), runtime)
            report['vectors'] = {'result': 'passed', 'count': len(expected), 'receipt': str(vectors / 'live-lane.json')}
        except BaseException as error:
            failures = []
            interrupted = []
            lane_error = None
            if (vectors / 'live-lane.json').is_file():
                try:
                    lane = json.loads((vectors / 'live-lane.json').read_text())
                    lane_error = lane.get('error')
                    failures = [{key: item.get(key) for key in ('operation', 'result', 'error')}
                                for item in lane.get('vectors', []) if item.get('result') == 'failed']
                    interrupted = [{key: item.get(key) for key in ('operation', 'result', 'error')}
                                   for item in lane.get('vectors', []) if item.get('result') == 'running']
                except (ValueError, AttributeError, TypeError):
                    pass  # Retain the original failure and still attempt the post-vector independent cases.
            detail = '; failed Operations: ' + ', '.join(str(item['operation']) for item in failures) if failures else ''
            if interrupted:
                detail += '; interrupted Operations: ' + ', '.join(str(item['operation']) for item in interrupted)
            if lane_error:
                detail += f'; lane error: {lane_error}'
            detail += f'; lane receipt: {vectors / "live-lane.json"}; runner stdout: {generation / "vectors-process.stdout.txt"}'
            vector_error = RuntimeError(str(error) + detail)
            report['vectors'] = {'result': 'failed', 'error': str(vector_error), 'failures': failures,
                                 'interrupted': interrupted, 'laneError': lane_error, 'receipt': str(vectors / 'live-lane.json')}
            if not isinstance(error, Exception):
                print(sanitized(f'Live CI interrupted: {type(error).__name__}: {vector_error}'), file=sys.stderr)
                raise
        run_independent(POST_VECTOR_CASES)
        if vector_error or independent_errors:
            raise RuntimeError('; '.join(([str(vector_error)] if vector_error else []) + independent_errors))
        expected_runtimes = len(expected) + len(INDEPENDENT_CASES)
        if len(list((runtime / 'runs').iterdir())) != expected_runtimes:
            raise ValueError(f'Expected exactly {len(expected)} fresh vector runtimes and {len(INDEPENDENT_CASES)} independent runtimes.')
        report.update(result='passed', fullLiveAccepted=True)
    except BaseException as error:
        report.update(result='failed', error=f'{type(error).__name__}: {error}')
        if isinstance(error, Exception) and report.get('vectors', {}).get('result') == 'failed' and not report.get('smoke'):
            combined = RuntimeError(f'{report["vectors"]["error"]}; independent smoke failed: {error}')
            report['error'] = f'RuntimeError: {combined}'
            raise combined from error
        raise
    finally:
        if runtime:
            copy_diagnostics(runtime, evidence / report['runId'] / 'runtime-diagnostics')
        for pattern in ('*.stdout.txt', '*.stderr.txt', 'tests.xml'):
            for path in (evidence / report['runId']).rglob(pattern):
                text = path.read_text(errors='replace')
                path.write_text(sanitized_xml(text) if path.name == 'tests.xml' else sanitized(text))
        save(evidence / 'ci-live.json', report)


def main() -> int:
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    try:
        evidence = evidence_directory(preparing=sys.argv[1:] == ['prepare'])
        if sys.argv[1:] == ['prepare']:
            prepare(evidence)
        elif sys.argv[1:] == ['run']:
            run(evidence)
        else:
            raise ValueError('Expected prepare or run.')
        return 0
    except Exception as error:
        print(sanitized(f'Live CI failed: {type(error).__name__}: {error}'), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
