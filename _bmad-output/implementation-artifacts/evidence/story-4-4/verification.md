# Story 4.4 candidate verification

Date: 2026-10-17. Current workflow state: spec and sprint story `ready-for-dev`.
The requesting user approved the deferred session scope with "approve and stop";
the source spec records that decision. Candidate finalization and review remain
pending; the candidate row metadata below still describes pre-finalization state.
This is repeatable planning evidence for the pending-approval candidates,
not a completed story, maintainer sign-off or live migration test.

- [Spec](../../spec-4-4-approve-chatbot-and-memories-migration-inventories.md)
- [ChatBot candidate](../../chatbot-migration-inventory-v1.md)
- [Memories candidate](../../memories-migration-inventory-v1.md)

The root source revision at planning entry was
`c8d32f181d9035acc93b884a5b6554784c8e5f5b`. ChatBot source is pinned to
`acc934599cf1efff36b0643eddc6a3cc4c2978d5`; Memories source is pinned to
`f6b60d5a2e9b81d84fddad789c7d9bed40d3a533`. Both owning checkouts were clean.
The root was clean at the initial check. Other work subsequently changed root
reference pointers, including Memories from tracked
`2a2daacaf39f08503a3f8bd93c665912a68d4abd` to its inspected pin. These changes
were preserved; this story makes no Git-state or upstream changes. Candidate
checks use actual inspected source pins, not a claim those pointer changes have
been approved or committed.

A separate workspace sync subsequently advanced root HEAD to
`b35b0975a234f1f97e2e35e9dad381d0a988f4af`, recording the external reference
changes and an earlier draft of this story's spec. The current working spec
contains the completed source-investigation corrections. This build run did
not stage or create that commit; it preserves the concurrent work.

## Repeatable candidate checks

Run this complete block from the McpCli root. It uses Python's standard library
and read-only Git/source commands. It independently derives registered tool and
CLI sets, cross-checks ChatBot metadata, distinguishes Memories stubs, validates
all concrete rows and the explicit variant/exclusion sets, checks pending
approval and source references, and rejects invalid in-memory mutations.
It also checks the actual scoped Memories client/bearer and exact tenant-membership
source seams supporting the identity gate. It does not execute a tool, CLI
operation, workflow, import/export, deletion, dependency restore or service call.

