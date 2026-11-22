#!/usr/bin/env python3
"""Verify prepared bytes; a completion request must also prove independent delivery gates."""
import argparse
from datetime import date
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[4]
E = Path('_bmad-output/implementation-artifacts/evidence/story-5-11')
spec = importlib.util.spec_from_file_location('packet511', ROOT/E/'build_packet.py')
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)


def require(condition, message):
    if not condition: raise ValueError(message)


def nonblank(value):
    return isinstance(value,str) and bool(value.strip())


def read(root,path):
    return json.loads((root/path).read_text())


def checked(root,item):
    require(isinstance(item,dict) and isinstance(item.get('path'),str), 'artifact binding lacks path')
    path = Path(item['path'])
    require(not path.is_absolute() and (root/path).resolve().is_relative_to(root), 'artifact path escapes repository')
    data = (root/path).read_bytes()
    require(B.sha(data) == item.get('sha256'), 'artifact hash mismatch: '+str(path))
    return data


def check_approval(receipt, artifacts, roles, completion=False):
    require(receipt.get('schemaVersion') == '1.0.0' and receipt.get('baselineCommit') == B.BASELINE, 'approval schema/baseline mismatch')
    require(receipt.get('artifacts') == artifacts, 'approval artifact accounting/hash mismatch')
    require(receipt.get('requiredApprovalRoles') == roles, 'approval required-role policy mismatch')
    require(receipt.get('decision') in {'pending','approved'}, 'unknown approval decision')
    keys = ['approver','exactApprovalInstruction','approvalSource','approvedOn','rolesCovered']
    if receipt['decision'] == 'approved':
        require(all(nonblank(receipt.get(k)) for k in keys[:-1]), 'approval lacks identity, words, source or date')
        require(receipt['exactApprovalInstruction'].strip().casefold() == 'approve', 'approval requires explicit exact-byte approve instruction')
        covered = receipt.get('rolesCovered')
        require(isinstance(covered,list) and len(covered) == len(set(covered)) and set(roles) <= set(covered), 'approval lacks explicitly covered roles')
        date.fromisoformat(receipt['approvedOn'])
    else:
        require(not any(k in receipt for k in keys), 'pending receipt must not claim fresh approval')
    if completion: require(receipt['decision'] == 'approved', 'completion requires fresh exact-byte successor approval')


def check_histories(root, inputs):
    histories = inputs.get('inventoryHistories')
    require(isinstance(histories,dict) and set(histories) == set(B.HISTORIES), 'eight-family history accounting mismatch')
    for family,expected in B.HISTORIES.items():
        chain = histories[family]
        require(isinstance(chain,list) and len(chain) == len(expected), family+': missing/duplicate historical version')
        for item,(version,path,receipt) in zip(chain,expected):
            require(item.get('version') == version and item.get('path') == str(B.A/path), family+': version/path history mismatch')
            data = checked(root,item)
            require(re.search(r"^inventory_version:\s*['\"]?"+re.escape(version)+r"['\"]?\s*$",data.decode(),re.M), family+': declared inventory version mismatch')
            source_revision = item.get('sourceRevision')
            require(isinstance(source_revision,str) and re.fullmatch('[0-9a-f]{40}',source_revision) and re.search(r"^source_revision:\s*['\"]?"+source_revision+r"['\"]?\s*$",data.decode(),re.M),family+': full source revision binding missing or mismatched')
            require(isinstance(item.get('sourceRepository'),str) and item['sourceRepository'] in data.decode(),family+': source repository binding missing')
            authority = item.get('approval',{})
            expected_kind = 'session-scope-only' if receipt is None else 'pending' if 'story-5-11' in receipt else 'owning-maintainer-receipt'
            require(authority.get('authority') == expected_kind, family+': earlier/fresh authority conflated')
            expected_status = 'scope-approved-only' if expected_kind=='session-scope-only' else 'candidate-pending' if expected_kind=='pending' else 'owner-approved'
            require(item.get('effectiveStatus') == expected_status,family+': approval versus delivery status conflated')
            if expected_kind == 'pending':
                require(authority.get('receipt') == {'path':str(E/'approval.json')}, family+': own effective-status receipt missing')
            else:
                expected_path = str(B.A/(receipt or path))
                require(authority.get('receipt',{}).get('path') == expected_path, family+': wrong approval receipt')
                checked(root,authority['receipt'])
            if 'story-5-11' not in str(path) and version not in [v2 for _,v2 in B.SUCCESSORS.values()]:
                require(B.git(root,'show',B.BASELINE+':'+item['path']) == data, family+': approved predecessor bytes changed')


