#!/usr/bin/env python3
"""Verify pending Folders 1.1.0; completion additionally requires approval and delivery.

Static documentary evidence only. No source service, legacy operation, enrollment,
Git mutation, fetch or remote operation is performed.
"""
import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[4]
ART = Path('_bmad-output/implementation-artifacts')
E = ART / 'evidence/story-5-8'


def load(root, name, path):
    spec = importlib.util.spec_from_file_location(name, root / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


B = load(ROOT, 'builder58verify', E / 'build_candidate.py')
COUNTS = dict(M=49,R=2,L=42,C=13,Q=35,V=10,N=4,G=6)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f'duplicate JSON member {key}')
        result[key] = value
    return result


def read_json(path):
    value = json.loads(path.read_bytes(), object_pairs_hook=unique)
    require(isinstance(value,dict),f'JSON document must be an object: {path.name}')
    return value


def nonblank(value):
    return isinstance(value,str) and bool(value.strip())


def parse(text):
    """Read every ID-first row; reject duplicate IDs and damaged table widths."""
    rows, headers = {}, []
    for line in text.splitlines():
        if not line.startswith('|'):
            headers = []
            continue
        cells = [c.strip() for c in re.split(r'(?<!\\)\|',line)[1:-1]]
        if not cells or cells[0].startswith('---'):
            continue
        if cells[0] == 'ID':
            headers = cells
            continue
        if not re.fullmatch(r'(?:[MRLCQVN]\d{2}|G\d)',cells[0]):
            continue
        key = cells[0]
        require(key not in rows, f'folders:{key}: duplicate entry')
        require(bool(headers) and len(cells) == len(headers) and all(cells), f'folders:{key}: damaged row or empty cell')
        rows[key] = {'cells':cells,'headers':headers[:],'text':line}
    return rows


def fields(row):
    return dict(zip(row['headers'],row['cells']))


def accounting(old, new, inventory):
    expected = {r['id'] for r in inventory['rows'] + inventory['records']}
    contiguous = {f'{p}{i}' if p == 'G' else f'{p}{i:02d}' for p,n in COUNTS.items() for i in range(1,n+1)}
    require(set(new) == set(old) == expected == contiguous and len(new) == 161 and Counter(k[0] for k in new) == COUNTS, 'folders: 161-entry AD-23 accounting mismatch')


def check_rows(root, old, new, inventory, classes, decl):
    entries = {r['id']:r.get('classId','governance') for r in inventory['rows']+inventory['records']}
    for key, row in new.items():
        f, original = fields(row), old[key]
        require(row['headers'][-len(B.EXTRA):] == B.EXTRA, f'folders:{key}: amendment columns damaged')
        require(f['Capability class'] == entries[key], f'folders:{key}: AD-23 class mismatch')
        outcome = classes[entries[key]]['outcome'] if entries[key] != 'governance' else 'Scope accounting; no independent capability outcome'
        require(f['Adopted outcome'] == outcome, f'folders:{key}: adopted outcome mismatch')
        decision, coverage = f['Amendment disposition'], f['Amendment coverage']
        require(decision in {'replace','withdraw','defer'} and coverage in {'include','exclude'} and ((decision == 'replace') == (coverage == 'include')), f'folders:{key}: include requires replace and replace requires include')
        if key in {'C01','C10','M01','M02','M04','M13','L10','L24','L25','L26'}:
            require(decision == 'defer' and 'AD-23 K12 reconciliation' in f['Amendment rationale or gap'] and 'Epic 6 cannot catalog Contracts 1.4.0' in f['Amendment rationale or gap'] and all(t in f['Amendment owner'] for t in ['Folders','McpCli','product/architecture/security']), f'folders:{key}: K12 reconciliation and catalog hold missing')
        elif key in B.DIAGNOSTICS or key.startswith('G') or key in {'N03','N04','V05'}:
            require(decision == 'defer', f'folders:{key}: required deferral changed')
        elif key in {'N01','N02','V04','V09','V10'}:
            require(decision == 'withdraw', f'folders:{key}: required withdrawal changed')
        else:
            require(decision == 'replace', f'folders:{key}: eligible replacement disposition changed')
        require(nonblank(f['Amendment rationale or gap']) and nonblank(f['Amendment owner']), f'folders:{key}: gap/rationale and owner required')
        expected_decision, rationale, owner = B.disposition(key,original,decl)
        require(f['Amendment rationale or gap'] == rationale and f['Amendment owner'] == owner, f'folders:{key}: required gap/loss or owning role changed')
        require(f['Exact replacement'] == B.replacement(key,original,decl), f'folders:{key}: exact replacement type/wire/route or experience mismatch')
        require(f['Approval reference'] == B.APPROVAL, f'folders:{key}: A2 approval reference missing')
        for i,h in enumerate(original['headers']):
            if h == 'Disposition': require(row['cells'][i] == decision, f'folders:{key}: legacy/amendment disposition mismatch')
            if h == 'Coverage': require(row['cells'][i] == coverage, f'folders:{key}: legacy/amendment coverage mismatch')
            if h == 'Disposition / coverage': require(row['cells'][i] == decision + ' / ' + coverage, f'folders:{key}: combined disposition mismatch')
        # Preserve identity, mappings, freshness and security; refresh only factual premise cells.
        stable = {'M':[0,1,4,5,6], 'R':[0,1,4,5], 'L':[0,1,2,5,6], 'C':[0,1,2,3], 'Q':[0,1,2,3], 'V':[0,1,4], 'N':[0,1,4], 'G':[0]}[key[0]]
        require(all(row['cells'][i] == original['cells'][i] for i in stable), f'folders:{key}: legacy identity/mapping/security/freshness changed')
        if key[0] in 'MRL':
            ds = {new[t]['cells'][new[t]['headers'].index('Amendment disposition')] for t in B.targets(key,original)}
            require(ds == {decision}, f'folders:{key}: target disposition inheritance mismatch')
        if key.startswith('G'):
            story,status,_,_ = B.GAPS[key]
            require(row['cells'][1] == f'Folders Story {story}: {status} at the pin. ' + rationale and row['cells'][2] == owner, f'folders:{key}: story/status or corrected prerequisite premise mismatch')


