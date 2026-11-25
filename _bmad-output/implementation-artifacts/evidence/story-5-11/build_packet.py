#!/usr/bin/env python3
"""Prepare documentary candidates only; never edits an owner checkout or authorizes delivery."""
from pathlib import Path
import difflib
import hashlib
import json
import re
import subprocess
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[4]/'scripts'))
from evidence_redaction import sanitized_xml

ROOT = Path(__file__).resolve().parents[4]
A = Path('_bmad-output/implementation-artifacts')
E = A/'evidence/story-5-11'
AD = Path('_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22')
SPEC = A/'spec-5-11-reconcile-product-claims-and-the-migration-plan.md'
BASELINE = '008d95ccc77d932a372cb6c749d9d1fb1bc1ea57'
SUCCESSORS = {'eventstore-admin': ('1.0.2', '1.0.3'), 'technical-tools': ('1.0.3', '1.0.4')}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def serialized(data):
    return (json.dumps(data, indent=2, ensure_ascii=False)+'\n').encode()


def git(repo, *args):
    result = subprocess.run(['git', '-C', str(repo), *args], capture_output=True)
    if result.returncode:
        raise ValueError('git '+ ' '.join(args)+': '+result.stderr.decode().strip())
    return result.stdout


def rows(text):
    result = {}
    headers = []
    for line in text.splitlines():
        if not line.startswith('|'): continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        if cells[0] == 'ID': headers = cells
        elif re.fullmatch(r'[A-Z]+\d+', cells[0]):
            if cells[0] in result: raise ValueError('duplicate inventory row '+cells[0])
            if len(cells) != len(headers): raise ValueError('malformed row '+cells[0])
            result[cells[0]] = dict(zip(headers, cells))
    return result


def successor(module):
    old, new = SUCCESSORS[module]
    source = A/f'{module}-migration-inventory-v{old}.md'
    text = (ROOT/source).read_text()
    text = text.replace(f"inventory_version: '{old}'", f"inventory_version: '{new}'")
    text = text.replace('status: pending\n', 'status: receipt-based\n', 1)
    text = text.replace('approval_status: pending', 'approval_status: receipt-based')
    text = text.replace("approval_ref: '#a2-amendment-approval-pending'", "approval_ref: 'evidence/story-5-11/approval.json'")
    text = text.replace('approval_authority: pending-exact-byte-owner-approval', 'approval_authority: receipt-based-exact-byte-owner-roles')
    text = text.replace('external_maintainer_approval: pending', 'external_maintainer_approval: receipt-based')
    text = re.sub(r'^predecessor:.*$', "predecessor: '"+str(source)+"'", text, flags=re.M)
    text = re.sub(r'^source_spec:.*$', "source_spec: '"+str(SPEC)+"'", text, flags=re.M)
    text = text.replace(f'# {module} migration inventory {old}', f'# {module} migration inventory {new}')
    start = text.index('Candidate amendment **')
    end = text.index('\n## Disposition and retained gates', start)
    text = text[:start]+f'''Receipt-based documentary successor **{new}**. Its effective status is the
`decision` in [its own approval receipt](evidence/story-5-11/approval.json),
which binds these exact bytes and explicitly covered roles. `pending` means a
candidate; only `approved` establishes the recorded amendment authority. Git
delivery and retirement require their separate evidence and authorization.

## A2 Receipt-based amendment authority

The immutable [{old} predecessor]({source.name}) was approved separately by
[Story 5.7's owner receipt](evidence/story-5-7/approval.json), despite its frozen
pending self-description. That earlier approval is not fresh approval of this
successor. All predecessor rows, source pins, safety fields, dispositions and
owners are preserved; only approval pointers and current companion citations
are reconciled. Accounting records are not operations. Historical gap prose
retains its historical meaning; amendment outcomes govern current disposition.
Neither head is retired. No execution, enrollment, parity, publication or
retirement authority follows from this documentary candidate.
''' + text[end:]
    text = text.replace('[A2](#a2-amendment-approval-pending)', '[A2](#a2-receipt-based-amendment-authority)')
    text = text.replace("PS14's four\nmodes still need Story 5.10's detailed inventory and independent safety evidence.", "PS14's four\nmodes are recorded in the delivered Memories 1.1.0 T01–T04 inventory. Its\nindependent safety gates remain open.")
    if module == 'technical-tools':
        # Keep the original pin/drift attributed to its own version. The separate
        # current citation uses the successor's declared source revision.
        families = ['eventstore-admin', 'eventstore-admin', 'frontcomposer',
                    'frontcomposer', 'parties', 'memories', 'memories', 'projects',
                    'projects', 'folders', 'folders', 'chatbot', 'chatbot', 'memories']
        lines = []
        for line in text.splitlines(keepends=True):
            match = re.match(r'\| PS(\d+) ', line)
            if match:
                family = families[int(match[1])-1]
                version, path, _ = HISTORIES[family][-1]
                # The Admin amendment changes no source pin.
                pin_path = HISTORIES[family][-2][1] if family == 'eventstore-admin' else path
                pin = re.search(r"^source_revision: '([0-9a-f]{40})'$",
                                (ROOT/A/pin_path).read_text(), re.M)[1]
                title = 'EventStore Admin' if family == 'eventstore-admin' else {
                    'frontcomposer':'FrontComposer', 'chatbot':'ChatBot'}.get(family, family.title())
                current = f'Current: [{title} inventory {version}]({path}), source `{pin}`'
                cells = line.split('|')
                original = cells[6].strip()
                if family == 'parties':
                    original = original.replace('(parties-migration-inventory-v1.md)',
                                                '('+HISTORIES['parties'][0][1]+')')
                if match[1] == '14':
                    current += ', T01–T04 account for all four modes'
                cells[6] = f' {current}. Historical census observation: {original} '
                line = '|'.join(cells).replace('Admin 1.0.2 G1–G6:', 'Admin 1.0.3 G1–G6:')
            lines.append(line)
        text = ''.join(lines)
        text += '''\n## Current companion authority and delivery\n\n+The PS rows retain the historical census source pins and drift observations;
each current inventory citation separately identifies its declared source revision.
Parties 1.2.0, Folders 1.1.0, Projects 2.1.0, FrontComposer 1.1.0, ChatBot 1.1.0
and Memories 1.1.0 have their separate owner receipts indexed in Story 5.11
inputs.json. Admin 1.0.3 and this 1.0.4 use their own receipt-based status.
Story 5.10 separately records ChatBot and Memories label delivery. Folders K12,
Projects Payload paging versus AD-20, Parties G01–G06 and its distinct exposure
conflict remain blocking, with their existing owners and successor gates.
'''.replace('\n+', '\n')
    return text.encode()


