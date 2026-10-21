"""Regression checks for restoring the exact approved artifact before enrollment validation."""
import base64
import copy
import hashlib
import io
import json
import subprocess
import zipfile
from contextlib import redirect_stderr
from unittest.mock import patch
from pathlib import Path
import tempfile
import unittest
from check_enrolled import artifact_for, approved_vectors
from verify_artifact import check_lint, resolved_packages, verify


class EnrolledArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.artifact = self.root / 'module.contracts/1.0.0/module.contracts.1.0.0.nupkg'
        self.artifact.parent.mkdir(parents=True)
        self.artifact.write_bytes(b'exact restored package bytes')
        digest = base64.b64encode(hashlib.sha512(self.artifact.read_bytes()).digest()).decode('ascii')
        self.assets = {'libraries': {'Module.Contracts/1.0.0': {'type': 'package', 'path': 'module.contracts/1.0.0', 'sha512': digest}},
                       'packageFolders': {str(self.root): {}}}
        self.receipt = {'packageId': 'Module.Contracts', 'version': '1.0.0', 'artifactHash': 'sha512-' + digest,
                        'approvalReference': 'test-only owner fixture'}

    def test_matches_both_restored_and_approved_bytes(self):
        self.assertEqual(self.artifact, artifact_for(self.assets, 'Module.Contracts', self.receipt))

    def test_replacing_restored_package_bytes_fails(self):
        self.artifact.write_bytes(b'same package version, different bytes')
        with self.assertRaisesRegex(RuntimeError, 'restored bytes differ'):
            artifact_for(self.assets, 'Module.Contracts', self.receipt)

    def test_assets_cannot_authorize_changed_bytes_without_approval(self):
        self.artifact.write_bytes(b'new package bytes')
        self.assets['libraries']['Module.Contracts/1.0.0']['sha512'] = base64.b64encode(hashlib.sha512(self.artifact.read_bytes()).digest()).decode('ascii')
        with self.assertRaisesRegex(RuntimeError, 'restored bytes differ'):
            artifact_for(self.assets, 'Module.Contracts', self.receipt)

    def test_other_versions_and_missing_approval_do_not_pass(self):
        for field, value in [('version', '2.0.0'), ('packageId', 'Other.Contracts'), ('approvalReference', '')]:
            with self.subTest(field=field):
                receipt = copy.deepcopy(self.receipt)
                receipt[field] = value
                with self.assertRaises(RuntimeError):
                    artifact_for(self.assets, 'Module.Contracts', receipt)

    def test_missing_restored_package_fails(self):
        self.artifact.unlink()
        with self.assertRaisesRegex(RuntimeError, 'unavailable'):
            artifact_for(self.assets, 'Module.Contracts', self.receipt)

    def test_missing_enrolled_package_fails(self):
        self.assets['libraries'] = {}
        with self.assertRaisesRegex(RuntimeError, 'expected one exact restored package'):
            artifact_for(self.assets, 'Module.Contracts', self.receipt)


class AcceptedLintTests(unittest.TestCase):
    def test_exact_accepted_lint_preserves_existing_contract_approval(self):
        finding = {'operation': 'tenants.list-tenants', 'code': 'payload_paging_member', 'property': '/properties/PageSize'}
        accepted = dict(finding, approvalReference='test-only previous approval')
        check_lint([finding], [accepted])
        for field, value in [('operation', 'parties.list-parties'), ('property', '/properties/Cursor'), ('code', 'missing_description')]:
            with self.subTest(field=field):
                changed = dict(finding, **{field: value})
                with self.assertRaisesRegex(RuntimeError, 'differs from exact approvals'):
                    check_lint([changed], [accepted])

    def test_missing_and_stale_lint_approvals_fail(self):
        finding = {'operation': 'parties.list-parties', 'code': 'payload_paging_member', 'property': '/properties/PageSize'}
        with self.assertRaises(RuntimeError):
            check_lint([finding], [])
        with self.assertRaises(RuntimeError):
            check_lint([], [dict(finding, approvalReference='test-only')])
        with self.assertRaises(RuntimeError):
            check_lint([], [dict(finding, approvalReference='')])


class ApprovedVectorSetTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.first = self.root / 'first.vector.json'
        self.second = self.root / 'nested/second.vector.json'
        self.second.parent.mkdir()
        self.first.write_text('{"operation":"module.first"}')
        self.second.write_text('{"operation":"module.second"}')
        self.receipt = {'vectorFilesSha256': {p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                            for p in [self.first, self.second]}}

    def test_matches_all_approved_relative_names_and_bytes(self):
        self.assertEqual([self.first, self.second], approved_vectors(self.root, self.receipt))

    def test_changed_vector_cannot_reuse_approved_artifact_receipt(self):
        self.first.write_text('{"operation":"module.first","assertions":[]}')
        with self.assertRaisesRegex(RuntimeError, 'differ from approval'):
            approved_vectors(self.root, self.receipt)

    def test_added_vector_cannot_hide_from_coverage(self):
        (self.root / 'added.vector.json').write_text('{}')
        with self.assertRaisesRegex(RuntimeError, 'differ from approval'):
            approved_vectors(self.root, self.receipt)

    def test_removed_or_renamed_vector_requires_fresh_approval(self):
        self.second.rename(self.root / 'renamed.vector.json')
        with self.assertRaisesRegex(RuntimeError, 'differ from approval'):
            approved_vectors(self.root, self.receipt)

    def test_missing_filename_hash_map_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, 'Missing complete approved vector'):
            approved_vectors(self.root, {})