```bash
set -euo pipefail
python3 - <<'PY_CANDIDATE'
from collections import Counter
from pathlib import Path
import re
import subprocess

root = Path.cwd()
base = root / '_bmad-output/implementation-artifacts'
pins = {
    'chatbot': ('Hexalith.ChatBot', 'acc934599cf1efff36b0643eddc6a3cc4c2978d5'),
    'memories': ('Hexalith.Memories', 'f6b60d5a2e9b81d84fddad789c7d9bed40d3a533'),
}

def source(module, project, filename):
    repo = pins[module][0]
    return (root / 'references' / repo / 'src' / (repo + '.' + project) / filename).read_text()

def check_pins():
    for repo, sha in pins.values():
        checkout = root / 'references' / repo
        assert subprocess.check_output(['git', '-C', str(checkout), 'rev-parse', 'HEAD'], text=True).strip() == sha, repo
        assert not subprocess.check_output(['git', '-C', str(checkout), 'status', '--porcelain'], text=True).strip(), repo

def chatbot_sets():
    tools = re.findall(r'\[McpServerTool\(Name = "([^"]+)"', source('chatbot', 'Mcp', 'ChatBotMcpTools.cs'))
    catalog = re.findall(r'(?:Read|Write)\(\s*"([^"]+)"', source('chatbot', 'Mcp', 'ChatBotMcpToolCatalog.cs'))
    assert len(tools) == 12 and Counter(tools) == Counter(catalog)
    cli = source('chatbot', 'Cli', 'ChatBotCliCommands.cs')
    wired = re.findall(r'root.Subcommands.Add\((Build\w+Command)\(service\)\)', cli)
    leaves = []
    for method in wired:
        block = re.search(r'private static Command ' + method + r'\([^)]*\)\s*\{(.*?)\n    \}', cli, re.S).group(1)
        group = re.search(r'var (\w+) = new Command\("([^"]+)"', block)
        leaf_map = dict(re.findall(r'Command (\w+) = Leaf\("([^"]+)"', block))
        if group is None:
            assert len(leaf_map) == 1 and not re.search(r'\.Subcommands.Add', block)
            leaves.extend(leaf_map.values())
            continue
        added = re.findall(group[1] + r'\.Subcommands.Add\((\w+)\)', block)
        assert set(added) == set(leaf_map) and len(added) == len(leaf_map)
        leaves.extend(group[2] + ' ' + leaf_map[var] for var in added)
    assert len(leaves) == 12
    return tools, leaves

def memories_sets():
    composition = source('memories', 'Mcp', 'McpCompositionRoot.cs')
    tools = []
    for cls in re.findall(r'\.WithTools<(\w+)>\(\)', composition):
        tools.extend(re.findall(r'\[McpServerTool\(Name = "([^"]+)"', source('memories', 'Mcp', 'Tools/' + cls + '.cs')))
    assert len(tools) == 4
    cli = source('memories', 'Cli', 'Commands/RootCommandFactory.cs')
    groups = dict(re.findall(r'var (\w+) = new Command\("([^"]+)"', cli))
    leaves = []
    for parent, cls in re.findall(r'(\w+)\.Subcommands.Add\((\w+)\.Build\(services\)\)', cli):
        leaf = re.search(r'(?:var|Command) command = new(?: Command)?\("([^"]+)"', source('memories', 'Cli', 'Commands/' + cls + '.cs'))[1]
        assert parent == 'root' or 'root.Subcommands.Add(' + parent + ')' in cli
        leaves.append((groups[parent] + ' ' if parent != 'root' else '') + leaf)
    stub_block = re.search(r'CommandGroups =\s*\[(.*?)\];', cli, re.S)[1]
    stubs = re.findall(r'\("([^"]+)", "[^"]+", "[^"]+"\)', stub_block)
    assert len(leaves) == 14 and len(stubs) == 4
    assert 'root.Subcommands.Add(NotImplementedCommand.Create(services, name, description, storyId))' in cli
    return tools, leaves, stubs

def rows(text, prefix):
    return [[cell.strip() for cell in line.strip().strip('|').split('|')]
            for line in text.splitlines() if re.match(r'\| ' + prefix + r'\d+ \|', line)]

def metadata(text, key):
    return re.search(r'^' + key + r':\s*(.*?)\s*$', text.split('---', 2)[1], re.M)[1].strip("'\"")

def validate(module, text, expected):
    assert metadata(text, 'inventory_version') == '1.0.0-candidate.1'
    assert metadata(text, 'status') == 'pending-approval'
    assert metadata(text, 'approval_status') == 'pending'
    assert metadata(text, 'approval_authority') == 'unasserted'
    assert metadata(text, 'external_maintainer_approval') == 'unasserted'
    assert metadata(text, 'source_revision') == pins[module][1]
    assert metadata(text, 'module') == module
    assert metadata(text, 'source_spec') == '_bmad-output/implementation-artifacts/spec-4-4-approve-chatbot-and-memories-migration-inventories.md'
    assert '#a0-approval-required' in text and '## A0 Approval required' in text
    all_rows = []
    for prefix, names in expected.items():
        actual = rows(text, prefix)
        assert len(actual) == len(names), (module, prefix, 'count')
        assert Counter(row[0] for row in actual) == Counter(f'{prefix}{n:02}' for n in range(1, len(names) + 1)), (module, prefix, 'ids')
        assert Counter(row[1].strip('`') for row in actual) == Counter(names), (module, prefix, 'surface set')
        for row in actual:
            assert len(row) == 8 and row[2:4] == ['defer', 'exclude'], row
            assert all(row[4:7]) and row[-1] == '[A0](#a0-approval-required)', row
        all_rows.extend(actual)
    for prefix in ('V', 'X'):
        actual = rows(text, prefix)
        count = {'chatbot': {'V': 15, 'X': 4}, 'memories': {'V': 17, 'X': 6}}[module][prefix]
        assert Counter(row[0] for row in actual) == Counter(f'{prefix}{n:02}' for n in range(1, count + 1)), (module, prefix)
        for row in actual:
            assert 'defer / exclude' in row and row[-1] == '[A0](#a0-approval-required)', row
    assert 'no Gateway-ready decorated replacement' in text
    if module == 'memories':
        assert 'not deletable before the HTTP release supports forwarded per-user identity' in text
        assert 'ingestedBy' in text and 'bearer' in text and 'tenant list' in text
    else:
        assert all(term in text for term in ('commandCorrelationId', 'taskIntentId', 'StateOwnerAggregateId', 'actor', 'tenant'))
        pairs = {m[0][1:]: m[1].strip('`').removeprefix('chatbot.').replace('ai_action', 'ai-action').replace('.', ' ')
                 for m in rows(text, 'M')}
        pairs = {key: ('conversation' if value == 'conversation get' else value) for key, value in pairs.items()}
        assert all(row[1].strip('`') == pairs[row[0][1:]] for row in rows(text, 'L')), 'CLI/MCP row association'

