"""Focused regressions for the candidate census evidence helper."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('candidate_census', HERE / 'run-candidate-census.py')
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class CandidateCensusTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.owner = self.root / 'owner'
        self.policy = self.owner / 'tools/proprietary-surfaces/v1'
        self.policy.mkdir(parents=True)
        self.source = self.root / 'stores'
        self.source.mkdir()
        self.owner_git = self.root / 'owner-git'
        self.source_git = self.root / 'source-git'
        for directory in (self.owner_git, self.source_git):
            directory.mkdir()
            (directory / 'HEAD').write_text('ref: refs/heads/main\n')
            (directory / 'index').write_bytes(b'original index')
        self.output = self.root / 'result.json'
        self.census = helper.load_census()
        self.report = {'schema': self.census.SCHEMA, 'status': 'passed', 'surfaces': [], 'errors': []}
        self.index = self.policy / 'amendments.json'
        self.index.write_text('[]')

    def amendment(self, path='receipt.json', index_path='amendments/1.0.1.json'):
        amendment = self.policy / 'amendments/1.0.1.json'
        amendment.parent.mkdir(exist_ok=True)
        amendment.write_text(json.dumps({'approval': {'evidence': {'path': path}}}))
        self.index.write_text(json.dumps([{'path': index_path, 'sha256': '0' * 64}]))
        return amendment

    @contextlib.contextmanager
    def scratch(self, **_):
        overlay = self.root / 'scratch/overlay'
        overlay.mkdir(parents=True)
        try:
            yield str(overlay)
        finally:
            shutil.rmtree(overlay)

    def run_helper(self, scan=None):
        def git(repository, *args):
            if args == ('rev-parse', 'HEAD'):
                return 'f' * 40
            return str(self.owner_git if Path(repository) == self.owner else self.source_git)

        stdout = io.StringIO()
        with mock.patch.object(self.census, 'git', side_effect=git), \
                mock.patch.object(self.census, 'Tree'), \
                mock.patch.object(self.census, 'declarations', return_value={'references/Fixture': 'a' * 40}), \
                mock.patch.object(self.census, 'scan', side_effect=scan, return_value=self.report) as scanned, \
                mock.patch.object(helper.tempfile, 'TemporaryDirectory', side_effect=self.scratch), \
                contextlib.redirect_stdout(stdout), mock.patch.dict(os.environ):
            result = helper.run_candidate(self.owner, self.source, self.output, self.census)
        return result, stdout.getvalue(), scanned

    def failure(self, result):
        self.assertEqual(1, result)
        report = json.loads(self.output.read_text())
        provenance = json.loads(self.output.with_name('result-provenance.json').read_text())
        self.assertEqual('failed', report['status'])
        self.assertFalse(provenance['inspectionSucceeded'])
        self.assertEqual(hashlib.sha256(self.output.read_bytes()).hexdigest(), provenance['reportSha256'])
        return report, provenance

    def test_index_path_is_validated_before_reading_an_outside_amendment(self):
        outside = self.root / 'outside-amendment.json'
        outside.write_text(json.dumps({'approval': {'evidence': {'path': 'receipt.json'}}}))
        (self.owner / 'receipt.json').write_text('{"decision":"approved"}')
        for path in [os.path.relpath(outside, self.policy), str(outside)]:
            with self.subTest(path=path):
                self.amendment(index_path=path)
                result, _, scanned = self.run_helper()
                report, _ = self.failure(result)
                self.assertEqual('unsafe-path', report['errors'][0]['rule'])
                scanned.assert_not_called()
                self.assertEqual({'approval': {'evidence': {'path': 'receipt.json'}}},
                                 json.loads(outside.read_text()))

    def test_receipt_traversal_cannot_overwrite_or_create_outside_scratch(self):
        for exists in [True, False]:
            with self.subTest(existing_destination=exists):
                self.amendment(path='../outside.json')
                (self.root / 'outside.json').write_text('replacement')
                destination = self.root / 'scratch/outside.json'
                destination.parent.mkdir(exist_ok=True)
                if exists:
                    destination.write_text('preserve')
                elif destination.exists():
                    destination.unlink()
                result, _, scanned = self.run_helper()
                report, _ = self.failure(result)
                self.assertEqual('unsafe-path', report['errors'][0]['rule'])
                scanned.assert_not_called()
                self.assertEqual('preserve', destination.read_text()) if exists else self.assertFalse(destination.exists())

    def test_symlink_receipt_is_refused_before_copying(self):
        self.amendment()
        target = self.root / 'outside-receipt.json'
        target.write_text('{"decision":"approved"}')
        (self.owner / 'receipt.json').symlink_to(target)
        result, _, scanned = self.run_helper()
        report, _ = self.failure(result)
        self.assertEqual('amendment-approval-mismatch', report['errors'][0]['rule'])
        scanned.assert_not_called()
        self.assertEqual('{"decision":"approved"}', target.read_text())

    def test_source_diagnostic_is_redacted_in_stdout_and_retained_output(self):
        credential = 'source-' + 'derived-credential'
        diagnostic = 'unresolved source: ' + 'Bearer ' + credential
        self.report.update(status='failed', errors=[{'rule': diagnostic}])
        result, stdout, _ = self.run_helper()
        self.failure(result)
        for text in [stdout, self.output.read_text(), self.output.with_name('result-provenance.json').read_text()]:
            self.assertNotIn(credential, text)
        self.assertIn('[REDACTED]', stdout)
        self.assertIn('[REDACTED]', self.output.read_text())

    def test_failed_policy_rerun_replaces_prior_success_and_its_provenance(self):
        result, _, _ = self.run_helper()
        self.assertEqual(0, result)
        previous = json.loads(self.output.with_name('result-provenance.json').read_text())
        for invalid in [b'\xff', b'{', None]:
            with self.subTest(policy=invalid):
                if invalid is None:
                    self.index.unlink()
                else:
                    self.index.write_bytes(invalid)
                result, _, scanned = self.run_helper()
                report, provenance = self.failure(result)
                self.assertFalse(report['inspectionComplete'])
                self.assertFalse(provenance['scanReturned'])
                self.assertNotEqual(previous['attemptId'], provenance['attemptId'])
                scanned.assert_not_called()

    def test_metadata_refusal_is_unconditional_under_optimized_python(self):
        if not sys.flags.optimize:
            environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
            result = subprocess.run(
                [sys.executable, '-O', '-m', 'unittest', '-v',
                 'test_run_candidate_census.CandidateCensusTests.test_metadata_refusal_is_unconditional_under_optimized_python'],
                cwd=HERE, env=environment, capture_output=True, text=True, timeout=30)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            return

        def mutate(*_):
            (self.owner_git / 'index').write_bytes(b'changed')
            return self.report

        result, _, _ = self.run_helper(scan=mutate)
        report, provenance = self.failure(result)
        self.assertEqual('measured-git-file-content-changed', report['errors'][0]['rule'])
        self.assertFalse(provenance['measuredGitFileContentsUnchanged'])
        self.assertEqual(helper.MEASURED_SCOPE, provenance['measuredGitFileContentScope'])
        self.assertNotIn('objectStoreMetadataUnchanged', provenance)

    def test_prerequisite_failures_replace_prior_success_before_inspection(self):
        result, _, _ = self.run_helper()
        self.assertEqual(0, result)
        with mock.patch.object(Path, 'resolve', side_effect=OSError('fixture prerequisite unavailable')):
            result, _, scanned = self.run_helper()
        _, provenance = self.failure(result)
        self.assertFalse(provenance['scanReturned'])
        scanned.assert_not_called()
        with mock.patch.object(self.census, '__file__', str(self.root / 'missing-checker.py')):
            result, _, scanned = self.run_helper()
        _, provenance = self.failure(result)
        self.assertIsNone(provenance['checkerSha256'])
        scanned.assert_not_called()


if __name__ == '__main__':
    unittest.main()
