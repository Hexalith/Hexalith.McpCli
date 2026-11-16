#!/usr/bin/env python3
"""Derive pending inventories and README-only patches from frozen bytes and Git objects."""
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
E = ART/'evidence/story-5-10'
AD = Path('_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22')
BASELINE = '979e1e126c6d7010997f4f20b2bb3defae81333e'
SPEC = ART/'spec-5-10-refresh-and-re-disposition-chatbot-and-memories-inventories.md'
APPROVAL = '[A2](#a2-amendment-approval-pending)'
MODULES = {
    'chatbot': dict(title='ChatBot', version='1.1.0', old=ART/'chatbot-migration-inventory-v1.md',
                    new=ART/'chatbot-migration-inventory-v1.1.0.md', map=ART/'chatbot-migration-inventory-v1.md',
                    pin='6a4ca07b18e9b58500dc79dfede1f308da36c828', oldpin='acc934599cf1efff36b0643eddc6a3cc4c2978d5'),
    'memories': dict(title='Memories', version='1.1.0', old=ART/'memories-migration-inventory-v1.md',
                     new=ART/'memories-migration-inventory-v1.1.0.md', map=ART/'memories-migration-inventory-v1.md',
                     pin='9d87500eaf4c39ce0cec0cb3a03e5dd62c167106', oldpin='f6b60d5a2e9b81d84fddad789c7d9bed40d3a533'),
}
OLD_SOURCE_PIN = '839aee31e2a9be11feab3fb726006bb4c2f890b5'
OLD_SOURCE_TREE = 'src'
EXTRA = ['Capability class', 'Adopted outcome', 'Amendment disposition', 'Amendment coverage',
         'Amendment rationale or gap', 'Amendment owner', 'Exact replacement', 'Pinned evidence', 'Drift']
ROLES = ['ChatBot owning maintainer', 'ChatBot Contracts/handler/admission/security maintainer',
         'Memories owning maintainer', 'Memories Contracts/handler/identity/security maintainer',
         'Memories operator-tooling/custody maintainer', 'EventStore/Gateway admission maintainer',
         'McpCli product/architecture owner', 'McpCli contract/transport/security maintainer',
         'McpCli dependency/Catalog and conformance maintainer', 'Platform architecture/security maintainer']
LIMITS = ['Disposition authority only; no enrollment, publication, execution, parity or retirement authority.',
          'Exact-byte owner approval and separate explicit delivery authorization are independent gates.',
          'No commit, push, merge or upstream checkout write is authorized by this packet.']
AUTHORITIES = [m['old'] for m in MODULES.values()] + [
    AD/'AD-23-non-gateway-capability-classes.md', AD/'AD-23-capability-class-map.json',
    ART/'evidence/story-5-2/approval.json', ART/'evidence/story-5-2/main-integration.json',
    ART/'technical-tools-migration-inventory-v1.0.3.md',
    *[ART/f'evidence/story-5-{story}/{name}.json' for story in [7,8,9] for name in ['approval','labels']],
    Path('Directory.Build.props'), Path('tools/dependency-policy.json'),
    Path('src/Hexalith.McpCli/Hexalith.McpCli.csproj')]
IDENTITY = {'M01','M02','M03','M04','V01','V02','V03'}
HTTP_GATE = ('The HTTP release with forwarded per-user identity is necessary but insufficient: '
             'prove authenticated tenant and user authorization, administrative scope, semantic behavior, '
             'selected-environment denials, release and rollback evidence before retirement; actor/tenant strings grant no authority.')
CONTEXT_GATE = ('Task and correlation context travel only as Payload properties, declared actorProperty or allowed Envelope extensions; '
                'Queries have no extension channel. Plain Commands, REST DTOs and OpenAPI are legacy evidence, never decorated Gateway readiness.')
TOOL = 'tools/MigrateEmbeddingVectors/Program.cs'
SERVICE = 'src/Hexalith.Memories.Server/Migration/EmbeddingVectorMigrationService.cs'
EXITS = 'src/Hexalith.Memories.Server/Migration/EmbeddingMigrationExitCodes.cs'
PS14_HEADERS = ['ID','Legacy surface','Effect','Security class','Tenant rule','Confirmation and refusal',
                'Direct access and authority','Exit codes','Plan and custody','Disposition','Coverage','Approval']
WRITES = {'M02','M03','M04','M05','M08','M09','M10','L02','L03','L04','L05','L08','L09','L10','V07','V08','G2','G3','G4','G5'}
EXECUTION = ('Retained write/provider/dispatcher code is not currently executable through the pinned admission pipeline: '
             'ValidateAtomicParticipationAsync always returns canonical_execution_unavailable after earlier checks, before reservation/dispatch; '
             'the public refusal is nonretryable HTTP 503. Provider/pre-submit effects describe retained implementation, not current successful writes; '
             'accepted atomic owner participation remains a module gap.')
AUTHENTICATION = ('Authentication drift: the ChatBot route boundary now calls scheme-bound CreateHumanPolicy, requiring a human bearer '
                  'and rejecting workload/channel and mixed-credential principals. Unconfigured JWT authentication still registers the bearer '
                  'scheme with no issuer/signing key, authenticates nothing and returns typed authentication denial.')
STATUS = ('Status drift: OperationStatusHttpResults requires valid canonical metadata and known lifecycle/execution/projection/reason fields; '
          'malformed metadata becomes failed/generic_denial with dismiss-only actions and cleared sensitive outcome/retry metadata. '
          'CanonicalRevision-bearing status never grants public retry eligibility; no canonical retry profile is approved.')
OWNED_IDS = ('Identity drift: NewUnitId qualifies Guid.NewGuid().ToString() through UnitOwnershipAuthority.Qualify as '
             'owned-<generation>-<guid> when a validated ownership generation is configured. Unconfigured GUIDs and historical identifiers '
             'retain their exact forms; workflow and memory-unit identifiers are distinct, with no ULID inference or silent conversion.')
