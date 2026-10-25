#!/usr/bin/env python3
"""Strict, hash-bound companion plans; no domain-specific execution behavior."""
from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

import jsonschema

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/conformance-vectors/v1'))
from validate import VectorError, _load_json, validate_vectors
from check_enrolled import approved_inventory, approved_vectors, approval_directory, artifact_for, required_scope
from run_loopback import HeadProcess, _manifest_operations, _pointer, _preflight_vectors, _steps, _verify_artifact_in_host
from verify_artifact import restored_package

BINDING_KEYS = ('packageId', 'version', 'artifactHash', 'vectorSha256', 'planSha256', 'approvalSha256', 'inventorySha256')


def selection_binding(selection: dict) -> dict:
    return {key: selection[key] for key in BINDING_KEYS}


def declared_phases(selection: dict) -> list[dict]:
    steps = dict(_steps(_load_json(selection['vector'])))
    return [{'phase': action.get('step', action.get('label')),
             'operation': (steps[action['step']] if 'step' in action else action['query'])['operation'],
             'kind': (steps[action['step']] if 'step' in action else action['query'])['kind']}
            for action in selection['plan']['actions']]


def require_phases(selection: dict, phases: list[dict]) -> None:
    expected = declared_phases(selection)
    if len(phases) != len(expected):
        raise VectorError('Semantic receipt omits or duplicates declared phases.')
    for declared, phase in zip(expected, phases):
        if any(phase.get(key) != value for key, value in declared.items()) or phase.get('result') != 'passed' \
                or not phase.get('attempts') or phase['attempts'][-1].get('result') != 'passed' \
                or phase['attempts'][-1].get('exitCode') != 0 \
                or (declared['kind'] == 'command' and len(phase['attempts']) != 1):
            raise VectorError(f"{declared['phase']}: incomplete semantic phase or invalid Command attempt cardinality")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def timestamp(value: object) -> datetime:
    if not isinstance(value, str):
        raise VectorError('Expected an RFC3339 timestamp string.')
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if parsed.tzinfo is None:
            raise ValueError('timezone required')
        return parsed
    except ValueError as error:
        raise VectorError(f'Invalid timestamp {value!r}.') from error


def typed(value: object, kind: str) -> object:
    if not isinstance(value, str) or not value.strip():
        raise VectorError(f'Capture must be a nonempty {kind} string.')
    if kind == 'timestamp':
        timestamp(value)
    return value


def replace(document: dict, path: str, value: object) -> None:
    tokens = path[1:].split('/')
    parent = document
    for token in tokens[:-1]:
        token = token.replace('~1', '/').replace('~0', '~')
        if not isinstance(parent, dict) or token not in parent:
            raise VectorError(f'Binding target does not exist: {path}')
        parent = parent[token]
    key = tokens[-1].replace('~1', '/').replace('~0', '~')
    if not isinstance(parent, dict) or key not in parent:
        raise VectorError(f'Binding target does not exist: {path}')
    parent[key] = value


def resolve(call: dict, bindings: list[dict], values: dict) -> dict:
    result = copy.deepcopy(call)
    for binding in bindings:
        if binding['capture'] not in values:
            raise VectorError(f"Unresolved capture {binding['capture']!r} at {binding['path']}")
        value = values[binding['capture']]
        if 'offsetSeconds' in binding:
            value = (timestamp(value) + timedelta(seconds=binding['offsetSeconds'])).isoformat()
        replace(result, binding['path'], value)
    return result


