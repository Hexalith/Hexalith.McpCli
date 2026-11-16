#!/usr/bin/env python3
"""Generate pending documentary successors from immutable predecessors and Git objects.

Never applies patches, mutates source checkouts, or overwrites an approved packet.
"""
import difflib
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[4]
ART = Path('_bmad-output/implementation-artifacts')
E = ART / 'evidence/story-5-9'
AD = Path('_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22')
BASELINE = 'fbe4b6bd5502741ff8006abedac5c9bb27a4df3c'
SPEC = ART / 'spec-5-9-refresh-and-re-disposition-projects-and-frontcomposer-inventories.md'
APPROVAL = '[A2](#a2-amendment-approval-pending)'
MODULES = {
    'projects': dict(title='Projects', version='2.1.0', old=ART/'projects-migration-inventory-v2.md',
                     new=ART/'projects-migration-inventory-v2.1.0.md',
                     map=ART/'projects-migration-inventory-v1.md',
                     pin='bf9f98969efa036fd60700c627e712b4375e654a',
                     oldpin='3d256e632a7645bc2261e668ac7c74be81155f58'),
    'frontcomposer': dict(title='FrontComposer', version='1.1.0', old=ART/'frontcomposer-migration-inventory-v1.md',
                          new=ART/'frontcomposer-migration-inventory-v1.1.0.md',
                          map=ART/'frontcomposer-migration-inventory-v1.md',
                          pin='33e71036c04f2b99955376e9c90cbb1fc3a81e64',
                          oldpin='81a440a8890a17edb39924bd0cf676eb6f6b5c25'),
}
EXTRA = ['Capability class', 'Adopted outcome', 'Amendment disposition', 'Amendment coverage',
         'Amendment rationale or gap', 'Amendment owner', 'Exact replacement', 'Pinned evidence', 'Drift']
ROLES = ['Projects owning maintainer', 'Projects Contracts/query/security maintainer',
         'FrontComposer owning maintainer', 'FrontComposer host/compiler/security maintainer',
         'EventStore/Gateway admission maintainer', 'McpCli product/architecture owner',
         'McpCli dependency/Catalog and conformance maintainer', 'McpCli contract/transport/security maintainer',
         'Platform architecture/security maintainer']
LIMITS = ['Disposition authority only; no enrollment, publication, execution, parity or retirement authority.',
          'Exact-byte owner approval and separate explicit delivery authorization are independent gates.',
          'No commit, push, merge or upstream checkout write is authorized by this packet.']
AUTHORITIES = list(dict.fromkeys([m[k] for m in MODULES.values() for k in ['old','map']] + [
    AD/'AD-23-non-gateway-capability-classes.md', AD/'AD-23-capability-class-map.json',
    ART/'evidence/story-5-2/approval.json', ART/'evidence/story-5-2/main-integration.json',
    ART/'technical-tools-migration-inventory-v1.0.3.md', ART/'evidence/story-5-1/verification.md',
    ART/'evidence/story-5-7/approval.json', ART/'evidence/story-5-7/labels.json',
    ART/'evidence/story-5-8/approval.json', ART/'evidence/story-5-8/labels.json',
    Path('Directory.Build.props'), Path('tools/dependency-policy.json'), Path('tools/inventory-coverage/v1/projects-approved.json'),
    Path('src/Hexalith.McpCli/Hexalith.McpCli.csproj'), Path('src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs')]))
TARGETS = {'T01':'ListProjectsQuery', 'T02':'GetProjectQuery',
           'T03':'ResolveProjectFromConversationQuery', 'T04':'ResolveProjectFromAttachmentsQuery'}
MAPPING = {'L01':['T01'],'R01':['T01'],
           **{k:['T02'] for k in ['L02','L03','L06','L07','R02','R04']},
           **{k:['T03','T04'] for k in ['L04','L05','V02']},
           'V01':['T01','T02'],'V08':['T01','T02','T03','T04'],
           **{k:[k] for k in TARGETS}}
READ_GAPS = 'Open: DW-82 publication, live acceptance and Projects 6.7 cutover.'
PAGING_GAP = ('K03/AD-20 conformity gap: ListProjectsQuery declares Payload cursor/pageSize (default 50, maximum 200); '
              'the executor submits Payload unchanged and separately constructs Envelope Paging from call options. '
              'The owner-accepted envelope-paging difference is not established for this Payload-declared contract. '
              'No conversion, conformity, readiness or parity is claimed.')
LOSSES = ('Owner accepts loss of resource URIs/subscriptions, first-visible selection (use explicit --aggregate-id), '
          '25/50/100 caps (intended envelope paging up to 200), descriptive metadata by default '
          '(Safe Metadata now defaults), file-ID scoring in trace, and legacy error/exit dialect '
          '(McpCli JSON errors on stdout and exit 2). No legacy format is silently converted.')
COUPLED = ('FK01 Projects plug-in registration, FK02 Counter.Web /mcp sample, FK03 Parties.UI dependency and '
           'FK04 FrontComposer Mcp.Tests, Shell.Tests.Bench, SourceTools.Tests and the Shell.Tests Counter sample fixture must move first. '
           'Then FrontComposer host and Projects plug-in retire together only after both inventories, '
           'K12 confidential Web/Chatbot UI evidence (Projects 7.6–7.14), Projects 6.7 cutover, DW-82 publication, '
           'live authorization/behavior acceptance, release and rollback gates pass. '
           'K13 compiler CLI (C01/C02/V06–V08) is exempt under merged AI.Tools plan 1.2.0, retained, '
           'excluded from this gate and never counted retired.')
FV_PARITY = ('FV04: distinguish rejection, contract validation, caller cancellation, timeout (including non-caller '
             'OperationCanceledException), downstream failure, optional identifiers, IsError/StructuredContent/text '
             'and successful lifecycle snapshots with rejected/unconfirmed outcomes; Category is not separately serialized. '
             'FV08: blank first argument prints help/exit 0; cancellation and I/O/access failures in either verb '
             'return exit 4 with sanitized stderr. Preserve or obtain a specific accepted difference; no retry authority.')
