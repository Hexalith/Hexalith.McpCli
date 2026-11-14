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

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from evidence_redaction import sanitized, sanitized_xml
PROJECT = 'tests/Hexalith.McpCli.Integration.Tests'
TESTS = ROOT / PROJECT / 'bin/Release/net10.0/Hexalith.McpCli.Integration.Tests.dll'
MODULES = native_cohort.MODULES
# Published Testing.Integration remains independent of these test-owned launched SDK hosts.
EVENTSTORE_COHORT = native_cohort.COHORT
NATIVE_SELECTION = ROOT / 'tools/live-topology/native-runtime-current.json'
PACKAGE_GATEWAY = 'tests/Hexalith.McpCli.EventStoreGateway.TestHost/Hexalith.McpCli.EventStoreGateway.TestHost.csproj'
SERVICES = {'sentry', 'redis', 'placement', 'scheduler'}
NAMESPACES = {'user', 'pid', 'net', 'mnt'}
OWNER_FILE = '.mcpcli-ci-owner'
ASPIRE_CLI_URL = 'https://github.com/microsoft/aspire/releases/download/v13.6.5/aspire-cli-linux-x64-13.6.5.tar.gz'
ASPIRE_CLI_SHA256 = '6e22bd4daaa62d09320638246e57bfaf56ed147a3a87cdd5eafec277726ca978'
SOURCE_COMPATIBILITY_VERSIONS = {
    'Hexalith.Commons.UniqueIds': '2.30.10',
    'Microsoft.AspNetCore.Authentication.JwtBearer': '10.0.15',
    'Microsoft.AspNetCore.OpenApi': '10.0.15',
    'Microsoft.AspNetCore.SignalR.StackExchangeRedis': '10.0.15',
    'Microsoft.OpenApi': '2.13.0',
}
# Private selections for the archived net10 Parties host; these are not root overrides.
PARTIES_SOURCE_COMPATIBILITY_VERSIONS = {
    'Hexalith.Commons': '2.30.10',
    'Hexalith.Commons.Http': '2.30.10',
}


