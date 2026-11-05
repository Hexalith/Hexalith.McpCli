from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json, os, queue, re, subprocess, tempfile, threading
from pathlib import Path
root = Path.cwd()
readme = (root / 'README.md').read_text()
blocks = [json.loads(block) for block in re.findall(r'```json\n([^`]+)\n```', readme) if '"operation":"tenants.get-tenant"' in block]
assert len(blocks) == 2 and blocks[0] == blocks[1]
arguments = {key: value.replace('APPROVED-TENANT', 'readme-probe') for key, value in blocks[1].items()}
requests = []
class Gateway(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.headers.get('Transfer-Encoding', '').lower() == 'chunked':
            body = bytearray()
            while True:
                size = int(self.rfile.readline().strip(), 16)
                if size == 0:
                    self.rfile.readline()
                    break
                body.extend(self.rfile.read(size))
                self.rfile.read(2)
        else:
            body = self.rfile.read(int(self.headers['Content-Length']))
        request = json.loads(body)
        requests.append(request)
        raw = json.dumps({'correlationId': '01J9MZHXT3RKM0VWXRXGSJDATK', 'payload': {'tenantId': 'readme-probe', 'status': 'Active'}, 'success': True}).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)
    def log_message(self, *args): pass
with tempfile.TemporaryDirectory(prefix='mcpcli-4-18-readme-') as temporary:
    env = {key: value for key, value in os.environ.items() if not key.startswith('EVENTSTORE_')}
    env['MCPCLI_HOME'] = temporary
    gateway = ThreadingHTTPServer(('127.0.0.1', 0), Gateway)
    threading.Thread(target=gateway.serve_forever, daemon=True).start()
    command = ['dotnet', str(root / 'src/Hexalith.McpCli/bin/Release/net10.0/Hexalith.McpCli.dll'),
        '--url', f'http://127.0.0.1:{gateway.server_port}', '--token', 'synthetic-readme-token', '--tenant', 'readme-probe']
    try:
        cli = subprocess.run([*command, 'query', arguments['operation'], '--aggregate-id', arguments['aggregateId'],
            '--payload', arguments['payload']], env=env, text=True, capture_output=True, timeout=30)
        assert cli.returncode == 0, (cli.stdout, cli.stderr)
        cli_document = json.loads(cli.stdout)
        assert cli_document['tenant'] == 'readme-probe' and cli_document['document'] == {'tenantId': 'readme-probe', 'status': 'Active'}
        child = subprocess.Popen([*command, 'mcp', '--transport', 'stdio'], env=env, text=True,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        messages = queue.Queue()
        def read():
            for line in child.stdout: messages.put(json.loads(line))
        threading.Thread(target=read, daemon=True).start()
        def send(document):
            child.stdin.write(json.dumps(document) + '\n')
            child.stdin.flush()
        def response(identity):
            while True:
                document = messages.get(timeout=30)
                if document.get('id') == identity:
                    assert 'error' not in document, document
                    return document['result']
        try:
            send({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '2025-06-18', 'capabilities': {}, 'clientInfo': {'name': 'synthetic-readme-probe', 'version': '1'}}})
            response(1)
            send({'jsonrpc': '2.0', 'method': 'notifications/initialized'})
            send({'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call', 'params': {'name': 'run_query', 'arguments': arguments}})
            result = response(2)
            assert result['isError'] is False and json.loads(result['content'][0]['text']) == result['structuredContent'], result
            assert result['structuredContent']['tenant'] == 'readme-probe' and result['structuredContent']['document'] == {'tenantId': 'readme-probe', 'status': 'Active'}, result
            child.stdin.close()
            assert child.wait(timeout=15) == 0
        finally:
            if child.poll() is None:
                child.kill()
                child.wait(timeout=5)
    finally:
        gateway.shutdown()
        gateway.server_close()
    assert len(requests) == 2 and all(item['tenant'] == 'readme-probe' and item['aggregateId'] == 'readme-probe' for item in requests)
for name in ('docs/release/canonical-scope-upgrade.md', '_bmad-output/implementation-artifacts/evidence/story-4-18/tenants704-public-artifact/approval.json'):
    assert (root / name).is_file()
assert 'supplied four hashes' not in readme and 'all four package/receipt hashes' not in readme
assert 'Advance Story 4.18' not in readme
assert 'Require result `tenant: "system"`' not in readme
print(json.dumps({'readme_query_examples': 2, 'built_cli_query': 'passed', 'built_mcp_run_query': 'passed',
    'synthetic_loopback_reads': len(requests), 'live_domain_calls': 0, 'new_links_and_hash_guidance': 'passed'}, indent=2))
