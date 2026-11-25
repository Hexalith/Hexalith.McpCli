"""Evidence scanning binds exact files and fails closed without echoing secrets."""

import hashlib
import importlib.util
import io
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
        # Resolve the temporary root: linked system temp directories would otherwise be refused ancestors.
        self.root = Path(self.temporary.name).resolve()
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
            r'diagnostic {\"PrivateKey\":\"private-component-canary',
            '<root><setting name="Private&#75;ey">private-component-canary</setting><unfinished',
            '<root><setting PrivateKey="prefix>private-component-canary"/><unfinished',
            '--SigningKey private-component-canary --safe kept',
            '"command": ["--PrivateKey", "private-component-canary", "--safe"]',
            r'--PrivateKey="prefix\"private-component-canary" kept',
            '<failure message="Bearer&#32;opaque-canary-credential" /><unfinished',
            '{"PrivateKey":{"d":"private-component-canary"},"PrivateKey":"[REDACTED]"}',
            '{"\\u0050rivateKey":"private-component-canary"}',
            'eyJcanary.payload.signature',
            'log "raw\ttab eyJcanary.payload.signature" kept',
            r'log "C:\Users\log Bearer\u0020opaque-canary-credential" kept',
            'log "details\n-----BEGIN PRIVATE KEY-----\nprivate-component-canary" kept',
        ]
        for index, text in enumerate(cases):
            with self.subTest(index=index):
                source = self.packet / 'child.log'
                source.write_text(text)
                receipt = f'scan-{index}.json'
                result = self.invoke(receipt)
                self.assertEqual((1, ''), (result.returncode, result.stderr), result.stdout)
                report = json.loads(result.stdout)
                self.assertEqual('secrets-detected', report['result'])
                self.assertEqual([{'path': 'child.log', 'rule': 'redaction-required'}], report['findings'])
                self.assertEqual([], report['errors'])
                retained = result.stdout + result.stderr + (self.root / receipt).read_text()
                for canary in ('opaque-canary', 'private-component-canary', 'eyJcanary.payload.signature'):
                    self.assertNotIn(canary, retained)
                self.assertEqual(text, source.read_text())

    def test_known_environment_secret_is_checked_without_repeating_its_value(self):
        for index, secret in enumerate(('synthetic-arbitrary-secret-canary', 'bc123-aB')):
            with self.subTest(index=index):
                (self.packet / 'stdout.txt').write_text(json.dumps({'output': secret}))
                result = self.invoke(f'environment-{index}.json', environment={'MCPCLI_TEST_SECRET': secret})
                self.assertEqual(1, result.returncode, result.stdout)
                self.assertEqual(1, json.loads(result.stdout)['knownCredentialCount'])
                self.assertNotIn(secret, result.stdout + result.stderr)

    def test_short_known_credentials_refuse_even_a_clean_packet_without_a_receipt(self):
        source = self.packet / 'data.json'
        contents = '{"sha256":"ab12cd34ef","ok":true}\n'
        source.write_text(contents)
        for name, value in {'X_TOKEN_TTL': '12', 'SECRET_ENABLED': 'true', 'MCPCLI_TEST_SECRET': 'abc12-A'}.items():
            with self.subTest(name=name):
                result = self.invoke(environment={name: value})
                self.assertEqual(2, result.returncode)
                self.assertEqual('', result.stdout)
                self.assertEqual('Secret scan refused: Structured evidence requires known environment credentials '
                                 'of at least eight characters.\n', result.stderr)
                self.assertFalse((self.root / 'scan.json').exists())
                self.assertEqual(contents, source.read_text())

    def test_standalone_evidence_commands_refuse_before_creating_outputs(self):
        output = self.root / 'disallowed-output'
        root = SCRIPTS.parent
        for command, arguments in (
            ('scripts/product_ci.py', ['linux']),
            ('scripts/verify-paired-publication.py', ['record-operator', '--output', str(output)]),
            ('tools/proprietary-surfaces/v1/check.py', ['--output', str(output)]),
        ):
            with self.subTest(command=command):
                environment = {'PATH': os.environ.get('PATH', ''), 'MCPCLI_LIVE_TOKEN': 'abc1234'}
                result = subprocess.run([sys.executable, str(root / command), *arguments],
                                        env=environment, capture_output=True, text=True, timeout=15)
                self.assertEqual(1, result.returncode, result.stderr)
                self.assertEqual('', result.stdout)
                self.assertIn('Structured evidence requires known environment credentials', result.stderr)
                self.assertNotIn(environment['MCPCLI_LIVE_TOKEN'], result.stderr)
                self.assertFalse(output.exists())
                self.assertFalse(output.with_suffix('.failure.json').exists())

    def test_refusal_redacts_a_short_value_matching_its_message(self):
        result = self.invoke(environment={'MCPCLI_TEST_SECRET': 'eight'})
        self.assertEqual(2, result.returncode)
        self.assertEqual('', result.stdout)
        self.assertNotIn('eight', result.stderr)
        self.assertIn('[REDACTED]', result.stderr)
        self.assertFalse((self.root / 'scan.json').exists())

    def test_utf16_bom_and_hidden_extensionless_files_are_scanned(self):
        (self.packet / '.capture').write_bytes('Bearer opaque-canary'.encode('utf-16'))
        result = self.invoke()
        self.assertEqual(1, result.returncode, result.stdout)
        self.assertEqual('.capture', json.loads(result.stdout)['findings'][0]['path'])

    def test_clean_content_with_credentials_in_filenames_reports_only_redacted_paths(self):
        names = {'eyJcanary.payload.signature': '[REDACTED JWT]', 'synthetic-path-canary': '[REDACTED]'}
        for name in names:
            (self.packet / (name + '.log')).write_text('ordinary diagnostic')
        result = self.invoke(environment={'MCPCLI_TEST_SECRET': 'synthetic-path-canary'})
        receipt = (self.root / 'scan.json').read_text()
        for name in names:
            self.assertNotIn(name, result.stdout + result.stderr + receipt)
        self.assertEqual((1, '', receipt), (result.returncode, result.stderr, result.stdout))
        report = json.loads(receipt)
        paths = sorted(label + '.log' for label in names.values())
        self.assertEqual(('secrets-detected', 1, []), (report['result'], report['exitCode'], report['errors']))
        self.assertEqual([{'path': path, 'rule': 'sensitive-path'} for path in paths], report['findings'])
        self.assertEqual(paths, [entry['path'] for entry in report['files']])

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

    def test_linked_ancestors_and_parent_steps_cannot_substitute_the_packet(self):
        real = self.root / 'real' / 'packet'
        real.mkdir(parents=True)
        (real / 'capture.txt').write_text('retained diagnostic\n')
        (self.root / 'link').symlink_to(self.root / 'real', target_is_directory=True)
        for index, evidence in enumerate((self.root / 'link' / 'packet', self.packet / '..' / 'real' / 'packet',
                                          Path(os.path.relpath(real, self.root)))):
            with self.subTest(evidence=str(evidence)):
                if not evidence.is_absolute():
                    result = subprocess.run([sys.executable, str(SCRIPTS / 'scan-evidence-secrets.py'), str(evidence),
                                             '--receipt', str(self.root / f'relative-{index}.json')],
                                            env={'PATH': os.environ.get('PATH', '')}, cwd=self.root,
                                            capture_output=True, text=True, timeout=15)
                    self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                    self.assertEqual(['capture.txt'], [file['path'] for file in json.loads(result.stdout)['files']])
                    continue
                result = self.invoke(f'linked-{index}.json', evidence=evidence)
                self.assertEqual((2, ''), (result.returncode, result.stderr), result.stdout)
                report = json.loads(result.stdout)
                self.assertEqual(('scan-error', [{'path': '.', 'rule': 'root-path-not-canonical'}], [], []),
                                 (report['result'], report['errors'], report['files'], report['findings']))
        clean = self.invoke('real.json', evidence=real)
        self.assertEqual(0, clean.returncode, clean.stdout)

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
        (self.packet / 'unreadable-directory').mkdir()
        original = SCANNER.os.open
        def refuse(path, *args, **kwargs):
            if Path(path).name == 'capture':
                raise PermissionError('sensitive error detail')
            return original(path, *args, **kwargs)
        with patch.object(SCANNER.os, 'open', side_effect=refuse):
            report = SCANNER.scan(self.packet, environment={})
        self.assertEqual(2, report['exitCode'])
        self.assertEqual([{'path': 'capture', 'rule': 'file-unreadable'}], report['errors'])
        def inaccessible(path, *args, **kwargs):
            if path == 'unreadable-directory':
                raise PermissionError(13, 'private failure', path)
            return original(path, *args, **kwargs)
        with patch.object(SCANNER.os, 'open', side_effect=inaccessible):
            report = SCANNER.scan(self.packet, environment={})
        self.assertEqual(2, report['exitCode'])
        self.assertEqual([{'path': 'unreadable-directory', 'rule': 'directory-unreadable'}], report['errors'])

    def test_directory_replaced_before_open_is_refused(self):
        outside = self.root / 'outside'
        outside.mkdir()
        (outside / 'subdirectory').mkdir()
        (outside / 'subdirectory' / 'capture').write_text('outside packet')
        original = SCANNER.os.open
        for component, target, rule, error_path in (
                ('packet', outside, 'root-path-not-canonical', '.'),
                ('subdirectory', outside / 'subdirectory', 'directory-unreadable', 'subdirectory')):
            with self.subTest(component=component):
                nested = self.packet / 'subdirectory'
                nested.mkdir(exist_ok=True)
                changed = self.packet if component == 'packet' else nested
                saved = self.root / 'saved'

                def replace(path, *args, **kwargs):
                    if path == component:
                        changed.rename(saved)
                        changed.symlink_to(target, target_is_directory=True)
                    return original(path, *args, **kwargs)

                with patch.object(SCANNER.os, 'open', side_effect=replace):
                    report = SCANNER.scan(self.packet, environment={})
                self.assertEqual((2, [], [{'path': error_path, 'rule': rule}]),
                                 (report['exitCode'], report['files'], report['errors']))
                changed.unlink()
                saved.rename(changed)

    def test_file_reads_remain_relative_to_the_opened_directory(self):
        nested = self.packet / 'nested'
        nested.mkdir()
        (nested / 'capture').write_bytes(b'original bytes')
        outside = self.root / 'outside'
        outside.mkdir()
        (outside / 'capture').write_bytes(b'different bytes')
        original = SCANNER.os.open

        def replace(path, *args, **kwargs):
            if path == 'capture':
                nested.rename(self.root / 'saved')
                nested.symlink_to(outside, target_is_directory=True)
            return original(path, *args, **kwargs)

        with patch.object(SCANNER.os, 'open', side_effect=replace):
            report = SCANNER.scan(self.packet, environment={})
        self.assertEqual(0, report['exitCode'])
        self.assertEqual([{'path': 'nested/capture', 'bytes': 14,
                           'sha256': hashlib.sha256(b'original bytes').hexdigest()}], report['files'])

    @unittest.skipUnless(hasattr(os, 'O_PATH') or hasattr(os, 'O_SEARCH'), 'search-only directory handles are required')
    def test_ancestor_requires_only_search_permission(self):
        ancestor = self.root / 'search-only'
        ancestor.mkdir()
        packet = ancestor / 'packet'
        packet.mkdir()
        (packet / 'capture').write_text('safe')
        ancestor.chmod(0o100)
        try:
            report = SCANNER.scan(packet, environment={})
        finally:
            ancestor.chmod(0o700)
        self.assertEqual((0, ['capture']), (report['exitCode'], [item['path'] for item in report['files']]))

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

    def test_receipt_cannot_attest_to_a_replacement_packet(self):
        (self.packet / 'capture').write_text('reviewed bytes')
        saved = self.root / 'saved'
        receipt = self.packet / 'scan.json'
        original = SCANNER.os.open

        def replace(path, *args, **kwargs):
            if path == 'capture':
                self.packet.rename(saved)
                self.packet.mkdir()
                (self.packet / 'capture').write_text('unreviewed bytes')
            return original(path, *args, **kwargs)

        with patch.object(SCANNER.os, 'open', side_effect=replace), \
                patch.object(sys, 'argv', ['scan-evidence-secrets.py', str(self.packet), '--receipt', str(receipt)]), \
                patch.object(sys, 'stdout', new_callable=io.StringIO) as stdout, \
                patch.object(sys, 'stderr', new_callable=io.StringIO) as stderr:
            self.assertEqual(2, SCANNER.main())
        self.assertEqual('', stdout.getvalue())
        self.assertEqual('Secret scan failed: receipt could not be written.\n', stderr.getvalue())
        self.assertFalse(receipt.exists())

    def test_redaction_failure_cannot_report_clean(self):
        (self.packet / 'capture').write_text('safe')
        with patch.object(SCANNER, 'sanitized_xml', side_effect=RecursionError('sensitive detail')):
            report = SCANNER.scan(self.packet, environment={})
        self.assertEqual(2, report['exitCode'])
        self.assertEqual([{'path': 'capture', 'rule': 'redaction-failed'}], report['errors'])

    def test_receipt_write_failure_has_distinct_exit_and_diagnostic(self):
        (self.packet / 'capture').write_text('safe')
        parent = self.root / 'regular-file'
        parent.write_text('keep')
        result = self.invoke('regular-file/scan.json')
        self.assertEqual((2, '', 'Secret scan failed: receipt could not be written.\n'),
                         (result.returncode, result.stdout, result.stderr))
        self.assertEqual('keep', parent.read_text())


if __name__ == '__main__':
    unittest.main()
