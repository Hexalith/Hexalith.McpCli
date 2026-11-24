"""Audit exact restored package bytes in private fixtures, without restoring module outputs."""
from __future__ import annotations

import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import xml.etree.ElementTree as ET

PACKAGE_SOURCE = 'https://api.nuget.org/v3/index.json'
ADVISORY_ORIGIN = 'https://data.nuget.org'
AUDIT_SOURCE = ADVISORY_ORIGIN + '/v3/index.json'
INDEX = ADVISORY_ORIGIN + '/v3/vulnerabilities/index.json'
PAGE_PREFIX = ADVISORY_ORIGIN + '/v3-vulnerabilities/'


def write_restore_config(config: Path) -> None:
    """Use the official audit-only endpoint for both restores and advisory proof."""
    config.write_text('<configuration><packageSources><clear/><add key="nuget.org" value="' + PACKAGE_SOURCE
                      + '"/></packageSources><auditSources><clear/><add key="nuget.org" value="' + AUDIT_SOURCE
                      + '"/></auditSources></configuration>\n')


def package_graph(assets_path: Path) -> dict:
    """Bind every direct/transitive restored package to its content and archive hashes."""
    assets = json.loads(assets_path.read_text())
    graph = {}
    for identity, item in assets['libraries'].items():
        if item.get('type') != 'package':
            continue
        content = item.get('sha512', '')
        if not re.fullmatch(r'[A-Za-z0-9+/]{86}==', content):
            raise ValueError('The audited graph requires every package content hash: ' + identity)
        filename = identity.lower().replace('/', '.') + '.nupkg'
        archives = [Path(folder) / identity.lower() / filename for folder in assets['packageFolders']]
        archives = [path for path in archives if path.is_file() and not path.is_symlink()]
        if len(archives) != 1:
            raise ValueError('The audited graph requires one unambiguous package archive: ' + identity)
        graph[identity] = {'contentSha512': content,
                           'archiveSha512': base64.b64encode(hashlib.sha512(archives[0].read_bytes()).digest()).decode()}
    if not graph:
        raise ValueError('The audited package graph is empty.')
    return graph


def require_policy(assets_path: Path) -> dict:
    assets = json.loads(assets_path.read_text())
    restore = assets['project']['restore']
    audit, warnings = restore.get('restoreAuditProperties', {}), restore.get('warningProperties', {})
    suppressed = [*warnings.get('noWarn', []), *warnings.get('warnNotAsError', []),
                  *(code for framework in assets['project'].get('frameworks', {}).values()
                    for package in framework.get('dependencies', {}).values() for code in package.get('noWarn', []))]
    if any(audit.get(name) != value for name, value in
           {'enableAudit': 'true', 'auditLevel': 'low', 'auditMode': 'all'}.items()) \
            or audit.get('suppressedAdvisories') or warnings.get('allWarningsAsErrors') is not True \
            or any(re.fullmatch(r'NU19\d{2}', code, re.IGNORECASE) for code in suppressed) \
            or any(item.get('level', '').lower() in ('warning', 'error') for item in assets.get('logs', [])):
        raise ValueError('The private native audit requires unsuppressed low-and-higher all-dependency audits with every warning fatal.')
    return {'audit': audit, 'warnings': warnings}


def require_coverage(expected: dict, actual: dict) -> None:
    """Every original transitive dependency must have the identical audited package bytes."""
    for identity, hashes in expected.items():
        if actual.get(identity) != hashes:
            raise ValueError('The native audit has incomplete or changed package-byte coverage: ' + identity)


def advisory_bytes_match(cached: bytes, online: bytes) -> bool:
    """Exact bytes, or equivalent JSON, prove the restore cache is the live advisory document."""
    if cached == online:
        return True
    try:
        return json.loads(cached) == json.loads(online)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return False


def refuse_advisory_mismatch(name: str, cached: bytes | None, online: bytes | None, status: str) -> None:
    def meta(payload: bytes | None) -> str:
        if payload is None:
            return 'missing'
        return hashlib.sha256(payload).hexdigest() + '/' + str(len(payload))
    raise ValueError('The native audit used stale, incomplete or cache-only advisory bytes: ' + name
                     + ' (cache=' + meta(cached) + ' online=' + meta(online) + ' status=' + status + ')')


def advisory_cache_index(cache: Path) -> Path:
    """Require the restore HTTP cache to contain exactly one NuGet advisory index."""
    indexes = list(cache.rglob('vuln_index.dat'))
    if len(indexes) != 1:
        raise ValueError('The native audit requires one complete freshly populated advisory cache.')
    return indexes[0]