def load_plan(path: Path, vector_path: Path) -> dict:
    plan = _load_json(path)
    schema = _load_json(Path(__file__).with_name('live-plan.schema.json'))
    errors = sorted(jsonschema.Draft202012Validator(schema).iter_errors(plan), key=lambda e: str(e.path))
    if errors:
        raise VectorError(f'{path}: /' + '/'.join(map(str, errors[0].path)) + ': ' + errors[0].message)
    vector = _load_json(vector_path)
    if plan['operation'] != vector['operation'] or plan['vectorSha256'] != digest(vector_path):
        raise VectorError(f'{path}: stale vector/Operation binding')
    steps = dict(_steps(vector))
    selected = [action['step'] for action in plan['actions'] if 'step' in action]
    if selected != list(steps):
        raise VectorError(f'{path}: each declared step must appear exactly once, in vector order')
    captures: dict[str, tuple[str, str, str]] = {}
    for index, action in enumerate(plan['actions']):
        location = f'{path}:/actions/{index}'
        call = steps[action['step']] if 'step' in action else action['query']
        for assertion in call['assertions']:
            if assertion['operator'] == 'arrayLength' and (type(assertion['value']) is not int or assertion['value'] < 0):
                raise VectorError(f'{location}: arrayLength requires a nonnegative integer token')
            if assertion['operator'] == 'exists' and type(assertion['value']) is not bool:
                raise VectorError(f'{location}: exists requires a boolean token')
        bound_paths = set()
        for binding in action.get('bindings', []):
            if binding['path'] in bound_paths:
                raise VectorError(f'{location}: duplicate binding target')
            bound_paths.add(binding['path'])
            capture = captures.get(binding['capture'])
            if capture is None:
                raise VectorError(f'{location}: unresolved capture {binding["capture"]}')
            if binding['path'] == '/envelope/cursor':
                if capture[0] != 'string' or capture[2] != '/paging/nextCursor':
                    raise VectorError(f'{location}: cursor must bind a captured returned cursor')
            elif binding['path'] in ('/payload/From', '/payload/To') and 'query' in action:
                if capture[0] != 'timestamp':
                    raise VectorError(f'{location}: time binding requires a timestamp capture')
            else:
                raise VectorError(f'{location}: unsupported or static binding target {binding["path"]}')
            if 'step' in action:
                present, original = _pointer(call, binding['path'])
                if not present or not isinstance(original, str) or not original.startswith('scripted-'):
                    raise VectorError(f'{location}: cannot weaken static vector inputs')
        for capture in action.get('captures', []):
            if capture['name'] in captures:
                raise VectorError(f'{location}: duplicate capture {capture["name"]}')
            captures[capture['name']] = (capture['type'], action.get('step', action.get('label')), capture['path'])
        replacements = set()
        for binding in action.get('assertionBindings', []):
            assertion_index = binding['index']
            if type(assertion_index) is not int or assertion_index < 0:
                raise VectorError(f'{location}: assertionBindings index requires a nonnegative integer token')
            if assertion_index >= len(call['assertions']) or assertion_index in replacements:
                raise VectorError(f'{location}: invalid or duplicate assertion selector')
            replacements.add(assertion_index)
            assertion = call['assertions'][assertion_index]
            capture = captures.get(binding['capture'])
            if assertion['operator'] != 'equals' or assertion['path'] != '/paging/nextCursor' \
                    or not isinstance(assertion['value'], str) or not assertion['value'].startswith('scripted-') \
                    or capture != ('string', action.get('step'), assertion['path']):
                raise VectorError(f'{location}: cannot weaken static vector assertions')
        for assertion_index, assertion in enumerate(call['assertions']):
            if isinstance(assertion['value'], str) and assertion['value'].startswith('scripted-') \
                    and assertion_index not in replacements:
                raise VectorError(f'{location}: scripted assertion must bind a real capture')
        if isinstance(call['envelope'].get('cursor'), str) and call['envelope']['cursor'].startswith('scripted-') \
                and '/envelope/cursor' not in bound_paths:
            raise VectorError(f'{location}: scripted cursor input has no live binding')
        if call['kind'] == 'command':
            following = plan['actions'][index + 1] if index + 1 < len(plan['actions']) else {}
            assertions = following.get('query', {}).get('assertions', [])
            if not any(assertion['path'].startswith('/document/') and
                       (assertion['operator'] != 'exists' or assertion['value'] is True) for assertion in assertions):
                raise VectorError(f'{location}: each Command needs an explicit persisted read barrier with document assertions')
    return plan


