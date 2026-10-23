import hashlib, importlib.util, json, shutil, subprocess, sys, tempfile, zipfile
from pathlib import Path
from xml.sax.saxutils import escape
source=Path(sys.argv[1]).resolve()
artifact=Path(sys.argv[2]).resolve()
published = len(sys.argv) == 5 and sys.argv[4] == '--published'
if len(sys.argv) not in {4, 5} or (len(sys.argv) == 5 and not published):
 raise SystemExit('Usage: qualify-parties-helper.py SOURCE ARTIFACT MANIFEST [--published]')
sys.path.insert(0,str(source/'scripts'))
spec=importlib.util.spec_from_file_location('package_validator',source/'scripts/validate-nuget-packages.py')
validator=importlib.util.module_from_spec(spec);sys.modules[spec.name]=validator;spec.loader.exec_module(validator)
metadata=validator.get_metadata(artifact)
manifest=json.loads(Path(sys.argv[3]).read_text())
if published:
 metadata=validator.validate_published_metadata(artifact,'Hexalith.Parties.Aspire',metadata.version,'https://github.com/Hexalith/Hexalith.Parties',manifest['sourceCommit'],{},'3.126.1')
for name,expected in manifest['files'].items():
 if hashlib.sha256((source/name).read_bytes()).hexdigest()!=expected:
  raise RuntimeError('Source input changed: '+name)
with zipfile.ZipFile(artifact) as archive:
 assemblies=sorted(name for name in archive.namelist() if name.lower().endswith('.dll'))
 if assemblies!=['lib/net10.0/Hexalith.Parties.Aspire.dll']:
  raise RuntimeError('Unexpected packaged assemblies: '+repr(assemblies))
validator.validate_dependency_boundaries(artifact,metadata)
validator.validate_event_store_dependency_versions(artifact,metadata,'3.126.1')
receipt={'artifact':artifact.name,'version':metadata.version,'sha256':hashlib.sha256(artifact.read_bytes()).hexdigest(),'published':published,
'assemblies':assemblies,'artifactBytes':artifact.stat().st_size,'sourceBinding':{'baselineCommit':manifest['baselineCommit'],'taskTreeSha256':manifest['taskTreeSha256'],**({'sourceCommit':manifest['sourceCommit']} if 'sourceCommit' in manifest else {})},'directDependencies':{dependency.package_id:dependency.version for dependency in metadata.dependencies},'rootSelection':[]}
with tempfile.TemporaryDirectory(prefix='story412-consumer-') as directory:
 root=Path(directory)/'root';(root/'src').mkdir(parents=True);project=root/'tests/Consumer';project.mkdir(parents=True)
 shutil.copy(source/'global.json',root/'global.json')
 (project/'Consumer.csproj').write_text(f'<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework><OutputType>Exe</OutputType><ImplicitUsings>enable</ImplicitUsings></PropertyGroup><ItemGroup><PackageReference Include="Hexalith.Parties.Aspire" Version="{metadata.version}" /></ItemGroup></Project>')
 (project/'Program.cs').write_text('''using Aspire.Hosting;
using Hexalith.EventStore.Aspire;
using Hexalith.Parties.Aspire;
var type = typeof(HexalithPartiesServerExtensions).Assembly.GetType("Hexalith.Parties.Aspire.PartiesServerProjectMetadata", true)!;
var metadata = (IProjectMetadata)Activator.CreateInstance(type, true)!;
if (!metadata.SuppressBuild) throw new Exception("Server build is not suppressed");
var root = RepositoryProjectPaths.GetRepositoryRoot();
try {
 var path = metadata.ProjectPath;
 if (args[0] != "found" || path != Path.GetFullPath(Path.Combine(root, args[1], "src", "Hexalith.Parties", "Hexalith.Parties.csproj")))
  throw new Exception("Incorrect source root: " + path);
} catch (InvalidOperationException error) when (args[0] == "missing") {
 var required = Path.Combine(root, "references", "Hexalith.Parties", "src", "Hexalith.Parties", "Hexalith.Parties.csproj");
 if (!error.Message.Contains(required)) throw;
 Console.WriteLine("missing-root|rejected"); return;
}
if (args[0] == "missing") throw new Exception("Missing root checkout was accepted");
Console.WriteLine("root-selection|verified");
''')
 def run(*arguments):
  result=subprocess.run(arguments,cwd=root,capture_output=True,text=True,timeout=120)
  if result.returncode: raise RuntimeError(result.stdout+result.stderr)
  return result.stdout.strip()
 packages=Path(directory)/'isolated-packages'
 sources=['--source','https://api.nuget.org/v3/index.json']
 if not published: sources=['--source',str(artifact.parent)]+sources
 run('dotnet','restore',str(project/'Consumer.csproj'),'--packages',str(packages),'-p:RestoreFallbackFolders=',*sources)
 restored=packages/'hexalith.parties.aspire'/metadata.version.lower()/('hexalith.parties.aspire.'+metadata.version.lower()+'.nupkg')
 if hashlib.sha256(restored.read_bytes()).hexdigest()!=receipt['sha256']:
  raise RuntimeError('Restored helper archive does not match the qualified artifact')
 receipt['restoredArtifactSha256']=hashlib.sha256(restored.read_bytes()).hexdigest()
 run('dotnet','build',str(project/'Consumer.csproj'),'--no-restore','--configuration','Release','-warnaserror','-m:1')
 assets=json.loads((project/'obj/project.assets.json').read_text())
 receipt['resolvedClosure']={identity.rsplit('/',1)[0]:identity.rsplit('/',1)[1] for identity,node in sorted(assets['libraries'].items()) if node['type']=='package'}
 forbidden=[package for package in receipt['resolvedClosure'] if package.startswith('Hexalith.') and package not in {'Hexalith.Parties.Aspire','Hexalith.EventStore.Aspire'}]
 if forbidden: raise RuntimeError(f'Forbidden helper dependency closure: {forbidden}')
 dll=str(project/'bin/Release/net10.0/Consumer.dll')
 def source_project(base):
  path=base/'src/Hexalith.Parties/Hexalith.Parties.csproj';path.parent.mkdir(parents=True,exist_ok=True);path.write_text('<Project Sdk="Microsoft.NET.Sdk" />')
 # Each probe invokes the packed artifact in a fresh process; unrelated workspace references cannot satisfy it.
 source_project(root);(root/'Hexalith.Parties.slnx').write_text('<Solution />')
 run('dotnet',dll,'found','.');receipt['rootSelection'].append({'case':'own-root','result':'pass'})
 (root/'Hexalith.Parties.slnx').unlink();shutil.rmtree(root/'src/Hexalith.Parties')
 source_project(root/'references/Hexalith.Parties')
 run('dotnet',dll,'found','references/Hexalith.Parties');receipt['rootSelection'].append({'case':'direct-root-reference','result':'pass'})
 shutil.rmtree(root/'references/Hexalith.Parties')
 for case,base in [('missing',None),('nested-only',root/'references/Other/references/Hexalith.Parties'),('root-level-only',root/'Hexalith.Parties'),('sibling-only',root.parent/'Hexalith.Parties')]:
  if base: source_project(base)
  run('dotnet',dll,'missing');receipt['rootSelection'].append({'case':case,'result':'pass'})
receipt['resolvedClosureSha256']=hashlib.sha256(json.dumps(receipt['resolvedClosure'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
receipt['result']='pass'
(artifact.parent/'qualification.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k!='resolvedClosure'},indent=2))
print('Resolved packages:',len(receipt['resolvedClosure']))
