"""Run serial Exists() guard verification; retain each attempt, the final report once and repeats as hashes."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

PACKET = Path(__file__).resolve().parent
ROOT = Path.cwd()
PRIOR_REPORT = PACKET.parent / 'nested-pin-resolution-20261111/runs/final-2/census.json'
PRIOR_CHECKER_SHA256 = '3cfcc05db9c7f4e35f0a2eb8e3cb908466908d56e176d475178300cf297097a5'
UPSTREAM_CHECKER_SHA256 = '60a07e707a4036966340f5336eb13b44b9928168674100573d09224cb3ccda02'
runs = PACKET / 'runs'
runs.mkdir(exist_ok=True)
RUN = runs / ('final-' + str(len(list(runs.iterdir())) + 1))
RUN.mkdir()
environment = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
implementation = ['tools/proprietary-surfaces/v1/check.py', 'tools/proprietary-surfaces/v1/test_census.py',
                  'tools/proprietary-surfaces/v1/README.md', 'README.md',
                  str((PACKET / 'mutation-guards.py').relative_to(ROOT)), str((PACKET / 'before-check.py').relative_to(ROOT)),
                  str((PACKET / 'before-upstream-check.py').relative_to(ROOT))]
sha = lambda raw: hashlib.sha256(raw).hexdigest()
git = lambda *args: subprocess.run(['git', *args], check=True, capture_output=True).stdout
commands = []


def preserved_paths():
    """Every prior evidence, policy and inventory file this change must leave byte-identical."""
    paths = []
    for base in ('_bmad-output/implementation-artifacts/evidence/story-5-6', '_bmad-output/implementation-artifacts/evidence/story-5-1'):
        paths += [p for p in (ROOT / base).rglob('*') if p.is_file() and PACKET not in p.parents]
    policy = ROOT / 'tools/proprietary-surfaces/v1'
    paths += [policy / 'baseline.json', policy / 'amendments.json', policy / 'legacy-receipts.json', *sorted((policy / 'amendments').iterdir()),
              ROOT / '_bmad-output/implementation-artifacts/technical-tools-migration-inventory-v1.md']
    return {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in sorted(set(paths))}


def workspace_state():
    # Reference checkouts may be moved by other sessions; only committed gitlinks bind the scan.
    return {'head': git('rev-parse', 'HEAD').decode().strip(), 'gitmodulesSha256': sha(git('show', 'HEAD:.gitmodules')),
            'gitlinks': git('ls-tree', 'HEAD', 'references/').decode(),
            'referenceStatus': git('status', '--porcelain', '--', 'references').decode()}


def save(name, value):
    (RUN / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def run(name, arguments, expected, extra=None, retain=True):
    print('Running ' + name, flush=True)
    result = subprocess.run(arguments, capture_output=True, env={**environment, **(extra or {})}, timeout=1800)
    row = {'name': name, 'command': [str(value) for value in arguments], 'exitCode': result.returncode,
           'expectedExitCode': expected, 'environment': {'PYTHONDONTWRITEBYTECODE': '1', **(extra or {})},
           'stdoutSha256': sha(result.stdout), 'stderrSha256': sha(result.stderr)}
    if retain:
        (RUN / (name + '.stdout.txt')).write_bytes(result.stdout)
        (RUN / (name + '.stderr.txt')).write_bytes(result.stderr)
        row.update(stdout=name + '.stdout.txt', stderr=name + '.stderr.txt')
    commands.append(row)
    save('commands.json', commands)
    print(name + ': exit ' + str(result.returncode), flush=True)
    if result.returncode != expected:
        raise SystemExit('Unexpected result retained in ' + str(RUN.relative_to(ROOT)))
    return result


save('workspace-before.json', workspace_state())
save('prior-integrity-before.json', preserved_paths())
before = {path: sha((ROOT / path).read_bytes()) for path in implementation}
run('census-tests', [sys.executable, '-m', 'unittest', 'discover', '-v', '-s', 'tools/proprietary-surfaces/v1', '-p', 'test_*.py'], 0)
run('mutations', [sys.executable, PACKET / 'mutation-guards.py'], 0)
run('release-tests', [sys.executable, '-m', 'unittest', 'discover', '-s', 'scripts/tests', '-p', 'test_*.py'], 0)
revision = git('rev-parse', 'HEAD').decode().strip()
arguments = [sys.executable, 'tools/proprietary-surfaces/v1/check.py', '--revision', revision, '--output']
census = run('current-pin-census', arguments + [RUN / 'census.json'], 1, retain=False)
(RUN / 'current-pin-census.stderr.txt').write_bytes(census.stderr)
report = (RUN / 'census.json').read_bytes()
assert census.stdout == report, 'Census stdout must equal its retained report.'
repeats = {}
with tempfile.TemporaryDirectory() as temporary:
    for seed in ('1', '2'):
        output = Path(temporary) / f'determinism-{seed}.json'
        result = run('determinism-' + seed, arguments + [output], 1, {'PYTHONHASHSEED': seed}, retain=False)
        repeats[seed] = {'reportSha256': sha(output.read_bytes()), 'stdoutSha256': sha(result.stdout),
                         'stderrSha256': sha(result.stderr), 'identicalToFinal': output.read_bytes() == report
                         and result.stdout == report and result.stderr == census.stderr}
    pins = lambda value: {row['repository']: row['gitlink'] for row in value['repositories']}
    counts = lambda value: {'errors': len(value['errors']), 'observations': len(value['surfaces']),
                            'rejected': sum(row['status'] == 'rejected' for row in value['surfaces']), 'stale': len(value['stale']),
                            'completeRoots': sum(row.get('inspectionComplete', True) for row in value['repositories'])}

    def before_checker(name, file, expected_sha, output):
        original = (PACKET / file).read_bytes()
        assert sha(original) == expected_sha, file + ' changed.'
        adapted = original.replace(b"ROOT = Path(__file__).resolve().parents[3]", ('ROOT = Path(' + repr(str(ROOT)) + ')').encode(), 1)
        copy = Path(temporary) / file
        copy.write_bytes(adapted)
        result = run(name, [sys.executable, copy, '--revision', revision,
                            '--baseline', ROOT / 'tools/proprietary-surfaces/v1/baseline.json',
                            '--amendments', ROOT / 'tools/proprietary-surfaces/v1/amendments.json', '--output', output], 1, retain=False)
        assert result.stdout == output.read_bytes(), name + ' stdout must equal its report.'
        report_value = json.loads(output.read_text())
        assert report_value['parentRevision'] == json.loads(report)['parentRevision'] and pins(report_value) == pins(json.loads(report))
        return {'checker': file, 'checkerSha256': sha(original), 'executedCopySha256': sha(adapted),
                'reportSha256': sha(output.read_bytes()), 'stderrSha256': sha(result.stderr), 'counts': counts(report_value)}, result

    prior = json.loads(PRIOR_REPORT.read_text())
    nested, _ = before_checker('before-nested-pin-census', 'before-check.py', PRIOR_CHECKER_SHA256, Path(temporary) / 'nested.json')
    previous_value = json.loads((Path(temporary) / 'nested.json').read_text())
    nested['identicalToPriorExceptRevisionAndDate'] = {**previous_value, 'parentRevision': prior['parentRevision'],
                                                       'utcDate': prior['utcDate']} == prior
    # The same-revision baseline that differs only by the guard extension is retained once.
    upstream, result = before_checker('before-census', 'before-upstream-check.py', UPSTREAM_CHECKER_SHA256, RUN / 'before-census.json')
    (RUN / 'before-census.stderr.txt').write_bytes(result.stderr)
    save('before-run.json', {'report': 'before-census.json', 'baseline': upstream, 'nestedPinCheckerAtCurrentPins': nested,
                             'onlyAdaptation': 'ROOT names the workspace because each before-checker runs from a temporary copy.',
                             'parentRevision': json.loads(report)['parentRevision'],
                             'priorReport': str(PRIOR_REPORT.relative_to(ROOT)), 'priorReportSha256': sha(PRIOR_REPORT.read_bytes()),
                             'priorParentRevision': prior['parentRevision'], 'priorCounts': counts(prior),
                             'rootPinChanges': [{'repository': repository, 'prior': pins(prior).get(repository), 'current': gitlink}
                                                for repository, gitlink in pins(json.loads(report)).items() if pins(prior).get(repository) != gitlink]})
assert all(row['identicalToFinal'] for row in repeats.values()), 'Complete census bytes differ by hash seed.'
save('determinism.json', {'result': 'passed', 'seeds': [1, 2], 'finalReportSha256': sha(report), 'repeats': repeats})
run('diff-check', ['git', 'diff', '--check'], 0)
after = {path: sha((ROOT / path).read_bytes()) for path in implementation}
assert before == after, 'Implementation changed during verification; rerun after stabilizing it.'
save('implementation-integrity.json', {'result': 'passed', 'before': before, 'after': after})
assert workspace_state() == json.loads((RUN / 'workspace-before.json').read_text())
assert preserved_paths() == json.loads((RUN / 'prior-integrity-before.json').read_text())
(PACKET / 'latest-run.json').write_text(json.dumps({'path': str(RUN.relative_to(PACKET)), 'result': 'passed'}, indent=2) + '\n')
print('Final checks retained at ' + str(RUN.relative_to(ROOT)), flush=True)
