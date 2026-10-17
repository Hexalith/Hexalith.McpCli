# Story 4.3 static verification

Run this entire block from the McpCli root with Python 3 and Git. It reads only
the two pinned upstream checkouts, local inventories and ordinary FrontComposer
documentation resource metadata. It never discovers or loads agent `SKILL.md`
manifests, restores packages, runs legacy tools or changes a reference checkout.

These checks verify source sets, variants, row references and the recorded
session-approved deferred scope at inventory version 1.0.0. Pending approval
fails. No static checker supplies external owning-maintainer sign-off, package
closure, Catalog coverage, Gateway behavior, security parity or retirement
readiness. Workflow review and final status transitions remain separate gates;
the block checks that the spec and sprint states agree at each applicable stage.

```bash
set -e
python3 - <<'PY'
from pathlib import Path
from collections import Counter
import re
import subprocess

root = Path.cwd()
base = root / '_bmad-output/implementation-artifacts'
spec_name = 'spec-4-3-approve-projects-and-frontcomposer-migration-inventories.md'
spec = (base / spec_name).read_text()
spec_status = re.search(r"^status: '([^']+)'$", spec, re.M)[1]
sprint = (base / 'sprint-status.yaml').read_text()
sprint_status = re.search(r'^  4-3-approve-projects-and-frontcomposer-migration-inventories: (\S+)$', sprint, re.M)[1]
assert (spec_status, sprint_status) in {('in-progress','in-progress'), ('in-review','in-progress'), ('done','review'), ('done','done')}
assert '"approve"' in spec and 'session scope approval' in spec
assert 'No external' in spec and 'owning-maintainer sign-off is asserted' in spec
approval_anchor = '#a1-session-approval-2026-10-16'
approval_ref = f'[A1]({approval_anchor})'
pins = {
    'projects': ('Hexalith.Projects', '3d256e632a7645bc2261e668ac7c74be81155f58'),
    'frontcomposer': ('Hexalith.FrontComposer', '81a440a8890a17edb39924bd0cf676eb6f6b5c25'),
}

def check_approval(module, text):
    sha = pins[module][1]
    for literal in ["inventory_version: '1.0.0'", 'status: approved\n',
                    'approval_status: session-approved\n',
                    'approval_authority: requesting-user-session\n',
                    f"approval_ref: '{approval_anchor}'",
                    'external_maintainer_approval: unasserted\n',
                    f"source_revision: '{sha}'", f"source_spec: '_bmad-output/implementation-artifacts/{spec_name}'",
                    '## A1 Session approval (2026-10-16)', '**Exact approving instruction:** "approve"',
                    'external', 'owning-maintainer sign-off is asserted', 'retirement']:
        assert literal in text, (module, literal)
    assert 'approval-pending' not in text and 'approval_status: pending' not in text
    assert 'maintainer_approval_ref:' not in text
    # A1 is a shared decision and must name both exact source revisions.
    assert all(sha in text for repo, sha in pins.values())

documents = {}
for module, (repo, sha) in pins.items():
    up = root / 'references' / repo
    git = lambda *args: subprocess.check_output(['git', '-C', str(up), *args], text=True).strip()
    assert git('rev-parse', 'HEAD') == sha, module
    assert not git('status', '--porcelain'), module
    text = (base / f'{module}-migration-inventory-v1.md').read_text()
    documents[module] = text
    check_approval(module, text)

def rows(text, widths):
    result = {}
    for line in text.splitlines():
        if not re.match(r'^\| [A-Z]\d+ \|', line):
            continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        key = cells[0]
        assert key not in result, key
        assert key[0] in widths and len(cells) == widths[key[0]] and all(cells), line
        assert cells[-1] == approval_ref, key
        if key[0] == 'V':
            assert cells[2] == 'defer / exclude', key
        elif key[0] != 'G':
            offset = 3 if key[0] in 'LD' else 2
            assert cells[offset:offset+2] == ['defer', 'exclude'], key
        result[key] = cells
    for prefix, count in Counter(k[0] for k in result).items():
        expected = {f'{prefix}{i}' if prefix == 'G' else f'{prefix}{i:02d}' for i in range(1, count+1)}
        assert {k for k in result if k.startswith(prefix)} == expected
    return result

p = rows(documents['projects'], dict(R=8, M=8, L=8, V=6, G=4))
f = rows(documents['frontcomposer'], dict(H=8, D=8, C=8, V=6, G=4))
assert Counter(k[0] for k in p) == dict(R=11, M=5, L=18, V=12, G=6)
assert Counter(k[0] for k in f) == dict(H=3, D=13, C=2, V=8, G=4)
for inventory, prefixes in [(p,'RML'), (f,'HDC')]:
    for prefix in prefixes:
        names = [cells[1] for key,cells in inventory.items() if key[0] == prefix]
        assert len(names) == len(set(names)), prefix

# Guard the documented variant/authority handoffs as well as their row counts.
# These are static requirements, not proof that any replacement implements them.
variant_terms = {
    'projects': {
        'V01': ['first visible project', '--project-id', 'DefaultResourceTake (50 by default)', 'MaxResourceTake (default 200)', 'fall back to 25', 'cap rows at 100', 'audit dispatch fixes 25', 'helper permits up to 100', 'envelope paging'],
        'V02': ['--conversation-id', '--folder-id', '--file-id', 'static'],
        'V03': ['first 25', 'unavailable', 'partial'],
        'V04': ['local metadata', 'No state validation'],
        'V05': ['task', 'dry-run', 'reevaluate', 'descriptor', 'Gateway/module admission'],
        'V06': ['Relink folder/file/memory', 'unlink conversation/file/memory', 'transient', 'ReplacementConfirmed', 'unsupported'],
        'V07': ['Acknowledged', 'Syncing', 'Confirmed', 'REST refresh', 'acceptance only', 'executor retry'],
        'V08': ['accepted.TaskId', 'lifecycle callback identity', 'caller idempotency key as Gateway MessageId', 'canonical uppercase ULIDs', 'fresh per-call MessageId', 'caller-only IdempotencyKey', 'lifecycle handle lookup', 'audit association', 'replay/conflict'],
        'V09': ['extensions["taskId"]', 'UserId', 'payload', 'envelope-only', 'actorProperty', 'Queries have no generic extension bag'],
        'V10': ['No stream reader', 'file upload/download/content export', 'search', 'erasure', 'key-rotation', 'remain defer/exclude', 'Eventually_consistent'],
        'V11': ['HEXALITH_PROJECTS_BASE_ADDRESS', 'stderr', 'stdout', '0/2/3/4/5/10'],
        'V12': ['repeated', 'last single value wins', 'arrays'],
    },
    'frontcomposer': {
        'V01': ['canonical ULID', 'bounded in-memory', 'current-tool admission', 'no originating tenant/user binding', 'originating ownership proof', 'not a registered event stream', 'acceptance is not effect confirmation'],
        'V02': ['authorization', 'tenant', 'Development', 'forwarded per-user HTTP identity'],
        'V03': ['X-FrontComposer-Mcp-Key', 'without claims fallback', 'valid key takes precedence', 'claimsSource: null', 'tenant/user only', 'preserves source roles/claims', 'not equivalent authenticated authority', 'No erasure/key-rotation operation', 'configuration, not a rotation tool', 'Dynamic manifest', 'remain defer/exclude'],
        'V04': ['hidden', 'server fields injected', 'sanitized', 'deny-before-dispatch'],
        'V05': ['schema fingerprints', 'bound take/rows/cells/Markdown', 'lowercase SHA-256', 'Corpus docs bypass'],
        'V06': ['optional build', 'text default or JSON', 'information'],
        'V07': ['dry-run/apply', '9.1.0 to 9.2.0', 'submodule paths', 'canonical targets', 'source hashes', 'sequential writes', 'Earlier writes remain', 'failure/cancellation', 'applied:false'],
        'V08': ['no-arg/help/--help/-h', '0–4', '.slnx', '--name=value', 'reject repeated named options', 'presence', '--apply=false selects apply', 'future compatibility decision'],
    },
}
for module, terms in variant_terms.items():
    inventory = p if module == 'projects' else f
    for key, required in terms.items():
        body = ' | '.join(inventory[key])
        assert all(term in body for term in required), (module,key)
assert 'Manifest-defined command tool family' in f['H02'][1]
assert 'Manifest-defined projection resource family' in f['H03'][1]
assert 'M01–M05' in f['H02'][4] and 'R01–R11' in f['H03'][4]
assert 'undecorated' in documents['projects'] and 'Projects remains post-v1' in documents['projects']
assert 'strict unknown-payload rejection' in documents['projects']
assert all('unresolved' in text and 'nondeletable' in text for text in documents.values())
assert all('Post-approval prerequisite clarifications' in text and 'change no approved disposition, coverage, authority or source' in text for text in documents.values())
assert 'identity/name/lifecycle' in p['R03'][4] and 'reference/audit counts' in p['R03'][4]
assert 'Detailed task/correlation/audit/reason entries belong to R06' in p['R03'][4]
assert 'originating ownership unproven' in f['H01'][5] and 'Identity-bound' not in f['H01'][5]

projects = root / 'references/Hexalith.Projects'
front = root / 'references/Hexalith.FrontComposer'

def check_review_sources(projects, front, documents):
    reader = (projects / 'src/Hexalith.Projects.Mcp/ProjectsMcpResourceReader.cs').read_text()
    settings = (front / 'src/Hexalith.FrontComposer.Mcp/FrontComposerMcpOptions.cs').read_text()
    host_reader = (front / 'src/Hexalith.FrontComposer.Mcp/Invocation/FrontComposerMcpProjectionReader.cs').read_text()
    assert re.search(r'DefaultResourceTake \{ get; set; \} = 50;',settings)
    assert re.search(r'MaxResourceTake \{ get; set; \} = 200;',settings)
    assert 'Math.Max(1, Math.Min(options.Value.DefaultResourceTake, options.Value.MaxResourceTake))' in host_reader
    assert 'new ProjectionQuery(snapshot.Descriptor.ProjectionTypeName, Take: take)' in host_reader
    assert 'ReadInventoryAsync(request.Criteria.Take, cancellationToken)' in reader
    assert 'LimitWarningRows(scan, request.Criteria.Take)' in reader
    for name,value in [('DefaultAuditLimit',25),('MaxAuditLimit',100),('MaxRows',100)]:
        assert re.search(rf'const int {name} = {value};',reader)
    assert 'ReadAuditTimelineAsync(null, DefaultAuditLimit, cancellationToken)' in reader
    assert 'Math.Max(1, Math.Min(requested.GetValueOrDefault(DefaultAuditLimit), maximum))' in reader
    assert '.Take(Bound(auditLimit, MaxAuditLimit))' in reader
    assert '.Take(Bound(take, MaxRows))' in reader

    # Pin exact emitted fields and literal discriminators, independently matching
    # the processor's strict private callback DTOs. Public Contracts are not ready.
    submitter = (projects / 'src/Hexalith.Projects.Server/EventStoreProjectCommandSubmitter.cs').read_text()
    processor = (projects / 'src/Hexalith.Projects.Server/ProjectsDomainProcessor.cs').read_text()
    assert 'UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow' in processor
    fields = {
        'ArchiveProject': ['archiveIntent','requestSchemaVersion'],
        'RestoreProject': ['requestSchemaVersion','restoreIntent'],
        'SetProjectFolder': ['requestSchemaVersion','operation','projectId','folderId','folderMetadata','replacementConfirmed'],
        'LinkFileReference': ['requestSchemaVersion','operation','projectId','fileReferenceId','folderId','fileMetadata'],
        'UnlinkFileReference': ['requestSchemaVersion','operation','unlinkIntent','projectId','fileReferenceId'],
        'LinkMemory': ['requestSchemaVersion','operation','projectId','memoryReferenceId','memoryMetadata'],
        'UnlinkMemory': ['requestSchemaVersion','operation','unlinkIntent','projectId','memoryReferenceId'],
    }
    section = documents['projects'].split('Existing strict wire evidence',1)[1].split('\n| ID |',1)[0]
    assert 'every one carries `requestSchemaVersion = "v1"`' in section
    assert 'no transient workspace/path fields' in section and 'not callback payload members' in section
    for command, expected in fields.items():
        body = re.search(rf'\bSubmit{command}Async\(.*?object payload = new\s*\{{(.*?)\}};',submitter,re.S)[1]
        emitted = dict(re.findall(r'^\s*(\w+) = (.+?),\s*$',body,re.M))
        assert list(emitted) == expected, command
        dto = re.search(rf'private sealed record {command}Payload\((.*?)\);',processor,re.S)[1]
        accepted = [name[0].lower()+name[1:] for name in re.findall(r'(\w+)\s*(?:,|\Z)',dto)]
        assert accepted == expected, command
        recorded = re.search(rf'^- `{command}`:(.*?)(?=^- `|\Z)',section,re.S|re.M)[1]
        for field, expression in emitted.items():
            literal = {'requestSchemaVersion':'"v1"','archiveIntent':'"archive"','restoreIntent':'"restore"',
                       'operation':'"set"' if command == 'SetProjectFolder' else '"unlink"' if command.startswith('Unlink') else '"link"',
                       'unlinkIntent':'"removeReference"'}.get(field)
            if literal is not None:
                assert expression == literal, (command,field)
                if field != 'requestSchemaVersion':
                    assert f'`{field} = {literal}`' in recorded, (command,field)
            else:
                member = field[0].upper()+field[1:]
                assert expression == f'command.{member}' + ('.Value' if field == 'projectId' else ''), (command,field)
                assert f'`{field}`' in recorded, (command,field)

