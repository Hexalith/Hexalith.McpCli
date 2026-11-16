#!/usr/bin/env python3
"""Verify pending successors; completion also requires exact approval and delivered labels.

Read-only static documentary checks. No fetch, Git mutation or live operation.
"""
import argparse
import importlib.util
import io
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[4]
E = Path('_bmad-output/implementation-artifacts/evidence/story-5-9')


def load(root,name,path):
    spec = importlib.util.spec_from_file_location(name,root/path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


B = load(ROOT,'builder59verify',E/'build_candidate.py')
read_json = B.read_json
COUNTS = {'projects':dict(T=4,R=11,M=5,L=18,V=12,G=6),
          'frontcomposer':dict(H=3,D=13,C=2,V=8,G=4)}


def require(condition,message):
    if not condition:
        raise ValueError(message)


def nonblank(value):
    return isinstance(value,str) and bool(value.strip())


def fields(row):
    return dict(zip(row['headers'],row['cells']))


def accounting(module,old,new,entries):
    expected = {f'{p}{i}' if p == 'G' else f'{p}{i:02d}' for p,n in COUNTS[module].items() for i in range(1,n+1)}
    require(set(old) == set(new) == set(entries) == expected,
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
    expected = dict(inventory_version=m['version'],status='pending',module=module,
                    source_repository='https://github.com/Hexalith/Hexalith.'+m['title'],source_revision=m['pin'],
                    source_spec=str(B.SPEC),predecessor=str(m['old']),approval_ref='#a2-amendment-approval-pending')
    require(values == expected,f'{module}: metadata/pin/approval-state mismatch')


def check_rows(module,old,new,entries,outcomes,decl):
    for key,row in new.items():
        f,klass = fields(row),entries[key]
        prefix = f'{module}:{key} ({klass})'
        require(row['headers'][-len(B.EXTRA):] == B.EXTRA,prefix+': amendment columns damaged')
        require(f['Capability class'] == klass and f['Adopted outcome'] == outcomes.get(klass,'Scope accounting; no independent capability outcome'),prefix+': AD-23 class/outcome mismatch')
        decision,coverage = f['Amendment disposition'],f['Amendment coverage']
        require(decision in {'replace','defer','withdraw'} and coverage in {'include','exclude'} and ((decision == 'replace') == (coverage == 'include')),prefix+': include requires replace and replace requires include')
        expected = 'replace' if module == 'projects' and key in B.MAPPING else 'withdraw' if klass in {'K07','K08','K12','K13','K15'} else 'defer'
        require(decision == expected,prefix+': disposition contradicts class/approved target decision')
        require(nonblank(f['Amendment rationale or gap']) and nonblank(f['Amendment owner']),prefix+': rationale/gap and owner required')
        why = f['Amendment rationale or gap']
        if decision == 'withdraw':
            require(all(t in why for t in ['Owner rationale:','Replacement experience:','Accepted loss:']),prefix+': withdrawal lacks rationale, replacement experience or accepted loss')
        if decision == 'defer':
            require('gap:' in why.lower() and f['Amendment owner'] != 'none',prefix+': deferral lacks named gap or owner')
        if decision == 'replace':
            require(module == 'projects' and key in B.MAPPING and all(t in decl for t in B.MAPPING[key]),prefix+': replacement lacks decorated target')
            require(B.READ_GAPS in why,prefix+': publication/live/cutover gates missing')
        if klass == 'K12':
            require('confidential Web/Chatbot UI' in why and 'Projects 7.6–7.14' in why,prefix+': K12 confidential UI evidence gate missing')
        if klass == 'K13':
            require(all(t in why for t in ['1.2.0','Retained','never counted retired']),prefix+': K13 retained exemption missing')
        if module == 'projects' and key in {'T01','R01','L01','V01','G1','G3'}:
            require(B.PAGING_GAP in why,prefix+': K03/AD-20 Payload/Envelope conformity gap missing')
        if module == 'projects' and key == 'V09':
            require('no Query extension channel' in why and 'T01–T04 need no task context' in why,prefix+': task/actor channel gap missing')
        if module == 'frontcomposer' and decision == 'replace':
            require(B.FV_PARITY in why,prefix+': FV04/FV08 parity clarification missing')
        require(f['Exact replacement'] == B.replacement(module,key,klass,decl),prefix+': exact decorated type/wire/Gateway route/eligibility or replacement experience mismatch')
        require(why == B.rationale(module,key,klass) and f['Amendment owner'] == B.owner(module,klass),prefix+': required owner/gap/loss changed')
        require(f['Drift'] == B.drift(module,key),prefix+': drift status missing or incorrect')
        for h in ['Approval','Approval reference']:
            if h in f: require(f[h] == B.APPROVAL,prefix+': approval reference missing')
        require(row['cells'][0:2] == old[key]['cells'][0:2] or key.startswith(('G','V')),prefix+': predecessor identity changed')
        for h in ['Disposition','Coverage','Disposition / coverage']:
            if h in f:
                value = decision if h == 'Disposition' else coverage if h == 'Coverage' else decision+' / '+coverage
                require(f[h] == value,prefix+': legacy and amendment disposition disagree')
        if (module,key) in {('projects','G6'),('frontcomposer','G4')}:
            require(B.COUPLED in why,prefix+': coupled FK01–FK04/K12/K13 retirement gate missing')


def check_anchors(root,module,old,new,decl):
    for key,row in new.items():
        cell = fields(row)['Pinned evidence']
        expected = B.evidence(root,module,key,old[key],decl)
        require(cell == '`'+'`; `'.join(expected)+'`',f'{module}:{key}: pinned anchor identity mismatch')
        anchors = re.findall(r'`([^`]+):(\d+)`',cell)
        require(bool(anchors),f'{module}:{key}: pinned anchor missing')
        for path,line in anchors:
            require(not Path(path).is_absolute() and '..' not in Path(path).parts,f'{module}:{key}: source anchor escapes repository')
            lines = B.source(root,module,path).splitlines()
            require(0 < int(line) <= len(lines) and lines[int(line)-1].strip(),f'{module}:{key}: unresolvable anchor {path}:{line}')


def check_declarations(root,decl):
    module = B.source(root,'projects','src/Hexalith.Projects.Contracts/ProjectsMcpCliModule.cs')
    require('[assembly: HexalithModule("projects",' in module and 'IdentifierKind.String' in module,'projects: decorated module/String kind missing')
    expected_names = ['projects.list','projects.describe','projects.trace-conversation','projects.trace-attachments']
    for (key,d),canonical in zip(decl.items(),expected_names):
        text = d['source']
        name = B.TARGETS[key]
        require('[HexalithQuery(' in text and f'public sealed record {name}(' in text,f'projects:{key}: absent or undecorated replacement type')
        wire = 'Hexalith.Projects.Queries.'+name.removesuffix('Query')+'.v1'
        require(d['name'] == canonical and d['wire'] == wire and 'Domain = "projects"' in text and 'WireType = QueryType' in text,f'projects:{key}: decorated canonical name/wire/domain mismatch')
        require(d['aggregate'] == ('caller --aggregate-id' if key == 'T02' else 'projects') and 'ProjectionType =' not in text and 'ProjectionActorType =' not in text,f'projects:{key}: aggregate or projection route mismatch')
    paths = B.git(root/B.repo('projects'),'ls-tree','-r','--name-only',B.MODULES['projects']['pin'],'src/Hexalith.Projects.Contracts/Commands').decode().splitlines()
    require(all('[HexalithCommand(' not in B.source(root,'projects',p) for p in paths if p.endswith('.cs')),'projects: unexpected decorated Command; restriction precedence requires owner reconciliation')
    targets = read_json(root/'tools/inventory-coverage/v1/projects-approved.json')['targets']
    require({r['id']:(r['name'],r['contractType']) for r in targets} == {k:(d['name'],d['clr']) for k,d in decl.items()},'projects: enrolled candidate target declarations mismatch')
    policy = read_json(root/'tools/dependency-policy.json')
    require(policy['modules'].get('Hexalith.Projects.Contracts') == '2.0.0-story66.3','projects: enrolled candidate package/version mismatch')
    declared_versions = ET.parse(root/'Directory.Build.props').findall('.//HexalithProjectsVersion')
    require(len(declared_versions) == 1 and declared_versions[0].text == policy['modules']['Hexalith.Projects.Contracts'],
            'projects: Directory.Build.props candidate version mismatch')
    project = (root/'src/Hexalith.McpCli/Hexalith.McpCli.csproj').read_text(encoding='utf-8')
    require('<PackageReference Include="Hexalith.Projects.Contracts" HexalithContracts="true" />' in project,'projects: versionless enrolled Contracts candidate missing')
    # Exact package and the owner-recorded resolved closure come from immutable Git objects.
    with zipfile.ZipFile(io.BytesIO(B.blob(root,'projects',B.PACKAGE))) as package:
        names = [n for n in package.namelist() if n.endswith('.nuspec')]
        require(len(names) == 1,'projects: candidate nuspec missing or duplicated')
        nuspec = ET.fromstring(package.read(names[0]))
        values = {e.tag.rsplit('}',1)[-1]:e.text for e in nuspec.iter() if e.tag.rsplit('}',1)[-1] in {'id','version'}}
        dependencies = {e.attrib['id']:e.attrib['version'] for e in nuspec.iter() if e.tag.rsplit('}',1)[-1] == 'dependency'}
        require(values == dict(id='Hexalith.Projects.Contracts',version='2.0.0-story66.3'),'projects: pinned candidate package identity mismatch')
        require(dependencies == {'Hexalith.EventStore.Contracts':'5.1.0','Hexalith.McpCli.Abstractions':'2.0.1','ByteAether.Ulid':'1.4.2','Hexalith.Commons.UniqueIds':'3.0.0'} and not any(e.tag.rsplit('}',1)[-1] in {'frameworkReference','frameworkAssembly'} for e in nuspec.iter()),'projects: candidate adds unapproved or framework dependencies')
    import json
    closure = json.loads(B.blob(root,'projects',B.CLOSURE))
    expected = dict(policy['baselinePackages'])
    expected[policy['decorationPackage']['id']] = policy['decorationPackage']['version']
    for identity in closure['libraries']:
        name,version = identity.rsplit('/',1)
        require(expected.get(name) == version,f'projects: candidate closure violates dependency policy: {name}/{version}')
    require(set(closure['libraries']) == {'ByteAether.Ulid/1.4.2','Hexalith.Commons.UniqueIds/3.0.0','Hexalith.EventStore.Contracts/5.1.0','Hexalith.McpCli.Abstractions/2.0.1'},'projects: candidate closure accounting mismatch')
    executor = (root/'src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs').read_text(encoding='utf-8')
    require('operation.Routing.ProjectionType, rebuilt.ValueKind == JsonValueKind.Null ? null : rebuilt' in executor and 'new QueryPagingOptions(run.PageSize, run.Offset, run.Cursor)' in executor,'projects: independent Payload/Envelope submission evidence mismatch')


def check_consumers(root):
    links,hits = B.consumers(root)
    allowed = {'references/Hexalith.Projects','references/Hexalith.FrontComposer','references/Hexalith.Parties'}
    require({h[0] for h in hits} <= allowed,'coupled gate: additional root host/dependency consumer requires inventory')
    for path,pin,file,line,text in hits:
        if path.endswith('Projects'):
            require(file.startswith('src/Hexalith.Projects.Mcp/'),f'coupled gate: unaccounted Projects consumer {file}')
        if path.endswith('Parties'):
            require(file == 'src/Hexalith.Parties.UI/Hexalith.Parties.UI.csproj',f'coupled gate: unaccounted Parties consumer {file}')
        if path.endswith('FrontComposer'):
            allowed_prefixes = ('src/Hexalith.FrontComposer.Mcp/','samples/Counter/Counter.Web/',
                                'tests/Hexalith.FrontComposer.Mcp.Tests/','tests/Hexalith.FrontComposer.Shell.Tests.Bench/',
                                'tests/Hexalith.FrontComposer.SourceTools.Tests/','tests/Hexalith.FrontComposer.Shell.Tests/Samples/CounterMcpSampleAccessTests.cs')
            require(file.startswith(allowed_prefixes),f'coupled gate: unaccounted FrontComposer consumer {file}')


def check_source_drift(root):
    projects = B.MODULES['projects']
    stable = ['src/Hexalith.Projects.Mcp','src/Hexalith.Projects.Cli',
              'src/Hexalith.Projects.Server/EventStoreProjectCommandSubmitter.cs',
              'src/Hexalith.Projects.Contracts/Commands',
              'src/Hexalith.Projects.Client/Diagnostics/ProjectWarningScanWindow.cs']
    require(B.git(root/B.repo('projects'),'diff','--name-only',projects['oldpin'],projects['pin'],'--',*stable) == b'',
            'projects: claimed unchanged legacy source has drifted')
    B.git(root/B.repo('projects'),'merge-base','--is-ancestor','ce71717a965eb21454b3e13068b9072404dac5f5',projects['pin'])
    front = B.MODULES['frontcomposer']
    require(B.git(root/B.repo('frontcomposer'),'merge-base',front['oldpin'],front['pin']).decode().strip() == 'b06f86d554363ea5b8192cbc149a75c820dab2b8',
            'frontcomposer: historical merge-base comparison differs')
    require(B.git(root/B.repo('frontcomposer'),'diff','--name-only','11c8377a',front['pin'],'--',
                  'src/Hexalith.FrontComposer.Mcp','src/Hexalith.FrontComposer.Cli',
                  'docs/skills/frontcomposer','samples/Counter/Counter.Web') == b'',
            'frontcomposer: source changed after the stated comparison revision')
    checks = [
        ('frontcomposer','src/Hexalith.FrontComposer.Mcp/Invocation/FrontComposerMcpLifecycleStore.cs',['existing.IsOwnedBy(creator)','TenantId']),
        ('frontcomposer','src/Hexalith.FrontComposer.Mcp/Extensions/FrontComposerMcpEndpointRouteBuilderExtensions.cs',['.RequireAuthenticatedUser()']),
        ('frontcomposer','src/Hexalith.FrontComposer.Mcp/HttpFrontComposerMcpAgentContextAccessor.cs',['HasConflictingClaim(http.User']),
        ('frontcomposer','src/Hexalith.FrontComposer.Cli/WriteSafetyPolicy.cs',['HasLinkedPathSegment','HasNestedRepositorySegment']),
        ('projects','src/Hexalith.Projects.Server/Queries/ProjectQueryRequestPreamble.cs',['BeginQueryRequest','ValidateQueryRequest','Idempotency-Key']),
        ('projects','src/Hexalith.Projects.Server/Queries/ResolveProjectFromAttachmentsEndpoint.cs',['.ListByReferenceAsync(authoritativeTenantId, acceptedFolders, [],','AuthorizeLegacyResolutionCandidatesAsync']),
        ('projects','src/Hexalith.Projects.Server/Authorization/ProjectAuthorizationGate.cs',['taskId: null']),
        ('projects','src/Hexalith.Projects.Server/ProjectsServerServiceCollectionExtensions.cs',[n+'QueryHandler>' for n in ['ListProjects','GetProject','ResolveProjectFromConversation','ResolveProjectFromAttachments']]),
    ]
    for module,path,needles in checks:
        text=B.source(root,module,path)
        require(all(n in text for n in needles),f'{module}: corrected source premise missing: {path}')


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
    for path,key in [(B.SPEC,'status'),(B.ART/'sprint-status.yaml','  5-9-refresh-and-re-disposition-projects-and-frontcomposer-invent')]:
        text = (root/path).read_text(encoding='utf-8')
        found = re.findall(r'^'+re.escape(key)+r':\s*[\'"]?([\w-]+)',text,re.M)
        require(len(found) <= 1,'duplicate workflow status '+key.strip())
        requested = requested or found == ['done']
    return requested


def verify_owner_packet(root,completion=False):
    root = Path(root).resolve()
    for path in B.AUTHORITIES:
        if path == B.MODULES['projects']['old']:
            current = (root/path).read_bytes()
            require(current == B.git(root,'show',f'HEAD:{path}'),f'preserved authority changed: {path}')
            require(B.parse(current.decode('utf-8'),'projects') == B.parse(B.predecessor_bytes(root,'projects').decode('utf-8'),'projects'),
                    'projects: committed predecessor rows differ from the approved baseline')
        require(B.authority_bytes(root,path) == B.git(root,'show',f'{B.BASELINE}:{path}'),f'preserved authority changed: {path}')
    for module,m in B.MODULES.items():
        link = B.git(root,'ls-tree',B.BASELINE,str(B.repo(module))).decode().split()[2]
        require(link == m['pin'],f'{module}: approval-time root gitlink pin mismatch')
    ad = load(root,'ad2359',B.ART/'evidence/story-5-2/verify_class_map.py')
    _,state = ad.verify(root,root/B.AD/'AD-23-capability-class-map.json')
    require(state == 'adopted','AD-23 must remain exactly adopted')
    decl = B.declarations(root)
    check_declarations(root,decl)
    check_consumers(root)
    check_source_drift(root)
    for module,m in B.MODULES.items():
        text = (root/m['new']).read_text(encoding='utf-8')
        old,new = B.parse(B.predecessor_bytes(root,module).decode('utf-8'),module),B.parse(text,module)
        entries,outcomes = B.class_entries(root,module)
        metadata(module,text)
        accounting(module,old,new,entries)
        check_rows(module,old,new,entries,outcomes,decl)
        check_anchors(root,module,old,new,decl)
        require((root/m['new']).read_bytes() == B.candidate(root,module),f'{module}: prose/source premises differ from deterministic derivation')
    writes = B.packet(root)
    import json
    expected = json.loads(writes[E/'approval.json'])
    receipt = read_json(root/E/'approval.json')
    check_approval(receipt,expected,completion)
    return receipt


def verify(root,completion=False):
    root = Path(root).resolve()
    completion = completion_requested(root,completion) or read_json(root/E/'labels.json').get('state') == 'integrated'
    receipt = verify_owner_packet(root,completion)
    labels = load(root,'labels59verify',E/'verify_labels.py')
    labels.verify(root,completion,owner_checked=True)
    return receipt['decision'],completion


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--approved-completion',action='store_true')
    args = parser.parse_args(argv)
    try:
        decision,completed = verify(args.root,args.approved_completion)
    except (ValueError,KeyError,TypeError,OSError,IndexError,UnicodeError,ET.ParseError,zipfile.BadZipFile) as error:
        print(f'FAIL: {error}',file=sys.stderr)
        return 1
    print('PASS: projects: 56 entries; frontcomposer: 30 entries; pinned declarations/anchors/drift, AD-23 dispositions and hash chains')
    print(f'PASS: owner decision: {decision}; '+('approved completion verified' if completed else 'candidate only; owner approval and integrated PS03/PS04/PS08/PS09 labels remain completion gates'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