CLOSURE = '_bmad-output/implementation-artifacts/evidence/epic6/6.6/d9/contracts-package-closure.json'
PACKAGE = '_bmad-output/implementation-artifacts/evidence/epic6/6.6/review-pass2/candidate/Hexalith.Projects.Contracts.2.0.0-story66.3.nupkg'
# Source bytes used during derivation are bound in approval.json, including all anchors.
SOURCES = {}
RAW = {}
CONSUMER_CACHE = {}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            require(key not in value, f'duplicate JSON member {key}')
            value[key] = item
        return value
    value = json.loads(path.read_bytes(), object_pairs_hook=unique)
    require(isinstance(value, dict), f'JSON document must be an object: {path.name}')
    return value


def load(root, name, path):
    spec = importlib.util.spec_from_file_location(name, root/path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(repo, *args):
    result = subprocess.run(['git','-C',str(repo),*args], capture_output=True)
    require(result.returncode == 0, f'git {" ".join(args)} failed: ' + (result.stderr.decode(errors='replace').strip() or '(no stderr)'))
    return result.stdout


def predecessor_bytes(root,module):
    """Use the exact predecessor snapshot named by the approval baseline."""
    path = MODULES[module]['old']
    return git(root,'show',f'{BASELINE}:{path}')


def repo(module):
    return Path('references/Hexalith.' + MODULES[module]['title'])


def blob(root, module, path, pin=None):
    pin = pin or MODULES[module]['pin']
    key = (str((root/repo(module)).resolve()),pin,path)
    if key not in RAW:
        RAW[key] = git(root/repo(module), 'show', f'{pin}:{path}')
    data = RAW[key]
    SOURCES[f'{repo(module)}@{pin}:{path}'] = sha(data)
    return data


def source(root, module, path, pin=None):
    return blob(root,module,path,pin).decode('utf-8-sig')


def anchor(root, module, path, needle, pin=None):
    text = source(root,module,path,pin)
    require(needle in text, f'{module}: pinned source lacks {needle!r}: {path}')
    return path + ':' + str(text.count('\n',0,text.index(needle)) + 1)


def parse(text, module):
    rows, headers = {}, []
    for line in text.splitlines():
        if not line.startswith('|'):
            headers = []
            continue
        cells = [c.strip() for c in re.split(r'(?<!\\)\|',line)[1:-1]]
        if cells and cells[0] == 'ID':
            headers = cells
        elif cells and re.fullmatch(r'(?:[TRMLVHDC]\d{2}|G\d+)',cells[0]):
            key = cells[0]
            require(key not in rows, f'{module}:{key}: duplicate entry')
            require(headers and len(cells) == len(headers) and all(cells), f'{module}:{key}: damaged row or empty cell')
            rows[key] = dict(cells=cells, headers=headers[:], text=line)
    return rows


def class_entries(root, module):
    mapping = read_json(root/AD/'AD-23-capability-class-map.json')
    inv = next(i for i in mapping['inventories'] if i['path'] == str(MODULES[module]['map']))
    entries = {r['id']:r.get('classId','governance') for r in inv['rows']+inv['records']}
    if module == 'projects':
        entries.update({k:'K01' for k in TARGETS})  # additive 2.0.0 targets; AD-23 map binds 1.0.0 rows only
    return entries, {c['id']:c['outcome'] for c in mapping['classes']}


def declarations(root):
    result = {}
    for key, name in TARGETS.items():
        path = f'src/Hexalith.Projects.Contracts/Queries/{name}.cs'
        text = source(root,'projects',path)
        wire = re.search(r'public const string QueryType = "([^"]+)";',text)
        declaration = re.search(r'\[HexalithQuery\((.*?)\)\]',text,re.S)
        require(wire is not None and declaration is not None, f'projects:{key}: absent decorated Query')
        body = declaration[1]
        canonical = re.search(r'Name = "([^"]+)"',body)
        aggregate = re.search(r'AggregateId = "([^"]+)"',body)
        require(canonical is not None, f'projects:{key}: missing canonical name')
        result[key] = dict(clr='Hexalith.Projects.Contracts.Queries.'+name,
                           name='projects.'+canonical[1], wire=wire[1],
                           aggregate=aggregate[1] if aggregate else 'caller --aggregate-id',
                           evidence=anchor(root,'projects',path,'[HexalithQuery('), path=path, source=text)
    return result


def decision(module, key, klass):
    if module == 'projects' and key in MAPPING:
        return 'replace'
    if klass in {'K07','K08','K12','K13','K15'}:
        return 'withdraw'
    return 'defer'


def rationale(module, key, klass):
    d = decision(module,key,klass)
    if d == 'replace':
        note = READ_GAPS + ' ' + LOSSES
        if key in {'T01','R01','L01','V01'}:
            note += ' ' + PAGING_GAP
        if key == 'V08':
            note += ' Read correlation uses canonical uppercase ULIDs; fresh MessageId remains separate. Command parts follow K12 withdrawal; no task-as-message or key conversion.'
        return note
    if klass == 'K12':
        return ('Owner rationale: restriction precedence keeps confirmation-required/destructive/unsupported erasure and key-rotation '
                'behavior off the public agent surface. Replacement experience: confidential Web/Chatbot UI. '
                'Accepted loss: all legacy agent maintenance/confirmation conveniences in this row. '
                'Projects 7.6–7.14 UI coverage evidence is required before retirement; no decorated Command at the pin.')
    if klass == 'K07':
        return ('Owner rationale: documentation is not a Gateway Query. Replacement experience: packages, README and AI.Tools. '
                'Accepted loss: resource URI, Markdown rendering, subscription and schema-negotiation delivery conventions; no business operation inferred.')
    if klass == 'K08':
        return ('Owner rationale: retire the synthetic lifecycle observation engine from migration scope. Replacement experience: '
                'Gateway acceptance and separately decorated business status Queries where available. Accepted loss: synthetic '
                'timed_out/needs_review, bounded in-memory history, expiry/eviction, long-poll and subscription semantics. Acceptance is not completion.')
    if klass == 'K13':
        return ('Owner rationale: exempt local compiler tooling under merged AI.Tools amendment 1.2.0. Replacement experience: '
                'retain inspect/migrate independently with existing build/freshness, path/hash/drift, sequential partial writes/applied:false '
                'and output-privacy gates. Accepted loss: compiler coverage in McpCli migration, no local tool capability lost. Retained; never counted retired.')
    if klass == 'K15':
        return ('Owner rationale: local preview/parser/profile/output conventions are withdrawn. Replacement experience: caller-authored '
                'McpCli JSON and profiles, safe structured stdout errors/exit 2; no simulation or generated subcommand. '
                'Accepted loss: the legacy convention in this row, including preview convenience, ignored options and output/exit dialects; no credential copying or silent conversion.')
    if key.startswith('G'):
        if (module,key) in {('projects','G6'),('frontcomposer','G4')}:
            return 'Open gap: coupled retirement gate: ' + COUPLED
        gates = {
            ('projects','G1'): 'Slim Contracts now exist; enrolled candidate 2.0.0-story66.3 has an approved closure. DW-82 publication remains open. ' + PAGING_GAP,
            ('projects','G2'): 'Authenticated envelope binding, role/scope/audience and fresh Tenant admission now exist. Live denied/foreign/absent safety and cross-tenant zero effects remain open.',
            ('projects','G3'): 'Command serialization, actor/task/correlation and separate caller-key handoff remain open; Commands are K12 UI-only. Task context uses Payload, declared actorProperty or allowed Command extensions; no Query extension channel. ' + PAGING_GAP,
            ('projects','G4'): 'Four supported Query handlers now exist; remaining audit/export/context/composite handlers and semantics remain open (Projects 8.1/8.2/8.4/8.5). ' + READ_GAPS,
            ('projects','G5'): 'Independent Catalog coverage, both-head live requests/denials, metadata, persisted effects, release and rollback remain open. ' + READ_GAPS,
            ('frontcomposer','G1'): 'Exact-byte owner approval of both successors and FK01–FK04 consumer handoffs remains open; session approval is not owner completeness.',
            ('frontcomposer','G2'): 'Projects slim decorated candidate exists; DW-82 publication, live acceptance, 6.7 cutover and dependency/authorization/release gates remain open.',
            ('frontcomposer','G3'): 'AD-23 withdraws lifecycle/documentation, retains K13 compiler exemption and defers K10 per-user HTTP authority. Remaining consumer Contracts, redaction/schema and authorization parity remain open.',
        }
        return 'Open gap: ' + gates[(module,key)]
    if module == 'frontcomposer':
        return ('Open gap: no decorated replacement type for this framework/manifest family at the pin; '
                + ('K10 forwarded per-user HTTP identity and caller authority needs an approved generic transport/security decision; actor/task values grant no authority.' if klass == 'K10' else
                   'each business consumer needs exact decorated Contracts, Gateway route, bounded safe machine results and deny-before-dispatch parity. ' + FV_PARITY))
    if key == 'V09':
        return ('Open gap: no Query extension channel for Commands and M05 task/actor handoff; taskId Command extension must be '
                'explicitly allowed, actorProperty only fills a declared Payload member and neither grants authority. '
                'T01–T04 need no task context (supported admission passes taskId: null). Owner: Projects 8.4/8.5 and Gateway admission.')
    story = '8.1' if key in {'R06','L08'} else '8.2' if key in {'R03','R07','R08','R09','R10','L09','L10','L11','V03'} else '8.4/8.5'
    return ('Open gap: no decorated equivalent Query at the pin; Projects '+story+' owns the missing audit/export/context/composite '
            'contract, bounded safe result, handler and live authorization/freshness evidence. Task-dependent reads without Payload context stay deferred; no Query extension channel is invented.')


def owner(module, klass):
    if klass == 'K10':
        return 'FrontComposer and McpCli contract/transport/security maintainers'
    if klass == 'governance':
        return 'Projects and FrontComposer owning maintainers; Gateway and McpCli conformance maintainers'
    return MODULES[module]['title'] + ' owning and Contracts/query/security maintainers'


def replacement(module, key, klass, decl):
    if decision(module,key,klass) == 'replace':
        parts = []
        for target in MAPPING[key]:
            d = decl[target]
            parts.append(f'{target}: {d["name"]}; {d["clr"]}; eligibility: decorated agent read at pin; Gateway SubmitQueryRequest(domain=projects, wire={d["wire"]}, aggregate={d["aggregate"]}, projectionType=null, projectionActorType=null); enrolled candidate Hexalith.Projects.Contracts/2.0.0-story66.3, closure fits tools/dependency-policy.json')
        return '<br>'.join(parts)
    if klass == 'K12': return 'Confidential interactive Web/Chatbot UI; Projects 7.6–7.14 evidence required; no public agent route.'
    if klass == 'K13': return 'Retained local FrontComposer inspect/migrate; AI.Tools amendment 1.2.0; exempt and never counted retired.'
    if klass == 'K07': return 'Documentation in packages, README and AI.Tools; no Gateway route.'
    if klass == 'K08': return 'Gateway acceptance plus independently decorated business Queries, without synthetic lifecycle parity.'
    if klass == 'K15': return 'McpCli generic invocation/profiles/JSON; owner accepts loss of legacy convenience.'
    return 'None; named owner gap remains open.'


def expand(module, path):
    if path.startswith(('Mcp/','Cli/','Contracts/','Server/')):
        name,rest = path.split('/',1)
        return f'src/Hexalith.{MODULES[module]["title"]}.{name}/{rest}'
    if path.startswith('Corpus/'):
        return 'docs/skills/frontcomposer/' + path[7:]
    return path


def predecessor_anchors(root,module,row):
    """Re-anchor original source lines by their exact text, never an old line number alone."""
    oldpin = MODULES[module]['oldpin']
    evidence = []
    last = None
    for match in re.finditer(r'`([^`]+)`',row['text']):
        token = match[1]
        m = re.fullmatch(r'(.+):(\d+)',token)
        if m:
            last, number = expand(module,m[1]), int(m[2])
        elif re.fullmatch(r':\d+',token) and last:
            number = int(token[1:])
        else:
            continue
        if last.startswith('src/Hexalith.McpCli'):
            continue
        before = source(root,module,last,oldpin).splitlines()
        require(0 < number <= len(before), f'{module}: invalid predecessor anchor {last}:{number}')
        needle = before[number-1].strip()
        after = source(root,module,last).splitlines()
        matches = [i for i,line in enumerate(after,1) if line.strip() == needle and needle]
        if matches:
            current = min(matches,key=lambda n:abs(n-number))
            value = f'{last}:{current}'
            if value not in evidence: evidence.append(value)
        else:
            # Changed statements are re-anchored below using current semantic needles.
            continue
    return evidence


# Logical REST reads reached by the pinned resource/CLI/variant call chains.
# R05/R11 and local preview/parser variants are static and deliberately absent.
PROJECTS_REST_PATHS = {
    'R01':['list'], 'R02':['detail'],
    **{k:['diagnostic'] for k in ['R03','R04','R06','R07']},
    **{k:['list','diagnostic'] for k in ['R08','R09','R10']},
    'M05':['refresh'], 'L01':['list'], 'L02':['detail'], 'L03':['detail'],
    **{k:['conversation','attachments'] for k in ['L04','L05','V02']},
    **{k:['diagnostic'] for k in ['L06','L07','L08','L11','L14','L15','L16','L17','V06']},
    **{k:['list','diagnostic'] for k in ['L09','L10','V03']},
    **{k:['refresh','diagnostic'] for k in ['L18','V05','V07']},
    **{k:['list','detail','diagnostic'] for k in ['V01','V08','V10','V11']},
}
REST_ENDPOINTS = {
    'list':('src/Hexalith.Projects.Server/ProjectsDomainServiceEndpoints.cs','ListProjectsAsync'),
    'detail':('src/Hexalith.Projects.Server/ProjectsDomainServiceEndpoints.cs','GetProjectAsync'),
    'diagnostic':('src/Hexalith.Projects.Server/ProjectsDomainServiceEndpoints.cs','GetProjectOperatorDiagnosticsAsync'),
    'refresh':('src/Hexalith.Projects.Server/Queries/RefreshProjectContextEndpoint.cs','RefreshProjectContextAsync'),
    'conversation':('src/Hexalith.Projects.Server/Queries/ResolveProjectFromConversationEndpoint.cs','ResolveProjectFromConversationAsync'),
    'attachments':('src/Hexalith.Projects.Server/Queries/ResolveProjectFromAttachmentsEndpoint.cs','ResolveProjectFromAttachmentsAsync'),
}


def rest_evidence(root,key):
    result=[]
    for route in PROJECTS_REST_PATHS.get(key,[]):
        path,method=REST_ENDPOINTS[route]
        text=source(root,'projects',path)
        declaration=re.search(r'(?:private|internal|public) static async Task<IResult> '+method+r'\(',text)
        require(declaration is not None,f'projects:{key}: missing REST endpoint {method}')
        start=declaration.start()
        following=re.search(r'\n    (?:private|internal|public) ',text[declaration.end():])
        end=declaration.end()+following.start() if following else len(text)
        block=text[start:end]
        require('BeginQueryRequest(httpContext,' in block,f'projects:{key}: {method} no longer uses the shared preamble')
        offset=start+block.index('BeginQueryRequest(httpContext,')
        result.append(path+':'+str(text.count('\n',0,offset)+1))
    if result:
        path='src/Hexalith.Projects.Server/Queries/ProjectQueryRequestPreamble.cs'
        result += [anchor(root,'projects',path,'private static string BeginQueryRequest'),
                   anchor(root,'projects',path,'private static IResult? ValidateQueryRequest')]
    return result


def current_behavior(module,key,original):
    if module != 'frontcomposer' or key not in {'V01','V02','V03'}:
        return original
    replacements = {
        'V01':('The process-wide store indexes handles and has no originating tenant/user binding.',
               'The process-wide store binds indexed handles to the originating tenant/user and enforces ownership before current-tool admission.'),
        'V02':('HTTP `/mcp` requires authorization',
               'HTTP `/mcp` always requires an authenticated user and authorization'),
        'V03':('A valid key takes precedence over authenticated claims and calls Create with claimsSource: null, yielding tenant/user only;',
               'A valid key uses the explicit API-key authentication scheme and refuses conflicting authenticated tenant/user identities; it calls Create with claimsSource: null, yielding tenant/user only;'),
    }
    before,after=replacements[key]
    require(original.count(before)==1,f'frontcomposer:{key}: expected historical behavior premise missing or duplicated')
    return original.replace(before,after)


def evidence(root,module,key,row,decl):
    if key in TARGETS and module == 'projects': return [decl[key]['evidence']]
    anchors = predecessor_anchors(root,module,row)
    if module == 'projects' and key.startswith('L'):
        text = source(root,module,'src/Hexalith.Projects.Cli/ProjectsCliParser.cs')
        spelling = row['cells'][1].strip('`').split()[-1]
        anchors.insert(0,anchor(root,module,'src/Hexalith.Projects.Cli/ProjectsCliParser.cs','"'+spelling+'"'))
    extras = {
        ('projects','G1'):[('src/Hexalith.Projects.Contracts/Hexalith.Projects.Contracts.csproj','FrontComposer, ASP.NET'),('src/Hexalith.Projects.UI.Contracts/Hexalith.Projects.UI.Contracts.csproj','<Project')],
        ('projects','G2'):[('src/Hexalith.Projects.Server/Queries/ProjectReadQueryAdmission.cs','internal static async'),('src/Hexalith.Projects.Server/Authorization/ProjectAuthorizationGate.cs','AuthorizeSupportedScopeAsync')],
        ('projects','G3'):[('src/Hexalith.Projects.Server/Authorization/ProjectAuthorizationGate.cs','taskId: null')],
        ('projects','G4'):[('src/Hexalith.Projects.Server/ProjectsServerServiceCollectionExtensions.cs','services.AddSingleton<IDomainQueryHandler, ResolveProjectFromConversationQueryHandler>')],
        ('projects','G5'):[('_bmad-output/planning-artifacts/epics.md','**UX-DR19')],
        ('projects','G6'):[('src/Hexalith.Projects.Mcp/ProjectsMcpModule.cs','public static IServiceCollection AddProjectsMcp')],
        ('projects','V09'):[('src/Hexalith.Projects.Server/ProjectsDomainProcessor.cs','taskId'),('src/Hexalith.Projects.Server/Authorization/ProjectAuthorizationGate.cs','taskId: null')],
        ('frontcomposer','G1'):[('src/Hexalith.FrontComposer.Mcp/FrontComposerMcpOptions.cs','public sealed class')],
        ('frontcomposer','G2'):[('src/Hexalith.FrontComposer.Mcp/FrontComposerMcpOptions.cs','public sealed class')],
        ('frontcomposer','G3'):[('src/Hexalith.FrontComposer.Mcp/Extensions/FrontComposerMcpEndpointRouteBuilderExtensions.cs','MapFrontComposerMcp')],
        ('frontcomposer','G4'):[('samples/Counter/Counter.Web/Program.cs','MapFrontComposerMcp')],
        ('frontcomposer','H01'):[('src/Hexalith.FrontComposer.Mcp/Invocation/FrontComposerMcpLifecycleTracker.cs','TryResolveReader(out FrontComposerMcpAgentContext? reader)')],
        ('frontcomposer','V01'):[('src/Hexalith.FrontComposer.Mcp/Invocation/FrontComposerMcpLifecycleStore.cs','TenantId')],
        ('frontcomposer','V02'):[('src/Hexalith.FrontComposer.Mcp/Extensions/FrontComposerMcpEndpointRouteBuilderExtensions.cs','RequireAuthenticatedUser()')],
        ('frontcomposer','V03'):[('src/Hexalith.FrontComposer.Mcp/FrontComposerMcpApiKeyAuthenticationHandler.cs','HandleAuthenticateAsync'),('src/Hexalith.FrontComposer.Mcp/HttpFrontComposerMcpAgentContextAccessor.cs','HasConflictingClaim(http.User')],
        ('frontcomposer','C02'):[('src/Hexalith.FrontComposer.Cli/WriteSafetyPolicy.cs','class WriteSafetyPolicy')],
        ('frontcomposer','V07'):[('src/Hexalith.FrontComposer.Cli/PathUtilities.cs','Resolve')],
    }
    for path,needle in extras.get((module,key),[]): anchors.append(anchor(root,module,path,needle))
    if module == 'projects': anchors.extend(rest_evidence(root,key))
    if module == 'projects' and key in {'L04','L05','V02'}:
        for name in ['Attachments','Conversation']:
            path = f'src/Hexalith.Projects.Server/Queries/ResolveProjectFrom{name}Endpoint.cs'
            anchors.append(anchor(root,module,path,'CancellationTokenSource'))
            anchors.append(anchor(root,module,path,'AuthorizeLegacyResolutionCandidatesAsync'))
            if name == 'Attachments': anchors.append(anchor(root,module,path,'.ListByReferenceAsync(authoritativeTenantId, acceptedFolders, [],'))
    require(bool(anchors),f'{module}:{key}: no current pinned anchor')
    return list(dict.fromkeys(anchors))


def drift(module,key):
    changes = {
        'projects': {
            **{k:'shared REST request preamble now applies through '+', '.join(routes)+' read path(s); correlation normalization precedes authorization and freshness/idempotency-key validation follows authorization' for k,routes in PROJECTS_REST_PATHS.items()},
            **{k:'shared REST request preamble applies to conversation/attachment resolution; file IDs no longer score, candidates are re-authorized and owner-read deadlines apply' for k in ['L04','L05','V02']},
            **{k:'supported decorated Query source and UI Contracts split now exist' for k in ['T01','T02','T03','T04','G1']},
            'G2':'supported read admission binds authenticated envelope, role/scope/audience and fresh Tenant evidence',
            'G4':'four supported Query handlers registered; remaining legacy coverage still absent',
            'V09':'processor anchors shift four lines; supported Query authorization passes taskId: null',
            'G6':'coupled gate now explicitly accounts for FK01–FK04, K12 UI evidence and K13 exemption',
        },
        'frontcomposer': {
            **{k:'lifecycle entries now bind originating tenant and user and enforce ownership' for k in ['H01','V01']},
            'V02':'/mcp now always requires an authenticated user',
            'V03':'API-key authentication scheme and conflicting-identity refusal now exist',
            'D11':'setup documentation body changed; same registered document and URI',
            'D13':'synthetic manifest rendering changed; same resource identity',
            **{k:'ancestor-link/junction/nested-repository refusals now guard local migration targets' for k in ['C02','V07']},
            'V08':'help/output anchors shifted; blank input help and exit-4 cancellation/I/O apply to both verbs',
            'G4':'coupled gate now explicitly accounts for FK01–FK04 and retained K13 compiler',
        },
    }
    return 'changed: '+changes[module][key]+'.' if key in changes[module] else 'unchanged: legacy registration/behavior at the comparison base; disposition is amended separately.'


def consumers(root):
    """Recheck the four named consumers at all root gitlinks, without scanning nested repos."""
    links = []
    for line in git(root,'ls-tree',BASELINE,'references/').decode().splitlines():
        mode,kind,pin,path = line.replace('\t',' ').split(maxsplit=3)
        if mode == '160000': links.append((path,pin))
    require(len(links) == 17,'root reference scope differs from approved 17-gitlink scan')
    cache_key = tuple(links)
    if cache_key in CONSUMER_CACHE: return links,CONSUMER_CACHE[cache_key]
    hits = []
    for path,pin in links:
        result = subprocess.run(['git','-C',str(root/path),'grep','-n','-I','-E',
                                 'AddFrontComposerMcp|MapFrontComposerMcp|Hexalith\\.FrontComposer\\.Mcp',
                                 pin,'--','*.cs','*.csproj'], capture_output=True)
        require(result.returncode in {0,1}, f'consumer scan failed: {path}')
        for line in result.stdout.decode('utf-8-sig').splitlines():
            _,filename,number,text = line.split(':',3)
            # Only live root source/project declarations are consumers. Namespace
            # strings, fixture assertions and archived evidence copies are not hosts.
            if not filename.startswith(('src/','samples/','examples/','tests/','test/')):
                continue
            dependency = filename.endswith('.csproj') and re.search(r'<(?:ProjectReference|PackageReference)\b[^>]*Include=[^>]*Hexalith\.FrontComposer\.Mcp',text)
            registration = filename.endswith('.cs') and re.match(r'\s*(?:return |_=|_ = )?[\w.]*\.(?:AddFrontComposerMcp|MapFrontComposerMcp)\s*\(',text)
            if dependency or registration:
                hits.append((path,pin,filename,int(number),text))
    CONSUMER_CACHE[cache_key] = hits
    return links,hits


def candidate(root,module):
    m = MODULES[module]
    old = parse(predecessor_bytes(root,module).decode('utf-8'),module)
    entries,outcomes = class_entries(root,module)
    decl = declarations(root)
    header = f'''---
inventory_version: '{m['version']}'
status: pending
module: {module}
source_repository: 'https://github.com/Hexalith/Hexalith.{m['title']}'
source_revision: '{m['pin']}'
source_spec: '{SPEC}'
predecessor: '{m['old']}'
approval_ref: '#a2-amendment-approval-pending'
---

# {m['title']} migration inventory {m['version']}

Additive successor to immutable {('Projects 2.0.0 (and 1.0.0)' if module == 'projects' else 'FrontComposer 1.0.0')}.
Every predecessor entry appears exactly once: {len(old)} entries. Pins are the approval-time
root gitlinks, rechecked at `{BASELINE}`. Sources and anchors are read only with
`git show {m['pin']}:<path>`; moving checkouts are never source evidence.

## A2 Amendment approval pending

This is a pending proposal. The separate [approval receipt](evidence/story-5-9/approval.json)
will establish effective exact-byte owner approval with identity, date, exact words and
covered roles under the single-maintainer model. It will replace A1 and Projects
2.0.0's session-only decision for these successors; no external maintainer approval
is asserted now. The receipt replaces the old `unasserted` field with the roles
it actually covers only after approval. The specification's approval approved
intent, not these inventory bytes. Delivery needs a separate explicit "authorize"
instruction after the candidate "approve" instruction. No enrollment, publication,
execution, parity, release acceptance or retirement follows. All existing
compatibility binaries remain retained with their gates closed.

## Amendment notation

The predecessor row shapes and identities remain visible with explicit amendment
columns; factual rationale, G/V premises and source evidence are refreshed. This is
an explicit versioned amendment, never a silent legacy-format conversion.
`include` occurs only with `replace` and means a documentary migration target.
It is not a readiness claim. AD-23 restriction precedence applies to every row.
The map binds the 1.0.0 legacy rows; Projects T01–T04 are the four additive 2.0.0
supported-read targets classified K01, not invented entries in the frozen map.
Withdrawals name rationale, replacement experience and accepted loss; deferrals
name the missing contract/channel and owning maintainer.

'''
    if module == 'projects':
        header += f'''Projects has four decorated String-kind Queries and no decorated Commands.
T01–T04 keep replace/include; approved UX-DR19 maps the legacy reads to them.
{READ_GAPS} Projects Contracts candidate 2.0.0-story66.3 is already declared
in McpCli's enrollment files; this story changes none of those files.
Its exact candidate package and owner closure are read at this pin; the four
closure packages fit the current policy. The current pin may contain later
source fields than the candidate: source decoration does not prove artifact parity.
{PAGING_GAP} No task context is required by T01–T04; supported admission passes
`taskId: null`. Other context reads cannot invent a Query extension bag.

'''
    else:
        header += '''The fixed framework set remains one configurable lifecycle tool, 13 documentation
resources and two local compiler leaves. Manifest families have consumer-owned
business operations; Projects is counted in its companion only. The compiler
catalog still covers only 9.1.0→9.2.0. K13 withdraws it only from migration scope:
inspect/migrate stay retained under merged AI.Tools plan 1.2.0 and never count retired.
Any future FrontComposer replace row must carry both FV04 and FV08 clarifications
from Story 5.1; this candidate has no FrontComposer replacement.

'''
    chunks = [header]
    previous = None
    for key,row in old.items():
        klass = entries[key]
        d = decision(module,key,klass)
        coverage = 'include' if d == 'replace' else 'exclude'
        why = rationale(module,key,klass)
        cells,headers = list(row['cells']),list(row['headers'])
        for i,h in enumerate(headers):
            if h == 'Disposition': cells[i] = d
            elif h == 'Coverage': cells[i] = coverage
            elif h == 'Disposition / coverage': cells[i] = d+' / '+coverage
            elif h in {'Approval','Approval reference'}: cells[i] = APPROVAL
            elif h == 'Source evidence': cells[i] = 'See current Pinned evidence column.'
            elif h in {'Query requirement / rationale','Rationale / missing contract','Missing replacement / rationale',
                        'Rationale / security class','Rationale / missing replacement','Required handoff / rationale',
                        'Required decision / evidence','Required decision / evidence before inclusion'}:
                cells[i] = why
        if key.startswith('G'): cells[1] = why
        if key.startswith('V'):
            cells[3] = why
            if (module,key) in {('frontcomposer','V01'),('frontcomposer','V02'),('frontcomposer','V03')}:
                cells[1] = current_behavior(module,key,row['cells'][1])
        if module == 'projects' and key == 'V09': cells[1] += ' Supported read authorization now passes taskId: null.'
        if module == 'frontcomposer' and key == 'H01':
            cells[4] = why
            cells[5] = 'Originating tenant/user ownership and current-tool admission are checked at this pin.'
        if key in TARGETS and module == 'projects':
            cells[3] = replacement(module,key,klass,decl)
        ev = evidence(root,module,key,row,decl)
        extra = [klass,outcomes.get(klass,'Scope accounting; no independent capability outcome'),d,coverage,why,
                 owner(module,klass),replacement(module,key,klass,decl),'`'+'`; `'.join(ev)+'`',drift(module,key)]
        if headers != previous:
            chunks += ['\n## '+{'T':'Supported decorated read targets','R':'Legacy resources','M':'Legacy maintenance tools',
                                  'L':'Frozen CLI spellings','V':'Compatibility variants','G':'Retained prerequisites',
                                  'H':'Framework host surfaces','D':'Documentation resources','C':'Retained compiler leaves'}[key[0]]+'\n\n',
                       '| '+' | '.join(headers+EXTRA)+' |\n','| '+' | '.join(['---']*(len(headers)+len(EXTRA)))+' |\n']
        chunks.append('| '+' | '.join(cells+extra)+' |\n')
        previous = headers
    chunks += ['\n## Coupled host and plug-in retirement gate\n\n'+COUPLED+'\n\n']
    links,hits = consumers(root)
    for ident,path,needle in [
        ('FK01','references/Hexalith.Projects','src/Hexalith.Projects.Mcp/ProjectsMcpModule.cs'),
        ('FK02','references/Hexalith.FrontComposer','samples/Counter/Counter.Web/Program.cs'),
        ('FK03','references/Hexalith.Parties','src/Hexalith.Parties.UI/Hexalith.Parties.UI.csproj'),
        ('FK04','references/Hexalith.FrontComposer','tests/')]:
        selected = [h for h in hits if h[0] == path and h[2].startswith(needle) and (ident != 'FK04' or h[2].endswith('.csproj') or 'Hexalith.FrontComposer.Shell.Tests/Samples/' in h[2])]
        require(selected,f'{ident}: required current consumer missing')
        chunks.append('- '+ident+': '+ '; '.join(f'`{p}@{pin}:{file}:{line}`' for p,pin,file,line,text in selected)+'; owner '+('Parties' if ident=='FK03' else 'Projects' if ident=='FK01' else 'FrontComposer')+'.\n')
    chunks += ['''
All 17 root gitlinks were checked for tracked C# registrations and project/package
consumers without entering nested submodules. No additional host consumer was
found; module-owned framework implementation/tests are accounted for in FK04.
Compiler leaves are independently retained and do not delay or count toward host
retirement. K12 UI proof and all live/release/rollback evidence remain open.

## Source comparison and verification limits

''']
    if module == 'projects':
        chunks += [f'''Compare legacy rows against `3d256e632a7645bc2261e668ac7c74be81155f58`;
2.0.0 baseline `ce71717a965eb21454b3e13068b9072404dac5f5` is an ancestor of
this pin. Mcp/Cli, strict submitter, Commands and Client scan-window source remain
unchanged. Server reads now share the request preamble; trace no longer scores
file IDs and reauthorizes candidates with deadlines. Supported handlers, admission
and the UI Contracts split correct the historical G1/G2/G4 premises.

Module: `src/Hexalith.Projects.Contracts/ProjectsMcpCliModule.cs:3`.
Owner UX-DR19: `_bmad-output/planning-artifacts/epics.md:229`.
Package: `{PACKAGE}`; closure: `{CLOSURE}`.
McpCli-local `src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs:270`
submits unchanged rebuilt Payload; lines 274–276 independently build Envelope Paging.
Payload declaration: `src/Hexalith.Projects.Contracts/Queries/ListProjectsQuery.cs:22`
(cursor) and `:26` (pageSize); default 50 and cap 200. {PAGING_GAP}
Freshness is module-owned and live defaults/conflicting values still need proof.
No automatic data or identifier conversion is inferred from a replacement mapping.
''']
    else:
        chunks += ['''Historical pin `81a440a8890a17edb39924bd0cf676eb6f6b5c25` is not an
ancestor. Compare through merge-base `b06f86d5`; Mcp/Cli/corpus/Counter.Web are
unchanged since `11c8377a`. Earlier drift includes tenant/user-bound lifecycle,
authenticated-user-only /mcp, explicit API-key authentication and identity-conflict
refusal, D11/D13 documentation rendering and local compiler link safety.
FV04/FV08 remain independent machine-result/exit-code parity constraints:
'''+FV_PARITY+'\n']
    chunks += ['''
[Story 5.9 verification](evidence/story-5-9/verification.md) proves static accounting,
source anchors, class/disposition rules and hash chains only. It executes no
legacy operation or live Query. Protected predecessors, AD-23, technical 1.0.3,
prior receipts, dependencies, enrollment, census, gitlinks, AI.Tools plan and
`references/` remain unchanged. Story 5.11 owns indexing these successors.
''']
    return ''.join(chunks).encode('utf-8')


def compatibility_section(data):
    lines = data.decode('utf-8').splitlines(keepends=True)
    starts = [i for i,l in enumerate(lines) if l.rstrip('\r\n') == '## Legacy compatibility surfaces']
    require(len(starts) == 1,'README must have exactly one compatibility section')
    start = starts[0]
    end = next((i for i in range(start+1,len(lines)) if lines[i].startswith('#')),len(lines))
    return ''.join(lines[start:end]).encode()


def label_candidate(root, inventories):
    prior_path = ART/'evidence/story-5-8/labels.json'
    old = read_json(root/ART/'evidence/story-5-7/labels.json')
    repositories, rows, writes = [], [], {}
    for module,m in MODULES.items():
        registration = next(r for r in old['repositories'] if r['name'] == module)
        before = blob(root,module,'README.md')
        text = before.decode('utf-8')
        for row in [r for r in old['rows'] if r['repository'] == module]:
            oldtext = row['label']['text']
            require(text.count(oldtext) == 1,row['id']+': prior label missing or duplicated at pin')
            new = re.sub(r'\['+m['title']+r' inventory 1\.0\.0\]\([^)]*\)',
                         f'[{m["title"]} inventory {m["version"]}](https://github.com/Hexalith/Hexalith.McpCli/blob/main/{m["new"]})',oldtext)
            if row['id'] in {'PS04','PS09'}:
                new += ' Coupled gate: FK01–FK04 consumers move first; K12 Web/Chatbot UI evidence, Projects 6.7 cutover, DW-82 publication and live/release/rollback acceptance remain required; K13 compiler is retained independently.'
            if row['id'] == 'PS08':
                new += ' Projects successor G1–G6 retain publication, live acceptance, K03/AD-20 conformity, 6.7 cutover and K12 confidential UI evidence gates.'
            new += f' {m["title"]} inventory SHA-256: `'+inventories[str(m['new'])]+'`.'
            text = text.replace(oldtext,new)
            rows.append(dict(row,label=dict(file='README.md',line=text.splitlines().index(new)+1,text=new,sha256=sha(new.encode()))))
        after = text.encode('utf-8')
        patch = ''.join(difflib.unified_diff(before.decode().splitlines(keepends=True),text.splitlines(keepends=True),fromfile='a/README.md',tofile='b/README.md',n=0)).encode()
        files = {'README.before.section.md':compatibility_section(before),'README.after.section.md':compatibility_section(after),'README.patch':patch}
        repository = dict(name=module,repository=registration['repository'],ownerCheckout=registration['ownerCheckout'],baseRevision=m['pin'],
                          readme=dict(beforeSha256=sha(before),afterSha256=sha(after)),integration=None)
        for k,n in [('before','README.before.section.md'),('after','README.after.section.md'),('patch','README.patch')]:
            path = E/'upstream'/module/n
            repository[k] = dict(path=str(path),sha256=sha(files[n]))
            writes[path] = files[n]
        repositories.append(repository)
    return dict(schemaVersion='1.0.0',state='candidate-pending-owner-approval-and-delivery',
                predecessor=dict(path=str(prior_path),sha256=sha((root/prior_path).read_bytes())),
                priorRows=dict(path=str(ART/'evidence/story-5-7/labels.json'),sha256=sha((root/ART/'evidence/story-5-7/labels.json').read_bytes())),
                inventoryArtifacts=inventories,inventoryRevision=None,deliveryAuthorization=None,repositories=repositories,rows=rows),writes


def authority_bytes(root,path):
    if path == MODULES['projects']['old']:
        return predecessor_bytes(root,'projects')
    data = (root/path).read_bytes()
    # .gitattributes canonicalizes tracked C# to LF blobs and checks out CRLF.
    return data.replace(b'\r\n',b'\n') if path.suffix == '.cs' else data


def packet(root):
    SOURCES.clear()
    writes = {m['new']:candidate(root,n) for n,m in MODULES.items()}
    artifacts = {str(p):sha(authority_bytes(root,p)) for p in AUTHORITIES}
    artifacts.update({str(p):sha(data) for p,data in writes.items()})
    amendments = []
    for module,m in MODULES.items():
        old = parse(predecessor_bytes(root,module).decode('utf-8'),module)
        new = parse(writes[m['new']].decode(),module)
        amendments.append(dict(module=module,fromPath=str(m['old']),fromVersion='2.0.0' if module=='projects' else '1.0.0',fromSha256=artifacts[str(m['old'])],
                               toPath=str(m['new']),toVersion=m['version'],toSha256=artifacts[str(m['new'])],
                               changedRows=[dict(id=k,fromSha256=sha(r['text'].encode()),toSha256=sha(new[k]['text'].encode())) for k,r in old.items()],addedRows=[],removedRows=[]))
    blob(root,'projects',PACKAGE)
    blob(root,'projects',CLOSURE)
    register,labels = label_candidate(root,{str(m['new']):artifacts[str(m['new'])] for m in MODULES.values()})
    receipt = dict(schemaVersion='1.0.0',decision='pending',baselineCommit=BASELINE,sourceRevisions={n:m['pin'] for n,m in MODULES.items()},
                   supersedes=['A1','Projects 2.0.0 session decision'],requiredApprovalRoles=ROLES,
                   rolesPolicy='Single maintainer may cover the named roles explicitly; no role coverage is inferred from session approval.',
                   artifacts=artifacts,pinnedArtifacts=dict(sorted(SOURCES.items())),amendments=amendments,limits=LIMITS)
    writes.update(labels)
    writes[E/'approval.json'] = (json.dumps(receipt,indent=2)+'\n').encode()
    writes[E/'labels.json'] = (json.dumps(register,indent=2)+'\n').encode()
    return writes


def main(argv=None):
    try:
        approval,labels = ROOT/E/'approval.json',ROOT/E/'labels.json'
        initial_receipts = {p:p.read_bytes() if p.exists() else None for p in [approval,labels]}
        require(not any((ROOT/m['new']).exists() for m in MODULES.values()) or approval.exists() and labels.exists(),
                'refusing to overwrite existing successor without approval and label receipts')
        if approval.exists(): require(read_json(approval).get('decision') == 'pending','refusing to overwrite approved or unknown-state packet')
        if labels.exists():
            register = read_json(labels)
            require(register.get('state') == 'candidate-pending-owner-approval-and-delivery' and register.get('deliveryAuthorization') is None
                    and register.get('inventoryRevision') is None and all(r.get('integration') is None for r in register.get('repositories',[])),
                    'refusing to overwrite authorized, integrated or unknown-state labels')
        writes = packet(ROOT)
        for path in writes:
            destination = ROOT/path
            require(not any(p.is_symlink() for p in [destination,*destination.parents] if p.is_relative_to(ROOT)),f'refusing symlink output destination: {path}')
        for path,initial in initial_receipts.items():
            require((path.read_bytes() if path.exists() else None) == initial,
                    'refusing to overwrite receipt changed during packet derivation: '+path.name)
        for path,data in writes.items():
            (ROOT/path).parent.mkdir(parents=True,exist_ok=True)
            (ROOT/path).write_bytes(data)
    except (ValueError,KeyError,TypeError,OSError,IndexError,UnicodeError) as error:
        print(f'FAIL: {error}',file=sys.stderr)
        return 1
    print('Prepared Projects 2.1.0 and FrontComposer 1.1.0 pending candidates; PS03/PS04/PS08/PS09 README-only patches; approval and delivery pending.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
