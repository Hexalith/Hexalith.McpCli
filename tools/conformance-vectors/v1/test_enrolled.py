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
import xml.etree.ElementTree as ET
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

    def test_accepted_lint_requires_exact_fields_and_unique_exceptions(self):
        accepted = {'operation': 'tenants.list-tenants', 'code': 'payload_paging_member',
                    'property': '/properties/PageSize', 'approvalReference': 'test-only previous approval'}
        for field in accepted:
            with self.subTest(missing=field):
                changed = {key: value for key, value in accepted.items() if key != field}
                with self.assertRaisesRegex(RuntimeError, '^Accepted lint requires exact operation, code, property and approvalReference\\.$'):
                    check_lint([], [changed])
        for changed in [dict(accepted, extra='unapproved field'),
                        {key if key != 'approvalReference' else 'reference': value for key, value in accepted.items()}]:
            with self.subTest(row=changed):
                with self.assertRaisesRegex(RuntimeError, '^Accepted lint requires exact operation, code, property and approvalReference\\.$'):
                    check_lint([], [changed])
        with self.assertRaisesRegex(RuntimeError, '^Duplicate accepted lint exception\\.$'):
            check_lint([], [accepted, dict(accepted)])


class VerifierFailureTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.repo = self.root / 'repo'
        for name in ['src', 'references/Hexalith.Builds/Props', 'tests/Hexalith.McpCli.ConformanceHost', 'tests/Hexalith.McpCli.Core.Tests']:
            (self.repo / name).mkdir(parents=True, exist_ok=True)
        (self.repo / 'Directory.Packages.props').write_text('<Project />')
        project = self.repo / 'src/Hexalith.McpCli/Hexalith.McpCli.csproj'
        project.parent.mkdir(parents=True)
        project.write_text('<Project />')
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

    def test_path_bearing_package_identity_cannot_escape_the_frozen_feed(self):
        sentinel = self.root / 'sentinel.1.0.0.nupkg'
        sentinel_bytes = b'existing file outside the frozen feed'
        malformed = [('id', str(self.root / 'sentinel')), ('id', '../../../sentinel'),
                     ('id', r'..\..\..\sentinel'), ('id', r'C:\sentinel'), ('id', r'C:sentinel'),
                     ('id', r'\sentinel'), ('id', r'\\server\share\sentinel'), ('id', 'CON'),
                     ('id', 'Module?Contracts'), ('version', '../sentinel'), ('version', r'..\sentinel'),
                     ('version', r'C:\sentinel'), ('version', '1.0.0:sentinel')]
        for field, value in malformed:
            with self.subTest(field=field, value=value):
                sentinel.write_bytes(sentinel_bytes)
                (self.output / 'verification.json').write_text('{"result":"passed"}')
                (self.output / 'artifact.sha512').write_text('old successful hash')
                identity = {'id': 'Module.Contracts', 'version': '1.0.0', field: value}
                nuspec = ET.Element('package')
                metadata = ET.SubElement(nuspec, 'metadata')
                for key, text in identity.items():
                    ET.SubElement(metadata, key).text = text
                with zipfile.ZipFile(self.artifact, 'w') as archive:
                    archive.writestr('Module.Contracts.nuspec', ET.tostring(nuspec))
                with patch('verify_artifact.subprocess.run') as run:
                    try:
                        with self.assertRaisesRegex(RuntimeError, '^Artifact package identity must form a single safe filename\\.$'):
                            verify(self.repo, self.artifact, [], self.output)
                    finally:
                        self.assertEqual(sentinel_bytes, sentinel.read_bytes())
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
            self.assertFalse((self.output / 'artifact.sha512').exists())
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


