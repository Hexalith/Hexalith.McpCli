from pathlib import Path
import subprocess,json,os,time,sys,hashlib,xml.etree.ElementTree as ET
r=Path('/tmp/mcpcli-418-tenants410-isolated');e=Path(__file__).parent;env=os.environ.copy();env['NUGET_PACKAGES']='/tmp/mcpcli-418-sdk410-public-cache';env['NUGET_HTTP_CACHE_PATH']='/tmp/mcpcli-418-sdk410-public-http-cache'
common=['-c','Release','-warnaserror','-m:1','-nr:false','-p:UseHexalithProjectReferences=false','-p:UseNuGetDeps=true','-p:HexalithEventStoreFromSource=false','-p:HexalithFrontComposerFromSource=false','-p:HexalithMemoriesFromSource=false']
strict=['-p:NuGetAudit=true','-p:NuGetAuditMode=all','-p:NuGetAuditLevel=low','-p:TreatWarningsAsErrors=true','-p:WarningsNotAsErrors=','-p:UseHexalithProjectReferences=false','-p:UseNuGetDeps=true','-p:HexalithEventStoreFromSource=false','-p:HexalithEventStoreVersion=4.1.0','-p:HexalithBuildPackageVersions1='+str(e/'native-runtime-packages.props')]
records=[]
def run(name,cmd,limit=300):
 started=time.monotonic()
 with (e/(name+'.log')).open('w') as f:p=subprocess.run(cmd,cwd=r,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=limit)
 records.append({'name':name,'command':cmd,'exit_code':p.returncode,'elapsed_seconds':round(time.monotonic()-started,2),'private_cache':env['NUGET_PACKAGES']});(e/'final-commands.json').write_text(json.dumps(records,indent=2)+'\n');print(name,p.returncode,flush=True)
 if p.returncode:raise SystemExit(p.returncode)
failed=[n.attrib['name'] for n in ET.parse(e/'server-tests-sdk410.xml').iter('test') if n.attrib.get('result')=='Fail']
assert len(failed)==7
cmd=['dotnet','tests/Hexalith.Tenants.Server.Tests/bin/Release/net10.0/Hexalith.Tenants.Server.Tests.dll']
for method in failed:cmd+=['-method',method]
run('server-missing-fixtures-retest',cmd+['-xml',str(e/'server-missing-fixtures-retest.xml')],90)
run('native-strict-build',['dotnet','build','src/Hexalith.Tenants/Hexalith.Tenants.csproj','--configuration','Release','-warnaserror','-m:1',*strict])
sys.path.insert(0,'/tmp/mcpcli-418-sdk410-isolated/tools/live-topology')
import ci
assert ci.EVENTSTORE_COHORT=='4.1.0'
proof=ci.restored_cohort(r/'src/Hexalith.Tenants/Hexalith.Tenants.csproj','Hexalith.EventStore.DomainService')
(e/'native-public-sdk-provenance.json').write_text(json.dumps(proof,indent=2)+'\n')
# Same source/path/build properties; vary only the public SDK selection and then restore it.
comparisons={}
for version,label in [('4.1.0','410-before'),('4.0.4','404'),('4.1.0','410-after')]:
 props=[p if not p.startswith('-p:HexalithEventStoreVersion=') else '-p:HexalithEventStoreVersion='+version for p in strict]
 run('controlled-contracts-build-'+label,['dotnet','build','src/Hexalith.Tenants.Contracts/Hexalith.Tenants.Contracts.csproj','--configuration','Release','-warnaserror','-m:1',*props],180)
 dll=(r/'src/Hexalith.Tenants.Contracts/bin/Release/net10.0/Hexalith.Tenants.Contracts.dll').read_bytes()
 comparisons[label]={'sdk':version,'dll_sha256':hashlib.sha256(dll).hexdigest()}
 (e/('controlled-contracts-'+label+'.dll')).write_bytes(dll)
comparisons['same_410_bytes_after_restore']=comparisons['410-before']['dll_sha256']==comparisons['410-after']['dll_sha256']
comparisons['different_when_only_sdk_changes']=comparisons['410-before']['dll_sha256']!=comparisons['404']['dll_sha256']
assert comparisons['same_410_bytes_after_restore'] and comparisons['different_when_only_sdk_changes']
(e/'controlled-contracts-sdk-comparison.json').write_text(json.dumps(comparisons,indent=2)+'\n')
for sdk,label in [('4.0.4','legacy404'),('4.1.0','public410')]:
 run(label+'-catalog-test-build',['dotnet','build','tests/Hexalith.Tenants.Contracts.Tests/Hexalith.Tenants.Contracts.Tests.csproj',*common,'-p:HexalithEventStoreVersion='+sdk],180)
 run(label+'-compiled-catalog-tests',['dotnet','tests/Hexalith.Tenants.Contracts.Tests/bin/Release/net10.0/Hexalith.Tenants.Contracts.Tests.dll','-class','Hexalith.Tenants.Contracts.Tests.PublishedTenantCatalogTests','-class','Hexalith.Tenants.Contracts.Tests.TenantCatalogTests','-xml',str(e/(label+'-compiled-catalog-tests.xml'))],60)
run('diff-check',['git','diff','--check'],30)
(e/'proposed-upgrade.patch').write_bytes(subprocess.check_output(['git','diff'],cwd=r))
