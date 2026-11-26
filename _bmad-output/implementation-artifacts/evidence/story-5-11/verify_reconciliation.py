#!/usr/bin/env python3
"""Verify prepared bytes; a completion request must also prove independent delivery gates."""
import argparse
from datetime import date, datetime, timezone
from difflib import SequenceMatcher
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
INVENTORY_PUBLICATION = 'c6a40c10fd6db19cfce4cb0592f3b82bbb853729'
PUBLICATION_RECORD = '91abf6df53a9f415e0c8be06e17aaf7c42ec55ac'
FINAL_INTEGRATION_RECORD = 'efc7f815937bbe116d410b59ecf15b4b4fb951cc'
LEDGER = E.parents[1]/'deferred-work.md'
RELEASE_NOTES_ENTRY = '77748cf5a6cb9421'
ROOT_REPOSITORY = 'https://github.com/Hexalith/Hexalith.McpCli'
AI_TOOLS_GITLINK = 'references/Hexalith.AI.Tools'
PLAN_PATH = 'hexalith-mcpcli-migration-instructions.md'
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
    keys = ['approver','exactApprovalInstruction','approvalSource','approvedOn','rolesCovered',
            'exactRoleConfirmation','reviewedReceiptSha256']
    if receipt['decision'] == 'approved':
        require(all(nonblank(receipt.get(k)) for k in keys[:4]), 'approval lacks identity, words, source or date')
        require(receipt['exactApprovalInstruction'].strip().casefold() == 'approve', 'approval requires explicit exact-byte approve instruction')
        covered = receipt.get('rolesCovered')
        require(isinstance(covered,list) and len(covered) == len(set(covered)) and set(roles) <= set(covered), 'approval lacks explicitly covered roles')
        require(receipt.get('exactRoleConfirmation') == f'Yes, I cover all {len(roles)} listed roles',
                'approval lacks explicit confirmation of the reviewed roles')
        reviewed = {key: value for key, value in receipt.items() if key not in keys}
        reviewed['decision'] = 'pending'
        require(receipt.get('reviewedReceiptSha256') == B.sha(B.serialized(reviewed)),
                'approval lacks the exact reviewed receipt digest')
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
                receipt_bytes = checked(root,authority['receipt'])
                require(B.git(root,'show',B.BASELINE+':'+expected_path) == receipt_bytes,
                        family+': historical approval receipt bytes changed: '+expected_path)
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
                    # The approved receipt binds the historical bytes. A new
                    # packet uses the status-neutral wording for the same rules.
                    historical = after != B.corrected_document(name,file['path'],before,labels['rows'])
                    require(not historical or after == B.corrected_document(name,file['path'],before,labels['rows'],historical=True),
                            name+': applied document differs from required corrections: '+file['path'])
                if file['path'] == 'README.md':
                    text = after.decode().replace('\r\n','\n')
                    require(B.setup(name,historical=historical) in text,name+': setup/refusal/discovery or retained-gate guidance lost')
                    for row in labels['rows']:
                        if row['repository'] == name: require(text.count(row['label']['text']) == 1,row['id']+': label missing or duplicated in patch')
                if 'candidate' in file: require(checked(root,file['candidate']) == after,name+': candidate and applied bytes differ')


def historical_deferrals(root):
    # The approved audit used this redaction policy. Later policy and ledger
    # changes must not replace the inputs to an already approved audit.
    source = B.git(root,'show',INVENTORY_PUBLICATION+':scripts/evidence_redaction.py')
    historical = {}
    exec(compile(source,'historical evidence_redaction.py','exec'),historical)
    ledger = B.git(root,'show',INVENTORY_PUBLICATION+':'+str(LEDGER)).decode()
    return B.scoped_deferrals(ledger, lambda text: historical['sanitized_xml'](text,environment={}))


def check_deferrals(root, audit):
    expected = historical_deferrals(root)
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
              '`inventory_revision` whenever an indexed inventory is added or re-pinned',
              'All PS01–PS14 remain present; no evidenced retirement is claimed.',
              'Unsupported transports\nfail safely; confidential human actions hand off to their owning UI.',
              'Admin A1–A4 and module K12 confidential-UI-only',
              'A5–A8 plus K07 documentation and K08 synthetic lifecycle withdrawn, K09\nstream/file and K10 per-user HTTP deferred.',
              'Eligible K01–K06 need exact decorated\nContracts, handlers, admission and independent semantic proof.']
    for token in tokens:
        require(token in plan,phase+' plan lost independent gate/exemption: '+token)


def prior_verifier(root):
    module_spec = importlib.util.spec_from_file_location('prior510reconciliation',root/E.parent/'story-5-10/verify_labels.py')
    prior = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(prior)
    return prior


def check_origin(repo, expected, normalize, owner):
    actual = B.git(repo,'remote','get-url','origin').decode().strip()
    require(normalize(actual) == normalize(expected),owner+': owner repository mismatch')


def check_prior_delivery(root,prior_module=None,register=None):
    # Replay the frozen packet at its recorded revisions. Current supersession
    # is checked against the separate Story 5.11 integrations.
    prior = prior_module or prior_verifier(root)
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
                check_origin(local_repo, repository['repository'], prior.L57.github_repository,
                             repository['name']+': historical')
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


