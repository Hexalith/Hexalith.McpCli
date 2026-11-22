"""Policy-boundary tests, including exact command streams and removed-guard controls."""
import ast
import contextlib
import copy
import difflib
import tempfile
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
module_spec = importlib.util.spec_from_file_location('reconciliation511tests',HERE/'verify_reconciliation.py')
V = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(V)
B,ROOT,E = V.B,V.ROOT,V.E
PASS = 'PASS: eight inventory histories; preserved AD-23/predecessors; fourteen labels; nine owner patch sets; scoped deferral accounting\n'


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
    receipt = data('approval.json')
    receipt.update(decision='approved',approver='Fixture owner',exactApprovalInstruction='approve',approvalSource='Synthetic test only',approvedOn='2026-11-16',rolesCovered=receipt['requiredApprovalRoles'])
    return receipt


def streams(action):
    stdout,stderr = io.StringIO(),io.StringIO()
    with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
        code = action()
    return code,stdout.getvalue(),stderr.getvalue()


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
        receipt=pending();receipt['approver']='Invented approval'
        self.refusal({str(E/'approval.json'):receipt},'pending receipt must not claim fresh approval')
        receipt=data('approval.json');receipt['amendments'][0]['rows'].pop()
        self.refusal({str(E/'approval.json'):receipt},'amendment predecessor/row/approval bindings mismatch')

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
        with mock.patch.object(B,'correct',side_effect=lambda name,text:text):
            incomplete = B.corrected_document(owner['name'],file['path'],before,labels['rows'])
        target=file['path']
        patch = ''.join(difflib.unified_diff(before.decode().splitlines(True),incomplete.decode().splitlines(True),
                                             fromfile='a/'+target,tofile='b/'+target)).encode()
        file.update(afterSha256=B.sha(incomplete))
        file['patch']['sha256'] = B.sha(patch)
        check = V.checked
        with mock.patch.object(V,'checked',side_effect=lambda root,item: patch if item==file['patch'] else check(root,item)):
            self.refusal({str(E/'upstream/manifest.json'):manifest},owner['name']+': applied document differs from required corrections: '+target)

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
        expected = B.scoped_deferrals((ROOT/B.A/'deferred-work.md').read_text())
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
        for path,old,new in [(ROOT/B.SPEC,"status: 'in-review'","status: 'done'"),(ROOT/B.A/'sprint-status.yaml','5-11-reconcile-product-claims-and-the-migration-plan: review','5-11-reconcile-product-claims-and-the-migration-plan: done')]:
            def read_text(p,*args,**kwargs):
                text=original(p,*args,**kwargs)
                return text.replace(old,new) if p==path else text
            with self.subTest(path=path),mock.patch.object(Path,'read_text',read_text):
                self.refusal({str(E/'approval.json'):pending()},'completion requires fresh exact-byte successor approval')

    def test_guard_removals_are_detected_for_hash_roles_history_labels_and_gates(self):
        cases=[]
        receipt=approved();receipt['rolesCovered']=[]
        cases.append(('approval lacks explicitly covered roles',lambda ns:ns['check_approval'](receipt,receipt['artifacts'],receipt['requiredApprovalRoles'])))
        bad=approved();bad['artifacts']={}
        cases.append(('approval artifact accounting/hash mismatch',lambda ns:ns['check_approval'](bad,receipt['artifacts'],receipt['requiredApprovalRoles'])))
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
    """Synthetic authorized delivery exercises every integration boundary without remote effects."""
    def fixture(self,plan_transform=None):
        revision,ai,gitlink,owner_commit = ['a'*40,'b'*40,'c'*40,'d'*40]
        plan = (ROOT/E/'upstream/ai-tools/hexalith-mcpcli-migration-instructions.md').read_text()
        plan = plan.replace('inventory_revision: null',f"inventory_revision: '{revision}'").replace('status: candidate-not-publishable','status: approved')
        start,end = plan.index('Version **1.3.0'),plan.index('## Ownership')
        plan = plan[:start]+'Version **1.3.0** indexes the published inventories.\n\n'+plan[end:]
        plan = plan.replace('candidate-pending; pending:', 'owner-approved; owning-maintainer-receipt:')
        plan = plan[:plan.index('## Integration and release prerequisite')]
        for chain in data('inputs.json')['inventoryHistories'].values():
            for item in chain:
                for path in [item['path'],item['approval']['receipt']['path']]:
                    plan += f'[{path}](https://github.com/Hexalith/Hexalith.McpCli/blob/{revision}/{path})\n'
        if plan_transform:plan=plan_transform(plan)
        plan=plan.encode()
        receipt=approved()
        receipt['artifacts']['artifact.md']=B.sha(b'published bytes')
        owner={'name':'eventstore','ownerCheckout':str(ROOT.parent/'eventstore'),'files':[{'path':'README.md','afterSha256':B.sha(b'documented bytes')}]}
        manifest={'owners':[owner,{'name':'ai-tools','ownerCheckout':str(ROOT.parent/'aitools'),'files':[{'path':'hexalith-mcpcli-migration-instructions.md','afterSha256':B.sha(plan)}]}]}
        integration={'state':'integrated','inventoryRevision':revision,'aiToolsCommit':ai,'aiToolsGitlink':gitlink,'planSha256':B.sha(plan),'deliveryAuthorization':{'exactWords':'authorize','source':'Synthetic fixture only','approvedOn':'2026-11-16'},'ownerIntegrations':[{'name':'eventstore','commit':owner_commit,'checks':{'commitlint':'passed','builds':'passed'}},{'name':'ai-tools','commit':ai,'checks':{'commitlint':'passed','builds':'passed'}}],'instructionSync':'passed','completedOn':'2026-11-16','rootIntegrationRevision':'e'*40,'sm3Assessment':{'assessedOn':'2026-11-16','deadline':'2027-02-05','outcome':'pending-not-met','retirements':[],'owner':'Fixture owner','source':'Explicit fixture decision'},'deferralOwnerDecision':{'decision':'accept-audit-preserve-open-gates','owner':'Fixture owner','source':'Explicit fixture decision','decidedOn':'2026-11-16','auditSha256':B.sha((ROOT/E/'deferral-dispositions.json').read_bytes()),'auditMarkdownSha256':B.sha((ROOT/E/'deferral-dispositions.md').read_bytes()),'preserveUnresolvedGates':True,'retainedUnresolvedEntryIds':[entry['id'] for entry in data('deferral-dispositions.json')['entries'] if not entry['disposition'].startswith('existing resolution')]},'finalPlanApproval':{'path':'fixture-plan-approval.json','sha256':'fixture'}}
        integration['deferralOwnerDecision']['acceptCompletionWithDeferredReleaseNotes'] = True
        final={'decision':'approved','planSha256':B.sha(plan),'inventoryRevision':revision,'rolesCovered':receipt['requiredApprovalRoles'],'approver':'Fixture owner','exactApprovalInstruction':'approve','approvalSource':'Synthetic fixture only','approvedOn':'2026-11-16'}
        def git(repo,*args):
            if args[0]=='merge-base': return b''
            if args[0]=='ls-tree': return f'160000 commit {gitlink}\treferences/Hexalith.AI.Tools\n'.encode()
            path=args[1].split(':',1)[1]
            if path=='artifact.md':return b'published bytes'
            if path==str(E/'approval.json'):return B.serialized(receipt)
            if path=='README.md':return b'documented bytes'
            if path=='hexalith-mcpcli-migration-instructions.md':return plan
            if path=='hexalith-llm-instructions.md':return b'approved rule'
            if (ROOT/path).is_file():return (ROOT/path).read_bytes()
            raise AssertionError(args)
        return receipt,manifest,integration,final,git

    def run_binding(self,mutate=None,git_override=None,plan_transform=None):
        receipt,manifest,integration,final,git=self.fixture(plan_transform)
        if mutate: mutate(receipt,manifest,integration,final)
        def verified(*args):
            V.check_completion(ROOT,receipt,{},manifest,integration)
            return 'approved',True
        read_bytes = Path.read_bytes
        def working_bytes(path):
            return B.serialized(receipt) if path==ROOT/E/'approval.json' else read_bytes(path)
        with mock.patch.object(Path,'read_bytes',working_bytes),mock.patch.object(V,'check_prior_delivery'),mock.patch.object(B,'git',side_effect=git_override or git),mock.patch.object(V,'checked',return_value=B.serialized(final)),mock.patch.object(V,'verify',side_effect=verified):
            return streams(lambda:V.main(['--approved-completion']))

    def test_complete_synthetic_binding_succeeds_with_exact_streams(self):
        self.assertEqual(self.run_binding(),(0,PASS+'PASS: decision: approved; approved integration verified\n',''))

    def test_missing_authorization_revision_owner_hash_gate_role_and_sync_refuse(self):
        cases=[
            (lambda r,m,i,f:i.update(state='blocked'),'completion requires integrated plan and all fourteen labels'),
            (lambda r,m,i,f:i.update(deliveryAuthorization=None),'completion requires separate explicit Git delivery authorization'),
            (lambda r,m,i,f:i.update(inventoryRevision=None),'completion requires full published inventory revision'),
            (lambda r,m,i,f:i.update(ownerIntegrations=[]),'completion requires every owner integration binding'),
            (lambda r,m,i,f:i['ownerIntegrations'][0].update(commit=None),'eventstore: upstream integration missing'),
            (lambda r,m,i,f:i['ownerIntegrations'][0]['checks'].update(builds='blocked'),'eventstore: mandatory commitlint/Builds checks missing'),
            (lambda r,m,i,f:i.update(aiToolsCommit=None),'completion requires full AI.Tools integration revision'),
            (lambda r,m,i,f:i.update(aiToolsGitlink=None),'containing AI.Tools gitlink missing'),
            (lambda r,m,i,f:i.update(planSha256=None),'ai-tools: integrated documentation bytes mismatch'),
            (lambda r,m,i,f:f.update(decision='pending'),'final plan exact-byte approval/hash/revision binding missing'),
            (lambda r,m,i,f:f.update(rolesCovered=[]),'final plan approval lacks covered roles'),
            (lambda r,m,i,f:i.update(instructionSync=None),'passing instruction synchronization binding missing'),
            (lambda r,m,i,f:i['sm3Assessment'].update(assessedOn='2026-01-01'),'SM-3 assessment must bind recorded completion date'),
            (lambda r,m,i,f:i.update(deferralOwnerDecision=None),'completion requires explicit structured deferral owner decision'),
        ]
        for mutate,message in cases:
            with self.subTest(binding=message):self.assertEqual(self.run_binding(mutate),(1,'','FAIL: '+message+'\n'))

    def test_published_and_upstream_bytes_and_main_containment_are_checked(self):
        _,_,_,_,git=self.fixture()
        def bad_publication(repo,*args):
            return b'wrong bytes' if args[0]=='show' and args[1].endswith(':artifact.md') else git(repo,*args)
        self.assertEqual(self.run_binding(git_override=bad_publication),(1,'','FAIL: published approved artifact bytes mismatch: artifact.md\n'))
        def bad_owner(repo,*args):
            return b'wrong bytes' if args[0]=='show' and args[1].endswith(':README.md') else git(repo,*args)
        self.assertEqual(self.run_binding(git_override=bad_owner),(1,'','FAIL: eventstore: integrated documentation bytes mismatch\n'))
        def off_main(repo,*args):
            if Path(repo)==ROOT.parent/'eventstore' and args[0]=='merge-base':raise ValueError('upstream main excludes integrated commit')
            return git(repo,*args)
        self.assertEqual(self.run_binding(git_override=off_main),(1,'','FAIL: upstream main excludes integrated commit\n'))

    def test_new_checkout_cannot_hide_older_committed_gitlink(self):
        _,_,_,_,git=self.fixture()
        old='0'*40
        def older_gitlink(repo,*args):
            if args[0]=='ls-tree':return f'160000 commit {old}\treferences/Hexalith.AI.Tools\n'.encode()
            if Path(repo)==ROOT.parent/'aitools' and args==('merge-base','--is-ancestor','b'*40,old):
                raise ValueError('committed gitlink excludes actual AI.Tools owner integration')
            return git(repo,*args)
        self.assertEqual(self.run_binding(lambda r,m,i,f:i.update(aiToolsGitlink=old),git_override=older_gitlink),(1,'','FAIL: committed gitlink excludes actual AI.Tools owner integration\n'))

    def test_final_plan_requires_gates_change_control_and_every_exact_immutable_link(self):
        self.assertEqual(self.run_binding(plan_transform=lambda p:p.replace('G01–G06','REMOVED')),(1,'','FAIL: final approved plan lost independent gate/exemption: G01–G06\n'))
        self.assertEqual(self.run_binding(plan_transform=lambda p:p.replace('Publish every change to this plan under a new `plan_version`','REMOVED')),(1,'','FAIL: final approved plan lost independent gate/exemption: Publish every change to this plan under a new `plan_version`\n'))
        inventory=data('inputs.json')['inventoryHistories']['parties'][0]['path']
        receipt=str(E/'approval.json')
        for path in [inventory,receipt]:
            target='https://github.com/Hexalith/Hexalith.McpCli/blob/'+'a'*40+'/'+path
            for replacement in ['https://github.invalid/Hexalith/Hexalith.McpCli/blob/'+'a'*40+'/'+path,'https://github.com/Hexalith/Hexalith.McpCli/blob/main/'+path,'unlinked-'+path]:
                with self.subTest(path=path,replacement=replacement):
                    self.assertEqual(self.run_binding(plan_transform=lambda p:p.replace(target,replacement)),(1,'','FAIL: final plan lacks immutable inventory/approval link: '+path+'\n'))

    def test_open_ac3_requires_an_explicit_changed_owner_decision(self):
        self.assertEqual(self.run_binding(lambda r,m,i,f:i['deferralOwnerDecision'].pop('acceptCompletionWithDeferredReleaseNotes')),
                         (1,'','FAIL: AC3 generated release notes remain deferred by the owner\n'))
        self.assertEqual(self.run_binding()[0],0)

    def test_resolved_ac3_audit_allows_completion_without_new_release_receipt(self):
        _,_,integration,_,_=self.fixture()
        decision=integration['deferralOwnerDecision']
        del decision['acceptCompletionWithDeferredReleaseNotes']
        audit=data('deferral-dispositions.json')
        notes=next(e for e in audit['entries'] if e['id']=='77748cf5a6cb9421')
        notes.update(sourceStatus='resolved by the owning release team',disposition='existing resolution recorded')
        updated=B.serialized(audit)
        decision['auditSha256']=B.sha(updated)
        decision['retainedUnresolvedEntryIds'].remove(notes['id'])
        read_bytes=Path.read_bytes
        with mock.patch.object(Path,'read_bytes',lambda p: updated if p==ROOT/E/'deferral-dispositions.json' else read_bytes(p)):
            V.check_assessments(ROOT,integration)

    def test_only_inventory_legacy_servers_can_meet_sm3(self):
        binding={'path':'synthetic-retirement.json','sha256':'fixture'}
        _,_,i,_,_=self.fixture()
        i['sm3Assessment'].update(outcome='met',retirements=[binding])
        for surface in ['Hexalith.FrontComposer.Cli','tools/MigrateEmbeddingVectors','Hexalith.ChatBot.Cli','unknown','Hexalith.Parties.Mcp','Hexalith.EventStore.Admin.Mcp','Hexalith.Projects.Mcp']:
            receipt={'state':'retired','owner':'Fixture owner','source':'Fixture','surface':surface,'retiredOn':'2026-11-16'}
            with self.subTest(surface=surface),mock.patch.object(V,'checked',return_value=B.serialized(receipt)):
                if surface.endswith('.Mcp'): V.check_assessments(ROOT,i)
                else:
                    with self.assertRaisesRegex(ValueError,'inventoried Legacy Server'):V.check_assessments(ROOT,i)

    def test_final_wording_authority_and_every_published_blob(self):
        for before,after,message in [
            ('Version **1.3.0**','Version **1.3.0 candidate**','completion requires final plan 1.3.0 bytes'),
            ('scope-approved-only; session-scope-only:', 'owner-approved; owning-maintainer-receipt:', 'parties 1.0.0: final inventory row authority/path/hash mismatch'),
            ('owner-approved; owning-maintainer-receipt: `'+str(E/'approval.json'), 'candidate-pending; pending: `'+str(E/'approval.json'), 'eventstore-admin 1.0.3: final inventory row authority/path/hash mismatch')]:
            with self.subTest(message=message):
                self.assertEqual(self.run_binding(plan_transform=lambda p:p.replace(before,after)),(1,'','FAIL: '+message+'\n'))
        history=data('inputs.json')['inventoryHistories']['parties']
        _,_,_,_,git=self.fixture()
        for path,kind in [(history[0]['path'],'inventory'),(history[1]['approval']['receipt']['path'],'receipt')]:
            def changed(repo,*args):
                return b'changed' if args==('show','a'*40+':'+path) else git(repo,*args)
            self.assertEqual(self.run_binding(git_override=changed),(1,'',f'FAIL: linked {kind} bytes differ: {path}\n'))

    def test_descendant_cannot_revert_rule_or_plan_or_mismatch_commit_instructions(self):
        _,_,_,_,git=self.fixture()
        for path in ['hexalith-mcpcli-migration-instructions.md','hexalith-llm-instructions.md','CLAUDE.md']:
            def changed(repo,*args):
                revision='e'*40 if path=='CLAUDE.md' else 'c'*40
                return b'changed' if args==('show',revision+':'+path) else git(repo,*args)
            message='committed root agent instructions differ' if path=='CLAUDE.md' else 'committed AI.Tools gitlink differs: '+path
            self.assertEqual(self.run_binding(git_override=changed),(1,'','FAIL: '+message+'\n'))

    def test_push_all_changes_requires_scoped_final_delivery(self):
        def scoped(r,m,i,f):
            i['deliveryAuthorization'].update(exactWords='push all changes',footprint='All final Story 5.11 owner patches and published packet')
        self.assertEqual(self.run_binding(scoped)[0],0)
        def all_main(r,m,i,f):
            scoped(r,m,i,f)
            i['deliveryAuthorization']['exactWords'] = 'push all changes of all repositories to main.\\'
        self.assertEqual(self.run_binding(all_main)[0],0)
        self.assertEqual(self.run_binding(lambda r,m,i,f:i['deliveryAuthorization'].update(exactWords='push all changes')),
                         (1,'','FAIL: completion requires separate explicit Git delivery authorization\n'))

    def test_structured_deferral_decision_binds_audit_and_retains_all_unresolved_gates(self):
        cases=[
            (lambda i:i.update(deferralOwnerDecision='undecided'),'completion requires explicit structured deferral owner decision'),
            (lambda i:i['deferralOwnerDecision'].update(decision='undecided'),'completion requires explicit structured deferral owner decision'),
            (lambda i:i['deferralOwnerDecision'].update(auditSha256='0'*64),'deferral decision must bind exact audit bytes'),
            (lambda i:i['deferralOwnerDecision'].update(retainedUnresolvedEntryIds=[]),'deferral decision must preserve every unresolved owner/gate'),
            (lambda i:i['deferralOwnerDecision'].update(preserveUnresolvedGates=False),'deferral decision must preserve every unresolved owner/gate'),
        ]
        for mutate,message in cases:
            with self.subTest(message=message):self.assertEqual(self.run_binding(lambda r,m,i,f:mutate(i)),(1,'','FAIL: '+message+'\n'))

    def test_recorded_sm3_assessment_survives_later_verification_and_overdue_needs_owner_reason(self):
        from datetime import date
        class Later(date):
            @classmethod
            def today(cls):return cls(2028,1,1)
        with mock.patch.object(V,'date',Later):
            self.assertEqual(self.run_binding()[0],0)
            def overdue(r,m,i,f):
                i['completedOn']='2027-02-06';i['sm3Assessment'].update(assessedOn='2027-02-06')
            self.assertEqual(self.run_binding(overdue),(1,'','FAIL: overdue SM-3 requires explicit owner slip reason\n'))
            def slip(r,m,i,f):
                overdue(r,m,i,f);i['sm3Assessment'].update(outcome='slip',ownerReason='The owner retains G01–G06 and schedules a successor; no legacy server deleted.')
            self.assertEqual(self.run_binding(slip)[0],0)
            self.assertEqual(self.run_binding(lambda r,m,i,f:i['sm3Assessment'].update(outcome='met')),(1,'','FAIL: SM-3 met requires evidenced retirement\n'))


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
