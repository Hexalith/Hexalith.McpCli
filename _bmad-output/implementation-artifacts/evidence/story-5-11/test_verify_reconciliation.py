"""Policy-boundary tests, including exact command streams and removed-guard controls."""
import ast
import contextlib
import copy
import difflib
from functools import cache
import tempfile
import importlib.util
import io
import json
from pathlib import Path
import re
import sys
import unittest
from unittest import mock

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
module_spec = importlib.util.spec_from_file_location('reconciliation511tests',HERE/'verify_reconciliation.py')
V = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(V)
B,ROOT,E = V.B,V.ROOT,V.E
recorded_git = cache(B.git)
PASS = 'PASS: eight inventory histories; preserved AD-23/predecessors; fourteen labels; nine owner patch sets; scoped deferral accounting\n'
VERIFIED = PASS+'PASS: decision: approved; approved integration verified\n'


def data(name):
    return json.loads((ROOT/E/name).read_text())


def pending():
    receipt = data('approval.json')
    receipt['decision'] = 'pending'
    for key in ['approver','exactApprovalInstruction','approvalSource','approvedOn','rolesCovered',
                'exactRoleConfirmation','reviewedReceiptSha256']:
        receipt.pop(key, None)
    return receipt


def approved():
    return data('approval.json')


def streams(action):
    stdout,stderr = io.StringIO(),io.StringIO()
    with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
        code = action()
    return code,stdout.getvalue(),stderr.getvalue()


def replay_follow_up():
    folder = HERE/'owner-doc-follow-up'
    index = (folder/'README.md').read_text()
    rows = re.findall(r'^\| \[[^\]]+\]\(([^)]+)\.patch\) \| `([a-f0-9]{40})` \| (\d+) \| `([a-f0-9]{64})` \|$',index,re.M)
    expected_patches = {patch.stem for patch in folder.glob('*.patch')}
    if len(rows) != len(expected_patches) or {row[0] for row in rows} != expected_patches:
        raise AssertionError('Follow-up patch index does not match the patch files')
    results = {}
    for owner,revision,count,digest in rows:
        patch = folder/f'{owner}.patch'
        raw = patch.read_bytes()
        paths = re.findall(rb'^--- a/([^\r\n]+)',raw,re.M)
        if B.sha(raw) != digest or len(paths) != int(count) or len(set(paths)) != len(paths):
            raise AssertionError(f'{owner}: follow-up patch hash or footprint differs')
        repo = ROOT.parent/owner
        if owner == 'works' and not (repo/'.git').exists():
            repo = ROOT/'references/Hexalith.Works'
        B.git(repo,'merge-base','--is-ancestor',revision,'origin/main')
        with tempfile.TemporaryDirectory() as directory:
            scratch = Path(directory)
            B.git(scratch,'init','--quiet')
            for name in paths:
                path = name.decode()
                dest = scratch/path
                dest.parent.mkdir(parents=True,exist_ok=True)
                dest.write_bytes(B.git(repo,'show',revision+':'+path))
            B.git(scratch,'-c','core.whitespace=cr-at-eol','apply','--whitespace=error',str(patch))
            for name in paths:
                path = name.decode()
                results[owner,path] = (scratch/path).read_bytes()
    return results


def without_guard(token):
    tree = ast.parse((HERE/'verify_reconciliation.py').read_text())
    removed = []
    class Remove(ast.NodeTransformer):
        def visit_Expr(self,node):
            if isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id == 'require' and token in ast.unparse(node.value):
                removed.append(node)
                return ast.copy_location(ast.Pass(),node)
            return self.generic_visit(node)
    tree = Remove().visit(tree)
    if len(removed) != 1: raise AssertionError((token,len(removed)))
    namespace = {'__file__':str(HERE/'verify_reconciliation.py'),'__name__':'guard_removal_fixture'}
    exec(compile(ast.fix_missing_locations(tree),'<removed-reconciliation-guard>','exec'),namespace)
    return namespace


