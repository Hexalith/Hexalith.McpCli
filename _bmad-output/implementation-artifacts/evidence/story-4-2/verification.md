# Story 4.2 static verification

Run this complete block from the McpCli repository root with Python 3 and Git.
It reads the pinned Folders checkout without editing, restoring, building or
updating it. The parser recognizes this source revision's explicit command
registrations; refresh it with the inventory if that source shape changes.

These checks verify inventory completeness, normalized target reuse, explicit
exclusions, source-backed operation/wire mappings and the recorded session approval.
The two in-memory mutation checks reject swapped ordinary targets and invented
command names/types/wires. They do not establish Catalog
coverage, package compliance, live effects, authorization parity, an external
maintainer's approval or retirement readiness. No .NET build is required for
this Markdown/YAML-only change.

```bash
set -e
python3 - <<'PY'
from pathlib import Path
from collections import Counter
import re
import subprocess
import xml.etree.ElementTree as ET

root = Path.cwd()
base = root / '_bmad-output/implementation-artifacts'
up = root / 'references/Hexalith.Folders'
snapshot = 'e2252f29a2dba2b64786ee483eb59fbceaadd387'
approval_anchor = '#a1-session-approval-2026-10-16'
approval_ref = f'[A1]({approval_anchor})'
spec_name = 'spec-4-2-approve-the-folders-migration-inventory.md'
git = lambda *args: subprocess.check_output(['git', '-C', str(up), *args], text=True).strip()
assert git('rev-parse', 'HEAD') == snapshot
assert not git('status', '--porcelain')
s = (base / 'folders-migration-inventory-v1.md').read_text()
assert f"source_revision: '{snapshot}'" in s
assert 'status: approved\n' in s
assert f"maintainer_approval_ref: '{approval_anchor}'" in s
assert "inventory_version: '1.0.0'" in s
assert f"source_spec: '_bmad-output/implementation-artifacts/{spec_name}'" in s
assert '## A1 Session approval (2026-10-16)' in s
assert '"approve and stop"' in s and '"approve and stop"' in (base / spec_name).read_text()
assert 'Pending' not in s and 'Approval is pending' not in s

rows = {}
widths = dict(M=9, C=6, Q=6, R=8, L=9, V=6, N=6, G=4)
for line in s.splitlines():
    if re.match(r'^\| (?:[MCQRLVN]\d{2}|G\d) \|', line):
        cells = [c.strip() for c in line.strip('|').split('|')]
        assert cells[0] not in rows and len(cells) == widths[cells[0][0]] and all(cells), line
        assert approval_ref == cells[-1], line
        rows[cells[0]] = cells
counts = Counter(k[0] for k in rows)
assert counts == dict(M=49, C=13, Q=35, R=2, L=42, V=10, N=4, G=6), counts
for prefix,count in counts.items():
    expected = {f'{prefix}{i}' if prefix == 'G' else f'{prefix}{i:02d}' for i in range(1,count+1)}
    assert {k for k in rows if k.startswith(prefix)} == expected
for prefix in 'MRL':
    for cells in (v for k,v in rows.items() if k[0] == prefix):
        pos = 3 if prefix == 'L' else 2
        assert cells[pos:pos+2] == ['defer', 'exclude'], cells
for cells in (v for k,v in rows.items() if k[0] in 'VN'):
    assert cells[2] == 'defer / exclude', cells
assert 'All 13 candidates are deferred/excluded' in s
assert 'All 35 candidates are deferred/excluded' in s

names = lambda prefix, cell: [v[cell].strip('`') for k,v in rows.items() if k.startswith(prefix)]
pascal = lambda value: ''.join(w[0].upper()+w[1:] for w in value.split('-'))
for prefix in 'MCQL':
    assert len(names(prefix,1)) == len(set(names(prefix,1)))
