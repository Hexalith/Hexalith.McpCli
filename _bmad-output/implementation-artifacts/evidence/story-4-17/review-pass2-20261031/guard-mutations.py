import sys,shutil,subprocess,pathlib
S=pathlib.Path(sys.argv[1]);base=S/'base'
muts={
 'M0-none':('phases.py','',''),
 'M1-forward-sidecar':('phases.py',"  if require_ready:require(all(self.sidecar_ready(app) for app in APPS),'sidecar-runtime-unready')\n",''),
 'M2-forward-boundary':('phases.py',"  if metadata:self.gateway_api_boundary()\n  port=",'  port='),
 'M3-handoff-podmissing':('phases.py',"   require(all(self.app_pod(app) is not None for app in APPS),'application-pod-missing')\n   require(all(self.sidecar_ready(app) for app in APPS),'sidecar-runtime-unready')\n   value,expiry","   require(all(self.sidecar_ready(app) for app in APPS),'sidecar-runtime-unready')\n   value,expiry"),
 'M4-handoff-sidecar':('phases.py',"   require(all(self.sidecar_ready(app) for app in APPS),'sidecar-runtime-unready')\n   value,expiry","   value,expiry"),
 'M5-handoff-chmod':('phases.py',";profile.chmod(0o600)",''),
 'M6-tenants-marker':('prepare.py'," and next(i for i in images if i['name']=='tenants')['markers']['BootstrapGlobalAdminEnabled']",''),
 'M7-seed-diverges':('phases.py',"'commandType':wire,'payload':operation['payload']}","'commandType':wire,'payload':dict(operation['payload'],Role='TenantOwner') if wire=='add-user-to-tenant' else operation['payload']}"),
 'M9-json-fixtures':('prepare.py',"access=yaml.safe_load((MCPCLI/FIXTURES[3])","access=json.loads((MCPCLI/FIXTURES[3])"),
}
for name,(f,old,new) in muts.items():
 d=S/name;shutil.rmtree(d,ignore_errors=True);shutil.copytree(base,d)
 p=d/'a/b/v1'/f;t=p.read_text()
 if old and t.count(old)!=1:print(name,'PATTERN COUNT',t.count(old));continue
 if old:p.write_text(t.replace(old,new))
 r=subprocess.run([sys.executable,'-B','-m','unittest','test_v1'],cwd=d/'a/b/v1',capture_output=True,text=True,timeout=200)
 last=[l for l in r.stderr.splitlines() if l.startswith(('Ran','OK','FAILED'))]
 failing=sorted({l.split('(')[0].replace('FAIL: ','').replace('ERROR: ','').strip() for l in r.stderr.splitlines() if l.startswith(('FAIL:','ERROR:'))})
 print(name,r.returncode,last,failing[:4])
