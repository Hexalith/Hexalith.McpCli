"""A skipped, empty, stale or failed isolated process cannot grant full acceptance."""
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout

from live_plans import VectorError, BINDING_KEYS, selection_binding

spec = importlib.util.spec_from_file_location('run_vectors', Path(__file__).with_name('run-vectors.py'))
lane = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lane)


class LaneTests(unittest.TestCase):
    def test_full_coverage_cannot_be_inferred_from_returned_preflight_subset(self):
        expected = ['fixture.first', 'fixture.second']
        lane.require_coverage([{'operation': op} for op in expected], expected)
        for selections in [[], [{'operation': 'fixture.second'}],
                           [{'operation': op} for op in expected + ['fixture.first']]]:
            with self.subTest(selections=selections), self.assertRaisesRegex(VectorError, 'complete approved vector coverage'):
                lane.require_coverage(selections, expected)
        with tempfile.TemporaryDirectory() as directory, \
                patch.dict('os.environ', {'MCPCLI_ISOLATED_RUNTIME_DIR': '/private/test-runtime'}), \
                patch.object(lane, 'expected_operations', return_value=expected), \
                patch.object(lane, 'preflight', return_value=[{'operation': 'fixture.second'}]), \
                patch.object(lane, 'bounded_child') as child:
            self.assertEqual(1, lane.main(['--output', directory]))
            child.assert_not_called()
            self.assertFalse(json.loads((Path(directory) / 'live-lane.json').read_text())['fullLiveAccepted'])

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
            with patch.dict('os.environ', {'MCPCLI_ISOLATED_RUNTIME_DIR': '/private/test-runtime'}), \
                    patch.object(lane, 'preflight', side_effect=VectorError('stale binding')) as preflight, \
                    patch.object(lane, 'bounded_child') as child:
                self.assertEqual(1, lane.main(['--output', directory]))
                preflight.assert_called_once()
            result = json.loads((output / 'live-lane.json').read_text())
            self.assertEqual('failed', result['result']); self.assertFalse(result['fullLiveAccepted'])
            child.assert_not_called()

    def test_failed_children_keep_all_operation_outcomes_and_exact_selectors(self):
        with tempfile.TemporaryDirectory() as directory:
            selections = [{'operation': f'fixture.operation-{i}', **{key: key for key in BINDING_KEYS}} for i in range(21)]
            with patch.object(lane, 'preflight', return_value=selections), \
                    patch.object(lane, 'expected_operations', return_value=[item['operation'] for item in selections]), \
                    patch.dict('os.environ', {'MCPCLI_ISOLATED_RUNTIME_DIR': '/private/test-runtime'}), \
                    patch.object(lane, 'bounded_child', return_value=1) as child:
                self.assertEqual(1, lane.main(['--output', directory]))
            self.assertEqual(21, child.call_count)
            for i, call in enumerate(child.call_args_list):
                self.assertIn('Operation=fixture.operation-' + str(i), call.args[0])
                self.assertEqual(1, call.args[0].count('-trait'))
                self.assertEqual('Hexalith.McpCli.Integration.Tests.LiveVectorTests',
                                 call.args[0][call.args[0].index('-class') + 1])
                self.assertEqual('fixture.operation-' + str(i), call.args[1]['MCPCLI_LIVE_OPERATION'])
                self.assertIn('run-isolated.py', call.args[0][1])
                self.assertEqual(str(lane.ROOT / 'tests/Hexalith.McpCli.ConformanceHost/bin/Release/net10.0/Hexalith.McpCli.ConformanceHost.dll'), call.args[1]['MCPCLI_LIVE_HOST'])
                self.assertEqual(selection_binding(selections[i]), json.loads(call.args[1]['MCPCLI_LIVE_BINDING']))
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
                       'bootstrap-ready', 'bootstrap-source', 'bootstrap-interrupted', 'phase-missing', 'phase-duplicated', 'command-repeated', 'command-omitted']:
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
                    phases = [{'phase': '/invocation', 'operation': 'fixture.operation', 'kind': 'command', 'result': 'passed', 'attempts': [{'result': 'passed', 'exitCode': 0}]}]
                    if broken == 'phase-missing': phases = []
                    if broken == 'phase-duplicated': phases *= 2
                    if broken == 'command-repeated': phases[0]['attempts'] *= 2
                    if broken == 'command-omitted': phases[0]['attempts'] = []
                    (output / 'live-result.json').write_text(json.dumps({
                        'operation': 'wrong' if broken == 'operation' else 'fixture.operation',
                        'result': 'failed' if broken == 'semantic-result' else 'passed', 'binding': binding, 'phases': phases}))
                    runtime = output / 'runtime'; runtime.mkdir()
                    stopped = {name: 0 for name in ['sentry', 'redis', 'placement', 'scheduler']}
                    if broken == 'cleanup': stopped['redis'] = None
                    if broken == 'cleanup-missing': del stopped['sentry']
                    (runtime / 'result.json').write_text(json.dumps({'commandExitCode': 1 if broken == 'child-exit' else 0, 'prerequisitesReady': broken != 'prerequisite',
                        'ownedInfrastructureStopped': stopped, 'initialRedisBackup': {'sha256': 'genesis-hash', 'backupFile': '/private/initial-empty.rdb'}}))
                    (output / 'writer-bootstrap.json').write_text(json.dumps({'result': 'failed' if broken == 'bootstrap-status' else 'passed',
                        'sourceCommit': 'unknown' if broken == 'bootstrap-source' else 'a' * 40,
                        'activationCount': 2 if broken == 'bootstrap-count' else 1, 'readinessObserved': broken != 'bootstrap-ready',
                        'backupReference': 'bad' if broken == 'bootstrap' else 'sha256:genesis-hash;file:/private/initial-empty.rdb'}))
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