tool_source = '\n'.join(p.read_text() for p in (up / 'src/Hexalith.Folders.Mcp/Tools').glob('*.cs'))
tool_names = re.findall(r'\[McpServerTool\(Name = "([^"]+)"\)\]', tool_source)
assert len(tool_names) == len(set(tool_names)) == 49
assert set(names('M',1)) == set(tool_names)
program = (up / 'src/Hexalith.Folders.Mcp/Program.cs').read_text()
assert '.WithToolsFromAssembly()' in program and '.WithResourcesFromAssembly()' in program
resource_sources = list((up / 'src/Hexalith.Folders.Mcp/Resources').glob('*.cs'))
resource_pairs = [re.search(r'Name = "([^"]+)"\s*,\s*UriTemplate = "([^"]+)"', p.read_text()).groups() for p in resource_sources]
assert len(resource_pairs) == len(set(resource_pairs)) == 2
assert set(resource_pairs) == {tuple(re.findall(r'`([^`]+)`',v[1])) for k,v in rows.items() if k.startswith('R')}

# Recognize explicit leaf registrations, validate their SDK links, and anchor each declaration.
actual_leaves = {}
expected_counts = dict(Provider=4, Folder=11, Workspace=8, File=3, Commit=5, Context=7, Audit=4)
cli_root = (up / 'src/Hexalith.Folders.Cli/CliApplication.cs').read_text()
assert set(re.findall(r'root.Subcommands.Add\((\w+)Command.Create\(pipeline, global\)\)',cli_root)) == set(expected_counts)
for group,expected in expected_counts.items():
    path = f'src/Hexalith.Folders.Cli/Commands/{group}/{group}Command.cs'
    source = (up / path).read_text()
    prefixes = dict(command=group.lower(), acl='folder acl', branchPolicy='folder branch-policy', timeline='audit timeline')
    matches = list(re.finditer(r'(\w+)\.Subcommands\.Add\((CommandFactory\.\w+|\w+)\(\s*"([^"]+)"',source))
    found = []
    for i,match in enumerate(matches):
        leaf = prefixes[match[1]] + ' ' + match[3]
        end = matches[i+1].start() if i+1 < len(matches) else len(source)
        body = source[match.end():end]
        if group == 'File':
            assert match[2] == 'Upload' and match[3] in ['add','change']
            assert f'FileMutationRequestFileOperationKind.{match[3].title()}' in body
            operation = match[3].title() + 'File'
        else:
            operation = re.search(r'client\.(\w+)Async\(',body)[1]
        found.append((leaf,operation,f'{path}:{source.count(chr(10),0,match.start(3))+1}'))
    if group == 'File':
        assert 'command.Subcommands.Add(Remove(pipeline, global))' in source
        match = re.search(r'return CommandFactory.Mutation\(\s*"(remove)"',source)
        assert 'client.RemoveFileAsync(' in source[match.end():]
        found.append(('file remove','RemoveFile',f'{path}:{source.count(chr(10),0,match.start(1))+1}'))
    assert len(found) == expected, (group,found)
    for leaf,operation,anchor in found:
        assert leaf not in actual_leaves
        actual_leaves[leaf] = (operation,anchor)
assert len(actual_leaves) == 42 and set(names('L',1)) == set(actual_leaves)
tool_rows = {v[1].strip('`'):v for k,v in rows.items() if k.startswith('M')}
for k,v in rows.items():
    if k.startswith('L'):
        operation,anchor = actual_leaves[v[1].strip('`')]
        linked = v[2].strip('`')
        assert linked in tool_rows and pascal(linked) == operation, v
        assert v[5] == tool_rows[linked][4] and v[7].strip('`') == anchor, v
helper_upload = (up / 'src/Hexalith.Folders.Client/Convenience/FoldersFileUploadExtensions.cs').read_text()
for kind in ['Add','Change']:
    assert re.search(rf'FileMutationRequestFileOperationKind\.{kind} => await client\s*\.{kind}FileAsync',helper_upload)

fixture = (up / 'tests/fixtures/parity-contract.yaml').read_text()
fixture_families = dict(re.findall(r"^- operation_id: '([^']+)'\n  operation_family: '([^']+)'",fixture,re.M))
assert len(fixture_families) == 49 and set(fixture_families) == {pascal(n) for n in tool_names}
assert set(fixture_families.values()) == {'mutating_command','audit','query_status','context_query','operations_console_projection'}
kind = lambda op: 'mutating_command' if fixture_families[op] == 'mutating_command' else 'read_query'
assert Counter(map(kind,fixture_families)) == dict(mutating_command=14,read_query=35)
assert Counter(kind(op) for op,anchor in actual_leaves.values()) == dict(mutating_command=14,read_query=28)
diagnostics = {n for n in tool_names if n.endswith('-diagnostics') or n == 'get-projection-freshness'}
assert len(diagnostics) == 7
assert {pascal(n) for n in diagnostics} == set(fixture_families) - {op for op,anchor in actual_leaves.values()}
for op in map(pascal,diagnostics):
    block = fixture.split(f"- operation_id: '{op}'",1)[1].split('\n- operation_id:',1)[0]
    assert 'non_policy_placeholder: true' in block