VISIBILITY = ('Read visibility drift: managed-source native search filtering hides staged/superseded candidates; '
              'the current source pointer rechecks every returned search axis and refuses an incomplete changed window. '
              'For managed sources, graph paths and returned neighbor edges exclude unpublished source versions; publication epochs reject overlapping snapshots.')
WINDOWS = ('Ranking/paging drift: syntactic search selects raw windows ordered by BM25 score descending then unique Redis key ascending '
           'before hydration. Raw total counts/offsets remain distinct from returned documents: invalid/stale documents consume raw positions. '
           'Incomplete ordered windows, missing/duplicate/substituted hydration keys, missing completion profiles or execution warnings/timeouts '
           'fail instead of claiming exhaustion or a complete result/count; native-filtered pointer changes also refuse the page.')
WORKLOAD = ('Gateway composition drift: the package fallback configures fixed-domain workload authority for memories-tenants and refuses '
            'case/unit operations. Only HEXALITH_EVENTSTORE_MULTI_DOMAIN_WORKLOAD enables all three exact domains and SubmitBoundWorkloadCommandAsync '
            'with an exact command/principal proof; absent/blank proof fails closed. Neither branch forwards user authority, and admission is not uniform across builds.')
ROW_NOTES = {
    **{('chatbot',k):EXECUTION for k in WRITES},
    **{('chatbot',k):AUTHENTICATION for k in ['V01','V03']},
    **{('chatbot',k):STATUS for k in ['M11','L11','V10']},
    ('memories','V06'):OWNED_IDS,
    **{('memories',k):VISIBILITY for k in ['M01','M03','L03','V04','V07']},
    ('memories','V05'):WINDOWS,
    **{('memories',k):WORKLOAD for k in ['V08','G3']},
}
ROW_NOTES[('memories','V04')] += ' '+WINDOWS
SOURCES, RAW = {}, {}

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

def compatibility_section(data):
    lines = data.decode('utf-8').splitlines(keepends=True)
    starts = [i for i,l in enumerate(lines) if l.rstrip('\r\n') == '## Legacy compatibility surfaces']
    require(len(starts) == 1,'README must have exactly one compatibility section')
    start = starts[0]
    end = next((i for i in range(start+1,len(lines)) if lines[i].startswith('#')),len(lines))
    return ''.join(lines[start:end]).encode()

def parse(text, module):
    rows, headers = {}, []
    for line in text.splitlines():
        if not line.startswith('|'):
            headers = []
            continue
        cells = [c.strip() for c in re.split(r'(?<!\\)\|',line)[1:-1]]
        if cells and cells[0] in {'ID','Gate','Gap'}:
            headers = cells
        elif cells and re.fullmatch(r'(?:[MLVSXT]\d{2}|G\d+)',cells[0]):
            key = cells[0]
            require(key not in rows, f'{module}:{key}: duplicate entry')
            require(headers and len(cells) == len(headers) and all(cells), f'{module}:{key}: damaged row or empty cell')
            rows[key] = dict(cells=cells, headers=headers[:], text=line)
    return rows


def class_entries(root, module):
    mapping = read_json(root/AD/'AD-23-capability-class-map.json')
    inv = next(i for i in mapping['inventories'] if i['path'] == str(MODULES[module]['map']))
    entries = {r['id']:r.get('classId','governance') for r in inv['rows']+inv['records']}
    if module == 'memories': entries.update({f'T{i:02d}':'K14' for i in range(1,5)})
    return entries, {c['id']:c['outcome'] for c in mapping['classes']}


def decision(module, key, klass):
    return 'withdraw' if klass in {'K07','K12','K14','K15'} else 'defer'


def owner(module, klass):
    name = MODULES[module]['title']
    if klass == 'K09': return name+' owning maintainer; McpCli product/architecture owner'
    if klass == 'K10': return name+' owning/security maintainer; McpCli product owner'
    if klass == 'K14': return 'Memories owning and operator-tooling/custody maintainers'
    return name+' owning and Contracts/handler/admission/security maintainers'


