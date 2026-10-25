#!/usr/bin/env python3
"""Preflight full enrollment, then run each vector in a fresh isolated MTP process."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import uuid
import xml.etree.ElementTree as ET

from live_plans import ROOT, preflight, require_phases, selection_binding
from validate import VectorError, _load_json


def expected_operations() -> list[str]:
    """Independently require the complete vector inventory, never a returned subset."""
    operations = [_load_json(path)['operation'] for path in
                  (ROOT / 'tools/conformance-vectors/v1/modules').rglob('*.vector.json')]
    if not operations or len(operations) != len(set(operations)):
        raise VectorError('Approved vector coverage is empty or duplicated.')
    return sorted(operations)


def require_coverage(selections: list[dict], expected: list[str]) -> None:
    """Catch omitted or duplicate execution selections independently of preflight."""
    actual = [item['operation'] for item in selections]
    if sorted(actual) != sorted(expected):
        raise VectorError('Preflight execution selections differ from complete approved vector coverage.')


def require_case(path: Path, operation: str) -> None:
    """A zero exit is insufficient: require exactly one passing, unskipped selected row."""
    root = ET.parse(path).getroot()
    assemblies = root.findall('assembly')
    tests = root.findall('.//test')
    if len(assemblies) != 1 or len(tests) != 1:
        raise VectorError(f'{operation}: expected exactly one selected MTP case, found {len(tests)}')
    assembly, test = assemblies[0], tests[0]
    if any(assembly.get(key) != expected for key, expected in
           [('total', '1'), ('passed', '1'), ('failed', '0'), ('skipped', '0'), ('errors', '0')]):
        raise VectorError(f'{operation}: selected case failed, skipped or had runner errors: {assembly.attrib}')
    traits = {(item.get('name'), item.get('value')) for item in test.findall('./traits/trait')}
    if test.get('result') != 'Pass' or test.get('method') != 'ApprovedVectorHasPersistentSemantics' \
            or ('Operation', operation) not in traits:
        raise VectorError(f'{operation}: result does not identify the selected passing vector')


def bounded_child(command: list[str], environment: dict, output: Path, timeout: float) -> int:
    with (output / 'child.stdout.txt').open('w') as stdout, (output / 'child.stderr.txt').open('w') as stderr:
        child = subprocess.Popen(command, cwd=ROOT, env=environment, stdout=stdout, stderr=stderr, start_new_session=True)
        try:
            return child.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            return 124
        finally:
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait(timeout=5)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--host', type=Path, default=ROOT / 'tests/Hexalith.McpCli.ConformanceHost/bin/Release/net10.0/Hexalith.McpCli.ConformanceHost.dll')
    parser.add_argument('--tests', type=Path, default=ROOT / 'tests/Hexalith.McpCli.Integration.Tests/bin/Release/net10.0/Hexalith.McpCli.Integration.Tests.dll')
    parser.add_argument('--child-timeout', type=float, default=960)
    parser.add_argument('--operation', help='Diagnostic subset; never grants full live acceptance.')
    parser.add_argument('--preflight-only', action='store_true')
    args = parser.parse_args(argv)
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    report = {'runId': uuid.uuid4().hex, 'result': 'pending', 'fullLiveAccepted': False, 'vectors': []}
    receipt = args.output / 'live-lane.json'
    # Invalidate the public receipt before any fallible preflight. Child outputs use a unique generation.
    receipt.write_text(json.dumps(report, indent=2) + '\n')
    generation = args.output / report['runId']
    generation.mkdir()
    previous_handler = signal.getsignal(signal.SIGTERM)
    def terminate(*_):
        raise SystemExit(143)
    signal.signal(signal.SIGTERM, terminate)

    def save():
        receipt.write_text(json.dumps(report, indent=2) + '\n')

    try:
        if not 1 <= args.child_timeout <= 960:
            raise VectorError('--child-timeout must be between 1 and 960 seconds.')
        selections = preflight(args.host.resolve(), generation / 'preflight')
        report['coverage'] = expected_operations()
        require_coverage(selections, report['coverage'])
        if args.operation:
            selections = [item for item in selections if item['operation'] == args.operation]
            if len(selections) != 1:
                raise VectorError('Selector must name exactly one approved vector Operation.')
        report['vectors'] = [{'operation': item['operation'], 'result': 'not-run'} for item in selections]
        save()
        if args.preflight_only:
            report['result'] = 'preflight-only'
            save()
            return 0
        if not os.environ.get('MCPCLI_ISOLATED_RUNTIME_DIR', '').strip():
            raise VectorError('MCPCLI_ISOLATED_RUNTIME_DIR must name a prepared private runtime.')
        for item, outcome in zip(selections, report['vectors']):
            operation = item['operation']
            output = generation / operation
            output.mkdir()
            outcome.update(result='running', output=str(output.relative_to(args.output)))
            command = [sys.executable, str(ROOT / 'tools/live-topology/run-isolated.py'), '--',
                       'dotnet', str(args.tests.resolve()), '-class', 'Hexalith.McpCli.Integration.Tests.LiveVectorTests',
                       '-trait', 'Operation=' + operation, '-preEnumerateTheories', '-failSkips', '-result-xml', str(output / 'tests.xml')]
            outcome['command'] = command
            save()
            environment = os.environ.copy()
            for key in list(environment):
                if key.startswith(('MCPCLI_LIVE_', 'EVENTSTORE_')):
                    del environment[key]
            environment.update(MCPCLI_LIVE_OPERATION=operation, MCPCLI_LIVE_OUTPUT=str(output),
                               MCPCLI_LIVE_HOST=str(args.host.resolve()),
                               MCPCLI_LIVE_BINDING=json.dumps(selection_binding(item)))
            try:
                code = bounded_child(command, environment, output, args.child_timeout)
                outcome['exitCode'] = code
                if code != 0:
                    raise VectorError(f'{operation}: isolated child exited {code}; see {output}')
                require_case(output / 'tests.xml', operation)
                live = json.loads((output / 'live-result.json').read_text())
                if live.get('operation') != operation or live.get('result') != 'passed' \
                        or live.get('binding') != selection_binding(item):
                    raise VectorError(f'{operation}: missing, stale or unsuccessful semantic receipt')
                require_phases(item, live.get('phases', []))
                # Verify the wrapper's ownership receipt, including successful private infrastructure cleanup.
                lines = (output / 'child.stdout.txt').read_text().splitlines()
                runs = [Path(line.removeprefix('Isolated run: ')) for line in lines if line.startswith('Isolated run: ')]
                if len(runs) != 1:
                    raise VectorError(f'{operation}: missing isolated runtime receipt')
                owned = json.loads((runs[0] / 'result.json').read_text())
                if owned.get('commandExitCode') != 0 or not owned.get('prerequisitesReady') \
                        or set(owned.get('ownedInfrastructureStopped', {})) != {'sentry', 'redis', 'placement', 'scheduler'} \
                        or any(value is None for value in owned['ownedInfrastructureStopped'].values()):
                    raise VectorError(f'{operation}: private runtime did not prove successful cleanup')
                outcome.update(result='passed', isolatedReceipt=str(runs[0] / 'result.json'))
                bootstrap = json.loads((output / 'writer-bootstrap.json').read_text())
                backup = owned.get('initialRedisBackup', {})
                reference = 'sha256:' + backup.get('sha256', '') + ';file:' + backup.get('backupFile', '')
                if bootstrap.get('result') != 'passed' or bootstrap.get('activationCount') != 1 \
                        or bootstrap.get('readinessObserved') is not True or bootstrap.get('backupReference') != reference \
                        or len(bootstrap.get('sourceCommit', '')) != 40:
                    raise VectorError(f'{operation}: private writer bootstrap is missing or not bound to its genesis backup')
            except Exception as error:
                outcome.update(result='failed', error=f'{type(error).__name__}: {error}')
            save()
        report['passed'] = sum(item['result'] == 'passed' for item in report['vectors'])
        report['failed'] = sum(item['result'] == 'failed' for item in report['vectors'])
        report['fullLiveAccepted'] = not args.operation and report['failed'] == 0 and report['passed'] == len(report['coverage'])
        report['result'] = 'passed' if report['fullLiveAccepted'] else 'partial' if not report['failed'] else 'failed'
    except Exception as error:
        report.update(result='failed', error=f'{type(error).__name__}: {error}')
    finally:
        save()
        signal.signal(signal.SIGTERM, previous_handler)
    print(f"{report['result'].upper()}: full live acceptance={report['fullLiveAccepted']}; receipt: {receipt}")
    return 0 if report['result'] in ('passed', 'partial') else 1


if __name__ == '__main__':
    raise SystemExit(main())