class CandidateHostPreparationTests(unittest.TestCase):
    setUp = VerifierFailureTests.setUp

    def test_candidate_dependency_overrides_apply_only_when_alignment_is_enabled(self):
        dependencies = {'Hexalith.EventStore.Contracts': '3.125.1', 'Hexalith.Commons.UniqueIds': '2.30.2'}
        nuspec = ET.Element('package')
        metadata = ET.SubElement(nuspec, 'metadata')
        ET.SubElement(metadata, 'id').text = 'Module.Contracts'
        ET.SubElement(metadata, 'version').text = '1.0.0'
        group = ET.SubElement(metadata, 'dependencies')
        for name, version in dependencies.items():
            ET.SubElement(group, 'dependency', id=name, version=version)
        with zipfile.ZipFile(self.artifact, 'w') as archive:
            archive.writestr('Module.Contracts.nuspec', ET.tostring(nuspec))
        for align in [True, False]:
            with self.subTest(align_candidate_dependencies=align):
                expected = ['-p:HexalithEventStoreVersion=3.125.1', '-p:HexalithCommonsVersion=2.30.2'] if align else []
                def execute(command, cwd, **kwargs):
                    if command[1] == 'restore':
                        assets = Path(cwd) / 'host/obj/project.assets.json'
                        assets.parent.mkdir()
                        assets.write_text('{}')
                        feed = command[-1]
                        self.assertTrue(feed.startswith('-p:RestoreAdditionalProjectSources='))
                        self.assertEqual(['dotnet', 'restore', 'host/ArtifactHost.csproj', *expected, feed], command)
                        return subprocess.CompletedProcess(command, 0, '', '')
                    self.assertEqual(['dotnet', 'build', 'host/ArtifactHost.csproj', '--no-restore', '-c',
                                      'Release', '-m:1', '-warnaserror', *expected], command)
                    return subprocess.CompletedProcess(command, 7, '', '')
                # Omitting the true flag also pins the documented default candidate path.
                options = {} if align else {'align_candidate_dependencies': False}
                with patch('verify_artifact.subprocess.run', side_effect=execute) as run, \
                     patch('verify_artifact.resolved_packages', return_value=[]):
                    with self.assertRaisesRegex(RuntimeError, 'build failed with exit 7'):
                        verify(self.repo, self.artifact, [], self.output, **options)
                self.assertEqual(2, run.call_count)
                receipt = json.loads((self.output / 'verification.json').read_text())
                self.assertEqual('failed', receipt['result'])
                self.assertEqual(dependencies, receipt['artifactDependencies'])
                self.assertEqual(expected, receipt['candidateDependencyOverrides'])

    def test_candidate_host_removes_inherited_contracts_but_preserves_stack_references(self):
        project = self.repo / 'src/Hexalith.McpCli/Hexalith.McpCli.csproj'
        project.write_text('''<Project><ItemGroup>
          <PackageReference Include="Existing.Contracts" HexalithContracts="true" />
          <PackageReference Include="Metadata.Contracts"><HexalithContracts>TRUE</HexalithContracts></PackageReference>
          <PackageReference Include="LowerAttribute.Contracts" hexalithcontracts="true" />
          <PackageReference Include="MixedAttribute.Contracts" hexalithContracts="TRUE" />
          <PackageReference Include="LowerElement.Contracts"><hexalithcontracts>true</hexalithcontracts></PackageReference>
          <PackageReference Include="MixedElement.Contracts"><hexalithContracts>TRUE</hexalithContracts></PackageReference>
          <PackageReference Include="Hexalith.EventStore.Contracts" hexalithcontracts="false" />
          <PackageReference Include="Microsoft.Extensions.Hosting"><hexalithContracts>FALSE</hexalithContracts></PackageReference>
        </ItemGroup></Project>''')
        def inspect_restore(command, cwd, **kwargs):
            selected = ET.parse(Path(cwd) / 'src/Hexalith.McpCli/Hexalith.McpCli.csproj')
            self.assertEqual(['Hexalith.EventStore.Contracts', 'Microsoft.Extensions.Hosting'],
                             [item.get('Include') for item in selected.iter('PackageReference')])
            host = ET.parse(Path(cwd) / 'host/ArtifactHost.csproj')
            self.assertEqual(['Module.Contracts'], [item.get('Include') for item in host.iter('PackageReference')])
            return subprocess.CompletedProcess(command, 7, '', '')
        with patch('verify_artifact.subprocess.run', side_effect=inspect_restore) as run:
            with self.assertRaisesRegex(RuntimeError, 'restore failed with exit 7'):
                verify(self.repo, self.artifact, [], self.output)
        run.assert_called_once()

    def test_candidate_pin_replaces_existing_versions_and_adds_unlisted_packages(self):
        for prior_version in [None, '0.9.0']:
            with self.subTest(prior_version=prior_version):
                props = self.repo / 'Directory.Packages.props'
                props.write_text('<Project />' if prior_version is None else
                                 f'<Project><ItemGroup><PackageVersion Include="Module.Contracts" Version="{prior_version}" /></ItemGroup></Project>')
                def inspect_restore(command, cwd, **kwargs):
                    selected = ET.parse(Path(cwd) / 'Directory.Packages.props')
                    pins = [item.attrib for item in selected.iter('PackageVersion')]
                    self.assertEqual([{'Remove': 'Module.Contracts'}, {'Include': 'Module.Contracts', 'Version': '1.0.0'}], pins[-2:])
                    return subprocess.CompletedProcess(command, 7, '', '')
                with patch('verify_artifact.subprocess.run', side_effect=inspect_restore) as run:
                    with self.assertRaisesRegex(RuntimeError, 'restore failed with exit 7'):
                        verify(self.repo, self.artifact, [], self.output)
                run.assert_called_once()


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
        self.seed_successful_child()

    def seed_successful_child(self):
        (self.child / 'verification.json').write_text('{"result":"passed","checks":[{"label":"replay","exitCode":0}]}')
        (self.child / 'artifact.sha512').write_text('previous successful artifact')

    def invoke(self, verifier=None, evaluation_error=None, contracts_metadata='HexalithContracts', local=False, missing=None, required=None,
               production_error=None):
        (self.directory / 'approval.json').write_text(json.dumps(self.receipt))
        evaluation = subprocess.CompletedProcess([], 0, json.dumps({'Items': {'PackageReference': [
            {'Identity': self.package_id, contracts_metadata: 'true'}]}}), '')
        captured = io.StringIO()
        with patch.object(check_enrolled, '__file__', str(self.repo / 'tools/conformance-vectors/v1/check_enrolled.py')), \
             patch.object(sys, 'argv', ['check_enrolled.py', '--output', str(self.output)] + (['--local'] if local else [])), \
             patch('check_enrolled.subprocess.run', side_effect=evaluation_error, return_value=evaluation), \
             patch('check_enrolled.verify', side_effect=verifier, return_value={'result': 'passed'}) as mocked, \
             patch('check_enrolled.production_replay', side_effect=production_error,
                   return_value={'result': 'passed', 'modules': ['module']}), \
             patch('check_enrolled.required_scope', side_effect=lambda path, modules: sorted(set(required) - modules) if required is not None else missing or []), \
             redirect_stderr(captured), redirect_stdout(io.StringIO()):
            code = check_enrolled.main()
        return code, json.loads((self.output / 'enrolled.json').read_text()), captured.getvalue(), mocked

    def assert_invalidated_child(self):
        self.assertNotEqual('passed', json.loads((self.child / 'verification.json').read_text())['result'])
        self.assertFalse((self.child / 'artifact.sha512').exists())

    def test_failed_production_rerun_removes_previous_observations_and_all_production_logs(self):
        observations = self.output / 'production-observations'
        observations.mkdir()
        stale = observations / 'old.json'
        stale.write_text('{"documents":[{"status":"accepted"}]}')
        logs = [self.output / f'production-{phase}.{stream}.txt'
                for phase in ['restore', 'build', 'replay'] for stream in ['stdout', 'stderr']]
        for log in logs:
            log.write_text('PASS previous production run')
        code, report, diagnostic, verifier = self.invoke(production_error=RuntimeError('production restore failed'))
        self.assertEqual(1, code)
        self.assertEqual('failed', report['result'])
        self.assertFalse(report['fullV1Accepted'])
        self.assertEqual('production restore failed', report['error'])
        self.assertEqual('production restore failed\n', diagnostic)
        self.assertFalse(stale.exists())
        self.assertEqual([], [log.name for log in logs if log.exists()])
        verifier.assert_called_once()

    def test_inventory_requires_the_exact_approved_digest_before_verification(self):
        for mutation in ['changed bytes', 'missing digest', 'wrong digest', 'malformed digest']:
            with self.subTest(mutation=mutation):
                self.seed_successful_child()
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
                self.seed_successful_child()
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
        self.assertIs(False, verifier.call_args.kwargs['align_candidate_dependencies'])
        self.assertEqual(self.receipt['inventorySha256'], verifier.call_args.kwargs['expected_inventory_hash'])
        self.assertEqual({str(self.vector.resolve()): self.receipt['vectorFilesSha256'][self.vector.name]},
                         verifier.call_args.kwargs['expected_vector_hashes'])

    def test_enrollment_metadata_name_is_case_insensitive(self):
        for metadata in ['HexalithContracts', 'hexalithcontracts', 'hexalithContracts', 'HEXALITHCONTRACTS']:
            with self.subTest(metadata=metadata):
                code, report, diagnostic, verifier = self.invoke(contracts_metadata=metadata)
                self.assertEqual(0, code)
                self.assertEqual('passed', report['result'])
                self.assertEqual([self.package_id], report['packages'])
                self.assertEqual([{'result': 'passed', 'approvedModule': 'module'}], report['results'])
                self.assertEqual('', diagnostic)
                verifier.assert_called_once()
                self.assertEqual(self.artifact.read_bytes(), verifier.call_args.args[1].read_bytes())
                self.assertIs(False, verifier.call_args.kwargs['align_candidate_dependencies'])

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

    def test_missing_approval_directory_fails_before_verification(self):
        with patch('check_enrolled.Path.iterdir', return_value=iter([])):
            code, report, diagnostic, verifier = self.invoke()
        self.assertEqual(1, code)
        self.assertEqual('failed', report['result'])
        self.assertEqual('Module.Contracts: expected one approval directory (package IDs are case-insensitive).\n', diagnostic)
        verifier.assert_not_called()
        self.assert_invalidated_child()

    def test_missing_or_invalid_module_names_fail_before_verification(self):
        for value in [None, '', 7, 'module/name', 'module\\name']:
            with self.subTest(module=value):
                self.seed_successful_child()
                self.receipt['module'] = value
                code, report, diagnostic, verifier = self.invoke()
                self.assertEqual(1, code)
                self.assertEqual('failed', report['result'])
                self.assertEqual('Module.Contracts: receipt requires a canonical module name.\n', diagnostic)
                verifier.assert_not_called()
                self.assert_invalidated_child()

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


    def test_missing_required_module_fails_full_gate_after_available_replay(self):
        code, report, diagnostic, verifier = self.invoke(missing=['tenants'])
        self.assertEqual(1, code)
        self.assertEqual('failed', report['result'])
        self.assertFalse(report['fullV1Accepted'])
        self.assertEqual(['tenants'], report['missingRequiredModules'])
        self.assertEqual({'result': 'passed', 'modules': ['module']}, report['productionReplay'])
        self.assertIn('Full-v1 gate: missing required production module(s): tenants', diagnostic)
        verifier.assert_called_once()

    def test_local_evidence_cannot_grant_full_acceptance_even_when_scope_is_present(self):
        for missing in [[], ['tenants']]:
            with self.subTest(missing=missing):
                code, report, diagnostic, _ = self.invoke(local=True, missing=missing)
                self.assertEqual(0, code)
                self.assertEqual('local-only', report['result'])
                self.assertFalse(report['fullV1Accepted'])
                self.assertEqual(missing, report['missingRequiredModules'])
                self.assertEqual('', diagnostic)


    def test_full_scope_comes_from_combined_discovery_instead_of_receipt_labels(self):
        self.receipt['module'] = 'tenants'
        shutil.copy2(self.inventory, self.inventory.with_name('tenants-approved.json'))
        code, report, diagnostic, _ = self.invoke(required=['tenants'])
        self.assertEqual(1, code)
        self.assertFalse(report['fullV1Accepted'])
        self.assertEqual(['tenants'], report['missingRequiredModules'])
        self.assertIn('missing required production module(s): tenants', diagnostic)