candidates = {k:v for k,v in rows.items() if k[0] in 'CQ'}
assert len(set(v[1] for v in candidates.values())) == len(set(v[2] for v in candidates.values())) == 48
used = set()
for k,v in rows.items():
    if k[0] in 'MRL':
        for ref in v[5 if k[0] == 'L' else 4].split(', '):
            assert ref in candidates, (k,ref)
            used.add(ref)
assert used == set(candidates)
assert all(tool_rows[n][4] == 'C10' for n in ['add-file','change-file','remove-file'])
assert tool_rows['update-folder-acl-entry'][4] == 'C08, C13'
assert rows['R01'][4] == tool_rows['list-audit-trail'][4] == 'Q28'
assert rows['R02'][4] == tool_rows['list-folder-files'][4] == 'Q30'
helper = (up / 'src/Hexalith.Folders.Client/Generated/HexalithFoldersIdempotencyHelpers.g.cs').read_text()
freshness = dict(re.findall(r'\["([^"]+)"\] = "(eventually_consistent|snapshot_per_task|read_your_writes)"',helper))
assert len(freshness) == 35
for k,v in candidates.items():
    intended = v[2].strip('`')
    kind = 'Commands' if k.startswith('C') else 'Queries'
    assert intended == f'Hexalith.Folders.Contracts.{kind}.{pascal(v[1].strip(chr(96)).split(".")[1])}'
    assert not (up / 'src/Hexalith.Folders.Contracts' / kind / (intended.rsplit('.',1)[1] + '.cs')).exists()
    if k.startswith('Q'):
        assert freshness[intended.rsplit('.',1)[1]] == v[3].strip('`')
    else:
        assert v[3].strip('`') == 'Hexalith.Folders.Commands.' + intended.rsplit('.',1)[1]
# Resolve command wires from the module, including the two aggregate-owned constants.
module_source = (up / 'src/Hexalith.Folders.Server/FoldersServerModule.cs').read_text()
command_wires = {}
for constant,expression in re.findall(r'public const string (\w+CommandType) = ([^;]+);',module_source):
    if expression.startswith('"'):
        command_wires[constant] = expression.strip('"')
    else:
        aggregate = expression.removesuffix('.CommandTypeName')
        aggregate_source = (up / f'src/Hexalith.Folders/Aggregates/Folder/{aggregate}.cs').read_text()
        command_wires[constant] = re.search(r'public const string CommandTypeName = "([^"]+)";',aggregate_source)[1]
processor = (up / 'src/Hexalith.Folders.Server/FolderDomainProcessor.cs').read_text()
dispatched = set(re.findall(r'if \(string.Equals\(command.CommandType, FoldersServerModule\.(\w+CommandType), StringComparison.Ordinal\)\)\s*\{\s*return await Process\w+Async\(command',processor))
assert len(dispatched) == 13
resource_operations = {re.search(r'Name = "([^"]+)"',p.read_text())[1]:re.search(r'client\.(\w+)Async\(',p.read_text())[1] for p in resource_sources}