def check_successors(root, receipt):
    expected_amendments = []
    for module,(old,new) in B.SUCCESSORS.items():
        oldpath,newpath = B.A/f'{module}-migration-inventory-v{old}.md',B.A/f'{module}-migration-inventory-v{new}.md'
        before,after = (root/oldpath).read_bytes(),(root/newpath).read_bytes()
        require(B.git(root,'show',B.BASELINE+':'+str(oldpath)) == before, module+': immutable predecessor changed')
        require(after == B.successor(module), module+': successor differs from preserved receipt-based derivation')
        oldrows,newrows = B.rows(before.decode()),B.rows(after.decode())
        require(set(oldrows) == set(newrows), module+': row accounting mismatch')
        for key,row in oldrows.items():
            require(set(row) == set(newrows[key]), module+': row fields missing: '+key)
            for field,value in row.items():
                if field == 'Approval' or (module == 'technical-tools' and key.startswith('PS') and field in {'Inventory / scope','Required inventory / migration gate','Removal prerequisite','Operations and inventory','Inventory','Removal gate','Operation inventory','Behavior / migration gate'}): continue
                # Companion citations can change only inside their existing cells; the entire derivation is checked above.
                if module == 'technical-tools' and key.startswith('PS') and ('inventory' in value or 'Admin 1.0.2 G1–G6:' in value): continue
                require(newrows[key][field] == value, module+': preserved field changed: '+key+'/'+field)
        expected_amendments.append({'module':module,'predecessor':{'path':str(oldpath),'sha256':B.sha(before)},'successor':{'path':str(newpath),'sha256':B.sha(after)},'priorApproval':{'path':str(B.A/'evidence/story-5-7/approval.json'),'sha256':B.sha((root/B.A/'evidence/story-5-7/approval.json').read_bytes())},'rows':sorted(newrows)})
    require(receipt.get('amendments') == expected_amendments, 'amendment predecessor/row/approval bindings mismatch')


def check_labels(root, labels):
    require(labels.get('state') in {'candidate','integrated'}, 'unknown label state')
    expected = {}
    for story,binding in zip([7,8,9,10],labels.get('predecessors',[])):
        require(binding.get('path') == str(B.A/f'evidence/story-5-{story}/labels.json'), 'label predecessor path mismatch')
        register = json.loads(checked(root,binding))
        expected.update({row['id']:row for row in register['rows']})
    require(len(labels.get('predecessors',[])) == 4, 'label predecessor chain incomplete')
    rows = labels.get('rows',[])
    require(len(rows) == 14 and {r.get('id') for r in rows} == set(expected), 'fourteen-label accounting/duplicate mismatch')
    inventory = {str(B.A/f'{m}-migration-inventory-v{v}.md'):B.sha((root/B.A/f'{m}-migration-inventory-v{v}.md').read_bytes()) for m,(_,v) in B.SUCCESSORS.items()}
    require(labels.get('inventoryArtifacts') == inventory, 'label successor inventory hash binding mismatch')
    for row in rows:
        prior = expected[row['id']]
        require(all(row.get(k) == prior[k] for k in ['repository','surface','gate']), row['id']+': owner/surface/removal gate changed')
        text = row.get('label',{}).get('text','')
        require(row['label'].get('sha256') == B.sha(text.encode()) and 'technical-tools inventory 1.0.4' in text and inventory[str(B.A/'technical-tools-migration-inventory-v1.0.4.md')] in text, row['id']+': label text/hash/citation mismatch')
        if row['id'] in {'PS01','PS02'}:
            admin = str(B.A/'eventstore-admin-migration-inventory-v1.0.3.md')
            citation = f'[EventStore Admin inventory 1.0.3](https://github.com/Hexalith/Hexalith.McpCli/blob/main/{admin})'
            require(citation in text and f"Admin inventory SHA-256: `{inventory[admin]}`" in text,
                    row['id']+': Admin 1.0.3 label citation/hash missing')
        require(row['gate'] in text, row['id']+': removal gate lost')
        for token in ['necessary but not sufficient','Never counted as retired','never counted as retired','G01–G06','retirement-blocked','FK01–FK04','T01–T04','independent safety gates']:
            if token in prior['label']['text']: require(token in text,row['id']+': retained gate/exemption lost: '+token)
    require(set(labels.get('repositories',[])) == {row['repository'] for row in rows} and len(labels['repositories']) == 7, 'seven README owner accounting mismatch')


def prepared_before(root, owner, file):
    repo = (root/owner['ownerCheckout']).resolve()
    data = B.git(repo,'show',owner['baseRevision']+':'+file['path'])
    require(B.sha(data) == file['sourceSha256'], owner['name']+': source snapshot changed')
    if owner['name'] in {'chatbot','memories'} and file['path'] == 'README.md':
        e = B.A/f"evidence/story-5-10/upstream/{owner['name']}"
        newline = b'\r\n' if b'\r\n' in data else b'\n'
        data = data.replace(b'\r\n',b'\n')
        old = (root/e/'README.before.section.md').read_bytes().replace(b'\r\n',b'\n')
        new = (root/e/'README.after.section.md').read_bytes().replace(b'\r\n',b'\n')
        if old in data: data = data.replace(old,new)
        else: require(new in data, owner['name']+': missing Story 5.10 composition prerequisite')
        data = data.replace(b'\n',newline)
    require(B.sha(data) == file['beforeSha256'], owner['name']+': prepared patch base mismatch')
    return data


