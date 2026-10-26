"""Exercise bounded reads and exactly-once write submission without a live service."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import subprocess
import unittest
from unittest.mock import patch

import run_live
from validate import VectorError


class Head:
    def __init__(self, documents):
        self.timeout = 30
        self.calls = []
        self.documents = iter(documents)

    def cli(self, *arguments):
        self.calls.append((arguments, self.timeout))
        document = next(self.documents)
        if 'error' not in document:
            document = {'operation': 'fixture.operation', 'tenant': 'test', **document}
        return (2 if 'error' in document else 0), document


class RunnerTests(unittest.TestCase):
    def call(self, kind='query'):
        return {'operation': 'fixture.operation', 'kind': kind, 'payload': {}, 'envelope': {'tenant': 'test'},
                'expectedGateway': {'body': {'aggregateId': 'approved-id'}},
                'assertions': [{'path': '/document/value', 'operator': 'equals', 'value': 7}]}

    def observe(self, head, call, action=None, values=None, record=None):
        tick = [0]
        def clock(): return tick[0]
        def pause(seconds): tick[0] += seconds
        return run_live.observe(head, call, 'http://127.0.0.1/', action or {}, values if values is not None else {},
                                {'deadlineSeconds': 1, 'pollSeconds': .5},
                                record if record is not None else {'phase': '/invocation', 'attempts': []},
                                clock=clock, pause=pause)

    def test_only_queries_poll_for_persisted_convergence(self):
        head = Head([{'document': {'value': 0}}, {'document': {'value': 7}}])
        self.assertEqual(7, self.observe(head, self.call())['document']['value'])
        self.assertEqual(2, len(head.calls))
        self.assertLessEqual(head.calls[-1][1], .5)
        self.assertEqual(30, head.timeout)

    def test_broken_business_effect_fails_with_phase_operation_and_path(self):
        head = Head([{'document': {'value': 0}}] * 3)
        with self.assertRaisesRegex(VectorError, r'/invocation fixture.operation: read deadline: .*?/document/value'):
            self.observe(head, self.call())
        self.assertEqual(2, len(head.calls))

    def test_missing_persisted_document_deadline_retains_declared_assertion_paths(self):
        head = Head([{'error': {'code': 'gateway_error', 'status': 404}}] * 3)
        call = self.call()
        call['assertions'].append({'path': '/document/id', 'operator': 'equals', 'value': 'missing-entity'})
        with self.assertRaisesRegex(VectorError, r'/invocation fixture.operation: read deadline: .*404') as failure:
            self.observe(head, call)
        self.assertIn('declared assertion paths: ["/document/value", "/document/id"]', str(failure.exception))
        self.assertEqual(2, len(head.calls))

    def test_final_process_timeout_retains_the_semantic_assertion_path(self):
        head = Head([])
        document = {'operation': 'fixture.operation', 'tenant': 'test', 'document': {'value': 0}}
        record = {'phase': '/invocation', 'attempts': []}
        with patch.object(head, 'cli', side_effect=[(0, document), subprocess.TimeoutExpired('dotnet', .5)]):
            with self.assertRaisesRegex(VectorError, r'read deadline: .*?/document/value'):
                self.observe(head, self.call(), record=record)
        self.assertIn('/document/value', record['lastFailure'])
        self.assertIn('timed out', record['lastTimeout'])

    def test_write_failure_is_never_retried(self):
        head = Head([{'document': {'value': 0}}, {'document': {'value': 7}}])
        with self.assertRaisesRegex(VectorError, '/document/value'):
            self.observe(head, self.call('command'))
        self.assertEqual(1, len(head.calls))

    def test_write_acceptance_is_submitted_once(self):
        identifier = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        head = Head([{'status': 'accepted', 'messageId': identifier, 'correlationId': identifier, 'aggregateId': 'approved-id'}])
        call = self.call('command')
        call['assertions'] = [{'path': '/status', 'operator': 'equals', 'value': 'accepted'}]
        self.observe(head, call)
        self.assertEqual(1, len(head.calls))

    def test_command_requires_approved_aggregate_identity(self):
        for aggregate in [None, 'wrong-id']:
            with self.subTest(aggregate=aggregate):
                identifier = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
                document = dict(status='accepted', messageId=identifier, correlationId=identifier)
                if aggregate is not None: document['aggregateId'] = aggregate
                call = self.call('command')
                call['assertions'] = [{'path': '/status', 'operator': 'equals', 'value': 'accepted'}]
                head = Head([document])
                with self.assertRaisesRegex(VectorError, '/aggregateId'):
                    self.observe(head, call)
                self.assertEqual(1, len(head.calls))

    def test_nonretryable_query_error_does_not_poll(self):
        errors = [{'code': 'gateway_error', 'status': status, 'detail': 'Gateway refused the query.'}
                  for status in (400, 401, 403)]
        errors.append({'code': 'validation_failed', 'operation': 'fixture.operation',
                       'violations': [{'path': '/id', 'message': 'Invalid identifier.'}]})
        for error in errors:
            with self.subTest(error=error):
                document = {'error': error}
                head = Head([document])
                record = {'phase': '/invocation', 'attempts': []}
                diagnostic = f'/invocation fixture.operation: CLI exit 2: {document}'
                with self.assertRaises(VectorError) as failure:
                    self.observe(head, self.call(), record=record)
                self.assertEqual(diagnostic, str(failure.exception))
                self.assertEqual(diagnostic, record['lastFailure'])
                self.assertEqual([{'result': 'failed', 'exitCode': 2, 'document': document}], record['attempts'])
                self.assertEqual(1, len(head.calls))

    def test_malformed_cli_output_fails_immediately_even_after_a_converging_poll(self):
        for previous in [None, {'error': {'code': 'gateway_error', 'status': 404}},
                         {'document': {'value': 0}}]:
            with self.subTest(previous=previous):
                head = Head([])
                responses = [] if previous is None else [(2 if 'error' in previous else 0,
                    {'operation': 'fixture.operation', 'tenant': 'test', **previous})]
                responses.append(VectorError('invalid JSON stdout; stderr adapter crashed'))
                record = {'phase': '/invocation', 'attempts': []}
                with patch.object(head, 'cli', side_effect=responses) as cli:
                    with self.assertRaisesRegex(VectorError,
                            '/invocation fixture.operation: invalid JSON stdout; stderr adapter crashed'):
                        self.observe(head, self.call(), record=record)
                self.assertEqual(len(responses), cli.call_count)
                self.assertEqual('failed', record['result'])
                self.assertEqual({'result': 'failed'}, record['attempts'][-1])
                self.assertEqual(30, head.timeout)

    def test_invalid_output_contract_cannot_converge_to_a_later_valid_response(self):
        identifier = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        for kind, defect, message in [('query', 'operation', '/operation or /tenant'),
                                      ('query', 'tenant', '/operation or /tenant'),
                                      ('command', 'operation', '/operation or /tenant'),
                                      ('command', 'tenant', '/operation or /tenant'),
                                      ('query', 'document', '/document is missing'),
                                      ('command', 'messageId', 'invalid accepted identifiers'),
                                      ('command', 'correlationId', '/correlationId differs')]:
            with self.subTest(kind=kind, defect=defect):
                call = self.call(kind)
                # These guards must protect calls even when vector assertions only check acceptance.
                call['assertions'] = []
                valid = dict(operation='fixture.operation', tenant='test', document={'value': 7},
                             status='accepted', aggregateId='approved-id', messageId=identifier,
                             correlationId=identifier)
                document = valid.copy()
                if defect == 'document':
                    del document['document']
                else:
                    document[defect] = ('01ARZ3NDEKTSV4RRFFQ69G5FAW' if defect == 'correlationId' else 'wrong')
                    if defect == 'messageId':
                        document['correlationId'] = document['messageId']
                head = Head([document, valid])
                record = {'phase': '/invocation', 'attempts': []}
                with self.assertRaisesRegex(VectorError, message) as failure:
                    self.observe(head, call, record=record)
                self.assertNotIn('read deadline', str(failure.exception))
                self.assertEqual(1, len(head.calls))
                self.assertEqual('failed', record['result'])
                self.assertEqual([{'result': 'failed', 'exitCode': 0, 'document': document}], record['attempts'])
                self.assertEqual(30, head.timeout)

    def test_actual_returned_cursor_is_captured_and_asserted(self):
        head = Head([{'document': {'value': 7}, 'paging': {'nextCursor': 'signed-real-cursor'}}])
        call = self.call()
        call['assertions'].append({'path': '/paging/nextCursor', 'operator': 'equals', 'value': 'scripted-cursor'})
        values = {}
        self.observe(head, call, {'captures': [{'name': 'cursor', 'path': '/paging/nextCursor', 'type': 'string'}],
                                  'assertionBindings': [{'index': 1, 'capture': 'cursor'}]}, values)
        self.assertEqual('signed-real-cursor', values['cursor'])

    def test_failed_capture_does_not_commit_partial_values(self):
        head = Head([{'document': {'value': 0}, 'paging': {'nextCursor': 'premature'}}] * 3)
        values = {}
        with self.assertRaises(VectorError):
            self.observe(head, self.call(), {'captures': [{'name': 'cursor', 'path': '/paging/nextCursor', 'type': 'string'}]}, values)
        self.assertEqual({}, values)

    def test_failing_preflight_invalidates_receipt_and_redacts_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            (output / 'live-result.json').write_text('{"result":"passed"}')
            with patch.dict('os.environ', {'MCPCLI_ISOLATED_TOPOLOGY': '1', 'MCPCLI_LIVE_TOKEN': 'private-token',
                                          'MCPCLI_LIVE_URL': 'http://127.0.0.1:1234/'}), \
                    patch.object(run_live, 'preflight', side_effect=VectorError(
                        '/invocation fixture.operation: /document/value invalid private-token')), \
                    redirect_stdout(io.StringIO()) as stdout:
                self.assertEqual(1, run_live.main(['--operation', 'fixture.operation', '--output', str(output)]))
            content = (output / 'live-result.json').read_text()
            self.assertNotIn('private-token', content)
            self.assertEqual('failed', json.loads(content)['result'])
            self.assertNotIn('private-token', stdout.getvalue())
            self.assertIn('VectorError: /invocation fixture.operation: /document/value invalid <redacted>', stdout.getvalue())

    def test_successful_main_retains_bound_inputs_and_passing_phases(self):
        from live_plans import BINDING_KEYS
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            vector = output / 'vector.json'
            vector.write_text(json.dumps({'prerequisites': [], 'invocation': self.call('command'), 'postconditions': []}))
            binding = {key: 'bound-' + key for key in BINDING_KEYS}
            selection = {'operation': 'fixture.operation', 'vector': vector,
                         'plan': {'actions': [{'step': '/invocation'}]}, **binding}
            phases = [{'phase': '/invocation', 'operation': 'fixture.operation', 'kind': 'command',
                       'result': 'passed', 'attempts': [{'result': 'passed', 'exitCode': 0}]}]
            def execute(selected, host, url, token, report, *, checkpoint):
                self.assertEqual(selection, selected)
                report['phases'].extend(phases)
                checkpoint()
            with patch.dict('os.environ', {'MCPCLI_ISOLATED_TOPOLOGY': '1', 'MCPCLI_LIVE_TOKEN': 'private-token',
                                          'MCPCLI_LIVE_URL': 'http://127.0.0.1:1234/',
                                          'MCPCLI_LIVE_BINDING': json.dumps(binding)}), \
                    patch.object(run_live, 'preflight', return_value=[selection]), \
                    patch.object(run_live, 'execute', side_effect=execute) as executed:
                self.assertEqual(0, run_live.main(['--operation', 'fixture.operation', '--output', directory]))
            executed.assert_called_once()
            report = json.loads((output / 'live-result.json').read_text())
            self.assertEqual('fixture.operation', report['operation'])
            self.assertEqual('passed', report['result'])
            self.assertEqual(binding, report['binding'])
            self.assertEqual(phases, report['phases'])

    def test_live_entry_guards_fail_before_preflight_or_execution(self):
        valid = {'MCPCLI_ISOLATED_TOPOLOGY': '1', 'MCPCLI_LIVE_TOKEN': 'private-token',
                 'MCPCLI_LIVE_URL': 'http://127.0.0.1:1234/'}
        refused = [('MCPCLI_ISOLATED_TOPOLOGY', None), ('MCPCLI_ISOLATED_TOPOLOGY', '0'),
                   ('MCPCLI_LIVE_TOKEN', ''), ('MCPCLI_LIVE_TOKEN', None), ('MCPCLI_LIVE_TOKEN', '   \t\n'),
                   ('MCPCLI_LIVE_URL', ''), ('MCPCLI_LIVE_URL', 'https://127.0.0.1/'),
                   ('MCPCLI_LIVE_URL', 'http://example.com/'), ('MCPCLI_LIVE_URL', 'http://127.0.0.2/'),
                   ('MCPCLI_LIVE_URL', 'http://user@127.0.0.1/'), ('MCPCLI_LIVE_URL', 'http://user:secret@localhost/'),
                   ('MCPCLI_LIVE_URL', 'http://:secret@localhost/'), ('MCPCLI_LIVE_URL', 'http://@127.0.0.1/'),
                   ('MCPCLI_LIVE_URL', 'http://localhost/?query=value'), ('MCPCLI_LIVE_URL', 'http://[::1]/#fragment')]
        for key, value in refused:
            with self.subTest(key=key, value=value), tempfile.TemporaryDirectory() as directory:
                environment = dict(valid)
                if value is None:
                    del environment[key]
                else:
                    environment[key] = value
                with patch.dict('os.environ', environment, clear=True), \
                        patch.object(run_live, 'preflight') as preflight, patch.object(run_live, 'execute') as execute:
                    self.assertEqual(1, run_live.main(['--operation', 'fixture.operation', '--output', directory]))
                preflight.assert_not_called()
                execute.assert_not_called()
                report = json.loads((Path(directory) / 'live-result.json').read_text())
                self.assertEqual('failed', report['result'])
                self.assertEqual([], report['phases'])


class ExecutionTests(unittest.TestCase):
    def selection(self, operation='parties.deactivate-party'):
        from live_plans import ROOT, load_plan
        vector = next(path for path in (ROOT / 'tools/conformance-vectors/v1/modules').rglob('*.vector.json')
                      if json.loads(path.read_text())['operation'] == operation)
        plan = load_plan(ROOT / 'tools/live-topology/plans' / (operation + '.json'), vector)
        return {'operation': operation, 'vector': vector, 'plan': plan}

    @staticmethod
    def put(document, pointer, value):
        tokens = pointer[1:].split('/')
        parent = document
        for i, token in enumerate(tokens[:-1]):
            key = int(token) if isinstance(parent, list) else token
            container = [] if tokens[i + 1].isdigit() else {}
            if isinstance(parent, list):
                while len(parent) <= key: parent.append({})
            if key not in parent if isinstance(parent, dict) else parent[key] is None:
                parent[key] = container
            parent = parent[key]
        key = int(tokens[-1]) if isinstance(parent, list) else tokens[-1]
        if isinstance(parent, list):
            while len(parent) <= key: parent.append({})
        parent[key] = value

    def documents(self, selection):
        from live_plans import _load_json, _steps
        import copy
        steps = dict(_steps(_load_json(selection['vector'])))
        documents, calls = [], []
        command = 0
        for action in selection['plan']['actions']:
            call = steps[action['step']] if 'step' in action else action['query']
            calls.append(call)
            document = {'operation': call['operation'], 'tenant': call['envelope']['tenant']}
            if call['kind'] == 'command':
                command += 1
                identifier = str(command).zfill(26)
                document.update(status='accepted', aggregateId=call['expectedGateway']['body']['aggregateId'],
                                messageId=identifier, correlationId=call['envelope'].get('correlationId', identifier))
            else:
                document['document'] = {}
                response = call.get('scriptedResponse', {}).get('body', {})
                if 'payload' in response: document['document'] = copy.deepcopy(response['payload'])
                paging = response.get('metadata', {}).get('paging')
                if paging is not None: document['paging'] = copy.deepcopy(paging)
            for assertion in call['assertions']:
                if assertion['operator'] == 'exists' and assertion['value'] is False:
                    continue
                present, _ = run_live._pointer(document, assertion['path'])
                if present:
                    continue
                value = assertion['value']
                if assertion['operator'] == 'arrayLength': value = [{} for _ in range(value)]
                elif assertion['operator'] == 'contains': value = [value]
                elif assertion['operator'] == 'exists': value = 'present'
                self.put(document, assertion['path'], value)
            for capture in action.get('captures', []):
                self.put(document, capture['path'], '2026-01-01T00:00:00Z' if capture['type'] == 'timestamp' else 'real-cursor')
            documents.append(document)
        return calls, documents

    def execute(self, selection, documents, report=None, *, validation=None):
        head = Head(documents)
        head.env = {}
        head.allow_extensions = lambda _: None
        report = report if report is not None else {'phases': []}
        original = run_live.observe
        tick = [0]
        def pause(seconds): tick[0] += seconds
        def observe(*args, **kwargs):
            return original(*args, **kwargs, clock=lambda: tick[0], pause=pause)
        with patch.object(run_live, 'HeadProcess', return_value=head), \
                patch.object(run_live, 'validate_call', side_effect=validation) as validate, \
                patch.object(run_live, 'observe', side_effect=observe):
            run_live.execute(selection, Path('/selected/host.dll'), 'http://127.0.0.1/', 'private-token', report)
        self.assertEqual(len(selection['plan']['actions']), validate.call_count)
        for checked, phase in zip(validate.call_args_list, report['phases']):
            self.assertIs(head, checked.args[0])
            self.assertEqual(phase['resolvedCall'], {key: checked.args[1][key] for key in phase['resolvedCall']})
        return head, report

    def test_dynamic_cursor_and_audit_windows_reach_cli_and_actual_core_validation(self):
        from live_plans import HeadProcess, ROOT, validate_call
        host = ROOT / 'tests/Hexalith.McpCli.ConformanceHost/bin/Release/net10.0/Hexalith.McpCli.ConformanceHost.dll'
        first = '2026-10-20T12:34:56.123456+00:00'
        last = '2026-10-20T12:35:57.654321+00:00'
        for operation in ['tenants.get-tenant-users', 'tenants.get-tenant-audit']:
            with self.subTest(operation=operation), tempfile.TemporaryDirectory() as home:
                selection = self.selection(operation)
                _, documents = self.documents(selection)
                actions = selection['plan']['actions']
                for action, document in zip(actions, documents):
                    for capture in action.get('captures', []):
                        value = {'continuation': 'signed-cursor-from-live-result',
                                 'firstTime': first, 'lastTime': last}[capture['name']]
                        self.put(document, capture['path'], value)
                core = HeadProcess(host, home, 30)
                def validate(_, call):
                    validate_call(core, call)
                head, report = self.execute(selection, documents, validation=validate)
                indices = {action.get('step', action.get('label')): index for index, action in enumerate(actions)}
                continuation = head.calls[indices['/postconditions/0']][0][0]
                self.assertEqual('signed-cursor-from-live-result', continuation[continuation.index('--cursor') + 1])
                if operation == 'tenants.get-tenant-audit':
                    expected = {'time-upper-inclusive': ('To', first), 'time-lower-inclusive': ('From', last),
                                'time-before-first': ('To', '2026-10-20T12:34:56.122456+00:00'),
                                'time-after-last': ('From', '2026-10-20T12:35:57.655321+00:00')}
                    for phase, (field, value) in expected.items():
                        arguments = head.calls[indices[phase]][0][0]
                        payload = json.loads(arguments[arguments.index('--payload') + 1])
                        self.assertEqual(value, payload[field], phase)

    def test_resolved_core_refusal_prevents_that_phase_from_reaching_cli(self):
        from live_plans import HeadProcess, ROOT, validate_call
        selection = self.selection('tenants.get-tenant-audit')
        _, documents = self.documents(selection)
        action = next(item for item in selection['plan']['actions'] if item.get('label') == 'time-upper-inclusive')
        action['query']['payload']['UnexpectedProperty'] = True
        rejected_index = selection['plan']['actions'].index(action)
        report = {'phases': []}
        host = ROOT / 'tests/Hexalith.McpCli.ConformanceHost/bin/Release/net10.0/Hexalith.McpCli.ConformanceHost.dll'
        with tempfile.TemporaryDirectory() as home:
            core = HeadProcess(host, home, 30)
            def validate(_, call):
                validate_call(core, call)
            with self.assertRaisesRegex(VectorError, 'resolved Core compatibility failed'):
                self.execute(selection, documents, report, validation=validate)
        self.assertEqual(rejected_index + 1, len(report['phases']))
        self.assertEqual('failed', report['phases'][-1]['result'])
        self.assertEqual([], report['phases'][-1]['attempts'])

    def test_every_vector_submits_each_declared_command_once_at_executor_boundary(self):
        from live_plans import ROOT, require_phases
        for path in sorted((ROOT / 'tools/live-topology/plans').glob('*.json')):
            operation = json.loads(path.read_text())['operation']
            with self.subTest(operation=operation):
                selection = self.selection(operation)
                calls, documents = self.documents(selection)
                head, report = self.execute(selection, documents)
                self.assertEqual(len(calls), len(head.calls))
                require_phases(selection, report['phases'])
                commands = [call for call in calls if call['kind'] == 'command']
                actual = [phase for phase in report['phases'] if phase['kind'] == 'command']
                self.assertEqual([call['operation'] for call in commands], [phase['operation'] for phase in actual])
                self.assertTrue(all(len(phase['attempts']) == 1 for phase in actual))

    def test_intentional_repeated_noop_is_submitted_and_only_delayed_reads_repeat(self):
        from live_plans import require_phases
        selection = self.selection()
        calls, documents = self.documents(selection)
        delayed = dict(documents[1], document={})
        head, report = self.execute(selection, [documents[0], delayed, *documents[1:]])
        self.assertEqual(len(calls) + 1, len(head.calls))
        commands = [phase for phase in report['phases'] if phase['kind'] == 'command']
        self.assertEqual(['parties.create-party', 'parties.deactivate-party', 'parties.deactivate-party'],
                         [phase['operation'] for phase in commands])
        self.assertTrue(all(len(phase['attempts']) == 1 for phase in commands))
        self.assertEqual(2, len(report['phases'][1]['attempts']))
        require_phases(selection, report['phases'])

    def test_parties_offset_probes_reject_a_server_that_repeats_the_first_page(self):
        for operation in ['parties.list-parties', 'parties.search-parties']:
            with self.subTest(operation=operation):
                selection = self.selection(operation)
                calls, documents = self.documents(selection)
                invocation_index = next(i for i, action in enumerate(selection['plan']['actions'])
                                        if action.get('step') == '/invocation')
                probe_index = next(i for i, call in enumerate(calls) if call['envelope'].get('offset') == 2)
                probe, invocation = calls[probe_index], calls[invocation_index]
                self.assertEqual(invocation['payload'], probe['payload'])
                self.assertEqual({**invocation['envelope'], 'offset': 2, 'pageSize': 2}, probe['envelope'])
                repeated = {**documents[probe_index], 'document': documents[invocation_index]['document']}
                report = {'phases': []}
                with self.assertRaisesRegex(VectorError, 'offset-after-only-match .*?/document/items'):
                    self.execute(selection, documents[:probe_index] + [repeated] * 91, report)
                self.assertEqual('failed', report['phases'][-1]['result'])

    def test_reused_message_identity_fails_repeated_noop_phase(self):
        selection = self.selection()
        calls, documents = self.documents(selection)
        indices = [i for i, call in enumerate(calls) if call['kind'] == 'command']
        documents[indices[-1]]['messageId'] = documents[indices[-2]]['messageId']
        report = {'phases': []}
        with self.assertRaisesRegex(VectorError, '/messageId was reused'):
            self.execute(selection, documents, report)
        self.assertEqual('failed', report['phases'][-1]['result'])

    def test_ordinary_failed_observation_marks_its_phase_failed(self):
        selection = self.selection()
        _, documents = self.documents(selection)
        report = {'phases': []}
        with self.assertRaisesRegex(VectorError, 'CLI exit 2'):
            self.execute(selection, [documents[0], {'error': {'code': 'gateway_error', 'status': 403}}], report)
        self.assertEqual('passed', report['phases'][0]['result'])
        self.assertEqual('failed', report['phases'][1]['result'])
        self.assertEqual('failed', report['phases'][1]['attempts'][0]['result'])

    def test_parent_binding_mismatch_never_reaches_execute(self):
        from live_plans import BINDING_KEYS
        for changed in BINDING_KEYS:
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as directory:
                binding = {key: 'parent-' + key for key in BINDING_KEYS}
                selected = {'operation': 'fixture.operation', **binding, changed: 'valid-new-identity'}
                with patch.dict('os.environ', {'MCPCLI_ISOLATED_TOPOLOGY': '1', 'MCPCLI_LIVE_TOKEN': 'private-token',
                                              'MCPCLI_LIVE_URL': 'http://127.0.0.1:1234/', 'MCPCLI_LIVE_BINDING': json.dumps(binding)}), \
                        patch.object(run_live, 'preflight', return_value=[selected]), patch.object(run_live, 'execute') as execute:
                    self.assertEqual(1, run_live.main(['--operation', 'fixture.operation', '--output', directory]))
                execute.assert_not_called()
                self.assertIn('parent preflight binding', json.loads((Path(directory) / 'live-result.json').read_text())['error'])

    def test_hard_termination_retains_prior_phases_and_sanitized_inflight_attempt(self):
        import os
        import sys
        import time
        from live_plans import ROOT, BINDING_KEYS
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            binding = {key: key for key in BINDING_KEYS}
            script = '''
import json,os,pathlib,sys,time
sys.path.insert(0, sys.argv[1])
import run_live
from live_plans import _load_json,_steps
vector=pathlib.Path(sys.argv[2]); plan=json.loads(pathlib.Path(sys.argv[3]).read_text())
selection=dict(operation='parties.deactivate-party',vector=vector,plan=plan,**json.loads(os.environ['MCPCLI_LIVE_BINDING']))
run_live.preflight=lambda *a,**k:[selection]
run_live.validate_call=lambda *a:None
class Head:
 def __init__(self,*a): self.env={}; self.timeout=30; self.count=0
 def allow_extensions(self,*a): pass
 def cli(self,*a):
  self.count+=1
  if self.count>1:
   pathlib.Path(sys.argv[4],'blocked').touch()
   time.sleep(60)
  call=dict(_steps(_load_json(vector)))['/prerequisites/0']
  return 0,dict(operation=call['operation'],tenant=call['envelope']['tenant'],status='accepted',aggregateId=call['expectedGateway']['body']['aggregateId'],messageId='0'*25+'1',correlationId=call['envelope']['correlationId'],note=os.environ['MCPCLI_LIVE_TOKEN'])
run_live.HeadProcess=Head
sys.exit(run_live.main(['--operation','parties.deactivate-party','--output',sys.argv[4]]))
'''
            selection = self.selection()
            environment = os.environ.copy()
            environment.update(MCPCLI_ISOLATED_TOPOLOGY='1', MCPCLI_LIVE_URL='http://127.0.0.1:1234/',
                               MCPCLI_LIVE_TOKEN='private-kill-token', MCPCLI_LIVE_BINDING=json.dumps(binding))
            process = subprocess.Popen([sys.executable, '-c', script, str(ROOT / 'tools/live-topology'),
                                        str(selection['vector']), str(ROOT / 'tools/live-topology/plans/parties.deactivate-party.json'), directory],
                                       env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            try:
                deadline = time.monotonic() + 10
                while not (output / 'blocked').exists() and process.poll() is None and time.monotonic() < deadline:
                    time.sleep(.01)
                self.assertTrue((output / 'blocked').exists())
                process.kill(); process.communicate(timeout=5)
                raw = (output / 'live-result.json').read_text()
                self.assertNotIn('private-kill-token', raw)
                report = json.loads(raw)
                self.assertEqual('passed', report['phases'][0]['result'])
                self.assertEqual('running', report['phases'][1]['result'])
                self.assertEqual(1, len(report['phases'][1]['attempts']))
            finally:
                if process.poll() is None: process.kill()
                process.communicate(timeout=5)
