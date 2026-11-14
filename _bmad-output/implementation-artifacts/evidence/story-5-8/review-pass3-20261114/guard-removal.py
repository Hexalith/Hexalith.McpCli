"""Code-review pass 3 guard-removal controls, run only in isolated workspace copies.

Each mutation deletes one guard or reverts one fix inside a fresh copy made by the
test module's workspace_view(pending=False), as delivery/lifecycle-proof.py does,
and runs only the tests that protect it with that copy as the working directory.
A mutation counts as detected only when at least one test ran and the run ends
in a failures-only summary with at least one AssertionError. An unmutated copy
first proves that the selected tests pass. Real packet sources are never written;
their hashes are compared before and after. Run from the repository root:
python3 -B -I <this file>.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import time

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
OUT = HERE / 'guard-removal.json'
E = Path('_bmad-output/implementation-artifacts/evidence/story-5-8')
VA, VL, LP, BC = E / 'verify_amendment.py', E / 'verify_labels.py', E / 'delivery/lifecycle-proof.py', E / 'build_candidate.py'

M = [
 ('verify_amendment.py:234 unknown approval decision', [(VA, "    require(receipt.get('decision') in {'pending','approved'}, 'unknown approval decision')\n", '')], ['test_unknown_approval_decision']),
 ('verify_amendment.py:91 amendment columns', [(VA, "        require(row['headers'][-len(B.EXTRA):] == B.EXTRA, f'folders:{key}: amendment columns damaged')\n", '')], ['test_amendment_columns']),
 ('verify_amendment.py:111 legacy disposition', [(VA, "if h == 'Disposition': require(row['cells'][i] == decision, f'folders:{key}: legacy/amendment disposition mismatch')", "if h == 'Disposition': pass")], ['test_amendment_columns']),
 ('verify_amendment.py:112 legacy coverage', [(VA, "if h == 'Coverage': require(row['cells'][i] == coverage, f'folders:{key}: legacy/amendment coverage mismatch')", "if h == 'Coverage': pass")], ['test_amendment_columns']),
 ('verify_amendment.py:113 combined disposition', [(VA, "if h == 'Disposition / coverage': require(row['cells'][i] == decision + ' / ' + coverage, f'folders:{key}: combined disposition mismatch')", "if h == 'Disposition / coverage': pass")], ['test_amendment_columns']),
 ('verify_amendment.py:131 anchor path escapes', [(VA, "            require(not Path(path).is_absolute() and '..' not in Path(path).parts, f'folders:{key}: anchor path escapes source')\n", '')], ['test_anchor_escape']),
 ('verify_amendment.py:135 source anchor', [(VA, "            require(row['cells'][7 if key[0] in 'ML' else 6] == '`'+expected.split('; ')[0]+'`', f'folders:{key}: source anchor differs from pin')\n", '            pass\n')], ['test_anchor_escape']),
 ('verify_amendment.py:199 historical predecessor inspection', [(VA, "    require(historical.returncode in {0,1}, 'folders: cannot inspect historical predecessor object')\n", '')], ['test_published_predecessor_tree_binding']),
 ('verify_amendment.py:246 frontmatter', [(VA, "    require(text.startswith('---\\n'), 'folders: inventory frontmatter missing')\n", '')], ['test_story_status_and_metadata']),
 ('verify_amendment.py:252 duplicate metadata', [(VA, "        require(bool(sep) and k not in result, 'folders: damaged or duplicate metadata')\n", '')], ['test_story_status_and_metadata']),
 ('utf-8 reads reverted together (verify_amendment.py:265/285/286, build_candidate.py:357/512)', [
     (VA, "            text = (root/path).read_text(encoding='utf-8')\n", "            text = (root/path).read_text()\n"),
     (VA, "    old, new = parse((root/B.OLD).read_text(encoding='utf-8')), parse((root/B.NEW).read_text(encoding='utf-8'))\n    check_metadata((root/B.NEW).read_text(encoding='utf-8'))\n",
          "    old, new = parse((root/B.OLD).read_text()), parse((root/B.NEW).read_text())\n    check_metadata((root/B.NEW).read_text())\n"),
     (BC, "'AD-23-capability-class-map.json').read_text(encoding='utf-8'))", "'AD-23-capability-class-map.json').read_text())"),
     (BC, "'evidence/story-5-7/labels.json').read_text(encoding='utf-8'))", "'evidence/story-5-7/labels.json').read_text())")], ['test_entrypoints_decode']),
 ('verify_amendment.py:265 read alone reverted', [(VA, "            text = (root/path).read_text(encoding='utf-8')\n", "            text = (root/path).read_text()\n")], ['test_entrypoints_decode']),
 ('verify_amendment.py:285 B.OLD read alone reverted', [(VA, "parse((root/B.OLD).read_text(encoding='utf-8'))", "parse((root/B.OLD).read_text())")], ['test_entrypoints_decode']),
 ('verify_amendment.py:285 B.NEW read alone reverted', [(VA, "parse((root/B.NEW).read_text(encoding='utf-8'))", "parse((root/B.NEW).read_text())")], ['test_entrypoints_decode']),
 ('verify_amendment.py:286 read alone reverted', [(VA, "check_metadata((root/B.NEW).read_text(encoding='utf-8'))", "check_metadata((root/B.NEW).read_text())")], ['test_entrypoints_decode']),
 ('build_candidate.py:357 read alone reverted', [(BC, "'AD-23-capability-class-map.json').read_text(encoding='utf-8'))", "'AD-23-capability-class-map.json').read_text())")], ['test_entrypoints_decode']),
 ('build_candidate.py:512 read alone reverted', [(BC, "'evidence/story-5-7/labels.json').read_text(encoding='utf-8'))", "'evidence/story-5-7/labels.json').read_text())")], ['test_entrypoints_decode']),
 ('verify_labels.py:28 label artifact path', [(VL, "    require(isinstance(item,dict) and isinstance(item.get('path'),str), 'label artifact path missing')\n", '')], ['test_label_artifact_path']),
 ('verify_labels.py:30 label path escapes', [(VL, "    require(not path.is_absolute() and (root/path).resolve().is_relative_to(root), 'label path escapes repository')\n", '')], ['test_label_artifact_path']),
 ('verify_labels.py:40 invalid register state', [(VL, "    require(register.get('state') in {'candidate-pending-owner-approval-and-delivery','integrated'}, 'invalid label register state')\n", '')], ['test_unknown_register_state']),
 ('verify_labels.py:41 integrated-state trigger', [(VL, "register.get('state') == 'integrated' or ", '')], ['test_standalone_integrated']),
 ('verify_labels.py:70 retained authority text', [(VL, "        require('[technical-tools inventory 1.0.3]' in text and old['gate'] in text and 'Folders inventory SHA-256: `'+inventory_hash+'`.' in text, f'{key}: retained technical authority or successor hash missing')\n", '')], ['test_retained_authority']),
 ('verify_labels.py:89 origin/main half', [(VL, " and B.sha(B.git(root,'show',f'origin/main:{path}')) == digest", '')], ['test_completion_rejects_rewritten']),
 ('verify_labels.py:89 inventoryRevision half', [(VL, "B.sha(B.git(root,'show',f'{inv_revision}:{path}')) == digest and ", '')], ['test_completion_rejects_rewritten']),
 ('lifecycle-proof.py post-child workflow bytes check reverted to completion_requested', [(LP, "module.V.require(all((fixture / path).read_bytes() == data for path, data in workflow.items()),", "module.V.require(module.V.completion_requested(fixture, False),")], ['test_lifecycle_proof_rejects_child_workflow']),
 ('lifecycle-proof.py post-child candidate bytes check removed', [(LP, "        module.V.require((fixture / B.NEW).read_bytes() == before[str(B.NEW)],\n                         'synthetic lifecycle candidate bytes changed during child run')\n", '')], ['test_lifecycle_proof_rejects_child_candidate']),
 ('lifecycle-proof.py sidecars written before integrity checks', [
     (LP, "        after_fixture = module.V.read_json(approval_path), module.V.read_json(labels_path)\n",
          "        for stream, data in streams.items():\n            (delivery / captures[stream]['path']).write_bytes(data)\n        after_fixture = module.V.read_json(approval_path), module.V.read_json(labels_path)\n")],
  ['test_lifecycle_proof_rejects_changed_real_inputs', 'test_lifecycle_proof_rejects_child_label_mutation', 'test_lifecycle_proof_rejects_child_workflow', 'test_lifecycle_proof_rejects_child_candidate']),
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load_tests():
    spec = importlib.util.spec_from_file_location('guard58tests', ROOT / E / 'test_verify_amendment.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_tests(copy, tests):
    command = [sys.executable, '-B', '-I', '-m', 'unittest', 'discover', '-s', str(E), '-p', 'test_*.py']
    for test in tests:
        command += ['-k', test]
    start = time.monotonic()
    run = subprocess.run(command, cwd=copy, capture_output=True)
    lines = run.stderr.decode(errors='replace').splitlines()
    ran = [int(m[1]) for m in (re.fullmatch(r'Ran (\d+) tests? in [\d.]+s', l) for l in lines) if m]
    return {'tests': tests, 'exitCode': run.returncode, 'testsRan': ran[0] if len(ran) == 1 else None,
            'summary': [l for l in lines if l.startswith(('Ran ', 'OK', 'FAILED', 'NO TESTS RAN'))],
            'assertions': sorted({l[:240] for l in lines if l.startswith('AssertionError')}),
            'stderrSha256': digest(run.stderr), 'elapsedSeconds': round(time.monotonic() - start, 3)}


def main():
    module = load_tests()
    sources = sorted({path for _, edits, _ in M for path, _, _ in edits})
    before = {path: (ROOT / path).read_bytes() for path in sources}
    selected = list(dict.fromkeys(test for _, _, tests in M for test in tests))
    with module.workspace_view(pending=False) as copy:
        baseline = run_tests(copy, selected)
    baseline['passed'] = baseline['exitCode'] == 0 and (baseline['testsRan'] or 0) >= 1 and baseline['summary'][-1:] == ['OK']
    print(baseline['passed'], 'unmutated baseline', baseline['summary'], flush=True)
    results = []
    for name, edits, tests in M:
        with module.workspace_view(pending=False) as copy:
            for path, old, new in edits:
                text = (copy / path).read_text(encoding='utf-8')
                if text.count(old) != 1:
                    raise SystemExit(f'{name}: mutation anchor not unique in {path}')
                (copy / path).write_text(text.replace(old, new), encoding='utf-8')
            result = run_tests(copy, tests)
        result['detected'] = (result['exitCode'] != 0 and (result['testsRan'] or 0) >= 1
                              and any(re.fullmatch(r'FAILED \(failures=\d+\)', l) for l in result['summary'])
                              and bool(result['assertions']))
        results.append({'mutation': name, **result})
        print(result['detected'], name, result['summary'], flush=True)
    after = {path: (ROOT / path).read_bytes() for path in sources}
    report = {'isolation': 'each run uses a fresh workspace_view(pending=False) copy; real sources are never written',
              'baseline': baseline, 'mutations': results,
              'allDetected': baseline['passed'] and all(r['detected'] for r in results),
              'realSourcesUnchanged': before == after,
              'realSourceSha256': {str(path): digest(data) for path, data in after.items()}}
    OUT.write_text(json.dumps(report, indent=2) + '\n')
    print('allDetected', report['allDetected'], 'realSourcesUnchanged', report['realSourcesUnchanged'])
    return 0 if report['allDetected'] and report['realSourcesUnchanged'] else 1


if __name__ == '__main__':
    sys.exit(main())
