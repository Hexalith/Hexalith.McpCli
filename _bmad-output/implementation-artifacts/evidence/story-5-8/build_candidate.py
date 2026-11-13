#!/usr/bin/env python3
"""Deterministically prepare the pending Folders successor and README-only patch.

All owner source is read with git show at canonical pins. Never write references,
owner checkouts, approved inventories, receipts, indices or remote refs.
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
E = ART / 'evidence/story-5-8'
AD = Path('_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22')
BASELINE = 'a92a2969db6903b8c6cca7e437446167e135ec9d'
PIN = '7eab70e9332c0573b50dce5b219e425b6a2d363c'
OLD_PIN = 'e2252f29a2dba2b64786ee483eb59fbceaadd387'
LABEL_PIN = '583d3d492f94217809a8efe00424b80ce3fdfa61'
REPO = Path('references/Hexalith.Folders')
OLD = ART / 'folders-migration-inventory-v1.md'
NEW = ART / 'folders-migration-inventory-v1.1.0.md'
SPEC = ART / 'spec-5-8-refresh-and-re-disposition-the-folders-inventory.md'
DECLARATIONS = 'docs/contract/mcpcli-folders-operation-declarations.md'
APPROVAL = '[A2](#a2-amendment-approval-pending)'
EXTRA = ['Capability class', 'Adopted outcome', 'Amendment disposition', 'Amendment coverage',
         'Amendment rationale or gap', 'Amendment owner', 'Exact replacement', 'Pinned evidence', 'Drift']
ROLES = ['Folders owning maintainer', 'Folders Contracts maintainer', 'Folders security maintainer',
         'Folders query/file/privacy/runtime maintainer', 'Folders provider maintainer',
         'EventStore/Gateway admission maintainer', 'McpCli product/architecture owner',
         'McpCli security and contract/transport maintainer', 'McpCli dependency/Catalog maintainer',
         'Platform architecture/security and platform/operator maintainer']
LIMITS = ['Disposition authority only; no execution, enrollment, publication, parity or retirement authority.',
          'Completion requires exact-byte owner approval and separate authorized upstream label integration.',
          'Commits, pushes and merges require separate explicit authorization.']
K12 = {'C01', 'C10', 'M01', 'M02', 'M04', 'M13', 'L10', 'L24', 'L25', 'L26'}
DIAGNOSTICS = {'Q04', 'Q06', 'Q10', 'Q12', 'Q15', 'Q17', 'Q20',
               'M18', 'M20', 'M24', 'M26', 'M29', 'M31', 'M34'}
AUTHORITIES = [OLD, AD / 'AD-23-non-gateway-capability-classes.md', AD / 'AD-23-capability-class-map.json',
               ART / 'evidence/story-5-2/approval.json', ART / 'evidence/story-5-2/main-integration.json',
               ART / 'technical-tools-migration-inventory-v1.0.3.md', ART / 'evidence/story-5-7/approval.json',
               ART / 'evidence/story-5-7/labels.json']
GAPS = {
 'G1': ('5.12', 'done', 'Decorated Contracts now exist (13 Commands, 28 Queries); AD-15 exact restored package/closure and Epic 6.1 Catalog acceptance remain open.', 'Folders Contracts and McpCli dependency/Catalog maintainers'),
 'G2': ('5.13', 'backlog', 'Verified tenant/actor authority, layered authorization, revocation, task/workspace/lease ownership, deny-before-access and zero unauthorized effects remain unproved.', 'Folders security and EventStore/Gateway admission maintainers'),
 'G3': ('5.13', 'backlog', 'Uppercase envelope ULIDs, independent caller-key replay/conflict/expiry/task association and command-payload-translation remain open; no silent identifier conversion. task-extension-profile and task-extension-trailing-double-hyphen remain explicit.', 'Folders command and EventStore/Gateway admission maintainers; McpCli enrollment/parity owner'),
 'G4': ('5.14', 'backlog', 'Three internal IDomainQueryHandler implementations and POST /query exist; none serves these 28 decorated types. Fixed freshness, payload/envelope paging precedence, filters, task context and tenant-wide-query-aggregate for Q16 remain open.', 'Folders query and McpCli contract/transport maintainers'),
 'G5': ('5.14', 'backlog', 'Real file/path/delete/context implementations now exist; the default commit executor remains unavailable. Metadata-only results/errors, redaction, read-file-range-window and configured live effects remain unproved.', 'Folders file/privacy/runtime maintainers'),
 'G6': ('5.10', 'backlog', 'Authorized provider egress, credential references, readiness/failure/reconciliation and reserved provider-binding actor/tenant namespace separation remain open; no module-specific REST fallback.', 'Folders provider and Platform/operator maintainers'),
}
VARIANTS = {
 'V01': ('replace', 'Fixed freshness is owned per Query in the 5.12 table, never silently ignored. G4 / Story 5.14 must prove default/omission and unsupported-value rejection; seven diagnostics remain deferred.', 'Folders query maintainer', 'Decorated Queries Q01–Q35 except Q04/Q06/Q10/Q12/Q15/Q17/Q20; each has fixed freshness; G1/G2/G4/G5 remain.'),
 'V02': ('replace', 'Typed cursor/limit/filter fields and eight exact payload_paging_member approval tuples exist. G4 / Story 5.14 must define authoritative payload/envelope precedence, reject conflicts and prove filter-before-page totals/continuations.', 'Folders query and McpCli contract/transport maintainers', 'Decorated paging/filter Queries Q16/Q27/Q28/Q29/Q30/Q31/Q33/Q34; G4 and Q16 tenant-wide-query-aggregate remain.'),
 'V03': ('replace', 'taskId is a required caller-chosen envelope extension on all 13 Commands; profile allowedExtensions must preserve existing keys and add taskId. Five Commands also carry Payload TaskId, reconciled by Story 5.13. Nine reads retain task scope in typed payloads; Q05 optional context; Q21 task ID is a route resource, not a fabricated task header. G2/G3/G4 remain.', 'Folders command/query and EventStore/Gateway admission maintainers; McpCli enrollment/parity owner', 'Decorated Commands C01–C13 (C01/C10 remain K12 deferred) and typed task-scoped Queries; no task-as-authority.'),
 'V04': ('withdraw', 'Owner accepts loss of local-file/stdin upload helper and derived evidence convenience under 5.12 for C10, M01/M04/M13 and L24–L26 (content input on add/change). Caller supplies inline content/media type/decoded byteLength/hashref/path/policy evidence; inclusive 262144-byte inline limit remains. C10 and its rows remain K12 deferred.', 'Folders owning maintainer', 'Caller-authored typed JSON; no local-file reading or automatic evidence derivation in McpCli.'),
 'V05': ('defer', 'K09 staged-content-above-inline: 262145–1048576 decoded bytes require a future generic authenticated staging/transport decision and configured live content store. Above inclusive 1048576 is invalid. REST multipart PutFileStream now exists but is outside the MCP/CLI surface and grants no generic readiness.', 'McpCli product/architecture owner and Platform/operator maintainer', 'No approved generic staging transport; retain compatible SDK/REST experience only.'),
 'V06': ('replace', 'G5 / Story 5.14 must preserve recursive contentBytes/inlineContent/streamDescriptor suppression, authorization-before-read, safe results/errors/diagnostics and metadata-only read-file-range. No future content-read authority is granted.', 'Folders privacy/runtime/query maintainers', 'Decorated operations with module-side metadata-only Gateway results; G2/G4/G5 remain.'),
 'V07': ('replace', 'Owner accepts loss of --allow-auto-key and sha256: hash-format sourcing for C01–C13, M01–M14 and mutation leaves L01/L05–L07/L10/L13–L14/L16–L18/L24–L27. Caller supplies canonical uppercase ULID; no generated replacement key or conversion. G3 / Story 5.13 preserves replay/conflict/expiry/task association independently of message identity.', 'Folders command and EventStore/Gateway admission maintainers', 'Required caller-owned canonical uppercase ULID idempotency key on every decorated Command; C01/C10 stay K12 deferred.'),
 'V08': ('replace', 'C08 grant / C13 revoke derive effect from exact wire identity. Reject caller-supplied effect via additionalProperties:false; Story 5.13 translates and validates authorized ACL inputs. No permission erasure equivalence. G2/G3 remain.', 'Folders authorization and EventStore/Gateway admission maintainers', 'Hexalith.Folders.Contracts.Commands.GrantFolderAccess / RevokeFolderAccess; folders domain; FolderId aggregate; exact routes in C08/C13.'),
 'V09': ('withdraw', '5.12 accepts loss of legacy credential precedence, human output and operational exits 64–77; 2026-11-13 owner decision additionally accepts legacy REST setup, stderr errors and internal/unmapped exit 1. All CLI L01–L42 and all legacy tools except diagnostics are affected. No credentials are copied and no legacy format is silently converted.', 'Folders owning maintainer and McpCli product/security maintainer', 'McpCli profiles, stdout JSON errors and operational exit 2; setup/result migration and secret-safe evidence remain required before retirement.'),
 'V10': ('withdraw', 'No implemented dry-run exists at either pin. Adopted K15 withdraws unsupported local conventions; no simulation parity or staging/REST effect is invented.', 'Folders owning maintainer', 'Documented McpCli JSON operation invocation; no dry-run replacement is claimed.'),
}
DRIFT_FIELDS = {
 **{key: 'ownerFileId/expectedFileVersion/expectedLockFence' for key in ['M01','M04','M13','L24','L25','L26','C10']},
 **{key: 'fileId/version' for key in ['M21','M41','M44','M47','R02','L32','L33','L34','L35']},
 **{key: 'lockFence' for key in ['M37','M40','L19','L22']},
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    def unique(pairs):
        result = {}
        for key,value in pairs:
            require(key not in result, f'duplicate JSON member {key}')
            result[key] = value
        return result
    value = json.loads(path.read_bytes(),object_pairs_hook=unique)
    require(isinstance(value,dict),f'JSON document must be an object: {path.name}')
    return value


def git(repo, *args):
    result = subprocess.run(['git', '-C', str(repo), *args], capture_output=True)
    if result.returncode:
        detail = result.stderr.decode(errors='replace').strip() or '(no stderr)'
        raise ValueError(f'git {" ".join(args)} failed: {detail}')
    return result.stdout


def load(root, name, path):
    spec = importlib.util.spec_from_file_location(name, root / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source(root, path, pin=PIN):
    return git(root / REPO, 'show', f'{pin}:{path}').decode()


def anchor(path, text, needle):
    if needle not in text:
        raise ValueError(f'pinned source missing {needle!r}: {path}')
    return f'{path}:{text.count(chr(10), 0, text.index(needle)) + 1}'


def declarations(root):
    result = {}
    for line in source(root, DECLARATIONS).splitlines():
        if re.match(r'^\| [CQ]\d{2} \|', line):
            cells = [c.strip().strip('`') for c in line.split('|')[1:-1]]
            key, eligibility, clr, wire, _, aggregate, _, freshness = cells
            kind, name = clr.split('.')[-2:]
            path = f'src/Hexalith.Folders.Contracts/{kind}/{name}.cs'
            if eligibility != 'eligible':
                path = DECLARATIONS
            text = source(root, path)
            decorated = '[Hexalith' + ('Command' if kind == 'Commands' else 'Query') + '('
            result[key] = dict(eligibility=eligibility, clr=clr, wire=wire, aggregate=aggregate,
                               freshness=freshness, path=path, source=text,
                               evidence=anchor(path, text, decorated if eligibility == 'eligible' else line),
                               ownerEvidence=anchor(DECLARATIONS, source(root, DECLARATIONS), line))
    return result


def surfaces(root, pin=PIN):
    """Re-discover exact Name declarations and CLI leaf/client links at the pin."""
    paths = git(root / REPO, 'ls-tree', '-r', '--name-only', pin, 'src').decode().splitlines()
    tools, resources, leaves = {}, {}, {}
    for path in paths:
        if '/Tools/' in path and path.endswith('.cs') and '.Mcp/' in path:
            text = source(root, path, pin)
            for match in re.finditer(r'\[McpServerTool\(Name = "([^"]+)"\)\]', text):
                if match[1] in tools:
                    raise ValueError('duplicate pinned MCP tool ' + match[1])
                tools[match[1]] = anchor(path, text, match[0])
        if '/Resources/' in path and path.endswith('.cs') and '.Mcp/' in path:
            text = source(root, path, pin)
            for match in re.finditer(r'\[McpServerResource\(\s*Name = "([^"]+)"\s*,\s*UriTemplate = "([^"]+)"', text):
                resources[(match[1], match[2])] = anchor(path, text, match[0])
    root_source = source(root,'src/Hexalith.Folders.Cli/CliApplication.cs',pin)
    registrations = re.findall(r'root\.Subcommands\.Add\(([^\n]+)\);',root_source)
    groups = []
    for registration in registrations:
        match = re.fullmatch(r'(\w+)Command\.Create\(pipeline, global\)',registration)
        require(match is not None and match[1] in {'Provider','Folder','Workspace','File','Commit','Context','Audit'},f'unaccounted pinned CLI root registration: {registration}')
        groups.append(match[1])
    require(len(groups) == len(set(groups)) and len(registrations) == root_source.count('root.Subcommands.Add('),'damaged or duplicate pinned CLI root registrations')
    upload = upload_operations(root,pin)
    for group in groups:
        path = f'src/Hexalith.Folders.Cli/Commands/{group}/{group}Command.cs'
        text = source(root, path, pin)
        prefixes = dict(command=group.lower(), acl='folder acl', branchPolicy='folder branch-policy', timeline='audit timeline')
        matches = list(re.finditer(r'(\w+)\.Subcommands\.Add\((CommandFactory\.\w+|\w+)\(\s*"([^"]+)"', text))
        for i, match in enumerate(matches):
            leaf = prefixes[match[1]] + ' ' + match[3]
            body = text[match.end():matches[i+1].start() if i+1 < len(matches) else len(text)]
            if group == 'File':
                require(match[2] == 'Upload','unsupported pinned file CLI registration')
                kind = re.match(r'\s*,\s*"[^"]*",\s*FileMutationRequestFileOperationKind\.(\w+)',body)
                require(kind is not None and kind[1] in upload,'unsupported pinned file CLI upload kind')
                operation = upload[kind[1]]
                helper = text.split('private static Command Upload(',1)[-1].split('private static Command Remove(',1)[0]
                require('FileOperationKind = kind' in helper and re.findall(r'client\s*\.\s*(\w+)Async\(',helper) == ['UploadFile'],'pinned file CLI upload helper/client link changed')
            else:
                calls = re.findall(r'client\s*\.\s*(\w+)Async\(',body)
                require(len(calls) == 1,f'unsupported pinned CLI client-call grammar: {leaf}')
                operation = calls[0]
            if leaf in leaves:
                raise ValueError('duplicate pinned CLI leaf ' + leaf)
            leaves[leaf] = (operation, f'{path}:{text.count(chr(10),0,match.start(3))+1}')
        if group == 'File':
            require('command.Subcommands.Add(Remove(pipeline, global));' in text,'pinned file CLI remove registration missing')
            match = re.search(r'return CommandFactory.Mutation\(\s*"(remove)"', text)
            require(match is not None,'unsupported pinned file CLI remove grammar')
            body = text[match.end():].split('\n    private static ',1)[0]
            calls = re.findall(r'client\s*\.\s*(\w+)Async\(',body)
            require(len(calls) == 1,'unsupported pinned file CLI remove client-call grammar')
            leaves['file remove'] = (calls[0], f'{path}:{text.count(chr(10),0,match.start(1))+1}')
    return tools, resources, leaves


def upload_operations(root,pin=PIN):
    text = source(root,'src/Hexalith.Folders.Client/Convenience/FoldersFileUploadExtensions.cs',pin)
    body = text.split('private static async Task<AcceptedCommand> InvokeFileMutationAsync(',1)[-1].split('\n    private static ',1)[0]
    pairs = re.findall(r'FileMutationRequestFileOperationKind\.(\w+) => await client\s*\.\s*(\w+)Async\(',body)
    require(len(pairs) == 2 and {k for k,v in pairs} == {'Add','Change'},'unsupported pinned upload-kind/client-call grammar')
    return dict(pairs)


def client_operations(root,pin=PIN):
    """Read current attribute/method/helper grammar; refuse unknown call shapes."""
    upload = upload_operations(root,pin)
    paths = git(root/REPO,'ls-tree','-r','--name-only',pin,'src/Hexalith.Folders.Mcp').decode().splitlines()
    tools,resources = {},{}
    for path in paths:
        if not path.endswith('.cs') or not any('/'+part+'/' in path for part in ['Tools','Resources']):
            continue
        text = source(root,path,pin)
        matches = list(re.finditer(r'\[McpServerTool\(Name = "([^"]+)"\)\]|\[McpServerResource\(\s*Name = "([^"]+)"\s*,\s*UriTemplate = "([^"]+)"',text))
        for i,match in enumerate(matches):
            body = text[match.end():matches[i+1].start() if i+1 < len(matches) else len(text)].split('\n    private static ',1)[0]
            kind = re.search(r'=> Upload\(pipeline, FileMutationRequestFileOperationKind\.(\w+)',body)
            if kind:
                require(kind[1] in upload,'unsupported pinned MCP upload kind')
                helper = text.split('private static Task<string> Upload(',1)[-1].split('\n    private static ',1)[0]
                require('FileOperationKind = kind' in helper and re.findall(r'client\s*\.\s*(\w+)Async\(',helper) == ['UploadFile'],'pinned MCP upload helper/client link changed')
                operation = upload[kind[1]]
            else:
                calls = re.findall(r'client\s*\.\s*(\w+)Async\(',body)
                require(len(calls) == 1,f'unsupported pinned MCP client-call grammar: {match[1] or match[2]}')
                operation = calls[0]
            (tools if match[1] else resources)[match[1] or (match[2],match[3])] = operation
    return tools,resources


def targets(key, row):
    if key[0] in 'CQ':
        return [key]
    if key[0] in 'MRL':
        return row['cells'][5 if key[0] == 'L' else 4].split(', ')
    return []


def disposition(key, row, decl):
    if key in K12:
        return ('defer', 'AD-23 K12 reconciliation: adopted confidential UI only conflicts with 5.12 owner decoration/agent eligibility. Epic 6 cannot catalog Contracts 1.4.0 until separately resolved; no exposure or classification override.', 'Folders owning maintainer and McpCli product/architecture/security owners')
    if key in DIAGNOSTICS:
        return ('defer', 'Owner decoration and product-approved C13 not-applicable decision for the seed-backed operations_console_projection diagnostic remain missing; G1/G2/G4/G5 remain.', 'Folders owning maintainer and product/query maintainer')
    if key.startswith('G'):
        return 'defer', GAPS[key][2], GAPS[key][3]
    if key in {'N01','N02'}:
        return 'withdraw', 'Adopted K12 confidential UI only; no public agent replacement. Human admission, authorization/retention/audit and independent safety evidence precede any legacy retirement.', 'Folders owning maintainer and Platform/security maintainer'
    if key == 'N03':
        return 'defer', 'Organization ACL baseline/grant/revoke recognizers are adjacent to the legacy surface; no decorated organization-ACL type exists at the pin. Owner declaration, organization-wide scope and layered authority proof are required; folder ACL candidates do not authorize this scope.', 'Folders authorization owning maintainer'
    if key == 'N04':
        return 'defer', 'No decorated type at the pin. N04 future-v2 banner is superseded; renewal remains adjacent and not a legacy surface. Owner declaration, lease/authority semantics and revised inventory required.', 'Folders authorization/workspace owning maintainer'
    if key.startswith('V'):
        return VARIANTS[key][:3]
    ts = targets(key, row)
    gaps = 'G1/G2/G3/G5; command-payload-translation / Story 5.13; task-extension-profile; task-extension-trailing-double-hyphen' if ts[0].startswith('C') else 'G1/G2/G4/G5 / Story 5.14'
    if any(t in {'C02','C03','C04','C05','C07','C11','Q13','Q14','Q16','Q18','Q19','Q35'} for t in ts):
        gaps += '; G6 / Story 5.10; provider-binding-reserved-actor where applicable'
    gaps += '; identifier-aggregate-grammar remains open without conversion'
    if 'Q16' in ts:
        gaps += '; tenant-wide-query-aggregate: separately supplied envelope aggregateId needs authorized tenant-wide scope'
    if key in {'R01','R02'}:
        gaps += '; owner accepts loss of resource URI and subscription; use independently decorated authorized metadata Query'
    return 'replace', gaps, 'Folders Contracts/security/query/runtime owning maintainers; EventStore/Gateway and McpCli enrollment maintainers'


def replacement(key, row, decl):
    parts = []
    ts = targets(key, row)
    if key.startswith('V') and VARIANTS[key][0] == 'replace':
        ts = variant_targets(key, decl)
    for t in ts:
        d = decl[t]
        if d['eligibility'] != 'eligible':
            parts.append(f'{t}: no decorated replacement; {d["eligibility"]}')
            continue
        projection = 'none' if t.startswith('C') else row_name(decl[t]['clr'])
        aggregate = 'caller-supplied envelope aggregateId (no declared accessor/constant)' if d['aggregate'] == 'none' else 'Payload.' + d['aggregate']
        route = 'SubmitCommandRequest' if t.startswith('C') else 'SubmitQueryRequest'
        parts.append(f'{t}: `{d["clr"]}`; owner eligible; wire `{d["wire"]}`; domain `folders`; aggregate {aggregate}; projection `{projection}`; {route}(tenant, folders, aggregateId, wire' + (', projection)' if t.startswith('Q') else ')') + ('; required caller idempotency key' if t.startswith('C') else f'; fixed freshness `{d["freshness"]}`'))
    if parts:
        return '<br>'.join(parts) + ('<br>K12 and diagnostic entries remain deferred/excluded; variant replacement does not admit them.' if key.startswith('V') else '')
    if key.startswith('V'):
        return VARIANTS[key][3]
    if key in {'N01','N02'}:
        return 'Confidential UI, with independent human admission and safety proof; no agent route.'
    return 'None; named prerequisite remains open.'


def variant_targets(key, decl):
    allowed = [k for k,d in decl.items() if d['eligibility'] == 'eligible' and k not in K12]
    if key == 'V01': return [k for k in allowed if k.startswith('Q')]
    if key == 'V02': return ['Q16','Q27','Q28','Q29','Q30','Q31','Q33','Q34']
    if key == 'V03': return [k for k in allowed if k.startswith('C')] + ['Q05','Q07','Q21','Q22','Q24','Q26','Q27','Q30','Q32','Q33','Q34']
    if key == 'V06': return allowed
    if key == 'V07': return [k for k in allowed if k.startswith('C')]
    if key == 'V08': return ['C08','C13']
    return []


def row_name(clr):
    return re.sub(r'(?<!^)(?=[A-Z])', '-', clr.rsplit('.',1)[1]).lower()


def drift(key, decl):
    if key in DRIFT_FIELDS:
        return 'changed: gains ' + DRIFT_FIELDS[key] + ' at the refreshed pin.' + (' ownerFileId is an optional explicit owner incarnation; when omitted the owner resolves an exact accepted path.' if 'ownerFileId' in DRIFT_FIELDS[key] else '') + (' Decorated command and owner eligibility now exist.' if key == 'C10' else '')
    if key[0] in 'CQ' and decl[key]['eligibility'] == 'eligible':
        return 'changed: decorated type, explicit wire/routing and owner eligibility now exist; runtime gaps remain.'
    changed = {'G1':'Contracts decorated in Story 5.12', 'G4':'three internal query handlers and POST /query; none serves the 28 declared types',
               'G5':'real default implementations except unavailable commit executor', 'V05':'REST multipart PutFileStream now exists outside MCP/CLI surface',
               'N04':'future v2-only RenewWorkspaceLock banner superseded'}
    return 'changed: ' + changed[key] + '.' if key in changed else 'unchanged: no added, removed or renamed legacy capability; existing semantics retained subject to recorded gaps/losses.'


def evidence(root, key, row, decl, surface):
    tools, resources, leaves = surface
    if key.startswith('M'):
        return tools[row['cells'][1].strip('`')] + drift_evidence(root, key)
    if key.startswith('R'):
        return resources[tuple(re.findall(r'`([^`]+)`', row['cells'][1]))] + drift_evidence(root, key)
    if key.startswith('L'):
        return leaves[row['cells'][1].strip('`')][1] + drift_evidence(root, key)
    if key[0] in 'CQ':
        return decl[key]['evidence'] + '; ' + decl[key]['ownerEvidence'] + drift_evidence(root,key)
    if key.startswith('G'):
        path = '_bmad-output/implementation-artifacts/sprint-status.yaml'
        story = GAPS[key][0].replace('.', '-')
        text = source(root, path)
        line = next(l for l in text.splitlines() if l.lstrip().startswith(story + '-'))
        return anchor(path, text, line) + '; ' + anchor(DECLARATIONS, source(root, DECLARATIONS), '## Named gaps')
    if key.startswith('V'):
        return anchor(DECLARATIONS, source(root, DECLARATIONS), '## ' + ('Accepted behavior losses' if key in {'V04','V05','V07','V09'} else 'Candidate decisions and routing'))
    paths = {'N01':('src/Hexalith.Folders.Workers/FolderPermissionMaintenanceEndpoints.cs','Map'),
             'N02':('docs/operations/container-images-and-dapr-app-ids.md','rotation'),
             'N03':('src/Hexalith.Folders.Server/Authorization/FolderCommandActionTokenMapper.cs','class '),
             'N04':('_bmad-output/implementation-artifacts/story-4-19-prerequisites-decision-2026-10-07.md','RenewWorkspaceLock')}
    path, needle = paths[key]
    text = source(root, path)
    return anchor(path, text, needle)


def drift_evidence(root, key):
    if key not in DRIFT_FIELDS:
        return ''
    path = 'src/Hexalith.Folders.Client/Generated/HexalithFoldersClient.g.cs'
    text = source(root,path)
    return ''.join('; '+anchor(path,text,'JsonProperty("'+field+'"') for field in DRIFT_FIELDS[key].split('/'))


def candidate(root):
    parser = load(root, 'classmap58build', ART / 'evidence/story-5-2/verify_class_map.py')
    _, rows = parser.inventory_rows(root / OLD)
    mapping = json.loads((root / AD / 'AD-23-capability-class-map.json').read_text())
    inv = next(i for i in mapping['inventories'] if i['path'] == str(OLD))
    classes = {c['id']: c for c in mapping['classes']}
    entries = {r['id']: r['classId'] for r in inv['rows']}
    entries.update({r['id']: r.get('classId', 'governance') for r in inv['records']})
    decl, surface = declarations(root), surfaces(root)
    header = f'''---
inventory_version: '1.1.0'
status: pending
module: folders
source_repository: 'https://github.com/Hexalith/Hexalith.Folders'
source_revision: '{PIN}'
source_spec: '{SPEC}'
predecessor: '{OLD}'
approval_ref: '#a2-amendment-approval-pending'
---

# Folders migration inventory 1.1.0

This additive successor accounts for all **161 entries** from immutable 1.0.0:
49 MCP tools (14 mutations, 35 reads), 2 resources, 42 CLI leaves (14 mutations,
28 reads), 13 Command candidates, 35 Query candidates, 10 variants, 4 adjacent
records and 6 prerequisites. The 93 legacy surfaces are unchanged as a set.
Source was refreshed from `{OLD_PIN}` to `{PIN}`; the former is not an ancestor
of the latter. Every evidence anchor below is relative to the Folders repository
and is resolved with `git show {PIN}:<path>`, never its moving worktree.

## A2 Amendment approval pending

The candidate metadata and A2 heading stay immutable after approval. The separate
[approval receipt](evidence/story-5-8/approval.json) establishes effective approval
only when it records exact-byte owner words, identity, date and covered Folders
roles. Until then this is a pending proposal. A2 supersedes A1's disposition scope
only after that approval. The specification's "approve and stop" approved intent,
not these bytes. No execution, enrollment, publication, parity or retirement
is granted; label delivery additionally requires separate explicit authorization.
Both legacy heads remain compatibility binaries. No new approver is asserted.

## Reading the rows and retained gates

Original row shapes are retained with explicit amendment fields. `include` occurs
if and only if the amendment disposition is `replace`; it is a migration target,
never an enrollment or readiness claim. Deferred rows name their gap and owner;
withdrawals name accepted losses and a replacement experience. The immutable
AD-23 class and adopted outcome remain beside the Folders 5.12 eligibility.
C01/C10 and M01/M02/M04/M13/L10/L24/L25/L26 stay deferred for **AD-23 K12
reconciliation**, owned by the Folders owner and McpCli product/architecture/security
owners. The adopted outcome is confidential UI only. Epic 6 cannot catalog
Contracts 1.4.0 until this gap is resolved; decoration does not override AD-23.
The seven undecorated diagnostics still need owner decoration and a product C13
not-applicable decision. N01/N02 are confidential-UI withdrawals from migration.

Payload identifiers follow the Module's String kind and round-trip unchanged.
Message/correlation IDs and caller idempotency keys are canonical uppercase ULIDs;
never silently lowercase identifiers, convert `sha256:` keys or generate keys.
All 13 Commands need caller-owned keys independently of message identity, and
required `extensions["taskId"]`. Profiles default to no allowed extensions: add
`taskId` using `config set <profile> allowedExtensions taskId` only for an empty
allowlist; preserve existing keys in its comma-separated value otherwise (setter
replaces the allowlist). Payload TaskId on C03/C09/C10/C11/C12 must agree. Domain
task grammar is lowercase letters/digits/dot/underscore/hyphen, at most 128;
trailing `--` is a platform-wide extension rejection, an open gap, not accepted
loss. identifier-aggregate-grammar retains all eight source examples without
conversion, including leading dot/underscore/hyphen and trailing dot/underscore/
hyphen. G2/G3 (5.13) reconcile admission, schema-v2-to-v1 payload translation,
task grammar/association and key replay/conflict/expiry. ProviderBindingRef on
C05/Q13/Q35 requires reserved actor derivation and tenant/namespace separation.
Q16 has no aggregate accessor/constant: caller supplies envelope aggregateId;
tenant-wide-query-aggregate (5.14) must validate its scope independently.
G1 still owes AD-15 package closure and Epic 6.1 Catalog acceptance; G2–G6 and
all applicable variants remain gates. Acceptance is never completion.

Accepted losses bind V04/V05, V07, V09 and R01/R02 and their affected rows in the
5.12 source table. R01/R02 lose URI/subscription transport. V04 loses local-file/
stdin upload and automatic derived evidence. V07 loses auto-key and hash keys.
V09 also accepts the 2026-11-13 decision's REST setup, stderr errors and internal/
unmapped exit 1: use McpCli profiles, stdout JSON errors and operational exit 2.
No credentials are copied. Inline input remains bounded at 262144 decoded bytes;
262145–1048576 requires unavailable generic staging; larger content is invalid.
V05 stays K09 deferred. EXT-MCPCLI-FOLDERS-RETIREMENT-GATE remains closed.

Cross-cutting source drift: `Bearer` credentials now travel only over HTTPS or to
a loopback host (`src/shared/AdapterCore/BearerTransportPolicy.cs:12`). Native REST
endpoints (`src/Hexalith.Folders.Server/Content/WorkspaceNativeEndpoints.cs:33`) were added
outside this MCP/CLI inventory scope and add no surface rows. Registration moved
to `src/Hexalith.Folders.Mcp/Program.cs:61`. Technical inventory 1.0.3, AD-23,
prior receipts, dependencies, census, gitlinks and the AI.Tools plan are unchanged.

'''
    chunks, last = [header], None
    for key, row in rows.items():
        cells, headers = list(row['cells']), list(row['headers'])
        decision, rationale, owner = disposition(key, row, decl)
        coverage = 'include' if decision == 'replace' else 'exclude'
        for i, h in enumerate(headers):
            if h == 'Disposition': cells[i] = decision
            if h == 'Coverage': cells[i] = coverage
            if h == 'Disposition / coverage': cells[i] = decision + ' / ' + coverage
            if h == 'Approval reference': cells[i] = APPROVAL
        if key.startswith('G'):
            story, status, _, _ = GAPS[key]
            cells[1], cells[2] = f'Folders Story {story}: {status} at the pin. ' + rationale, owner
        if key.startswith(('V','N')):
            cells[3] = rationale + ' Replacement: ' + replacement(key, row, decl)
        if key[0] in 'CQ':
            headers = [h.replace('Canonical future name', 'Canonical name').replace('Intended decorated CLR type (new)', 'Declared CLR type or undecorated roadmap candidate').replace('Existing wire candidate', 'Explicit wire name at the pin') for h in headers]
            cells[4] = rationale
        ev = evidence(root, key, row, decl, surface)
        if key[0] in 'MRL':
            cells[7 if key[0] in 'ML' else 6] = '`' + ev.split('; ')[0] + '`'
        class_id = entries[key]
        outcome = classes[class_id]['outcome'] if class_id != 'governance' else 'Scope accounting; no independent capability outcome'
        extra = [class_id, outcome, decision, coverage, rationale, owner, replacement(key, row, decl), '`' + ev.replace('; ', '`; `') + '`', drift(key, decl)]
        if headers != last:
            title = {'G':'Gateway prerequisites and owners','M':'Legacy MCP tool rows','R':'Legacy MCP resource rows','L':'Frozen CLI leaves','C':'Normalized Command candidates','Q':'Normalized Query candidates','V':'Behavior variants and compatibility decisions','N':'Adjacent nonlegacy exclusions'}[key[0]]
            chunks += ['\n## ' + title + '\n\n', '| ' + ' | '.join(headers + EXTRA) + ' |\n', '| ' + ' | '.join(['---'] * (len(headers)+len(EXTRA))) + ' |\n']
        chunks.append('| ' + ' | '.join(cells + extra) + ' |\n')
        last = headers
    chunks += ['''
## Source evidence and verification limits

The exact pinned owner declaration at `docs/contract/mcpcli-folders-operation-declarations.md:1`
is the eligibility, fixed freshness, routing, task, identifier, accepted-loss and
named-gap authority. Decorated Contracts at this pin declare module `folders`
(`src/Hexalith.Folders.Contracts/FoldersModule.cs:3`), String identifiers and
explicit WireType. The exact McpCli route is formed by SubmitCommandRequest /
SubmitQueryRequest in McpCli-local `src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs:251`.
The source table's seven diagnostic exclusions have no decorated route.
All row source anchors were regenerated; no old line number establishes new-pin
behavior. FileMutationRequest.ownerFileId optionally names an explicit owner
incarnation; omission leaves exact accepted-path resolution to the owner. Drift
is explicit per row, with this addition, new file versions/fences and contextual
fileId/version/lockFence fields accounted for. Native REST endpoints are noted
only. Three internal query handlers do not implement these declared Queries;
real default implementations leave the commit executor unavailable.

[Story verifier and tests](evidence/story-5-8/verification.md) establish static
accounting, source declarations, anchors, disposition and hash chains only.
No live operation was invoked. No parity, package enrollment, retirement,
legacy deletion or release acceptance follows from this documentary packet.
''']
    return ''.join(chunks).encode()


def compatibility_section(data):
    lines = data.decode().splitlines(keepends=True)
    positions = [i for i,l in enumerate(lines) if l.rstrip('\r\n') == '## Legacy compatibility surfaces']
    if len(positions) != 1:
        raise ValueError('README must have exactly one compatibility section')
    start = positions[0]
    end = next((i for i in range(start+1,len(lines)) if lines[i].startswith('#')),len(lines))
    return ''.join(lines[start:end]).encode()


def label_candidate(root, digest):
    prior = json.loads((root / ART / 'evidence/story-5-7/labels.json').read_text())
    repo = next(r for r in prior['repositories'] if r['name'] == 'folders')
    owner = Path(repo['ownerCheckout'])
    before = git(owner, 'show', LABEL_PIN + ':README.md')
    after, rows = before.decode(), []
    for old in [r for r in prior['rows'] if r['repository'] == 'folders']:
        text = old['label']['text']
        if after.count(text) != 1:
            raise ValueError(old['id'] + ': prior label missing or duplicated')
        new = re.sub(r'\[Folders inventory 1\.0\.0\]\([^)]*\)', '[Folders inventory 1.1.0](https://github.com/Hexalith/Hexalith.McpCli/blob/main/' + str(NEW) + ')', text)
        new += ' Folders inventory SHA-256: `' + digest + '`.'
        after = after.replace(text, new)
        rows.append(dict(old, label={'file':'README.md','line':after.splitlines().index(new)+1,'text':new,'sha256':sha(new.encode())}))
    after = after.encode()
    patch = ''.join(difflib.unified_diff(before.decode().splitlines(keepends=True), after.decode().splitlines(keepends=True),fromfile='a/README.md',tofile='b/README.md',n=0)).encode()
    files = {'README.before.section.md':compatibility_section(before),'README.after.section.md':compatibility_section(after),'README.patch':patch}
    register = {'schemaVersion':'1.0.0','state':'candidate-pending-owner-approval-and-delivery',
                'predecessor':{'path':str(ART / 'evidence/story-5-7/labels.json'),'sha256':sha((root / ART / 'evidence/story-5-7/labels.json').read_bytes())},
                'inventoryArtifacts':{str(NEW):digest},'inventoryRevision':None,'deliveryAuthorization':None,
                'repository':{'name':'folders','repository':repo['repository'],'ownerCheckout':str(owner),'baseRevision':LABEL_PIN,
                              'readme':{'beforeSha256':sha(before),'afterSha256':sha(after)},'integration':None,
                              **{key:{'path':str(E / 'upstream/folders' / name),'sha256':sha(files[name])} for key,name in [('before','README.before.section.md'),('after','README.after.section.md'),('patch','README.patch')]}},'rows':rows}
    return register, files


def main(argv=None):
    try:
        receipt_path = ROOT / E / 'approval.json'
        if receipt_path.exists() and read_json(receipt_path).get('decision') != 'pending':
            raise ValueError('refusing to overwrite an approved or unknown-state packet')
        labels_path = ROOT / E / 'labels.json'
        if labels_path.exists():
            labels = read_json(labels_path)
            require(isinstance(labels.get('repository'),dict),'Folders label repository must be an object')
            if labels.get('state') != 'candidate-pending-owner-approval-and-delivery':
                raise ValueError('refusing to overwrite a delivered or unknown-state label packet')
        data = candidate(ROOT)
        parser = load(ROOT, 'parser58receipt', ART / 'evidence/story-5-2/verify_class_map.py')
        _, old = parser.inventory_rows(ROOT / OLD)
        # Parse generated bytes without a temporary mutation of the published path.
        class BytesPath:
            name = NEW.name
            def read_text(self, **kwargs): return data.decode()
        _, new = parser.inventory_rows(BytesPath())
        artifacts = {str(p):sha((ROOT / p).read_bytes()) for p in AUTHORITIES}
        artifacts[str(NEW)] = sha(data)
        pinned = {DECLARATIONS:sha(source(ROOT,DECLARATIONS).encode()),
                  **{d['path']:sha(d['source'].encode()) for d in declarations(ROOT).values()}}
        receipt = {'schemaVersion':'1.0.0','decision':'pending','baselineCommit':BASELINE,'sourceRevision':PIN,
                   'supersedes':'A1','requiredApprovalRoles':ROLES,'rolesPolicy':'Folders roles covered for this successor only; no cross-module authority is inferred.',
                   'artifacts':artifacts,'pinnedArtifacts':pinned,'amendment':{'fromPath':str(OLD),'fromVersion':'1.0.0','fromSha256':artifacts[str(OLD)],
                   'toPath':str(NEW),'toVersion':'1.1.0','toSha256':sha(data),'changedRows':[{'id':k,'fromSha256':sha(r['text'].encode()),'toSha256':sha(new[k]['text'].encode())} for k,r in old.items()],
                   'addedRows':[],'removedRows':[]},'limits':LIMITS}
        labels, files = label_candidate(ROOT, sha(data))
        writes = {NEW:data,E / 'approval.json':(json.dumps(receipt,indent=2)+'\n').encode(), E / 'labels.json':(json.dumps(labels,indent=2)+'\n').encode(),
                  **{E / 'upstream/folders' / name:blob for name,blob in files.items()}}
        for path, blob in writes.items():
            (ROOT / path).parent.mkdir(parents=True,exist_ok=True)
            (ROOT / path).write_bytes(blob)
    except (ValueError,KeyError,TypeError,OSError,IndexError) as error:
        print(f'FAIL: {error}',file=sys.stderr)
        return 1
    print('Prepared Folders 1.1.0 pending candidate and PS10/PS11 README-only patch; no approval or delivery granted.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
