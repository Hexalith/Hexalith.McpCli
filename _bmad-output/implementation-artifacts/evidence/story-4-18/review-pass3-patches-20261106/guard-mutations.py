from pathlib import Path
import hashlib
import io
import json
import os
import sys
import types
import unittest
from unittest.mock import patch

root = Path(__file__).resolve().parents[5]
evidence = Path(__file__).resolve().parent
sys.path[:0] = [str(root / 'scripts/tests'), str(root / 'scripts'), str(root / 'tools/live-topology')]
import test_paired_publication as publication
import test_ci as topology

release_mutations = [
    ('duplicate-operator-keys', 'verify-paired-publication',
     'decision = json.loads(serialized, object_pairs_hook=unique_operator_keys)', 'decision = json.loads(serialized)',
     publication.PublicationBoundaryTests, 'test_duplicate_operator_keys_refuse_recording_and_raw_retention_redacts_every_value'),
    ('raw-operator-redaction', 'verify-paired-publication',
     '        retained = redact_operator_text(decoded)',
     '        document = json.loads(decoded)\n        sanitized = redact_operator_values(document)\n        retained = json.dumps(sanitized) if sanitized != document else decoded',
     publication.PublicationBoundaryTests, 'test_duplicate_operator_keys_refuse_recording_and_raw_retention_redacts_every_value'),
    ('paired-source-phase', 'verify-release-source', "paired = args.phase == 'paired'", 'paired = False',
     publication.PublicationTests, 'test_real_paired_source_producer_writes_evidence_accepted_by_publication'),
    ('paired-source-current-main', 'verify-release-source', "'current_main': live_main,", '',
     publication.PublicationTests, 'test_real_paired_source_producer_writes_evidence_accepted_by_publication'),
    ('recomputed-acceptance', 'verify-paired-publication', 'if read_json(recomputed) != read_json(accepted_path):', 'if False:',
     publication.PublicationTests, 'test_recomputed_acceptance_must_equal_authenticated_and_operator_bound_record'),
    ('import-preflight-bindings', 'publish-paired-release', 'if any(original.get(key) != checked[key] for key in bindings):', 'if False:',
     publication.PublicationTests, 'test_changed_valid_operator_decision_refuses_import_after_initial_preflight'),
    ('duplicate-public-members', 'publish-paired-release', 'if len(archive.namelist()) != len(set(archive.namelist())):', 'if False:',
     publication.PublicationTests, 'test_duplicate_public_archive_member_refuses_even_when_consumer_bytes_match'),
]
source_condition = "if commit != source['selectedCommit'] or status or remote != source['repository']:"
topology_mutations = [
    ('prepared-selection', "if prepared.get('selection') != selection:", 'if False:',
     'test_after_preparation_source_and_selection_drift_refuse_before_vectors'),
    ('prepared-head', source_condition, "if status or remote != source['repository']:",
     'test_after_preparation_source_and_selection_drift_refuse_before_vectors'),
    ('prepared-status', source_condition, "if commit != source['selectedCommit'] or remote != source['repository']:",
     'test_after_preparation_source_and_selection_drift_refuse_before_vectors'),
    ('prepared-remote', source_condition, "if commit != source['selectedCommit'] or status:",
     'test_after_preparation_source_and_selection_drift_refuse_before_vectors'),
    ('before-smoke-provenance', '        require_prepared_provenance(prepared)\n', '        pass\n',
     'test_after_vector_source_and_selection_drift_refuse_before_independent_smoke'),
    ('root-redis-override', "if not catalog.is_file() or redis != ['3.4.31']:", 'if not catalog.is_file():',
     'test_preparation_requires_exact_root_redis_override_before_builds'),
]
results = []
def run(name, case, method, changed):
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.TestSuite([case(method)]))
    log = stream.getvalue()
    (evidence / ('mutation-' + name + '.txt')).write_text(log)
    detected = not result.wasSuccessful()
    results.append({'name': name, 'test': case.__name__ + '.' + method,
                    'detected': detected, 'failures': len(result.failures), 'errors': len(result.errors),
                    'mutation': changed, 'log_sha256': hashlib.sha256(log.encode()).hexdigest()})
    (evidence / 'guard-mutations.json').write_text(json.dumps({'mutations': results}, indent=2) + '\n')
    print(name, 'detected' if detected else 'MISSED', flush=True)
    if not detected:
        raise SystemExit(1)

original_loader = publication.module
for name, target, old, new, case, method in release_mutations:
    path = root / 'scripts' / (target + '.py')
    original = path.read_text()
    assert original.count(old) == 1, (name, original.count(old))
    mutated = original.replace(old, new)
    def load(filename, target=target, path=path, mutated=mutated):
        if filename != target:
            return original_loader(filename)
        result = types.ModuleType(filename.replace('-', '_'))
        result.__file__ = str(path)
        exec(compile(mutated, str(path), 'exec'), result.__dict__)
        return result
    with patch.object(publication, 'module', side_effect=load):
        run(name, case, method, {'file': str(path.relative_to(root)), 'removed': old, 'replacement': new})

original_setup = topology.CiHooksTests.setUp
for name, old, new, method in topology_mutations:
    def setup(self, old=old, new=new):
        original_setup(self)
        path = self.tools / 'ci.py'
        original = path.read_text()
        assert original.count(old) == 1, (name, original.count(old))
        path.write_text(original.replace(old, new))
    with patch.object(topology.CiHooksTests, 'setUp', setup):
        run(name, topology.CiHooksTests, method,
            {'file': 'tools/live-topology/ci.py', 'removed': old, 'replacement': new})

print('Detected', len(results), 'of', len(results), 'guard removals.', flush=True)
