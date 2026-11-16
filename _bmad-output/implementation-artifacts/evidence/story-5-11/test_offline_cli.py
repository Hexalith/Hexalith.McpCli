import importlib.util
import json
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
