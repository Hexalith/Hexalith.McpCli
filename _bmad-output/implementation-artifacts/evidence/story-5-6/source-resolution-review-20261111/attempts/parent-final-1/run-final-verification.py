"""Capture the final serial checks without changing source policy or references."""
import json
import os
from pathlib import Path
import subprocess
import sys

PACKET = Path(__file__).resolve().parent
ROOT = Path.cwd()
environment = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
commands = []


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
(PACKET / 'determinism.json').write_text(json.dumps({'result': 'passed', 'seeds': [1, 2],
    'sameReportAsPrimary': True}, indent=2) + '\n')
run('binding-audit', [sys.executable, str(PACKET / 'build-verification.py')], 0)
run('diff-check', ['git', 'diff', '--check'], 0)
print('Final checks captured.', flush=True)
