import gzip
import json
from pathlib import Path
import re
import subprocess
import yaml

root = Path('/home/administrator/projects/hexalith/mcpcli')
base = 'a133f603790375ff51a03f3d0844c7218da36ced'
artifact = root / '_bmad-output/implementation-artifacts'
spec = artifact / 'spec-4-5-gate-module-coverage-against-the-approved-inventory.md'
sprint = artifact / 'sprint-status.yaml'
retro = artifact / 'epic-4-retro-2026-11-06.md'
evidence = artifact / 'evidence/epic-4-retro-item-4-f4'

def previous(path):
    return subprocess.check_output(['git', 'show', base + ':' + str(path.relative_to(root))], cwd=root).decode()

def frontmatter(text):
    return yaml.safe_load(text.split('---', 2)[1])

assert frontmatter(spec.read_text())['status'] == 'done'
assert '- [ ] [Review][Patch]' not in spec.read_text()
second = spec.read_text().split('### Review Findings (second pass)', 1)[1].split('#### Rejected (second pass)', 1)[0]
assert second.count('- [x] [Review][Patch]') == 7
pattern = r'<frozen-after-approval[\s\S]*?</frozen-after-approval>'
assert re.search(pattern, previous(spec)).group() == re.search(pattern, spec.read_text()).group()
assert frontmatter(retro.read_text()) == frontmatter(previous(retro))
assert frontmatter(retro.read_text())['verdict'] == 'rejected'
before = yaml.safe_load(previous(sprint))
after = yaml.safe_load(sprint.read_text())
item = next(item for item in before['action_items'] if item.get('id') == 'epic-4-retro-item-4-finish-story-4-5')
assert item['status'] == 'open'
item['status'] = 'done'
assert before == after, 'Only retrospective item 4 may change parsed sprint state.'
assert after['development_status']['4-5-gate-module-coverage-against-the-approved-inventory'] == 'done'
for sha in ['9b44fe2026efa4b9234dd6a5c53e068b752a1837', '078fd22bbbe591d6b912fa6e33967b174b61379a', '27ad6b75689bbcf56f424ab40c786f7e9c3fc5bb', base]:
    subprocess.run(['git', 'merge-base', '--is-ancestor', sha, 'HEAD'], cwd=root, check=True)
test = root / 'tests/Hexalith.McpCli.Core.Tests/InventoryCoverageTests.cs'
assert b'\n' not in test.read_bytes().replace(b'\r\n', b'')
gate = root / 'tests/Hexalith.McpCli.Core.Tests/InventoryCoverageGate.cs'
assert gate.read_bytes() == subprocess.check_output(['git', 'show', base + ':' + str(gate.relative_to(root))], cwd=root)
for file in [spec, retro, evidence / 'README.md', root / 'tools/inventory-coverage/v1/README.md']:
    for target in re.findall(r'\]\(([^)]+)\)', file.read_text()):
        if not target.startswith(('http:', 'https:', '#')):
            assert (file.parent / target.split('#', 1)[0]).exists(), (file, target)
for file in evidence.glob('*.json'):
    receipt = json.loads(file.read_text())
    if 'command' in receipt and file.stem != 'closure-documentation-check-initial':
        assert receipt['exit_code'] == 0, file
mutations = json.loads((evidence / 'mutations/commands.json').read_text())
failed = [entry for entry in mutations if entry['exit_code'] == 1]
assert len(failed) == 6
assert all(entry['exit_code'] in (0, 1) for entry in mutations)
for entry in mutations:
    retained = evidence / 'mutations' / (Path(entry['log']).name + '.gz')
    output = gzip.decompress(retained.read_bytes()).decode()
    if entry['exit_code'] == 1:
        assert output.count('[FAIL]') == 1, retained
subprocess.run(['git', 'diff', '--check'], cwd=root, check=True)
print('PASS: seven checked patches; done statuses; preserved frozen intent, verdict, other sprint state and named commits; unchanged gate; CRLF; local links; all normal receipts green; six expected mutant failures; diff whitespace.')