def commit_date(repo, revision):
    timestamp = B.git(repo,'show','-s','--format=%cI',revision).decode().strip()
    try:
        committed = datetime.fromisoformat(timestamp)
        require(committed.tzinfo is not None,'commit date missing: '+revision)
        return committed.astimezone(timezone.utc).date()
    except ValueError as error:
        raise ValueError('commit date missing: '+revision) from error


def check_release_publication(root, resolution, released, generated, decided):
    tag,run_id,revision = (resolution.get(key) for key in ('releaseTag','releaseRunId','evidenceRevision'))
    require(isinstance(tag,str) and re.fullmatch(r'v[0-9]+\.[0-9]+\.[0-9]+',tag) is not None and
            type(run_id) is int and run_id > 0 and isinstance(revision,str) and
            re.fullmatch('[0-9a-f]{40}',revision) is not None and revision != released,
            'AC3 requires committed release and generation-run evidence for the tag')
    B.git(root,'merge-base','--is-ancestor',released,revision)
    B.git(root,'merge-base','--is-ancestor',revision,'origin/main')

    def committed(field):
        ref = resolution.get(field)
        raw = checked(root,ref)
        require(B.git(root,'show',revision+':'+ref['path']) == raw,
                'AC3 release evidence differs from the committed record: '+field)
        return raw

    release = json.loads(committed('publishedRelease'))
    require(release.get('html_url') == ROOT_REPOSITORY+'/releases/tag/'+tag and
            release.get('draft') is False and release.get('tag_name') == tag and type(release.get('id')) is int,
            'AC3 requires a published McpCli release record for the tag')
    published = release.get('published_at') or ''
    require(commit_date(root,released) <= recorded_date(published[:10],'AC3 release publication date missing') <=
            commit_date(root,revision) <= decided,'AC3 owner approval predates the committed release evidence')
    ref = 'refs/tags/'+tag
    require(B.git(root,'rev-parse',ref+'^{commit}').decode().strip() == released,
            'AC3 release tag does not identify the approved source revision')
    run = json.loads(committed('releaseRun'))
    require(run.get('id') == run_id and run.get('conclusion') == 'success' and run.get('head_sha') == released and
            run.get('path','').split('@',1)[0] == '.github/workflows/release.yml' and
            run.get('html_url') == ROOT_REPOSITORY+'/actions/runs/'+str(run_id),
            'AC3 release generation run does not bind the tagged source')
    body = release.get('body')
    require(committed('generatedNotes') == generated and isinstance(body,str) and body.encode().rstrip() == generated.rstrip(),
            'AC3 approved generated notes do not match the published release body')


def check_release_notes(root, integration, note, completed):
    binding = integration.get('releaseNotesResolution')
    require(binding is not None,'AC3 generated release notes remain deferred by the owner')
    resolution = json.loads(checked(root,binding))
    require(resolution.get('decision') == 'resolved' and resolution.get('entryId') == note['id'] and
            resolution.get('auditedEntrySha256') == note['entrySha256'] and
            resolution.get('owner') in {'Hexalith.CiCd','Hexalith.Builds','Hexalith.CiCd / Hexalith.Builds'} and
            resolution.get('exactWords','').strip().casefold() == 'approve' and nonblank(resolution.get('source')),
            'AC3 resolution lacks an explicit owner decision bound to the approved entry')
    current = [entry for entry in B.scoped_deferrals((root/LEDGER).read_text()) if entry['id'] == note['id']]
    require(len(current) == 1 and current[0]['sourceSpec'] == note['sourceSpec'] and
            current[0]['owner'] == note['owner'] and current[0]['sourceStatus'].startswith('resolved') and
            current[0]['entrySha256'] == resolution.get('resolvedEntrySha256') and
            nonblank(current[0].get('resolution')), 'AC3 resolution must bind the resolved release ledger entry')
    released = resolution.get('releaseRevision','')
    require(re.fullmatch('[0-9a-f]{40}',released) is not None,
            'AC3 resolution requires the full release source revision')
    B.git(root,'merge-base','--is-ancestor',integration['inventoryRevision'],released)
    B.git(root,'merge-base','--is-ancestor',released,'origin/main')
    decided = recorded_date(resolution.get('decidedOn'),'AC3 owner decision date missing')
    require(commit_date(root,released) <= decided <= completed,'AC3 resolution date does not follow release or exceeds completion')
    generated = checked(root,resolution.get('generatedNotes'))
    migration_status = B.git(root,'show',released+':docs/release/migration-status.md').strip()
    require(bool(migration_status) and generated.rstrip().endswith(b'\n\n'+migration_status),
            'AC3 generated notes omit the committed migration status')
    check_release_publication(root,resolution,released,generated,decided)


