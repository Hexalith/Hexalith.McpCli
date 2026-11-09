"""Evidence scanning binds exact files and fails closed without echoing secrets."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location('evidence_secret_scan', SCRIPTS / 'scan-evidence-secrets.py')
SCANNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCANNER)


class EvidenceSecretScanTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.packet = self.root / 'packet'
        self.packet.mkdir()

    def invoke(self, receipt='scan.json', evidence=None, environment=None):
        return subprocess.run([sys.executable, str(SCRIPTS / 'scan-evidence-secrets.py'),
                               str(evidence or self.packet), '--receipt', str(self.root / receipt)],
                              env={'PATH': os.environ.get('PATH', ''), **(environment or {})},
                              capture_output=True, text=True, timeout=15)

    def test_clean_receipt_is_deterministic_and_binds_every_file_and_implementation(self):
        (self.packet / 'nested').mkdir()
        (self.packet / 'nested/z.xml').write_text('<assembly passed="1"><PrivateKey/><safe>retained</safe></assembly>\n')
        (self.packet / '.hidden').write_text('retained diagnostic\n')
        (self.packet / 'a.json').write_text('{"PrivateKey":"[REDACTED]","token":"Bearer [REDACTED]"}\n')
        first = self.invoke('first.json')
        second = self.invoke('second.json')
        self.assertEqual((0, ''), (first.returncode, first.stderr), first.stdout)
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(first.stdout, (self.root / 'first.json').read_text())
        result = json.loads(first.stdout)
        self.assertEqual(('clean', [], [], 3),
                         (result['result'], result['findings'], result['errors'], result['fileCount']))
        self.assertEqual(['.hidden', 'a.json', 'nested/z.xml'], [file['path'] for file in result['files']])
        for file in result['files']:
            data = (self.packet / file['path']).read_bytes()
            self.assertEqual({'path': file['path'], 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}, file)
        self.assertEqual(hashlib.sha256(SCANNER.serialized(result['files'])).hexdigest(), result['manifestSha256'])
        for name, digest in result['implementationSha256'].items():
            self.assertEqual(hashlib.sha256((SCRIPTS / name).read_bytes()).hexdigest(), digest)
        (self.packet / '.hidden').write_text('changed diagnostic\n')
        changed = json.loads(self.invoke('changed.json').stdout)
        self.assertNotEqual(result['manifestSha256'], changed['manifestSha256'])

    def test_secrets_in_direct_escaped_truncated_and_malformed_output_fail_without_echo(self):
        cases = [
            'Authorization: Bearer opaque-canary-credential+/_~.abc==',
            json.dumps({'output': 'Authorization: Bearer opaque-canary-credential+/_~.abc=='}),
            json.dumps({'output': json.dumps({'output': 'Bearer opaque-canary-credential'})}),
            '-----BEGIN EC PRIVATE KEY-----\nprivate-component-canary',
            json.dumps({'output': '-----BEGIN PRIVATE KEY-----\nprivate-component-canary'}),
            '<root><PrivateKey>private-component-canary</PrivateKey><unfinished',
            '<root><PrivateKey>private-component-canary',
            '<root><PrivateKey kind="rsa">private-component-canary</PrivateKey><unfinished',
            '<root><setting name="PrivateKey" value="private-component-canary" /><unfinished',
            '<root><setting name="PrivateKey">private-component-canary</setting><unfinished',
            'prefix "quoted" <root><PrivateKey kind="rsa">private-component-canary</PrivateKey><unfinished',
            '<root><setting name="PrivateKey" value="private-component-canary',
            '<root><setting name="safe" key="PrivateKey" value="private-component-canary"/><unfinished',
            '--PrivateKey="private-component-canary with spaces"',
            '<failure message="Bearer&#32;opaque-canary-credential" /><unfinished',
            '{"PrivateKey":{"d":"private-component-canary"},"PrivateKey":"[REDACTED]"}',
            '{"\\u0050rivateKey":"private-component-canary"}',
            'eyJcanary.payload.signature',
        ]
        for index, text in enumerate(cases):
            with self.subTest(index=index):
                source = self.packet / 'child.log'
                source.write_text(text)
                result = self.invoke(f'scan-{index}.json')
                self.assertEqual((1, ''), (result.returncode, result.stderr), result.stdout)
                report = json.loads(result.stdout)
                self.assertEqual('secrets-detected', report['result'])
                self.assertEqual([{'path': 'child.log', 'rule': 'redaction-required'}], report['findings'])
                self.assertEqual([], report['errors'])
                self.assertNotIn('opaque-canary', result.stdout + result.stderr)
                self.assertNotIn('private-component-canary', result.stdout + result.stderr)
                self.assertEqual(text, source.read_text())

    def test_known_environment_secret_is_checked_without_repeating_its_value(self):
        for index, secret in enumerate(('synthetic-arbitrary-secret-canary', 'abc123')):
            with self.subTest(index=index):
                (self.packet / 'stdout.txt').write_text(json.dumps({'output': secret}))
                result = self.invoke(f'environment-{index}.json', environment={'MCPCLI_TEST_SECRET': secret})
                self.assertEqual(1, result.returncode, result.stdout)
                self.assertEqual(1, json.loads(result.stdout)['knownCredentialCount'])
                self.assertNotIn(secret, result.stdout + result.stderr)

    def test_utf16_bom_and_hidden_extensionless_files_are_scanned(self):
        (self.packet / '.capture').write_bytes('Bearer opaque-canary'.encode('utf-16'))
        result = self.invoke()
        self.assertEqual(1, result.returncode, result.stdout)
        self.assertEqual('.capture', json.loads(result.stdout)['findings'][0]['path'])

    def test_all_findings_are_sorted_and_receipt_contains_no_source_snippets(self):
        for name in ('z.log', 'a.log'):
            (self.packet / name).write_text('Bearer opaque-canary')
        first, second = self.invoke('first.json'), self.invoke('second.json')
        self.assertEqual(first.stdout, second.stdout)
        report = json.loads(first.stdout)
        self.assertEqual(['a.log', 'z.log'], [finding['path'] for finding in report['findings']])
        self.assertNotIn('opaque-canary', first.stdout)

    def test_invalid_encoding_and_binary_content_produce_failing_receipts(self):
        for index, data in enumerate((b'\xffinvalid', b'prefix\x00Bearer canary', b'%PDF-1.4\nopaque compressed stream',
                                      b'\x01\x02\x03\x04', b'!<arch>\n', b'!<thin>\n',
                                      b' ' * 257 + b'ustar' + b' ' * 250)):
            with self.subTest(index=index):
                (self.packet / 'capture').write_bytes(data)
                result = self.invoke(f'scan-{index}.json')
                self.assertEqual(2, result.returncode, result.stdout)
                report = json.loads(result.stdout)
                self.assertEqual('scan-error', report['result'])
                self.assertEqual([{'path': 'capture', 'rule': 'unsupported-text-or-binary'}], report['errors'])
                self.assertEqual(1, report['fileCount'])

    def test_empty_missing_and_symlink_roots_cannot_report_clean(self):
        link = self.root / 'link'
        link.symlink_to(self.packet, target_is_directory=True)
        for index, evidence in enumerate((self.packet, self.root / 'absent', link)):
            with self.subTest(index=index):
                result = self.invoke(f'scan-{index}.json', evidence=evidence)
                self.assertEqual(2, result.returncode, result.stdout)
                self.assertEqual('scan-error', json.loads(result.stdout)['result'])

    def test_links_and_special_files_are_refused_without_reading_their_targets(self):
        outside = self.root / 'outside.txt'
        outside.write_text('Bearer outside-canary')
        (self.packet / 'linked-file').symlink_to(outside)
        (self.packet / 'linked-directory').symlink_to(self.root, target_is_directory=True)
        os.mkfifo(self.packet / 'pipe')
        result = self.invoke()
        self.assertEqual(2, result.returncode, result.stdout)
        report = json.loads(result.stdout)
        self.assertEqual(['linked-directory', 'linked-file', 'pipe'], [error['path'] for error in report['errors']])
        self.assertEqual([], report['files'])
        self.assertNotIn('outside-canary', result.stdout + result.stderr)

    def test_unreadable_file_and_directory_are_errors_not_clean_omissions(self):
        (self.packet / 'capture').write_text('safe')
        original = SCANNER.os.open
        def refuse(path, *args, **kwargs):
            if Path(path).name == 'capture':
                raise PermissionError('sensitive error detail')
            return original(path, *args, **kwargs)
        with patch.object(SCANNER.os, 'open', side_effect=refuse):
            report = SCANNER.scan(self.packet, environment={})
        self.assertEqual(2, report['exitCode'])
        self.assertEqual([{'path': 'capture', 'rule': 'file-unreadable'}], report['errors'])
        def inaccessible(*args, onerror, **kwargs):
            onerror(PermissionError(13, 'private failure', str(self.packet / 'unreadable-directory')))
            return iter([])
        with patch.object(SCANNER.os, 'walk', side_effect=inaccessible):
            report = SCANNER.scan(self.packet, environment={})
        self.assertEqual([{'path': 'unreadable-directory', 'rule': 'directory-unreadable'}], report['errors'])
        self.assertEqual(2, report['exitCode'])

    def test_receipt_inside_packet_is_explicitly_excluded_and_must_be_new(self):
        (self.packet / 'capture').write_text('safe')
        result = self.invoke('packet/secret-scan.json')
        report = json.loads(result.stdout)
        self.assertEqual(0, result.returncode, result.stdout)
        self.assertEqual('secret-scan.json', report['receiptExcluded'])
        self.assertEqual(['capture'], [file['path'] for file in report['files']])
        original = (self.packet / 'secret-scan.json').read_bytes()
        refused = self.invoke('packet/secret-scan.json')
        self.assertEqual((2, '', 'Secret scan refused: receipt destination must be new.\n'),
                         (refused.returncode, refused.stdout, refused.stderr))
        self.assertEqual(original, (self.packet / 'secret-scan.json').read_bytes())

    def test_redaction_failure_cannot_report_clean(self):
        (self.packet / 'capture').write_text('safe')
        with patch.object(SCANNER, 'sanitized_xml', side_effect=RecursionError('sensitive detail')):
            report = SCANNER.scan(self.packet, environment={})
        self.assertEqual(2, report['exitCode'])
        self.assertEqual([{'path': 'capture', 'rule': 'redaction-failed'}], report['errors'])


if __name__ == '__main__':
    unittest.main()