def check_anchors(root, old, new, decl, surface):
    for key,row in new.items():
        f = fields(row)
        expected = B.evidence(root,key,old[key],decl,surface)
        require(f['Pinned evidence'] == '`' + expected.replace('; ','`; `') + '`', f'folders:{key}: pinned anchor identity mismatch')
        for path,number in re.findall(r'`([^`]+):(\d+)`',f['Pinned evidence']):
            require(not Path(path).is_absolute() and '..' not in Path(path).parts, f'folders:{key}: anchor path escapes source')
            lines = B.source(root,path).splitlines()
            require(0 < int(number) <= len(lines) and bool(lines[int(number)-1].strip()), f'folders:{key}: unresolvable pinned anchor {path}:{number}')
        if key[0] in 'MRL':
            require(row['cells'][7 if key[0] in 'ML' else 6] == '`'+expected.split('; ')[0]+'`', f'folders:{key}: source anchor differs from pin')
        if key.startswith('G'):
            story,status,_,_ = B.GAPS[key]
            source = B.source(root,'_bmad-output/implementation-artifacts/sprint-status.yaml')
            match = re.findall(r'^\s*'+story.replace('.','-')+r'-[^:]+:\s*(\S+)',source,re.M)
            require(match == [status], f'folders:{key}: Folders story status differs at pin')