check_review_sources(projects, front, documents)
descriptor = (projects / 'src/Hexalith.Projects.Mcp/ProjectsMcpDescriptors.cs').read_text()
resource_block = descriptor.split('ResourceNames =', 1)[1].split('];', 1)[0]
resources = re.findall(r'"(projects\.[^"]+)"', resource_block)
assert len(resources) == len(set(resources)) == 11
assert resources == [p[f'R{i:02d}'][1].strip('`') for i in range(1,12)]
assert set(resources) == set(re.findall(r'Resource\("([^"]+)"', descriptor))
actions = re.findall(r'ProjectMaintenanceActions\.(\w+)', descriptor.split('MaintenanceActionNames =',1)[1].split('];',1)[0])
constants = (projects / 'src/Hexalith.Projects.Contracts/Ui/ProjectMaintenanceActionProjection.cs').read_text().split('public static class ProjectMaintenanceActions',1)[1]
tools = ['projects.' + re.search(rf'const string {name} = "([^"]+)"',constants)[1] for name in actions]
assert len(tools) == len(set(tools)) == 5
assert tools == [p[f'M{i:02d}'][1].strip('`') for i in range(1,6)]
assert 'ProtocolName: $"projects.{action}"' in descriptor
assert 'ProtocolUri: $"frontcomposer://Projects/projections/{name}"' in descriptor

