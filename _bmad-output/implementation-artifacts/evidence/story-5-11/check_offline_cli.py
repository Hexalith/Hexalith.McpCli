#!/usr/bin/env python3
"""Probe published 2.0.1 offline, without profiles, credentials or Gateway calls."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[4]
E = Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts'))
from evidence_redaction import sanitized_xml


def retained(data):
    return sanitized_xml(data.decode(errors='replace')).encode()


TOOLS = {'list_modules','list_operations','describe_operation','send_command','run_query'}
OPERATIONS = {
    'tenants': {'add-user-to-tenant':'write','change-user-role':'write','create-tenant':'write','disable-tenant':'write','enable-tenant':'write','get-tenant':'read','get-tenant-audit':'read','get-tenant-users':'read','get-user-tenants':'read','list-tenants':'read','remove-tenant-configuration':'write','remove-user-from-tenant':'write','set-tenant-configuration':'write','update-tenant':'write'},
    'parties': {'create-party':'write','deactivate-party':'write','get-party':'read','list-parties':'read','reactivate-party':'write','search-parties':'read','update-party':'write'},
}
UNKNOWN = {'error':{'code':'unknown_operation','operation':'folders.unavailable','suggestions':['parties.update-party','parties.create-party','parties.get-party']}}


def require(condition,message):
    if not condition: raise ValueError(message)


def validate_probe(name,result):
    require(result.returncode == (2 if name=='unknown' else 0),name+': unexpected exit code')
    if name == 'unknown':
        require(result.stdout == (json.dumps(UNKNOWN,indent=2)+'\n').encode() and result.stderr == b'', 'unknown: complete error document/stdout/stderr mismatch')
    elif name in {'modules','tenants','parties','describe'}:
        require(result.stderr == b'',name+': unexpected discovery stderr')
        document = json.loads(result.stdout)
        require(isinstance(document,dict) and 'error' not in document,name+': discovery result required')
        if name == 'modules':
            modules=document.get('modules',[])
            require(len(modules)==2 and {m.get('name'):m.get('operationCount') for m in modules}=={'parties':7,'tenants':14} and all(m.get('description') for m in modules),'modules: expected published cohort required')
        elif name in OPERATIONS:
            operations=document.get('operations',[])
            expected={name+'.'+op:kind for op,kind in OPERATIONS[name].items()}
            require(document.get('module')==name and len(operations)==len(expected) and {r.get('name'):r.get('kind') for r in operations}==expected and all(r.get('description') for r in operations),name+': expected operation names/kinds/descriptions required')
        else:
            require(document.get('name')=='tenants.list-tenants' and document.get('kind')=='read' and document.get('description') and isinstance(document.get('schema'),dict) and document['schema'].get('properties',{}).keys()=={'Cursor','PageSize'} and document.get('envelope',{}).get('platformScope')=='platform:tenants' and document.get('submittable') is False and document.get('reason')=='configuration_invalid','describe: expected typed offline discovery required')
    else:
        require(result.stdout and result.stderr == b'' and b'error' not in result.stdout[:20].lower(),name+': help output required')


def validate_tools(response):
    tools=response.get('result',{}).get('tools',[])
    require(response.get('id')==2 and response.get('jsonrpc')=='2.0' and len(tools)==5 and {t.get('name') for t in tools}==TOOLS and all(isinstance(t.get('inputSchema'),dict) for t in tools),'stdio: exact generic tool names and schemas required')
    return tools


class Responses:
    """Read chunks under one absolute deadline, including partial JSON lines."""
    def __init__(self,stream):
        self.stream,self.pending,self.output=stream,b'',[]

    def receive(self,request_id,timeout=30):
        deadline=time.monotonic()+timeout
        while True:
            while b'\n' in self.pending:
                line,self.pending=self.pending.split(b'\n',1)
                response=json.loads(line)
                require(isinstance(response,dict),'stdio response must be a JSON object')
                if response.get('id')==request_id:return response
            remaining=deadline-time.monotonic()
            if remaining<=0 or not select.select([self.stream],[],[],remaining)[0]:raise ValueError('stdio response deadline exceeded')
            chunk=os.read(self.stream.fileno(),65536)
            if not chunk:raise ValueError('stdio closed before discovery response')
            self.output.append(chunk);self.pending+=chunk
            require(len(self.pending)<=1024*1024,'stdio response exceeds buffer bound')


def stop_process(process,timeout=2):
    if process.stdin and not process.stdin.closed:process.stdin.close()
    try: process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill();process.wait(timeout=timeout)
    if process.stdout:process.stdout.close()


def install_tool(command, environment, evidence):
    try:
        result = subprocess.run(command,capture_output=True,env=environment,timeout=120)
    except subprocess.TimeoutExpired as error:
        (evidence/'offline-install.stdout.txt').write_bytes(retained(error.stdout or b''))
        (evidence/'offline-install.stderr.txt').write_bytes(retained(error.stderr or b''))
        raise ValueError('Published CLI install timed out; see offline-install streams') from error
    (evidence/'offline-install.stdout.txt').write_bytes(retained(result.stdout))
    (evidence/'offline-install.stderr.txt').write_bytes(retained(result.stderr))
    require(result.returncode == 0,'Published CLI install failed; see offline-install streams')


def discover_stdio(command, environment, scratch, evidence):
    # Discovery over stdio only: initialize, tools/list, then end input. No tool invocation.
    requests = [{'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'story-5-11-offline','version':'1.0.0'}}},{'jsonrpc':'2.0','method':'notifications/initialized'},{'jsonrpc':'2.0','id':2,'method':'tools/list','params':{}}]
    responses = None
    with tempfile.TemporaryFile(dir=scratch) as diagnostics:
        try:
            process = subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=diagnostics,env=environment)
            responses=Responses(process.stdout)
            try:
                for request in requests:
                    process.stdin.write((json.dumps(request)+'\n').encode());process.stdin.flush()
                    if 'id' not in request: continue
                    response=responses.receive(request['id'])
                    if request['id']==1:
                        require(response.get('result',{}).get('protocolVersion')=='2025-06-18' and response['result'].get('serverInfo',{}).get('name')=='hexalith','stdio: valid initialization required')
                    else:tools=validate_tools(response)
            finally:
                stop_process(process)
        finally:
            stdout = b''.join(responses.output) if responses is not None else b''
            retained_stdout = retained(stdout)
            (evidence/'offline-stdio.stdout.txt').write_bytes(retained_stdout)
            diagnostics.seek(0)
            (evidence/'offline-stdio.stderr.txt').write_bytes(retained(diagnostics.read()))
    require(process.returncode==0,'stdio: clean shutdown required')
    return {'name':'stdio-discovery','command':['hexalith','mcp','--transport','stdio'],
            'exitCode':process.returncode,'tools':[t['name'] for t in tools],
            'rawStdoutSha256':hashlib.sha256(stdout).hexdigest(),
            'stdoutSha256':hashlib.sha256(retained_stdout).hexdigest(),
            'stderrSha256':hashlib.sha256((evidence/'offline-stdio.stderr.txt').read_bytes()).hexdigest()}


def collect(evidence):
    records = []
    with tempfile.TemporaryDirectory(prefix='mcpcli-offline-') as temporary:
        scratch = Path(temporary)
        environment = {k:v for k,v in os.environ.items() if not k.startswith(('EVENTSTORE_','MCPCLI_','NUGET_','GH_','GITHUB_'))}
        environment.update(NUGET_PACKAGES=str(scratch/'packages'),DOTNET_CLI_HOME=str(scratch/'dotnet'),MCPCLI_HOME=str(scratch/'profile'),DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1',DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_GENERATE_ASPNET_CERTIFICATE='false')
        install = ['dotnet','tool','install','--tool-path',str(scratch/'tool'),'Hexalith.McpCli','--version','2.0.1']
        install_tool(install,environment,evidence)
        tool = str(scratch/'tool/hexalith')
        cases = [('modules',['modules']),('tenants',['operations','tenants']),('parties',['operations','parties']),('describe',['describe','tenants.list-tenants']),('config-help',['config','--help']),('query-help',['query','--help']),('send-help',['send','--help']),('mcp-help',['mcp','--help']),('unknown',['describe','folders.unavailable'])]
        for name,args in cases:
            result = subprocess.run([tool,*args],capture_output=True,env=environment,timeout=30)
            stdout, stderr = retained(result.stdout), retained(result.stderr)
            (evidence/f'offline-{name}.stdout.txt').write_bytes(stdout)
            (evidence/f'offline-{name}.stderr.txt').write_bytes(stderr)
            records.append({'name':name,'command':['hexalith',*args],'exitCode':result.returncode,'rawStdoutSha256':hashlib.sha256(result.stdout).hexdigest(),'rawStderrSha256':hashlib.sha256(result.stderr).hexdigest(),'stdoutSha256':hashlib.sha256(stdout).hexdigest(),'stderrSha256':hashlib.sha256(stderr).hexdigest()})
            validate_probe(name,result)
        records.append(discover_stdio([tool,'mcp','--transport','stdio'],environment,scratch,evidence))
        packages = [{'path':str(p.relative_to(scratch)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(scratch.rglob('*.nupkg')) if p.name.startswith('hexalith.mcpcli.')]
    return {'source':'Published tool 2.0.1','scope':'Offline discovery/help only; no query/command execution or tools/call, profile write or Gateway call','records':records,'packages':packages}


def run_probe(output):
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.run-', dir=output) as preparation:
        staging = Path(preparation)
        try:
            manifest = collect(staging)
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            failed = staging.rename(output/f'failed-{staging.name.removeprefix(".run-")}')
            raise ValueError(f'{error}. Retained evidence in {failed}') from error
        (staging/'offline-cli.json').write_text(json.dumps(manifest,indent=2)+'\n')
        return staging.rename(output/staging.name.removeprefix('.'))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=E/'offline-runs', help='Parent directory for separate probe runs')
    try:
        evidence = run_probe(parser.parse_args(argv).output)
    except (OSError, ValueError) as error:
        print(f'FAIL: {error}', file=sys.stderr)
        return 1
    print(f'PASS: published 2.0.1 offline discovery/help, safe unknown-operation refusal and five generic stdio tools. Evidence in {evidence}')
    return 0


if __name__ == '__main__': sys.exit(main())