def check_declarations(root, old, new, decl, surface):
    tools,resources,leaves = surface
    require(len(tools) == 49 and set(tools) == {r['cells'][1].strip('`') for k,r in old.items() if k.startswith('M')}, 'folders: exact pinned 49-tool set mismatch')
    require(len(resources) == 2 and set(resources) == {tuple(re.findall(r'`([^`]+)`',r['cells'][1])) for k,r in old.items() if k.startswith('R')}, 'folders: exact pinned two-resource set mismatch')
    require(len(leaves) == 42 and set(leaves) == {r['cells'][1].strip('`') for k,r in old.items() if k.startswith('L')}, 'folders: exact pinned 42-leaf set mismatch')
    pascal = lambda value: ''.join(w[0].upper()+w[1:] for w in value.split('-'))
    tool_calls,resource_calls = B.client_operations(root)
    for key,row in old.items():
        if key[0] in 'MRL':
            if key[0] == 'M':
                op = tool_calls[row['cells'][1].strip('`')]
                expected_op = pascal(row['cells'][1].strip('`'))
            elif key[0] == 'R':
                op = resource_calls[tuple(re.findall(r'`([^`]+)`',row['cells'][1]))]
                expected_op = decl[B.targets(key,row)[0]]['clr'].rsplit('.',1)[1]
            else:
                op = leaves[row['cells'][1].strip('`')][0]
                expected_op = pascal(row['cells'][2].strip('`'))
            expected = {'AddFile':['MutateFiles'],'ChangeFile':['MutateFiles'],'RemoveFile':['MutateFiles'],'UpdateFolderAclEntry':['GrantFolderAccess','RevokeFolderAccess']}.get(op,[op])
            require(op == expected_op and [decl[t]['clr'].rsplit('.',1)[1] for t in B.targets(key,row)] == expected, f'folders:{key}: pinned client call/kind or operation-to-target mapping mismatch')
    program = B.source(root,'src/Hexalith.Folders.Mcp/Program.cs')
    require('.WithToolsFromAssembly()' in program and '.WithResourcesFromAssembly()' in program and '.WithStdioServerTransport()' in program.splitlines()[60], 'folders: pinned registration mismatch')
    module = B.source(root,'src/Hexalith.Folders.Contracts/FoldersModule.cs')
    require('[assembly: HexalithModule("folders",' in module and 'IdentifierKind.String)]' in module, 'folders: module domain/String identifier declaration mismatch')
    require(len(decl) == 48 and sum(d['eligibility']=='eligible' for d in decl.values()) == 41, 'folders: 48-candidate/41-decoration owner set mismatch')
    for key,row in new.items():
        if fields(row)['Amendment disposition'] != 'replace':
            continue
        ts = B.variant_targets(key,decl) if key.startswith('V') else B.targets(key,old[key])
        require(bool(ts), f'folders:{key}: replacement has no decorated target')
        for t in ts:
            d = decl[t]
            kind = 'Command' if t.startswith('C') else 'Query'
            require(d['eligibility'] == 'eligible' and re.search(r'\[Hexalith'+kind+r'\(',d['source']) is not None and f'public sealed record {d["clr"].rsplit(".",1)[1]}(' in d['source'], f'folders:{key}: {t} replacement is absent, undecorated or owner-ineligible')
            expected_wire = 'Hexalith.Folders.' + ('Commands.' if t.startswith('C') else 'Queries.') + d['clr'].rsplit('.',1)[1]
            require(d['wire'] == expected_wire and f'WireType = "{expected_wire}"' in d['source'] and 'Domain = "folders"' in d['source'], f'folders:{key}: {t} decorated wire/domain mismatch')
            accessor = re.search(r'AggregateIdProperty = nameof\((\w+)\)',d['source'])
            require((accessor[1] if accessor else 'none') == d['aggregate'], f'folders:{key}: {t} aggregate route mismatch')
            if t.startswith('Q'):
                require(f'ProjectionType = "{B.row_name(d["clr"])}"' in d['source'], f'folders:{key}: {t} projection route mismatch')
            else:
                key_attributes = re.search(r'\[property:\s*((?:[^"\]]|"(?:\\.|[^"\\])*")*)\]\s*string\s+IdempotencyKey\b',d['source'])
                require('IdempotencyKeyProperty = nameof(IdempotencyKey)' in d['source'] and key_attributes is not None and re.search(r'\bJsonRequired\b',key_attributes[1]) is not None and 'JsonPropertyName("idempotencyKey")' in key_attributes[1], f'folders:{key}: {t} required caller key declaration missing')
    route = (root / 'src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs').read_text()
    require('new SubmitCommandRequest(messageId!, tenant!, operation.Routing.Domain, aggregateId!,' in route and 'operation.Routing.WireType, rebuilt, correlationId,' in route and 'new SubmitQueryRequest(tenant!, operation.Routing.Domain, aggregateId!, operation.Routing.WireType,' in route and 'operation.Routing.ProjectionType' in route, 'folders: McpCli wire route evidence mismatch')


def check_drift(new, decl):
    for key,row in new.items():
        require(fields(row)['Drift'] == B.drift(key,decl), f'folders:{key}: source drift missing or incorrect')