parser = (projects / 'src/Hexalith.Projects.Cli/ProjectsCliParser.cs').read_text()
spellings = []
for name in ['ReadCommands', 'MutationCommands']:
    spellings += re.findall(r'"([^"]+)"', parser.split(name+' =',1)[1].split('};',1)[0])
assert 'command = "diagnostic export"' in parser
spellings.append('diagnostic export')
assert len(spellings) == len(set(spellings)) == 18
assert set(spellings) == {p[f'L{i:02d}'][1].strip('`') for i in range(1,19)}
expected_associations = ['R01','R02','R02, L02','V02','L04','R04','L06','R06',
                         'R08, R09','R10','R07','V04','V04','M01','M02','M03','M04','M05']
def check_associations(candidate):
    assert [candidate[f'L{i:02d}'][2] for i in range(1,19)] == expected_associations
check_associations(p)
assert '"trace-resolution" => "trace"' in parser
assert '"validate-references" => "validate"' in parser
contracts = '\n'.join(path.read_text() for path in (projects / 'src/Hexalith.Projects.Contracts').rglob('*.cs') if not {'obj','bin'} & set(path.parts))
assert not re.search(r'\[\s*(?:assembly:\s*)?Hexalith(?:Module|Command|Query)(?:Attribute)?\s*\(', contracts)