class FrozenArtifactInputTests(unittest.TestCase):
    setUp = VerifierFailureTests.setUp

    def test_mutating_original_inputs_during_restore_cannot_change_verified_bytes(self):
        self.artifact = self.artifact.rename(self.root / 'download.nupkg')
        expected_filename = 'Module.Contracts.1.0.0.nupkg'
        (self.root / expected_filename.lower()).write_bytes(b'unselected package with the canonical filename')
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
                self.assertEqual([expected_filename], [path.name for path in feed.glob('*.nupkg')])
                self.assertEqual(artifact_bytes, (feed / expected_filename).read_bytes())
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
        self.assertEqual(expected_filename, Path(receipt['retainedInputs']['artifact']).name)
        self.assertEqual({str(vector): hashlib.sha256(vector_bytes).hexdigest()}, receipt['vectors'])
        self.assertEqual(artifact_bytes, (self.output / receipt['retainedInputs']['artifact']).read_bytes())
        self.assertEqual(vector_bytes, (self.output / receipt['retainedInputs']['vectors'][str(vector)]).read_bytes())
        validation.assert_called_once()
        self.assertTrue((self.output / 'artifact.sha512').exists())

    def test_unapproved_lint_blocks_replay_and_exact_acceptance_allows_completion(self):
        vector = self.root / 'read.vector.json'
        vector.write_text('{"operation":"module.read"}')
        finding = {'code': 'missing_description', 'severity': 'warning', 'message': 'Missing description.',
                   'property': '/properties/Name'}
        accepted = self.root / 'accepted-lint.json'
        accepted.write_text(json.dumps([{'operation': 'module.read', 'code': finding['code'],
                                         'property': finding['property'], 'approvalReference': 'test-only recorded approval'}]))
        artifact_bytes = self.artifact.read_bytes()
        def execute(command, cwd, **kwargs):
            cwd = Path(cwd)
            stdout, exit_code = '{}', 0
            if command[1] == 'restore':
                cached = cwd / 'packages/module.contracts/1.0.0/module.contracts.1.0.0.nupkg'
                cached.parent.mkdir(parents=True)
                cached.write_bytes(artifact_bytes)
                assets = cwd / 'host/obj/project.assets.json'
                assets.parent.mkdir()
                assets.write_text('{}')
            elif '--full-catalog' in command:
                stdout = json.dumps({'diagnostics': [], 'modules': [{'name': 'module', 'operations': [{'name': 'module.read'}]}]})
            elif 'describe' in command:
                stdout, exit_code = json.dumps({'lintFindings': [finding]}), 1
            return subprocess.CompletedProcess(command, exit_code, stdout, '')
        for accepted_lint in [None, accepted]:
            with self.subTest(accepted=accepted_lint is not None):
                (self.output / 'artifact.sha512').write_text('old successful hash')
                with patch('verify_artifact.subprocess.run', side_effect=execute), \
                     patch('verify_artifact.resolved_packages', return_value=[]), \
                     patch('verify_artifact.validate_vectors', return_value=[]) as validation, redirect_stdout(io.StringIO()):
                    if accepted_lint is None:
                        with self.assertRaisesRegex(RuntimeError, 'Description lint differs from exact approvals: unapproved='):
                            verify(self.repo, self.artifact, [vector], self.output)
                    else:
                        verify(self.repo, self.artifact, [vector], self.output, accepted_lint=accepted_lint)
                receipt = json.loads((self.output / 'verification.json').read_text())
                self.assertEqual([1], [check['exitCode'] for check in receipt['checks'] if check['label'] == 'module.read'])
                replays = [check for check in receipt['checks'] if check['label'] == 'replay']
                if accepted_lint is None:
                    self.assertEqual('failed', receipt['result'])
                    self.assertFalse((self.output / 'artifact.sha512').exists())
                    self.assertEqual([], replays)
                    validation.assert_not_called()
                else:
                    self.assertEqual('passed', receipt['result'])
                    self.assertEqual([0], [check['exitCode'] for check in replays])
                    self.assertTrue((self.output / 'artifact.sha512').exists())
                    self.assertEqual(str(accepted), receipt['acceptedLint'])
                    validation.assert_called_once()


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

