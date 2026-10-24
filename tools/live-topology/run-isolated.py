#!/usr/bin/env python3
"""Run topology tests with private PIDs, networking and Dapr state."""
from __future__ import annotations

import datetime
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
import uuid


RUNTIME_DIR = Path(os.environ.get('MCPCLI_ISOLATED_RUNTIME_DIR', Path(__file__).resolve().parent)).resolve()
COMMAND_TIMEOUT_SECONDS = 900
PREREQUISITE_TIMEOUT_SECONDS = 40
STOP_GRACE_SECONDS = 10


def namespaces() -> dict[str, str]:
    return {name: os.readlink('/proc/self/ns/' + name) for name in ('user', 'pid', 'net', 'mnt')}


def stop_owned(process: subprocess.Popen) -> None:
    if process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            process.wait(timeout=5)
            return
        try:
            process.wait(timeout=STOP_GRACE_SECONDS)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)


def inside(run_dir: Path, command: list[str]) -> int:
    outside = json.loads((run_dir / 'outside.json').read_text())
    current = namespaces()
    if os.getpid() != 1:
        raise RuntimeError('The supervisor must own this private PID namespace.')
    if any(current[key] == outside['namespaces'][key] for key in current):
        raise RuntimeError('The supervisor requires private user, PID, network and mount namespaces.')
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    # The private veth pair supplies multicast-capable networking for the topology.
    for arguments in (
        ['ip', 'link', 'set', 'lo', 'up'],
        ['ip', 'link', 'add', 'mcpcli0', 'type', 'veth', 'peer', 'name', 'mcpcli1'],
        ['ip', 'addr', 'add', '172.31.251.1/24', 'dev', 'mcpcli0'],
        ['ip', 'link', 'set', 'mcpcli0', 'up'],
        ['ip', 'link', 'set', 'mcpcli1', 'up'],
    ):
        subprocess.run(arguments, check=True, capture_output=True)

    environment = os.environ.copy()
    environment.update({
        # Set only after proving all four namespaces differ from the caller.
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
    })
    certificate_dir = run_dir / 'sentry-certificates'
    certificate_dir.mkdir(mode=0o700)
    sentry_config = run_dir / 'sentry-config.json'
    sentry_config.write_text(json.dumps({'apiVersion': 'dapr.io/v1alpha1', 'kind': 'Configuration',
        'metadata': {'name': 'mcpcli-private-sentry', 'namespace': 'default'},
        'spec': {'mtls': {'enabled': True, 'controlPlaneTrustDomain': 'public'}}}) + '\n')
    environment['NAMESPACE'] = 'default'
    environment['DAPR_CONTROLPLANE_TRUST_DOMAIN'] = 'public'
    environment['DAPR_CONTROLPLANE_NAMESPACE'] = 'default'
    commands = {
        'sentry': [str(RUNTIME_DIR / 'bin/sentry'), '--port', '50001', '--listen-address', '127.0.0.1',
                   '--trust-domain', 'public', '--issuer-credentials', str(certificate_dir),
                   '--config', str(sentry_config),
                   '--healthz-port', '18082', '--healthz-listen-address', '127.0.0.1',
                   '--enable-metrics=false', '--log-level', 'warn'],
        'redis': [str(RUNTIME_DIR / 'bin/redis-server'), '--bind', '127.0.0.1', '--port', '6379',
                  '--save', '', '--appendonly', 'no', '--dir', str(run_dir), '--loglevel', 'warning'],
        'placement': [str(RUNTIME_DIR / 'bin/placement'), '--port', '6050', '--listen-address', '0.0.0.0',
                      '--healthz-port', '18080', '--healthz-listen-address', '127.0.0.1',
                      '--enable-metrics=false', '--log-level', 'warn', '--tls-enabled',
                      '--trust-domain', 'public', '--sentry-address', '127.0.0.1:50001',
                      '--trust-anchors-file', str(certificate_dir / 'ca.crt')],
        'scheduler': [str(RUNTIME_DIR / 'bin/scheduler'), '--port', '6060', '--listen-address', '0.0.0.0',
                      '--healthz-port', '18081', '--healthz-listen-address', '127.0.0.1',
                      '--enable-metrics=false', '--log-level', 'warn',
                      '--etcd-data-dir', str(run_dir / 'scheduler-data'),
                      '--override-broadcast-host-port', '127.0.0.1:6060', '--tls-enabled',
                      '--trust-domain', 'public', '--sentry-address', '127.0.0.1:50001',
                      '--trust-anchors-file', str(certificate_dir / 'ca.crt')],
    }
    processes: dict[str, subprocess.Popen] = {}
    logs = []
    result = {'namespaces': current, 'supervisorPid': os.getpid(), 'services': {}, 'command': command,
              'environmentOverrides': {key: environment[key] for key in environment if key in (
                  'MCPCLI_ISOLATED_TOPOLOGY', 'GOMAXPROCS', 'DOTNET_PROCESSOR_COUNT', 'HEXALITH_EVENTSTORE_TEST_REDIS_PORT',
                  'HEXALITH_EVENTSTORE_TEST_PLACEMENT_PORT',
                  'HEXALITH_EVENTSTORE_TEST_SCHEDULER_PORT', 'Dapr__PlacementHostAddress',
                  'Dapr__SchedulerHostAddress', 'Dapr__GatewayHttpPort', 'NAMESPACE',
                  'DAPR_CONTROLPLANE_TRUST_DOMAIN', 'DAPR_CONTROLPLANE_NAMESPACE')}}
    try:
        for name, arguments in commands.items():
            log = (run_dir / (name + '.log')).open('wb')
            logs.append(log)
            process = subprocess.Popen(arguments, cwd=run_dir, env=environment,
                                       stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            processes[name] = process
            result['services'][name] = {'pid': process.pid, 'arguments': arguments}
            if name == 'sentry':
                deadline = time.monotonic() + PREREQUISITE_TIMEOUT_SECONDS
                certificate_files = ['ca.crt', 'issuer.crt', 'issuer.key']
                while not all((certificate_dir / filename).is_file() for filename in certificate_files):
                    if process.poll() is not None:
                        raise RuntimeError(f'Sentry exited before generating certificates: {process.returncode}')
                    if time.monotonic() >= deadline:
                        raise TimeoutError('Private Sentry certificates were not ready')
                    time.sleep(0.1)
                environment.update({
                    'DAPR_TRUST_ANCHORS': (certificate_dir / 'ca.crt').read_text(),
                    'DAPR_CERT_CHAIN': (certificate_dir / 'issuer.crt').read_text(),
                    'DAPR_CERT_KEY': (certificate_dir / 'issuer.key').read_text(),
                    'NAMESPACE': 'default',
                })
                result['mtls'] = {'enabled': True, 'trustDomain': 'public', 'namespace': 'default',
                                  'sentryAddress': '127.0.0.1:50001',
                                  'certificateValuesWithheld': True}
        deadline = time.monotonic() + PREREQUISITE_TIMEOUT_SECONDS
        for port in (50001, 6379, 6050, 6060):
            while True:
                for name, process in processes.items():
                    if process.poll() is not None:
                        raise RuntimeError(f'{name} exited before prerequisites were ready: {process.returncode}')
                try:
                    with socket.create_connection(('127.0.0.1', port), timeout=1) as connection:
                        if port == 6379:
                            connection.sendall(b'*1\r\n$4\r\nPING\r\n')
                            if not connection.recv(128).startswith(b'+PONG'):
                                raise RuntimeError('Private Redis did not respond with PONG.')
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise TimeoutError(f'Private prerequisite port {port} did not become reachable')
                    time.sleep(0.1)
        probe = subprocess.run(['dapr', 'list', '--output', 'json'], env=environment,
                               text=True, capture_output=True, timeout=10)
        detail = probe.stderr.strip()
        if len(detail) > 512:
            detail = detail[:512] + '...'
        result['daprBeforeCommand'] = {'exitCode': probe.returncode, 'stderr': detail}
        if probe.returncode != 0:
            raise RuntimeError(f'Private Dapr registration probe exited {probe.returncode}. stderr: {detail}')
        result['daprBeforeCommand']['applications'] = json.loads(probe.stdout)
        if result['daprBeforeCommand']['applications'] != []:
            raise RuntimeError('Private Dapr environment contains pre-existing applications.')
        result['prerequisitesReady'] = True
        print('Private Sentry, Redis, TLS placement and TLS scheduler are ready; Dapr has no pre-existing applications.', flush=True)
        if command:
            with (run_dir / 'command.stdout.txt').open('wb') as output, (run_dir / 'command.stderr.txt').open('wb') as error:
                child = subprocess.Popen(command, cwd=outside['cwd'], env=environment,
                                         stdout=output, stderr=error, start_new_session=True)
                started = time.monotonic()
                try:
                    result['commandExitCode'] = child.wait(timeout=COMMAND_TIMEOUT_SECONDS)
                except subprocess.TimeoutExpired:
                    stop_owned(child)
                    result['commandExitCode'] = 124
                result['commandElapsedSeconds'] = round(time.monotonic() - started, 3)
            if result['commandExitCode'] == 0:
                for name, process in processes.items():
                    if process.poll() is not None:
                        raise RuntimeError(f'{name} exited while the command ran: {process.returncode}')
            print(f"Command completed: exit {result['commandExitCode']}; logs: {run_dir}", flush=True)
            return result['commandExitCode']
        result['commandExitCode'] = 0
        return 0
    except Exception as exception:
        result['error'] = {'type': type(exception).__name__, 'message': str(exception)}
        result['commandExitCode'] = 1
        print(f'Private environment failed: {type(exception).__name__}: {exception}', flush=True)
        return 1
    finally:
        for private_key in certificate_dir.glob('*.key'):
            private_key.unlink()
        for process in reversed(list(processes.values())):
            stop_owned(process)
        for log in logs:
            log.close()
        result['ownedInfrastructureStopped'] = {name: process.poll() for name, process in processes.items()}
        (run_dir / 'result.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    if not os.environ.get('MCPCLI_ISOLATED_RUNTIME_DIR', '').strip():
        sys.exit('MCPCLI_ISOLATED_RUNTIME_DIR must name a prepared private runtime directory.')
    if sys.argv[1:2] == ['--inside']:
        sys.exit(inside(Path(sys.argv[2]), sys.argv[4:]))
    command = sys.argv[1:]
    if command[:1] == ['--']:
        command = command[1:]
    if not command:
        sys.exit('A command to execute is required.')
    run_id = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    run_dir = RUNTIME_DIR / 'runs' / run_id
    run_dir.mkdir(parents=True)
    (run_dir / 'outside.json').write_text(json.dumps({'namespaces': namespaces(), 'cwd': os.getcwd()}, indent=2) + '\n')
    print('Isolated run:', run_dir, flush=True)
    completed = subprocess.run(['unshare', '--user', '--map-root-user', '--net', '--pid', '--mount',
                                '--fork', '--mount-proc', sys.executable, str(Path(__file__).resolve()),
                                '--inside', str(run_dir), '--', *command])
    sys.exit(completed.returncode)