def literal_patch(before,patch,path):
    recipe = json.loads(patch)
    require(recipe.get('schemaVersion') == '1.0.0' and recipe.get('path') == path,'literal patch schema/target mismatch')
    data = before.decode()
    for edit in recipe.get('edits',[]):
        require(nonblank(edit.get('old')) and data.count(edit['old']) == 1,'literal patch target missing/duplicated')
        data = data.replace(edit['old'],edit['new'])
    return data.encode()


def check_patches(root, manifest, labels):
    owners = manifest.get('owners',[])
    require(len(owners) == 9 and {o.get('name') for o in owners} == set(B.PATHS)|{'ai-tools'}, 'active owner patch accounting mismatch')
    require(len(manifest.get('noChange',[])) == 8 and {o.get('name') for o in manifest['noChange']} == {'platform','agents','conversations','timesheets','works','builds','commons','polymorphicserializations'}, 'inspected no-change owner accounting mismatch')
    for audit in manifest['noChange']:
        name,revision = audit['name'],audit.get('revision','')
        require(isinstance(revision,str) and re.fullmatch('[0-9a-f]{40}',revision),name+': invalid inspection revision')
        repo = root.parent/name
        if not (repo/'.git').exists():
            title = 'PolymorphicSerializations' if name=='polymorphicserializations' else name.capitalize()
            repo = root/'references'/('Hexalith.'+title)
        B.git(repo,'merge-base','--is-ancestor',revision,'origin/main')
        expected = B.inspect_unchanged(repo,name,B.NO_CHANGE[name],revision)
        require(audit == expected,name+': inspected main paths, hashes or rationale differ')
    for owner in owners:
        name = owner['name']
        expected_repo = root.parent/('aitools' if name=='ai-tools' else name)
        require((root/owner.get('ownerCheckout','')).resolve() == expected_repo, name+': wrong owning checkout')
        require(re.fullmatch('[0-9a-f]{40}',owner.get('baseRevision','')) is not None and owner['baseRevision'] == owner.get('observedOriginMain'), name+': canonical main base missing')
        expected_paths = {'hexalith-llm-instructions.md','hexalith-mcpcli-migration-instructions.md'} if name == 'ai-tools' else {'_bmad-output/planning-artifacts/'+p for p in B.PATHS[name]}|({'README.md'} if name!='tenants' else set())
        require(len(owner.get('files',[])) == len(expected_paths) and {f.get('path') for f in owner['files']} == expected_paths,name+': active-topic file accounting mismatch')
        with tempfile.TemporaryDirectory(prefix='reconciliation-patch-') as temporary:
            scratch = Path(temporary).resolve()
            # A TMPDIR inside a checkout otherwise makes git apply inherit the
            # parent repository and silently skip paths outside its prefix.
            env = {k:v for k,v in os.environ.items() if not k.startswith('GIT_')}
            git = ['git', '-C', str(scratch)]
            initialized = subprocess.run([*git,'init','--quiet'],env=env,capture_output=True)
            require(initialized.returncode == 0, name+': cannot initialize isolated patch repository')
            for file in owner['files']:
                path = scratch/file['path']
                require(path.resolve().is_relative_to(scratch),name+': patch target escapes repository')
                path.parent.mkdir(parents=True,exist_ok=True)
                before = prepared_before(root,owner,file)
                path.write_bytes(before)
                patch = checked(root,file['patch'])
                require(patch and file['afterSha256'] != file['beforeSha256'], name+': empty correction patch')
                if file.get('format') == 'literal-replacements':
                    path.write_bytes(literal_patch(path.read_bytes(),patch,file['path']))
                else:
                    stats = subprocess.run([*git,'apply','--numstat','-z','-'],input=patch,capture_output=True,env=env)
                    names = [entry.split(b'\t',2)[-1] for entry in stats.stdout.split(b'\0') if entry]
                    require(stats.returncode == 0 and names == [file['path'].encode()] and
                            not re.search(rb'^(?:rename|copy) (?:from|to) ',patch,re.M),
                            name+': patch must affect only '+file['path'])
                    result = subprocess.run([*git,'apply','--check','-'],input=patch,capture_output=True,env=env)
                    require(result.returncode == 0,name+': patch does not apply: '+result.stderr.decode().strip())
                    result = subprocess.run([*git,'apply','-'],input=patch,capture_output=True,env=env)
                    require(result.returncode == 0,name+': patch application failed')
                after = path.read_bytes()
                require(B.sha(after) == file['afterSha256'],name+': applied patch bytes differ')
                if name != 'ai-tools':
                    expected = B.corrected_document(name,file['path'],before,labels['rows'])
                    require(after == expected,name+': applied document differs from required corrections: '+file['path'])
                if file['path'] == 'README.md':
                    text = after.decode().replace('\r\n','\n')
                    require(B.setup(name) in text,name+': setup/refusal/discovery or retained-gate guidance lost')
                    for row in labels['rows']:
                        if row['repository'] == name: require(text.count(row['label']['text']) == 1,row['id']+': label missing or duplicated in patch')
                if 'candidate' in file: require(checked(root,file['candidate']) == after,name+': candidate and applied bytes differ')


