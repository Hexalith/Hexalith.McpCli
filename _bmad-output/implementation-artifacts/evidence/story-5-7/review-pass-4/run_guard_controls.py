#!/usr/bin/env python3
"""Re-run every pass-3 guard removal against live module globals, plus the pass-4 guards.

This corrects review-pass-3/run_guard_controls.py, which compiled each mutant into a copy
of the module globals: the tests' patch.object fixtures never reached those mutants, so
seven L.verify controls failed at unrelated assertions even with nothing removed.

Each control runs its target test twice through the same mechanism. The unchanged
rebuild (baseline) must pass. The guard-removed rebuild must fail with no errors, and a
failing assertEqual must name that guard's diagnostic in its operands (traceback text is
not searched: unittest truncates and pprint wraps long strings). One identity control removes nothing
and must report detected: false. For the pass-3 rebuilds, the unchanged function is also
rebuilt with the pass-3 copied-globals mechanism; any failure there is vacuous detection.

Mutations exist only in memory. No approved artifact, verifier source file or owner
repository is written.
"""
import sys

sys.dont_write_bytecode = True

import importlib.util
import inspect
import io
import json
from pathlib import Path
import textwrap
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
PACKET = HERE.parent
spec = importlib.util.spec_from_file_location('controls57tests', PACKET / 'test_verify_amendments.py')
T = importlib.util.module_from_spec(spec)
spec.loader.exec_module(T)


def rebuild(module, function, before, after, *, live=True):
    """Return a patch that replaces module.function with a rebuilt, optionally mutated, copy."""
    original = getattr(module, function)
    source = textwrap.dedent(inspect.getsource(original))
    if source.count(before) != 1:
        raise ValueError(f'{function}: mutation must match exactly once: {before}')
    code = compile(source.replace(before, after, 1), f'<guard-control:{function}>', 'exec')
    if live:
        body = next(c for c in code.co_consts if isinstance(c, types.CodeType) and c.co_name == function)
        mutant = types.FunctionType(body, original.__globals__, function, original.__defaults__, original.__closure__)
        mutant.__kwdefaults__ = original.__kwdefaults__
    else:  # the pass-3 mechanism, kept only to measure its vacuous failures
        namespace = dict(original.__globals__)
        exec(code, namespace)
        mutant = namespace[function]
    return patch.object(module, function, mutant)


def replacement(module, function, before, after):
    def mutation(removed):
        return rebuild(module, function, before, after if removed else before)
    mutation.copied_globals = lambda: rebuild(module, function, before, before, live=False)
    return mutation


def skip_guard(module, message):
    def mutation(removed):
        original = module.require
        def require(condition, diagnostic):
            if not removed or diagnostic != message:
                original(condition, diagnostic)
        return patch.object(module, 'require', side_effect=require)
    return mutation


def child_bytecode():
    def mutation(removed):
        run = T.subprocess.run
        def process(args, **kwargs):
            if removed and args[1:3] == ['-I', '-c']:
                args = list(args)
                args[3] = args[3].replace('sys.dont_write_bytecode = True\n', '', 1)
            return run(args, **kwargs)
        return patch.object(T.subprocess, 'run', side_effect=process)
    return mutation


def anchor_count():
    def mutation(removed):
        if removed:
            return patch.object(T.V, 'anchor_evidence', return_value=0)
        return patch.object(T.V, 'anchor_evidence', side_effect=T.V.anchor_evidence)
    return mutation


