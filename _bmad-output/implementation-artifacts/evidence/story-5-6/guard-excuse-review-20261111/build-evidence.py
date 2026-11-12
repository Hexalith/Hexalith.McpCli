"""Bind guard-excuse verification, blocker accounting and the proven excuse facts; grant no authority."""
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
PRIOR_PACKET = PACKET.parent / 'exists-guard-resolution-20261111'
PRIOR_REPORT = PRIOR_PACKET / 'runs/final-1/census.json'
BASELINE_REPORT = PRIOR_PACKET / 'runs/final-1/before-census.json'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
git = lambda *args: subprocess.run(['git', *args], check=True, capture_output=True).stdout
IMPORT_RULES = ('unsafe-import-path', 'unavailable-local-import')
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
before_run = json.loads((RUN / 'before-run.json').read_text())
# Same revision, root pins and policy: the superseded pruning checker, then the no-guard baseline.
pruning = json.loads((RUN / 'before-census.json').read_text())
baseline = json.loads(BASELINE_REPORT.read_text())
roots = lambda report: {row['repository']: row['gitlink'] for row in report['repositories']}
assert before_run['pruningChecker']['identicalToPriorExceptRevisionAndDate']
assert before_run['noGuardBaseline']['identicalToPriorExceptRevisionAndDate']
assert pruning['parentRevision'] == after['parentRevision'] and roots(pruning) == roots(after) == roots(baseline)
assert pruning['policy'] == after['policy'] == baseline['policy']

# Prior evidence, policy and inventory: unchanged during the run, and equal to committed bytes or to
# the hash its own packet recorded. The exists-guard packet is bound by its secret-scan receipt.
recorded = json.loads((RUN / 'prior-integrity-before.json').read_text())
receipt = json.loads((PRIOR_PACKET / 'secret-scan.json').read_text())
prior_prefix = str(PRIOR_PACKET.relative_to(ROOT)) + '/'
scanned = {prior_prefix + row['path']: row['sha256'] for row in receipt['files']}
prior_implementation = json.loads((PRIOR_PACKET / 'runs/final-1/implementation-integrity.json').read_text())['after']
prior_integrity = {row['path']: row['afterSha256'] for row in json.loads((PRIOR_PACKET / 'prior-policy-integrity.json').read_text())['bindings']}
integrity = []
for path, value in recorded.items():
    tracked = subprocess.run(['git', 'cat-file', '-e', 'HEAD:' + path], capture_output=True).returncode == 0
    committed = sha(git('show', 'HEAD:' + path)) if tracked else None
    current = sha((ROOT / path).read_bytes())
    ignored = subprocess.run(['git', 'check-ignore', '-q', path], capture_output=True).returncode == 0
    bound = ('committed' if committed == current else 'prior-secret-scan' if scanned.get(path) == current
             else 'prior-implementation-integrity' if prior_implementation.get(path) == current
             else 'prior-packet-integrity' if prior_integrity.get(path) == current else None)
    integrity.append({'path': path, 'beforeSha256': value, 'afterSha256': current, 'committedSha256': committed,
                      'tracked': tracked, 'ignored': ignored, 'boundBy': bound, 'unchanged': value == current})
assert integrity and all(row['unchanged'] for row in integrity)
unbound = [row['path'] for row in integrity if row['boundBy'] is None]
write('prior-policy-integrity.json', {'result': 'passed', 'files': len(integrity), 'byBinding': dict(collections.Counter(
    str(row['boundBy']) for row in integrity)), 'unboundButUnchanged': unbound, 'bindings': integrity,
    'note': 'Every file is byte-identical across the run. Tracked files equal HEAD except the exists-guard mutation runner, '
            'whose working bytes equal that packet\'s implementation-integrity record; untracked exists-guard files equal '
            'its secret-scan receipt; git-ignored files equal that packet\'s prior-integrity record. Its secret-scan receipt '
            'is outside its own scan and is bound only by being unchanged.'})
workspace_before = json.loads((RUN / 'workspace-before.json').read_text())
workspace_after = {'head': git('rev-parse', 'HEAD').decode().strip(), 'gitmodulesSha256': sha(git('show', 'HEAD:.gitmodules')),
                   'gitlinks': git('ls-tree', 'HEAD', 'references/').decode(),
                   'referenceStatus': git('status', '--porcelain', '--', 'references').decode()}