HISTORIES = {
    'parties': [('1.0.0', 'evidence/story-5-3/approval/1.0.0/parties-migration-inventory-v1.md', None),
                ('1.1.0', 'evidence/story-5-3/approval/1.1.0/parties-migration-inventory-v1.md', 'evidence/story-5-3/approval/1.1.0/approval.json'),
                ('1.2.0', 'parties-migration-inventory-v1.md', 'evidence/story-5-3/approval/amendment-1.2.0.json')],
    'eventstore-admin': [('1.0.0', 'evidence/story-5-1/approval/1.0.0/eventstore-admin-migration-inventory-v1.md', 'evidence/story-5-1/approval/approval.json'),
                         ('1.0.1', 'eventstore-admin-migration-inventory-v1.md', 'evidence/story-5-1/approval/approval.json'),
                         ('1.0.2', 'eventstore-admin-migration-inventory-v1.0.2.md', 'evidence/story-5-7/approval.json'),
                         ('1.0.3', 'eventstore-admin-migration-inventory-v1.0.3.md', 'evidence/story-5-11/approval.json')],
    'technical-tools': [('1.0.0', 'evidence/story-5-1/approval/1.0.0/technical-tools-migration-inventory-v1.md', 'evidence/story-5-1/approval/approval.json'),
                        ('1.0.1', 'evidence/story-5-1/approval/1.0.1/technical-tools-migration-inventory-v1.md', 'evidence/story-5-1/approval/approval.json'),
                        ('1.0.2', 'technical-tools-migration-inventory-v1.md', 'evidence/story-5-1/approval/approval.json'),
                        ('1.0.3', 'technical-tools-migration-inventory-v1.0.3.md', 'evidence/story-5-7/approval.json'),
                        ('1.0.4', 'technical-tools-migration-inventory-v1.0.4.md', 'evidence/story-5-11/approval.json')],
    'folders': [('1.0.0','folders-migration-inventory-v1.md', None), ('1.1.0','folders-migration-inventory-v1.1.0.md','evidence/story-5-8/approval.json')],
    'projects': [('1.0.0','projects-migration-inventory-v1.md', None), ('2.0.0','projects-migration-inventory-v2.md', None), ('2.1.0','projects-migration-inventory-v2.1.0.md','evidence/story-5-9/approval.json')],
    'frontcomposer': [('1.0.0','frontcomposer-migration-inventory-v1.md', None), ('1.1.0','frontcomposer-migration-inventory-v1.1.0.md','evidence/story-5-9/approval.json')],
    'chatbot': [('1.0.0','chatbot-migration-inventory-v1.md', None), ('1.1.0','chatbot-migration-inventory-v1.1.0.md','evidence/story-5-10/approval.json')],
    'memories': [('1.0.0','memories-migration-inventory-v1.md', None), ('1.1.0','memories-migration-inventory-v1.1.0.md','evidence/story-5-10/approval.json')],
}

PATHS = {
    'eventstore': ['architecture.md','prd.md','ux-designs/ux-eventstore-2026-07-05/EXPERIENCE.md'],
    'frontcomposer': ['prd.md','architecture.md','architecture/architecture-gov-1-2026-07-19/ARCHITECTURE-SPINE.md','ux-designs/ux-frontcomposer-2026-09-09/EXPERIENCE.md'],
    'memories': ['prd.md','architecture.md','architecture/architecture-memories-2026-09-09/ARCHITECTURE-SPINE.md','ux-designs/ux-memories-2026-09-12/EXPERIENCE.md'],
    'chatbot': ['architecture.md','architecture/architecture-chatbot-2026-09-14/ARCHITECTURE-SPINE.md','prds/prd-Hexalith.ChatBot-2026-05-28/prd.md','ux-designs/ux-Hexalith.ChatBot-2026-05-28/EXPERIENCE.md'],
    'folders': ['prd.md','architecture.md'],
    'projects': ['epics.md','prds/prd-Hexalith.Projects-2026-05-24/prd.md','architecture/architecture-projects-2026-07-15/ARCHITECTURE-SPINE.md'],
    'tenants': ['architecture.md'],
    'parties': [],
}
NOTES = {
    'eventstore': 'Remote Admin A1–A4 are confidential-UI-only under adopted AD-23; local Admin A5–A8 are withdrawn from the public migration target. No generic Admin contract or transport is required or admitted. EventStore and platform/operator maintainers retain Admin G1–G6, G4 route/scope, token/URL safety fixes, human authorization, bounded behavior, audit and persisted-effect proof before removal.',
    'frontcomposer': 'Generated command tools, projection/skill resources and lifecycle subscriptions below are historical migration sources. Eligible business data requires an owner-decorated Gateway Query; K07 documentation and K08 synthetic lifecycle are withdrawn. The K13 inspect/migrate compiler is retained local tooling under merged AI.Tools plan 1.2.0, never retired or migrated to generic diagnostics. FK01–FK04 and G4 still couple host and Projects plug-in retirement.',
    'memories': 'The proprietary CLI/MCP phases, ingress topology and installation commands below describe retained compatibility. There is no promised generic migration or diagnostics surface. No Memories operation is enrolled in the current shipped McpCli cohort. Forwarded per-user HTTP authority is necessary but insufficient for retirement; tenant/user/administrative authorization, semantics, release and rollback evidence remain. PS14 stays owner-held local tooling in all four modes, never counted retired.',
    'chatbot': 'The module CLI and stdio MCP adapter are retained compatibility sources. ChatBot has no operation enrolled in the current shipped McpCli cohort. Eligible reads/proposals need decorated Contracts, handler/admission and enrollment proof first. Association decisions, AI-action approval, execution and confirmation-required behavior stay on confidential UI; human-delegated MCP, presence, actorType or confirm claims never grant public-agent authority.',
    'folders': 'C13 remains the adopted four-surface accounting denominator, not evidence that every operation is public-agent eligible. The separate owner-approved K12 successor must resolve restricted and mixed operation classifications and C13 cells before any enrollment or retirement claim; existing 1.1.0 approval does not waive it. Current shipped McpCli has no Folders enrollment. Legacy adapters below remain retained compatibility; no resource/stream fallback is admitted.',
    'projects': 'Current McpCli source enrolls published Projects.Contracts 2.0.0 and discovers four reads: projects.list, projects.describe, projects.trace-conversation and projects.trace-attachments. The published McpCli 2.0.1 tool predates Projects enrollment. Independent Gateway authorization, native live qualification and release evidence remain required. Readiness/setup/task-control and audit operations must not be inferred from those reads. Preserve 6.7 cutover, K12 confidential UI and Payload paging versus AD-20 gates. Tenant selection is envelope-owned; actor attribution and independent Gateway authorization remain separate.',
    'tenants': 'The FrontComposer inspect/migrate compiler is retained K13 local tooling under merged AI.Tools plan 1.2.0. It requires no generic McpCli migration/diagnostic transport and is never counted retired.',
    'parties': 'The five-tool parties-mcp host is retained compatibility. Current McpCli source enrolls published Parties Contracts 4.0.0; the earlier local-candidate descriptions are historical development context. The published McpCli 2.0.1 tool discovers seven Parties operations; source-selected package versions and released tool contents must be assessed separately. Retirement remains blocked by G01–G06 and the separate destructive-classification/exposure conflict, requiring an exact-byte owner successor and both-head direct/chained denial with zero unauthorized effects. This documentation does not change existing exposure or owner tests.',
}