def validate_call(head: HeadProcess, call: dict) -> None:
    """Run resolved calls through the production Core without contacting a Gateway."""
    with tempfile.TemporaryDirectory(prefix='mcpcli-live-core-') as directory:
        path = Path(directory) / 'call.json'
        path.write_text(json.dumps({'prerequisites': [], 'invocation': call, 'postconditions': []}))
        process = subprocess.run(head._base() + ['--validate-vectors', str(path)], env=head.env,
                                 capture_output=True, text=True, timeout=head.timeout, check=False)
        try:
            result = json.loads(process.stdout)
        except ValueError as error:
            raise VectorError('Core live-call validation returned no valid document.') from error
        if process.returncode or result.get('findings') or len(result.get('requests', [])) != 1:
            raise VectorError(f"{call['operation']}: resolved Core compatibility failed: {result.get('findings')}")


def check_dependencies(assets: dict, policy: dict) -> None:
    """Require the reviewed exact production closure, including the Gateway client."""
    expected = {name.casefold(): version for name, version in (policy['baselinePackages'] | policy['modules']).items()}
    actual = {}
    for identity, library in assets['libraries'].items():
        if library['type'] != 'package':
            continue
        name, version = identity.rsplit('/', 1)
        if name.casefold() in actual:
            raise VectorError(f'Restored production dependency closure has duplicate package {name}.')
        actual[name.casefold()] = version
    if actual != expected:
        differences = {name: {'approved': expected.get(name), 'restored': actual.get(name)}
                       for name in sorted(actual.keys() | expected.keys()) if actual.get(name) != expected.get(name)}
        raise VectorError('Restored production dependency closure differs from tools/dependency-policy.json: ' + json.dumps(differences))


def shared_runtime_assemblies(host: Path) -> set[str]:
    """Only declared installed shared frameworks may supply absent private assemblies."""
    options = _load_json(host.with_suffix('.runtimeconfig.json'))['runtimeOptions']
    frameworks = options.get('frameworks', []) + ([options['framework']] if 'framework' in options else [])
    installed = subprocess.run(['dotnet', '--list-runtimes'], capture_output=True, text=True, timeout=30, check=True)
    names = set()
    for line in installed.stdout.splitlines():
        name, version, location = line.split(maxsplit=2)
        if any(name == framework['name'] and version.split('.')[:2] == framework['version'].split('.')[:2]
               for framework in frameworks):
            names.update(path.name for path in (Path(location.strip('[]')) / version).glob('*.dll'))
    return names


def check_adapter_dependencies(host: Path, assets: dict) -> None:
    """Bind executable metadata and every private package DLL to the approved restore."""
    deps = _load_json(host.with_suffix('.deps.json'))
    actual = {identity: value for identity, value in deps['libraries'].items() if value['type'] == 'package'}
    expected = {identity: value for identity, value in assets['libraries'].items() if value['type'] == 'package'}
    if set(actual) - set(expected):
        raise VectorError(f'{host}: executable dependency identities differ from the approved production closure')
    target_name = deps['runtimeTarget']['name']
    target = deps['targets'][target_name]
    versions = {identity.rsplit('/', 1)[0].casefold(): identity.rsplit('/', 1)[1] for identity in expected}
    for entry in target.values():
        for name, version in entry.get('dependencies', {}).items():
            if name.casefold() in versions and version != versions[name.casefold()]:
                raise VectorError(f'{host}: executable dependency reference differs from production restore: {name}@{version}')
    restored_target = assets['targets'].get(target_name, assets['targets'].get(target_name.split('/')[0]))
    if restored_target is None:
        # Modern NuGet assets use the short TFM; executable deps retain the framework moniker.
        moniker = re.fullmatch(r'\.NETCoreApp,Version=v([0-9]+\.[0-9]+)(/[^/]+)?', target_name)
        if moniker:
            tfm = 'net' + moniker[1]
            restored_target = assets['targets'].get(tfm + (moniker[2] or ''), assets['targets'].get(tfm))
    if restored_target is None:
        raise VectorError(f'{host}: executable runtime target differs from production restore')
    shared = shared_runtime_assemblies(host)
    for identity, library in expected.items():
        runtime = {asset for asset in restored_target.get(identity, {}).get('runtime', {}) if asset.endswith('.dll')}
        if identity not in actual:
            if any((host.parent / Path(asset).name).exists() or Path(asset).name not in shared for asset in runtime):
                raise VectorError(f'{host}: executable dependency identity is missing: {identity}')
            continue
        if actual[identity].get('sha512') != 'sha512-' + library['sha512'].removeprefix('sha512-'):
            raise VectorError(f'{host}: executable dependency content hash differs: {identity}')
        selected = {asset for asset in target.get(identity, {}).get('runtime', {}) if asset.endswith('.dll')}
        if selected - runtime or any(asset not in selected and
                                    ((host.parent / Path(asset).name).exists() or Path(asset).name not in shared)
                                    for asset in runtime):
            raise VectorError(f'{host}: executable dependency runtime assets differ: {identity}')
        artifact, _ = restored_package(assets, identity, library)
        with zipfile.ZipFile(artifact) as archive:
            # RID-specific runtime assets may legitimately be absent on another OS.
            rid_assets = target.get(identity, {}).get('runtimeTargets', {})
            restored_rid = restored_target.get(identity, {}).get('runtimeTargets', {})
            for asset, metadata in rid_assets.items():
                if metadata.get('assetType') == 'runtime' and asset.endswith('.dll'):
                    if asset not in restored_rid:
                        raise VectorError(f'{host}: executable RID runtime asset differs: {identity}')
                    output = host.parent / asset
                    if output.is_file() and output.read_bytes() != archive.read(asset):
                        raise VectorError(f'{output}: private runtime DLL bytes differ from restored package {identity}')
            for asset in selected:
                output = host.parent / Path(asset).name
                if not output.exists() and output.name in shared:
                    continue
                if not output.is_file() or asset not in archive.namelist() or output.read_bytes() != archive.read(asset):
                    raise VectorError(f'{output}: private runtime DLL bytes differ from restored package {identity}')


