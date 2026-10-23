#!/usr/bin/env python3
"""Run the unchanged topology tests with private PIDs, networking and Dapr state."""
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
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)


def inside(run_dir: Path, command: list[str]) -> int:
    outside = json.loads((run_dir / 'outside.json').read_text())
    current = namespaces()
    assert os.getpid() == 1, 'The supervisor must own this private PID namespace.'
    assert all(current[key] != outside['namespaces'][key] for key in current)
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
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
        'GOMAXPROCS': '2',
        'DOTNET_PROCESSOR_COUNT': '2',
        'DOTNET_CLI_TELEMETRY_OPTOUT': '1',
        'HEXALITH_EVENTSTORE_TEST_PLACEMENT_PORT': '6050',
        'HEXALITH_EVENTSTORE_TEST_SCHEDULER_PORT': '6060',
        'Dapr__PlacementHostAddress': '127.0.0.1:6050',
        'Dapr__SchedulerHostAddress': '127.0.0.1:6060',
        'Dapr__GatewayHttpPort': '3501',
    })
    commands = {
        'redis': [str(RUNTIME_DIR / 'bin/redis-server'), '--bind', '127.0.0.1', '--port', '6379',
                  '--save', '', '--appendonly', 'no', '--dir', str(run_dir), '--loglevel', 'warning'],
        'placement': [str(RUNTIME_DIR / 'bin/placement'), '--port', '6050', '--listen-address', '0.0.0.0',
                      '--healthz-port', '18080', '--healthz-listen-address', '127.0.0.1',
                      '--enable-metrics=false', '--log-level', 'warn'],
        'scheduler': [str(RUNTIME_DIR / 'bin/scheduler'), '--port', '6060', '--listen-address', '0.0.0.0',
                      '--healthz-port', '18081', '--healthz-listen-address', '127.0.0.1',
                      '--enable-metrics=false', '--log-level', 'warn',
                      '--etcd-data-dir', str(run_dir / 'scheduler-data'),
                      '--override-broadcast-host-port', '127.0.0.1:6060'],
    }
    processes: dict[str, subprocess.Popen] = {}
    logs = []
    result = {'namespaces': current, 'supervisorPid': os.getpid(), 'services': {}, 'command': command,
              'environmentOverrides': {key: environment[key] for key in environment if key in (
                  'GOMAXPROCS', 'DOTNET_PROCESSOR_COUNT', 'HEXALITH_EVENTSTORE_TEST_PLACEMENT_PORT',
                  'HEXALITH_EVENTSTORE_TEST_SCHEDULER_PORT', 'Dapr__PlacementHostAddress',
                  'Dapr__SchedulerHostAddress', 'Dapr__GatewayHttpPort')}}
    try:
        for name, arguments in commands.items():
            log = (run_dir / (name + '.log')).open('wb')
            logs.append(log)
            process = subprocess.Popen(arguments, cwd=run_dir, env=environment,
                                       stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            processes[name] = process
            result['services'][name] = {'pid': process.pid, 'arguments': arguments}
        deadline = time.monotonic() + 40
        for port in (6379, 6050, 6060):
            while True:
                for name, process in processes.items():
                    if process.poll() is not None:
                        raise RuntimeError(f'{name} exited before prerequisites were ready: {process.returncode}')
                try:
                    with socket.create_connection(('127.0.0.1', port), timeout=1) as connection:
                        if port == 6379:
                            connection.sendall(b'*1\r\n$4\r\nPING\r\n')
                            assert connection.recv(128).startswith(b'+PONG')
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise TimeoutError(f'Private prerequisite port {port} did not become reachable')
                    time.sleep(0.1)
        probe = subprocess.run(['dapr', 'list', '--output', 'json'], env=environment,
                               text=True, capture_output=True, timeout=10)
        result['daprBeforeCommand'] = {'exitCode': probe.returncode, 'applications': json.loads(probe.stdout)}
        assert probe.returncode == 0 and result['daprBeforeCommand']['applications'] == []
        result['prerequisitesReady'] = True
        print('Private Redis, placement and scheduler are ready; Dapr has no pre-existing applications.', flush=True)
        if command:
            with (run_dir / 'command.stdout.txt').open('wb') as output, (run_dir / 'command.stderr.txt').open('wb') as error:
                child = subprocess.Popen(command, cwd=outside['cwd'], env=environment,
                                         stdout=output, stderr=error, start_new_session=True)
                started = time.monotonic()
                try:
                    result['commandExitCode'] = child.wait(timeout=900)
                except subprocess.TimeoutExpired:
                    stop_owned(child)
                    result['commandExitCode'] = 124
                result['commandElapsedSeconds'] = round(time.monotonic() - started, 3)
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
        for process in reversed(list(processes.values())):
            stop_owned(process)
        for log in logs:
            log.close()
        result['ownedInfrastructureStopped'] = {name: process.poll() for name, process in processes.items()}
        (run_dir / 'result.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    if sys.argv[1:2] == ['--inside']:
        sys.exit(inside(Path(sys.argv[2]), sys.argv[4:]))
    command = sys.argv[1:]
    if command[:1] == ['--']:
        command = command[1:]
    run_id = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    run_dir = RUNTIME_DIR / 'runs' / run_id
    run_dir.mkdir(parents=True)
    (run_dir / 'outside.json').write_text(json.dumps({'namespaces': namespaces(), 'cwd': os.getcwd()}, indent=2) + '\n')
    print('Isolated run:', run_dir, flush=True)
    completed = subprocess.run(['unshare', '--user', '--map-root-user', '--net', '--pid', '--mount',
                                '--fork', '--mount-proc', sys.executable, str(Path(__file__).resolve()),
                                '--inside', str(run_dir), '--', *command])
    sys.exit(completed.returncode)