def setup(name):
    return f'''## Shared McpCli access (reconciliation candidate)

{NOTES[name]}

For the verified 2.0.1 examples, install `dotnet tool install --global Hexalith.McpCli --version 2.0.1`.
Run `hexalith modules`, `hexalith operations tenants` or
`hexalith operations parties`, and `hexalith describe tenants.list-tenants`
for offline discovery of the installed cohort. Start the MCP server with
`hexalith mcp --transport stdio`; it offers five generic tools, never a tool or
CLI subcommand per operation. Configure a McpCli profile with the documented
`hexalith config --help` flow before authorized `query` or `send` submission.
Do not copy the Admin `profiles.json`. Offline Catalog discovery proves neither
Gateway authorization, live availability nor retirement. A missing operation
fails safely; confidential human actions hand off to the owning UI, never to
an alternative module endpoint. No Gateway call is needed for this setup check.

'''


def correct(name, text):
    # Correct active claims in place; frozen decisions and completed stories are outside PATHS.
    if name == 'eventstore':
        text = text.replace('and admin operations only through Admin Server over the public AD-21 edge, in both cases', 'while Admin remains confidential UI under adopted McpCli AD-23, always')
        text = text.replace('until an approved generic McpCli administration contract and transport decision preserves those checks', 'through McpCli; confidential UI coverage and independent safety evidence preserve those checks')
        text = text.replace('require an approved generic McpCli administration contract, authorization, and parity evidence before removal', 'require confidential UI coverage, explicit withdrawal and independent authorization, audit and behavior evidence before removal under adopted AD-23')
        text = text.replace('after a generic admin contract and equivalent safety evidence are approved', 'for eligible decorated Gateway operations; Admin requires confidential UI coverage and equivalent safety evidence')
        text = text.replace('McpCli generic administration contract and transport decision (AD-35)', 'Adopted AD-23 confidential UI/withdrawal reconciliation (AD-35)')
        text = text.replace('Approved McpCli contract/inventory/parity before legacy removal', 'Approved inventory, confidential UI coverage and independent authorization/behavior proof before legacy removal')
    if name == 'frontcomposer':
        text = text.replace('**MCP Surface** — the MCP server tools and resources generated', '**Legacy MCP Surface** — retained compatibility tools and resources generated')
        text = text.replace('Ravi hosts the MCP server behind host authentication', 'For the historical compatibility flow, Ravi hosts the MCP server behind host authentication')
        text = text.replace('These resource capabilities require an approved generic `Hexalith.McpCli` representation or owner-approved withdrawal before the legacy host retires', 'Adopted AD-23 withdraws K07 documentation and K08 synthetic lifecycle; eligible business-state reads require decorated Queries and owner evidence before the legacy host retires')
        text = text.replace('`Hexalith.FrontComposer.Cli` is an obsolete compatibility tool.', '`Hexalith.FrontComposer.Cli` is retained K13 local compiler tooling.')
        text = re.sub(r'`inspect` and `migrate` need a generic .*?before the old tool is retired\.', '`inspect` and `migrate` remain local under the merged AI.Tools 1.2.0 exemption, require no generic diagnostics migration and never count as retired.', text)
        text = text.replace('A generic `Hexalith.McpCli` diagnostics contract must preserve approved behavior before the old CLI retires.', 'The retained K13 compiler exemption preserves these local safety obligations; no McpCli transport or retirement is implied.')
        text = text.replace('and `.Mcp`, including inspect/migrate, resources, skill corpus, and lifecycle calls, are obsolete migration sources.', 'is retained K13 local compiler tooling; `.Mcp`, including resources, skill corpus and lifecycle calls, remains a historical migration source.')
        text = text.replace('Their replacement or approved withdrawal needs a generic McpCli contract and owner-approved parity evidence before package removal.', 'AD-23 disposition and independent owner evidence govern MCP package removal; the compiler stays exempt locally.')
        text = text.replace('Each requires an owner-approved generic McpCli replacement or explicit withdrawal before retirement;', 'AD-23 governs MCP replacement or withdrawal, while inspect/migrate stays exempt locally;')
    if name == 'memories':
        text = text.replace('### 5. Install the CLI (~1 min first time, ~10s subsequent)', '### 5. Install the retained compatibility CLI (~1 min first time, ~10s subsequent)')
        text = text.replace('## CLI (preview)', '## Retained compatibility CLI (preview)')
        text = text.replace('`Hexalith.McpCli` generic diagnostic/migration contract for approved `explore` and EventStore diagnostics', 'Owner-decorated Gateway diagnostics only after separate Contracts/handler/admission/enrollment evidence; no promised generic migration surface')
        text = text.replace('The MVP architecture (Phase 1: CLI-only, no MCP, no EventStore integration)', 'The historical compatibility MVP architecture (Phase 1: CLI-only, no MCP, no EventStore integration)')
        text = text.replace('MCP Server and EventStore Integration must be pluggable', 'The retained compatibility MCP Server and EventStore Integration must be pluggable')
        text = text.replace('| CLI | .NET global tool', '| Retained compatibility CLI | .NET global tool')
        text = text.replace('**LLM Agent** → ingress → MCP Server', '**Legacy compatibility LLM Agent** → ingress → MCP Server')
        text = text.replace('**CLI / Third-party apps** → ingress', '**Legacy CLI / Third-party apps** → ingress')
        text = text.replace('# MVP essentials; Phase 1.5 polish expansion', '# Retained compatibility; historical MVP/Phase 1.5')
        text = text.replace('Hexalith.Memories.Mcp/                 # Phase 1.5', 'Hexalith.Memories.Mcp/                 # Retained compatibility; historical Phase 1.5')
    if name == 'chatbot':
        text = text.replace('Epic 5 CLI and MCP surfaces are implemented as thin adapters', 'The retained compatibility Epic 5 CLI and MCP surfaces are implemented as thin adapters')
        text = text.replace('| CLI surface (M1)', '| Retained compatibility CLI surface (M1)')
        text = text.replace('| MCP surface (M1)', '| Retained compatibility MCP surface (M1)')
        text = text.replace('CLI (M1); MCP server (M1,', 'retained compatibility CLI (M1); MCP server (M1,')
        text = text.replace('| Human-delegated MCP Client | Same backend resources as the currently authenticated delegating human | Access the parity set, including human decisions, only while current user presence and `actorType=human` are recorded | Delegation without current human presence; any originating-AI/tool/service self-approval; restricted or cross-tenant access |', '| Human-delegated MCP Client | Public agent surface; no elevation from delegation or presence | Approved eligible read/proposal set only after Gateway authorization | Human decisions, confirmation, approved execution, restricted/admin/outbound mutation and cross-tenant access; hand off to confidential UI |')
        text = text.replace('# [M1] System.CommandLine, wraps Client', '# Retained compatibility: System.CommandLine, wraps Client')
        text = text.replace('# [M1] ModelContextProtocol stdio server, wraps Client', '# Retained compatibility: ModelContextProtocol stdio server, wraps Client')
    if name == 'folders':
        text = text.replace('← CLI adapter wrapping the SDK (REFERENCE: EventStore.Admin.Cli)', '← retained compatibility CLI wrapping SDK; historical reference only')
        text = text.replace('← MCP server wrapping the SDK (REFERENCE: EventStore.Admin.Mcp)', '← retained compatibility MCP wrapping SDK; historical reference only')
        text = text.replace('`Hexalith.Folders.Cli` and `Hexalith.Folders.Mcp` wrap the SDK', 'the retained compatibility `Hexalith.Folders.Cli` and `Hexalith.Folders.Mcp` wrap the SDK')
        text = text.replace('one decorated public Command or Query type per owner-approved inventory candidate', 'one decorated public Command or Query type per separately approved agent-eligible candidate after the K12 successor resolves restricted and mixed rows')
    if name == 'projects':
        text = text.replace('Tenant and actor come from the credential, and the Gateway authorizes the call.', 'Tenant comes from the envelope: exact PlatformScope first, else exact FixedTenant, else canonical public session/per-call tenant under AD-22 override rules. Payload grants no authority. The Gateway independently authorizes credential, scope, actor, surface and operation.')
    if name == 'tenants':
        text = text.replace('is an obsolete compatibility **inspect/migrate** tool; `Hexalith.McpCli` is the target Hexalith-owned CLI after generic migration/diagnostic contracts are approved,', 'is retained K13 local compiler **inspect/migrate** tooling under merged AI.Tools plan 1.2.0; no generic migration/diagnostic transport or retirement is implied,')
    if name == 'parties':
        text = text.replace('# Separate parties-mcp host over the typed client', '# Retained compatibility parties-mcp host over the typed client')
        text = text.replace('### Generic McpCli command declarations (local migration increment)', '### Generic McpCli command declarations (historical local increment; now enrolled)')
        text = text.replace('### Generic McpCli read declarations (local candidate)', '### Generic McpCli read declarations (historical local candidate; now enrolled)')
        text = text.replace('`Hexalith.McpCli.Abstractions` 1.0.0 supplies declaration', 'The historical `Hexalith.McpCli.Abstractions` 1.0.0 supplied declaration')
        text = text.replace('The Contracts candidate declares exactly seven operations:', 'The declaration set contains exactly seven operations:')
        text = text.replace('The complete candidate still requires fresh maintainer approval, exact-source CI,\nand the protected owning release workflow before its published version can be\npinned in Builds and enrolled in McpCli. The existing five-tool MCP host remains\navailable; this declaration work does not authorize retirement.', 'The original local candidate has since been published and enrolled in McpCli;\ncurrent source selects Parties Contracts 4.0.0. The published McpCli 2.0.1 tool\ndiscovers these seven operations. The existing five-tool MCP host remains\nretained compatibility; enrollment does not authorize retirement.')
    return text


