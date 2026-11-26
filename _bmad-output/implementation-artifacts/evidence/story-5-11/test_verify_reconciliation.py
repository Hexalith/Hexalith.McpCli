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
import subprocess
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
RELEASE_REVISION = '1'*40


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


def missing_ancestry(checkout, ancestor, descendant):
    args = ('merge-base','--is-ancestor',ancestor,descendant)
    message = 'git '+' '.join(args)+': '

    def reject(repo, command, git):
        if repo == checkout and command == args:
            raise ValueError(message)

    return message,reject


class GuardRefusalTests(unittest.TestCase):
    def refuses(self,message,action,*args):
        with self.assertRaises(ValueError) as refused:
            action(*args)
        self.assertEqual(str(refused.exception),message)

    def test_builder_reports_git_failure_and_refuses_invalid_inventory_rows(self):
        with mock.patch.object(subprocess,'run',return_value=subprocess.CompletedProcess(
                ['git'],128,b'',b'object is missing\n')):
            self.refuses('git show absent: object is missing',B.git,ROOT,'show','absent')
        self.refuses('duplicate inventory row PS01',B.rows,
                     '| ID | Surface |\n| PS01 | CLI |\n| PS01 | MCP |\n')
        self.refuses('malformed row PS01',B.rows,'| ID | Surface |\n| PS01 |\n')

    def test_builder_refuses_missing_or_duplicate_readme_labels(self):
        label = next(row for row in data('labels.json')['rows'] if row['id'] == 'PS01')
        line = b'- `Hexalith.EventStore.Admin.Cli`: Previous guidance.\n'
        for count in (0,2):
            with self.subTest(label_count=count):
                self.refuses('eventstore: missing/duplicate README label PS01',B.corrected_document,
                             'eventstore','README.md',b'# EventStore\n\n'+line*count,[label])

    def test_artifact_binding_rejects_missing_and_escaping_paths(self):
        self.refuses('artifact binding lacks path',V.checked,ROOT,{})
        self.refuses('artifact binding lacks path',V.checked,ROOT,None)
        self.refuses('artifact path escapes repository',V.checked,ROOT,{'path':'../foreign.json'})
        receipt = ROOT/E/'approval.json'
        self.refuses('artifact path escapes repository',V.checked,ROOT,{'path':str(receipt),
                     'sha256':B.sha(receipt.read_bytes())})

    def test_approval_requires_valid_schema_roles_state_and_attribution(self):
        for field,value,message in (
            ('schemaVersion','0','approval schema/baseline mismatch'),
            ('baselineCommit','0'*40,'approval schema/baseline mismatch'),
            ('requiredApprovalRoles',[],'approval required-role policy mismatch'),
            ('decision','draft','unknown approval decision'),
            ('approver','','approval lacks identity, words, source or date'),
        ):
            with self.subTest(field=field):
                receipt = approved()
                self.refuses(message,V.check_approval,dict(receipt,**{field:value}),
                             receipt['artifacts'],receipt['requiredApprovalRoles'])
        receipt = approved()
        roles = receipt['rolesCovered']
        for covered in (dict.fromkeys(roles),[*roles,roles[0]]):
            with self.subTest(covered=type(covered)):
                self.refuses('approval lacks explicitly covered roles',V.check_approval,
                             dict(receipt,rolesCovered=covered),receipt['artifacts'],receipt['requiredApprovalRoles'])
        receipt = pending()
        self.refuses('completion requires fresh exact-byte successor approval',V.check_approval,
                     receipt,receipt['artifacts'],receipt['requiredApprovalRoles'],True)

    def test_history_requires_version_repository_status_receipt_and_committed_predecessor(self):
        inputs = data('inputs.json')
        item = inputs['inventoryHistories']['eventstore-admin'][0]
        oldpath = item['path']
        original = Path.read_bytes
        for field,change,message in (
            ('declared version',lambda item:item,'declared inventory version mismatch'),
            ('source repository',lambda item:item.update(sourceRepository='foreign'),'source repository binding missing'),
            ('authority status',lambda item:item.update(effectiveStatus='delivered'),'approval versus delivery status conflated'),
            ('receipt',lambda item:item['approval']['receipt'].update(path='other.json'),'wrong approval receipt'),
            ('predecessor',lambda item:item,'approved predecessor bytes changed'),
        ):
            with self.subTest(field=field):
                changed = copy.deepcopy(inputs)
                row = changed['inventoryHistories']['eventstore-admin'][0]
                change(row)
                raw = original(ROOT/oldpath)
                if field == 'declared version':
                    raw = re.sub(rb'(?m)^inventory_version: .+$',b"inventory_version: '9.0.0'",raw,count=1)
                if field == 'predecessor':
                    raw += b'\nChanged predecessor content.\n'
                row['sha256'] = B.sha(raw)
                with mock.patch.object(Path,'read_bytes',lambda path: raw if path == ROOT/oldpath else original(path)):
                    self.refuses('eventstore-admin: '+message,V.check_histories,ROOT,changed)
        technical = inputs['inventoryHistories']['technical-tools'][-2]
        self.assertEqual(technical['version'],B.SUCCESSORS['eventstore-admin'][1])
        technical_path = ROOT/technical['path']
        tampered = original(technical_path) + b'\nChanged historical technical inventory.\n'
        technical['sha256'] = B.sha(tampered)
        with mock.patch.object(Path,'read_bytes',lambda path: tampered if path == technical_path else original(path)):
            self.refuses('technical-tools: approved predecessor bytes changed',V.check_histories,ROOT,inputs)

    def test_successor_preserves_rows_fields_and_values_beyond_the_derivation(self):
        module = 'eventstore-admin'
        version = B.SUCCESSORS[module][1]
        path = ROOT/B.A/f'{module}-migration-inventory-v{version}.md'
        original = Path.read_bytes
        derived = B.successor
        tampered = original(path) + b'\nChanged successor content.\n'
        with mock.patch.object(Path,'read_bytes',lambda p: tampered if p == path else original(p)):
            self.refuses(module+': successor differs from preserved receipt-based derivation',V.check_successors,ROOT,approved())

        parse_rows = B.rows
        for failure in ('row accounting mismatch','row fields missing','preserved field changed'):
            with self.subTest(failure=failure):
                rows = parse_rows(original(path).decode())
                key = next(iter(rows))
                field = next(iter(rows[key]))
                if failure == 'row accounting mismatch':
                    rows.pop(key)
                    message = failure
                elif failure == 'row fields missing':
                    rows[key].pop(field)
                    message = failure+': '+key
                else:
                    rows[key][field] += ' altered'
                    message = failure+': '+key+'/'+field
                with mock.patch.object(B,'rows',side_effect=lambda raw: rows if raw == derived(module).decode() else parse_rows(raw)):
                    self.refuses(module+': '+message,V.check_successors,ROOT,approved())

    def test_label_register_requires_state_predecessors_inventory_citations_and_owners(self):
        for change,message in (
            (lambda labels:labels.update(state='unknown'),'unknown label state'),
            (lambda labels:labels['predecessors'][0].update(path='unrelated.json'),'label predecessor path mismatch'),
            (lambda labels:labels.update(inventoryArtifacts={}),'label successor inventory hash binding mismatch'),
            (lambda labels:labels['rows'][0]['label'].update(sha256='0'*64),'PS01: label text/hash/citation mismatch'),
            (lambda labels:labels['repositories'].pop(),'seven README owner accounting mismatch'),
        ):
            with self.subTest(message=message):
                labels = data('labels.json')
                change(labels)
                self.refuses(message,V.check_labels,ROOT,labels)
        labels = data('labels.json')
        row = labels['rows'][0]
        text = row['label']['text'].replace(row['gate'],'UNBOUND')
        row['label'].update(text=text,sha256=B.sha(text.encode()))
        self.refuses('PS01: removal gate lost',V.check_labels,ROOT,labels)

    def test_patch_sources_bind_snapshot_composition_and_base(self):
        manifest = data('upstream/manifest.json')
        owner = next(owner for owner in manifest['owners'] if owner['name']=='chatbot')
        file = next(file for file in owner['files'] if file['path']=='README.md')
        self.refuses('chatbot: source snapshot changed',V.prepared_before,ROOT,owner,dict(file,sourceSha256='0'*64))
        self.refuses('chatbot: prepared patch base mismatch',V.prepared_before,ROOT,owner,dict(file,beforeSha256='0'*64))
        unrelated = b'Unrelated README\n'
        with mock.patch.object(B,'git',return_value=unrelated):
            self.refuses('chatbot: missing Story 5.10 composition prerequisite',V.prepared_before,ROOT,owner,
                         dict(file,sourceSha256=B.sha(unrelated)))
        recipe = {'schemaVersion':'1.0.0','path':'other.md','edits':[]}
        self.refuses('literal patch schema/target mismatch',V.literal_patch,b'contents',B.serialized(recipe),'README.md')

    def test_patch_manifest_requires_valid_inspection_and_canonical_owner_base(self):
        for change,message in (
            (lambda packet:packet['noChange'][0].update(revision='abc'),'platform: invalid inspection revision'),
            (lambda packet:packet['owners'][0].update(ownerCheckout='.'),'eventstore: wrong owning checkout'),
            (lambda packet:packet['owners'][0].update(observedOriginMain='0'*40),'eventstore: canonical main base missing'),
            (lambda packet:packet['owners'][0]['files'][0].update(afterSha256=packet['owners'][0]['files'][0]['beforeSha256']),
             'eventstore: empty correction patch'),
            (lambda packet:packet['owners'][0]['files'][0].update(afterSha256='0'*64),'eventstore: applied patch bytes differ'),
        ):
            with self.subTest(message=message):
                manifest = data('upstream/manifest.json')
                change(manifest)
                self.refuses(message,V.check_patches,ROOT,manifest,data('labels.json'))

    def test_patch_application_reports_each_failed_git_step(self):
        actual = V.subprocess.run
        for subcommand,message in (
            (['init','--quiet'],'eventstore: cannot initialize isolated patch repository'),
            (['apply','--check','-'],'eventstore: patch does not apply: fixture git error'),
            (['apply','-'],'eventstore: patch application failed'),
        ):
            with self.subTest(subcommand=subcommand):
                def fail(command,*args,**kwargs):
                    if command[-len(subcommand):] == subcommand:
                        return V.subprocess.CompletedProcess(command,1,b'',b'fixture git error')
                    return actual(command,*args,**kwargs)
                with mock.patch.object(V.subprocess,'run',side_effect=fail):
                    self.refuses(message,V.check_patches,ROOT,data('upstream/manifest.json'),data('labels.json'))

    def test_patch_manifest_requires_applied_candidate_bytes(self):
        manifest = data('upstream/manifest.json')
        owner = next(owner for owner in manifest['owners'] if owner['name']=='ai-tools')
        file = next(file for file in owner['files'] if 'candidate' in file)
        path = E/'inputs.json'
        file['candidate'] = {'path':str(path),'sha256':B.sha((ROOT/path).read_bytes())}
        self.refuses('ai-tools: candidate and applied bytes differ',V.check_patches,ROOT,manifest,data('labels.json'))

    def test_commit_date_requires_an_offset(self):
        revision = '0'*40
        with mock.patch.object(B,'git',return_value=b'2026-11-22T23:59:00'):
            self.refuses('commit date missing: '+revision,V.commit_date,ROOT,revision)

    def test_audit_prose_and_candidate_plan_account_for_every_entry(self):
        audit = data('deferral-dispositions.json')
        path = ROOT/E/'deferral-dispositions.md'
        text = Path.read_text
        with mock.patch.object(Path,'read_text',lambda p,*a,**kw:'' if p == path else text(p,*a,**kw)):
            self.refuses('deferral prose accounting mismatch',V.check_deferrals,ROOT,audit)
        plan = ROOT/E/'upstream/ai-tools/hexalith-mcpcli-migration-instructions.md'
        inputs = data('inputs.json')
        first = inputs['inventoryHistories']['eventstore-admin'][0]
        for old,message in (
            ('inventory_revision: null','prepared plan must expose missing immutable publication binding'),
            (first['sha256'],'eventstore-admin: prepared plan omits version/path/hash'),
        ):
            with self.subTest(message=message),mock.patch.object(Path,'read_text',lambda p,*a,**kw:
                    text(p,*a,**kw).replace(old,'removed') if p == plan else text(p,*a,**kw)):
                self.refuses(message,V.check_candidate_plan,ROOT,inputs)