prior_workspace = json.loads((PRIOR_PACKET / 'reference-integrity.json').read_text())['after']
assert workspace_before == workspace_after
write('reference-integrity.json', {'result': 'passed', 'before': workspace_before, 'after': workspace_after,
    'priorPacket': prior_workspace, 'identicalToPriorPacket': {k: v for k, v in prior_workspace.items()} == workspace_after,
    'unchangedDuringRun': True, 'nestedSubmodulesInitialized': False,
    'note': 'This change made no reference, gitlink or .gitmodules edit. The census reads only committed objects at the parent gitlinks.'})

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
read_key = lambda report: {(row['repository'], json.dumps(record, sort_keys=True)) for row in report['repositories']
                           for record in row['crossTreeReads']}
write('cross-tree-provenance.json', {'parentRevision': after['parentRevision'], 'reads': reads,
    'byResolution': dict(collections.Counter(row['resolution'] for row in reads)),
    'byInspectedRepository': dict(collections.Counter(row['inspectedRepository'] for row in reads)),
    'versusPruning': {'onlyPruning': [json.loads(record) | {'inspectedRepository': repository} for repository, record in sorted(read_key(pruning) - read_key(after))],
                      'onlyExcuse': [json.loads(record) | {'inspectedRepository': repository} for repository, record in sorted(read_key(after) - read_key(pruning))]}})


def blockers(report):
    result = collections.defaultdict(list)
    for row in report['errors']:
        result[('inspection-error', row['repository'], row.get('path'), None, None, row['rule'])].append(row)
    for row in report['surfaces']:
        if row['status'] == 'rejected':
            surface = row['surface']
            result[('rejected-observation', surface['repository'], surface['path'], surface['kind'], surface['identity'], None)].append(row)
    return result


def account(previous_report, current_report):
    previous, current = blockers(previous_report), blockers(current_report)
    rows = []
    for key, observations in sorted(previous.items(), key=lambda item: json.dumps(item[0])):
        category, repository, path = key[:3]
        remaining = [row for other, values in current.items() if other[1] == repository and other[2] == path for row in values]
        rows.append({'category': category, 'repository': repository, 'path': path, 'observations': observations,
                     'outcome': 'retained' if key in current else 'diagnostic-resolved-source-partial' if remaining else 'resolved-for-source',
                     'current': current.get(key, []), 'remainingSourceBlockers': remaining})
    added = [{'category': key[0], 'repository': key[1], 'path': key[2], 'observations': observations,
              'sameSourcePreviousBlockers': [row for other, values in previous.items() if other[1] == key[1] and other[2] == key[2]
                                             for row in values],
              'sourceBindings': bind(key[1], [key[2]])}
             for key, observations in sorted(current.items(), key=lambda item: json.dumps(item[0])) if key not in previous]
    outcomes = collections.Counter(row['outcome'] for row in rows)
    assert len(rows) == len(previous) and outcomes['retained'] + len(added) == len(current)
    return rows, added, dict(outcomes)


versus_pruning, added_versus_pruning, outcomes_pruning = account(pruning, after)
versus_baseline, added_versus_baseline, outcomes_baseline = account(baseline, after)
# A blocker new against the pruning checker sits on a source whose no-guard refusal masked it.
for row in added_versus_pruning:
    row['maskedInNoGuardBaselineBy'] = [error for error in baseline['errors'] if error['repository'] == row['repository']
                                        and error.get('path') == row['path']]
    row['cause'] = ('The pruning checker dropped a property alternative whose Exists() guard it proved false; the excuse-only rule '
                    'keeps every alternative, and a Compile item is never excused.')
assert all(row['maskedInNoGuardBaselineBy'] for row in added_versus_pruning)
fallbacks = [row for row in versus_baseline if row['category'] == 'inspection-error'
             and any(o['rule'].split(':')[0] == 'unsafe-import-path' for o in row['observations'])
             and row['outcome'] != 'retained']
fallback_summary = {'resolved': len(fallbacks), 'byRepository': dict(collections.Counter(row['repository'] for row in fallbacks)),
                    'importRefusalsRemaining': sum(1 for row in after['errors'] if row['rule'].split(':')[0] in IMPORT_RULES)}

