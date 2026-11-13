#!/usr/bin/env python3
"""Run isolated one-guard removals against the pass-3 regression tests.

Mutations exist only in memory. No approved artifact, verifier source file or
owner repository is written. Every control must produce an assertion failure.
"""
import sys

sys.dont_write_bytecode = True

import importlib.util
import inspect
import io
import json
from pathlib import Path
import textwrap
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
PACKET = HERE.parent
spec = importlib.util.spec_from_file_location('controls57tests', PACKET / 'test_verify_amendments.py')
T = importlib.util.module_from_spec(spec)
spec.loader.exec_module(T)


def replacement(module, function, before, after):
    original = getattr(module, function)
    source = textwrap.dedent(inspect.getsource(original))
    if source.count(before) != 1:
        raise ValueError(f'{function}: mutation must match exactly once: {before}')
    namespace = dict(original.__globals__)
    exec(compile(source.replace(before, after, 1), f'<guard-control:{function}>', 'exec'), namespace)
    return patch.object(module, function, namespace[function])


def skip_guard(module, message):
    original = module.require
    def removed(condition, diagnostic):
        if diagnostic != message:
            original(condition, diagnostic)
    return patch.object(module, 'require', side_effect=removed)


def child_bytecode_mutation():
    run = T.subprocess.run
    def process(args, **kwargs):
        if args[1:3] == ['-I', '-c']:
            args = list(args)
            args[3] = args[3].replace('sys.dont_write_bytecode = True\n', '', 1)
        return run(args, **kwargs)
    return patch.object(T.subprocess, 'run', side_effect=process)


def controls():
    V, L = T.V, T.L
    yield ('child imports disable bytecode first', T.AmendmentTests,
           'test_real_process_accepts_only_exact_permitted_drift_reports',
           child_bytecode_mutation())
    yield ('pinned-anchor re-read', T.AmendmentTests,
           'test_default_success_reports_effective_completion_from_status_or_integrated_labels',
           patch.object(V, 'anchor_evidence', return_value=0))
    for header, expected in [('Disposition', 'action'), ('Disposition / coverage', "action + ' / exclude'")]:
        yield (f'source {header}', T.AmendmentTests,
               'test_source_dispositions_must_reflect_the_adopted_amendment_action',
               replacement(V, 'check_rows', f"elif header == '{header}':\n                expected = {expected}",
                           f"elif header == '{header}':\n                expected = before"))
    for message in ('invalid successor label state', 'label register must designate integrated successor state'):
        yield (message, T.LabelTests, 'test_register_state_and_each_delivery_authorization_field', skip_guard(L, message))
    for field in ('exactWords', 'source', 'approvedOn'):
        kept = tuple(k for k in ('exactWords', 'source', 'approvedOn') if k != field)
        yield (f'delivery authorization {field}', T.LabelTests, 'test_register_state_and_each_delivery_authorization_field',
               replacement(L, 'verify', "('exactWords', 'source', 'approvedOn')", repr(kept)))
    for field, before, after in [
        ('file', "label['file'] == 'README.md' and ", ''),
        ('sha256', " and label['sha256'] == sha(text.encode())", ''),
        ('gate', "row['gate'] == gates[key] and ", ''),
    ]:
        yield (f'label {field}', T.LabelTests, 'test_registered_label_hash_file_and_gate_damaged_independently',
               replacement(L, 'verify', before, after))
    yield ('canonical integration commit', T.LabelTests, 'test_complete_delivery_fixture_and_each_completion_binding',
           skip_guard(L, 'eventstore: missing integrated commit'))
    yield ('before section matches committed base', T.LabelTests,
           'test_readme_bindings_row_owner_and_rehashed_patch_damaged_independently',
           replacement(L, 'verify', ' and compatibility_section(before) == before_section', ''))
    yield ('duplicate workflow key', T.AmendmentTests, 'test_workflow_status_rejects_duplicate_keys_and_unsupported_scalars',
           replacement(V, 'yaml_status', "require(len(values) <= 1, f'duplicate workflow status {key.strip()}')", 'pass'))
    yield ('unsupported workflow scalar', T.AmendmentTests, 'test_workflow_status_rejects_duplicate_keys_and_unsupported_scalars',
           replacement(V, 'yaml_status', "require(scalar is not None, f'unsupported workflow status scalar {key.strip()}')",
                       'if scalar is None:\n        return None'))
    for name, before, after in [
        ('Git repository diagnostic', 'failed for label evidence in {repo}: {detail}', 'failed for label evidence: {detail}'),
        ('Git stderr diagnostic', 'failed for label evidence in {repo}: {detail}', 'failed for label evidence in {repo}'),
    ]:
        yield (name, T.LabelTests, 'test_current_origin_main_reports_section_drift_and_retains_exact_inventory_artifacts',
               replacement(L, 'git', before, after))


def main():
    results = []
    for name, case, method, mutation in controls():
        stream = io.StringIO()
        with mutation:
            result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.TestSuite([case(method)]))
        if name == 'child imports disable bytecode first':
            for generated in PACKET.glob('__pycache__/verify_*.pyc'):
                generated.unlink()
            cache = PACKET / '__pycache__'
            if cache.exists():
                cache.rmdir()
        detected = bool(result.failures) and not result.errors
        results.append({'guard': name, 'test': f'{case.__name__}.{method}',
                        'detected': detected, 'failures': len(result.failures), 'errors': len(result.errors),
                        'output': stream.getvalue()})
    print(json.dumps({'controls': results, 'detected': sum(r['detected'] for r in results),
                      'total': len(results)}, indent=2))
    return 0 if all(r['detected'] for r in results) else 1


if __name__ == '__main__':
    sys.exit(main())