class ReconciliationTests(unittest.TestCase):
    def main(self,overrides=None,completion=False):
        candidate = dict(data('integration.json'), state='blocked')
        overrides = {str(E/'integration.json'):candidate, **(overrides or {})}
        original = V.read
        def read(root,path):
            return copy.deepcopy((overrides or {}).get(str(path),original(root,path)))
        with mock.patch.object(V,'read',side_effect=read):
            return streams(lambda:V.main(['--approved-completion'] if completion else []))

    def refusal(self,overrides,message,completion=False):
        self.assertEqual(self.main(overrides,completion),(1,'','FAIL: '+message+'\n'))

    def test_pending_candidate_exact_streams_and_completion_refusal(self):
        overrides = {str(E/'approval.json'):pending()}
        self.assertEqual(self.main(overrides),(0,PASS+'PASS: decision: pending; candidate only; approval, publication and upstream integration remain gates\n',''))
        self.refusal(overrides,'completion requires fresh exact-byte successor approval',True)

    def test_approved_inventory_is_distinct_from_incomplete_delivery(self):
        self.assertEqual(self.main({str(E/'approval.json'):approved()}),
                         (0,PASS+'PASS: decision: approved; packet approved; publication and upstream integration pending\n',''))
        self.refusal({str(E/'approval.json'):approved()},'completion requires integrated plan and all fourteen labels',True)
        with mock.patch.object(V,'check_prior_delivery',side_effect=ValueError('historical delivery missing')):
            self.refusal({str(E/'approval.json'):approved()},'historical delivery missing',True)

    def test_history_missing_duplicate_version_and_hash(self):
        for mutate,message in [
            (lambda x:x['inventoryHistories'].pop('folders'),'eight-family history accounting mismatch'),
            (lambda x:x['inventoryHistories']['folders'].pop(),'folders: missing/duplicate historical version'),
            (lambda x:x['inventoryHistories']['folders'][0].update(version='9.0.0'),'folders: version/path history mismatch'),
            (lambda x:x['inventoryHistories']['folders'][0].update(sha256='0'*64),'artifact hash mismatch: '+str(B.A/'folders-migration-inventory-v1.md')),
            (lambda x:x['inventoryHistories']['folders'][0].update(sourceRevision=None),'folders: full source revision binding missing or mismatched'),
            (lambda x:x['inventoryHistories']['folders'][0]['approval'].update(authority='owning-maintainer-receipt'),'folders: earlier/fresh authority conflated'),
        ]:
            with self.subTest(message=message):
                value = data('inputs.json');mutate(value)
                self.refusal({str(E/'inputs.json'):value},message)

    def test_prior_authority_and_own_receipt_are_required(self):
        value=data('inputs.json');value['authorities'].pop()
        self.refusal({str(E/'inputs.json'):value},'adopted authority binding incomplete')
        value=data('inputs.json');value['priorApprovals'].pop()
        self.refusal({str(E/'inputs.json'):value},'prior approval binding incomplete')
        value=data('inputs.json');value['inventoryHistories']['technical-tools'][-1]['approval']['receipt']={'path':'unrelated.json'}
        self.refusal({str(E/'inputs.json'):value},'technical-tools: own effective-status receipt missing')

    def test_fresh_approval_needs_hashes_roles_words_and_no_pending_claim(self):
        receipt=data('approval.json');receipt['artifacts'].pop(next(iter(receipt['artifacts'])))
        self.refusal({str(E/'approval.json'):receipt},'approval artifact accounting/hash mismatch')
        for role in approved()['requiredApprovalRoles']:
            with self.subTest(role=role):
                receipt=approved();receipt['rolesCovered']=[r for r in receipt['rolesCovered'] if r!=role]
                self.refusal({str(E/'approval.json'):receipt},'approval lacks explicitly covered roles')
        receipt=approved();receipt['exactApprovalInstruction']='approve and continue'
        self.refusal({str(E/'approval.json'):receipt},'approval requires explicit exact-byte approve instruction')
        receipt=approved();receipt.pop('exactRoleConfirmation')
        self.refusal({str(E/'approval.json'):receipt},'approval lacks explicit confirmation of the reviewed roles')
        receipt=approved();receipt.pop('reviewedReceiptSha256')
        self.refusal({str(E/'approval.json'):receipt},'approval lacks the exact reviewed receipt digest')
        receipt=pending();receipt['approver']='Invented approval'
        self.refusal({str(E/'approval.json'):receipt},'pending receipt must not claim fresh approval')
        receipt=data('approval.json');receipt['amendments'][0]['rows'].pop()
        self.refusal({str(E/'approval.json'):receipt},'amendment predecessor/row/approval bindings mismatch')

    def test_historical_receipt_cannot_be_replaced_with_a_matching_new_digest(self):
        inputs = data('inputs.json')
        early = inputs['inventoryHistories']['eventstore-admin'][0]['approval']['receipt']
        path = ROOT/early['path']
        original = path.read_bytes()
        tampered = B.serialized(dict(json.loads(original),approver='Different fixture approver'))
        early['sha256'] = B.sha(tampered)
        read = Path.read_bytes
        with mock.patch.object(Path,'read_bytes',lambda p: tampered if p == path else read(p)):
            self.refusal({str(E/'inputs.json'):inputs},
                         'eventstore-admin: historical approval receipt bytes changed: '+early['path'])

    def test_every_label_and_gate_is_required(self):
        for row in data('labels.json')['rows']:
            with self.subTest(surface=row['id']):
                labels=data('labels.json');labels['rows']=[r for r in labels['rows'] if r['id']!=row['id']]
                self.refusal({str(E/'labels.json'):labels},'fourteen-label accounting/duplicate mismatch')
        labels=data('labels.json');labels['rows'][0]['gate']='Waived'
        self.refusal({str(E/'labels.json'):labels},'PS01: owner/surface/removal gate changed')
        labels=data('labels.json');labels['predecessors'].pop()
        self.refusal({str(E/'labels.json'):labels},'label predecessor chain incomplete')
        labels=data('labels.json');labels['inventoryRevision']='a'*40
        self.refusal({str(E/'labels.json'):labels},'candidate must not claim delivered publication or labels')

    def test_compiler_and_vector_exemptions_remain_retained_never_retired(self):
        for surface,token in [('PS03','never counted as retired'),('PS14','Never counted as retired')]:
            with self.subTest(surface=surface):
                labels=data('labels.json');row=next(r for r in labels['rows'] if r['id']==surface)
                row['label']['text']=row['label']['text'].replace(token,'Retired')
                row['label']['sha256']=B.sha(row['label']['text'].encode())
                self.refusal({str(E/'labels.json'):labels},surface+': retained gate/exemption lost: '+token)

    def test_every_active_file_and_no_change_owner_is_accounted(self):
        manifest=data('upstream/manifest.json');manifest['owners'].pop()
        self.refusal({str(E/'upstream/manifest.json'):manifest},'active owner patch accounting mismatch')
        manifest=data('upstream/manifest.json');manifest['noChange'].pop()
        self.refusal({str(E/'upstream/manifest.json'):manifest},'inspected no-change owner accounting mismatch')
        manifest=data('upstream/manifest.json');manifest['owners'][0]['files'].pop()
        self.refusal({str(E/'upstream/manifest.json'):manifest},'eventstore: active-topic file accounting mismatch')

    def test_admin_labels_bind_exact_successor_link_and_hash(self):
        labels = data('labels.json')
        admin = str(B.A/'eventstore-admin-migration-inventory-v1.0.3.md')
        for old in ('Admin inventory 1.0.3',admin,labels['inventoryArtifacts'][admin]):
            with self.subTest(old=old):
                changed = copy.deepcopy(labels)
                row = next(r for r in changed['rows'] if r['id']=='PS02')
                row['label']['text'] = row['label']['text'].replace(old,'stale')
                row['label']['sha256'] = B.sha(row['label']['text'].encode())
                self.refusal({str(E/'labels.json'):changed},'PS02: Admin 1.0.3 label citation/hash missing')

    def test_nested_tempdir_applies_patches_locally(self):
        with tempfile.TemporaryDirectory() as parent:
            B.git(parent,'init','--quiet')
            with mock.patch.object(tempfile,'tempdir',parent):
                V.check_patches(ROOT,data('upstream/manifest.json'),data('labels.json'))
            self.assertEqual(B.git(parent,'status','--porcelain'),b'')

    def test_notice_with_missing_in_place_edit_refuses_even_when_rehashed(self):
        manifest,labels = data('upstream/manifest.json'),data('labels.json')
        owner = manifest['owners'][0]
        file = next(f for f in owner['files'] if f['path'].endswith('/prd.md'))
        before = V.prepared_before(ROOT,owner,file)
        with mock.patch.object(B,'correct',side_effect=lambda name,text,**kwargs:text):
            incomplete = B.corrected_document(owner['name'],file['path'],before,labels['rows'],historical=True)
        target=file['path']
        patch = ''.join(difflib.unified_diff(before.decode().splitlines(True),incomplete.decode().splitlines(True),
                                             fromfile='a/'+target,tofile='b/'+target)).encode()
        file.update(afterSha256=B.sha(incomplete))
        file['patch']['sha256'] = B.sha(patch)
        check = V.checked
        with mock.patch.object(V,'checked',side_effect=lambda root,item: patch if item==file['patch'] else check(root,item)):
            self.refusal({str(E/'upstream/manifest.json'):manifest},owner['name']+': applied document differs from required corrections: '+target)

    def test_fresh_packet_can_replay_status_neutral_setup_with_original_install_example(self):
        manifest,labels = data('upstream/manifest.json'),data('labels.json')
        owner = next(item for item in manifest['owners'] if item['name']=='projects')
        file = next(item for item in owner['files'] if item['path']=='README.md')
        before = V.prepared_before(ROOT,owner,file)
        after = B.corrected_document('projects','README.md',before,labels['rows'])
        self.assertIn(b'## Shared McpCli access\n',after)
        self.assertIn(b'dotnet tool install --global Hexalith.McpCli --version 2.0.1',after)
        self.assertIn(b'An installed tool discovers them only from a published McpCli release that enrolls Projects.Contracts 2.0.0.',after)
        patch = b''.join(difflib.diff_bytes(difflib.unified_diff,before.splitlines(True),after.splitlines(True),
                                             b'a/README.md',b'b/README.md'))
        file.update(afterSha256=B.sha(after))
        file['patch']['sha256'] = B.sha(patch)
        check = V.checked
        with mock.patch.object(V,'checked',side_effect=lambda root,item:patch if item==file['patch'] else check(root,item)):
            V.check_patches(ROOT,manifest,labels)

    def test_unchanged_owner_audit_reads_main_when_head_differs(self):
        def snapshot(repo,*args):
            if args[0]=='rev-parse':return b'main-revision' if args[1]=='origin/main' else b'local-head'
            if args[0]=='ls-tree':
                return b'README.md\n_bmad-output/planning-artifacts/prd.md\n' if args[3]=='main-revision' else b'README.md\n'
            if args[0]=='show':return ('McpCli '+args[1]).encode()
            self.fail(args)
        with mock.patch.object(B,'git',side_effect=snapshot):
            audit=B.inspect_unchanged(ROOT,'commons','no proprietary product target')
        self.assertEqual(audit['revision'],'main-revision')
        self.assertEqual(audit['inspected'],[{'path':p,'sha256':B.sha(('McpCli main-revision:'+p).encode())}
                                             for p in ['README.md','_bmad-output/planning-artifacts/prd.md']])

    def test_technical_companions_separate_current_authority_from_historical_pins(self):
        rows=B.rows(B.successor('technical-tools').decode())
        for key, family in [('PS05','parties'),('PS06','memories'),('PS08','projects'),('PS10','folders'),('PS12','chatbot'),('PS14','memories')]:
            cell=next(v for v in rows[key].values() if v.startswith('Current:'))
            current,historical=cell.split('Historical census observation:',1)
            binding=data('inputs.json')['inventoryHistories'][family][-1]
            self.assertIn(binding['sourceRevision'],current)
            self.assertIn(Path(binding['path']).name,current)
            if key=='PS14':
                self.assertIn('T01–T04 account for all four modes',current)
                self.assertIn('Memories inventory 1.0.0',historical)

    def test_unlisted_secondary_patch_target_refused(self):
        manifest = data('upstream/manifest.json')
        file = manifest['owners'][0]['files'][0]
        patch = V.checked(ROOT,file['patch']) + b'--- /dev/null\n+++ b/other.md\n@@ -0,0 +1 @@\n+unrequested\n'
        file['patch']['sha256'] = B.sha(patch)
        checked = V.checked
        with mock.patch.object(V,'checked',side_effect=lambda root,item: patch if item==file['patch'] else checked(root,item)):
            self.refusal({str(E/'upstream/manifest.json'):manifest},'eventstore: patch must affect only README.md')

    def test_unchanged_inspections_bind_reason_and_source_files(self):
        for field in ['reason','inspected']:
            manifest = data('upstream/manifest.json')
            entry = manifest['noChange'][0]
            entry[field] = 'unjustified' if field=='reason' else []
            self.refusal({str(E/'upstream/manifest.json'):manifest},entry['name']+': inspected main paths, hashes or rationale differ')

    def test_audit_includes_resolution_and_identifies_unsourced_owner(self):
        entries=data('deferral-dispositions.json')['entries']
        drift=next(e for e in entries if e['summary'].startswith('Migration planning artifacts disagree'))
        self.assertIn('Unrecorded; proposed',drift['owner'])
        self.assertIn('exact-byte owner acceptance',drift['audit'])
        resolved=next(e for e in entries if 'delivery-outcomes.json' in e.get('resolution',''))
        self.assertTrue(resolved['sourceStatus'].startswith('resolved'))
        self.assertIn(resolved['resolution'],(ROOT/E/'deferral-dispositions.md').read_text())

    def test_failed_regeneration_does_not_mutate_existing_packet(self):
        receipt_path=ROOT/E/'approval.json'
        initial=receipt_path.read_bytes()
        pending_text=json.dumps(pending())
        read=Path.read_text
        def pending_receipt(path,*args,**kwargs):
            return pending_text if path==receipt_path else read(path,*args,**kwargs)
        # Replay the incoming owner files even after their main branches publish the packet.
        bases = {(ROOT / owner['ownerCheckout']).resolve(): owner['baseRevision']
                 for owner in data('upstream/manifest.json')['owners']}
        git = B.git
        def before_publication(repo, *args):
            if repo in bases and args in [('rev-parse', 'origin/main'), ('rev-parse', 'HEAD')]:
                return bases[repo].encode()
            return git(repo, *args)
        with mock.patch.object(Path,'read_text',pending_receipt), mock.patch.object(B,'git',side_effect=before_publication), \
             mock.patch.object(B,'inspect_unchanged',side_effect=ValueError('missing owner main')), \
             mock.patch.object(Path,'write_bytes',side_effect=AssertionError('early packet write')), \
             mock.patch.object(Path,'write_text',side_effect=AssertionError('early packet write')):
            self.assertEqual(streams(B.cli),(1,'','FAIL: missing owner main\n'))
        self.assertEqual((ROOT/E/'approval.json').read_bytes(),initial)

    def test_all_deferrals_retain_source_owner_gate_and_acceptance_boundary(self):
        audit=data('deferral-dispositions.json')
        expected = V.historical_deferrals(ROOT)
        self.assertEqual(audit['entries'],expected)
        self.assertTrue(any('invoke_plugins.mjs' in row['evidence'] and 'AC3' in row['sourceStatus'] for row in expected))
        for field,value in [('entries',audit['entries'][1:]),('state','accepted')]:
            changed=copy.deepcopy(audit);changed[field]=value
            message='deferral accounting/source/owner/gate mismatch' if field=='entries' else 'deferral audit must retain explicit owner-decision gate'
            self.refusal({str(E/'deferral-dispositions.json'):changed},message)
        for field in ['owner','gate','ownerDecision']:
            changed=copy.deepcopy(audit);changed['entries'][0][field]='Accepted without owner' if field=='ownerDecision' else ''
            self.refusal({str(E/'deferral-dispositions.json'):changed},'deferral accounting/source/owner/gate mismatch')

    def test_unresolved_conflicts_and_deadline_cannot_disappear_from_plan(self):
        path=ROOT/E/'upstream/ai-tools/hexalith-mcpcli-migration-instructions.md'
        original=Path.read_text
        for token in ['G01–G06','Folders owners retain the K12','Payload paging versus AD-20','2027-02-05','never counted retired']:
            def read_text(p,*args,**kwargs):
                text=original(p,*args,**kwargs)
                return text.replace(token,'REMOVED') if p==path else text
            with self.subTest(token=token),mock.patch.object(Path,'read_text',read_text):
                self.refusal({},'prepared plan lost independent gate/exemption: '+token)

    def test_completion_automatically_triggers_for_done_spec_and_sprint(self):
        original=Path.read_text
        for path,key in [(ROOT/B.SPEC,'status'),(ROOT/B.A/'sprint-status.yaml','  5-11-reconcile-product-claims-and-the-migration-plan')]:
            def read_text(p,*args,**kwargs):
                text=original(p,*args,**kwargs)
                return V.re.subn(r'^'+V.re.escape(key)+r': \S+',key+': done',text,count=1,flags=V.re.M)[0] if p==path else text
            with self.subTest(path=path),mock.patch.object(Path,'read_text',read_text):
                self.refusal({str(E/'approval.json'):pending()},'completion requires fresh exact-byte successor approval')

    def test_integrated_state_triggers_completion_from_both_records(self):
        for record in ('integration.json','labels.json'):
            with self.subTest(record=record), mock.patch.object(
                V,'check_completion',side_effect=ValueError('completion checks invoked')
            ):
                value = dict(data(record),state='integrated')
                overrides = {str(E/'integration.json'):data('integration.json'),str(E/record):value}
                self.refusal(overrides,'completion checks invoked')

    def test_story_510_requires_the_exact_approval_labels_and_delivery_binding(self):
        changes = [
            ('labels binding',lambda bound:bound['labels'].update(sha256='0'*64)),
            ('approval binding',lambda bound:bound['approval'].update(sha256='0'*64)),
            ('delivery binding',lambda bound:bound.update(inventoryRevision='0'*40)),
        ]
        for message,change in changes:
            with self.subTest(binding=message):
                inputs = data('inputs.json')
                change(inputs['prerequisites']['story510'])
                self.refusal({str(E/'inputs.json'):inputs},'Story 5.10 '+message+' mismatch')

    def test_guard_removals_are_detected_for_hash_roles_history_labels_and_gates(self):
        cases=[]
        receipt=approved();receipt['rolesCovered']=[]
        cases.append(('approval lacks explicitly covered roles',lambda ns:ns['check_approval'](receipt,receipt['artifacts'],receipt['requiredApprovalRoles'])))
        bad=pending();bad['artifacts']={}
        cases.append(('approval artifact accounting/hash mismatch',lambda ns:ns['check_approval'](bad,receipt['artifacts'],receipt['requiredApprovalRoles'])))
        unconfirmed=approved();unconfirmed.pop('exactRoleConfirmation')
        cases.append(('approval lacks explicit confirmation of the reviewed roles',lambda ns:ns['check_approval'](unconfirmed,unconfirmed['artifacts'],unconfirmed['requiredApprovalRoles'])))
        undigested=approved();undigested.pop('reviewedReceiptSha256')
        cases.append(('approval lacks the exact reviewed receipt digest',lambda ns:ns['check_approval'](undigested,undigested['artifacts'],undigested['requiredApprovalRoles'])))
        inputs=data('inputs.json');inputs['inventoryHistories']['invented']=[]
        cases.append(('eight-family history accounting mismatch',lambda ns:ns['check_histories'](ROOT,inputs)))
        labels=data('labels.json');labels['rows']=[r for r in labels['rows'] if r['id']!='PS01']
        cases.append(('fourteen-label accounting/duplicate mismatch',lambda ns:ns['check_labels'](ROOT,labels)))
        gate=data('labels.json');gate['rows'][0]['gate']='Invented gate';gate['rows'][0]['label']['text']+=' Invented gate';gate['rows'][0]['label']['sha256']=B.sha(gate['rows'][0]['label']['text'].encode())
        cases.append(('owner/surface/removal gate changed',lambda ns:ns['check_labels'](ROOT,gate)))
        for token,action in cases:
            with self.subTest(guard=token):
                with self.assertRaises(ValueError): action(V.__dict__)
                action(without_guard(token))

    def test_builder_refuses_approved_packet_without_writing(self):
        original=Path.read_text
        approved_text=json.dumps(approved())
        def read_text(path,*args,**kwargs):
            return approved_text if path==ROOT/E/'approval.json' else original(path,*args,**kwargs)
        with mock.patch.object(Path,'read_text',read_text),mock.patch.object(B,'deferral_documents') as writes:
            self.assertEqual(streams(B.cli),(1,'','FAIL: Approved packet is immutable; prepare an explicitly authorized successor instead\n'))
            writes.assert_not_called()

    def test_literal_patch_preserves_source_and_refuses_missing_or_duplicate_targets(self):
        patch=B.serialized({'schemaVersion':'1.0.0','path':'architecture.md','edits':[{'old':'before','new':'after'}]})
        self.assertEqual(V.literal_patch(b'before',patch,'architecture.md'),b'after')
        for before in [b'missing',b'before before']:
            with self.subTest(before=before),self.assertRaisesRegex(ValueError,'literal patch target missing/duplicated'):
                V.literal_patch(before,patch,'architecture.md')