parent_tree = census.Tree(ROOT, after['parentRevision'])
workspace = census.Workspace(ROOT, parent_tree, census.declarations(parent_tree))
proofs = []
for repository, project in sorted({(row['repository'], row['path']) for row in fallbacks}):
    tree = trees[repository]
    resolver = census.Resolver(workspace, repository, tree)
    facts = []
    for kind in ('present', 'absent'):
        original = getattr(resolver, kind)
        setattr(resolver, kind, lambda *values, _kind=kind, _original=original: facts.append(
            (_kind, values[0], _original(*values))) or facts[-1][2])
    metadata_errors = []
    census.project_metadata(tree, project, {p for p, entry in tree.entries.items() if entry[0] != '160000'}, metadata_errors, resolver)
    proofs.append({'repository': repository, 'project': project, 'gitlink': roots(after)[repository],
                   'provenFacts': [dict(fact=kind, label=label) for kind, label in sorted({(k, l) for k, l, r in facts if r})],
                   'unprovenFacts': [dict(fact=kind, label=label) for kind, label in sorted({(k, l) for k, l, r in facts if not r})],
                   'metadataErrors': metadata_errors, 'noGuardBaselineErrors': [o for row in fallbacks if row['repository'] == repository
                                                                                and row['path'] == project for o in row['observations']]})
# The import refusals are excused; only Compile sources a retained alternative reaches may stay refused.
assert all(error['rule'].split(':')[0] not in IMPORT_RULES for proof in proofs for error in proof['metadataErrors'])
proof_summary = {'excusedProjects': len(proofs), 'byRepository': dict(collections.Counter(proof['repository'] for proof in proofs)),
                 'projectsWithRetainedCompileRefusals': sorted({(proof['repository'], proof['project']) for proof in proofs
                                                                if proof['metadataErrors']}),
                 'distinctProvenFacts': sorted({(fact['fact'], proof['repository'], fact['label']) for proof in proofs for fact in proof['provenFacts']})}
write('excuse-proofs.json', {'parentRevision': after['parentRevision'], 'summary': proof_summary, 'projects': proofs,
    'limit': 'Facts come only from committed tree entries: the inspected root, root-declared references at their pins, the parent tree '
             'outside every root and nested commits for absence. Nested paths are never proven present. No inspected code ran, '
             'and no property alternative was removed.'})
write('blocker-delta.json', {
    'beforeReport': str((RUN / 'before-census.json').relative_to(PACKET)), 'beforeReportSha256': sha((RUN / 'before-census.json').read_bytes()),
    'beforeChecker': before_run['pruningChecker'], 'noGuardBaseline': before_run['noGuardBaseline'],
    'afterReport': str((RUN / 'census.json').relative_to(PACKET)), 'afterReportSha256': sha((RUN / 'census.json').read_bytes()),
    'parentRevision': after['parentRevision'], 'sameRootPins': roots(after), 'samePolicy': after['policy'],
    'counts': {'noGuardBaseline': counts(baseline), 'pruning': counts(pruning), 'excuse': counts(after)},
    'errorRules': {name: dict(collections.Counter(row['rule'].split(':')[0] for row in value['errors']))
                   for name, value in (('noGuardBaseline', baseline), ('pruning', pruning), ('excuse', after))},
    'versusPruning': {'outcomes': outcomes_pruning, 'accounting': versus_pruning, 'newBlockers': added_versus_pruning},
    'versusNoGuardBaseline': {'outcomes': outcomes_baseline, 'accounting': versus_baseline, 'newBlockers': added_versus_baseline,
                              'crossTreeFallbacks': fallback_summary},
    'excuseProofs': proof_summary,
    'keying': 'Blockers match on category, repository, path, kind, identity and rule. Cross-tree refusals also carry a target label.'})