def controls():
    """Yield (pass, guard, test case, method, mutation, diagnostic) for every control."""
    V, L, A, B = T.V, T.L, T.AmendmentTests, T.LabelTests
    yield (3, 'child imports disable bytecode first', A, 'test_real_process_accepts_only_exact_permitted_drift_reports',
           child_bytecode(), '__pycache__')
    yield (3, 'pinned-anchor re-read', A, 'test_default_success_reports_effective_completion_from_status_or_integrated_labels',
           anchor_count(), '277 pinned anchors')
    for header, expected in [('Disposition', 'action'), ('Disposition / coverage', "action + ' / exclude'")]:
        yield (3, f'source {header}', A, 'test_source_dispositions_must_reflect_the_adopted_amendment_action',
               replacement(V, 'check_rows', f"elif header == '{header}':\n                expected = {expected}",
                           f"elif header == '{header}':\n                expected = before"),
               f'changed protected source field {header}')
    for message in ('invalid successor label state', 'label register must designate integrated successor state'):
        yield (3, message, B, 'test_register_state_and_each_delivery_authorization_field', skip_guard(L, message), message)
    for field in ('exactWords', 'source', 'approvedOn'):
        kept = tuple(k for k in ('exactWords', 'source', 'approvedOn') if k != field)
        yield (3, f'delivery authorization {field}', B, 'test_register_state_and_each_delivery_authorization_field',
               replacement(L, 'verify', "('exactWords', 'source', 'approvedOn')", repr(kept)),
               'completion requires explicit upstream delivery authorization')
    for field, before, after, diagnostic in [
        ('file', "label['file'] == 'README.md' and ", '', 'label hash/file mismatch'),
        ('sha256', " and label['sha256'] == sha(text.encode())", '', 'label hash/file mismatch'),
        ('gate', "row['gate'] == gates[key] and ", '', 'removal gate differs from successor inventory'),
    ]:
        yield (3, f'label {field}', B, 'test_registered_label_hash_file_and_gate_damaged_independently',
               replacement(L, 'verify', before, after), diagnostic)
    yield (3, 'canonical integration commit', B, 'test_complete_delivery_fixture_and_each_completion_binding',
           skip_guard(L, 'eventstore: missing integrated commit'), 'eventstore: missing integrated commit')
    yield (3, 'before section matches committed base', B, 'test_readme_bindings_row_owner_and_rehashed_patch_damaged_independently',
           replacement(L, 'verify', ' and compatibility_section(before) == before_section', ''),
           'before snapshot differs from committed base')
    yield (3, 'duplicate workflow key', A, 'test_workflow_status_rejects_duplicate_keys_and_unsupported_scalars',
           replacement(V, 'yaml_status', "require(len(values) <= 1, f'duplicate workflow status {key.strip()}')", 'pass'),
           'duplicate workflow status')
    yield (3, 'unsupported workflow scalar', A, 'test_workflow_status_rejects_duplicate_keys_and_unsupported_scalars',
           replacement(V, 'yaml_status', "require(scalar is not None, f'unsupported workflow status scalar {key.strip()}')",
                       'if scalar is None:\n        return None'),
           'unsupported workflow status scalar')
    for name, after, diagnostic in [
        ('Git repository diagnostic', 'failed for label evidence: {detail}', 'failed for label evidence in '),
        ('Git stderr diagnostic', 'failed for label evidence in {repo}', 'fatal: current README unavailable'),
    ]:
        yield (3, name, B, 'test_current_origin_main_reports_section_drift_and_retains_exact_inventory_artifacts',
               replacement(L, 'git', 'failed for label evidence in {repo}: {detail}', after), diagnostic)
    # Pass-4 guards that no test protected before this pass.
    yield (4, 'check_rows checks the Exact replacement column', A, 'test_exact_replacement_column_is_checked_through_every_row',
           replacement(V, 'check_rows', "check_replacement(f'{module}:{key} ({cid})', expected_outcome, action, fields['Exact replacement'])", 'pass'),
           'invented replacement; pinned decorated type/eligibility not established')
    yield (4, 'successor version', A, 'test_owner_packet_checks_successor_version_and_metadata',
           replacement(V, 'verify_owner_packet', "require(new_version == version, f'{module}: successor version mismatch')", 'pass'),
           'successor version mismatch')
    yield (4, 'successor metadata', A, 'test_owner_packet_checks_successor_version_and_metadata',
           replacement(V, 'verify_owner_packet', 'check_metadata(module, version, old.read_text(), new.read_text())', 'pass'),
           'metadata/pin/scope/approval state differs from candidate policy')
    yield (4, 'anchor continuation has a path', A, 'test_anchor_paths_must_resolve_to_declared_ordinary_files',
           replacement(V, 'anchor_evidence', "require(current is not None, f'{module}:{key}: source anchor continuation has no path')", 'pass'),
           'source anchor continuation has no path')
    yield (4, 'CODEOWNERS anchor names its repository', A, 'test_anchor_paths_must_resolve_to_declared_ordinary_files',
           replacement(V, 'anchor_evidence', "require(declared_repo is not None, f'{module}:{key}: CODEOWNERS lacks repository context')", 'pass'),
           'CODEOWNERS lacks repository context')
    yield (4, 'anchor path resolves', A, 'test_anchor_paths_must_resolve_to_declared_ordinary_files',
           replacement(V, 'anchor_evidence', "raise InvalidAmendment(f'{module}:{key}: unresolved source anchor {current}')", 'continue'),
           'unresolved source anchor Unknown/Command.cs')
    yield (4, 'anchor repository is declared', A, 'test_anchor_paths_must_resolve_to_declared_ordinary_files',
           replacement(V, 'anchor_evidence', "require(repo in pins and not source.endswith('/SKILL.md')", "require(not source.endswith('/SKILL.md')"),
           'source outside declared ordinary files')
    yield (4, 'anchor is not an agent skill', A, 'test_anchor_paths_must_resolve_to_declared_ordinary_files',
           replacement(V, 'anchor_evidence', "require(repo in pins and not source.endswith('/SKILL.md')", 'require(repo in pins'),
           'source outside declared ordinary files')
    # Identity control: nothing is removed, so it must not be detected.
    yield (None, 'identity (nothing removed)', B, 'test_register_state_and_each_delivery_authorization_field',
           replacement(L, 'verify', "('exactWords', 'source', 'approvedOn')", "('exactWords', 'source', 'approvedOn')"),
           'completion requires explicit upstream delivery authorization')