def snapshot_matches_cache(cache: Path, snapshot: Path) -> bool:
    """True when the restore cache still equals an already-proven live advisory snapshot."""
    try:
        index = advisory_cache_index(cache)
    except ValueError:
        return False
    try:
        pages = json.loads(index.read_text())
    except (json.JSONDecodeError, OSError):
        return False
    files = {'index': index}
    if not isinstance(pages, list):
        return False
    for page in pages:
        name = page.get('@name') if isinstance(page, dict) else None
        if not isinstance(name, str):
            return False
        files[name] = index.with_name('vuln_data_' + name + '.dat')
    return all((snapshot / (name + '.json')).is_file() and path.is_file()
               and advisory_bytes_match(path.read_bytes(), (snapshot / (name + '.json')).read_bytes())
               for name, path in files.items())


def online_advisories(cache: Path, output: Path, bounded, proven: Path | None = None) -> dict:
    """Reject cache-only/stale local data by comparing every page to a live or already-proven snapshot."""
    index = advisory_cache_index(cache)
    pages = json.loads(index.read_text())
    if not isinstance(pages, list) or not pages or len(pages) > 16:
        raise ValueError('The native audit advisory index is incomplete.')
    names = [page.get('@name', '') for page in pages]
    if len(set(names)) != len(names) or any(not re.fullmatch(r'[A-Za-z0-9_-]+', name) for name in names):
        raise ValueError('The native audit advisory index has invalid or ambiguous pages.')
    requests = [(INDEX, index, 'index')]
    for page in pages:
        url = page.get('@id', '')
        if not url.startswith(PAGE_PREFIX) or not isinstance(page.get('@updated'), str):
            raise ValueError('The native audit advisory page is not bound to its official source.')
        requests.append((url, index.with_name('vuln_data_' + page['@name'] + '.dat'), page['@name']))
    receipt = {'retrievedAtUtc': datetime.now(timezone.utc).isoformat(), 'pages': {}, 'index': pages}
    output.mkdir()
    for url, cached, name in requests:
        destination, headers = output / (name + '.json'), output / (name + '.headers')
        if proven is not None:
            proven_file = proven / (name + '.json')
            if not proven_file.is_file():
                raise ValueError('The native audit is missing the already-proven advisory page: ' + name)
            destination.write_bytes(proven_file.read_bytes())
            headers.write_text('HTTP/2 200\n')
        else:
            for attempt in range(3):
                bounded(['curl', '--fail', '--silent', '--show-error', '--location', '--compressed', '--connect-timeout', '15', '--max-time', '120',
                         '--header', 'Cache-Control: no-cache', '--dump-header', str(headers), url, '-o', str(destination)],
                        130, output / (name + '-fetch-' + str(attempt)))
                cached_bytes = cached.read_bytes() if cached.is_file() else None
                online_bytes = destination.read_bytes() if destination.is_file() else None
                statuses = re.findall(r'^HTTP/\S+\s+(\d+)', headers.read_text(errors='replace'), re.MULTILINE) if headers.is_file() else []
                if cached_bytes is None:
                    break
                if statuses and statuses[-1] == '200' and online_bytes is not None \
                        and advisory_bytes_match(cached_bytes, online_bytes):
                    break
        cached_bytes = cached.read_bytes() if cached.is_file() else None
        online_bytes = destination.read_bytes() if destination.is_file() else None
        statuses = re.findall(r'^HTTP/\S+\s+(\d+)', headers.read_text(errors='replace'), re.MULTILINE) if headers.is_file() else []
        if not statuses or statuses[-1] != '200' or cached_bytes is None or online_bytes is None \
                or not advisory_bytes_match(cached_bytes, online_bytes):
            refuse_advisory_mismatch(name, cached_bytes, online_bytes, statuses[-1] if statuses else 'missing')
        json.loads(destination.read_text())
        receipt['pages'][name] = {'url': url, 'sha256': hashlib.sha256(destination.read_bytes()).hexdigest(), 'httpStatus': 200}
    return receipt


