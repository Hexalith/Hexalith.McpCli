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
        for phase in ('linux', 'linux-packages', 'linux-census', 'linux-conformance'):
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
                ('linux-census', ['init_submodules', 'execute:proprietary-surfaces/v1/check.py']),
                ('linux-conformance', ['execute:scripts/tests', 'execute:run-sample-validation.sh',
                                       'execute:run-sample-loopback.sh', 'execute:check_enrolled.py',
                                       'execute:tools/live-topology', 'execute:run-vectors.py']),
                ('linux', ['stage_packages', 'package_checks', 'init_submodules',
                           'execute:proprietary-surfaces/v1/check.py', 'execute:scripts/tests',
                           'execute:run-sample-validation.sh', 'execute:run-sample-loopback.sh',
                           'execute:check_enrolled.py', 'execute:tools/live-topology', 'execute:run-vectors.py'])):
            events = []
            def record_execute(command, **_):
                joined = ' '.join(map(str, command))
                matched = False
                for marker in ('proprietary-surfaces/v1/check.py', 'scripts/tests', 'run-sample-validation.sh',
                               'run-sample-loopback.sh', 'check_enrolled.py', 'tools/live-topology', 'run-vectors.py'):
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
                    patch.object(product_ci, 'initialize_direct_submodules', side_effect=lambda **_: events.append('init_submodules') or []), \
                    patch.object(product_ci, 'execute', side_effect=record_execute), \
                    contextlib.redirect_stderr(io.StringIO()) as stderr:
                self.assertEqual(0, product_ci.main(), stderr.getvalue())
                self.assertEqual(expected, events)

    def test_linux_census_initializes_only_missing_direct_roots_non_recursively_and_propagates_failure(self):
        sha_a, sha_b, sha_c = 'a' * 40, 'b' * 40, 'c' * 40
        gitmodules = (
            '[submodule "references/A"]\n\tpath = references/A\n\turl = https://example.invalid/A.git\n'
            '[submodule "references/B"]\n\tpath = references/B\n\turl = https://example.invalid/B.git\n'
            '[submodule "references/C"]\n\tpath = references/C\n\turl = https://example.invalid/C.git\n'
        )
        ls_tree = (
            f'160000 commit {sha_a}\treferences/A\n'
            f'160000 commit {sha_b}\treferences/B\n'
            f'160000 commit {sha_c}\treferences/C\n'
        )
        initialized = {('references/A', sha_a)}
        calls = []

        def fake_git(*args, cwd=None):
            if args == ('show', 'HEAD:.gitmodules'):
                return gitmodules
            if args == ('-c', 'core.quotePath=false', 'ls-tree', '-r', '--full-tree', 'HEAD'):
                return ls_tree
            raise AssertionError(f'Unexpected git call: {args}')

        def fake_execute(command, **kwargs):
            args = list(map(str, command))
            calls.append((args, kwargs))
            if args[:6] == ['git', '--literal-pathspecs', '-c', 'protocol.file.allow=never', '-c', 'submodule.recurse=false']:
                self.assertNotIn('--recursive', args)
                self.assertIn('--init', args)
                self.assertIn('--checkout', args)
                self.assertEqual(480, kwargs.get('timeout'))
                self.assertEqual(self.fixture.root, kwargs.get('cwd'))
                self.assertEqual('0', kwargs['environment']['GIT_TERMINAL_PROMPT'])
                sep = args.index('--')
                for path in args[sep + 1:]:
                    initialized.add((path, {'references/A': sha_a, 'references/B': sha_b, 'references/C': sha_c}[path]))
            return subprocess.CompletedProcess(command, 0, stdout='', stderr='')

        with patch.object(product_ci, 'git', side_effect=fake_git), \
                patch.object(product_ci, 'submodule_initialized', side_effect=lambda p, s, cwd=None: (p, s) in initialized), \
                patch.object(product_ci, 'execute', side_effect=fake_execute):
            product_ci.linux_census()

        self.assertEqual(2, len(calls))
        self.assertEqual(['git', '--literal-pathspecs', '-c', 'protocol.file.allow=never', '-c', 'submodule.recurse=false',
                          'submodule', 'update', '--init', '--checkout', '--', 'references/B', 'references/C'], calls[0][0])
        self.assertTrue(calls[1][0][1].endswith('tools/proprietary-surfaces/v1/check.py'))
        self.assertEqual(['--output', str(self.product / 'diagnostics' / 'census.json')], calls[1][0][2:])
        self.assertEqual(300, calls[1][1].get('timeout'))
        self.assertFalse(any('test_census.py' in ' '.join(cmd) for cmd, _ in calls))

        # Skip git submodule init entirely when every direct root already has its pinned commit.
        skip_calls = []
        with patch.object(product_ci, 'git', side_effect=fake_git), \
                patch.object(product_ci, 'submodule_initialized', return_value=True), \
                patch.object(product_ci, 'execute', side_effect=lambda cmd, **kw: skip_calls.append(list(map(str, cmd))) or subprocess.CompletedProcess(cmd, 0)):
            product_ci.linux_census()
        self.assertEqual(1, len(skip_calls))
        self.assertTrue(skip_calls[0][1].endswith('tools/proprietary-surfaces/v1/check.py'))

        # Custom cwd propagates to both direct_submodule_paths and execute().
        custom_cwd = self.root / 'custom-workspace'
        custom_cwd.mkdir()
        git_cwds, exec_cwds = [], []
        custom_init = set()
        def custom_git(*args, cwd=None):
            git_cwds.append(cwd)
            return fake_git(*args, cwd=cwd)
        def custom_exec(command, **kwargs):
            exec_cwds.append(kwargs.get('cwd'))
            custom_init.update({('references/A', sha_a), ('references/B', sha_b), ('references/C', sha_c)})
            return subprocess.CompletedProcess(command, 0)
        with patch.object(product_ci, 'git', side_effect=custom_git), \
                patch.object(product_ci, 'submodule_initialized', side_effect=lambda p, s, cwd=None: (p, s) in custom_init), \
                patch.object(product_ci, 'execute', side_effect=custom_exec):
            product_ci.initialize_direct_submodules(cwd=custom_cwd)
        self.assertTrue(git_cwds and all(c == custom_cwd for c in git_cwds))
        self.assertEqual([custom_cwd], exec_cwds)

        # Still-uninitialized root after init fails closed before invoking check.py.
        with patch.object(product_ci, 'git', side_effect=fake_git), \
                patch.object(product_ci, 'submodule_initialized', return_value=False), \
                patch.object(product_ci, 'execute') as exec_mock:
            with self.assertRaisesRegex(ValueError, 'remain uninitialized'):
                product_ci.linux_census()
            self.assertEqual(1, exec_mock.call_count)

        # Census failure propagates non-zero.
        def failing_census(command, **_):
            if str(command[1]).endswith('check.py'):
                raise subprocess.CalledProcessError(1, command, stderr='error: unapproved-root')
            return subprocess.CompletedProcess(command, 0, stdout='', stderr='')

        with patch.object(product_ci, 'git', side_effect=fake_git), \
                patch.object(product_ci, 'submodule_initialized', return_value=True), \
                patch.object(product_ci, 'execute', side_effect=failing_census):
            with self.assertRaises(subprocess.CalledProcessError):
                product_ci.linux_census()

    def test_linux_census_refuses_dirty_before_and_drifted_after(self):
        with patch.object(product_ci, 'source_changes', return_value=' M dirty.py'), \
                patch.object(product_ci, 'initialize_direct_submodules') as init_mock, \
                patch.object(product_ci, 'execute') as exec_mock:
            with self.assertRaisesRegex(ValueError, 'exact clean checkout SHA'):
                product_ci.linux_census()
            init_mock.assert_not_called()
            exec_mock.assert_not_called()
        with patch.object(product_ci, 'source_changes', side_effect=['', '?? drifted.txt']), \
                patch.object(product_ci, 'initialize_direct_submodules', return_value=[]), \
                patch.object(product_ci, 'execute', return_value=subprocess.CompletedProcess([], 0)) as exec_mock:
            with self.assertRaisesRegex(ValueError, 'exact clean checkout SHA'):
                product_ci.linux_census()
            self.assertEqual(1, exec_mock.call_count)

    def test_direct_submodule_paths_rejects_malformed_unsafe_and_mismatched_gitlinks(self):
        sha_a = 'a' * 40
        valid_tree = f'160000 commit {sha_a}\treferences/A\n'
        for label, gitmodules, ls_tree in (
                ('empty', '', ''),
                ('escape-path', '[submodule "bad"]\n\tpath = ../escape\n\turl = https://example.invalid/x.git\n', valid_tree),
                ('control-char-path', '[submodule "bad"]\n\tpath = references/A\x07\n\turl = https://example.invalid/a.git\n', valid_tree),
                ('missing-url', '[submodule "a"]\n\tpath = references/A\n', valid_tree),
                ('control-char-url', '[submodule "a"]\n\tpath = references/A\n\turl = https://example.invalid/\x1ba.git\n', valid_tree),
                ('duplicate', '[submodule "d1"]\n\tpath = references/A\n\turl = https://example.invalid/a.git\n[submodule "d2"]\n\tpath = references/A\n\turl = https://example.invalid/a.git\n', valid_tree),
                ('overlapping', '[submodule "d1"]\n\tpath = references/A\n\turl = https://example.invalid/a.git\n[submodule "d2"]\n\tpath = references/A/B\n\turl = https://example.invalid/b.git\n',
                 f'160000 commit {sha_a}\treferences/A\n160000 commit {sha_a}\treferences/A/B\n'),
                ('invalid-section', '[other]\n\tpath = references/A\n\turl = https://example.invalid/a.git\n', valid_tree),
                ('non-gitlink', '[submodule "a"]\n\tpath = references/A\n\turl = https://example.invalid/a.git\n', f'100644 blob {sha_a}\treferences/A\n'),
                ('undeclared-gitlink', '[submodule "a"]\n\tpath = references/A\n\turl = https://example.invalid/a.git\n',
                 f'160000 commit {sha_a}\treferences/A\n160000 commit {sha_a}\treferences/Extra\n')):
            def fake_git(*args, cwd=None, gm=gitmodules, lt=ls_tree):
                return gm if args == ('show', 'HEAD:.gitmodules') else lt
            with self.subTest(case=label), patch.object(product_ci, 'git', side_effect=fake_git):
                with self.assertRaises(ValueError):
                    product_ci.direct_submodule_paths(cwd=self.root)

    def test_real_submodule_initialized_checks_symlinks_git_dir_and_pinned_commit(self):
        workspace = self.root / 'real-git-ws'
        workspace.mkdir()
        def run_git(repo, *args):
            res = subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', '-c', 'user.name=Test', '-c', 'user.email=t@example.invalid',
                                  '-C', str(repo), *args], capture_output=True, text=True, check=True)
            return res.stdout.strip()
        run_git(workspace, 'init', '-q')
        # 1. Valid initialized submodule with pinned commit.
        sub = workspace / 'references/valid'
        sub.mkdir(parents=True)
        run_git(sub, 'init', '-q')
        (sub / 'file.txt').write_text('ok\n')
        run_git(sub, 'add', 'file.txt')
        run_git(sub, 'commit', '-q', '-m', 'init')
        pinned_sha = run_git(sub, 'rev-parse', 'HEAD')
        self.assertTrue(product_ci.submodule_initialized('references/valid', pinned_sha, cwd=workspace))
        # 2. Missing pinned commit in submodule object store returns False (forces re-init).
        self.assertFalse(product_ci.submodule_initialized('references/valid', '0' * 40, cwd=workspace))
        # 3. Empty mountpoint returns False.
        (workspace / 'references/empty').mkdir()
        self.assertFalse(product_ci.submodule_initialized('references/empty', pinned_sha, cwd=workspace))
        # 4. Broken .git returns False.
        broken = workspace / 'references/broken'
        broken.mkdir()
        (broken / '.git').write_text('gitdir: /nonexistent/path\n')
        self.assertFalse(product_ci.submodule_initialized('references/broken', pinned_sha, cwd=workspace))
        # 5. Leaf symlink returns False.
        (workspace / 'references/leaf-link').symlink_to(sub)
        self.assertFalse(product_ci.submodule_initialized('references/leaf-link', pinned_sha, cwd=workspace))
        # 6. Intermediate symlink returns False.
        (workspace / 'linked-refs').symlink_to(workspace / 'references')
        self.assertFalse(product_ci.submodule_initialized('linked-refs/valid', pinned_sha, cwd=workspace))

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

    def test_split_conformance_checks_sealed_preparation_sha_on_entry_and_exit(self):
        preparation = self.root / 'preparation.json'
        preparation_id, boundary_id = '1' * 32, '2' * 32
        preparation_data = {'result': 'prepared', 'runId': preparation_id, 'source_sha': SHA}
        preparation.write_text(json.dumps(preparation_data))
        boundary = self.root / 'boundary-receipt.json'
        report = self.root / 'ci-live.json'
        boundary_data = {'schema': 'mcpcli-live-boundary/v1', 'result': 'passed', 'fullLiveAccepted': False,
                         'boundaryRunId': boundary_id, 'preparationRunId': preparation_id,
                         'preparationSha256': product_packages.digest(preparation)}
        report_data = {'result': 'boundary-passed', 'phase': 'boundary', 'fullLiveAccepted': False,
                       'runId': boundary_id, 'preparationRunId': preparation_id}

        def seal(boundary_payload, prior, *, digest=None):
            boundary.write_text(json.dumps({**boundary_payload,
                'contentSha256': product_packages.canonical_digest(boundary_payload) if digest is None else digest}))
            report.write_text(json.dumps({**prior,
                'boundaryReceipt': {'path': str(boundary), 'sha256': product_packages.digest(boundary)}}))

        argv = ['product_ci.py', 'linux-conformance', '--live-preparation', str(preparation)]
        invalid = 'receipt sealed by the passing live boundary'

        for mode, heads, changes, calls, message in (
                ('complete', [SHA, SHA], ['', ''], 6, ''),
                ('head-before', ['b' * 40], [''], 0, 'exact clean checkout SHA'),
                ('dirty-before', [SHA], [' M source.cs'], 0, 'exact clean checkout SHA'),
                ('head-after', [SHA, 'b' * 40], [''], 6, 'exact clean checkout SHA'),
                ('dirty-after', [SHA, SHA], ['', '?? source.cs'], 6, 'exact clean checkout SHA'),
                ('changed-evidence', [SHA, SHA], ['', ''], 6, 'evidence changed during split conformance'),
                ('unsealed-preparation', ['b' * 40], [''], 0, invalid),
                ('failed-boundary', [], [], 0, invalid),
                ('wrong-phase', [], [], 0, invalid),
                ('wrong-schema', [], [], 0, invalid),
                ('content-hash', [], [], 0, invalid),
                ('different-boundary-run', [], [], 0, invalid),
                ('missing-run-ids', [], [], 0, invalid)):
            with self.subTest(mode=mode):
                preparation.write_text(json.dumps(preparation_data))
                payload, prior = boundary_data.copy(), report_data.copy()
                if mode == 'failed-boundary':
                    payload['result'] = 'failed'
                if mode == 'wrong-phase':
                    prior['phase'] = 'remaining'
                if mode == 'wrong-schema':
                    payload['schema'] = 'unknown'
                if mode == 'different-boundary-run':
                    prior['runId'] = '3' * 32
                if mode == 'missing-run-ids':
                    preparation.write_text(json.dumps({key: value for key, value in preparation_data.items() if key != 'runId'}))
                    payload.update(preparationSha256=product_packages.digest(preparation))
                    for document, keys in ((payload, ('preparationRunId', 'boundaryRunId')), (prior, ('preparationRunId', 'runId'))):
                        for key in keys:
                            document.pop(key)
                seal(payload, prior, digest='invalid' if mode == 'content-hash' else None)
                if mode == 'unsealed-preparation':
                    preparation.write_text(json.dumps({**preparation_data, 'source_sha': 'b' * 40}))

                def execute(*_args, **_kwargs):
                    if mode == 'changed-evidence':
                        report.write_bytes(report.read_bytes() + b' ')

                with patch.object(sys, 'argv', argv), \
                        patch.dict(os.environ, {'HEXALITH_CI_PYTHON': sys.executable}), \
                        patch('importlib.metadata.version', return_value='4.26.0'), \
                        patch.object(product_ci.signal, 'signal'), \
                        patch.object(product_ci, 'source_sha', side_effect=heads), \
                        patch.object(product_ci, 'source_changes', side_effect=changes), \
                        patch.object(product_ci, 'execute', side_effect=execute) as child, \
                        contextlib.redirect_stderr(io.StringIO()) as stderr:
                    error = int(bool(message))
                    self.assertEqual(error, product_ci.main(), stderr.getvalue())
                    if error:
                        self.assertIn(message, stderr.getvalue())
                    else:
                        self.assertEqual('', stderr.getvalue())
                    self.assertEqual(calls, child.call_count)


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