class CompletionBindingTests(unittest.TestCase):
    """Replay the actual delivery and validate isolated broken bindings."""

    def run_binding(self, mutate=None, git_mutation=None, plan_mutation=None, *,
                    resolved=True, default=False, full=False, file_mutation=None,
                    owner_conflict=None, hosted_mutation=None):
        receipt = data('approval.json')
        manifest = data('upstream/manifest.json')
        integration = data('integration.json')
        final = data('final-plan-approval.json')
        integration.update(state='delivered' if default else 'integrated',
                           completedOn=None if default else '2026-11-22')
        git = recorded_git
        ai_repo = ROOT.parent/'aitools'
        if plan_mutation:
            raw = git(ai_repo,'show',integration['aiToolsCommit']+':'+V.PLAN_PATH)
            plan = plan_mutation(raw.decode()).encode()
            final['planSha256'] = integration['planSha256'] = B.sha(plan)

        files, hosted, release_evidence = {}, {}, {}
        tag = 'v2.0.2'
        tag_ref = 'refs/tags/'+tag
        def binding(path, raw):
            files[ROOT/path] = raw
            return {'path':str(path),'sha256':B.sha(raw)}

        if resolved:
            audit = data('deferral-dispositions.json')
            entry = next(row for row in audit['entries'] if row['id'] == V.RELEASE_NOTES_ENTRY)
            ledger = git(ROOT,'show',V.INVENTORY_PUBLICATION+':'+str(V.LEDGER)).decode()
            start = ledger.index('  summary: '+entry['summary'])
            end = len(ledger.rstrip())
            update = ledger[start:end].replace('  status: open;','  status: resolved;',1)
            update += '\n  resolution: The release owner verified the generated notes.\n'
            ledger = ledger[:start]+update+ledger[end:]
            files[ROOT/V.LEDGER] = ledger.encode()
            active = next(row for row in B.scoped_deferrals(ledger) if row['id'] == entry['id'])
            rev = integration['rootIntegrationRevision']
            status = git(ROOT,'show',rev+':docs/release/migration-status.md')
            notes_body = b'# Generated release notes\n\n'+status
            notes = binding('fixture-notes.md',notes_body)
            resolution = {
                'decision':'resolved','entryId':entry['id'],'auditedEntrySha256':entry['entrySha256'],
                'resolvedEntrySha256':active['entrySha256'],'owner':'Hexalith.Builds',
                'exactWords':'approve','source':'Fixture release owner decision',
                'decidedOn':'2026-11-22','releaseRevision':rev,'releaseTag':tag,'releaseRunId':123,'generatedNotes':notes,
                'evidenceRevision':V.FINAL_INTEGRATION_RECORD,
            }
            hosted.update({
                'publishedRelease':{'html_url':V.ROOT_REPOSITORY+'/releases/tag/'+tag,'draft':False,'tag_name':tag,
                                    'published_at':'2026-11-22T23:59:00Z','id':456,'body':notes_body.decode()},
                'releaseRun':{'id':123,'conclusion':'success','head_sha':rev,'path':'.github/workflows/release.yml',
                              'html_url':V.ROOT_REPOSITORY+'/actions/runs/123'},
            })
            if hosted_mutation:
                hosted_mutation(hosted)
            for key,value in hosted.items():
                resolution[key] = binding('fixture-'+key+'.json',B.serialized(value))
            release_evidence = {str(path.relative_to(ROOT)):raw for path,raw in files.items() if path != ROOT/V.LEDGER}
            integration['releaseNotesResolution'] = binding('fixture-resolution.json',B.serialized(resolution))
        if mutate:
            mutate(integration,final)
        if final != data('final-plan-approval.json'):
            integration['finalPlanApproval'] = binding(E/'final-plan-approval.json',B.serialized(final))
        if file_mutation:
            file_mutation(integration,files,binding)
        read,read_bytes,read_text = V.read,Path.read_bytes,Path.read_text
        deliveries = {owner['name']:owner['commit'] for owner in data('integration.json')['ownerIntegrations']}
        delivered = {(owner['name'],file['path']):deliveries[owner['name']]
                     for owner in manifest['owners'] for file in owner['files']}
        owner_text = {
            'prd-Hexalith.ChatBot-2026-05-28/prd.md':
                ((b'Inspect, associate, reject, defer, retry, approve, execute',
                  b'human-decision mutations require current presence at submission',
                  b'user-delegated via OAuth device flow',
                  b'UI/API, CLI, and MCP association/status/audit parity',
                  b'CLI and MCP integration must expose the same governed operations as the UI'),
                 b'approved execution and confirmation-required behavior route to the confidential ChatBot UI.'),
            'ux-Hexalith.ChatBot-2026-05-28/EXPERIENCE.md':
                ((b'Human-delegated MCP approval is candidate M1 behavior',
                  b'candidate human-delegated MCP approval remains unavailable',
                  b'explicitly exposed on UI, CLI, and/or MCP',
                  b'He confirms an association through an exposed surface'),b'Both McpCli heads refuse those operations.'),
            'ux-works-2026-06-14/EXPERIENCE.md':
                ((b'Exact MCP tools/resources and CLI commands over the kernel',
                  b'exact tool/resource names and syntax remain source-open'),
                 b'Discover enrolled Works Commands and Queries through the generic McpCli heads.'),
            'ux-works-2026-06-14/DESIGN.md':
                ((b'exact tools, resources, syntax, and protocol remain source-open',),
                 b'after Works Contracts enrollment and authorization.'),
            'ux-works-2026-06-14/mockups/key-mcp-cli.html':
                ((b'Both adapters expose registered domain commands and resources',),
                 b'The shared McpCli CLI and stdio MCP heads expose eligible Works operations'),
        }
        owner_check = V.check_owner_conflicts
        checking_owner_conflicts = False

        def check_conflicts(root):
            nonlocal checking_owner_conflicts
            checking_owner_conflicts = True
            try:
                owner_check(root)
            finally:
                checking_owner_conflicts = False

        def git_fixture(repo,*args):
            if git_mutation:
                changed = git_mutation(repo,args,git)
                if changed is not None:
                    return changed
            if plan_mutation and repo == ai_repo and args[0] == 'show' and args[1].endswith(':'+V.PLAN_PATH):
                return plan
            if args in (('rev-parse',tag_ref),('rev-parse',tag_ref+'^{commit}')):
                return integration['rootIntegrationRevision'].encode()
            if repo == ROOT and args[0] == 'show' and args[1].startswith(V.FINAL_INTEGRATION_RECORD+':'):
                artifact = args[1].split(':',1)[1]
                if artifact in release_evidence:
                    return release_evidence[artifact]
            if args[0] == 'show' and args[1].startswith('origin/main:'):
                owner = Path(repo).name.lower().split('.')[-1]
                if owner == 'aitools':
                    owner = 'ai-tools'
                path = args[1].removeprefix('origin/main:')
                revision = delivered.get((owner,path))
                if checking_owner_conflicts:
                    for suffix,(prior,replacement) in owner_text.items():
                        if path.endswith(suffix):
                            return b'\n'.join(prior) if owner == owner_conflict else replacement
                if revision:
                    return git(repo,'show',revision+':'+path)
            return git(repo,*args)

        def run(*args):
            check = V.check_delivery if default else V.check_completion
            check(ROOT,receipt,data('labels.json'),manifest,integration)
            return 'approved', True

        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(Path,'read_bytes',lambda path: files[path] if path in files else read_bytes(path)))
            stack.enter_context(mock.patch.object(Path,'read_text',lambda path,*a,**kw: files[path].decode() if path in files else read_text(path,*a,**kw)))
            stack.enter_context(mock.patch.object(V,'read',side_effect=lambda root,path: integration if path==E/'integration.json' else read(root,path)))
            stack.enter_context(mock.patch.object(B,'git',side_effect=git_fixture))
            stack.enter_context(mock.patch.object(V,'check_owner_conflicts',side_effect=check_conflicts))
            if not full:
                stack.enter_context(mock.patch.object(V,'verify',side_effect=run))
                stack.enter_context(mock.patch.object(V,'check_prior_delivery'))
            return streams(lambda:V.main([] if default else ['--approved-completion']))

    def refusal(self, message, *args, **kwargs):
        self.assertEqual(self.run_binding(*args,**kwargs),(1,'','FAIL: '+message+'\n'))

    def test_actual_delivery_and_later_ac3_resolution_run_through_default_entry_point(self):
        expected = (0,VERIFIED,'')
        self.assertEqual(self.run_binding(default=True,full=True),expected)
        self.assertEqual(self.run_binding(full=True),expected)
        self.refusal('eventstore: verified owner file count mismatch',
                     lambda i,f:i['ownerIntegrations'][0].update(verifiedFileCount=0),default=True,full=True)

    def test_open_ac3_boolean_is_no_substitute_for_an_explicit_resolution(self):
        self.refusal('AC3 generated release notes remain deferred by the owner',
                     lambda i,f:i['deferralOwnerDecision'].update(acceptCompletionWithDeferredReleaseNotes=True),
                     resolved=False,full=True)

    def test_ac3_requires_current_ledger_decision_and_actual_generated_text(self):
        def change_resolution(update):
            def mutate(integration,files,binding):
                value = json.loads(files[ROOT/'fixture-resolution.json'])
                update(value,files,binding)
                integration['releaseNotesResolution'] = binding('fixture-resolution.json',B.serialized(value))
            return mutate

        cases = [
            ('AC3 resolution lacks an explicit owner decision bound to the approved entry',
             lambda r,files,b:r.update(exactWords='I do not approve closing AC3')),
            ('AC3 resolution lacks an explicit owner decision bound to the approved entry',
             lambda r,files,b:r.update(owner='Unrelated maintainer')),
            ('AC3 resolution must bind the resolved release ledger entry',
             lambda r,files,b:files.pop(ROOT/V.LEDGER)),
            ('AC3 generated notes omit the committed migration status',
             lambda r,files,b:r.update(generatedNotes=b('fixture-notes.md',b'Notes without migration status.'))),
            ('AC3 generated notes omit the committed migration status',
             lambda r,files,b:r.update(generatedNotes=b('fixture-notes.md',files[ROOT/'fixture-notes.md']+b'\nAll surfaces retired.'))),
            ('AC3 requires committed release and generation-run evidence for the tag',
             lambda r,files,b:r.pop('releaseRunId')),
            ('AC3 resolution requires the full release source revision',
             lambda r,files,b:r.update(releaseRevision=r['releaseRevision'][:8])),
            ('AC3 owner decision date missing',
             lambda r,files,b:r.pop('decidedOn')),
            ('AC3 resolution date does not follow release or exceeds completion',
             lambda r,files,b:r.update(decidedOn='2026-11-21')),
            ('AC3 resolution date does not follow release or exceeds completion',
             lambda r,files,b:r.update(decidedOn='2026-11-23')),
        ]
        for message,update in cases:
            with self.subTest(message=message):
                self.refusal(message,file_mutation=change_resolution(update))

    def test_release_requires_exact_source_workflow_and_committed_published_notes(self):
        self.refusal('AC3 release tag does not identify the approved source revision',
                     git_mutation=lambda r,a,g:('0'*40).encode() if a == ('rev-parse','refs/tags/v2.0.2^{commit}') else None)
        self.refusal('AC3 release generation run does not bind the tagged source',
                     hosted_mutation=lambda records:records['releaseRun'].update(head_sha='0'*40))
        self.refusal('AC3 approved generated notes do not match the published release body',
                     hosted_mutation=lambda records:records['publishedRelease'].update(body='Different notes.'))
        self.refusal('AC3 release evidence differs from the committed record: releaseRun',
                     git_mutation=lambda r,a,g:b'other' if a == ('show',V.FINAL_INTEGRATION_RECORD+':fixture-releaseRun.json') else None)

    def test_release_requires_published_identity_and_ordered_evidence(self):
        for key,value in [('draft',True),('tag_name','v0.0.0'),('id','456'),('html_url','https://example.invalid/release')]:
            with self.subTest(field=key):
                self.refusal('AC3 requires a published McpCli release record for the tag',
                             hosted_mutation=lambda hosted:hosted['publishedRelease'].update({key:value}))
        release = data('integration.json')['rootIntegrationRevision']
        def commit_time(revision, timestamp):
            return lambda repo,args,git: timestamp.encode() if args == ('show','-s','--format=%cI',revision) else None
        for mutation in (
            {'hosted_mutation':lambda hosted:hosted['publishedRelease'].update(published_at='2026-11-21T23:59:00Z')},
            {'git_mutation':commit_time(V.FINAL_INTEGRATION_RECORD,'2026-11-21T23:59:00+00:00')},
            {'git_mutation':commit_time(V.FINAL_INTEGRATION_RECORD,'2026-11-22T23:30:00-02:00')},
        ):
            with self.subTest(mutation=mutation):
                self.refusal('AC3 owner approval predates the committed release evidence',**mutation)
        self.assertEqual(self.run_binding(git_mutation=commit_time(release,'2026-11-23T00:30:00+02:00')),
                         (0,VERIFIED,''))

    def test_completion_requires_both_owner_conflicts_to_be_closed(self):
        for owner,path in [
            ('chatbot','prds/prd-Hexalith.ChatBot-2026-05-28/prd.md'),
            ('works','ux-designs/ux-works-2026-06-14/EXPERIENCE.md'),
        ]:
            self.refusal('completion requires published '+owner+' migration guidance: _bmad-output/planning-artifacts/'+path,
                         owner_conflict=owner)

    def test_owner_guidance_requires_visible_correction_and_refuses_each_stale_claim(self):
        documents = replay_follow_up()
        self.assertIsNone(self.check_guidance(documents))
        for (owner,path),raw in documents.items():
            with self.subTest(owner=owner,path=path):
                self.assertNotIn(b'Current McpCli disposition (Story 5.11 candidate)',raw)
                self.assertNotIn(b'Shared McpCli access (reconciliation candidate)',raw)
                if owner in {'frontcomposer','tenants'}:
                    self.assertIn(b'the approved AI.Tools migration plan',raw)
                if owner == 'projects':
                    self.assertIn(b'An installed tool discovers them only from a published McpCli release that enrolls Projects.Contracts 2.0.0.',raw)
                if owner == 'parties':
                    self.assertIn(b'dotnet tool install --global Hexalith.McpCli --version 2.0.1',raw)
        targets = (
            ('chatbot','prds/prd-Hexalith.ChatBot-2026-05-28/prd.md',
             b'approved execution and confirmation-required behavior route to the confidential ChatBot UI.',
             [b'user-delegated via OAuth device flow',b'UI/API, CLI, and MCP association/status/audit parity']),
            ('chatbot','ux-designs/ux-Hexalith.ChatBot-2026-05-28/EXPERIENCE.md',
             b'Both McpCli heads refuse those operations.',
             [b'explicitly exposed on UI, CLI, and/or MCP']),
            ('works','ux-designs/ux-works-2026-06-14/EXPERIENCE.md',
             b'Discover enrolled Works Commands and Queries through the generic McpCli heads.',
             [b'Exact MCP tools/resources and CLI commands over the kernel']),
        )
        for owner,suffix,required,obsolete in targets:
            path = '_bmad-output/planning-artifacts/'+suffix
            raw = documents[owner,path]
            changes = [raw.replace(required,b'<!-- '+required+b' -->'),*(raw+b'\n'+phrase for phrase in obsolete)]
            for index,changed in enumerate(changes):
                with self.subTest(path=path,edit=index):
                    self.assertEqual(self.check_guidance({**documents,(owner,path):changed}),
                                     'completion requires published '+owner+' migration guidance: '+path)

    def check_guidance(self, documents):
        git = B.git
        def owner_docs(repo,*args):
            if args[0]=='show' and args[1].startswith('origin/main:'):
                return documents[repo.name.lower().split('.')[-1],args[1].removeprefix('origin/main:')]
            return git(repo,*args)
        with mock.patch.object(B,'git',side_effect=owner_docs):
            try:
                V.check_owner_conflicts(ROOT)
            except ValueError as error:
                return str(error)
        return None

    def test_audited_unresolved_owner_cannot_change_without_a_separate_resolution(self):
        first = next(e for e in data('deferral-dispositions.json')['entries'] if e['id']=='fb595c8ae94063d4')
        def change_owner(integration,files,binding):
            text = files[ROOT/V.LEDGER].decode()
            start = text.index('  summary: '+first['summary'])
            index = text.index('  owner:',start)
            files[ROOT/V.LEDGER] = (text[:index]+text[index:].replace('  owner:', '  owner: Unrelated owner replaces',1)).encode()
        self.refusal('audited deferral changed without a separate resolution: fb595c8ae94063d4',
                     file_mutation=change_owner)
        def update_evidence(integration,files,binding):
            text = files[ROOT/V.LEDGER].decode()
            start = text.index('  summary: '+first['summary'])
            index = text.index('  evidence:',start)
            files[ROOT/V.LEDGER] = (text[:index]+text[index:].replace('  evidence:', '  evidence: More verification. ',1)).encode()
        self.assertEqual(self.run_binding(file_mutation=update_evidence)[0],0)

    def test_changed_deferral_requires_a_unique_entry_and_a_committed_owner_resolution(self):
        entry = next(e for e in data('deferral-dispositions.json')['entries'] if e['id']=='fb595c8ae94063d4')
        entry_id = entry['id']
        revision = V.FINAL_INTEGRATION_RECORD
        def exercise(change_resolution=None, ledger_change=None, committed=True):
            def update(integration,files,binding):
                text = files[ROOT/V.LEDGER].decode()
                summary = text.index('  summary: '+entry['summary'])
                start = text.rindex('- source_spec:',0,summary)
                end = text.index('\n\n',summary)
                raw = text[start:end]
                if ledger_change is not None:
                    files[ROOT/V.LEDGER] = (text[:start]+ledger_change(raw)+text[end:]).encode()
                    return
                resolved = re.sub(r'\n  status: [^\n]*','',raw)+'\n  status: resolved by the owning maintainer.'
                resolved += '\n  resolution: The maintainer verified the existing requirement.'
                files[ROOT/V.LEDGER] = (text[:start]+resolved+text[end:]).encode()
                resolution = {
                    'entryId':entry_id,'auditedEntrySha256':entry['entrySha256'],
                    'resolvedEntrySha256':B.sha(resolved.encode()),'owner':entry['owner'],
                    'exactWords':'approve','source':'Fixture owning maintainer decision','decision':'resolved',
                    'revision':revision,
                }
                if change_resolution:
                    change_resolution(resolution)
                integration['deferralResolutions'] = {
                    entry_id: binding('fixture-deferral-resolution.json',B.serialized(resolution)),
                }
                if committed:
                    published[str(V.LEDGER)] = files[ROOT/V.LEDGER]
            published = {}
            def git_fixture(repo,args,git):
                if repo == ROOT and args == ('show',revision+':'+str(V.LEDGER)):
                    return published.get(str(V.LEDGER),b'Unrelated ledger')
            return self.run_binding(file_mutation=update,git_mutation=git_fixture)

        self.assertEqual(exercise(),(0,VERIFIED,''))
        for change in (lambda raw:'',lambda raw:raw+'\n\n'+raw,
                       lambda raw:raw.replace(entry['sourceSpec'],str(B.A/'spec-5-20-fixture.md'))):
            with self.subTest(change=change):
                self.assertEqual(exercise(ledger_change=change),
                                 (1,'','FAIL: audited deferral missing or duplicated: '+entry_id+'\n'))
        for field,value in [('owner','Unrelated maintainer'),('exactWords','I do not approve'),
                            ('decision','denied'),('auditedEntrySha256','0'*64),
                            ('resolvedEntrySha256','0'*64),('entryId','unrelated')]:
            with self.subTest(field=field):
                self.assertEqual(exercise(change_resolution=lambda resolution:resolution.update({field:value})),
                                 (1,'','FAIL: separate resolution does not close the audited owner gate: '+entry_id+'\n'))
        self.assertEqual(exercise(change_resolution=lambda resolution:resolution.update(revision=revision[:8])),
                         (1,'','FAIL: audited deferral resolution lacks a committed revision: '+entry_id+'\n'))
        self.assertEqual(exercise(committed=False),
                         (1,'','FAIL: audited deferral resolution differs from the recorded ledger revision: '+entry_id+'\n'))

    def test_mandatory_delivery_bindings(self):
        cases = [
            ('completion requires integrated plan and all fourteen labels',lambda i,f:i.update(state='blocked')),
            ('completion requires separate explicit Git delivery authorization',lambda i,f:i['deliveryAuthorization'].update(exactWords='authorize',footprint='')),
            ('Git delivery authorization does not bind the approved packet receipt',lambda i,f:i['deliveryAuthorization'].update(approvalSha256='0'*64)),
            ('Git delivery authorization differs from the immutable publication record',lambda i,f:i['deliveryAuthorization'].update(footprint='Only unrelated edits.')),
            ('completion requires the frozen published inventory revision',lambda i,f:i.update(inventoryRevision=None)),
            ('McpCli publication lacks approved artifact count or receipt digest',lambda i,f:i.pop('inventoryPublication')),
            ('McpCli publication lacks approved artifact count or receipt digest',lambda i,f:i['inventoryPublication'].update(approvedArtifactsVerified=0)),
            ('McpCli publication lacks approved artifact count or receipt digest',lambda i,f:i['inventoryPublication'].update(approvalSha256='0'*64)),
            ('McpCli publication lacks passing commitlint and story tests',lambda i,f:i['inventoryPublication']['checks'].update(commitlint='failed')),
            ('McpCli publication checks or scoped Builds exception differ from recorded evidence',lambda i,f:i['inventoryPublication'].pop('exception')),
            ('completion requires every owner integration binding',lambda i,f:i.update(ownerIntegrations=[])),
            ('eventstore: upstream integration missing',lambda i,f:i['ownerIntegrations'][0].update(commit=None)),
            ('eventstore: mandatory commitlint/Builds checks missing',lambda i,f:i['ownerIntegrations'][0]['checks'].update(builds='blocked')),
            ('completion requires full AI.Tools integration revision',lambda i,f:i.update(aiToolsCommit=None)),
            ('AI.Tools revision differs from actual owner integration',lambda i,f:i.update(aiToolsCommit='0'*40)),
            ('containing AI.Tools gitlink missing',lambda i,f:i.update(aiToolsGitlink=None)),
            ('ai-tools: integrated documentation bytes mismatch',lambda i,f:i.update(planSha256=None)),
            ('final plan exact-byte approval/hash/revision binding missing',lambda i,f:f.update(decision='pending')),
            ('final plan approval lacks covered roles',lambda i,f:f.update(rolesCovered=[])),
            ('passing instruction synchronization binding missing',lambda i,f:i.update(instructionSync=None)),
            ('AI.Tools final approval must bind the merged review and its exact head',lambda i,f:i['finalPlanReview'].update(state='open')),
            ('AI.Tools final approval must bind the merged review and its exact head',lambda i,f:f.update(reviewCommit='0'*40)),
            ('AI.Tools hosted checks do not bind the approved review head',lambda i,f:i['ownerIntegrations'][-1]['checks'].update(testedHead='0'*40)),
            ('AI.Tools hosted checks differ from the immutable final integration record',lambda i,f:i['ownerIntegrations'][-1]['checks'].update(run='https://github.com/Hexalith/Hexalith.AI.Tools/actions/runs/1')),
            ('completion requires explicit structured deferral owner decision',lambda i,f:i.update(deferralOwnerDecision=None)),
            ('deferral decision must bind exact audit bytes',lambda i,f:i['deferralOwnerDecision'].update(auditSha256='0'*64)),
            ('deferral decision must bind the reviewed packet and owner instruction',lambda i,f:i['deferralOwnerDecision'].update(exactWords='deny')),
            ('deferral decision must bind the reviewed packet and owner instruction',lambda i,f:i['deferralOwnerDecision'].update(reviewedReceiptSha256='0'*64)),
            ('deferral decision must preserve every unresolved owner/gate',lambda i,f:i['deferralOwnerDecision'].update(retainedUnresolvedEntryIds=[])),
            ('recorded completion date is in the future',lambda i,f:i.update(completedOn='9999-12-31')),
            ('deferral decision occurs after completion',lambda i,f:i['deferralOwnerDecision'].update(decidedOn='2026-11-23')),
            ('completion predates approval or verified delivery',lambda i,f:f.update(approvedOn='2026-11-23')),
            ('completion predates approval or verified delivery',lambda i,f:i.update(integratedOn='2026-11-23')),
            ('SM-3 assessment must bind recorded completion date',lambda i,f:i['sm3Assessment'].update(assessedOn='2026-01-01')),
            ('SM-3 met requires evidenced retirement',lambda i,f:i['sm3Assessment'].update(outcome='met')),
        ]
        for message,mutate in cases:
            with self.subTest(message=message):
                self.refusal(message,mutate)

    def test_content_and_complete_delivery_footprints(self):
        integration = data('integration.json')
        receipt = data('approval.json')
        path = next(iter(receipt['artifacts']))
        eventstore = integration['ownerIntegrations'][0]['commit']
        pin = integration['rootIntegrationRevision']
        self.refusal('published approved artifact bytes mismatch: '+path,
                     git_mutation=lambda r,a,g:b'changed' if a==('show',V.INVENTORY_PUBLICATION+':'+path) else None)
        self.refusal('published receipt bytes mismatch',
                     git_mutation=lambda r,a,g:g(r,*a)+b'\n' if a==('show',V.INVENTORY_PUBLICATION+':'+str(E/'approval.json')) else None)
        self.refusal('eventstore: integrated documentation bytes mismatch',
                     git_mutation=lambda r,a,g:b'changed' if a==('show',eventstore+':README.md') else None)
        self.refusal('eventstore: mandatory commitlint/Builds checks missing',
                     git_mutation=lambda r,a,g:b'.github/hexalith-ci.json' if a==('ls-tree','--name-only',eventstore,'--','.github/hexalith-ci.json') else None)
        for commit,owner in [(eventstore,'eventstore'),(pin,'McpCli AI.Tools pin')]:
            self.refusal(owner+': delivery commit changes files outside its approved footprint',
                         git_mutation=lambda r,a,g:g(r,*a)+b'other.md\0' if a[0]=='diff' and a[-1]==commit else None)
        self.refusal('committed root agent instructions differ',
                     git_mutation=lambda r,a,g:b'changed' if a==('show',pin+':CLAUDE.md') else None)
        final = data('final-plan-approval.json')
        self.refusal('AI.Tools tested and merged documentation bytes differ: hexalith-llm-instructions.md',
                     git_mutation=lambda r,a,g:b'changed' if a==('show',final['reviewCommit']+':hexalith-llm-instructions.md') else None)

    def test_squash_merged_checkout_can_replay_immutable_review_with_pr_head_absent(self):
        reviewed = data('final-plan-approval.json')['reviewCommit']
        def missing(repo,args,git):
            if repo == ROOT.parent/'aitools':
                if args == ('rev-list','--no-walk','--ignore-missing',reviewed):
                    return b''
                if any(value.startswith(reviewed) for value in args[1:]):
                    self.fail('Verifier tried to inspect a missing squash-merge PR head: '+repr(args))
        self.assertEqual(self.run_binding(git_mutation=missing,default=True)[0],0)
        self.refusal('AI.Tools hosted checks differ from the immutable final integration record',
                     lambda i,f:i['ownerIntegrations'][-1]['checks'].update(
                         run='https://github.com/Hexalith/Hexalith.AI.Tools/actions/runs/1'),
                     git_mutation=missing,default=True)

    def test_delivery_requires_main_containment_committed_pin_bytes_and_historical_blobs(self):
        integration = data('integration.json')
        eventstore = integration['ownerIntegrations'][0]['commit']
        def off_main(repo,args,git):
            if args == ('merge-base','--is-ancestor',eventstore,'origin/main'):
                raise ValueError('upstream main excludes integrated commit')
        self.refusal('upstream main excludes integrated commit',git_mutation=off_main)

        ai = integration['aiToolsCommit']
        pin = integration['rootIntegrationRevision']
        changed_link = '0'*40
        rule = 'hexalith-llm-instructions.md'
        def changed_gitlink(repo,args,git):
            if args == ('ls-tree',pin,V.AI_TOOLS_GITLINK):
                return f'160000 commit {changed_link}\t{V.AI_TOOLS_GITLINK}\n'.encode()
            if args == ('merge-base','--is-ancestor',ai,changed_link):
                return b''
            if args == ('show',changed_link+':'+V.PLAN_PATH):
                return git(repo,'show',ai+':'+V.PLAN_PATH)
            if args == ('show',changed_link+':'+rule):
                return b'changed'
        self.refusal('committed AI.Tools gitlink differs: '+rule,
                     lambda i,f:i.update(aiToolsGitlink=changed_link),git_mutation=changed_gitlink)
        parties = data('inputs.json')['inventoryHistories']['parties']
        for kind,path in [('inventory',parties[0]['path']),('receipt',parties[1]['approval']['receipt']['path'])]:
            self.refusal(f'linked {kind} bytes differ: {path}',
                         git_mutation=lambda r,a,g:b'changed' if a==('show',V.INVENTORY_PUBLICATION+':'+path) else None)

    def test_each_owner_origin_requires_canonical_github_repository(self):
        def origin(url):
            return lambda repo,args,git: url.encode() if repo==ROOT.parent/'eventstore' and args==('remote','get-url','origin') else None
        self.assertEqual(self.run_binding(git_mutation=origin('git@github.com:Hexalith/Hexalith.EventStore.git'))[0],0)
        self.refusal('eventstore: owner repository mismatch',
                     git_mutation=origin('https://github.com/fork/Hexalith.EventStore.git'))

    def test_recorded_projects_rebase_is_verified_by_the_delivery_caller(self):
        self.assertEqual(self.run_binding()[0],0)
        def corrupt(i,f):
            projects = next(d for d in i['ownerIntegrations'] if d['name']=='projects')
            projects['rebasedFiles'][0]['patchSha256'] = '0'*64
        self.refusal('rebased document approval or patch binding differs: _bmad-output/planning-artifacts/epics.md',corrupt)
        def change_base(i,f):
            projects = next(d for d in i['ownerIntegrations'] if d['name']=='projects')
            projects['rebasedFiles'][0]['beforeSha256'] = '0'*64
        self.refusal('rebased document base differs: _bmad-output/planning-artifacts/epics.md',change_base)
        def extra_rebase(i,f):
            projects = next(d for d in i['ownerIntegrations'] if d['name']=='projects')
            projects['rebasedFiles'].append(dict(projects['rebasedFiles'][0],path='unapproved.md'))
        self.refusal('projects: invalid owner rebase footprint',extra_rebase)

    def test_git_authorization_date_and_ai_tools_link_count_are_independent_of_immutable_record(self):
        predates_approval = '2026-11-21'
        def authorization(repo,args,git):
            if repo == ROOT and args == ('show',V.INVENTORY_PUBLICATION+':'+str(E/'integration.json')):
                record = json.loads(git(repo,*args))
                record['deliveryAuthorization']['approvedOn'] = predates_approval
                return B.serialized(record)
        self.refusal('Git delivery authorization predates exact-byte approval',
                     lambda i,f:i['deliveryAuthorization'].update(approvedOn=predates_approval),
                     git_mutation=authorization)
        def review(repo,args,git):
            if repo == ROOT and args == ('show',V.FINAL_INTEGRATION_RECORD+':'+str(E/'integration.json')):
                record = json.loads(git(repo,*args))
                record['finalPlanReview']['verifiedInventoryAndReceiptLinks'] = 0
                return B.serialized(record)
        self.refusal('AI.Tools final review lacks complete immutable link verification',
                     lambda i,f:i['finalPlanReview'].update(verifiedInventoryAndReceiptLinks=0),git_mutation=review)

    def test_current_main_reports_migration_drift_and_enforces_visible_labels(self):
        owner = data('upstream/manifest.json')['owners'][0]
        repo = (ROOT/owner['ownerCheckout']).resolve()
        revision = next(item['commit'] for item in data('integration.json')['ownerIntegrations']
                        if item['name']=='eventstore')
        label = next(row['label']['text'].encode() for row in data('labels.json')['rows'] if row['id']=='PS01')
        def transform(change):
            def mutate(checkout,args,git):
                if checkout==repo and args[0]=='show' and args[1].startswith('origin/main:'):
                    path = args[1].removeprefix('origin/main:')
                    raw = git(checkout,'show',revision+':'+path)
                    if path == 'README.md':
                        return change(raw.replace(b' (reconciliation candidate)',b'')+b'\nOther owner information.\n')
                    return raw.replace(b' (Story 5.11 candidate)',b'')
            return mutate
        self.assertEqual(self.run_binding(git_mutation=transform(lambda raw:raw)),(0,VERIFIED,''))
        reported = 'reported: eventstore: current main migration text drift: README.md\n'
        self.assertEqual(self.run_binding(git_mutation=transform(lambda raw:raw.replace(
            b'Run `hexalith modules`',b'Run the module discovery command',1))),
            (0,VERIFIED,reported))
        for replacement in (b'- An obsolete Admin recommendation.',b'<!--\n'+label+b'\n-->'):
            with self.subTest(replacement=replacement):
                self.assertEqual(self.run_binding(git_mutation=transform(lambda raw:raw.replace(label,replacement,1))),
                                 (1,'',reported+'FAIL: PS01: current main label is missing or duplicated\n'))
        self.refusal('PS01: current main label is missing or duplicated',
                     git_mutation=transform(lambda raw:raw+b'\n'+label+b'\n'))
        self.assertEqual(self.run_binding(git_mutation=transform(lambda raw:raw+b'\n<!--\n'+label+b'\n-->\n'))[0],0)
        def change_projects(checkout,args,git):
            if checkout == ROOT.parent/'projects' and args[0]=='show' and args[1].startswith('origin/main:') and args[1].endswith('/ARCHITECTURE-SPINE.md'):
                return git(checkout,*args).replace(b'Both public heads refuse UI-only',b'Both public heads execute UI-only')
        self.assertEqual(self.run_binding(git_mutation=change_projects),
                         (0,VERIFIED,'reported: projects: current main migration text drift: _bmad-output/planning-artifacts/architecture/architecture-projects-2026-07-15/ARCHITECTURE-SPINE.md\n'))

    def test_missing_current_planning_document_reports_drift_without_waiving_delivery(self):
        path = '_bmad-output/planning-artifacts/prd.md'
        eventstore = ROOT.parent/'eventstore'
        def deleted(checkout,args,git):
            if checkout == eventstore and args == ('show','origin/main:'+path):
                raise ValueError('missing current path')
            if checkout == eventstore and args == ('ls-tree','--name-only','origin/main','--',path):
                return b''
        self.assertEqual(self.run_binding(git_mutation=deleted,default=True,full=True),
                         (0,VERIFIED,'reported: eventstore: current main migration text drift: '+path+'\n'))

    def test_final_plan_requires_authority_and_capability_outcomes(self):
        cases = [
            ('status: approved','status: draft','final plan lacks approved authority for the canonical inventory repository'),
            ('G01–G06','REMOVED','final approved plan lost independent gate/exemption: G01–G06'),
            ('Version **1.3.0**','Version **1.3.0 candidate**','completion requires final plan 1.3.0 bytes'),
            ('scope-approved-only; session-scope-only:', 'owner-approved; owning-maintainer-receipt:', 'parties 1.0.0: final inventory row authority/path/hash mismatch'),
            ('All PS01–PS14 remain present; no evidenced retirement is claimed.','All compatibility surfaces are retired.',
             'final approved plan lost independent gate/exemption: All PS01–PS14 remain present; no evidenced retirement is claimed.'),
            ('Unsupported transports\nfail safely; confidential human actions hand off to their owning UI.',
             'A proprietary adapter executes and approves these actions over MCP.',
             'final approved plan lost independent gate/exemption: Unsupported transports\nfail safely; confidential human actions hand off to their owning UI.'),
        ]
        for before,after,message in cases:
            with self.subTest(before=before):
                self.refusal(message,plan_mutation=lambda plan:plan.replace(before,after))

    def test_immutable_links_are_verified_inside_each_row(self):
        for family in ('eventstore-admin','technical-tools'):
            row = data('inputs.json')['inventoryHistories'][family][-1]
            for path in (row['path'],row['approval']['receipt']['path']):
                url = V.ROOT_REPOSITORY+'/blob/'+V.INVENTORY_PUBLICATION+'/'+path
                version = row['version']
                def change(plan):
                    return ''.join(line.replace(url,url.replace(V.INVENTORY_PUBLICATION,'main'))
                                   if line.startswith(f'| {family} | {version} |') else line
                                   for line in plan.splitlines(keepends=True))
                self.refusal(f'{family} {version}: final inventory row lacks immutable link: {path}',plan_mutation=change)

    def test_published_inventory_receipt_must_approve_the_exact_indexed_digest(self):
        family = 'eventstore-admin'
        row = data('inputs.json')['inventoryHistories'][family][-2]
        receipt = row['approval']['receipt']
        revision = V.INVENTORY_PUBLICATION
        plan_commit = data('integration.json')['aiToolsCommit']
        plan = recorded_git(ROOT.parent/'aitools','show',plan_commit+':'+V.PLAN_PATH).decode()
        indexed = {'inventoryHistories':{family:[row]}}

        def verify(*args):
            V.check_published_index(ROOT,plan,indexed,revision)
            return 'approved',True

        for decision,digest in [('approved',row['sha256']),('pending',row['sha256']),('approved','0'*64)]:
            with self.subTest(decision=decision,digest=digest):
                raw = B.serialized({'decision':decision,'inventorySha256':digest})
                receipt['sha256'] = B.sha(raw)
                def git(repo,*args):
                    return raw if args == ('show',revision+':'+receipt['path']) else recorded_git(repo,*args)
                with mock.patch.object(B,'git',side_effect=git), mock.patch.object(V,'verify',side_effect=verify):
                    expected = (0,VERIFIED,'') if decision=='approved' and digest==row['sha256'] else (
                        1,'','FAIL: published receipt lacks approval for '+row['path']+'\n')
                    self.assertEqual(streams(lambda:V.main([])),expected)

    def test_final_approval_digest_checks_actual_file_bytes(self):
        def append_space(integration,files,binding):
            path = ROOT/integration['finalPlanApproval']['path']
            files[path] = path.read_bytes()+b'\n'
        self.refusal('artifact hash mismatch: '+str(E/'final-plan-approval.json'),file_mutation=append_space)

    def test_overdue_assessment_requires_a_recorded_owner_reason(self):
        from datetime import date
        class Later(date):
            @classmethod
            def today(cls):
                return cls(2028,1,1)
        def overdue(i,f):
            i['completedOn'] = '2027-02-06'
            i['sm3Assessment']['assessedOn'] = '2027-02-06'
        with mock.patch.object(V,'date',Later):
            self.assertEqual(self.run_binding()[0],0)
            self.refusal('overdue SM-3 requires explicit owner slip reason',overdue)
            def slip(i,f):
                overdue(i,f)
                i['sm3Assessment'].update(outcome='slip',ownerReason='Successor is scheduled and gates remain open.')
            self.assertEqual(self.run_binding(slip)[0],0)

    def test_sm3_requires_the_parties_gates_verdict_and_proof_of_owner_removal(self):
        label = next(row for row in data('labels.json')['rows'] if row['id']=='PS05')
        surface = label['surface']
        def claim(surface,gates=None,with_verdict=False,tamper_result=False,words='approve'):
            def mutate(integration,files,binding):
                receipt = {
                    'state':'retired','owner':'Fixture owner','source':'Fixture','surface':surface,'retiredOn':'2026-11-22',
                    'ownerRole':'Parties owning maintainer','exactApprovalInstruction':words,
                    'removalRevision':next(d['commit'] for d in integration['ownerIntegrations'] if d['name']=='parties'),
                }
                if gates is not None:
                    receipt['gateEvidence'] = gates
                if with_verdict:
                    verdict = json.loads((ROOT/E.parent/'story-5-4-owner-approval/owner-approval.json').read_text())
                    verdict['decision'].update(verdict='retirement-ready',retainedBlockingGapIds=[])
                    for gap in verdict['gapDispositions']:
                        gap['workStatus'] = 'resolved'
                    if with_verdict == 'empty':
                        verdict['approvedSnapshot'].update(
                            {key:binding(f'fixture-{key}.json',b'{}') for key in ('scanReceipt','manifest')})
                    else:
                        candidate = integration['rootIntegrationRevision']
                        manifest = binding('fixture-manifest.json',B.serialized({
                            'schema':'mcpcli-story-5-4-evidence/v1','candidate':{'headCommit':candidate},
                            'ownerCheckpoint':{'proposal':'retirement-ready'},
                            'acceptanceEvidence':{'fullLiveAccepted':True,'fullV1Accepted':True},
                        }))
                        index_hash = B.sha(json.dumps([manifest],sort_keys=True,separators=(',',':')).encode())
                        scan = binding('fixture-scanReceipt.json',B.serialized({
                            'schema':'mcpcli-evidence-secret-scan/v1','result':'clean','exitCode':0,
                            'fileCount':1,'manifestSha256':index_hash,'files':[manifest],
                        }))
                        scan.update(inputFileCount=1,manifestSha256=index_hash)
                        verdict.update(recordedAtUtc='2026-11-22T23:59:01Z',approvalScope='Approve the exact successor as retirement-ready.')
                        verdict['approvedSnapshot'].update(commit=candidate,candidateHeadCommit=candidate,manifest=manifest,scanReceipt=scan)
                    receipt['story54Verdict'] = binding('fixture-parties-verdict.json',B.serialized(verdict))
                    receipt['gateEvidence'] = {}
                    for index,gate in enumerate(gates):
                        raw = binding(f'fixture-gate-result-{index}.txt',f'{gate}: PASS\n'.encode())
                        if tamper_result and index == 0:
                            files[ROOT/raw['path']] += b'changed'
                        proof = {'surface':surface,'gate':gate,'result':'passed','owner':'Fixture gate owner',
                                 'source':'Fixture gate evidence','verifiedOn':'2026-11-22','resultEvidence':raw,
                                 'removalRevision':receipt['removalRevision']}
                        receipt['gateEvidence'][gate] = binding(f'fixture-gate-proof-{index}.json',B.serialized(proof))
                retirement = binding('fixture-retirement.json',B.serialized(receipt))
                integration['sm3Assessment'].update(outcome='met',retirements=[retirement])
            return mutate
        for exempt in ('Hexalith.FrontComposer.Cli','tools/MigrateEmbeddingVectors','Hexalith.ChatBot.Cli'):
            self.refusal('SM-3 requires an inventoried Legacy Server',file_mutation=claim(exempt))
        gates = dict.fromkeys([label['gate'],*(f'G{number:02}' for number in range(1,7))],{})
        self.refusal('SM-3 retirement does not bind every independent removal gate for '+surface,
                     file_mutation=claim(surface,gates))
        gates['restricted/destructive exposure conflict'] = {}
        project = 'src/Hexalith.Parties.Mcp/Hexalith.Parties.Mcp.csproj'
        self.refusal('SM-3 retirement lacks explicit owning-maintainer approval',
                     file_mutation=claim(surface,gates,words='I do not approve retiring Parties.'))
        self.refusal('SM-3 retirement lacks owner removal of '+project,
                     file_mutation=claim(surface,gates))
        def removed(repo,args,git):
            if repo == ROOT.parent/'parties':
                if args[:2] == ('ls-tree','--name-only') and args[-1] == project:
                    return (project+'\n').encode() if args[2].endswith('^') else b''
                if args[:3] == ('ls-tree','-r','--name-only'):
                    return b'README.md\n'
                if args[:3] == ('diff','--name-status','--find-renames'):
                    return b'D\0'+project.encode()+b'\0'
        def renamed(repo,args,git):
            if repo == ROOT.parent/'parties' and args[:3] == ('diff','--name-status','--find-renames'):
                return b'R100\0'+project.encode()+b'\0moved.csproj\0'
            return removed(repo,args,git)
        self.refusal('SM-3 owner revision renames or retains the retired project: '+project,
                     git_mutation=renamed,file_mutation=claim(surface,gates))
        self.refusal('SM-3 Parties retirement lacks the successor Story 5.4 owner verdict',
                     git_mutation=removed,file_mutation=claim(surface,gates))
        self.refusal('SM-3 Parties verdict must approve a new evidence snapshot',
                     git_mutation=removed,file_mutation=claim(surface,gates,with_verdict='empty'))
        def complete_fixture(tamper=False, verdict_changes=None, gate_changes=None, scan_changes=False, outcome='met'):
            evidence = {}
            def write_fixture(integration,files,binding):
                claim(surface,gates,with_verdict=True,tamper_result=tamper)(integration,files,binding)
                assessment = integration['sm3Assessment']
                assessment['outcome'] = outcome
                retirement = json.loads(files[ROOT/'fixture-retirement.json'])
                verdict = json.loads(files[ROOT/'fixture-parties-verdict.json'])
                if verdict_changes:
                    verdict_changes(verdict)
                if gate_changes:
                    first_gate = next(iter(retirement['gateEvidence']))
                    proof = json.loads(files[ROOT/'fixture-gate-proof-0.json'])
                    proof.update(gate_changes)
                    retirement['gateEvidence'][first_gate] = binding('fixture-gate-proof-0.json',B.serialized(proof))
                if scan_changes:
                    scan = json.loads(files[ROOT/'fixture-scanReceipt.json'])
                    scan['files'][0]['path'] = 'unrelated-manifest.json'
                    scan['manifestSha256'] = B.sha(json.dumps(scan['files'],sort_keys=True,separators=(',',':')).encode())
                    scan_ref = binding('fixture-scanReceipt.json',B.serialized(scan))
                    scan_ref.update(inputFileCount=1,manifestSha256=scan['manifestSha256'])
                    verdict['approvedSnapshot']['scanReceipt'] = scan_ref
                retirement['story54Verdict'] = binding('fixture-parties-verdict.json',B.serialized(verdict))
                assessment['retirements'] = [binding('fixture-retirement.json',B.serialized(retirement))]
                evidence.update({str(path.relative_to(ROOT)):raw for path,raw in files.items()
                                 if path.name in {'fixture-scanReceipt.json','fixture-manifest.json'}})
            def git_fixture(repo,args,git):
                if repo == ROOT and args[0]=='show' and ':' in args[1]:
                    path = args[1].split(':',1)[1]
                    if path in evidence:
                        return evidence[path]
                return removed(repo,args,git)
            return {'git_mutation':git_fixture,'file_mutation':write_fixture}
        self.refusal('artifact hash mismatch: fixture-gate-result-0.txt',
                     **complete_fixture(tamper=True))
        self.assertEqual(self.run_binding(**complete_fixture())[0],0)
        for field,value in [('approval','denied'),('verdict','retirement-blocked')]:
            with self.subTest(verdict=field):
                self.refusal('SM-3 Parties retirement requires the successor retirement-ready owner verdict',
                             **complete_fixture(verdict_changes=lambda verdict:verdict['decision'].update({field:value})))
        for change in (lambda verdict:verdict['gapDispositions'][0].update(workStatus='open'),
                       lambda verdict:verdict['gapDispositions'][0].update(owner='Unrelated maintainer'),
                       lambda verdict:verdict['gapDispositions'].pop()):
            self.refusal('SM-3 Parties verdict lacks resolved G01–G06 with their recorded owners',
                         **complete_fixture(verdict_changes=change))
        self.refusal('SM-3 Parties clean scan does not bind the approved successor manifest',
                     **complete_fixture(scan_changes=True))
        for field,value in [('surface','An unrelated server'),('gate','An unrelated gate'),
                            ('result','failed'),('removalRevision','0'*40)]:
            with self.subTest(gate_proof=field):
                self.refusal('SM-3 removal evidence does not prove '+next(iter(gates))+' for '+surface,
                             **complete_fixture(gate_changes={field:value}))
        for outcome in ('pending-not-met','slip'):
            self.refusal('SM-3 pending/slip must not claim retirement',**complete_fixture(outcome=outcome))
        self.refusal('pre-deadline unmet SM-3 remains pending',
                     lambda i,f:i['sm3Assessment'].update(outcome='slip',ownerReason='Premature slip.'))

    def test_sm3_admin_gates_are_independent_and_pair_is_required_from_both_owners(self):
        labels = {row['id']:row for row in data('labels.json')['rows']}
        census = B.rows((ROOT/B.A/'technical-tools-migration-inventory-v1.0.4.md').read_text())
        def only(key):
            def mutate(integration,files,binding):
                row=labels[key]
                retirement = {
                    'state':'retired','owner':'Fixture owner','source':'Fixture','surface':row['surface'],
                    'ownerRole':census[key]['Owning maintainer role'],'exactApprovalInstruction':'approve',
                    'gateEvidence':{row['gate']:{}},'retiredOn':'2026-11-22',
                }
                ref = binding('fixture-retirement.json',B.serialized(retirement))
                integration['sm3Assessment'].update(outcome='met',retirements=[ref])
            return mutate
        self.refusal('SM-3 retirement does not bind every independent removal gate for '+labels['PS02']['surface'],
                     file_mutation=only('PS02'))
        for key in ('PS04','PS09'):
            self.refusal('SM-3 FrontComposer and Projects must retire together',file_mutation=only(key))


