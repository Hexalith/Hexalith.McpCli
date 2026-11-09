"""Publication refusal, immutable-byte and partial-outcome controls with synthetic evidence."""

import contextlib
import copy
import hashlib
import io
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
import warnings
from zipfile import ZipFile, ZipInfo

import test_paired_release as fixtures
import test_bootstrap_release as shell_fixtures
from test_paired_release import SHA, VERSION, jobs
from paired_release import PAIR, digest, module, packages, validate_source_evidence, write_new


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
        self.download_push_counts = []
        self.mode = None
        self.preflight_count = 0

    def execute(self, argv, **kwargs):
        if 'verify-release-source.py' in str(argv[1]):
            if self.mode == 'source-before-second' and len(self.pushes) == 1:
                raise subprocess.CalledProcessError(1, argv, stderr=b'main moved\n' + self.env['NUGET_API_KEY'].encode())
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
        self.download_push_counts.append(len(self.pushes))
        name = next(filename for filename in self.package_hashes if filename.lower() in url)
        destination.write_bytes((self.staging / name).read_bytes())
        with ZipFile(destination, 'a') as archive:
            archive.writestr('.signature.p7s', 'fixture NuGet repository signature')
            archive.writestr('package/services/metadata/core-properties/nuget.psmdcp', 'fixture NuGet metadata')
            if self.mode == 'public-mismatch': archive.writestr('unapproved.txt', 'different consumer bytes')
            if self.mode == 'public-duplicate': archive.writestr('fixture.dll', archive.read('fixture.dll'))

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
        self.assertEqual(result['operator_decision'], {'schema': self.decision['schema']})
        for name in ('snapshot-preflight.json', 'before-push-1.json', 'before-push-2.json'):
            receipt = json.loads((self.publisher.OUTCOMES / name).read_text())
            self.assertEqual(receipt['operator_decision'], {'schema': self.decision['schema']})
        self.assertEqual(result['origin'], self.origin)

    def test_public_verification_waits_until_both_guarded_pushes_complete(self):
        with self.controls():
            self.import_pair()
            self.publisher.publish(VERSION)
        self.assertEqual(self.download_push_counts, [2, 2])
        self.assertEqual(self.preflight_count, 5)

    def test_changed_valid_operator_decision_refuses_import_after_initial_preflight(self):
        with self.controls() as reserve:
            self.real_preflight(self.candidate, self.operator, VERSION, self.initial)
            self.change_json(self.operator, lambda document: document.update(decided_at_utc='2026-11-01T00:03:01Z'))
            with self.assertRaisesRegex(ValueError, 'Preflight bindings changed before import'):
                self.publisher.prepare(VERSION)
        self.assertEqual(self.preflight_count, 2)
        self.assertTrue((self.publisher.IMPORTED / 'preflight.json').exists())
        self.assertFalse((self.publisher.IMPORTED / 'import.json').exists())
        self.assertFalse((self.publisher.IMPORTED / 'packages').exists())
        self.assertEqual(self.pushes, [])
        reserve.assert_not_called()

    def test_duplicate_public_archive_member_refuses_even_when_consumer_bytes_match(self):
        self.mode = 'public-duplicate'
        with self.controls():
            self.import_pair()
            with self.assertWarnsRegex(UserWarning, 'Duplicate name'), self.assertRaisesRegex(ValueError, 'duplicate archive members'):
                self.publisher.publish(VERSION)
        self.assertEqual(len(self.pushes), 2)
        outcome = json.loads((self.publisher.OUTCOMES / 'outcome.json').read_text())
        self.assertEqual(outcome['status'], 'partial-or-uncertain')
        self.assertEqual([outcome['packages'][identity]['status'] for identity in PAIR],
                         ['push-succeeded-public-unverified'] * 2)
        self.assertFalse(list(self.publisher.OUTCOMES.glob('*-public-verification.json')))

    def test_configured_shell_hooks_publish_pair_and_first_source_bound_markers(self):
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
        references = json.loads((shell.root / 'paired-refs.json').read_text())
        self.assertEqual(references, [{'ref': 'refs/tags/' + self.publisher.MARKER + suffix,
            'object': {'type': 'commit', 'sha': SHA}} for suffix in ('', '-v' + VERSION)])
        with patch.dict(os.environ, shell.env), patch.object(self.request, 'registry_versions', return_value=['2.0.1']):
            with self.assertRaisesRegex(ValueError, 'closed'):
                self.request.check_bootstrap_line()
            with self.assertRaisesRegex(ValueError, 'not in the fixed historical allowlist'):
                self.request.historical_sha(VERSION)
        self.assertEqual(self.request.historical_sha('1.0.0'),
                         'd9f822d64f7afa9bd51ca1698f5051147b86b554')

    def test_snapshot_survives_original_import_changes_and_pushes_only_checked_bytes(self):
        self.mode = 'mutate-original-after-first'
        with self.controls():
            self.import_pair()
            self.publisher.publish(VERSION)
        for name, raw in self.pushes: self.assertEqual(hashlib.sha256(raw).hexdigest(), self.package_hashes[name])

    def test_partial_uncertain_and_public_mismatch_outcomes_are_retained_without_retry(self):
        for mode, pushes, first, second in [('first-push', 1, 'push-uncertain', 'not-attempted'),
                ('second-push', 2, 'push-succeeded-public-unverified', 'push-uncertain'),
                ('public-mismatch', 2, 'push-succeeded-public-unverified', 'push-succeeded-public-unverified'),
                ('source-before-second', 1, 'push-succeeded-public-unverified', 'not-attempted'),
                ('second-occupied', 1, 'push-succeeded-public-unverified', 'not-attempted')]:
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
                if mode == 'source-before-second':
                    self.assertTrue(result['reason'].endswith('main moved\n[REDACTED]'), result['reason'])
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
        for mode in ('hash', 'receipt', 'decision', 'extra'):
            self.publisher.IMPORTED = self.root / ('bad-import-' + mode)
            self.publisher.OUTCOMES = self.root / ('bad-outcome-' + mode)
            self.initial = self.root / ('bad-preflight-' + mode + '.json')
            self.env['MCPCLI_PAIRED_PREFLIGHT'] = str(self.initial)
            with self.controls():
                self.import_pair()
                if mode == 'hash': next((self.publisher.IMPORTED / 'packages').iterdir()).write_bytes(b'tamper')
                elif mode == 'extra': (self.publisher.IMPORTED / 'packages/extra.nupkg').write_bytes(b'extra')
                elif mode == 'decision': self.change_json(self.publisher.IMPORTED / 'import.json',
                    lambda document: document.update(operator_decision={'schema': 'mcpcli-paired-automated-acceptance/v1'}))
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
        # A self-consistent decision from a bot or an unauthenticated actor never attests the bypass.
        for index, actor in enumerate(('fixture-app[bot]', '')):
            path = self.root / f'automated-actor-{index}.json'
            write_new(path, {**decision, 'approved_by': actor})
            with self.subTest(actor=actor), self.assertRaisesRegex(ValueError, 'Automated authorization must bind'):
                self.verifier.operator_acceptance(path, self.prepared, self.accepted_path, self.origin, actor)

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
        expected = {'schema': decision['schema'], 'authorization': decision['authorization']}
        self.assertEqual(result['operator_decision'], expected)
        for path in (self.initial, self.publisher.IMPORTED / 'preflight.json',
                     self.publisher.IMPORTED / 'import.json', self.publisher.OUTCOMES / 'snapshot-preflight.json',
                     self.publisher.OUTCOMES / 'before-push-1.json', self.publisher.OUTCOMES / 'before-push-2.json'):
            self.assertEqual(json.loads(path.read_text())['operator_decision'], expected)
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
            lambda d: d.update(decided_at_utc='9999-01-01T00:00:00Z'),
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
            *[lambda d, value=value: d['sessions'][0]['persisted_party'].update(synthetic_fields_verified=value)
              for value in (False, 'false', 'true', 1, ['verified'], {'verified': True})]]
        for index, change in enumerate(mutations):
            decision = copy.deepcopy(self.decision)
            change(decision)
            self.operator.write_text(json.dumps(decision))
            with self.subTest(index=index), self.controls():
                output = self.root / f'rejected-{index}.json'
                with self.assertRaises(ValueError): self.real_preflight(self.candidate, self.operator, VERSION, output)
                self.assertFalse(output.exists())
        self.assertEqual(self.pushes, [])
        # Session evidence approved by a bot or an unauthenticated actor is refused even when self-consistent.
        for index, actor in enumerate(('fixture-owner', 'fixture-app[bot]', '')):
            path = self.root / f'actual-actor-{index}.json'
            write_new(path, {**copy.deepcopy(self.decision), 'approved_by': actor})
            with self.subTest(actor=actor):
                if actor == 'fixture-owner':
                    accepted = self.verifier.operator_acceptance(path, self.prepared, self.accepted_path, self.origin, actor)
                    self.assertEqual(accepted['approved_by'], actor)
                    continue
                with self.assertRaisesRegex(ValueError, 'Explicit authenticated operator decision'):
                    self.verifier.operator_acceptance(path, self.prepared, self.accepted_path, self.origin, actor)

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

    def test_recomputed_acceptance_must_equal_authenticated_and_operator_bound_record(self):
        self.change_json(self.accepted_path, lambda document: document.update(publication='changed acceptance'))
        acceptance_hash = digest(self.accepted_path)
        self.decision['acceptance_sha256'] = acceptance_hash
        for session in self.decision['sessions']:
            session['acceptance_sha256'] = acceptance_hash
        self.operator.write_text(json.dumps(self.decision))
        archive_path = self.candidate / 'accepted-staging-only.zip'
        with ZipFile(archive_path, 'w') as archive:
            archive.write(self.accepted_path, 'accepted-pair.json')
            archive.write(self.acceptance_source, 'acceptance-source.json')
        next(item for item in self.origin['artifacts'] if item['name'] == 'accepted-staging-only')['digest'] = 'sha256:' + digest(archive_path)
        (self.candidate / 'staging-origin.json').write_text(json.dumps(self.origin))
        output = self.root / 'refused-acceptance.json'
        with self.controls(), self.assertRaisesRegex(ValueError, 'does not equal recomputed acceptance'):
            self.real_preflight(self.candidate, self.operator, VERSION, output)
        self.assertFalse(output.exists())
        self.assertEqual(self.pushes, [])

    def test_real_paired_source_producer_writes_evidence_accepted_by_publication(self):
        gate = module('verify-release-source')
        output = self.root / 'produced-source.json'
        requested = []
        workflow_runs = {workflow: {'id': index + 10, 'run_number': 1, 'run_attempt': 1,
            'head_sha': SHA, 'head_branch': 'main', 'event': 'push', 'status': 'completed',
            'conclusion': 'success', 'html_url': 'https://example.invalid/' + workflow}
            for index, workflow in enumerate(('ci.yml', 'commitlint.yml'))}
        def github(endpoint, *parameters):
            requested.append(endpoint)
            if endpoint.endswith('/git/ref/heads/main'):
                return {'object': {'sha': SHA}}
            for workflow, run in workflow_runs.items():
                if endpoint.endswith('/workflows/' + workflow + '/runs'):
                    return {'workflow_runs': [run]}
                if endpoint.endswith(f'/runs/{run["id"]}/attempts/1/jobs'):
                    required = gate.STAGING_JOBS if workflow == 'ci.yml' else gate.STAGING_COMMITLINT_JOBS
                    result = jobs(required)
                    return {'total_count': len(result), 'jobs': result}
            self.fail('Unexpected GitHub request: ' + endpoint)
        def git(argv, **kwargs):
            values = {('git', 'rev-parse', 'HEAD'): SHA, ('git', 'branch', '--show-current'): '',
                      ('git', 'status', '--porcelain', '--untracked-files=normal'): ''}
            self.assertIn(tuple(argv), values)
            return subprocess.CompletedProcess(argv, 0, stdout=values[tuple(argv)] + '\n', stderr='')
        prerequisite = module('verify-paired-prerequisites')
        with patch.dict(os.environ, {'REPOSITORY': 'fixture/repo'}), \
                patch.object(sys, 'argv', ['verify-release-source.py', '--output', str(output), '--', SHA, 'refs/heads/main', 'paired']), \
                patch.object(gate, 'github_json', side_effect=github), patch.object(subprocess, 'run', side_effect=git), \
                patch('paired_release.module', return_value=prerequisite), \
                patch.object(prerequisite, 'verify', return_value=self.source_gate['fr22']) as verify, \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(gate.main(), 0)
        verify.assert_called_once_with()
        document = json.loads(output.read_text())
        validate_source_evidence(document, SHA)
        self.assertEqual(set(document['gates']), {'ci.yml', 'commitlint.yml'})
        self.assertEqual(document['current_main'], SHA)
        self.assertEqual(len(requested), 5)
        self.assertFalse(any('bootstrap-package.yml' in endpoint for endpoint in requested))
        self.assertEqual(self.pushes, [])

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

    def test_staged_package_with_duplicate_or_unsafe_members_is_refused(self):
        path = self.staging / f'{PAIR[0]}.{VERSION}.nupkg'
        original = path.read_bytes()
        self.verifier.validate_pair_content(self.staging, VERSION, SHA)
        for member in ('fixture.dll', '../escape.txt', '/absolute.txt', 'lib\\escape.dll'):
            path.write_bytes(original)
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', UserWarning)
                with ZipFile(path, 'a') as archive: archive.writestr(member, 'unapproved member')
            with self.subTest(member=member), self.assertRaisesRegex(ValueError, 'unsafe or duplicate members'):
                self.verifier.validate_pair_content(self.staging, VERSION, SHA)

    def test_candidate_symlink_or_extra_entry_is_refused_before_import(self):
        link = self.root / 'candidate-link'
        link.symlink_to(self.candidate, target_is_directory=True)
        refusal = 'only authenticated original staging archives'
        with self.controls():
            output = self.root / 'symlink-preflight.json'
            with self.assertRaisesRegex(ValueError, refusal):
                self.real_preflight(link, self.operator, VERSION, output)
            self.assertFalse(output.exists())
            self.real_preflight(self.candidate, self.operator, VERSION, self.initial)
            (self.candidate / 'unauthenticated.txt').write_text('not a staging archive')
            output = self.root / 'extra-preflight.json'
            with self.assertRaisesRegex(ValueError, refusal):
                self.real_preflight(self.candidate, self.operator, VERSION, output)
            self.assertFalse(output.exists())
            with self.assertRaisesRegex(ValueError, refusal):
                self.publisher.prepare(VERSION)
        self.assertFalse((self.publisher.IMPORTED / 'import.json').exists())
        self.assertFalse((self.publisher.IMPORTED / 'packages').exists())
        self.assertEqual(self.pushes, [])



