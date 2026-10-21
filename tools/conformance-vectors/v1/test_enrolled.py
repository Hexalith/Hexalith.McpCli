"""Regression checks for restoring the exact approved artifact before enrollment validation."""
import base64
import copy
import hashlib
import io
import json
import shutil
import subprocess
import sys
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile
import unittest
import check_enrolled
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

    def test_package_identity_is_case_insensitive(self):
        self.receipt['packageId'] = 'MODULE.contracts'
        self.assertEqual(self.artifact, artifact_for(self.assets, 'module.CONTRACTS', self.receipt))

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

    def test_duplicate_vector_paths_cannot_be_hidden_by_snapshot_capture(self):
        vector = self.root / 'read.vector.json'
        vector.write_text('{"operation":"module.read"}')
        with patch('verify_artifact.subprocess.run') as run:
            with self.assertRaisesRegex(RuntimeError, 'Duplicate vector paths'):
                verify(self.repo, self.artifact, [vector, vector], self.output)
        run.assert_not_called()
        self.assert_failed_without_old_success()

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


class EnrolledPreflightTests(unittest.TestCase):
    def setUp(self):
        VerifierFailureTests.setUp(self)
        self.package_id = 'Module.Contracts'
        self.directory = self.repo / 'tools/conformance-vectors/v1/modules' / self.package_id
        self.directory.mkdir(parents=True)
        self.vector = self.directory / 'read.vector.json'
        self.vector.write_text('{"operation":"module.read"}')
        self.inventory = self.repo / 'tools/inventory-coverage/v1/module-approved.json'
        self.inventory.parent.mkdir(parents=True)
        self.inventory.write_text('{"purpose":"fixture"}')
        cached = self.root / 'packages/module.contracts/1.0.0/module.contracts.1.0.0.nupkg'
        cached.parent.mkdir(parents=True)
        shutil.copy2(self.artifact, cached)
        digest = base64.b64encode(hashlib.sha512(cached.read_bytes()).digest()).decode('ascii')
        project = self.repo / 'src/Hexalith.McpCli/Hexalith.McpCli.csproj'
        (project.parent / 'obj').mkdir(parents=True)
        (project.parent / 'obj/project.assets.json').write_text(json.dumps({
            'libraries': {'Module.Contracts/1.0.0': {'type': 'package', 'path': 'module.contracts/1.0.0', 'sha512': digest}},
            'packageFolders': {str(self.root / 'packages'): {}}}))
        self.receipt = {'packageId': self.package_id, 'version': '1.0.0', 'module': 'module',
                        'artifactHash': 'sha512-' + digest, 'approvalReference': 'test-only fixture',
                        'inventorySha256': hashlib.sha256(self.inventory.read_bytes()).hexdigest(),
                        'vectorFilesSha256': {'read.vector.json': hashlib.sha256(self.vector.read_bytes()).hexdigest()}}
        self.child = self.output / self.package_id
        self.child.mkdir()
        (self.child / 'verification.json').write_text('{"result":"passed","checks":[{"label":"replay","exitCode":0}]}')
        (self.child / 'artifact.sha512').write_text('previous successful artifact')

    def invoke(self, verifier=None, evaluation_error=None):
        (self.directory / 'approval.json').write_text(json.dumps(self.receipt))
        evaluation = subprocess.CompletedProcess([], 0, json.dumps({'Items': {'PackageReference': [
            {'Identity': self.package_id, 'HexalithContracts': 'true'}]}}), '')
        captured = io.StringIO()
        with patch.object(check_enrolled, '__file__', str(self.repo / 'tools/conformance-vectors/v1/check_enrolled.py')), \
             patch.object(sys, 'argv', ['check_enrolled.py', '--output', str(self.output)]), \
             patch('check_enrolled.subprocess.run', side_effect=evaluation_error, return_value=evaluation), \
             patch('check_enrolled.verify', side_effect=verifier, return_value={'result': 'passed'}) as mocked, \
             redirect_stderr(captured), redirect_stdout(io.StringIO()):
            code = check_enrolled.main()
        return code, json.loads((self.output / 'enrolled.json').read_text()), captured.getvalue(), mocked

    def assert_invalidated_child(self):
        self.assertNotEqual('passed', json.loads((self.child / 'verification.json').read_text())['result'])
        self.assertFalse((self.child / 'artifact.sha512').exists())

    def test_inventory_requires_the_exact_approved_digest_before_verification(self):
        for mutation in ['changed bytes', 'missing digest', 'wrong digest', 'malformed digest']:
            with self.subTest(mutation=mutation):
                original = copy.deepcopy(self.receipt)
                if mutation == 'changed bytes':
                    self.inventory.write_text('{"purpose":"fixture","changed":true}')
                elif mutation == 'missing digest':
                    self.receipt.pop('inventorySha256')
                else:
                    self.receipt['inventorySha256'] = '0' * 64 if mutation == 'wrong digest' else []
                code, report, diagnostic, verifier = self.invoke()
                self.assertEqual(1, code)
                self.assertEqual('failed', report['result'])
                self.assertIn('inventorySha256', diagnostic)
                verifier.assert_not_called()
                self.assert_invalidated_child()
                self.receipt = original
                self.inventory.write_text('{"purpose":"fixture"}')

    def test_malformed_receipt_roots_fail_deterministically(self):
        for value in [[], 'text', 1, None, False]:
            with self.subTest(value=value):
                self.receipt = value
                code, report, diagnostic, verifier = self.invoke()
                self.assertEqual(1, code)
                self.assertEqual('failed', report['result'])
                self.assertIn('approval receipt must be a JSON object', diagnostic)
                self.assertNotIn('AttributeError', diagnostic)
                verifier.assert_not_called()
                self.assert_invalidated_child()

    def test_evaluation_failure_invalidates_old_child_success_before_preflight(self):
        code, report, diagnostic, verifier = self.invoke(evaluation_error=subprocess.CalledProcessError(9, ['dotnet'], stderr='specific evaluation failure'))
        self.assertEqual(1, code)
        self.assertEqual('failed', report['result'])
        self.assertIn('specific evaluation failure', diagnostic)
        verifier.assert_not_called()
        self.assert_invalidated_child()

    def test_existing_approval_directory_and_package_id_ignore_case(self):
        self.package_id = 'module.CONTRACTS'
        self.receipt['packageId'] = 'MODULE.contracts'
        self.directory = self.directory.rename(self.directory.with_name('mOdUlE.cOnTrAcTs'))
        self.vector = self.directory / self.vector.name
        code, report, _, verifier = self.invoke()
        self.assertEqual(0, code)
        self.assertEqual('passed', report['result'])
        self.assertEqual(self.receipt['inventorySha256'], verifier.call_args.kwargs['expected_inventory_hash'])
        self.assertEqual({str(self.vector.resolve()): self.receipt['vectorFilesSha256'][self.vector.name]},
                         verifier.call_args.kwargs['expected_vector_hashes'])

    def test_ambiguous_case_variant_directories_fail(self):
        entries = [Mock(), Mock()]
        for entry, name in zip(entries, ['Module.Contracts', 'module.contracts']):
            entry.name = name
            entry.is_dir.return_value = True
        with patch('check_enrolled.Path.iterdir', return_value=iter(entries)):
            code, report, diagnostic, verifier = self.invoke()
        self.assertEqual(1, code)
        self.assertEqual('failed', report['result'])
        self.assertIn('expected one approval directory', diagnostic)
        verifier.assert_not_called()

    def test_vector_mutation_between_preflight_and_capture_cannot_pass(self):
        def mutate(*args, **kwargs):
            self.vector.write_text('{"changed":"between preflight and verification"}')
            return verify(*args, **kwargs)
        code, report, diagnostic, _ = self.invoke(verifier=mutate)
        self.assertEqual(1, code)
        self.assertEqual('failed', report['result'])
        self.assertIn('Vector files differ from approval during snapshot capture', diagnostic)
        self.assert_invalidated_child()

    def test_inventory_mutation_between_preflight_and_capture_cannot_pass(self):
        def mutate(*args, **kwargs):
            self.inventory.write_text('{"changed":"between preflight and verification"}')
            return verify(*args, **kwargs)
        code, report, diagnostic, _ = self.invoke(verifier=mutate)
        self.assertEqual(1, code)
        self.assertEqual('failed', report['result'])
        self.assertIn('approved inventorySha256 during snapshot capture', diagnostic)
        self.assert_invalidated_child()