def check_source_anchors(module, text):
    repo = pins[module][0]
    aliases = {part: root / 'references' / repo / 'src' / (repo + '.' + part)
               for part in ('Mcp', 'Cli', 'Contracts', 'Server', 'Client', 'Client.Rest', 'EventStore')}
    if module == 'memories':
        aliases['Client'] = aliases['Client.Rest']
    anchors = re.findall(r'`((?:(?:Mcp|Cli|Contracts|Server|Client(?:\.Rest)?|EventStore)/[^`]+|README\.md)):([0-9]+)`', text)
    assert anchors, module
    for rel, number in anchors:
        if '/' in rel:
            alias, path = rel.split('/', 1)
            target = aliases[alias] / path
        else:
            target = root / 'references' / repo / rel
        lines = target.read_text().splitlines()
        assert 0 < int(number) <= len(lines) and lines[int(number) - 1].strip(), (module, rel, number)
    for destination in re.findall(r'\]\(([^)]+)\)', text):
        if not destination.startswith(('#', 'https://')):
            assert (base / destination.split('#', 1)[0]).is_file(), destination

check_pins()
chat_tools, chat_cli = chatbot_sets()
memory_tools, memory_cli, memory_stubs = memories_sets()
expected = {
    'chatbot': {'M': chat_tools, 'L': chat_cli},
    'memories': {'M': memory_tools, 'L': memory_cli, 'S': memory_stubs},
}
spec_path = base / 'spec-4-4-approve-chatbot-and-memories-migration-inventories.md'
spec_text = spec_path.read_text()
assert metadata(spec_text, 'status') == 'ready-for-dev'
assert 'The requesting user answered "approve and\nstop"' in spec_text
assert re.search(r'^  4-4-approve-chatbot-and-memories-migration-inventories: ready-for-dev$', (base / 'sprint-status.yaml').read_text(), re.M)
composition = source('memories', 'Mcp', 'McpCompositionRoot.cs')
assert 'services.AddScoped<MemoriesClient>' in composition
assert 'ApplyServerUpstreamBearer(sp, invokeClient)' in composition
assert 'invokeClient.DefaultRequestHeaders.Authorization = parsed;' in composition
tenant_filter = source('memories', 'Mcp', 'Authentication/TenantClaimAuthorizationFilter.cs')
assert 'user.Identity?.IsAuthenticated != true' in tenant_filter
assert 'string.Equals(value, tenantId, StringComparison.Ordinal)' in tenant_filter
for module in pins:
    text = (base / (module + '-migration-inventory-v1.md')).read_text()
    validate(module, text, expected[module])
    check_source_anchors(module, text)
    m = rows(text, 'M')[0]
    line = next(line for line in text.splitlines() if line.startswith('| ' + m[0] + ' |'))
    mutations = {
        'missing row': text.replace(line + '\n', '', 1),
        'duplicate row': text + '\n' + line + '\n',
        'invented surface': text.replace(line, line.replace(m[1], '`invented.surface`'), 1),
        'unsupported inclusion': text.replace('| defer | exclude |', '| replace | include |', 1),
        'false approval': text.replace('approval_status: pending', 'approval_status: approved', 1),
        'invented owner sign-off': text.replace('external_maintainer_approval: unasserted', 'external_maintainer_approval: approved', 1),
        'missing variant': '\n'.join(line for line in text.splitlines() if not line.startswith('| V01 |')) + '\n',
        'duplicate exclusion': text + '\n' + next(line for line in text.splitlines() if line.startswith('| X01 |')) + '\n',
    }
    if module == 'chatbot':
        first, second = rows(text, 'L')[:2]
        mutations['swapped CLI associations'] = text.replace(first[1], '`__swap__`').replace(second[1], first[1]).replace('`__swap__`', second[1])
    if module == 'memories':
        mutations['weakened identity gate'] = text.replace('not deletable before the HTTP release supports forwarded per-user identity', 'deletable now')
    for name, mutant in mutations.items():
        try:
            validate(module, mutant, expected[module])
        except AssertionError:
            continue
        raise AssertionError((module, 'accepted ' + name))
    print(f'PASS {module}: exact source surface sets, row metadata, approval state, source anchors and {len(mutations)} negative mutations.')
    contracts = root / 'references' / pins[module][0] / 'src' / (pins[module][0] + '.Contracts')
    for path in contracts.rglob('*.cs'):
        if not {'bin', 'obj'}.intersection(path.parts):
            assert not re.search(r'\[\s*(?:assembly:\s*)?Hexalith(?:Module|Command|Query)(?:Attribute)?\s*\(', path.read_text()), path
    mcp = root / 'references' / pins[module][0] / 'src' / (pins[module][0] + '.Mcp')
    for path in mcp.rglob('*.cs'):
        if not {'bin', 'obj'}.intersection(path.parts):
            assert not re.search(r'With(?:Resources|Prompts)|\[McpServer(?:Resource|Prompt)', path.read_text()), path