def rationale(module, key, klass):
    name = MODULES[module]['title']
    if klass == 'K12':
        why = ('Owner rationale: restriction precedence excludes confirmation-required, destructive, erasure and key-rotation variants '
               'from the public agent surface. Replacement experience: confidential Web/Chatbot UI for supported operations; '
               'unsupported erasure/key-rotation variants remain absent. Accepted loss: legacy agent confirmation and restricted-operation '
               'conveniences for this row. Confidential-UI coverage evidence, including authority/confirmation, applicable retention/key-shred/'
               'tombstone/WORM and safe audit/effect proof, is required before retirement; deletion success is not erasure proof.')
    elif klass == 'K07':
        why = ('Owner rationale: withdraw absent MCP resources/prompts from migration scope; none are registered at the pin. '
               'Replacement experience: package documentation, README and AI.Tools. Accepted loss: resource URIs, Markdown rendering, '
               'subscriptions, prompts and schema negotiation conventions; no business Query or existing resource is invented.')
    elif klass == 'K15':
        why = ('Owner rationale: withdraw the legacy local configuration, stub, wizard, parser or output convention recorded in this row. '
               'Replacement experience: generic McpCli invocation/profiles/JSON and owner-held documentation, with supported business '
               'operations remaining separately deferred. Accepted loss: this row\'s local convenience and legacy output/exit dialect, '
               'including unimplemented advertised leaves; no automatic credential copying or silent format conversion.')
    elif klass == 'K14':
        why = ('Owner rationale: withdraw only from McpCli migration scope under merged AI.Tools plan 1.2.0. Replacement experience: '
               'retained owner-held MigrateEmbeddingVectors local operator tooling with independent tenant/credential/custody, blue/green, '
               'rollback/abort and audit safety gates. Accepted loss: McpCli coverage of this mode; no operator capability is removed. '
               'Retained; never counted retired; --yes grants no agent authority.')
    elif key.startswith('G'):
        gates = {
            ('chatbot','G1'): 'Exact-byte owning-maintainer approval is satisfied only by the recorded approved receipt and explicitly covered roles; it is pending now, and supersedes A1 only when recorded.',
            ('chatbot','G2'): 'Module admission/relay must bind tenant, actor, referenced-owner authority, enriched/compound dispatch and replay/concurrency; admission-evidence validation exists but establishes no cross-head proof.',
            ('chatbot','G3'): 'No decorated module Contracts type exists; publish exact Commands/Queries with handler/admission, wire/domain/aggregate/projection routing and identifier policy.',
            ('chatbot','G4'): 'Exact published allowed package closure, Catalog coverage and both-head authorization/semantic conformance remain absent.',
            ('chatbot','G5'): 'Compatibility release, selected-environment behavior, other server/UI/API consumers and release/rollback evidence remain open; retirement is unapproved.',
            ('memories','G1'): 'No decorated Contracts type exists; owner must publish exact Commands/Queries, identifier declarations and real handler/admission routes without referencing the EventStore implementation package.',
            ('memories','G2'): 'Tenant/user membership, subject and content authority, administrative scope, actor/provenance/correlation binding and selected-environment denials remain unproved; workload credentials do not forward user authority.',
            ('memories','G3'): 'Gateway workload authority exists without forwarding user credentials; exact routes, module side effects, external projection scheduling, workflow receipts/status and dedup remain owner work.',
            ('memories','G4'): 'AD-23 now adopts K09/K10 deferral, K12 confidential UI, K15 withdrawal and K14 retained exemption; class decisions alone prove no UI coverage, authority, semantics or retirement.',
            ('memories','G5'): 'Exact published decorated package, allowed closure, enrollment and built Catalog snapshots remain absent; dependency-free undecorated Contracts is insufficient.',
            ('memories','G6'): 'Exact-byte owning-maintainer approval is satisfied only by the recorded approved receipt and covered roles, pending now; conformance, selected-environment semantics/authorization and release/rollback retirement gates remain open.',
        }
        why = 'Open gap: '+gates[(module,key)]
    elif klass == 'K09':
        why = ('Open gap: AD-23 K09 requires a generic authenticated out-of-band staging/stream/file transport, versioned declarations, '
               'content/lease/size/cleanup lifecycle, authority, audit and conformance, an admitting Platform AD under AD-14 and approved PRD change; '
               +name+' Contracts/handler/admission gaps remain. Retain compatibility support.')
    elif klass == 'K10':
        why = ('Open gap: AD-23 K10 requires approved shared HTTP transport and forwarded per-user authority under AD-14 token exchange, '
               'actor/effective-origin attestation, issuer/audience/client mapping and selected-environment denial evidence; no raw user-token forwarding. '
               +name+' Contracts/handler/admission and security owners must prove equivalent authority.')
    else:
        why = ('Open gap: no exact decorated '+name+' Contracts replacement type, handler and admission route at the pin; '
               'module owner must declare wire/domain/aggregate/projection routing, identifier kind and safe result/error semantics, '
               'then prove authorization and behavior through both generic heads. Existing plain Commands and REST DTOs provide no readiness.')
        if klass == 'K05':
            why += (' Module-side provider egress and pre-submit authority, workflow enrichment and external effects must be retained; '
                    'approval/proposal versions remain Payload concurrency inputs, never transport authority.')
        if module == 'chatbot' and key == 'V10':
            why += (' OperationId now precedes TaskId and CommandId in both formatters, and the server sets OperationId = CommandId; '
                    'this fixes the upstream handle drift but no decorated status Query exists. Preserve command-accepted, '
                    'accepted-projection-pending and audit-reconciling distinctions; acceptance never proves completion; '
                    'TaskId is not ownership proof, and authoritative retry-progress/post-commit audit and wrong-tenant/rebound-handle denials remain open.')
        if module == 'memories' and key in {'L01','L13'}:
            why += ' Deployment-wide unscoped metadata at the pin; no checked admin-role or caller-tenant filtering claim.'
    if module == 'chatbot' and decision(module,key,klass) == 'defer': why += ' '+CONTEXT_GATE
    if module == 'memories' and decision(module,key,klass) == 'defer':
        why += ' '+HTTP_GATE if key in IDENTITY else ' G2 remains open: '+HTTP_GATE
    if (module,key) in ROW_NOTES: why += ' '+ROW_NOTES[(module,key)]
    return why


def replacement(module, key, klass):
    if klass == 'K12': return 'Confidential Web/Chatbot UI with coverage evidence before retirement; unsupported variants remain absent.'
    if klass == 'K14': return 'Retained owner-held local MigrateEmbeddingVectors mode under AI.Tools plan 1.2.0; never counted retired.'
    if klass == 'K07': return 'Package documentation, README and AI.Tools; no MCP resources/prompts.'
    if klass == 'K15': return 'Generic McpCli invocation/profiles/JSON or owner documentation; accepted legacy convenience loss.'
    return 'None: no exact decorated Gateway replacement at the pin; owner gap remains open.'


def expand(module,path):
    if path.startswith(('Mcp/','Cli/','Contracts/','Server/','Client/','EventStore/')):
        name,rest = path.split('/',1)
        suffix = 'Client.Rest' if module == 'memories' and name == 'Client' else name
        return f'src/Hexalith.{MODULES[module]["title"]}.{suffix}/{rest}'
    return path


def old_anchors(row,module):
    result, last = [],None
    for token in re.findall(r'`([^`]+)`',row['text']):
        match = re.fullmatch(r'(.+):(\d+)',token)
        if match: last,number = expand(module,match[1]),int(match[2])
        elif re.fullmatch(r':\d+',token) and last: number = int(token[1:])
        else: continue
        result.append((last,number))
    return result


def predecessor_anchors(root,module,row):
    result = []
    for path,number in old_anchors(row,module):
        before = source(root,module,path,MODULES[module]['oldpin']).splitlines()
        require(0 < number <= len(before),f'{module}: invalid predecessor anchor {path}:{number}')
        after = source(root,module,path).splitlines()
        # Sequence alignment preserves the original statement's context when repeated.
        for tag,a,b,c,d in difflib.SequenceMatcher(None,before,after,autojunk=False).get_opcodes():
            if tag == 'equal' and a <= number-1 < b:
                current = c+number-a
                if after[current-1].strip(): result.append(f'{path}:{current}')
                break
    return list(dict.fromkeys(result))