def check_retained_deferrals(root, integration, audit):
    current = {}
    for entry in B.scoped_deferrals((root/LEDGER).read_text()):
        current.setdefault(entry['id'],[]).append(entry)
    separate = integration.get('deferralResolutions',{})
    for approved in audit:
        entry_id = approved['id']
        if entry_id == RELEASE_NOTES_ENTRY or approved['disposition'].startswith('existing resolution'):
            continue
        matches = current.get(entry_id,[])
        require(len(matches) == 1 and matches[0]['sourceSpec'] == approved['sourceSpec'],
                'audited deferral missing or duplicated: '+entry_id)
        entry = matches[0]
        if all(entry[field] == approved[field] for field in ('summary','owner','sourceStatus')):
            continue
        require(entry_id in separate,'audited deferral changed without a separate resolution: '+entry_id)
        resolution = json.loads(checked(root,separate[entry_id]))
        require(resolution.get('entryId') == entry_id and resolution.get('auditedEntrySha256') == approved['entrySha256'] and
                resolution.get('resolvedEntrySha256') == entry['entrySha256'] and
                resolution.get('owner') == approved['owner'] and resolution.get('exactWords','').strip().casefold() == 'approve' and
                nonblank(resolution.get('source')) and resolution.get('decision') == 'resolved' and
                entry['sourceStatus'].startswith(('resolved','done','obsolete','superseded')),
                'separate resolution does not close the audited owner gate: '+entry_id)
        revision = resolution.get('revision','')
        require(re.fullmatch('[0-9a-f]{40}',revision) is not None,'audited deferral resolution lacks a committed revision: '+entry_id)
        B.git(root,'merge-base','--is-ancestor',revision,'origin/main')
        committed = B.scoped_deferrals(B.git(root,'show',revision+':'+str(LEDGER)).decode())
        require(any(candidate['entrySha256'] == entry['entrySha256'] for candidate in committed),
                'audited deferral resolution differs from the recorded ledger revision: '+entry_id)


def check_owner_conflicts(root):
    projects = '_bmad-output/planning-artifacts/'
    checks = {
        'chatbot': [
            (projects+'prds/prd-Hexalith.ChatBot-2026-05-28/prd.md',
             'approved execution and confirmation-required behavior route to the confidential ChatBot UI.',
             ('Inspect, associate, reject, defer, retry, approve, execute',
              'human-decision mutations require current presence at submission',
              'user-delegated via OAuth device flow',
              'UI/API, CLI, and MCP association/status/audit parity',
              'CLI and MCP integration must expose the same governed operations as the UI')),
            (projects+'ux-designs/ux-Hexalith.ChatBot-2026-05-28/EXPERIENCE.md',
             'Both McpCli heads refuse those operations.',
             ('Human-delegated MCP approval is candidate M1 behavior',
              'candidate human-delegated MCP approval remains unavailable',
              'explicitly exposed on UI, CLI, and/or MCP',
              'He confirms an association through an exposed surface')),
        ],
        'works': [
            (projects+'ux-designs/ux-works-2026-06-14/EXPERIENCE.md',
             'Discover enrolled Works Commands and Queries through the generic McpCli heads.',
             ('Exact MCP tools/resources and CLI commands over the kernel',
              'exact tool/resource names and syntax remain source-open')),
            (projects+'ux-designs/ux-works-2026-06-14/DESIGN.md',
             'after Works Contracts enrollment and authorization.',
             ('exact tools, resources, syntax, and protocol remain source-open',)),
            (projects+'ux-designs/ux-works-2026-06-14/mockups/key-mcp-cli.html',
             'The shared McpCli CLI and stdio MCP heads expose eligible Works operations',
             ('Both adapters expose registered domain commands and resources',)),
        ],
    }
    normalize = prior_verifier(root).L57.github_repository
    for owner,files in checks.items():
        repo = root.parent/owner
        if owner == 'works' and not (repo/'.git').exists():
            repo = root/'references/Hexalith.Works'
        check_origin(repo,'https://github.com/Hexalith/Hexalith.'+owner,normalize,owner)
        for path,required,obsolete in files:
            current = visible_markdown(B.git(repo,'show','origin/main:'+path))
            require(required in current and all(claim not in current for claim in obsolete),
                    'completion requires published '+owner+' migration guidance: '+path)


