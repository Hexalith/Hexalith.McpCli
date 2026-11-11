"""Independent parent checks of the frozen implementation and retained packet."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent
PACKET = HERE.parent
sha = lambda raw: hashlib.sha256(raw).hexdigest()
before = json.loads((HERE / 'before.json').read_text())
verification = json.loads((PACKET / 'verification.json').read_text())
run = PACKET / verification['run']
commands = []


def execute(name, arguments, expected=0):
    result = subprocess.run(arguments, capture_output=True, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}, timeout=300)
    (HERE / (name + '.stdout.txt')).write_bytes(result.stdout)
    (HERE / (name + '.stderr.txt')).write_bytes(result.stderr)
    commands.append({'name': name, 'command': arguments, 'exitCode': result.returncode,
                     'environment': {'PYTHONDONTWRITEBYTECODE': '1'},
                     'stdout': name + '.stdout.txt', 'stderr': name + '.stderr.txt'})
    (HERE / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
    assert result.returncode == expected, (name, result.returncode)
    return result.stdout


for path, digest in before['files'].items():
    assert sha((ROOT / path).read_bytes()) == digest, path
assert execute('head', ['git', 'rev-parse', 'HEAD']).decode().strip() == before['head']
assert execute('reference-entries', ['git', 'ls-files', '--stage', '--', '.gitmodules', 'references']).decode() == before['trackedReferenceEntries']
assert execute('reference-status', ['git', 'status', '--porcelain', '--ignore-submodules=none', '--', '.gitmodules', 'references']).decode() == before['referenceStatus'] == ''
execute('unstaged-index', ['git', 'diff', '--cached', '--quiet'])
execute('diff-check', ['git', 'diff', '--check'])
for path, digest in verification['implementation']['after'].items():
    assert sha((ROOT / path).read_bytes()) == digest, path

test_code = '''import importlib.util,pathlib,unittest,sys
p=pathlib.Path('tools/proprietary-surfaces/v1/test_census.py')
s=importlib.util.spec_from_file_location('parent_cases',p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
names=[n for n in unittest.defaultTestLoader.getTestCaseNames(m.CensusTests) if n.startswith('test_manifest_selector_')]
r=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(m.CensusTests(n) for n in names))
sys.exit(0 if r.wasSuccessful() else 1)
'''
execute('selector-tests', [sys.executable, '-c', test_code])
assert not (HERE / 'selector-tests.stdout.txt').read_bytes()
execute('census', [sys.executable, 'tools/proprietary-surfaces/v1/check.py', '--output', str(HERE / 'census.json')], 1)
assert (HERE / 'census.stdout.txt').read_bytes() == (HERE / 'census.json').read_bytes() == (run / 'census.json').read_bytes()
assert (HERE / 'census.stderr.txt').read_bytes() == (run / 'current-pin-census.stderr.txt').read_bytes()
delta = json.loads((PACKET / 'blocker-delta.json').read_text())
assert len(delta['beforeAccounting']) == delta['beforeCounts']['inspectionErrors'] + delta['beforeCounts']['rejectedObservations']
assert not delta['newBlockers']
assert sum(row['outcome'] != 'retained' for row in delta['beforeAccounting']) == 2
assert len(json.loads((PACKET / 'matrix-coverage.json').read_text())['rows']) == 5
proof = json.loads((PACKET / 'selector-source-proof.json').read_text())
assert not proof['resolverErrors']
assert all(not row['metadataErrors'] and not row['observations'] for row in proof['selectedProjectInspection'])
for path, digest in verification['implementation']['after'].items():
    assert sha((ROOT / path).read_bytes()) == digest, path
result = {'result': 'passed', 'parentRevision': before['head'],
          'independentlyPreservedFiles': len(before['files']),
          'frozenImplementation': verification['implementation']['after'],
          'completeReportSha256': sha((HERE / 'census.json').read_bytes()),
          'reportAndDiagnosticsMatchFinalSerialRun': True,
          'selectedMetadataClean': True, 'matrixRows': 5,
          'exactlyTwoPriorBlockersResolved': True, 'newBlockers': 0,
          'indexEmpty': True, 'referencesUnchanged': True,
          'acceptance': 'failed', 'storyStatus': 'in-progress'}
(HERE / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, sort_keys=True))