def check_deferrals(root, audit):
    expected = B.scoped_deferrals((root/B.A/'deferred-work.md').read_text())
    require(audit.get('entries') == expected, 'deferral accounting/source/owner/gate mismatch')
    require(audit.get('state') == 'candidate-awaiting-explicit-owner-decision', 'deferral audit must retain explicit owner-decision gate')
    require(all(e['owner'] and e['gate'] and e['ownerDecision'] is None for e in expected), 'deferral lacks retained owner/gate or invents acceptance')
    text = (root/E/'deferral-dispositions.md').read_text()
    for entry in expected: require(text.count('## '+entry['id']+' —') == 1, 'deferral prose accounting mismatch')


def check_candidate_plan(root, inputs):
    plan = (root/E/'upstream/ai-tools/hexalith-mcpcli-migration-instructions.md').read_text()
    require("plan_version: '1.3.0'" in plan and 'inventory_revision: null' in plan and 'status: candidate-not-publishable' in plan, 'prepared plan must expose missing immutable publication binding')
    for family,chain in inputs['inventoryHistories'].items():
        for item in chain:
            require(item['path'] in plan and item['sha256'] in plan and item['version'] in plan, family+': prepared plan omits version/path/hash')
    check_plan_semantics(plan,'prepared')


def check_plan_semantics(plan,phase):
    tokens = ['G01–G06','restricted/\ndestructive','Folders owners retain the K12','Payload paging versus AD-20','FK01–FK04','forwarded per-user HTTP authority','confidential UI coverage','K13','K14','never counted retired','2027-02-05','Labels + slip',
              'requires a\nversioned inventory amendment and its owning-maintainer approval',
              'Publish every change to this plan under a new `plan_version`',
              '`inventory_revision` whenever an indexed inventory is added or re-pinned']
    for token in tokens:
        require(token in plan,phase+' plan lost independent gate/exemption: '+token)


def check_immutable_links(plan,inputs,revision):
    links = set(re.findall(r'\]\((https?://[^\s)]+)\)',plan))
    paths = {item['path'] for chain in inputs['inventoryHistories'].values() for item in chain}
    paths |= {item['approval']['receipt']['path'] for chain in inputs['inventoryHistories'].values() for item in chain}
    for path in sorted(paths):
        expected = 'https://github.com/Hexalith/Hexalith.McpCli/blob/'+revision+'/'+path
        require(expected in links,'final plan lacks immutable inventory/approval link: '+path)


def check_prior_delivery(root,prior_module=None,register=None):
    # Validate the frozen packet and reuse its delivery checker at its recorded
    # revisions. Current approved supersession is checked independently below.
    if prior_module is None:
        module_spec = importlib.util.spec_from_file_location('prior510reconciliation',root/E.parent/'story-5-10/verify_labels.py')
        prior_module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(prior_module)
    prior = prior_module
    try:
        register = read(root,E.parent/'story-5-10/labels.json') if register is None else register
        require(register.get('state') == 'integrated','completion requires integrated PS06/PS07/PS12/PS13/PS14 labels')
        # The receipt was already approved and published. Verify those bytes at
        # publication; regenerating its source audit needs an unpublished old
        # ChatBot object and is not evidence of label delivery.
        receipt_path = E.parent/'story-5-10/approval.json'
        receipt_bytes = B.git(root,'show',B.BASELINE+':'+str(receipt_path))
        require(receipt_bytes == (root/receipt_path).read_bytes(),'historical Story 5.10 owner receipt differs')
        receipt = json.loads(receipt_bytes)
        prior.V.check_approval(receipt,json.loads(receipt_bytes),True)
        for path,digest in receipt['artifacts'].items():
            published = prior.B.git(root,'show',register['inventoryRevision']+':'+path)
            require(B.sha(published) == digest,'historical Story 5.10 published artifact mismatch: '+path)
        inventory = {str(m['new']):B.sha((root/m['new']).read_bytes()) for m in prior.B.MODULES.values()}
        expected,_ = prior.B.label_candidate(root,inventory)
        for key in ['predecessor','priorRows','inventoryArtifacts','rows']:
            require(register.get(key) == expected[key],'historical Story 5.10 '+key+' binding mismatch')
        repositories = register.get('repositories',[])
        require(len(repositories) == 2 and {r.get('name') for r in repositories} == {'chatbot','memories'},'historical Story 5.10 owner accounting mismatch')
        original_git = prior.B.git
        revisions = {str(root.parent/r['name']):(r.get('integration') or {}).get('commit') for r in repositories}
        revisions[str(root)] = register.get('inventoryRevision')
        def historical_git(repo,*args):
            if args[0] == 'show' and args[1].startswith('origin/main:'):
                revision = revisions.get(str(Path(repo)))
                require(isinstance(revision,str) and re.fullmatch('[0-9a-f]{40}',revision),'historical Story 5.10 published revision missing')
                args = ('show',revision+':'+args[1].split(':',1)[1],*args[2:])
            return original_git(repo,*args)
        try:
            prior.B.git = historical_git
            for repository in repositories:
                target = next(r for r in expected['repositories'] if r['name']==repository['name'])
                require({k:v for k,v in repository.items() if k!='integration'} == {k:v for k,v in target.items() if k!='integration'},'historical Story 5.10 repository binding mismatch')
                before = prior.B.blob(root,repository['name'],'README.md')
                before_section = prior.checked_file(root,repository['before'])
                after_section = prior.checked_file(root,repository['after'])
                checked(root,repository['patch'])
                after = before.replace(before_section,after_section)
                require(B.sha(after) == repository['readme']['afterSha256'],'historical Story 5.10 README reconstruction mismatch')
                local_repo = root.parent/repository['name']
                actual_origin = B.git(local_repo,'remote','get-url','origin').decode().strip()
                require(prior.L57.github_repository(actual_origin) == prior.L57.github_repository(repository['repository']),
                        repository['name']+': historical owner repository mismatch')
                prior.check_delivery(root,register,dict(repository,ownerCheckout=str(local_repo)),before,after)
        finally:
            prior.B.git = original_git
        check_labels(root,read(root,E/'labels.json'))
    except (ValueError,KeyError,TypeError,OSError) as error:
        raise ValueError('Story 5.10 prerequisite delivery incomplete: '+str(error)) from error