check_pins()
for path in (spec_path, base / 'chatbot-migration-inventory-v1.md', base / 'memories-migration-inventory-v1.md', base / 'evidence/story-4-4/verification.md'):
    if path.exists():
        content = path.read_bytes()
        assert content.endswith(b'\n'), path
        assert all(line == line.rstrip() for line in content.decode('utf-8').splitlines()), path
print('PASS: 42 implemented surfaces and 4 executable stubs; candidate evidence only. Approval and live parity remain unproven.')
PY_CANDIDATE
git diff --check
```

## Recorded result and limits

The complete Bash block above was executed through Python
`subprocess.run(['bash', '-e'], input=block, text=True)` and exited 0.

```text
PASS chatbot: exact source surface sets, row metadata, approval state, source anchors and 9 negative mutations.
PASS memories: exact source surface sets, row metadata, approval state, source anchors and 9 negative mutations.
PASS: 42 implemented surfaces and 4 executable stubs; candidate evidence only. Approval and live parity remain unproven.
```

ChatBot has 12 MCP and 12 CLI rows, 15 compatibility variants and four adjacent
exclusions. Memories has four MCP tools, 14 implemented CLI leaves, four
executable stubs, 17 variants and six adjacent exclusions. All **88 scope rows**
reference pending A0; none is included or approved. The two CLI/MCP sets are
existing legacy implementations, not features added to McpCli by this story.

Negative mutations reject missing/duplicate concrete rows, invented surfaces,
unsupported inclusion, false approval, invented owner sign-off, a missing
variant and a duplicate exclusion. The ninth check rejects swapped ChatBot
CLI/MCP row associations or a weakened Memories forwarded-identity retirement
gate, respectively. No on-disk inventory is mutated by these checks.

The source-reference checks prove file existence, line bounds and nonblank
anchors. The pinned-source investigation supplies the associated behavior
interpretation; a passing reference check alone cannot validate every prose
claim. Local companion links, UTF-8, final newlines and trailing whitespace are
checked. `git diff --check` also passed; Python checks cover newly created,
untracked artifacts that Git's ordinary diff does not include. Git emitted
existing `warning: unable to find all commit-graph files` messages while returning
successful command results.

Before approval, the spec measured **1,391 tokens** with `tiktoken`'s `o200k_base`, below the
workflow's 1,600-token proposal threshold. No project dependency was changed to
run that tooling. No .NET build or application suite applies to this planning
artifact change, and none is claimed to have run.

The static candidate checks do not supply external owner approval,
decorated published Contracts, exact Gateway/projection routes, restored
allowlist/Catalog coverage, authorization or live persisted-effect proof,
compatibility/release/rollback evidence or retirement permission. Memories'
current authenticated tenant membership is distinct from a private per-user
owner policy; subject normalization does not establish such a policy. Its
current source forwards authenticated caller bearer tokens, and McpCli v1
stdio does not replace that behavior. The Legacy Server remains nondeletable
until a later HTTP release supports forwarded per-user identity and all other
owner, security, behavior and release gates pass.

The user's "approve and stop" records session scope approval in the spec and
synchronizes both tracking states to `ready-for-dev`. Inventory finalization,
required workflow review and completion synchronization remain before story
completion. Prior stories' approvals do not apply to these candidates. The
documented check intentionally accepts approved-spec/candidate-inventory state;
it must be revised with final inventory approval references during implementation.
