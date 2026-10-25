#!/usr/bin/env python3
"""Execute one approved vector once through the production CLI against a private live topology."""
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

from live_plans import ROOT, preflight, require_phases, resolve, selection_binding, typed, validate_call
from run_loopback import HeadProcess, _assert_result, _call_args, _pointer, _steps
from validate import VectorError, _load_json


def observe(head: HeadProcess, call: dict, url: str, action: dict, values: dict, plan: dict,
            record: dict, *, clock=time.monotonic, pause=time.sleep, checkpoint=lambda: None) -> dict:
    """Submit writes once. Only reads may converge, within an independent hard deadline."""
    deadline = clock() + plan['deadlineSeconds']
    last_failure = None
    assertion_paths = json.dumps([assertion['path'] for assertion in call['assertions']])
    while True:
        remaining = deadline - clock()
        if remaining <= 0:
            raise VectorError(f"{record['phase']} {call['operation']}: read deadline: {last_failure}; declared assertion paths: {assertion_paths}")
        original_timeout = head.timeout
        head.timeout = min(original_timeout, remaining)
        attempt = {'result': 'running'}
        record['attempts'].append(attempt)
        checkpoint()
        try:
            arguments, _, _ = _call_args(call)
            code, document = head.cli(arguments, url, call['envelope']['tenant'], call['envelope'].get('actor'))
            attempt.update(exitCode=code, document=document)
            checkpoint()
            if code != 0 or 'error' in document:
                raise VectorError(f"{record['phase']} {call['operation']}: CLI exit {code}: {document}")
            if document.get('operation') != call['operation'] or document.get('tenant') != call['envelope']['tenant']:
                raise VectorError(f"{record['phase']} {call['operation']}: /operation or /tenant does not match the submitted call")
            if call['kind'] == 'query' and 'document' not in document:
                raise VectorError(f"{record['phase']} {call['operation']}: /document is missing")
            captured = values.copy()
            for capture in action.get('captures', []):
                present, value = _pointer(document, capture['path'])
                if not present:
                    raise VectorError(f"{record['phase']} {call['operation']}: capture missing at {capture['path']}")
                captured[capture['name']] = typed(value, capture['type'])
            assertions = copy.deepcopy(call['assertions'])
            for binding in action.get('assertionBindings', []):
                assertions[binding['index']]['value'] = captured[binding['capture']]
            for assertion in assertions:
                _assert_result(document, assertion, f"{record['phase']} {call['operation']}")
            if call['kind'] == 'command':
                from run_loopback import ULID
                if document.get('status') != 'accepted':
                    raise VectorError(f"{record['phase']} {call['operation']}: /status is not accepted")
                if document.get('aggregateId') != call['expectedGateway']['body']['aggregateId']:
                    raise VectorError(f"{record['phase']} {call['operation']}: /aggregateId differs from approved Gateway identity")
                if not ULID.fullmatch(document.get('messageId', '')) or not ULID.fullmatch(document.get('correlationId', '')):
                    raise VectorError(f"{record['phase']} {call['operation']}: invalid accepted identifiers")
                expected = call['envelope'].get('correlationId', document['messageId'])
                if document['correlationId'] != expected:
                    raise VectorError(f"{record['phase']} {call['operation']}: /correlationId differs from submitted/default identity")
            values.update(captured)
            attempt['result'] = 'passed'
            record['result'] = 'passed'
            checkpoint()
            return document
        except (VectorError, subprocess.TimeoutExpired) as error:
            attempt['result'] = 'failed'
            if not isinstance(error, subprocess.TimeoutExpired) or last_failure is None:
                last_failure = str(error)
            else:
                record['lastTimeout'] = str(error)
            record['lastFailure'] = last_failure
            checkpoint()
            if call['kind'] == 'command':
                record['result'] = 'failed'
                checkpoint()
                raise
            # Authentication and Core refusals do not represent projection convergence.
            if 'document' in locals() and 'error' in document \
                    and (document['error'].get('code') != 'gateway_error'
                         or document['error'].get('status') in (400, 401, 403)):
                raise
            remaining = deadline - clock()
            if remaining <= 0:
                raise VectorError(f"{record['phase']} {call['operation']}: read deadline: {last_failure}; declared assertion paths: {assertion_paths}") from error
            pause(min(plan['pollSeconds'], remaining))
        finally:
            head.timeout = original_timeout