def clean_bytecode():
    """Remove only the verifier caches a bytecode-removal control generated."""
    for generated in PACKET.glob('__pycache__/verify_*.pyc'):
        generated.unlink()
    cache = PACKET / '__pycache__'
    if cache.exists():
        cache.rmdir()


def execute(case, method, mutation):
    test, failed = case(method), []
    assert_equal = test.assertEqual
    def recording(first, second, msg=None):
        try:
            assert_equal(first, second, msg)
        except AssertionError:
            failed.append(f'{first!r}\n{second!r}')
            raise
    test.assertEqual = recording
    stream = io.StringIO()
    with mutation:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.TestSuite([test]))
    clean_bytecode()
    return {'failures': len(result.failures), 'errors': len(result.errors), 'passed': result.wasSuccessful(),
            'failedAssertions': failed, 'output': stream.getvalue()}


def main():
    results = []
    for introduced, name, case, method, mutation, diagnostic in controls():
        baseline = execute(case, method, mutation(False))
        removed = execute(case, method, mutation(True))
        named = any(diagnostic in operands for operands in removed['failedAssertions'])
        detected = baseline['passed'] and removed['failures'] > 0 and removed['errors'] == 0 and named
        entry = {'guard': name, 'introducedInPass': introduced, 'test': f'{case.__name__}.{method}', 'diagnostic': diagnostic,
                 'detected': detected,
                 'baseline': {k: baseline[k] for k in ('passed', 'failures', 'errors')},
                 'removed': {'failures': removed['failures'], 'errors': removed['errors'], 'diagnosticInFailedAssertion': named},
                 'removedOutput': removed['output']}
        copied = getattr(mutation, 'copied_globals', None)
        if introduced == 3 or introduced is None:
            pass3 = execute(case, method, copied()) if copied else baseline
            entry['pass3MechanismIdentity'] = {k: pass3[k] for k in ('passed', 'failures', 'errors')}
        results.append(entry)
    guards = [r for r in results if r['introducedInPass'] is not None]
    identity = [r for r in results if r['introducedInPass'] is None]
    pass3 = [r for r in guards if r['introducedInPass'] == 3]
    summary = {
        'detected': sum(r['detected'] for r in guards), 'total': len(guards),
        'pass3Controls': len(pass3), 'pass3DetectedWithLiveGlobals': sum(r['detected'] for r in pass3),
        'pass3SupportedByPass3Receipt': sum(r['pass3MechanismIdentity']['passed'] for r in pass3),
        'pass4Controls': len(guards) - len(pass3),
        'identityDetected': [r['detected'] for r in identity],
    }
    print(json.dumps({'summary': summary, 'controls': results}, indent=2))
    return 0 if all(r['detected'] for r in guards) and not any(r['detected'] for r in identity) else 1


if __name__ == '__main__':
    sys.exit(main())
