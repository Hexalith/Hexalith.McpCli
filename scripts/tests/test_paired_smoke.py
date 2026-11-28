"""Exercise installed-smoke assertions and retained failure diagnostics without hosted services."""

import importlib
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class PairedSmokeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.smoke = importlib.import_module('smoke-paired-tool')

    def test_protocol_requires_response_or_notification_envelopes(self):
        valid = [
            {'jsonrpc': '2.0', 'id': 1, 'result': {}},
            {'jsonrpc': '2.0', 'id': 'one', 'error': {'code': -32601, 'message': 'missing'}},
            {'jsonrpc': '2.0', 'method': 'notifications/message', 'params': {'level': 'info'}},
        ]
        for document in valid:
            self.assertEqual(self.smoke.protocol_document(json.dumps(document)), document)
        invalid = [[], {'jsonrpc': '2.0', 'debug': 'not protocol'},
                   {'jsonrpc': '2.0', 'id': 1}, {'jsonrpc': '2.0', 'id': True, 'result': {}},
                   {'jsonrpc': '2.0', 'id': 1, 'result': {}, 'debug': 'extra'},
                   {'jsonrpc': '2.0', 'id': 1, 'result': {}, 'error': {}},
                   {'jsonrpc': '2.0', 'id': 1, 'error': {'code': 'bad', 'message': 'missing'}},
                   {'jsonrpc': '2.0', 'method': 'notifications/message', 'params': 'debug'},
                   {'jsonrpc': '2.0', 'id': 2, 'method': 'server/request'}]
        for document in invalid:
            with self.subTest(document=document), self.assertRaises(ValueError):
                self.smoke.protocol_document(json.dumps(document))

    def test_unrelated_messages_share_one_monotonic_request_deadline(self):
        class Messages:
            def __init__(self): self.timeouts = []
            def get(self, timeout):
                self.timeouts.append(timeout)
                if len(self.timeouts) > 2:
                    raise AssertionError('The request restarted its deadline after unrelated output.')
                return b'{"jsonrpc":"2.0","method":"notifications/message","params":{}}\n'
        messages = Messages()
        sent = []
        with patch.object(self.smoke.time, 'monotonic', side_effect=[100, 100, 130, 160]):
            with self.assertRaisesRegex(ValueError, '60 second deadline'):
                self.smoke.request_mcp(sent.append, messages, 1, 'initialize', {})
        self.assertEqual(messages.timeouts, [60, 30])
        self.assertEqual(len(sent), 1)

    def test_timeout_retains_partial_channels_and_command_outcome(self):
        error = subprocess.TimeoutExpired(['tool', 'modules'], 120, output=b'partial stdout\n', stderr=b'partial stderr\n')
        with patch.object(self.smoke.subprocess, 'run', side_effect=error) as run:
            with self.assertRaises(subprocess.TimeoutExpired):
                self.smoke.execute_command(self.root, self.root, {}, 'modules', ['tool', 'modules'])
        self.assertEqual(run.call_count, 1)
        self.assertEqual(run.call_args.kwargs['timeout'], 120)
        self.assertEqual((self.root / 'modules.stdout.txt').read_bytes(), b'partial stdout\n')
        self.assertEqual((self.root / 'modules.stderr.txt').read_bytes(), b'partial stderr\n')
        self.assertEqual(json.loads((self.root / 'modules.command.json').read_text()),
                         {'argv': ['tool', 'modules'], 'exit_code': None, 'outcome': 'timeout', 'timeout_seconds': 120})
        self.assertFalse((self.root / 'smoke.json').exists())

    def config_fixture(self, no_op=None, wrong_document=False):
        path = self.root / 'mcpcli.json'
        profile = {'url': 'http://127.0.0.1:1', 'token': 'staged-private-token'}
        stored = {'version': 1, 'profiles': {}}
        path.write_text(json.dumps(stored))
        calls = []
        def execute(name, argv):
            calls.append(name)
            state = json.loads(json.dumps(stored))
            if name == 'config-add':
                state['profiles']['staged'] = profile
                document = {'name': 'staged', 'activeProfile': None}
            elif name == 'config-use':
                state['activeProfile'] = 'staged'
                document = {'activeProfile': 'staged'}
            elif name == 'config-current':
                document = {'profile': 'staged', 'url': 'http://127.0.0.1:1/', 'token': 'stag***',
                    'tenant': None, 'actor': None, 'allowTenantOverride': False, 'allowedExtensions': [],
                    'format': 'json', 'output': None, 'readOnly': False, 'strict': False,
                    'sources': {key: 'default' for key in ('tenant', 'actor', 'format', 'allowTenantOverride',
                                'readOnly', 'strict', 'output', 'allowedExtensions')}}
                document['sources'].update(profile='activeProfile', url='profile', token='profile')
                if no_op == name: document['profile'] = None
            elif name == 'config-clear':
                state.pop('activeProfile')
                document = {'activeProfile': None}
            else:
                state['profiles'].pop('staged')
                document = {'name': 'staged', 'activeProfile': None}
            if name != no_op:
                stored.clear()
                stored.update(state)
                path.write_text(json.dumps(stored))
            return subprocess.CompletedProcess(argv, 0, stdout=(json.dumps({} if wrong_document else document) + '\n').encode(), stderr=b'')
        return path, execute, calls

    def test_config_requires_exact_documents_and_every_persisted_transition(self):
        path, execute, calls = self.config_fixture()
        self.smoke.config_smoke('tool', execute, path)
        self.assertEqual(calls, ['config-add', 'config-use', 'config-current', 'config-clear', 'config-remove'])
        self.assertEqual(json.loads(path.read_text()), {'version': 1, 'profiles': {}})
        for name in calls:
            path, execute, _ = self.config_fixture(no_op=name)
            with self.subTest(no_op=name), self.assertRaises(ValueError):
                self.smoke.config_smoke('tool', execute, path)
        path, execute, _ = self.config_fixture(wrong_document=True)
        with self.assertRaisesRegex(ValueError, 'output document'):
            self.smoke.config_smoke('tool', execute, path)

    def mcp_fixture(self, mode):
        captures = self.root / ('captures-' + mode)
        captures.mkdir()
        output = self.root / ('output-' + mode)
        output.mkdir()
        modules = {'modules': [{'name': 'alpha'}, {'name': 'beta'}]}
        documents = {'alpha': {'operations': [{'name': 'alpha.one'}, {'name': 'alpha.two'}]},
                     'beta': {'operations': [{'name': 'beta.one'}]}}
        for name, document in documents.items():
            (captures / ('operations-' + name + '.json')).write_text(json.dumps(document))
            for operation in document['operations']:
                (captures / ('describe-' + operation['name'] + '.json')).write_text(json.dumps(operation))
        script = self.root / ('tool-' + mode)
        script.write_text('#!' + sys.executable + '\n' + '''import json, sys
mode = ''' + repr(mode) + '''
modules = ''' + repr(modules) + '''
operations = ''' + repr(documents) + '''
for line in sys.stdin:
    request = json.loads(line)
    if 'id' not in request: continue
    if mode == 'malformed':
        print('{"jsonrpc":"2.0","debug":"not a notification"}', flush=True)
    method = request['method']
    if method == 'initialize': result = {'protocolVersion': '2025-06-18'}
    elif method == 'tools/list':
        result = {'tools': [{'name': name} for name in ['list_modules', 'list_operations', 'describe_operation', 'send_command', 'run_query']]}
    else:
        parameters = request['params']
        name = parameters['name']
        arguments = parameters['arguments']
        error = False
        if name == 'list_modules': document = modules
        elif name == 'list_operations':
            document = operations[arguments['module']]
            if mode == 'wrong-list' and arguments['module'] == 'beta': document = {'operations': []}
        elif arguments['operation'] == '__missing__':
            document = {'error': {'code': 'unknown_operation'}}
            error = True
        else:
            document = {'name': arguments['operation']}
            if mode == 'wrong-description' and arguments['operation'] == 'alpha.two': document = {'name': 'wrong'}
        result = {'isError': error, 'structuredContent': document, 'content': [{'type': 'text', 'text': json.dumps(document)}]}
    print(json.dumps({'jsonrpc': '2.0', 'id': request['id'], 'result': result}), flush=True)
''')
        script.chmod(0o700)
        return script, output, captures, modules

    def test_mcp_checks_every_operation_list_and_description_and_retains_captures(self):
        tool, output, captures, modules = self.mcp_fixture('passed')
        self.smoke.mcp_smoke(tool, os.environ.copy(), self.root, output, captures, modules)
        expected = {'mcp-tools.json', 'mcp-modules.json', 'mcp-operations-alpha.json', 'mcp-operations-beta.json',
                    'mcp-describe-alpha.one.json', 'mcp-describe-alpha.two.json', 'mcp-describe-beta.one.json'}
        self.assertEqual({path.name for path in captures.glob('mcp-*.json')}, expected)
        self.assertTrue((output / 'mcp.stdout.jsonl').read_bytes())
        self.assertEqual((output / 'mcp.stderr.txt').read_bytes(), b'')
        for mode in ('wrong-list', 'wrong-description', 'malformed'):
            tool, output, captures, modules = self.mcp_fixture(mode)
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                self.smoke.mcp_smoke(tool, os.environ.copy(), self.root, output, captures, modules)
            transcript = (output / 'mcp.stdout.jsonl').read_bytes()
            self.assertTrue(transcript)
            self.assertTrue((output / 'mcp.stderr.txt').is_file())
            self.assertFalse((output / 'smoke.json').exists())
            if mode == 'malformed': self.assertIn(b'not a notification', transcript)

    def test_json_document_requires_utf8_lf_without_cr_or_bom(self):
        self.assertEqual(self.smoke.json_document(b'{"ok":true}\n'), {'ok': True})
        for bad in (b'{"ok":true}', b'{"ok":true}\r\n', b'{"ok":\rtrue}\n', b'\xef\xbb\xbf{"ok":true}\n'):
            with self.subTest(raw=bad), self.assertRaisesRegex(ValueError, 'LF internally'):
                self.smoke.json_document(bad)
        with self.assertRaises(ValueError):
            self.smoke.json_document('{"ok":true}\n'.encode('utf-16-be'))

    def _smoke_fixture(self, mode):
        case_root = self.root / ('smoke-' + mode)
        staging = case_root / 'packages'
        staging.mkdir(parents=True)
        version = '3.0.1'
        sha = 'a' * 40
        for name in (f'Hexalith.McpCli.Abstractions.{version}.nupkg', f'Hexalith.McpCli.{version}.nupkg'):
            (staging / name).write_bytes(b'fake-nupkg-' + name.encode('utf-8'))
        from product_packages import packages as package_digests
        prepared_path = case_root / 'prepared.json'
        prepared_path.write_text(json.dumps({
            'schema': 'mcpcli-product-packages/v1',
            'source_sha': sha,
            'version': version,
            'tool_version': version,
            'packages': package_digests(staging, version),
        }), encoding='utf-8')
        bin_dir = case_root / 'bin'
        bin_dir.mkdir()
        fake_tool = case_root / 'fake_hexalith.py'
        fake_tool.write_text(f'''#!{sys.executable}
import json, os, pathlib, sys
mode = {mode!r}
version = {version!r}
staging = pathlib.Path({str(staging)!r})
args = sys.argv[1:]
modules = {{'modules': [{{'name': 'alpha'}}]}}
ops = {{'operations': [{{'name': 'alpha.one'}}]}}
desc = {{'name': 'alpha.one', 'kind': 'query'}}
expected_err = {{'error': {{'code': 'configuration_invalid', 'message': 'Invalid mcpcli profile file: MCPCLI_HOME must be an absolute directory path.'}}}}

def emit(doc, stream=sys.stdout.buffer, crlf=False, bom=False, no_lf=False):
    raw = json.dumps(doc).encode('utf-8')
    if crlf:
        raw = raw + b'\\r\\n'
    elif not no_lf:
        raw = raw + b'\\n'
    if bom:
        raw = b'\\xef\\xbb\\xbf' + raw
    stream.write(raw)
    stream.flush()

if args == ['--version']:
    if mode == 'bad-version':
        sys.stdout.write('9.9.9\\n')
    else:
        sys.stdout.write(version + '\\n')
    if mode == 'version-stderr':
        sys.stderr.write('unexpected warning\\n')
    raise SystemExit(0)

if args == ['modules']:
    if mode == 'discovery-stderr':
        sys.stderr.write('diag\\n')
    if mode == 'empty-modules':
        emit({{'modules': []}})
    else:
        emit(modules, crlf=(mode == 'discovery-crlf'), bom=(mode == 'discovery-bom'), no_lf=(mode == 'discovery-no-lf'))
    raise SystemExit(0)

if args[:2] == ['operations', 'alpha']:
    emit({{'operations': []}} if mode == 'empty-operations' else ops)
    raise SystemExit(0)

if args[:2] == ['describe', 'alpha.one']:
    if mode == 'describe-stderr':
        sys.stderr.write('describe diag\\n')
    emit(desc)
    raise SystemExit(0)

if args[:2] == ['modules', '--output']:
    target = pathlib.Path(args[2])
    body = json.dumps(modules).encode('utf-8') + b'\\n'
    if mode == 'output-file-mismatch':
        body = b'{{"modules":[]}}\\n'
    if mode != 'output-file-missing':
        target.write_bytes(body)
    if mode == 'output-file-stdout':
        sys.stdout.write('leaked\\n')
    if mode == 'output-file-stderr':
        sys.stderr.write('leaked\\n')
    raise SystemExit(0)

if args == ['modules', '--format', 'table']:
    if mode == 'table-header-mismatch':
        sys.stdout.write('WRONG\\tHEADER\\n')
    else:
        sys.stdout.write('NAME\\tOPERATIONS\\tDESCRIPTION\\nalpha\\t1\\tSample\\n')
    if mode == 'table-stderr':
        sys.stderr.write('table diag\\n')
    raise SystemExit(0)

if args == ['config', 'current'] and os.environ.get('MCPCLI_HOME') == 'relative-secret-home':
    if mode == 'invalid-home-stderr':
        sys.stderr.write('leaked\\n')
    body = {{'error': {{'code': 'wrong'}}}} if mode == 'invalid-home-body' else expected_err
    emit(body, crlf=(mode == 'invalid-home-crlf'))
    raise SystemExit(0 if mode == 'invalid-home-exit' else 2)

if args == ['mcp', '--transport', 'stdio'] and os.environ.get('MCPCLI_HOME') == 'relative-secret-home':
    if mode == 'mcp-invalid-home-stdout':
        sys.stdout.write('polluted\\n')
    body = {{'error': {{'code': 'wrong'}}}} if mode == 'mcp-invalid-home-body' else expected_err
    emit(body, stream=sys.stderr.buffer, crlf=(mode == 'mcp-invalid-home-crlf'))
    raise SystemExit(0 if mode == 'mcp-invalid-home-exit' else 2)

if args and args[0] == 'config':
    home = pathlib.Path(os.environ['MCPCLI_HOME']) / '.eventstore'
    home.mkdir(parents=True, exist_ok=True)
    store = home / 'mcpcli.json'
    state = json.loads(store.read_text()) if store.exists() else {{'version': 1, 'profiles': {{}}}}
    if args[1:3] == ['profile', 'add']:
        state['profiles'][args[3]] = {{'url': args[5], 'token': args[7]}}
        store.write_text(json.dumps(state))
        emit({{'name': args[3], 'activeProfile': state.get('activeProfile')}})
    elif args[1:3] == ['use', '--clear']:
        state.pop('activeProfile', None)
        store.write_text(json.dumps(state))
        emit({{'activeProfile': None}})
    elif args[1] == 'use':
        state['activeProfile'] = args[2]
        store.write_text(json.dumps(state))
        emit({{'activeProfile': args[2]}})
    elif args[1] == 'current':
        sources = {{k: 'default' for k in ('tenant', 'actor', 'format', 'allowTenantOverride', 'readOnly', 'strict', 'output', 'allowedExtensions')}}
        sources.update(profile='activeProfile', url='profile', token='profile')
        emit({{'profile': 'staged', 'url': 'http://127.0.0.1:1/', 'token': 'stag***', 'tenant': None,
              'actor': None, 'allowTenantOverride': False, 'allowedExtensions': [], 'format': 'json',
              'output': None, 'readOnly': False, 'strict': False, 'sources': sources}})
    elif args[1:3] == ['profile', 'remove']:
        state['profiles'].pop(args[3], None)
        store.write_text(json.dumps(state))
        emit({{'name': args[3], 'activeProfile': state.get('activeProfile')}})
    raise SystemExit(0)

if args == ['mcp', '--transport', 'stdio']:
    if mode == 'post-smoke-mutation':
        target_pkg = staging / f'Hexalith.McpCli.{{version}}.nupkg'
        target_pkg.write_bytes(target_pkg.read_bytes() + b'tampered')
    for line in sys.stdin:
        req = json.loads(line)
        if 'id' not in req:
            continue
        method = req['method']
        if method == 'initialize':
            res = {{'protocolVersion': '2025-06-18'}}
        elif method == 'tools/list':
            res = {{'tools': [{{'name': n}} for n in ['list_modules', 'list_operations', 'describe_operation', 'send_command', 'run_query']]}}
        else:
            pname = req['params']['name']
            pargs = req['params']['arguments']
            err = False
            if pname == 'list_modules':
                doc = modules
            elif pname == 'list_operations':
                doc = ops
            elif pargs['operation'] == '__missing__':
                doc = {{'error': {{'code': 'unknown_operation'}}}}
                err = True
            else:
                doc = desc
            res = {{'isError': err, 'structuredContent': doc, 'content': [{{'type': 'text', 'text': json.dumps(doc)}}]}}
        print(json.dumps({{'jsonrpc': '2.0', 'id': req['id'], 'result': res}}), flush=True)
    raise SystemExit(0)
raise SystemExit(1)
''', encoding='utf-8')
        fake_tool.chmod(0o700)
        fake_dotnet = bin_dir / 'dotnet'
        fake_dotnet.write_text(f'''#!{sys.executable}
import pathlib, shutil, sys
args = sys.argv[1:]
if args[:3] == ['tool', 'install', 'Hexalith.McpCli']:
    tool_dir = pathlib.Path(args[args.index('--tool-path') + 1])
    tool_dir.mkdir(parents=True, exist_ok=True)
    dest = tool_dir / 'hexalith'
    shutil.copyfile({str(fake_tool)!r}, dest)
    dest.chmod(0o700)
    raise SystemExit(0)
raise SystemExit(1)
''', encoding='utf-8')
        fake_dotnet.chmod(0o700)
        output = case_root / 'smoke-out'
        return staging, prepared_path, output, str(bin_dir) + os.pathsep + os.environ.get('PATH', '')

    def test_smoke_succeeds_and_derives_checks_dynamically(self):
        staging, prepared_path, output, path_env = self._smoke_fixture('passed')
        with patch.dict(os.environ, {'PATH': path_env}):
            self.smoke.smoke(staging, prepared_path, output)
        receipt = json.loads((output / 'smoke.json').read_text(encoding='utf-8'))
        self.assertEqual(receipt['schema'], 'mcpcli-paired-smoke/v1')
        self.assertEqual(receipt['status'], 'passed')
        self.assertEqual(
            set(receipt['checks']),
            {'version', 'offline-discovery', 'output-file', 'table', 'errors', 'config', 'mcp-protocol', 'json-lf'},
        )
        self.assertEqual(len(receipt['checks']), len(set(receipt['checks'])))
        with patch.dict(os.environ, {'PATH': path_env}):
            with self.assertRaisesRegex(ValueError, 'already exists'):
                self.smoke.smoke(staging, prepared_path, output)

    def test_smoke_refuses_every_contract_violation_without_writing_receipt(self):
        cases = [
            ('bad-version', 'version/channel mismatch'),
            ('version-stderr', 'version/channel mismatch'),
            ('discovery-stderr', 'wrote unexpected diagnostics'),
            ('describe-stderr', 'wrote unexpected diagnostics'),
            ('discovery-crlf', 'LF internally'),
            ('discovery-bom', 'LF internally'),
            ('discovery-no-lf', 'LF internally'),
            ('empty-modules', 'catalog is empty'),
            ('empty-operations', 'has no operations'),
            ('output-file-stdout', 'Output-file bytes/channels'),
            ('output-file-stderr', 'Output-file bytes/channels'),
            ('output-file-missing', 'Output-file bytes/channels'),
            ('output-file-mismatch', 'Output-file bytes/channels'),
            ('table-header-mismatch', 'Table output/channel mismatch'),
            ('table-stderr', 'Table output/channel mismatch'),
            ('invalid-home-exit', 'invalid-home returned 0'),
            ('invalid-home-stderr', 'Invalid home did not fail safely'),
            ('invalid-home-body', 'Invalid home did not fail safely'),
            ('invalid-home-crlf', 'LF internally'),
            ('mcp-invalid-home-exit', 'mcp-invalid-home returned 0'),
            ('mcp-invalid-home-stdout', 'polluted the protocol channel'),
            ('mcp-invalid-home-body', 'polluted the protocol channel'),
            ('mcp-invalid-home-crlf', 'LF internally'),
            ('post-smoke-mutation', 'Staged bytes changed'),
        ]
        for mode, pattern in cases:
            staging, prepared_path, output, path_env = self._smoke_fixture(mode)
            with self.subTest(mode=mode):
                with patch.dict(os.environ, {'PATH': path_env}):
                    with self.assertRaisesRegex(ValueError, pattern):
                        self.smoke.smoke(staging, prepared_path, output)
                self.assertFalse((output / 'smoke.json').exists())


if __name__ == '__main__':
    unittest.main()
