#!/usr/bin/env python3
"""Verify README examples with accepted tool against a synthetic loopback, never live acceptance."""
from pathlib import Path
import argparse
import copy
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import queue
import re
import subprocess
import sys
import tempfile
import threading
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'scripts'))


def verify(tool, output):
    assert not output.exists(), 'Preserve earlier evidence'
    output.mkdir(parents=True)
    readme = (ROOT / 'README.md').read_text()
    section = readme.split('## Operator setup with the staged 1.2.0 tool\n', 1)[1].split('## Gateway boundary\n', 1)[0]
    blocks = re.findall(r'```(\w+)\n(.*?)```', section, re.S)
    json_blocks = [json.loads(body) for language, body in blocks if language == 'json']
    assert len(json_blocks) == 5
    desktop, vscode, tenant_args, command_args, party_args = json_blocks
    assert desktop['mcpServers']['hexalith']['args'] == vscode['servers']['hexalith']['args'] == ['mcp', '--transport', 'stdio', '--profile', 'operator']
    assert desktop['mcpServers']['hexalith']['command'].startswith('/') and vscode['servers']['hexalith']['type'] == 'stdio'
    xml = next(body for language, body in blocks if language == 'xml')
    assert ET.fromstring(xml).find('packageSources/clear') is not None
    assert ET.fromstring(xml).find('fallbackPackageFolders/clear') is not None
    token_script = next(body for language, body in blocks if language == 'python')
    selected = 'mcpcli-417-offline'; party = 'party-417-offline-01'
    arguments = [json.loads(json.dumps(item).replace('mcpcli-417-SELECTED', selected).replace('party-417-CLIENT-ATTEMPT', party)
        .replace('email-417-CLIENT-ATTEMPT', 'email-417-offline-01').replace('external-417-CLIENT-ATTEMPT', 'external-417-offline-01'))
        for item in [tenant_args, command_args, party_args]]
    tenant_args, command_args, party_args = arguments
    vectors = ROOT / 'tools/conformance-vectors/v1/modules'
    tenant_response = json.loads((vectors / 'Hexalith.Tenants.Contracts/get-tenant.vector.json').read_text())['invocation']['scriptedResponse']['body']
    party_response = json.loads((vectors / 'Hexalith.Parties.Contracts/get-party.vector.json').read_text())['invocation']['scriptedResponse']['body']
    tenant_response['payload'].update(tenantId=selected)
    party_response['payload'].update(id=party, personDetails={'firstName':'Operator','lastName':'Setup'},
        contactChannels=[{'id':'email-417-offline-01','type':'Email','value':'operator@example.test','isPreferred':True}],
        identifiers=[{'id':'external-417-offline-01','type':'Other','value':'operator-setup'}])
    requests = []
    class Gateway(BaseHTTPRequestHandler):
        def log_message(self, *unused): pass
        def do_POST(self):
            if self.headers.get('Transfer-Encoding', '').lower() == 'chunked':
                raw = bytearray()
                while True:
                    size = int(self.rfile.readline().split(b';', 1)[0].strip(), 16)
                    if size == 0:
                        while self.rfile.readline().strip(): pass
                        break
                    raw.extend(self.rfile.read(size)); self.rfile.read(2)
            else:
                raw = self.rfile.read(int(self.headers.get('Content-Length', '0')))
            body = json.loads(raw)
            requests.append({'path':self.path,'body':body})
            if self.path == '/api/v1/commands':
                response = {'messageId':body['messageId'],'correlationId':body['correlationId']}; status = 202
            elif body['domain'] == 'tenants':
                response = tenant_response; status = 200
            else:
                response = party_response; status = 200
            data = json.dumps(response).encode(); self.send_response(status); self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    server = ThreadingHTTPServer(('127.0.0.1',0), Gateway)
    thread = threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    with tempfile.TemporaryDirectory(prefix='mcpcli-417-readme-') as private:
        env = {k:v for k,v in os.environ.items() if not k.startswith(('EVENTSTORE_','MCPCLI_'))}
        env['MCPCLI_HOME'] = private
        def cli(name, args):
            run = subprocess.run([str(tool),*args],env=env,capture_output=True,timeout=30)
            (output/(name+'.stdout.txt')).write_bytes(run.stdout);(output/(name+'.stderr.txt')).write_bytes(run.stderr)
            assert run.returncode == 0 and not run.stderr, (name,run.returncode)
            return json.loads(run.stdout)
        cli('profile-add',['config','profile','add','operator','--url',f'http://127.0.0.1:{server.server_port}'])
        cli('profile-tenant',['config','set','operator','tenant',selected])
        cli('profile-actor',['config','set','operator','actor','operator-offline'])
        wrapper = 'import getpass\ngetpass.getpass=lambda prompt: "synthetic-offline-token"\nexec('+repr(token_script)+')'
        result = subprocess.run([sys.executable,'-c',wrapper],env=env,capture_output=True,timeout=10)
        assert result.returncode == 0 and not result.stdout and not result.stderr
        current = cli('profile-current',['config','current','--profile','operator'])
        assert current['tenant'] == selected and current['actor'] == 'operator-offline' and current['token'] != 'synthetic-offline-token'
        child = subprocess.Popen([str(tool),'mcp','--transport','stdio','--profile','operator'],env=env,
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        lines = queue.Queue(); transcript = []
        def reader():
            for line in child.stdout: lines.put(line)
        reader_thread = threading.Thread(target=reader,daemon=True);reader_thread.start()
        def request(identity, method, parameters):
            document = {'jsonrpc':'2.0','id':identity,'method':method,'params':parameters}
            transcript.append({'direction':'client','document':document})
            child.stdin.write((json.dumps(document)+'\n').encode());child.stdin.flush()
            while True:
                response = json.loads(lines.get(timeout=30));transcript.append({'direction':'server','document':response})
                if response.get('id') == identity:
                    assert 'error' not in response, response
                    return response['result']
        try:
            request(1,'initialize',{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'README-offline-verifier','version':'1'}})
            child.stdin.write(b'{"jsonrpc":"2.0","method":"notifications/initialized"}\n');child.stdin.flush()
            tools = request(2,'tools/list',{})
            assert [t['name'] for t in tools['tools']] == ['list_modules','list_operations','describe_operation','send_command','run_query']
            identity = 3
            for name,args in [('list_modules',{}),('list_operations',{'module':'tenants'}),('list_operations',{'module':'parties'}),
                *[('describe_operation',{'operation':op}) for op in ['tenants.get-tenant','parties.create-party','parties.get-party']],
                ('run_query',tenant_args),('send_command',command_args),('run_query',party_args)]:
                result = request(identity,'tools/call',{'name':name,'arguments':args});identity+=1
                assert result['isError'] is False and json.loads(result['content'][0]['text']) == result['structuredContent']
                document = result['structuredContent']
                if args.get('operation') == 'tenants.get-tenant' and name == 'run_query': assert document['tenant'] == 'system' and document['document']['tenantId'] == selected
                if name == 'send_command': assert document['status'] == 'accepted' and document['tenant'] == selected and document['aggregateId'] == party
                if args.get('operation') == 'parties.get-party' and name == 'run_query': assert document['tenant'] == selected and document['document'] == party_response['payload']
            child.stdin.close();child.wait(timeout=15);assert child.returncode == 0
            diagnostics = child.stderr.read()
            (output/'mcp.stderr.txt').write_bytes(diagnostics)
            assert b'synthetic-offline-token' not in diagnostics
        finally:
            if child.poll() is None: child.kill();child.wait(timeout=15)
    server.shutdown();server.server_close();thread.join(timeout=5)
    assert len(requests) == 3 and sum(r['path']=='/api/v1/commands' for r in requests) == 1
    assert requests[0]['body']['tenant'] == 'system' and requests[1]['body']['tenant'] == requests[2]['body']['tenant'] == selected
    assert requests[1]['body']['domain'] == 'party' and requests[1]['body']['payload'] == json.loads(command_args['payload'])
    assert requests[2]['body']['entityId'] == party
    (output/'synthetic-mcp-transcript.json').write_text(json.dumps(transcript,indent=2)+'\n')
    (output/'synthetic-gateway-requests.json').write_text(json.dumps(requests,indent=2)+'\n')
    receipt = {'status':'passed-offline-only','readmeSha256':hashlib.sha256((ROOT/'README.md').read_bytes()).hexdigest(),
        'tool':str(tool),'checks':['JSON client configurations','local-only XML configuration','private token prompt in isolated profile',
        'CLI profile verbs and masked sources','README MCP argument objects against synthetic loopback','system/selected-tenant routing','single command submission'],
        'limits':'Synthetic loopback only; no actual Claude/VS Code session, live persisted Party or independent operator timing.'}
    (output/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--tool',required=True,type=Path);parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();verify(args.tool.absolute(),args.output.absolute())