options = (front / 'src/Hexalith.FrontComposer.Mcp/FrontComposerMcpOptions.cs').read_text()
tool_name = re.search(r'LifecycleToolName.*?= "([^"]+)"',options)[1]
assert f['H01'][1].strip('`') == tool_name
registrar = (front / 'src/Hexalith.FrontComposer.Mcp/FrontComposerMcpServerOptionsConfigurator.cs').read_text()
assert 'foreach (McpResourceDescriptor descriptor in registry.Resources)' in registrar
assert 'skillProvider.CreateMcpResources()' in registrar
assert 'LifecycleUriPrefix' not in registrar
corpus = front / 'docs/skills/frontcomposer'
metadata = []
for path in sorted(corpus.rglob('*.md')):
    assert path.name != 'SKILL.md', 'Agent skills must not be inspected'
    content = path.read_text()
    doc_id = re.search(r'^id: (.+)$', content, re.M)[1].strip().strip('"\'')
    uri = re.search(r'^resourceUri: (.+)$', content, re.M)[1].strip().strip('"\'')
    assert uri.startswith('frontcomposer://skills/')
    metadata.append((doc_id,uri.removeprefix('frontcomposer://skills/')))
assert len(metadata) == len(set(metadata)) == 12
assert set(metadata) == {(f[f'D{i:02d}'][1].strip('`'),f[f'D{i:02d}'][2].strip('`')) for i in range(1,13)}
builder = (front / 'src/Hexalith.FrontComposer.Mcp/Skills/SkillCorpusAggregateManifestBuilder.cs').read_text()
provider = (front / 'src/Hexalith.FrontComposer.Mcp/Skills/FrontComposerSkillResourceProvider.cs').read_text()
assert 'frontcomposer://skills/manifest' in builder and '"skills-manifest"' in provider
assert [c.strip('`') for c in f['D13'][1:3]] == ['skills-manifest','manifest']
cli = (front / 'src/Hexalith.FrontComposer.Cli/CliApplication.cs').read_text()
assert set(re.findall(r'"(\w+)" => await \w+Command.RunAsync',cli)) == {f['C01'][1].strip('`'),f['C02'][1].strip('`')}

