# Story 4.4 static verification

Date: 2026-10-17. Inventories are finalized at version **1.0.0** with the
requesting user's actual session approval in their shared A1 record. Every one
of the 88 scope rows remains `defer / exclude`. External owning-maintainer
sign-off stays unasserted. Implementation and workflow review/status gates are
separate from those downstream owner, execution and retirement gates.

- [Spec](../../spec-4-4-approve-chatbot-and-memories-migration-inventories.md)
- [ChatBot inventory](../../chatbot-migration-inventory-v1.md)
- [Memories inventory](../../memories-migration-inventory-v1.md)

The implementation baseline is `2833aafba8ddf49222774a39eea5bf05a744f878`.
ChatBot source is pinned to `acc934599cf1efff36b0643eddc6a3cc4c2978d5` and
Memories to `f6b60d5a2e9b81d84fddad789c7d9bed40d3a533`. Both root gitlinks
already named those pins at implementation entry; both owning checkouts were
clean. The spec and sprint status already contained the active build's changes.
This story preserves those changes and changes no upstream source, dependency,
enrollment, submodule pointer or runtime behavior.

## Approval provenance and historical candidate check

The exact approving instruction was **"approve and stop"** to the recommended
scope that all rows in both source-pinned candidates retain `defer / exclude`.
That decision stopped at `ready-for-dev`; the subsequent build request resumed
finalization without reopening that approval. A1 binds this actual decision to
both source pins, inventory 1.0.0, every row and its limits. It never identifies
the requesting user as an external owning maintainer or approves future proposed
context mappings.

At preparation, the original candidate checks exited 0 with exact source sets,
88 pending A0 references and nine negative mutations per module. They supplied
static bookkeeping only. The version-controlled candidate evidence predates
finalization; pending metadata is rejected by the current checks below.
Earlier workspace syncs and their reference movements were separate work.
During implementation, concurrent external updates advanced ChatBot checkout
HEAD to `d6c4deb70dcce90344f86d7dee3d6e7027e61e24`; the original candidate-style
HEAD-equality check stopped with `AssertionError: Hexalith.ChatBot` (exit 1).
No checkout was reset or updated. Final verification reads the immutable required
pin directly and reports current HEAD/status separately, preserving checkout drift
without substituting newer source. Memories remained at its mandated pin at this
observation; other root reference changes are unrelated and preserved.

## Repeatable final checks

Run this entire block from the McpCli root using Python 3 and Git. It derives
registered tool and CLI sets independently, distinguishes the four stubs,
checks all concrete rows and variant/exclusion IDs, surface/source associations,
source pins, source anchors, local links and exact limited approval metadata.
Every upstream source read uses `git show <pin>:<path>` and `git ls-tree <pin>`;
current checkout content cannot silently replace the mandated source revision.
It verifies the frozen approved intent, generic context limits and the current
Memories scoped bearer/tenant-membership source seams, then rejects invalid
in-memory mutations. No on-disk inventory is mutated.

These read-only checks execute no legacy operation, workflow, migration,
import/export, deletion, package restore or service call. They do not discover
or load agent skills in `references/`.

