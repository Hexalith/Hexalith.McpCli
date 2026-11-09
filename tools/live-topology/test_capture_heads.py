"""Pin discovery parity and exact binary/Catalog binding without live infrastructure."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import capture_heads
from validate import VectorError


class CaptureHeadsTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.host = Path(temporary.name) / 'Head.dll'
        self.host.write_bytes(b'compiled-head')
        revision = patch.object(capture_heads.subprocess, 'check_output', return_value='a' * 40 + '\n')
        revision.start()
        self.addCleanup(revision.stop)
        self.modules = {'modules': [{'name': 'sample'}]}
        self.catalog = {'operations': [{'name': 'sample.read', 'description': 'Unicode é', 'kind': 'query'}]}

    def head(self):
        mock = patch.object(capture_heads, 'HeadProcess')
        self.addCleanup(mock.stop)
        process = mock.start().return_value
        process.cli.side_effect = [(0, self.modules), (0, self.catalog)]
        process.mcp.side_effect = [(False, self.modules), (False, self.catalog)]
        return process

    def test_exact_structured_catalog_and_binary_hashes_are_retained(self):
        process = self.head()
        receipt = capture_heads.capture(self.host)
        encoded = json.dumps(self.catalog, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
        self.assertEqual(hashlib.sha256(encoded).hexdigest(), receipt['modules']['sample']['sha256'])
        self.assertEqual(self.catalog, receipt['modules']['sample']['structuredContent'])
        self.assertEqual({'Head.dll': hashlib.sha256(b'compiled-head').hexdigest()}, receipt['binariesSha256'])
        self.assertEqual(capture_heads.digest({'sample': self.catalog}), receipt['catalogSha256'])
        self.assertEqual('a' * 40, receipt['sourceCommit'])
        self.assertEqual([('list_modules', {}), ('list_operations', {'module': 'sample'})],
                         [call.args for call in process.mcp.call_args_list])

    def test_different_head_documents_and_error_exits_refuse_capture(self):
        for code, error, cli, mcp in [(2, False, self.catalog, self.catalog),
                                      (0, True, self.catalog, self.catalog),
                                      (0, False, self.catalog, {'operations': []})]:
            with self.subTest(code=code, error=error):
                process = self.head()
                process.cli.side_effect = [(0, self.modules), (code, cli)]
                process.mcp.side_effect = [(False, self.modules), (error, mcp)]
                with self.assertRaises(VectorError):
                    capture_heads.capture(self.host)

    def test_empty_catalog_refuses_capture(self):
        process = self.head()
        process.cli.side_effect = [(0, {'modules': []})]
        process.mcp.side_effect = [(False, {'modules': []})]
        with self.assertRaisesRegex(ValueError, 'nonempty'):
            capture_heads.capture(self.host)

    def test_duplicate_modules_refuse_capture(self):
        process = self.head()
        duplicate = {'modules': [{'name': 'sample'}, {'name': 'sample'}]}
        process.cli.side_effect = [(0, duplicate), (0, self.catalog)]
        process.mcp.side_effect = [(False, duplicate), (False, self.catalog)]
        with self.assertRaisesRegex(ValueError, 'Duplicate module'):
            capture_heads.capture(self.host)

    def test_missing_host_refuses_capture(self):
        self.host.unlink()
        with self.assertRaisesRegex(ValueError, 'compiled host'):
            capture_heads.capture(self.host)

    def test_abbreviated_candidate_commit_refuses_capture(self):
        with patch.object(capture_heads.subprocess, 'check_output', return_value='abcdef1\n'):
            with self.assertRaisesRegex(ValueError, 'full canonical'):
                capture_heads.capture(self.host)

    def test_binary_drift_during_discovery_refuses_capture(self):
        process = self.head()
        def mcp(tool, arguments):
            if tool == 'list_modules':
                return False, self.modules
            self.host.write_bytes(b'drifted-head')
            return False, self.catalog
        process.mcp.side_effect = mcp
        with self.assertRaisesRegex(ValueError, 'changed during'):
            capture_heads.capture(self.host)


if __name__ == '__main__':
    unittest.main()