def semantic_evidence(root,module,key):
    groups = [
        ('chatbot',WRITES,[
            ('Server/Gateway/Admission/ChatBotAdmissionEvidenceValidator.cs','return ValueTask.FromResult<string?>(ChatBotMessageCodes.CanonicalExecutionUnavailable)'),
            ('Server/Gateway/ChatBotCommandAdmissionPipeline.cs','string? atomicFailure ='),
            ('Server/Gateway/ChatBotCommandAdmissionPipeline.cs','.RecordAdmissionAsync(context'),
            ('Server/Gateway/ChatBotProblemDetailsFactory.cs','public ProblemDetails CreateCanonicalExecutionUnavailable')]),
        ('chatbot',{'V01','V03'},[
            ('Server/Authentication/ChatBotApplicationBoundaryPolicy.cs','EventStoreHttpHostSecurityExtensions.CreateHumanPolicy()'),
            ('Server/Authentication/ChatBotJwtAuthentication.cs','if (!IsConfigured(configuration))')]),
        ('chatbot',{'M11','L11','V10'},[
            ('Server/Gateway/Status/OperationStatusHttpResults.cs','bool validCanonicalMetadata ='),
            ('Server/Gateway/Status/OperationStatusHttpResults.cs','RetryEligible = knownReason && record.CanonicalRevision is null'),
            ('Server/Gateway/Status/OperationStatusHttpResults.cs','LifecycleState = knownReason ? record.LifecycleState : LifecycleState.Failed')]),
        ('memories',{'V06'},[
            ('Server/Ingestion/IngestionWorkflowConfigurationCapture.cs','internal string NewUnitId()'),
            ('Server/Ingestion/UnitOwnershipAuthority.cs','internal static string Qualify('),
            ('Server/Ingestion/UnitOwnershipAuthority.cs','internal static void ValidateConfiguration(')]),
        ('memories',{'M01','M03','L03','V04','V07'},[
            ('Server/Ingestion/SourcePublicationVisibility.cs','internal static async Task<string> FilterQueryAsync'),
            ('Server/Ingestion/RefreshPublicationStore.cs','internal async Task<IReadOnlyList<ScoredResult>> FilterAsync'),
            ('Server/Ingestion/RefreshPublicationStore.cs','internal async Task<SearchResult> FilterResultAsync'),
            ('Server/Ingestion/GraphSourcePublication.cs','internal const string NativeFilter'),
            ('Server/Graph/GraphQueryBuilder.cs','neighborPublication.currentId=m.id'),
            ('Server/Ingestion/GraphPublicationReadGate.cs','internal static async Task EndAsync')]),
        ('memories',{'V04','V05'},[
            ('Server/Search/SyntacticSearchService.cs','"SORTBY", 4, "@__score", "DESC", "@__key", "ASC"'),
            ('Server/Search/SyntacticSearchService.cs','if (orderedKeys.LongLength != expectedRows)'),
            ('Server/Search/SyntacticSearchService.cs','ValidateHydratedKeys(hydrated, orderedKeys)'),
            ('Server/Search/SyntacticSearchService.cs','private static async Task<RedisResult> ExecuteCompleteQueryAsync'),
            ('Server/Search/SyntacticSearchService.cs','// Check raw identities before required-field filtering.')]),
        ('memories',{'V08','G3'},[
            ('Server/Hosting/MemoriesServerServiceCollectionExtensions.cs','.AddEventStoreGatewayWorkloadTransport(MemoriesDomain.Tenants,'),
            ('Server/Hosting/MemoriesServerServiceCollectionExtensions.cs','.AddEventStoreGatewayMultiDomainWorkloadTransport('),
            ('Server/EventStoreIntegration/EventStoreMemoriesCommandStore.cs','if (string.IsNullOrWhiteSpace(proof))'),
            ('Server/EventStoreIntegration/EventStoreMemoriesCommandStore.cs','SubmitBoundWorkloadCommandAsync(bound, proof')]),
        ('memories',{'T02'},[
            ('Server/Migration/RedisEmbeddingMigrationStore.cs','public async Task CutoverStagingSemanticIndexesAsync('),
            ('Server/Migration/RedisEmbeddingMigrationStore.cs','transaction.ExecuteAsync("FT.ALIASUPDATE", rawActiveAlias'),
            ('Server/Migration/RedisEmbeddingMigrationStore.cs','await SetEmbeddingConfigAsync(tenantId, targetConfig, forceReindex: false, ct)'),
            ('Server/Migration/EmbeddingVectorMigrationService.cs','await store.CompleteMigrationMarkerAsync(tenantId, targetConfig, lease')]),
    ]
    result=[]
    if module == 'chatbot' and key in WRITES:
        path=expand(module,'Server/Gateway/ChatBotProblemDetailsFactory.cs')
        text=source(root,module,path)
        start=text.index('public ProblemDetails CreateCanonicalExecutionUnavailable')
        block=text[start:].split('public ProblemDetails CreateDependencyUnavailable',1)[0]
        for needle in ['Status = StatusCodes.Status503ServiceUnavailable','Retryable = false']:
            require(needle in block,f'chatbot:{key}: canonical execution refusal semantic content changed')
            result.append(path+':'+str(text.count('\n',0,start+block.index(needle))+1))
        path=expand(module,'Server/Gateway/ChatBotCommandAdmissionPipeline.cs')
        text=source(root,module,path)
        require(text.index('string? atomicFailure =') < text.index('.RecordAdmissionAsync(context'),
                f'chatbot:{key}: atomic refusal must precede reservation')
    for owner,keys,items in groups:
        if owner == module and key in keys:
            result.extend(anchor(root,module,expand(module,path),needle) for path,needle in items)
    return result