```bash
set -euo pipefail
python3 - <<'PY_FINAL'
from collections import Counter
from pathlib import Path
import re
import hashlib
from functools import lru_cache
import subprocess

root = Path.cwd()
base = root / '_bmad-output/implementation-artifacts'
pins = {
    'chatbot': ('Hexalith.ChatBot', 'acc934599cf1efff36b0643eddc6a3cc4c2978d5'),
    'memories': ('Hexalith.Memories', 'f6b60d5a2e9b81d84fddad789c7d9bed40d3a533'),
}

git_warnings = set()

def git_output(module, *arguments):
    checkout = root / 'references' / pins[module][0]
    command = ['git', '-C', str(checkout), *arguments]
    result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(f'{command!r}: exit {result.returncode}\n{result.stdout}{result.stderr}')
    git_warnings.update(result.stderr.splitlines())
    return result.stdout

@lru_cache(maxsize=None)
def pinned_text(module, relative):
    repo, sha = pins[module]
    return git_output(module, 'show', f'{sha}:{relative}')

def source(module, project, filename):
    repo = pins[module][0]
    return pinned_text(module, 'src/' + repo + '.' + project + '/' + filename)

def source_files(module, project):
    repo, sha = pins[module]
    prefix = 'src/' + repo + '.' + project + '/'
    names = git_output(module, 'ls-tree', '-r', '--name-only', sha, '--', prefix).splitlines()
    return [name for name in names if name.endswith('.cs') and not {'bin', 'obj'}.intersection(Path(name).parts)]

approval_anchor = '#a1-session-approval-2026-10-17'
approval_ref = f'[A1]({approval_anchor})'
associations = {}

def check_pins():
    modules = (root / '.gitmodules').read_text()
    for module, (repo, sha) in pins.items():
        assert f'path = references/{repo}' in modules, repo
        checkout = root / 'references' / repo
        git_output(module, 'cat-file', '-e', sha + '^{commit}')
        observed = git_output(module, 'rev-parse', 'HEAD').strip()
        status = git_output(module, 'status', '--porcelain').strip()
        print(f'SOURCE {repo}: verified immutable pin {sha}; observed checkout {observed}; status {status or "clean"}')

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
    associations['memories'] = {}
    for cls in re.findall(r'\.WithTools<(\w+)>\(\)', composition):
        tool_text = source('memories', 'Mcp', 'Tools/' + cls + '.cs')
        name = re.search(r'\[McpServerTool\(Name = "([^"]+)"', tool_text)[1]
        associations['memories'][name] = 'Mcp/Tools/' + cls + '.cs'
    for parent, cls in re.findall(r'(\w+)\.Subcommands.Add\((\w+)\.Build\(services\)\)', cli):
        leaf = re.search(r'(?:var|Command) command = new(?: Command)?\("([^"]+)"', source('memories', 'Cli', 'Commands/' + cls + '.cs'))[1]
        assert parent == 'root' or 'root.Subcommands.Add(' + parent + ')' in cli
        name = (groups[parent] + ' ' if parent != 'root' else '') + leaf
        leaves.append(name)
        associations['memories'][name] = 'Cli/Commands/' + cls + '.cs'
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
    assert metadata(text, 'inventory_version') == '1.0.0'
    assert metadata(text, 'status') == 'approved'
    assert metadata(text, 'approval_status') == 'session-approved'
    assert metadata(text, 'approval_authority') == 'requesting-user-session'
    assert metadata(text, 'external_maintainer_approval') == 'unasserted'
    assert metadata(text, 'source_revision') == pins[module][1]
    assert metadata(text, 'module') == module
    assert metadata(text, 'source_spec') == '_bmad-output/implementation-artifacts/spec-4-4-approve-chatbot-and-memories-migration-inventories.md'
    assert metadata(text, 'approval_ref') == approval_anchor
    assert '## A1 Session approval (2026-10-17)' in text
    assert '**Exact approving instruction:** "approve and stop"' in text
    assert 'No external\n  owning-maintainer sign-off is asserted' in text
    assert all(sha in text for repo, sha in pins.values()), 'shared source-pinned approval'
    assert 'A0' not in text and 'approval_status: pending' not in text
    scope = [row[0] for row in rows(text, '[A-Z]') if not row[0].startswith('G')]
    allowed = set(expected) | {'V', 'X'}
    assert all(key[0] in allowed for key in scope), 'unknown scope row family'

    all_rows = []
    for prefix, names in expected.items():
        actual = rows(text, prefix)
        assert len(actual) == len(names), (module, prefix, 'count')
        assert Counter(row[0] for row in actual) == Counter(f'{prefix}{n:02}' for n in range(1, len(names) + 1)), (module, prefix, 'ids')
        assert Counter(row[1].strip('`') for row in actual) == Counter(names), (module, prefix, 'surface set')
        for row in actual:
            assert len(row) == 8 and row[2:4] == ['defer', 'exclude'], row
            assert all(row[4:7]) and row[-1] == approval_ref, row
            if module == 'memories' and prefix != 'S':
                name = row[1].strip('`')
                assert re.search(r'`' + re.escape(associations[module][name]) + r':\d+`', row[6]), (module, row[0], 'surface/source association')
        all_rows.extend(actual)
    for prefix in ('V', 'X'):
        actual = rows(text, prefix)
        count = {'chatbot': {'V': 15, 'X': 4}, 'memories': {'V': 17, 'X': 6}}[module][prefix]
        assert Counter(row[0] for row in actual) == Counter(f'{prefix}{n:02}' for n in range(1, count + 1)), (module, prefix)
        for row in actual:
            assert len(row) == 6 and all(row) and row[2] == 'defer / exclude' and row[-1] == approval_ref, row
    assert re.search(r'no\s+Gateway-ready\s+decorated replacement', text, re.I)
    if module == 'memories':
        assert 'not deletable before the HTTP release supports forwarded per-user identity' in text
        assert 'ingestedBy' in text and 'bearer' in text and 'tenant list' in text
    else:
        assert all(term in text for term in ('commandCorrelationId', 'taskIntentId', 'StateOwnerAggregateId', 'actor', 'tenant', 'ExpectedApprovalSourceVersion', 'ExpectedProposalSourceVersion', 'Queries have no extension channel', 'proposed future mapping'))
        pairs = {m[0][1:]: m[1].strip('`').removeprefix('chatbot.').replace('ai_action', 'ai-action').replace('.', ' ')
                 for m in rows(text, 'M')}
        pairs = {key: ('conversation' if value == 'conversation get' else value) for key, value in pairs.items()}
        assert all(row[1].strip('`') == pairs[row[0][1:]] for row in rows(text, 'L')), 'CLI/MCP row association'

