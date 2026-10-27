import hashlib
import json
from pathlib import Path
import re
import subprocess
import tarfile
import xml.etree.ElementTree as ET

root = Path('/home/administrator/projects/hexalith/mcpcli')
evidence = root / '_bmad-output/implementation-artifacts/evidence/story-4-14/review-patches-20261027'
base = root / 'TestResults/live-ci-review-patches-20261027'
prepared = json.loads((base / 'preparation.json').read_text())
report = json.loads((base / 'ci-live.json').read_text())
assert report['result'] == 'passed' and report['fullLiveAccepted'] is True
assert report['vectors']['count'] == 21 and report['smoke']['result'] == 'passed'
output = Path(report['output'])
lane = json.loads((output / 'vectors/live-lane.json').read_text())
assert len(lane['vectors']) == 21 and lane['passed'] == 21 and lane['failed'] == 0
assert all(row['result'] == 'passed' and row['exitCode'] == 0 for row in lane['vectors'])
xml_paths = sorted(output.rglob('tests.xml'))
cases = [case for path in xml_paths for case in ET.parse(path).getroot().findall('.//test')]
assert len(cases) == 22 and all(case.get('result') == 'Pass' for case in cases)
owned = sorted((output / 'runtime-diagnostics').glob('*/result.json'))
assert len(owned) == 22
for path in owned:
    receipt = json.loads(path.read_text())
    assert receipt['commandExitCode'] == 0 and receipt['prerequisitesReady'] is True
    assert set(receipt['ownedInfrastructureStopped']) == {'redis', 'sentry', 'placement', 'scheduler'}
    assert receipt['supervisorPid'] == 1
semantics = [json.loads(path.read_text()) for path in output.rglob('live-result.json')]
assert len(semantics) == 21 and all(receipt['result'] == 'passed' for receipt in semantics)
phases = [phase for receipt in semantics for phase in receipt['phases']]
commands = [phase for phase in phases if phase['kind'] == 'command']
assert all(len(phase['attempts']) == 1 and phase['attempts'][0]['result'] == 'passed' for phase in commands)
message_ids = [phase['attempts'][0]['document']['messageId'] for phase in commands]
assert len(message_ids) == len(set(message_ids)) == 53
query_attempts = sum(len(phase['attempts']) for phase in phases if phase['kind'] == 'query')
files = sorted(path for path in base.rglob('*') if path.is_file())
for path in files:
    assert path.suffix not in ('.key', '.pem', '.rdb'), path
    text = path.read_text(errors='replace')
    assert re.search(r'\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', text) is None, path
    assert '-----BEGIN PRIVATE KEY-----' not in text and '-----BEGIN CERTIFICATE-----' not in text, path
archive = evidence / 'live-ci.tar.gz'
with tarfile.open(archive, 'w:gz') as saved:
    saved.add(base, arcname='live-ci')
with tarfile.open(archive, 'r:gz') as saved:
    members = [member for member in saved.getmembers() if member.isfile()]
    assert len(members) == len(files)
    for member in members:
        original = base / Path(member.name).relative_to('live-ci')
        assert saved.extractfile(member).read() == original.read_bytes(), member.name
verification = {
    'sourceHead': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
    'builds': {'base': '35587cfd104c5750d8ec3c0716933f386d6a0232',
               'qualifiedCommit': '857ef02dbb4bde1bd4e678546aa41e73fb7d68b1',
               'published': False, 'workflowAssertions': 323, 'commitlint': 'passed',
               'changedPaths': ['.github/workflows/domain-ci.md']},
    'verification': {'releaseRestore': 'passed', 'releaseWarningsAsErrorsBuild': 'passed',
                     'dotnetPassed': 1531, 'dotnetExistingSkipped': 5, 'dotnetFailed': 0,
                     'dotnetProjects': {'Abstractions': 20, 'Analyzers': 19, 'Core': 704,
                                        'Manifest': 251, 'Cli': 479, 'Mcp': 58},
                     'pythonTests': 137, 'guardRemovalMutationsCaught': 18, 'callerInputRemovalsCaught': 3,
                     'bashSyntax': 'passed', 'callerActionlint': 'passed', 'buildsActionlint': 'passed'},
    'live': {'fullLiveAccepted': True, 'vectorsPassed': 21, 'smokePassed': 1,
             'passingXmlCases': len(cases), 'ownedCleanupReceipts': len(owned),
             'semanticPhases': len(phases), 'commandSubmissions': len(commands),
             'distinctCommandMessageIds': len(set(message_ids)), 'queryAttempts': query_attempts,
             'evidenceDirectory': str(base), 'privateDirectory': prepared['privateDirectory'],
             'archiveFilesComparedWithOriginals': len(files),
             'archiveSha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
             'aspireArchive': prepared['tools']['aspireArchive'],
             'sourceEventStoreVersions': {row['module']: row['HexalithEventStoreVersion'] for row in prepared['sources']}},
    'remaining': ['Publish the qualified local Builds revision and obtain hosted acceptance for the updated caller.',
                  'Previously deferred Dapr port-bind intermittence and agent-context package-version wording remain outside these patches.'],
}
(evidence / 'verification.json').write_text(json.dumps(verification, indent=2) + '\n')
print(json.dumps(verification, indent=2))
