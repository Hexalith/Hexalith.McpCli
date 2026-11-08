import json, os, pathlib, subprocess, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[4]
OUT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools/live-topology'))
from ci import sanitized
sys.path.insert(0, str(ROOT / 'tools/conformance-vectors/v1'))
from run_loopback import _JsonRpcClient
out=OUT
with tempfile.TemporaryDirectory(prefix='mcpcli-schema-probe-') as home:
    environment={k:v for k,v in os.environ.items() if not k.startswith('EVENTSTORE_')}
    environment['MCPCLI_HOME']=home
    environment['MCPCLI_STDIO_PROFILE_PATH']=str(pathlib.Path(home)/'profiles.json')
    process=subprocess.Popen(['dotnet',str(ROOT / 'tests/fixtures/StdioHost/bin/Release/net10.0/Hexalith.McpCli.StdioHost.dll'),'mcp','--transport','stdio'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=environment,cwd=ROOT)
    try:
        client=_JsonRpcClient(process,20)
        client.request('initialize',{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'output-contract-probe','version':'1.0'}})
        client.notify('notifications/initialized',{})
        result=client.request('tools/list',{})['result']
        (out/'advertised-tools.json').write_text(sanitized(json.dumps(result,indent=2))+'\n')
        print('Captured',len(result['tools']),'actual advertised schemas.')
    finally:
        process.stdin.close();process.wait(timeout=20)
        (out/'advertisement-host.stderr.txt').write_text(sanitized(process.stderr.read().decode(errors='replace')))
        assert process.returncode==0,process.returncode