def corrected_document(name, file, prepared, label_rows):
    newline = '\r\n' if b'\r\n' in prepared else '\n'
    text = prepared.decode('utf-8-sig').replace('\r\n','\n')
    after = correct(name,text)
    if file == 'README.md':
        for row in label_rows:
            if row['repository'] != name: continue
            # Some registers surface includes packaging prose; use the original line's prefix.
            original = row['label']['text'].split('`',2)[1]
            pattern = r'^- `'+re.escape(original)+r'`.*$'
            after,n = re.subn(pattern,lambda _:row['label']['text'],after,flags=re.M)
            if n != 1: raise ValueError(name+': missing/duplicate README label '+row['id'])
        after += '\n'+setup(name)
    else:
        # An active-topic notice makes retained topology blocks explicitly historical.
        lines = after.splitlines(keepends=True)
        index = next((i+1 for i,line in enumerate(lines) if line.startswith('# ')),0)
        lines[index:index] = ['\n> **Current McpCli disposition (Story 5.11 candidate):** '+NOTES[name]+'\n\n']
        after = ''.join(lines)
    encoding = 'utf-8-sig' if prepared.startswith(b'\xef\xbb\xbf') else 'utf-8'
    return after.replace('\n',newline).encode(encoding)


def scoped_deferrals(text, sanitize=sanitized_xml):
    entries = []
    heading = ''
    lines = text.splitlines()
    for i,line in enumerate(lines):
        if line.startswith('## '): heading = line
        if not line.startswith('- source_spec:'): continue
        end = i+1
        while end < len(lines) and not lines[end].startswith(('- source_spec:','## ')): end += 1
        block = '\n'.join(lines[i:end]).rstrip()
        fields = {}
        key = None
        for item in block.splitlines():
            match = re.match(r'^(?:- |  )([a-z_]+):\s*(.*)$',item)
            if match:
                key = match[1]
                fields[key] = match[2].strip()
            elif key and item.strip():
                fields[key] = (fields[key]+' '+item.strip()).strip()
        fields['source_spec'] = fields.get('source_spec','').strip('`')
        if not ('spec-5-' in fields.get('source_spec','') or fields.get('summary','').startswith('Migration planning artifacts disagree')): continue
        summary = fields['summary']
        owner = fields.get('owner','Unrecorded; proposed McpCli product/architecture owner')
        status = fields.get('status','open; retain the source-spec acceptance gate')
        # A source story is provenance, not an assignment to another story's gate.
        # Preserve each entry's own obligation, recorded disposition and evidence.
        gate = 'Recorded obligation: '+summary+' Owner: '+owner+' Recorded disposition: '+status
        if fields.get('evidence'): gate += ' Recorded gate evidence: '+fields['evidence']
        prepared = any(s in summary for s in ['Migration planning artifacts disagree','Reconcile epics MR1','Older upstream README','bytes still say',"Re-cite Folders 1.1.0","Story 5.10's later ledger"])
        disposition = 'prepared; exact-byte approval and integration pending' if prepared else 'already tracked; unresolved gate retained'
        if status.startswith('resolved'): disposition = 'existing resolution recorded; no fresh acceptance inferred'
        entries.append({'id':sha(summary.encode())[:16],'sourceSpec':fields['source_spec'],'heading':heading,'ledger':str(A/'deferred-work.md')+':'+str(i+1),'entrySha256':sha(block.encode()),'summary':summary,'owner':owner,'gate':gate,'sourceStatus':status,'evidence':fields.get('evidence',''),'disposition':disposition,'ownerDecision':None})
        for field in ['resolution','audit']:
            if fields.get(field):
                entries[-1][field] = sanitize(fields[field])
        for field in ['summary','owner','gate','sourceStatus','evidence']:
            entries[-1][field] = sanitize(entries[-1][field])
    return entries


