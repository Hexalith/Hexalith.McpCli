"""Bind every spec matrix row to current passing live results or named regression tests."""
import json
from pathlib import Path
out=Path(__file__).resolve().parent
read=lambda name:json.loads((out/name).read_text())
log=(out/'live-tools.stderr.txt').read_text().splitlines()
def tests(*names):
    for name in names:
        assert any(line.startswith(name+' (') and line.endswith(' ... ok') for line in log),name
    return list(names)
lane=read('live/live-lane.json'); live=read('live-audit.stdout.txt'); paging=read('paging-audit.json')
assert lane['fullLiveAccepted'] is True and lane['result']=='passed' and lane['passed']==21 and lane['failed']==0
assert live['result']=='passed' and live['vectors']==21 and live['phases']==144
assert live['commandSubmissions']==live['distinctCommandMessageIds']==53
assert paging['result']=='passed' and {row['operation'] for row in paging['operations']}=={'parties.list-parties','parties.search-parties'}
assert all(row['offset']==2 and row['laterPageItems']==0 and row['totalCount']==1 for row in paging['operations'])
by_operation={row['operation']:row for row in live['operations']}
assert by_operation['tenants.get-tenant-users']['result']==by_operation['tenants.get-tenant-audit']['result']=='passed'
rows=[
 dict(state='Complete approved inputs',result='passed',evidence=['live/live-lane.json','live-audit.stdout.txt'],vectors=21,phases=144,commandSubmissions=53),
 dict(state='Stale package, vector or live-plan binding',result='passed',evidence=['live-tools.stderr.txt'],tests=tests('test_stale_vector_hash_rejects_plan','test_actual_preflight_delegates_artifact_inventory_and_core_rejections','test_parent_binding_mismatch_never_reaches_execute')),
 dict(state='Delayed bootstrap/projection',result='passed',evidence=['live-tools.stderr.txt','validation-reuse.json'],tests=tests('test_only_queries_poll_for_persisted_convergence','test_write_failure_is_never_retried','test_every_vector_submits_each_declared_command_once_at_executor_boundary')),
 dict(state='Dynamic cursor/time',result='passed',evidence=['live-audit.stdout.txt','paging-audit.json'],operations=['tenants.get-tenant-users','tenants.get-tenant-audit','parties.list-parties','parties.search-parties']),
 dict(state='Missing prerequisite, invalid selector or unresolved binding',result='passed',evidence=['live-tools.stderr.txt'],tests=tests('test_unknown_or_empty_selector_starts_no_topology','test_missing_runtime_fails_before_preflight_or_child','test_exactly_one_passing_selected_case_is_required','test_unresolved_cursor_is_rejected_before_execution')),
 dict(state='Semantic mismatch',result='passed',evidence=['live-tools.stderr.txt'],tests=tests('test_broken_business_effect_fails_with_phase_operation_and_path','test_missing_persisted_document_deadline_retains_declared_assertion_paths','test_failing_preflight_invalidates_receipt_and_redacts_identity'))]
report=dict(result='passed',fullLiveAccepted=True,runId=lane['runId'],rows=rows)
(out/'matrix-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