def validate_operation_mappings(checked_rows):
    targets = {k:v for k,v in checked_rows.items() if k[0] in 'CQ'}
    for k,v in targets.items():
        if k.startswith('C'):
            constant = v[2].strip('`').rsplit('.',1)[1] + 'CommandType'
            assert constant in command_wires and constant in dispatched, (k,constant)
            assert v[3].strip('`') == command_wires[constant], (k,v[3])
    exceptions = dict(AddFile=['MutateFiles'],ChangeFile=['MutateFiles'],RemoveFile=['MutateFiles'],UpdateFolderAclEntry=['GrantFolderAccess','RevokeFolderAccess'])
    for k,v in checked_rows.items():
        if k[0] not in 'MRL':
            continue
        if k.startswith('M'):
            operation = pascal(v[1].strip('`'))
        elif k.startswith('L'):
            operation = actual_leaves[v[1].strip('`')][0]
        else:
            operation = resource_operations[re.findall(r'`([^`]+)`',v[1])[0]]
        expected = exceptions.get(operation,[operation])
        expected_kind = 'C' if fixture_families[operation] == 'mutating_command' else 'Q'
        refs = v[5 if k.startswith('L') else 4].split(', ')
        assert len(refs) == len(expected), (k,refs,expected)
        for ref,operation_name in zip(refs,expected):
            assert ref in targets and ref[0] == expected_kind, (k,ref,expected_kind)
            target = targets[ref]
            canonical = 'folders.' + re.sub(r'(?<!^)(?=[A-Z])','-',operation_name).lower()
            namespace = 'Commands' if expected_kind == 'C' else 'Queries'
            assert target[1].strip('`') == canonical, (k,ref,canonical)
            assert target[2].strip('`') == f'Hexalith.Folders.Contracts.{namespace}.{operation_name}', (k,ref,operation_name)

validate_operation_mappings(rows)
# Prove the ordinary mapping and invented-command regressions fail without editing files.
swapped = {k:list(v) for k,v in rows.items()}
for row_id in ['M16','M17','L15','L28']:
    cell = 5 if row_id.startswith('L') else 4
    swapped[row_id][cell] = {'Q02':'Q03','Q03':'Q02'}[swapped[row_id][cell]]
invented = {k:list(v) for k,v in rows.items()}
invented['C01'][1] = '`folders.archive-folder-invented`'
for cell in [2,3]:
    invented['C01'][cell] = invented['C01'][cell].replace('ArchiveFolder','ArchiveFolderInvented')
for label,mutated in [('Q02/Q03 swap on M16/M17/L15/L28',swapped),('invented C01 name/type/wire',invented)]:
    try:
        validate_operation_mappings(mutated)
    except AssertionError:
        print('PASS: rejected in-memory ' + label)
    else:
        raise AssertionError('Accepted invalid operation mapping: ' + label)
# End mapping-focused checks.

contracts = list((up / 'src/Hexalith.Folders.Contracts').rglob('*.cs'))
assert not any(re.search(r'\[Hexalith(?:Module|Command|Query)\b',p.read_text()) for p in contracts)
contracts_project = ET.parse(up / 'src/Hexalith.Folders.Contracts/Hexalith.Folders.Contracts.csproj')
assert not list(contracts_project.iter('PackageReference'))
assert not any('IDomainQueryHandler' in p.read_text() for p in (up / 'src').rglob('*.cs'))
endpoints = (up / 'src/Hexalith.Folders.Server/FoldersDomainServiceEndpoints.cs').read_text()
assert 'DomainProjectionDispatcher.Project(' in endpoints
for adapter in ['Mcp','Cli']:
    serializer = (up / f'src/Hexalith.Folders.{adapter}/Infrastructure/MetadataOnlyJson.cs').read_text()
    assert all('"'+field+'"' in serializer for field in ['contentBytes','inlineContent','streamDescriptor'])
# Verify exact declaration anchors for every MCP tool/resource.
for k,v in rows.items():
    if k[0] in 'MR':
        path,line = v[7 if k[0] == 'M' else 6].strip('`').rsplit(':',1)
        name = re.findall(r'`([^`]+)`',v[1])[0]
        declaration = (up / path).read_text().splitlines()[int(line)-1:int(line)+1]
        assert f'Name = "{name}"' in declaration[0 if k[0] == 'M' else 1]
        if k[0] == 'R':
            assert declaration[0].strip() == '[McpServerResource('
