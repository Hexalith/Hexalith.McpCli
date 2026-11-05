from pathlib import Path,PurePosixPath
import json,subprocess,hashlib,zipfile,xml.etree.ElementTree as E,datetime
out=Path('/tmp/mcpcli-418-readme-link-fix');gh='/tmp/mcpcli-418-tools/gh-2.103.3/bin/gh';run_id=42072073153;sha='aa2845edbea23444a1d362060b8d0f5dc05a132e'
def api(path):return json.loads(subprocess.check_output([gh,'api',path]))
run=api(f'repos/Hexalith/Hexalith.McpCli/actions/runs/{run_id}');assert run['head_sha']==sha and run['status']=='completed' and run['conclusion']=='success'
artifacts=api(f'repos/Hexalith/Hexalith.McpCli/actions/runs/{run_id}/artifacts?per_page=100');(out/'artifacts-live-final.json').write_text(json.dumps(artifacts,indent=2)+'\n');a=next(a for a in artifacts['artifacts'] if a['name']=='aspire-hook-evidence');raw=subprocess.check_output([gh,'api',f"repos/Hexalith/Hexalith.McpCli/actions/artifacts/{a['id']}/zip"]);assert 'sha256:'+hashlib.sha256(raw).hexdigest()==a['digest'];p=out/'aspire-hook-evidence.original.zip';p.write_bytes(raw)
with zipfile.ZipFile(p) as z:
 names=z.namelist();assert len(names)==len(set(names)) and all(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts for n in names)
 def only(suffix):
  hits=[n for n in names if n.endswith(suffix)];assert len(hits)==1,hits;return hits[0]
 ci=json.loads(z.read(only('ci-live.json')));lane=json.loads(z.read(only('live-lane.json')));assert ci['result']=='passed' and ci['fullLiveAccepted'] is True;assert lane['result']=='passed' and lane['fullLiveAccepted'] is True and lane['passed']==21 and lane['failed']==0 and len(lane['vectors'])==21
 expected=sorted(json.loads(f.read_text())['operation'] for f in Path('tools/conformance-vectors/v1/modules').rglob('*.vector.json'));assert sorted(lane['coverage'])==expected and sorted(v['operation'] for v in lane['vectors'])==expected;assert all(v['result']=='passed' and v['exitCode']==0 for v in lane['vectors'])
 smoke=E.fromstring(z.read(only('/smoke/tests.xml')));cases=smoke.findall('.//test');assert len(cases)==1 and cases[0].get('result')=='Pass';vectors=[n for n in names if n.endswith('/tests.xml') and '/vectors/' in n];assert len(vectors)==21
 for n in vectors:
  cases=E.fromstring(z.read(n)).findall('.//test');assert len(cases)==1 and cases[0].get('result')=='Pass'
 for name,data in [('ci-live.json',ci),('live-lane.json',lane)]: (out/name).write_text(json.dumps(data,indent=2)+'\n')
receipt=dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source=sha,run_id=run_id,artifact_id=a['id'],archive_digest=a['digest'],vectors_passed=21,independent_smoke_passed=1,result='passed',scope='Authenticated original hosted artifact, exact approved coverage, all21 individual XML cases and independent smoke; CI itself also enforces phase/provenance/ownership cleanup receipts.');(out/'live-verified.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
