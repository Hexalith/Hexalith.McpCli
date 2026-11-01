import hashlib, importlib.util, json, os
from pathlib import Path
import shlex, subprocess, sys, tempfile
root=Path('/home/administrator/projects/hexalith/mcpcli')
sys.path.insert(0,str(root/'scripts'))
from paired_release import module, write_new
output=Path('/tmp/mcpcli-418-readme-verification-final')
output.mkdir(exist_ok=False)
checks=[]
with tempfile.TemporaryDirectory(prefix='mcpcli-418-profile-') as temporary:
    private=Path(temporary)
    tool=private/'hexalith'
    tool.write_text('#!/bin/sh\nexec dotnet '+shlex.quote(str(root/'src/Hexalith.McpCli/bin/Release/net10.0/Hexalith.McpCli.dll'))+' "$@"\n')
    tool.chmod(0o700)
    env={k:v for k,v in os.environ.items() if not k.startswith(('EVENTSTORE_', 'MCPCLI_'))}
    env['MCPCLI_HOME']=str(private/'home')
    def execute(label,*arguments):
        run=subprocess.run([str(tool),*arguments],cwd=private,env=env,capture_output=True)
        (output/(label+'.stdout.txt')).write_bytes(run.stdout)
        (output/(label+'.stderr.txt')).write_bytes(run.stderr)
        assert run.returncode==0,(label,run.stderr)
        assert not run.stderr,(label,run.stderr)
        checks.append(label)
        return json.loads(run.stdout) if arguments[0]!='--version' else run.stdout.decode().strip()
    version=execute('version','--version')
    modules=execute('modules','modules','--strict')
    assert {x['name']:x['operationCount'] for x in modules['modules']}=={'parties':7,'tenants':14},modules
    for name in ('parties','tenants'):
        operations=execute('operations-'+name,'operations',name)
        (output/('operations-'+name+'.json')).write_text(json.dumps(operations)+'\n')
        for operation in operations['operations']:
            document=execute('describe-'+operation['name'],'describe',operation['name'])
            (output/('describe-'+operation['name']+'.json')).write_text(json.dumps(document)+'\n')
    execute('profile-add','config','profile','add','operator','--url','http://127.0.0.1:18170')
    tenant="fixture tenant $(never-run) 'quoted'"
    actor="fixture actor $USER $(never-run)"
    execute('tenant-set','config','set','operator','tenant',tenant)
    execute('actor-set','config','set','operator','actor',actor)
    current=execute('profile-current','config','current','--profile','operator')
    assert current['tenant']==tenant and current['actor']==actor,current
    execute('profile-renew','config','profile','add','operator','--url','http://127.0.0.1:18170','--token','synthetic-local-token')
    current=execute('profile-after-renew','config','current','--profile','operator')
    assert current['tenant'] is None and current['actor'] is None,current
    assert 'synthetic-local-token' not in json.dumps(current),current
    execute('tenant-renew','config','set','operator','tenant',tenant)
    execute('actor-renew','config','set','operator','actor',actor)
    captures=output/'discovery';captures.mkdir()
    (captures/'modules.json').write_text(json.dumps(modules)+'\n')
    for path in output.glob('operations-*.json'):
        (captures/path.name).write_bytes(path.read_bytes())
    for path in output.glob('describe-*.json'):
        (captures/path.name).write_bytes(path.read_bytes())
    module('smoke-paired-tool').mcp_smoke(tool,env,private,output,captures,modules)
    checks.append('actual-stdio-initialize-tools-and-discovery-parity')
readme=(root/'README.md').read_text()
assert 'HANDOFF, VERSION, TENANT or ACTOR' in readme
assert 'four placeholder words' in readme
assert not __import__('re').search(r'\]\((?!https?://|#)[^)]+\)', readme)
checks.extend(['prompt-requires-literal-version-substitution','all-packed-readme-links-absolute-or-local-anchor'])
write_new(output/'receipt.json',{'schema':'mcpcli-readme-local-verification/v1','readme_sha256':hashlib.sha256(readme.encode()).hexdigest(),
 'built_tool_version':version,'status':'passed','checks':checks,'live_gateway_calls':0,'actual_gui_sessions':0,
 'limitation':'Built CLI/profile/discovery/stdio checks only. No fresh accepted package installation, hosted staging or client acceptance.'})
print(len(checks),'checks passed')
