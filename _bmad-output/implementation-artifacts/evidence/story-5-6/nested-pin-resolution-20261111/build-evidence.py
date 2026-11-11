"""Bind nested-pin verification, blocker accounting and cross-tree provenance; grant no authority."""
import collections
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess

ROOT = Path.cwd()
PACKET = Path(__file__).resolve().parent
RUN = PACKET / json.loads((PACKET / 'latest-run.json').read_text())['path']
PRIOR_PACKET = PACKET.parent / 'manifest-selector-resolution-20261111'
PRIOR_REPORT = PRIOR_PACKET / 'runs/final-1/census.json'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
git = lambda *args: subprocess.run(['git', *args], check=True, capture_output=True).stdout
CROSS_TREE_RULES = ('unsafe-import-path', 'unsafe-or-nested-compile-source', 'nested-pin-unresolvable',
                    'nested-object-unavailable', 'workspace-object-unavailable')


def write(name, value):
    (PACKET / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def counts(report):
    return {'roots': len(report['repositories']),
            'completeRoots': sum(row.get('inspectionComplete', True) for row in report['repositories']),
            'observations': len(report['surfaces']),
            'rejectedObservations': sum(row['status'] == 'rejected' for row in report['surfaces']),
            'inspectionErrors': len(report['errors']), 'stale': len(report['stale']),
            'crossTreeReads': sum(len(row.get('crossTreeReads', [])) for row in report['repositories'])}


after = json.loads((RUN / 'census.json').read_text())
prior = json.loads(PRIOR_REPORT.read_text())
before_run = json.loads((RUN / 'before-run.json').read_text())
roots = lambda report: {row['repository']: row['gitlink'] for row in report['repositories']}
assert before_run['identicalToPriorExceptParentRevision'] and before_run['priorReportSha256'] == sha(PRIOR_REPORT.read_bytes())
assert roots(prior) == roots(after) and prior['policy'] == after['policy']

# Prior evidence, policy and inventory: unchanged during the run and equal to their committed blobs.
recorded = json.loads((RUN / 'prior-integrity-before.json').read_text())
integrity = []
for path, value in recorded.items():
    # Git-ignored prior evidence has no committed blob; its retained bytes must still be unchanged.
    tracked = subprocess.run(['git', 'cat-file', '-e', 'HEAD:' + path], capture_output=True).returncode == 0
    committed = sha(git('show', 'HEAD:' + path)) if tracked else None
    current = sha((ROOT / path).read_bytes())
    integrity.append({'path': path, 'beforeSha256': value, 'afterSha256': current, 'committedSha256': committed,
                      'tracked': tracked, 'unchanged': value == current and (committed == value or not tracked)})
assert integrity and all(row['unchanged'] for row in integrity)
write('prior-policy-integrity.json', {'result': 'passed', 'files': len(integrity),
                                      'untrackedIgnored': sum(not row['tracked'] for row in integrity), 'bindings': integrity})
workspace_before = json.loads((RUN / 'workspace-before.json').read_text())
workspace_after = {'head': git('rev-parse', 'HEAD').decode().strip(), 'gitmodulesSha256': sha(git('show', 'HEAD:.gitmodules')),
                   'gitlinks': git('ls-tree', 'HEAD', 'references/').decode(),
                   'referenceStatus': git('status', '--porcelain', '--', 'references').decode()}
assert workspace_before == workspace_after and workspace_after['referenceStatus'] == ''
write('reference-integrity.json', {'result': 'passed', 'before': workspace_before, 'after': workspace_after,
                                   'nestedSubmodulesInitialized': False})

spec = importlib.util.spec_from_file_location('census', ROOT / 'tools/proprietary-surfaces/v1/check.py')
census = importlib.util.module_from_spec(spec)
spec.loader.exec_module(census)
trees = {repository: census.Tree(ROOT / repository, revision) for repository, revision in roots(after).items()}


def bind(repository, paths):
    tree = trees[repository]
    return [{'path': path, 'gitBlob': tree.entries[path][2], 'sha256': sha(tree.blob(path))}
            if path in tree.entries and tree.entries[path][0] in ('100644', '100755')
            else {'path': path, 'regularCommittedBlob': False} for path in sorted(set(paths))]


# Every substituted read is re-verified at its recorded commit in its source root's object store.
reads = []
for summary in after['repositories']:
    for record in summary['crossTreeReads']:
        tree = census.Tree(ROOT / record['repository'], record['commit'])
        if record['resolution'] == 'workspace':
            pinned = record['commit'] == roots(after)[record['repository']]
        else:
            pinned = trees[summary['repository']].entries[record['nestedGitlink']][2] == record['commit']
        reads.append({'inspectedRepository': summary['repository'], 'inspectedGitlink': summary['gitlink'], **record,
                      'verifiedSha256': sha(tree.blob(record['path'])) == record['sha256'], 'pinVerified': pinned})
assert reads and all(row['verifiedSha256'] and row['pinVerified'] for row in reads)
write('cross-tree-provenance.json', {'parentRevision': after['parentRevision'], 'reads': reads,
    'byResolution': dict(collections.Counter(row['resolution'] for row in reads)),
    'byInspectedRepository': dict(collections.Counter(row['inspectedRepository'] for row in reads))})


def blockers(report):
    result = collections.defaultdict(list)
    for row in report['errors']:
        key = ('inspection-error', row['repository'], row.get('path'), None, None, row['rule'])
        result[key].append(row)
    for row in report['surfaces']:
        if row['status'] == 'rejected':
            surface = row['surface']
            result[('rejected-observation', surface['repository'], surface['path'], surface['kind'], surface['identity'], None)].append(row)
    return result


previous, current = blockers(prior), blockers(after)
association = []
accounting = []
for key, rows in sorted(previous.items(), key=lambda item: json.dumps(item[0])):
    category, repository, path, kind, identity, rule = key
    remaining = [row for other, values in current.items() if other[1] == repository and other[2] == path for row in values]
    entry = {'category': category, 'repository': repository, 'path': path, 'observations': rows,
             'outcome': 'retained' if key in current else 'diagnostic-resolved-source-partial' if remaining else 'resolved-for-source',
             'current': current.get(key, []), 'remainingSourceBlockers': remaining, 'sourceBindings': bind(repository, [path])}
    if category == 'rejected-observation' and kind == 'source' and key not in current:
        owners = [{'surface': row['surface'], 'status': row['status'], 'classification': row.get('classification'),
                   'row': row.get('row'), 'signals': row['signals']}
                  for row in after['surfaces'] if row['surface']['repository'] == repository
                  and row['surface']['kind'] == 'project' and path in row['sources']]
        entry['associatedProjects'] = owners
        association.append({'repository': repository, 'path': path, 'signals': rows[0]['signals'], 'associatedProjects': owners})
    if category == 'rejected-observation' and kind == 'publication' and key not in current:
        referenced = [error for error in prior['errors'] if error['repository'] == repository and error.get('path')
                      and (error['path'] == identity or Path(error['path']).stem == identity)]
        entry['referencedProjectPriorErrors'] = referenced
        entry['referencedProjectCurrentErrors'] = [error for error in after['errors'] if error['repository'] == repository
                                                  and error.get('path') in {row.get('path') for row in referenced}]
    accounting.append(entry)
# A new key on a source whose earlier blocker resolved was masked by that earlier refusal.
added = [{'category': key[0], 'repository': key[1], 'path': key[2], 'observations': rows,
          'previouslyMaskedBy': [row for other, values in previous.items() if other[1] == key[1] and other[2] == key[2]
                                 and other not in current for row in values],
          'sourceBindings': bind(key[1], [key[2]])} for key, rows in sorted(current.items(), key=lambda item: json.dumps(item[0]))
         if key not in previous]
outcomes = collections.Counter(row['outcome'] for row in accounting)
assert len(accounting) == len(previous) and outcomes['retained'] + len(added) == len(current)
approved_only = [row for row in association if row['associatedProjects'] and all(p['status'] == 'approved' for p in row['associatedProjects'])]
association_summary = {
    'priorRejectedSourceObservations': sum(1 for key in previous if key[0] == 'rejected-observation' and key[3] == 'source'),
    'noLongerStandalone': len(association),
    'associatedWithApprovedProjectOnly': len(approved_only),
    'associatedWithRejectedProject': sum(any(p['status'] == 'rejected' for p in row['associatedProjects']) for row in association),
    'withoutAssociatedProjectCandidate': sum(not row['associatedProjects'] for row in association),
    'approvedProjects': dict(collections.Counter(p['surface']['path'] for row in approved_only for p in row['associatedProjects']))}
write('source-association.json', {'summary': association_summary, 'sources': association})
write('blocker-delta.json', {
    'beforeReport': str(PRIOR_REPORT.relative_to(ROOT)), 'beforeReportSha256': sha(PRIOR_REPORT.read_bytes()),
    'beforeParentRevision': prior['parentRevision'], 'afterReport': str((RUN / 'census.json').relative_to(PACKET)),
    'afterReportSha256': sha((RUN / 'census.json').read_bytes()), 'afterParentRevision': after['parentRevision'],
    'sameRootPins': roots(after), 'samePolicy': after['policy'],
    'sameRevisionBeforeRun': {key: before_run[key] for key in ('checkerSha256', 'reportSha256', 'identicalToPriorExceptParentRevision')},
    'beforeCounts': counts(prior), 'afterCounts': counts(after), 'outcomes': dict(outcomes),
    'errorRulesBefore': dict(collections.Counter(row['rule'].split(':')[0] for row in prior['errors'])),
    'errorRulesAfter': dict(collections.Counter(row['rule'].split(':')[0] for row in after['errors'])),
    'sourceAssociation': association_summary, 'beforeAccounting': accounting, 'newBlockers': added,
    'keying': 'Blockers match on category, repository, path, kind, identity and rule. Cross-tree refusals now also carry a target label, listed in each current row.'})

baseline = json.loads((ROOT / 'tools/proprietary-surfaces/v1/baseline.json').read_text())
owners = {row['repository']: row['owner'] for row in baseline['roots']}
decisions = []
for key, rows in sorted(current.items(), key=lambda item: json.dumps(item[0])):
    category, repository, path = key[:3]
    rule = (key[5] or '').split(':')[0]
    if category == 'rejected-observation':
        group, action = 'exact-owner-disposition', ('Owning maintainer classifies this exact identity and signal set at its pin with committed '
                                                     'proof or an exact versioned approval; the rejection stays until then.')
    elif rule in CROSS_TREE_RULES:
        group, action = 'cross-tree-boundary', ('The refused fallback lies outside the approved rules (no exact Exists() guard on that path, '
                                               'or a parent-tree path outside every root). The owner can guard the exact fallback path upstream, '
                                               'or a separately approved generic design may evaluate negated or property-definition Exists() guards.')
    elif rule.startswith(('nested-', 'dynamic-generated', 'unresolved-compile')):
        group, action = 'protected-source-boundary', ('Nested publication targets, generated task output and unresolved Compile inputs stay refused; '
                                                      'supply root-contained committed sources or seek an approved generic boundary design.')
    elif rule.startswith(('malformed-', 'duplicate-')):
        group, action = 'embedded-metadata-context', ('Owner identifies active composition versus test/evidence data for this exact blob; '
                                                      'an exclusion needs exact hash-bound versioned authority.')
    else:
        group, action = 'scanner-limit-or-unproven-input', ('Inspect this exact committed dependency and design only a finite generic proof with '
                                                            'refusal fixtures; runtime and PowerShell evaluation stay unsupported.')
    paths = {path, *[source for row in rows for source in row.get('sources', [])]}
    paths |= {candidate for candidate in trees[repository].entries if (key[5] or '').endswith(':' + candidate)}
    decisions.append({'category': category, 'repository': repository, 'path': path, 'observations': rows, 'group': group,
                      'owner': owners[repository], 'gitlink': roots(after)[repository],
                      'sourceBindings': bind(repository, [p for p in paths if p and not p.startswith('../')]),
                      'nextConcreteAction': action, 'newAuthority': None})
groups = {group: {'keys': sum(row['group'] == group for row in decisions),
                  'observations': sum(len(row['observations']) for row in decisions if row['group'] == group)}
          for group in sorted({row['group'] for row in decisions})}
write('acceptance-blockers.json', {'parentRevision': after['parentRevision'], 'utcDate': after['utcDate'], 'rootPins': roots(after),
    'reportSha256': sha((RUN / 'census.json').read_bytes()), 'policy': after['policy'], 'groups': groups,
    'provenActiveUpstreamDefects': [], 'decisions': decisions})

fixture_log = (RUN / 'census-tests.stderr.txt').read_text()
release_log = (RUN / 'release-tests.stderr.txt').read_text()
assert fixture_log.endswith('\nOK\n') and release_log.endswith('\nOK\n')
mutations = json.loads((RUN / 'mutations.stdout.txt').read_text())
assert mutations['result'] == 'passed'
matrix = [
    ('New unapproved project/tool/container/release', [
        'test_orphan_package_tool_container_and_workflow_publications_fail',
        'test_nested_pin_workspace_import_reads_sibling_root_at_its_pin',
        'test_nested_pin_import_reads_same_url_root_at_the_nested_commit',
        'test_nested_pin_compile_sources_and_globs_resolve_with_provenance']),
    ('Approved exemption or exact unexpired exception', [
        'test_each_approved_classification_is_retained_without_broadening',
        'test_exception_is_exact_including_kind_identity_path_and_root',
        'test_nested_pin_local_closure_and_context_free_api']),
    ('Invalid/malformed/expired exception, including allowed target', [
        'test_invalid_exception_fails_even_when_target_is_already_allowed', 'test_expiry_is_inclusive_and_production_uses_utc']),
    ('Removed surface reports stale without changing policy', ['test_stale_allowances_are_reported_and_never_rewritten']),
    ('Missing source/root, malformed metadata or unsafe path', [
        'test_missing_root_uninitialized_root_and_missing_committed_object_fail',
        'test_nested_pin_exists_guarded_absent_escapes_are_optional_only_when_required',
        'test_nested_pin_url_identity_requires_one_exact_absolute_declaration',
        'test_nested_pin_ambiguous_and_relative_root_identities_refuse',
        'test_nested_pin_missing_nested_commit_is_unavailable',
        'test_nested_pin_partial_clone_objects_are_never_fetched',
        'test_nested_pin_second_hop_escapes_and_substituted_gitlinks_refuse',
        'test_nested_pin_unavailable_workspace_root_object_refuses'])]
for row, methods in matrix:
    for method in methods:
        assert re.search(r'^' + re.escape(method) + r' .* \.\.\. ok$', fixture_log, re.M), method
write('matrix-coverage.json', {'result': 'passed', 'rows': [{'row': row, 'executed': True, 'passed': True, 'tests': methods}
                                                           for row, methods in matrix]})
determinism = json.loads((RUN / 'determinism.json').read_text())
write('verification.json', {'parentRevision': after['parentRevision'], 'utcDate': after['utcDate'],
    'counts': {**counts(after), 'censusTests': int(re.search(r'Ran (\d+) tests', fixture_log)[1]),
               'releaseRegressions': int(re.search(r'Ran (\d+) tests', release_log)[1]),
               'guardRemovalControls': mutations['mutationCount'], 'newGuardRemovalControls': mutations['newCount'],
               'adaptedPriorControls': mutations['adaptedCount']},
    'beforeCounts': counts(prior), 'sourceAssociation': association_summary, 'determinism': determinism,
    'acceptance': 'passed' if after['status'] == 'passed' else 'failed',
    'storyStatus': 'done' if after['status'] == 'passed' else 'in-progress', 'run': str(RUN.relative_to(PACKET)),
    'policy': after['policy'], 'rootPins': roots(after), 'reportSha256': sha((RUN / 'census.json').read_bytes()),
    'implementation': json.loads((RUN / 'implementation-integrity.json').read_text()),
    'remainingGroups': groups, 'newAuthority': None})
print(json.dumps({'counts': counts(after), 'before': counts(prior), 'outcomes': dict(outcomes), 'newBlockers': len(added),
                  'newUnmasked': sum(not row['previouslyMaskedBy'] for row in added),
                  'sourceAssociation': association_summary, 'groups': groups}, indent=2))