def current_runtime_profile() -> dict:
    """Load only the finite current toolchain and its exact pinned native binary map."""
    path = ROOT / 'tools/live-topology/runtime-profile-current.json'
    value = json.loads(path.read_text())
    expected = {'aspire': '13.6.5', 'dapr': '1.19.1', 'daprd': '1.19.1'}
    if value.get('schemaVersion') != 1 or value.get('profile') != 'current-sdk42-aspire1365-dapr1191' \
            or set(value.get('tools', {})) != set(expected):
        raise ValueError('The exact finite current runtime profile is required.')
    if value.get('managedTestHosts') != {'runtime': '11.0.0', 'targetFramework': 'net10.0',
            'projects': ['Hexalith.McpCli.AppHost', 'Hexalith.McpCli.Integration.Tests'],
            'resourceLaunch': {'rollForward': 'LatestMajor', 'highestInstalledRuntime': '11.0.0',
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
    """LatestMajor is finite here: refuse any missing or newer selected shared framework."""
    names = {'Microsoft.NETCore.App', 'Microsoft.AspNetCore.App'}
    found = {name: [] for name in names}
    for line in output.splitlines():
        parts = line.split()
        if parts and parts[0] in names:
            if len(parts) < 3 or not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', parts[1]):
                raise ValueError('Current native resources require a stable, measured managed runtime inventory.')
            found[parts[0]].append(tuple(map(int, parts[1].split('.'))))
    if any(not versions or max(versions) != (11, 0, 0) for versions in found.values()):
        raise ValueError('Current native resource roll-forward requires highest installed Core and ASP.NET runtime 11.0.0.')
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
    actual = ['timeout', '--signal=TERM', '--kill-after=30s', str(seconds), *map(str, command)]
    print(sanitized(f'Running ({seconds}s): {" ".join(map(str, command))}', environment=environment), flush=True)
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
            save(output.parent / (output.name + '.command.json'), {'command': list(map(str, command)), 'cwd': str(cwd),
                 'timeoutSeconds': seconds, 'exitCode': child.returncode}, environment=environment)
    if code != 0:
        raise RuntimeError(sanitized(f'{" ".join(map(str, command))} exited {code}; '
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


def restored_cohort(project: Path, required: str, *, deployed_required: bool = True) -> dict:
    """Verify restored EventStore archives and any assemblies copied to the project output."""
    assets = json.loads((project.parent / 'obj/project.assets.json').read_text())
    libraries = {name: item for name, item in assets['libraries'].items()
                 if name.lower().startswith('hexalith.eventstore.')}
    if required + '/' + EVENTSTORE_COHORT not in libraries or any(
            not name.endswith('/' + EVENTSTORE_COHORT) or item.get('type') != 'package'
            for name, item in libraries.items()):
        raise ValueError(f'{project}: restored assets must contain only the exact published EventStore package cohort.')
    target = assets['targets']['net10.0']
    output = project.parent / 'bin/Release/net10.0'
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
    return {'packages': packages, 'output': owned, 'deploymentRequired': deployed_required}


def gateway_package_provenance() -> dict:
    """Bind every launched host, the restored archives and actual configuration to one receipt."""
    selection = native_cohort.manifest(NATIVE_SELECTION)
    gateway = restored_cohort(ROOT / PACKAGE_GATEWAY, 'Hexalith.EventStore.Gateway')
    identity = 'Hexalith.EventStore.Gateway/' + EVENTSTORE_COHORT
    package = gateway['packages'][identity]
    domains = {module: restored_cohort(ROOT / 'references' / module / 'src' / module / (module + '.csproj'),
                                      'Hexalith.EventStore.DomainService')
               for module in ('Hexalith.Tenants', 'Hexalith.Parties')}
    adapter = restored_cohort(ROOT / 'references/Hexalith.Parties/src/Hexalith.Parties.EventStoreExtensions/Hexalith.Parties.EventStoreExtensions.csproj',
                              'Hexalith.EventStore.DomainService', deployed_required=True)
    composition = native_cohort.verify_runtime_assets(ROOT / 'tests/Hexalith.McpCli.AppHost/Hexalith.McpCli.AppHost.csproj',
                                                      selection, 'Hexalith.Tenants.Aspire/7.0.7')
    client = native_cohort.verify_runtime_assets(ROOT / 'tests/Hexalith.McpCli.ConformanceHost/Hexalith.McpCli.ConformanceHost.csproj',
                                                 selection, 'Hexalith.Tenants.Contracts/7.0.7')
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
    deployed = host / 'bin/Release/net10.0/appsettings.gateway.json'
    if (host / 'Configuration/appsettings.gateway.json').read_bytes() != deployed.read_bytes():
        raise ValueError('The published gateway configuration differs from its source-bound snapshot.')
    paths = [manifest, *(host / relative for relative in expected_files), deployed,
             ROOT / 'tests/Hexalith.McpCli.AppHost/appsettings.json']
    paths.extend(sorted((ROOT / 'tests/Hexalith.McpCli.AppHost/DaprComponents').glob('*.yaml')))
    for module in ('Hexalith.Tenants', 'Hexalith.Parties'):
        directory = ROOT / 'references' / module / 'src' / module
        paths.extend(sorted(directory.glob('appsettings*.json')))
        paths.extend(sorted((directory / 'bin/Release/net10.0').glob('appsettings*.json')))
    configuration = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    return {'profile': 'published', 'version': EVENTSTORE_COHORT, 'sourceCommit': package['sourceCommit'],
            'sha256': package['sha256'], 'gatewayHost': gateway, 'domainHosts': domains, 'partiesAdapter': adapter,
            'compositionHost': composition, 'clientHost': client,
            'configurationSourceCommit': commit, 'configuration': configuration}


def source_compatibility_versions(own_versions: ET.Element) -> dict[str, str]:
    """Reuse only the exact reviewed, unconditional root package selections."""
    expected = SOURCE_COMPATIBILITY_VERSIONS | {
        'Hexalith.EventStore.Testing.Integration': EVENTSTORE_COHORT,
        'StackExchange.Redis': '3.4.31',
    }
    rows = own_versions.findall('./ItemGroup/PackageVersion')
    if len(rows) != len(expected) or len(list(own_versions.iter('PackageVersion'))) != len(rows) \
            or any(group.attrib for group in own_versions.findall('ItemGroup') if group.findall('PackageVersion')) \
            or any(item.attrib != {'Update': item.get('Update'), 'Version': expected.get(item.get('Update'))}
                   or len(item) for item in rows) \
            or {item.get('Update') for item in rows} != set(expected):
        raise ValueError('The source compatibility selections require the exact finite unconditional root package overrides.')
    return {item.get('Update'): item.get('Version') for item in rows
            if item.get('Update') in SOURCE_COMPATIBILITY_VERSIONS}


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
    files = {'source-runtime-packages.props': 'overlaySha256', 'source-runtime-overrides.targets': 'overridesSha256'}
    for name, key in files.items():
        path = private / name
        if path.is_symlink() or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected.get(key):
            raise ValueError('The prepared private source package override changed or is missing.')
    own_versions = ET.parse(ROOT / 'Directory.Build.props').getroot()
    redis = [item.get('Version') for item in own_versions.iter('PackageVersion')
             if item.get('Update') == 'StackExchange.Redis']
    if redis != ['3.4.31']:
        raise ValueError('The prepared source package override differs from the exact root Redis pin.')
    source_compatibility_versions(own_versions)
    return private / 'source-runtime-overrides.targets'


def reader_audit_provenance() -> dict:
    """Retain exact package-byte coverage from successful online all-dependency audits."""
    projects = [PACKAGE_GATEWAY, 'tests/Hexalith.McpCli.AppHost/Hexalith.McpCli.AppHost.csproj',
                'tests/Hexalith.McpCli.ConformanceHost/Hexalith.McpCli.ConformanceHost.csproj',
                *(f'references/Hexalith.{name}/src/Hexalith.{name}/Hexalith.{name}.csproj' for name in ('Tenants', 'Parties')),
                'references/Hexalith.Parties/src/Hexalith.Parties.EventStoreExtensions/Hexalith.Parties.EventStoreExtensions.csproj']
    packages, archives, sources = {}, {}, {}
    for relative in projects:
        assets = json.loads((ROOT / relative).parent.joinpath('obj/project.assets.json').read_text())
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
    inputs = ['global.json', 'Directory.Build.props', 'Directory.Packages.props',
              'references/Hexalith.Builds/Props/Directory.Packages.props',
              'references/Hexalith.Platform/src/Hexalith.Platform.CatalogBuilder/Hexalith.Platform.CatalogBuilder.csproj',
              'references/Hexalith.Platform/src/Hexalith.Platform.CatalogBuilder/Program.cs']
    cohort_source = 'references/Hexalith.Platform/src/Hexalith.Platform.CatalogBuilder/PublishedCatalogArtifactCohort.cs'
    if (ROOT / cohort_source).is_file():
        inputs.append(cohort_source)
    return {'schemaVersion': 1, 'result': 'audited', 'sdkVersion': EVENTSTORE_COHORT,
            'sources': sources, 'packages': packages, 'archives': archives,
            'inputs': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in inputs}}


def require_reader_audit(prepared: dict) -> Path:
    """Refuse drift in the retained audit proof or its current online audited graphs."""
    expected = prepared.get('readerAudit', {})
    path = Path(expected.get('path', ''))
    if path.is_symlink() or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected.get('sha256') \
            or json.loads(path.read_text()) != reader_audit_provenance():
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
    for source in prepared['sources']:
        checkout = ROOT / source['path']
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=checkout, timeout=10, text=True).strip()
        status = subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=normal', '--ignore-submodules=all'], cwd=checkout, timeout=10, text=True).strip()
        remote = subprocess.check_output(['git', 'remote', 'get-url', 'origin'], cwd=checkout, timeout=10, text=True).strip()
        if commit != source['selectedCommit'] or status or remote != source['repository']:
            raise ValueError('The prepared qualified source identity or clean owned files changed before execution.')
    actual = gateway_package_provenance()
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


def prepare(evidence: Path) -> None:
    receipt = {'result': 'preparing', 'runId': uuid.uuid4().hex, 'sources': [], 'tools': {},
               'ownershipId': (evidence / OWNER_FILE).read_text().strip()}
    save(evidence / 'preparation.json', receipt)
    save(evidence / 'ci-live.json', {'result': 'not-run', 'fullLiveAccepted': False})
    try:
        require_contract()
        if sys.version_info < (3, 11, 4) or platform.system() != 'Linux' or platform.machine() != 'x86_64':
            raise RuntimeError('Live CI requires Linux amd64 and Python 3.11.4 or later.')
        for tool in ('timeout', 'git', 'dotnet', 'docker', 'dapr', 'unshare', 'ip', 'curl', 'bash'):
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
        tools['sdkPolicy'] = json.loads((ROOT / 'global.json').read_text())['sdk']
        # This command runs at ROOT, so the SDK resolver enforces global.json,
        # including its explicitly permitted patch roll-forward policy.
        tools['dotnet'] = bounded(['dotnet', '--version'], 30, evidence / 'dotnet-version')
        tools['managedResourceRuntimes'] = current_managed_runtime_selection(
            bounded(['dotnet', '--list-runtimes'], 30, evidence / 'dotnet-shared-runtimes'))
        tools['dapr'] = bounded(['dapr', '--version'], 30, evidence / 'dapr-version')
        if not re.search(r'CLI version: 1\.19\.1\s', tools['dapr'] + '\n') or not re.search(r'Runtime version: 1\.19\.1\s', tools['dapr'] + '\n'):
            raise RuntimeError('Dapr CLI 1.19.1 and initialized runtime 1.19.1 are required; initialize Dapr in the reusable workflow.')
        daprd = Path.home() / '.dapr/bin/daprd'
        if not daprd.is_file():
            raise RuntimeError(f'Missing initialized Dapr runtime: {daprd}')
        bounded(['docker', 'info', '--format', '{{.ServerVersion}}'], 30, evidence / 'docker-info')
        namespace_probe = ['unshare', '--user', '--map-root-user', '--net', '--pid', '--mount', '--fork', '--mount-proc', 'true']
        try:
            bounded(namespace_probe, 30, evidence / 'namespace-probe')
        except RuntimeError:
            if os.environ.get('GITHUB_ACTIONS') != 'true' or os.environ.get('RUNNER_ENVIRONMENT') != 'github-hosted':
                raise
            # Only the disposable hosted VM is configured; every test still
            # proves private user/PID/network/mount namespaces in the wrapper.
            bounded(['sudo', '-n', 'sysctl', '-w', 'kernel.apparmor_restrict_unprivileged_userns=0'],
                    30, evidence / 'hosted-namespace-setup')
            bounded(namespace_probe, 30, evidence / 'namespace-probe-configured')
        temporary_root = Path(os.environ.get('RUNNER_TEMP') or tempfile.gettempdir()).resolve()
        if temporary_root.is_relative_to(evidence.resolve()):
            raise RuntimeError('RUNNER_TEMP must be outside the evidence upload directory; no private directory was created.')
        private = Path(tempfile.mkdtemp(prefix='mcpcli-live-ci-', dir=temporary_root)).resolve()
        receipt['privateDirectory'] = str(private)
        save(evidence / 'preparation.json', receipt)
        if not shutil.which('aspire'):
            archive = private / 'aspire-cli.tar.gz'
            bounded(['curl', '--fail', '--silent', '--show-error', '--location', '--connect-timeout', '15', '--max-time', '120',
                     ASPIRE_CLI_URL, '-o', str(archive)], 130, evidence / 'aspire-download')
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            if digest != ASPIRE_CLI_SHA256:
                raise RuntimeError('Aspire CLI release archive SHA-256 mismatch; refusing extraction.')
            tools['aspireArchive'] = {'url': ASPIRE_CLI_URL, 'sha256': digest}
            installed_cli = private / 'aspire-cli'
            with tarfile.open(archive, 'r:gz') as release:
                release.extractall(installed_cli, filter='data')
            os.environ['PATH'] = str(installed_cli) + os.pathsep + os.environ['PATH']
        tools['aspire'] = bounded(['aspire', '--version'], 30, evidence / 'aspire-version')
        if tools['aspire'].split('+')[0] != '13.6.5':
            raise RuntimeError('Aspire CLI 13.6.5 is required.')
        tools['hostPython'] = sys.version
        tools['executables'] = {name: {'path': shutil.which(name), 'sha256': hashlib.sha256(Path(shutil.which(name)).read_bytes()).hexdigest()}
                                for name in ('aspire', 'dapr', 'dotnet')}
        tools['daprdSha256'] = hashlib.sha256(daprd.read_bytes()).hexdigest()
        profile = current_runtime_profile()
        verify_current_tool_bytes(profile, {name: tools['executables'][name]['path'] for name in ('aspire', 'dapr')} | {'daprd': str(daprd)})
        receipt['runtimeProfile'] = {'sha256': hashlib.sha256((ROOT / 'tools/live-topology/runtime-profile-current.json').read_bytes()).hexdigest(),
                                     'binariesSha256': profile['binaries']['sha256']}
        bundle = Path.home() / '.aspire'
        fresh_bundle = private / 'qualified-aspire'
        bounded(['aspire', 'setup', '--install-path', str(fresh_bundle), '--force', '--non-interactive'],
                180, evidence / 'aspire-bundle-extract')
        hosted_runner = os.environ.get('GITHUB_ACTIONS') == 'true' and os.environ.get('RUNNER_ENVIRONMENT') == 'github-hosted'
        if hosted_runner or any(not (bundle / 'bundle' / relative).is_file() for relative in ('dcp/dcp', 'dashboard/Aspire.Dashboard')):
            bounded(['aspire', 'setup', '--install-path', str(bundle), '--force', '--non-interactive'], 180, evidence / 'aspire-bundle-setup')
        expected_bundle = {str(path.relative_to(fresh_bundle / 'bundle')): hashlib.sha256(path.read_bytes()).hexdigest()
                           for path in (fresh_bundle / 'bundle').rglob('*') if path.is_file()}
        if not {'dcp/dcp', 'dashboard/Aspire.Dashboard'} <= set(expected_bundle):
            raise RuntimeError('Selected qualified Aspire CLI did not extract its required embedded bundle files.')
        for relative, expected_hash in expected_bundle.items():
            installed = bundle / 'bundle' / relative
            if not installed.is_file() or hashlib.sha256(installed.read_bytes()).hexdigest() != expected_hash:
                raise RuntimeError(f'Qualified Aspire bundle mismatch: {relative}; installed bytes differ from the selected CLI embedded bundle.')
        save(evidence / 'aspire-bundle-hashes.json', expected_bundle)
        for relative in ('dcp/dcp', 'dashboard/Aspire.Dashboard'):
            binary = Path.home() / '.aspire/bundle' / relative
            tools[relative] = {'path': str(binary), 'sha256': hashlib.sha256(binary.read_bytes()).hexdigest()}
        selection = native_cohort.manifest(NATIVE_SELECTION)
        receipt['selection'] = selection
        # Never restore an unpublished local candidate: all subprocesses share one new cache.
        package_cache = private / 'packages'
        package_cache.mkdir()
        os.environ['NUGET_PACKAGES'] = str(package_cache)
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
        # catalog and the root's reviewed net10 compatibility selections for source hosts.
        builds_root = ROOT / 'references/Hexalith.Builds'
        declared_builds = bounded(['git', 'rev-parse', 'HEAD:references/Hexalith.Builds'],
                                  10, evidence / 'builds-declared', cwd=ROOT)
        actual_builds = bounded(['git', 'rev-parse', 'HEAD'], 10, evidence / 'builds-actual', cwd=builds_root)
        builds_status = bounded(['git', 'status', '--porcelain', '--untracked-files=normal', '--ignore-submodules=all'],
                                10, evidence / 'builds-status', cwd=builds_root)
        if actual_builds != declared_builds or builds_status or builds_root.is_symlink():
            raise ValueError('The root-declared Builds catalog must match its pinned clean direct checkout.')
        catalog = builds_root / 'Props/Directory.Packages.props'
        own_versions = ET.parse(ROOT / 'Directory.Build.props').getroot()
        redis = [item.get('Version') for item in own_versions.iter('PackageVersion')
                 if item.get('Update') == 'StackExchange.Redis']
        if not catalog.is_file() or redis != ['3.4.31']:
            raise ValueError('The qualified source catalog requires the exact root Redis 3.4.31 override.')
        mcpcli = [item.text for item in own_versions.iter('HexalithMcpCliVersion')]
        if mcpcli != ['2.0.1']:
            raise ValueError('The qualified source catalog requires the exact root McpCli 2.0.1 pin.')
        compatibility = source_compatibility_versions(own_versions)
        # Include the selected owners' local project graphs, whose centrally pinned
        # transitive dependencies also need net10-compatible versions. Apply these
        # only in the post-import hook, after the owner has selected its framework.
        source_condition = "$(MSBuildProjectFullPath.Equals('" + msbuild_path_literal(ROOT / PACKAGE_GATEWAY) + "'))"
        for owner in ('Hexalith.Tenants', 'Hexalith.Parties'):
            source_condition += " Or $(MSBuildProjectFullPath.StartsWith('" + msbuild_path_literal(ROOT / 'references' / owner / 'src') + "/'))"
        overlay = private / 'source-runtime-packages.props'
        project_xml = ET.Element('Project')
        ET.SubElement(project_xml, 'Import', {'Project': msbuild_path_literal(catalog)})
        ET.SubElement(ET.SubElement(project_xml, 'ItemGroup'), 'PackageVersion',
                      {'Update': 'StackExchange.Redis', 'Version': redis[0]})
        ET.ElementTree(project_xml).write(overlay, encoding='utf-8', xml_declaration=True)
        # Standard MSBuild post-import configuration reaches SDK preparation and Aspire's
        # later dotnet rebuilds without changing an owner's source or nested catalog.
        overrides = private / 'source-runtime-overrides.targets'
        overrides_xml = ET.Element('Project')
        # Keep later SDK/Aspire builds on the same compiler warning policy as
        # preparation. Owner props can append exemptions even when the inherited
        # TreatWarningsAsErrors is true, changing deterministic assembly bytes.
        ET.SubElement(ET.SubElement(overrides_xml, 'PropertyGroup'), 'WarningsNotAsErrors')
        ET.SubElement(ET.SubElement(overrides_xml, 'ItemGroup'), 'PackageVersion',
                      {'Update': 'StackExchange.Redis', 'Version': redis[0]})
        compatible_packages = ET.SubElement(overrides_xml, 'ItemGroup', {
            'Condition': "'$(TargetFramework)' == 'net10.0' And (" + source_condition + ')'})
        for package, version in compatibility.items():
            ET.SubElement(compatible_packages, 'PackageVersion', {'Update': package, 'Version': version})
        # The frozen Parties host/Security graph also directly references these two
        # Commons packages, whose current catalog versions require net11. Keep this
        # private compatibility selection separate from the seven root override rows.
        parties_condition = "'$(TargetFramework)' == 'net10.0' And $(MSBuildProjectFullPath.StartsWith('" \
            + msbuild_path_literal(ROOT / 'references/Hexalith.Parties/src') + "/'))"
        parties_packages = ET.SubElement(overrides_xml, 'ItemGroup', {'Condition': parties_condition})
        for package, version in PARTIES_SOURCE_COMPATIBILITY_VERSIONS.items():
            ET.SubElement(parties_packages, 'PackageVersion', {'Update': package, 'Version': version})
        # The AppHost loads the root's Abstractions assembly. Source owners must
        # compile against that same version, including later SDK/Aspire rebuilds.
        ET.SubElement(ET.SubElement(overrides_xml, 'ItemGroup'), 'PackageVersion',
                      {'Update': 'Hexalith.McpCli.Abstractions', 'Version': mcpcli[0]})
        # The published Parties Web project excludes this package for its old generator
        # workaround. The current catalog requires the actual 11.x reference consistently
        # across its projects instead of silently resolving the shared-framework 10.x image.
        ET.SubElement(ET.SubElement(overrides_xml, 'ItemGroup'), 'PackageReference',
                      {'Update': 'Microsoft.Extensions.Logging.Abstractions', 'ExcludeAssets': ''})
        # Only these selected net10 source hosts need the legacy pruning workaround.
        # Applying it to the ordinary CLI changes the authenticated production closure.
        pruning_owners = ('Hexalith.McpCli.EventStoreGateway.TestHost', 'Hexalith.Tenants',
                          'Hexalith.Parties', 'Hexalith.Parties.EventStoreExtensions')
        pruning_condition = ' Or '.join("'$(MSBuildProjectName)' == '" + name + "'" for name in pruning_owners)
        ET.SubElement(ET.SubElement(overrides_xml, 'PropertyGroup', {'Condition': pruning_condition}),
                      'RestoreEnablePackagePruning').text = 'false'
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
                ('_McpCliStandardLoggingGenerator', 'Microsoft.Extensions.Logging.Generators', 'Microsoft.Extensions.Logging.Abstractions')):
            ET.SubElement(ET.SubElement(logging, 'ItemGroup'), item, {
                'Include': '@(Analyzer)', 'Condition': "'%(Analyzer.Filename)' == '" + filename + "'"})
            ET.SubElement(logging, 'Error', {'Condition': "'@(" + item + "->Count())' != '1'",
                'Text': 'The current Tenant fixture requires exactly one ' + filename + ' generator.'})
            ET.SubElement(ET.SubElement(logging, 'ItemGroup'), item + 'Expected', {
                'Include': '@(' + item + ')',
                'Condition': "'%(" + item + ".NuGetPackageId)' == '" + package
                    + "' And '%(" + item + ".NuGetPackageVersion)' == '11.0.0'"})
            ET.SubElement(logging, 'Error', {'Condition': "'@(" + item + "Expected->Count())' != '1'",
                'Text': 'The current Tenant fixture requires the exact ' + package + ' 11.0.0 generator identity.'})
        ET.SubElement(ET.SubElement(logging, 'ItemGroup'), 'Analyzer', {
            'Remove': '@(_McpCliTelemetryLoggingGenerator)'})
        ET.ElementTree(overrides_xml).write(overrides, encoding='utf-8', xml_declaration=True)
        os.environ['CustomAfterMicrosoftCommonTargets'] = str(overrides)
        receipt['sourcePackageCatalog'] = {'buildsCommit': actual_builds,
                                           'catalogSha256': hashlib.sha256(catalog.read_bytes()).hexdigest(),
                                           'overlaySha256': hashlib.sha256(overlay.read_bytes()).hexdigest(),
                                           'overridesSha256': hashlib.sha256(overrides.read_bytes()).hexdigest()}
        receipt['sources'] = native_cohort.select_sources(ROOT, selection, evidence, bounded)
        for source in receipt['sources']:
            module = source['module']
            if module == 'Hexalith.Platform':
                continue
            project = PACKAGE_GATEWAY if module == 'Hexalith.EventStore' else f'src/{module}/{module}.csproj'
            working = ROOT if module == 'Hexalith.EventStore' else ROOT / 'references' / module
            # Source owners may downgrade audit warnings; this native qualification requires every warning to fail.
            properties = ['-p:NuGetAudit=true', '-p:NuGetAuditMode=all', '-p:NuGetAuditLevel=low', '-p:TreatWarningsAsErrors=true',
                          '-p:WarningsNotAsErrors=', '-p:RestoreEnablePackagePruning=false',
                          '-p:UseHexalithProjectReferences=false', '-p:UseNuGetDeps=true',
                          '-p:HexalithEventStoreFromSource=false', '-p:HexalithEventStoreVersion=' + EVENTSTORE_COHORT]
            properties.append('-p:HexalithMcpCliVersion=' + mcpcli[0])
            if module in ('Hexalith.Tenants', 'Hexalith.Parties'):
                properties.append('-p:HexalithBuildPackageVersions1=' + str(overlay))
            source['HexalithEventStoreVersion'] = bounded(
                ['dotnet', 'msbuild', project, '-getProperty:HexalithEventStoreVersion', *properties],
                30, evidence / (module + '-eventstore-version'), cwd=working)
            if source['HexalithEventStoreVersion'] != EVENTSTORE_COHORT:
                raise ValueError(f'{module} did not select the exact published EventStore cohort.')
            command = ['dotnet', 'build', project, '--configuration', 'Release', '-warnaserror', '-m:1',
                       *properties]
            bounded(command, 300, evidence / (module + '-build'), cwd=working)
            if module == 'Hexalith.Parties':
                bounded(['dotnet', 'build', 'src/Hexalith.Parties.EventStoreExtensions/Hexalith.Parties.EventStoreExtensions.csproj',
                         '--configuration', 'Release', '-warnaserror', '-m:1', '-p:CopyLocalLockFileAssemblies=true', *properties],
                        300, evidence / 'parties-adapter-build', cwd=working)
        # Rebuild the actual AppHost and tests in the same fresh public cache.
        bounded(['dotnet', 'build', PROJECT + '/Hexalith.McpCli.Integration.Tests.csproj',
                 '--configuration', 'Release', '--no-incremental', '-warnaserror', '-m:1', '-p:McpCliCurrentNativeProfile=true',
                 '-p:NuGetAudit=true', '-p:NuGetAuditMode=all',
                 '-p:NuGetAuditLevel=low', '-p:TreatWarningsAsErrors=true', '-p:WarningsNotAsErrors='],
                300, evidence / 'native-tests-build')
        receipt['gateway'] = gateway_package_provenance()
        audit_path = evidence / 'native-reader-audit.json'
        save(audit_path, reader_audit_provenance())
        receipt['readerAudit'] = {'path': str(audit_path.resolve()), 'sha256': hashlib.sha256(audit_path.read_bytes()).hexdigest()}
        python = private / 'venv/bin/python'
        bounded([sys.executable, '-m', 'venv', str(private / 'venv')], 60, evidence / 'python-venv')
        bounded([str(python), '-m', 'pip', 'install', '--disable-pip-version-check', '-r', str(ROOT / 'tools/conformance-vectors/v1/requirements.txt')],
                180, evidence / 'python-requirements')
        tools['python'] = bounded([str(python), '--version'], 30, evidence / 'python-version')
        tools['jsonschema'] = bounded([str(python), '-c', 'import importlib.metadata; print(importlib.metadata.version("jsonschema"))'],
                                     30, evidence / 'jsonschema-version')
        catalog_path = evidence / 'head-catalog.json'
        bounded([str(python), str(ROOT / 'tools/live-topology/capture_heads.py'), '--host',
                 str(ROOT / 'tests/Hexalith.McpCli.ConformanceHost/bin/Release/net10.0/Hexalith.McpCli.ConformanceHost.dll'),
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
RUN_TIMEOUT_SECONDS = 17700
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
                           CustomAfterMicrosoftCommonTargets=str(source_overrides),
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
        # The early isolated cases can rebuild hosts; reseal-check before any vector executes.
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