def check_source_anchors(module, text):
    repo = pins[module][0]
    aliases = {part: 'src/' + repo + '.' + part + '/'
               for part in ('Mcp', 'Cli', 'Contracts', 'Server', 'Client', 'Client.Rest', 'EventStore')}
    if module == 'memories':
        aliases['Client'] = aliases['Client.Rest']
    anchors = re.findall(r'`((?:(?:Mcp|Cli|Contracts|Server|Client(?:\.Rest)?|EventStore)/[^`]+|README\.md)):([0-9]+)`', text)
    assert anchors, module
    for rel, number in anchors:
        if '/' in rel:
            alias, path = rel.split('/', 1)
            relative = aliases[alias] + path
        else:
            relative = rel
        lines = pinned_text(module, relative).splitlines()
        assert 0 < int(number) <= len(lines) and lines[int(number) - 1].strip(), (module, rel, number)
    for destination in re.findall(r'\]\(([^)]+)\)', text):
        if destination.startswith('https://'):
            continue
        rel, _, fragment = destination.partition('#')
        target = base / rel if rel else base / (module + '-migration-inventory-v1.md')
        assert target.is_file(), destination
        if fragment:
            headings = re.findall(r'^#{1,6} +(.+)$', target.read_text(), re.M)
            slugs = [re.sub(r'[^\w -]', '', heading.lower()).replace(' ', '-') for heading in headings]
            assert fragment in slugs, destination
    for rel, number in re.findall(r'`(src/[^`]+):([0-9]+)`', text):
        lines = (root / rel).read_text().splitlines()
        assert 0 < int(number) <= len(lines) and lines[int(number) - 1].strip(), (rel, number)


check_pins()
chat_tools, chat_cli = chatbot_sets()
memory_tools, memory_cli, memory_stubs = memories_sets()
expected = {
    'chatbot': {'M': chat_tools, 'L': chat_cli},
    'memories': {'M': memory_tools, 'L': memory_cli, 'S': memory_stubs},
}
spec_path = base / 'spec-4-4-approve-chatbot-and-memories-migration-inventories.md'
spec_text = spec_path.read_text()
spec_status = metadata(spec_text, 'status')
sprint_status = re.search(r'^  4-4-approve-chatbot-and-memories-migration-inventories: (\S+)$', (base / 'sprint-status.yaml').read_text(), re.M)[1]
assert (spec_status, sprint_status) in {('in-progress', 'in-progress'), ('in-review', 'in-progress'), ('done', 'review'), ('done', 'done')}, (spec_status, sprint_status)
frozen = re.search(r'<frozen-after-approval.*?</frozen-after-approval>', spec_text, re.S)[0]
assert hashlib.sha256(frozen.encode()).hexdigest() == '6fcb8a85a4ea996683371a2b173b63678dc17635138657bcfabfff8a00a85a74', 'approved intent changed'
assert 'The requesting user answered "approve and\nstop"' in spec_text
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
        'false approval': text.replace('approval_status: session-approved', 'approval_status: owner-approved', 1),
        'pending approval': text.replace('approval_status: session-approved', 'approval_status: pending', 1),
        'false authority': text.replace('approval_authority: requesting-user-session', 'approval_authority: owning-maintainer', 1),
        'wrong approval reference': text.replace('[A1](#a1-session-approval-2026-10-17)', '[A0](#a0-approval-required)', 1),
        'missing approval decision': text.replace('**Exact approving instruction:** "approve and stop"', '**Approval instruction absent**', 1),
        'invented owner sign-off': text.replace('external_maintainer_approval: unasserted', 'external_maintainer_approval: approved', 1),
        'missing variant': '\n'.join(line for line in text.splitlines() if not line.startswith('| V01 |')) + '\n',
        'duplicate exclusion': text + '\n' + next(line for line in text.splitlines() if line.startswith('| X01 |')) + '\n',
    }
    if module == 'chatbot':
        first, second = rows(text, 'L')[:2]
        mutations['swapped CLI associations'] = text.replace(first[1], '`__swap__`').replace(second[1], first[1]).replace('`__swap__`', second[1])
    if module == 'memories':
        first, second = rows(text, 'L')[:2]
        mutations['swapped CLI associations'] = text.replace(first[1], '`__swap__`').replace(second[1], first[1]).replace('`__swap__`', second[1])
        mutations['implemented stub'] = text.replace('| S01 |', '| L15 |', 1)
        mutations['weakened identity gate'] = text.replace('not deletable before the HTTP release supports forwarded per-user identity', 'deletable now')
    for name, mutant in mutations.items():
        try:
            validate(module, mutant, expected[module])
        except AssertionError:
            continue
        raise AssertionError((module, 'accepted ' + name))
    print(f'PASS {module}: exact source surface sets, row metadata, session approval, source anchors and {len(mutations)} negative mutations.')
    for relative in source_files(module, 'Contracts'):
        assert not re.search(r'\[\s*(?:assembly:\s*)?Hexalith(?:Module|Command|Query)(?:Attribute)?\s*\(', pinned_text(module, relative)), relative
    for relative in source_files(module, 'Mcp'):
        assert not re.search(r'With(?:Resources|Prompts)|\[McpServer(?:Resource|Prompt)', pinned_text(module, relative)), relative
