"""Publication refusal, immutable-byte and partial-outcome controls with synthetic evidence."""

import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from zipfile import ZipFile

import test_paired_release as fixtures
import test_bootstrap_release as shell_fixtures
from test_paired_release import SHA, VERSION, jobs
from paired_release import PAIR, digest, module, packages, write_new


class PublicationTests(unittest.TestCase):
    save_gates = fixtures.PairedReleaseTests.save_gates
    save_prepared = fixtures.PairedReleaseTests.save_prepared
    change_json = fixtures.PairedReleaseTests.change_json
    compare = fixtures.PairedReleaseTests.compare

    def setUp(self):
        fixtures.PairedReleaseTests.setUp(self)
        self.verifier = module('verify-paired-publication')
        self.publisher = module('publish-paired-release')
        self.request = module('release-request')
        self.recovery = module('recover-bootstrap-release')
        self.publisher.IMPORTED = self.root / 'imported'
        self.publisher.OUTCOMES = self.root / 'outcomes'
        for identity in PAIR:
            with ZipFile(self.staging / f'{identity}.{VERSION}.nupkg', 'w') as archive:
                archive.writestr(identity + '.nuspec', f'<package><metadata><id>{identity}</id><version>{VERSION}</version><repository commit="{SHA}" /></metadata></package>')
                archive.writestr('README.md', (self.verifier.ROOT / 'README.md').read_bytes())
                archive.writestr('fixture.dll', identity)
        self.package_hashes = packages(self.staging, VERSION)
        self.prepared['packages'] = self.package_hashes
        self.save_gates()
        for directory in self.consumers:
            for name in ('smoke/smoke.json', 'tests/tests.json'):
                self.change_json(directory / name, lambda document: document.update(packages=self.package_hashes))
        self.compare()
        self.accepted_path = self.root / 'accepted.json'
        self.candidate = self.root / 'candidate'
        self.candidate.mkdir()
        sources = {'paired-preparation': {'packages': self.staging, 'evidence': self.evidence, 'prepared.json': self.prepared_path},
                   'accepted-staging-only': {'accepted-pair.json': self.accepted_path}}
        self.acceptance_source = self.root / 'acceptance-source.json'
        write_new(self.acceptance_source, self.source_gate)
        sources['accepted-staging-only']['acceptance-source.json'] = self.acceptance_source
        for system, name in [('Linux', 'ubuntu-latest'), ('Windows', 'windows-latest'), ('Darwin', 'macos-latest')]:
            sources['paired-consumer-' + name] = {'smoke': self.root / system / 'smoke', 'tests': self.root / system / 'tests'}
        self.origin = {'repository': 'fixture/repo', 'staging_run_id': 123, 'source_sha': SHA,
                       'run_attempt': 1, 'completed_at': '2026-11-01T00:00:00Z', 'artifacts': []}
        for index, name in enumerate(self.verifier.ARTIFACTS):
            archive_path = self.candidate / (name + '.zip')
            with ZipFile(archive_path, 'w') as archive:
                for destination, source in sources[name].items():
                    if source.is_dir():
                        for path in source.rglob('*'):
                            if path.is_file(): archive.write(path, str(Path(destination) / path.relative_to(source)))
                    else: archive.write(source, destination)
            self.origin['artifacts'].append({'id': index + 1, 'name': name, 'digest': 'sha256:' + digest(archive_path)})
        write_new(self.candidate / 'staging-origin.json', self.origin)
        self.bindings = {key: self.prepared[key] for key in ('source_sha', 'version', 'packages')}
        self.bindings.update(staging_run_id=123, preparation_sha256=digest(self.prepared_path),
                             acceptance_sha256=digest(self.accepted_path), readme_sha256=digest(self.verifier.ROOT / 'README.md'))
        evidence = {name: {'content': 'Synthetic test fixture for ' + name,
                          'sha256': hashlib.sha256(('Synthetic test fixture for ' + name).encode()).hexdigest()}
                    for name in ('initialization', 'discovery', 'tenant_read', 'command', 'persisted_party', 'cleanup', 'environment_approval')}
        sessions = []
        for index, client in enumerate(('Claude Code', 'Claude Desktop', 'VS Code')):
            sessions.append({**self.bindings, 'client': client, 'status': 'passed', 'actual_client': True,
                'operator': 'fixture', 'observer': 'fixture observer', 'os_version': 'fixture OS', 'client_version': 'fixture version',
                'harness': 'fixture harness', 'launch_environment': 'fixture', 'executable_path': '/fixture/hexalith',
                'selected_tenant': 'fixture-tenant', 'party_id': 'fixture-party-' + str(index), 'assistance': ['fixture assistance'], 'failures': [],
                'started_at_utc': '2026-11-01T00:01:00Z', 'ended_at_utc': '2026-11-01T00:02:00Z',
                'environment_approval': {'decision': 'approved', 'ready': True, 'owner': 'fixture', 'target': 'fixture',
                    'namespace_uid': 'fixture-uid', 'tenant': 'fixture-tenant', 'approved_at_utc': '2026-11-01T00:00:30Z',
                    'expires_at_utc': '2026-11-01T00:03:00Z'}, 'evidence': copy.deepcopy(evidence),
                'server_identity': {'name': 'hexalith', 'version': VERSION}, 'tools': sorted(self.verifier.TOOLS),
                'modules': ['parties', 'tenants'], 'operation_lists': ['parties', 'tenants'],
                'described_operations': ['tenants.get-tenant', 'parties.create-party', 'parties.get-party'],
                'tenant_read': {'tenant': 'fixture-tenant', 'document_id': 'fixture-tenant', 'is_active': True, 'membership_verified': True},
                'command_result': {'status': 'accepted', 'tenant': 'fixture-tenant', 'aggregate_id': 'fixture-party-' + str(index),
                                   'message_id': '01M695PTVDN76PQH5F0WTE7HS6', 'correlation_id': '01M695PTVDN76PQH5F0WTE7HS6'},
                'persisted_party': {'tenant': 'fixture-tenant', 'id': 'fixture-party-' + str(index), 'isActive': True,
                                    'isErased': False, 'synthetic_fields_verified': True}})
        self.operator = self.root / 'operator.json'
        self.decision = {'schema': 'mcpcli-paired-operator-acceptance/v1', 'decision': 'approved', 'approved_by': 'fixture-owner',
                         'decided_at_utc': '2026-11-01T00:03:00Z', **self.bindings, 'sessions': sessions,
                         'timing_exception': {'reference': self.verifier.TIMING, 'sha256': digest(self.verifier.ROOT / self.verifier.TIMING),
                             'elapsed_seconds': 685, 'first_time_operator': False, 'unassisted_success': False,
                             'decision': 'accepted-existing-exception'}}
        write_new(self.operator, self.decision)
        self.initial = self.root / 'preflight.json'
        self.env = {'REPOSITORY': 'fixture/repo', 'DISPATCH_SHA': SHA, 'DISPATCH_REF': 'refs/heads/main',
                    'MCPCLI_STAGING_RUN_ID': '123', 'GITHUB_ACTOR': 'fixture-owner', 'NUGET_API_KEY': 'never-print-this-key',
                    'MCPCLI_RECOVERY_VERSION': '', 'RECOVERY_VERSION': '', 'MCPCLI_PAIRED_CANDIDATE': str(self.candidate),
                    'MCPCLI_OPERATOR_ACCEPTANCE': str(self.operator), 'MCPCLI_PAIRED_PREFLIGHT': str(self.initial)}
        self.pushes = []
        self.mode = None
        self.preflight_count = 0

    def execute(self, argv, **kwargs):
        if 'verify-release-source.py' in str(argv[1]):
            if self.mode == 'source-before-second' and len(self.pushes) == 1:
                raise subprocess.CalledProcessError(1, argv, stderr='main moved')
            write_new(Path(argv[argv.index('--output') + 1]), self.source_gate)
            return subprocess.CompletedProcess(argv, 0, stdout=b'', stderr=b'')
        self.assertEqual(argv[:3], ['dotnet', 'nuget', 'push'])
        self.assertNotIn('--skip-duplicate', argv)
        self.assertNotEqual(Path(argv[3]).parent, self.staging)
        self.pushes.append((Path(argv[3]).name, Path(argv[3]).read_bytes()))
        if self.mode == 'mutate-original-after-first' and len(self.pushes) == 1:
            for path in (self.publisher.IMPORTED / 'packages').iterdir():
                path.write_bytes(b'changed outside the snapshot')
        failure = self.mode == 'first-push' or self.mode == 'second-push' and len(self.pushes) == 2
        return subprocess.CompletedProcess(argv, 47 if failure else 0, stdout='fixture result', stderr=self.env['NUGET_API_KEY'] if failure else '')

    def real_preflight(self, candidate, operator, version, output):
        self.preflight_count += 1
        return self.verifier.validate(candidate, operator, version, SHA, 123, 'fixture-owner', output)

    def downloaded(self, url, destination, pushed):
        self.assertTrue(pushed)
        name = next(filename for filename in self.package_hashes if filename.lower() in url)
        destination.write_bytes((self.staging / name).read_bytes())
        with ZipFile(destination, 'a') as archive:
            archive.writestr('.signature.p7s', 'fixture NuGet repository signature')
            archive.writestr('package/services/metadata/core-properties/nuget.psmdcp', 'fixture NuGet metadata')
            if self.mode == 'public-mismatch': archive.writestr('unapproved.txt', 'different consumer bytes')

    @contextlib.contextmanager
    def controls(self):
        def modules(name):
            return {'release-request': self.request, 'recover-bootstrap-release': self.recovery}.get(name) or module(name)
        with patch.dict(os.environ, self.env), patch.object(self.verifier, 'authenticate_run', return_value=self.origin), \
                patch.object(self.publisher, 'preflight', side_effect=self.real_preflight), \
                patch.object(self.publisher, 'reserve_version') as reserve, \
                patch.object(self.publisher, 'module', side_effect=modules), \
                patch.object(self.request, 'check_registry'), patch.object(self.request, 'registry_versions',
                    side_effect=lambda *args, **kwargs: [VERSION] if self.mode == 'second-occupied' and len(self.pushes) == 1 else []), \
                patch.object(self.recovery, 'download_public_package', side_effect=self.downloaded), \
                patch.object(subprocess, 'run', side_effect=self.execute):
            yield reserve

    def import_pair(self):
        self.real_preflight(self.candidate, self.operator, VERSION, self.initial)
        self.publisher.prepare(VERSION)

    def test_complete_preflight_and_exact_byte_two_pushes_verify_signed_public_contents(self):
        with self.controls() as reserve:
            self.import_pair()
            self.publisher.publish(VERSION)
        self.assertEqual([name for name, _ in self.pushes], [f'{identity}.{VERSION}.nupkg' for identity in PAIR])
        for name, raw in self.pushes: self.assertEqual(hashlib.sha256(raw).hexdigest(), self.package_hashes[name])
        reserve.assert_called_once_with(VERSION, SHA)
        result = json.loads((self.publisher.OUTCOMES / 'outcome.json').read_text())
        self.assertEqual(result['status'], 'paired-public-verified')
        self.assertTrue(all(item['status'] == 'public-verified' for item in result['packages'].values()))
        self.assertEqual(self.preflight_count, 5)  # initial, import, snapshot and immediately before each push
        self.assertEqual(result['operator_sha256'], digest(self.operator))
        self.assertEqual(result['origin'], self.origin)

    def test_configured_shell_hooks_publish_both_exact_archives_and_complete_outcome(self):
        shell = shell_fixtures.BootstrapReleaseTests()
        shell.setUp()
        self.addCleanup(shell.doCleanups)
        shell.paired_controls(self.origin, self.source_gate, jobs(self.verifier.STAGING_JOBS))
        shell.env.update(self.env, MCPCLI_RELEASE_PHASE='paired')
        shutil.copy(self.verifier.ROOT / 'README.md', shell.root / 'README.md')
        timing = shell.root / self.verifier.TIMING
        timing.parent.mkdir(parents=True)
        shutil.copy(self.verifier.ROOT / self.verifier.TIMING, timing)
        configuration = json.loads((self.verifier.ROOT / '.releaserc.json').read_text())
        hooks = dict(plugin for plugin in configuration['plugins'] if isinstance(plugin, list))['@semantic-release/exec']
        for name in ('verifyReleaseCmd', 'prepareCmd', 'publishCmd'):
            result = subprocess.run(hooks[name].replace('${nextRelease.version}', VERSION), shell=True,
                cwd=shell.root, env=shell.env, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, f'{name}: {result.stdout}{result.stderr}')
        pushes = shell.calls()
        self.assertEqual(len(pushes), 2)
        self.assertEqual([Path(call[2]).name for call in pushes], [f'{identity}.{VERSION}.nupkg' for identity in PAIR])
        for name, expected in self.package_hashes.items():
            self.assertEqual(digest(shell.root / 'pushed' / name), expected)
        outcome = json.loads((shell.root / 'nupkgs/paired-publication/outcome.json').read_text())
        self.assertEqual(outcome['status'], 'paired-public-verified')
        self.assertEqual(set(outcome['packages']), set(PAIR))
        self.assertTrue(all(item['status'] == 'public-verified' for item in outcome['packages'].values()))
        self.assertEqual(outcome['packages_sha256'], self.package_hashes)
        self.assertEqual(outcome['operator_sha256'], digest(self.operator))
        self.assertEqual(outcome['source_sha'], SHA)
        self.assertEqual(outcome['origin'], self.origin)
        self.assertEqual(len((shell.root / 'source.log').read_text().splitlines()), 5)

    def test_snapshot_survives_original_import_changes_and_pushes_only_checked_bytes(self):
        self.mode = 'mutate-original-after-first'
        with self.controls():
            self.import_pair()
            self.publisher.publish(VERSION)
        for name, raw in self.pushes: self.assertEqual(hashlib.sha256(raw).hexdigest(), self.package_hashes[name])

    def test_partial_uncertain_and_public_mismatch_outcomes_are_retained_without_retry(self):
        for mode, pushes, first, second in [('first-push', 1, 'push-uncertain', 'not-attempted'),
                ('second-push', 2, 'public-verified', 'push-uncertain'),
                ('public-mismatch', 1, 'push-succeeded-public-unverified', 'not-attempted'),
                ('source-before-second', 1, 'public-verified', 'not-attempted'),
                ('second-occupied', 1, 'public-verified', 'not-attempted')]:
            with self.subTest(mode=mode):
                # Each test case has a new immutable attempt and no retries.
                self.publisher.IMPORTED = self.root / ('imported-' + mode)
                self.publisher.OUTCOMES = self.root / ('outcomes-' + mode)
                self.initial = self.root / ('preflight-' + mode + '.json')
                self.env['MCPCLI_PAIRED_PREFLIGHT'] = str(self.initial)
                self.mode, self.pushes = mode, []
                with self.controls():
                    self.import_pair()
                    with self.assertRaises((ValueError, subprocess.CalledProcessError)):
                        self.publisher.publish(VERSION)
                    with self.assertRaises(FileExistsError): self.publisher.publish(VERSION)
                self.assertEqual(len(self.pushes), pushes)
                result = json.loads((self.publisher.OUTCOMES / 'outcome.json').read_text())
                self.assertEqual(result['status'], 'partial-or-uncertain')
                self.assertEqual([result['packages'][identity]['status'] for identity in PAIR], [first, second])
                for path in self.publisher.OUTCOMES.rglob('*.json'):
                    self.assertNotIn(self.env['NUGET_API_KEY'], path.read_text())

    def test_missing_key_or_uncertain_registry_never_pushes_and_retains_refusal(self):
        for reason in ('NuGet publication key is required', 'uncertain registry response'):
            self.publisher.OUTCOMES = self.root / ('refusal-' + reason.split()[0])
            with self.controls(), patch.object(self.request, 'check_registry', side_effect=ValueError(reason)):
                with self.assertRaisesRegex(ValueError, reason): self.publisher.publish(VERSION)
            self.assertEqual(self.pushes, [])
            result = json.loads((self.publisher.OUTCOMES / 'outcome.json').read_text())
            self.assertEqual(result['status'], 'failed-before-push')
            self.assertEqual(result['reason'], reason)

    def test_mutated_import_receipt_package_or_extra_package_never_pushes(self):
        for mode in ('hash', 'receipt', 'extra'):
            self.publisher.IMPORTED = self.root / ('bad-import-' + mode)
            self.publisher.OUTCOMES = self.root / ('bad-outcome-' + mode)
            self.initial = self.root / ('bad-preflight-' + mode + '.json')
            self.env['MCPCLI_PAIRED_PREFLIGHT'] = str(self.initial)
            with self.controls():
                self.import_pair()
                if mode == 'hash': next((self.publisher.IMPORTED / 'packages').iterdir()).write_bytes(b'tamper')
                elif mode == 'extra': (self.publisher.IMPORTED / 'packages/extra.nupkg').write_bytes(b'extra')
                else: self.change_json(self.publisher.IMPORTED / 'import.json', lambda document: document.update(operator_sha256='0' * 64))
                with self.assertRaises(ValueError): self.publisher.publish(VERSION)
            self.assertEqual(self.pushes, [])

    def test_unsupported_recovery_refuses_before_external_effects(self):
        with self.controls(), patch.dict(os.environ, {'MCPCLI_RECOVERY_VERSION': VERSION}):
            for action in (self.publisher.prepare, self.publisher.publish):
                with self.assertRaisesRegex(ValueError, 'recovery is unsupported'): action(VERSION)
        self.assertEqual(self.pushes, [])
        self.assertFalse(self.publisher.IMPORTED.exists())
        self.assertFalse(self.publisher.OUTCOMES.exists())

    def test_explicit_automated_authorization_binds_staging_without_claiming_client_sessions(self):
        decision = {'schema': 'mcpcli-paired-automated-acceptance/v1', 'decision': 'approved',
                    'authorization': 'user-requested-human-validation-bypass',
                    'approved_by': 'fixture-owner', 'decided_at_utc': '2026-11-01T00:03:00Z', **self.bindings}
        for change in (None, {'source_sha': 'b' * 40}, {'staging_run_id': 999},
                       {'authorization': 'unknown'}, {'sessions': []}, {'approved_by': 'other-user'},
                       {'decided_at_utc': '2026-10-31T23:59:59Z'}, {'decided_at_utc': '9999-01-01T00:00:00Z'},
                       {'decided_at_utc': None}):
            candidate = {**decision, **(change or {})}
            path = self.root / ('automated-' + str(len(list(self.root.glob('automated-*.json')))) + '.json')
            write_new(path, candidate)
            if change is None:
                self.assertEqual(self.verifier.operator_acceptance(path, self.prepared, self.accepted_path,
                                                                    self.origin, 'fixture-owner'), candidate)
            else:
                with self.assertRaises(ValueError):
                    self.verifier.operator_acceptance(path, self.prepared, self.accepted_path,
                                                      self.origin, 'fixture-owner')

    def test_automated_authorization_publishes_only_exact_candidate_without_claiming_sessions(self):
        decision = {'schema': 'mcpcli-paired-automated-acceptance/v1', 'decision': 'approved',
                    'authorization': 'user-requested-human-validation-bypass',
                    'approved_by': 'fixture-owner', 'decided_at_utc': '2026-11-01T00:03:00Z', **self.bindings}
        self.operator = self.root / 'automated-operator.json'
        write_new(self.operator, decision)
        self.env['MCPCLI_OPERATOR_ACCEPTANCE'] = str(self.operator)
        with self.controls():
            self.import_pair()
            self.publisher.publish(VERSION)
        result = json.loads((self.publisher.OUTCOMES / 'outcome.json').read_text())
        self.assertEqual(result['status'], 'paired-public-verified')
        self.assertEqual(result['operator_sha256'], digest(self.operator))
        self.assertNotIn('sessions', result)
        self.assertEqual([name for name, _ in self.pushes], [f'{identity}.{VERSION}.nupkg' for identity in PAIR])

    def test_operator_decision_requires_fresh_complete_hash_bound_actual_sessions(self):
        mutations = [lambda d: d.update(decision='pending'), lambda d: d.update(approved_by='other-user'),
            lambda d: d.update(source_sha='b' * 40), lambda d: d.update(staging_run_id=999), lambda d: d.update(version='1.2.0'),
            lambda d: d.update(packages={}), lambda d: d.update(acceptance_sha256='0' * 64),
            lambda d: d.update(preparation_sha256='0' * 64), lambda d: d.update(readme_sha256='0' * 64),
            lambda d: d['timing_exception'].update(unassisted_success=True), lambda d: d['timing_exception'].update(first_time_operator=True),
            lambda d: d['sessions'].pop(), lambda d: d['sessions'][0].update(actual_client=False),
            lambda d: d['sessions'][0].update(status='not-executed'), lambda d: d.update(decided_at_utc=None),
            lambda d: d.update(sessions=[None, None, None]), lambda d: d['sessions'][0].update(version='1.2.0'),
            lambda d: d['sessions'][0].update(started_at_utc='2026-10-31T00:01:00Z'),
            lambda d: d['sessions'][0]['environment_approval'].update(ready=False),
            lambda d: d['sessions'][0]['environment_approval'].update(expires_at_utc='2026-11-01T00:01:30Z'),
            lambda d: d['sessions'][0]['evidence'].pop('initialization'),
            lambda d: d['sessions'][0]['evidence']['command'].update(content='tampered'),
            lambda d: d['sessions'][0].update(operation_lists=['parties']), lambda d: d['sessions'][0].update(tools=[]),
            lambda d: d['sessions'][0].update(described_operations=[]),
            lambda d: d['sessions'][0]['command_result'].update(status='unknown'),
            lambda d: d['sessions'][0]['command_result'].update(aggregate_id='wrong-party'),
            lambda d: d['sessions'][0]['command_result'].update(message_id='01m695ptvdn76pqh5f0wte7hs6'),
            lambda d: d['sessions'][0]['tenant_read'].update(tenant='wrong'),
            lambda d: d['sessions'][0]['tenant_read'].update(tenant='system'),
            lambda d: d['sessions'][0]['persisted_party'].update(synthetic_fields_verified=False)]
        for index, change in enumerate(mutations):
            decision = copy.deepcopy(self.decision)
            change(decision)
            self.operator.write_text(json.dumps(decision))
            with self.subTest(index=index), self.controls():
                output = self.root / f'rejected-{index}.json'
                with self.assertRaises(ValueError): self.real_preflight(self.candidate, self.operator, VERSION, output)
                self.assertFalse(output.exists())
        self.assertEqual(self.pushes, [])

    def test_original_staging_archive_source_version_and_acceptance_source_must_match(self):
        with self.controls():
            for sha, version, error in [('b' * 40, VERSION, 'source'), (SHA, '9.0.0', 'version')]:
                with self.subTest(sha=sha, version=version), self.assertRaisesRegex(ValueError, error):
                    self.verifier.validate(self.candidate, self.operator, version, sha, 123, 'fixture-owner', self.root / 'bad.json')
            archive = self.candidate / 'paired-preparation.zip'
            archive.write_bytes(archive.read_bytes() + b'changed original ZIP bytes')
            with self.assertRaisesRegex(ValueError, 'changed after authentication'):
                self.real_preflight(self.candidate, self.operator, VERSION, self.root / 'bad.json')

    def test_acceptance_source_is_cross_checked_even_with_authentic_archive_digest(self):
        path = self.candidate / 'accepted-staging-only.zip'
        with ZipFile(path, 'w') as archive:
            archive.write(self.accepted_path, 'accepted-pair.json')
            source = copy.deepcopy(self.source_gate)
            source['gates']['ci.yml']['jobs'][0]['steps'][0]['conclusion'] = 'skipped'
            archive.writestr('acceptance-source.json', json.dumps(source))
        next(item for item in self.origin['artifacts'] if item['name'] == 'accepted-staging-only')['digest'] = 'sha256:' + digest(path)
        (self.candidate / 'staging-origin.json').write_text(json.dumps(self.origin))
        with self.controls(), self.assertRaisesRegex(ValueError, 'Required step'):
            self.real_preflight(self.candidate, self.operator, VERSION, self.root / 'bad.json')

    def test_credentials_are_refused_before_operator_packet_is_copied_into_import(self):
        with self.controls():
            self.real_preflight(self.candidate, self.operator, VERSION, self.initial)
            self.change_json(self.operator, lambda document: document.update(accidental_secret=self.env['NUGET_API_KEY']))
            with self.assertRaisesRegex(ValueError, 'contains a credential'):
                self.publisher.prepare(VERSION)
        self.assertFalse(self.publisher.IMPORTED.exists())
        self.assertEqual(self.pushes, [])

    def test_packed_readme_and_nuspec_are_rechecked_without_building(self):
        for mode in ('readme', 'source'):
            identity = PAIR[0]
            path = self.staging / f'{identity}.{VERSION}.nupkg'
            with ZipFile(path, 'w') as archive:
                archive.writestr(identity + '.nuspec', f'<package><metadata><id>{identity}</id><version>{VERSION}</version><repository commit="{SHA if mode == "readme" else "b" * 40}" /></metadata></package>')
                archive.writestr('README.md', b'wrong readme' if mode == 'readme' else (self.verifier.ROOT / 'README.md').read_bytes())
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, 'README|source'):
                self.verifier.validate_pair_content(self.staging, VERSION, SHA)



