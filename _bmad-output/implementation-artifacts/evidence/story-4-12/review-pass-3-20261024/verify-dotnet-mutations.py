import hashlib, json, pathlib, shutil, subprocess, tempfile, time
root=pathlib.Path('/home/administrator/projects/hexalith/mcpcli')
evidence=root/'_bmad-output/implementation-artifacts/evidence/story-4-12/review-pass-3-20261024'
results=[]
def execute(label,command,cwd,expect_success=False):
    started=time.monotonic()
    result=subprocess.run(command,cwd=cwd,text=True,capture_output=True,timeout=120)
    (evidence/(label+'.stdout.txt')).write_text(result.stdout)
    (evidence/(label+'.stderr.txt')).write_text(result.stderr)
    receipt={'label':label,'command':command,'cwd':str(cwd),'exitCode':result.returncode,'elapsedSeconds':round(time.monotonic()-started,3),'expectedSuccess':expect_success,'stdout':label+'.stdout.txt','stderr':label+'.stderr.txt'}
    results.append(receipt)
    (evidence/'dotnet-mutation-controls.json').write_text(json.dumps(results,indent=2)+'\n')
    if not expect_success and ('Errors: 0, Failed: 1' not in result.stdout or 'Assert.' not in result.stdout):
        raise RuntimeError('Mutation did not reach the expected assertion: '+label+'\n'+result.stdout[-3000:])
    if (result.returncode == 0) != expect_success: raise RuntimeError('Unexpected mutation result: '+label+'\n'+result.stdout[-3000:]+result.stderr[-3000:])
with tempfile.TemporaryDirectory(prefix='mcpcli-pass3-dotnet-mutations-') as directory:
    snapshot=pathlib.Path(directory)
    for name in ('src','tests'):
        shutil.copytree(root/name,snapshot/name,ignore=shutil.ignore_patterns('bin','obj'))
    shutil.copytree(root/'tools/live-topology',snapshot/'tools/live-topology',ignore=shutil.ignore_patterns('__pycache__'))
    for name in ('Directory.Build.props','Directory.Packages.props','global.json','.gitmodules','.editorconfig','Hexalith.McpCli.slnx'):
        shutil.copyfile(root/name,snapshot/name)
    (snapshot/'references').mkdir()
    (snapshot/'references/Hexalith.Builds').symlink_to(root/'references/Hexalith.Builds',target_is_directory=True)
    configuration=snapshot/'tests/Hexalith.McpCli.AppHost/TopologyConfiguration.cs'
    text=configuration.read_text()
    guard='\n                || !Path.GetFullPath(actual).Equals(Path.GetFullPath(checkout),\n                    OperatingSystem.IsWindows() ? StringComparison.OrdinalIgnoreCase : StringComparison.Ordinal)'
    if guard not in text: raise RuntimeError('Physical-root guard was not found')
    configuration.write_text(text.replace(guard,''))
    prerequisite=snapshot/'tests/Hexalith.McpCli.Integration.Tests/TopologyPrerequisites.cs'
    text=prerequisite.read_text()
    guard='            if (process.ExitCode != 0 || !(await output.ConfigureAwait(false)).Contains("CLI version:", StringComparison.Ordinal))\n                return "Dapr CLI \'--version\' did not report an installed CLI.";\n'
    if guard not in text: raise RuntimeError('CLI-version guard was not found')
    prerequisite.write_text(text.replace(guard,''))
    execute('dotnet-mutated-build',['dotnet','build','tests/Hexalith.McpCli.Manifest.Tests/Hexalith.McpCli.Manifest.Tests.csproj','--configuration','Release','-warnaserror'],snapshot,True)
    assembly=snapshot/'tests/Hexalith.McpCli.Manifest.Tests/bin/Release/net10.0/Hexalith.McpCli.Manifest.Tests.dll'
    execute('physical-root-guard-removal',['dotnet',str(assembly),'-method','*LinkedReferencesParentIsNotAQualifiedCheckout'],snapshot)
    execute('cli-version-guard-removal',['dotnet',str(assembly),'-method','*MissingDaprProducesStandardSkipAndNeverClaimsLiveSuccess'],snapshot)
    component=snapshot/'tests/Hexalith.McpCli.AppHost/DaprComponents/statestore.yaml'
    original=json.loads(component.read_text())
    for label in ('actor-state-disabled','parties-scope-removed'):
        altered=json.loads(json.dumps(original))
        if label == 'actor-state-disabled':
            next(item for item in altered['spec']['metadata'] if item['name']=='actorStateStore')['value']='false'
        else: altered['scopes'].remove('parties')
        component.write_text(json.dumps(altered,indent=2)+'\n')
        execute(label,['dotnet',str(assembly),'-class','Hexalith.McpCli.Manifest.Tests.TopologyDaprComponentTests'],snapshot)
print('Four of four focused .NET guard/component mutations rejected in a disposable source snapshot.')
