"""Retain verification bindings without changing any census policy or reference."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess

ROOT = Path.cwd()
PACKET = Path(__file__).resolve().parent
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def write(name, value):
    (PACKET / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def binding(path):
    file = ROOT / path
    return {'path': path, 'sha256': sha(file.read_bytes())}


report = json.loads((PACKET / 'census.json').read_text())
assert (PACKET / 'current-pin-census.stdout.txt').read_bytes() == (PACKET / 'census.json').read_bytes()
fixture_log = (PACKET / 'census-tests.stderr.txt').read_text()
release_log = (PACKET / 'release-tests.stderr.txt').read_text()
assert fixture_log.endswith('\nOK\n') and release_log.endswith('\nOK\n')
mutations = json.loads((PACKET / 'mutations.stdout.json').read_text())
assert mutations['result'] == 'passed'
assert not (PACKET / 'mutations.stderr.txt').read_bytes()
counts = {'fixtures': int(re.search(r'Ran (\d+) tests', fixture_log)[1]),
          'releaseRegressions': int(re.search(r'Ran (\d+) tests', release_log)[1]),
          'guardRemovalControls': mutations['mutationCount'],
          'roots': len(report['repositories']),
          'completeRoots': sum(root.get('inspectionComplete', True) for root in report['repositories']),
          'observations': len(report['surfaces']),
          'rejectedObservations': sum(e['status'] == 'rejected' for e in report['surfaces']),
          'inspectionErrors': len(report['errors']), 'stale': len(report['stale'])}

before = json.loads((PACKET / 'policy-before.json').read_text())
integrity = [{**row, 'afterSha256': sha((ROOT / row['path']).read_bytes()),
              'unchanged': row['sha256'] == sha((ROOT / row['path']).read_bytes())}
             for row in before]
assert all(row['unchanged'] and row['sha256'] == row['headSha256'] for row in integrity)
write('policy-integrity.json', {'result': 'passed', 'bindings': integrity})

matrix = [
    ('New unapproved project, tool, container or release entry', [
        'test_renamed_executable_outside_src_fails_with_actionable_committed_evidence',
        'test_literal_shell_variables_loops_functions_and_aliases_resolve_exact_targets']),
    ('Approved exemption or exact unexpired exception', [
        'test_each_approved_classification_is_retained_without_broadening',
        'test_exception_is_exact_including_kind_identity_path_and_root']),
    ('Invalid, malformed or expired exception including already allowed targets', [
        'test_invalid_exception_fails_even_when_target_is_already_allowed',
        'test_expiry_is_inclusive_and_production_uses_utc']),
    ('Removed baseline surface is stale without changing policy', [
        'test_stale_allowances_are_reported_and_never_rewritten']),
    ('Missing root/object, malformed metadata or unsafe path', [
        'test_missing_root_uninitialized_root_and_missing_committed_object_fail',
        'test_malformed_metadata_and_unsafe_xml_fail_instead_of_skipping',
        'test_working_directory_parent_paths_and_subshell_restore_are_contained',
        'test_missing_source_blob_keeps_other_committed_project_observations'])]
for row, tests in matrix:
    for test in tests:
        assert re.search(r'^' + re.escape(test) + r' .* \.\.\. ok$', fixture_log, re.M), test
write('matrix-coverage.json', {'result': 'passed', 'rows': [dict(row=row, tests=tests, executed=True, passed=True) for row, tests in matrix]})

spec = importlib.util.spec_from_file_location('census', ROOT / 'tools/proprietary-surfaces/v1/check.py')
census = importlib.util.module_from_spec(spec)
spec.loader.exec_module(census)
parent = census.Tree(ROOT, report['parentRevision'])
roots = census.declarations(parent)
previous = json.loads((PACKET.parent / 'handoff-verification-20261110/disposition-packet.json').read_text())
cases = []
for case in previous['decisions']:
    if case['category'] != 'inspection-error':
        continue
    repository, path = case['repository'], case['path']
    tree = census.Tree(ROOT / repository, roots[repository])
    raw = tree.blob(path)
    errors = [e for e in report['errors'] if e['repository'] == repository and e.get('path') == path]
    surfaces = [e for e in report['surfaces'] if e['surface']['repository'] == repository and e['surface']['path'] == path]
    resolved, resolver_errors = [], []
    if case['id'] != 'E02':
        text = census.logical_commands(tree.text(path))
        if path.startswith('.github/workflows/'):
            text = census.expand_workflow_projects(text, path)
        resolved = census.static_project_targets(tree, text, path, resolver_errors)
    cases.append({'id': case['id'], 'repository': repository, 'gitlink': roots[repository],
                  'source': {'path': path, 'gitBlob': tree.entries[path][2], 'sha256': sha(raw)},
                  'resolvedLocalTargets': resolved, 'resolverErrors': resolver_errors,
                  'reportedErrors': errors, 'reportedSurfaces': surfaces,
                  'priorDisposition': {'path': str((PACKET.parent / 'handoff-verification-20261110/disposition-packet.json').relative_to(ROOT)),
                                       'id': case['id']}, 'newAuthority': None})
write('inspection-cases.json', {'parentRevision': report['parentRevision'], 'cases': cases,
      'limits': ['No policy change or new owner authority.', 'No nested tree was opened or initialized.',
                 'No inspected command, condition, generator, project or Copy task was executed.']})

commands = [
    {'command': ['python3', '-m', 'unittest', 'discover', '-v', '-s', 'tools/proprietary-surfaces/v1', '-p', 'test_*.py'], 'exitCode': 0,
     'environment': {'PYTHONDONTWRITEBYTECODE': '1'}, 'stdout': 'census-tests.stdout.txt', 'stderr': 'census-tests.stderr.txt'},
    {'command': ['python3', '-m', 'unittest', 'discover', '-s', 'scripts/tests', '-p', 'test_*.py'], 'exitCode': 0,
     'environment': {'PYTHONDONTWRITEBYTECODE': '1'}, 'stdout': 'release-tests.stdout.txt', 'stderr': 'release-tests.stderr.txt',
     'note': 'Fresh parent verification after the review patches.'},
    {'command': ['python3', str((PACKET / 'mutation-guards.py').relative_to(ROOT))], 'exitCode': 0,
     'environment': {'PYTHONDONTWRITEBYTECODE': '1'}, 'stdout': 'mutations.stdout.json', 'stderr': 'mutations.stderr.txt'},
    {'command': ['python3', 'tools/proprietary-surfaces/v1/check.py', '--output', str((PACKET / 'census.json').relative_to(ROOT))], 'exitCode': 1,
     'stdout': 'current-pin-census.stdout.txt', 'stderr': 'current-pin-census.stderr.txt'}]
write('commands.json', commands)
write('verification.json', {'parentRevision': report['parentRevision'], 'utcDate': report['utcDate'],
      'counts': counts, 'rootPins': roots, 'policy': report['policy'], 'acceptance': 'failed',
      'sources': [binding(path) for path in ('tools/proprietary-surfaces/v1/check.py', 'tools/proprietary-surfaces/v1/test_census.py',
                  'tools/proprietary-surfaces/v1/README.md', 'README.md')],
      'report': {'path': 'census.json', 'sha256': sha((PACKET / 'census.json').read_bytes())}})
print(json.dumps(counts, sort_keys=True))