def check_parties_verdict(root, binding, retired):
    require(binding is not None,'SM-3 Parties retirement lacks the successor Story 5.4 owner verdict')
    verdict = json.loads(checked(root,binding))
    authority,decision = verdict.get('authority',{}),verdict.get('decision',{})
    require(verdict.get('schema') == 'mcpcli-story-5-4-owner-approval/v1' and
            authority.get('role') == 'Parties owner' and nonblank(authority.get('source')) and
            authority.get('responseVerbatim','').strip().casefold() == 'approve' and
            decision.get('approval') == 'approved' and decision.get('verdict') == 'retirement-ready' and
            decision.get('retainedBlockingGapIds') == [],
            'SM-3 Parties retirement requires the successor retirement-ready owner verdict')
    recorded = recorded_date(verdict.get('recordedAtUtc','')[:10],'SM-3 Parties verdict date missing')
    require(recorded <= retired,
            'SM-3 Parties verdict postdates retirement')
    prior_path = E.parent/'story-5-4-owner-approval/owner-approval.json'
    prior = json.loads(B.git(root,'show',B.BASELINE+':'+str(prior_path)))
    expected = {item['id']:item['owner'] for item in prior['gapDispositions']}
    resolutions = verdict.get('gapDispositions',[])
    require(len(resolutions) == len(expected) and {item['id']:item['owner'] for item in resolutions} == expected and
            all(item.get('workStatus','').startswith('resolved') for item in resolutions),
            'SM-3 Parties verdict lacks resolved G01–G06 with their recorded owners')
    snapshot = verdict.get('approvedSnapshot',{})
    revision = snapshot.get('commit','')
    previous = prior['approvedSnapshot']
    candidate = snapshot.get('candidateHeadCommit','')
    require(re.fullmatch('[0-9a-f]{40}',revision) is not None and revision != previous['commit'] and
            re.fullmatch('[0-9a-f]{40}',candidate) is not None and candidate != previous['candidateHeadCommit'],
            'SM-3 Parties verdict must approve a new evidence snapshot')
    B.git(root,'merge-base','--is-ancestor',previous['commit'],revision)
    B.git(root,'merge-base','--is-ancestor',revision,'origin/main')
    require(commit_date(root,revision) <= recorded and recorded_date(prior['recordedAtUtc'][:10],
            'historical Parties approval date missing') < recorded and
            verdict.get('approvalScope','').startswith('Approve') and 'retirement-ready' in verdict['approvalScope'] and
            'retirement-blocked' not in verdict['approvalScope'],
            'SM-3 Parties owner did not expressly approve the committed successor as retirement-ready')
    manifest,scan = (json.loads(checked(root,snapshot.get(field))) for field in ('manifest','scanReceipt'))
    acceptance = manifest.get('acceptanceEvidence',{})
    require(manifest.get('schema') == 'mcpcli-story-5-4-evidence/v1' and
            manifest.get('ownerCheckpoint',{}).get('proposal') == 'retirement-ready' and
            manifest.get('candidate',{}).get('headCommit') == candidate and
            acceptance.get('fullLiveAccepted') is True and acceptance.get('fullV1Accepted') is True and
            scan.get('schema') == 'mcpcli-evidence-secret-scan/v1' and
            scan.get('result') == 'clean' and scan.get('exitCode') == 0 and not scan.get('findings') and not scan.get('errors'),
            'SM-3 Parties successor manifest or clean scan is missing')
    files = scan.get('files',[])
    scan_ref,manifest_ref = snapshot['scanReceipt'],snapshot['manifest']
    index_digest = B.sha(json.dumps(files,sort_keys=True,ensure_ascii=True,separators=(',',':')).encode())
    require(len(files) == scan.get('fileCount') == scan_ref.get('inputFileCount') and
            scan.get('manifestSha256') == scan_ref.get('manifestSha256') == index_digest and
            any(row.get('path') == Path(manifest_ref['path']).name and row.get('sha256') == manifest_ref['sha256']
                for row in files),
            'SM-3 Parties clean scan does not bind the approved successor manifest')
    for ref in (manifest_ref,scan_ref):
        require(B.sha(B.git(root,'show',revision+':'+ref['path'])) == ref['sha256'],
                'SM-3 Parties snapshot bytes differ from the committed evidence: '+ref['path'])


def check_retirements(root, completed, retirements):
    census = B.rows((root/B.A/'technical-tools-migration-inventory-v1.0.4.md').read_text())
    servers = {row['surface']: row for row in read(root,E/'labels.json')['rows']
               if 'MCP' in census[row['id']]['Kind and transport'].split()}
    owners = {owner['name']: owner for owner in read(root,E/'upstream/manifest.json')['owners']}
    normalize = prior_verifier(root).L57.github_repository
    receipts = [json.loads(checked(root,binding)) for binding in retirements]
    by_surface = {receipt.get('surface'): receipt for receipt in receipts}
    require(len(by_surface) == len(receipts),'SM-3 duplicate retirement receipts')
    for surface, retirement in by_surface.items():
        require(retirement.get('state') == 'retired' and all(nonblank(retirement.get(k)) for k in ['surface','owner','source']),
                'SM-3 retirement receipt lacks retired state or authority')
        require(surface in servers,'SM-3 requires an inventoried Legacy Server')
        label = servers[surface]
        key = label['id']
        row = census[key]
        gates = {label['gate']}
        if key == 'PS02':
            gates.update(f'G{number}' for number in range(1,7))
        if key == 'PS05':
            gates.update(f'G{number:02}' for number in range(1,7))
            gates.add('restricted/destructive exposure conflict')
        if key in {'PS04','PS09'}:
            gates.update(f'FK{number:02}' for number in range(1,5))
            partner = 'PS09' if key == 'PS04' else 'PS04'
            require(any(candidate in by_surface for candidate, binding in servers.items() if binding['id'] == partner),
                    'SM-3 FrontComposer and Projects must retire together')
        evidence = retirement.get('gateEvidence')
        require(isinstance(evidence,dict) and set(evidence) == gates,
                'SM-3 retirement does not bind every independent removal gate for '+surface)
        require(retirement.get('ownerRole') == row['Owning maintainer role'] and
                retirement.get('exactApprovalInstruction','').strip().casefold() == 'approve',
                'SM-3 retirement lacks explicit owning-maintainer approval')
        retired = recorded_date(retirement.get('retiredOn'),'retirement date missing')
        require(retired <= min(completed,date(2027,2,5)),'SM-3 retirement must occur by its deadline and assessment')
        owner = owners[label['repository']]
        repo = (root/owner['ownerCheckout']).resolve()
        check_origin(repo,owner['repository'],normalize,label['repository'])
        revision = retirement.get('removalRevision','')
        require(re.fullmatch('[0-9a-f]{40}',revision) is not None, 'SM-3 retirement lacks owning repository removal revision')
        B.git(repo,'merge-base','--is-ancestor',revision,'origin/main')
        require(commit_date(repo,revision) <= retired,'SM-3 removal revision postdates the retirement')
        project = row['Project'].strip('`')
        require(B.git(repo,'ls-tree','--name-only',revision+'^','--',project).decode().strip() == project and
                all(not B.git(repo,'ls-tree','--name-only',rev,'--',project).strip() for rev in (revision,'origin/main')),
                'SM-3 retirement lacks owner removal of '+project)
        changes = B.git(repo,'diff','--name-status','--find-renames','-z',revision+'^',revision).split(b'\0')
        require(any(change == b'D' and target == project.encode() for change,target in zip(changes,changes[1:])) and
                not any(Path(path).name == Path(project).name for path in
                        B.git(repo,'ls-tree','-r','--name-only','origin/main').decode().splitlines()),
                'SM-3 owner revision renames or retains the retired project: '+project)
        if key == 'PS05':
            check_parties_verdict(root,retirement.get('story54Verdict'),retired)
        for gate, binding in evidence.items():
            proof = json.loads(checked(root,binding))
            require(proof.get('surface') == surface and proof.get('gate') == gate and proof.get('result') == 'passed' and
                    proof.get('removalRevision') == revision and
                    all(nonblank(proof.get(k)) for k in ('owner','source')) and
                    recorded_date(proof.get('verifiedOn'),'SM-3 gate date missing') <= retired,
                    'SM-3 removal evidence does not prove '+gate+' for '+surface)
            require(bool(checked(root,proof.get('resultEvidence'))),'SM-3 gate result evidence is empty: '+gate)