class PublicationBoundaryTests(unittest.TestCase):
    def test_fresh_credentials_are_refused_and_redacted_without_changing_originals(self):
        verifier = module('verify-paired-publication')
        samples = [
            ('jwt', 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJmaXh0dXJlIn0.c3ludGhldGlj', 'c3ludGhldGlj'),
            ('bearer', 'Bearer fixture-fresh-token+/_~.abc==', 'fixture-fresh-token'),
            *[(kind.lower().replace(' ', '-'), f'-----BEGIN {kind}-----\nZml4dHVyZS1wcml2YXRlLWtleQ==\n-----END {kind}-----',
               'Zml4dHVyZS1wcml2YXRlLWtleQ==') for kind in ('PRIVATE KEY', 'RSA PRIVATE KEY', 'EC PRIVATE KEY', 'OPENSSH PRIVATE KEY')],
        ]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name, secret, recognizable in samples:
                for escaped in (False, True):
                    with self.subTest(kind=name, escaped=escaped):
                        serialized = json.dumps({'evidence': secret})
                        if escaped:
                            serialized = serialized.replace('e', '\\u0065').replace('B', '\\u0042')
                        source = root / f'{name}-{escaped}.json'
                        source.write_text(serialized)
                        raw = source.read_bytes()
                        recorded = root / (source.stem + '-recorded.json')
                        with self.assertRaisesRegex(ValueError, 'credential|private key'):
                            verifier.record_operator(serialized, recorded)
                        self.assertFalse(recorded.exists())
                        retained = root / (source.stem + '-retained')
                        verifier.retain_operator([source], retained)
                        manifest = json.loads((retained / 'retention.json').read_text())['entries'][0]
                        self.assertTrue(manifest['redacted'])
                        self.assertEqual(manifest['original_sha256'], hashlib.sha256(raw).hexdigest())
                        self.assertEqual(manifest['retained_sha256'], digest(retained / manifest['retained_name']))
                        self.assertEqual(source.read_bytes(), raw)
                        evidence = json.loads((retained / manifest['retained_name']).read_text())['evidence']
                        self.assertIn('[REDACTED', evidence)
                        self.assertNotIn(recognizable, evidence)

    def test_dispatch_reads_operator_from_event_without_echoing_or_retaining_credentials(self):
        root = Path(__file__).resolve().parents[2]
        workflow = (root / '.github/workflows/release.yml').read_text()
        block = workflow.split('      - name: Authenticate the selected staging run and retain the explicit operator decision\n', 1)[1].split('      - name:', 1)[0]
        self.assertNotIn('OPERATOR_ACCEPTANCE:', block)
        self.assertNotIn('${{ inputs.operator_acceptance }}', workflow)
        command = next(line.strip() for line in block.splitlines() if ' record-operator ' in line)
        secret = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJmaXh0dXJlIn0.c3ludGhldGlj'
        for unsafe in (False, True):
            with self.subTest(unsafe=unsafe), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                event = directory / 'dispatch.json'
                decision = {'evidence': 'Bearer ' + secret if unsafe else 'sanitized actual excerpt'}
                event.write_text(json.dumps({'inputs': {'operator_acceptance': json.dumps(decision)}}))
                environment = {**os.environ, 'GITHUB_EVENT_PATH': str(event), 'RUNNER_TEMP': temporary,
                               'OPERATOR_ACCEPTANCE': json.dumps({'evidence': 'ignored local value'})}
                result = subprocess.run(['bash', '-e', '-c', command], cwd=root, env=environment, text=True, capture_output=True)
                self.assertEqual(result.returncode, 1 if unsafe else 0, result.stderr)
                self.assertEqual(result.stdout, '')
                self.assertNotIn(secret, result.stderr)
                output = directory / 'operator-acceptance.json'
                self.assertEqual(output.exists(), not unsafe)
                if not unsafe:
                    self.assertEqual(json.loads(output.read_text()), decision)
                else:
                    self.assertIn('Paired publication refused:', result.stderr)
                    self.assertEqual(json.loads(output.with_suffix('.json.failure.json').read_text())['status'], 'refused')
                retained = directory / 'retained'
                result = subprocess.run([sys.executable, str(root / 'scripts/verify-paired-publication.py'), 'retain-operator',
                    '--input', str(output), '--output', str(retained)], env=environment, text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn(secret, result.stdout + result.stderr)
                for path in directory.rglob('*'):
                    if path.is_file() and path != event:
                        self.assertNotIn(secret, path.read_text())

    def test_local_operator_json_environment_input_remains_supported(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'operator.json'
            environment = {key: value for key, value in os.environ.items() if key != 'GITHUB_EVENT_PATH'}
            environment['OPERATOR_ACCEPTANCE'] = '{"decision":"approved","evidence":"redacted excerpt"}'
            result = subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1] / 'verify-paired-publication.py'),
                'record-operator', '--output', str(output)], env=environment, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(output.read_text()), json.loads(environment['OPERATOR_ACCEPTANCE']))

    def test_operator_recording_refuses_known_credentials_and_retention_redacts_rejected_packets(self):
        verifier = module('verify-paired-publication')
        with tempfile.TemporaryDirectory() as temporary, patch.dict(os.environ, {'GH_TOKEN': 'fixture-github-secret',
                'NUGET_API_KEY': 'fixture-publication-secret'}):
            root = Path(temporary)
            for key in ('GH_TOKEN', 'NUGET_API_KEY'):
                output = root / (key + '.json')
                with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'credential'):
                    verifier.record_operator(json.dumps({'evidence': os.environ[key]}), output)
                self.assertFalse(output.exists())
            safe = root / 'safe.json'
            verifier.record_operator('{"decision":"approved","evidence":"redacted excerpt"}', safe)
            rejected = root / 'rejected.json'
            rejected.write_text('{"evidence":"fixture-publication-secret","escaped":"fixture-\\u0067ithub-secret"}')
            raw = rejected.read_bytes()
            output = root / 'retained'
            verifier.retain_operator([safe, rejected, root / 'absent'], output)
            manifest = json.loads((output / 'retention.json').read_text())
            self.assertEqual([item['redacted'] for item in manifest['entries']], [False, True])
            self.assertEqual((output / '1-safe.json').read_bytes(), safe.read_bytes())
            for path in output.iterdir():
                self.assertNotIn(os.environ['GH_TOKEN'], path.read_text())
                self.assertNotIn(os.environ['NUGET_API_KEY'], path.read_text())
            self.assertEqual(rejected.read_bytes(), raw)
            self.assertEqual(manifest['entries'][1]['original_sha256'], hashlib.sha256(raw).hexdigest())
            workflow = (Path(__file__).resolve().parents[2] / '.github/workflows/release.yml').read_text()
            upload = workflow.split('      - name: Retain paired publication success, refusal or partial outcomes', 1)[1].split('  recover:', 1)[0]
            self.assertNotIn('            ${{ runner.temp }}/operator-acceptance.json\n', upload)
            self.assertIn('!nupkgs/paired/operator.json', upload)
            self.assertIn('${{ runner.temp }}/retained-operator/', upload)

    def test_authenticated_fetch_checks_downloaded_bytes_and_preserves_prior_attempts(self):
        verifier = module('verify-paired-publication')
        raw = io.BytesIO()
        with ZipFile(raw, 'w') as archive: archive.writestr('fixture.txt', 'fixture')
        origin = {'artifacts': [{'id': 1, 'name': 'fixture', 'digest': 'sha256:' + hashlib.sha256(raw.getvalue()).hexdigest()}]}
        with tempfile.TemporaryDirectory() as temporary, patch.object(verifier, 'authenticate_run', return_value=origin):
            output = Path(temporary) / 'candidate'
            with patch.object(subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, stdout=raw.getvalue())) as download:
                verifier.fetch('fixture/repo', 123, SHA, output)
                self.assertEqual((output / 'fixture.zip').read_bytes(), raw.getvalue())
                with self.assertRaises(FileExistsError): verifier.fetch('fixture/repo', 123, SHA, output)
                self.assertEqual(download.call_count, 1)
            with patch.object(subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, stdout=raw.getvalue() + b'tamper')):
                with self.assertRaisesRegex(ValueError, 'GitHub artifact digest'):
                    verifier.fetch('fixture/repo', 123, SHA, Path(temporary) / 'changed')
                self.assertTrue((Path(temporary) / 'changed/staging-origin.json').is_file())

    def test_missing_credentials_retains_exact_preflight_refusal_without_external_calls(self):
        verifier = module('verify-paired-publication')
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'preflight.json'
            with patch.dict(os.environ, {'NUGET_API_KEY': ''}), patch.object(sys, 'argv', ['verify', 'verify',
                    '--candidate', '/absent', '--operator', '/absent', '--staging-run', '123', '--source-sha', SHA,
                    '--version', VERSION, '--actor', 'fixture', '--output', str(output)]), \
                    patch.object(subprocess, 'run') as external, contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(verifier.main(), 1)
                external.assert_not_called()
            self.assertFalse(output.exists())
            refusal = json.loads(output.with_name('preflight.json.failure.json').read_text())
            self.assertEqual(refusal['reason'], 'NuGet publication key is required')
            self.assertEqual(refusal['status'], 'refused')

    def test_first_ever_absence_requires_both_explicit_404s(self):
        request = module('release-request')
        for statuses, accepted in [([404, 404], True), ([404, 403], False), ([404, 500], False), ([500], False)]:
            responses = [HTTPError('fixture', status, 'fixture', {}, None) for status in statuses]
            with self.subTest(statuses=statuses), patch.object(request, 'urlopen', side_effect=responses):
                if accepted: self.assertEqual(request.registry_versions('Hexalith.McpCli', True), [])
                else:
                    with self.assertRaises(ValueError): request.registry_versions('Hexalith.McpCli', True)
        with patch.object(request, 'urlopen', side_effect=TimeoutError()):
            with self.assertRaisesRegex(ValueError, 'uncertain'): request.registry_versions('Hexalith.McpCli', True)

    def test_both_registry_identities_are_checked_and_occupied_version_fails(self):
        request = module('release-request')
        with patch.dict(os.environ, {'NUGET_API_KEY': 'fixture'}):
            for responses, expected in [([[], []], None), ([[VERSION]], PAIR[0]), ([[], [VERSION.upper()]], PAIR[1])]:
                with self.subTest(responses=responses), patch.object(request, 'registry_versions', side_effect=responses) as query:
                    if expected:
                        with self.assertRaisesRegex(ValueError, expected): request.check_registry(VERSION, 'paired')
                    else: request.check_registry(VERSION, 'paired')
                    self.assertEqual([call.args[0] for call in query.call_args_list], PAIR[:query.call_count])
        with patch.dict(os.environ, {'NUGET_API_KEY': ''}), patch.object(request, 'registry_versions') as query:
            with self.assertRaisesRegex(ValueError, 'key is required'): request.check_registry(VERSION, 'paired')
            query.assert_not_called()

    def test_global_marker_closes_new_bootstrap_and_second_paired_version_remains_possible(self):
        publisher, request = module('publish-paired-release'), module('release-request')
        gate = module('verify-release-source')
        marker = {'ref': 'refs/tags/' + publisher.MARKER, 'object': {'type': 'commit', 'sha': SHA}}
        old = {'ref': marker['ref'] + '-v1.2.2', 'object': {'type': 'commit', 'sha': 'b' * 40}}
        with patch.dict(os.environ, {'REPOSITORY': 'fixture/repo'}), patch.object(publisher, 'module', return_value=gate), \
                patch.object(gate, 'github_json', side_effect=[[marker, old], []]), patch.object(subprocess, 'run') as command:
            publisher.reserve_version(VERSION, SHA)
            self.assertEqual(command.call_count, 1)
            self.assertIn('ref=' + marker['ref'] + '-v' + VERSION, command.call_args.args[0])
        with patch.dict(os.environ, {'REPOSITORY': 'fixture/repo'}), patch('paired_release.module', return_value=gate):
            for response in ([marker], {'error': 'uncertain'}):
                with patch.object(gate, 'github_json', return_value=response), self.assertRaisesRegex(ValueError, 'closed'):
                    request.check_bootstrap_line()
            with patch.object(gate, 'github_json', return_value=[]): request.check_bootstrap_line()
        with patch.dict(os.environ, {'REPOSITORY': 'fixture/repo'}), patch.object(publisher, 'module', return_value=gate), \
                patch.object(gate, 'github_json', side_effect=[[marker], [old]]), patch.object(subprocess, 'run') as command:
            with self.assertRaisesRegex(ValueError, 'already started'): publisher.reserve_version(VERSION, SHA)
            command.assert_not_called()

    def test_bootstrap_recovery_cannot_target_paired_or_later_release_tags(self):
        request = module('release-request')
        gate = module('verify-release-source')
        marker = {'ref': 'refs/tags/mcpcli-paired-publication-started', 'object': {'type': 'commit', 'sha': 'b' * 40}}
        version = {'ref': marker['ref'] + '-v' + VERSION, 'object': {'type': 'commit', 'sha': 'c' * 40}}
        cases = [('before-any-pair', [[]], SHA, 0, True), ('historical', [[marker], []], SHA, 0, True),
                 ('paired-version', [[marker, version], [version]], SHA, 0, False),
                 ('same-source', [[marker], []], 'b' * 40, 0, False),
                 ('later-source', [[marker], []], 'c' * 40, 1, False),
                 ('missing-global', [[version]], SHA, 0, False), ('uncertain', [{'bad': 'state'}], SHA, 0, False)]
        for mode, responses, sha, code, accepted in cases:
            with self.subTest(mode=mode), patch.dict(os.environ, {'REPOSITORY': 'fixture/repo'}), \
                    patch('paired_release.module', return_value=gate), patch.object(gate, 'github_json', side_effect=responses), \
                    patch.object(subprocess, 'run', return_value=subprocess.CompletedProcess([], code)) as git:
                if accepted: request.check_bootstrap_recovery_line(VERSION, sha)
                else:
                    with self.assertRaises(ValueError): request.check_bootstrap_recovery_line(VERSION, sha)
                if mode in ('before-any-pair', 'paired-version', 'missing-global', 'uncertain'): git.assert_not_called()

    def test_original_run_and_artifact_metadata_must_be_exact_and_jobs_executed(self):
        verifier = module('verify-paired-publication')
        gate = module('verify-release-source')
        run = {'id': 123, 'workflow_id': 1, 'path': '.github/workflows/release.yml', 'head_sha': SHA, 'head_branch': 'main',
               'event': 'workflow_dispatch', 'head_repository': {'full_name': 'fixture/repo'}, 'status': 'completed',
               'conclusion': 'success', 'run_attempt': 1, 'updated_at': '2026-11-01T00:00:00Z'}
        artifacts = [{'id': index + 1, 'name': name, 'expired': False, 'digest': 'sha256:' + 'a' * 64,
                      'workflow_run': {'id': 123, 'head_sha': SHA, 'head_branch': 'main'}}
                     for index, name in enumerate(verifier.ARTIFACTS)]
        mutations = [('run', lambda d: d.update(head_sha='b' * 40)), ('run', lambda d: d.update(head_branch='topic')),
            ('run', lambda d: d.update(status='in_progress')), ('run', lambda d: d.update(event='push')),
            ('run', lambda d: d.update(workflow_id=2)), ('run', lambda d: d.update(path='different.yml')),
            ('run', lambda d: d.update(conclusion='failure')), ('artifacts', lambda d: d[0].update(expired=True)),
            ('artifacts', lambda d: d[0].update(digest='bad')), ('artifacts', lambda d: d[0]['workflow_run'].update(id=999)),
            ('artifacts', lambda d: d.pop()), ('artifacts', lambda d: d.append(copy.deepcopy(d[0]))),
            ('jobs', lambda d: d[0]['steps'][0].update(conclusion='skipped'))]
        for target, mutate in mutations + [('pass', lambda d: None)]:
            state = {'run': copy.deepcopy(run), 'artifacts': copy.deepcopy(artifacts), 'jobs': jobs(verifier.STAGING_JOBS)}
            if target != 'pass': mutate(state[target])
            def api(endpoint, *args):
                if endpoint.endswith('release.yml'): return {'id': 1}
                if endpoint.endswith('/artifacts'): return {'total_count': len(state['artifacts']), 'artifacts': state['artifacts']}
                return state['run']
            with self.subTest(target=target), patch.object(verifier, 'api', side_effect=api), \
                    patch.object(verifier, 'module', return_value=gate), \
                    patch.object(gate, 'github_json', return_value={'total_count': len(state['jobs']), 'jobs': state['jobs']}):
                if target == 'pass': self.assertEqual(verifier.authenticate_run('fixture/repo', 123, SHA)['staging_run_id'], 123)
                else:
                    with self.assertRaises(ValueError): verifier.authenticate_run('fixture/repo', 123, SHA)

    def test_full_ci_requires_the_release_automation_job_and_both_executed_steps(self):
        gate = module('verify-release-source')
        self.assertIn('release-automation', gate.STAGING_JOBS)
        required = gate.STAGING_JOBS['release-automation']
        for state in ('missing', 'skipped', *required):
            executed = jobs(gate.STAGING_JOBS)
            if state == 'missing': executed = [job for job in executed if job['name'] != 'release-automation']
            elif state == 'skipped': executed[0]['conclusion'] = 'skipped'
            else: next(step for step in executed[0]['steps'] if step['name'] == state)['conclusion'] = 'skipped'
            with self.subTest(state=state), self.assertRaises(ValueError): gate.validate_jobs(executed, gate.STAGING_JOBS)

    def test_workflow_refuses_no_release_or_partial_results_as_paired_completion(self):
        root = Path(__file__).resolve().parents[2]
        block = (root / '.github/workflows/release.yml').read_text().split(
            '      - name: Require both paired packages publicly verified\n', 1)[1].split('      - name:', 1)[0]
        command = '\n'.join(line[10:] for line in block.split('        run: |\n', 1)[1].splitlines())
        complete = {'status': 'paired-public-verified', 'source_sha': SHA, 'staging_run_id': '123',
                    'packages': {identity: {'status': 'public-verified'} for identity in PAIR}}
        for mode in ('missing', 'partial', 'wrong-source', 'wrong-run', 'one-package', 'passed'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                target = Path(temporary) / 'nupkgs/paired-publication/outcome.json'
                target.parent.mkdir(parents=True)
                outcome = copy.deepcopy(complete)
                if mode == 'partial': outcome['packages'][PAIR[1]]['status'] = 'push-uncertain'
                elif mode == 'wrong-source': outcome['source_sha'] = 'b' * 40
                elif mode == 'wrong-run': outcome['staging_run_id'] = '999'
                elif mode == 'one-package': outcome['packages'].pop(PAIR[1])
                if mode != 'missing': target.write_text(json.dumps(outcome))
                result = subprocess.run(['bash', '-e', '-c', command], cwd=temporary, capture_output=True,
                    env={**os.environ, 'RUNNER_TEMP': temporary, 'DISPATCH_SHA': SHA, 'MCPCLI_STAGING_RUN_ID': '123'})
                self.assertEqual(result.returncode == 0, mode == 'passed', result.stderr)
                receipt = json.loads((Path(temporary) / 'paired-publication-completion.json').read_text())
                self.assertEqual(receipt['status'], 'passed' if mode == 'passed' else 'refused')

    def test_workflow_binds_original_source_run_operator_production_and_retained_outcomes(self):
        root = Path(__file__).resolve().parents[2]
        workflow = (root / '.github/workflows/release.yml').read_text()
        publication = workflow.split('  publish:\n', 1)[1].split('  recover:\n', 1)[0]
        self.assertIn('    environment: production', publication)
        self.assertIn('id-token: write', publication)
        self.assertNotIn('${{ inputs.operator_acceptance }}', workflow)
        for text in ('MCPCLI_STAGING_RUN_ID: ${{ inputs.staging_run_id }}',
                     'DISPATCH_SHA: ${{ github.sha }}', '--source-sha "$DISPATCH_SHA"', 'paired-publication-outcomes',
                     "if: ${{ always() && inputs.phase == 'paired' }}", 'nupkgs/paired-publication/'):
            self.assertIn(text, publication)
        self.assertLess(publication.index('after production approval'), publication.index('verify-paired-publication.py fetch'))
        self.assertLess(publication.index('verify-paired-publication.py fetch'), publication.index('Get short-lived NuGet'))
        config = json.loads((root / '.releaserc.json').read_text())
        self.assertIn('nupkgs/paired/packages/*.nupkg', config['plugins'][-1][1]['assets'])
        ci = (root / '.github/workflows/ci.yml').read_text().split('  release-automation:', 1)[1].split('  conformance-vector-contract:', 1)[0]
        for text in ('scripts/tests', 'select-release-version.test.mjs', *module('verify-release-source').STAGING_JOBS['release-automation']):
            self.assertIn(text, ci)


if __name__ == '__main__':
    unittest.main()