@cache
def replay_follow_up():
    folder = HERE/'owner-doc-follow-up'
    index = (folder/'README.md').read_text()
    rows = re.findall(r'^\| \[[^\]]+\]\(([^)]+)\.patch\) \| `([a-f0-9]{40})` \| (\d+) \| `([a-f0-9]{64})` \|$',index,re.M)
    expected_patches = {patch.stem for patch in folder.glob('*.patch')}
    if len(rows) != len(expected_patches) or {row[0] for row in rows} != expected_patches:
        raise AssertionError('Follow-up patch index does not match the patch files')
    results, baselines = {}, {}
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
                base = B.git(repo,'show',revision+':'+path)
                dest.write_bytes(base)
                baselines[owner,path] = base
            B.git(scratch,'-c','core.whitespace=cr-at-eol','apply','--whitespace=error',str(patch))
            for name in paths:
                path = name.decode()
                results[owner,path] = (scratch/path).read_bytes()
            B.git(scratch,'-c','core.whitespace=cr-at-eol','apply','--reverse','--whitespace=nowarn',str(patch))
            for name in paths:
                path = name.decode()
                if (scratch/path).read_bytes() != baselines[owner,path]:
                    raise AssertionError(f'{owner}: reverse patch did not restore {path}')
    return results,baselines


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
    def main(self,overrides=None,completion=False,replay_patches=False):
        candidate = dict(data('integration.json'), state='blocked')
        overrides = {str(E/'integration.json'):candidate, **(overrides or {})}
        original = V.read
        def read(root,path):
            return copy.deepcopy((overrides or {}).get(str(path),original(root,path)))
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(V,'read',side_effect=read))
            if not replay_patches and str(E/'upstream/manifest.json') not in overrides:
                stack.enter_context(mock.patch.object(V,'check_patches'))
            return streams(lambda:V.main(['--approved-completion'] if completion else []))

    def refusal(self,overrides,message,completion=False):
        self.assertEqual(self.main(overrides,completion),(1,'','FAIL: '+message+'\n'))

    def test_pending_candidate_exact_streams_and_completion_refusal(self):
        overrides = {str(E/'approval.json'):pending()}
        self.assertEqual(self.main(overrides,replay_patches=True),(0,PASS+'PASS: decision: pending; candidate only; approval, publication and upstream integration remain gates\n',''))
        self.refusal(overrides,'completion requires fresh exact-byte successor approval',True)
        for field,value in [('inventoryRevision','1'*40),('deliveryAuthorization',{'decision':'authorized'})]:
            with self.subTest(premature_claim=field):
                labels = dict(data('labels.json'),**{field:value})
                self.refusal(dict(overrides,**{str(E/'labels.json'):labels}),
                             'candidate must not claim delivered publication or labels')
        manifest = data('upstream/manifest.json')
        manifest['owners'][0]['integration'] = {'commit':'1'*40}
        with mock.patch.object(V,'check_patches'):
            self.refusal(dict(overrides,**{str(E/'upstream/manifest.json'):manifest}),
                         'candidate must not claim delivered publication or labels')

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

    def test_adopted_and_prior_authority_bytes_match_baseline_even_when_rehashed(self):
        original = Path.read_bytes
        for key,message in [('authorities','adopted AD-23/authority bytes changed'),('priorApprovals','prior approval bytes changed')]:
            with self.subTest(key=key):
                inputs = data('inputs.json')
                binding = inputs[key][0]
                path = ROOT/binding['path']
                changed = original(path) + b'\n'
                binding['sha256'] = B.sha(changed)
                with mock.patch.object(Path,'read_bytes',lambda target:
                        changed if target == path else original(target)):
                    self.refusal({str(E/'inputs.json'):inputs},message)

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
        for path,key,value in [(ROOT/B.SPEC,'status','done'),
                               (ROOT/B.A/'sprint-status.yaml','  5-11-reconcile-product-claims-and-the-migration-plan','done'),
                               (ROOT/B.A/'sprint-status.yaml','  5-11-reconcile-product-claims-and-the-migration-plan',"'done'"),
                               (ROOT/B.A/'sprint-status.yaml','  5-11-reconcile-product-claims-and-the-migration-plan','"done"')]:
            def read_text(p,*args,**kwargs):
                text=original(p,*args,**kwargs)
                return V.re.subn(r'^'+V.re.escape(key)+r': \S+',key+': '+value,text,count=1,flags=V.re.M)[0] if p==path else text
            with self.subTest(path=path,value=value),mock.patch.object(Path,'read_text',read_text):
                self.refusal({str(E/'approval.json'):pending()},'completion requires fresh exact-byte successor approval')

    def test_integrated_state_triggers_completion_from_both_records(self):
        for record in ('integration.json','labels.json'):
            with self.subTest(record=record), mock.patch.object(
                V,'check_completion',side_effect=ValueError('completion checks invoked')
            ):
                value = dict(data(record),state='integrated')
                overrides = {str(E/'integration.json'):data('integration.json'),str(E/record):value}
                self.refusal(overrides,'completion checks invoked')

    def test_unknown_integration_state_is_refused_in_both_modes(self):
        for completion in (False,True):
            with self.subTest(completion=completion):
                integration = dict(data('integration.json'),state='deliverd')
                self.refusal({str(E/'integration.json'):integration},'unknown integration state',completion)

    def test_story_510_requires_the_exact_approval_labels_and_delivery_binding(self):
        changes = [
            ('labels binding',lambda bound:bound['labels'].update(sha256='0'*64)),
            ('approval binding',lambda bound:bound['approval'].update(sha256='0'*64)),
            ('delivery binding',lambda bound:bound.update(state='pending')),
            ('delivery binding',lambda bound:bound.update(inventoryRevision='0'*40)),
            ('delivery binding',lambda bound:bound.update(ownerIntegrations={})),
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
                    owner_conflict=None, hosted_mutation=None, current_documents=None,
                    release_ledger_change=None, assessments_only=False):
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
            summary = ledger.index('  summary: '+entry['summary'])
            start = ledger.rindex('- source_spec:',0,summary)
            end = len(ledger.rstrip())
            update = ledger[start:end].replace('  status: open;','  status: resolved;',1)
            update += '\n  resolution: The release owner verified the generated notes.\n'
            if release_ledger_change:
                update = release_ledger_change(update)
            ledger = ledger[:start]+update+ledger[end:]
            files[ROOT/V.LEDGER] = ledger.encode()
            active = next(row for row in B.scoped_deferrals(ledger) if row['id'] == entry['id'])
            status = git(ROOT,'show',integration['rootIntegrationRevision']+':docs/release/migration-status.md')
            notes_body = b'# Generated release notes\n\n'+status
            notes = binding('fixture-notes.md',notes_body)
            resolution = {
                'decision':'resolved','entryId':entry['id'],'auditedEntrySha256':entry['entrySha256'],
                'resolvedEntrySha256':active['entrySha256'],'owner':'Hexalith.Builds',
                'exactWords':'approve','source':'Fixture release owner decision',
                'decidedOn':'2026-11-22','releaseRevision':RELEASE_REVISION,'releaseTag':tag,'releaseRunId':123,'generatedNotes':notes,
                'evidenceRevision':V.FINAL_INTEGRATION_RECORD,
            }
            hosted.update({
                'publishedRelease':{'html_url':V.ROOT_REPOSITORY+'/releases/tag/'+tag,'draft':False,'tag_name':tag,
                                    'published_at':'2026-11-22T23:59:00Z','id':456,'body':notes_body.decode()},
                'releaseRun':{'id':123,'conclusion':'success','head_sha':RELEASE_REVISION,'path':'.github/workflows/release.yml',
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
            '/epics.md':
                ((b'A current human-delegated MCP client may access',),
                 b'Human-decision operations require a confidential interactive UI client'),
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
                return RELEASE_REVISION.encode()
            if resolved and repo == ROOT:
                if args[:2] == ('merge-base','--is-ancestor') and RELEASE_REVISION in args[2:]:
                    return b''
                if args == ('show','-s','--format=%cI',RELEASE_REVISION):
                    return b'2026-11-22T23:59:00+00:00'
                if args == ('show',RELEASE_REVISION+':docs/release/migration-status.md'):
                    return status
            if repo == ROOT and args[0] == 'show' and args[1].startswith(V.FINAL_INTEGRATION_RECORD+':'):
                artifact = args[1].split(':',1)[1]
                if artifact in release_evidence:
                    return release_evidence[artifact]
            if args[0] == 'show' and args[1].startswith('origin/main:'):
                owner = Path(repo).name.lower().split('.')[-1]
                if owner == 'aitools':
                    owner = 'ai-tools'
                path = args[1].removeprefix('origin/main:')
                if current_documents and (owner,path) in current_documents:
                    return current_documents[owner,path]
                revision = delivered.get((owner,path))
                if checking_owner_conflicts:
                    for suffix,(prior,replacement) in owner_text.items():
                        if path.endswith(suffix):
                            return b'\n'.join(prior) if owner == owner_conflict else replacement
                if revision:
                    return git(repo,'show',revision+':'+path)
            return git(repo,*args)

        def run(*args):
            if assessments_only:
                V.check_assessments(ROOT,integration)
            else:
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

    def assessment_refusal(self, message, *args, **kwargs):
        self.refusal(message,*args,assessments_only=True,**kwargs)

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

    def test_completion_requires_exactly_one_audited_ac3_disposition(self):
        def omit_ac3(integration,files,binding):
            audit = data('deferral-dispositions.json')
            audit['entries'] = [entry for entry in audit['entries'] if entry['id'] != V.RELEASE_NOTES_ENTRY]
            changed = binding(E/'deferral-dispositions.json',B.serialized(audit))
            decision = integration['deferralOwnerDecision']
            decision['auditSha256'] = changed['sha256']
            decision['retainedUnresolvedEntryIds'].remove(V.RELEASE_NOTES_ENTRY)
        self.refusal('AC3 release-note disposition missing',file_mutation=omit_ac3)

    def test_ac3_requires_current_ledger_decision_and_actual_generated_text(self):
        def change_resolution(update):
            def mutate(integration,files,binding):
                value = json.loads(files[ROOT/'fixture-resolution.json'])
                update(value,files,binding)
                integration['releaseNotesResolution'] = binding('fixture-resolution.json',B.serialized(value))
            return mutate

        cases = [
            ('AC3 resolution lacks an explicit owner decision bound to the approved entry',
             lambda r,files,b:r.update(decision='pending')),
            ('AC3 resolution lacks an explicit owner decision bound to the approved entry',
             lambda r,files,b:r.update(entryId='0'*16)),
            ('AC3 resolution lacks an explicit owner decision bound to the approved entry',
             lambda r,files,b:r.update(auditedEntrySha256='0'*64)),
            ('AC3 resolution lacks an explicit owner decision bound to the approved entry',
             lambda r,files,b:r.update(exactWords='I do not approve closing AC3')),
            ('AC3 resolution lacks an explicit owner decision bound to the approved entry',
             lambda r,files,b:r.update(owner='Unrelated maintainer')),
            ('AC3 resolution lacks an explicit owner decision bound to the approved entry',
             lambda r,files,b:r.update(source='')),
            ('AC3 resolution must bind the resolved release ledger entry',
             lambda r,files,b:files.pop(ROOT/V.LEDGER)),
            ('AC3 resolution must bind the resolved release ledger entry',
             lambda r,files,b:r.update(resolvedEntrySha256='0'*64)),
            ('AC3 generated notes omit the committed migration status',
             lambda r,files,b:r.update(generatedNotes=b('fixture-notes.md',b'Notes without migration status.'))),
            ('AC3 generated notes omit the committed migration status',
             lambda r,files,b:r.update(generatedNotes=b('fixture-notes.md',files[ROOT/'fixture-notes.md']+b'\nAll surfaces retired.'))),
            ('AC3 requires committed release and generation-run evidence for the tag',
             lambda r,files,b:r.pop('releaseRunId')),
            ('AC3 requires committed release and generation-run evidence for the tag',
             lambda r,files,b:r.update(releaseTag='latest')),
            ('AC3 requires committed release and generation-run evidence for the tag',
             lambda r,files,b:r.update(releaseRunId=0)),
            ('AC3 requires committed release and generation-run evidence for the tag',
             lambda r,files,b:r.update(evidenceRevision='bad')),
            ('AC3 requires committed release and generation-run evidence for the tag',
             lambda r,files,b:r.update(evidenceRevision=r['releaseRevision'])),
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
                self.assessment_refusal(message,file_mutation=change_resolution(update))

    def test_release_ledger_requires_its_owner_and_closed_disposition(self):
        changes = [
            lambda text: re.sub(r'^  owner: .+$','  owner: Unrelated maintainer',text,flags=re.M),
            lambda text: text.replace('status: resolved;', 'status: open;'),
            lambda text: re.sub(r'^  resolution: .+\n','',text,flags=re.M),
        ]
        for change in changes:
            with self.subTest(change=change):
                self.assessment_refusal('AC3 resolution must bind the resolved release ledger entry',release_ledger_change=change)
        self.assertEqual(self.run_binding(release_ledger_change=lambda text:
                         text.replace('status: resolved;','status: done;')),(0,VERIFIED,''))
        for change in (
            lambda text: text+'\n'+text,
            lambda text: re.sub(r'^- source_spec: .+', '- source_spec: spec-5-unrelated.md',text),
        ):
            with self.subTest(change=change):
                self.assessment_refusal('AC3 resolution must bind the resolved release ledger entry',release_ledger_change=change)

    def test_release_requires_exact_source_workflow_and_committed_published_notes(self):
        self.assessment_refusal('AC3 release tag does not identify the approved source revision',
                     git_mutation=lambda r,a,g:('0'*40).encode() if a == ('rev-parse','refs/tags/v2.0.2^{commit}') else None)
        for field,value in (('head_sha','0'*40),('conclusion','failure'),('id',124),
                            ('path','.github/workflows/ci.yml'),
                            ('html_url',V.ROOT_REPOSITORY+'/actions/runs/124')):
            with self.subTest(run=field):
                self.assessment_refusal('AC3 release generation run does not bind the tagged source',
                             hosted_mutation=lambda records:records['releaseRun'].update({field:value}))
        self.assessment_refusal('AC3 approved generated notes do not match the published release body',
                     hosted_mutation=lambda records:records['publishedRelease'].update(body='Different notes.'))
        self.assessment_refusal('AC3 release evidence differs from the committed record: releaseRun',
                     git_mutation=lambda r,a,g:b'other' if a == ('show',V.FINAL_INTEGRATION_RECORD+':fixture-releaseRun.json') else None)
        self.assessment_refusal('AC3 release evidence differs from the committed record: generatedNotes',
                     git_mutation=lambda r,a,g:b'other' if a == ('show',V.FINAL_INTEGRATION_RECORD+':fixture-notes.md') else None)

    def test_release_requires_published_identity_and_ordered_evidence(self):
        for key,value in [('draft',True),('tag_name','v0.0.0'),('id','456'),('html_url','https://example.invalid/release')]:
            with self.subTest(field=key):
                self.assessment_refusal('AC3 requires a published McpCli release record for the tag',
                             hosted_mutation=lambda hosted:hosted['publishedRelease'].update({key:value}))
        def commit_time(revision, timestamp):
            return lambda repo,args,git: timestamp.encode() if args == ('show','-s','--format=%cI',revision) else None
        for mutation in (
            {'hosted_mutation':lambda hosted:hosted['publishedRelease'].update(published_at='2026-11-21T23:59:00Z')},
            {'git_mutation':commit_time(V.FINAL_INTEGRATION_RECORD,'2026-11-21T23:59:00+00:00')},
            {'git_mutation':commit_time(V.FINAL_INTEGRATION_RECORD,'2026-11-22T23:30:00-02:00')},
        ):
            with self.subTest(mutation=mutation):
                self.assessment_refusal('AC3 owner approval predates the committed release evidence',**mutation)
        self.assertEqual(self.run_binding(git_mutation=commit_time(RELEASE_REVISION,'2026-11-23T00:30:00+02:00')),
                         (0,VERIFIED,''))

    def test_release_requires_ancestry_from_the_inventory_through_committed_main_evidence(self):
        release = RELEASE_REVISION
        evidence = V.FINAL_INTEGRATION_RECORD
        for ancestor,descendant in ((V.INVENTORY_PUBLICATION,release),(release,'origin/main'),
                                    (release,evidence),(evidence,'origin/main')):
            with self.subTest(ancestor=ancestor,descendant=descendant):
                message,git_mutation = missing_ancestry(ROOT,ancestor,descendant)
                self.assessment_refusal(message,git_mutation=git_mutation)

    def test_completion_requires_both_owner_conflicts_to_be_closed(self):
        for owner,path in [
            ('chatbot','prds/prd-Hexalith.ChatBot-2026-05-28/prd.md'),
            ('works','ux-designs/ux-works-2026-06-14/EXPERIENCE.md'),
        ]:
            self.refusal('completion requires published '+owner+' migration guidance: _bmad-output/planning-artifacts/'+path,
                         owner_conflict=owner)

    def test_default_and_completion_check_replayed_owner_main_documents(self):
        documents,_ = replay_follow_up()
        for row in data('labels.json')['rows']:
            if row['id'] in {'PS03','PS14'}:
                lines = documents[row['repository'],'README.md'].splitlines()
                self.assertEqual(lines.count(row['label']['text'].encode()),1,row['id'])
        planning = '_bmad-output/planning-artifacts/'
        drift = (
            ('eventstore',planning+'prd.md'),
            ('frontcomposer','README.md'),
            ('frontcomposer',planning+'prd.md'),
            ('frontcomposer',planning+'architecture.md'),
            ('frontcomposer',planning+'architecture/architecture-gov-1-2026-07-19/ARCHITECTURE-SPINE.md'),
            ('frontcomposer',planning+'ux-designs/ux-frontcomposer-2026-09-09/EXPERIENCE.md'),
            ('chatbot',planning+'prds/prd-Hexalith.ChatBot-2026-05-28/prd.md'),
            ('projects','README.md'),
            ('projects',planning+'epics.md'),
            ('projects',planning+'prds/prd-Hexalith.Projects-2026-05-24/prd.md'),
            ('tenants',planning+'architecture.md'),
        )
        reported = ''.join(f'reported: {owner}: current main migration text drift: {path}\n' for owner,path in drift)
        for default in (True,False):
            with self.subTest(default=default):
                self.assertEqual(self.run_binding(default=default,full=True,current_documents=documents),
                                 (0,VERIFIED,reported))

    def test_owner_guidance_requires_visible_correction_and_refuses_each_stale_claim(self):
        documents,bases = replay_follow_up()
        self.assertIsNone(self.check_guidance(documents))
        planning = '_bmad-output/planning-artifacts/'
        chatbot_prd = documents['chatbot',planning+'prds/prd-Hexalith.ChatBot-2026-05-28/prd.md'].splitlines()
        chatbot_epics = documents['chatbot',planning+'epics.md'].splitlines()
        [shared_client] = [line for line in chatbot_prd if line.startswith(b'| `cli-automation-client` |')]
        self.assertIn(b"Both McpCli heads use the profile's Gateway credential and session actor (`--actor`)",shared_client)
        self.assertIn(b'The EventStore Gateway authorizes the credential, tenant and operation.',shared_client)
        self.assertIn(b'The session actor provides attribution.',shared_client)
        self.assertIn(b'Both heads list enrolled operations in the shared agent-eligible set. The Gateway authorizes each submission.',shared_client)
        self.assertIn(b'Approval and approved execution require the confidential ChatBot UI.',shared_client)
        self.assertIn(b'Credential expiry and renewal follow the issuer. The stdio session ends when its process exits.',shared_client)
        self.assertIn(b'| `mcp-human-delegated-client` | Withdrawn for M1 | No credential issued | No operation access | No session |',
                      chatbot_prd)
        self.assertFalse(any(b'mcpcli-stdio-client' in line for line in chatbot_prd))
        for prefix in (b'- FR82: ', b'- FR83: ', b'- FR84: ', b'- NFR67: '):
            [requirement] = [line for line in chatbot_prd if line.startswith(prefix)]
            self.assertIn(requirement,chatbot_epics)
        self.assertIn('FR82: Epic 5 — Deliver parity for the approved agent-eligible M1 set on both McpCli heads after Contracts and Gateway enrollment.'.encode(),
                      chatbot_epics)
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
             (b'Inspect, associate, reject, defer, retry, approve, execute',
              b'human-decision mutations require current presence at submission',
              b'user-delegated via OAuth device flow',
              b'current authenticated human',
              b'scope, and delegation expiry |',
              b'1 hour maximum; terminates on logout, revocation, or lost presence',
              b'UI/API, CLI, and MCP association/status/audit parity',
              b'CLI and MCP integration must expose the same governed operations as the UI',
              b'CLI, human-delegated MCP, AI/tool MCP')),
            ('chatbot','ux-designs/ux-Hexalith.ChatBot-2026-05-28/EXPERIENCE.md',
             b'Both McpCli heads refuse those operations.',
             (b'Human-delegated MCP approval is candidate M1 behavior',
              b'candidate human-delegated MCP approval remains unavailable',
              b'explicitly exposed on UI, CLI, and/or MCP',
              b'He confirms an association through an exposed surface')),
            ('chatbot','epics.md',
             b'Human-decision operations require a confidential interactive UI client',
             (b'Authorized CLI users can perform the singular M1 parity set',
              b'A current human-delegated MCP client may access',
              b'UI, CLI, and MCP must return equivalent authorization outcomes and state transitions',
              b'CLI, human-delegated MCP, AI/tool MCP',
              b'Deliver CLI parity for the singular M1 set',
              b'Distinguish human-delegated MCP with current human presence')),
            ('works','ux-designs/ux-works-2026-06-14/EXPERIENCE.md',
             b'Discover enrolled Works Commands and Queries through the generic McpCli heads.',
             (b'Exact MCP tools/resources and CLI commands over the kernel',
              b'exact tool/resource names and syntax remain source-open')),
            ('works','ux-designs/ux-works-2026-06-14/DESIGN.md',
             b'after Works Contracts enrollment and authorization.',
             (b'exact tools, resources, syntax, and protocol remain source-open',)),
            ('works','ux-designs/ux-works-2026-06-14/mockups/key-mcp-cli.html',
             b'The shared McpCli CLI and stdio MCP heads expose eligible Works operations',
             (b'Both adapters expose registered domain commands and resources',
              b'adapter command syntax intentionally unspecified',
              b'input: retained in adapter context')),
        )
        for owner,suffix,required,obsolete in targets:
            path = planning+suffix
            raw = documents[owner,path]
            refusal = 'completion requires published '+owner+' migration guidance: '+path
            with self.subTest(path=path,hidden=required):
                self.assertIn(required,raw)
                changed = raw.replace(required,b'<!-- '+required+b' -->')
                self.assertEqual(self.check_guidance({**documents,(owner,path):changed}),refusal)
            baseline = V.visible_markdown(bases[owner,path]).encode()
            for phrase in obsolete:
                with self.subTest(path=path,obsolete=phrase):
                    self.assertIn(phrase,baseline)
                    self.assertNotIn(phrase,V.visible_markdown(raw).encode())
                    changed = raw+b'\n'+phrase+b'\n'
                    self.assertEqual(self.check_guidance({**documents,(owner,path):changed}),refusal)

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
        revision = recorded_git(ROOT,'rev-parse',V.INVENTORY_PUBLICATION+'^').decode().strip()
        def exercise(change_resolution=None, ledger_change=None, committed=True,
                     committed_at=b'2026-11-22T23:59:59+00:00', git_mutation=None,
                     status='resolved by the owning maintainer.'):
            def update(integration,files,binding):
                text = files[ROOT/V.LEDGER].decode()
                summary = text.index('  summary: '+entry['summary'])
                start = text.rindex('- source_spec:',0,summary)
                end = text.index('\n\n',summary)
                raw = text[start:end]
                if ledger_change is not None:
                    files[ROOT/V.LEDGER] = (text[:start]+ledger_change(raw)+text[end:]).encode()
                    return
                resolved = re.sub(r'\n  status: [^\n]*','',raw)+'\n  status: '+status
                resolved += '\n  resolution: The maintainer verified the existing requirement.'
                files[ROOT/V.LEDGER] = (text[:start]+resolved+text[end:]).encode()
                resolution = {
                    'entryId':entry_id,'auditedEntrySha256':entry['entrySha256'],
                    'resolvedEntrySha256':B.sha(resolved.encode()),'owner':entry['owner'],
                    'exactWords':'approve','source':'Fixture owning maintainer decision','decision':'resolved',
                    'revision':revision,'decidedOn':'2026-11-22',
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
                if git_mutation:
                    git_mutation(repo,args,git)
                if repo == ROOT and args == ('show','-s','--format=%cI',revision):
                    return committed_at
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
                            ('decision','denied'),('source',''),('auditedEntrySha256','0'*64),
                            ('resolvedEntrySha256','0'*64),('entryId','unrelated')]:
            with self.subTest(field=field):
                self.assertEqual(exercise(change_resolution=lambda resolution:resolution.update({field:value})),
                                 (1,'','FAIL: separate resolution does not close the audited owner gate: '+entry_id+'\n'))
        self.assertEqual(exercise(status='open; audited gate still applies'),
                         (1,'','FAIL: separate resolution does not close the audited owner gate: '+entry_id+'\n'))
        self.assertEqual(exercise(change_resolution=lambda resolution:resolution.update(revision=revision[:8])),
                         (1,'','FAIL: audited deferral resolution lacks a committed revision: '+entry_id+'\n'))
        self.assertEqual(exercise(committed=False),
                         (1,'','FAIL: audited deferral resolution differs from the recorded ledger revision: '+entry_id+'\n'))
        self.assertEqual(exercise(committed_at=b'2026-11-23T00:00:00+00:00'),
                         (1,'','FAIL: audited deferral resolution was committed after completion: '+entry_id+'\n'))
        refusal,off_main = missing_ancestry(ROOT,revision,'origin/main')
        self.assertEqual(exercise(git_mutation=off_main),(1,'','FAIL: '+refusal+'\n'))
        self.assertEqual(exercise(change_resolution=lambda resolution:resolution.pop('decidedOn')),
                         (1,'','FAIL: audited deferral owner decision date missing: '+entry_id+'\n'))
        for day in ('2026-11-21','2026-11-23'):
            with self.subTest(decidedOn=day):
                self.assertEqual(exercise(change_resolution=lambda resolution:resolution.update(decidedOn=day)),
                                 (1,'','FAIL: audited deferral owner decision predates the ledger revision or exceeds completion: '+entry_id+'\n'))

    def test_mandatory_delivery_bindings(self):
        cases = [
            ('completion requires integrated plan and all fourteen labels',lambda i,f:i.update(state='blocked')),
            ('completion requires separate explicit Git delivery authorization',lambda i,f:i['deliveryAuthorization'].update(exactWords='authorize',footprint='')),
            ('completion requires separate explicit Git delivery authorization',lambda i,f:i['deliveryAuthorization'].update(exactWords='I do not authorize')),
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
            ('eventstore: upstream integration missing',lambda i,f:i['ownerIntegrations'][0].update(
                commit=i['ownerIntegrations'][0]['commit'][:12])),
            ('eventstore: mandatory commitlint/Builds checks missing',lambda i,f:i['ownerIntegrations'][0]['checks'].update(builds='blocked')),
            ('eventstore: mandatory commitlint/Builds checks missing',lambda i,f:i['ownerIntegrations'][0]['checks'].update(commitlint='failed')),
            ('completion requires full AI.Tools integration revision',lambda i,f:i.update(aiToolsCommit=None)),
            ('AI.Tools revision differs from actual owner integration',lambda i,f:i.update(aiToolsCommit='0'*40)),
            ('committed root integration revision missing',lambda i,f:i.update(rootIntegrationRevision='bad')),
            ('containing AI.Tools gitlink missing',lambda i,f:i.update(aiToolsGitlink=None)),
            ('ai-tools: integrated documentation bytes mismatch',lambda i,f:i.update(planSha256=None)),
            ('final plan exact-byte approval/hash/revision binding missing',lambda i,f:f.update(decision='pending')),
            ('final plan exact-byte approval/hash/revision binding missing',lambda i,f:i.update(planVersion='1.2.0')),
            ('final plan exact-byte approval/hash/revision binding missing',lambda i,f:f.update(planSha256='0'*64)),
            ('final plan exact-byte approval/hash/revision binding missing',lambda i,f:f.update(inventoryRevision='0'*40)),
            ('final plan approval lacks covered roles',lambda i,f:f.update(rolesCovered=[])),
            ('passing instruction synchronization binding missing',lambda i,f:i.update(instructionSync=None)),
            ('AI.Tools final approval must bind the merged review and its exact head',lambda i,f:i['finalPlanReview'].update(state='open')),
            ('AI.Tools final approval must bind the merged review and its exact head',
             lambda i,f:i['finalPlanReview'].update(mergeCommit='0'*40)),
            ('AI.Tools final approval must bind the merged review and its exact head',lambda i,f:f.update(reviewCommit='0'*40)),
            ('AI.Tools final approval must bind the merged review and its exact head',
             lambda i,f:f.update(pullRequest='https://github.com/Hexalith/Hexalith.AI.Tools/pull/99999')),
            ('AI.Tools hosted checks do not bind the approved review head',lambda i,f:i['ownerIntegrations'][-1]['checks'].update(testedHead='0'*40)),
            ('AI.Tools hosted checks differ from the immutable final integration record',lambda i,f:i['ownerIntegrations'][-1]['checks'].update(run='https://github.com/Hexalith/Hexalith.AI.Tools/actions/runs/1')),
            ('AI.Tools hosted checks differ from the immutable final integration record',lambda i,f:i['finalPlanReview'].update(extra='unrecorded')),
            ('completion requires explicit structured deferral owner decision',lambda i,f:i.update(deferralOwnerDecision=None)),
            ('deferral decision must bind exact audit bytes',lambda i,f:i['deferralOwnerDecision'].update(auditSha256='0'*64)),
            ('deferral decision must bind exact audit bytes',lambda i,f:i['deferralOwnerDecision'].update(auditMarkdownSha256='0'*64)),
            ('deferral decision must bind the reviewed packet and owner instruction',lambda i,f:i['deferralOwnerDecision'].update(exactWords='deny')),
            ('deferral decision must bind the reviewed packet and owner instruction',lambda i,f:i['deferralOwnerDecision'].update(reviewedReceiptSha256='0'*64)),
            ('recorded completion date missing or invalid',lambda i,f:i.update(completedOn=None)),
            ('recorded completion date missing or invalid',lambda i,f:i.update(completedOn='20261122')),
            ('recorded completion date is in the future',lambda i,f:i.update(completedOn='9999-12-31')),
            ('deferral decision occurs after completion',lambda i,f:i['deferralOwnerDecision'].update(decidedOn='2026-11-23')),
            ('completion predates approval or verified delivery',lambda i,f:f.update(approvedOn='2026-11-23')),
            ('completion predates approval or verified delivery',lambda i,f:i.update(integratedOn='2026-11-23')),
            ('structured SM-3 assessment missing',lambda i,f:i.update(sm3Assessment=None)),
            ('SM-3 assessment must bind recorded completion date',lambda i,f:i['sm3Assessment'].update(assessedOn='2026-01-01')),
            ('SM-3 outcome/retirement accounting missing',lambda i,f:i['sm3Assessment'].update(outcome='unexpected')),
            ('SM-3 outcome/retirement accounting missing',lambda i,f:i['sm3Assessment'].update(retirements={})),
            ('SM-3 met requires evidenced retirement',lambda i,f:i['sm3Assessment'].update(outcome='met')),
        ]
        for message,mutate in cases:
            with self.subTest(message=message):
                self.refusal(message,mutate)
        def duplicate_delivery(integration, final):
            deliveries = integration['ownerIntegrations']
            deliveries.append(deliveries[0])
        self.refusal('completion requires every owner integration binding',duplicate_delivery)
        self.refusal('completion requires every owner integration binding',
                     lambda i,f:i['ownerIntegrations'][0].update(name='wrong-owner'))
        for field,value in (('decision','pending'),('owner',''),('source','')):
            with self.subTest(deferral_decision=field):
                self.refusal('completion requires explicit structured deferral owner decision',
                             lambda i,f:i['deferralOwnerDecision'].update({field:value}))
        self.refusal('deferral decision must preserve every unresolved owner/gate',
                     lambda i,f:i['deferralOwnerDecision'].update(preserveUnresolvedGates=False))
        def retained_as_tuple(integration, final):
            decision = integration['deferralOwnerDecision']
            decision['retainedUnresolvedEntryIds'] = tuple(decision['retainedUnresolvedEntryIds'])
        self.refusal('deferral decision must preserve every unresolved owner/gate',retained_as_tuple)
        def change_retained(change):
            return lambda i,f:change(i['deferralOwnerDecision']['retainedUnresolvedEntryIds'])
        self.refusal('deferral decision must preserve every unresolved owner/gate',
                     change_retained(lambda ids:ids.append(ids[0])))
        self.refusal('deferral decision must preserve every unresolved owner/gate',
                     change_retained(lambda ids:ids.__setitem__(0,'0'*16)))
        run = subprocess.run
        def failed_sync(command,*args,**kwargs):
            if command == ['bash','scripts/check-agent-instructions-sync.sh']:
                return subprocess.CompletedProcess(command,1,b'',b'instructions differ\n')
            return run(command,*args,**kwargs)
        with mock.patch.object(subprocess,'run',side_effect=failed_sync):
            self.refusal('passing instruction synchronization binding missing',default=True)
        for field,value in [('exactApprovalInstruction','I do not approve'),('approvalSource','')]:
            for default in (True,False):
                with self.subTest(field=field,default=default):
                    self.refusal('final plan approval lacks explicit owner instruction',
                                 lambda i,f:f.update({field:value}),default=default)
        for field,value in [('deadline','2027-06-30'),('owner','')]:
            for default in (True,False):
                with self.subTest(field=field,default=default):
                    def invalid_assessment(integration, final):
                        integration.update(state='integrated',completedOn='2026-11-22')
                        integration['sm3Assessment'][field] = value
                    self.refusal('SM-3 deadline/owner/source missing',invalid_assessment,default=default,full=default)

    def test_default_delivery_requires_the_packet_to_be_approved(self):
        read = V.read

        def candidate_receipt(root, path):
            return pending() if path == E/'approval.json' else read(root,path)

        with mock.patch.object(V, 'read', side_effect=candidate_receipt):
            self.refusal('completion requires fresh exact-byte successor approval',
                         resolved=False,default=True,full=True)

    def test_completion_requires_a_timezone_in_recorded_commit_dates(self):
        revision = data('integration.json')['rootIntegrationRevision']

        def naive_timestamp(repo, args, git):
            if repo == ROOT and args == ('show', '-s', '--format=%cI', revision):
                return b'2026-11-22T12:59:00'

        self.refusal('commit date missing: '+revision,git_mutation=naive_timestamp)

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
        def changed_working_instructions(integration,files,binding):
            files[ROOT/'CLAUDE.md'] = b'Changed working tree fixture'
        self.refusal('agent instructions differ',file_mutation=changed_working_instructions)
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
        inspection = data('upstream/manifest.json')['noChange'][0]
        repo = ROOT.parent/inspection['name']
        if not (repo/'.git').exists():
            repo = ROOT/'references'/('Hexalith.'+inspection['name'].capitalize())
        for checkout,ancestor,descendant,full in (
            (ROOT,V.INVENTORY_PUBLICATION,'origin/main',False),
            (ROOT,pin,'origin/main',False),
            (ROOT.parent/'aitools',ai,integration['aiToolsGitlink'],False),
            (repo,inspection['revision'],'origin/main',True),
        ):
            with self.subTest(ancestor=ancestor,descendant=descendant):
                message,git_mutation = missing_ancestry(checkout,ancestor,descendant)
                self.refusal(message,git_mutation=git_mutation,full=full)
        changed_link = '0'*40
        rule = 'hexalith-llm-instructions.md'
        self.refusal('committed AI.Tools gitlink missing',git_mutation=lambda repo,args,git:
                     f'100644 blob {changed_link}\t{V.AI_TOOLS_GITLINK}\n'.encode()
                     if args == ('ls-tree',pin,V.AI_TOOLS_GITLINK) else None)
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
        for field,value in (('base','0'*40),('publicationInstruction',''),
                            ('reviewedAfterSha256','0'*64),('patchSha256','0'*64)):
            def corrupt(i,f):
                projects = next(d for d in i['ownerIntegrations'] if d['name']=='projects')
                projects['rebasedFiles'][0][field] = value
            with self.subTest(rebase=field):
                self.refusal('rebased document approval or patch binding differs: _bmad-output/planning-artifacts/epics.md',corrupt)
        def change_base(i,f):
            projects = next(d for d in i['ownerIntegrations'] if d['name']=='projects')
            projects['rebasedFiles'][0]['beforeSha256'] = '0'*64
        self.refusal('rebased document base differs: _bmad-output/planning-artifacts/epics.md',change_base)
        def change_result(i,f):
            projects = next(d for d in i['ownerIntegrations'] if d['name']=='projects')
            projects['rebasedFiles'][0]['afterSha256'] = '0'*64
        self.refusal('rebased document differs from reviewed corrections: _bmad-output/planning-artifacts/epics.md',change_result)
        def extra_rebase(i,f):
            projects = next(d for d in i['ownerIntegrations'] if d['name']=='projects')
            projects['rebasedFiles'].append(dict(projects['rebasedFiles'][0],path='unapproved.md'))
        self.refusal('projects: invalid owner rebase footprint',extra_rebase)
        def duplicate_rebase(i,f):
            projects = next(d for d in i['ownerIntegrations'] if d['name']=='projects')
            projects['rebasedFiles'].append(projects['rebasedFiles'][0])
        self.refusal('projects: invalid owner rebase footprint',duplicate_rebase)
        def ai_tools_rebase(i,f):
            ai_delivery = next(d for d in i['ownerIntegrations'] if d['name']=='ai-tools')
            ai_delivery['rebasedFiles'] = [{'path':V.PLAN_PATH}]
        self.refusal('ai-tools: invalid owner rebase footprint',ai_tools_rebase)

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

    def test_current_projects_spine_accepts_the_adopted_ad29_guidance(self):
        path = '_bmad-output/planning-artifacts/architecture/architecture-projects-2026-07-15/ARCHITECTURE-SPINE.md'
        revision = '4d740a889787bb095b16303ed749ec7f165e5683'
        spine = recorded_git(ROOT.parent/'projects','show',revision+':'+path)
        self.assertEqual(self.run_binding(default=True,full=True,current_documents={('projects',path):spine}),
                         (0,VERIFIED,''))

    def test_current_main_reports_a_removed_passage_reintroduced_alongside_the_correction(self):
        repo = ROOT.parent/'memories'
        removed = b'## CLI (preview)'
        revision = next(row['commit'] for row in data('integration.json')['ownerIntegrations']
                        if row['name']=='memories')
        parent = recorded_git(repo,'show',revision+'^:README.md')
        delivered = recorded_git(repo,'show',revision+':README.md')
        self.assertIn(removed,parent.splitlines())
        self.assertNotIn(removed,delivered.splitlines())
        self.assertEqual(self.run_binding(default=True,full=True,
                         current_documents={('memories','README.md'):delivered+b'\n'+removed+b'\n'}),
                         (0,VERIFIED,'reported: memories: current main migration text drift: README.md\n'))

    def test_unreadable_current_planning_document_fails_when_main_lists_the_path(self):
        path = '_bmad-output/planning-artifacts/prd.md'
        eventstore = ROOT.parent/'eventstore'
        message = 'cannot read current Git object'
        def unreadable(checkout,args,git):
            if checkout == eventstore and args == ('show','origin/main:'+path):
                raise ValueError(message)
            if checkout == eventstore and args == ('ls-tree','--name-only','origin/main','--',path):
                return (path+'\n').encode()
        self.refusal(message,git_mutation=unreadable,default=True,full=True)

    def test_final_plan_requires_authority_and_capability_outcomes(self):
        self.refusal('exact plan bytes/publication binding missing',
                     plan_mutation=lambda plan:'Unexpected preface\n'+plan)
        cases = [
            (f"inventory_revision: '{V.INVENTORY_PUBLICATION}'",f"inventory_revision: '{'0'*40}'",
             'exact plan bytes/publication binding missing'),
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
        def overdue(outcome, reason):
            def change(integration, final):
                integration['completedOn'] = '2027-02-06'
                integration['sm3Assessment'].update(
                    assessedOn='2027-02-06',outcome=outcome,ownerReason=reason)
            return change
        with mock.patch.object(V,'date',Later):
            self.assertEqual(self.run_binding()[0],0)
            reason = 'Successor is scheduled and gates remain open.'
            self.assessment_refusal('overdue SM-3 requires explicit owner slip reason',overdue('slip',''))
            self.assessment_refusal('overdue SM-3 requires explicit owner slip reason',overdue('pending-not-met',reason))
            self.assertEqual(self.run_binding(overdue('slip',reason)),(0,VERIFIED,''))

    def test_sm3_requires_the_parties_gates_verdict_and_proof_of_owner_removal(self):
        label = next(row for row in data('labels.json')['rows'] if row['id']=='PS05')
        surface = label['surface']
        parties = ROOT.parent/'parties'
        delivered = next(d['commit'] for d in data('integration.json')['ownerIntegrations'] if d['name']=='parties')
        removal_revision = recorded_git(parties,'rev-parse',delivered+'^').decode().strip()
        snapshot_revision = recorded_git(ROOT,'rev-parse',V.INVENTORY_PUBLICATION+'^').decode().strip()
        def claim(surface,gates=None,with_verdict=False,tamper_result=False,words='approve',
                  receipt_changes=None,retirement_count=1):
            def mutate(integration,files,binding):
                receipt = {
                    'state':'retired','owner':'Fixture owner','source':'Fixture','surface':surface,'retiredOn':'2026-11-22',
                    'ownerRole':'Parties owning maintainer','exactApprovalInstruction':words,
                    'removalRevision':removal_revision,
                }
                receipt.update(receipt_changes or {})
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
                        verdict['approvedSnapshot'].update(commit=snapshot_revision,candidateHeadCommit=candidate,manifest=manifest,scanReceipt=scan)
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
                integration['sm3Assessment'].update(outcome='met',retirements=[retirement]*retirement_count)
            return mutate
        for exempt in ('Hexalith.FrontComposer.Cli','tools/MigrateEmbeddingVectors','Hexalith.ChatBot.Cli'):
            self.assessment_refusal('SM-3 requires an inventoried Legacy Server',file_mutation=claim(exempt))
        gates = dict.fromkeys([label['gate'],*(f'G{number:02}' for number in range(1,7))],{})
        self.assessment_refusal('SM-3 retirement does not bind every independent removal gate for '+surface,
                     file_mutation=claim(surface,gates))
        gates['restricted/destructive exposure conflict'] = {}
        self.assessment_refusal('SM-3 retirement does not bind every independent removal gate for '+surface,
                     file_mutation=claim(surface,list(gates)))
        project = 'src/Hexalith.Parties.Mcp/Hexalith.Parties.Mcp.csproj'
        self.assessment_refusal('SM-3 retirement lacks explicit owning-maintainer approval',
                     file_mutation=claim(surface,gates,words='I do not approve retiring Parties.'))
        self.assessment_refusal('SM-3 retirement lacks explicit owning-maintainer approval',
                     file_mutation=claim(surface,gates,receipt_changes={'ownerRole':'Unrelated maintainer'}))
        for field,value in [('state','planned'),('owner',''),('source','')]:
            with self.subTest(retirement_field=field):
                self.assessment_refusal('SM-3 retirement receipt lacks retired state or authority',
                             file_mutation=claim(surface,gates,receipt_changes={field:value}))
        self.assessment_refusal('SM-3 duplicate retirement receipts',file_mutation=claim(surface,gates,retirement_count=2))
        self.assessment_refusal('SM-3 retirement lacks owning repository removal revision',
                     file_mutation=claim(surface,gates,receipt_changes={'removalRevision':removal_revision[:8]}))
        self.assessment_refusal('SM-3 retirement must occur by its deadline and assessment',
                     file_mutation=claim(surface,gates,receipt_changes={'retiredOn':'2026-11-23'}))
        def after_deadline(integration,final):
            integration['completedOn'] = integration['sm3Assessment']['assessedOn'] = '2027-02-07'
        with mock.patch.object(V,'date',wraps=V.date) as clock:
            clock.today.return_value = V.date.fromisoformat('2027-02-08')
            self.assessment_refusal('SM-3 retirement must occur by its deadline and assessment',after_deadline,
                         file_mutation=claim(surface,gates,receipt_changes={'retiredOn':'2027-02-06'}))
        def future_removal(repo,args,git):
            if repo == parties and args == ('show','-s','--format=%cI',removal_revision):
                return b'2026-11-23T00:00:00+00:00'
        self.assessment_refusal('SM-3 removal revision postdates the retirement',
                     git_mutation=future_removal,file_mutation=claim(surface,gates))
        self.assessment_refusal('SM-3 retirement lacks owner removal of '+project,
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
        self.assessment_refusal('SM-3 owner revision renames or retains the retired project: '+project,
                     git_mutation=renamed,file_mutation=claim(surface,gates))
        for revision,presence in ((removal_revision+'^',b''),(removal_revision,project.encode()),
                                  ('origin/main',project.encode())):
            def tree_entry(repo,args,git):
                if repo == parties and args == ('ls-tree','--name-only',revision,'--',project):
                    return presence
                return removed(repo,args,git)
            with self.subTest(project_at=revision):
                self.assessment_refusal('SM-3 retirement lacks owner removal of '+project,
                             git_mutation=tree_entry,file_mutation=claim(surface,gates))
        def same_named_project(repo,args,git):
            if repo == parties and args == ('ls-tree','-r','--name-only','origin/main'):
                return ('moved/'+Path(project).name+'\n').encode()
            return removed(repo,args,git)
        self.assessment_refusal('SM-3 owner revision renames or retains the retired project: '+project,
                     git_mutation=same_named_project,file_mutation=claim(surface,gates))
        self.assessment_refusal('SM-3 Parties retirement lacks the successor Story 5.4 owner verdict',
                     git_mutation=removed,file_mutation=claim(surface,gates))
        self.assessment_refusal('SM-3 Parties verdict must approve a new evidence snapshot',
                     git_mutation=removed,file_mutation=claim(surface,gates,with_verdict='empty'))
        def complete_fixture(tamper=False, verdict_changes=None, gate_changes=None, scan_changes=None,
                             outcome='met', manifest_changes=None, gate_result=None, git_mutation=None,
                             scan_ref_changes=None, scan_digest=None):
            evidence = {}
            def write_fixture(integration,files,binding):
                claim(surface,gates,with_verdict=True,tamper_result=tamper)(integration,files,binding)
                assessment = integration['sm3Assessment']
                assessment['outcome'] = outcome
                retirement = json.loads(files[ROOT/'fixture-retirement.json'])
                verdict = json.loads(files[ROOT/'fixture-parties-verdict.json'])
                if verdict_changes:
                    verdict_changes(verdict)
                if gate_changes or gate_result is not None:
                    first_gate = next(iter(retirement['gateEvidence']))
                    proof = json.loads(files[ROOT/'fixture-gate-proof-0.json'])
                    proof.update(gate_changes or {})
                    if gate_result is not None:
                        proof['resultEvidence'] = binding('fixture-gate-result-0.txt',gate_result)
                    retirement['gateEvidence'][first_gate] = binding('fixture-gate-proof-0.json',B.serialized(proof))
                if scan_changes or manifest_changes or scan_ref_changes or scan_digest is not None:
                    scan = json.loads(files[ROOT/'fixture-scanReceipt.json'])
                    if manifest_changes:
                        manifest = json.loads(files[ROOT/'fixture-manifest.json'])
                        manifest_changes(manifest)
                        manifest_ref = binding('fixture-manifest.json',B.serialized(manifest))
                        verdict['approvedSnapshot']['manifest'] = manifest_ref
                        scan['files'] = [manifest_ref]
                    if scan_changes:
                        scan_changes(scan)
                    scan['manifestSha256'] = (scan_digest if scan_digest is not None else
                        B.sha(json.dumps(scan['files'],sort_keys=True,separators=(',',':')).encode()))
                    scan_ref = binding('fixture-scanReceipt.json',B.serialized(scan))
                    scan_ref.update(inputFileCount=1,manifestSha256=scan['manifestSha256'])
                    scan_ref.update(scan_ref_changes or {})
                    verdict['approvedSnapshot']['scanReceipt'] = scan_ref
                retirement['story54Verdict'] = binding('fixture-parties-verdict.json',B.serialized(verdict))
                assessment['retirements'] = [binding('fixture-retirement.json',B.serialized(retirement))]
                evidence.update({str(path.relative_to(ROOT)):raw for path,raw in files.items()
                                 if path.name in {'fixture-scanReceipt.json','fixture-manifest.json'}})
            def git_fixture(repo,args,git):
                if git_mutation:
                    changed = git_mutation(repo,args,git)
                    if changed is not None:
                        return changed
                if repo == ROOT and args[0]=='show' and args[1].startswith(snapshot_revision+':'):
                    path = args[1].split(':',1)[1]
                    if path in evidence:
                        return evidence[path]
                return removed(repo,args,git)
            return {'git_mutation':git_fixture,'file_mutation':write_fixture}
        self.assessment_refusal('artifact hash mismatch: fixture-gate-result-0.txt',
                     **complete_fixture(tamper=True))
        self.assertEqual(self.run_binding(**complete_fixture())[0],0)
        historical_verdict = 'story-5-4-owner-approval/owner-approval.json'
        previous = json.loads(recorded_git(ROOT,'show',B.BASELINE+':'+str(E.parent/historical_verdict)))
        previous_snapshot = previous['approvedSnapshot']['commit']
        for checkout,ancestor,descendant in ((parties,removal_revision,'origin/main'),
                                             (ROOT,previous_snapshot,snapshot_revision),
                                             (ROOT,snapshot_revision,'origin/main')):
            with self.subTest(ancestor=ancestor,descendant=descendant):
                message,git_mutation = missing_ancestry(checkout,ancestor,descendant)
                self.assessment_refusal(message,**complete_fixture(git_mutation=git_mutation))
        for field,value in [('approval','denied'),('verdict','retirement-blocked'),('retainedBlockingGapIds',['G01'])]:
            with self.subTest(verdict=field):
                self.assessment_refusal('SM-3 Parties retirement requires the successor retirement-ready owner verdict',
                             **complete_fixture(verdict_changes=lambda verdict:verdict['decision'].update({field:value})))
        self.assessment_refusal('SM-3 Parties retirement requires the successor retirement-ready owner verdict',
                     **complete_fixture(verdict_changes=lambda verdict:verdict.update(schema='unrelated/v1')))
        for field,value in [('role','Unrelated maintainer'),('source',''),('responseVerbatim','deny')]:
            with self.subTest(authority=field):
                self.assessment_refusal('SM-3 Parties retirement requires the successor retirement-ready owner verdict',
                             **complete_fixture(verdict_changes=lambda verdict:verdict['authority'].update({field:value})))
        for change in (lambda verdict:verdict['gapDispositions'][0].update(workStatus='open'),
                       lambda verdict:verdict['gapDispositions'][0].update(owner='Unrelated maintainer'),
                       lambda verdict:verdict['gapDispositions'].pop(),
                       lambda verdict:verdict['gapDispositions'].append(verdict['gapDispositions'][0])):
            self.assessment_refusal('SM-3 Parties verdict lacks resolved G01–G06 with their recorded owners',
                         **complete_fixture(verdict_changes=change))
        self.assessment_refusal('SM-3 Parties clean scan does not bind the approved successor manifest',
                     **complete_fixture(scan_changes=lambda scan:scan['files'][0].update(path='unrelated-manifest.json')))
        for field in ('fullLiveAccepted','fullV1Accepted'):
            with self.subTest(acceptance=field):
                self.assessment_refusal('SM-3 Parties successor manifest or clean scan is missing',
                             **complete_fixture(manifest_changes=lambda manifest:manifest['acceptanceEvidence'].update({field:False})))
        self.assessment_refusal('SM-3 Parties successor manifest or clean scan is missing',
                     **complete_fixture(scan_changes=lambda scan:scan.update(findings=[{'path':'fixture-manifest.json'}])))
        for change in (lambda manifest:manifest.update(schema='unrelated/v1'),
                       lambda manifest:manifest['ownerCheckpoint'].update(proposal='retirement-blocked'),
                       lambda manifest:manifest['candidate'].update(headCommit='0'*40)):
            self.assessment_refusal('SM-3 Parties successor manifest or clean scan is missing',
                         **complete_fixture(manifest_changes=change))
        for field,value in [('schema','unrelated/v1'),('result','findings'),
                            ('exitCode',1),('errors',['Fixture scan error'])]:
            with self.subTest(scan=field):
                self.assessment_refusal('SM-3 Parties successor manifest or clean scan is missing',
                             **complete_fixture(scan_changes=lambda scan:scan.update({field:value})))
        for case in (
            {'scan_changes':lambda scan:scan.update(fileCount=2)},
            {'scan_ref_changes':{'inputFileCount':2}},
            {'scan_ref_changes':{'manifestSha256':'0'*64}},
            {'scan_digest':'0'*64},
        ):
            with self.subTest(scan=case):
                self.assessment_refusal('SM-3 Parties clean scan does not bind the approved successor manifest',
                             **complete_fixture(**case))
        self.assessment_refusal('SM-3 Parties verdict must approve a new evidence snapshot',
                     **complete_fixture(verdict_changes=lambda verdict:verdict['approvedSnapshot'].update(commit=previous_snapshot)))
        for field,value in [('commit','short'),('candidateHeadCommit','short'),
                            ('candidateHeadCommit',previous['approvedSnapshot']['candidateHeadCommit'])]:
            with self.subTest(snapshot_field=field,value=value):
                self.assessment_refusal('SM-3 Parties verdict must approve a new evidence snapshot',
                             **complete_fixture(verdict_changes=lambda verdict:verdict['approvedSnapshot'].update({field:value})))
        for scope in ('Review the exact successor as retirement-ready.', 'Approve the exact successor.'):
            with self.subTest(scope=scope):
                self.assessment_refusal('SM-3 Parties owner did not expressly approve the committed successor as retirement-ready',
                             **complete_fixture(verdict_changes=lambda verdict:verdict.update(approvalScope=scope)))
        self.assessment_refusal('SM-3 Parties owner did not expressly approve the committed successor as retirement-ready',
                     **complete_fixture(verdict_changes=lambda verdict:verdict.update(
                         approvalScope='Approve a retirement-ready review with a retirement-blocked result.')))
        self.assessment_refusal('SM-3 Parties verdict postdates retirement',
                     **complete_fixture(verdict_changes=lambda verdict:verdict.update(recordedAtUtc='2026-11-23T00:00:00Z')))
        def late_snapshot(repo,args,git):
            if repo == ROOT and args == ('show','-s','--format=%cI',snapshot_revision):
                return b'2026-11-23T00:00:00+00:00'
        self.assessment_refusal('SM-3 Parties owner did not expressly approve the committed successor as retirement-ready',
                     **complete_fixture(git_mutation=late_snapshot))
        historical_date = previous['recordedAtUtc'][:10]
        self.assessment_refusal('SM-3 Parties owner did not expressly approve the committed successor as retirement-ready',
                     **complete_fixture(verdict_changes=lambda verdict:verdict.update(recordedAtUtc=historical_date),
                                        git_mutation=lambda repo,args,git: (historical_date+'T00:00:00+00:00').encode()
                                        if repo == ROOT and args == ('show','-s','--format=%cI',snapshot_revision) else None))
        for path in ('fixture-manifest.json','fixture-scanReceipt.json'):
            with self.subTest(snapshot=path):
                self.assessment_refusal('SM-3 Parties snapshot bytes differ from the committed evidence: '+path,
                             **complete_fixture(git_mutation=lambda repo,args,git:
                                 b'{}' if repo == ROOT and args == ('show',snapshot_revision+':'+path) else None))
        for field,value in [('surface','An unrelated server'),('gate','An unrelated gate'),
                            ('result','failed'),('removalRevision','0'*40),('owner',''),
                            ('source',''),('verifiedOn','2026-11-23')]:
            with self.subTest(gate_proof=field):
                self.assessment_refusal('SM-3 removal evidence does not prove '+next(iter(gates))+' for '+surface,
                             **complete_fixture(gate_changes={field:value}))
        self.assessment_refusal('SM-3 gate result evidence is empty: '+next(iter(gates)),**complete_fixture(gate_result=b''))
        for outcome in ('pending-not-met','slip'):
            self.assessment_refusal('SM-3 pending/slip must not claim retirement',**complete_fixture(outcome=outcome))
        self.assessment_refusal('pre-deadline unmet SM-3 remains pending',
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
    def test_live_ledger_matches_the_22_recorded_deferral_blockers(self):
        audit = data('deferral-dispositions.json')['entries']
        integration = data('integration.json')
        expected_ids = (
            '1c8ef2a87fc429cc cb256bc9ea051e97 cb5fc897454fbeac 52e621923be2365a '
            '97ff87a26c46ec8b e237a31da32a3ab2 ed8b36e5612e24e5 4fdf5ec4cd690c8d '
            '2825bc0195c0d54d ad73be0f7f31edc3 bcf011d9603aebe0 db3f193610c6db23 '
            '79dda498e65f04a7 7ea2341374f1a5cb cb83b6da301fa987 c92a970254e1caba '
            '260eb8ddd9199993 345a3ead37540792 7394777debdb0693 84668e94b642bd73 '
            'ddfd98571de3514a a03161fe049a33d2'
        ).split()
        changed = list(V.retained_deferral_changes(ROOT,audit))
        self.assertEqual(sorted(approved['id'] for approved,_ in changed),sorted(expected_ids))
        self.assertTrue(all(approved['sourceStatus'] != current['sourceStatus'] for approved,current in changed))
        self.assertEqual(integration.get('deferralResolutions',{}),{})
        self.assertIn(f'{len(expected_ids)} of the {len(audit)} approved audit entries still have changed ledger statuses '
                      f'after restoring ea9d3ee950934c10. The first refusal is {expected_ids[0]}. '
                      'No separate owner-approved resolutions are recorded.',integration['blockers'])
        text = (HERE/'verification.md').read_text()
        table = text.split('| Audited owner | Changed ledger entries awaiting resolution evidence |',1)[1].split('\n\n',1)[0]
        owners_by_id = [(entry_id,owner) for owner,ids in re.findall(r'^\| `([^`]+)` \| (.+) \|$',table,re.M)
                        for entry_id in re.findall(r'`([a-f0-9]{16})`',ids)]
        self.assertEqual(sorted(owners_by_id),sorted((approved['id'],approved['owner']) for approved,_ in changed))
        with self.assertRaises(ValueError) as refused:
            V.check_retained_deferrals(ROOT,integration,audit,V.date.fromisoformat('2026-11-26'))
        self.assertEqual(str(refused.exception),'audited deferral changed without a separate resolution: '+expected_ids[0])

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
        read_blob = prior.B.blob
        receipt_path = E.parent/'story-5-10/approval.json'
        published_artifact = next(iter(json.loads((ROOT/receipt_path).read_bytes())['artifacts']))
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

        def replay(candidate, *, changed_receipt=False, changed_publication=False, changed_reconstruction=False):
            readme_reads = 0

            def working_bytes(path):
                if path == ROOT/receipt_path and changed_receipt:
                    return read_bytes(path) + b'\n'
                return current[path] if path in current else read_bytes(path)

            def git_objects(repo, *args):
                if changed_publication and repo == ROOT and args == ('show', 'f'*40+':'+published_artifact):
                    return b'Unapproved historical artifact bytes'
                return historical_objects(repo, *args)

            def pinned_blob(root, owner, path):
                nonlocal readme_reads
                content = read_blob(root, owner, path)
                if changed_reconstruction and (owner, path) == ('chatbot', 'README.md'):
                    readme_reads += 1
                    if readme_reads == 2:
                        return b'# Unexpected content outside the compatibility section\n\n' + content
                return content

            with mock.patch.object(B,'git',side_effect=ssh_origin), \
                    mock.patch.object(prior.B,'git',side_effect=git_objects), \
                    mock.patch.object(prior.B,'blob',side_effect=pinned_blob), \
                    mock.patch.object(Path,'read_bytes',working_bytes):
                V.check_prior_delivery(ROOT,prior_module=prior,register=candidate)

        replay(register)
        self.assertEqual(set(historical),historical_reads)
        self.assertTrue(all('technical-tools inventory 1.0.4' in row['label']['text'] for row in data('labels.json')['rows']))
        wrong_repository = copy.deepcopy(register)
        wrong_repository['repositories'][0]['ownerCheckout'] = 'Unexpected owner checkout'
        cases = [
            (dict(register,state='candidate-pending-owner-approval-and-delivery'), {'changed_receipt': True},
             'completion requires integrated PS06/PS07/PS12/PS13/PS14 labels'),
            (register, {'changed_receipt': True}, 'historical Story 5.10 owner receipt differs'),
            (register, {'changed_publication': True}, 'historical Story 5.10 published artifact mismatch: '+published_artifact),
            (dict(register,repositories=[]), {}, 'historical Story 5.10 owner accounting mismatch'),
            (wrong_repository, {}, 'historical Story 5.10 repository binding mismatch'),
            (register, {'changed_reconstruction': True}, 'historical Story 5.10 README reconstruction mismatch'),
        ]
        for key in ('predecessor','priorRows','inventoryArtifacts','rows'):
            cases.append((dict(register, **{key: None}), {}, 'historical Story 5.10 '+key+' binding mismatch'))
        for candidate, fixture, message in cases:
            with self.subTest(message=message):
                with self.assertRaises(ValueError) as refused:
                    replay(candidate, **fixture)
                self.assertEqual(str(refused.exception), 'Story 5.10 prerequisite delivery incomplete: '+message)


if __name__ == '__main__':
    unittest.main()
