"""Non-live refusal and extraction checks for the maintained runtime tools."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch


def load(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bootstrap = load('bootstrap-runtime')
wrapper = load('run-isolated')


class RuntimeTests(unittest.TestCase):
    def test_bootstrap_verifies_bytes_and_removes_only_its_extraction_container(self):
        self.extract(mismatch=False)

    def test_bootstrap_removes_rejected_bytes_and_its_container_on_hash_mismatch(self):
        self.extract(mismatch=True)

    def extract(self, mismatch):
        binary = b'qualified native executable fixture'
        image = 'daprio/dapr@sha256:' + 'a' * 64
        records = [{'image': 'daprio/dapr:1.18.7', 'imageId': 'sha256:' + 'a' * 64,
                    'source': '/sentry', 'sha256': '0' * 64 if mismatch else hashlib.sha256(binary).hexdigest()}]
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory) / 'runtime'

            def command(arguments, **kwargs):
                if arguments[:2] == ['docker', 'cp']:
                    Path(arguments[3]).write_bytes(binary)
                self.assertTrue(kwargs['check'])
                self.assertGreater(kwargs['timeout'], 0)

            with patch.object(bootstrap.subprocess, 'run', side_effect=command) as run, \
                    patch.object(bootstrap.subprocess, 'check_output', return_value='owned-container\n') as create, \
                    patch.object(bootstrap.Path, 'read_text', return_value=json.dumps(records)), \
                    patch('sys.argv', ['bootstrap-runtime.py', str(runtime)]):
                if mismatch:
                    with self.assertRaisesRegex(RuntimeError, 'Extracted SHA-256 mismatch: /sentry'):
                        bootstrap.main()
                    self.assertFalse((runtime / 'bin/sentry').exists())
                    self.assertFalse((runtime / 'bootstrap-receipt.json').exists())
                else:
                    bootstrap.main()
                    self.assertEqual(binary, (runtime / 'bin/sentry').read_bytes())
                create.assert_called_once_with(['docker', 'create', '--network', 'none', image, '/bin/true'], text=True, timeout=30)
                self.assertEqual([
                    ['docker', 'pull', '--platform', 'linux/amd64', image],
                    ['docker', 'cp', 'owned-container:/sentry', str(runtime / 'bin/sentry')],
                    ['docker', 'rm', 'owned-container'],
                ], [call.args[0] for call in run.call_args_list])

    def test_bootstrap_refuses_an_existing_runtime_before_using_docker(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(bootstrap.subprocess, 'run') as run, \
                patch('sys.argv', ['bootstrap-runtime.py', directory]):
            with self.assertRaises(FileExistsError):
                bootstrap.main()
            run.assert_not_called()

    def test_wrapper_requires_each_namespace_to_differ_before_running_commands(self):
        original = {name: 'outside-' + name for name in ('user', 'pid', 'net', 'mnt')}
        for shared in original:
            with self.subTest(namespace=shared), tempfile.TemporaryDirectory() as directory:
                run_dir = Path(directory)
                (run_dir / 'outside.json').write_text(json.dumps({'namespaces': original}))
                current = {name: 'inside-' + name for name in original}
                current[shared] = original[shared]
                with patch.object(wrapper, 'namespaces', return_value=current), \
                        patch.object(wrapper.os, 'getpid', return_value=1), \
                        patch.object(wrapper.subprocess, 'run') as run:
                    with self.assertRaisesRegex(RuntimeError, "requires private user, PID, network and mount namespaces"):
                        wrapper.inside(run_dir, ['unused-command'])
                    run.assert_not_called()

    def test_optimized_wrapper_preserves_safety_guards(self):
        for mode, diagnostic in (
            ('pid', 'The supervisor must own this private PID namespace.'),
            ('namespace', 'The supervisor requires private user, PID, network and mount namespaces.'),
            ('redis', 'Private Redis did not respond with PONG.'),
            ('dapr-exit', 'Private Dapr registration probe exited 7.'),
            ('dapr-apps', 'Private Dapr environment contains pre-existing applications.'),
        ):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                result = self.wrapper_process(Path(directory), mode, optimized=True)
                self.assertEqual(1, result.returncode)
                self.assertIn(diagnostic, result.stdout + result.stderr)
                self.assertFalse((Path(directory) / 'command.stdout.txt').exists())

    def test_wrapper_pins_the_effective_child_environment_to_private_services(self):
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            result = self.wrapper_process(run_dir, 'success')
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            child = json.loads((run_dir / 'command.stdout.txt').read_text())
            expected = {
                'MCPCLI_ISOLATED_TOPOLOGY': '1',
                'HEXALITH_EVENTSTORE_TEST_REDIS_PORT': '6379',
                'HEXALITH_EVENTSTORE_TEST_PLACEMENT_PORT': '6050',
                'HEXALITH_EVENTSTORE_TEST_SCHEDULER_PORT': '6060',
                'Dapr__PlacementHostAddress': '127.0.0.1:6050',
                'Dapr__SchedulerHostAddress': '127.0.0.1:6060',
                'Dapr__GatewayHttpPort': '3501',
                'NAMESPACE': 'default',
                'DAPR_CONTROLPLANE_TRUST_DOMAIN': 'public',
                'DAPR_CONTROLPLANE_NAMESPACE': 'default',
            }
            self.assertEqual(expected, {key: child[key] for key in expected})
            for key in ('DAPR_TRUST_ANCHORS', 'DAPR_CERT_CHAIN', 'DAPR_CERT_KEY'):
                self.assertTrue(child[key], key)
            self.assertEqual('private-test-credential', child['DAPR_CERT_KEY'])
            receipt = json.loads((run_dir / 'result.json').read_text())
            self.assertEqual('6379', receipt['environmentOverrides']['HEXALITH_EVENTSTORE_TEST_REDIS_PORT'])
            certificate_dir = run_dir / 'sentry-certificates'
            expected_services = {
                'sentry': [str(wrapper.RUNTIME_DIR / 'bin/sentry'), '--port', '50001', '--listen-address', '127.0.0.1',
                           '--trust-domain', 'public', '--issuer-credentials', str(certificate_dir),
                           '--config', str(run_dir / 'sentry-config.json'),
                           '--healthz-port', '18082', '--healthz-listen-address', '127.0.0.1',
                           '--enable-metrics=false', '--log-level', 'warn'],
                'redis': [str(wrapper.RUNTIME_DIR / 'bin/redis-server'), '--bind', '127.0.0.1', '--port', '6379',
                          '--save', '', '--appendonly', 'no', '--dir', str(run_dir), '--loglevel', 'warning'],
                'placement': [str(wrapper.RUNTIME_DIR / 'bin/placement'), '--port', '6050', '--listen-address', '0.0.0.0',
                              '--healthz-port', '18080', '--healthz-listen-address', '127.0.0.1',
                              '--enable-metrics=false', '--log-level', 'warn', '--tls-enabled',
                              '--trust-domain', 'public', '--sentry-address', '127.0.0.1:50001',
                              '--trust-anchors-file', str(certificate_dir / 'ca.crt')],
                'scheduler': [str(wrapper.RUNTIME_DIR / 'bin/scheduler'), '--port', '6060', '--listen-address', '0.0.0.0',
                              '--healthz-port', '18081', '--healthz-listen-address', '127.0.0.1',
                              '--enable-metrics=false', '--log-level', 'warn',
                              '--etcd-data-dir', str(run_dir / 'scheduler-data'),
                              '--override-broadcast-host-port', '127.0.0.1:6060', '--tls-enabled',
                              '--trust-domain', 'public', '--sentry-address', '127.0.0.1:50001',
                              '--trust-anchors-file', str(certificate_dir / 'ca.crt')],
            }
            self.assertEqual(expected_services, {name: service['arguments'] for name, service in receipt['services'].items()})
            calls = [json.loads(line) for line in (run_dir / 'infrastructure-calls.jsonl').read_text().splitlines()]
            expected_network = [
                ['ip', 'link', 'set', 'lo', 'up'],
                ['ip', 'link', 'add', 'mcpcli0', 'type', 'veth', 'peer', 'name', 'mcpcli1'],
                ['ip', 'addr', 'add', '172.31.251.1/24', 'dev', 'mcpcli0'],
                ['ip', 'link', 'set', 'mcpcli0', 'up'],
                ['ip', 'link', 'set', 'mcpcli1', 'up'],
            ]
            self.assertEqual([{'kind': 'run', 'arguments': arguments} for arguments in expected_network], calls[:5])
            self.assertEqual({'kind': 'launch', 'arguments': expected_services['sentry']}, calls[5])
            self.assertEqual(['scheduler', 'placement', 'redis-server', 'sentry'],
                             [call['arguments'][0] for call in calls if call['kind'] == 'stop'])
            self.assertEqual({name: 0 for name in expected_services}, receipt['ownedInfrastructureStopped'])
            for name in ('placement', 'scheduler'):
                arguments = receipt['services'][name]['arguments']
                port = arguments[arguments.index('--port') + 1]
                self.assertEqual(port, child['HEXALITH_EVENTSTORE_TEST_' + name.upper() + '_PORT'])
                self.assertEqual('127.0.0.1:' + port, child['Dapr__' + name.title() + 'HostAddress'])
            self.assertFalse((run_dir / 'sentry-certificates/issuer.key').exists())
            for file in run_dir.rglob('*'):
                if file.is_file() and file != run_dir / 'command.stdout.txt':
                    self.assertNotIn('private-test-credential', file.read_text(), str(file))

    def test_wrapper_refuses_readiness_failures_before_starting_the_child(self):
        for mode, error_type, message in (
            ('sentry-exit', 'RuntimeError', 'Sentry exited before generating certificates: 17'),
            ('sentry-no-certificates', 'TimeoutError', 'Private Sentry certificates were not ready'),
            ('readiness-daemon-exit', 'RuntimeError', 'redis exited before prerequisites were ready: 19'),
            ('unreachable-port', 'TimeoutError', 'Private prerequisite port 6060 did not become reachable'),
        ):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                run_dir = Path(directory)
                result = self.wrapper_process(run_dir, mode)
                self.assertEqual(1, result.returncode, result.stdout + result.stderr)
                receipt = json.loads((run_dir / 'result.json').read_text())
                self.assertEqual(1, receipt['commandExitCode'])
                self.assertEqual({'type': error_type, 'message': message}, receipt['error'])
                self.assertFalse((run_dir / 'command.stdout.txt').exists())

    def test_wrapper_requires_a_nonempty_explicit_runtime_before_creating_files(self):
        for value in (None, '', '   '):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as directory:
                environment = os.environ.copy()
                if value is None:
                    environment.pop('MCPCLI_ISOLATED_RUNTIME_DIR', None)
                else:
                    environment['MCPCLI_ISOLATED_RUNTIME_DIR'] = value
                result = subprocess.run([sys.executable, str(Path(__file__).with_name('run-isolated.py').resolve())],
                                        cwd=directory, env=environment, text=True, capture_output=True, timeout=5)
                self.assertEqual(1, result.returncode)
                self.assertEqual('', result.stdout)
                self.assertEqual('MCPCLI_ISOLATED_RUNTIME_DIR must name a prepared private runtime directory.\n', result.stderr)
                self.assertEqual([], list(Path(directory).iterdir()))

    def test_public_wrapper_requires_a_command_before_creating_files_or_launching_namespaces(self):
        for arguments in ([], ['--']):
            with self.subTest(arguments=arguments), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                result = self.public_wrapper_process(root, arguments)
                self.assertEqual(1, result.returncode)
                self.assertEqual('', result.stdout)
                self.assertEqual('A command to execute is required.\n', result.stderr)
                self.assertEqual(['unshare'], [file.name for file in root.iterdir()])

    def test_public_wrapper_forwards_the_supplied_child_and_its_failure_through_namespace_launch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            command = [sys.executable, '-c',
                       "import pathlib,sys; pathlib.Path('supplied-child-marker').write_text('supplied child ran'); "
                       "print('supplied child stdout'); print('supplied child stderr', file=sys.stderr); sys.exit(23)"]
            result = self.public_wrapper_process(root, ['--', *command])
            self.assertEqual(23, result.returncode, result.stdout + result.stderr)
            self.assertEqual('', result.stderr)
            self.assertEqual('supplied child ran', (root / 'supplied-child-marker').read_text())
            runs = list((root / 'runtime/runs').iterdir())
            self.assertEqual(1, len(runs))
            run_dir = runs[0]
            self.assertEqual('supplied child stdout\n', (run_dir / 'command.stdout.txt').read_text())
            self.assertEqual('supplied child stderr\n', (run_dir / 'command.stderr.txt').read_text())
            receipt = json.loads((run_dir / 'result.json').read_text())
            self.assertEqual(command, receipt['command'])
            self.assertEqual(23, receipt['commandExitCode'])
            self.assertEqual(['unshare', '--user', '--map-root-user', '--net', '--pid', '--mount',
                              '--fork', '--mount-proc', sys.executable,
                              str(Path(__file__).with_name('run-isolated.py').resolve()),
                              '--inside', str(run_dir), '--', *command],
                             ['unshare', *json.loads((root / 'namespace-launch.json').read_text())])

    def public_wrapper_process(self, root, arguments):
        launcher = root / 'unshare'
        launcher.write_text('#!' + sys.executable + '\n' + r"""