# Resolve every explicit path:line anchor. Shorthand :line continuations are
# contextual prose; this checks each independently named source location.
for module, text in documents.items():
    repo = pins[module][0]
    prefixes = {'Mcp':f'src/{repo}.Mcp', 'Cli':f'src/{repo}.Cli',
                'Contracts':f'src/{repo}.Contracts', 'Server':f'src/{repo}.Server',
                'Corpus':'docs/skills/frontcomposer'}
    for anchor in re.findall(r'`((?:Mcp|Cli|Contracts|Server|Corpus|src)/[^`\n]+:\d+)`',text):
        path, number = anchor.rsplit(':',1)
        if path.startswith('src/Hexalith.McpCli.'):
            location = root / path
        else:
            first, rest = path.split('/',1)
            location = root / 'references' / repo / (prefixes.get(first,first)+'/'+rest)
        lines = location.read_text().splitlines()
        assert 1 <= int(number) <= len(lines) and lines[int(number)-1].strip(), anchor
    for target in re.findall(r'\]\(([^)]+)\)',text):
        path, _, fragment = target.partition('#')
        location = base / path if path else base / f'{module}-migration-inventory-v1.md'
        assert location.exists(), target
        if fragment:
            headings = re.findall(r'^#{1,6} (.+)$',location.read_text(),re.M)
            anchors = {re.sub(r'[^\w -]','',heading.lower()).replace(' ','-') for heading in headings}
            assert fragment in anchors, target