baseline_policy = json.loads((ROOT / 'tools/proprietary-surfaces/v1/baseline.json').read_text())
owners = {row['repository']: row['owner'] for row in baseline_policy['roots']}
decisions = []
for key, rows in sorted(blockers(after).items(), key=lambda item: json.dumps(item[0])):
    category, repository, path = key[:3]
    rule = (key[5] or '').split(':')[0]
    if category == 'rejected-observation':
        group, action = 'exact-owner-disposition', ('Owning maintainer classifies this exact identity and signal set at its pin with committed '
                                                     'proof or an exact versioned approval; the rejection stays until then.')
    elif rule == 'excluded-fixture-source-drift':
        group, action = 'exact-owner-disposition', ('The exact hash-bound exclusion no longer matches the committed bytes at this pin; '
                                                     'the owner approves the new bytes through a versioned amendment, or the pin keeps the approved bytes.')
    elif rule == 'unsafe-or-nested-compile-source' and any(row.get('target', '').startswith('../') for row in rows):
        group, action = 'guarded-compile-fallback', ('A retained, guarded property fallback reaches a Compile source outside every root. '
                                                    'The approved excuse covers imports only; the owner can make the source root-contained, '
                                                    'or a separately approved decision may extend the excuse to Compile items.')
    elif rule in CROSS_TREE_RULES:
        group, action = 'cross-tree-boundary', ('The refused path lies outside the approved cross-tree and excuse rules; the owner can make '
                                               'it root-contained or guard it with a provable Exists() condition upstream.')
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
        'test_guard_excuse_never_skips_present_imports_or_classification_alternatives',
        'test_nested_review_substituted_unresolved_import_is_refused_without_name_matching']),
    ('Approved exemption or exact unexpired exception', [
        'test_each_approved_classification_is_retained_without_broadening',
        'test_exception_is_exact_including_kind_identity_path_and_root',
        'test_nested_pin_local_closure_and_context_free_api',
        'test_nested_review_closure_allowance_binds_cross_tree_members_by_label']),
    ('Invalid/malformed/expired exception, including allowed target', [
        'test_invalid_exception_fails_even_when_target_is_already_allowed', 'test_expiry_is_inclusive_and_production_uses_utc']),
    ('Removed surface reports stale without changing policy', ['test_stale_allowances_are_reported_and_never_rewritten']),
    ('Missing source/root, malformed metadata or unsafe path', [
        'test_missing_root_uninitialized_root_and_missing_committed_object_fail',
        'test_nested_pin_exists_guarded_absent_escapes_are_optional_only_when_required',
        'test_guard_excuse_unproven_guards_keep_the_refusal',
        'test_guard_excuse_carried_property_guard_requires_every_producing_definition_refuted',
        'test_nested_review_missing_substituted_blobs_name_their_requested_labels',
        'test_nested_review_invalid_substituted_text_names_its_label_and_keeps_provenance',
        'test_nested_review_linked_root_checkout_and_tree_pin_refuse_cross_tree_reads',
        'test_nested_review_nested_declarations_need_valid_submodule_sections',
        'test_nested_review_amendment_fixture_validation_refuses_cross_tree_metadata'])]
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
               'controlOrigins': mutations['origins']},
    'pruningCounts': counts(pruning), 'noGuardBaselineCounts': counts(baseline), 'rootPinChanges': before_run['rootPinChanges'],
    'crossTreeFallbacks': fallback_summary, 'excuseProofs': {k: v for k, v in proof_summary.items() if k != 'distinctProvenFacts'},
    'determinism': determinism, 'acceptance': 'passed' if after['status'] == 'passed' else 'failed',
    'storyStatus': 'done' if after['status'] == 'passed' else 'in-progress', 'run': str(RUN.relative_to(PACKET)),
    'policy': after['policy'], 'rootPins': roots(after), 'reportSha256': sha((RUN / 'census.json').read_bytes()),
    'implementation': json.loads((RUN / 'implementation-integrity.json').read_text()),
    'remainingGroups': groups, 'newAuthority': None})
print(json.dumps({'counts': counts(after), 'pruning': counts(pruning), 'baseline': counts(baseline),
                  'versusPruning': outcomes_pruning, 'newVersusPruning': len(added_versus_pruning),
                  'versusBaseline': outcomes_baseline, 'newVersusBaseline': len(added_versus_baseline),
                  'fallbacks': fallback_summary, 'excuse': {k: v for k, v in proof_summary.items() if k != 'distinctProvenFacts'},
                  'groups': groups, 'unbound': unbound}, indent=2))