def output_snapshot(project: Path) -> dict:
    paths = [project.parent / 'obj/project.assets.json']
    paths.extend(path for path in (project.parent / 'bin/Release').rglob('*') if path.is_file())
    return {str(path.relative_to(project.parent)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def audit_project(project: Path, private: Path, evidence: Path, sdk_policy: dict, bounded,
                  proven_advisories: Path | None = None) -> dict:
    """Restore only a distinct package-only fixture under fresh package/HTTP caches."""
    assets_path = project.parent / 'obj/project.assets.json'
    original_bytes = assets_path.read_bytes()
    original_outputs = output_snapshot(project)
    expected = package_graph(assets_path)
    source = json.loads(original_bytes)
    frameworks = source['project']['frameworks']
    if set(frameworks) != {'net11.0'}:
        raise ValueError('The current native package audit requires the exact net11.0 graph.')
    private.mkdir()
    (private / 'global.json').write_text(json.dumps({'sdk': sdk_policy}) + '\n')
    xml = ET.Element('Project', {'Sdk': 'Microsoft.NET.Sdk'})
    properties = ET.SubElement(xml, 'PropertyGroup')
    for name, value in {'TargetFramework': 'net11.0', 'ManagePackageVersionsCentrally': 'false',
                        'ImportDirectoryBuildProps': 'false', 'ImportDirectoryBuildTargets': 'false',
                        'RestoreEnablePackagePruning': 'false', 'NuGetAudit': 'true', 'NuGetAuditLevel': 'low',
                        'NuGetAuditMode': 'all', 'TreatWarningsAsErrors': 'true',
                        'NoWarn': '', 'WarningsNotAsErrors': ''}.items():
        ET.SubElement(properties, name).text = value
    references = ET.SubElement(xml, 'ItemGroup')
    for identity in sorted(expected):
        name, version = identity.split('/')
        ET.SubElement(references, 'PackageReference', {'Include': name, 'Version': '[' + version + ']'})
    fixture = private / 'audit.csproj'
    ET.ElementTree(xml).write(fixture, encoding='utf-8', xml_declaration=True)
    config = private / 'NuGet.Config'
    write_restore_config(config)
    environment = dict(os.environ, NUGET_PACKAGES=str(private / 'packages'), NUGET_HTTP_CACHE_PATH=str(private / 'http'))
    for key in ('CustomAfterMicrosoftCommonTargets', 'CustomBeforeMicrosoftCommonTargets',
                'CustomAfterDirectoryBuildTargets', 'DirectoryBuildPropsPath',
                'DirectoryBuildTargetsPath', 'NuGetAuditSuppress', 'RestoreIgnoreFailedSources'):
        environment.pop(key, None)
    try:
        bounded(['dotnet', 'restore', str(fixture), '--configfile', str(config), '--force', '-warnaserror',
                 '-p:NuGetAudit=true', '-p:NuGetAuditMode=all', '-p:NuGetAuditLevel=low',
                 '-p:TreatWarningsAsErrors=true', '-p:WarningsNotAsErrors=', '-p:NoWarn='],
                300, evidence, cwd=private, environment=environment, require_complete_stdout=False)
        audited_path = private / 'obj/project.assets.json'
        policy = require_policy(audited_path)
        actual = package_graph(audited_path)
        require_coverage(expected, actual)
        online = online_advisories(private / 'http', private / 'advisories', bounded, proven=proven_advisories)
        return {'sourceAssetsSha256': hashlib.sha256(original_bytes).hexdigest(), 'sourceOutputs': original_outputs, 'packages': expected,
                'auditedPackages': actual, 'policy': policy, 'advisories': online,
                'privateDirectory': str(private), 'fixtureSha256': hashlib.sha256(fixture.read_bytes()).hexdigest(),
                'auditAssetsSha256': hashlib.sha256(audited_path.read_bytes()).hexdigest()}
    finally:
        if output_snapshot(project) != original_outputs or package_graph(assets_path) != expected:
            raise ValueError('The separate native audit changed module outputs, restore graph or package bytes.')


def require_audit(receipt: dict, project: Path) -> None:
    """Recheck sealed online coverage and both original and isolated fixture bytes before reuse."""
    private = Path(receipt['privateDirectory'])
    assets = private / 'obj/project.assets.json'
    if output_snapshot(project) != receipt['sourceOutputs'] \
            or hashlib.sha256((project.parent / 'obj/project.assets.json').read_bytes()).hexdigest() != receipt['sourceAssetsSha256'] \
            or package_graph(project.parent / 'obj/project.assets.json') != receipt['packages'] \
            or hashlib.sha256((private / 'audit.csproj').read_bytes()).hexdigest() != receipt['fixtureSha256'] \
            or hashlib.sha256(assets.read_bytes()).hexdigest() != receipt['auditAssetsSha256'] \
            or require_policy(assets) != receipt['policy'] or package_graph(assets) != receipt['auditedPackages']:
        raise ValueError('The separate native online audit or module input bytes changed after preparation.')
    require_coverage(receipt['packages'], receipt['auditedPackages'])
    for name, page in receipt['advisories']['pages'].items():
        if hashlib.sha256((private / 'advisories' / (name + '.json')).read_bytes()).hexdigest() != page['sha256']:
            raise ValueError('The separate native advisory proof changed after preparation.')
