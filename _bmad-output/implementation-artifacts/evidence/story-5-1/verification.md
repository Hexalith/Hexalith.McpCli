# Story 5.1 static verification

This evidence belongs to
[spec 5.1](../../spec-5-1-inventory-eventstore-admin-and-technical-tool-operations.md).
It verifies the approved
[EventStore Admin inventory](../../eventstore-admin-migration-inventory-v1.md) and
[technical-tools inventory](../../technical-tools-migration-inventory-v1.md),
both `1.0.0`, finalized from approved `1.0.0-candidate.3`. The unapproved planning
findings that preceded them are indexed in [planning/README.md](planning/README.md).

Run the block below from the McpCli root with Python 3 and Git. It reads tracked
files of the 17 root-declared checkouts through `git ls-files`, the first eight
metadata lines of each FrontComposer corpus document, and the local inventories.
It never discovers or loads an agent `SKILL.md`, restores, builds or tests
anything, runs a legacy CLI, MCP server, migration or service, initializes a
nested submodule, or changes a reference checkout.

The checks require A1 owning-maintainer approval on every row, with a receipt
binding the exact approving instruction, authority confirmation, reviewed
candidate and final inventory hashes, row IDs and all source revisions.
Missing approval, source drift and incomplete or inconsistent rows fail.
Static checks and inventory approval do not establish generic contract, Gateway
readiness, live authorization or behavior parity, publication or retirement.

## Pins and census scope

McpCli implementation baseline `ad7bf9ee415d09b16b47616740e2cc38fb3d6d9a`;
review resumed at HEAD `fa7c51601041ee6cf0d2f9d4613fb405758f2f7c` on 2026-11-08.
The preceding candidate.2 review was at
`ae4a317f208829681dc8eec36a308bc36f3f9715` on 2026-11-07.
The earlier 2026-11-06 observation at
`c8f97ddd5c12c90f990f616b30acb00db0395a78` used the baseline gitlinks.
Since then Builds moved from `beb85e497957fedc66854013efd2cc4bd216ecbc`,
Tenants from `cf36618a2c27b5722a1ff811cfbbce4528c3c105` and Platform from
`019f593544ad157036b7d12173ff89a16464f3cc` to the full revisions below.
The root `.gitmodules` and other gitlinks are unchanged. Every checkout below
is clean and equals its committed gitlink. The refreshed scan finds the same
production surfaces and owners; Builds' exempt CLI source/project metadata,
Tenants' project/client-config metadata and Platform's production project
metadata, CODEOWNERS and governing architecture are unchanged between these
pins. Among the compared project and authority paths, only Platform's test
project changed (package downloads and one embedded fixture).

| Root reference | Full revision | Role in this story |
| --- | --- | --- |
| `references/Hexalith.AI.Tools` | `1745b6663ad32bb1288167135ed0f979366c53a0` | Migration plan 1.1.0 and ownership rule (read only); PN01 |
| `references/Hexalith.Commons` | `11555ace9efcae2928a00122dcba91243e5a8a1a` | PN02 |
| `references/Hexalith.PolymorphicSerializations` | `bce4eb9f45c6b131b960ab4fa39e50ff01e51960` | PN03 |
| `references/Hexalith.Conversations` | `9a5c684de5ee4876448faa26737f6afd36cf33e7` | PN04 |
| `references/Hexalith.EventStore` | `3d4ba67db99f2f0bcd64b7d353609b555870cc9b` | Admin heads AC/AU/AM, Admin.Server routes; PS01–PS02 |
| `references/Hexalith.Memories` | `246157a7ff8e2dcd8d356c833a77a02514490d2f` | PS06–PS07 |
| `references/Hexalith.Tenants` | `d88aef6b52d7e8a2e2d81132b1d76b7e1d1f0f35` | PN05 |
| `references/Hexalith.Builds` | `567604b616613ba429be0609636d805db776a709` | Exempt PE01–PE02 |
| `references/Hexalith.FrontComposer` | `fbb9c3822dfa407e72739238cd472567f45f1e82` | FH/FD/FC/FV rows; PS03–PS04; FK02, FK04 |
| `references/Hexalith.Parties` | `1308ad000c79ebc394fc395588f9af91092e8c4c` | PS05; FK03 |
| `references/Hexalith.Agents` | `7957108c30d38b8e82eb072cf3437b6a67627cd7` | PN06 |
| `references/Hexalith.Projects` | `31cb92c4362becd83938bd550ca62d07b6af448a` | PS08–PS09; FK01 |
| `references/Hexalith.Folders` | `e88c940000446e13d17d86a7288649d8653a7138` | PS10–PS11 |
| `references/Hexalith.ChatBot` | `b13c58006d292836a9c8b242de476765676e5fb2` | PS12–PS13 |
| `references/Hexalith.Works` | `2e9fafba151a184eb4552796db7eecc25ffaf8c7` | PN07 |
| `references/Hexalith.Timesheets` | `f5bee2c91bec6e1e78d81b604cea6af0cee764fe` | PN08 |
| `references/Hexalith.Platform` | `01e5b6530af96ad6eaa69cc1867d43def56c43ca` | AD-11/AD-14 authority (read only); PN09 |

The FrontComposer historical pin `81a440a8890a17edb39924bd0cf676eb6f6b5c25`
and the companion inventory pins are read from this workspace's object stores.
Census scope is the root `.gitmodules` only: tracked `src/` projects in each
root, excluding test projects, nested gitlinks and captured `_bmad`,
`evidence` and `docs/implementation` artifacts. It asserts no completeness for
other repositories, unpublished forks or uninspected dynamic hosts.

## What the block checks

- **Registration sets:** the Admin CLI graph walked from `Program.cs` equals
  AC01–AC31 in order (21 remote, 7 local, 3 stubs); unreachable `Create`
  factories equal AU01–AU06; `[McpServerTool]` names equal AM01–AM28 (18 reads,
  7 `confirm`-gated writes, 3 process-local); no MCP resource, prompt, alias or
  annotation hint exists.
- **Routes and authority:** all 68 Admin.Server actions are parsed with their
  combined policies and platform-scope admission. The effective tenant filter
  is the filter attribute AND (a `tenantId` parameter OR platform admission),
  because the filter forwards other actions without a grant check; only
  `TriggerCheck` (AM06) carries the attribute without effect. Every remote
  row's verb and route exist in the head's source and match exactly one server
  action, except the AC03/AM23 root GET, which must match none. Each security
  cell must name `EventStoreHuman`, every derived policy, the tenant-filter
  state and platform scope where applicable, and carry the UI-only (AD-11/AD-14)
  class. The 39 actions no head reaches must equal AX06.
- **Effects and confirmation:** the destructive set is exactly AC13, AC20,
  AC21, AC25, AC28 and AM14; AV03 separately records the optional destructive
  local output-file variant. The seven MCP writes must be confirmation-required
  and state that `confirm: true` is not human authority; CLI mutations must
  record no prompt and their source must contain no confirmation path.
- **FrontComposer reconciliation:** historical-pin ancestry and merge base, the
  identical `Mcp/` and corpus trees, the six changed CLI files, the lifecycle
  tool name, the 12 corpus documents' metadata plus the synthetic manifest, the
  two CLI verbs, and every manifest registration and package consumer.
- **Census:** every production surface in the 17 roots is a PS row, an exempt
  Builds tool or the FK03 dependency consumer; packaging claims match project
  metadata and release lists; companion drift numbers match Git; other
  executables, test projects and developer MCP configs (JSON files and
  `.codex/config.toml` `[mcp_servers.*]` tables) are classified; the nine
  surface-free roots equal PN01–PN09; Platform's CODEOWNERS is the only
  ownership file.
- **Anchors and links:** every backticked `path:line` and `:line` continuation,
  including the `references/` anchors for Platform AD-11/AD-14, the AI.Tools
  rule and plan 1.1.0, EventStore AD-22 and the census routing points,
  resolves to a non-blank line at the pin; 65 load-bearing anchors also match
  expected content; row anchors point at their command, tool or metadata line;
  every local link and heading fragment resolves.
- **State and approval:** both inventories are approved `1.0.0` with A1 on
  every row and the requesting user's explicitly confirmed owning-maintainer
  authority. The approval receipt binds all 156 row IDs, both preserved
  candidate.3 snapshots, final inventory bytes, McpCli revision and all 17
  census pins. The spec's frozen block and historical inventories are unchanged;
  working-tree changes stay under `_bmad-output/implementation-artifacts/`.
  The 15 named story, planning and approval files have LF endings and no trailing
  whitespace; `git diff --check` covers the other tracked documentation.
  The Story 5.2 handoff assigns each AC/AM row once. The 29 damaged inputs
  include missing approval, corrupt receipts and completion while pending.

## Reproducible check