def recorded_date(value,message):
    require(isinstance(value,str),message)
    try:
        parsed=date.fromisoformat(value)
        require(parsed.isoformat()==value,message)
        return parsed
    except ValueError as error: raise ValueError(message) from error


def check_assessments(root,integration):
    decision = integration.get('deferralOwnerDecision')
    require(isinstance(decision,dict) and decision.get('decision') == 'accept-audit-preserve-open-gates' and all(nonblank(decision.get(k)) for k in ['owner','source']),'completion requires explicit structured deferral owner decision')
    audit_data = (root/E/'deferral-dispositions.json').read_bytes()
    require(decision.get('auditSha256') == B.sha(audit_data) and decision.get('auditMarkdownSha256') == B.sha((root/E/'deferral-dispositions.md').read_bytes()),'deferral decision must bind exact audit bytes')
    audit = json.loads(audit_data)
    unresolved = {entry['id'] for entry in audit['entries'] if not entry['disposition'].startswith('existing resolution')}
    retained = decision.get('retainedUnresolvedEntryIds')
    require(decision.get('preserveUnresolvedGates') is True and isinstance(retained,list) and len(retained)==len(unresolved) and set(retained)==unresolved,'deferral decision must preserve every unresolved owner/gate')

    notes = [entry for entry in audit['entries'] if entry['id']=='77748cf5a6cb9421']
    require(len(notes)==1,'AC3 release-note disposition missing')
    changed = decision.get('acceptCompletionWithDeferredReleaseNotes') is True
    require(notes[0]['sourceStatus'].startswith('resolved') or changed,
            'AC3 generated release notes remain deferred by the owner')

    completed = recorded_date(integration.get('completedOn'),'recorded completion date missing or invalid')
    require(completed <= date.today(),'recorded completion date is in the future')
    require(recorded_date(decision.get('decidedOn'),'deferral decision date missing') <= completed,'deferral decision occurs after completion')
    assessment = integration.get('sm3Assessment')
    require(isinstance(assessment,dict),'structured SM-3 assessment missing')
    require(recorded_date(assessment.get('assessedOn'),'SM-3 assessment date missing') == completed,'SM-3 assessment must bind recorded completion date')
    require(assessment.get('deadline') == '2027-02-05' and all(nonblank(assessment.get(k)) for k in ['owner','source']),'SM-3 deadline/owner/source missing')
    outcome,retirements = assessment.get('outcome'),assessment.get('retirements')
    require(outcome in {'met','pending-not-met','slip'} and isinstance(retirements,list),'SM-3 outcome/retirement accounting missing')
    if outcome == 'met':
        require(bool(retirements),'SM-3 met requires evidenced retirement')
        # PRD §3 includes proprietary MCP servers and plug-ins, including
        # EventStore Admin MCP. The census records the kind for every PS row.
        census = B.rows((root/B.A/'technical-tools-migration-inventory-v1.0.4.md').read_text())
        servers = {r['surface'] for r in read(root,E/'labels.json')['rows']
                   if 'MCP' in census[r['id']]['Kind and transport'].split()}
        for binding in retirements:
            retirement = json.loads(checked(root,binding))
            require(retirement.get('state') == 'retired' and all(nonblank(retirement.get(k)) for k in ['surface','owner','source']),'SM-3 retirement receipt lacks retired state or authority')
            require(retirement['surface'] in servers,'SM-3 requires an inventoried Legacy Server')
            require(recorded_date(retirement.get('retiredOn'),'retirement date missing') <= min(completed,date(2027,2,5)),'SM-3 retirement must occur by its deadline and assessment')
    else:
        require(not retirements,'SM-3 pending/slip must not claim retirement')
        if completed > date(2027,2,5):
            require(outcome == 'slip' and nonblank(assessment.get('ownerReason')),'overdue SM-3 requires explicit owner slip reason')
        else:
            require(outcome == 'pending-not-met','pre-deadline unmet SM-3 remains pending')