def check_assessments(root,integration):
    decision = integration.get('deferralOwnerDecision')
    require(isinstance(decision,dict) and decision.get('decision') == 'accept-audit-preserve-open-gates' and all(nonblank(decision.get(k)) for k in ['owner','source']),'completion requires explicit structured deferral owner decision')
    audit_data = (root/E/'deferral-dispositions.json').read_bytes()
    require(decision.get('auditSha256') == B.sha(audit_data) and decision.get('auditMarkdownSha256') == B.sha((root/E/'deferral-dispositions.md').read_bytes()),'deferral decision must bind exact audit bytes')
    approval = read(root,E/'approval.json')
    require(decision.get('exactWords') == approval['exactApprovalInstruction'] and
            decision.get('reviewedReceiptSha256') == approval['reviewedReceiptSha256'],
            'deferral decision must bind the reviewed packet and owner instruction')
    audit = json.loads(audit_data)
    unresolved = {entry['id'] for entry in audit['entries'] if not entry['disposition'].startswith('existing resolution')}
    retained = decision.get('retainedUnresolvedEntryIds')
    require(decision.get('preserveUnresolvedGates') is True and isinstance(retained,list) and len(retained)==len(unresolved) and set(retained)==unresolved,'deferral decision must preserve every unresolved owner/gate')

    notes = [entry for entry in audit['entries'] if entry['id']==RELEASE_NOTES_ENTRY]
    require(len(notes)==1,'AC3 release-note disposition missing')
    require(integration.get('releaseNotesResolution') is not None,'AC3 generated release notes remain deferred by the owner')

    completed = recorded_date(integration.get('completedOn'),'recorded completion date missing or invalid')
    require(completed <= date.today(),'recorded completion date is in the future')
    require(recorded_date(decision.get('decidedOn'),'deferral decision date missing') <= completed,'deferral decision occurs after completion')
    final = json.loads(checked(root,integration['finalPlanApproval']))
    events = [approval['approvedOn'], integration['deliveryAuthorization']['approvedOn'],
              integration['inventoryPublication']['verifiedOn'], final['approvedOn'], integration['integratedOn']]
    events += [item['verifiedOn'] for item in integration['ownerIntegrations']]
    delivered = [recorded_date(event,'delivery/approval date missing or invalid') for event in events]
    delivered += [commit_date(root,integration[key]) for key in ('inventoryRevision','rootIntegrationRevision')]
    require(max(delivered) <= completed,'completion predates approval or verified delivery')
    check_release_notes(root,integration,notes[0],completed)
    check_owner_conflicts(root)
    check_retained_deferrals(root,integration,audit['entries'])
    assessment = integration.get('sm3Assessment')
    require(isinstance(assessment,dict),'structured SM-3 assessment missing')
    require(recorded_date(assessment.get('assessedOn'),'SM-3 assessment date missing') == completed,'SM-3 assessment must bind recorded completion date')
    require(assessment.get('deadline') == '2027-02-05' and all(nonblank(assessment.get(k)) for k in ['owner','source']),'SM-3 deadline/owner/source missing')
    outcome,retirements = assessment.get('outcome'),assessment.get('retirements')
    require(outcome in {'met','pending-not-met','slip'} and isinstance(retirements,list),'SM-3 outcome/retirement accounting missing')
    if outcome == 'met':
        require(bool(retirements),'SM-3 met requires evidenced retirement')
        check_retirements(root,completed,retirements)
    else:
        require(not retirements,'SM-3 pending/slip must not claim retirement')
        if completed > date(2027,2,5):
            require(outcome == 'slip' and nonblank(assessment.get('ownerReason')),'overdue SM-3 requires explicit owner slip reason')
        else:
            require(outcome == 'pending-not-met','pre-deadline unmet SM-3 remains pending')