# Preserve the old snapshot byte-for-byte beneath its successor notice.
draft = base / 'projects-migration-inventory-draft.md'
baseline = re.search(r"^baseline_commit: '([^']+)'$",spec,re.M)[1]
historical = subprocess.check_output(['git','show',baseline+':'+str(draft.relative_to(root))])
assert draft.read_bytes().endswith(historical)
assert b'Historical, unapproved snapshot' in draft.read_bytes()
assert b'(projects-migration-inventory-v1.md)' in draft.read_bytes()
assert b'(frontcomposer-migration-inventory-v1.md)' in draft.read_bytes()

# Check that duplicate/missing rows and a wrong ordinary CLI association fail.
for damaged in [documents['projects'].replace('\n| R01 |', '\n| R02 |',1),
                '\n'.join(line for line in documents['projects'].splitlines() if not line.startswith('| R01 |'))]:
    try:
        candidate = rows(damaged,dict(R=8,M=8,L=8,V=6,G=4))
        assert Counter(k[0] for k in candidate) == dict(R=11,M=5,L=18,V=12,G=6)
    except AssertionError:
        pass
    else:
        raise AssertionError('Malformed inventory was accepted')
swapped = documents['projects'].replace('| `list` | R01 |', '| `list` | R02 |').replace('| `describe` | R02 |', '| `describe` | R01 |')
try:
    check_associations(rows(swapped,dict(R=8,M=8,L=8,V=6,G=4)))
except AssertionError:
    pass
else:
    raise AssertionError('Wrong CLI association was accepted')
for module, damaged in [
    ('projects', documents['projects'].replace('approval_status: session-approved','approval_status: pending')),
    ('frontcomposer', documents['frontcomposer'].replace('external_maintainer_approval: unasserted','external_maintainer_approval: approved')),
]:
    try:
        check_approval(module, damaged)
    except AssertionError:
        pass
    else:
        raise AssertionError('Invalid approval state was accepted: '+module)
for module, (repo, sha) in pins.items():
    assert subprocess.check_output(['git','-C',str(root/'references'/repo),'rev-parse','HEAD'],text=True).strip() == sha
    assert not subprocess.check_output(['git','-C',str(root/'references'/repo),'status','--porcelain'],text=True).strip()