# Preserve the old snapshot verbatim beneath its historical successor notice.
draft = base / 'folders-migration-inventory-draft.md'
baseline = '09655746f9373dbb5df4bcea46c5d155902f2208'
historical = subprocess.check_output(['git','show',baseline+':'+str(draft.relative_to(root))])
assert draft.read_bytes().endswith(historical)
assert b'Historical, unapproved snapshot' in draft.read_bytes()
assert b'(folders-migration-inventory-v1.md)' in draft.read_bytes()
assert git('rev-parse','HEAD') == snapshot and not git('status','--porcelain')
# --no-index returns 1 for different, whitespace-clean files; whitespace errors add bit 2.
for artifact in ['folders-migration-inventory-v1.md',spec_name,'evidence/story-4-2/verification.md']:
    result = subprocess.run(['git','diff','--no-index','--check','--','/dev/null',str(base / artifact)],capture_output=True,text=True)
    assert result.returncode in [0,1] and not result.stdout and not result.stderr, (artifact,result)
print('PASS: clean pinned source; exact 49 tool, 2 resource and 42 CLI sets/mappings; 48 unique reused future targets; 10 variants, 4 adjacent exclusions, 6 owned prerequisites; all 161 rows reference A1 session approval; all legacy coverage deferred/excluded. Static scope only.')
PY
git diff --check
```

## Recorded execution and limits

- **Candidate checkpoint (2026-10-16):** the previous version of this checker
  passed against candidate 1.0.0-candidate.1 with all approval references pending.
  The user subsequently instructed "approve and stop"; that session approval is
  recorded in the spec. Candidate checks did not establish approval.
- **Final inventory verification (2026-10-16):** implementation and the complete
  block above passed with exit 0, including tracked and new-file whitespace
  checks. All 93 legacy surface rows remain
  `defer / exclude`; 48 future targets occur exactly once in the normalized
  tables and every target is reused by at least one legacy row. The ten variant
  rows, four adjacent exclusions and six owned prerequisite rows all refer to
  the same limited A1 approval as the surface and target rows.
- **Evidence still absent:** no decorated Contracts release/closure, built
  Catalog match, approved Gateway vectors, loopback behavior, live persisted
  effects, authorization/tenant isolation, query paging/freshness or retirement
  proof was supplied by this documentation change. Folders remains post-v1.
  Neither `/project` projection delivery nor matching operation names fills
  those gaps. No dry-run implementation was found in pinned `src/` or the
  parity fixture; the historical draft's claim is explicitly superseded.
- Git emits its existing `unable to find all commit-graph files` warnings.
  Record actual exit codes; those warnings are not validation failures.

The final run produced:

```text
PASS: clean pinned source; exact 49 tool, 2 resource and 42 CLI sets/mappings; 48 unique reused future targets; 10 variants, 4 adjacent exclusions, 6 owned prerequisites; all 161 rows reference A1 session approval; all legacy coverage deferred/excluded. Static scope only.
```

The complete Bash block was executed with `bash -e` through Python's
`subprocess.run(..., check=True)`. The Folders source revision and clean working
tree were checked before and after verification. Workflow review and final
spec/sprint status synchronization remain separate parent-session gates.

Review follow-up (2026-10-16) adds source-backed mapping and Command/Query kind
checks for every legacy row, resolves command wires from FoldersServerModule
and aggregate-owned constants, and requires real processor dispatch. The two
in-memory mutations change Q02/Q03 on M16/M17/L15/L28 and invent C01's canonical
name, intended type and wire together; neither mutation edits the inventory.
The variant corrections preserve A1's deferred scope and generic runtime rules.

Executed the revised documented Bash block with `bash -e` via
`subprocess.run(..., check=True)`: exit 0. Both targeted in-memory mutations
were rejected; the unchanged inventory passed the source/mapping checks. Only
these artifact checks were run for this follow-up; no .NET suites were run.

Parent completion (2026-10-16): the three review layers finished; eight findings
were corrected and two were rejected with evidence in the spec's Review Triage
Log. The parent executed the complete revised block with exit 0, including both
mutation rejections. No new work was deferred. The build spec is `done`; sprint
tracking is `review`, pending the separate story review transition. These are
inventory completion states and do not close any future Folders readiness gate.

Local commit validation (2026-10-16), after `npm ci`: the exact candidate
`docs(folders): finalize story 4.2 migration inventory` passed the owning repository's
pinned `npx --no -- commitlint --verbose` CLI with exit 0.

```text
⧗   --- input ---
docs(folders): finalize story 4.2 migration inventory
✔   found 0 problems, 0 warnings
exit_code: 0
```