def deferral_documents():
    entries = scoped_deferrals((ROOT/A/'deferred-work.md').read_text())
    audit = {'schemaVersion':'1.0.0','state':'candidate-awaiting-explicit-owner-decision','entries':entries}
    text = '''# Story 5.11 deferral dispositions

This audit includes the original migration-drift entry and every current ledger
entry whose source spec is Epic 5 (including 5.12). Entries remain under their
original source headings. “Already tracked” points to the existing row and its
owner/gate; it is not closure, waiver or acceptance. No reconfirmation entry was
added. Existing resolved statuses are recorded as historical evidence, not a new
owner acceptance. The Story 5.11 owner must explicitly decide the exact audit
packet; pending approval and integration do not close any unresolved gate.

'''
    for entry in entries:
        text += f"## {entry['id']} — {entry['disposition']}\n\n"
        text += f"- Source: `{entry['sourceSpec']}`; already tracked (`{entry['ledger']}`).\n"
        text += f"- Original heading: {entry['heading'].lstrip('# ')}.\n"
        text += f"- Summary: {entry['summary']}\n- Owner: {entry['owner']}\n- Blocking successor/gate: {entry['gate']}\n"
        text += f"- Source state: {entry['sourceStatus']}\n- Evidence: {entry['evidence']}\n"
        for field in ('resolution','audit'):
            if field in entry:
                text += f"- Recorded {field}: {entry[field]}\n"
        text += "- Decision: pending; no new acceptance claimed.\n\n"
    return {E/'deferral-dispositions.json':serialized(audit), E/'deferral-dispositions.md':text.encode()}


NO_CHANGE = {'platform':'FR15/AD-14 already require eligibility, confidential UI and confirmation denial','agents':'existing correction banner qualifies future shared-head access','conversations':'existing correction banner qualifies future shared-head access','timesheets':'existing correction banner qualifies future shared-head access','works':'existing correction banner qualifies future shared-head access','builds':'exempt developer tooling; CiCd-owned files untouched','commons':'no proprietary product target','polymorphicserializations':'no proprietary product target'}


def inspect_unchanged(repo, name, reason, revision=None):
    if revision is None:
        revision = git(repo,'rev-parse','origin/main').decode().strip()
    paths = git(repo,'ls-tree','-r','--name-only',revision,'README.md','_bmad-output/planning-artifacts').decode().splitlines()
    inspected = []
    for path in paths:
        if path == 'README.md' or path.endswith(('/prd.md','/architecture.md','/ARCHITECTURE-SPINE.md')):
            data = git(repo,'show',revision+':'+path)
            if path == 'README.md' or b'McpCli' in data: inspected.append({'path':path,'sha256':sha(data)})
    return {'name':name,'revision':revision,'inspected':inspected,'reason':reason}