```bash
set -e
python3 - <<'PY'
from pathlib import Path
from collections import Counter
import hashlib
import json
import re
import subprocess
import tomllib

root = Path.cwd()
base = root / '_bmad-output/implementation-artifacts'
spec_name = 'spec-5-1-inventory-eventstore-admin-and-technical-tool-operations.md'
spec_text = (base / spec_name).read_text()
APPROVAL_REF = '[A1](#a1-owning-maintainer-approval-2026-11-08)'
OWNER = 'EventStore + platform/operator maintainer roles'
ES_SHA = '3d4ba67db99f2f0bcd64b7d353609b555870cc9b'
FC_SHA = 'fbb9c3822dfa407e72739238cd472567f45f1e82'
FC_OLD = '81a440a8890a17edb39924bd0cf676eb6f6b5c25'
FROZEN_SHA256 = '8be7892597e4e5f0aeb4a1aa8acef4d57eacffac4b75de417c882494a557a105'
FC_BASE = 'b06f86d554363ea5b8192cbc149a75c820dab2b8'
refs = root / 'references'
es = refs / 'Hexalith.EventStore'
fc = refs / 'Hexalith.FrontComposer'


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True,
                                   stderr=subprocess.DEVNULL).strip()


def section(text, heading):
    start = text.index('\n' + heading + '\n')
    rest = text[start + len(heading) + 2:]
    match = re.search(r'^#{2,3} ', rest, re.M)
    return rest[:match.start()] if match else rest


def rows(text, prefix, width):
    result = {}
    for line in text.splitlines():
        if not re.match(rf'^\| {prefix}\d+ \|', line):
            continue
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        key = cells[0]
        assert key not in result, ('duplicate row', key)
        assert len(cells) == width and all(cells), ('incomplete row', key)
        assert cells[-1] == APPROVAL_REF, ('approval reference', key)
        result[key] = cells
    expected = [f'{prefix}{i}' if prefix == 'G' else f'{prefix}{i:02d}' for i in range(1, len(result) + 1)]
    assert list(result) == expected, ('row identities', prefix, list(result))
    return result


def frontmatter(text):
    return dict(re.findall(r"^(\w+): '?([^'\n]*)'?$", text.split('\n---', 1)[0], re.M))


def check_approval(text):
    meta = frontmatter(text)
    assert meta['inventory_version'] == '1.0.0'
    assert meta['status'] == 'approved'
    assert meta['approval_status'] == 'approved'
    assert meta['approval_ref'] == '#a1-owning-maintainer-approval-2026-11-08'
    assert meta['approval_authority'] == 'requesting-user-owning-maintainer'
    assert meta['external_maintainer_approval'] == 'approved'
    assert 'owning_maintainer_approval' not in meta
    assert '\n## A1 Owning-maintainer approval (2026-11-08)\n' in text
    assert '"I approve"' in text and '"Authorized for all listed maintainer roles"' in text
    assert 'evidence/story-5-1/approval/approval.json' in text
    for claim in ['| replace |', '| include |', '| withdraw |']:
        assert claim not in text, claim


# ---------------------------------------------------------------- sources
def norm_route(path):
    return path.split('?', 1)[0].lstrip('/')


def source_routes(text):
    text = re.sub(r'\{Uri\.EscapeDataString\((\w+)\)\}', r'{\1}', text)
    return {norm_route(m) for m in re.findall(r'\$?"(/?api/v1/admin/[^"]*)"', text)}


def seg_ok(a, b):
    if b.startswith('{'):
        constraint = re.match(r'\{\w+:regex\((.*)\)\}$', b)
        return a.startswith('{') or not constraint or re.fullmatch(constraint[1], a) is not None
    return not a.startswith('{') and a.lower() == b.lower()


def seg_match(client, server):
    c, s = client.strip('/').split('/'), server.strip('/').split('/')
    return len(c) == len(s) and all(seg_ok(a, b) for a, b in zip(c, s))


POLICY = {'ReadOnly': 'AdminReadOnly', 'Operator': 'AdminOperator', 'Admin': 'AdminFull'}


def server_actions():
    actions = []
    for path in sorted((es / 'src/Hexalith.EventStore.Admin.Server/Controllers').glob('*.cs')):
        text = path.read_text()
        head, _, body = text.partition('public class ')
        route = re.search(r'\[Route\("([^"]+)"\)\]', head)[1]
        class_policies = set(re.findall(r'AdminAuthorizationPolicies\.(\w+)\)', head))
        assert '[Authorize(Policy = "EventStoreHuman")]' in head, path.name
        attrs, count = [], 0
        for line in body.splitlines():
            s = line.strip()
            if s.startswith('['):
                attrs.append(s)
                continue
            m = re.match(r'public async Task<IActionResult> (\w+)\(', s)
            if m:
                http = [a for a in attrs if a.startswith('[Http')]
                if http:
                    count += 1
                    hm = re.match(r'\[Http(Get|Post|Put|Delete)(?:\("([^"]*)"\))?\]', http[0])
                    policies = class_policies | set(re.findall(r'AdminAuthorizationPolicies\.(\w+)\)', ' '.join(attrs)))
                    params = re.search(rf'public async Task<IActionResult> {m[1]}\((.*?)\)\s*\{{', body, re.S)[1]
                    actions.append(dict(controller=path.stem.removeprefix('Admin').removesuffix('Controller'),
                                        action=m[1], verb=hm[1].upper(), route=(route + '/' + (hm[2] or '')).rstrip('/'),
                                        policies={POLICY[p] for p in policies},
                                        filter_attribute=any('AdminTenantAuthorizationFilter' in a for a in attrs),
                                        tenant_parameter=bool(re.search(r'\bstring\??\s+tenantId\b', params))))
                attrs = []
            elif s and not s.startswith('//'):
                attrs = []
        assert count == len(re.findall(r'^\s*\[Http(?:Get|Post|Put|Delete)', text, re.M)), path.name
    return actions


SERVER = server_actions()
catalog = (es / 'src/Hexalith.EventStore.Contracts/Routing/AdminPlatformScopeCatalog.cs').read_text()
PLATFORM = set(re.findall(r'"(\w+)"', catalog.split('ForAction', 1)[1])) & {a['action'] for a in SERVER}
assert PLATFORM == {'GetRecentCommandsAsync', 'GetRecentlyActiveStreamsAsync', 'GetSystemHealth'}
# The filter forwards without a grant check unless the action has a tenantId parameter or platform admission.
for _action in SERVER:
    _action['tenant_filter'] = _action['filter_attribute'] and (_action['tenant_parameter'] or _action['action'] in PLATFORM)
assert sorted(a['action'] for a in SERVER if a['filter_attribute'] and not a['tenant_filter']) == ['TriggerCheck']


def match(verb, path):
    return [a for a in SERVER if a['verb'] == verb and seg_match(path, a['route'])]


def cell_routes(cell):
    return [(v, norm_route(p)) for v, p in re.findall(r'`(GET|POST|PUT|DELETE) (/?api/v1/admin/[^`]*)`', cell)]


CLI = es / 'src/Hexalith.EventStore.Admin.Cli'
MCP = es / 'src/Hexalith.EventStore.Admin.Mcp'


def cli_graph():
    classes = {}
    for path in CLI.rglob('*.cs'):
        for name in re.findall(r'public static class (\w+)', path.read_text()):
            classes[name] = path
    program = (CLI / 'Program.cs').read_text()
    leaves, visited = [], set()

    def visit(cls, prefix):
        visited.add(cls)
        text = classes[cls].read_text()
        create = text.split('public static Command Create(', 1)[1]
        name = re.search(r'Command command = new\("([^"]+)"', create)[1]
        path = (prefix + ' ' + name).strip()
        body = create.split('return command;', 1)[0]
        if 'SetAction(' in body:
            kind = 'remote' if 'api/v1/admin' in text else 'local'
            leaves.append((path, kind, classes[cls]))
        for child in re.findall(r'command\.Subcommands\.Add\((?!StubCommands\b)(\w+)\.Create\(|StubCommands\.Create\("([^"]+)"', body):
            if child[0]:
                visit(child[0], path)
            else:
                leaves.append((path + ' ' + child[1], 'stub', classes['StubCommands']))
    for top in re.findall(r'rootCommand\.Subcommands\.Add\((\w+)\.Create\(', program):
        visit(top, '')
    factories = {name for name, path in classes.items()
                 if 'public static Command Create(' in path.read_text() and name in path.read_text().split('public static Command Create(')[0]}
    helpers = sorted(n for n in factories - visited if n != 'StubCommands')
    return leaves, helpers, classes


# ---------------------------------------------------------------- admin inventory
def check_admin(text):
    check_approval(text)
    meta = frontmatter(text)
    assert meta['source_revision'] == ES_SHA and meta['module'] == 'eventstore-admin'
    assert meta['source_spec'] == f'_bmad-output/implementation-artifacts/{spec_name}'
    ac = rows(section(text, '## Admin CLI registered operations'), 'AC', 14)
    au = rows(section(text, '## Unregistered CLI helper classes'), 'AU', 9)
    am = rows(section(text, '## Admin MCP tools'), 'AM', 14)
    av = rows(section(text, '## Behavior and authority variants'), 'AV', 6)
    ax = rows(section(text, '## Absent surfaces and scope evidence'), 'AX', 6)
    g = rows(section(text, '## Retirement and replacement prerequisites'), 'G', 4)
    assert (len(ac), len(au), len(am), len(av), len(ax), len(g)) == (31, 6, 28, 13, 7, 6)

    leaves, helpers, classes = cli_graph()
    assert [r[1].strip('`') for r in ac.values()] == [p for p, _, _ in leaves], 'CLI registration graph'
    kinds = Counter(k for _, k, _ in leaves)
    assert kinds == {'remote': 21, 'local': 7, 'stub': 3}
    assert sorted(r[1].split('`')[1] for r in au.values()) == helpers and len(helpers) == 6
    for r in au.values():
        cls, leaf = r[1].split('`')[1], r[1].split('`')[3]
        assert re.search(rf'Command command = new\("{re.escape(leaf)}"', classes[cls].read_text())

    tools = []
    for path in sorted((MCP / 'Tools').glob('*.cs')):
        source = path.read_text()
        assert not re.search(r'McpServerTool\([^)]*(?:Destructive|ReadOnly|Idempotent|OpenWorld)', source)
        for chunk in source.split('[McpServerTool(')[1:]:
            name = re.match(r'Name = "([^"]+)"\)\]', chunk)[1]
            body = chunk.split('[McpServerTool(')[0]
            kind = 'write' if 'bool confirm = false' in body else 'local' if 'AdminApiClient adminApiClient' not in body else 'read'
            if kind == 'write':
                assert 'if (!confirm)' in body and 'SerializePreview(' in body, name
            tools.append((name, kind))
    assert [r[1].strip('`') for r in am.values()] == sorted(n for n, _ in tools), 'MCP tool set'
    assert Counter(k for _, k in tools) == {'read': 18, 'write': 7, 'local': 3}
    program = (MCP / 'Program.cs').read_text()
    assert '.WithStdioServerTransport()' in program and '.WithToolsFromAssembly()' in program
    assert not re.search(r'WithResources|WithPrompts|WithHttpTransport', program)
    assert not any(re.search(r'McpServerResource|McpServerPrompt', p.read_text()) for p in MCP.rglob('*.cs'))
    assert not any(re.search(r'\.Aliases\.Add|Aliases =', p.read_text()) for p in CLI.rglob('*.cs'))
    mcp_client = '\n'.join(p.read_text() for p in MCP.glob('AdminApiClient*.cs'))

    reached = set()
    leaf_kind = {p: k for p, k, _ in leaves}
    tool_kind = dict(tools)
    destructive = {'AC13', 'AC20', 'AC21', 'AC25', 'AC28', 'AM14'}
    for key, r in {**ac, **am}.items():
        assert r[8:11] == ['defer', 'exclude', r[10]] and r[11] == OWNER, key
        kind = leaf_kind[r[1].strip('`')] if key.startswith('AC') else tool_kind[r[1].strip('`')]
        assert r[5].startswith('destructive') == (key in destructive), key
        security, routes = r[7], cell_routes(r[3])
        first = re.search(r'`((?:Cli|Mcp)/[^`]+):\d+`', r[12])[1]
        source_file = es / first.replace('Cli/', 'src/Hexalith.EventStore.Admin.Cli/', 1).replace('Mcp/', 'src/Hexalith.EventStore.Admin.Mcp/', 1)
        if kind in ('remote', 'read', 'write'):
            assert routes and re.search(r'UI-only(?: and confirmation-required)? \(AD-11/AD-14\)', security), key
            available = source_routes(source_file.read_text() if key.startswith('AC') else mcp_client)
            if key.startswith('AC'):
                verbs = {'Get': 'GET', 'TryGet': 'GET', 'Post': 'POST', 'Put': 'PUT', 'Delete': 'DELETE'}
                used = {verbs[v] for v in re.findall(r'\.(Get|TryGet|Post|Put|Delete)Async<', source_file.read_text())}
                assert used == {v for v, _ in routes}, key
            for verb, path in routes:
                assert path in available, (key, path)
                found = match(verb, path)
                if 'No matching server route' in security:
                    assert not found and key in ('AC03', 'AM23'), key
                    continue
                assert len(found) == 1, (key, verb, path)
                action = found[0]
                reached.add((action['controller'], action['action']))
                assert '`EventStoreHuman`' in security and all(f'`{p}`' in security for p in action['policies']), key
                assert ('no tenant filter' in security) == (not action['tenant_filter']), key
                assert ('platform-scope' in security) == (action['action'] in PLATFORM), key
            mutation = any(v != 'GET' for v, _ in routes)
            if key.startswith('AM'):
                if kind == 'write':
                    assert r[6] == 'caller `confirm: true` (default false: preview, zero requests)', key
                    assert 'confirmation-required' in security and '`confirm: true` is not human authority' in security, key
                else:
                    assert r[6] == 'none required' and 'confirmation-required' not in security, key
            else:
                assert (r[6] == 'none: no prompt and no confirmation flag') == mutation, key
                assert mutation or r[6] == 'n/a (read)', key
                assert not re.search(r'confirm|--yes|--force|ReadLine', source_file.read_text(), re.I), key
        else:
            assert not routes and 'UI-only' not in security, key
            if kind == 'stub':
                assert r[2] == 'registered unavailable stub' and r[5] == 'none (stub)', key
                assert re.search(rf'StubCommands\.Create\("{r[1].strip("`").split()[-1]}"',
                                 (CLI / 'Commands/Backup/BackupCommand.cs').read_text()), key
            elif key.startswith('AC'):
                assert security.startswith('Local') and 'api/v1/admin' not in source_file.read_text(), key
                writes = 'ProfileManager.Save(' in source_file.read_text()
                assert (r[6] == 'none: no prompt and no confirmation flag') == writes, key
            else:
                assert security.startswith('Process-local') and r[3].startswith('MCP stdio, process-local'), key
    for key, r in au.items():
        (verb, path), = cell_routes(r[3])
        cls = r[1].split('`')[1]
        assert path in source_routes(classes[cls].read_text()) and len(match(verb, path)) == 1, key
    assert len(SERVER) == 68 and len(reached) == 29
    residual = [a for a in SERVER if (a['controller'], a['action']) not in reached]
    assert len(residual) == 39 and '39 of the 68' in ax['AX06'][2]
    assert all(f'`{a["action"]}`' in ax['AX06'][2] for a in residual)
    named = re.findall(r'`(\w+)`', ax['AX06'][2])
    assert sorted(named) == sorted(a['action'] for a in residual), 'AX06 names'
    anchored = set()
    for name, number in re.findall(r'`Server/Controllers/Admin(\w+)Controller\.cs:(\d+)`', ax['AX06'][4]):
        line = (es / f'src/Hexalith.EventStore.Admin.Server/Controllers/Admin{name}Controller.cs').read_text().splitlines()[int(number) - 1]
        assert line.startswith('[Route("api/v1/admin/'), (name, number)
        anchored.add(name)
    assert anchored == {a['controller'] for a in residual}, ('AX06 controller anchors', anchored)
    stream = [a for a in SERVER if a['route'] == 'api/v1/admin/streams/GetRecentlyActiveStreams']
    assert stream and not match('GET', 'api/v1/admin/streams')

    corr = section(text, '## Cross-head correspondence')
    seen = []
    for line in corr.splitlines():
        if re.match(r'^\| (?:AC\d+|none)', line):
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            assert len(cells) == 4 and all(cells)
            seen += [x for c in cells[:2] for x in c.split(', ') if x != 'none']
    assert sorted(seen) == sorted([*ac, *am]) and len(seen) == len(set(seen)), 'correspondence coverage'
    assert 'No Admin route has\n  a declared agent eligibility' in text
    assert 'It proves no human authority' in text
    for gate in ['Story 5.2', 'Story 5.3', 'Stories 5.2 and 5.4', 'Story 5.5']:
        assert gate in text, gate
    return dict(AC=ac, AU=au, AM=am, AV=av, AX=ax, G=g)


# ---------------------------------------------------------------- technical inventory
ROOTS = re.findall(r'path = (references/\S+)', (root / '.gitmodules').read_text())
CAPTURED = ('_bmad', 'evidence', 'docs/implementation')


def tracked(repo, *patterns):
    return [f for f in git(repo, 'ls-files', *patterns).splitlines() if f and not f.startswith(CAPTURED)]


def census():
    surfaces, executables = {}, {}
    for rel in ROOTS:
        repo = root / rel
        for f in tracked(repo, '*.csproj'):
            if not f.startswith('src/') or 'Tests' in f:
                continue
            t = (repo / f).read_text(errors='ignore')
            surface = (re.search(r'\.(?:Cli|Mcp)\.csproj$', f) or 'ModelContextProtocol' in t
                       or 'FrontComposer.Mcp' in t or re.search(r'<PackAsTool>\s*true', t, re.I))
            if surface:
                surfaces.setdefault(rel, []).append(f)
            elif '<OutputType>Exe' in t and 'Sdk.Web' not in t and 'Aspire.AppHost.Sdk' not in t:
                executables.setdefault(rel, []).append(f)
    return surfaces, executables


def check_technical(text):
    check_approval(text)
    meta = frontmatter(text)
    assert meta['source_revision'] == FC_SHA and meta['historical_source_revision'] == FC_OLD
    fh = rows(section(text, '## FrontComposer host surfaces'), 'FH', 13)
    fd = rows(section(text, '## Documentation and skill resources'), 'FD', 11)
    fcl = rows(section(text, '## FrontComposer compiler CLI leaves'), 'FC', 15)
    fv = rows(section(text, '## FrontComposer behavior variants'), 'FV', 8)
    fk = rows(section(text, '## Manifest host consumers'), 'FK', 8)
    ps = rows(section(text, '### Production surfaces'), 'PS', 9)
    pe = rows(section(text, '### Exempt, test and non-surface tooling'), 'PE', 5)
    pn = rows(section(text, '### Root references without a production surface'), 'PN', 6)
    g = rows(section(text, '## Retirement and replacement prerequisites'), 'G', 4)
    assert (len(fh), len(fd), len(fcl), len(fv), len(fk), len(ps), len(pe), len(pn), len(g)) == (3, 13, 2, 9, 4, 13, 7, 9, 5)
    for group in (fh, fd, fcl):
        for key, r in group.items():
            disposition = r.index('defer')
            assert r[disposition + 1] == 'exclude', key
    assert all(r[4] == 'defer / exclude' for r in fv.values())

    # Historical/current reconciliation.
    assert git(fc, 'rev-parse', 'HEAD') == FC_SHA and git(fc, 'cat-file', '-t', FC_OLD) == 'commit'
    assert subprocess.run(['git', '-C', str(fc), 'merge-base', '--is-ancestor', FC_OLD, FC_SHA]).returncode == 1
    assert git(fc, 'merge-base', FC_OLD, FC_SHA) == FC_BASE
    assert git(fc, 'diff', '--name-status', FC_BASE, FC_OLD).split() == ['M', '.codex/config.toml', 'M', '.mcp.json']
    assert git(fc, 'diff', '--shortstat', FC_BASE, FC_OLD) == '2 files changed, 24 deletions(-)'
    for tree in ['src/Hexalith.FrontComposer.Mcp', 'docs/skills/frontcomposer']:
        assert git(fc, 'rev-parse', f'{FC_OLD}:{tree}') == git(fc, 'rev-parse', f'{FC_SHA}:{tree}'), tree
    changed = git(fc, 'diff', '--name-only', FC_OLD, FC_SHA, '--', 'src/Hexalith.FrontComposer.Cli').split()
    names = [Path(c).name for c in changed]
    assert names == ['CliApplication.cs', 'MigrationPlanner.cs', 'PathUtilities.cs', 'ProjectDocumentLoader.cs', 'README.md', 'WriteSafetyPolicy.cs']
    assert git(fc, 'diff', '--shortstat', FC_OLD, FC_SHA, '--', 'src/Hexalith.FrontComposer.Cli') == '6 files changed, 89 insertions(+), 30 deletions(-)'
    assert all(f'`{n}`' in text for n in names)
    assert set(re.findall(r'`(\w+\.cs)`', fv['FV09'][3])) == {n for n in names if n.endswith('.cs') and n != 'CliApplication.cs'}
    options = (fc / 'src/Hexalith.FrontComposer.Mcp/FrontComposerMcpOptions.cs').read_text()
    assert fh['FH01'][1].split('`')[1] == re.search(r'LifecycleToolName \{ get; set; \} = "([^"]+)"', options)[1]
    corpus = fc / 'docs/skills/frontcomposer'
    corpus_files = tracked(fc, 'docs/skills/frontcomposer')
    assert not any(Path(f).name == 'SKILL.md' for f in corpus_files), 'agent skills must not be inspected'
    metadata = []
    for f in sorted(f for f in corpus_files if f.endswith('.md')):
        head = (fc / f).read_text().splitlines()[:8]
        assert head[1].startswith('id: ') and head[7].startswith('resourceUri: frontcomposer://skills/'), f
        metadata.append((head[1][4:].strip(), head[7].split('frontcomposer://skills/', 1)[1].strip()))
    assert len(metadata) == len(set(metadata)) == 12
    assert {(r[1].strip('`'), r[2].strip('`')) for k, r in fd.items() if k != 'FD13'} == set(metadata)
    assert [c.strip('`') for c in fd['FD13'][1:3]] == ['skills-manifest', 'manifest']
    assert 'frontcomposer://skills/manifest' in (fc / 'src/Hexalith.FrontComposer.Mcp/Skills/SkillCorpusAggregateManifestBuilder.cs').read_text()
    assert [f for f in corpus_files if not f.endswith('.md')] == ['docs/skills/frontcomposer/benchmark-prompts/v1/prompt-set.json']
    assert r'docs\skills\frontcomposer\**\*.md' in (fc / 'src/Hexalith.FrontComposer.Mcp/Hexalith.FrontComposer.Mcp.csproj').read_text()
    cli = (fc / 'src/Hexalith.FrontComposer.Cli/CliApplication.cs').read_text()
    assert re.findall(r'"(\w+)" => await \w+Command\.RunAsync', cli) == [r[1].strip('`') for r in fcl.values()]
    assert fcl['FC02'][6].startswith('dry-run: local read. With `--apply`, destructive') and '`--apply=false` also applies' in fcl['FC02'][7]

    # Manifest consumers: registration calls and package references outside the host's own source.
    calls, references_ = set(), set()
    for rel in ROOTS:
        repo = root / rel
        for f in tracked(repo, '*.cs'):
            if re.search(r'(?:^|/)tests?/', f) or 'Tests' in f or f.startswith('src/Hexalith.FrontComposer.Mcp/'):
                continue
            if re.search(r'\b(?:AddFrontComposerMcp|MapFrontComposerMcp)\(', (repo / f).read_text(errors='ignore')):
                calls.add((Path(rel).name, f))
        for f in tracked(repo, '*.csproj'):
            if 'FrontComposer.Mcp' in (repo / f).read_text(errors='ignore') and not f.startswith('src/Hexalith.FrontComposer.Mcp/'):
                references_.add((Path(rel).name, f))
    assert calls == {('Hexalith.Projects', 'src/Hexalith.Projects.Mcp/ProjectsMcpModule.cs'),
                     ('Hexalith.FrontComposer', 'samples/Counter/Counter.Web/Program.cs')}, calls
    assert {f for r, f in references_ if 'tests/' not in f} == {
        'src/Hexalith.Projects.Mcp/Hexalith.Projects.Mcp.csproj', 'samples/Counter/Counter.Web/Counter.Web.csproj',
        'src/Hexalith.Parties.UI/Hexalith.Parties.UI.csproj'}, references_
    fc_tests = sorted(Path(f).stem for r, f in references_ if 'tests/' in f)
    assert fc_tests == ['Hexalith.FrontComposer.Mcp.Tests', 'Hexalith.FrontComposer.Shell.Tests.Bench', 'Hexalith.FrontComposer.SourceTools.Tests']
    assert all(n.split('Hexalith.FrontComposer.')[1].removesuffix('.Tests') in fk['FK04'][3] or n.endswith('Mcp.Tests') for n in fc_tests)
    projects_repo = refs / 'Hexalith.Projects'
    assert not any(re.search(r'\bAddProjectsMcp\(', (projects_repo / f).read_text(errors='ignore'))
                   for f in tracked(projects_repo, '*.cs') if not f.startswith('src/Hexalith.Projects.Mcp/') and 'Tests' not in f)

    # Census: every production surface is a PS row, an exempt Builds tool or the FK03 dependency consumer.
    surfaces, executables = census()
    recorded = {r[1].strip('`'): r for r in ps.values()}
    expected = {f for fs in surfaces.values() for f in fs}
    exempt = {'src/libraries/Hexalith.Builds.Evidence.Cli/Hexalith.Builds.Evidence.Cli.csproj',
              'src/libraries/Hexalith.Builds.Module.Cli/Hexalith.Builds.Module.Cli.csproj'}
    assert expected == set(recorded) | exempt | {'src/Hexalith.Parties.UI/Hexalith.Parties.UI.csproj'}, expected
    assert {rel for rel in surfaces} == {f'references/Hexalith.{n}' for n in
                                          ['EventStore', 'Memories', 'Builds', 'FrontComposer', 'Parties', 'Projects', 'Folders', 'ChatBot']}
    assert sum(1 for f in recorded) == 13 and len({r[2].split('`')[1] for r in ps.values()}) == 7
    for project, r in recorded.items():
        rel, sha = r[2].split('`')[1], r[2].split('`')[3]
        repo = root / rel
        assert git(repo, 'rev-parse', 'HEAD') == sha and project in surfaces[rel], project
        csproj = (repo / project).read_text()
        packaging = r[4]
        kind = 'Web' if 'Sdk.Web' in csproj else 'Exe' if '<OutputType>Exe' in csproj else 'Library'
        assert packaging.startswith(kind), project
        tool = re.search(r'`PackAsTool` `([^`]+)`', packaging)
        assert bool(tool) == bool(re.search(r'<PackAsTool>true', csproj)), project
        if tool:
            assert f'<ToolCommandName>{tool[1]}</ToolCommandName>' in csproj, project
        packable = re.search(r'`IsPackable` (true|false)', packaging)
        if packable:
            assert f'<IsPackable>{packable[1]}</IsPackable>' in csproj, project
        release = (repo / 'tools/release-packages.json').read_text() if (repo / 'tools/release-packages.json').exists() else ''
        if 'listed in `tools/release-packages.json`' in packaging:
            assert f'"project": "{project}"' in release, project
        if 'not in `tools/release-packages.json`' in packaging:
            assert project not in release, project
        container = re.search(r'container `([^`]+)`', packaging)
        if container:
            assert f'<ContainerRepository>{container[1]}</ContainerRepository>' in csproj, project
        directory = repo / Path(project).parent
        source = '\n'.join(p.read_text() for p in directory.rglob('*.cs') if 'obj' not in p.parts)
        if 'stdio MCP' in r[3]:
            assert '.WithStdioServerTransport()' in source, project
        if 'HTTP MCP' in r[3] and 'plug-in' not in r[3]:
            assert 'WithHttpTransport(' in source, project
        link = re.search(r'\]\(((\w+)-migration-inventory-v1\.md)\)', r[5])
        if link and link[2] in ('parties', 'memories', 'projects', 'folders', 'chatbot'):
            pin = frontmatter((base / link[1]).read_text())['source_revision']
            if pin in r[5]:
                ancestor = subprocess.run(['git', '-C', str(repo), 'merge-base', '--is-ancestor', pin, sha]).returncode == 0
                assert ('(ancestor)' in r[5]) == ancestor and ('(not an ancestor)' in r[5]) == (not ancestor), project
            if 'since' in r[5]:
                paths = [str(Path(project).parent)]
                if 'CLI and MCP together' in r[5]:
                    paths = sorted({str(Path(p).parent) for p in recorded if p.startswith(f'src/{Path(rel).name}.')})
                stat = git(repo, 'diff', '--ignore-cr-at-eol', '--shortstat', pin, sha, '--', *paths)
                if not stat:
                    assert re.search(r'no (?:surface-project|CLI) change since', r[5]), project
                else:
                    files, ins = re.search(r'(\d+) files? changed, (\d+) insertion', stat).groups()
                    dels = re.search(r'(\d+) deletion', stat)
                    assert re.search(rf'\b{files} [\w ]*files? ', r[5]) and f'({ins} insertions' in r[5], (project, stat)
                    assert (dels is None) or f'{dels[1]} deletions' in r[5], (project, stat)
    folders = refs / 'Hexalith.Folders'
    for rev in ['e2252f29a2dba2b64786ee483eb59fbceaadd387', 'HEAD']:
        names = set(re.findall(r'McpServerTool\(Name = "([^"]+)"', git(folders, 'grep', '-h', 'McpServerTool(Name', rev, '--', 'src/Hexalith.Folders.Mcp')))
        assert len(names) == 49, rev
    projects_ui = git(projects_repo, 'diff', '--ignore-cr-at-eol', '--name-only', '3d256e632a7645bc2261e668ac7c74be81155f58', 'HEAD', '--', 'src/Hexalith.Projects.Contracts/Ui').split()
    assert len(projects_ui) == 2 and 'two rendered `Contracts/Ui` projection types gained fields' in fk['FK01'][4]
    assert not git(projects_repo, 'diff', '--ignore-cr-at-eol', '--shortstat', '3d256e632a7645bc2261e668ac7c74be81155f58', 'HEAD', '--', 'src/Hexalith.Projects.Mcp', 'src/Hexalith.Projects.Cli')

    # Non-surface executables are each named by an exempt row.
    assert {f for fs in executables.values() for f in fs} == {
        'src/libraries/Hexalith.Builds.Module.Cli/pack/projects/EventStore/Host.csproj',
        'src/libraries/Hexalith.Builds.Module.Cli/pack/projects/Ui/Host.csproj',
        'src/Hexalith.Folders.Client/Generation/Hexalith.Folders.Client.Generation.csproj',
        'src/Hexalith.Projects.Client/Generation/Hexalith.Projects.Client.Generation.csproj',
        'src/Hexalith.Platform.CatalogBuilder/Hexalith.Platform.CatalogBuilder.csproj',
        'src/Hexalith.Platform.Protection.Qualification.Enrollment/Hexalith.Platform.Protection.Qualification.Enrollment.csproj',
        'src/Hexalith.Platform.Protection.Qualification.Executor/Hexalith.Platform.Protection.Qualification.Executor.csproj',
        'src/Hexalith.Platform.Protection.Qualification.Observer/Hexalith.Platform.Protection.Qualification.Observer.csproj'}
    for token in ['pack/projects/EventStore/Host.csproj', 'Hexalith.Platform.CatalogBuilder', 'Generation']:
        assert token in text, token
    tests_ = sorted(Path(f).stem for rel in ROOTS for f in tracked(root / rel, '*.csproj') if re.search(r'\.(?:Cli|Mcp)\.Tests\.csproj$', f))
    assert len(tests_) == 13 and '13 `.Cli.Tests` and `.Mcp.Tests` projects' in pe['PE05'][1]
    configs = {}
    for rel in ROOTS:
        for f in tracked(root / rel, '.mcp.json', '.vscode/mcp.json', '.cursor/mcp.json'):
            servers = json.loads((root / rel / f).read_text())
            configs.setdefault(Path(rel).name.removeprefix('Hexalith.'), set()).update((servers.get('mcpServers') or servers.get('servers')))
    assert set(configs) == {'ChatBot', 'EventStore', 'Folders', 'FrontComposer', 'Projects', 'Tenants', 'Timesheets'}
    assert set().union(*configs.values()) == {'microsoft-learn', 'fluent-ui-blazor'}
    assert all(name in pe['PE06'][1] for name in configs)
    codex = {}
    for rel in ROOTS:
        for f in tracked(root / rel, '.codex/config.toml'):
            with (root / rel / f).open('rb') as handle:
                codex[Path(rel).name.removeprefix('Hexalith.')] = set(tomllib.load(handle).get('mcp_servers') or {})
    declaring = {name for name, servers in codex.items() if servers}
    assert len(codex) == 11 and declaring == {'Memories', 'Projects'}, codex
    assert set().union(*codex.values()) <= {'microsoft-learn', 'fluent-ui-blazor'}, codex
    assert '`.codex/config.toml`' in pe['PE06'][1] and '11 roots track one' in pe['PE06'][1]
    assert all(name in pe['PE06'][1] for name in declaring)

    # Roots without surfaces and their owners.
    no_surface = [rel for rel in ROOTS if rel not in surfaces]
    assert [r[1].strip('`') for r in pn.values()] == no_surface and len(no_surface) == 9
    for r in pn.values():
        rel, sha = r[1].strip('`'), r[2].strip('`')
        repo = root / rel
        assert git(repo, 'rev-parse', 'HEAD') == sha
        for f in tracked(repo, '*.cs'):
            if f.startswith('src/'):
                assert not re.search(r'\b(?:AddMcpServer|MapMcp)\(', (repo / f).read_text(errors='ignore')), f
    owners = [f for rel in ROOTS for f in [rel + '/' + x for x in tracked(root / rel)]
              if re.search(r'(?:^|/)(?:CODEOWNERS|MAINTAINERS(?:\.md)?|OWNERS(?:\.md)?)$', f)]
    assert owners == ['references/Hexalith.Platform/.github/CODEOWNERS']
    assert (refs / 'Hexalith.Platform/.github/CODEOWNERS').read_text().splitlines()[1] == '* @jpiquot'
    assert all('maintainer' in r[6] for r in ps.values()) and all('maintainer' in r[4] for r in pn.values())
    for gate in ['Story 5.2', 'Story 5.5']:
        assert gate in text
    return dict(FH=fh, FD=fd, FC=fcl, FV=fv, FK=fk, PS=ps, PE=pe, PN=pn, G=g)


# ---------------------------------------------------------------- anchors and links
ABBREV = {
    'eventstore-admin': {'Cli': 'src/Hexalith.EventStore.Admin.Cli', 'Mcp': 'src/Hexalith.EventStore.Admin.Mcp',
                         'Server': 'src/Hexalith.EventStore.Admin.Server', 'UI': 'src/Hexalith.EventStore.Admin.UI',
                         'Contracts': 'src/Hexalith.EventStore.Contracts', 'ServiceDefaults': 'src/Hexalith.EventStore.ServiceDefaults',
                         'CliTests': 'tests/Hexalith.EventStore.Admin.Cli.Tests', 'McpTests': 'tests/Hexalith.EventStore.Admin.Mcp.Tests',
                         'ServerTests': 'tests/Hexalith.EventStore.Admin.Server.Tests'},
    'technical-tools': {'Mcp': 'src/Hexalith.FrontComposer.Mcp', 'Cli': 'src/Hexalith.FrontComposer.Cli',
                        'Corpus': 'docs/skills/frontcomposer'},
}
SPINE = 'references/Hexalith.Platform/_bmad-output/planning-artifacts/architecture/architecture-platform-2026-09-27/ARCHITECTURE-SPINE.md'
PLAN = 'references/Hexalith.AI.Tools/hexalith-mcpcli-migration-instructions.md'
RULE = 'references/Hexalith.AI.Tools/hexalith-llm-instructions.md'
ESAD = 'references/Hexalith.EventStore/_bmad-output/planning-artifacts/architecture.md'
MEM = 'references/Hexalith.Memories'
CONTENT = {
    f'{SPINE}:183': '*Scope:*',
    f'{SPINE}:184': '*Legacy surfaces:*',
    f'{SPINE}:185': '*New surfaces:*',
    f'{SPINE}:211': '*Classes:*',
    f'{SPINE}:213': '*Client types:*',
    f'{PLAN}:2': "plan_version: '1.1.0'",
    f'{PLAN}:36': 'Hexalith.EventStore.Admin.Mcp',
    f'{PLAN}:42': 'A later source change',
    f'{PLAN}:70': '## Successor administration and non-gateway scope',
    f'{RULE}:65': '## Hexalith MCP and CLI ownership',
    f'{RULE}:80': '`hexalith-module` and `hexalith-evidence`',
    f'{ESAD}:297': '### AD-22',
    'Server/Authorization/AdminTenantAuthorizationFilter.cs:25': '!hasTenantArgument && admission is null',
    'Server/Controllers/AdminConsistencyController.cs:100': 'TriggerCheck(',
    'Server/Controllers/AdminConsistencyController.cs:161': 'TryResolveTenantScopeForBody(',
    'references/Hexalith.Parties/src/Hexalith.Parties.AppHost/Hexalith.Parties.AppHost.csproj:18': 'Hexalith.Parties.Mcp.csproj',
    f'{MEM}/src/Hexalith.Memories.AppHost/Hexalith.Memories.AppHost.csproj:14': 'Hexalith.Memories.Mcp.csproj',
    f'{MEM}/deploy/kubernetes/base/mcp-deployment.yaml:4': 'name: memories-mcp',
    f'{MEM}/deploy/kubernetes/base/dapr/mcp-config.yaml:4': 'name: memories-mcp-config',
    f'{MEM}/deploy/kubernetes/base/services.yaml:17': 'name: memories-mcp',
    f'{MEM}/deploy/kubernetes/base/dapr/config.yaml:28': 'appId: memories-mcp',
    f'{MEM}/deploy/kubernetes/overlays/production/kustomization.yaml:55': 'memories-mcp',
    'Server/Controllers/AdminStreamsController.cs:350': 'GetRecentlyActiveStreams',
    'UI/Services/AdminStreamApiClient.cs:736': 'X-Hexalith-Scope',
    'ServerTests/IntegrationTests/AdminAuthorizationIntegrationTests.cs:54': 'GlobalHealthRequiresExplicitOperationScope',
    'Contracts/Routing/AdminPlatformScopeCatalog.cs:20': 'AdminStreamsController',
    'Server/Services/DaprBackupCommandService.cs:443': 'CreateDeferredResult',
    'Mcp/Tools/BackupWriteTools.cs:47': 'deferred backup backend',
    'Mcp/Tools/ProjectionWriteTools.cs:140': 'destructive operation',
    'Cli/Commands/StubCommands.cs:15': 'Command unavailable',
    'Mcp/Program.cs:63': 'WithToolsFromAssembly',
    'Mcp/FrontComposerMcpOptions.cs:52': 'LifecycleToolName',
    'Cli/CliApplication.cs:20': '"inspect"',
    'Cli/CliApplication.cs:22': '"migrate"',
    'Cli/PathUtilities.cs:32': 'HasLinkedPathSegment',
    'Cli/PathUtilities.cs:61': 'HasNestedRepositorySegment',
    'src/Hexalith.Projects.Mcp/ProjectsMcpModule.cs:51': 'AddFrontComposerMcp',
    'deferred-work.md:677': 'Four of the six approved migration inventories',
    'Cli/Formatting/JsonOutputFormatter.cs:42': 'IsRawPropertyWithDescriptor',
    'Cli/Formatting/JsonOutputFormatter.cs:68': 'IsRawPropertyWithDescriptor',
    'Cli/Formatting/TableOutputFormatter.cs:148': 'SafeOutputValueFormatter.Format',
    'Cli/Formatting/CsvOutputFormatter.cs:91': 'SafeOutputValueFormatter.Format',
    'Cli/Profiles/ProfileManager.cs:74': 'catch (JsonException)',
    'Cli/Profiles/ProfileManager.cs:109': 'File.WriteAllText',
    'Cli/GlobalOptionsBinding.cs:114': 'IOException or UnauthorizedAccessException',
    'Mcp/Tools/ToolHelper.cs:124': 'ValidateTenantId',
    'Mcp/Tools/ToolHelper.cs:143': 'ValidatePathSegments',
    'Mcp/Tools/ToolHelper.cs:343': 'continuationToken',
    'Mcp/Tools/StreamTools.cs:135': 'value.Trim()',
    'Cli/ProjectSelection.cs:7': 'PathUtilities.Canonical',
    'Cli/ProjectSelection.cs:26': 'PathUtilities.Canonical',
    'Cli/ProjectSelection.cs:52': 'PathUtilities.Canonical',
    'Cli/Profiles/ProfileManager.cs:88': 'token.Length <= 4',
    'Cli/Profiles/ProfileManager.cs:112': 'File.SetUnixFileMode',
    'Cli/Formatting/OutputWriter.cs:28': 'File.WriteAllText',
    'Cli/Client/AdminApiClient.cs:24': 'new HttpClient',
    'Cli/Client/AdminApiClient.cs:104': 'EnsureSuccessStatusCode',
    'Cli/Client/AdminApiClient.cs:384': 'contentLength is 0',
    'Mcp/Program.cs:19': "errors.Add($",
    'Mcp/Program.cs:25': 'IsNullOrWhiteSpace(adminToken)',
    'Mcp/Program.cs:89': 'AuthenticationHeaderValue',
    'Cli/GeneratedOutputLoader.cs:25': 'if (build)',
    'Cli/GeneratedOutputLoader.cs:49': 'Directory.EnumerateFiles',
    'Cli/MigrationCommand.cs:33': 'HasTopLevelImports',
    'Cli/ProjectDocumentLoader.cs:6': 'HasTopLevelImports',
}


def resolve(doc, path):
    first = path.split('/', 1)[0]
    if path.startswith('deferred-work.md'):
        return base / path
    if path.startswith('references/'):
        return root / path
    if path.startswith('.github/CODEOWNERS'):
        return refs / 'Hexalith.Platform' / path
    if first in ABBREV[doc]:
        repo = es if doc == 'eventstore-admin' else fc
        return repo / (ABBREV[doc][first] + '/' + path.split('/', 1)[1])
    m = re.match(r'(?:src|tests)/Hexalith\.(\w+)\.', path)
    if m and (refs / f'Hexalith.{m[1]}').is_dir():
        return refs / f'Hexalith.{m[1]}' / path
    if path.startswith('samples/'):
        return fc / path
    raise AssertionError(('unresolved anchor', doc, path))


def check_anchors(doc, text):
    count, checked = 0, set()
    current = None
    for line in text.splitlines():
        # A continuation binds to the last explicit path in the same table row or prose paragraph.
        if line.startswith('|') or not line.strip():
            current = None
        for m in re.finditer(r'`(?:([^`\s:]+(?:\.(?:cs|csproj|md|json|yaml)|CODEOWNERS))|):(\d+)`', line):
            path, number = m.group(1), int(m.group(2))
            if path:
                current = path
            assert current, ('continuation without path', doc, line[:80])
            location = resolve(doc, current)
            lines = location.read_text().splitlines()
            assert 1 <= number <= len(lines) and lines[number - 1].strip(), (doc, current, number)
            key = f'{current}:{number}'
            if key in CONTENT:
                assert CONTENT[key] in lines[number - 1], (doc, key)
                checked.add(key)
            count += 1
    for target in re.findall(r'\]\(([^)]+)\)', text):
        path, _, fragment = target.partition('#')
        location = base / path if path else base / f'{doc}-migration-inventory-v1.md'
        assert location.exists(), target
        if fragment:
            headings = re.findall(r'^#{1,6} (.+)$', location.read_text(), re.M)
            assert fragment in {re.sub(r'[^\w -]', '', h.lower()).replace(' ', '-') for h in headings}, target
    return count, checked


def check_row_anchor_content(admin, technical):
    for key, r in admin['AC'].items():
        anchor = re.search(r'`(Cli/[^`]+):(\d+)`', r[12])
        line = resolve('eventstore-admin', anchor[1]).read_text().splitlines()[int(anchor[2]) - 1]
        leaf = r[1].strip('`').split()[-1]
        assert f'new("{leaf}"' in line or f'StubCommands.Create("{leaf}"' in line, key
    for key, r in admin['AU'].items():
        anchor = re.search(r'`(Cli/[^`]+):(\d+)`', r[7])
        line = resolve('eventstore-admin', anchor[1]).read_text().splitlines()[int(anchor[2]) - 1]
        assert f'new("{r[1].split("`")[3]}"' in line, key
    for key, r in admin['AM'].items():
        anchor = re.search(r'`(Mcp/Tools/[^`]+):(\d+)`', r[12])
        line = resolve('eventstore-admin', anchor[1]).read_text().splitlines()[int(anchor[2]) - 1]
        assert f'Name = "{r[1].strip("`")}"' in line, key
    for key, r in technical['FD'].items():
        if key != 'FD13':
            anchor = re.search(r'`(Corpus/[^`]+):(\d+)`', r[9])
            line = resolve('technical-tools', anchor[1]).read_text().splitlines()[int(anchor[2]) - 1]
            assert line == f'resourceUri: frontcomposer://skills/{r[2].strip("`")}', key


# ---------------------------------------------------------------- workflow and repository state
def workflow_state(spec, sprint):
    status = re.search(r"^status: '([^']+)'$", spec, re.M)[1]
    story = re.search(r'^  5-1-inventory-eventstore-admin-and-technical-tool-operations: (\S+)', sprint, re.M)[1]
    return status, story


def check_workflow(status, story, pending):
    if pending:
        assert (status, story) in {('in-progress', 'in-progress'), ('in-review', 'in-progress'), ('in-review', 'review')}, (status, story)
    else:
        assert (status, story) in {('in-progress', 'in-progress'), ('in-review', 'review'), ('done', 'review'), ('done', 'done')}


def frozen_digest(spec):
    block = spec.split('<frozen-after-approval', 1)[1].split('</frozen-after-approval>', 1)[0]
    return hashlib.sha256(block.encode()).hexdigest()


def check_census_pins(evidence):
    pins = dict(re.findall(r'^\| `(references/[^`]+)` \| `([0-9a-f]{40})` \|', evidence, re.M))
    assert sorted(pins) == sorted(ROOTS), 'census pin coverage'
    for rel, sha in pins.items():
        assert git(root / rel, 'rev-parse', 'HEAD') == sha, ('stale census pin', rel, sha)
    return pins


def check_repository():
    check_census_pins((base / 'evidence/story-5-1/verification.md').read_text())
    gitlinks = {path: sha for sha, path in re.findall(r'^160000 commit (\w+)\t(\S+)$', git(root, 'ls-tree', 'HEAD', 'references/'), re.M)}
    assert sorted(gitlinks) == sorted(ROOTS) and len(ROOTS) == 17
    for rel in ROOTS:
        assert git(root / rel, 'rev-parse', 'HEAD') == gitlinks[rel], rel
        assert not git(root / rel, 'status', '--porcelain'), rel
    historical = [f'{m}-migration-inventory-v1.md' for m in ['parties', 'folders', 'projects', 'frontcomposer', 'chatbot', 'memories']]
    assert subprocess.run(['git', '-C', str(root), 'diff', '--quiet', 'HEAD', '--', *[str(base / h) for h in historical]]).returncode == 0
    status = subprocess.check_output(['git', '-C', str(root), 'status', '--porcelain', '-z', '--untracked-files=all'], text=True)
    changed = [entry[3:] for entry in status.split('\0') if entry]
    # A clean post-commit checkout has no changes; any working-tree change must stay in this story's area.
    assert all(p.startswith('_bmad-output/implementation-artifacts/') for p in changed), changed
    assert git(refs / 'Hexalith.AI.Tools', 'rev-parse', 'HEAD') == '1745b6663ad32bb1288167135ed0f979366c53a0'
    authored = ['eventstore-admin-migration-inventory-v1.md', 'technical-tools-migration-inventory-v1.md',
                'evidence/story-5-1/verification.md', 'evidence/story-5-1/commitlint-validation.txt', spec_name, 'sprint-status.yaml', 'epic-5-context.md',
                *sorted(str(f.relative_to(base)) for f in (base / 'evidence/story-5-1/planning').iterdir()),
                *sorted(str(f.relative_to(base)) for f in (base / 'evidence/story-5-1/approval').rglob('*') if f.is_file())]
    assert len(authored) == 15, authored
    for name in authored:
        data = (base / name).read_bytes()
        assert b'\r' not in data and data.endswith(b'\n') and not data.endswith(b'\n\n'), name
        assert not any(line.rstrip() != line for line in data.decode().split('\n')), name
    return authored


# ---------------------------------------------------------------- run
authored_files = check_repository()
admin_text = (base / 'eventstore-admin-migration-inventory-v1.md').read_text()
tech_text = (base / 'technical-tools-migration-inventory-v1.md').read_text()
admin = check_admin(admin_text)
technical = check_technical(tech_text)
def check_all_anchors(admin_doc, tech_doc):
    counts = [check_anchors('eventstore-admin', admin_doc), check_anchors('technical-tools', tech_doc)]
    assert set(CONTENT) == counts[0][1] | counts[1][1], set(CONTENT) - counts[0][1] - counts[1][1]
    return counts


anchor_counts = check_all_anchors(admin_text, tech_text)
check_row_anchor_content(admin, technical)


def check_handoff_partition(evidence, admin_rows):
    handoff = evidence.rsplit('- **Story 5.2, generic non-gateway capability decision.**', 1)[1].split('- **Story 5.3', 1)[0]
    ids = []
    for line in re.findall(r'^  - .*(?:\n    .*)*', handoff, re.M):
        for first, last in re.findall(r'\b(A[CM]\d{2})(?:–(A[CM]\d{2}))?', line):
            if last:
                assert first[:2] == last[:2] and int(first[2:]) < int(last[2:]), (first, last)
                ids += [f'{first[:2]}{i:02d}' for i in range(int(first[2:]), int(last[2:]) + 1)]
            else:
                ids.append(first)
    assert len(ids) == len(set(ids)) and sorted(ids) == sorted([*admin_rows['AC'], *admin_rows['AM']]), 'Story 5.2 class partition'


check_handoff_partition((base / 'evidence/story-5-1/verification.md').read_text(), admin)
approved_rows = sum(len(v) for v in admin.values()) + sum(len(v) for v in technical.values())


def check_receipt(receipt):
    assert receipt['decision'] == 'approved' and receipt['inventory_version'] == '1.0.0'
    assert receipt['reviewed_candidate_version'] == '1.0.0-candidate.3'
    assert receipt['approval_authority'] == 'requesting-user-owning-maintainer'
    assert receipt['exact_approval_instruction'] == 'I approve'
    assert receipt['exact_authority_confirmation'] == 'Authorized for all listed maintainer roles'
    assert receipt['mcpcli_revision'] == 'fa7c51601041ee6cf0d2f9d4613fb405758f2f7c'
    assert receipt['source_revisions'] == check_census_pins((base / 'evidence/story-5-1/verification.md').read_text())
    expected = {
        str(base.relative_to(root) / 'eventstore-admin-migration-inventory-v1.md'): admin,
        str(base.relative_to(root) / 'technical-tools-migration-inventory-v1.md'): technical,
    }
    assert len(receipt['inventories']) == 2
    assert {entry['path'] for entry in receipt['inventories']} == set(expected)
    for entry in receipt['inventories']:
        assert hashlib.sha256((root / entry['path']).read_bytes()).hexdigest() == entry['approved_sha256']
        assert entry['candidate_path'] == str(base.relative_to(root) / 'evidence/story-5-1/approval/candidate.3' / Path(entry['path']).name)
        candidate = (root / entry['candidate_path']).read_bytes()
        assert hashlib.sha256(candidate).hexdigest() == entry['candidate_sha256']
        assert frontmatter(candidate.decode())['inventory_version'] == '1.0.0-candidate.3'
        assert entry['row_ids'] == [key for group in expected[entry['path']].values() for key in group]


receipt = json.loads((base / 'evidence/story-5-1/approval/approval.json').read_text())
check_receipt(receipt)
spec_status, sprint_status = workflow_state(spec_text, (base / 'sprint-status.yaml').read_text())
check_workflow(spec_status, sprint_status, pending=False)
digest = frozen_digest(spec_text)
assert digest == FROZEN_SHA256, digest


def rejects(check, damaged, label):
    try:
        check(damaged)
    except (AssertionError, KeyError, IndexError, TypeError, ValueError):
        return
    raise AssertionError('accepted damaged input: ' + label)


line_of = lambda text, key: next(l for l in text.splitlines() if l.startswith(f'| {key} |'))
damages = [
    (check_admin, admin_text.replace(line_of(admin_text, 'AC13') + '\n', ''), 'missing CLI row'),
    (check_admin, admin_text.replace('| AM02 |', '| AM01 |', 1), 'duplicate MCP row'),
    (check_admin, admin_text.replace(line_of(admin_text, 'AM28'), line_of(admin_text, 'AM28') + '\n' + line_of(admin_text, 'AM28').replace('AM28', 'AM29').replace('`types-list`', '`types-search`')), 'extra MCP row'),
    (check_admin, admin_text.replace(line_of(admin_text, 'AC05'), line_of(admin_text, 'AC05').replace('| read |', '|  |', 1)), 'incomplete field'),
    (check_admin, admin_text.replace('approval_status: approved', 'approval_status: pending'), 'missing approval'),
    (check_admin, admin_text.replace(line_of(admin_text, 'AM14'), line_of(admin_text, 'AM14').replace(APPROVAL_REF, 'approved by owner')), 'row approval claim'),
    (check_admin, admin_text.replace(line_of(admin_text, 'AC13'), line_of(admin_text, 'AC13').replace('`AdminOperator`', '`AdminReadOnly`')), 'wrong policy'),
    (check_admin, admin_text.replace(line_of(admin_text, 'AC21'), line_of(admin_text, 'AC21').replace('destructive: removes', 'state change: removes')), 'lost destructive effect'),
    (check_admin, admin_text.replace(line_of(admin_text, 'AM12'), line_of(admin_text, 'AM12').replace('UI-only and confirmation-required', 'UI-only')), 'lost confirmation class'),
    (check_admin, admin_text.replace(line_of(admin_text, 'AM23'), line_of(admin_text, 'AM23').replace('No matching server route', 'Matched route')), 'route mismatch hidden'),
    (check_admin, admin_text.replace(line_of(admin_text, 'AC14'), line_of(admin_text, 'AC14').replace('| defer | exclude |', '| replace | include |')), 'invented replacement'),
    (check_technical, tech_text.replace(line_of(tech_text, 'PS13') + '\n', ''), 'missing census surface'),
    (check_technical, tech_text.replace(line_of(tech_text, 'FD07') + '\n', ''), 'missing documentation resource'),
    (check_technical, tech_text.replace(line_of(tech_text, 'PS06'), line_of(tech_text, 'PS06').replace('(34 insertions)', '(35 insertions)')), 'wrong drift'),
    (check_technical, tech_text.replace('external_maintainer_approval: approved', 'external_maintainer_approval: pending'), 'missing owner approval'),
    (lambda _: check_workflow('done', 'review', pending=True), None, 'completion while pending'),
    (lambda s: check_all_anchors(s, tech_text), admin_text.replace('`Cli/Commands/HealthCommand.cs:47`', '`Cli/Commands/HealthCommand.cs:9999`'), 'out-of-range anchor'),
    (lambda s: check_all_anchors(s, tech_text), admin_text.replace('`Server/Controllers/AdminStreamsController.cs:350`', '`Server/Controllers/AdminStreamsController.cs:351`'), 'moved content anchor'),
    (lambda s: check_all_anchors(admin_text, s), tech_text.replace('`Cli/PathUtilities.cs:32`', '`Cli/PathUtilities.cs:33`'), 'moved technical anchor'),
    (check_admin, admin_text.replace('`GetCorrelationTraceMap`', 'GetCorrelationTraceMap'), 'HTTP-only action omitted'),
    (check_technical, tech_text.replace(line_of(tech_text, 'PN04') + '\n', ''), 'missing root census row'),
    (check_technical, tech_text.replace(line_of(tech_text, 'PS10'), line_of(tech_text, 'PS10').replace('`PackAsTool` `folders`', '`PackAsTool` `folder`')), 'wrong packaging metadata'),
    (check_census_pins, (base / 'evidence/story-5-1/verification.md').read_text().replace('| `567604b616613ba429be0609636d805db776a709` |', '| `beb85e497957fedc66854013efd2cc4bd216ecbc` |'), 'stale exempt Builds census pin'),
]
for field, replacement in [('exact_authority_confirmation', 'Session reviewer only'),
                           ('source_revisions', {}), ('inventories', [])]:
    damaged = json.loads(json.dumps(receipt))
    damaged[field] = replacement
    damages.append((check_receipt, damaged, 'approval receipt ' + field))
for field in ['approved_sha256', 'candidate_sha256', 'row_ids']:
    damaged = json.loads(json.dumps(receipt))
    damaged['inventories'][0][field] = [] if field == 'row_ids' else '0' * 64
    damages.append((check_receipt, damaged, 'approval receipt ' + field))
for check, damaged, label in damages:
    rejects(check, damaged, label)

print(f"PASS: EventStore {ES_SHA} clean; CLI graph 31 registered (21 remote, 7 local, 3 stubs) = AC01-AC31; 6 unregistered helpers = AU01-AU06; 28 MCP tools (18 read, 7 confirm-gated, 3 process-local) = AM01-AM28; 0 resources/prompts.")
print(f"PASS: 68 Admin.Server actions parsed; 29 reached by the heads with matching policies, tenant filters and platform scope; 39 HTTP-only actions listed; stream-list root GET has no server route.")
print(f"PASS: FrontComposer {FC_SHA} vs historical {FC_OLD}: Mcp and corpus trees identical, 6 CLI files changed; 1 lifecycle tool, 2 families, 13 resources, 2 compiler leaves, 9 variants, 4 consumers.")
print(f"PASS: census of {len(ROOTS)} root references: 13 production surfaces in 7 repositories, 2 exempt Builds tools, 9 roots without surfaces, executables and configs classified; owners recorded.")
print(f"PASS: {anchor_counts[0][0] + anchor_counts[1][0]} source anchors resolve to non-blank lines ({len(CONTENT)} content-checked); local links resolve; historical inventories unchanged; working-tree changes confined to _bmad-output/implementation-artifacts/; {len(authored_files)} story files are LF without trailing whitespace.")
print(f"PASS: rejected {len(damages)} damaged inputs (missing, duplicate, extra, incomplete, approval claims, wrong policy, lost effect/confirmation, hidden mismatch, invented replacement, census/resource omissions, drift, packaging, anchors, census pins, premature completion, approval receipt).")
print(f"PASS: {approved_rows} rows carry A1 owning-maintainer approval; receipt binds candidate/final hashes, exact instructions, row IDs and all source pins. Workflow states: spec={spec_status}; sprint={sprint_status}. Frozen block sha256={digest}.")
PY
git diff --check
```

## Recorded execution (2026-11-07)

At that review, the initial rerun of the previous block, extracted from this
file and invoked with `bash -e` from the McpCli root, exited 1 at Python line 524:
`assert git(repo, 'rev-parse', 'HEAD') == sha` in `check_technical`.
That exposed the stale PN pins; no inventory approval was inferred.
After refreshing the census and the review corrections, the candidate.2 block was
extracted again and executed with `bash -e` from the McpCli root; it exited 0. `git diff --check` reported
no whitespace error; it covers tracked files only, so the Python block checks
all 11 story files itself. Git also prints the pre-existing
`warning: unable to find all commit-graph files`; command exit codes determine
the result. Output:

```text
PASS: EventStore 3d4ba67db99f2f0bcd64b7d353609b555870cc9b clean; CLI graph 31 registered (21 remote, 7 local, 3 stubs) = AC01-AC31; 6 unregistered helpers = AU01-AU06; 28 MCP tools (18 read, 7 confirm-gated, 3 process-local) = AM01-AM28; 0 resources/prompts.
PASS: 68 Admin.Server actions parsed; 29 reached by the heads with matching policies, tenant filters and platform scope; 39 HTTP-only actions listed; stream-list root GET has no server route.
PASS: FrontComposer fbb9c3822dfa407e72739238cd472567f45f1e82 vs historical 81a440a8890a17edb39924bd0cf676eb6f6b5c25: Mcp and corpus trees identical, 6 CLI files changed; 1 lifecycle tool, 2 families, 13 resources, 2 compiler leaves, 9 variants, 4 consumers.
PASS: census of 17 root references: 13 production surfaces in 7 repositories, 2 exempt Builds tools, 9 roots without surfaces, executables and configs classified; owners recorded.
PASS: 386 source anchors resolve to non-blank lines (52 content-checked); local links resolve; historical inventories unchanged; working-tree changes confined to _bmad-output/implementation-artifacts/; 11 story files are LF without trailing whitespace.
PASS: rejected 23 damaged inputs (missing, duplicate, extra, incomplete, approval claims, wrong policy, lost effect/confirmation, hidden mismatch, invented replacement, census/resource omissions, drift, packaging, anchors, census pins, premature completion).
BLOCKED: 156 rows carry A0 (approval pending); owner approval is required before Story 5.1 completion. Workflow states: spec=in-review; sprint=in-progress. Frozen block sha256=8be7892597e4e5f0aeb4a1aa8acef4d57eacffac4b75de417c882494a557a105.
```

The `BLOCKED` line is the expected state: the static checks are complete, but
no owner approval exists. No .NET build, test suite, live topology or legacy
tool was run; this change is documentation only.

## Recorded execution (2026-11-08)

Resumed the three review layers at McpCli HEAD
`fa7c51601041ee6cf0d2f9d4613fb405758f2f7c`. The edge-case and verification-gap
layers returned no findings; the blind layer reported ten. Nine documentation
corrections are applied as P28–P36 in the spec; both inventories are now
`1.0.0-candidate.3`. The remaining finding concerns pre-existing Epic 4 code
and is explicitly unverified, as described below.

Extracted the current first Bash block to
`/tmp/mcpcli-story-5-1-static-check.sh` and ran
`bash -e /tmp/mcpcli-story-5-1-static-check.sh` from the repository root:
exit 0. The block includes `git diff --check`, which also passed. Its output:

```text
PASS: EventStore 3d4ba67db99f2f0bcd64b7d353609b555870cc9b clean; CLI graph 31 registered (21 remote, 7 local, 3 stubs) = AC01-AC31; 6 unregistered helpers = AU01-AU06; 28 MCP tools (18 read, 7 confirm-gated, 3 process-local) = AM01-AM28; 0 resources/prompts.
PASS: 68 Admin.Server actions parsed; 29 reached by the heads with matching policies, tenant filters and platform scope; 39 HTTP-only actions listed; stream-list root GET has no server route.
PASS: FrontComposer fbb9c3822dfa407e72739238cd472567f45f1e82 vs historical 81a440a8890a17edb39924bd0cf676eb6f6b5c25: Mcp and corpus trees identical, 6 CLI files changed; 1 lifecycle tool, 2 families, 13 resources, 2 compiler leaves, 9 variants, 4 consumers.
PASS: census of 17 root references: 13 production surfaces in 7 repositories, 2 exempt Builds tools, 9 roots without surfaces, executables and configs classified; owners recorded.
PASS: 408 source anchors resolve to non-blank lines (65 content-checked); local links resolve; historical inventories unchanged; working-tree changes confined to _bmad-output/implementation-artifacts/; 11 story files are LF without trailing whitespace.
PASS: rejected 23 damaged inputs (missing, duplicate, extra, incomplete, approval claims, wrong policy, lost effect/confirmation, hidden mismatch, invented replacement, census/resource omissions, drift, packaging, anchors, census pins, premature completion).
BLOCKED: 156 rows carry A0 (approval pending); owner approval is required before Story 5.1 completion. Workflow states: spec=in-review; sprint=in-progress. Frozen block sha256=8be7892597e4e5f0aeb4a1aa8acef4d57eacffac4b75de417c882494a557a105.
```

No repository .NET build or test suite, legacy command, migration or live host
ran for these corrections. Source revisions, registrations and dispositions
are unchanged; all 156 A0 approval references remain pending.

### Inherited review follow-up

The broad saved review baseline also includes the earlier Epic 4 catalog-reader
repairs. The blind reviewer noted that the source seal excludes generated
`obj/` C# inputs. Its standalone .NET 10 experiment in
`/tmp/mcpcli-blind-obj-input-hgsp8wm2` built a project once, appended a module
initializer to its generated AssemblyInfo file, advanced that file's timestamp
by one hour, then built again with `--no-restore`. Both builds and execution
exited 0; the initializer wrote `unsealed obj code executed` to stderr.
The reviewer confirmed that this did not exercise `GenerateAsync` or establish
an injection point in its fresh-directory, first-build flow. It is an unverified
question, recorded under the owning Epic 4 source spec at
`deferred-work.md:806`. No runtime defect or live acceptance is inferred.

## Compatibility handoffs

- **Story 5.2, generic non-gateway capability decision.** Inputs are Admin G2
  and G3 and technical G2. Each Admin row belongs to exactly one class:
  - infrastructure administration: AC09–AC13, AC18–AC21, AM01, AM03–AM06,
    AM10–AM15, AM19;
  - operator diagnostics: AC01–AC02, AM07–AM09, AM28;
  - stream and state reads: AC03–AC08, AM02, AM20–AM24;
  - tenant administration reads: AC14–AC17, AM25–AM27;
  - process-local context: AM16–AM18;
  - retained unavailable stubs: AC22–AC24;
  - local credential and profile configuration: AC25–AC30 (Admin G6, Story 5.3);
  - shell completion, out of McpCli v1 under PRD §8.2: AC31.

  The Admin behavior handoff also includes AV02's corrupt-store overwrite and
  profile-load fallback, link-following in-place writes and post-write permissions,
  AV03's conditional CLI redaction and unconfirmed output-file overwrite,
  AV04's default redirects and empty-body HTTP errors, AV05's startup validation
  boundary and invalid-URL disclosure, AV06's error and
  cancellation categories, AV07's input guards, AV08's trim-before-fallback
  and AM22's unavailable cursor paging. Preserve each or obtain the owning
  maintainer's explicit change decision.

  The technical classes are lifecycle status (FH01, FV01), the manifest
  command family (FH02, classified by each consumer), documentation and
  projection resources (FD01–FD13, FH03) and local compiler tooling
  (FC01–FC02, including inspect's changed project selection in FV09).
  Without an explicit build, inspection establishes no source freshness; migration
  omits import-only files and warns on detected top-level MSBuild imports.
  Preserve those diagnostics and limits or obtain an explicit owner change.
  The decision must keep Platform AD-14's public-client denial of
  UI-only and confirmation-required operations, define treatment of the
  destructive set and name which operations become Gateway contracts and which
  need another authenticated transport. MCP resources and prompts,
  event-stream reading, plug-in loading and executor retries stay out of
  McpCli v1 unless the PRD changes.
- **Story 5.3, enrollment and profiles.** No row is `replace`, so nothing is
  enrollable. Admin G6 forbids automatic migration of `~/.eventstore/profiles.json`
  credentials; profiles bind one environment. Technical G3 asks the Projects,
  Memories, Folders and ChatBot owners to re-pin or confirm their companion
  inventories before their rows are used as enrollment inputs.
- **Story 5.4, parity and safety.** Negative evidence must deny every Admin
  remote row (UI-only) and the seven `confirm`-gated MCP writes
  (confirmation-required) through McpCli. The AV10 and AV11 source gaps must be
  resolved upstream before either head can serve as a parity baseline. The
  cross-head table records that similar names prove no equivalence.
- **Story 5.5, retirement.** Keep the compatibility binaries listed in PS01–PS13
  versioned and labeled with their removal gates, outside every Platform
  composition, and stop routing them from the Parties and Memories AppHosts
  and the Memories Kubernetes base and production overlay listed under the
  technical census. Admin G5 and technical G4 restate the ordering: EventStore Admin
  waits for its administration contract and destructive-operation safety
  evidence; the FrontComposer host and Projects plug-in retire together;
  Memories waits for forwarded per-user identity. Technical G5 uses this census
  as the baseline for rejecting new proprietary MCP/CLI projects or release
  entries. A deferred row is never counted as retired.

## Unresolved gaps

These remain open. Each inventory gap is retained in a row or gate, without a
duplicate ledger entry. The separate inherited, unverified source-seal question
is recorded under its owning Epic 4 source spec (`deferred-work.md:806`).

- **Owner inventory approval resolved:** A1 records the requesting user's
  approval and explicit authority confirmation for all 156 rows. The approval
  receipt binds the reviewed candidate, final inventory bytes and source pins.
  Downstream implementation and retirement gates remain unresolved.
- **Admin health platform scope (AV10, G4):** from source, `GET
  /api/v1/admin/health` is denied without an admitted `X-Hexalith-Scope`
  header, which only Admin.UI sends, so the pinned server source denies AC01,
  AM08 and AM09; optional-tenant lists without a tenant are also denied. This
  is static reading; no request was sent. Not previously in the ledger.
- **Stream-list route mismatch (AV11, G4):** AC03 and AM23 request a root GET
  the controller does not register. Not previously in the ledger.
- **Token and URL exposure (AC26, AC27, AC30, AV05, G4):** raw-token
  JSON, complete short-token display in other CLI formats and verbatim
  invalid-URL startup diagnostics are legacy privacy gaps. No target parity
  requirement is inferred. Not previously in the ledger.
- **Local file safety (AV02, AV03, G6):** profile saves and optional output
  writes follow links and truncate in place without atomic replacement or
  confirmation; profile permissions are applied after writing. Owner decisions
  must preserve McpCli's existing store and file-safety guarantees.
- **Transport and compiler limits (AV04, FV06, FV07):** CLI default redirects,
  empty-body HTTP failures, generated-output freshness and import-only migration
  exclusions need compatibility decisions, not inferred parity.
- **Backup backend deferred (AV12, G3):** AM01 submits to a backend that returns
  `Deferred`.
- **Companion inventory drift (technical G3):** surface source changed since
  the Projects, Memories, Folders and ChatBot inventory pins; whether a
  versioned update is required is undecided. Not previously in the ledger.
- **Already tracked, not duplicated:** the FrontComposer, Projects, Folders and
  ChatBot inventory pins are unpublished upstream (`deferred-work.md:677`); the
  planning artifacts' conflicting EventStore Admin timing statements
  (`deferred-work.md:144`).

## Evidence still absent

A generic non-gateway contract and transport decision;
any decorated replacement Contracts, Gateway routing or enrollment; authenticated
selected-environment authorization, audit, output and exit-code parity;
preservation or owner-approved change of REST/Dapr semantics, freshness,
redaction, task context, actor attribution, paging, token budgets and
idempotency (`epic-5-context.md:26`); destructive-operation safety evidence;
release, rollback and retirement evidence.
Static source reading cannot substitute for any of these or authorize loss of an
existing capability.

## Owning-maintainer approval and final verification (2026-11-08)

The requesting user approved both reviewed candidate.3 inventories with
"I approve", then confirmed "Authorized for all listed maintainer roles" for
EventStore, platform/operator, FrontComposer and every census owner. Both
inventories are finalized as `1.0.0`; every row cites A1. The
[approval receipt](approval/approval.json) binds the exact instructions,
explicit authority, all 156 row IDs, McpCli revision and 17 source pins. Exact
reviewed candidate files are preserved under `approval/candidate.3/`, and the
receipt binds both candidate and final inventory SHA-256 values. This resolves
Story 5.1's inventory approval task; the spec is `done`, and the sprint entry is
`review` as required by the build workflow. All downstream implementation,
authorization, parity and retirement gates retain their scope.

The first Bash block in this file is updated for approved inventories. After
`npm ci`, the exact local commit message passed the pinned commitlint CLI with
exit 0 and no warnings; [validation evidence](commitlint-validation.txt) records
the full message and result. Reran
`bash -e /tmp/mcpcli-story-5-1-static-check.sh` with exit 0, including
`git diff --check`. Output:

```text
PASS: EventStore 3d4ba67db99f2f0bcd64b7d353609b555870cc9b clean; CLI graph 31 registered (21 remote, 7 local, 3 stubs) = AC01-AC31; 6 unregistered helpers = AU01-AU06; 28 MCP tools (18 read, 7 confirm-gated, 3 process-local) = AM01-AM28; 0 resources/prompts.
PASS: 68 Admin.Server actions parsed; 29 reached by the heads with matching policies, tenant filters and platform scope; 39 HTTP-only actions listed; stream-list root GET has no server route.
PASS: FrontComposer fbb9c3822dfa407e72739238cd472567f45f1e82 vs historical 81a440a8890a17edb39924bd0cf676eb6f6b5c25: Mcp and corpus trees identical, 6 CLI files changed; 1 lifecycle tool, 2 families, 13 resources, 2 compiler leaves, 9 variants, 4 consumers.
PASS: census of 17 root references: 13 production surfaces in 7 repositories, 2 exempt Builds tools, 9 roots without surfaces, executables and configs classified; owners recorded.
PASS: 408 source anchors resolve to non-blank lines (65 content-checked); local links resolve; historical inventories unchanged; working-tree changes confined to _bmad-output/implementation-artifacts/; 15 story files are LF without trailing whitespace.
PASS: rejected 29 damaged inputs (missing, duplicate, extra, incomplete, approval claims, wrong policy, lost effect/confirmation, hidden mismatch, invented replacement, census/resource omissions, drift, packaging, anchors, census pins, premature completion, approval receipt).
PASS: 156 rows carry A1 owning-maintainer approval; receipt binds candidate/final hashes, exact instructions, row IDs and all source pins. Workflow states: spec=done; sprint=review. Frozen block sha256=8be7892597e4e5f0aeb4a1aa8acef4d57eacffac4b75de417c882494a557a105.
```

The six additional damaged-input cases reject a session-only authority
confirmation, missing source pins or inventory bindings, altered final or
candidate hashes, and missing row IDs. The earlier completion-while-pending
negative check still applies. No repository .NET build, legacy command or live
service was required or run. The inherited Epic 4 question remains explicitly
unverified and deferred at `deferred-work.md:806`.
