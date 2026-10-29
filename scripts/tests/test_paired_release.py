"""Exercise staged-pair acceptance and negative controls without publishing or hosted claims."""

import contextlib
import copy
import io
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from xml.etree import ElementTree

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
from paired_release import PAIR, digest, module, packages, write_new

SHA = 'a' * 40
VERSION = '1.2.3'
CHECKS = ['version', 'offline-discovery', 'config', 'json-lf', 'errors', 'mcp-protocol', 'output-file', 'table']


def jobs(required):
    return [{'name': name, 'status': 'completed', 'conclusion': 'success',
             'steps': [{'name': step, 'status': 'completed', 'conclusion': 'success'} for step in steps]}
            for name, steps in required.items()]


class PairedReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.staging = self.root / 'packages'
        self.staging.mkdir()
        for name in PAIR:
            (self.staging / f'{name}.{VERSION}.nupkg').write_bytes(name.encode())
        self.prepared_path = self.root / 'prepared.json'
        self.gate = module('verify-release-source')
        self.runner = module('run-paired-platform-tests')
        self.comparator = module('compare-paired-evidence')
        self.evidence = self.root / 'evidence'
        self.evidence.mkdir()
        workflow_gates = {}
        for workflow, required in [('ci.yml', self.gate.STAGING_JOBS), ('commitlint.yml', self.gate.STAGING_COMMITLINT_JOBS)]:
            workflow_gates[workflow] = {'source_sha': SHA, 'status': 'completed', 'conclusion': 'success', 'jobs': jobs(required)}
        self.source_gate = {'schema': 'mcpcli-paired-source/v1', 'source_sha': SHA, 'source_clean': True,
                            'current_main': SHA, 'gates': workflow_gates,
                            'fr22': {'required_revision': module('verify-paired-prerequisites').REQUIRED,
                                     'source_sha': SHA, 'source_clean': True, 'baseline_revision': 'c' * 40, 'upstream_main': 'd' * 40,
                                     'synchronization': {name: 'b' * 64 for name in ('AGENTS.md', 'CLAUDE.md', '.github/copilot-instructions.md')}}}
        self.package_hashes = packages(self.staging, VERSION)
        self.prepared = {'schema': 'mcpcli-paired-preparation/v1', 'source_sha': SHA, 'source_clean': True,
                         'eligibility': 'current-main', 'version': VERSION, 'packages': self.package_hashes}
        self.save_gates()
        self.consumers = []
        for system in ('Linux', 'Windows', 'Darwin'):
            directory = self.root / system
            smoke = directory / 'smoke'
            captures = smoke / 'discovery'
            captures.mkdir(parents=True)
            documents = {'modules.json': {'modules': [{'name': 'sample'}]},
                         'operations-sample.json': {'operations': [{'name': 'sample.read'}]},
                         'describe-sample.read.json': {'name': 'sample.read'},
                         'mcp-tools.json': {'jsonrpc': '2.0', 'id': 2, 'result': {}},
                         'mcp-modules.json': {'jsonrpc': '2.0', 'id': 3, 'result': {}},
                         'mcp-operations-sample.json': {'jsonrpc': '2.0', 'id': 4, 'result': {}},
                         'mcp-describe-sample.read.json': {'jsonrpc': '2.0', 'id': 5, 'result': {}}}
            for name, value in documents.items():
                write_new(captures / name, value)
            write_new(smoke / 'smoke.json', {'schema': 'mcpcli-paired-smoke/v1', 'status': 'passed', 'os': system,
                      'source_sha': SHA, 'version': VERSION, 'packages': self.package_hashes,
                      'preparation_sha256': digest(self.prepared_path), 'checks': CHECKS,
                      'discovery': {path.name: digest(path) for path in captures.iterdir()}})
            tests = directory / 'tests'
            tests.mkdir()
            suites = ['Core', 'Cli'] if system == 'Windows' else ['Cli'] if system == 'Darwin' else []
            for suite in suites:
                xml = ElementTree.Element('assemblies')
                collection = ElementTree.SubElement(xml, 'assembly')
                names = [name for name in self.runner.WINDOWS_REQUIRED if f'.{suite}.Tests.' in name]
                for name in names or ['sample.test']:
                    ElementTree.SubElement(collection, 'test', name=name, result='Pass')
                ElementTree.ElementTree(xml).write(tests / f'Hexalith.McpCli.{suite}.Tests.xml')
            write_new(tests / 'tests.json', {'schema': 'mcpcli-paired-platform-tests/v1', 'status': 'passed', 'os': system,
                      'source_sha': SHA, 'version': VERSION, 'packages': self.package_hashes, 'suites': suites,
                      'xml': {path.name: digest(path) for path in tests.glob('*.xml')}})
            self.consumers.append(directory)

    def save_gates(self):
        for name in ('source-before', 'source-after'):
            (self.evidence / (name + '.json')).write_text(json.dumps(self.source_gate))
        (self.evidence / 'validation.json').write_text(json.dumps({'phase': 'paired', 'source_sha': SHA, 'version': VERSION, 'packages': self.package_hashes}))
        (self.evidence / 'consumer-build.log').write_text('MissingDescriptionQuery.cs(2,1): warning MCPCLI001: fixture\n    1 Warning(s)\n')
        (self.evidence / 'consumer.command.json').write_text(json.dumps({'argv': ['bash', 'scripts/smoke-bootstrap-consumer.sh', VERSION, str(self.staging), '/private/consumer'], 'exit_code': 0}))
        for channel in ('stdout', 'stderr'):
            (self.evidence / ('consumer.' + channel + '.txt')).write_text('')
        (self.evidence / 'consumer.json').write_text(json.dumps({'schema': 'mcpcli-paired-consumer/v1', 'status': 'passed',
            'source_sha': SHA, 'version': VERSION, 'packages': self.package_hashes,
            'compiler_sha256': digest(self.evidence / 'consumer-build.log'),
            'command_sha256': digest(self.evidence / 'consumer.command.json')}))
        self.prepared['evidence'] = {path.name: digest(path) for path in self.evidence.iterdir()}
        self.save_prepared()

    def save_prepared(self):
        self.prepared_path.write_text(json.dumps(self.prepared))
        for directory in getattr(self, 'consumers', []):
            self.change_json(directory / 'smoke/smoke.json', lambda d: d.update(preparation_sha256=digest(self.prepared_path)))

    def compare(self, consumers=None):
        return self.comparator.compare(self.staging, self.prepared_path, consumers or self.consumers, self.root / 'accepted.json')

    def change_json(self, path, change):
        document = json.loads(path.read_text())
        change(document)
        path.write_text(json.dumps(document))

    def test_complete_synthetic_matrix_accepts_only_staging(self):
        self.compare()
        result = json.loads((self.root / 'accepted.json').read_text())
        self.assertEqual(result['status'], 'accepted-staging-only')
        self.assertIn('refused', result['publication'])
        self.assertEqual(result['packages'], self.package_hashes)

    def test_platform_failure_matrix_never_writes_acceptance(self):
        mutations = [lambda d: d.update(status='failed'), lambda d: d.update(source_sha='c' * 40),
                     lambda d: d.update(version='9.0.0'), lambda d: d.update(packages={}),
                     lambda d: d.update(preparation_sha256='d' * 64), lambda d: d.update(checks=['version']),
                     lambda d: d.update(os='Linux')]
        path = self.root / 'Windows/smoke/smoke.json'
        original = path.read_bytes()
        for change in mutations:
            with self.subTest(change=change):
                path.write_bytes(original)
                self.change_json(path, change)
                with self.assertRaises(ValueError):
                    self.compare()
                self.assertFalse((self.root / 'accepted.json').exists())

    def test_missing_platform_or_missing_receipt_refuses(self):
        with self.assertRaises(ValueError):
            self.compare(self.consumers[:2])
        (self.root / 'Windows/smoke/smoke.json').unlink()
        with self.assertRaises(FileNotFoundError):
            self.compare()

    def test_tampered_packages_extra_packages_and_prior_receipts_refuse(self):
        pair = next(self.staging.iterdir())
        pair.write_bytes(b'tampered')
        with self.assertRaises(ValueError):
            self.compare()
        (self.staging / 'extra.nupkg').write_bytes(b'extra')
        with self.assertRaises(ValueError):
            packages(self.staging, VERSION)
        self.assertFalse((self.root / 'accepted.json').exists())

    def test_raw_capture_tampering_and_cross_os_byte_drift_refuse(self):
        path = self.root / 'Darwin/smoke/discovery/modules.json'
        path.write_bytes(path.read_bytes().replace(b'\n', b'\r\n'))
        with self.assertRaises(ValueError):
            self.compare()
        receipt = self.root / 'Darwin/smoke/smoke.json'
        self.change_json(receipt, lambda d: d['discovery'].update({'modules.json': digest(path)}))
        with self.assertRaises(ValueError):
            self.compare()

    def test_all_windows_required_tests_must_execute_not_skip(self):
        for name in self.runner.WINDOWS_REQUIRED:
            with self.subTest(name=name):
                suite = 'Core' if '.Core.Tests.' in name else 'Cli'
                path = self.root / f'Windows/tests/Hexalith.McpCli.{suite}.Tests.xml'
                tree = ElementTree.parse(path)
                item = next(item for item in tree.findall('.//test') if item.get('name') == name)
                item.set('result', 'Skip')
                tree.write(path)
                self.change_json(self.root / 'Windows/tests/tests.json', lambda d: d['xml'].update({path.name: digest(path)}))
                with self.assertRaises(ValueError):
                    self.compare()
                item.set('result', 'Pass')
                tree.write(path)
                self.change_json(self.root / 'Windows/tests/tests.json', lambda d: d['xml'].update({path.name: digest(path)}))

    def test_missing_or_wrong_platform_suite_refuses(self):
        self.change_json(self.root / 'Windows/tests/tests.json', lambda d: d.update(suites=['Cli']))
        with self.assertRaises(ValueError):
            self.compare()

    def test_local_only_and_dirty_source_refuse(self):
        for key, value in [('source_clean', False), ('eligibility', 'local-only')]:
            with self.subTest(key=key):
                original = self.prepared_path.read_bytes()
                self.change_json(self.prepared_path, lambda d: d.update({key: value}))
                with self.assertRaises(ValueError):
                    self.compare()
                self.prepared_path.write_bytes(original)

    def test_missing_fr22_and_skipped_source_steps_refuse(self):
        for change in [lambda d: d.update(fr22={}),
                       lambda d: d['gates']['ci.yml']['jobs'][0]['steps'][0].update(conclusion='skipped'),
                       lambda d: d['gates']['ci.yml'].update(source_sha='d' * 40)]:
            with self.subTest(change=change):
                original = copy.deepcopy(self.source_gate)
                change(self.source_gate)
                self.save_gates()
                with self.assertRaises(ValueError):
                    self.compare()
                self.source_gate = original

    def test_latest_jobs_require_execution_and_complete_pagination(self):
        all_jobs = jobs(self.gate.STAGING_JOBS)
        with patch.object(self.gate, 'github_json', side_effect=[{'jobs': all_jobs[:2], 'total_count': len(all_jobs)},
                                                               {'jobs': all_jobs[2:], 'total_count': len(all_jobs)}]):
            self.gate.verify_jobs('fixture/repo', {'id': 1, 'run_attempt': 2}, self.gate.STAGING_JOBS)
        all_jobs[0]['conclusion'] = 'skipped'
        with self.assertRaises(ValueError):
            self.gate.validate_jobs(all_jobs, self.gate.STAGING_JOBS)
        with self.assertRaises(ValueError):
            self.gate.validate_jobs([], self.gate.STAGING_JOBS)

    def test_partial_reruns_select_newest_required_jobs_with_pagination(self):
        required = {'one': ['step'], 'two': ['step'], 'three': ['step']}
        all_jobs = jobs(required)
        pages = [{'jobs': [all_jobs[0]], 'total_count': 1},
                 {'jobs': [all_jobs[1]], 'total_count': 2}, {'jobs': [all_jobs[2]], 'total_count': 2}]
        with patch.object(self.gate, 'github_json', side_effect=pages) as api:
            selected = self.gate.verify_jobs('fixture/repo', {'id': 123, 'run_attempt': 2}, required)
        self.assertEqual(selected, all_jobs)
        self.assertEqual([call.args[0] for call in api.call_args_list], [
            'repos/fixture/repo/actions/runs/123/attempts/2/jobs',
            'repos/fixture/repo/actions/runs/123/attempts/1/jobs',
            'repos/fixture/repo/actions/runs/123/attempts/1/jobs'])
        self.assertEqual(api.call_args_list[-1].args[-1], 'page=2')
        # Older failures for a job successfully rerun do not override the newest occurrence.
        old = copy.deepcopy(all_jobs)
        old[0]['conclusion'] = 'failure'
        with patch.object(self.gate, 'github_json', side_effect=[{'jobs': [all_jobs[0]], 'total_count': 1},
                                                               {'jobs': old, 'total_count': 3}]):
            self.assertEqual(self.gate.verify_jobs('fixture/repo', {'id': 123, 'run_attempt': 2}, required), all_jobs)

    def test_newer_bad_or_duplicate_job_never_falls_back(self):
        required = {'one': ['step'], 'two': ['step']}
        valid = jobs(required)
        for mode in ('failed', 'skipped', 'step-skipped', 'duplicate'):
            newer = copy.deepcopy(valid[:1])
            if mode == 'duplicate': newer += copy.deepcopy(newer)
            elif mode == 'step-skipped': newer[0]['steps'][0]['conclusion'] = 'skipped'
            else: newer[0]['conclusion'] = 'failure' if mode == 'failed' else 'skipped'
            with self.subTest(mode=mode), patch.object(self.gate, 'github_json', side_effect=[
                    {'jobs': newer, 'total_count': len(newer)}, {'jobs': valid, 'total_count': len(valid)}]) as api:
                with self.assertRaises(ValueError):
                    self.gate.verify_jobs('fixture/repo', {'id': 123, 'run_attempt': 2}, required)
                self.assertEqual(api.call_count, 1)
        with patch.object(self.gate, 'github_json', side_effect=[{'jobs': valid[:1], 'total_count': 2},
                                                               {'jobs': [], 'total_count': 2}]):
            with self.assertRaisesRegex(ValueError, 'Incomplete'):
                self.gate.verify_jobs('fixture/repo', {'id': 123, 'run_attempt': 2}, required)

    def test_missing_or_malformed_fr22_revision_fields_refuse(self):
        for key in ('baseline_revision', 'upstream_main'):
            for value in (None, '', 123, [], 'abc123', 'A' * 40, 'a' * 39, 'a' * 40 + '\n'):
                original = copy.deepcopy(self.source_gate)
                if value is None: self.source_gate['fr22'].pop(key)
                else: self.source_gate['fr22'][key] = value
                self.save_gates()
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    self.compare()
                self.assertFalse((self.root / 'accepted.json').exists())
                self.source_gate = original

    def test_acceptance_requires_successful_staged_compiler_analyzer_evidence(self):
        for mode in ('missing', 'failed', 'wrong-source', 'wrong-packages', 'no-analyzer', 'load-failure'):
            self.save_gates()
            if mode == 'missing': (self.evidence / 'consumer.json').unlink()
            elif mode == 'failed': self.change_json(self.evidence / 'consumer.command.json', lambda d: d.update(exit_code=1))
            elif mode == 'wrong-source': self.change_json(self.evidence / 'consumer.json', lambda d: d.update(source_sha='e' * 40))
            elif mode == 'wrong-packages': self.change_json(self.evidence / 'consumer.json', lambda d: d.update(packages={}))
            else: (self.evidence / 'consumer-build.log').write_text('0 Warning(s)' if mode == 'no-analyzer' else 'CS8032')
            self.prepared['evidence'] = {path.name: digest(path) for path in self.evidence.iterdir()}
            # Bind mutations to their updated individual hashes so acceptance checks the actual assertion too.
            if mode != 'missing':
                self.change_json(self.evidence / 'consumer.json', lambda d: d.update(
                    compiler_sha256=digest(self.evidence / 'consumer-build.log'),
                    command_sha256=digest(self.evidence / 'consumer.command.json')))
                self.prepared['evidence']['consumer.json'] = digest(self.evidence / 'consumer.json')
            self.save_prepared()
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                self.compare()
            self.assertFalse((self.root / 'accepted.json').exists())

    def test_complete_mcp_capture_set_is_required(self):
        path = self.root / 'Windows/smoke/smoke.json'
        original = path.read_bytes()
        for name in ('mcp-operations-sample.json', 'mcp-describe-sample.read.json'):
            self.change_json(path, lambda d: d['discovery'].pop(name))
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'Raw discovery captures are incomplete'):
                self.compare()
            self.assertFalse((self.root / 'accepted.json').exists())
            path.write_bytes(original)

    def test_staging_workflow_guards_actual_dispatch_ref_before_selection(self):
        workflow = (SCRIPTS.parent / '.github/workflows/release.yml').read_text().split('  stage-pair:', 1)[1].split('  smoke-pair:', 1)[0]
        guard = workflow.split('      - name: Require staging dispatch from main\n', 1)[1].split('      - ', 1)[0]
        command = guard.split('        run: ', 1)[1].strip()
        self.assertLess(workflow.index('Require staging dispatch from main'), workflow.index('Select a version'))
        for ref in ('refs/heads/main', 'refs/heads/topic', 'refs/tags/v1.0.0', ''):
            result = subprocess.run(['bash', '-e', '-c', command], env={**os.environ, 'GITHUB_REF': ref}, capture_output=True)
            self.assertEqual(result.returncode == 0, ref == 'refs/heads/main')

    def test_source_gate_rejects_stale_dirty_or_wrong_head(self):
        for state in ('stale', 'dirty', 'wrong-head'):
            def fake_git(argv, **kwargs):
                command = argv[1:]
                result = SHA
                if command[0] == 'branch': result = 'main'
                elif command[0] == 'status': result = ' M source.cs' if state == 'dirty' else ''
                elif state == 'wrong-head': result = 'b' * 40
                return subprocess.CompletedProcess(argv, 0, stdout=result, stderr='')
            with self.subTest(state=state), patch.object(self.gate.subprocess, 'run', side_effect=fake_git), \
                    patch.object(self.gate, 'github_json', return_value={'object': {'sha': 'b' * 40}}), \
                    patch.dict('os.environ', {'REPOSITORY': 'fixture/repo'}), \
                    patch.object(sys, 'argv', ['verify', '--staging', '--output', str(self.root / 'gate.json'), SHA, 'refs/heads/main', 'paired']), \
                    contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(self.gate.main(), 1)
                self.assertFalse((self.root / 'gate.json').exists())

    def test_no_release_creates_no_staged_pair_and_existing_output_refuses(self):
        prepare = module('prepare-paired-release')
        selection = self.root / 'selection.json'
        write_new(selection, {'schema': 'mcpcli-version-selection/v1', 'source_sha': SHA, 'release': False, 'version': None})
        output = self.root / 'no-release'
        with patch.object(prepare, 'source', return_value={'source_sha': SHA, 'source_clean': True}):
            prepare.prepare(selection, output)
            self.assertTrue((output / 'no-release.json').is_file())
            self.assertFalse((output / 'packages').exists())
            with self.assertRaises(ValueError):
                prepare.prepare(selection, output)

    def test_native_or_malformed_payload_refuses(self):
        validator = module('validate-release-packages')
        for payload in (b'', b'MZnative', bytes(512)):
            with self.assertRaises(ValueError):
                validator.validate_managed(payload)

    def test_paired_publication_and_recovery_remain_refused(self):
        for version in (VERSION, '1.0.0'):
            with self.assertRaisesRegex(ValueError, 'Paired release is deferred'):
                module('release-request').validate_request(version, 'paired')

    def test_xml_errors_or_no_executed_tests_refuse(self):
        path = self.root / 'errors.xml'
        for document in ['<assemblies><assembly errors="1"><test name="sample" result="Pass" /></assembly></assemblies>',
                         '<assemblies><assembly><error /></assembly></assemblies>',
                         '<assemblies><assembly /></assemblies>',
                         '<assemblies><assembly><test name="sample" result="Skip" /></assembly></assemblies>']:
            path.write_text(document)
            with self.assertRaises(ValueError):
                self.runner.inspect_xml(path)

    def test_preparation_evidence_tampering_and_missing_discovery_refuse(self):
        path = self.evidence / 'source-before.json'
        path.write_text('{}')
        with self.assertRaises(ValueError):
            self.compare()
        self.save_gates()
        self.change_json(self.root / 'Windows/smoke/smoke.json', lambda d: d['discovery'].pop('operations-sample.json'))
        with self.assertRaises(ValueError):
            self.compare()

    def test_duplicate_platform_and_missing_package_refuse(self):
        with self.assertRaises(ValueError):
            self.compare([self.consumers[0], self.consumers[0], self.consumers[2]])
        next(self.staging.iterdir()).unlink()
        with self.assertRaises(ValueError):
            self.compare()

    def test_symlink_staging_and_dangling_output_refuse(self):
        alias = self.root / 'staging-alias'
        alias.symlink_to(self.staging, target_is_directory=True)
        with self.assertRaises(ValueError):
            packages(alias, VERSION)
        prepare = module('prepare-paired-release')
        selection = self.root / 'no-release-selection.json'
        write_new(selection, {'schema': 'mcpcli-version-selection/v1', 'source_sha': SHA, 'release': False, 'version': None})
        output = self.root / 'dangling'
        output.symlink_to(self.root / 'absent', target_is_directory=True)
        with patch.object(prepare, 'source', return_value={'source_sha': SHA, 'source_clean': True}):
            with self.assertRaises(ValueError):
                prepare.prepare(selection, output)
        self.assertTrue(output.is_symlink())
        self.assertFalse((self.root / 'absent').exists())

    def fake_preparation(self, failure=None):
        prepare = module('prepare-paired-release')
        selection = self.root / ('selection-' + str(failure) + '.json')
        write_new(selection, {'schema': 'mcpcli-version-selection/v1', 'source_sha': SHA, 'release': True, 'version': VERSION})
        output = self.root / ('prepare-' + str(failure))
        before = {'source_sha': SHA, 'source_clean': True}
        after = {**before, 'source_sha': 'f' * 40} if failure == 'source' else before
        def execute(argv, **kwargs):
            if argv[0] == 'dotnet' and argv[1] == 'pack':
                staging = Path(argv[argv.index('--output') + 1])
                identity = Path(argv[2]).stem
                (staging / f'{identity}.{VERSION}.nupkg').write_bytes(identity.encode())
            elif argv[0] == sys.executable and argv[1].endswith('validate-release-packages.py'):
                validation = Path(argv[argv.index('--output') + 1])
                write_new(validation, {'packages': packages(output / 'packages', VERSION)})
                if failure == 'tamper':
                    next((output / 'packages').iterdir()).write_bytes(b'tamper after validation')
            elif argv[:2] == ['bash', 'scripts/smoke-bootstrap-consumer.sh']:
                consumer = Path(argv[-1])
                self.assertFalse(consumer.exists())
                self.assertEqual(Path(argv[-2]), output / 'packages')
                self.assertEqual(argv[2], VERSION)
                self.assertNotEqual(kwargs['env']['DOTNET_CLI_HOME'], os.environ.get('DOTNET_CLI_HOME'))
                consumer.mkdir()
                (consumer / 'build.log').write_text('MissingDescriptionQuery.cs(2,1): warning MCPCLI001: fixture\n    1 Warning(s)\n')
                if failure == 'consumer':
                    return subprocess.CompletedProcess(argv, 1, stdout=b'compiler failure', stderr=b'')
            elif argv[0] == sys.executable and argv[1].endswith('verify-release-source.py'):
                write_new(Path(argv[argv.index('--output') + 1]), self.source_gate)
            code = 1 if len(argv) > 1 and argv[1] == failure else 0
            return subprocess.CompletedProcess(argv, code, stdout=b'fixture', stderr=b'')
        with patch.object(prepare, 'source', side_effect=[before, after]), \
                patch.object(prepare.subprocess, 'run', side_effect=execute), contextlib.redirect_stdout(io.StringIO()):
            if failure:
                with self.assertRaises((ValueError, subprocess.CalledProcessError)):
                    prepare.prepare(selection, output)
                self.assertFalse((output / 'prepared.json').exists())
                if failure == 'consumer':
                    self.assertTrue((output / 'evidence/consumer-build.log').is_file())
                    self.assertEqual(json.loads((output / 'evidence/consumer.command.json').read_text())['exit_code'], 1)
                    self.assertFalse((output / 'evidence/consumer.json').exists())
            else:
                prepare.prepare(selection, output)
                receipt = json.loads((output / 'prepared.json').read_text())
                self.assertEqual(receipt['eligibility'], 'current-main')
                self.assertEqual(receipt['packages'], packages(output / 'packages', VERSION))
                self.assertTrue((output / 'evidence/source-before.json').is_file())
                self.assertTrue((output / 'evidence/source-after.json').is_file())
                self.assertEqual(json.loads((output / 'evidence/consumer.json').read_text())['status'], 'passed')
                self.assertIn('consumer-build.log', receipt['evidence'])

    def test_preparation_binds_one_fresh_pair_and_both_source_checks(self):
        self.fake_preparation()

    def test_preparation_failures_never_record_success(self):
        for failure in ('restore', 'build', 'source', 'tamper', 'consumer'):
            with self.subTest(failure=failure):
                self.fake_preparation(failure)

    def test_fr22_requires_checkout_containment_authoritative_main_and_sync(self):
        prerequisite = module('verify-paired-prerequisites')
        success = subprocess.CompletedProcess([], 0, stdout=b'', stderr=b'')
        for state in ('wrong-checkout', 'missing-ancestor', 'unmerged-upstream', 'sync-drift'):
            def git_result(*args):
                if args[0] == 'config': return 'submodule.baseline.path references/Hexalith.AI.Tools'
                if args[0] == 'ls-tree': return '160000 commit ' + SHA + '\treferences/Hexalith.AI.Tools'
                return 'b' * 40 if state == 'wrong-checkout' and args[0] == '-C' else SHA
            def api_result(endpoint):
                return {'object': {'sha': SHA}} if '/git/ref/' in endpoint else {'status': 'behind' if state == 'unmerged-upstream' else 'identical'}
            with self.subTest(state=state), patch.object(prerequisite, 'git', side_effect=git_result), \
                    patch.object(prerequisite, 'run', side_effect=subprocess.CalledProcessError(1, ['git']) if state == 'missing-ancestor' else None, return_value=success), \
                    patch.object(prerequisite, 'digest', side_effect=['a', 'b', 'c'] if state == 'sync-drift' else None, return_value='d'), \
                    patch.object(prerequisite, 'module', return_value=type('Gate', (), {'github_json': staticmethod(api_result)})()):
                with self.assertRaises((ValueError, subprocess.CalledProcessError)):
                    prerequisite.verify()

    def test_stale_version_selection_refuses_before_building(self):
        prepare = module('prepare-paired-release')
        selection = self.root / 'stale-selection.json'
        write_new(selection, {'schema': 'mcpcli-version-selection/v1', 'source_sha': 'b' * 40, 'release': True, 'version': VERSION})
        with patch.object(prepare, 'source', return_value={'source_sha': SHA, 'source_clean': True}), \
                patch.object(prepare.subprocess, 'run') as command:
            with self.assertRaises(ValueError):
                prepare.prepare(selection, self.root / 'stale-output')
            command.assert_not_called()

    def test_baseline_requires_a_committed_root_declaration_and_gitlink(self):
        prerequisite = module('verify-paired-prerequisites')
        declaration = 'submodule.baseline.path references/Hexalith.AI.Tools'
        entry = '160000 commit ' + SHA + '\treferences/Hexalith.AI.Tools'
        invalid = [('', entry), (declaration + '\n' + declaration, entry),
                   (declaration, '100644 blob ' + SHA + '\treferences/Hexalith.AI.Tools'),
                   (declaration, '040000 tree ' + SHA + '\treferences/Hexalith.AI.Tools'),
                   (declaration, '160000 commit ' + SHA + '\treferences/Other'),
                   (declaration, '')]
        for declared, tree in invalid:
            with self.subTest(declaration=declared, tree=tree), patch.object(prerequisite, 'git', side_effect=[declared, tree]):
                with self.assertRaises(ValueError):
                    prerequisite.committed_baseline()
        with patch.object(prerequisite, 'git', side_effect=[declaration, entry]) as git:
            self.assertEqual(prerequisite.committed_baseline(), SHA)
            self.assertEqual(git.call_args_list[0].args[:3], ('config', '--blob', 'HEAD:.gitmodules'))
            self.assertEqual(git.call_args_list[1].args[:2], ('ls-tree', 'HEAD'))

    def test_platform_runner_collects_both_suites_before_acceptance(self):
        for mode in ('core-exit-failure', 'core-xml-failure', 'core-launch-failure', 'required-skip', 'passed'):
            output = self.root / ('runner-' + mode)
            calls = []
            def execute(argv, **kwargs):
                if '-xml' not in argv:
                    return subprocess.CompletedProcess(argv, 0, stdout=b'build/restore', stderr=b'')
                suite = 'Core' if '.Core.Tests/' in argv[1] else 'Cli'
                calls.append(suite)
                if suite == 'Core' and mode == 'core-launch-failure':
                    raise OSError('fixture Core process launch failure')
                xml = Path(argv[argv.index('-xml') + 1])
                if suite == 'Core' and mode == 'core-xml-failure':
                    xml.write_text('<malformed')
                else:
                    root = ElementTree.Element('assemblies')
                    assembly = ElementTree.SubElement(root, 'assembly')
                    names = [name for name in self.runner.WINDOWS_REQUIRED if f'.{suite}.Tests.' in name]
                    for index, name in enumerate(names):
                        ElementTree.SubElement(assembly, 'test', name=name,
                            result='Skip' if mode == 'required-skip' and suite == 'Core' and index == 0 else 'Pass')
                    if mode == 'core-exit-failure' and suite == 'Core':
                        ElementTree.SubElement(assembly, 'test', name='fixture.CoreFailure', result='Fail')
                    ElementTree.ElementTree(root).write(xml)
                code = 1 if suite == 'Core' and mode == 'core-exit-failure' else 0
                return subprocess.CompletedProcess(argv, code, stdout=(suite + ' diagnostic').encode(), stderr=b'fixture stderr')
            with self.subTest(mode=mode), patch.object(self.runner, 'git', return_value=SHA), \
                    patch.object(self.runner.platform, 'system', return_value='Windows'), \
                    patch.object(self.runner.subprocess, 'run', side_effect=execute):
                if mode == 'passed':
                    self.runner.run_tests(self.prepared_path, output)
                    self.assertEqual(json.loads((output / 'tests.json').read_text())['status'], 'passed')
                else:
                    with self.assertRaisesRegex(ValueError, 'after collecting all required suites'):
                        self.runner.run_tests(self.prepared_path, output)
                    self.assertFalse((output / 'tests.json').exists())
                self.assertEqual(calls, ['Core', 'Cli'])
                report = json.loads((output / 'suite-outcomes.json').read_text())
                self.assertEqual([item['suite'] for item in report['suites']], ['Core', 'Cli'])
                self.assertEqual(report['status'], 'passed' if mode == 'passed' else 'failed')
                for suite in ('Core', 'Cli'):
                    name = 'Hexalith.McpCli.' + suite + '.Tests'
                    self.assertTrue((output / (name + '.command.json')).is_file())
                    self.assertTrue((output / (name + '.stdout.txt')).is_file())
                    self.assertTrue((output / (name + '.stderr.txt')).is_file())
                self.assertTrue((output / 'Hexalith.McpCli.Cli.Tests.xml').is_file())

    def test_new_evidence_never_overwrites_a_prior_result(self):
        path = self.root / 'already.json'
        write_new(path, {'retained': True})
        with self.assertRaises(FileExistsError):
            write_new(path, {'retained': False})
        self.assertEqual(json.loads(path.read_text()), {'retained': True})


if __name__ == '__main__':
    unittest.main()
