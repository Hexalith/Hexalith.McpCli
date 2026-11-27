"""Exercise the controller's real child CLI parsers, package custody and OS/discovery contracts."""
import contextlib
import importlib
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
from xml.etree import ElementTree

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import product_ci
import product_packages
import test_product_packages as fixtures

SHA = fixtures.SHA


class ProductControllerTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.ProductPackageTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.product = self.root / 'mcpcli-product'
        self.staged = self.product / 'staged'
        path = self.fixture.staged(); self.fixture.paired_tool()
        shutil.copytree(path.parent, self.staged / 'packages')
        self.prepared = self.staged / 'prepared.json'
        product_packages.write_new(self.prepared, {'schema': 'mcpcli-product-packages/v1', 'source_sha': SHA,
            'version': '1.0.0', 'packages': product_packages.packages(self.staged / 'packages', '1.0.0')})
        for setting in (patch.object(product_ci, 'ROOT', self.fixture.root),
                        patch.object(product_ci, 'staging_root', return_value=self.product),
                        patch.object(product_ci, 'source_sha', return_value=SHA),
                        patch.object(product_ci, 'source_changes', return_value='')):
            setting.start(); self.addCleanup(setting.stop)
        self.fixture.executable('git', '#!/usr/bin/env python3\nprint(' + repr(SHA) + ')\n')

    def captures(self, directory):
        directory.mkdir(parents=True, exist_ok=True)
        for name, data in {'modules.json': b'{"modules":[]}\n', 'operations-sample.json': b'{"operations":[]}\n',
                           'mcp-tools-list.json': b'{"tools":[]}\n'}.items():
            (directory / name).write_bytes(data)
        return directory

    def test_staging_uses_one_no_build_pair_and_real_payload_validator(self):
        shutil.rmtree(self.staged)
        commands = []
        def execute(command, **kwargs):
            commands.append(list(map(str, command)))
            if command[:2] == ['dotnet', 'msbuild']:
                return subprocess.CompletedProcess(command, 0, stdout='1.0.0\n', stderr='')
            if command[0] == 'dotnet' and command[1].endswith('.dll'):
                return subprocess.CompletedProcess(command, 0, stdout='1.0.0+' + SHA + '\n', stderr='')
            if command[:2] == ['dotnet', 'pack']:
                package_id = Path(command[2]).stem
                shutil.copyfile(self.fixture.root / 'nupkgs/bootstrap' / (package_id + '.1.0.0.nupkg'),
                                Path(command[command.index('--output') + 1]) / (package_id + '.1.0.0.nupkg'))
                return subprocess.CompletedProcess(command, 0)
            result = subprocess.run(list(map(str, command)), cwd=self.fixture.root, env=self.fixture.env, capture_output=True, text=True, timeout=15)
            self.assertEqual(0, result.returncode, result.stderr)
            return result
        with patch.object(product_ci, 'execute', side_effect=execute): product_ci.stage_packages()
        packed = [command for command in commands if command[:2] == ['dotnet', 'pack']]
        self.assertEqual(2, len(packed))
        self.assertTrue(all('--no-build' in command and '--no-restore' in command for command in packed))
        receipt = product_packages.check_prepared(self.staged / 'packages', self.prepared)
        self.assertEqual(SHA, receipt['source_sha'])
        self.assertEqual('1.0.0+' + SHA, receipt['tool_version'])
        self.fixture.assert_no_push()

    def test_source_or_package_drift_refuses_before_children(self):
        for defect in ('head', 'tracked', 'untracked', 'package'):
            with self.subTest(defect=defect):
                original = (self.staged / 'packages' / fixtures.PACKAGE).read_bytes()
                if defect == 'package': (self.staged / 'packages' / fixtures.PACKAGE).write_bytes(original + b'changed')
                head = 'b' * 40 if defect == 'head' else SHA
                changes = ' M source.cs' if defect == 'tracked' else '?? source.cs' if defect == 'untracked' else ''
                try:
                    with patch.object(product_ci, 'source_sha', return_value=head), \
                            patch.object(product_ci, 'source_changes', return_value=changes), \
                            patch.object(product_ci, 'execute') as execute:
                        with self.assertRaises(ValueError): product_ci.package_checks()
                        execute.assert_not_called()
                finally: (self.staged / 'packages' / fixtures.PACKAGE).write_bytes(original)

    def test_platform_identity_mismatch_refuses_before_package_or_test_effects(self):
        for actual, expected in (('Windows', 'Darwin'), ('Darwin', 'Windows'), ('Linux', 'Windows'), ('Linux', None)):
            with self.subTest(actual=actual, expected=expected), patch.object(product_ci.platform, 'system', return_value=actual), \
                    patch.object(product_ci, 'execute') as execute:
                with self.assertRaisesRegex(ValueError, 'registered actual OS'):
                    product_ci.package_checks(platform_checks=True, expected_os=expected)
                execute.assert_not_called()

    def test_product_entry_refuses_short_credentials_before_creating_evidence(self):
        runner_temp = self.root / 'uncreated-runner-temp'
        credential = 'abc1234'
        environment = {'PATH': os.environ.get('PATH', ''), 'MCPCLI_LIVE_TOKEN': credential,
                       'RUNNER_TEMP': str(runner_temp)}
        result = subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1] / 'product_ci.py'), 'linux'],
                                env=environment, capture_output=True, text=True, timeout=15)
        self.assertEqual(1, result.returncode, result.stderr)
        self.assertEqual('', result.stdout)
        self.assertIn('Structured evidence requires known environment credentials', result.stderr)
        self.assertNotIn(credential, result.stderr)
        self.assertFalse(runner_temp.exists())

    def test_windows_platform_entry_removes_only_the_hosted_postgres_default(self):
        environment = {'RUNNER_ENVIRONMENT': 'github-hosted', 'PGUSER': 'postgres', 'PGPASSWORD': 'root'}
        for actual_os, overrides, succeeds in (
                ('Windows', {}, True),
                ('Darwin', {}, False),
                ('Windows', {'RUNNER_ENVIRONMENT': 'self-hosted'}, False),
                ('Windows', {'PGUSER': 'custom'}, False),
                ('Windows', {'PGPASSWORD': 'custom'}, False),
                ('Windows', {'MCPCLI_LIVE_TOKEN': 'secret'}, False)):
            with self.subTest(actual_os=actual_os, overrides=overrides), \
                    patch.dict(os.environ, environment | overrides, clear=True), \
                    patch.object(sys, 'argv', ['product_ci.py', 'platform', '--expected-os', 'Windows']), \
                    patch.object(product_ci.platform, 'system', return_value=actual_os), \
                    patch.object(product_ci.signal, 'signal'), \
                    patch.object(product_ci, 'package_checks') as checks, \
                    contextlib.redirect_stdout(io.StringIO()) as stdout, \
                    contextlib.redirect_stderr(io.StringIO()) as stderr:
                self.assertEqual(0 if succeeds else 1, product_ci.main())
                self.assertEqual('', stdout.getvalue())
                if succeeds:
                    checks.assert_called_once_with(platform_checks=True, expected_os='Windows')
                    self.assertNotIn('PGPASSWORD', os.environ)
                    self.assertEqual('', stderr.getvalue())
                else:
                    checks.assert_not_called()
                    self.assertEqual(
                        'Structured evidence requires known environment credentials of at least eight characters.\n',
                        stderr.getvalue())

    def test_linux_discovery_keeps_preparation_immutable_and_binds_its_exact_hash(self):
        original = self.prepared.read_bytes()
        original_hash = product_packages.digest(self.prepared)
        source = self.captures(self.root / 'linux')
        product_ci.bind_linux_discovery(self.prepared, source)
        self.assertEqual(original, self.prepared.read_bytes())
        manifest = json.loads((self.staged / 'linux-discovery.json').read_text())
        self.assertEqual(original_hash, manifest['preparation_sha256'])
        with self.assertRaises(FileExistsError): product_ci.bind_linux_discovery(self.prepared, source)
        platform = self.captures(self.root / 'platform')
        self.prepared.write_bytes(original + b' ')
        with self.assertRaisesRegex(ValueError, 'preparation binding'):
            product_ci.compare_linux_discovery(self.prepared, platform)
        self.assertEqual(original + b' ', self.prepared.read_bytes())

    def test_raw_discovery_requires_complete_identical_filenames_and_bytes(self):
        source = self.captures(self.root / 'linux')
        product_ci.bind_linux_discovery(self.prepared, source)
        platform = self.captures(self.root / 'platform')
        product_ci.compare_linux_discovery(self.prepared, platform)
        for defect in ('missing', 'extra', 'raw-byte-drift', 'reference-drift'):
            with self.subTest(defect=defect):
                changed = (self.staged / 'discovery/modules.json') if defect == 'reference-drift' else platform / 'modules.json'
                original = changed.read_bytes()
                if defect == 'missing': changed.unlink()
                elif defect == 'extra': (platform / 'extra.json').write_bytes(b'{}')
                else: changed.write_bytes(original + b' ')
                try:
                    with self.assertRaises(ValueError): product_ci.compare_linux_discovery(self.prepared, platform)
                finally:
                    changed.write_bytes(original); (platform / 'extra.json').unlink(missing_ok=True)

    def test_controller_smoke_call_reaches_the_real_cli_parser_and_propagates_failure(self):
        calls = []
        def execute(command, **kwargs):
            calls.append(list(map(str, command)))
            result = subprocess.run(list(map(str, command)), cwd=self.fixture.root, env=self.fixture.env, capture_output=True, text=True, timeout=15)
            if str(command[1]).endswith('smoke-paired-tool.py'):
                self.assertEqual(1, result.returncode, result.stderr)
                self.assertIn('Paired tool smoke failed:', result.stderr)
                self.assertNotIn('unrecognized arguments', result.stderr)
                self.assertNotIn('arguments are required', result.stderr)
                raise subprocess.CalledProcessError(result.returncode, command, output=result.stdout, stderr=result.stderr)
            self.assertEqual(0, result.returncode, result.stderr)
            return result
        with patch.object(product_ci, 'execute', side_effect=execute):
            with self.assertRaises(subprocess.CalledProcessError): product_ci.package_checks()
        self.assertEqual(2, len(calls), 'The controller must stop after the failed actual smoke entry point.')
        self.fixture.assert_no_push()

    def test_controller_platform_runner_call_reaches_real_parser_and_refuses_unsupported_os(self):
        product_ci.bind_linux_discovery(self.prepared, self.captures(self.root / 'linux'))
        reached = []
        def execute(command, **kwargs):
            if str(command[1]).endswith('smoke-paired-tool.py'):
                self.captures(Path(command[command.index('--output') + 1]) / 'discovery')
            if str(command[1]).endswith('run-paired-platform-tests.py'):
                result = subprocess.run(list(map(str, command)), cwd=self.fixture.root, env=self.fixture.env, capture_output=True, text=True, timeout=15)
                reached.append(result)
                self.assertEqual(1, result.returncode)
                self.assertIn('Platform suites require actual Windows or macOS execution', result.stderr)
                self.assertNotIn('arguments are required', result.stderr)
                raise subprocess.CalledProcessError(result.returncode, command, output=result.stdout, stderr=result.stderr)
            return subprocess.CompletedProcess(command, 0, stdout='', stderr='')
        with patch.object(product_ci.platform, 'system', return_value='Windows'), patch.object(product_ci, 'execute', side_effect=execute):
            with self.assertRaises(subprocess.CalledProcessError): product_ci.package_checks(platform_checks=True, expected_os='Windows')
        self.assertEqual(1, len(reached))

    def test_linux_entry_point_requires_prepared_python_without_reinstalling_tools(self):
        for phase in ('linux', 'linux-packages', 'linux-conformance'):
            with self.subTest(phase=phase), \
                    patch.object(sys, 'argv', ['product_ci.py', phase]), \
                    patch.dict(os.environ, {'HEXALITH_CI_PYTHON': str(self.root / 'wrong-python')}), \
                    patch.object(product_ci, 'execute') as execute, contextlib.redirect_stderr(io.StringIO()) as error:
                self.assertEqual(1, product_ci.main())
                self.assertIn('shared prepared Python', error.getvalue())
                execute.assert_not_called()

    def test_split_linux_phases_dispatch_and_preserve_combined_linux_order(self):
        for phase, expected in (
                ('linux-packages', ['stage_packages', 'package_checks']),
                ('linux-conformance', ['execute:scripts/tests', 'execute:run-sample-validation.sh',
                                       'execute:run-sample-loopback.sh', 'execute:check_enrolled.py',
                                       'execute:tools/live-topology', 'execute:run-vectors.py']),
                ('linux', ['stage_packages', 'package_checks', 'execute:scripts/tests',
                           'execute:run-sample-validation.sh', 'execute:run-sample-loopback.sh',
                           'execute:check_enrolled.py', 'execute:tools/live-topology', 'execute:run-vectors.py'])):
            events = []
            def record_execute(command, **_):
                joined = ' '.join(map(str, command))
                matched = False
                for marker in ('scripts/tests', 'run-sample-validation.sh', 'run-sample-loopback.sh',
                               'check_enrolled.py', 'tools/live-topology', 'run-vectors.py'):
                    if marker in joined and not (marker == 'tools/live-topology' and 'run-vectors.py' in joined):
                        events.append('execute:' + marker)
                        matched = True
                        break
                if not matched:
                    self.fail(f'Unexpected command executed: {joined}')
                return subprocess.CompletedProcess(command, 0, stdout='', stderr='')
            with self.subTest(phase=phase), \
                    patch.object(sys, 'argv', ['product_ci.py', phase]), \
                    patch.dict(os.environ, {'HEXALITH_CI_PYTHON': sys.executable}), \
                    patch('importlib.metadata.version', return_value='4.26.0'), \
                    patch.object(product_ci.signal, 'signal'), \
                    patch.object(product_ci, 'stage_packages', side_effect=lambda: events.append('stage_packages')), \
                    patch.object(product_ci, 'package_checks', side_effect=lambda: events.append('package_checks')), \
                    patch.object(product_ci, 'execute', side_effect=record_execute), \
                    contextlib.redirect_stderr(io.StringIO()) as stderr:
                self.assertEqual(0, product_ci.main(), stderr.getvalue())
                self.assertEqual(expected, events)

    def test_linux_conformance_refuses_dirty_or_drifted_checkout(self):
        with patch.object(product_ci, 'source_changes', return_value=' M dirty.cs'), \
                patch.object(product_ci, 'execute') as execute:
            with self.assertRaisesRegex(ValueError, 'exact clean checkout SHA'):
                product_ci.linux_conformance()
            execute.assert_not_called()
        calls = 0
        def drift_during_run(command, **_):
            nonlocal calls
            calls += 1
            return subprocess.CompletedProcess(command, 0, stdout='', stderr='')
        with patch.object(product_ci, 'source_changes', side_effect=['', '?? drifted.txt']), \
                patch.object(product_ci, 'execute', side_effect=drift_during_run):
            with self.assertRaisesRegex(ValueError, 'exact clean checkout SHA'):
                product_ci.linux_conformance()
        self.assertGreater(calls, 0)


class ProductPlatformTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(); self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.runner = importlib.import_module('run-paired-platform-tests')
        self.prepared_path = self.root / 'prepared.json'
        self.prepared_path.write_text(json.dumps({'source_sha': SHA, 'version': '1.0.0', 'packages': {}}))

    def test_platform_runner_collects_both_suites_before_acceptance(self):
        for mode in ('core-exit-failure', 'core-xml-failure', 'core-launch-failure', 'required-skip', 'passed'):
            output = self.root / ('runner-' + mode); calls = []
            def execute(argv, **kwargs):
                self.assertIn('-xml', argv, 'Platform checks must reuse already built suites without restore/build.')
                self.assertEqual({'MCPCLI_HOME': str(output.resolve() / 'home')},
                                 {key: value for key, value in kwargs['env'].items() if key.startswith(('EVENTSTORE_', 'MCPCLI_'))})
                self.assertEqual('kept', kwargs['env']['PLATFORM_FIXTURE_KEPT'])
                suite = 'Core' if '.Core.Tests/' in argv[1] else 'Cli'; calls.append(suite)
                if suite == 'Core' and mode == 'core-launch-failure': raise OSError('fixture Core process launch failure')
                xml = Path(argv[argv.index('-xml') + 1])
                if suite == 'Core' and mode == 'core-xml-failure': xml.write_text('<malformed')
                else:
                    root = ElementTree.Element('assemblies'); assembly = ElementTree.SubElement(root, 'assembly')
                    names = [name for name in self.runner.WINDOWS_REQUIRED if f'.{suite}.Tests.' in name]
                    for index, name in enumerate(names):
                        ElementTree.SubElement(assembly, 'test', name=name,
                            result='Skip' if mode == 'required-skip' and suite == 'Core' and index == 0 else 'Pass')
                    if mode == 'core-exit-failure' and suite == 'Core': ElementTree.SubElement(assembly, 'test', name='fixture.CoreFailure', result='Fail')
                    ElementTree.ElementTree(root).write(xml)
                return subprocess.CompletedProcess(argv, 1 if suite == 'Core' and mode == 'core-exit-failure' else 0,
                                                   stdout=(suite + ' diagnostic').encode(), stderr=b'fixture stderr')
            with self.subTest(mode=mode), patch.object(self.runner, 'source_sha', return_value=SHA), \
                    patch.object(self.runner.platform, 'system', return_value='Windows'), \
                    patch.dict(os.environ, {'MCPCLI_FIXTURE_TOKEN': 'removed', 'EVENTSTORE_FIXTURE_URL': 'removed',
                                            'PLATFORM_FIXTURE_KEPT': 'kept'}), \
                    patch.object(self.runner.subprocess, 'run', side_effect=execute):
                if mode == 'passed':
                    self.runner.run_tests(self.prepared_path, output)
                    self.assertEqual('passed', json.loads((output / 'tests.json').read_text())['status'])
                else:
                    with self.assertRaisesRegex(ValueError, 'after collecting all required suites'): self.runner.run_tests(self.prepared_path, output)
                    self.assertFalse((output / 'tests.json').exists())
                self.assertEqual(['Core', 'Cli'], calls)
                report = json.loads((output / 'suite-outcomes.json').read_text())
                self.assertEqual(['Core', 'Cli'], [item['suite'] for item in report['suites']])
                self.assertEqual('passed' if mode == 'passed' else 'failed', report['status'])
                for suite in ('Core', 'Cli'):
                    for suffix in ('.command.json', '.stdout.txt', '.stderr.txt'):
                        self.assertTrue((output / ('Hexalith.McpCli.' + suite + '.Tests' + suffix)).is_file())

    def test_xml_errors_or_empty_execution_are_rejected(self):
        for data in ('<assemblies/>', '<assemblies><assembly errors="1"><test result="Pass"/></assembly></assemblies>',
                     '<assemblies><assembly><test result="Fail"/></assembly></assemblies>'):
            path = self.root / 'tests.xml'; path.write_text(data)
            with self.assertRaises(ValueError): self.runner.inspect_xml(path)

    def test_native_or_malformed_managed_payload_is_rejected(self):
        validator = importlib.import_module('validate-release-packages')
        for data in (b'', b'MZnative', bytes(512)):
            with self.assertRaises(ValueError): validator.validate_managed(data)

    def test_effective_properties_reject_unportable_or_mismatched_packages(self):
        validator = importlib.import_module('validate-release-packages')
        tool = {'id': 'Hexalith.McpCli', 'project': 'src/Hexalith.McpCli/Hexalith.McpCli.csproj'}
        valid = {'TargetFramework': 'net11.0', 'TargetFrameworks': '', 'PackAsTool': 'true', 'ToolCommandName': 'hexalith',
                 'UseAppHost': 'false', 'PublishTrimmed': '', 'PublishAot': '', 'PublishReadyToRun': '', 'SelfContained': '',
                 'RuntimeIdentifier': '', 'RuntimeIdentifiers': '', 'CreateRidSpecificToolPackages': '', 'PackageId': 'Hexalith.McpCli', 'Version': '1.0.0'}
        def evaluate(changes):
            result = subprocess.CompletedProcess([], 0, stdout=json.dumps({'Properties': {**valid, **changes}}))
            with patch.object(validator.subprocess, 'run', return_value=result): validator.validate_effective_properties([tool], '1.0.0')
        evaluate({})
        for changes in ({'TargetFramework': 'net9.0'}, {'TargetFramework': 'net10.0'}, {'TargetFrameworks': 'net11.0;net9.0'},
                        {'PackageId': 'Other'}, {'Version': '9.9.9'}, {'PackAsTool': 'false'}, {'ToolCommandName': 'other'},
                        *({name: 'true'} for name in ('UseAppHost', 'PublishTrimmed', 'PublishAot', 'PublishReadyToRun', 'SelfContained', 'CreateRidSpecificToolPackages')),
                        {'RuntimeIdentifier': 'linux-x64'}, {'RuntimeIdentifiers': 'linux-x64'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError): evaluate(changes)


if __name__ == '__main__': unittest.main()
