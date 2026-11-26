import contextlib
import hashlib
import importlib.util
import io
import json
import os
import tempfile
from unittest import mock
from pathlib import Path
import subprocess
import sys
import time
import unittest

spec=importlib.util.spec_from_file_location('offline511',Path(__file__).with_name('check_offline_cli.py'))
C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)


class OfflineCliTests(unittest.TestCase):
    def test_captured_published_discovery_and_complete_unknown_streams(self):
        for name in ['modules','tenants','parties','describe','unknown']:
            with self.subTest(name=name):
                C.validate_probe(name,subprocess.CompletedProcess([],2 if name=='unknown' else 0,(C.E/f'offline-{name}.stdout.txt').read_bytes(),(C.E/f'offline-{name}.stderr.txt').read_bytes()))
        wrong=json.dumps({'error':{'code':'configuration_invalid'}}).encode()
        with self.assertRaisesRegex(ValueError,'complete error document'):C.validate_probe('unknown',subprocess.CompletedProcess([],2,wrong,b''))
        for stdout,stderr in [(json.dumps(C.UNKNOWN).encode(),b''),((json.dumps(C.UNKNOWN,indent=2)+'\n').encode(),b'unexpected')]:
            with self.assertRaisesRegex(ValueError,'complete error document'):C.validate_probe('unknown',subprocess.CompletedProcess([],2,stdout,stderr))
        with self.assertRaisesRegex(ValueError,'published cohort'):C.validate_probe('modules',subprocess.CompletedProcess([],0,b'{"modules":[]}',b''))

    def test_cli_refuses_bad_status_discovery_streams_and_help(self):
        modules = (C.E/'offline-modules.stdout.txt').read_bytes()
        unknown = (C.E/'offline-unknown.stdout.txt').read_bytes()
        error = json.loads(modules)
        error['error'] = {'code': 'configuration_invalid'}
        cases = (
            ('modules', 2, modules, b'', 'modules: unexpected exit code'),
            ('unknown', 0, unknown, b'', 'unknown: unexpected exit code'),
            ('modules', 0, modules, b'unexpected diagnostic\n', 'modules: unexpected discovery stderr'),
            ('modules', 0, json.dumps(error).encode(), b'', 'modules: discovery result required'),
            ('modules', 0, b'[]\n', b'', 'modules: discovery result required'),
            ('mcp-help', 0, b'', b'', 'mcp-help: help output required'),
            ('mcp-help', 0, b'Usage: hexalith mcp\n', b'unexpected diagnostic\n', 'mcp-help: help output required'),
            ('mcp-help', 0, b'ERROR: invalid arguments\n', b'', 'mcp-help: help output required'),
        )
        C.validate_probe('mcp-help', subprocess.CompletedProcess([], 0, b'Usage: hexalith mcp\n', b''))
        for name,status,stdout,stderr,message in cases:
            with self.subTest(name=name,status=status,stdout=stdout[:40],stderr=stderr):
                with self.assertRaises(ValueError) as refused:
                    C.validate_probe(name,subprocess.CompletedProcess([],status,stdout,stderr))
                self.assertEqual(str(refused.exception),message)

    def test_describe_requires_the_expected_offline_schema_scope_and_availability(self):
        captured = (C.E/'offline-describe.stdout.txt').read_bytes()
        for field,path,value in (('submittable',(),True),
                                 ('platformScope',('envelope',),'platform:other'),
                                 ('Unexpected',('schema','properties'),{'type':'string'})):
            with self.subTest(field=field):
                document = json.loads(captured)
                parent = document
                for key in path:
                    parent = parent[key]
                parent[field] = value
                result = subprocess.CompletedProcess([],0,json.dumps(document).encode(),b'')
                with self.assertRaisesRegex(ValueError,'^describe: expected typed offline discovery required$'):
                    C.validate_probe('describe',result)

    def test_exact_tool_names_are_required(self):
        response={'jsonrpc':'2.0','id':2,'result':{'tools':[{'name':name,'inputSchema':{}} for name in sorted(C.TOOLS)]}}
        C.validate_tools(response)
        response['result']['tools'][0]['name']='unrelated'
        with self.assertRaisesRegex(ValueError,'exact generic tool names'):C.validate_tools(response)

    def test_partial_line_obeys_absolute_deadline_and_bounded_cleanup(self):
        process=subprocess.Popen([sys.executable,'-c','import os,time;os.write(1,b\'{"id":1\');time.sleep(10)'],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
        started=time.monotonic()
        try:
            with self.assertRaisesRegex(ValueError,'response deadline'):C.Responses(process.stdout).receive(1,timeout=0.2)
        finally:C.stop_process(process,timeout=0.2)
        self.assertLess(time.monotonic()-started,2)
        self.assertIsNotNone(process.returncode)

    def test_stdio_rejects_a_response_larger_than_the_buffer(self):
        child = 'import sys; sys.stdout.buffer.write(b" " * (1024 * 1024 + 1) + b\'{"id": 1}\\n\')'
        process = subprocess.Popen([sys.executable,'-c',child],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
        try:
            with self.assertRaisesRegex(ValueError,'^stdio response exceeds buffer bound$'):
                C.Responses(process.stdout).receive(1,timeout=5)
        finally:
            C.stop_process(process,timeout=0.2)

    def test_stdio_rejects_nonobject_responses(self):
        for line in (b'null\n',b'[]\n',b'"message"\n',b'1\n'):
            read,write = os.pipe()
            with self.subTest(line=line),os.fdopen(read,'rb') as reader,os.fdopen(write,'wb',buffering=0) as writer:
                writer.write(line)
                with self.assertRaisesRegex(ValueError,'^stdio response must be a JSON object$'):
                    C.Responses(reader).receive(1,timeout=1)

    def test_install_timeout_retains_both_partial_streams(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for stdout,stderr in [(b'install started\n',b'partial diagnostic\n'),(b'partial \xc2',None),(None,None)]:
                timeout = subprocess.TimeoutExpired(['dotnet'],120,output=stdout,stderr=stderr)
                with mock.patch.object(subprocess,'run',side_effect=timeout):
                    with self.assertRaisesRegex(ValueError,'^Published CLI install timed out; see offline-install streams$'):
                        C.install_tool(['dotnet'],{},root)
                self.assertEqual((root/'offline-install.stdout.txt').read_bytes(),C.retained(stdout or b''))
                self.assertEqual((root/'offline-install.stderr.txt').read_bytes(),C.retained(stderr or b''))

    def test_malformed_stdio_retains_sanitized_captures_of_both_streams(self):
        sensitive=b'Bear'+b'er '+b'x'*40
        stdout = json.dumps(sensitive.decode()).encode() + b'\n'
        child=f'import os;os.write(2,{sensitive!r});os.write(1,{stdout!r})'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = root/'evidence'
            evidence.mkdir()
            with self.assertRaisesRegex(ValueError,'JSON object'):
                C.discover_stdio([sys.executable,'-c',child],None,root,evidence)
            diagnostic=(evidence/'offline-stdio.stderr.txt').read_bytes()
            self.assertEqual(diagnostic,C.retained(sensitive))
            self.assertNotIn(sensitive,diagnostic)
            retained_stdout = (evidence/'offline-stdio.stdout.txt').read_bytes()
            self.assertEqual(retained_stdout, C.retained(stdout))
            self.assertNotIn(sensitive, retained_stdout)

    def test_nonobject_stdio_payloads_retain_failed_run_evidence(self):
        initialization = {'protocolVersion': '2025-06-18', 'serverInfo': {'name': 'hexalith'}}
        valid_tools = [{'name': name, 'inputSchema': {}} for name in sorted(C.TOOLS)]
        cases = [
            ([], {'tools': valid_tools}, 'initialize result must be a JSON object'),
            (initialization, [], 'tools/list result must be a JSON object'),
            (initialization, {'tools': [*valid_tools[:-1], []]}, 'tools/list tools must be an array of JSON objects'),
        ]
        for initialize, tools, message in cases:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                responses = {request_id: {'id': request_id, 'jsonrpc': '2.0', 'result': result}
                             for request_id, result in ((1, initialize), (2, tools))}
                child = (
                    'import json, sys\n'
                    f'responses = {responses!r}\n'
                    'print("probe diagnostic", file=sys.stderr, flush=True)\n'
                    'for line in sys.stdin:\n'
                    '    request_id = json.loads(line).get("id")\n'
                    '    if request_id in responses:\n'
                    '        print(json.dumps(responses[request_id]), flush=True)\n'
                )
                def collect(staging):
                    C.discover_stdio([sys.executable, '-c', child], None, root, staging)
                with mock.patch.object(C, 'collect', side_effect=collect):
                    with self.assertRaisesRegex(ValueError, f'^stdio: {message}\\. Retained evidence in '):
                        C.run_probe(root/'runs')
                [failed] = (root/'runs').iterdir()
                self.assertTrue(failed.name.startswith('failed-'))
                self.assertFalse((failed/'offline-cli.json').exists())
                seen = [1] if initialize == [] else [1, 2]
                expected = ''.join(json.dumps(responses[request_id])+'\n' for request_id in seen)
                self.assertEqual((failed/'offline-stdio.stdout.txt').read_text(), expected)
                self.assertEqual((failed/'offline-stdio.stderr.txt').read_text(), 'probe diagnostic\n')

    def test_main_reports_success_and_failure_to_the_correct_streams(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            for error in (None, ValueError('offline verification failed'), OSError('output unavailable')):
                with self.subTest(error=error):
                    status, stdout, stderr = 0, io.StringIO(), io.StringIO()
                    published = output/'run-fixture'
                    with mock.patch.object(C, 'run_probe', return_value=published, side_effect=error) as run, \
                            contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                        status = C.main(['--output', str(output)])
                    run.assert_called_once_with(output)
                    if error:
                        self.assertEqual((status, stdout.getvalue(), stderr.getvalue()),
                                         (1, '', f'FAIL: {error}\n'))
                    else:
                        expected = ('PASS: published 2.0.1 offline discovery/help, safe unknown-operation refusal '
                                    f'and five generic stdio tools. Evidence in {published}\n')
                        self.assertEqual((status, stdout.getvalue(), stderr.getvalue()), (0, expected, ''))

    def test_nonobject_discovery_payloads_retain_failed_run_evidence(self):
        cases = (
            ('modules', 'modules', [1, 2], 'modules must be an array of JSON objects'),
            ('modules', 'modules', None, 'modules must be an array of JSON objects'),
            ('modules', 'modules', [{'name': [], 'description': 'fixture'}]*2, 'expected published cohort required'),
            ('tenants', 'operations', [None]*14, 'operations must be an array of JSON objects'),
            ('tenants', 'operations', [{'name': {}, 'description': 'fixture'}]*14,
             'expected operation names/kinds/descriptions required'),
            ('parties', 'operations', {}, 'operations must be an array of JSON objects'),
            ('describe', 'schema', [], 'schema, schema properties and envelope must be JSON objects'),
            ('describe', 'schema', {'properties': []}, 'schema, schema properties and envelope must be JSON objects'),
            ('describe', 'envelope', [], 'schema, schema properties and envelope must be JSON objects'),
        )
        for name, field, value, message in cases:
            with self.subTest(name=name, field=field, value=value), tempfile.TemporaryDirectory() as directory:
                output = Path(directory)
                capture = f'offline-{name}.stdout.txt'
                document = json.loads((C.E/capture).read_bytes())
                document[field] = value
                invalid = json.dumps(document).encode()
                preceding = ['modules', 'tenants', 'parties', 'describe']
                results = [subprocess.CompletedProcess([], 0, (C.E/f'offline-{probe}.stdout.txt').read_bytes(), b'')
                           for probe in preceding[:preceding.index(name)]]
                results.append(subprocess.CompletedProcess([], 0, invalid, b''))
                stdout, stderr = io.StringIO(), io.StringIO()
                with mock.patch.object(C, 'install_tool'), mock.patch.object(subprocess, 'run', side_effect=results), \
                        contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    status = C.main(['--output', str(output)])
                [failed] = output.iterdir()
                self.assertTrue(failed.name.startswith('failed-'))
                self.assertEqual((status, stdout.getvalue(), stderr.getvalue()),
                                 (1, '', f'FAIL: {name}: {message}. Retained evidence in {failed}\n'))
                self.assertEqual((failed/capture).read_bytes(), C.retained(invalid))
                self.assertEqual((failed/f'offline-{name}.stderr.txt').read_bytes(), b'')
                self.assertFalse((failed/'offline-cli.json').exists())

    def test_successful_stdio_binds_raw_and_retained_stdout_separately(self):
        sensitive = 'Bear' + 'er ' + 'x' * 40
        responses = {
            1: {'jsonrpc': '2.0', 'id': 1, 'result': {
                'protocolVersion': '2025-06-18', 'serverInfo': {'name': 'hexalith'}}},
            2: {'jsonrpc': '2.0', 'id': 2, 'result': {'tools': [
                {'name': name, 'inputSchema': {}, 'description': sensitive}
                for name in sorted(C.TOOLS)]}},
        }
        raw = ''.join(json.dumps(responses[request_id]) + '\n' for request_id in (1, 2)).encode()
        child = (
            'import json, sys\n'
            f'responses = {responses!r}\n'
            'for line in sys.stdin:\n'
            '    request_id = json.loads(line).get("id")\n'
            '    if request_id in responses:\n'
            '        print(json.dumps(responses[request_id]), flush=True)\n'
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = C.discover_stdio([sys.executable, '-c', child], None, root, root)
            captured = (root/'offline-stdio.stdout.txt').read_bytes()
            self.assertNotEqual(raw, captured)
            self.assertEqual(captured, C.retained(raw))
            self.assertEqual(record['stdoutSha256'], hashlib.sha256(captured).hexdigest())
            self.assertEqual(record['rawStdoutSha256'], hashlib.sha256(raw).hexdigest())

    def test_stdio_requires_initialize_identity_and_clean_shutdown(self):
        cases = (
            ('2024-11-05', {'name': 'hexalith'}, 0, 'stdio: valid initialization required'),
            ('2025-06-18', {'name': 'unrelated'}, 0, 'stdio: valid initialization required'),
            ('2025-06-18', [], 0, 'stdio: valid initialization required'),
            ('2025-06-18', {'name': 'hexalith'}, 3, 'stdio: clean shutdown required'),
        )
        for protocol,server,status,message in cases:
            with self.subTest(protocol=protocol,server=server,status=status), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                responses = {
                    1: {'id': 1, 'jsonrpc': '2.0', 'result': {'protocolVersion': protocol, 'serverInfo': server}},
                    2: {'id': 2, 'jsonrpc': '2.0', 'result': {'tools': [
                        {'name': name, 'inputSchema': {}} for name in sorted(C.TOOLS)]}},
                }
                child = (
                    'import json, sys\n'
                    f'responses = {responses!r}\n'
                    'for line in sys.stdin:\n'
                    '    request_id = json.loads(line).get("id")\n'
                    '    if request_id in responses:\n'
                    '        print(json.dumps(responses[request_id]), flush=True)\n'
                    f'sys.exit({status})\n'
                )
                with self.assertRaises(ValueError) as refused:
                    C.discover_stdio([sys.executable,'-c',child],None,root,root)
                self.assertEqual(str(refused.exception),message)
                seen = (1,2) if status else (1,)
                self.assertEqual((root/'offline-stdio.stdout.txt').read_text(),
                                 ''.join(json.dumps(responses[request_id])+'\n' for request_id in seen))
                self.assertEqual((root/'offline-stdio.stderr.txt').read_bytes(),b'')

    def test_failed_rerun_preserves_prior_manifest_and_capture(self):
        capture = 'offline-modules.stdout.txt'

        def successful(evidence):
            (evidence/capture).write_bytes(b'first capture')
            return {'records': [{'name': 'modules'}]}

        def failed(evidence):
            (evidence/capture).write_bytes(b'failed capture')
            raise ValueError('modules: unexpected exit code')

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with mock.patch.object(C, 'collect', side_effect=successful):
                published = C.run_probe(root)
            manifest = (published/'offline-cli.json').read_bytes()
            with mock.patch.object(C, 'collect', side_effect=failed):
                with self.assertRaisesRegex(ValueError, r'^modules: unexpected exit code\. Retained evidence in '):
                    C.run_probe(root)
            failures = list(root.glob('failed-*'))
            self.assertEqual(list(root.glob('run-*')), [published])
            self.assertEqual(len(failures), 1)
            self.assertEqual((failures[0]/capture).read_bytes(), b'failed capture')
            self.assertEqual(list(failures[0].glob('*.json')), [])
            self.assertEqual((published/'offline-cli.json').read_bytes(), manifest)
            self.assertEqual((published/capture).read_bytes(), b'first capture')
