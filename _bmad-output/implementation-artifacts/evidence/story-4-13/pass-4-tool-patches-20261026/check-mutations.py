"""Run each reviewed guard-removal mutant in a separate process without editing sources."""
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[5]
TOOLS = ROOT / 'tools/live-topology'
sys.path.insert(0, str(TOOLS))
CASES = [
    ('inventory-findings', 'live_plans',
     'capture_output=True, text=True, timeout=30, check=False)\n            if inventory_check.returncode',
     'capture_output=True, text=True, timeout=30, check=True)\n            if inventory_check.returncode',
     'test_live_plans.PlanTests.test_actual_inventory_coverage_and_vector_validator_rejections_stop_preflight'),
    ('backup-bytes', 'lane', 'reference = verified_backup_reference(backup, runs[0])',
     "reference = 'sha256:' + backup.get('sha256', '') + ';file:' + backup.get('backupFile', '')",
     'test_lane.LaneTests.test_success_requires_fresh_binding_case_and_owned_cleanup'),
    ('malformed-output', 'run_live', " or (document is None and isinstance(error, VectorError))", '',
     'test_live_runner.RunnerTests.test_malformed_cli_output_fails_immediately_even_after_a_converging_poll'),
    ('attempt-document-reset', 'run_live', '        document = None\n', '',
     'test_live_runner.RunnerTests.test_malformed_cli_output_fails_immediately_even_after_a_converging_poll'),
    ('blank-token', 'run_live', 'not token.strip()', 'not token',
     'test_live_runner.RunnerTests.test_live_entry_guards_fail_before_preflight_or_execution'),
    ('policy-id-collision', 'live_plans', 'if name.casefold() in expected:', 'if False:',
     'test_live_plans.PlanTests.test_policy_package_ids_cannot_collide_case_insensitively'),
    ('resolved-inputs', 'run_live', "call = resolve(call, action.get('bindings', []), values)",
     'call = copy.deepcopy(call)',
     'test_live_runner.ExecutionTests.test_dynamic_cursor_and_audit_windows_reach_cli_and_actual_core_validation'),
    ('resolved-core-validation', 'run_live', '                validate_call(head, call)', '                pass',
     'test_live_runner.ExecutionTests.test_resolved_core_refusal_prevents_that_phase_from_reaching_cli'),
    ('converged-query-receipt', 'live_plans', "declared['kind'] == 'command' and len(phase['attempts']) != 1",
     "len(phase['attempts']) != 1",
     'test_live_runner.ExecutionTests.test_intentional_repeated_noop_is_submitted_and_only_delayed_reads_repeat'),
    ('inherited-environment', 'lane', "if key.startswith(('MCPCLI_LIVE_', 'EVENTSTORE_')):", 'if False:',
     'test_lane.LaneTests.test_failed_children_keep_all_operation_outcomes_and_exact_selectors'),
    ('rid-runtime-bytes', 'live_plans', 'if output.is_file() and output.read_bytes() != archive.read(asset):', 'if False:',
     'test_live_plans.AdapterDependencyTests.test_rid_runtime_assets_verify_present_bytes_and_restored_inventory'),
    ('last-phase-exit', 'live_plans', "                or phase['attempts'][-1].get('exitCode') != 0 \\\n", '',
     'test_lane.LaneTests.test_success_requires_fresh_binding_case_and_owned_cleanup'),
    ('pending-before-preflight', 'lane', "    receipt.write_text(json.dumps(report, indent=2) + '\\n')\n    generation",
     '    pass\n    generation', 'test_lane.LaneTests.test_hard_kill_during_preflight_cannot_leave_previous_success'),
]


def run_case(index):
    name, module_name, before, after, test = CASES[index]
    if module_name == 'lane':
        module = importlib.import_module('test_lane').lane
    else:
        module = importlib.import_module(module_name)
    source = Path(module.__file__).read_text()
    if source.count(before) != 1:
        raise RuntimeError(f'{name}: mutation anchor is not unique')
    changed = source.replace(before, after, 1)
    if name == 'pending-before-preflight':
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            (temporary / 'run-vectors.py').write_text(changed)
            importlib.import_module('test_lane').__file__ = str(temporary / 'test_lane.py')
            os.environ['PYTHONPATH'] = str(TOOLS)
            result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName(test))
    else:
        exec(compile(changed, module.__file__, 'exec'), module.__dict__)
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName(test))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--case':
        raise SystemExit(run_case(int(sys.argv[2])))
    results = []
    for index, (name, _, _, _, test) in enumerate(CASES):
        command = [sys.executable, str(Path(__file__).resolve()), '--case', str(index)]
        child = subprocess.run(command, capture_output=True, text=True, timeout=90)
        (Path(__file__).parent / (name + '.mutation.log')).write_text(child.stdout + child.stderr)
        detected = child.returncode == 1 and ('FAIL:' in child.stderr or 'ERROR:' in child.stderr)
        results.append({'mutation': name, 'test': test, 'command': command, 'exitCode': child.returncode, 'detected': detected})
        print(name + ': ' + ('detected' if detected else 'NOT DETECTED'), flush=True)
    (Path(__file__).parent / 'mutations.json').write_text(json.dumps(results, indent=2) + '\n')
    raise SystemExit(0 if all(result['detected'] for result in results) else 1)
