from pathlib import Path
import sys,json,subprocess,hashlib,zipfile,io,importlib.util,datetime
run_id=int(sys.argv[1]);sha=sys.argv[2];out=Path(sys.argv[3]);out.mkdir(parents=True,exist_ok=True);gh='/tmp/mcpcli-418-tools/gh-2.103.3/bin/gh'
def api(path):return json.loads(subprocess.check_output([gh,'api',path]))
run=api(f'repos/Hexalith/Hexalith.McpCli/actions/runs/{run_id}');assert run['head_sha']==sha and run['event']=='workflow_dispatch' and run['head_branch']=='main'
artifacts=api(f'repos/Hexalith/Hexalith.McpCli/actions/runs/{run_id}/artifacts?per_page=100');matches=[a for a in artifacts['artifacts'] if a['name']=='paired-preparation'];assert len(matches)==1;a=matches[0];raw=subprocess.check_output([gh,'api',f"repos/Hexalith/Hexalith.McpCli/actions/artifacts/{a['id']}/zip"]);assert 'sha256:'+hashlib.sha256(raw).hexdigest()==a['digest'];(out/'paired-preparation.original.zip').write_bytes(raw);(out/'preparation-artifact-metadata.json').write_text(json.dumps(a,indent=2)+'\n')
spec=importlib.util.spec_from_file_location('readme_scan','/tmp/mcpcli-418-tools/scan-readme-links.py');scanner=importlib.util.module_from_spec(spec);spec.loader.exec_module(scanner);source=Path('README.md').read_bytes();source_scan=scanner.scan(source);assert not source_scan['relative_destinations'];results={}
with zipfile.ZipFile(io.BytesIO(raw)) as z:
 prepared_raw=z.read('prepared.json');prepared=json.loads(prepared_raw);assert prepared['source_sha']==sha and prepared['version']=='2.0.1';expected={f'{p}.2.0.1.nupkg' for p in ['Hexalith.McpCli.Abstractions','Hexalith.McpCli']};assert set(prepared['packages'])==expected
 for name,digest in prepared['packages'].items():
  package=z.read('packages/'+name);assert hashlib.sha256(package).hexdigest()==digest
  with zipfile.ZipFile(io.BytesIO(package)) as nupkg:readme=nupkg.read('README.md')
  assert readme==source;report=scanner.scan(readme);assert not report['relative_destinations'];results[name]=dict(package_sha256=digest,readme_sha256=report['readme_sha256'],destinations=len(report['destinations']),relative_destinations=report['relative_destinations']);(out/(name+'.readme-link-scan.json')).write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
receipt=dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source=sha,staging_run_id=run_id,artifact_id=a['id'],original_zip_digest=a['digest'],preparation_sha256=hashlib.sha256(prepared_raw).hexdigest(),packages=results,result='passed',scope='Read-only original staged bytes, both main packaged README entries equal source and contain zero relative file destinations. This does not grant platform or operator acceptance.');(out/'staged-readmes-verified.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