class FullV1ScopeTests(unittest.TestCase):
    def test_required_modules_cannot_be_replaced_by_local_green(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'v1-scope.json'
            source.write_text(json.dumps({'requiredModules': ['parties', 'tenants']}))
            self.assertEqual(['tenants'], check_enrolled.required_scope(source, {'parties', 'sample'}))
            self.assertEqual([], check_enrolled.required_scope(source, {'parties', 'tenants'}))
            for invalid in [{}, {'requiredModules': []}, {'requiredModules': ['parties', 'parties']},
                            {'requiredModules': [None]}, []]:
                source.write_text(json.dumps(invalid))
                with self.subTest(invalid=invalid), self.assertRaisesRegex(RuntimeError, 'requiredModules'):
                    check_enrolled.required_scope(source, {'parties', 'tenants'})


class CombinedConsumptionHashTests(unittest.TestCase):
    def test_combined_replay_uses_retained_inputs_host_assets_and_every_approved_module(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            output = repo / 'evidence'
            receipts, selections = [], []
            for module in ['first', 'second']:
                package_id = module.title() + '.Contracts'
                retained = output / package_id / 'inputs-retained'
                retained.mkdir(parents=True)
                artifact = retained / 'contracts.nupkg'
                artifact.write_bytes(b'retained package bytes')
                vector = retained / 'read.vector.json'
                vector.write_text(json.dumps({'operation': module + '.read'}))
                receipts.append({'packageId': package_id, 'version': '1.0.0', 'approvedModule': module,
                    'operations': [module + '.read'], 'retainedInputs': {
                        'artifact': 'inputs-retained/contracts.nupkg',
                        'vectors': {'original/read.json': 'inputs-retained/read.vector.json'}},
                    'vectors': {'original/read.json': hashlib.sha256(vector.read_bytes()).hexdigest()}})
                selections.append((artifact, (package_id, '1.0.0'), [vector]))
            with patch('check_enrolled.subprocess.run', return_value=subprocess.CompletedProcess([], 0, '', '')), \
                    patch('check_enrolled.run_catalog', return_value={'modules': ['first', 'second']}) as replay:
                progress = check_enrolled.production_replay(repo, output, receipts)
            host = repo / 'tests/Hexalith.McpCli.ConformanceHost'
            replay.assert_called_once_with(host / 'bin/Release/net10.0/Hexalith.McpCli.ConformanceHost.dll', selections,
                assets_path=host / 'obj/project.assets.json', evidence_dir=output / 'production-observations',
                expected_modules={'First.Contracts': 'first', 'Second.Contracts': 'second'})
            self.assertEqual('passed', progress['result'])
            self.assertEqual(2, progress['operationCount'])

    def test_retained_vector_mutation_during_production_build_blocks_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / 'evidence'
            package = output / 'Module.Contracts'
            package.mkdir(parents=True)
            vector = package / 'read.vector.json'
            vector.write_text('{"operation":"module.read"}')
            receipt = {'packageId': 'Module.Contracts', 'version': '1.0.0', 'approvedModule': 'module',
                       'operations': ['module.read'],
                       'retainedInputs': {'artifact': 'module.nupkg', 'vectors': {'original.json': vector.name}},
                       'vectors': {'original.json': hashlib.sha256(vector.read_bytes()).hexdigest()}}
            def build(command, **kwargs):
                if command[1] == 'build':
                    vector.write_text('{"operation":"module.read","changed":true}')
                return subprocess.CompletedProcess(command, 0, '', '')
            with patch('check_enrolled.subprocess.run', side_effect=build), \
                    patch('check_enrolled.run_catalog') as replay:
                with self.assertRaisesRegex(RuntimeError, 'retained vector bytes differ from recorded verification hash'):
                    check_enrolled.production_replay(root, output, [receipt])
            replay.assert_not_called()


class ProductionProgressTests(unittest.TestCase):
    def test_restore_build_and_replay_failures_retain_structured_progress_in_enrolled_json(self):
        for failed_phase in ['production-restore', 'production-build', 'production-replay']:
            with self.subTest(phase=failed_phase), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                output = root / 'evidence'
                package = output / 'Module.Contracts'
                package.mkdir(parents=True)
                vector = package / 'read.vector.json'
                vector.write_text('{"operation":"module.read"}')
                receipt = {'result': 'passed', 'packageId': 'Module.Contracts', 'version': '1.0.0',
                           'operations': ['module.read'], 'retainedInputs': {
                               'artifact': 'module.nupkg', 'vectors': {'original.json': vector.name}},
                           'vectors': {'original.json': hashlib.sha256(vector.read_bytes()).hexdigest()}}
                source = root / 'src/Hexalith.McpCli/obj/project.assets.json'
                source.parent.mkdir(parents=True)
                source.write_text('{}')
                report_path = output / 'enrolled.json'
                observed = []

                def execute(command, **kwargs):
                    if command[1] == 'msbuild':
                        return subprocess.CompletedProcess(command, 0, json.dumps({'Items': {'PackageReference': [
                            {'Identity': 'Module.Contracts', 'HexalithContracts': 'true'}]}}), '')
                    phase = 'production-' + command[1]
                    current = json.loads(report_path.read_text())['productionReplay']
                    observed.append(copy.deepcopy(current))
                    self.assertEqual(phase, current['phase'])
                    self.assertEqual('running', current['checks'][-1]['result'])
                    return subprocess.CompletedProcess(command, 9 if phase == failed_phase else 0,
                                                       phase + ' output', phase + ' diagnostic')

                def replay(*args, **kwargs):
                    current = json.loads(report_path.read_text())['productionReplay']
                    observed.append(copy.deepcopy(current))
                    self.assertEqual('production-replay', current['phase'])
                    raise RuntimeError('specific replay failure')

                with patch.object(check_enrolled, '__file__', str(root / 'tools/conformance-vectors/v1/check_enrolled.py')), \
                        patch.object(sys, 'argv', ['check_enrolled.py', '--output', str(output)]), \
                        patch('check_enrolled.required_scope', return_value=[]), \
                        patch('check_enrolled.approval_directory', return_value=root), \
                        patch('check_enrolled._load_json', return_value={
                            'module': 'module', 'artifactHash': 'approved', 'vectorFilesSha256': {}}), \
                        patch('check_enrolled.artifact_for', return_value=root / 'module.nupkg'), \
                        patch('check_enrolled.approved_vectors', return_value=[]), \
                        patch('check_enrolled.approved_inventory', return_value='0' * 64), \
                        patch('check_enrolled.verify', return_value=receipt), \
                        patch('check_enrolled.subprocess.run', side_effect=execute), \
                        patch('check_enrolled.run_catalog', side_effect=replay) as catalog, \
                        redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    self.assertEqual(1, check_enrolled.main())
                result = json.loads(report_path.read_text())
                progress = result['productionReplay']
                self.assertEqual('failed', result['result'])
                self.assertFalse(result['fullV1Accepted'])
                self.assertEqual('failed', progress['result'])
                self.assertEqual(failed_phase, progress['phase'])
                expected_codes = [9] if failed_phase == 'production-restore' else [0, 9] if failed_phase == 'production-build' else [0, 0]
                self.assertEqual(expected_codes, [row['exitCode'] for row in progress['checks']])
                for check in progress['checks']:
                    self.assertEqual('dotnet', check['command'][0])
                    self.assertEqual('failed' if check['exitCode'] else 'passed', check['result'])
                self.assertIn('specific replay failure' if failed_phase == 'production-replay' else failed_phase + ' failed with exit 9', progress['error'])
                self.assertEqual(len(expected_codes) + (failed_phase == 'production-replay'), len(observed))
                if failed_phase == 'production-replay':
                    self.assertIn('specific replay failure', (output / 'production-replay.stderr.txt').read_text())
                else:
                    catalog.assert_not_called()
                    self.assertEqual(failed_phase + ' output', (output / (failed_phase + '.stdout.txt')).read_text())
                    self.assertEqual(failed_phase + ' diagnostic', (output / (failed_phase + '.stderr.txt')).read_text())
