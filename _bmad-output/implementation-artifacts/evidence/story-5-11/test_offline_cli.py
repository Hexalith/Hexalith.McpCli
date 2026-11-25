import hashlib
import importlib.util
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
