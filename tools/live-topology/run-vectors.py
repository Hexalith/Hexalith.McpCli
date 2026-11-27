#!/usr/bin/env python3
"""Preflight full enrollment, then run each vector in a fresh isolated MTP process."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import uuid
import xml.etree.ElementTree as ET

from live_plans import preflight, require_phases, selection_binding
from evidence_redaction import ShortEvidenceCredentialError, require_evidence_credentials, sanitized
from retained_output import OUTPUT_LIMIT, read_capped
from validate import VectorError, _load_json

ROOT = Path(__file__).resolve().parents[2]


def path_argument(value: str) -> Path:
    """Convert a path option without passing the Path class itself to argparse."""
    return Path(value)


def expected_operations() -> list[str]:
    """Independently require every approved vector that has a companion plan, never a returned subset."""
    plans = ROOT / 'tools/live-topology/plans-current'
    operations = [operation for operation in (_load_json(path)['operation'] for path in
                  (ROOT / 'tools/conformance-vectors/v1/current/modules').rglob('*.vector.json'))
                  if (plans / (operation + '.json')).is_file()]
    if not operations or len(operations) != len(set(operations)):
        raise VectorError('Approved live vector coverage is empty or duplicated.')
    return sorted(operations)


def require_coverage(selections: list[dict], expected: list[str]) -> None:
    """Catch omitted or duplicate execution selections independently of preflight."""
    actual = [item['operation'] for item in selections]
    if sorted(actual) != sorted(expected):
        raise VectorError('Preflight execution selections differ from complete approved live vector coverage.')


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


def verified_backup_reference(backup: dict, run_directory: Path) -> str:
    """Bind acceptance to the owned genesis RDB bytes, not just matching receipt fields."""
    try:
        path = Path(backup['backupFile']).resolve()
        if path.parent != run_directory.resolve():
            raise VectorError('Private genesis backup is outside its isolated run directory.')
        content = path.read_bytes()
    except (KeyError, OSError, TypeError) as error:
        raise VectorError(f'Private genesis backup cannot be read: {error}') from error
    actual = hashlib.sha256(content).hexdigest()
    if backup.get('databaseSize') != 0 or backup.get('createdBeforeApplications') is not True \
            or not content.startswith(b'REDIS') or backup.get('sha256') != actual:
        raise VectorError('Private genesis backup bytes or pre-application evidence do not match its receipt.')
    return f'sha256:{actual};file:{path}'


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


def classify_immediate_fail_fast(output: Path, exit_code: int | None) -> str | None:
    """Return an immediate fail-fast reason for timeouts or wrapper/fixture init failures."""
    if exit_code == 124:
        return 'child process timed out (exit 124)'
    stdout_path = output / 'child.stdout.txt'
    try:
        with stdout_path.open('rb') as stream:
            stdout, omitted = read_capped(stream, OUTPUT_LIMIT)
    except OSError:
        return 'wrapper initialization failed: missing isolated child stdout'
    if stdout is None:
        return f'wrapper initialization failed: isolated child stdout exceeded {OUTPUT_LIMIT} bytes ({omitted} bytes observed)'
    lines = stdout.decode('utf-8', errors='replace').splitlines()
    runs = [Path(line.removeprefix('Isolated run: ')) for line in lines if line.startswith('Isolated run: ')]
    if len(runs) != 1:
        return 'wrapper initialization failed: missing isolated runtime receipt'
    try:
        owned = json.loads((runs[0] / 'result.json').read_text())
    except (OSError, ValueError):
        return 'wrapper initialization failed: missing or unreadable runtime receipt'
    if not isinstance(owned, dict):
        return 'wrapper initialization failed: invalid runtime receipt'
    if owned.get('commandExitCode') == 124:
        return 'child process timed out (exit 124)'
    if owned.get('prerequisitesReady') is not True:
        return 'wrapper initialization failed: prerequisitesReady is not true'
    if owned.get('error'):
        return 'wrapper initialization failed: runtime receipt reported error'
    stopped = owned.get('ownedInfrastructureStopped')
    if (not isinstance(stopped, dict)
            or set(stopped) != {'sentry', 'redis', 'placement', 'scheduler'}
            or any(value is None for value in stopped.values())):
        return 'wrapper initialization failed: incomplete ownedInfrastructureStopped'
    tests_xml = output / 'tests.xml'
    if not tests_xml.is_file():
        return 'fixture initialization failed: missing tests.xml'
    try:
        root = ET.parse(tests_xml).getroot()
    except (OSError, ET.ParseError):
        return 'fixture initialization failed: malformed tests.xml'
    assemblies = root.findall('assembly')
    if len(assemblies) != 1:
        return 'fixture initialization failed: malformed tests.xml'
    errors = assemblies[0].get('errors')
    if errors != '0':
        return f'fixture initialization failed: tests.xml reported errors={errors}'
    skipped = assemblies[0].get('skipped')
    if skipped != '0':
        return f'fixture initialization failed: tests.xml reported skipped={skipped}'
    for failure in root.findall('.//failure'):
        exception_type = failure.get('exception-type') or ''
        message = failure.findtext('message') or ''
        if exception_type == 'Xunit.Sdk.TestPipelineException' or 'threw in InitializeAsync' in message:
            return f'fixture initialization failed: {exception_type or "InitializeAsync"}'
    if not root.findall('.//test'):
        return 'fixture initialization failed: tests.xml recorded no executed test cases'
    return None


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=path_argument, required=True)
    parser.add_argument('--host', type=path_argument, default=ROOT / 'tests/Hexalith.McpCli.ConformanceHost/bin/Release/net11.0/Hexalith.McpCli.ConformanceHost.dll')
    parser.add_argument('--tests', type=path_argument, default=ROOT / 'tests/Hexalith.McpCli.Integration.Tests/bin/Release/net11.0/Hexalith.McpCli.Integration.Tests.dll')
    parser.add_argument('--child-timeout', type=float, default=960)
    parser.add_argument('--max-failures', type=int, default=2,
                        help='Abort remaining vectors after this many failures (0 disables fail-fast).')
    parser.add_argument('--operation', help='Diagnostic subset; never grants full live acceptance.')
    parser.add_argument('--preflight-only', action='store_true')
    args = parser.parse_args(argv)
    try:
        require_evidence_credentials()
    except ShortEvidenceCredentialError as error:
        print(sanitized(f'Live vector lane refused: {error}'), file=sys.stderr)
        return 1
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    report = {'runId': uuid.uuid4().hex, 'result': 'pending', 'fullLiveAccepted': False,
              'skipped': 0, 'failFastTriggered': False, 'failFastReason': None, 'vectors': [], 'reported': []}
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

    def launch(command: list[str], environment: dict, output: Path, outcome: dict) -> int:
        """Record the exact child argv in the receipt, then start that same argv."""
        outcome['command'] = list(command)
        save()
        return bounded_child(command, environment, output, args.child_timeout)

    try:
        if not 1 <= args.child_timeout <= 960:
            raise VectorError('--child-timeout must be between 1 and 960 seconds.')
        if args.max_failures < 0:
            raise VectorError('--max-failures must be 0 or greater.')
        if not args.preflight_only and not os.environ.get('MCPCLI_ISOLATED_RUNTIME_DIR', '').strip():
            raise VectorError('MCPCLI_ISOLATED_RUNTIME_DIR must name a prepared private runtime.')
        try:
            selections = preflight(args.host.resolve(), generation / 'preflight', reports=report['reported'])
        finally:
            # Reports never change the exit code or acceptance.
            for item in report['reported']:
                print(f'reported: {item}', file=sys.stderr)
        report['coverage'] = expected_operations()
        require_coverage(selections, report['coverage'])
        if args.operation is not None:
            selections = [item for item in selections if item['operation'] == args.operation]
            if len(selections) != 1:
                raise VectorError('Selector must name exactly one approved vector Operation.')
        report['vectors'] = [{'operation': item['operation'], 'result': 'not-run'} for item in selections]
        save()
        if args.preflight_only:
            report['result'] = 'preflight-only'
        else:
            fail_fast_triggered = False
            fail_fast_reason = None
            failed_count = 0
            for index, (item, outcome) in enumerate(zip(selections, report['vectors'])):
                operation = item['operation']
                output = generation / operation
                output.mkdir()
                outcome.update(result='running', output=str(output.relative_to(args.output)))
                environment = os.environ.copy()
                for key in list(environment):
                    if key.startswith(('MCPCLI_LIVE_', 'EVENTSTORE_')):
                        del environment[key]
                host = str(args.host.resolve())
                binding = json.dumps(selection_binding(item))
                environment.update(MCPCLI_LIVE_OPERATION=operation, MCPCLI_LIVE_OUTPUT=str(output),
                                   MCPCLI_LIVE_HOST=host, MCPCLI_LIVE_BINDING=binding)
                try:
                    code = launch([sys.executable, str(ROOT / 'tools/live-topology/run-isolated.py'), '--',
                                   'dotnet', str(args.tests.resolve()), '-class', 'Hexalith.McpCli.Integration.Tests.LiveVectorTests',
                                   '-trait', 'Operation=' + operation, '-preEnumerateTheories', '-failSkips', '-result-xml', str(output / 'tests.xml')],
                                  environment, output, outcome)
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
                    with (output / 'child.stdout.txt').open('rb') as stream:
                        stdout, omitted = read_capped(stream, OUTPUT_LIMIT)
                    if stdout is None:
                        raise VectorError(f'{operation}: isolated child stdout exceeded {OUTPUT_LIMIT} bytes ({omitted} bytes observed)')
                    lines = stdout.decode('utf-8', errors='replace').splitlines()
                    runs = [Path(line.removeprefix('Isolated run: ')) for line in lines if line.startswith('Isolated run: ')]
                    if len(runs) != 1:
                        raise VectorError(f'{operation}: missing isolated runtime receipt')
                    owned = json.loads((runs[0] / 'result.json').read_text())
                    if owned.get('commandExitCode') != 0 or not owned.get('prerequisitesReady') \
                            or set(owned.get('ownedInfrastructureStopped', {})) != {'sentry', 'redis', 'placement', 'scheduler'} \
                            or any(value is None for value in owned['ownedInfrastructureStopped'].values()):
                        raise VectorError(f'{operation}: private runtime did not prove successful cleanup')
                    bootstrap = json.loads((output / 'writer-bootstrap.json').read_text())
                    backup = owned.get('initialRedisBackup', {})
                    reference = verified_backup_reference(backup, runs[0])
                    if bootstrap.get('result') != 'passed' or bootstrap.get('activationCount') != 1 \
                            or bootstrap.get('readinessObserved') is not True or bootstrap.get('backupReference') != reference \
                            or len(bootstrap.get('sourceCommit', '')) != 40:
                        raise VectorError(f'{operation}: private writer bootstrap is missing or not bound to its genesis backup')
                    outcome.update(result='passed', isolatedReceipt=str(runs[0] / 'result.json'))
                except Exception as error:
                    outcome.update(result='failed', error=f'{type(error).__name__}: {error}')
                    failed_count += 1
                    if args.max_failures > 0 and index + 1 < len(report['vectors']):
                        immediate = classify_immediate_fail_fast(output, outcome.get('exitCode'))
                        if immediate is not None:
                            fail_fast_triggered = True
                            fail_fast_reason = f'{operation}: {immediate}'
                        elif failed_count >= args.max_failures:
                            fail_fast_triggered = True
                            fail_fast_reason = f'reached --max-failures {args.max_failures} after {operation}'
                        if fail_fast_triggered:
                            report['failFastTriggered'] = True
                            report['failFastReason'] = fail_fast_reason
                            for remaining in report['vectors'][index + 1:]:
                                remaining['result'] = 'skipped-fail-fast'
                            report['skipped'] = sum(entry['result'] == 'skipped-fail-fast' for entry in report['vectors'])
                report['skipped'] = sum(entry['result'] == 'skipped-fail-fast' for entry in report['vectors'])
                save()
                if fail_fast_triggered:
                    break
            report['passed'] = sum(item['result'] == 'passed' for item in report['vectors'])
            report['failed'] = sum(item['result'] == 'failed' for item in report['vectors'])
            report['skipped'] = sum(item['result'] == 'skipped-fail-fast' for item in report['vectors'])
            report['failFastTriggered'] = fail_fast_triggered
            report['failFastReason'] = fail_fast_reason
            report['fullLiveAccepted'] = (
                not args.operation
                and not fail_fast_triggered
                and report['failed'] == 0
                and report['skipped'] == 0
                and report['passed'] == len(report['coverage'])
            )
            report['result'] = (
                'passed' if report['fullLiveAccepted']
                else 'partial' if not report['failed'] and not report['skipped'] and not fail_fast_triggered
                else 'failed'
            )
    except Exception as error:
        report.update(result='failed', error=f'{type(error).__name__}: {error}')
    finally:
        save()
        signal.signal(signal.SIGTERM, previous_handler)
    print(f"{report['result'].upper()}: full live acceptance={report['fullLiveAccepted']}; receipt: {receipt}")
    return 0 if report['result'] in ('passed', 'partial', 'preflight-only') else 1


if __name__ == '__main__':
    raise SystemExit(main())