def evidence(root,module,key,row):
    result = predecessor_anchors(root,module,row) if row else []
    if key.startswith('G'):
        result += [anchor(root,module,f'src/Hexalith.{MODULES[module]["title"]}.Contracts/Hexalith.{MODULES[module]["title"]}.Contracts.csproj','<Project'),
                   anchor(root,module,'_bmad-output/planning-artifacts/epics.md','McpCli' if module == 'chatbot' else 'per-user identity path')]
    if module == 'chatbot':
        extras = {
            'V10':[('Mcp/ChatBotMcpResultFormatter.cs','response.OperationId'),('Cli/ChatBotCliOutputFormatter.cs','response.OperationId'),('Server/Gateway/CommandGateway.cs','OperationId = submission.Request.CommandId')],
            'V08':[('Contracts/Serialization/CommandOperationConcurrencyJsonConverter.cs','class CommandOperationConcurrencyJsonConverter')],
            'V11':[('Contracts/Messages/ChatBotMessageCodes.cs','public static class')],
        }
        if key in {'M11','M12','L11','L12','V12'}:
            path = 'src/Hexalith.ChatBot.Contracts/openapi/hexalith.chatbot.v1.yaml'
            text = source(root,module,path)
            if key == 'V12':
                needle = '    TaskIntentAvailableTransition:\n'
                block = text.split(needle,1)[1].split('    TaskIntentReviewSourceMessage:',1)[0]
                require('actorId' not in block and 'requiresPredecessorTaskIntentId:' in block,
                        'chatbot:V12: transition schema semantic content changed')
                result.append(anchor(root,module,path,needle))
            else:
                operation = 'GetOperationStatus' if key in {'M11','L11'} else 'GetOperationAuditHistory'
                needle = '      operationId: '+operation+'\n'
                require(text.count(needle) == 1,f'chatbot:{key}: OpenAPI operation not unique')
                start = text.index(needle)
                block = text[start:].split('\n  /',1)[0]
                schema = '$ref: "#/components/schemas/CommandId"'
                require(schema in block and 'tenantAuthority: authenticated-context' in block,
                        f'chatbot:{key}: status/audit schema or authority semantic content changed')
                result += [anchor(root,module,path,needle),path+':'+str(text.count('\n',0,start+block.index(schema))+1)]
        if key in {'M02','M03','M04','M05','M08','M09','M10','L02','L03','L04','L05','L08','L09','L10','G2','V11'}:
            result.append(anchor(root,module,'src/Hexalith.ChatBot.Server/Gateway/Admission/ChatBotAdmissionEvidenceValidator.cs','class ChatBotAdmissionEvidenceValidator'))
        for path,needle in extras.get(key,[]): result.append(anchor(root,module,expand(module,path),needle))
    else:
        if key in {'V01','V02','V15'}: result.append(anchor(root,module,expand(module,'Mcp/McpCompositionRoot.cs'),'ValidAlgorithms'))
        if key in {'M02','L06','V06'}: result.append(anchor(root,module,expand(module,'Server/Endpoints/IngestionEndpoints.cs'),'EnsureAdmissionOpenAsync'))
        if key in {'M01','M03','L03'}:
            path = 'GraphEndpoints.cs' if key == 'M03' else 'SearchEndpoints.cs'
            result.append(anchor(root,module,expand(module,'Server/Endpoints/'+path),'SOURCE_PUBLICATION_CHANGED'))
        if key in {'G2','G3','V08'}: result.append(anchor(root,module,expand(module,'Server/Hosting/MemoriesServerServiceCollectionExtensions.cs'),'workload authority'))
        if key in {'L06','V10'}: result.append(anchor(root,module,expand(module,'Cli/Quickstart/PrerequisiteChecks.cs'),'11.0.100'))
        if key in {'V16','X06'}: result.append(anchor(root,module,expand(module,'Client/MemoriesClient.cs'),'GetSourceInventoryAsync'))
        if key == 'V17': result.append(anchor(root,module,expand(module,'Cli/Errors/ErrorMessageCatalog.cs'),'SOURCE_PUBLICATION_CHANGED'))
        if key.startswith('T'):
            mode = {'T01':'DryRun','T02':'Live','T03':'Rollback','T04':'Abort'}[key]
            for path,needle in [(TOOL,'selectedModes != 1'),(TOOL,'options.Interactive ='),(TOOL,'options.Mode is not'),
                                (TOOL,'ConnectionMultiplexer.ConnectAsync'),(TOOL,'new DaprClientBuilder'),
                                (TOOL,'HttpEndpoint = daprHttpEndpoint'),(SERVICE,'requires --tenant'),(SERVICE,'Mutation requires explicit confirmation'),
                                (SERVICE,'Task<EmbeddingMigrationResult> '+mode+'Async'),(EXITS,'public const int Success'),
                                ('docs/operations/embedding-providers.md','--dry-run')]:
                result.append(anchor(root,module,path,needle))
    result.extend(semantic_evidence(root,module,key))
    require(result,f'{module}:{key}: no current pinned anchor')
    return list(dict.fromkeys(result))


