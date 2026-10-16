# Story 4.1 verification evidence

This preserves the complete one-off source/row checker previously run from
`/tmp/validate-parties-inventory-4-1.py`, with repository-relative paths. Run the
following block from the McpCli repository root with Python 3 and Git. The
root-declared Parties checkout must already be present, clean and at the pinned
revision; the checker does not initialize or update any submodule.

This checks static inventory completeness and whitespace only. It does not
execute Gateway calls or prove the authorization, error privacy, validation,
EntityId routing or repeated-deactivation cases assigned to Stories 4.9–4.13.
No test framework, CI gate, runtime change or retirement authorization is added.

```bash
python3 - <<'PY'
from pathlib import Path
import re
import subprocess

root = Path('.')
parties = root / 'references/Hexalith.Parties'
revision = '493730941329d1bca3b4f6b2f6a67ffe305c2443'
def git(*args):
    return subprocess.check_output(['git', '-C', str(parties), *args], text=True).strip()
assert git('rev-parse', 'HEAD') == revision
assert git('status', '--porcelain') == ''
text = (root / '_bmad-output/implementation-artifacts/parties-migration-inventory-v1.md').read_text()
assert "inventory_version: '1.0.0'" in text and 'status: approved' in text
assert "maintainer_approval_ref: '#a1-session-approval-2026-10-16'" in text
assert revision in text
assert '**Exact instruction:** "apply recommended"' in text
rows = {}
for line in text.splitlines():
    if re.match(r'\| [LTNC]\d\d(?: /| \|)', line):
        cells = [cell.strip() for cell in line.strip('|').split('|')]
        key = cells[0].split(' /')[0]
        assert key not in rows, key
        assert all(cells), key
        assert cells[-1] == '[A1](#a1-session-approval-2026-10-16)', key
        rows[key] = cells
assert set(rows) == ({f'L{i:02}' for i in range(1, 6)} | {f'T{i:02}' for i in range(1, 8)} | {f'N{i:02}' for i in range(1, 5)} | {f'C{i:02}' for i in range(1, 9)})
constants = (parties / 'src/Hexalith.Parties.Mcp/Tools/PartiesMcpToolNames.cs').read_text()
source_names = dict(re.findall(r'const string (\w+) = "([^"]+)";', constants))
assert len(source_names) == 5
legacy_names = {re.search(r'`([^`]+)`', rows[f'L{i:02}'][1])[1] for i in range(1, 6)}
assert legacy_names == set(source_names.values())
tools = (parties / 'src/Hexalith.Parties.Mcp/Tools/PartiesMcpTools.cs').read_text()
attributes = re.findall(r'\[McpServerTool\(Name = PartiesMcpToolNames\.(\w+),', tools)
assert len(attributes) == 5 and set(attributes) == set(source_names)
assert 'if (!string.IsNullOrWhiteSpace(query))' in tools
assert '.SearchPartiesAsync(query.Trim(), page, pageSize, cancellationToken)' in tools
assert '.ListPartiesAsync(' in tools
contract_tests = (parties / 'tests/Hexalith.Parties.Mcp.Tests/PartiesMcpToolContractTests.cs').read_text()
expected = re.search(r'toolNames.ShouldBe\(\[(.*?)\]\);', contract_tests, re.S)[1]
assert set(re.findall(r'"([^"]+)"', expected)) == legacy_names
program = (parties / 'src/Hexalith.Parties.Mcp/Program.cs').read_text()
assert '.WithToolsFromAssembly();' in program
names, types, used = [], [], set()
for i in range(1, 6):
    cells = rows[f'L{i:02}']
    assert cells[2:4] == ['replace', 'include']
    targets = re.findall(r'T\d\d', cells[4])
    assert targets and all(target in rows for target in targets)
    used.update(targets)
assert used == {f'T{i:02}' for i in range(1, 8)}
for i in range(1, 5):
    assert rows[f'N{i:02}'][2] == 'defer / exclude'
for i in range(1, 8):
    cells = rows[f'T{i:02}']
    assert len(cells) == 6
    names.append(cells[1])
    clr_type = re.search(r'`([^`]+)`', cells[2])[1]
    types.append(clr_type)
    namespace, type_name = clr_type.rsplit('.', 1)
    kind = namespace.rsplit('.', 1)[1]
    source = parties / f'src/Hexalith.Parties.Contracts/{kind}/{type_name}.cs'
    if i <= 3:
        assert '(new)' in cells[2] and not source.exists()
    else:
        dto = source.read_text()
        assert f'namespace {namespace};' in dto
        assert re.search(rf'\brecord {type_name}\b', dto)
        assert 'required string PartyId' in dto
assert len(set(names)) == len(set(types)) == 7
assert 'A0' not in text and "1.0.0-proposed" not in text
files = [Path(path) for path in git('ls-files', 'src', 'Hexalith.Parties.slnx').splitlines()]
source_text = '\n'.join((parties / path).read_text(errors='replace') for path in files if path.suffix in {'.cs', '.csproj', '.slnx'})
assert not re.search(r'McpServerResource|WithResources', source_text)
assert not re.search(r'System\.CommandLine|Spectre\.Console\.Cli|CommandLineApplication|new RootCommand\b', source_text)
assert git('rev-parse', 'HEAD') == revision and git('status', '--porcelain') == ''
print('PASS: pinned clean source; five tool names/attributes/test names; both find branches; seven unique targets (four existing Commands, three missing Queries); four deferrals; all 24 rows complete and linked to A1; valid disposition/coverage pairs; no resources or proprietary CLI declarations.')

# Whitespace checks include new/untracked artifacts without staging them.
edited = [
    '_bmad-output/implementation-artifacts/parties-migration-inventory-v1.md',
    '_bmad-output/implementation-artifacts/evidence/story-4-1/verification.md',
]
subprocess.run(['git', 'diff', '--check', '--', *edited], check=True)
for path in edited:
    check = subprocess.run(
        ['git', 'diff', '--no-index', '--check', '--', '/dev/null', path],
        capture_output=True, text=True,
    )
    # Exit 1 is the expected new-file difference; whitespace errors emit diagnostics.
    assert check.returncode in (0, 1) and not check.stdout and not check.stderr, (
        path, check.returncode, check.stdout, check.stderr,
    )
print('PASS: inventory and supporting evidence have no whitespace diagnostics.')
PY
```

Execution on 2026-10-16: PASS. The source remained clean at
`493730941329d1bca3b4f6b2f6a67ffe305c2443`; five registered tools and both find
branches matched the inventory and contract-test expectations. Seven distinct
targets comprise four existing Command DTOs and three absent intended Query
files. All 24 legacy/target/compatibility/exclusion rows were complete and linked
to A1, all disposition/coverage pairs were valid, and the source scan found no
MCP resources or proprietary CLI declarations. Both edited Markdown files
produced no whitespace diagnostics; no-index exit 1 denotes expected file
differences. Git's existing missing commit-graph warnings do not change the
successful check result.

Commit-message validation used the repository's locked tooling after `npm ci`:
`@commitlint/cli@21.2.2`, invoked as `npx --no -- commitlint --verbose` with the
complete candidate on stdin:

```text
docs(parties): approve story 4.1 migration inventory
```

Result: exit 0, `found 0 problems, 0 warnings`. The exact message and validator
output were also preserved in `/tmp/mcpcli-story-4-1-commit-message.txt` and
`/tmp/mcpcli-story-4-1-commitlint.log` before creating the local commit.