def freeze_input(source: Path, target: Path, expected_hash: str | None = None) -> Path:
    """Capture execution bytes once; validate the captured bytes against approval."""
    target.parent.mkdir(parents=True, exist_ok=True)
    content = source.read_bytes()
    if expected_hash is not None and hashlib.sha256(content).hexdigest() != expected_hash:
        raise VectorError(f'{source}: input changed after approval preflight')
    target.write_bytes(content)
    return target


def execution_selection(selections: list[dict], operation: str | None) -> list[dict]:
    """Full-lane preflight validates every call; a child validates its selected calls."""
    if operation is None:
        return selections
    selected = [item for item in selections if item['operation'] == operation]
    if len(selected) != 1:
        raise VectorError('Exactly one approved Operation must be selected.')
    return selected


def preflight(host: Path, output: Path, repo: Path = ROOT, *, operation: str | None = None) -> list[dict]:
    """Recheck the entire enrollment, immutable approvals, inventories, Catalog and plans."""
    output.mkdir(parents=True, exist_ok=True)
    project = repo / 'src/Hexalith.McpCli/Hexalith.McpCli.csproj'
    evaluated = subprocess.run(['dotnet', 'msbuild', str(project), '-p:Configuration=Release', '-getItem:PackageReference'],
                               capture_output=True, text=True, timeout=60, check=True)
    packages = [p['Identity'] for p in json.loads(evaluated.stdout)['Items']['PackageReference']
                if any(k.casefold() == 'hexalithcontracts' and v.casefold() == 'true' for k, v in p.items())]
    if not packages or len(set(packages)) != len(packages):
        raise VectorError('Production enrollment is empty or duplicated.')
    assets = _load_json(project.parent / 'obj/project.assets.json')
    check_dependencies(assets, _load_json(repo / 'tools/dependency-policy.json'))
    check_adapter_dependencies(host, assets)
    selections, catalog, modules = [], {}, set()
    with tempfile.TemporaryDirectory(prefix='mcpcli-live-preflight-') as home:
        head = HeadProcess(host, home, 30)
        manifest = subprocess.run(head._base() + ['--manifest-catalog'], env=head.env,
                                  capture_output=True, text=True, timeout=30, check=True)
        if {entry['packageId'] for entry in json.loads(manifest.stdout)} != set(packages):
            raise VectorError('Adapter manifest differs from production enrollment.')
        for package in packages:
            directory = approval_directory(repo / 'tools/conformance-vectors/v1/modules', package)
            receipt_path = freeze_input(directory / 'approval.json', output / 'inputs' / package / 'approval.json')
            receipt = _load_json(receipt_path)
            artifact = artifact_for(assets, package, receipt)
            vectors = approved_vectors(directory, receipt)
            vectors = [freeze_input(source, output / 'inputs' / package / source.relative_to(directory),
                                    receipt['vectorFilesSha256'][source.relative_to(directory).as_posix()])
                       for source in vectors]
            inventory_source = repo / 'tools/inventory-coverage/v1' / (receipt['module'] + '-approved.json')
            inventory = freeze_input(inventory_source, output / 'inputs' / package / 'inventory.json', receipt['inventorySha256'])
            approved_inventory(inventory, receipt)
            _verify_artifact_in_host(host, artifact, (package, receipt['version']))
            operations = _manifest_operations(head, package)
            findings = validate_vectors(vectors, artifact, (package, receipt['version']), list(operations))
            if findings:
                raise VectorError('\n'.join(findings))
            inventory_check = subprocess.run(head._base() + ['--inventory', str(inventory)], env=head.env,
                                             capture_output=True, text=True, timeout=30, check=True)
            if json.loads(inventory_check.stdout):
                raise VectorError(f'{package}: inventory coverage failed')
            for catalog_operation, kind in operations.items():
                if catalog_operation in catalog or catalog_operation.split('.')[0] != receipt['module']:
                    raise VectorError('Duplicate or mismatched owning Catalog Operation.')
                catalog[catalog_operation] = 'write' if kind == 'command' else 'read'
            modules.add(receipt['module'])
            for source in vectors:
                vector = _load_json(source)
                plan_path = freeze_input(repo / 'tools/live-topology/plans' / (vector['operation'] + '.json'),
                                         output / 'inputs' / package / 'plans' / (vector['operation'] + '.json'))
                plan = load_plan(plan_path, source)
                selections.append({'operation': vector['operation'], 'vector': source, 'planPath': plan_path,
                                   'plan': plan, 'packageId': package, 'version': receipt['version'],
                                   'artifactHash': receipt['artifactHash'], 'inventorySha256': digest(inventory),
                                   'approvalSha256': digest(receipt_path),
                                   'vectorSha256': digest(source), 'planSha256': digest(plan_path)})
        if required_scope(repo / 'tools/conformance-vectors/v1/v1-scope.json', modules):
            raise VectorError('Full v1 scope is missing required modules.')
        exit_code, discovered = head.cli(['modules', '--strict'])
        if exit_code or {m['name'] for m in discovered['modules']} != modules:
            raise VectorError('Complete production Catalog differs from approved modules.')
        found = {}
        for module in modules:
            exit_code, document = head.cli(['operations', module, '--strict'])
            if exit_code:
                raise VectorError('Complete production Catalog discovery failed.')
            found.update({op['name']: op['kind'] for op in document['operations']})
        if found != catalog or {item['operation'] for item in selections} != set(catalog):
            raise VectorError('Live vectors do not cover the complete production Catalog.')
        if {p.name for p in (repo / 'tools/live-topology/plans').glob('*.json')} != {i['operation'] + '.json' for i in selections}:
            raise VectorError('Live plan inventory differs from complete vector coverage.')
        selected = execution_selection(selections, operation)
        _preflight_vectors(head, [item['vector'] for item in selected], catalog, output / 'core-preflight.json')
        for item in selected:
            values = {}
            steps = dict(_steps(_load_json(item['vector'])))
            for action in item['plan']['actions']:
                call = steps[action['step']] if 'step' in action else action['query']
                resolved = resolve(call, action.get('bindings', []), values)
                if catalog.get(resolved['operation']) != ('write' if resolved['kind'] == 'command' else 'read'):
                    raise VectorError('Plan call is absent from the production Catalog.')
                validate_call(head, resolved)
                for capture in action.get('captures', []):
                    values[capture['name']] = '2026-01-01T00:00:00+00:00' if capture['type'] == 'timestamp' else 'live-preflight-cursor'
    bindings = [{k: v for k, v in item.items() if k not in ('vector', 'plan', 'planPath')} for item in selections]
    (output / 'bindings.json').write_text(json.dumps(bindings, indent=2) + '\n')
    return selected
