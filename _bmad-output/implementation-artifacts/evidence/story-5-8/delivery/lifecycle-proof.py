"""Prove suite independence from synthetic lifecycle metadata, not real completion."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
SCRIPT = Path(__file__).resolve()
PACKET = Path('_bmad-output/implementation-artifacts/evidence/story-5-8')


def load_tests(root):
    spec = importlib.util.spec_from_file_location('lifecycle58', root / PACKET / 'test_verify_amendment.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(*, root=None, delivery=None):
    root = SCRIPT.parents[5] if root is None else Path(root)
    delivery = SCRIPT.parent if delivery is None else Path(delivery)
    module = load_tests(root)
    B = module.B
    protected = [B.NEW, B.E / 'approval.json', B.E / 'labels.json', B.SPEC, B.ART / 'sprint-status.yaml']
    before = {str(path): (root / path).read_bytes() for path in protected}
    with module.workspace_view(pending=False) as fixture:
        approval_path = fixture / B.E / 'approval.json'
        approval = module.V.read_json(approval_path)
        approval.update(decision='approved', approver='Synthetic lifecycle fixture owner',
                        exactApprovalInstruction='Synthetic fixture approval only',
                        approvalSource='Isolated lifecycle test, no real authority',
                        approvedOn='2026-11-13', rolesCovered=B.ROLES[:])
        approval_path.write_text(json.dumps(approval, indent=2) + '\n')
        labels_path = fixture / B.E / 'labels.json'
        labels = module.V.read_json(labels_path)
        labels.update(state='integrated', inventoryRevision=B.git(root, 'rev-parse', 'HEAD').decode().strip(),
                      deliveryAuthorization={'exactWords': 'Synthetic fixture delivery',
                                             'source': 'Isolated lifecycle test only', 'approvedOn': '2026-11-13'})
        labels['repository']['integration'] = {'commit': B.LABEL_PIN,
                                              'commitSha256': B.sha(B.git(Path(labels['repository']['ownerCheckout']), 'cat-file', 'commit', B.LABEL_PIN))}
        labels_path.write_text(json.dumps(labels, indent=2) + '\n')
        for path, key in [(fixture / B.SPEC, 'status'),
                          (fixture / B.ART / 'sprint-status.yaml', '  5-8-refresh-and-re-disposition-the-folders-inventory')]:
            module.workflow_status(path, key, 'done')
        module.V.require(module.V.read_json(approval_path)['decision'] == 'approved',
                         'synthetic lifecycle approval is not approved')
        module.V.require(module.V.read_json(labels_path)['state'] == 'integrated',
                         'synthetic lifecycle labels are not integrated')
        module.V.require(module.V.completion_requested(fixture, False),
                         'synthetic lifecycle workflow is not done')
        module.V.require((fixture / B.NEW).read_bytes() == before[str(B.NEW)],
                         'synthetic lifecycle candidate bytes changed')
        command = [sys.executable, '-I', '-m', 'unittest', 'discover', '-v',
                   '-s', str(PACKET), '-p', 'test_*.py']
        result = subprocess.run(command, cwd=fixture, capture_output=True)
        captures = {}
        for stream in ['stdout', 'stderr']:
            name = 'lifecycle-integrated.' + stream + '.txt'
            data = getattr(result, stream)
            (delivery / name).write_bytes(data)
            captures[stream] = {'path': name, 'sha256': hashlib.sha256(data).hexdigest()}
        after_fixture = module.V.read_json(approval_path), module.V.read_json(labels_path)
        module.V.require(after_fixture[0] == approval and after_fixture[1] == labels,
                         'synthetic lifecycle receipt or labels changed during child run')
        module.V.require(module.V.completion_requested(fixture, False),
                         'synthetic lifecycle workflow changed during child run')
    after = {str(path): (root / path).read_bytes() for path in protected}
    real_inputs_unchanged = before == after
    if not real_inputs_unchanged:
        raise ValueError('real candidate/receipt/workflow bytes changed')
    summary = {'suiteExitCode': result.returncode,
               'claim': 'Suite independence from synthetic lifecycle metadata; real approved-completion is verified separately.',
               'sourceFixture': 'approved / integrated / spec done / sprint done',
               'realInputsUnchanged': real_inputs_unchanged,
               'candidateSha256': hashlib.sha256(before[str(B.NEW)]).hexdigest(),
               'child': {'command': command, 'cwd': '.', 'cwdBase': 'isolated synthetic lifecycle workspace created by this helper'},
               'helper': {'command': ['python3', '-B', '-I', str(SCRIPT.relative_to(root))],
                          'cwd': '.', 'cwdBase': 'repository root containing this retained script'},
               **captures}
    (delivery / 'lifecycle-integrated.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))
    print('\n'.join(result.stderr.decode(errors='replace').splitlines()[-5:]))
    return result.returncode


if __name__ == '__main__':
    sys.exit(main())