class FrozenArtifactInputTests(unittest.TestCase):
    setUp = VerifierFailureTests.setUp

    def test_mutating_original_inputs_during_restore_cannot_change_verified_bytes(self):
        vector = self.root / 'read.vector.json'
        vector.write_text('{"operation":"module.read"}')
        inventory = self.root / 'approved.json'
        inventory.write_text('{"purpose":"fixture"}')
        artifact_bytes, vector_bytes, inventory_bytes = self.artifact.read_bytes(), vector.read_bytes(), inventory.read_bytes()
        source_reads = {self.artifact: 0, vector: 0}
        original_read = Path.read_bytes
        def count_reads(path):
            if path in source_reads:
                source_reads[path] += 1
            return original_read(path)
        def execute(command, cwd, **kwargs):
            cwd = Path(cwd)
            stdout = '{}'
            if command[1] == 'restore':
                self.artifact.write_bytes(b'changed original artifact during restore')
                vector.write_text('{"changed":"during restore"}')
                inventory.write_text('{"changed":"during restore"}')
                feed = Path(next(value.split('=', 1)[1] for value in command if value.startswith('-p:RestoreAdditionalProjectSources=')))
                self.assertNotEqual(self.artifact.parent, feed)
                self.assertEqual(artifact_bytes, (feed / self.artifact.name).read_bytes())
                cached = cwd / 'packages/module.contracts/1.0.0/module.contracts.1.0.0.nupkg'
                cached.parent.mkdir(parents=True)
                cached.write_bytes(artifact_bytes)
                assets = cwd / 'host/obj/project.assets.json'
                assets.parent.mkdir()
                assets.write_text('{}')
            elif '--full-catalog' in command:
                stdout = json.dumps({'diagnostics': [], 'modules': [{'name': 'module', 'operations': [{'name': 'module.read'}]}]})
            elif 'describe' in command:
                stdout = '{"lintFindings":[]}'
            elif '--inventory' in command:
                self.assertEqual(inventory_bytes, Path(command[-1]).read_bytes())
            elif '--artifact' in command:
                supplied_artifact = Path(command[command.index('--artifact') + 1])
                self.assertNotEqual(self.artifact, supplied_artifact)
                self.assertEqual(artifact_bytes, supplied_artifact.read_bytes())
                self.assertNotEqual(vector, Path(command[-1]))
                self.assertEqual(vector_bytes, Path(command[-1]).read_bytes())
            return subprocess.CompletedProcess(command, 0, stdout, '')
        def validate(vectors, artifact, package, operations):
            self.assertEqual(artifact_bytes, artifact.read_bytes())
            self.assertEqual([vector_bytes], [path.read_bytes() for path in vectors])
            self.assertEqual(('Module.Contracts', '1.0.0'), package)
            self.assertEqual(['module.read'], operations)
            return []
        with patch('verify_artifact.subprocess.run', side_effect=execute), \
             patch('verify_artifact.resolved_packages', return_value=[]), \
             patch('verify_artifact.validate_vectors', side_effect=validate) as validation, \
             patch.object(Path, 'read_bytes', count_reads), redirect_stdout(io.StringIO()):
            receipt = verify(self.repo, self.artifact, [vector], self.output, inventory=inventory)
        self.assertEqual('passed', receipt['result'])
        self.assertEqual({self.artifact: 1, vector: 1}, source_reads)
        self.assertEqual(str(self.artifact), receipt['artifactSource'])
        self.assertEqual({str(vector): hashlib.sha256(vector_bytes).hexdigest()}, receipt['vectors'])
        self.assertEqual(artifact_bytes, (self.output / receipt['retainedInputs']['artifact']).read_bytes())
        self.assertEqual(vector_bytes, (self.output / receipt['retainedInputs']['vectors'][str(vector)]).read_bytes())
        validation.assert_called_once()
        self.assertTrue((self.output / 'artifact.sha512').exists())


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

    def test_matching_content_metadata_without_archive_sidecar_cannot_authorize_signed_bytes(self):
        canonical = 'NuGet canonical restore content hash'
        self.assets['libraries']['Module.Contracts/1.0.0']['sha512'] = canonical
        (self.artifact.parent / '.nupkg.metadata').write_text(json.dumps({'contentHash': canonical}))
        for archive in [b'original signed archive', b'changed signed dependency archive']:
            with self.subTest(archive=archive):
                self.artifact.write_bytes(archive)
                with self.assertRaisesRegex(RuntimeError, 'independent cached archive hash is required'):
                    resolved_packages(self.assets)

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