import json, os, pathlib, sys
arguments = sys.argv[1:]
pathlib.Path(os.environ['MCPCLI_TEST_NAMESPACE_LAUNCH']).write_text(json.dumps(arguments))
inside = arguments.index('--inside')
os.execv(sys.executable, [sys.executable, os.environ['MCPCLI_TEST_WRAPPER_FIXTURE'],
    '--wrapper-fixture', arguments[inside + 1], 'supplied-command', '--', *arguments[inside + 3:]])
""")
        launcher.chmod(0o700)
        environment = os.environ.copy()
        environment['PATH'] = str(root) + os.pathsep + environment.get('PATH', '')
        environment['MCPCLI_ISOLATED_RUNTIME_DIR'] = str(root / 'runtime')
        environment['MCPCLI_TEST_NAMESPACE_LAUNCH'] = str(root / 'namespace-launch.json')
        environment['MCPCLI_TEST_WRAPPER_FIXTURE'] = str(Path(__file__).resolve())
        return subprocess.run([sys.executable, str(Path(__file__).with_name('run-isolated.py').resolve()), *arguments],
                              cwd=root, env=environment, text=True, capture_output=True, timeout=10)

    def test_wrapper_stops_a_real_hung_child_and_records_its_deadline(self):
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            result = self.wrapper_process(run_dir, 'hung-child')
            self.assertEqual(124, result.returncode, result.stdout + result.stderr)
            receipt = json.loads((run_dir / 'result.json').read_text())
            self.assertEqual(124, receipt['commandExitCode'])
            self.assertTrue((run_dir / 'child-started').exists())
            self.assertTrue((run_dir / 'child-stopped').exists())

    def test_wrapper_removes_private_keys_before_an_interrupted_daemon_shutdown(self):
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            result = self.wrapper_process(run_dir, 'interrupted-shutdown')
            self.assertEqual(143, result.returncode, result.stdout + result.stderr)
            self.assertEqual([], json.loads((run_dir / 'keys-at-shutdown.json').read_text()))
            self.assertFalse((run_dir / 'sentry-certificates/issuer.key').exists())

    def test_wrapper_forces_a_sigterm_ignoring_child_to_exit_at_its_deadline(self):
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            result = self.wrapper_process(run_dir, 'ignores-term')
            self.assertEqual(124, result.returncode, result.stdout + result.stderr)
            self.assertEqual(124, json.loads((run_dir / 'result.json').read_text())['commandExitCode'])
            child = json.loads((run_dir / 'child-exit.json').read_text())
            self.assertEqual(-signal.SIGKILL, child['returncode'])
            with self.assertRaises(ProcessLookupError):
                os.kill(child['pid'], 0)

    def test_wrapper_records_bounded_stderr_before_parsing_a_failed_dapr_probe(self):
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            result = self.wrapper_process(run_dir, 'dapr-exit')
            self.assertEqual(1, result.returncode, result.stdout + result.stderr)
            receipt = json.loads((run_dir / 'result.json').read_text())
            detail = 'probe failure: ' + 'x' * (512 - len('probe failure: ')) + '...'
            self.assertEqual({'exitCode': 7, 'stderr': detail}, receipt['daprBeforeCommand'])
            self.assertEqual('RuntimeError', receipt['error']['type'])
            self.assertEqual('Private Dapr registration probe exited 7. stderr: ' + detail, receipt['error']['message'])

    def test_wrapper_propagates_a_real_failing_child_exit_and_records_it(self):
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            result = self.wrapper_process(run_dir, 'failing-child')
            self.assertEqual(23, result.returncode, result.stdout + result.stderr)
            self.assertEqual(23, json.loads((run_dir / 'result.json').read_text())['commandExitCode'])

    def test_inner_wrapper_refuses_an_empty_command_without_recording_success(self):
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            result = self.wrapper_process(run_dir, 'empty-command')
            self.assertEqual(1, result.returncode, result.stdout + result.stderr)
            self.assertEqual('', result.stderr)
            self.assertIn('Private environment failed: IndexError: list index out of range\n', result.stdout)
            receipt = json.loads((run_dir / 'result.json').read_text())
            self.assertEqual([], receipt['command'])
            self.assertEqual(1, receipt['commandExitCode'])
            self.assertEqual({'type': 'IndexError', 'message': 'list index out of range'}, receipt['error'])

    def test_wrapper_rejects_a_daemon_that_exits_during_a_successful_child(self):
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            result = self.wrapper_process(run_dir, 'failed-daemon')
            self.assertTrue((run_dir / 'child-succeeded').exists())
            self.assertEqual(1, result.returncode, result.stdout + result.stderr)
            receipt = json.loads((run_dir / 'result.json').read_text())
            self.assertEqual(1, receipt['commandExitCode'])
            self.assertEqual('redis exited while the command ran: 17', receipt['error']['message'])

    def wrapper_process(self, run_dir, mode, optimized=False):
        command = [sys.executable]
        if optimized:
            command.append('-O')
        command.extend([str(Path(__file__).resolve()), '--wrapper-fixture', str(run_dir), mode])
        environment = os.environ.copy()
        environment['HEXALITH_EVENTSTORE_TEST_REDIS_PORT'] = '19999'
        for variable in ('NAMESPACE', 'DAPR_CONTROLPLANE_TRUST_DOMAIN', 'DAPR_CONTROLPLANE_NAMESPACE',
                         'DAPR_TRUST_ANCHORS', 'DAPR_CERT_CHAIN', 'DAPR_CERT_KEY',
                         'HEXALITH_EVENTSTORE_TEST_PLACEMENT_PORT', 'HEXALITH_EVENTSTORE_TEST_SCHEDULER_PORT',
                         'Dapr__PlacementHostAddress', 'Dapr__SchedulerHostAddress', 'Dapr__GatewayHttpPort'):
            environment.pop(variable, None)
        return subprocess.run(command, env=environment, text=True, capture_output=True, timeout=10)

    def test_bootstrap_termination_during_extraction_removes_its_owned_container(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            docker = root / 'docker'
            docker.write_text('#!' + sys.executable + '\n' + r"""
