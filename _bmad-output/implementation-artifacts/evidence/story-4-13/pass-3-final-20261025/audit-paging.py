"""Independently check the approved Parties second-page probes against live documents."""
import hashlib,json
from pathlib import Path
root=Path('/home/administrator/projects/hexalith/mcpcli')
out=Path(__file__).resolve().parent
lane=json.loads((out/'live/live-lane.json').read_text())
assert lane['result']=='passed' and lane['fullLiveAccepted'] is True
rows=[]
for operation in ('parties.list-parties','parties.search-parties'):
    outcome=next(item for item in lane['vectors'] if item['operation']==operation)
    assert outcome['result']=='passed'
    live=json.loads((out/'live'/outcome['output']/'live-result.json').read_text())
    vector=json.loads((root/'tools/conformance-vectors/v1/modules/Hexalith.Parties.Contracts'/(operation.split('.')[1]+'.vector.json')).read_text())
    plan_path=root/'tools/live-topology/plans'/(operation+'.json')
    plan=json.loads(plan_path.read_text())
    action=next(item for item in plan['actions'] if item.get('label')=='offset-after-only-match')
    assert live['binding']['planSha256']==hashlib.sha256(plan_path.read_bytes()).hexdigest()
    invocation=vector['invocation']; expected_envelope={**invocation['envelope'],'offset':2,'pageSize':2}
    assert action['query']['payload']==invocation['payload']
    assert action['query']['envelope']==expected_envelope
    initial=next(phase for phase in live['phases'] if phase['phase']=='/invocation')['attempts'][-1]['document']
    assert len(initial['document']['items'])==1 and initial['document']['totalCount']==1
    assert initial['paging']['offset']==0 and initial['paging']['pageSize']==2
    probe=next(phase for phase in live['phases'] if phase['phase']=='offset-after-only-match')
    assert probe['kind']=='query' and probe['result']=='passed'
    assert probe['resolvedCall']==dict(operation=operation,kind='query',payload=invocation['payload'],envelope=expected_envelope)
    attempt=probe['attempts'][-1]
    assert attempt['result']=='passed' and attempt['exitCode']==0
    document=attempt['document']
    assert document['document']['items']==[] and document['document']['totalCount']==1
    assert document['paging']['offset']==2 and document['paging']['totalCount']==1
    rows.append(dict(operation=operation,originalFiltersPreserved=True,firstPageItems=1,laterPageItems=0,pageSize=2,offset=2,totalCount=1,queryAttempts=len(probe['attempts'])))
report=dict(result='passed',runId=lane['runId'],operations=rows)
(out/'paging-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