check_pins()
for path in (spec_path, base / 'chatbot-migration-inventory-v1.md', base / 'memories-migration-inventory-v1.md', base / 'evidence/story-4-4/verification.md'):
    if path.exists():
        content = path.read_bytes()
        assert content.endswith(b'\n'), path
        assert all(line == line.rstrip() for line in content.decode('utf-8').splitlines()), path
scope_counts = [sum(len(rows((base / (module + '-migration-inventory-v1.md')).read_text(), prefix)) for prefix in expected[module]) for module in pins]
assert sum(scope_counts) == 46
assert sum(len(rows((base / (module + '-migration-inventory-v1.md')).read_text(), prefix)) for module in pins for prefix in ('V', 'X')) == 42
for warning in sorted(git_warnings):
    print('Git diagnostic:', warning)
print('PASS: 42 implemented surfaces, 4 executable stubs, 32 variants and 10 exclusions; all 88 scope rows session-approved defer/exclude. External owner and live parity gates remain open.')
PY_FINAL
git diff --check
```

## Recorded result and limits

The full Bash block above was executed through Python
`subprocess.run(['bash', '-e'], input=block, text=True)` and exited 0:

```text
PASS chatbot: exact source surface sets, row metadata, session approval, source anchors and 13 negative mutations.
PASS memories: exact source surface sets, row metadata, session approval, source anchors and 15 negative mutations.
PASS: 42 implemented surfaces, 4 executable stubs, 32 variants and 10 exclusions; all 88 scope rows session-approved defer/exclude. External owner and live parity gates remain open.
```

Observed source state at that successful run: ChatBot HEAD
`d6c4deb70dcce90344f86d7dee3d6e7027e61e24`, Memories HEAD
`f6b60d5a2e9b81d84fddad789c7d9bed40d3a533`, both clean. The required
ChatBot pin remains `acc934599cf1efff36b0643eddc6a3cc4c2978d5` and all
source assertions read that commit, including when current checkout HEAD differs.
`git diff --check` passed; the existing commit-graph warnings returned exit 0.
The frozen spec approval span remained SHA-256
`6fcb8a85a4ea996683371a2b173b63678dc17635138657bcfabfff8a00a85a74`. No .NET build applies to these documents;
static checks supply no live Gateway, authorization, persisted-effect or release
proof.

ChatBot accounts for 12 MCP tools, 12 CLI leaves, 15 variants and four explicit
exclusions. Memories accounts for four MCP tools, 14 implemented CLI leaves,
four executable stubs, 17 variants and six exclusions. A1 approves only retaining
their gaps. The new wording explicitly preserves approval/proposal concurrency
inputs and distinguishes the current Memories gitlink from its historical
planning entry; these prerequisite clarifications change no disposition,
coverage, authority or source pin and do not claim the user approved later prose.

Negative mutations reject missing/duplicate rows, invented surfaces, unsupported
inclusion, false or pending approval, invented authority or external owner
sign-off, invalid row approval links, missing decision evidence, missing variants,
duplicate exclusions, swapped surface/source associations, an implemented stub
claim and a weakened Memories forwarded-identity gate. Candidate pending state
cannot pass as final approval.

Source-reference checks prove file existence, nonblank line bounds and local
link targets, including fragments. Behavior interpretations come from the pinned
source investigation; an anchor check alone does not prove every prose claim.
Final-newline, UTF-8 and whitespace checks accompany `git diff --check`.
Git may emit the existing `warning: unable to find all commit-graph files` while
returning exit 0; this warning does not alter the checked source pins.

External owner approval, decorated published Contracts, exact Gateway and
projection routes, restored dependency closure/Catalog coverage, authenticated
identity and authorization parity, live persisted effects and release/rollback
evidence remain open. Memories' authenticated tenant membership and subject
normalization do not establish private per-user ownership or an admin-role gate.
Its existing MCP host propagates the authenticated bearer; generic v1 stdio
cannot replace that behavior. The Memories Legacy Server remains nondeletable
until a later HTTP release supports forwarded per-user identity and all other
owner, security, behavior and release gates pass.