import json, os, pathlib, sys, time
with pathlib.Path(os.environ['DOCKER_TEST_LOG']).open('a') as log:
    log.write(json.dumps(sys.argv[1:]) + '\n')
if sys.argv[1] == 'create':
    print('owned-extraction-container', flush=True)
if sys.argv[1] == 'cp':
    pathlib.Path(os.environ['DOCKER_TEST_READY']).touch()
    time.sleep(60)
""")
            docker.chmod(0o700)
            environment = os.environ.copy()
            environment['PATH'] = str(root) + os.pathsep + environment.get('PATH', '')
            environment['DOCKER_TEST_LOG'] = str(root / 'docker-calls.jsonl')
            environment['DOCKER_TEST_READY'] = str(root / 'copy-started')
            process = subprocess.Popen([sys.executable, str(Path(__file__).with_name('bootstrap-runtime.py')), str(root / 'runtime')],
                                       env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                deadline = time.monotonic() + 5
                while not (root / 'copy-started').exists():
                    if process.poll() is not None or time.monotonic() >= deadline:
                        if process.poll() is None:
                            process.kill()
                        stdout, stderr = process.communicate(timeout=5)
                        self.fail('Extraction did not reach its controlled termination point: ' + stdout + stderr)
                    time.sleep(0.01)
                process.send_signal(signal.SIGTERM)
                stdout, stderr = process.communicate(timeout=10)
                self.assertEqual(143, process.returncode, stdout + stderr)
                calls = [json.loads(line) for line in (root / 'docker-calls.jsonl').read_text().splitlines()]
                self.assertEqual(['rm', 'owned-extraction-container'], calls[-1])
                self.assertFalse((root / 'runtime/bootstrap-receipt.json').exists())
            finally:
                if process.poll() is None:
                    process.kill()
                    process.communicate(timeout=5)
                process.stdout.close()
                process.stderr.close()


def wrapper_fixture(run_dir, mode, supplied_command=None):
    """Run the real supervisor and real child with inert private-infrastructure stand-ins."""
    original = {name: 'outside-' + name for name in ('user', 'pid', 'net', 'mnt')}
    current = {name: 'inside-' + name for name in original}
    if mode == 'namespace':
        current['net'] = original['net']
    cwd = json.loads((run_dir / 'outside.json').read_text())['cwd'] if supplied_command is not None else str(run_dir)
    (run_dir / 'outside.json').write_text(json.dumps({'namespaces': original, 'cwd': cwd}))
    real_popen = subprocess.Popen
    fixture_assertions = unittest.TestCase()
    expected_daemon_environment = os.environ.copy()
    expected_daemon_environment.update({
        'MCPCLI_ISOLATED_TOPOLOGY': '1',
        'GOMAXPROCS': '2',
        'DOTNET_PROCESSOR_COUNT': '2',
        'DOTNET_CLI_TELEMETRY_OPTOUT': '1',
        'HEXALITH_EVENTSTORE_TEST_REDIS_PORT': '6379',
        'HEXALITH_EVENTSTORE_TEST_PLACEMENT_PORT': '6050',
        'HEXALITH_EVENTSTORE_TEST_SCHEDULER_PORT': '6060',
        'Dapr__PlacementHostAddress': '127.0.0.1:6050',
        'Dapr__SchedulerHostAddress': '127.0.0.1:6060',
        'Dapr__GatewayHttpPort': '3501',
        'NAMESPACE': 'default',
        'DAPR_CONTROLPLANE_TRUST_DOMAIN': 'public',
        'DAPR_CONTROLPLANE_NAMESPACE': 'default',
    })

    class Daemon:
        returncode = None

        def __init__(self, name):
            self.name = name
            self.pid = 100

        def poll(self):
            if mode == 'sentry-exit' and self.name == 'sentry':
                self.returncode = 17
            if mode == 'readiness-daemon-exit' and self.name == 'redis-server':
                self.returncode = 19
            if mode == 'failed-daemon' and self.name == 'redis-server' and (run_dir / 'child-succeeded').exists():
                self.returncode = 17
            return self.returncode

    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def sendall(self, _):
            pass

        def recv(self, _):
            return b'-ERR wrong service' if mode == 'redis' else b'+PONG\r\n'

    def record_call(kind, arguments):
        with (run_dir / 'infrastructure-calls.jsonl').open('a') as log:
            log.write(json.dumps({'kind': kind, 'arguments': arguments}) + '\n')

    def start(arguments, **kwargs):
        record_call('launch', arguments)
        if not arguments or arguments[0] == sys.executable:
            process = real_popen(arguments, **kwargs)
            if mode == 'ignores-term':
                deadline = time.monotonic() + 2
                while not (run_dir / 'child-started').exists():
                    if process.poll() is not None or time.monotonic() >= deadline:
                        if process.poll() is None:
                            process.kill()
                        process.wait(timeout=5)
                        raise RuntimeError('The SIGTERM-ignoring test child did not become ready.')
                    time.sleep(0.01)
            return process
        name = Path(arguments[0]).name
        fixture_assertions.assertIs(True, kwargs.get('start_new_session'), name)
        fixture_assertions.assertEqual(run_dir, kwargs.get('cwd'), name)
        log_name = 'redis' if name == 'redis-server' else name
        fixture_assertions.assertEqual(str(run_dir / (log_name + '.log')), kwargs['stdout'].name)
        fixture_assertions.assertEqual('wb', kwargs['stdout'].mode)
        fixture_assertions.assertFalse(kwargs['stdout'].closed)
        fixture_assertions.assertEqual(subprocess.STDOUT, kwargs.get('stderr'), name)
        expected_environment = expected_daemon_environment.copy()
        if name != 'sentry':
            expected_environment.update({'DAPR_TRUST_ANCHORS': 'public-test-certificate',
                                         'DAPR_CERT_CHAIN': 'public-test-certificate',
                                         'DAPR_CERT_KEY': 'private-test-credential'})
        fixture_assertions.assertEqual(set(expected_environment), set(kwargs['env']), name)
        for key, value in expected_environment.items():
            fixture_assertions.assertTrue(kwargs['env'][key] == value, name + ' environment variable ' + key)
        if name == 'sentry' and mode not in ('sentry-exit', 'sentry-no-certificates'):
            certificates = run_dir / 'sentry-certificates'
            for filename in ('ca.crt', 'issuer.crt', 'issuer.key'):
                (certificates / filename).write_text('private-test-credential' if filename.endswith('.key') else 'public-test-certificate')
        return Daemon(name)

    def run(arguments, **_):
        record_call('run', arguments)
        return subprocess.CompletedProcess(arguments, 7 if mode == 'dapr-exit' else 0,
                                           '' if mode == 'dapr-exit' else '[{"appId":"existing"}]' if mode == 'dapr-apps' else '[]',
                                           'probe failure: ' + 'x' * 600 if mode == 'dapr-exit' else '')

    def connect(address, **_):
        if mode == 'unreachable-port' and address[1] == 6060:
            raise OSError('Controlled unreachable private port')
        return Connection()

    def stop(process):
        if isinstance(process, real_popen):
            try:
                return real_stop(process)
            finally:
                # A broken forced-stop guard must fail without leaving the test child alive.
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=5)
                (run_dir / 'child-exit.json').write_text(json.dumps({'pid': process.pid, 'returncode': process.returncode}))
        record_call('stop', [process.name])
        if mode == 'interrupted-shutdown':
            (run_dir / 'keys-at-shutdown.json').write_text(json.dumps(
                [file.name for file in (run_dir / 'sentry-certificates').glob('*.key')]))
            raise SystemExit(143)
        if process.poll() is None:
            process.returncode = 0

    real_stop = wrapper.stop_owned
    child_variables = ['MCPCLI_ISOLATED_TOPOLOGY', 'HEXALITH_EVENTSTORE_TEST_REDIS_PORT',
                       'HEXALITH_EVENTSTORE_TEST_PLACEMENT_PORT', 'HEXALITH_EVENTSTORE_TEST_SCHEDULER_PORT',
                       'Dapr__PlacementHostAddress', 'Dapr__SchedulerHostAddress', 'Dapr__GatewayHttpPort',
                       'NAMESPACE', 'DAPR_CONTROLPLANE_TRUST_DOMAIN', 'DAPR_CONTROLPLANE_NAMESPACE',
                       'DAPR_TRUST_ANCHORS', 'DAPR_CERT_CHAIN', 'DAPR_CERT_KEY']
    child = [sys.executable, '-c',
             "import json,os,pathlib,sys; print(json.dumps({key:os.environ.get(key) for key in " + repr(child_variables) + "})); "
             "pathlib.Path('child-succeeded').touch(); sys.exit(" + ('23' if mode == 'failing-child' else '0') + ")"]
    if mode == 'hung-child':
        child = [sys.executable, '-c',
                 "import pathlib,signal,sys,time; "
                 "signal.signal(signal.SIGTERM, lambda *_: (pathlib.Path('child-stopped').touch(), sys.exit(143))); "
                 "pathlib.Path('child-started').touch(); time.sleep(60)"]
    if mode == 'ignores-term':
        child = [sys.executable, '-c',
                 "import pathlib,signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); "
                 "pathlib.Path('child-started').touch(); time.sleep(60)"]
    if mode == 'empty-command':
        child = []
    if supplied_command is not None:
        child = supplied_command
    with patch.object(wrapper, 'namespaces', return_value=current), \
            patch.object(wrapper.os, 'getpid', return_value=2 if mode == 'pid' else 1), \
            patch.object(wrapper.subprocess, 'run', side_effect=run), \
            patch.object(wrapper.subprocess, 'Popen', side_effect=start), \
            patch.object(wrapper.socket, 'create_connection', side_effect=connect), \
            patch.object(wrapper, 'PREREQUISITE_TIMEOUT_SECONDS', 0.05), \
            patch.object(wrapper, 'COMMAND_TIMEOUT_SECONDS', 0.5 if mode in ('hung-child', 'ignores-term') else wrapper.COMMAND_TIMEOUT_SECONDS), \
            patch.object(wrapper, 'STOP_GRACE_SECONDS', 0.2 if mode == 'ignores-term' else wrapper.STOP_GRACE_SECONDS), \
            patch.object(wrapper, 'stop_owned', side_effect=stop):
        return wrapper.inside(run_dir, child)


if __name__ == '__main__':
    if sys.argv[1:2] == ['--wrapper-fixture']:
        sys.exit(wrapper_fixture(Path(sys.argv[2]), sys.argv[3], sys.argv[5:] if sys.argv[4:5] == ['--'] else None))
    unittest.main()
