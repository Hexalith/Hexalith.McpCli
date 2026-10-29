"""Exercise installed-smoke assertions and retained failure diagnostics without hosted services."""

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
from paired_release import module


class PairedSmokeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.smoke = module('smoke-paired-tool')

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


if __name__ == '__main__':
    unittest.main()
