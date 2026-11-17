"""Private, source-identical domain fixtures; no nested Builds initialization."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess

MODULES = ('Hexalith.Tenants', 'Hexalith.Parties')


def files(checkout: Path) -> dict:
    paths = subprocess.check_output(['git', 'ls-files', '-z'], cwd=checkout, timeout=10).decode().split('\0')
    regular = [checkout / path for path in paths if path and (checkout / path).is_file()]
    for project in ('Hexalith.Tenants', 'Hexalith.Parties', 'Hexalith.Parties.EventStoreExtensions'):
        directory = checkout / 'src' / project
        regular.extend(path for path in (directory / 'bin/Release').rglob('*') if path.is_file())
        assets = directory / 'obj/project.assets.json'
        if assets.is_file(): regular.append(assets)
    if any(path.is_symlink() for path in regular):
        raise ValueError('Private source fixture files must not be symbolic links.')
    return {str(path.relative_to(checkout)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(set(regular))}


def create(root: Path, destination: Path, selection: dict, evidence: Path, bounded) -> dict:
    if destination.resolve().is_relative_to(root.resolve()):
        raise ValueError('Source fixtures must be outside the module build checkout.')
    destination.mkdir()
    result = {'schemaVersion': 1, 'result': 'building', 'selection': {}, 'modules': {}}
    for module in MODULES:
        commit = selection['sources'][module]['commit']
        checkout = destination / module
        bounded(['git', 'clone', '--shared', '--no-checkout', '--no-recurse-submodules', str(root / 'references' / module), str(checkout)],
                120, evidence / (module + '-fixture-clone'))
        bounded(['git', 'checkout', '--no-recurse-submodules', '--detach', commit], 30,
                evidence / (module + '-fixture-checkout'), cwd=checkout)
        result['selection'][module] = commit
        result['modules'][module] = {'path': str(checkout.resolve()), 'commit': commit}
    return result


def seal(proof: dict) -> dict:
    for module, entry in proof['modules'].items():
        checkout = Path(entry['path'])
        if subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=checkout, timeout=10).decode().strip() != entry['commit'] \
                or subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=normal', '--ignore-submodules=all'],
                                           cwd=checkout, timeout=10).strip():
            raise ValueError('The private domain fixture changed its qualified source identity: ' + module)
        nested = checkout / 'references/Hexalith.Builds'
        if (nested / '.git').exists() or (nested / 'Props/Directory.Packages.props').exists():
            raise ValueError('Nested Builds must remain uninitialized in each private source fixture.')
        entry['files'] = files(checkout)
    proof['result'] = 'prepared'
    return proof


def require(proof: dict) -> None:
    expected = json.loads(json.dumps(proof))
    if seal(expected) != proof:
        raise ValueError('The separately built source fixture bytes changed after preparation.')