def check_source_drift(root,surface):
    old_surface = B.surfaces(root,B.OLD_PIN)
    require(all(set(a) == set(b) for a,b in zip(old_surface,surface)), 'folders: source drift added, removed or renamed a legacy surface')
    path = 'src/Hexalith.Folders.Client/Generated/HexalithFoldersClient.g.cs'
    before,after = B.source(root,path,B.OLD_PIN),B.source(root,path)
    for model,properties in [('FileMutationRequest',['ownerFileId','expectedFileVersion','expectedLockFence']),('FileMetadataItem',['fileId','version']),('LockLeaseMetadata',['lockFence'])]:
        def block(text):
            match = re.search(r'public partial class '+model+r'[^\n]*\n(.*?)(?=\n    \[System.CodeDom.Compiler.|\Z)',text,re.S)
            return match[0] if match else ''
        for prop in properties:
            needle = 'JsonProperty("'+prop+'"'
            require(needle not in block(before) and needle in block(after), f'folders: source drift {model}.{prop} is not evidenced at both pins')
            if prop == 'ownerFileId' and needle in block(after):
                require('Optional explicit owner incarnation; an exact accepted path is resolved by the owner when omitted.' in block(after) and re.search(r'JsonProperty\("ownerFileId", Required = Newtonsoft.Json.Required.DisallowNull, NullValueHandling = Newtonsoft.Json.NullValueHandling.Ignore\)',block(after)) is not None, 'folders: ownerFileId optional owner-incarnation semantics missing')
    policy = B.source(root,'src/shared/AdapterCore/BearerTransportPolicy.cs')
    require('Uri.UriSchemeHttps' in policy and 'IPAddress.IsLoopback(address)' in policy and 'Uri.UriSchemeHttp' in policy, 'folders: HTTPS/loopback credential source premise missing')
    defaults = B.source(root,'src/Hexalith.Folders.Server/FoldersServerServiceCollectionExtensions.cs')
    require('IWorkspaceCommitExecutor, UnavailableWorkspaceCommitExecutor' in defaults and all(name in defaults for name in ['IWorkspaceFileContentStore','provider.GetRequiredService','WorkspaceContentMutationAdapter']), 'folders: default implementation/commit-executor source premise missing')
    for query in ['FolderFileOwnerRead','FolderFileReferenceRead','FolderOwnerRead']:
        text = B.source(root,f'src/Hexalith.Folders.Server/Queries/{query}QueryHandler.cs')
        require('IDomainQueryHandler' in text and query+'Query' in text and 'Hexalith.Folders.Contracts.Queries' not in text, f'folders: internal {query} query-handler premise missing')


def check_approval(receipt,artifacts,pinned,delta,completion):
    require(isinstance(receipt,dict),'approval receipt must be an object')
    require(receipt.get('schemaVersion') == '1.0.0' and receipt.get('baselineCommit') == B.BASELINE and receipt.get('sourceRevision') == B.PIN, 'approval schema/baseline/pin mismatch')
    require(receipt.get('artifacts') == artifacts and receipt.get('pinnedArtifacts') == pinned, 'approval artifact/hash-chain binding mismatch')
    require(receipt.get('amendment') == delta, 'approval predecessor/successor row delta mismatch')
    require(receipt.get('supersedes') == 'A1', 'approval must supersede A1')
    require(receipt.get('requiredApprovalRoles') == B.ROLES and receipt.get('rolesPolicy') == 'Folders roles covered for this successor only; no cross-module authority is inferred.', 'approval required Folders roles mismatch')
    require(receipt.get('limits') == B.LIMITS, 'approval authority limits changed')
    require(receipt.get('decision') in {'pending','approved'}, 'unknown approval decision')
    if receipt['decision'] == 'approved':
        require(all(nonblank(receipt.get(k)) for k in ['approver','exactApprovalInstruction','approvalSource','approvedOn']), 'owner approval lacks identity, exact words, source or date')
        roles = receipt.get('rolesCovered')
        require(isinstance(roles,list) and all(nonblank(r) for r in roles) and set(B.ROLES) <= set(roles), 'owner approval lacks required covered Folders roles')
    else:
        require(not any(k in receipt for k in ['approver','exactApprovalInstruction','approvalSource','approvedOn','rolesCovered']), 'pending receipt must not claim owner approval')
    if completion:
        require(receipt['decision'] == 'approved', 'completion requires exact-byte owner approval and covered Folders roles')


def metadata(text):
    require(text.startswith('---\n'), 'folders: inventory frontmatter missing')
    result = {}
    for line in text.split('---',2)[1].splitlines():
        if not line:
            continue
        k,sep,v = line.partition(':')
        require(bool(sep) and k not in result, 'folders: damaged or duplicate metadata')
        result[k] = v.strip().strip("'\"")
    return result


