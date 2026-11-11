"""Execute serial verification and preserve each attempt without overwriting it."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

PACKET = Path(__file__).resolve().parent
ROOT = Path.cwd()
runs = PACKET / 'runs'
runs.mkdir(exist_ok=True)
RUN = runs / ('final-' + str(len(list(runs.iterdir())) + 1))
RUN.mkdir()
environment = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
paths = ['tools/proprietary-surfaces/v1/check.py', 'tools/proprietary-surfaces/v1/test_census.py',
         'tools/proprietary-surfaces/v1/README.md', 'README.md']
sha = lambda raw: hashlib.sha256(raw).hexdigest()
before = {path: sha((ROOT / path).read_bytes()) for path in paths}
commands = []


def run(name, arguments, expected, extra=None):
    print('Running ' + name, flush=True)
    result = subprocess.run(arguments, capture_output=True, env={**environment, **(extra or {})}, timeout=900)
    stdout, stderr = name + '.stdout.txt', name + '.stderr.txt'
    (RUN / stdout).write_bytes(result.stdout)
    (RUN / stderr).write_bytes(result.stderr)
    commands.append({'name': name, 'command': arguments, 'exitCode': result.returncode,
                     'expectedExitCode': expected, 'stdout': stdout, 'stderr': stderr,
                     'environment': {'PYTHONDONTWRITEBYTECODE': '1', **(extra or {})}})
    (RUN / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
    print(name + ': exit ' + str(result.returncode), flush=True)
    if result.returncode != expected:
        raise SystemExit('Unexpected result retained in ' + str(RUN.relative_to(ROOT)))
    return result


run('census-tests', [sys.executable, '-m', 'unittest', 'discover', '-v', '-s',
                    'tools/proprietary-surfaces/v1', '-p', 'test_*.py'], 0)
run('mutations', [sys.executable, str(PACKET / 'mutation-guards.py')], 0)
run('release-tests', [sys.executable, '-m', 'unittest', 'discover', '-s', 'scripts/tests', '-p', 'test_*.py'], 0)
revision = subprocess.run(['git', 'rev-parse', 'HEAD'], check=True, capture_output=True, text=True).stdout.strip()
run('before-census', [sys.executable, str(PACKET / 'before-check.py'), '--revision', revision,
                      '--baseline', str(ROOT / 'tools/proprietary-surfaces/v1/baseline.json'),
                      '--amendments', str(ROOT / 'tools/proprietary-surfaces/v1/amendments.json'),
                      '--output', str(RUN / 'before-census.json')], 1)
arguments = [sys.executable, 'tools/proprietary-surfaces/v1/check.py', '--revision', revision, '--output']
run('current-pin-census', arguments + [str(RUN / 'census.json')], 1)
for seed in ('1', '2'):
    run('determinism-' + seed, arguments + [str(RUN / ('determinism-' + seed + '.json'))], 1,
        {'PYTHONHASHSEED': seed})
reports = [(RUN / name).read_bytes() for name in ('census.json', 'determinism-1.json', 'determinism-2.json')]
assert reports[0] == reports[1] == reports[2], 'Complete census bytes differ by hash seed.'
assert all('repositories' in json.loads(raw) and json.loads(raw)['parentRevision'] == revision for raw in reports)
assert 'repositories' in json.loads((RUN / 'before-census.json').read_text()), 'Original-checker scan must cover committed roots.'
assert reports[0] == (RUN / 'current-pin-census.stdout.txt').read_bytes()
(RUN / 'determinism.json').write_text(json.dumps({'result': 'passed', 'seeds': [1, 2],
    'identicalCompleteBytes': True, 'sha256': sha(reports[0])}, indent=2) + '\n')
run('diff-check', ['git', 'diff', '--check'], 0)
after = {path: sha((ROOT / path).read_bytes()) for path in paths}
assert before == after, 'Implementation changed during verification; rerun after stabilizing it.'
(RUN / 'implementation-integrity.json').write_text(json.dumps({'result': 'passed', 'before': before, 'after': after}, indent=2) + '\n')
(PACKET / 'latest-run.json').write_text(json.dumps({'path': str(RUN.relative_to(PACKET)), 'result': 'passed'}, indent=2) + '\n')
print('Final checks retained at ' + str(RUN.relative_to(ROOT)), flush=True)
