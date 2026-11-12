"""Run serial guard-excuse verification; retain each attempt, the final report once and repeats as hashes."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

PACKET = Path(__file__).resolve().parent
ROOT = Path.cwd()
PRIOR_PACKET = PACKET.parent / 'exists-guard-resolution-20261111'
PRIOR_REPORT = PRIOR_PACKET / 'runs/final-1/census.json'
PRIOR_BASELINE_REPORT = PRIOR_PACKET / 'runs/final-1/before-census.json'
# The superseded pruning checker (exists-guard final) and the same-revision no-guard baseline it was measured against.
PRUNING = (PACKET / 'before-pruning-check.py', '3e10669799b5f520960071aec645acf1995d874c4f81e288d51b471e666fc2a3')
NO_GUARD = (PRIOR_PACKET / 'before-upstream-check.py', '60a07e707a4036966340f5336eb13b44b9928168674100573d09224cb3ccda02')
runs = PACKET / 'runs'
runs.mkdir(exist_ok=True)
RUN = runs / ('final-' + str(len(list(runs.iterdir())) + 1))
RUN.mkdir()
environment = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
implementation = ['tools/proprietary-surfaces/v1/check.py', 'tools/proprietary-surfaces/v1/test_census.py',
                  'tools/proprietary-surfaces/v1/README.md', 'README.md',
                  str((PACKET / 'mutation-guards.py').relative_to(ROOT)), str(PRUNING[0].relative_to(ROOT)),
                  str((PACKET / 'run-final-verification.py').relative_to(ROOT))]
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
    result = subprocess.run(arguments, capture_output=True, env={**environment, **(extra or {})}, timeout=3000)
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
pins = lambda value: {row['repository']: row['gitlink'] for row in value['repositories']}
counts = lambda value: {'errors': len(value['errors']), 'observations': len(value['surfaces']),
                        'rejected': sum(row['status'] == 'rejected' for row in value['surfaces']), 'stale': len(value['stale']),
                        'completeRoots': sum(row.get('inspectionComplete', True) for row in value['repositories'])}
with tempfile.TemporaryDirectory() as temporary:
    for seed in ('1', '2'):
        output = Path(temporary) / f'determinism-{seed}.json'
        result = run('determinism-' + seed, arguments + [output], 1, {'PYTHONHASHSEED': seed}, retain=False)
        repeats[seed] = {'reportSha256': sha(output.read_bytes()), 'stdoutSha256': sha(result.stdout),
                         'stderrSha256': sha(result.stderr), 'identicalToFinal': output.read_bytes() == report
                         and result.stdout == report and result.stderr == census.stderr}

    def before_checker(name, checker, prior_report, output):
        file, expected_sha = checker
        original = file.read_bytes()
        assert sha(original) == expected_sha, str(file) + ' changed.'
        adapted = original.replace(b"ROOT = Path(__file__).resolve().parents[3]", ('ROOT = Path(' + repr(str(ROOT)) + ')').encode(), 1)
        copy = Path(temporary) / (name + '.py')
        copy.write_bytes(adapted)
        result = run(name, [sys.executable, copy, '--revision', revision,
                            '--baseline', ROOT / 'tools/proprietary-surfaces/v1/baseline.json',
                            '--amendments', ROOT / 'tools/proprietary-surfaces/v1/amendments.json', '--output', output], 1, retain=False)
        assert result.stdout == output.read_bytes(), name + ' stdout must equal its report.'
        value = json.loads(output.read_text())
        assert value['parentRevision'] == json.loads(report)['parentRevision'] and pins(value) == pins(json.loads(report))
        prior = json.loads(prior_report.read_text())
        return {'checker': str(file.relative_to(ROOT)), 'checkerSha256': expected_sha, 'executedCopySha256': sha(adapted),
                'reportSha256': sha(output.read_bytes()), 'stderrSha256': sha(result.stderr), 'counts': counts(value),
                'priorReport': str(prior_report.relative_to(ROOT)), 'priorReportSha256': sha(prior_report.read_bytes()),
                'identicalToPriorExceptRevisionAndDate': {**value, 'parentRevision': prior['parentRevision'],
                                                          'utcDate': prior['utcDate']} == prior}, result

    # The superseded pruning checker is retained once as the before report; the no-guard baseline as hashes.
    pruning, result = before_checker('before-census', PRUNING, PRIOR_REPORT, RUN / 'before-census.json')
    (RUN / 'before-census.stderr.txt').write_bytes(result.stderr)
    baseline, _ = before_checker('no-guard-census', NO_GUARD, PRIOR_BASELINE_REPORT, Path(temporary) / 'no-guard.json')
    prior = json.loads(PRIOR_REPORT.read_text())
    save('before-run.json', {'report': 'before-census.json', 'pruningChecker': pruning, 'noGuardBaseline': baseline,
                             'onlyAdaptation': 'ROOT names the workspace because each before-checker runs from a temporary copy.',
                             'parentRevision': json.loads(report)['parentRevision'], 'priorParentRevision': prior['parentRevision'],
                             'rootPinChanges': [{'repository': repository, 'prior': pins(prior).get(repository), 'current': gitlink}
                                                for repository, gitlink in pins(json.loads(report)).items()
                                                if pins(prior).get(repository) != gitlink]})
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
