"""Recheck complete live coverage, immutable bindings, phase/Command cardinality and owned cleanup."""
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

repo, lane_path = map(Path, sys.argv[1:3])
sys.path.insert(0, str(repo / 'tools/conformance-vectors/v1'))
from run_loopback import _assert_result, _pointer

read = lambda path: json.loads(path.read_text())
hash_file = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
lane = read(lane_path / 'live-lane.json')
vectors = {read(path)['operation']: path for path in (repo / 'tools/conformance-vectors/v1/modules').rglob('*.vector.json')}
assert len(vectors) == 21
assert lane['result'] == 'passed' and lane['fullLiveAccepted'] is True
assert lane['passed'] == 21 and lane['failed'] == 0
assert sorted(lane['coverage']) == sorted(vectors)
assert sorted(item['operation'] for item in lane['vectors']) == sorted(vectors)
bindings = {item['operation']: item for item in read(lane_path / lane['runId'] / 'preflight/bindings.json')}
source_bindings = read(Path(__file__).with_name('source-bindings.json'))
all_ids, rows = [], []
for outcome in lane['vectors']:
    operation = outcome['operation']
    assert outcome['result'] == 'passed' and outcome['exitCode'] == 0
    output = lane_path / outcome['output']
    live = read(output / 'live-result.json')
    vector = read(vectors[operation])
    plan_path = repo / 'tools/live-topology/plans' / (operation + '.json')
    plan = read(plan_path)
    binding = dict(bindings[operation]); del binding['operation']
    assert live['operation'] == operation and live['result'] == 'passed' and live['binding'] == binding
    assert binding['vectorSha256'] == hash_file(vectors[operation]) == plan['vectorSha256']
    assert binding['planSha256'] == hash_file(plan_path)
    child_bindings = {item['operation']: item for item in read(output / 'preflight/bindings.json')}
    assert child_bindings == bindings
    xml = ET.parse(output / 'tests.xml').getroot()
    assemblies, tests = xml.findall('assembly'), xml.findall('.//test')
    assert len(assemblies) == len(tests) == 1
    assert {key: assemblies[0].get(key) for key in ['total','passed','failed','skipped','errors']} == dict(total='1',passed='1',failed='0',skipped='0',errors='0')
    steps = {f'/prerequisites/{i}': call for i, call in enumerate(vector['prerequisites'])}
    steps['/invocation'] = vector['invocation']
    steps.update({f'/postconditions/{i}': call for i, call in enumerate(vector['postconditions'])})
    assert [action['step'] for action in plan['actions'] if 'step' in action] == list(steps)
    assert len(live['phases']) == len(plan['actions'])
    captures, commands, query_attempts = {}, 0, 0
    for action, phase in zip(plan['actions'], live['phases']):
        name = action.get('step', action.get('label'))
        call = steps[action['step']] if 'step' in action else action['query']
        assert (phase['phase'], phase['operation'], phase['kind'], phase['result']) == (name,call['operation'],call['kind'],'passed')
        assert phase['attempts'] and phase['attempts'][-1]['result'] == 'passed' and phase['attempts'][-1]['exitCode'] == 0
        document = phase['attempts'][-1]['document']
        assert document['operation'] == call['operation'] and document['tenant'] == call['envelope']['tenant']
        for target in action.get('bindings', []):
            expected = captures[target['capture']]
            if 'offsetSeconds' in target:
                expected = (datetime.fromisoformat(expected.replace('Z','+00:00')) + timedelta(seconds=target['offsetSeconds'])).isoformat()
            assert _pointer(phase['resolvedCall'],target['path']) == (True,expected)
        for capture in action.get('captures', []):
            present, value = _pointer(document,capture['path'])
            assert present and isinstance(value,str) and value
            captures[capture['name']] = value
        assertion_captures = {item['index']: captures[item['capture']] for item in action.get('assertionBindings', [])}
        for index, assertion in enumerate(call['assertions']):
            if index in assertion_captures: assertion = dict(assertion,value=assertion_captures[index])
            _assert_result(document,assertion,operation+' '+name)
        if call['kind'] == 'command':
            commands += 1
            assert len(phase['attempts']) == 1 and document['status'] == 'accepted'
            assert document['aggregateId'] == call['expectedGateway']['body']['aggregateId']
            assert re.fullmatch('[0-7][0-9A-HJKMNP-TV-Z]{25}',document['messageId'])
            assert document['correlationId'] == call['envelope'].get('correlationId',document['messageId'])
            all_ids.append(document['messageId'])
        else:
            assert 'document' in document
            query_attempts += len(phase['attempts'])
    assert live['captures'] == captures
    owned_path = Path(outcome['isolatedReceipt'])
    if not owned_path.exists():
        owned_path = lane_path / 'private-runtime-receipts' / owned_path.parent.name / owned_path.name
    owned = read(owned_path)
    assert owned['commandExitCode'] == 0 and owned['prerequisitesReady'] is True
    assert owned['daprBeforeCommand']['applications'] == [] and owned['mtls']['enabled'] is True
    assert owned['ownedInfrastructureStopped'] == dict(sentry=0,redis=0,placement=0,scheduler=0)
    backup = owned['initialRedisBackup']
    assert backup['databaseSize'] == 0 and backup['createdBeforeApplications'] is True
    backup_path = Path(backup['backupFile'])
    if not backup_path.exists():
        backup_path = owned_path.parent / backup_path.name
    assert backup_path.read_bytes().startswith(b'REDIS') and backup['sha256'] == hash_file(backup_path)
    bootstrap = read(output / 'writer-bootstrap.json')
    assert bootstrap == dict(result='passed',sourceCommit=source_bindings['referenceCommits']['Hexalith.EventStore'],
        backupReference='sha256:'+backup['sha256']+';file:'+backup['backupFile'],activationCount=1,readinessObserved=True)
    rows.append(dict(operation=operation,phases=len(live['phases']),commands=commands,queryAttempts=query_attempts,result='passed'))
assert len(all_ids) == len(set(all_ids)) == 53
assert sum(row['phases'] for row in rows) == 142
print(json.dumps(dict(result='passed',runId=lane['runId'],vectors=len(rows),phases=sum(row['phases'] for row in rows),
    commandSubmissions=len(all_ids),distinctCommandMessageIds=len(set(all_ids)),queryAttempts=sum(row['queryAttempts'] for row in rows),operations=rows),indent=2))