def check_published_index(root, plan, inputs, revision):
    check_immutable_links(plan,inputs,revision)
    receipts = {}
    table = [line.strip('|').split('|') for line in plan.splitlines() if line.startswith('|')]
    for family,chain in inputs['inventoryHistories'].items():
        for item in chain:
            path,digest = item['path'],item['sha256']
            require(B.sha(B.git(root,'show',revision+':'+path)) == digest,
                    'linked inventory bytes differ: '+path)
            authority = item['approval']
            ref = authority['receipt']
            receipt_path = ref['path']
            if receipt_path not in receipts:
                raw = B.git(root,'show',revision+':'+receipt_path)
                expected = ref.get('sha256') or B.sha((root/receipt_path).read_bytes())
                require(B.sha(raw)==expected,'linked receipt bytes differ: '+receipt_path)
                receipts[receipt_path] = raw
            if authority['authority']=='session-scope-only':
                status = 'scope-approved-only; session-scope-only'
            else:
                raw = receipts[receipt_path]
                approved = json.loads(raw)
                require(approved.get('decision')=='approved' and digest.encode() in raw,
                        'published receipt lacks approval for '+path)
                status = 'owner-approved; owning-maintainer-receipt'
            entries = [cells for cells in table if len(cells)==5 and cells[0].strip()==family and cells[1].strip()==item['version']]
            require(len(entries)==1 and path in entries[0][2] and digest in entries[0][3] and
                    entries[0][4].strip().startswith(status+':') and receipt_path in entries[0][4],
                    family+' '+item['version']+': final inventory row authority/path/hash mismatch')


def rebased_document_hash(repo, commit, owner, file, rebase, labels):
    path = file['path']
    parent = B.git(repo, 'rev-parse', commit+'^').decode().strip()
    require(rebase.get('base') == parent and nonblank(rebase.get('publicationInstruction')) and
            rebase.get('reviewedAfterSha256') == file['afterSha256'] and
            rebase.get('patchSha256') == file['patch']['sha256'], 'rebased document approval or patch binding differs: '+path)
    before = B.git(repo, 'show', parent+':'+path)
    require(B.sha(before) == rebase.get('beforeSha256'), 'rebased document base differs: '+path)
    # Replay the reviewed corrections on the actual parent so unrelated upstream edits survive.
    after = B.corrected_document(owner, path, before, labels['rows'])
    require(B.sha(after) == rebase.get('afterSha256'), 'rebased document differs from reviewed corrections: '+path)
    return B.sha(after)


