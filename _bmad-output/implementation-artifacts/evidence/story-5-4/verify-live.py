from pathlib import Path
import hashlib,json,sys,signal,xml.etree.ElementTree as ET
sys.path.insert(0,str(Path.cwd()/'tools/live-topology'))
from live_plans import require_phases
from ci import INDEPENDENT_CASES
ROOT=Path.cwd();PACKET=ROOT/'_bmad-output/implementation-artifacts/evidence/story-5-4';LIVE=PACKET/'live'
def load(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
ci=load(LIVE/'ci-live.json');assert ci['result']=='passed' and ci['fullLiveAccepted'] is True,ci
prepared=load(LIVE/'preparation.json');assert prepared['result']=='prepared' and prepared['runId']==ci['preparationRunId']
assert sha(LIVE/'head-catalog.json')==prepared['headCatalog']['sha256']
heads=load(LIVE/'head-catalog.json');assert heads['result']=='passed'
assert heads['binariesSha256']=={k:v for k,v in prepared['gateway']['clientHost']['output'].items() if k.endswith('.dll')}
compact=lambda value:hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')).hexdigest()
for name,module in heads['modules'].items():assert module['sha256']==compact(module['structuredContent'])
assert heads['catalogSha256']==compact({k:v['structuredContent'] for k,v in heads['modules'].items()})
generation=LIVE/ci['runId'];lane=load(generation/'vectors/live-lane.json')
assert lane['result']=='passed' and lane['fullLiveAccepted'] is True
vectors={load(path)['operation']:path for path in (ROOT/'tools/conformance-vectors/v1/modules').rglob('*.vector.json')}
assert lane['coverage']==sorted(vectors) and lane['passed']==len(vectors) and lane['failed']==0
assert sorted(row['operation'] for row in lane['vectors'])==sorted(vectors)
verified=[]
for row in lane['vectors']:
 op=row['operation'];assert row['result']=='passed' and row['exitCode']==0
 path=generation/'vectors'/row['output']/'live-result.json';receipt=load(path)
 assert receipt['operation']==op and receipt['result']=='passed'
 vector=vectors[op];v=load(vector);approval_path=vector.parent/'approval.json';approval=load(approval_path)
 plan_path=ROOT/'tools/live-topology/plans'/(op+'.json');plan=load(plan_path)
 inventory=ROOT/'tools/inventory-coverage/v1'/(approval['module']+'-approved.json')
 expected={'packageId':approval['packageId'],'version':approval['version'],'artifactHash':approval['artifactHash'],
  'vectorSha256':sha(vector),'planSha256':sha(plan_path),'approvalSha256':sha(approval_path),'inventorySha256':sha(inventory)}
 assert receipt['binding']==expected,(op,receipt['binding'],expected)
 require_phases({'vector':vector,'plan':plan},receipt['phases'])
 verified.append({'operation':op,'receipt':path.relative_to(PACKET).as_posix(),'binding':expected,
  'cliQueryPhases':sum(p['head']=='cli' and p['kind']=='query' for p in receipt['phases']),
  'mcpQueryPhases':sum(p['head']=='mcp' and p['kind']=='query' for p in receipt['phases']),
  'commandSubmissions':sum(p['kind']=='command' for p in receipt['phases'])})
for name,cls,method in INDEPENDENT_CASES:
 assert ci[name]['result']=='passed'
 xml=ET.parse(generation/name/'tests.xml').getroot();cases=xml.findall('.//test');assert len(cases)==1
 test=cases[0];assert test.get('type')==cls and test.get('method')==method and test.get('result')=='Pass'
 assembly=xml.find('assembly');assert all(assembly.get(k)==v for k,v in {'total':'1','passed':'1','failed':'0','skipped':'0','errors':'0'}.items())
boundary=load(generation/'boundary/boundary-result.json');assert boundary['result']=='passed'
cases=boundary['cases'];assert len(cases)==45
auth=[r for r in cases if r['scenario'] in ('missing-token','forged-token','tenant-a-grant','nonmember')]
assert len(auth)==16
assert {(r['scenario'],r['head'],r['kind']) for r in auth}=={(s,h,k) for s in ('missing-token','forged-token','tenant-a-grant','nonmember') for h in ('cli','mcp') for k in ('command','query')}
assert all(r.get('responseFormat') in ('empty','problem+json') and r.get('publicError',{}).get('error',{}).get('code')=='gateway_error' for r in auth)
for row in auth:
 error=row['publicError']['error']
 if row['responseFormat']=='empty':
  assert row['status']==401 or row['kind']=='command'
  expected_error={'code':'gateway_error','status':row['status'],'detail':'Unauthorized' if row['status']==401 else 'Forbidden'}
 elif row['status']==401:
  expected_error={'code':'gateway_error','status':401,'detail':'Authentication is required to access this resource.' if row['scenario']=='missing-token' else 'The provided authentication token is invalid.','reason':'authentication_required'}
 else:
  reason='tenant_mismatch' if row['scenario']=='tenant-a-grant' else 'principal_not_member'
  detail="Not authorized for tenant 'tenant-b'."+(' No tenant authorization claims found. Access denied.' if reason=='principal_not_member' else '')
  correlation=error.get('correlationId');assert isinstance(correlation,str) and len(correlation)==26 and correlation==correlation.upper()
  expected_error={'code':'gateway_error','status':403,'detail':detail,'reason':reason,'correlationId':correlation}
 assert row['publicError']=={'error':expected_error},(row['scenario'],row['head'],row['kind'],error,expected_error)
for kind in ('command','query'):
 missing_docs=[r['publicError'] for r in auth if r['scenario']=='missing-token' and r['kind']==kind]
 assert len(missing_docs)==2 and missing_docs[0]==missing_docs[1]
assert all(r['gatewayRequests']==1 and r['persistedBeforeSha256']==r['persistedAfterSha256'] and r['status']==(401 if r['scenario'] in ('missing-token','forged-token') else 403) for r in auth)
missing=[r for r in cases if r['scenario']=='C05-missing'];assert len(missing)==2
assert {r['head'] for r in missing}=={'cli','mcp'}
assert all(r['status']==404 and r['reason']=='party-not-found' and r['persistedPartyAbsentBeforeAndAfter'] is True for r in missing)
concurrent=[r for r in cases if r['scenario']=='C05-concurrent-repeat'];assert len(concurrent)==1
assert concurrent[0]['accepted']==2 and len(set(concurrent[0]['distinctMessageIds']))==2 and concurrent[0]['persistedDeactivationEvents']==1
invalid=[r for r in cases if r['scenario']=='invalid-public-tenant'];expected_tenants={'platform:tenants','system','SYSTEM','tenant-а','İ','ｔｅｎａｎｔ'}
assert len(invalid)==24
assert {(r['tenant'],r['head'],r['kind']) for r in invalid}=={(t,h,k) for t in expected_tenants for h in ('cli','mcp') for k in ('command','query')}
assert all(r['gatewayRequests']==0 for r in invalid)
overrides=[r for r in cases if r['scenario']=='mcp-override-disabled-and-authorized-selection-denied'];assert len(overrides)==2
assert {r['kind'] for r in overrides}=={'command','query'}
runtimes=list((generation/'runtime-diagnostics').glob('*/result.json'));assert len(runtimes)==len(vectors)+len(INDEPENDENT_CASES)
for p in runtimes:
 r=load(p);assert r['commandExitCode']==0 and r['prerequisitesReady'] is True
 assert set(r['namespaces'])=={'user','pid','net','mnt'}
 assert set(r['ownedInfrastructureStopped'])=={'sentry','redis','placement','scheduler'}
 assert all(type(v) is int and -signal.NSIG<v<=255 for v in r['ownedInfrastructureStopped'].values())
 outside=load(p.parent/'outside.json')['namespaces']
 assert set(outside)==set(r['namespaces']) and all(outside[k]!=v for k,v in r['namespaces'].items())
 assert r['supervisorPid']==1
result={'result':'passed','githubRunId':42652261452,'fullLiveAccepted':True,'sourceCommit':heads['sourceCommit'],
 'catalogSha256':heads['catalogSha256'],'approvedVectorCount':len(vectors),'independentCaseCount':len(INDEPENDENT_CASES),
 'ownedRuntimeCount':len(runtimes),'allRuntimeCleanupPassed':True,'boundaryCaseReceipts':len(cases),
 'credentialAndTenantStateComparisonsPassed':True,'concurrentDeactivation':concurrent[0],
 'vectors':verified,'verifierSha256':sha(Path(__file__))}
(PACKET/'live-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='vectors'},indent=2))
