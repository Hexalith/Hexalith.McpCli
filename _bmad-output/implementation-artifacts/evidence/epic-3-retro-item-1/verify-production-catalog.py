import json, os, pathlib, subprocess, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[4]
OUT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools/live-topology'))
from ci import sanitized
sys.path.insert(0, str(ROOT / 'tools/conformance-vectors/v1'))
from run_loopback import _JsonRpcClient
from jsonschema import Draft202012Validator
out=OUT
with tempfile.TemporaryDirectory(prefix='mcpcli-production-schema-') as home:
    environment={k:v for k,v in os.environ.items() if not k.startswith('EVENTSTORE_')}
    environment['MCPCLI_HOME']=home
    process=subprocess.Popen(['dotnet',str(ROOT / 'src/Hexalith.McpCli/bin/Release/net10.0/Hexalith.McpCli.dll'),'mcp','--transport','stdio'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=environment,cwd=ROOT)
    documents=[]
    try:
        client=_JsonRpcClient(process,20)
        client.request('initialize',{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'production-output-contract','version':'1.0'}})
        client.notify('notifications/initialized',{})
        tools=client.request('tools/list',{})['result']['tools']
        schemas={tool['name']:tool['outputSchema'] for tool in tools}
        validators={name:Draft202012Validator(schema) for name,schema in schemas.items()}
        def call(name,arguments):
            result=client.request('tools/call',{'name':name,'arguments':arguments})['result']
            assert not result.get('isError'),result
            document=result['structuredContent']
            assert document==json.loads(result['content'][0]['text'])
            errors=list(validators[name].iter_errors(document))
            assert not errors,'\n'.join(str(e) for e in errors)
            documents.append({'tool':name,'arguments':arguments,'document':document})
            return document
        modules=call('list_modules',{})['modules']
        operations=[]
        examples=0
        for module in modules:
            for operation in call('list_operations',{'module':module['name']})['operations']:
                description=call('describe_operation',{'operation':operation['name']})
                assert isinstance(description['schema'],dict),operation['name']
                if 'example' in description:
                    assert isinstance(description['example'],dict),operation['name']
                    examples+=1
                operations.append(operation['name'])
        (out/'production-discovery.json').write_text(sanitized(json.dumps({'operations':operations,'examples':examples,'documents':documents,'schemas':schemas},indent=2))+'\n')
        print(f'Built production catalog: {len(modules)} modules, {len(operations)} operation descriptions ({examples} examples); all {len(documents)} discovery documents validate against actual advertisements and match structured/text JSON. Every embedded schema/example root is an object. No live services used.')
    finally:
        process.stdin.close();process.wait(timeout=20)
        (out/'production-host.stderr.txt').write_text(sanitized(process.stderr.read().decode(errors='replace')))
        assert process.returncode==0,process.returncode