def check_metadata(text):
    expected = dict(inventory_version='1.1.0',status='pending',module='folders',source_repository='https://github.com/Hexalith/Hexalith.Folders',source_revision=B.PIN,source_spec=str(B.SPEC),predecessor=str(B.OLD),approval_ref='#a2-amendment-approval-pending')
    require(metadata(text) == expected, 'folders: candidate metadata/pin/approval state mismatch')


def completion_requested(root,requested):
    for path,key in [(B.SPEC,'status'),(ART/'sprint-status.yaml','  5-8-refresh-and-re-disposition-the-folders-inventory')]:
        if (root/path).exists():
            found = re.findall(r'^'+re.escape(key)+r':\s*[\'"]?([\w-]+)',(root/path).read_text(),re.M)
            require(len(found) <= 1, 'duplicate workflow status '+key.strip())
            requested = requested or found == ['done']
    return requested


def verify_owner_packet(root,completion=False):
    root = Path(root).resolve()
    artifacts = {}
    for path in B.AUTHORITIES:
        data = (root/path).read_bytes()
        require(B.git(root,'show',f'{B.BASELINE}:{path}') == data, f'preserved authority changed: {path}')
        artifacts[str(path)] = B.sha(data)
    ad = load(root,'ad2358',ART/'evidence/story-5-2/verify_class_map.py')
    _,state = ad.verify(root,root/B.AD/'AD-23-capability-class-map.json')
    require(state == 'adopted', 'AD-23 exact-byte owner adoption is required')
    mapping = read_json(root/B.AD/'AD-23-capability-class-map.json')
    inv = next(i for i in mapping['inventories'] if i['path'] == str(B.OLD))
    old, new = parse((root/B.OLD).read_text()), parse((root/B.NEW).read_text())
    check_metadata((root/B.NEW).read_text())
    accounting(old,new,inv)
    decl,surface = B.declarations(root),B.surfaces(root)
    check_rows(root,old,new,inv,{c['id']:c for c in mapping['classes']},decl)
    check_anchors(root,old,new,decl,surface)
    check_declarations(root,old,new,decl,surface)
    check_drift(new,decl)
    check_source_drift(root,surface)
    # Protect non-row factual prose as well as the independently checked table semantics.
    require((root/B.NEW).read_bytes() == B.candidate(root), 'folders: candidate prose/source premises differ from deterministic derivation')
    artifacts[str(B.NEW)] = B.sha((root/B.NEW).read_bytes())
    pinned = {B.DECLARATIONS:B.sha(B.source(root,B.DECLARATIONS).encode()),**{d['path']:B.sha(d['source'].encode()) for d in decl.values()}}
    delta = {'fromPath':str(B.OLD),'fromVersion':'1.0.0','fromSha256':artifacts[str(B.OLD)],'toPath':str(B.NEW),'toVersion':'1.1.0','toSha256':artifacts[str(B.NEW)],
             'changedRows':[{'id':k,'fromSha256':B.sha(r['text'].encode()),'toSha256':B.sha(new[k]['text'].encode())} for k,r in old.items()],'addedRows':[],'removedRows':[]}
    receipt = read_json(root/E/'approval.json')
    check_approval(receipt,artifacts,pinned,delta,completion)
    return receipt


def verify(root,completion=False):
    root = Path(root).resolve()
    completion = completion_requested(root,completion)
    labels = read_json(root/E/'labels.json')
    completion = completion or labels.get('state') == 'integrated'
    receipt = verify_owner_packet(root,completion)
    label_module = load(root,'labels58',E/'verify_labels.py')
    label_module.verify(root,completion,owner_checked=True)
    return receipt['decision'],completion


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--approved-completion',action='store_true')
    args = parser.parse_args(argv)
    try:
        decision,complete = verify(args.root,args.approved_completion)
    except (ValueError,KeyError,TypeError,OSError,IndexError) as error:
        print(f'FAIL: {error}',file=sys.stderr)
        return 1
    print('PASS: folders: 161 entries, pinned declarations/anchors/drift, AD-23 dispositions and complete hash chain')
    print(f'PASS: owner decision: {decision}; ' + ('approved completion verified' if complete else 'candidate only; approval and integrated PS10/PS11 labels remain completion gates'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
