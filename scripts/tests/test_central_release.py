"""Removal-sensitive unit tests for scripts/verify-central-release.py."""

from datetime import datetime, timedelta, timezone
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from product_packages import ROOT, digest

VERIFIER = importlib.import_module('verify-central-release')
SHA = 'a' * 40
OTHER_SHA = 'b' * 40
VERSION = '3.0.1'
TIMING_FILE = ROOT / 'docs/release/operator-setup-timing-exception.json'


def make_nupkg(path: Path, package_id: str, version: str, commit: str, readme: bytes, extra_payload: bytes = b'final') -> str:
    nuspec = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<package xmlns="http://schemas.microsoft.com/packaging/2012/06/nuspec.xsd">'
        '<metadata>'
        f'<id>{package_id}</id>'
        f'<version>{version}</version>'
        f'<repository type="git" url="https://github.com/Hexalith/Hexalith.McpCli" commit="{commit}" />'
        '</metadata></package>'
    ).encode('utf-8')
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr(f'{package_id}.nuspec', nuspec)
        archive.writestr('README.md', readme)
        archive.writestr('content/marker.bin', extra_payload)
    return digest(path)


class CentralReleaseVerifierTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.now = datetime.now(timezone.utc)
        self.ci_completed = self.now - timedelta(minutes=15)
        self.decided_at = self.now - timedelta(minutes=5)

    def build_valid_fixture(self, name: str = 'valid'):
        base = self.root / name
        packages_dir = base / 'release/packages'
        packages_dir.mkdir(parents=True)
        ci_dir = base / 'ci/packages'
        ci_dir.mkdir(parents=True)
        readme = base / 'README.md'
        readme_bytes = b'# Hexalith.McpCli\n'
        readme.write_bytes(readme_bytes)

        final_packages = {}
        ci_packages = {}
        for pkg_id in ('Hexalith.McpCli.Abstractions', 'Hexalith.McpCli'):
            fname = f'{pkg_id}.{VERSION}.nupkg'
            final_packages[fname] = make_nupkg(packages_dir / fname, pkg_id, VERSION, SHA, readme_bytes, b'final-ci-build')
            ci_fname = f'{pkg_id}.3.0.0.nupkg'
            ci_packages[ci_fname] = make_nupkg(ci_dir / ci_fname, pkg_id, '3.0.0', SHA, readme_bytes, b'ci-fixture-only')

        manifest_path = base / 'release/release-manifest.json'
        manifest_path.write_text(json.dumps({
            'sha': SHA,
            'version': VERSION,
            'packages': [
                {'id': 'Hexalith.McpCli', 'path': f'packages/Hexalith.McpCli.{VERSION}.nupkg', 'verifyPublishedPackage': True},
                {'id': 'Hexalith.McpCli.Abstractions', 'path': f'packages/Hexalith.McpCli.Abstractions.{VERSION}.nupkg', 'verifyPublishedPackage': True},
            ],
            'containers': [],
        }), encoding='utf-8')

        ci_prepared = base / 'ci/prepared.json'
        ci_prepared.write_text(json.dumps({
            'schema': 'mcpcli-product-packages/v1',
            'source_sha': SHA,
            'version': '3.0.0',
            'tool_version': '3.0.0',
            'packages': ci_packages,
        }), encoding='utf-8')

        ci_receipt = base / 'ci-receipt.json'
        ci_receipt.write_text(json.dumps({
            'schema': 'mcpcli-central-ci-receipt/v1',
            'repository': 'Hexalith/Hexalith.McpCli',
            'source_sha': SHA,
            'ci_run_id': 46068136287,
            'status': 'completed',
            'conclusion': 'success',
            'completed_at_utc': self.ci_completed.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'platforms': {
                'Linux': {'status': 'passed'},
                'Windows': {'status': 'passed'},
                'Darwin': {'status': 'passed'},
            },
            'ci_fixture_packages': ci_packages,
        }), encoding='utf-8')

        validation = base / 'validation.json'
        validation.write_text(json.dumps({
            'phase': 'paired',
            'source_sha': SHA,
            'version': VERSION,
            'packages': final_packages,
        }), encoding='utf-8')

        smoke = base / 'smoke.json'
        smoke.write_text(json.dumps({
            'schema': 'mcpcli-paired-smoke/v1',
            'status': 'passed',
            'os': 'Linux',
            'source_sha': SHA,
            'version': VERSION,
            'packages': final_packages,
            'checks': sorted(VERIFIER.REQUIRED_SMOKE_CHECKS),
            'discovery': {
                'modules.json': '1' * 64,
                'mcp-tools.json': '2' * 64,
                'mcp-modules.json': '3' * 64,
            },
        }), encoding='utf-8')

        consumer = base / 'consumer.json'
        consumer.write_text(json.dumps({
            'schema': 'mcpcli-central-consumer/v1',
            'status': 'passed',
            'source_sha': SHA,
            'version': VERSION,
            'packages': final_packages,
            'exit_code': 0,
            'warning_code': 'MCPCLI001',
        }), encoding='utf-8')

        acceptance = base / 'acceptance.json'
        acceptance.write_text(json.dumps({
            'schema': 'mcpcli-central-release-acceptance/v1',
            'decision': 'approved',
            'version': VERSION,
            'source_sha': SHA,
            'final_packages': final_packages,
            'ci_receipt_sha256': digest(ci_receipt),
            'approved_by': 'jpiquot',
            'decided_at_utc': self.decided_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'readme_sha256': digest(readme),
            'timing_exception': {
                'status': 'accepted-existing-exception',
                'reference': 'docs/release/operator-setup-timing-exception.json',
                'sha256': digest(TIMING_FILE),
                'elapsed_seconds': 685,
                'first_time_operator': False,
                'unassisted_success': False,
            },
        }), encoding='utf-8')

        return {
            'base': base,
            'packages_dir': packages_dir,
            'manifest': manifest_path,
            'ci_prepared': ci_prepared,
            'ci_receipt': ci_receipt,
            'validation': validation,
            'smoke': smoke,
            'consumer': consumer,
            'acceptance': acceptance,
            'readme': readme,
            'final_packages': final_packages,
            'ci_packages': ci_packages,
        }

    def run_verify(self, fx, output: Path, **overrides):
        kwargs = dict(
            packages_dir=fx['packages_dir'],
            version=VERSION,
            source_sha=SHA,
            validation_path=fx['validation'],
            smoke_path=fx['smoke'],
            consumer_path=fx['consumer'],
            ci_receipt_path=fx['ci_receipt'],
            acceptance_path=fx['acceptance'],
            output=output,
            release_manifest_path=fx['manifest'],
            ci_prepared_path=fx['ci_prepared'],
            readme_path=fx['readme'],
            now=self.now,
        )
        kwargs.update(overrides)
        return VERIFIER.verify_candidate(**kwargs)

    def test_valid_rehearsal_emits_separate_ci_fixture_and_final_hashes(self):
        fx = self.build_valid_fixture()
        output = fx['base'] / 'verified.json'
        receipt = self.run_verify(fx, output)
        self.assertEqual(receipt['schema'], 'mcpcli-central-release-verification/v1')
        self.assertEqual(receipt['status'], 'passed')
        self.assertTrue(receipt['non_publishing'])
        self.assertEqual(receipt['final_packages'], fx['final_packages'])
        self.assertEqual(receipt['ci_fixture_packages'], fx['ci_packages'])
        self.assertEqual(receipt['signed_public_packages'], {})
        self.assertNotEqual(set(receipt['final_packages'].values()), set(receipt['ci_fixture_packages'].values()))
        # Refuses overwriting an existing receipt.
        with self.assertRaisesRegex(ValueError, 'already exists'):
            self.run_verify(fx, output)

    def test_changed_package_digest_is_rejected_with_package_and_digest(self):
        fx = self.build_valid_fixture('tamper-archive')
        target = fx['packages_dir'] / f'Hexalith.McpCli.{VERSION}.nupkg'
        make_nupkg(target, 'Hexalith.McpCli', VERSION, SHA, fx['readme'].read_bytes(), b'tampered-bytes')
        output = fx['base'] / 'verified.json'
        with self.assertRaisesRegex(ValueError, rf'Hexalith\.McpCli\.{VERSION}\.nupkg'):
            self.run_verify(fx, output)
        self.assertFalse(output.exists())

    def test_acceptance_digest_mismatch_is_rejected_with_package_and_digest(self):
        fx = self.build_valid_fixture('tamper-acceptance-digest')
        acc = json.loads(fx['acceptance'].read_text())
        acc['final_packages'][f'Hexalith.McpCli.{VERSION}.nupkg'] = 'f' * 64
        fx['acceptance'].write_text(json.dumps(acc), encoding='utf-8')
        output = fx['base'] / 'verified.json'
        with self.assertRaisesRegex(ValueError, rf'Hexalith\.McpCli\.{VERSION}\.nupkg.*{"f" * 64}'):
            self.run_verify(fx, output)
        self.assertFalse(output.exists())

    def test_wrong_source_sha_refused_in_nuspec_manifest_ci_receipt_and_acceptance(self):
        # 1. Wrong nuspec commit
        fx = self.build_valid_fixture('wrong-nuspec')
        make_nupkg(fx['packages_dir'] / f'Hexalith.McpCli.{VERSION}.nupkg', 'Hexalith.McpCli', VERSION, OTHER_SHA, fx['readme'].read_bytes())
        with self.assertRaisesRegex(ValueError, 'Source SHA mismatch'):
            self.run_verify(fx, fx['base'] / 'out.json')

        # 2. Wrong release-manifest sha
        fx = self.build_valid_fixture('wrong-manifest')
        m = json.loads(fx['manifest'].read_text())
        m['sha'] = OTHER_SHA
        fx['manifest'].write_text(json.dumps(m), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Source SHA mismatch'):
            self.run_verify(fx, fx['base'] / 'out.json')

        # 3. Wrong 3-OS CI receipt sha
        fx = self.build_valid_fixture('wrong-ci-receipt')
        ci = json.loads(fx['ci_receipt'].read_text())
        ci['source_sha'] = OTHER_SHA
        fx['ci_receipt'].write_text(json.dumps(ci), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Source SHA mismatch'):
            self.run_verify(fx, fx['base'] / 'out.json')

        # 4. Wrong acceptance sha
        fx = self.build_valid_fixture('wrong-acceptance-sha')
        acc = json.loads(fx['acceptance'].read_text())
        acc['source_sha'] = OTHER_SHA
        fx['acceptance'].write_text(json.dumps(acc), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Source SHA mismatch'):
            self.run_verify(fx, fx['base'] / 'out.json')

    def test_fixture_hash_substituted_for_final_is_rejected(self):
        fx = self.build_valid_fixture('fixture-in-acceptance')
        acc = json.loads(fx['acceptance'].read_text())
        ci_hash = fx['ci_packages']['Hexalith.McpCli.3.0.0.nupkg']
        acc['final_packages'][f'Hexalith.McpCli.{VERSION}.nupkg'] = ci_hash
        fx['acceptance'].write_text(json.dumps(acc), encoding='utf-8')
        output = fx['base'] / 'out.json'
        with self.assertRaisesRegex(ValueError, 'Fixture hash rejected'):
            self.run_verify(fx, output)
        self.assertFalse(output.exists())

        # Also reject if CI fixture bytes themselves are placed into the final directory.
        fx2 = self.build_valid_fixture('fixture-bytes-as-final')
        pkg_name = f'Hexalith.McpCli.{VERSION}.nupkg'
        # Make CI prepared record the exact same hash as the final archive.
        ci_prep = json.loads(fx2['ci_prepared'].read_text())
        ci_prep['packages']['Hexalith.McpCli.3.0.0.nupkg'] = fx2['final_packages'][pkg_name]
        fx2['ci_prepared'].write_text(json.dumps(ci_prep), encoding='utf-8')
        ci_rec = json.loads(fx2['ci_receipt'].read_text())
        ci_rec['ci_fixture_packages'] = ci_prep['packages']
        fx2['ci_receipt'].write_text(json.dumps(ci_rec), encoding='utf-8')
        acc2 = json.loads(fx2['acceptance'].read_text())
        acc2['ci_receipt_sha256'] = digest(fx2['ci_receipt'])
        fx2['acceptance'].write_text(json.dumps(acc2), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Fixture hash rejected'):
            self.run_verify(fx2, fx2['base'] / 'out.json')

    def test_invalid_or_missing_acceptance_and_bypass_attempts_are_rejected(self):
        # Missing acceptance file
        fx = self.build_valid_fixture('missing-acc')
        fx['acceptance'].unlink()
        with self.assertRaisesRegex(ValueError, 'central acceptance'):
            self.run_verify(fx, fx['base'] / 'out.json')

        # Bot actors
        for actor in ('github-actions[bot]', 'dependabot[bot]', 'github-actions', 'release-bot'):
            fx = self.build_valid_fixture('bot-' + actor.replace('[', '').replace(']', ''))
            acc = json.loads(fx['acceptance'].read_text())
            acc['approved_by'] = actor
            fx['acceptance'].write_text(json.dumps(acc), encoding='utf-8')
            with self.subTest(actor=actor), self.assertRaisesRegex(ValueError, 'bot actor'):
                self.run_verify(fx, fx['base'] / 'out.json')

        # Bad timestamps: no timezone, before CI completion, in the future
        bad_times = [
            ('no-tz', '2026-11-28T11:55:00', 'timezone offset'),
            ('before-ci', (self.ci_completed - timedelta(minutes=1)).strftime('%Y-%m-%dT%H:%M:%SZ'), 'precede 3-OS CI'),
            ('future', (self.now + timedelta(minutes=1)).strftime('%Y-%m-%dT%H:%M:%SZ'), 'in the future'),
        ]
        for label, value, pattern in bad_times:
            fx = self.build_valid_fixture('ts-' + label)
            acc = json.loads(fx['acceptance'].read_text())
            acc['decided_at_utc'] = value
            fx['acceptance'].write_text(json.dumps(acc), encoding='utf-8')
            with self.subTest(label=label), self.assertRaisesRegex(ValueError, pattern):
                self.run_verify(fx, fx['base'] / 'out.json')

        # Bypass attempts (legacy schema and authorization field)
        for label, patch_fn in [
            ('legacy-schema', lambda d: d.update(schema='mcpcli-paired-automated-acceptance/v1', authorization='user-requested-human-validation-bypass')),
            ('bypass-auth', lambda d: d.update(authorization='user-requested-human-validation-bypass')),
            ('bypass-key', lambda d: d.update(bypass='true')),
        ]:
            fx = self.build_valid_fixture('bypass-' + label)
            acc = json.loads(fx['acceptance'].read_text())
            patch_fn(acc)
            fx['acceptance'].write_text(json.dumps(acc), encoding='utf-8')
            with self.subTest(label=label), self.assertRaisesRegex(ValueError, 'bypass.*forbidden'):
                self.run_verify(fx, fx['base'] / 'out.json')

        # Wrong version, missing pair entry, workflow-bundle-only digest without final_packages
        fx = self.build_valid_fixture('bundle-only')
        acc = json.loads(fx['acceptance'].read_text())
        del acc['final_packages']
        acc['artifact_digest'] = 'sha256:' + 'c' * 64
        fx['acceptance'].write_text(json.dumps(acc), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'missing required fields'):
            self.run_verify(fx, fx['base'] / 'out.json')

        # Timing exception pointing to _bmad-output/
        fx = self.build_valid_fixture('bmad-timing')
        acc = json.loads(fx['acceptance'].read_text())
        acc['timing_exception']['reference'] = '_bmad-output/implementation-artifacts/evidence/story-4-17/timing-attempts.json'
        fx['acceptance'].write_text(json.dumps(acc), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, '_bmad-output/'):
            self.run_verify(fx, fx['base'] / 'out.json')

        # Duplicate JSON keys in acceptance
        fx = self.build_valid_fixture('dup-keys')
        raw = fx['acceptance'].read_text()
        fx['acceptance'].write_text('{"decision":"rejected",' + raw[1:], encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'duplicate JSON key'):
            self.run_verify(fx, fx['base'] / 'out.json')

        # Missing verifyPublishedPackage=true in release-manifest.json
        fx = self.build_valid_fixture('no-verify-flag')
        m = json.loads(fx['manifest'].read_text())
        m['packages'][0]['verifyPublishedPackage'] = False
        fx['manifest'].write_text(json.dumps(m), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'verifyPublishedPackage=true'):
            self.run_verify(fx, fx['base'] / 'out.json')

        # Missing platform in 3-OS CI receipt
        fx = self.build_valid_fixture('missing-os')
        ci = json.loads(fx['ci_receipt'].read_text())
        del ci['platforms']['Darwin']
        fx['ci_receipt'].write_text(json.dumps(ci), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'exact platforms'):
            self.run_verify(fx, fx['base'] / 'out.json')

        # Incomplete smoke checks
        fx = self.build_valid_fixture('missing-smoke-check')
        sm = json.loads(fx['smoke'].read_text())
        sm['checks'].remove('errors')
        fx['smoke'].write_text(json.dumps(sm), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'smoke receipt checks'):
            self.run_verify(fx, fx['base'] / 'out.json')

    def test_verify_published_separates_signed_hashes_and_enforces_payload_equality(self):
        fx = self.build_valid_fixture('pub-valid')
        cand_out = fx['base'] / 'candidate.json'
        self.run_verify(fx, cand_out)

        pub_doc = {
            'schema': 'hexalith.package-publication.v1',
            'repository': 'Hexalith/Hexalith.McpCli',
            'sha': SHA,
            'version': VERSION,
            'artifactRun': 99999,
            'artifactId': 88888,
            'artifactDigest': 'sha256:' + 'd' * 64,
            'packages': [
                {
                    'id': pkg_id,
                    'archiveSha256': hashlib.sha256(f'signed-{pkg_id}'.encode()).hexdigest(),
                    'files': VERIFIER.payload_map_from_nupkg(fx['packages_dir'] / f'{pkg_id}.{VERSION}.nupkg'),
                }
                for pkg_id in ('Hexalith.McpCli', 'Hexalith.McpCli.Abstractions')
            ],
        }
        pub_path = fx['base'] / 'hexalith-package-publication.v1.json'
        pub_path.write_text(json.dumps(pub_doc), encoding='utf-8')
        pub_out = fx['base'] / 'pub-verified.json'
        receipt = VERIFIER.verify_published(
            publication_path=pub_path,
            packages_dir=fx['packages_dir'],
            source_sha=SHA,
            version=VERSION,
            output=pub_out,
            candidate_receipt_path=cand_out,
            readme_path=fx['readme'],
        )
        self.assertEqual(receipt['status'], 'passed')
        self.assertEqual(receipt['ci_fixture_packages'], fx['ci_packages'])
        self.assertEqual(receipt['final_packages'], fx['final_packages'])
        self.assertEqual(set(receipt['signed_public_packages']), set(fx['final_packages']))
        self.assertNotEqual(receipt['signed_public_packages'], receipt['final_packages'])

        # Mutating any nonsignature file digest in publication inventory must fail.
        pub_doc['packages'][0]['files']['README.md'] = '0' * 64
        pub_path.write_text(json.dumps(pub_doc), encoding='utf-8')
        bad_out = fx['base'] / 'pub-bad.json'
        with self.assertRaisesRegex(ValueError, 'nonsignature payload differs'):
            VERIFIER.verify_published(
                publication_path=pub_path,
                packages_dir=fx['packages_dir'],
                source_sha=SHA,
                version=VERSION,
                output=bad_out,
                candidate_receipt_path=cand_out,
            )
        self.assertFalse(bad_out.exists())

    def test_cli_returns_nonzero_on_failure_and_zero_on_valid(self):
        fx = self.build_valid_fixture('cli')
        out_ok = fx['base'] / 'cli-ok.json'
        code = VERIFIER.main([
            'verify-candidate',
            '--packages-dir', str(fx['packages_dir']),
            '--version', VERSION,
            '--source-sha', SHA,
            '--validation', str(fx['validation']),
            '--smoke', str(fx['smoke']),
            '--consumer', str(fx['consumer']),
            '--ci-receipt', str(fx['ci_receipt']),
            '--acceptance', str(fx['acceptance']),
            '--release-manifest', str(fx['manifest']),
            '--ci-prepared', str(fx['ci_prepared']),
            '--readme', str(fx['readme']),
            '--output', str(out_ok),
        ])
        self.assertEqual(code, 0)
        self.assertTrue(out_ok.is_file())

        out_bad = fx['base'] / 'cli-bad.json'
        code_bad = VERIFIER.main([
            'verify-candidate',
            '--packages-dir', str(fx['packages_dir']),
            '--version', VERSION,
            '--source-sha', OTHER_SHA,
            '--validation', str(fx['validation']),
            '--smoke', str(fx['smoke']),
            '--consumer', str(fx['consumer']),
            '--ci-receipt', str(fx['ci_receipt']),
            '--acceptance', str(fx['acceptance']),
            '--output', str(out_bad),
        ])
        self.assertEqual(code_bad, 1)
        self.assertFalse(out_bad.exists())

    def test_check_project_packaging_enforces_manifest_packability_and_verify_flag(self):
        manifest_root = self.root / 'proj-check'
        (manifest_root / 'tools').mkdir(parents=True)
        (manifest_root / 'tools/release-packages.json').write_text(
            (ROOT / 'tools/release-packages.json').read_text(encoding='utf-8'), encoding='utf-8'
        )
        (manifest_root / 'Hexalith.McpCli.slnx').write_text(
            '<Solution>'
            '<Project Path="src/Hexalith.McpCli.Abstractions/Hexalith.McpCli.Abstractions.csproj" />'
            '<Project Path="src/Hexalith.McpCli/Hexalith.McpCli.csproj" />'
            '<Project Path="src/Hexalith.McpCli.Core/Hexalith.McpCli.Core.csproj" />'
            '</Solution>',
            encoding='utf-8',
        )

        def fake_msbuild(props_by_project):
            def runner(argv, **_kwargs):
                proj = Path(argv[2]).relative_to(manifest_root).as_posix()
                return subprocess.CompletedProcess(argv, 0, stdout=json.dumps({'Properties': props_by_project[proj]}), stderr='')
            return runner

        good = {
            'src/Hexalith.McpCli.Abstractions/Hexalith.McpCli.Abstractions.csproj': {
                'IsPackable': 'true', 'PackageId': 'Hexalith.McpCli.Abstractions',
                'HexalithVerifyPublishedPackage': 'true', 'IsTestProject': 'false',
            },
            'src/Hexalith.McpCli/Hexalith.McpCli.csproj': {
                'IsPackable': 'true', 'PackageId': 'Hexalith.McpCli',
                'HexalithVerifyPublishedPackage': 'true', 'IsTestProject': 'false',
            },
            'src/Hexalith.McpCli.Core/Hexalith.McpCli.Core.csproj': {
                'IsPackable': 'false', 'PackageId': 'Hexalith.McpCli.Core',
                'HexalithVerifyPublishedPackage': '', 'IsTestProject': 'false',
            },
        }
        with patch.object(VERIFIER.subprocess, 'run', side_effect=fake_msbuild(good)):
            evaluated = VERIFIER.check_project_packaging(root=manifest_root)
        self.assertEqual(len(evaluated), 3)

        bad_non_manifest = json.loads(json.dumps(good))
        bad_non_manifest['src/Hexalith.McpCli.Core/Hexalith.McpCli.Core.csproj']['IsPackable'] = 'true'
        with patch.object(VERIFIER.subprocess, 'run', side_effect=fake_msbuild(bad_non_manifest)):
            with self.assertRaisesRegex(ValueError, 'Non-manifest project.*IsPackable=false'):
                VERIFIER.check_project_packaging(root=manifest_root)

        bad_verify = json.loads(json.dumps(good))
        bad_verify['src/Hexalith.McpCli/Hexalith.McpCli.csproj']['HexalithVerifyPublishedPackage'] = 'false'
        with patch.object(VERIFIER.subprocess, 'run', side_effect=fake_msbuild(bad_verify)):
            with self.assertRaisesRegex(ValueError, 'HexalithVerifyPublishedPackage=true'):
                VERIFIER.check_project_packaging(root=manifest_root)


if __name__ == '__main__':
    unittest.main()