def check_delivery(root, receipt, labels, manifest, integration):
    require(receipt.get('decision') == 'approved', 'completion requires fresh exact-byte successor approval')
    check_prior_delivery(root)
    require(integration.get('state') in {'delivered','integrated'},'completion requires integrated plan and all fourteen labels')
    authorization = integration.get('deliveryAuthorization')
    require(isinstance(authorization,dict) and all(nonblank(authorization.get(k)) for k in ['source','approvedOn','exactWords']),
            'completion requires separate explicit Git delivery authorization')
    words = authorization['exactWords'].strip().casefold().rstrip('.\\')
    push_requests = {'push all changes', 'push all changes of all repositories to main'}
    require(words == 'authorize' or (words in push_requests and nonblank(authorization.get('footprint'))),
            'completion requires separate explicit Git delivery authorization')
    inventory_revision = integration.get('inventoryRevision')
    require(isinstance(inventory_revision,str) and re.fullmatch('[0-9a-f]{40}',inventory_revision), 'completion requires full published inventory revision')
    B.git(root,'merge-base','--is-ancestor',inventory_revision,'origin/main')
    for path,digest in receipt['artifacts'].items():
        require(B.sha(B.git(root,'show',inventory_revision+':'+path)) == digest, 'published approved artifact bytes mismatch: '+path)
    require(B.git(root,'show',inventory_revision+':'+str(E/'approval.json')) == (root/E/'approval.json').read_bytes(), 'published receipt bytes mismatch')
    deliveries = integration.get('ownerIntegrations',[])
    require(len(deliveries) == len(manifest['owners']) and {d.get('name') for d in deliveries} == {o['name'] for o in manifest['owners']}, 'completion requires every owner integration binding')
    for owner in manifest['owners']:
        delivered = next(d for d in deliveries if d['name'] == owner['name'])
        require(isinstance(delivered,dict) and isinstance(delivered.get('commit'),str) and re.fullmatch('[0-9a-f]{40}',delivered['commit']),owner['name']+': upstream integration missing')
        repo,commit = (root/owner['ownerCheckout']).resolve(),delivered['commit']
        B.git(repo,'merge-base','--is-ancestor',commit,'origin/main')
        for file in owner['files']:
            target_hash = integration.get('planSha256') if file['path']=='hexalith-mcpcli-migration-instructions.md' else file['afterSha256']
            for rebase in delivered.get('rebasedFiles', []):
                if rebase['path'] == file['path'] and owner['name'] != 'ai-tools':
                    target_hash = rebased_document_hash(repo, commit, owner['name'], file, rebase, labels)
            require(B.sha(B.git(repo,'show',commit+':'+file['path'])) == target_hash,owner['name']+': integrated documentation bytes mismatch')
            require(B.sha(B.git(repo,'show','origin/main:'+file['path'])) == target_hash,owner['name']+': current main documentation drift')
        checks = delivered.get('checks',{})
        builds_ok = checks.get('builds') == 'passed'
        if checks.get('builds') == 'not applicable; owning repository has not adopted Hexalith.CiCd':
            builds_ok = not B.git(repo,'ls-tree','--name-only',commit,'--','.github/hexalith-ci.json').strip()
        require(checks.get('commitlint') == 'passed' and builds_ok,owner['name']+': mandatory commitlint/Builds checks missing')
    ai = integration.get('aiToolsCommit')
    require(isinstance(ai,str) and re.fullmatch('[0-9a-f]{40}',ai),'completion requires full AI.Tools integration revision')
    ai_delivery = next((d for d in deliveries if d['name']=='ai-tools'),None)
    require(isinstance(ai_delivery,dict) and ai_delivery.get('commit') == ai,'AI.Tools revision differs from actual owner integration')
    containing = integration.get('rootIntegrationRevision')
    require(isinstance(containing,str) and re.fullmatch('[0-9a-f]{40}',containing),'committed root integration revision missing')
    B.git(root,'merge-base','--is-ancestor',containing,'origin/main')
    tree = B.git(root,'ls-tree',containing,'references/Hexalith.AI.Tools').decode().split()
    require(len(tree)==4 and tree[:2]==['160000','commit'] and tree[3]=='references/Hexalith.AI.Tools' and re.fullmatch('[0-9a-f]{40}',tree[2]),'committed AI.Tools gitlink missing')
    gitlink = tree[2]
    require(gitlink == integration.get('aiToolsGitlink'), 'containing AI.Tools gitlink missing')
    B.git(root.parent/'aitools','merge-base','--is-ancestor',ai,gitlink)
    plan = B.git(root.parent/'aitools','show',ai+':hexalith-mcpcli-migration-instructions.md')
    for file in ['hexalith-mcpcli-migration-instructions.md','hexalith-llm-instructions.md']:
        merged = plan if file.startswith('hexalith-mcpcli') else B.git(root.parent/'aitools','show',ai+':'+file)
        require(B.git(root.parent/'aitools','show',gitlink+':'+file)==merged,'committed AI.Tools gitlink differs: '+file)
    frontmatter = plan.decode().split('---',2)
    require(len(frontmatter)==3 and not frontmatter[0] and B.sha(plan)==integration.get('planSha256'),
            'exact plan bytes/publication binding missing')
    metadata = frontmatter[1].splitlines()
    require([line for line in metadata if line.startswith('inventory_revision:')] == [f"inventory_revision: '{inventory_revision}'"],
            'exact plan bytes/publication binding missing')
    wording = ' '.join(plan.decode().lower().split())
    candidate_markers = ['candidate-not-publishable','1.3.0 candidate','inventory_revision: null','never publish this candidate',
                         'not the authoritative plan until','before approval of final plan bytes','missing publication binding',
                         'bind final plan bytes','/blob/<sha>/']
    require([line for line in metadata if line.startswith('plan_version:')] == ["plan_version: '1.3.0'"] and
            not any(marker in wording for marker in candidate_markers),'completion requires final plan 1.3.0 bytes')
    check_plan_semantics(plan.decode(),'final approved')
    final_approval = json.loads(checked(root,integration.get('finalPlanApproval')))
    require(final_approval.get('decision') == 'approved' and final_approval.get('planSha256') == B.sha(plan) and final_approval.get('inventoryRevision') == inventory_revision, 'final plan exact-byte approval/hash/revision binding missing')
    require(all(nonblank(final_approval.get(k)) for k in ['approver','exactApprovalInstruction','approvalSource','approvedOn']) and final_approval['exactApprovalInstruction'].strip().casefold() == 'approve', 'final plan approval lacks explicit owner instruction')
    require(set(receipt['requiredApprovalRoles']) <= set(final_approval.get('rolesCovered',[])), 'final plan approval lacks covered roles')
    inputs = read(root,E/'inputs.json')
    check_published_index(root,plan.decode(),inputs,inventory_revision)
    paths = ['AGENTS.md','CLAUDE.md','.github/copilot-instructions.md']
    committed = [B.git(root,'show',containing+':'+path) for path in paths]
    require(committed[0] == committed[1] == committed[2], 'committed root agent instructions differ')
    entries = [(root/p).read_bytes() for p in paths]
    require(entries[0] == entries[1] == entries[2], 'agent instructions differ')
    result = subprocess.run(['bash','scripts/check-agent-instructions-sync.sh'],cwd=root,capture_output=True)
    require(result.returncode == 0 and integration.get('instructionSync') == 'passed','passing instruction synchronization binding missing')


def check_completion(root, receipt, labels, manifest, integration):
    check_delivery(root,receipt,labels,manifest,integration)
    check_assessments(root,integration)