class MalformedAcceptedLintTests(unittest.TestCase):
    def test_only_an_array_of_objects_is_accepted(self):
        for malformed in [{}, "", 0, False, None, [""], [[]], [None]]:
            with self.subTest(value=malformed):
                with self.assertRaises(RuntimeError):
                    check_lint([], malformed)
        check_lint([], [])


class VerifierFailureTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root / 'repo'
        for name in ['src', 'references/Hexalith.Builds/Props', 'tests/Hexalith.McpCli.ConformanceHost', 'tests/Hexalith.McpCli.Core.Tests']:
            (self.repo / name).mkdir(parents=True, exist_ok=True)
        (self.repo / 'Directory.Packages.props').write_text('<Project />')
        (self.repo / 'tests/Hexalith.McpCli.ConformanceHost/Program.cs').write_text('// test fixture')
        self.artifact = self.root / 'Module.Contracts.1.0.0.nupkg'
        with zipfile.ZipFile(self.artifact, 'w') as archive:
            archive.writestr('Module.Contracts.nuspec', '<package><metadata><id>Module.Contracts</id><version>1.0.0</version></metadata></package>')
        self.output = self.root / 'output'
        self.output.mkdir()
        (self.output / 'verification.json').write_text('{"result":"passed"}')
        (self.output / 'artifact.sha512').write_text('old successful hash')

    def assert_failed_without_old_success(self):
        receipt = json.loads((self.output / 'verification.json').read_text())
        self.assertEqual('failed', receipt['result'])
        self.assertFalse((self.output / 'artifact.sha512').exists())
        return receipt

    def test_missing_artifact_invalidates_previous_success_before_preflight(self):
        with self.assertRaises(FileNotFoundError):
            verify(self.repo, self.root / 'missing.nupkg', [], self.output)
        self.assert_failed_without_old_success()

    def test_wrong_artifact_hash_retains_failed_identity(self):
        with self.assertRaisesRegex(RuntimeError, 'hash differs'):
            verify(self.repo, self.artifact, [], self.output, expected_hash='old approved bytes')
        self.assertEqual('Module.Contracts', self.assert_failed_without_old_success()['packageId'])

    def test_subprocess_failure_retains_and_prints_diagnostics_and_freezes_approval_inputs(self):
        inventory = self.root / 'inventory.json'
        accepted = self.root / 'lint.json'
        inventory.write_text('{"purpose":"fixture"}')
        accepted.write_text('[]')
        original = inventory.read_bytes()
        def fail_restore(command, **kwargs):
            pending = json.loads((self.output / 'verification.json').read_text())
            self.assertEqual('pending', pending['result'])
            inventory.write_text('{"changed":"after input capture"}')
            return subprocess.CompletedProcess(command, 7, 'useful restore stdout', 'specific restore failure')
        captured = io.StringIO()
        with patch('verify_artifact.subprocess.run', side_effect=fail_restore), redirect_stderr(captured):
            with self.assertRaisesRegex(RuntimeError, 'restore failed with exit 7'):
                verify(self.repo, self.artifact, [], self.output, inventory=inventory, accepted_lint=accepted)
        receipt = self.assert_failed_without_old_success()
        self.assertEqual(hashlib.sha256(original).hexdigest(), receipt['approvalInputs']['inventory']['sha256'])
        self.assertEqual(original, (self.output / receipt['approvalInputs']['inventory']['retainedInput']).read_bytes())
        self.assertEqual(hashlib.sha256(b'[]').hexdigest(), receipt['approvalInputs']['acceptedLint']['sha256'])
        self.assertIn('useful restore stdout', captured.getvalue())
        self.assertIn('specific restore failure', captured.getvalue())
        self.assertEqual('specific restore failure', (self.output / 'restore.stderr.txt').read_text())
        self.assertEqual(7, receipt['checks'][0]['exitCode'])


class ResolvedPackageEvidenceTests(unittest.TestCase):
    setUp = EnrolledArtifactTests.setUp

    def test_records_actual_restored_version_and_both_hashes(self):
        records = resolved_packages(self.assets)
        self.assertEqual('Module.Contracts', records[0]['id'])
        self.assertEqual('1.0.0', records[0]['version'])
        self.assertEqual(self.receipt['artifactHash'], records[0]['artifactHash'])
        self.assertEqual(records[0]['assetsHash'], records[0]['artifactHash'])

    def test_changed_resolved_support_bytes_fail(self):
        self.artifact.write_bytes(b'modified restored support package')
        with self.assertRaisesRegex(RuntimeError, 'differ from the assets content hash'):
            resolved_packages(self.assets)


class SignedPackageHashTests(unittest.TestCase):
    setUp = EnrolledArtifactTests.setUp

    def test_restore_content_hash_and_exact_archive_hash_can_differ(self):
        canonical = 'NuGet canonical restore content hash'
        self.assets['libraries']['Module.Contracts/1.0.0']['sha512'] = canonical
        (self.artifact.parent / '.nupkg.metadata').write_text(json.dumps({'contentHash': canonical}))
        self.artifact.with_suffix('.nupkg.sha512').write_text(self.receipt['artifactHash'].removeprefix('sha512-'))
        self.assertEqual(self.artifact, artifact_for(self.assets, 'Module.Contracts', self.receipt))
        restored = resolved_packages(self.assets)[0]
        self.assertEqual('sha512-' + canonical, restored['assetsHash'])
        self.assertEqual(self.receipt['artifactHash'], restored['artifactHash'])
        self.assertNotEqual(restored['assetsHash'], restored['artifactHash'])
        self.artifact.write_bytes(b'changed signed archive bytes')
        with self.assertRaisesRegex(RuntimeError, 'cached archive hash'):
            artifact_for(self.assets, 'Module.Contracts', self.receipt)
