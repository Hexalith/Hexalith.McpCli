#!/usr/bin/env python3
"""Verify static candidates; completion also requires exact approval and delivered labels."""
import argparse
import importlib.util
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[4]
E = Path('_bmad-output/implementation-artifacts/evidence/story-5-10')


def load(root,name,path):
    spec = importlib.util.spec_from_file_location(name,root/path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


B = load(ROOT,'builder510verify',E/'build_candidate.py')
read_json, require = B.read_json,B.require
COUNTS = {'chatbot':dict(M=12,L=12,V=15,X=4,G=5),
          'memories':dict(M=4,L=14,S=4,V=17,X=6,G=6,T=4)}


def nonblank(value):
    return isinstance(value,str) and bool(value.strip())


def fields(row):
    return dict(zip(row['headers'],row['cells']))


def accounting(module,old,new,entries):
    expected = {f'{p}{i}' if p == 'G' else f'{p}{i:02d}' for p,n in COUNTS[module].items() for i in range(1,n+1)}
    require(set(new) == set(entries) == expected and set(old) == expected-{f'T{i:02d}' for i in range(1,5)},
            f'{module}: predecessor/AD-23 entry accounting mismatch (missing={sorted(expected-set(new))}, extra={sorted(set(new)-expected)})')


def metadata(module,text):
    require(text.startswith('---\n'),f'{module}: frontmatter missing')
    values = {}
    for line in text.split('---',2)[1].splitlines():
        if not line: continue
        key,sep,value = line.partition(':')
        require(sep and key not in values,f'{module}: damaged or duplicate metadata')
        values[key] = value.strip().strip("'\"")
    m = B.MODULES[module]
    expected = dict(inventory_version='1.1.0',status='pending',module=module,
                    source_repository='https://github.com/Hexalith/Hexalith.'+m['title'],source_revision=m['pin'],
                    source_spec=str(B.SPEC),predecessor=str(m['old']),approval_ref='#a2-amendment-approval-pending')
    require(values == expected,f'{module}: metadata/pin/approval-state mismatch')


def check_rows(root,module,old,new,entries,outcomes):
    for key,row in new.items():
        f,klass = fields(row),entries[key]
        prefix = f'{module}:{key} ({klass})'
        require(row['headers'][-len(B.EXTRA):] == B.EXTRA,prefix+': amendment columns damaged')
        require(f['Capability class'] == klass and f['Adopted outcome'] == outcomes.get(klass,'Scope accounting; no independent capability outcome'),prefix+': AD-23 class/outcome mismatch')
        d,coverage = f['Amendment disposition'],f['Amendment coverage']
        require(d != 'replace' and coverage != 'include',prefix+': invented readiness; no decorated Gateway replacement at pin')
        expected = 'withdraw' if klass in {'K07','K12','K14','K15'} else 'defer'
        require(d == expected and coverage == 'exclude',prefix+': disposition contradicts AD-23 class')
        why = f['Amendment rationale or gap']
        require(nonblank(why) and nonblank(f['Amendment owner']),prefix+': rationale/gap and owner required')
        if d == 'withdraw':
            require(all(t in why for t in ['Owner rationale:','Replacement experience:','Accepted loss:']),prefix+': withdrawal lacks rationale, replacement experience or accepted loss')
        else:
            require('gap:' in why.lower() and f['Amendment owner'] != 'none',prefix+': deferral lacks named gap or owner')
            if klass in {'K01','K03','K04','K05','K06'}:
                require('Contracts' in why and 'handler' in why and 'admission' in why,prefix+': module Contracts/handler/admission gap missing')
        if klass == 'K12': require('Confidential-UI coverage evidence' in why and 'before retirement' in why,prefix+': confidential UI retirement prerequisite missing')
        if klass == 'K14': require(all(t in why for t in ['1.2.0','Retained','never counted retired','--yes grants no agent authority']),prefix+': retained owner-tooling exemption missing')
        if module == 'memories' and d == 'defer':
            require(B.HTTP_GATE in why,prefix+': necessary-but-insufficient HTTP/user/tenant/administrative/semantic/release gate missing')
            if key not in B.IDENTITY: require('G2' in why,prefix+': G2 identity gate missing')
        if module == 'chatbot' and d == 'defer':
            require(B.CONTEXT_GATE in why,prefix+': governed workflow or context-channel gap missing')
        if module == 'chatbot' and key in {'M10','L10','V07','V08'}:
            require('Module-side provider egress and pre-submit authority' in why and 'Payload concurrency inputs' in why,prefix+': K05 provider/pre-submit authority gap missing')
        if module == 'chatbot' and key == 'V10': require('no decorated status Query' in why and 'acceptance never proves completion' in why,prefix+': status Query/acceptance gap missing')
        if module == 'memories' and key in {'L01','L13'}: require('unscoped metadata' in why and 'no checked admin-role' in why,prefix+': unscoped deployment metadata premise missing')
        if key.startswith('T'):
            require(row['headers'][:len(B.PS14_HEADERS)] == B.PS14_HEADERS,prefix+': PS14 fields missing')
            expected_row = fields(B.ps14_rows()[key])
            for h in B.PS14_HEADERS[1:]:
                require(nonblank(f[h]) and f[h] == expected_row[h],prefix+': PS14 required field changed: '+h)
        require(f['Exact replacement'] == B.replacement(module,key,klass),prefix+': plain Command/REST DTO/OpenAPI cannot establish decorated readiness or replacement')
        require(why == B.rationale(module,key,klass) and f['Amendment owner'] == B.owner(module,klass),prefix+': required owner/gap/loss changed')
        require(f['Drift'] == B.drift(root,module,key,old.get(key)),prefix+': drift status missing or incorrect')
        if key in old and not key.startswith(('G','V')):
            require(row['cells'][0:2] == old[key]['cells'][0:2],prefix+': predecessor identity changed')
        for h in ['Disposition','Coverage','Disposition / coverage']:
            if h in f: require(f[h] == (d if h == 'Disposition' else coverage if h == 'Coverage' else d+' / '+coverage),prefix+': legacy and amendment disposition disagree')
        if 'Approval' in f: require(f['Approval'] == B.APPROVAL,prefix+': approval reference missing')


def check_anchors(root,module,old,new):
    for key,row in new.items():
        cell = fields(row)['Pinned evidence']
        expected = B.evidence(root,module,key,old.get(key))
        require(cell == '`'+'`; `'.join(expected)+'`',f'{module}:{key}: pinned anchor identity mismatch')
        anchors = re.findall(r'`([^`]+):(\d+)`',cell)
        require(anchors,f'{module}:{key}: pinned anchor missing')
        for path,line in anchors:
            require(not Path(path).is_absolute() and '..' not in Path(path).parts,f'{module}:{key}: source anchor escapes repository')
            lines = B.source(root,module,path).splitlines()
            require(0 < int(line) <= len(lines) and lines[int(line)-1].strip(),f'{module}:{key}: unresolvable anchor {path}:{line}')


def check_source_drift(root):
    B.preconditions(root)
    for module,m in B.MODULES.items():
        project = f'src/Hexalith.{m["title"]}.Contracts/Hexalith.{m["title"]}.Contracts.csproj'
        require(B.blob(root,module,project) == B.blob(root,module,project,m['oldpin']),f'{module}: Contracts project unexpectedly changed')
        files = B.git(root/B.repo(module),'ls-tree','-r','--name-only',m['pin'],f'src/Hexalith.{m["title"]}.Contracts').decode().splitlines()
        for path in [p for p in files if p.endswith('.cs')]:
            text = B.git(root/B.repo(module),'show',f'{m["pin"]}:{path}').decode('utf-8-sig')
            require(re.search(r'\[\s*(?:assembly:\s*)?(?:[A-Za-z_]\w*\.)*Hexalith(?:Module|Command|Query)(?:Attribute)?\b',text) is None,f'{module}: unexpected decorated type at pin: {path}')
    c,m = B.MODULES['chatbot'],B.MODULES['memories']
    require(B.git(root/B.repo('chatbot'),'rev-parse',c['oldpin']+':'+B.OLD_SOURCE_TREE) == B.git(root/B.repo('chatbot'),'rev-parse',B.OLD_SOURCE_PIN+':'+B.OLD_SOURCE_TREE),'chatbot: unpublished old src tree differs from published comparison')
    B.git(root/B.repo('chatbot'),'merge-base','--is-ancestor',B.OLD_SOURCE_PIN,c['pin'])
    require(B.git(root/B.repo('chatbot'),'diff','--name-status',B.OLD_SOURCE_PIN,c['oldpin']).decode().splitlines() == ['M\t.mcp.json'],'chatbot: historical source-only comparison premise changed')
    stable = ['src/Hexalith.ChatBot.Mcp/ChatBotMcpTools.cs','src/Hexalith.ChatBot.Cli/ChatBotCliCommands.cs']
    require(B.git(root/B.repo('chatbot'),'diff','--name-only',c['oldpin'],c['pin'],'--',*stable) == b'','chatbot: fixed tool/leaf declarations changed')
    require(len(re.findall(r'\[McpServerTool\(',B.source(root,'chatbot',stable[0]))) == 12,'chatbot: expected twelve registered tools')
    host = B.source(root,'chatbot','src/Hexalith.ChatBot.Mcp/Program.cs')
    require('WithTools<ChatBotMcpTools>()' in host and not re.search(r'WithResources|WithPrompts',host),'chatbot: host tool/resource/prompt premise changed')
    require(B.git(root/B.repo('memories'),'diff','--name-only',m['oldpin'],m['pin'],'--','src/Hexalith.Memories.Mcp/Tools','src/Hexalith.Memories.Cli/Commands','tools/MigrateEmbeddingVectors',B.SERVICE,B.EXITS) == b'','memories: fixed tools/leaves/stubs/operator source changed')
    host = B.source(root,'memories','src/Hexalith.Memories.Mcp/McpCompositionRoot.cs')
    require(len(re.findall(r'\.WithTools<',host)) == 4 and not re.search(r'WithResources|WithPrompts',host),'memories: expected four registered tools and no resources/prompts')
    require('ValidAlgorithms' in host,'memories: JWT algorithm drift missing')
    program,service = B.source(root,'memories',B.TOOL),B.source(root,'memories',B.SERVICE)
    require(all(n in program for n in ['selectedModes != 1','options.Interactive = !Console.IsInputRedirected','!options.Yes && options.Interactive','ConnectionMultiplexer.ConnectAsync','new DaprClientBuilder','HttpEndpoint = daprHttpEndpoint']), 'memories: PS14 mode/confirmation/direct-access premise changed')
    require(all(n in service for n in ['requires --tenant','Mutation requires explicit confirmation','PrepareStagingSemanticIndexesAsync','CutoverStagingSemanticIndexesAsync','RollbackMigrationAsync','AbortMigrationAsync']), 'memories: PS14 tenant/confirmation/effect premise changed')



def check_approval(receipt,expected,completion):
    for key in ['schemaVersion','baselineCommit','sourceRevisions','supersedes','requiredApprovalRoles','rolesPolicy','artifacts','pinnedArtifacts','amendments','limits']:
        require(receipt.get(key) == expected[key],f'approval {key} hash/authority/delta binding mismatch')
    require(receipt.get('decision') in {'pending','approved'},'unknown approval decision')
    keys = ['approver','exactApprovalInstruction','approvalSource','approvedOn','rolesCovered']
    if receipt['decision'] == 'approved':
        require(all(nonblank(receipt.get(k)) for k in keys[:-1]),'approval lacks identity, exact words, source or date')
        require(receipt['exactApprovalInstruction'].strip().casefold() == 'approve','approval requires exact owner approve instruction')
        roles = receipt.get('rolesCovered')
        require(isinstance(roles,list) and all(nonblank(r) for r in roles) and set(B.ROLES) <= set(roles),'approval lacks explicitly covered single-maintainer roles')
    else:
        require(not any(k in receipt for k in keys),'pending receipt must not claim owner approval')
    if completion:
        require(receipt['decision'] == 'approved','completion requires exact-byte owner approval and covered roles')

def completion_requested(root,requested):
    for path,key in [(B.SPEC,'status'),(B.ART/'sprint-status.yaml','  5-10-refresh-and-re-disposition-chatbot-and-memories-inventories')]:
        text = (root/path).read_text(encoding='utf-8')
        found = re.findall(r'^'+re.escape(key)+r':\s*[\'"]?([\w-]+)',text,re.M)
        require(len(found) <= 1,'duplicate workflow status '+key.strip())
        requested = requested or found == ['done']
    return requested

def verify_owner_packet(root,completion=False):
    root = Path(root).resolve()
    for path in B.AUTHORITIES:
        require(B.authority_bytes(root,path) == B.git(root,'show',f'{B.BASELINE}:{path}'),f'preserved authority changed: {path}')
    ad = load(root,'ad23510',B.ART/'evidence/story-5-2/verify_class_map.py')
    _,state = ad.verify(root,root/B.AD/'AD-23-capability-class-map.json')
    require(state == 'adopted','AD-23 must remain exactly adopted')
    check_source_drift(root)
    for module,m in B.MODULES.items():
        text = (root/m['new']).read_text()
        old,new = B.parse(B.predecessor_bytes(root,module).decode(),module),B.parse(text,module)
        entries,outcomes = B.class_entries(root,module)
        metadata(module,text)
        accounting(module,old,new,entries)
        check_rows(root,module,old,new,entries,outcomes)
        check_anchors(root,module,old,new)
        require((root/m['new']).read_bytes() == B.candidate(root,module),f'{module}: prose/source premises differ from deterministic derivation')
    import json
    writes = B.packet(root)
    expected,receipt = json.loads(writes[E/'approval.json']),read_json(root/E/'approval.json')
    check_approval(receipt,expected,completion)
    return receipt


def verify(root,completion=False):
    root = Path(root).resolve()
    completion = completion_requested(root,completion) or read_json(root/E/'labels.json').get('state') == 'integrated'
    receipt = verify_owner_packet(root,completion)
    labels = load(root,'labels510verify',E/'verify_labels.py')
    labels.verify(root,completion,owner_checked=True)
    return receipt['decision'],completion


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--approved-completion',action='store_true')
    args = parser.parse_args(argv)
    try:
        decision,completed = verify(args.root,args.approved_completion)
    except (ValueError,KeyError,TypeError,OSError,IndexError,UnicodeError) as error:
        print(f'FAIL: {error}',file=sys.stderr)
        return 1
    print('PASS: chatbot: 48 entries; memories: 55 entries (4 added PS14 modes); pinned anchors/drift, AD-23 dispositions and hash chains')
    remaining = ('integrated PS06/PS07/PS12/PS13/PS14 labels remain a completion gate' if decision == 'approved'
                 else 'owner approval and integrated PS06/PS07/PS12/PS13/PS14 labels remain completion gates')
    print(f'PASS: owner decision: {decision}; '+('approved completion verified' if completed else 'candidate only; '+remaining))
    return 0


if __name__ == '__main__':
    sys.exit(main())