DRIFT = {
    'chatbot': {
        **{k:'server query handler gained four lines; same registered read' for k in ['M01','M06','M07']},
        **{k:'OpenAPI status/audit identifiers are CommandId-only; query handler anchors shift' for k in ['M11','M12','L11','L12']},
        **{k:'OpenAPI write responses add 422/409/503 fail-closed outcomes; admission-evidence validation added; dispatcher anchors shift' for k in ['M02','M03','M04','M05','M08','M09','M10','L02','L03','L04','L05','L08','L09','L10']},
        'V08':'concurrency converter tightened; module admission-evidence validation added',
        'V10':'MCP/CLI formatters now select OperationId, then TaskId, then CommandId; server OperationId = CommandId; no decorated status Query',
        'V11':'three new message codes and fail-closed write response statuses',
        'V12':'OpenAPI transitions drop actorId; local CLI/output convention stays K15',
        'G1':'A2 exact-byte owner receipt replaces session-only A1 only when recorded; currently pending',
        'G2':'admission-evidence validation added; trusted owner/tenant authority and cross-head proof remain open',
    },
    'memories': {
        **{k:'JWT ValidAlgorithms enforced; authentication anchors shift ten lines' for k in ['V01','V02','V15']},
        **{k:'ingest admission fence can return HTTP 409' for k in ['M02','V06']},
        **{k:'search/graph adds SOURCE_PUBLICATION_CHANGED fail-closed behavior' for k in ['M01','M03','L03']},
        **{k:'Gateway composition now declares workload authority without forwarding user credentials; EventStore project explicitly references EventStore.Contracts' for k in ['G2','G3','V08']},
        **{k:'quickstart prerequisite requires SDK 11.0.100; adapter command unchanged' for k in ['L06','V10']},
        **{k:'new ingestion-input/source-inventory/retry client methods have no CLI/MCP caller; adjacent completeness remains excluded' for k in ['V16','X06']},
        'V17':'CLI error catalog adds eight codes; output/exit conventions remain withdrawn',
        'G4':'AD-23 now adopted; K14 four-mode inventory added without executing operator tooling',
        'G6':'A2 exact-byte owner receipt replaces session-only A1 only when recorded; currently pending',
    },
}


def drift(root,module,key,row):
    if key.startswith('T'): return 'added: PS14 mode omitted from predecessor; source unchanged since the old pin.'
    details = []
    if key in DRIFT[module]: details.append(DRIFT[module][key])
    if (module,key) in ROW_NOTES: details.append(ROW_NOTES[(module,key)])
    before = [f'{p}:{n}' for p,n in old_anchors(row,module)]
    after = predecessor_anchors(root,module,row)
    if before != after: details.append('predecessor source anchors re-aligned to current statements; changed statements use semantic pinned evidence')
    return 'changed: '+'; '.join(details)+'.' if details else 'unchanged'


def ps14_rows():
    effects = [
        ('--dry-run','Read affected tenant configurations/counts/index metadata only; no writes; optional tenant filter otherwise enumerates tenants.'),
        ('--live','Acquire migration marker/lease; prepare blue/green indexes, regenerate raw/natural-language vectors, verify staging and cut over only after successful staging. Pre-cutover failures preserve active indexes; alias cutover precedes SetEmbeddingConfigAsync and later heartbeat/marker completion, so failures after cutover may leave active aliases changed with stale metadata/incomplete markers and require manual rollback or owner follow-up.'),
        ('--rollback','Acquire/resume marker lease and restore retained previous blue/green targets and tenant embedding configuration; unavailable state fails closed.'),
        ('--abort','Recover/resume marker lease and clean staging, or restore previous active targets if cutover began; failures fail closed.'),
    ]
    rows = {}
    for i,(mode,effect) in enumerate(effects,1):
        key = f'T{i:02d}'
        cells = [key,'`MigrateEmbeddingVectors '+mode+'`',effect,
                 'Owner-held local operator; deployment infrastructure/credential custody; no checked user or tenant authority.',
                 'Optional --tenant filter; absent means all registered tenants.' if i == 1 else 'Explicit nonblank --tenant required; missing tenant returns plumbing exit 2; selector grants no authority.',
                 'No --yes or interactive confirmation required for read-only dry-run; non-interactive dry-run allowed.' if i == 1 else '--yes or interactive y/yes required; redirected input without --yes refuses; declined prompt exits 2. --yes grants no agent authority.',
                 'Direct Redis connection (--redis/MEMORIES_REDIS) and Dapr client/actor HTTP (--dapr-http/DAPR_HTTP_ENDPOINT), no Gateway path; no explicit Dapr API token in tool code, no authenticated user/tenant authorization check. Infrastructure access is not caller authority.',
                 '0 success; 1 domain failure; 2 CLI/configuration/plumbing or confirmation refusal; 130 service cancellation. Unhandled resource-bootstrap failures have no mapped exit guarantee.',
                 'AI.Tools plan 1.2.0 K14; retained owner-held tooling; independent credential/custody, tenant, blue/green, rollback/abort and audit evidence; never counted retired.',
                 'withdraw','exclude',APPROVAL]
        rows[key] = dict(cells=cells,headers=PS14_HEADERS[:],text='| '+' | '.join(cells)+' |')
    return rows


def current_behavior(module,key,original):
    if module == 'chatbot' and key == 'V10':
        return ('Both MCP and CLI formatters prefer OperationId, then TaskId, then CommandId. Server acceptance sets OperationId = CommandId and carries TaskId separately. '
                'Status/audit OpenAPI handles are CommandId-only; acceptance, pending projection and audit reconciliation remain distinct. No decorated status Query exists.')
    if module == 'chatbot' and key in {'V07','V08'}:
        return 'Retained implementation (blocked before reservation/dispatch at this pin): '+original+' '+EXECUTION
    return original


