"""Authenticate exact public runtime inputs before selecting disposable CI sources."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET
from zipfile import ZipFile

COHORT = '4.0.4'
MODULES = ('Hexalith.EventStore', 'Hexalith.Tenants', 'Hexalith.Parties', 'Hexalith.Platform')
REPOSITORIES = {name: f'https://github.com/Hexalith/{name}.git' for name in MODULES}


def manifest(path: Path) -> dict:
    """Require a complete, immutable public-artifact and qualified-owner selection."""
    value = json.loads(path.read_text())
    if value.get('eventStoreVersion') != COHORT or set(value.get('sources', {})) != set(MODULES):
        raise ValueError('The native runtime requires the complete exact public cohort and qualified source set.')
    for module, source in value['sources'].items():
        if source.get('repository') != REPOSITORIES[module] or not re.fullmatch('[0-9a-f]{40}', source.get('commit', '')):
            raise ValueError(f'Invalid qualified source identity: {module}.')
    packages = value.get('packages', [])
    identities = {(item.get('id'), item.get('version')) for item in packages}
    if len(identities) != len(packages) or not {('Hexalith.EventStore.Gateway', COHORT),
            ('Hexalith.EventStore.Aspire', COHORT), ('Hexalith.Tenants.Contracts', '7.0.0'),
            ('Hexalith.Tenants.Aspire', '7.0.0')} <= identities:
        raise ValueError('Public Gateway, Aspire and Tenants7 archive identities are required.')
    for item in packages:
        module = 'Hexalith.EventStore' if item['id'].startswith('Hexalith.EventStore.') else 'Hexalith.Tenants'
        if not re.fullmatch(r'Hexalith\.(EventStore|Tenants)\.[A-Za-z.]+', item['id']) \
                or item['version'] != (COHORT if module == 'Hexalith.EventStore' else '7.0.0') \
                or not re.fullmatch('[0-9a-f]{64}', item.get('sha256', '')) \
                or item.get('sourceCommit') != value['sources'][module]['commit']:
            raise ValueError('Every public archive must bind its exact package version, hash and repository source.')
    return value


def verify_archive(path: Path, package: dict) -> dict:
    """Bind archive bytes and embedded repository metadata, rejecting local candidates."""
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != package['sha256']:
        raise ValueError(f'Public package archive hash mismatch: {package["id"]}.')
    with ZipFile(path) as archive:
        names = [name for name in archive.namelist() if name.endswith('.nuspec')]
        if len(names) != 1:
            raise ValueError('A public package requires exactly one embedded nuspec.')
        metadata = ET.fromstring(archive.read(names[0])).find('{*}metadata')
        repository = metadata.find('{*}repository') if metadata is not None else None
        expected_repository = REPOSITORIES['Hexalith.EventStore' if package['id'].startswith('Hexalith.EventStore.') else 'Hexalith.Tenants']
        if metadata is None or metadata.findtext('{*}id') != package['id'] \
                or metadata.findtext('{*}version') != package['version'] or repository is None \
                or repository.get('url', '').removesuffix('.git') != expected_repository.removesuffix('.git') \
                or repository.get('commit') != package['sourceCommit']:
            raise ValueError('Public package identity or repository source differs from its authenticated selection.')
    return dict(package, sha256=digest)


def select_sources(root: Path, selection: dict, evidence: Path, bounded) -> list[dict]:
    """Validate every owned checkout first; only disposable hosted CI may change revisions."""
    declared = bounded(['git', 'config', '--file', str(root / '.gitmodules'), '--get-regexp', r'^submodule\..*\.path$'],
                       10, evidence / 'root-submodules')
    paths = {line.split(maxsplit=1)[1] for line in declared.splitlines()}
    sources = []
    for module in MODULES:
        relative = 'references/' + module
        checkout = root / relative
        project = checkout / 'src' / (module + '.CatalogBuilder' if module == 'Hexalith.Platform' else module)
        project_file = project / (project.name + '.csproj')
        if relative not in paths or checkout.is_symlink() or not (checkout / '.git').exists() or not project_file.is_file():
            raise ValueError(f'Missing declared direct root source prerequisite: {project_file}')
        actual = bounded(['git', 'rev-parse', '--show-toplevel'], 10, evidence / (module + '-root'), cwd=checkout)
        if Path(actual).resolve() != checkout.resolve():
            raise ValueError(f'{checkout} is not its own Git working tree.')
        remote = bounded(['git', 'remote', 'get-url', 'origin'], 10, evidence / (module + '-remote'), cwd=checkout)
        if remote.removesuffix('.git') != REPOSITORIES[module].removesuffix('.git'):
            raise ValueError(f'Wrong repository identity for qualified source: {module}.')
        status = bounded(['git', 'status', '--porcelain', '--untracked-files=normal', '--ignore-submodules=all'],
                         10, evidence / (module + '-status'), cwd=checkout)
        if status:
            raise ValueError(f'Qualified runtime source has dirty owned files: {module}.')
        commit = bounded(['git', 'rev-parse', 'HEAD'], 10, evidence / (module + '-commit'), cwd=checkout)
        sources.append(dict(module=module, path=relative, commit=commit, status=status, repository=remote,
                            selectedCommit=selection['sources'][module]['commit']))
    disposable = os.environ.get('GITHUB_ACTIONS') == 'true' and os.environ.get('RUNNER_ENVIRONMENT') == 'github-hosted'
    if any(source['commit'] != source['selectedCommit'] for source in sources) and not disposable:
        raise ValueError('Source revision selection is permitted only in disposable GitHub-hosted CI; local checkouts were left unchanged.')
    # Resolve every immutable source object before changing any working tree.
    for source in sources:
        checkout = root / source['path']
        if source['commit'] != source['selectedCommit']:
            bounded(['git', 'fetch', '--no-recurse-submodules', '--depth=1', 'origin', source['selectedCommit']],
                    120, evidence / (source['module'] + '-fetch'), cwd=checkout)
        resolved = bounded(['git', 'rev-parse', source['selectedCommit'] + '^{commit}'], 10,
                           evidence / (source['module'] + '-qualified-object'), cwd=checkout)
        if resolved != source['selectedCommit']:
            raise ValueError('A qualified immutable source commit is missing or mismatched; no working tree was selected.')
    for source in sources:
        checkout = root / source['path']
        if source['commit'] != source['selectedCommit']:
            bounded(['git', 'checkout', '--detach', source['selectedCommit']], 30,
                    evidence / (source['module'] + '-select'), cwd=checkout)
        actual = bounded(['git', 'rev-parse', 'HEAD'], 10, evidence / (source['module'] + '-selected'), cwd=checkout)
        status = bounded(['git', 'status', '--porcelain', '--untracked-files=normal', '--ignore-submodules=all'],
                         10, evidence / (source['module'] + '-selected-status'), cwd=checkout)
        if actual != source['selectedCommit'] or status:
            raise ValueError('Qualified source revision or clean owned source did not survive selection.')
        source['commit'] = actual
    return sources


def require_restored_archive(archive: Path, selection: dict, identity: str) -> None:
    """Require the restored archive to be one of the authenticated public bytes."""
    package = next((item for item in selection['packages'] if item['id'] + '/' + item['version'] == identity), None)
    if package is None:
        raise ValueError(f'Runtime package has no authenticated public archive selection: {identity}.')
    verify_archive(archive, package)


def verify_runtime_assets(project: Path, selection: dict, required: str) -> dict:
    """Seal actual public SDK/helper/Contracts bytes in the composition and client hosts."""
    assets = json.loads((project.parent / 'obj/project.assets.json').read_text())
    libraries = {name: item for name, item in assets['libraries'].items()
                 if name.startswith(('Hexalith.EventStore.', 'Hexalith.Tenants.'))}
    if required not in libraries or any(item.get('type') != 'package' for item in libraries.values()):
        raise ValueError('Composition/client runtime requires its actual published package identities.')
    target = assets['targets']['net10.0']
    output = project.parent / 'bin/Release/net10.0'
    packages = {}
    for identity in sorted(libraries):
        name, version = identity.split('/')
        filename = f'{name.lower()}.{version}.nupkg'
        folders = [Path(root) / identity.lower() for root in assets['packageFolders']
                   if (Path(root) / identity.lower() / filename).is_file()]
        if len(folders) != 1:
            raise ValueError(f'One actual restored public archive is required: {identity}.')
        folder = folders[0]
        archive = folder / filename
        require_restored_archive(archive, selection, identity)
        binaries = {}
        with ZipFile(archive) as content:
            metadata = next(name for name in content.namelist() if name.endswith('.nuspec'))
            if (folder / (name.lower() + '.nuspec')).read_bytes() != content.read(metadata):
                raise ValueError('Extracted runtime metadata differs from its authenticated public archive.')
            for asset in target[identity].get('runtime', {}):
                if asset.lower().endswith('.dll'):
                    expected = content.read(asset)
                    if (folder / asset).read_bytes() != expected or (output / Path(asset).name).read_bytes() != expected:
                        raise ValueError('Deployed composition/client runtime differs from its authenticated public archive.')
                    binaries[Path(asset).name] = hashlib.sha256(expected).hexdigest()
        packages[identity] = {'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'binaries': binaries}
    return {'packages': packages, 'output': {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(output.iterdir()) if path.is_file() and path.suffix in ('.dll', '.json')}}