def check_published_index(root, plan, inputs, revision):
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
            require(len(entries)==1 and entries[0][3].strip()==f'`{digest}`' and entries[0][4].strip().startswith(status+':'),
                    family+' '+item['version']+': final inventory row authority/path/hash mismatch')
            for cell,target in [(entries[0][2],path),(entries[0][4],receipt_path)]:
                url = f'{ROOT_REPOSITORY}/blob/{revision}/{target}'
                require(re.findall(r'\]\(([^\s)]+)\)',cell) == [url],
                        f"{family} {item['version']}: final inventory row lacks immutable link: {target}")


def rebased_document_hash(repo, commit, owner, file, rebase, labels):
    path = file['path']
    parent = B.git(repo, 'rev-parse', commit+'^').decode().strip()
    require(rebase.get('base') == parent and nonblank(rebase.get('publicationInstruction')) and
            rebase.get('reviewedAfterSha256') == file['afterSha256'] and
            rebase.get('patchSha256') == file['patch']['sha256'], 'rebased document approval or patch binding differs: '+path)
    before = B.git(repo, 'show', parent+':'+path)
    require(B.sha(before) == rebase.get('beforeSha256'), 'rebased document base differs: '+path)
    # Replay the reviewed corrections on the actual parent so unrelated upstream edits survive.
    after = B.corrected_document(owner, path, before, labels['rows'], historical=True)
    require(B.sha(after) == rebase.get('afterSha256'), 'rebased document differs from reviewed corrections: '+path)
    return B.sha(after)


def check_footprint(repo, revision, paths, name):
    changed = B.git(repo,'diff','--name-only','--no-renames','-z',revision+'^',revision).decode().split('\0')
    require(set(changed) - {''} == set(paths),name+': delivery commit changes files outside its approved footprint')


def visible_markdown(raw):
    return re.sub(r'<!--.*?(?:-->|\Z)','',raw.decode('utf-8-sig'),flags=re.S)


def verify_current_migration_text(repo, commit, path, delivered, name):
    report = 'reported: '+name+': current main migration text drift: '+path
    try:
        current = B.git(repo,'show','origin/main:'+path)
    except ValueError:
        if B.git(repo,'ls-tree','--name-only','origin/main','--',path).strip():
            raise
        print(report,file=sys.stderr)
        return
    if current == delivered:
        return
    parent = B.git(repo,'show',commit+'^:'+path)
    def migration_lines(text):
        normalized = visible_markdown(text)
        normalized = re.sub(r'(?m)^(## Shared McpCli access) \(reconciliation candidate\)\r?$',r'\1',normalized)
        normalized = re.sub(r'(?m)^(> \*\*Current McpCli disposition) \(Story 5\.11 candidate\)(:\*\*)',r'\1\2',normalized)
        return normalized.splitlines()
    before, after, now = (migration_lines(text) for text in (parent,delivered,current))
    after_text, current_text = ('\n'+'\n'.join(lines)+'\n' for lines in (after,now))
    # Retain the passages the integration changed. The surrounding owner text
    # can change independently of this approved correction.
    for operation, i, j, first, last in SequenceMatcher(None,before,after,autojunk=False).get_opcodes():
        if operation == 'equal':
            continue
        added = '\n'+'\n'.join(after[first:last])+'\n'
        removed = '\n'+'\n'.join(before[i:j])+'\n'
        retained = added in current_text or not any(line.strip() for line in after[first:last])
        if not retained and name == 'projects' and path.endswith('/ARCHITECTURE-SPINE.md') and 'Current McpCli disposition' in added:
            # Projects moved this guidance into its adopted AD-29. Check the
            # replacement rule there, rather than accepting banner deletion.
            adopted = re.search(r'^### AD-29 — \[ADOPTED\][^\n]*\n(.*?)(?=^### |\Z)',current_text,re.M|re.S)
            statements = (
                '`projects.list`, `projects.describe`, `projects.trace-conversation` and `projects.trace-attachments`',
                'readiness, Setup, task-control, audit, export and write operations are outside it',
                'EventStore Gateway authorizes each invocation',
                'Both public heads refuse UI-only and confirmation-required actions',
                'resolution and proposal confirmation stay on the confidential Chatbot UI',
                '`Projects.Cli` and `Projects.Mcp` are frozen obsolete migration sources',
            )
            retained = bool(adopted and all(statement in adopted[1] for statement in statements))
        obsolete = any(line.strip() for line in before[i:j]) and removed not in after_text and removed in current_text
        if not retained or obsolete:
            print(report,file=sys.stderr)
            return


def check_inventory_publication(root, receipt, integration, receipt_digest):
    publication = integration.get('inventoryPublication')
    require(isinstance(publication,dict) and publication.get('approvedArtifactsVerified') == len(receipt['artifacts']) and
            publication.get('approvalSha256') == receipt_digest,
            'McpCli publication lacks approved artifact count or receipt digest')
    verified = recorded_date(publication.get('verifiedOn'),'McpCli publication verification date missing')
    checks = publication.get('checks',{})
    require(checks.get('commitlint') == 'passed' and type(checks.get('storyTestsPassed')) is int and
            checks['storyTestsPassed'] > 0,'McpCli publication lacks passing commitlint and story tests')
    historical = json.loads(B.git(root,'show',PUBLICATION_RECORD+':'+str(E/'integration.json')))['inventoryPublication']
    require(publication == historical,'McpCli publication checks or scoped Builds exception differ from recorded evidence')
    require(commit_date(root,integration['inventoryRevision']) <= verified,
            'McpCli publication verification predates the inventory revision')


