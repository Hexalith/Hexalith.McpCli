"""Focused checks for scratch verifier input binding, isolation and publication."""
import base64
import hashlib
import io
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from unittest.mock import patch
import zipfile

spec = importlib.util.spec_from_file_location('story49_verifier', Path(__file__).with_name('verify-scratch.py'))
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


class VerifyScratchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'mcpcli'
        self.parties = self.root / 'parties'
        self.evidence = self.root / 'evidence'
        for directory in [self.repo, self.parties, self.evidence]:
            directory.mkdir()
        self.revision = 'a' * 40
        validator = self.repo / 'tools/conformance-vectors/v1/validate.py'
        validator.parent.mkdir(parents=True)
        validator.write_text('# validator\n')
        self.source = self.parties / 'command.cs'
        self.source.write_text('record Command;\n')
        vectors = self.parties / 'tests/conformance-vectors/mcpcli-v1'
        vectors.mkdir(parents=True)
        self.vector = vectors / 'create-party.json'
        self.vector.write_text('{"postconditions": [{"operation":"parties.get-party"}]}\n')
        (self.evidence / 'ScratchProgram.cs').write_text('// adapter\n')
        (self.evidence / 'expected-operations.json').write_text('["parties.create-party"]')
        for name, root, files in [
            ('source-files.sha256.json', self.parties, ['command.cs']),
            ('vector-files.sha256.json', self.parties, [str(self.vector.relative_to(self.parties))]),
            ('verifier-files.sha256.json', self.evidence, ['ScratchProgram.cs', 'expected-operations.json']),
        ]:
            (self.evidence / name).write_text(json.dumps({name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in files}))
        artifact = self.evidence / 'artifacts/Hexalith.Parties.Contracts.0.0.0-story49.nupkg'
        artifact.parent.mkdir()
        with zipfile.ZipFile(artifact, 'w') as archive:
            archive.writestr('package.nuspec', '<package><metadata><dependencies><dependency id="Hexalith.EventStore.Contracts" version="3.125.1" /><dependency id="Hexalith.Commons.UniqueIds" version="2.30.3" /></dependencies></metadata></package>')
        self.digest = base64.b64encode(hashlib.sha512(artifact.read_bytes()).digest()).decode('ascii')
        (self.evidence / 'artifact.sha512').write_text('sha512-' + self.digest)
        (self.evidence / 'maintainer-vector-approval.json').write_text(json.dumps({
            'status': 'pending-maintainer-approval',
            'validatorRevision': self.revision,
            'sourceManifestSha256': hashlib.sha256((self.evidence / 'source-files.sha256.json').read_bytes()).hexdigest(),
            'vectorManifestSha256': hashlib.sha256((self.evidence / 'vector-files.sha256.json').read_bytes()).hexdigest(),
            'verifierManifestSha256': hashlib.sha256((self.evidence / 'verifier-files.sha256.json').read_bytes()).hexdigest(),
            'artifactHash': 'sha512-' + self.digest,
            'validatorFileSha256': hashlib.sha256(validator.read_bytes()).hexdigest(),
        }))

    def git_success(self, args, **kwargs):
        output = self.revision if args[1] == 'rev-parse' else ''
        return subprocess.CompletedProcess(args, 0, output, '')

    def test_source_vector_and_adapter_drift_fail_before_any_git_or_build(self):
        for path in [self.source, self.vector, self.evidence / 'ScratchProgram.cs']:
            with self.subTest(path=path):
                before = path.read_bytes()
                path.write_text('drift')
                with patch.object(verifier.subprocess, 'run') as run:
                    with self.assertRaisesRegex(RuntimeError, 'Recorded input drift'):
                        verifier.check_recorded_inputs(self.repo, self.parties, self.evidence)
                    run.assert_not_called()
                path.write_bytes(before)

    def test_unrecorded_vector_is_rejected_before_build(self):
        self.vector.with_name('unrecorded.json').write_text('{}')
        with patch.object(verifier.subprocess, 'run') as run:
            with self.assertRaisesRegex(RuntimeError, 'vector file set drift'):
                verifier.check_recorded_inputs(self.repo, self.parties, self.evidence)
            run.assert_not_called()

    def test_recorded_validator_hash_is_enforced_before_git_or_build(self):
        (self.repo / 'tools/conformance-vectors/v1/validate.py').write_text('drift')
        with patch.object(verifier.subprocess, 'run') as run:
            with self.assertRaisesRegex(RuntimeError, 'validator hash drift'):
                verifier.check_recorded_inputs(self.repo, self.parties, self.evidence)
            run.assert_not_called()

    def test_default_cli_root_reaches_the_repository_without_an_override(self):
        repo = next(parent for parent in Path(__file__).resolve().parents
                    if (parent / 'Hexalith.McpCli.slnx').is_file())
        with patch.object(sys, 'argv', [verifier.__file__]), patch.object(verifier, 'verify') as verify:
            self.assertEqual(verifier.main(), 0)
        verify.assert_called_once_with(repo, Path('/home/administrator/projects/hexalith/parties'),
                                       Path(verifier.__file__).resolve().parent)

    def test_binding_manifest_and_artifact_receipt_mismatches_fail_before_git_or_publication(self):
        self.prepare_execution()
        binding_path = self.evidence / 'maintainer-vector-approval.json'
        before = binding_path.read_bytes()
        for key in ['sourceManifestSha256', 'vectorManifestSha256', 'verifierManifestSha256', 'artifactHash']:
            with self.subTest(key=key):
                binding = json.loads(before)
                binding[key] = 'wrong'
                binding_path.write_text(json.dumps(binding))
                with patch.object(verifier.subprocess, 'run') as run:
                    with self.assertRaisesRegex(RuntimeError, 'Recorded (manifest|artifact receipt) hash drift'):
                        verifier.verify(self.repo, self.parties, self.evidence)
                    run.assert_not_called()
                self.assertEqual((self.evidence / 'catalog.json').read_text(), self.catalog_before)
        binding_path.write_bytes(before)
        for path in [self.evidence / 'source-files.sha256.json', self.evidence / 'vector-files.sha256.json',
                     self.evidence / 'artifact.sha512',
                     self.evidence / 'artifacts/Hexalith.Parties.Contracts.0.0.0-story49.nupkg']:
            with self.subTest(path=path):
                original = path.read_bytes()
                path.write_bytes(original + b' ')
                # Whitespace does not change the parsed artifact receipt token; change that token too.
                if path.name == 'artifact.sha512':
                    path.write_text('sha512-wrong')
                with patch.object(verifier.subprocess, 'run') as run:
                    with self.assertRaises(RuntimeError):
                        verifier.verify(self.repo, self.parties, self.evidence)
                    run.assert_not_called()
                self.assertEqual((self.evidence / 'catalog.json').read_text(), self.catalog_before)
                path.write_bytes(original)

    def test_declared_revision_checks_host_and_validator_changes(self):
        def drift(args, **kwargs):
            if args[1] == 'diff':
                self.assertIn('src', args)
                self.assertIn('tools/conformance-vectors/v1/run_loopback.py', args)
                raise subprocess.CalledProcessError(1, args)
            return self.git_success(args, **kwargs)
        with patch.object(verifier.subprocess, 'run', side_effect=drift):
            with self.assertRaises(subprocess.CalledProcessError):
                verifier.check_recorded_inputs(self.repo, self.parties, self.evidence)

    def test_untracked_host_code_is_rejected(self):
        def untracked(args, **kwargs):
            if args[1] == 'ls-files':
                return subprocess.CompletedProcess(args, 0, 'src/injected.cs\n', '')
            return self.git_success(args, **kwargs)
        with patch.object(verifier.subprocess, 'run', side_effect=untracked):
            with self.assertRaisesRegex(RuntimeError, 'Unrecorded host/validator files'):
                verifier.check_recorded_inputs(self.repo, self.parties, self.evidence)

    def prepare_execution(self):
        assets = self.repo / 'src/Hexalith.McpCli/obj/project.assets.json'
        assets.parent.mkdir(parents=True)
        assets.write_text('unchanged assets')
        (self.repo / 'references/Hexalith.Builds/Props').mkdir(parents=True)
        (self.repo / 'Directory.Packages.props').write_text('<Project></Project>')
        self.catalog_before = 'previous verified catalog'
        (self.evidence / 'catalog.json').write_text(self.catalog_before)
        (self.evidence / 'catalog-checks.json').write_text('previous verified checks')
        self.runtime_calls = []

    def execution(self, failure=None):
        def run(args, **kwargs):
            self.runtime_calls.append((args, kwargs.get('env')))
            env = kwargs['env']
            self.assertNotIn('EVENTSTORE_TENANT', env)
            self.assertNotIn('EVENTSTORE_PROFILE', env)
            self.assertNotIn('MCPCLI_OTHER_SETTING', env)
            self.assertNotEqual(env['MCPCLI_CONFORMANCE_PROFILE_PATH'], '/operator/profile.json')
            if args[1] in ['restore', 'build']:
                self.assertIn('-p:HexalithEventStoreVersion=3.125.1', args)
                self.assertIn('-p:HexalithCommonsVersion=2.30.3', args)
            if args[1] == 'restore':
                cache = Path(next(a.split('=', 1)[1] for a in args if a.startswith('-p:RestorePackagesPath=')))
                restored = cache / 'hexalith.parties.contracts/0.0.0-story49/hexalith.parties.contracts.0.0.0-story49.nupkg.sha512'
                restored.parent.mkdir(parents=True)
                restored.write_text('wrong' if failure == 'artifact' else self.digest)
            if any(str(a).endswith(('run_loopback.py', 'validate.py')) for a in args):
                self.assertEqual(args[0], sys.executable)
            if any(str(a).endswith('run_loopback.py') for a in args) and failure == 'routing':
                raise subprocess.CalledProcessError(1, args)
            if any(str(a).endswith('validate.py') for a in args):
                self.assertEqual((self.evidence / 'catalog.json').read_text(), self.catalog_before)
                if failure == 'vectors':
                    raise subprocess.CalledProcessError(7, args, output='captured vector stdout\n', stderr='captured vector stderr\n')
                return subprocess.CompletedProcess(args, 0, 'Validated 1 vector(s)\n', '')
            if '--full-catalog' in args:
                output = json.dumps({'diagnostics': ['invalid'] if failure == 'catalog-diagnostics' else [],
                                     'modules': [{'operations': [{'name': 'unexpected' if failure == 'coverage' else 'parties.create-party'}]}]})
            elif 'describe' in args:
                output = json.dumps({'lintFindings': ['invalid'] if failure == 'lint' else []})
            else:
                output = '{}'
            stderr = 'unexpected diagnostic' if (failure == 'catalog-stderr' and '--full-catalog' in args) or (failure == 'discovery-stderr' and '--manifest-catalog' in args) else ''
            return subprocess.CompletedProcess(args, 0, output, stderr)
        return run

    def test_later_routing_artifact_or_vector_failure_preserves_published_evidence(self):
        self.prepare_execution()
        for stage in ['routing', 'artifact', 'vectors', 'catalog-stderr', 'catalog-diagnostics', 'coverage', 'discovery-stderr', 'lint']:
            with self.subTest(stage=stage), patch.object(verifier, 'check_recorded_inputs'), \
                 patch.object(verifier.subprocess, 'run', side_effect=self.execution(stage)):
                with self.assertRaises((subprocess.CalledProcessError, RuntimeError)):
                    verifier.verify(self.repo, self.parties, self.evidence)
                self.assertEqual((self.evidence / 'catalog.json').read_text(), self.catalog_before)
                self.assertEqual((self.evidence / 'catalog-checks.json').read_text(), 'previous verified checks')

    def test_absent_production_assets_remain_absent_and_unexpected_creation_blocks_publication(self):
        self.prepare_execution()
        assets = self.repo / 'src/Hexalith.McpCli/obj/project.assets.json'
        assets.unlink()
        with patch.object(verifier, 'check_recorded_inputs'), \
             patch.object(verifier.subprocess, 'run', side_effect=self.execution()):
            verifier.verify(self.repo, self.parties, self.evidence)
        self.assertFalse(assets.exists())
        published = (self.evidence / 'catalog.json').read_bytes()
        self.catalog_before = published.decode()
        execute = self.execution()

        def create_assets(args, **kwargs):
            result = execute(args, **kwargs)
            if any(str(a).endswith('validate.py') for a in args):
                assets.write_text('unexpected restore')
            return result

        with patch.object(verifier, 'check_recorded_inputs'), \
             patch.object(verifier.subprocess, 'run', side_effect=create_assets):
            with self.assertRaisesRegex(RuntimeError, 'Production McpCli restored assets changed'):
                verifier.verify(self.repo, self.parties, self.evidence)
        self.assertEqual((self.evidence / 'catalog.json').read_bytes(), published)

    def test_cli_emits_captured_failure_diagnostics_and_preserves_published_evidence(self):
        self.prepare_execution()
        diagnostics = io.StringIO()
        argv = ['verify-scratch.py', '--mcpcli-root', str(self.repo), '--parties-root', str(self.parties)]
        verify_inputs = verifier.verify
        with patch.object(sys, 'argv', argv), \
             patch.object(verifier, 'verify', side_effect=lambda repo, parties, evidence: verify_inputs(repo, parties, self.evidence)), \
             patch.object(verifier, 'check_recorded_inputs'), \
             patch.object(verifier.subprocess, 'run', side_effect=self.execution('vectors')), redirect_stderr(diagnostics):
            self.assertEqual(verifier.main(), 7)
        self.assertIn('Command failed (7)', diagnostics.getvalue())
        self.assertIn('captured vector stdout', diagnostics.getvalue())
        self.assertIn('captured vector stderr', diagnostics.getvalue())
        self.assertEqual((self.evidence / 'catalog.json').read_text(), self.catalog_before)
        self.assertEqual((self.evidence / 'catalog-checks.json').read_text(), 'previous verified checks')

    def test_success_publishes_only_after_all_checks_and_sanitizes_every_runtime_call(self):
        self.prepare_execution()
        dirty = {'EVENTSTORE_TENANT': 'operator-tenant', 'EVENTSTORE_PROFILE': 'operator',
                 'MCPCLI_CONFORMANCE_PROFILE_PATH': '/operator/profile.json', 'MCPCLI_OTHER_SETTING': 'operator'}
        with patch.dict(os.environ, dirty), patch.object(verifier, 'check_recorded_inputs'), \
             patch.object(verifier.subprocess, 'run', side_effect=self.execution()):
            verifier.verify(self.repo, self.parties, self.evidence)
        self.assertNotEqual((self.evidence / 'catalog.json').read_text(), self.catalog_before)
        self.assertEqual((self.evidence / 'vector-validation.txt').read_text(), 'Validated 1 vector(s)\n')
        profiles = {env['MCPCLI_CONFORMANCE_PROFILE_PATH'] for _, env in self.runtime_calls}
        self.assertEqual(len(profiles), 1)
        self.assertEqual(json.loads(self.vector.read_text())['postconditions'], [{'operation': 'parties.get-party'}])


if __name__ == '__main__':
    unittest.main()