def verify(root=ROOT, completion=False):
    root = Path(root).resolve()
    receipt,inputs,labels,manifest,audit,integration = [read(root,E/p) for p in ['approval.json','inputs.json','labels.json','upstream/manifest.json','deferral-dispositions.json','integration.json']]
    status = (root/B.SPEC).read_text()
    sprint = (root/B.A/'sprint-status.yaml').read_text()
    completion = completion or bool(re.search(r'^status: [\'\"]?done',status,re.M)) or bool(re.search(r'^  5-11-reconcile-product-claims-and-the-migration-plan: done',sprint,re.M)) or integration.get('state') == 'integrated' or labels.get('state') == 'integrated'
    for binding in inputs.get('authorities',[]):
        data = checked(root,binding)
        require(B.git(root,'show',B.BASELINE+':'+binding['path']) == data,'adopted AD-23/authority bytes changed')
    authority_paths = {str(B.AD/p) for p in ['AD-23-non-gateway-capability-classes.md','AD-23-capability-class-map.json']}|{str(B.A/'evidence/story-5-2'/p) for p in ['approval.json','main-integration.json']}
    require(len(inputs.get('authorities',[])) == 4 and {b['path'] for b in inputs['authorities']} == authority_paths,'adopted authority binding incomplete')
    priors = inputs.get('priorApprovals',[])
    require(len(priors) == 4 and {b.get('path') for b in priors} == {str(B.A/f'evidence/story-5-{s}/approval.json') for s in [7,8,9,10]}, 'prior approval binding incomplete')
    for binding in priors:
        data = checked(root,binding)
        require(data == B.git(root,'show',B.BASELINE+':'+binding['path']), 'prior approval bytes changed')
        prior = json.loads(data)
        require(prior.get('decision') == 'approved' and set(prior['requiredApprovalRoles']) <= set(prior.get('rolesCovered',[])), 'prior approval lacks decision or covered roles')
    prior_register = read(root,E.parent/'story-5-10/labels.json')
    bound = inputs.get('prerequisites',{}).get('story510',{})
    for key in ('labels','approval'):
        path = E.parent/'story-5-10'/(key+'.json')
        require(bound.get(key) == {'path':str(path),'sha256':B.sha((root/path).read_bytes())},
                'Story 5.10 '+key+' binding mismatch')
    require(bound.get('state') == 'approved-and-delivered' and prior_register.get('state') == 'integrated' and
            bound.get('inventoryRevision') == prior_register['inventoryRevision'] and
            bound.get('ownerIntegrations') == {r['name']:r['integration']['commit'] for r in prior_register['repositories']},
            'Story 5.10 delivery binding mismatch')
    check_histories(root,inputs)
    check_successors(root,receipt)
    check_labels(root,labels)
    check_patches(root,manifest,labels)
    check_deferrals(root,audit)
    check_candidate_plan(root,inputs)
    artifacts = {str(B.A/f'{m}-migration-inventory-v{v}.md'):B.sha((root/B.A/f'{m}-migration-inventory-v{v}.md').read_bytes()) for m,(_,v) in B.SUCCESSORS.items()}
    for path in [E/'inputs.json',E/'labels.json',E/'upstream/manifest.json',E/'deferral-dispositions.md',E/'deferral-dispositions.json']:
        artifacts[str(path)] = B.sha((root/path).read_bytes())
    for owner in manifest['owners']:
        for file in owner['files']:
            for key in ['patch','candidate']:
                if key in file: artifacts[file[key]['path']] = file[key]['sha256']
    roles = read(root,B.A/'evidence/story-5-7/approval.json')['requiredApprovalRoles']+['Tenants owning maintainer']
    check_approval(receipt,artifacts,roles,completion)
    require(integration.get('state') in {'blocked','delivered','integrated'}, 'unknown integration state')
    if completion: check_completion(root,receipt,labels,manifest,integration)
    else:
        require(labels.get('inventoryRevision') is None and labels.get('deliveryAuthorization') is None and all(o.get('integration') is None for o in manifest['owners']), 'candidate must not claim delivered publication or labels')
        if integration['state'] == 'delivered':
            check_delivery(root,receipt,labels,manifest,integration)
    return receipt['decision'], integration['state'] in {'delivered','integrated'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--approved-completion',action='store_true')
    args = parser.parse_args(argv)
    try: decision,delivery_verified = verify(args.root,args.approved_completion)
    except (ValueError,KeyError,TypeError,OSError,IndexError,UnicodeError) as error:
        print('FAIL: '+str(error),file=sys.stderr)
        return 1
    print('PASS: eight inventory histories; preserved AD-23/predecessors; fourteen labels; nine owner patch sets; scoped deferral accounting')
    if delivery_verified:
        status = 'approved integration verified'
    elif decision == 'approved':
        status = 'packet approved; publication and upstream integration pending'
    else:
        status = 'candidate only; approval, publication and upstream integration remain gates'
    print('PASS: decision: '+decision+'; '+status)
    return 0


if __name__ == '__main__':
    sys.exit(main())