print('PASS: exact pins, clean sources, 34 Projects surfaces, 2 host families, lifecycle, 13 documents, 2 compiler leaves, 20 variants, all 82 A1 row references, source anchors and preserved historical body.')
print('PASS: rejected duplicate/missing rows, swapped CLI associations, pending approval and invented external approval. Session scope only; external owner, Gateway and retirement gates remain open.')
print(f'Workflow states: spec={spec_status}; sprint={sprint_status}. Static checks do not complete workflow review.')
PY
git diff --check
```

## Recorded execution and limits

- **Candidate checkpoint (2026-10-16):** the previous candidate checker passed
  with exit 0, rejecting duplicate/missing rows and swapped CLI associations.
  At that checkpoint approval was pending and the spec measured 1,218 tokens
  under `o200k_base`. That historical result supplied no approval. The user
  subsequently answered "approve" to the all-deferred recommendation; the
  approved frozen decision and Implementation Notes in the source spec record
  the limited authority actually given.
- **Finalization scope:** inventory 1.0.0 records A1 session approval on all
  82 rows. All concrete surfaces, dynamic host families and 20 compatibility
  variants remain deferred/excluded; ten prerequisite rows remain unresolved.
  The historical September Projects body is preserved byte-for-byte beneath
  its successor notice. There is no runtime, dependency, upstream, enrollment,
  publication or retention change. No .NET build applies to these local
  Markdown/YAML artifacts.
- **Evidence still absent:** external owning-maintainer sign-off, slim published
  Contracts and exact restored closure, Catalog matching, Gateway readiness,
  strict wire/replay proof, authenticated tenant/task/actor authorization,
  redaction/paging/freshness behavior, live persisted effects, release and shared
  host/plug-in retirement gates remain open. Static source checks cannot
  substitute for these prerequisites or authorize loss of an existing capability.
- Git emits the existing `warning: unable to find all commit-graph files`;
  actual command exit codes determine validation success.

**Implementation verification (2026-10-16):** the entire documented Bash block
was executed through Python `subprocess.run(['bash','-e'], input=block,
text=True)` and exited 0. The source pins and clean working trees were checked
before and after the inventory checks. The block also ran `git diff --check`,
which exited 0. The result was:

```text
PASS: exact pins, clean sources, 34 Projects surfaces, 2 host families, lifecycle, 13 documents, 2 compiler leaves, 20 variants, all 82 A1 row references, source anchors and preserved historical body.
PASS: rejected duplicate/missing rows, swapped CLI associations, pending approval and invented external approval. Session scope only; external owner, Gateway and retirement gates remain open.
Workflow states: spec=in-progress; sprint=in-progress. Static checks do not complete workflow review.
```

At the implementation checkpoint, required workflow review and final spec/sprint
synchronization remained with the parent build session. Parent completion is
recorded below. No future readiness or retirement gate is closed by this result.

Review follow-up (2026-10-16): both A1 sections label the corrections as
post-approval prerequisite clarifications, with no disposition, coverage,
authority or source-pin change. The checker now directly reads effective
FrontComposer take settings, Projects dispatch/helper bounds and all seven
existing maintenance wire payloads, matching their exact fields against the
strict processor DTOs. Variant guards cover lifecycle ownership limits,
task/message identities, key/claims authority, partial apply, CLI parsing and
unsupported erasure/key rotation; R03 remains a diagnostic summary.

Focused validation compiled the documented Python block and executed only its
row/variant/approval checks, `check_review_sources`, and local/source anchor
checks: exit 0. The emitted/accepted file-link shape contains no transient
workspace/path fields. The full documented block and final workflow transition
remain parent-session checks. No .NET suite or migration tooling was executed.

## Parent completion (2026-10-16)

All three required review layers completed. Edge-case review found no issue;
verification-gap review found no gap in this story's checks. The nine verified
blind-hunter corrections were applied with no change to the approved deferred
scope. The separate, pre-existing Builds/dependency-policy mismatch is tracked
under this spec in `../../deferred-work.md:478`; no dependency or restore gate
is claimed to have passed here.

The parent executed the **entire revised Bash block** after the corrections,
then again with the final spec/sprint states `done` / `review`: exit 0. It
confirmed all 82 A1 rows, unchanged clean upstream source pins, effective
host/helper defaults, seven strict emitted/accepted wire shapes, local/source
references, historical-body preservation and rejection of the documented
invalid cases. `git diff --check` passed. The approved frozen block's SHA-256
remains `627de046e93b439723d754f102bb1beba61773c0584b472f05f35acc836c8eca`.
This completes the approved session scope and build workflow; external owner,
Gateway, package, authorization, behavior, release and retirement gates remain
open. The sprint remains `review` for the separate story review transition.

The exact local commit message was validated after successful `npm ci`, using
the owning repository's pinned `@commitlint/cli` 21.2.2:

```text
Command: npx --no -- commitlint --verbose
Input: docs(migration): finalize story 4.3 inventories
✔   found 0 problems, 0 warnings
Exit: 0
```

The full message and successful validator output were also preserved in
`/tmp/mcpcli-story-4-3-message-rxv68s1h.txt` and its `.validation.log` sibling
before committing. Only this story's seven local Markdown/YAML artifacts are
included in the local commit; earlier reference gitlink updates in the complete
baseline diff were already committed by the separate sync operation.