def check_ai_review(repo, delivery, review, approval, files, inputs, historical):
    reviewed = approval.get('reviewCommit','')
    pull_request = approval.get('pullRequest','')
    require(re.fullmatch('[0-9a-f]{40}',reviewed) is not None and
            re.fullmatch(r'https://github\.com/Hexalith/Hexalith\.AI\.Tools/pull/[0-9]+',pull_request) is not None and
            review.get('state') == 'merged' and review.get('mergeCommit') == delivery['commit'] and
            review.get('reviewCommit') == reviewed and review.get('pullRequest') == pull_request,
            'AI.Tools final approval must bind the merged review and its exact head')
    checks = delivery['checks']
    run = checks.get('run','')
    require(checks.get('builds') == 'passed' and checks.get('testedHead') == reviewed and
            checks.get('buildsSource') == 'GitHub Actions PR build and tests' and
            re.fullmatch(r'https://github\.com/Hexalith/Hexalith\.AI\.Tools/actions/runs/[0-9]+',run) is not None,
            'AI.Tools hosted checks do not bind the approved review head')
    recorded_ai = next(owner for owner in historical['ownerIntegrations'] if owner['name'] == 'ai-tools')
    require(checks == recorded_ai['checks'] and review == historical['finalPlanReview'],
            'AI.Tools hosted checks differ from the immutable final integration record')
    # The reviewed head is not an ancestor of a squash merge. A standard main
    # checkout can replay the committed review record without the old PR ref.
    if B.git(repo,'rev-list','--no-walk','--ignore-missing',reviewed).strip():
        check_footprint(repo,reviewed,files,'AI.Tools reviewed head')
        for path in files:
            require(B.git(repo,'show',reviewed+':'+path) == B.git(repo,'show',delivery['commit']+':'+path),
                    'AI.Tools tested and merged documentation bytes differ: '+path)
    indexed = {path for chain in inputs['inventoryHistories'].values() for item in chain
               for path in (item['path'],item['approval']['receipt']['path'])}
    require(review.get('verifiedInventoryAndReceiptLinks') == len(indexed),
            'AI.Tools final review lacks complete immutable link verification')