def main():
    existing = ROOT/E/'approval.json'
    if existing.exists() and json.loads(existing.read_text()).get('decision') == 'approved':
        raise ValueError('Approved packet is immutable; prepare an explicitly authorized successor instead')
    writes = deferral_documents()

    def contents(path):
        return writes[path] if path in writes else (ROOT/path).read_bytes()

    def binding(path):
        return {'path':str(path),'sha256':sha(contents(path))}

    for module,(_,version) in SUCCESSORS.items():
        writes[A/f'{module}-migration-inventory-v{version}.md'] = successor(module)
    inventory = {str(A/f'{m}-migration-inventory-v{v}.md'): sha(successor(m)) for m,(_,v) in SUCCESSORS.items()}
    label_rows = {}
    for story in [7,8,9,10]:
        register = json.loads((ROOT/A/f'evidence/story-5-{story}/labels.json').read_text())
        label_rows.update({r['id']:r for r in register['rows']})
    oldtech = sha((ROOT/A/'technical-tools-migration-inventory-v1.0.3.md').read_bytes())
    newtech = inventory[str(A/'technical-tools-migration-inventory-v1.0.4.md')]
    oldadmin = sha((ROOT/A/'eventstore-admin-migration-inventory-v1.0.2.md').read_bytes())
    newadmin = inventory[str(A/'eventstore-admin-migration-inventory-v1.0.3.md')]
    for row in label_rows.values():
        text = row['label']['text'].replace('technical-tools inventory 1.0.3','technical-tools inventory 1.0.4').replace('technical-tools-migration-inventory-v1.0.3.md','technical-tools-migration-inventory-v1.0.4.md').replace(oldtech,newtech)
        text = text.replace('Admin inventory 1.0.2','Admin inventory 1.0.3').replace('eventstore-admin-migration-inventory-v1.0.2.md','eventstore-admin-migration-inventory-v1.0.3.md').replace(oldadmin,newadmin)
        # Do not change removal gates: their existing version wording is historical gate identity.
        row['label']['text'] = text
        row['label']['sha256'] = sha(text.encode())
    owners = []
    for name,paths in PATHS.items():
        owner = ROOT.parent/name
        remote = git(owner,'rev-parse','origin/main').decode().strip()
        owner_head = git(owner,'rev-parse','HEAD').decode().strip()
        base = remote
        files = [('_bmad-output/planning-artifacts/'+p) for p in paths]
        if name != 'tenants': files.insert(0,'README.md')
        packet = E/'upstream'/name
        changed = []
        prerequisites = []
        for file in files:
            before = git(owner,'show',base+':'+file)
            prepared = before
            # Compose the approved but undelivered Story 5.10 README section first.
            if name in {'chatbot','memories'} and file == 'README.md':
                prior = A/f'evidence/story-5-10/upstream/{name}'
                newline = b'\r\n' if b'\r\n' in prepared else b'\n'
                normalized = prepared.replace(b'\r\n',b'\n')
                old = (ROOT/prior/'README.before.section.md').read_bytes().replace(b'\r\n',b'\n')
                new = (ROOT/prior/'README.after.section.md').read_bytes().replace(b'\r\n',b'\n')
                if old in normalized:
                    prepared = normalized.replace(old,new).replace(b'\n',newline)
                    prerequisites.append('Story 5.10 exact README section integration')
                elif new not in normalized:
                    raise ValueError(name+': Story 5.10 README section drift; rebase required')
            payload = corrected_document(name, file, prepared, label_rows.values())
            diff = ''.join(difflib.unified_diff(prepared.decode().splitlines(keepends=True),payload.decode().splitlines(keepends=True),fromfile='a/'+file,tofile='b/'+file))
            patchpath = packet/(Path(file).name.replace('.md','')+'-'+str(len(changed))+'.patch')
            patch_format = 'unified-diff'
            if name == 'eventstore' and file.endswith('/architecture.md'):
                # The shared scanner treats ordinary authentication prose in a diff's
                # immutable removed/context lines as credentials. A literal edit
                # recipe preserves the source bytes without copying those lines.
                edits = [
                    ('and admin operations only through Admin Server over the public AD-21 edge, in both cases','while Admin remains confidential UI under adopted McpCli AD-23, always'),
                    ('until an approved generic McpCli administration contract and transport decision preserves those checks','through McpCli; confidential UI coverage and independent safety evidence preserve those checks'),
                    ('McpCli generic administration contract and transport decision (AD-35)','Adopted AD-23 confidential UI/withdrawal reconciliation (AD-35)'),
                ]
                newline = '\r\n' if b'\r\n' in prepared else '\n'
                text = prepared.decode().replace('\r\n', '\n')
                title = next(line for line in text.splitlines() if line.startswith('# '))+'\n'
                edits.append((title,title+'\n> **Current McpCli disposition (Story 5.11 candidate):** '+NOTES[name]+'\n\n'))
                recipe = []
                applied = prepared.decode()
                for old,new in edits:
                    old,new = old.replace('\n',newline),new.replace('\n',newline)
                    if applied.count(old) != 1: raise ValueError('EventStore literal patch target missing/duplicated')
                    applied = applied.replace(old,new)
                    recipe.append({'old':old,'new':new})
                if applied.encode() != payload: raise ValueError('EventStore literal patch differs from reviewed correction')
                patchpath = Path(str(patchpath)+'.json')
                diff = serialized({'schemaVersion':'1.0.0','path':file,'edits':recipe}).decode()
                patch_format = 'literal-replacements'
            writes[patchpath] = diff.encode()
            changed.append({'path':file,'format':patch_format,'sourceSha256':sha(before),'beforeSha256':sha(prepared),'afterSha256':sha(payload),'patch':binding(patchpath)})
        guidance = []
        for file in ['AGENTS.md','.editorconfig','.gitattributes','Directory.Build.props','package.json','.gitmodules']:
            result = subprocess.run(['git','-C',str(owner),'show',base+':'+file],capture_output=True)
            if not result.returncode: guidance.append({'path':file,'sha256':sha(result.stdout)})
        owners.append({'name':name,'ownerCheckout':'../'+name,'repository':git(owner,'remote','get-url','origin').decode().strip(),'baseRevision':base,'observedOriginMain':remote,'observedOwnerHead':owner_head,'mainVerification':'local refs only; fresh remote verification required before delivery','files':changed,'guidance':guidance,'prerequisites':prerequisites,'integration':None})
    writes[E/'labels.json'] = serialized({'schemaVersion':'1.0.0','state':'candidate','predecessors':[binding(A/f'evidence/story-5-{s}/labels.json') for s in [7,8,9,10]],'inventoryArtifacts':inventory,'rows':list(sorted(label_rows.values(),key=lambda x:x['id'])),'repositories':[o['name'] for o in owners if o['name']!='tenants'],'inventoryRevision':None,'deliveryAuthorization':None})
    history = {}
    for family,chain in HISTORIES.items():
        history[family] = []
        for version,path,receipt in chain:
            item = {'version':version,**binding(A/path),'approval':{'authority':'session-scope-only','receipt':binding(A/path)} if receipt is None else {'authority':'pending' if 'story-5-11' in receipt else 'owning-maintainer-receipt','receipt':{'path':str(A/receipt)} if 'story-5-11' in receipt else binding(A/receipt)}}
            metadata = contents(A/path).decode().split('---',2)[1]
            for field,target in [('source_revision','sourceRevision'),('source_repository','sourceRepository')]:
                match = re.search(r'^'+field+r":\s*['\"]?([^'\"\n]+)",metadata,re.M)
                if not match: raise ValueError(f'{family} {version}: missing {field}')
                item[target] = match.group(1).strip()
            item['effectiveStatus'] = 'scope-approved-only' if receipt is None else 'candidate-pending' if 'story-5-11' in receipt else 'owner-approved'
            history[family].append(item)
    # A reviewable plan candidate cannot invent the not-yet-published inventory revision.
    ai_owner = ROOT.parent/'aitools'
    ai_base = git(ai_owner,'rev-parse','origin/main').decode().strip()
    plan = """---
plan_version: '1.3.0'
inventory_repository: 'https://github.com/Hexalith/Hexalith.McpCli'
inventory_revision: null
status: candidate-not-publishable
---

# Hexalith MCP and CLI migration plan

Version **1.3.0 candidate**, prepared by McpCli Story 5.11. This file is not the
authoritative plan until fresh exact-byte approval, verified Story 5.10 delivery, immutable
inventory publication and authoritative AI.Tools main integration are verified.
`inventory_revision: null` explicitly records the missing publication binding;
replace it with the verified full McpCli commit and render immutable `/blob/<sha>/`
links before approval of final plan bytes. Never publish this candidate as-is.

## Ownership and capability outcomes

McpCli owns one generic CLI and stdio MCP server for agent-eligible decorated
Gateway Commands and Queries. Do not add proprietary module MCP servers,
plug-ins or CLIs. Both heads are one public agent surface. Payload, task, actor,
delegation and confirm claims cannot elevate authority. Unsupported transports
fail safely; confidential human actions hand off to their owning UI.

Adopted AD-23 keeps Admin A1–A4 and module K12 confidential-UI-only, Admin
A5–A8 plus K07 documentation and K08 synthetic lifecycle withdrawn, K09
stream/file and K10 per-user HTTP deferred. Eligible K01–K06 need exact decorated
Contracts, handlers, admission and independent semantic proof. A business status
Query may observe effects; acceptance never establishes completion. These
outcomes need no invented Admin, resource, diagnostic or lifecycle transport.

External Aspire, Dapr and dotnet CLIs and Builds hexalith-module/hexalith-evidence
remain outside module-operation migration. K13 FrontComposer inspect/migrate and
K14 Memories MigrateEmbeddingVectors (--dry-run, --live, --rollback, --abort)
remain the named local exemptions adopted by plan 1.2.0. They stay supported
locally, never agent-facing, never counted retired, and keep their independent
freshness/path/hash/partial-write/privacy and custody/tenant/credential/consent/
no-write dry-run/denial/rollback/abort/audit obligations. No new CLI is exempt.

## Immutable inventory histories

The complete eight-family index below preserves every predecessor. Paths are
inside the McpCli inventory repository; hashes bind the prepared bytes. Final
publication must bind every path and its approval receipt to one full immutable
`inventory_revision`, never a moving branch. Earlier session-scope authority and
later owning-maintainer approval remain distinct. Receipt decisions determine
effective approval; an approved inventory never establishes delivery or retirement.

| Family | Version | McpCli path | SHA-256 | Authority / receipt |
| --- | --- | --- | --- | --- |
"""
    for family,chain in history.items():
        for item in chain:
            plan += f"| {family} | {item['version']} | `{item['path']}` | `{item['sha256']}` | {item['effectiveStatus']}; {item['approval']['authority']}: `{item['approval']['receipt']['path']}` |\n"
    plan += """
## Ongoing change control

A source change that adds, removes or alters an inventoried tool, resource,
CLI operation or behavior variant, or a newly discovered surface, requires a
versioned inventory amendment and its owning-maintainer approval. Safety and
continuity fixes that leave those identities and behaviors unchanged do not.
Publish every change to this plan under a new `plan_version`. Move
`inventory_revision` whenever an indexed inventory is added or re-pinned.
Preserve every approved predecessor and its recorded approval limits.

## Independent delivery and removal gates

All PS01–PS14 remain present; no evidenced retirement is claimed. PS03/PS14 are
retained exemptions. The Admin/technical documentary successors have fresh
receipt-based status; Story 5.7 approval of their predecessors remains factual.
Story 5.10 records separate owner approval and delivery of ChatBot/Memories 1.1.0
and five labels. See its integrated register and the recorded owner commits.
No missing version, role, hash, gate, publication or upstream binding permits a
success claim. Preserve the proprietary-surface census and independent release gates.

Parties retirement remains blocked by G01–G06 and the separate restricted/
destructive classification versus existing exposure conflict. Parties and McpCli
owners must approve the exact successor and both-head exposure/direct/chained
denial evidence with zero unauthorized effects; this plan changes no exposure.
Folders owners retain the K12 restricted/mixed-operation successor and C13 hold.
Projects owners retain Payload paging versus AD-20, publication/live acceptance
and 6.7 cutover gates. FrontComposer host and Projects plug-in retire together
only after FK01–FK04 and every host consumer are accounted for. Memories needs
forwarded per-user HTTP authority plus tenant/user/administrative authorization,
semantic, release and rollback proof. ChatBot retains governed workflow,
approval, identity, authorization and behavior gates; human decisions stay UI.
Admin retains G1–G6, confidential UI coverage and G4 route/scope/token/URL fixes,
audit and persisted-effect evidence. AM01's backup backend remains deferred.

Every operation and variant retains replace, withdraw or defer, rationale,
security class, exact replacement or gap, and explicit owning-role approval.
Include requires replace; exclude requires approved withdraw or defer and never
means deletion. Inventory is migration documentation, never runtime exposure
configuration. Uninventoried decorated Operations and version differences are
reported; duplicate/stale vectors and uncovered Operation Shapes fail. Retire
only after the owner-approved disposition and selected-environment authorization,
behavior, conformance, release and rollback evidence pass independently.

The owner chose “Labels + slip”; SM-3 is pending-not-met with deadline 2027-02-05,
three months after first paired release 2.0.1 on 2026-11-05. Assessment 2026-11-22:
deadline future, no measured miss. Reassess at completion; the product owner
records a reason if no Legacy Server is deleted by the deadline. Every Epic 5
deferral retains its sourced owner/gate; already tracked is never acceptance.

## Integration and release prerequisite

Publish approved inventory bytes first under an explicitly authorized McpCli
commit; verify published bytes and all approval roles. Deliver rebased owner
README/active-topic patches with separate authorization and mandatory owner
commitlint and applicable Builds checks. McpCli has adopted CiCd and its
committed .github/hexalith-ci.json requires the shared pre-push check.
Bind final plan bytes and full inventory revision, integrate into
authoritative AI.Tools main, verify main containment, then change only McpCli's
AI.Tools gitlink and pass byte-identical local instruction synchronization.
Open PRs, local candidates and missing upstream integrations leave completion
blocked. Dependency, census, enrollment, loopback, live, package and post-2.0.1
output-contract publication gates remain independent. No release, binary removal,
operation execution, package publication or ecosystem completion is authorized.
"""
    ai_packet = E/'upstream/ai-tools'
    ai_files = []
    for file in ['hexalith-mcpcli-migration-instructions.md','hexalith-llm-instructions.md']:
        before = git(ai_owner,'show',ai_base+':'+file)
        if file.startswith('hexalith-mcpcli'): after = plan
        else:
            after = before.decode().replace('\r\n','\n')
            after = after.replace('Infrastructure\nadministration, resources, and other non-gateway capabilities need an\napproved generic McpCli contract and transport decision before migration.', 'Adopted McpCli AD-23 assigns confidential UI, explicit withdrawal, named local\nexemptions or deferral to other capability classes. Confidential UI, withdrawal\nand those exemptions need no invented McpCli transport. Eligible business\nbehavior still needs exact decorated Gateway Contracts and independent gates.')
        after_bytes = after.replace('\n','\r\n' if b'\r\n' in before else '\n').encode()
        candidate_path = ai_packet/file
        writes[candidate_path] = after_bytes
        patch_path = ai_packet/(file+'.patch')
        patch = ''.join(difflib.unified_diff(before.decode().splitlines(keepends=True),after_bytes.decode().splitlines(keepends=True),fromfile='a/'+file,tofile='b/'+file))
        writes[patch_path] = patch.encode()
        ai_files.append({'path':file,'sourceSha256':sha(before),'beforeSha256':sha(before),'afterSha256':sha(after_bytes),'candidate':binding(candidate_path),'patch':binding(patch_path)})
    owners.append({'name':'ai-tools','ownerCheckout':'../aitools','repository':git(ai_owner,'remote','get-url','origin').decode().strip(),'baseRevision':ai_base,'observedOriginMain':ai_base,'observedOwnerHead':git(ai_owner,'rev-parse','HEAD').decode().strip(),'mainVerification':'local refs only; fresh remote verification required before delivery','files':ai_files,'guidance':[],'prerequisites':['immutable approved inventory revision','Story 5.10 delivery','fresh exact-byte final plan approval'],'integration':None})
    no_change = []
    for name,reason in NO_CHANGE.items():
        repo = ROOT.parent/name
        if not (repo/'.git').exists():
            title = {'polymorphicserializations':'PolymorphicSerializations'}.get(name,name.capitalize())
            repo = ROOT/'references'/('Hexalith.'+title)
        no_change.append(inspect_unchanged(repo,name,reason))
    writes[E/'upstream/manifest.json'] = serialized({'schemaVersion':'1.0.0','state':'candidate','owners':owners,'noChange':no_change})
    # Approval receipt is written last: inventory bytes point at its decision, never at themselves.
    roles = json.loads((ROOT/A/'evidence/story-5-7/approval.json').read_text())['requiredApprovalRoles']
    roles = [*roles, 'Tenants owning maintainer']
    artifacts = {**inventory, str(E/'labels.json'):sha(writes[E/'labels.json']),str(E/'upstream/manifest.json'):sha(writes[E/'upstream/manifest.json'])}
    for path in [E/'deferral-dispositions.md',E/'deferral-dispositions.json']:
        artifacts[str(path)] = sha(writes[path])
    for owner in owners:
        for file in owner['files']:
            artifacts[file['patch']['path']] = file['patch']['sha256']
            if 'candidate' in file: artifacts[file['candidate']['path']] = file['candidate']['sha256']
    receipt = {'schemaVersion':'1.0.0','decision':'pending','baselineCommit':BASELINE,'requiredApprovalRoles':roles,'rolesPolicy':'Single maintainer must explicitly cover every required role; intent approval and predecessor approval do not approve these bytes.','artifacts':artifacts,'amendments':[{'module':m,'predecessor':binding(A/f'{m}-migration-inventory-v{v1}.md'),'successor':binding(A/f'{m}-migration-inventory-v{v2}.md'),'priorApproval':binding(A/'evidence/story-5-7/approval.json'),'rows':sorted(rows(successor(m).decode()))} for m,(v1,v2) in SUCCESSORS.items()],'limits':['Documentary disposition and citations only; no runtime, census, dependencies or AD-23 bytes change.','No execution, enrollment, parity, retirement, Git delivery or package publication authorized.','Separate exact-byte approval and delivery authorization required; plan awaits immutable inventory publication.']}
    delivered = json.loads((ROOT/A/'evidence/story-5-10/labels.json').read_text())
    if delivered['state'] != 'integrated':
        raise ValueError('Story 5.10 integrated label register required for this rebind')
    story510 = {'approval':binding(A/'evidence/story-5-10/approval.json'),
                'labels':binding(A/'evidence/story-5-10/labels.json'),
                'state':'approved-and-delivered', 'inventoryRevision':delivered['inventoryRevision'],
                'ownerIntegrations':{r['name']:r['integration']['commit'] for r in delivered['repositories']}}
    inputs = {'schemaVersion':'1.0.0','recordedOn':'2026-11-22','baselineCommit':BASELINE,'authorities':[binding(AD/'AD-23-non-gateway-capability-classes.md'),binding(AD/'AD-23-capability-class-map.json'),binding(A/'evidence/story-5-2/approval.json'),binding(A/'evidence/story-5-2/main-integration.json')],'inventoryHistories':history,'priorApprovals':[binding(A/f'evidence/story-5-{s}/approval.json') for s in [7,8,9,10]],'labelRegisters':[binding(A/f'evidence/story-5-{s}/labels.json') for s in [7,8,9,10]],'prerequisites':{'story510':story510,'parties':{'state':'retirement-blocked','decision':'Labels + slip','gates':['G01','G02','G03','G04','G05','G06'],'separateConflict':'restricted/destructive source classifications versus existing enrollment; exact owner successor and both-head direct/chained denial with zero unauthorized effects','sm3':binding(A/'evidence/story-5-5/sm3-status.json'),'deadline':'2027-02-05','assessmentDate':'2026-11-22','deadlinePassed':False,'outcome':'pending-not-met'}},'rootReferencePins':git(ROOT,'ls-tree','HEAD','references/').decode().splitlines()}
    inputs['prerequisites']['parties']['ownerDecision'] = {**binding(A/'spec-5-5-retire-legacy-packages-and-platform-routes.md'),'anchor':str(A/'spec-5-5-retire-legacy-packages-and-platform-routes.md')+':42','decision':'Split: labels + slip; retirement waits for G01–G06 and a new retirement-ready verdict'}
    writes[E/'inputs.json'] = serialized(inputs)
    receipt['artifacts'][str(E/'inputs.json')] = sha(writes[E/'inputs.json'])
    writes[E/'approval.json'] = serialized(receipt)
    # Derivation and all hash bindings are complete. Stage every write on the
    # destination filesystem before changing the working packet; receipt is last.
    with tempfile.TemporaryDirectory(dir=ROOT/A) as temporary:
        stage = Path(temporary)
        previous = {}
        installed = []
        for path,payload in writes.items():
            destination = ROOT/path
            staged = stage/path
            staged.parent.mkdir(parents=True,exist_ok=True)
            staged.write_bytes(payload)
            if destination.exists():
                previous[path] = destination.read_bytes()
                staged.chmod(destination.stat().st_mode)
        if existing.exists() and json.loads(existing.read_text()).get('decision') == 'approved':
            raise ValueError('Approved packet is immutable; prepare an explicitly authorized successor instead')
        try:
            for path in writes:
                (ROOT/path).parent.mkdir(parents=True,exist_ok=True)
                (stage/path).replace(ROOT/path)
                installed.append(path)
        except OSError:
            for path in reversed(installed):
                if path in previous:
                    (ROOT/path).write_bytes(previous[path])
                else:
                    (ROOT/path).unlink()
            raise
    print('Prepared receipt-based successors, eight inventory histories, fourteen labels and nine owner patch sets; no approval or delivery claimed.')


def cli():
    try: main()
    except (ValueError,OSError,KeyError,TypeError) as error:
        print('FAIL: '+str(error),file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(cli())
