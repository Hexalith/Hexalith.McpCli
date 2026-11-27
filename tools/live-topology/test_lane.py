"""A skipped, empty, stale or failed isolated process cannot grant full acceptance."""
import importlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stderr, redirect_stdout

from live_plans import VectorError, BINDING_KEYS, selection_binding

lane = importlib.import_module('run-vectors')


class LaneTests(unittest.TestCase):
    def test_short_credentials_preserve_a_prior_receipt_and_refuse_a_new_generation(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.dict('os.environ', {'X_TOKEN_TTL': '12'}), \
                redirect_stdout(io.StringIO()) as stdout, redirect_stderr(io.StringIO()) as stderr:
            receipt = Path(directory) / 'live-lane.json'
            previous = '{"result":"passed","fullLiveAccepted":true}\n'
            receipt.write_text(previous)
            self.assertEqual(1, lane.main(['--output', directory, '--preflight-only']))
            self.assertEqual('', stdout.getvalue())
            self.assertIn('Structured evidence requires known environment credentials', stderr.getvalue())
            self.assertEqual([receipt], list(receipt.parent.iterdir()))
            self.assertEqual(previous, receipt.read_text())

    def test_oversized_child_stdout_cannot_supply_an_isolation_receipt(self):
        operation = 'fixture.operation'
        selected = {'operation': operation, **{key: key for key in BINDING_KEYS}}

        def child(_command, _environment, output, _timeout):
            (output / 'tests.xml').write_text(self.xml())
            (output / 'live-result.json').write_text(json.dumps({
                'operation': operation, 'result': 'passed', 'binding': selection_binding(selected)}))
            (output / 'child.stdout.txt').write_bytes(b'x' * 65)
            return 0

        with tempfile.TemporaryDirectory() as directory, \
                patch.dict('os.environ', {'MCPCLI_ISOLATED_RUNTIME_DIR': '/private/test-runtime'}), \
                patch.object(lane, 'expected_operations', return_value=[operation]), \
                patch.object(lane, 'preflight', return_value=[selected]), \
                patch.object(lane, 'require_phases'), \
                patch.object(lane, 'bounded_child', side_effect=child), \
                patch.object(lane, 'OUTPUT_LIMIT', 64):
            self.assertEqual(1, lane.main(['--output', directory]))
            report = json.loads((Path(directory) / 'live-lane.json').read_text())
            self.assertFalse(report['fullLiveAccepted'])
            self.assertIn('isolated child stdout exceeded 64 bytes (65 bytes observed)', report['vectors'][0]['error'])

    def test_full_coverage_cannot_be_inferred_from_returned_preflight_subset(self):
        expected = ['fixture.first', 'fixture.second']
        lane.require_coverage([{'operation': op} for op in expected], expected)
        for selections in [[], [{'operation': 'fixture.second'}],
                           [{'operation': op} for op in expected + ['fixture.first']]]:
            with self.subTest(selections=selections), self.assertRaisesRegex(
                    VectorError, '^Preflight execution selections differ from complete approved live vector coverage\\.$'):
                lane.require_coverage(selections, expected)
        with tempfile.TemporaryDirectory() as directory, \
                patch.dict('os.environ', {'MCPCLI_ISOLATED_RUNTIME_DIR': '/private/test-runtime'}), \
                patch.object(lane, 'expected_operations', return_value=expected), \
                patch.object(lane, 'preflight', return_value=[{'operation': 'fixture.second'}]), \
                patch.object(lane, 'bounded_child') as child:
            self.assertEqual(1, lane.main(['--output', directory]))
            child.assert_not_called()
            self.assertFalse(json.loads((Path(directory) / 'live-lane.json').read_text())['fullLiveAccepted'])

    def test_expected_live_set_is_every_approved_vector_with_a_companion_plan(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            modules = root / 'tools/conformance-vectors/v1/current/modules/Module.Contracts'
            plans = root / 'tools/live-topology/plans-current'
            modules.mkdir(parents=True)
            plans.mkdir(parents=True)
            for name in ['module.write', 'module.read', 'module.loopback-only']:
                (modules / (name + '.vector.json')).write_text(json.dumps({'operation': name}))
            for name in ['module.write', 'module.read']:
                (plans / (name + '.json')).write_text('{}')
            with patch.object(lane, 'ROOT', root):
                self.assertEqual(['module.read', 'module.write'], lane.expected_operations())
                (modules / 'copy.vector.json').write_text(json.dumps({'operation': 'module.read'}))
                with self.assertRaisesRegex(VectorError, '^Approved live vector coverage is empty or duplicated\\.$'):
                    lane.expected_operations()
                for path in plans.glob('*.json'):
                    path.unlink()
                with self.assertRaisesRegex(VectorError, '^Approved live vector coverage is empty or duplicated\\.$'):
                    lane.expected_operations()

    def test_preflight_reports_reach_live_lane_json_and_stderr_without_changing_the_exit_code(self):
        def report_then(result):
            def preflight(host, output, reports):
                reports.extend(['first report', 'second report'])
                if isinstance(result, Exception):
                    raise result
                return result
            return preflight
        for result, code, outcome in [([{'operation': 'fixture.operation'}], 0, 'preflight-only'),
                                      (VectorError('specific preflight failure'), 1, 'failed')]:
            with self.subTest(outcome=outcome), tempfile.TemporaryDirectory() as directory, \
                    patch.object(lane, 'preflight', side_effect=report_then(result)), \
                    patch.object(lane, 'expected_operations', return_value=['fixture.operation']), \
                    patch.object(lane, 'bounded_child') as child, \
                    redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as stderr:
                self.assertEqual(code, lane.main(['--output', directory, '--preflight-only']))
                child.assert_not_called()
                report = json.loads((Path(directory) / 'live-lane.json').read_text())
                self.assertEqual(outcome, report['result'])
                self.assertEqual(['first report', 'second report'], report['reported'])
                self.assertEqual('reported: first report\nreported: second report\n', stderr.getvalue())

    def xml(self, **changes):
        values = dict(total='1', passed='1', failed='0', skipped='0', errors='0', result='Pass', operation='fixture.operation')
        values.update(changes)
        return ('<assemblies><assembly total="{total}" passed="{passed}" failed="{failed}" skipped="{skipped}" errors="{errors}">'
                '<collection><test result="{result}" method="ApprovedVectorHasPersistentSemantics"><traits>'
                '<trait name="Operation" value="{operation}"/></traits></test></collection></assembly></assemblies>').format(**values)

    def test_exactly_one_passing_selected_case_is_required(self):
        for changes in [{}, {'skipped': '1', 'passed': '0', 'result': 'Skip'}, {'total': '0'},
                        {'failed': '1'}, {'errors': '1'}, {'operation': 'wrong'}]:
            with self.subTest(changes=changes), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'tests.xml'
                path.write_text(self.xml(**changes))
                if changes:
                    with self.assertRaises(VectorError): lane.require_case(path, 'fixture.operation')
                else: lane.require_case(path, 'fixture.operation')

    def test_extra_or_empty_results_are_rejected(self):
        for content in ['<assemblies/>', self.xml().replace('</collection>', '<test result="Pass"/></collection>')]:
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'tests.xml'; path.write_text(content)
                with self.assertRaises(VectorError): lane.require_case(path, 'fixture.operation')

    def test_preflight_failure_invalidates_prior_lane_success(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            (output / 'live-lane.json').write_text('{"result":"passed","fullLiveAccepted":true}')
            def refuse_preflight(*_):
                pending = json.loads((output / 'live-lane.json').read_text())
                self.assertEqual('pending', pending['result'])
                self.assertFalse(pending['fullLiveAccepted'])
                self.assertEqual([], pending['vectors'])
                raise VectorError('stale binding')
            with patch.dict('os.environ', {'MCPCLI_ISOLATED_RUNTIME_DIR': '/private/test-runtime'}), \
                    patch.object(lane, 'preflight', side_effect=refuse_preflight) as preflight, \
                    patch.object(lane, 'bounded_child') as child:
                self.assertEqual(1, lane.main(['--output', directory]))
                preflight.assert_called_once()
            result = json.loads((output / 'live-lane.json').read_text())
            self.assertEqual('failed', result['result']); self.assertFalse(result['fullLiveAccepted'])
            child.assert_not_called()

    def test_hard_kill_during_preflight_cannot_leave_previous_success(self):
        import os
        import subprocess
        import sys
        import time
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            (output / 'live-lane.json').write_text('{"result":"passed","fullLiveAccepted":true}')
            script = '''
import importlib.util,pathlib,sys,time
sys.path.insert(0,sys.argv[1])
spec=importlib.util.spec_from_file_location('lane',pathlib.Path(sys.argv[1])/'run-vectors.py')
lane=importlib.util.module_from_spec(spec); spec.loader.exec_module(lane)
def preflight(*args, **kwargs):
 pathlib.Path(sys.argv[2],'blocked').touch()
 time.sleep(60)
lane.preflight=preflight
lane.main(['--output',sys.argv[2],'--preflight-only'])
'''
            process = subprocess.Popen([sys.executable, '-c', script, str(Path(__file__).resolve().parent), directory],
                                       env=os.environ.copy(), stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            try:
                deadline = time.monotonic() + 10
                while not (output / 'blocked').exists() and process.poll() is None and time.monotonic() < deadline:
                    time.sleep(.01)
                self.assertTrue((output / 'blocked').exists())
                process.kill()
                process.communicate(timeout=5)
                pending = json.loads((output / 'live-lane.json').read_text())
                self.assertEqual('pending', pending['result'])
                self.assertFalse(pending['fullLiveAccepted'])
                self.assertEqual([], pending['vectors'])
            finally:
                if process.poll() is None: process.kill()
                process.communicate(timeout=5)

    def test_failed_children_keep_all_operation_outcomes_and_exact_selectors(self):
        with tempfile.TemporaryDirectory() as directory:
            selections = [{'operation': f'fixture.operation-{i}', **{key: key for key in BINDING_KEYS}} for i in range(21)]
            with patch.object(lane, 'preflight', return_value=selections), \
                    patch.object(lane, 'expected_operations', return_value=[item['operation'] for item in selections]), \
                    patch.dict('os.environ', {'MCPCLI_ISOLATED_RUNTIME_DIR': '/private/test-runtime',
                        'MCPCLI_LIVE_TOKEN': 'inherited-token', 'MCPCLI_LIVE_URL': 'http://user-topology/',
                        'MCPCLI_LIVE_UNEXPECTED': 'inherited-value', 'EVENTSTORE_TOKEN': 'user-token',
                        'EVENTSTORE_TENANT': 'user-tenant', 'EVENTSTORE_UNEXPECTED': 'inherited-value'}), \
                    patch.object(lane, 'bounded_child', return_value=1) as child:
                self.assertEqual(1, lane.main(['--output', directory, '--max-failures', '0']))
            self.assertEqual(21, child.call_count)
            for i, call in enumerate(child.call_args_list):
                self.assertIn('Operation=fixture.operation-' + str(i), call.args[0])
                self.assertEqual(1, call.args[0].count('-trait'))
                self.assertEqual('Hexalith.McpCli.Integration.Tests.LiveVectorTests',
                                 call.args[0][call.args[0].index('-class') + 1])
                self.assertEqual('fixture.operation-' + str(i), call.args[1]['MCPCLI_LIVE_OPERATION'])
                self.assertIn('run-isolated.py', call.args[0][1])
                self.assertEqual(str(lane.ROOT / 'tests/Hexalith.McpCli.ConformanceHost/bin/Release/net11.0/Hexalith.McpCli.ConformanceHost.dll'), call.args[1]['MCPCLI_LIVE_HOST'])
                self.assertEqual(selection_binding(selections[i]), json.loads(call.args[1]['MCPCLI_LIVE_BINDING']))
                self.assertEqual({'MCPCLI_LIVE_OPERATION', 'MCPCLI_LIVE_OUTPUT', 'MCPCLI_LIVE_HOST', 'MCPCLI_LIVE_BINDING'},
                                 {key for key in call.args[1] if key.startswith(('MCPCLI_LIVE_', 'EVENTSTORE_'))})
                self.assertEqual('/private/test-runtime', call.args[1]['MCPCLI_ISOLATED_RUNTIME_DIR'])
            result = json.loads((Path(directory) / 'live-lane.json').read_text())
            self.assertEqual(21, result['failed']); self.assertEqual(0, result['passed'])
            self.assertFalse(result['fullLiveAccepted'])

    def test_out_of_range_child_timeout_starts_no_topology(self):
        for timeout in ['0', '961']:
            with self.subTest(timeout=timeout), tempfile.TemporaryDirectory() as directory, \
                    patch.object(lane, 'preflight') as preflight, patch.object(lane, 'bounded_child') as child:
                self.assertEqual(1, lane.main(['--output', directory, '--child-timeout', timeout]))
                preflight.assert_not_called()
                child.assert_not_called()
                report = json.loads((Path(directory) / 'live-lane.json').read_text())
                self.assertEqual('failed', report['result'])
                self.assertIn('--child-timeout must be between 1 and 960 seconds.', report['error'])

    def test_preflight_only_prints_summary_and_never_starts_children(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(lane, 'preflight', return_value=[{'operation': 'fixture.operation'}]), \
                patch.object(lane, 'expected_operations', return_value=['fixture.operation']), \
                patch.object(lane, 'bounded_child') as child, redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(0, lane.main(['--output', directory, '--preflight-only']))
            child.assert_not_called()
            report = json.loads((Path(directory) / 'live-lane.json').read_text())
            self.assertEqual('preflight-only', report['result'])
            self.assertFalse(report['fullLiveAccepted'])
            self.assertEqual(f'PREFLIGHT-ONLY: full live acceptance=False; receipt: {Path(directory) / "live-lane.json"}\n', stdout.getvalue())

    def test_unknown_or_empty_selector_starts_no_topology(self):
        for selector in ['unknown', '']:
            with self.subTest(selector=selector), tempfile.TemporaryDirectory() as directory, \
                    patch.dict('os.environ', {'MCPCLI_ISOLATED_RUNTIME_DIR': '/private/test-runtime'}), \
                    patch.object(lane, 'preflight', return_value=[{'operation': 'fixture.operation'}]), \
                    patch.object(lane, 'expected_operations', return_value=['fixture.operation']), \
                    patch.object(lane, 'bounded_child') as child:
                self.assertEqual(1, lane.main(['--output', directory, '--operation', selector]))
                child.assert_not_called()
                result = json.loads((Path(directory) / 'live-lane.json').read_text())
                self.assertIn('Selector must name exactly one', result['error'])

    def test_missing_runtime_fails_before_preflight_or_child(self):
        for runtime in [None, '', '   ']:
            environment = {} if runtime is None else {'MCPCLI_ISOLATED_RUNTIME_DIR': runtime}
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as directory, \
                    patch.dict('os.environ', environment, clear=True), \
                    patch.object(lane, 'preflight') as preflight, patch.object(lane, 'bounded_child') as child:
                self.assertEqual(1, lane.main(['--output', directory]))
                preflight.assert_not_called()
                child.assert_not_called()
                result = json.loads((Path(directory) / 'live-lane.json').read_text())
                self.assertEqual('failed', result['result'])
                self.assertFalse(result['fullLiveAccepted'])
                self.assertIn('MCPCLI_ISOLATED_RUNTIME_DIR must name a prepared private runtime.', result['error'])

    def test_success_requires_fresh_binding_case_and_owned_cleanup(self):
        for broken in [None, 'selected-subset', 'binding', 'operation', 'semantic-result', 'cleanup', 'cleanup-missing',
                       'child-exit', 'prerequisite', 'bootstrap', 'bootstrap-status', 'bootstrap-count',
                       'bootstrap-ready', 'bootstrap-source', 'bootstrap-interrupted', 'phase-missing', 'phase-duplicated', 'command-repeated', 'command-omitted',
                       'phase-exit', 'backup-missing', 'backup-empty', 'backup-changed', 'backup-header', 'backup-outside',
                       'backup-not-empty', 'backup-not-genesis']:
            with self.subTest(broken=broken), tempfile.TemporaryDirectory() as directory:
                selection = {'operation': 'fixture.operation', **{key: 'bound-' + key for key in
                    BINDING_KEYS}}
                vector = Path(directory) / 'vector.json'
                vector.write_text(json.dumps({'prerequisites': [], 'invocation': {'operation': 'fixture.operation', 'kind': 'command'}, 'postconditions': []}))
                selection.update(vector=vector, plan={'actions': [{'step': '/invocation'}]})
                def child(command, environment, output, timeout):
                    (output / 'tests.xml').write_text(self.xml())
                    binding = selection_binding(selection)
                    if broken == 'binding': binding['planSha256'] = 'stale-plan'
                    phases = [{'head': 'cli', 'phase': '/invocation', 'operation': 'fixture.operation', 'kind': 'command', 'result': 'passed', 'attempts': [{'result': 'passed', 'exitCode': 0}]}]
                    if broken == 'phase-missing': phases = []
                    if broken == 'phase-duplicated': phases *= 2
                    if broken == 'command-repeated': phases[0]['attempts'] *= 2
                    if broken == 'command-omitted': phases[0]['attempts'] = []
                    if broken == 'phase-exit': phases[0]['attempts'][-1]['exitCode'] = 2
                    (output / 'live-result.json').write_text(json.dumps({
                        'operation': 'wrong' if broken == 'operation' else 'fixture.operation',
                        'result': 'failed' if broken == 'semantic-result' else 'passed', 'binding': binding, 'phases': phases}))
                    runtime = output / 'runtime'; runtime.mkdir()
                    backup_file = (output if broken == 'backup-outside' else runtime) / 'initial-empty.rdb'
                    backup_file.write_bytes(b'' if broken == 'backup-empty' else b'not an RDB' if broken == 'backup-header' else b'REDIS0011fixture')
                    backup_hash = hashlib.sha256(backup_file.read_bytes()).hexdigest()
                    if broken == 'backup-missing': backup_file.unlink()
                    if broken == 'backup-changed': backup_file.write_bytes(b'REDIS0011changed')
                    backup = {'sha256': backup_hash, 'backupFile': str(backup_file),
                              'databaseSize': 1 if broken == 'backup-not-empty' else 0,
                              'createdBeforeApplications': broken != 'backup-not-genesis'}
                    stopped = {name: 0 for name in ['sentry', 'redis', 'placement', 'scheduler']}
                    if broken == 'cleanup': stopped['redis'] = None
                    if broken == 'cleanup-missing': del stopped['sentry']
                    (runtime / 'result.json').write_text(json.dumps({'commandExitCode': 1 if broken == 'child-exit' else 0, 'prerequisitesReady': broken != 'prerequisite',
                        'ownedInfrastructureStopped': stopped, 'initialRedisBackup': backup}))
                    (output / 'writer-bootstrap.json').write_text(json.dumps({'result': 'failed' if broken == 'bootstrap-status' else 'passed',
                        'sourceCommit': 'unknown' if broken == 'bootstrap-source' else 'a' * 40,
                        'activationCount': 2 if broken == 'bootstrap-count' else 1, 'readinessObserved': broken != 'bootstrap-ready',
                        'backupReference': 'bad' if broken == 'bootstrap' else 'sha256:' + backup_hash + ';file:' + str(backup_file)}))
                    (output / 'child.stdout.txt').write_text('Isolated run: ' + str(runtime) + '\n')
                    return 0
                read_text = Path.read_text
                def read(path, *args, **kwargs):
                    if broken == 'bootstrap-interrupted' and path.name == 'writer-bootstrap.json':
                        raise SystemExit(143)
                    return read_text(path, *args, **kwargs)
                selections = ([{'operation': 'fixture.first'}, selection] if broken == 'selected-subset' else [selection])
                arguments = ['--output', directory]
                if broken == 'selected-subset': arguments.extend(['--operation', 'fixture.operation'])
                with patch.object(lane, 'preflight', return_value=selections), \
                        patch.object(lane, 'expected_operations', return_value=[item['operation'] for item in selections]), \
                        patch.dict('os.environ', {'MCPCLI_ISOLATED_RUNTIME_DIR': '/private/test-runtime'}), \
                        patch.object(Path, 'read_text', autospec=True, side_effect=read), \
                        patch.object(lane, 'bounded_child', side_effect=child) as process:
                    if broken == 'bootstrap-interrupted':
                        with self.assertRaises(SystemExit):
                            lane.main(arguments)
                    else:
                        self.assertEqual(0 if broken in (None, 'selected-subset') else 1, lane.main(arguments))
                result = json.loads((Path(directory) / 'live-lane.json').read_text())
                self.assertEqual(broken is None, result['fullLiveAccepted'])
                if broken == 'selected-subset':
                    process.assert_called_once()
                    command = process.call_args.args[0]
                    self.assertEqual(1, command.count('-trait'))
                    self.assertEqual('Operation=fixture.operation', command[command.index('-trait') + 1])
                    self.assertEqual('partial', result['result'])
                    self.assertEqual(['fixture.operation'], [item['operation'] for item in result['vectors']])
                if broken == 'bootstrap-interrupted':
                    self.assertNotEqual('passed', result['vectors'][0]['result'])
                if broken and broken.startswith('backup-'):
                    self.assertIn('genesis backup', result['vectors'][0]['error'])

    def test_real_child_deadline_stops_only_its_owned_process_group(self):
        import subprocess
        import os
        import sys
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            command = [sys.executable, '-c', 'import os,time; print(os.getpid(),flush=True); time.sleep(60)']
            self.assertEqual(124, lane.bounded_child(command, os.environ.copy(), output, .2))
            pid = int((output / 'child.stdout.txt').read_text())
            with self.assertRaises(ProcessLookupError): os.kill(pid, 0)

    def test_outer_termination_stops_the_running_session_child_and_never_accepts(self):
        import os
        import signal
        import subprocess
        import sys
        import time
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            script = '''
import importlib.util,pathlib,sys
sys.path.insert(0,sys.argv[1])
spec=importlib.util.spec_from_file_location('lane',pathlib.Path(sys.argv[1])/'run-vectors.py')
lane=importlib.util.module_from_spec(spec); spec.loader.exec_module(lane)
from live_plans import BINDING_KEYS
selection={'operation':'fixture.operation',**{key:key for key in BINDING_KEYS}}
lane.preflight=lambda *args, **kwargs:[selection]
lane.expected_operations=lambda:['fixture.operation']
sleeper=[sys.executable,'-c','import os,pathlib,sys,time; pathlib.Path(sys.argv[1]).write_text(str(os.getpid())); time.sleep(60)',str(pathlib.Path(sys.argv[2])/'child.pid')]
bounded_child=lane.bounded_child
lane.bounded_child=lambda command,environment,output,timeout: bounded_child(sleeper,environment,output,timeout)
lane.main(['--output',sys.argv[2]])
'''
            process = subprocess.Popen([sys.executable, '-c', script, str(Path(__file__).resolve().parent), directory],
                                       env={**os.environ, 'MCPCLI_ISOLATED_RUNTIME_DIR': '/private/test-runtime'},
                                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            pid = None
            try:
                deadline = time.monotonic() + 10
                while not (output / 'child.pid').exists() and process.poll() is None and time.monotonic() < deadline:
                    time.sleep(.01)
                pid = int((output / 'child.pid').read_text())
                process.send_signal(signal.SIGTERM)
                process.communicate(timeout=30)
                self.assertEqual(143, process.returncode)
                with self.assertRaises(ProcessLookupError): os.kill(pid, 0)
                result = json.loads((output / 'live-lane.json').read_text())
                self.assertFalse(result['fullLiveAccepted'])
                self.assertEqual(['fixture.operation'], [item['operation'] for item in result['vectors']])
                self.assertNotIn('passed', [item['result'] for item in result['vectors']])
            finally:
                if process.poll() is None: process.kill()
                process.communicate(timeout=5)
                if pid is not None:
                    try: os.kill(pid, signal.SIGKILL)
                    except ProcessLookupError: pass

    def test_child_selector_lists_exactly_its_operation_case_from_built_tests(self):
        import subprocess
        operations = lane.expected_operations()
        selections = [{'operation': operation, **{key: key for key in BINDING_KEYS}} for operation in operations]
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(lane, 'preflight', return_value=selections), \
                patch.dict('os.environ', {'MCPCLI_ISOLATED_RUNTIME_DIR': '/private/test-runtime'}), \
                patch.object(lane, 'bounded_child', return_value=1) as child:
            self.assertEqual(1, lane.main(['--output', directory, '--max-failures', '0']))
        self.assertEqual(len(operations), child.call_count)
        for operation, call in zip(operations, child.call_args_list):
            with self.subTest(operation=operation):
                # Run the exact isolated selector against the built assembly, listing instead of writing results.
                selector = call.args[0][call.args[0].index('--') + 1:]
                index = selector.index('-result-xml')
                selector[index:index + 2] = ['-list', 'tests']
                listed = subprocess.run(selector, cwd=lane.ROOT, capture_output=True, text=True, timeout=60, check=True)
                self.assertEqual(['Hexalith.McpCli.Integration.Tests.LiveVectorTests.ApprovedVectorHasPersistentSemantics(operation: "' + operation + '")'],
                                 [line for line in listed.stdout.splitlines() if line.startswith('Hexalith.McpCli.Integration.Tests.')])

    def test_explicit_host_selection_is_forwarded_privately_to_child(self):
        with tempfile.TemporaryDirectory() as directory:
            selected_host = Path(directory) / 'custom host.dll'
            selection = {'operation': 'fixture.operation', **{key: key for key in BINDING_KEYS}}
            with patch.object(lane, 'preflight', return_value=[selection]) as preflight, \
                    patch.object(lane, 'expected_operations', return_value=['fixture.operation']), \
                    patch.dict('os.environ', {'MCPCLI_ISOLATED_RUNTIME_DIR': '/private/runtime'}), \
                    patch.object(lane, 'bounded_child', return_value=1) as child:
                self.assertEqual(1, lane.main(['--output', directory, '--host', str(selected_host)]))
            self.assertEqual(selected_host.resolve(), preflight.call_args.args[0])
            self.assertEqual(str(selected_host.resolve()), child.call_args.args[1]['MCPCLI_LIVE_HOST'])
            self.assertEqual(selection_binding(selection), json.loads(child.call_args.args[1]['MCPCLI_LIVE_BINDING']))

    def write_wrapper_receipt(self, output: Path, *, prerequisites_ready: bool = True,
                              error=None, command_exit_code: int = 1, omit_stdout_line: bool = False) -> Path:
        runtime = output / 'runtime'
        runtime.mkdir(exist_ok=True)
        receipt = {'commandExitCode': command_exit_code, 'prerequisitesReady': prerequisites_ready,
                   'ownedInfrastructureStopped': {name: 0 for name in ('sentry', 'redis', 'placement', 'scheduler')}}
        if error is not None:
            receipt['error'] = error
        (runtime / 'result.json').write_text(json.dumps(receipt))
        if not omit_stdout_line:
            (output / 'child.stdout.txt').write_text('Isolated run: ' + str(runtime) + '\n')
        else:
            (output / 'child.stdout.txt').write_text('unshare failed\n')
        return runtime

    def test_negative_max_failures_fails_before_preflight_with_vector_error(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.dict('os.environ', {'MCPCLI_ISOLATED_RUNTIME_DIR': '/private/test-runtime'}), \
                patch.object(lane, 'preflight') as preflight, \
                patch.object(lane, 'bounded_child') as child:
            self.assertEqual(1, lane.main(['--output', directory, '--max-failures', '-1']))
            preflight.assert_not_called()
            child.assert_not_called()
            report = json.loads((Path(directory) / 'live-lane.json').read_text())
            self.assertEqual('failed', report['result'])
            self.assertFalse(report['fullLiveAccepted'])
            self.assertIn('VectorError: --max-failures must be 0 or greater.', report['error'])

    def test_threshold_fail_fast_aborts_after_two_normal_failures_by_default(self):
        with tempfile.TemporaryDirectory() as directory:
            selections = [{'operation': f'fixture.operation-{i}', **{key: key for key in BINDING_KEYS}} for i in range(5)]

            def normal_failure(_command, environment, output, _timeout):
                operation = environment['MCPCLI_LIVE_OPERATION']
                self.write_wrapper_receipt(output, prerequisites_ready=True, command_exit_code=1)
                (output / 'tests.xml').write_text(
                    self.xml(total='1', passed='0', failed='1', skipped='0', errors='0', result='Fail', operation=operation))
                return 1

            with patch.object(lane, 'preflight', return_value=selections), \
                    patch.object(lane, 'expected_operations', return_value=[item['operation'] for item in selections]), \
                    patch.dict('os.environ', {'MCPCLI_ISOLATED_RUNTIME_DIR': '/private/test-runtime'}), \
                    patch.object(lane, 'bounded_child', side_effect=normal_failure) as child:
                self.assertEqual(1, lane.main(['--output', directory]))
            self.assertEqual(2, child.call_count)
            report = json.loads((Path(directory) / 'live-lane.json').read_text())
            self.assertEqual('failed', report['result'])
            self.assertFalse(report['fullLiveAccepted'])
            self.assertTrue(report['failFastTriggered'])
            self.assertIn('--max-failures 2', report['failFastReason'])
            self.assertEqual(0, report['passed'])
            self.assertEqual(2, report['failed'])
            self.assertEqual(3, report['skipped'])
            self.assertEqual(['failed', 'failed', 'skipped-fail-fast', 'skipped-fail-fast', 'skipped-fail-fast'],
                             [item['result'] for item in report['vectors']])

    def test_immediate_fail_fast_aborts_on_timeout_wrapper_or_fixture_init_failure(self):
        modes = ('exit-124', 'wrapper-missing-receipt', 'wrapper-prerequisites-false', 'wrapper-error',
                 'fixture-missing-xml', 'fixture-malformed-xml', 'fixture-unknown-encoding',
                 'fixture-unsupported-encoding', 'fixture-xml-errors')
        encodings = {'fixture-unknown-encoding': 'unknown-encoding', 'fixture-unsupported-encoding': 'cp932'}
        for mode in modes:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                selections = [{'operation': f'fixture.operation-{i}', **{key: key for key in BINDING_KEYS}} for i in range(4)]

                def failing_child(_command, environment, output, _timeout):
                    operation = environment['MCPCLI_LIVE_OPERATION']
                    if mode == 'exit-124':
                        return 124
                    if mode == 'wrapper-missing-receipt':
                        self.write_wrapper_receipt(output, omit_stdout_line=True)
                        return 1
                    if mode == 'wrapper-prerequisites-false':
                        self.write_wrapper_receipt(output, prerequisites_ready=False)
                        return 1
                    if mode == 'wrapper-error':
                        self.write_wrapper_receipt(output, prerequisites_ready=True,
                                                   error={'type': 'RuntimeError', 'message': 'private sentry failed'})
                        return 1
                    self.write_wrapper_receipt(output, prerequisites_ready=True)
                    if mode == 'fixture-missing-xml':
                        return 1
                    if mode == 'fixture-malformed-xml':
                        (output / 'tests.xml').write_text('<assemblies><broken')
                        return 1
                    if mode in encodings:
                        (output / 'tests.xml').write_text(f'<?xml version="1.0" encoding="{encodings[mode]}"?><assemblies/>')
                        return 1
                    if mode == 'fixture-xml-errors':
                        (output / 'tests.xml').write_text(
                            self.xml(total='1', passed='0', failed='0', skipped='0', errors='1', result='Fail', operation=operation))
                        return 1
                    return 1

                with patch.object(lane, 'preflight', return_value=selections), \
                        patch.object(lane, 'expected_operations', return_value=[item['operation'] for item in selections]), \
                        patch.dict('os.environ', {'MCPCLI_ISOLATED_RUNTIME_DIR': '/private/test-runtime'}), \
                        patch.object(lane, 'bounded_child', side_effect=failing_child) as child:
                    self.assertEqual(1, lane.main(['--output', directory]))
                self.assertEqual(1, child.call_count)
                report = json.loads((Path(directory) / 'live-lane.json').read_text())
                self.assertEqual('failed', report['result'])
                self.assertFalse(report['fullLiveAccepted'])
                self.assertTrue(report['failFastTriggered'])
                self.assertIsInstance(report['failFastReason'], str)
                self.assertTrue(report['failFastReason'])
                if mode in encodings:
                    self.assertEqual('fixture.operation-0: fixture initialization failed: malformed tests.xml', report['failFastReason'])
                self.assertEqual(1, report['failed'])
                self.assertEqual(3, report['skipped'])
                self.assertEqual(['failed', 'skipped-fail-fast', 'skipped-fail-fast', 'skipped-fail-fast'],
                                 [item['result'] for item in report['vectors']])

    def test_max_failures_zero_disables_immediate_and_threshold_fail_fast(self):
        with tempfile.TemporaryDirectory() as directory:
            selections = [{'operation': f'fixture.operation-{i}', **{key: key for key in BINDING_KEYS}} for i in range(4)]

            def mixed_failures(_command, environment, output, _timeout):
                op = environment['MCPCLI_LIVE_OPERATION']
                if op.endswith('-0'):
                    return 124
                return 1

            with patch.object(lane, 'preflight', return_value=selections), \
                    patch.object(lane, 'expected_operations', return_value=[item['operation'] for item in selections]), \
                    patch.dict('os.environ', {'MCPCLI_ISOLATED_RUNTIME_DIR': '/private/test-runtime'}), \
                    patch.object(lane, 'bounded_child', side_effect=mixed_failures) as child:
                self.assertEqual(1, lane.main(['--output', directory, '--max-failures', '0']))
            self.assertEqual(4, child.call_count)
            report = json.loads((Path(directory) / 'live-lane.json').read_text())
            self.assertEqual('failed', report['result'])
            self.assertFalse(report['fullLiveAccepted'])
            self.assertFalse(report['failFastTriggered'])
            self.assertIsNone(report['failFastReason'])
            self.assertEqual(4, report['failed'])
            self.assertEqual(0, report['skipped'])

    def test_preflight_only_receipt_initializes_skipped_zero(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(lane, 'preflight', return_value=[{'operation': 'fixture.operation'}]), \
                patch.object(lane, 'expected_operations', return_value=['fixture.operation']), \
                patch.object(lane, 'bounded_child') as child, redirect_stdout(io.StringIO()):
            self.assertEqual(0, lane.main(['--output', directory, '--preflight-only']))
            child.assert_not_called()
            report = json.loads((Path(directory) / 'live-lane.json').read_text())
            self.assertEqual(0, report['skipped'])
            self.assertFalse(report['failFastTriggered'])
            self.assertIsNone(report['failFastReason'])

    def test_immediate_fail_fast_catches_real_xunit_initialize_async_skip_and_incomplete_cleanup(self):
        import os
        import subprocess
        import sys
        for mode in ('real-xunit-initialize-async', 'fail-skips-xml', 'incomplete-cleanup', 'owned-exit-124'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                operations = lane.expected_operations()[:3]
                selections = [{'operation': op, **{key: key for key in BINDING_KEYS}} for op in operations]

                def failing_child(command, environment, output, _timeout):
                    op = environment['MCPCLI_LIVE_OPERATION']
                    if mode == 'real-xunit-initialize-async':
                        self.write_wrapper_receipt(output, prerequisites_ready=True, command_exit_code=1)
                        dotnet_cmd = command[command.index('--') + 1:]
                        child_env = {k: v for k, v in os.environ.items() if k != 'MCPCLI_ISOLATED_TOPOLOGY'}
                        result = subprocess.run(dotnet_cmd, cwd=lane.ROOT, env=child_env,
                                                capture_output=True, text=True, timeout=60)
                        self.assertNotEqual(0, result.returncode)
                        self.assertTrue((output / 'tests.xml').is_file())
                        return result.returncode
                    if mode == 'fail-skips-xml':
                        self.write_wrapper_receipt(output, prerequisites_ready=True, command_exit_code=1)
                        (output / 'tests.xml').write_text(
                            self.xml(total='1', passed='0', failed='1', skipped='1', errors='0', result='Skip', operation=op))
                        return 1
                    if mode == 'incomplete-cleanup':
                        runtime = self.write_wrapper_receipt(output, prerequisites_ready=True, command_exit_code=1)
                        owned = json.loads((runtime / 'result.json').read_text())
                        owned['ownedInfrastructureStopped']['redis'] = None
                        (runtime / 'result.json').write_text(json.dumps(owned))
                        (output / 'tests.xml').write_text(
                            self.xml(total='1', passed='0', failed='1', skipped='0', errors='0', result='Fail', operation=op))
                        return 1
                    if mode == 'owned-exit-124':
                        self.write_wrapper_receipt(output, prerequisites_ready=True, command_exit_code=124)
                        (output / 'tests.xml').write_text(
                            self.xml(total='1', passed='0', failed='1', skipped='0', errors='0', result='Fail', operation=op))
                        return 1
                    return 1

                with patch.object(lane, 'preflight', return_value=selections), \
                        patch.object(lane, 'expected_operations', return_value=operations), \
                        patch.dict('os.environ', {'MCPCLI_ISOLATED_RUNTIME_DIR': '/private/test-runtime'}), \
                        patch.object(lane, 'bounded_child', side_effect=failing_child) as child:
                    self.assertEqual(1, lane.main(['--output', directory]))
                self.assertEqual(1, child.call_count)
                report = json.loads((Path(directory) / 'live-lane.json').read_text())
                self.assertEqual('failed', report['result'])
                self.assertFalse(report['fullLiveAccepted'])
                self.assertTrue(report['failFastTriggered'])
                self.assertEqual(2, report['skipped'])
                self.assertEqual(['failed', 'skipped-fail-fast', 'skipped-fail-fast'],
                                 [item['result'] for item in report['vectors']])
                if mode == 'real-xunit-initialize-async':
                    self.assertIn('fixture initialization failed', report['failFastReason'])
                elif mode == 'fail-skips-xml':
                    self.assertIn('skipped=1', report['failFastReason'])
                elif mode == 'incomplete-cleanup':
                    self.assertIn('incomplete ownedInfrastructureStopped', report['failFastReason'])
                elif mode == 'owned-exit-124':
                    self.assertIn('exit 124', report['failFastReason'])

    def test_max_failures_one_and_non_consecutive_failures_and_final_vector_boundary(self):
        # 1. --max-failures 1 aborts after first normal failure
        with tempfile.TemporaryDirectory() as directory:
            selections = [{'operation': f'fixture.operation-{i}', **{key: key for key in BINDING_KEYS}} for i in range(3)]
            def normal_fail(_command, environment, output, _timeout):
                self.write_wrapper_receipt(output, prerequisites_ready=True, command_exit_code=1)
                (output / 'tests.xml').write_text(
                    self.xml(total='1', passed='0', failed='1', skipped='0', errors='0', result='Fail',
                             operation=environment['MCPCLI_LIVE_OPERATION']))
                return 1
            with patch.object(lane, 'preflight', return_value=selections), \
                    patch.object(lane, 'expected_operations', return_value=[item['operation'] for item in selections]), \
                    patch.dict('os.environ', {'MCPCLI_ISOLATED_RUNTIME_DIR': '/private/test-runtime'}), \
                    patch.object(lane, 'bounded_child', side_effect=normal_fail) as child:
                self.assertEqual(1, lane.main(['--output', directory, '--max-failures', '1']))
            self.assertEqual(1, child.call_count)
            report = json.loads((Path(directory) / 'live-lane.json').read_text())
            self.assertTrue(report['failFastTriggered'])
            self.assertEqual(2, report['skipped'])

        # 2. Non-consecutive failures (fail -> pass -> fail) abort remaining vectors under default --max-failures 2
        with tempfile.TemporaryDirectory() as directory:
            selections = []
            for i in range(4):
                vector = Path(directory) / f'v{i}.json'
                vector.write_text(json.dumps({'prerequisites': [], 'invocation': {'operation': f'fixture.op-{i}', 'kind': 'command'}, 'postconditions': []}))
                selections.append({'operation': f'fixture.op-{i}', 'vector': vector, 'plan': {'actions': [{'step': '/invocation'}]},
                                   **{key: f'bound-{key}' for key in BINDING_KEYS}})
            by_op = {item['operation']: item for item in selections}
            def fail_pass_fail(_command, environment, output, _timeout):
                op = environment['MCPCLI_LIVE_OPERATION']
                if op == 'fixture.op-1':
                    (output / 'tests.xml').write_text(self.xml(operation=op))
                    (output / 'live-result.json').write_text(json.dumps({
                        'operation': op, 'result': 'passed', 'binding': selection_binding(by_op[op]),
                        'phases': [{'head': 'cli', 'phase': '/invocation', 'operation': op, 'kind': 'command',
                                    'result': 'passed', 'attempts': [{'result': 'passed', 'exitCode': 0}]}]}))
                    runtime = self.write_wrapper_receipt(output, prerequisites_ready=True, command_exit_code=0)
                    backup_file = runtime / 'initial-empty.rdb'
                    backup_file.write_bytes(b'REDIS0011fixture')
                    backup_hash = hashlib.sha256(backup_file.read_bytes()).hexdigest()
                    owned = json.loads((runtime / 'result.json').read_text())
                    owned['initialRedisBackup'] = {'sha256': backup_hash, 'backupFile': str(backup_file),
                                                   'databaseSize': 0, 'createdBeforeApplications': True}
                    (runtime / 'result.json').write_text(json.dumps(owned))
                    (output / 'writer-bootstrap.json').write_text(json.dumps({
                        'result': 'passed', 'sourceCommit': 'a' * 40, 'activationCount': 1, 'readinessObserved': True,
                        'backupReference': f'sha256:{backup_hash};file:{backup_file}'}))
                    return 0
                self.write_wrapper_receipt(output, prerequisites_ready=True, command_exit_code=1)
                (output / 'tests.xml').write_text(
                    self.xml(total='1', passed='0', failed='1', skipped='0', errors='0', result='Fail', operation=op))
                return 1
            with patch.object(lane, 'preflight', return_value=selections), \
                    patch.object(lane, 'expected_operations', return_value=[item['operation'] for item in selections]), \
                    patch.dict('os.environ', {'MCPCLI_ISOLATED_RUNTIME_DIR': '/private/test-runtime'}), \
                    patch.object(lane, 'bounded_child', side_effect=fail_pass_fail) as child:
                self.assertEqual(1, lane.main(['--output', directory]))
            self.assertEqual(3, child.call_count)
            report = json.loads((Path(directory) / 'live-lane.json').read_text())
            self.assertTrue(report['failFastTriggered'])
            self.assertEqual(1, report['passed'])
            self.assertEqual(2, report['failed'])
            self.assertEqual(1, report['skipped'])
            self.assertEqual(['failed', 'passed', 'failed', 'skipped-fail-fast'],
                             [item['result'] for item in report['vectors']])

        # 3. Failure on the final vector leaves failFastTriggered=False because zero vectors remain
        with tempfile.TemporaryDirectory() as directory:
            selection = {'operation': 'fixture.only', **{key: key for key in BINDING_KEYS}}
            with patch.object(lane, 'preflight', return_value=[selection]), \
                    patch.object(lane, 'expected_operations', return_value=['fixture.only']), \
                    patch.dict('os.environ', {'MCPCLI_ISOLATED_RUNTIME_DIR': '/private/test-runtime'}), \
                    patch.object(lane, 'bounded_child', return_value=124) as child:
                self.assertEqual(1, lane.main(['--output', directory]))
            self.assertEqual(1, child.call_count)
            report = json.loads((Path(directory) / 'live-lane.json').read_text())
            self.assertEqual('failed', report['result'])
            self.assertFalse(report['fullLiveAccepted'])
            self.assertFalse(report['failFastTriggered'])
            self.assertIsNone(report['failFastReason'])
            self.assertEqual(0, report['skipped'])