def check_delivery(root, receipt, labels, manifest, integration):
    require(receipt.get('decision') == 'approved', 'completion requires fresh exact-byte successor approval')
    check_prior_delivery(root)
    require(integration.get('state') in {'delivered','integrated'},'completion requires integrated plan and all fourteen labels')
    authorization = integration.get('deliveryAuthorization')
    require(isinstance(authorization,dict) and all(nonblank(authorization.get(k)) for k in ['source','approvedOn','exactWords','footprint']),
            'completion requires separate explicit Git delivery authorization')
    words = authorization['exactWords'].strip().casefold().rstrip('.\\')
    push_requests = {'push all changes', 'push all changes of all repositories to main'}
    require(words == 'authorize' or words in push_requests,
            'completion requires separate explicit Git delivery authorization')
    receipt_bytes = (root/E/'approval.json').read_bytes()
    receipt_digest = B.sha(receipt_bytes)
    require(authorization.get('approvalSha256') == receipt_digest,
            'Git delivery authorization does not bind the approved packet receipt')
    published_record = json.loads(B.git(root,'show',INVENTORY_PUBLICATION+':'+str(E/'integration.json')))
    require(authorization == published_record['deliveryAuthorization'],
            'Git delivery authorization differs from the immutable publication record')
    require(recorded_date(authorization['approvedOn'],'Git delivery authorization date missing') >=
            recorded_date(receipt['approvedOn'],'packet approval date missing'),
            'Git delivery authorization predates exact-byte approval')
    inventory_revision = integration.get('inventoryRevision')
    require(inventory_revision == INVENTORY_PUBLICATION,'completion requires the frozen published inventory revision')
    normalize = prior_verifier(root).L57.github_repository
    check_origin(root,ROOT_REPOSITORY,normalize,'McpCli')
    B.git(root,'merge-base','--is-ancestor',inventory_revision,'origin/main')
    for path,digest in receipt['artifacts'].items():
        require(B.sha(B.git(root,'show',inventory_revision+':'+path)) == digest, 'published approved artifact bytes mismatch: '+path)
    require(B.git(root,'show',inventory_revision+':'+str(E/'approval.json')) == receipt_bytes, 'published receipt bytes mismatch')
    check_inventory_publication(root,receipt,integration,receipt_digest)
    deliveries = integration.get('ownerIntegrations',[])
    require(len(deliveries) == len(manifest['owners']) and {d.get('name') for d in deliveries} == {o['name'] for o in manifest['owners']}, 'completion requires every owner integration binding')
    for owner in manifest['owners']:
        delivered = next(d for d in deliveries if d['name'] == owner['name'])
        require(isinstance(delivered,dict) and isinstance(delivered.get('commit'),str) and re.fullmatch('[0-9a-f]{40}',delivered['commit']),owner['name']+': upstream integration missing')
        repo,commit = (root/owner['ownerCheckout']).resolve(),delivered['commit']
        check_origin(repo,owner['repository'],normalize,owner['name'])
        B.git(repo,'merge-base','--is-ancestor',commit,'origin/main')
        paths = {file['path'] for file in owner['files']}
        check_footprint(repo,commit,paths,owner['name'])
        require(delivered.get('verifiedFileCount') == len(paths),owner['name']+': verified owner file count mismatch')
        rebase_items = delivered.get('rebasedFiles',[])
        rebases = {rebase['path']:rebase for rebase in rebase_items}
        require(len(rebases) == len(rebase_items) and rebases.keys() <= paths and
                (owner['name'] != 'ai-tools' or not rebases),owner['name']+': invalid owner rebase footprint')
        for file in owner['files']:
            path = file['path']
            target_hash = integration.get('planSha256') if path == PLAN_PATH else file['afterSha256']
            if path in rebases:
                target_hash = rebased_document_hash(repo,commit,owner['name'],file,rebases[path],labels)
            documented = B.git(repo,'show',commit+':'+path)
            require(B.sha(documented) == target_hash,owner['name']+': integrated documentation bytes mismatch')
            verify_current_migration_text(repo,commit,path,documented,owner['name'])
            if path == 'README.md':
                current = visible_markdown(B.git(repo,'show','origin/main:'+path)).splitlines()
                for row in labels['rows']:
                    if row['repository'] == owner['name']:
                        require(current.count(row['label']['text']) == 1,row['id']+': current main label is missing or duplicated')
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
    check_footprint(root,containing,{AI_TOOLS_GITLINK},'McpCli AI.Tools pin')
    tree = B.git(root,'ls-tree',containing,AI_TOOLS_GITLINK).decode().split()
    require(len(tree)==4 and tree[:2]==['160000','commit'] and tree[3]==AI_TOOLS_GITLINK and re.fullmatch('[0-9a-f]{40}',tree[2]),'committed AI.Tools gitlink missing')
    gitlink = tree[2]
    require(gitlink == integration.get('aiToolsGitlink'), 'containing AI.Tools gitlink missing')
    B.git(root.parent/'aitools','merge-base','--is-ancestor',ai,gitlink)
    plan = B.git(root.parent/'aitools','show',ai+':'+PLAN_PATH)
    ai_files = [PLAN_PATH,'hexalith-llm-instructions.md']
    for file in ai_files:
        merged = plan if file == PLAN_PATH else B.git(root.parent/'aitools','show',ai+':'+file)
        require(B.git(root.parent/'aitools','show',gitlink+':'+file)==merged,'committed AI.Tools gitlink differs: '+file)
    frontmatter = plan.decode().split('---',2)
    require(len(frontmatter)==3 and not frontmatter[0] and B.sha(plan)==integration.get('planSha256'),
            'exact plan bytes/publication binding missing')
    metadata = frontmatter[1].splitlines()
    require([line for line in metadata if line.startswith('inventory_revision:')] == [f"inventory_revision: '{inventory_revision}'"],
            'exact plan bytes/publication binding missing')
    require([line for line in metadata if line.startswith('status:')] == ['status: approved'] and
            [line for line in metadata if line.startswith('inventory_repository:')] == [f"inventory_repository: '{ROOT_REPOSITORY}'"],
            'final plan lacks approved authority for the canonical inventory repository')
    wording = ' '.join(plan.decode().lower().split())
    candidate_markers = ['candidate-not-publishable','1.3.0 candidate','inventory_revision: null','never publish this candidate',
                         'not the authoritative plan until','before approval of final plan bytes','missing publication binding',
                         'bind final plan bytes','/blob/<sha>/']
    require([line for line in metadata if line.startswith('plan_version:')] == ["plan_version: '1.3.0'"] and
            not any(marker in wording for marker in candidate_markers),'completion requires final plan 1.3.0 bytes')
    check_plan_semantics(plan.decode(),'final approved')
    final_approval = json.loads(checked(root,integration.get('finalPlanApproval')))
    require(final_approval.get('decision') == 'approved' and final_approval.get('planVersion') == integration.get('planVersion') == '1.3.0' and final_approval.get('planSha256') == B.sha(plan) and final_approval.get('inventoryRevision') == inventory_revision, 'final plan exact-byte approval/hash/revision binding missing')
    require(all(nonblank(final_approval.get(k)) for k in ['approver','exactApprovalInstruction','approvalSource','approvedOn']) and final_approval['exactApprovalInstruction'].strip().casefold() == 'approve', 'final plan approval lacks explicit owner instruction')
    require(set(receipt['requiredApprovalRoles']) <= set(final_approval.get('rolesCovered',[])), 'final plan approval lacks covered roles')
    inputs = read(root,E/'inputs.json')
    historical = json.loads(B.git(root,'show',FINAL_INTEGRATION_RECORD+':'+str(E/'integration.json')))
    check_ai_review(root.parent/'aitools',ai_delivery,integration.get('finalPlanReview') or {},
                    final_approval,ai_files,inputs,historical)
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