class RecordedAuthorityAndLifecycleTests(unittest.TestCase):
    def test_parties_original_scope_and_later_owner_authority_are_distinct(self):
        chain=data('inputs.json')['inventoryHistories']['parties']
        self.assertEqual(chain[0]['approval']['authority'],'session-scope-only')
        self.assertTrue(all(item['approval']['authority']=='owning-maintainer-receipt' for item in chain[1:]))

    def test_independent_deferrals_use_their_own_recorded_obligations(self):
        entries=data('deferral-dispositions.json')['entries']
        runtime=next(e for e in entries if e['summary'].startswith('Align CI SDK installation'))
        citation=next(e for e in entries if e['summary'].startswith('Re-cite Folders 1.1.0'))
        self.assertIn('11.0.0',runtime['gate']);self.assertIn('CI and live-topology',runtime['owner']);self.assertNotIn('K12',runtime['gate'])
        self.assertIn('Story 5.11',citation['gate']);self.assertIn('technical',citation['owner']);self.assertNotIn('K12',citation['gate'])

    def test_real_prior_lifecycle_checks_historical_delivery_with_superseding_current_labels(self):
        previous=ROOT/E.parent/'story-5-10/verify_labels.py'
        spec=importlib.util.spec_from_file_location('historical510fixture',previous)
        prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
        register=json.loads((ROOT/E.parent/'story-5-10/labels.json').read_text())
        register.update(state='integrated',inventoryRevision='f'*40,deliveryAuthorization={'exactWords':'authorize','source':'Synthetic historical delivery','approvedOn':'2026-11-16'})
        befores,afters,commits={},{},{}
        for index,owner in enumerate(register['repositories'],1):
            commit=str(index)*40;raw=('fixture historical commit '+str(index)).encode()
            owner['integration']={'commit':commit,'commitSha256':B.sha(raw)}
            before=prior.B.blob(ROOT,owner['name'],'README.md')
            after=before.replace((ROOT/owner['before']['path']).read_bytes(),(ROOT/owner['after']['path']).read_bytes())
            befores[(str(ROOT.parent/owner['name']),commit)]=before
            afters[(str(ROOT.parent/owner['name']),commit)]=after;commits[commit]=raw
        original=prior.B.git
        project='src/Hexalith.McpCli/Hexalith.McpCli.csproj'
        policy='tools/dependency-policy.json'
        historical={path:original(ROOT,'show',B.BASELINE+':'+path) for path in (project,policy)}
        current={
            ROOT/project:b'<Project><ItemGroup><PackageReference Include="Hexalith.ChatBot.Contracts" HexalithContracts="true"/></ItemGroup></Project>',
            ROOT/policy:b'{"modules":{"Hexalith.Memories.Contracts":"2.0.0"}}',
        }
        historical_reads=set()
        read_bytes=Path.read_bytes
        def working_bytes(path):
            return current[path] if path in current else read_bytes(path)
        def historical_objects(repo,*args):
            if args[0]=='show':
                revision,path=args[1].split(':',1)
                if revision.endswith('^') and revision[:-1] in commits and path=='README.md':return befores[(str(Path(repo)),revision[:-1])]
                if revision in commits and path=='README.md':return afters[(str(Path(repo)),revision)]
                if revision=='f'*40 and path in historical:
                    historical_reads.add(path)
                    return historical[path]
                if revision=='f'*40:return original(ROOT,'show',B.BASELINE+':'+path)
                if revision=='origin/main' and ROOT/path in current:return current[ROOT/path]
                if revision=='origin/main' and path=='README.md':return b'current approved technical-tools 1.0.4 supersession'
            if args[0]=='cat-file' and args[-1] in commits:return commits[args[-1]]
            if args[0]=='diff' and args[3] in commits:return b'README.md\n'
            if args[0]=='merge-base' and args[2] in {*commits,'f'*40}:return b''
            return original(repo,*args)
        root_git=B.git
        def ssh_origin(repo,*args):
            if args==('remote','get-url','origin'):return f'git@github.com:Hexalith/Hexalith.{Path(repo).name}.git'.encode()
            return root_git(repo,*args)
        with mock.patch.object(B,'git',side_effect=ssh_origin),mock.patch.object(prior.B,'git',side_effect=historical_objects),mock.patch.object(Path,'read_bytes',working_bytes):
            V.check_prior_delivery(ROOT,prior_module=prior,register=register)
        self.assertEqual(set(historical),historical_reads)
        self.assertTrue(all('technical-tools inventory 1.0.4' in row['label']['text'] for row in data('labels.json')['rows']))


if __name__ == '__main__':
    unittest.main()
