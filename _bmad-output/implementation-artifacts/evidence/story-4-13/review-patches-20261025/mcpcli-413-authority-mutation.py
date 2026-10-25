from pathlib import Path
import json
import subprocess
import tempfile
root=Path.cwd()
output=root/'tests/Hexalith.McpCli.Manifest.Tests/bin/Release/net10.0'
sdk=subprocess.check_output(['dotnet','--list-sdks'],text=True).splitlines()[-1]
version,base=sdk.split(' ',1)
sdk_root=Path(base.strip('[]'))
compiler=sdk_root/version/'Roslyn/bincore/csc.dll'
references=next((sdk_root.parent/'packs/Microsoft.NETCore.App.Ref').glob('10.0.*/ref/net10.0'))
source=(root/'tests/Hexalith.McpCli.Integration.Tests/AdministratorAuthorityBootstrap.cs').read_text()
test=root/'tests/Hexalith.McpCli.Manifest.Tests/AdministratorAuthorityBootstrapTests.cs'
results=[]
with tempfile.TemporaryDirectory(prefix='mcpcli-authority-mutation-') as directory:
 work=Path(directory)
 for path in output.glob('*.dll'):
  if path.name!='Hexalith.McpCli.Manifest.Tests.dll': (work/path.name).symlink_to(path)
 (work/'AuthorityMutation.runtimeconfig.json').write_bytes((output/'Hexalith.McpCli.Manifest.Tests.runtimeconfig.json').read_bytes())
 (work/'AuthorityMutation.deps.json').write_bytes((output/'Hexalith.McpCli.Manifest.Tests.deps.json').read_bytes())
 (work/'GlobalUsings.cs').write_text('global using System; global using System.Collections.Generic; global using System.Linq; global using System.Net.Http; global using System.Threading; global using System.Threading.Tasks; global using Xunit;')
 (work/'Program.cs').write_text('''using Hexalith.McpCli.Manifest.Tests;
try { await new AdministratorAuthorityBootstrapTests().DocumentWithoutAdministratorKeepsPolling(); Console.WriteLine("accepted"); return 0; }
catch (Xunit.Sdk.EqualException) { Console.WriteLine("missing administrator released barrier after one query"); return 2; }
''')
 for mutation in [False,True]:
  helper=source
  if mutation:
   helper=helper.replace('result.Payload is { } payload && payload.TryGetProperty("items", out JsonElement items)\n                        && items.EnumerateArray().Any(item => item.GetProperty("userId").GetString() == administratorId)', 'result.Payload is not null')
   if helper==source: raise RuntimeError('Authority predicate mutation did not match')
  (work/'AdministratorAuthorityBootstrap.cs').write_text(helper)
  command=['dotnet',str(compiler),'-nologo','-t:exe','-nullable:enable','-out:'+str(work/'AuthorityMutation.dll')]
  command+=['-r:'+str(path) for path in references.glob('*.dll')]
  command+=['-r:'+str(path) for path in work.glob('*.dll') if path.name!='AuthorityMutation.dll']
  command+=list(map(str,[work/'GlobalUsings.cs',work/'Program.cs',work/'AdministratorAuthorityBootstrap.cs',test,root/'tests/Hexalith.McpCli.Manifest.Tests/ProjectionWriterBootstrapHandler.cs']))
  build=subprocess.run(command,capture_output=True,text=True,timeout=30)
  if build.returncode: raise RuntimeError(build.stdout+build.stderr)
  run=subprocess.run(['dotnet',str(work/'AuthorityMutation.dll')],capture_output=True,text=True,timeout=10)
  results.append(dict(mutated=mutation,exitCode=run.returncode,stdout=run.stdout,stderr=run.stderr))
  if run.returncode != (2 if mutation else 0): raise RuntimeError(run.stdout+run.stderr)
print(json.dumps({'detected':True,'runs':results},indent=2))
