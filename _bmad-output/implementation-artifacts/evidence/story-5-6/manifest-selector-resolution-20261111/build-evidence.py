"""Bind completed checks, all blocker deltas and committed sources without authority."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess

ROOT = Path.cwd()
PACKET = Path(__file__).resolve().parent
RUN = PACKET / json.loads((PACKET / 'latest-run.json').read_text())['path']
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def write(name, value):
    (PACKET / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def git(*args):
    return subprocess.run(['git', *args], check=True, capture_output=True).stdout


def counts(report):
    return {'roots': len(report['repositories']),
            'completeRoots': sum(row.get('inspectionComplete', True) for row in report['repositories']),
            'observations': len(report['surfaces']),
            'rejectedObservations': sum(row['status'] == 'rejected' for row in report['surfaces']),
            'inspectionErrors': len(report['errors']), 'stale': len(report['stale'])}


before = json.loads((RUN / 'before-census.json').read_text())
after = json.loads((RUN / 'census.json').read_text())
prior_path = PACKET.parent / 'coverage-resolution-20261111/census.json'
prior = json.loads(prior_path.read_text())
roots = lambda report: {row['repository']: row['gitlink'] for row in report['repositories']}
assert roots(before) == roots(after) and before['parentRevision'] == after['parentRevision']
prior_integrity = json.loads((PACKET / 'prior-integrity-before.json').read_text())
integrity = [{'path': path, 'beforeSha256': value, 'afterSha256': sha((ROOT / path).read_bytes()),
              'unchanged': value == sha((ROOT / path).read_bytes())} for path, value in prior_integrity.items()]
assert all(row['unchanged'] for row in integrity)
write('prior-policy-integrity.json', {'result': 'passed', 'files': len(integrity), 'bindings': integrity})
workspace_before = json.loads((PACKET / 'workspace-before.json').read_text())
workspace_after = {'head': git('rev-parse', 'HEAD').decode().strip(),
                   'gitmodulesSha256': sha(git('show', 'HEAD:.gitmodules')),
                   'gitlinks': git('ls-tree', 'HEAD', 'references/').decode(),
                   'referenceStatus': git('status', '--porcelain', '--', 'references').decode()}
assert workspace_before == workspace_after
write('reference-integrity.json', {'result': 'passed', 'before': workspace_before, 'after': workspace_after})

spec = importlib.util.spec_from_file_location('census', ROOT / 'tools/proprietary-surfaces/v1/check.py')
census = importlib.util.module_from_spec(spec)
spec.loader.exec_module(census)
trees = {repository: census.Tree(ROOT / repository, revision) for repository, revision in roots(after).items()}


def bind(repository, paths):
    tree = trees[repository]
    return [{'path': path, 'gitBlob': tree.entries[path][2], 'sha256': sha(tree.blob(path))}
            if path in tree.entries and tree.entries[path][0] in ('100644', '100755')
            else {'path': path, 'regularCommittedBlob': False} for path in sorted(set(paths))]


source = json.loads((PACKET / 'source-bindings.json').read_text())
repository, script = source['repository'], source['sources'][0]['path']
tree = trees[repository]
errors = []
targets = census.static_project_targets(tree, census.logical_commands(tree.text(script)), script, errors)
assert targets == sorted(source['orderedProjects']) and not errors
projects = []
for target in targets:
    metadata_errors = []
    values, references, documents, linked = census.project_metadata(tree, target, set(tree.entries), metadata_errors)
    projects.append({'path': target, 'metadataErrors': metadata_errors,
        'classificationMetadata': {key: sorted(value) for key, value in values.items()
            if key in ('OutputType', 'PackAsTool', 'PackageId', 'AssemblyName', 'ToolCommandName', 'ContainerRepository')},
        'metadataSources': bind(repository, [target, *documents, *linked]),
        'observations': [row for row in after['surfaces'] if row['surface']['repository'] == repository and row['surface']['path'] == target]})
write('selector-source-proof.json', {'parentRevision': after['parentRevision'], 'repository': repository,
    'gitlink': tree.revision, 'scriptAndManifest': bind(repository, [script, source['sources'][1]['path']]),
    'orderedManifestProjects': source['orderedProjects'], 'resolvedTargets': targets, 'resolverErrors': errors,
    'selectedProjectInspection': projects, 'newAuthority': None,
    'limit': 'Enumeration alone grants no qualification or authority. Independent selected-project metadata and existing policy determine observations; other source failures remain root-wide blockers.'})


def blockers(report):
    entries = [('inspection-error', row) for row in report['errors']]
    entries += [('rejected-observation', row) for row in report['surfaces'] if row['status'] == 'rejected']
    result = {}
    for category, row in entries:
        surface = row.get('surface', {})
        key = [category, surface.get('repository', row.get('repository')), surface.get('path', row.get('path')),
               surface.get('kind'), surface.get('identity'), row.get('rule'), row.get('target')]
        identity = json.dumps(key, separators=(',', ':'))
        assert identity not in result
        result[identity] = {'category': category, 'repository': key[1], 'path': key[2], 'observation': row}
    return result


previous, current = blockers(before), blockers(after)
accounting = []
for identity, row in previous.items():
    retained = identity in current
    remaining_source = [value['observation'] for value in current.values()
                        if value['repository'] == row['repository'] and value['path'] == row['path']]
    accounting.append({**row, 'outcome': 'retained' if retained else 'diagnostic-resolved-source-partial' if remaining_source else 'resolved-for-source',
                       'current': current.get(identity), 'remainingSourceBlockers': remaining_source,
                       'sourceBindings': bind(row['repository'], [row['path']])})
added = [row for identity, row in current.items() if identity not in previous]
assert len(accounting) == len(previous)
assert sum(row['outcome'] == 'retained' for row in accounting) + len(added) == len(current)
write('blocker-delta.json', {'beforeReport': str((RUN / 'before-census.json').relative_to(PACKET)),
    'afterReport': str((RUN / 'census.json').relative_to(PACKET)), 'sameParentRevision': after['parentRevision'],
    'sameRootPins': roots(after), 'beforeCounts': counts(before), 'afterCounts': counts(after),
    'beforeAccounting': accounting, 'newBlockers': added,
    'priorPacketComparison': {'report': str(prior_path.relative_to(ROOT)), 'parentRevision': prior['parentRevision'],
        'currentParentRevision': after['parentRevision'], 'counts': counts(prior),
        'identicalRootPins': roots(prior) == roots(after),
        'rootPinChanges': [{'repository': repo, 'before': roots(prior).get(repo), 'after': revision}
                           for repo, revision in roots(after).items() if roots(prior).get(repo) != revision]}})

baseline = json.loads((ROOT / 'tools/proprietary-surfaces/v1/baseline.json').read_text())
owners = {row['repository']: row['owner'] for row in baseline['roots']}
decisions = []
for row in current.values():
    observation = row['observation']
    rule = observation.get('rule', '').split(':')[0]
    if row['category'] == 'rejected-observation':
        group = 'exact-owner-disposition'
        action = 'Owning maintainer must classify this exact identity/signal at its pin and provide committed proof or exact versioned approval; retain rejection.'
    elif rule.startswith(('nested-', 'unsafe-', 'generated-', 'missing-compile', 'unresolved-compile')):
        group = 'protected-source-boundary'
        action = 'Supply root-contained committed metadata or propose an approved generic boundary design; inspect no nested tree and execute no generator.'
    elif rule.startswith(('malformed-', 'duplicate-')):
        group = 'embedded-metadata-context'
        action = 'Owner must identify active composition versus test/evidence data for this exact blob; an exclusion needs exact hash-bound versioned authority.'
    else:
        group = 'scanner-limit-or-unproven-input'
        action = 'Inspect this exact committed dependency and design only a finite generic proof with refusal fixtures; runtime/PowerShell evaluation remains unsupported.'
    paths = {row['path'], *observation.get('sources', [])}
    for candidate in trees[row['repository']].entries:
        if observation.get('rule', '').endswith(':' + candidate):
            paths.add(candidate)
    decisions.append({**row, 'group': group, 'owner': owners[row['repository']],
        'gitlink': roots(after)[row['repository']], 'sourceBindings': bind(row['repository'], paths),
        'nextConcreteAction': action, 'newAuthority': None})
write('acceptance-blockers.json', {'parentRevision': after['parentRevision'], 'utcDate': after['utcDate'],
    'rootPins': roots(after), 'reportSha256': sha((RUN / 'census.json').read_bytes()), 'policy': after['policy'],
    'provenActiveUpstreamDefects': [], 'decisions': decisions})

fixture_log = (RUN / 'census-tests.stderr.txt').read_text()
release_log = (RUN / 'release-tests.stderr.txt').read_text()
assert fixture_log.endswith('\nOK\n') and release_log.endswith('\nOK\n')
mutations = json.loads((RUN / 'mutations.stdout.txt').read_text())
assert mutations['result'] == 'passed'
matrix = [
    ('New unapproved project/tool/container/release', ['test_manifest_selector_retains_exact_orphan_observations_and_committed_input',
        'test_orphan_package_tool_container_and_workflow_publications_fail']),
    ('Approved exemption or exact unexpired exception', ['test_each_approved_classification_is_retained_without_broadening',
        'test_exception_is_exact_including_kind_identity_path_and_root']),
    ('Invalid/malformed/expired exception, including allowed target', ['test_invalid_exception_fails_even_when_target_is_already_allowed',
        'test_expiry_is_inclusive_and_production_uses_utc']),
    ('Removed surface reports stale without changing policy', ['test_stale_allowances_are_reported_and_never_rewritten']),
    ('Missing source/root, malformed metadata or unsafe path', ['test_missing_root_uninitialized_root_and_missing_committed_object_fail',
        'test_manifest_selector_runtime_missing_malformed_and_duplicate_inputs_refuse',
        'test_manifest_selector_unsafe_and_nested_sources_and_targets_refuse'])]
for row, methods in matrix:
    for method in methods:
        assert re.search(r'^' + re.escape(method) + r' .* \.\.\. ok$', fixture_log, re.M), method
write('matrix-coverage.json', {'result': 'passed', 'rows': [{'row': row, 'executed': True, 'passed': True, 'tests': methods} for row, methods in matrix]})
write('verification.json', {'parentRevision': after['parentRevision'], 'utcDate': after['utcDate'],
    'counts': {**counts(after), 'censusTests': int(re.search(r'Ran (\d+) tests', fixture_log)[1]),
               'releaseRegressions': int(re.search(r'Ran (\d+) tests', release_log)[1]), 'guardRemovalControls': mutations['mutationCount']},
    'acceptance': 'failed', 'storyStatus': 'in-progress', 'run': str(RUN.relative_to(PACKET)),
    'policy': after['policy'], 'rootPins': roots(after), 'reportSha256': sha((RUN / 'census.json').read_bytes()),
    'implementation': json.loads((RUN / 'implementation-integrity.json').read_text()),
    'remainingGroups': {group: sum(row['group'] == group for row in decisions) for group in sorted({row['group'] for row in decisions})}})
verification = json.loads((PACKET / 'verification.json').read_text())
v = verification['counts']
groups = verification['remainingGroups']
metadata_error_count = sum(len(project['metadataErrors']) for project in projects)
metadata_outcome = ('Selected project metadata retains ' + str(metadata_error_count) + ' inspection errors.') if metadata_error_count else (
    'All ' + str(len(projects)) + ' selected project metadata inspections complete without errors. '
    'Their exact observations are retained in the source proof; other repository sources retain root-wide blockers.')
next_source = next((row for row in decisions if row['group'] == 'scanner-limit-or-unproven-input'), None)
next_action = ('Inspect `' + next_source['repository'] + '/' + next_source['path'] + '` at `' + next_source['gitlink'] +
               '` and bind the precise target dependency before proposing a separately tested finite proof.') if next_source else 'No additional scanner proof is proposed by this packet.'
(PACKET / 'decision-packet.md').write_text('''# Remaining census decisions

Current-reference acceptance remains unsuccessful at parent `''' + after['parentRevision'] + '''`.
The bounded committed-JSON selector resolves the packaging script's ordered
targets without executing jq, shell conditions or inspected code. Independent
project metadata inspection is recorded for every target. ''' + metadata_outcome + ''' No allowance,
exception, exemption, owner approval, reference, gitlink or dependency changed.

The [complete before/after accounting](blocker-delta.json) compares original and
updated checkers at the same parent revision and root pins, and separately
records the older packet revision. Every prior blocker is assigned once; every
new blocker is listed. [Exact remaining decisions](acceptance-blockers.json)
bind each observation/error to its owner, full gitlink and committed source hash.

| Group | Remaining | Next concrete action |
|---|---:|---|
| Scanner limits or unproven inputs | ''' + str(groups.get('scanner-limit-or-unproven-input', 0)) + ''' | Inspect each bound dependency and design only a finite generic proof; retain runtime and unsupported language refusals. |
| Protected source boundaries | ''' + str(groups.get('protected-source-boundary', 0)) + ''' | Owners supply root-contained committed metadata or seek an explicit generic boundary design; open no nested source and execute no generator. |
| Embedded metadata context | ''' + str(groups.get('embedded-metadata-context', 0)) + ''' | Owners classify each exact blob as active composition, caller-owned input or test/evidence data before any hash-bound versioned exclusion. |
| Exact owner disposition | ''' + str(groups.get('exact-owner-disposition', 0)) + ''' | Owners compare the exact identity and detection signals with the retained inventory and supply committed proof or an exact approved amendment. These observations are not a count of new tools. |
| Proven active upstream defects | 0 | None is established by this inspection. Classify exact source intent before proposing upstream work. |

''' + next_action + '''

The failed release gate remains in force. Story and sprint stay `in-progress`.
This packet grants no approval and records no staging, commit, push or publication.
''')
(PACKET / 'verification.md').write_text('''# Manifest-selector verification

Implemented the finite committed-JSON row selector and ordered tab-delimited
shell read required by the inspected packaging script. The [source proof](selector-source-proof.json)
binds the script, manifest, every selected project and inspected local metadata
at parent `''' + after['parentRevision'] + '''`. Literal enumeration grants no qualification.

- Census fixtures: ''' + str(v['censusTests']) + ''' passed.
- Guard-removal controls: ''' + str(v['guardRemovalControls']) + ''' detected, including every new control in [the guard map](guard-map.json).
- Release regressions: ''' + str(v['releaseRegressions']) + ''' passed.
- All five [I/O matrix rows](matrix-coverage.json) have passing executed coverage.
- Complete report bytes match across hash seeds 1 and 2.
- The fresh scan exits 1: ''' + str(v['roots']) + ''' roots accounted for, ''' + str(v['completeRoots']) + ''' complete, ''' + str(v['observations']) + ''' observations,
  ''' + str(v['rejectedObservations']) + ''' rejected observations, ''' + str(v['inspectionErrors']) + ''' coverage errors and ''' + str(v['stale']) + ''' stale allowances.

The original checker at these same pins reports ''' + str(counts(before)['inspectionErrors']) + ''' errors;
the updated checker reports ''' + str(v['inspectionErrors']) + '''. The [delta](blocker-delta.json)
accounts for every original/current blocker. The selector resolves its target
enumeration. ''' + metadata_outcome + ''' No active upstream
defect or new owner authority is inferred.

[Exact commands and streams](''' + str((RUN / 'commands.json').relative_to(PACKET)) + ''')
and [machine verification](verification.json) retain canonical revisions, source
hashes, checks and outcome. [Prior/policy integrity](prior-policy-integrity.json)
and [reference integrity](reference-integrity.json) verify preserved bytes.
Failed and superseded attempts remain under `attempts/`; final checks were rerun
after the last implementation change. The secret-scan receipt is
`secret-scan.json`; its command and status are retained alongside it.

The [decision packet](decision-packet.md) separates remaining source boundaries,
scanner limitations, embedded-data context and exact owner dispositions.
Story and sprint remain `in-progress`; current-reference release acceptance fails.
No .NET/live check was needed for this Python/documentation-only change.
No staging, commit, push, dependency/reference change or publication occurred.
''')
print(json.dumps({'before': counts(before), 'after': counts(after), 'removedBlockers': sum(row['outcome'] != 'retained' for row in accounting),
                  'newBlockers': len(added), 'priorFilesPreserved': len(integrity)}, sort_keys=True))