def candidate(root,module):
    m = MODULES[module]
    old = parse(predecessor_bytes(root,module).decode(),module)
    rows = dict(old)
    if module == 'memories': rows.update(ps14_rows())
    entries,outcomes = class_entries(root,module)
    chunks = [f'''---
inventory_version: '{m['version']}'
status: pending
module: {module}
source_repository: 'https://github.com/Hexalith/Hexalith.{m['title']}'
source_revision: '{m['pin']}'
source_spec: '{SPEC}'
predecessor: '{m['old']}'
approval_ref: '#a2-amendment-approval-pending'
---

# {m['title']} migration inventory 1.1.0

Additive successor to immutable {m['title']} 1.0.0: every one of its {len(old)} entries
appears exactly once, including governance and adjacency records.'''+(' Four PS14 modes are added as T01–T04.' if module == 'memories' else '')+f'''
Source pin `{m['pin']}` is the approval-time root gitlink at `{BASELINE}`.
Only `git show <pin>:<path>` supplies module source evidence; working checkouts are not evidence.

## A2 Amendment approval pending

The [approval receipt](evidence/story-5-10/approval.json) establishes the effective
approval state for these exact bytes. It is pending. After exact-word "approve",
it records identity, date, source and explicitly covered roles under the
single-maintainer model, supersedes A1 and replaces the predecessor's `unasserted`
with only the roles it covers. No owning role is asserted by spec approval alone.
Delivery requires a separate exact-word "authorize" instruction. Nothing here
authorizes enrollment, publication, execution, parity, release acceptance or retirement.

## Amendment notation and preserved gates

AD-23 restriction precedence applies row by row. No type at this pin is decorated:
all Gateway-eligible K01/K03/K04/K05/K06 rows remain defer/exclude with module
Contracts/handler/admission gaps. K09/K10 remain deferred with their class gap and
owner. K07/K12/K15 withdrawals record owner rationale, replacement experience and
accepted loss under the spec's "Accept all" decision, subject to exact-byte approval.
K12 requires confidential-UI coverage evidence before retirement; unsupported
variants stay absent. Legacy behavior columns preserve finite scope, while the
amendment columns explicitly update dispositions, gaps and anchors and govern
any historical handoff wording retained in legacy behavior cells. No silent
format conversion is claimed. All compatibility binaries remain retained and
retirement gates remain open.

''']
    if module == 'chatbot':
        chunks.append('''The pin registers 12 tools (5 reads, 7 writes), 12 CLI leaves and no resources
or prompts. The historical unpublished acc93459 is not an ancestor; its src tree
is identical to published comparison 839aee31 (only .mcp.json changed).
The Contracts project is unchanged and has no McpCli decoration. Governed server
admission and workflow enrichment remain module responsibilities.
'''+CONTEXT_GATE+''' Acceptance never proves completion. The upstream V10 formatter
handle fix does not supply a decorated status Query or cross-head authority proof.

''')
    else:
        chunks.append('''The pin retains 4 tools, 14 implemented CLI leaves and 4 stubs. Mcp/Tools and
Cli/Commands are byte-identical to the predecessor pin; the Contracts project is
unchanged and has no decoration. Plain EventStore command records and REST/V1
DTOs are not Gateway-ready Contracts. Workload Gateway authority forwards no
user credentials. L01/L13 remain unscoped deployment metadata; no admin-role
check or caller-tenant filtering is asserted. G2 applies to every deferred row.
'''+HTTP_GATE+'''

PS14 is retained owner-held tooling under merged AI.Tools plan 1.2.0. Exactly one
mode is required; no mode is a Gateway/public-agent operation. Tool resources
connect before service option validation, so a refusal does not prove zero
infrastructure connections. --yes never grants agent authority. No mode was run.

''')
    previous = None
    for key,row in rows.items():
        klass = entries[key]
        d,coverage = decision(module,key,klass),'exclude'
        why = rationale(module,key,klass)
        cells,headers = row['cells'][:],row['headers'][:]
        for i,h in enumerate(headers):
            if h == 'Disposition': cells[i] = d
            elif h == 'Coverage': cells[i] = coverage
            elif h == 'Disposition / coverage': cells[i] = d+' / '+coverage
            elif h in {'Approval','Approval reference'}: cells[i] = APPROVAL
            elif h == 'Source evidence': cells[i] = 'See current Pinned evidence column.'
        if key.startswith('V'):
            cells[1] = current_behavior(module,key,cells[1])
            if module == 'memories' and key in {'V01','V02','V15'}:
                cells[3] += ' Current pin additionally enforces JWT ValidAlgorithms.'
            if module == 'memories' and key == 'V08':
                cells[3] += ' Current Gateway composition uses workload authority without forwarding user credentials.'
            if module == 'chatbot' and key == 'V10':
                cells[3] = rationale(module,key,klass)

        if module == 'memories' and key == 'V06':
            cells[3] = cells[3].replace('REST uses GUID workflow/file-memory identity; do not invent canonical ULID.',OWNED_IDS)
        if key.startswith('G'): cells[-1] = why
        ev = evidence(root,module,key,old.get(key))
        extra = [klass,outcomes.get(klass,'Scope accounting; no independent capability outcome'),d,coverage,why,owner(module,klass),
                 replacement(module,key,klass),'`'+'`; `'.join(ev)+'`',drift(root,module,key,old.get(key))]
        if headers != previous:
            section = {'M':'MCP tools','L':'Frozen CLI leaves','S':'Unsupported CLI stubs','V':'Compatibility and authority variants',
                       'X':'Adjacent and unsupported scope','G':'Retained prerequisites','T':'PS14 retained operator modes'}[key[0]]
            chunks += ['\n## '+section+'\n\n','| '+' | '.join(headers+EXTRA)+' |\n','| '+' | '.join(['---']*(len(headers)+len(EXTRA)))+' |\n']
        chunks.append('| '+' | '.join(cells+extra)+' |\n')
        previous = headers
    chunks.append('''
## Verification and retirement limits

[Story 5.10 verification](evidence/story-5-10/verification.md) establishes static
row accounting, class/disposition rules, pinned anchors/drift and hash bindings
only. It executes no legacy operation. Approval and PS06/PS07/PS12/PS13/PS14
label delivery remain independent completion gates. Protected predecessors,
AD-23, technical 1.0.3, earlier receipts/registers, production code, enrollment,
dependencies, census, gitlinks and AI.Tools plan remain unchanged. Story 5.11
indexes these successors and delivers the Admin/technical successors.
''')
    return ''.join(chunks).encode()


