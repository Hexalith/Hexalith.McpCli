import importlib
import io
import json
from pathlib import Path
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
sys.path.insert(0, str(Path.cwd() / 'tools/live-topology'))
import live_plans
import run_live
import test_live_plans
import test_live_runner
import test_lane
checks = []
def check(label, module, function, before, after, test):
    source = Path(module.__file__).read_text()
    if source.count(before) != 1:
        raise RuntimeError(f'{label}: replacement is not unique: {source.count(before)}')
    namespace = {'__file__': module.__file__, '__name__': module.__name__}
    exec(compile(source.replace(before, after), module.__file__, 'exec'), namespace)
    target = getattr(module, function)
    original = target.__code__
    target.__code__ = namespace[function].__code__
    try:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            result = unittest.TextTestRunner(stream=io.StringIO()).run(unittest.defaultTestLoader.loadTestsFromName(test))
        record = dict(guard=label, test=test, detected=not result.wasSuccessful(), failures=len(result.failures), errors=len(result.errors))
        checks.append(record)
        if result.wasSuccessful():
            raise RuntimeError(f'{label}: guard removal survived')
    finally:
        target.__code__ = original
plan_guards = [
 ('duplicate binding target', "if binding['path'] in bound_paths:", 'if False:', 'test_duplicate_binding_target_is_rejected'),
 ('captured cursor provenance', "if capture[0] != 'string' or capture[2] != '/paging/nextCursor':", 'if False:', 'test_cursor_binding_requires_a_capture_of_the_returned_cursor'),
 ('timestamp capture type', "if capture[0] != 'timestamp':", 'if False:', 'test_time_binding_requires_a_timestamp_capture'),
 ('static step input', "if not present or not isinstance(original, str) or not original.startswith('scripted-'):", 'if False:', 'test_step_binding_cannot_replace_static_cursor_input'),
 ('duplicate capture name', "if capture['name'] in captures:", 'if False:', 'test_duplicate_capture_name_is_rejected'),
 ('duplicate assertion selector', "or assertion_index in replacements:", 'or False:', 'test_duplicate_assertion_binding_index_is_rejected'),
 ('capture tuple binding', "or capture != ('string', action.get('step'), assertion['path']):", 'or False:', 'test_assertion_binding_requires_matching_capture_type_phase_and_path')]
for label, before, after, test in plan_guards:
    check(label, live_plans, 'load_plan', before, after, 'test_live_plans.PlanTests.' + test)
for label, before in [
 ('returned operation/tenant identity', "document.get('operation') != call['operation'] or document.get('tenant') != call['envelope']['tenant']"),
 ('query document presence', "call['kind'] == 'query' and 'document' not in document"),
 ('command identifier syntax', "not ULID.fullmatch(document.get('messageId', '')) or not ULID.fullmatch(document.get('correlationId', ''))"),
 ('command default correlation', "document['correlationId'] != expected")]:
    check(label, run_live, 'observe', 'if '+before+':', 'if False:', 'test_live_runner.RunnerTests.test_returned_document_identity_guards_reject_one_cli_response')
check('empty userinfo rejected', run_live, 'main', 'parsed.username is not None or parsed.password is not None', 'parsed.username or parsed.password', 'test_live_runner.RunnerTests.test_live_entry_guards_fail_before_preflight_or_execution')
check('isolation entry requirement', run_live, 'main', "if os.environ.get('MCPCLI_ISOLATED_TOPOLOGY') != '1':", 'if False:', 'test_live_runner.RunnerTests.test_live_entry_guards_fail_before_preflight_or_execution')
for label, before in [('HTTP only', "parsed.scheme != 'http'"), ('loopback only', "parsed.hostname not in ('localhost', '127.0.0.1', '::1')"), ('no userinfo', 'parsed.username is not None or parsed.password is not None'), ('no query', 'parsed.query'), ('no fragment', 'parsed.fragment'), ('nonempty token', 'not token')]:
    check(label, run_live, 'main', before, 'False', 'test_live_runner.RunnerTests.test_live_entry_guards_fail_before_preflight_or_execution')
check('child timeout range', test_lane.lane, 'main', 'if not 1 <= args.child_timeout <= 960:', 'if False:', 'test_lane.LaneTests.test_out_of_range_child_timeout_starts_no_topology')
check('exact selected class', test_lane.lane, 'main', "'-class', 'Hexalith.McpCli.Integration.Tests.LiveVectorTests'", "'-class', 'Hexalith.McpCli.Integration.Tests.WrongTests'", 'test_lane.LaneTests.test_failed_children_keep_all_operation_outcomes_and_exact_selectors')
check('one trait selector', test_lane.lane, 'main', "'-trait', 'Operation=' + operation,", "'-trait', 'Operation=' + operation, '-trait', 'Operation=extra',", 'test_lane.LaneTests.test_failed_children_keep_all_operation_outcomes_and_exact_selectors')
check('preflight summary stdout', test_lane.lane, 'main', "report['result'] = 'preflight-only'", "report['result'] = 'preflight-only'\n            return 0", 'test_lane.LaneTests.test_preflight_only_prints_summary_and_never_starts_children')
line = "                    outcome.update(result='passed', isolatedReceipt=str(runs[0] / 'result.json'))\n"
source = Path(test_lane.lane.__file__).read_text()
# Move the only pass assignment back ahead of the bootstrap-read interruption point.
check('bootstrap before pass receipt', test_lane.lane, 'main',
      source[source.index("                    bootstrap = json.loads"):source.index('                except Exception as error:')],
      line + source[source.index("                    bootstrap = json.loads"):source.index('                except Exception as error:')].replace(line, ''),
      'test_lane.LaneTests.test_success_requires_fresh_binding_case_and_owned_cleanup')
print(json.dumps({'mutants': len(checks), 'detected': sum(item['detected'] for item in checks), 'checks': checks}, indent=2))