class PublicationBoundaryTests(unittest.TestCase):
    def test_unsafe_or_duplicate_staging_archive_members_are_refused_before_extraction(self):
        verifier = module('verify-paired-publication')
        def archive(*members):
            buffer = io.BytesIO()
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', UserWarning)
                with ZipFile(buffer, 'w') as zipped:
                    for member in members: zipped.writestr(member, 'fixture')
            return buffer.getvalue()
        link = ZipInfo('link')
        link.external_attr = 0o120777 << 16
        cases = {'duplicate': archive('a.txt', 'a.txt'), 'absolute': archive('/absolute.txt'),
                 'parent': archive('../escape.txt'), 'backslash': archive('dir\\escape.txt'),
                 'drive': archive('C:escape.txt'), 'symlink': archive(link)}
        with tempfile.TemporaryDirectory() as temporary:
            safe = Path(temporary) / 'safe'
            verifier.extract(archive('dir/a.txt', 'b.txt'), safe)
            self.assertEqual((safe / 'dir/a.txt').read_text(), 'fixture')
            for name, data in cases.items():
                target = Path(temporary) / name
                with self.subTest(name=name):
                    with self.assertRaisesRegex(ValueError, 'Unsafe or duplicate staging artifact member'):
                        verifier.extract(data, target)
                    self.assertFalse(target.exists())

    def test_named_private_containers_are_redacted_including_duplicates_and_encoded_json(self):
        verifier = module('verify-paired-publication')
        component = 'synthetic-private-key-component'
        for key in ('PrivateKey', 'SigningKey'):
            for value in ({'d': component}, [component, {'nested': [component]}]):
                for depth in range(3):
                    for duplicate in (False, True):
                        with self.subTest(key=key, value=value, depth=depth, duplicate=duplicate), tempfile.TemporaryDirectory() as temporary:
                            root = Path(temporary)
                            inner = '{' + json.dumps(key) + ':' + json.dumps(value)
                            if duplicate:
                                inner += ',' + json.dumps(key) + ':"[REDACTED]"'
                            inner += ',"message":"safe container evidence"}'
                            for _ in range(depth):
                                inner = json.dumps(inner)
                            raw = '{"evidence":' + inner + ',"safe":[{"unchanged":true}]}'
                            recorded = root / 'recorded.json'
                            with self.assertRaisesRegex(ValueError, 'credential|duplicate JSON keys'):
                                verifier.record_operator(raw, recorded)
                            self.assertFalse(recorded.exists())
                            source = root / 'source.json'
                            source.write_text(raw)
                            verifier.retain_operator([source], root / 'retained')
                            retained = (root / 'retained/1-source.json').read_text()
                            self.assertNotIn(component, retained)
                            document = json.loads(retained)
                            self.assertEqual(document['safe'], [{'unchanged': True}])
                            nested = document['evidence']
                            for _ in range(depth):
                                nested = json.loads(nested)
                            self.assertEqual(nested, {key: '[REDACTED]', 'message': 'safe container evidence'})
                            self.assertEqual(source.read_text(), raw)
                            entry = json.loads((root / 'retained/retention.json').read_text())['entries'][0]
                            self.assertTrue(entry['redacted'])
                            self.assertEqual(entry['original_sha256'], digest(source))
                            self.assertEqual(entry['retained_sha256'], digest(root / 'retained/1-source.json'))

    def test_named_private_operator_values_are_refused_and_redacted_in_raw_and_encoded_json(self):
        verifier = module('verify-paired-publication')
        secret, duplicate_secret = 'unbound-named-key-first-20261106', 'unbound-named-key-second-20261106'
        ordinary = 'retain "quotes", back\\slashes and new\nlines; SigningKey is configured'
        self.assertNotIn(secret, verifier.credentials())
        self.assertNotIn(duplicate_secret, verifier.credentials())
        for key in ('SigningKey', 'PrivateKey', 'Authentication:JwtBearer:SigningKey', 'pRiVaTeKeY'):
            for depth in range(3):
                for duplicate in (False, True):
                    with self.subTest(key=key, depth=depth, duplicate=duplicate), tempfile.TemporaryDirectory() as temporary:
                        root = Path(temporary)
                        inner = '{' + json.dumps(key) + ':' + json.dumps(secret)
                        if duplicate:
                            inner += ',' + json.dumps(key) + ':' + json.dumps(duplicate_secret)
                        inner += ',"message":' + json.dumps(ordinary) + '}'
                        for _ in range(depth):
                            inner = json.dumps(inner)
                        serialized = '{"evidence":' + inner + ',"message":' + json.dumps(ordinary) + '}'
                        recorded = root / 'recorded.json'
                        stdout, stderr = io.StringIO(), io.StringIO()
                        reason = ('Operator acceptance contains duplicate JSON keys.' if duplicate and depth == 0 else
                                  'Operator acceptance contains a credential or private key; redact the source evidence first.')
                        with patch.dict(os.environ, {'OPERATOR_ACCEPTANCE': serialized, 'GITHUB_EVENT_PATH': ''}), \
                                patch.object(sys, 'argv', ['verify-paired-publication.py', 'record-operator', '--output', str(recorded)]), \
                                contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                            self.assertEqual(verifier.main(), 1)
                        self.assertEqual(stdout.getvalue(), '')
                        self.assertEqual(stderr.getvalue(), 'Paired publication refused: ' + reason + '\n')
                        self.assertEqual(json.loads(recorded.with_name('recorded.json.failure.json').read_text()),
                            {'schema': 'mcpcli-paired-publication-refusal/v1', 'status': 'refused', 'reason': reason})
                        self.assertFalse(recorded.exists())
                        source = root / 'source.json'
                        source.write_text(serialized)
                        verifier.retain_operator([source], root / 'retained')
                        retained = (root / 'retained/1-source.json').read_text()
                        self.assertNotIn(secret, retained)
                        self.assertNotIn(duplicate_secret, retained)
                        document = json.loads(retained)
                        self.assertEqual(document['message'], ordinary)
                        nested = document['evidence']
                        for _ in range(depth):
                            nested = json.loads(nested)
                        self.assertEqual(nested, {key: '[REDACTED]', 'message': ordinary})
                        self.assertEqual(source.read_text(), serialized)
                        entry = json.loads((root / 'retained/retention.json').read_text())['entries'][0]
                        self.assertTrue(entry['redacted'])
                        self.assertEqual(entry['original_sha256'], digest(source))
                        self.assertEqual(entry['retained_sha256'], digest(root / 'retained/1-source.json'))

    def test_duplicate_operator_keys_refuse_recording_and_raw_retention_redacts_every_value(self):
        verifier = module('verify-paired-publication')
        for packet in ('{"schema":"x","note":"Authorization: Bearer opaqueSecretToken123","note":"clean"}',
                       '{"nested":[{"note":"Authorization: \\u0042earer\\topaqueSecretToken123","note":"clean"}]}',
                       '{"note":"Authorization: Bearer opaqueSecretToken123","\\u006eote":"clean"}',
                       '{"note":"first","note":"clean"}'):
            with self.subTest(packet=packet), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                recorded = root / 'recorded.json'
                with self.assertRaisesRegex(ValueError, 'duplicate JSON keys'):
                    verifier.record_operator(packet, recorded)
                self.assertFalse(recorded.exists())
                stdout, stderr = io.StringIO(), io.StringIO()
                with patch.dict(os.environ, {'OPERATOR_ACCEPTANCE': packet, 'GITHUB_EVENT_PATH': ''}), \
                        patch.object(sys, 'argv', ['verify-paired-publication.py', 'record-operator', '--output', str(recorded)]), \
                        contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    self.assertEqual(verifier.main(), 1)
                self.assertEqual(stdout.getvalue(), '')
                self.assertEqual(stderr.getvalue(), 'Paired publication refused: Operator acceptance contains duplicate JSON keys.\n')
                self.assertEqual(json.loads(recorded.with_name('recorded.json.failure.json').read_text()),
                    {'schema': 'mcpcli-paired-publication-refusal/v1', 'status': 'refused',
                     'reason': 'Operator acceptance contains duplicate JSON keys.'})
                self.assertFalse(recorded.exists())
                source = root / 'source.json'
                source.write_text(packet)
                verifier.retain_operator([source], root / 'retained')
                retained = (root / 'retained/1-source.json').read_text()
                self.assertNotIn('opaqueSecretToken123', retained)
                self.assertEqual(source.read_text(), packet)
                entry = json.loads((root / 'retained/retention.json').read_text())['entries'][0]
                self.assertEqual(entry['redacted'], 'opaqueSecretToken123' in packet)
                self.assertEqual(entry['original_sha256'], digest(source))
                self.assertEqual(entry['retained_sha256'], digest(root / 'retained/1-source.json'))

    def test_decoded_nested_bearer_credentials_are_refused_and_redacted(self):
        verifier = module('verify-paired-publication')
        for separator in ('\t', '\n', '\r\n'):
            credential = 'Bearer' + separator + 'opaque-fresh-credential'
            for packet in ({'evidence': [{'nested': credential}]}, {credential: 'value'},
                           {'evidence': json.dumps({'nested': [credential]})},
                           {'evidence': json.dumps(json.dumps({credential: 'value'}))}):
                with self.subTest(separator=repr(separator), packet=packet), tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    serialized = json.dumps(packet).replace('B', '\\u0042')
                    source = root / 'source.json'
                    source.write_text(serialized)
                    with self.assertRaisesRegex(ValueError, 'credential'):
                        verifier.record_operator(serialized, root / 'recorded.json')
                    self.assertFalse((root / 'recorded.json').exists())
                    verifier.retain_operator([source], root / 'retained')
                    self.assertNotIn('opaque-fresh-credential', (root / 'retained/1-source.json').read_text())
                    self.assertTrue(json.loads((root / 'retained/retention.json').read_text())['entries'][0]['redacted'])
                    self.assertEqual(source.read_text(), serialized)

    def test_safe_operator_recording_and_retention_preserve_exact_input_bytes(self):
        verifier = module('verify-paired-publication')
        raw = b'{\r\n  "evidence": ["safe\\ttext", {"nested": "\\u0061"}],\r\n  "SigningKey": "\\u005bREDACTED]"\r\n}\r\n'
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            recorded = root / 'recorded.json'
            verifier.record_operator(raw.decode('utf-8'), recorded)
            self.assertEqual(recorded.read_bytes(), raw)
            verifier.retain_operator([recorded], root / 'retained')
            self.assertEqual((root / 'retained/1-recorded.json').read_bytes(), raw)
            self.assertFalse(json.loads((root / 'retained/retention.json').read_text())['entries'][0]['redacted'])

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
        with patch.dict(os.environ, {'REPOSITORY': 'fixture/repo'}), patch('paired_release.module', return_value=gate), \
                patch.object(request, 'registry_versions', return_value=[]):
            for response in ([marker], {'error': 'uncertain'}):
                with patch.object(gate, 'github_json', return_value=response), self.assertRaisesRegex(ValueError, 'closed'):
                    request.check_bootstrap_line()
            with patch.object(gate, 'github_json', return_value=[]): request.check_bootstrap_line()
        with patch.dict(os.environ, {'REPOSITORY': 'fixture/repo'}), patch.object(publisher, 'module', return_value=gate), \
                patch.object(gate, 'github_json', side_effect=[[marker], [old]]), patch.object(subprocess, 'run') as command:
            with self.assertRaisesRegex(ValueError, 'already started'): publisher.reserve_version(VERSION, SHA)
            command.assert_not_called()

    def test_bootstrap_recovery_cannot_target_unlisted_paired_or_later_versions(self):
        request = module('release-request')
        for version in (VERSION, '2.0.1', '2.0.2', '3.0.0'):
            with self.subTest(version=version), patch.object(subprocess, 'run') as git, \
                    patch.object(request, 'urlopen') as registry:
                with self.assertRaisesRegex(ValueError, 'not in the fixed historical allowlist'):
                    request.historical_sha(version)
                git.assert_not_called()
                registry.assert_not_called()

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

    def test_topology_discovery_required_step_matches_the_current_workflow(self):
        gate = module('verify-release-source')
        workflow = (Path(__file__).resolve().parents[2] / '.github/workflows/ci.yml').read_text()
        block = workflow.split('  topology-vector-discovery:\n', 1)[1]
        block = re.split(r'(?m)^  [\w-]+:', block, maxsplit=1)[0]
        names = re.findall(r'(?m)^      - name: (.+)$', block)
        required = gate.STAGING_JOBS['topology-vector-discovery']
        self.assertEqual(1, len(required))
        self.assertTrue(set(required).issubset(names), (required, names))

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