def execute(selection: dict, host: Path, url: str, token: str, report: dict, *, checkpoint=lambda: None) -> None:
    vector = _load_json(selection['vector'])
    steps = dict(_steps(vector))
    values = {}
    message_ids = set()
    with tempfile.TemporaryDirectory(prefix='mcpcli-live-home-') as home:
        head = HeadProcess(host, home, 30)
        # Private inherited environment, never command-line arguments or receipts.
        head.env['EVENTSTORE_TOKEN'] = token
        head.allow_extensions({key for step in steps.values() for key in step['envelope'].get('extensions', {})})
        for index, action in enumerate(selection['plan']['actions']):
            phase = action.get('step', action.get('label'))
            call = steps[action['step']] if 'step' in action else action['query']
            call = resolve(call, action.get('bindings', []), values)
            record = {'phase': phase, 'operation': call['operation'], 'kind': call['kind'],
                      'resolvedCall': {key: call[key] for key in ('operation', 'kind', 'payload', 'envelope')},
                      'result': 'running', 'attempts': []}
            report['phases'].append(record)
            checkpoint()
            # Validate every resolved dynamic call again before it can reach the live Gateway.
            try:
                validate_call(head, call)
                document = observe(head, call, url, action, values, selection['plan'], record, checkpoint=checkpoint)
                if call['kind'] == 'command':
                    if document['messageId'] in message_ids:
                        raise VectorError(f'{phase} {call["operation"]}: /messageId was reused across Command phases')
                    message_ids.add(document['messageId'])
            except Exception as error:
                record.update(result='failed', error=f'{type(error).__name__}: {error}')
                checkpoint()
                raise
            report['captures'] = values.copy()
            checkpoint()
    report['captures'] = values


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--operation', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--host', type=Path, default=ROOT / 'tests/Hexalith.McpCli.ConformanceHost/bin/Release/net10.0/Hexalith.McpCli.ConformanceHost.dll')
    args = parser.parse_args(argv)
    args.output.mkdir(parents=True, exist_ok=True)
    report = {'operation': args.operation, 'result': 'pending', 'phases': []}
    receipt = args.output / 'live-result.json'
    token = os.environ.get('MCPCLI_LIVE_TOKEN', '')
    def save():
        content = json.dumps(report, indent=2)
        temporary = receipt.with_suffix('.tmp')
        temporary.write_text((content.replace(token, '<redacted>') if token else content) + '\n')
        temporary.replace(receipt)
    save()
    try:
        if os.environ.get('MCPCLI_ISOLATED_TOPOLOGY') != '1':
            raise VectorError('Live execution requires the isolated topology wrapper.')
        url = os.environ.get('MCPCLI_LIVE_URL', '')
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if parsed.scheme != 'http' or parsed.hostname not in ('localhost', '127.0.0.1', '::1') \
                or parsed.username is not None or parsed.password is not None or parsed.query or parsed.fragment or not token:
            raise VectorError('Private discovered loopback endpoint and short-lived identity are required.')
        selections = preflight(args.host.resolve(), args.output / 'preflight', operation=args.operation)
        selected = [item for item in selections if item['operation'] == args.operation]
        if len(selected) != 1:
            raise VectorError('Exactly one approved Operation must be selected.')
        report['binding'] = selection_binding(selected[0])
        expected = json.loads(os.environ.get('MCPCLI_LIVE_BINDING', 'null'))
        if expected != report['binding']:
            raise VectorError('Selected live inputs differ from the parent preflight binding.')
        report['result'] = 'running'
        save()
        execute(selected[0], args.host.resolve(), url, token, report, checkpoint=save)
        require_phases(selected[0], report['phases'])
        report['result'] = 'passed'
    except Exception as error:
        report.update(result='failed', error=f'{type(error).__name__}: {error}')
    finally:
        # Defensive redaction covers adapter errors as well as ordinary result documents.
        save()
    print(f"{report['result'].upper()} {args.operation}; receipt: {receipt}")
    return 0 if report['result'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