def label_candidate(root,inventories):
    prior_path = ART/'evidence/story-5-9/labels.json'
    rows_path = ART/'evidence/story-5-7/labels.json'
    prior = read_json(root/rows_path)
    repositories,rows,writes = [],[],{}
    for module,m in MODULES.items():
        registration = next(r for r in prior['repositories'] if r['name'] == module)
        before = blob(root,module,'README.md')
        text = before.decode()
        for row in [r for r in prior['rows'] if r['repository'] == module]:
            oldtext = row['label']['text']
            require(text.count(oldtext) == 1,row['id']+': prior label missing or duplicated at pin')
            new = re.sub(r'\['+m['title']+r' inventory 1\.0\.0\]\([^)]*\)',
                         f'[{m["title"]} inventory 1.1.0](https://github.com/Hexalith/Hexalith.McpCli/blob/main/{m["new"]})',oldtext)
            gate = row['gate']
            if row['id'] == 'PS14':
                gate = gate.replace('four-mode inventory and independent safety gates remain','T01–T04 four-mode inventory recorded; independent safety gates remain')
                new = new.replace(row['gate'],gate).replace('still require Story 5.10 operation accounting and independent','are recorded in T01–T04 and still require independent')
                new += f' [Memories inventory 1.1.0](https://github.com/Hexalith/Hexalith.McpCli/blob/main/{m["new"]}) T01–T04 records --dry-run, --live, --rollback and --abort; no mode is retired.'
            new += f' {m["title"]} inventory SHA-256: `'+inventories[str(m['new'])]+'`.'
            text = text.replace(oldtext,new)
            rows.append(dict(row,gate=gate,label=dict(file='README.md',line=text.splitlines().index(new)+1,text=new,sha256=sha(new.encode()))))
        after = text.encode()
        patch = ''.join(difflib.unified_diff(before.decode().splitlines(keepends=True),text.splitlines(keepends=True),fromfile='a/README.md',tofile='b/README.md',n=3)).encode()
        files = {'README.before.section.md':compatibility_section(before),'README.after.section.md':compatibility_section(after),'README.patch':patch}
        repository = dict(name=module,repository=registration['repository'],ownerCheckout=registration['ownerCheckout'],baseRevision=m['pin'],
                          readme=dict(beforeSha256=sha(before),afterSha256=sha(after)),integration=None)
        for key,name in [('before','README.before.section.md'),('after','README.after.section.md'),('patch','README.patch')]:
            path = E/'upstream'/module/name
            repository[key] = dict(path=str(path),sha256=sha(files[name]))
            writes[path] = files[name]
        repositories.append(repository)
    return dict(schemaVersion='1.0.0',state='candidate-pending-owner-approval-and-delivery',
                predecessor=dict(path=str(prior_path),sha256=sha((root/prior_path).read_bytes())),
                priorRows=dict(path=str(rows_path),sha256=sha((root/rows_path).read_bytes())),
                inventoryArtifacts=inventories,inventoryRevision=None,deliveryAuthorization=None,repositories=repositories,rows=rows),writes


def authority_bytes(root,path):
    return (root/path).read_bytes()


def preconditions(root):
    """Halt on changed approved gitlinks or an unfetched main divergence."""
    git(root,'merge-base','--is-ancestor','origin/main','HEAD')
    for module,m in MODULES.items():
        for revision in [BASELINE,'HEAD']:
            link = git(root,'ls-tree',revision,str(repo(module))).decode().split()[2]
            require(link == m['pin'],f'{module}: approval-time/HEAD root gitlink pin mismatch; halt')
        git(root/repo(module),'merge-base','--is-ancestor',m['pin'],'origin/main')


def packet(root):
    preconditions(root)
    SOURCES.clear()
    writes = {m['new']:candidate(root,n) for n,m in MODULES.items()}
    artifacts = {str(p):sha(authority_bytes(root,p)) for p in AUTHORITIES}
    artifacts.update({str(p):sha(data) for p,data in writes.items()})
    amendments = []
    for module,m in MODULES.items():
        old,new = parse(predecessor_bytes(root,module).decode(),module),parse(writes[m['new']].decode(),module)
        amendments.append(dict(module=module,fromPath=str(m['old']),fromVersion='1.0.0',fromSha256=artifacts[str(m['old'])],
                               toPath=str(m['new']),toVersion='1.1.0',toSha256=artifacts[str(m['new'])],
                               changedRows=[dict(id=k,fromSha256=sha(r['text'].encode()),toSha256=sha(new[k]['text'].encode())) for k,r in old.items()],
                               addedRows=[dict(id=k,toSha256=sha(r['text'].encode())) for k,r in new.items() if k not in old],removedRows=[]))
    ai_repo = Path('references/Hexalith.AI.Tools')
    ai_pin = git(root,'ls-tree',BASELINE,str(ai_repo)).decode().split()[2]
    for path in ['hexalith-llm-instructions.md','hexalith-mcpcli-migration-instructions.md']:
        data = git(root/ai_repo,'show',f'{ai_pin}:{path}')
        require(b'1.2.0' in data if 'migration' in path else b'MigrateEmbeddingVectors' in data,'AI.Tools merged exemption missing')
        SOURCES[f'{ai_repo}@{ai_pin}:{path}'] = sha(data)
    register,labels = label_candidate(root,{str(m['new']):artifacts[str(m['new'])] for m in MODULES.values()})
    receipt = dict(schemaVersion='1.0.0',decision='pending',baselineCommit=BASELINE,sourceRevisions={n:m['pin'] for n,m in MODULES.items()},
                   supersedes=['ChatBot 1.0.0 A1 session approval','Memories 1.0.0 A1 session approval'],requiredApprovalRoles=ROLES,
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
        def check_receipts():
            for path,initial in initial_receipts.items():
                require((path.read_bytes() if path.exists() else None) == initial,
                        'refusing to overwrite receipt changed during generation: '+path.name)
        check_receipts()
        # Snapshot rechecks catch observed approvals between our mutations. This
        # is not cross-process atomicity against arbitrary external writers.
        for path,data in writes.items():
            destination = ROOT/path
            if destination.exists() and destination.read_bytes() == data:
                continue
            check_receipts()
            destination.parent.mkdir(parents=True,exist_ok=True)
            check_receipts()
            destination.write_bytes(data)
            if destination in initial_receipts:
                initial_receipts[destination] = data
    except (ValueError,KeyError,TypeError,OSError,IndexError,UnicodeError) as error:
        print(f'FAIL: {error}',file=sys.stderr)
        return 1
    print('Prepared ChatBot 1.1.0 and Memories 1.1.0 pending candidates; PS06/PS07/PS12/PS13/PS14 README-only patches; approval and delivery pending.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
