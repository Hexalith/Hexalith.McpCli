"""Capture the final serial checks without changing source policy or references."""
import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys

PACKET = Path(__file__).resolve().parent
ROOT = Path.cwd()
environment = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
commands = []
implementation_paths = ['tools/proprietary-surfaces/v1/check.py',
    'tools/proprietary-surfaces/v1/test_census.py', 'tools/proprietary-surfaces/v1/README.md', 'README.md']
before = {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in implementation_paths}
(PACKET / 'implementation-before.json').write_text(json.dumps(before, indent=2, sort_keys=True) + '\n')


def run(name, arguments, expected, *, extra_environment=None):
    print('Running ' + name, flush=True)
    result = subprocess.run(arguments, capture_output=True,
                            env={**environment, **(extra_environment or {})}, timeout=600)
    stdout = name + ('.stdout.json' if name == 'mutations' else '.stdout.txt')
    stderr = name + '.stderr.txt'
    (PACKET / stdout).write_bytes(result.stdout)
    (PACKET / stderr).write_bytes(result.stderr)
    commands.append({'name': name, 'command': arguments, 'exitCode': result.returncode,
                     'environment': {'PYTHONDONTWRITEBYTECODE': '1', **(extra_environment or {})},
                     'stdout': stdout, 'stderr': stderr})
    (PACKET / 'commands-executed.json').write_text(json.dumps(commands, indent=2) + '\n')
    print(name + ': exit ' + str(result.returncode), flush=True)
    if result.returncode != expected:
        raise SystemExit('Unexpected exit for ' + name + '; inspect its retained streams.')
    return result


run('census-tests', [sys.executable, '-m', 'unittest', 'discover', '-v', '-s',
                    'tools/proprietary-surfaces/v1', '-p', 'test_*.py'], 0)
run('mutations', [sys.executable, str(PACKET / 'mutation-guards.py')], 0)
run('release-tests', [sys.executable, '-m', 'unittest', 'discover', '-s',
                     'scripts/tests', '-p', 'test_*.py'], 0)
arguments = [sys.executable, 'tools/proprietary-surfaces/v1/check.py', '--output']
primary = run('current-pin-census', arguments + [str(PACKET / 'census.json')], 1)
reports = []
for seed in ('1', '2'):
    result = run('determinism-' + seed, arguments + [str(PACKET / ('determinism-' + seed + '.json'))],
                 1, extra_environment={'PYTHONHASHSEED': seed})
    reports.append(json.loads(result.stdout))
assert reports[0] == reports[1] == json.loads(primary.stdout), 'Census output differs by hash seed.'
raw_reports = [(PACKET / name).read_bytes() for name in ('census.json', 'determinism-1.json', 'determinism-2.json')]
assert raw_reports[0] == raw_reports[1] == raw_reports[2], 'Complete census bytes differ by hash seed.'
(PACKET / 'determinism.json').write_text(json.dumps({'result': 'passed', 'seeds': [1, 2],
    'sameReportAsPrimary': True, 'identicalCompleteBytes': True,
    'sha256': hashlib.sha256(raw_reports[0]).hexdigest()}, indent=2) + '\n')
run('binding-audit', [sys.executable, str(PACKET / 'build-verification.py')], 0)
run('blocker-bindings', [sys.executable, str(PACKET / 'build-acceptance-blockers.py')], 0)
run('coverage-assessment', [sys.executable, str(PACKET / 'build-coverage-assessment.py')], 0)
run('diff-check', ['git', 'diff', '--check'], 0)
after = {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in implementation_paths}
assert before == after, 'Implementation changed during final serial verification.'
(PACKET / 'implementation-integrity.json').write_text(json.dumps({'result': 'passed',
    'before': before, 'after': after}, indent=2, sort_keys=True) + '\n')
print('Final checks captured.', flush=True)
