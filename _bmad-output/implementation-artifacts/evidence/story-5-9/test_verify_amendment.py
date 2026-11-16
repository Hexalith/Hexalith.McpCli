"""Damaged-input, exact-stream, approved-lifecycle and live guard-removal tests."""
import contextlib
import copy
import importlib.util
import io
import inspect
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]



def load(name,filename):
    spec = importlib.util.spec_from_file_location(name,HERE/filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V = load('verify59tests','verify_amendment.py')
L = load('labels59tests','verify_labels.py')
B = V.B
L.V,L.B = V,B
PASS = ('PASS: projects: 56 entries; frontcomposer: 30 entries; pinned declarations/anchors/drift, AD-23 dispositions and hash chains\n'
        'PASS: owner decision: pending; candidate only; owner approval and integrated PS03/PS04/PS08/PS09 labels remain completion gates\n')
LABEL_PASS = 'PASS: Story 5.8 register chain; PS03/PS04/PS08/PS09 in two README-only patches; candidate only; approval and delivery pending\n'


def invoke(module,args):
    out,err = io.StringIO(),io.StringIO()
    # Share the read-only immutable-object cache; all checks still run.
    original = V.load
    def loader(root,name,path):
        if str(path) == str(B.E/'verify_labels.py'): return L
        return original(root,name,path)
    with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err),patch.object(V,'load',side_effect=loader):
        code = module.main(args)
    return code,out.getvalue(),err.getvalue()


def pending(receipt):
    """Build a pending test fixture without changing the real owner approval."""
    value = copy.deepcopy(receipt)
    value['decision'] = 'pending'
    for key in ['approver','exactApprovalInstruction','approvalSource','approvedOn','rolesCovered']:
        value.pop(key,None)
    return value


def pending_labels(register):
    """Isolate pre-delivery tests from the real integrated label receipt."""
    value = copy.deepcopy(register)
    value.update(state='candidate-pending-owner-approval-and-delivery',inventoryRevision=None,deliveryAuthorization=None)
    for repository in value['repositories']:
        repository['integration'] = None
    return value


@contextlib.contextmanager
def workspace():
    # TemporaryDirectory owns cleanup; callers run this suite under run-with-temp.
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        for name in ['.git','.gitmodules','references','src','tools','scripts']:
            (root/name).symlink_to(ROOT/name,target_is_directory=(ROOT/name).is_dir())
        shutil.copyfile(ROOT/'Directory.Build.props',root/'Directory.Build.props')
        art = root/B.ART
        art.mkdir(parents=True)
        for path in (ROOT/B.ART).iterdir():
            if path.is_file(): shutil.copyfile(path,art/path.name)
        (root/B.AD).parent.mkdir(parents=True,exist_ok=True)
        shutil.copytree(ROOT/B.AD,root/B.AD)
        (art/'evidence').mkdir()
        for story in (ROOT/B.ART/'evidence').iterdir():
            if story.name in {'story-5-2','story-5-9'}:
                shutil.copytree(story,art/'evidence'/story.name,ignore=shutil.ignore_patterns('__pycache__'))
            else:
                (art/'evidence'/story.name).symlink_to(story,target_is_directory=True)
        approval = root/B.E/'approval.json'
        approval.write_text(json.dumps(pending(V.read_json(approval)),indent=2)+'\n',encoding='utf-8')
        labels = root/B.E/'labels.json'
        labels.write_text(json.dumps(pending_labels(V.read_json(labels)),indent=2)+'\n',encoding='utf-8')
        for path,key,value in [(root/B.SPEC,'status',"'in-review'"),
                               (root/B.ART/'sprint-status.yaml','  5-9-refresh-and-re-disposition-projects-and-frontcomposer-invent','review')]:
            text,count = re.subn('^'+re.escape(key)+r':[^\n]*',key+': '+value,path.read_text(),flags=re.M)
            if count != 1: raise AssertionError('fixture requires exactly one '+key.strip())
            path.write_text(text,encoding='utf-8')
        yield root


def replace_cell(root,module,key,column,value):
    path = root/B.MODULES[module]['new']
    text = path.read_text(encoding='utf-8')
    row = B.parse(text,module)[key]
    cells = row['cells'][:]
    cells[row['headers'].index(column)] = value
    path.write_text(text.replace(row['text'],'| '+' | '.join(cells)+' |'),encoding='utf-8')


def approved(receipt):
    value = copy.deepcopy(receipt)
    value.update(decision='approved',approver='Fixture owner',exactApprovalInstruction='approve',
                 approvalSource='unit-test fixture only',approvedOn='2026-11-16',rolesCovered=B.ROLES[:])
    return value


def git_fixture(path,*args):
    result=subprocess.run(['git','-C',str(path),*args],capture_output=True,text=True)
    if result.returncode:
        raise AssertionError((args,result.stdout,result.stderr))
    return result.stdout.strip()


def divergent_history(path,before,after):
    path.mkdir()
    git_fixture(path,'init','-b','main')
    for key,value in [('user.name','Fixture'),('user.email','fixture@example.invalid'),
                      ('commit.gpgsign','false'),('core.hooksPath','/dev/null')]:
        git_fixture(path,'config',key,value)
    def write(files):
        for name,data in files.items():
            (path/name).parent.mkdir(parents=True,exist_ok=True)
            (path/name).write_bytes(data)
        git_fixture(path,'add','.')
    write(before)
    git_fixture(path,'commit','--quiet','-m','test: fixture base')
    git_fixture(path,'checkout','--quiet','-b','off-main')
    write(after)
    git_fixture(path,'commit','--quiet','--allow-empty','-m','test: off-main fixture')
    off=git_fixture(path,'rev-parse','HEAD')
    git_fixture(path,'checkout','--quiet','main')
    write(after)
    git_fixture(path,'commit','--quiet','--allow-empty','-m','test: main fixture')
    main=git_fixture(path,'rev-parse','HEAD')
    git_fixture(path,'update-ref','refs/remotes/origin/main',main)
    return main,off


@contextlib.contextmanager
def delivery_history(which):
    with tempfile.TemporaryDirectory() as temp:
        base=Path(temp)
        root,owner=base/'inventory',base/'owner'
        inventory={m['new']:(ROOT/m['new']).read_bytes() for m in B.MODULES.values()}
        inventory[B.E/'approval.json']=json.dumps(approved(V.read_json(ROOT/B.E/'approval.json'))).encode()
        inv_main,inv_off=divergent_history(root,inventory,inventory)
        before=B.blob(ROOT,'projects','README.md')
        register=V.read_json(ROOT/B.E/'labels.json')
        repository=next(r for r in register['repositories'] if r['name']=='projects')
        after=before.replace((ROOT/Path(repository['before']['path'])).read_bytes(),(ROOT/Path(repository['after']['path'])).read_bytes())
        owner_main,owner_off=divergent_history(owner,{Path('README.md'):before},{Path('README.md'):after})
        revision=owner_off if which=='owner' else owner_main
        repository.update(ownerCheckout=str(owner),integration=dict(commit=revision,commitSha256=B.sha(B.git(owner,'cat-file','commit',revision))))
        register.update(state='integrated',inventoryRevision=inv_off if which=='inventory' else inv_main,
                        deliveryAuthorization=dict(exactWords='authorize',source='fixture only',approvedOn='2026-11-16'))
        yield root,register,repository,before,after


def remove_guard(function,line):
    text=inspect.getsource(function)
    if text.count(line)!=1: raise AssertionError('expected one actual guard: '+line)
    namespace=dict(function.__globals__)
    exec(compile(text.replace(line,line[:len(line)-len(line.lstrip())]+'pass  # removed guard control'),'<removed-guard>','exec'),namespace)
    return namespace[function.__name__]


class PacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.decl = B.declarations(ROOT)
        cls.inputs = {}
        for module,m in B.MODULES.items():
            old = B.parse(B.predecessor_bytes(ROOT,module).decode('utf-8'),module)
            new = B.parse((ROOT/m['new']).read_text(encoding='utf-8'),module)
            entries,outcomes = B.class_entries(ROOT,module)
            cls.inputs[module] = old,new,entries,outcomes
        cls.expected = pending(V.read_json(ROOT/B.E/'approval.json'))

    def assert_failure(self,root,message,module=V,args=()):
        self.assertEqual((1,'','FAIL: '+message+'\n'),invoke(module,['--root',str(root),*args]))

    def test_projects_rest_drift_follows_actual_resource_cli_and_variant_callers(self):
        expected={
            **{k:['list'] for k in ['R01','L01']},
            **{k:['detail'] for k in ['R02','L02','L03']},
            **{k:['diagnostic'] for k in ['R03','R04','R06','R07','L06','L07','L08','L11','L14','L15','L16','L17','V06']},
            **{k:['list','diagnostic'] for k in ['R08','R09','R10','L09','L10','V03']},
            'M05':['refresh'],
            **{k:['refresh','diagnostic'] for k in ['L18','V05','V07']},
            **{k:['conversation','attachments'] for k in ['L04','L05','V02']},
            **{k:['list','detail','diagnostic'] for k in ['V01','V08','V10','V11']},
        }
        self.assertEqual(expected,B.PROJECTS_REST_PATHS)
        rows=B.parse(B.candidate(ROOT,'projects').decode(),'projects')
        for key,routes in expected.items():
            with self.subTest(key=key):
                self.assertIn('shared REST request preamble',V.fields(rows[key])['Drift'])
                anchors=B.rest_evidence(ROOT,key)
                self.assertEqual(len(routes)+2,len(anchors))
                for route,anchor in zip(routes,anchors):
                    path,line=anchor.rsplit(':',1)
                    self.assertEqual(B.REST_ENDPOINTS[route][0],path)
                    self.assertIn('BeginQueryRequest(httpContext,',B.source(ROOT,'projects',path).splitlines()[int(line)-1])
                self.assertTrue(all('`'+a+'`' in V.fields(rows[key])['Pinned evidence'] for a in anchors))
        for key in ['R05','R11','L12','L13','V04','V12']:
            self.assertEqual([],B.rest_evidence(ROOT,key))
            self.assertNotIn('ProjectQueryRequestPreamble.cs',V.fields(rows[key])['Pinned evidence'])
            self.assertTrue(V.fields(rows[key])['Drift'].startswith('unchanged:'))

    def test_frontcomposer_current_behavior_retains_supported_facts(self):
        rows=B.parse(B.candidate(ROOT,'frontcomposer').decode(),'frontcomposer')
        required={
            'V01':['exactly one canonical ULID correlationId/messageId','bounded in-memory transitions',
                   'current-tool admission','originating tenant/user','ownership','Acknowledgement URI is metadata','not a registered event stream'],
            'V02':['always requires an authenticated user','authorization','tenant tool/resource gates',
                   'allow-all gates are rejected outside Development'],
            'V03':['X-FrontComposer-Mcp-Key','invalid/multiple keys fail without claims fallback',
                   'explicit API-key authentication scheme','conflicting authenticated tenant/user identities',
                   'claimsSource: null','tenant/user only','no-key authenticated-claims path preserves source roles/claims',
                   'No erasure/key-rotation operation'],
        }
        for key,facts in required.items():
            for fact in facts:
                with self.subTest(key=key,fact=fact): self.assertIn(fact,rows[key]['cells'][1])
        self.assertNotIn('no originating tenant/user binding',rows['V01']['cells'][1])
        self.assertNotIn('takes precedence over authenticated claims',rows['V03']['cells'][1])

    def test_directory_props_is_bound_and_candidate_version_checked(self):
        self.assertIn(Path('Directory.Build.props'),B.AUTHORITIES)
        self.assertEqual(B.sha((ROOT/'Directory.Build.props').read_bytes()),self.expected['artifacts']['Directory.Build.props'])
        with workspace() as root:
            path=root/'Directory.Build.props'
            path.write_text(path.read_text().replace('>2.0.0-story66.3<','>2.0.0-wrong<'))
            with self.assertRaisesRegex(ValueError,'Directory.Build.props candidate version mismatch'):
                V.check_declarations(root,self.decl)
            self.assert_failure(root,'preserved authority changed: Directory.Build.props')

    def test_pending_labels_use_root_references_without_sibling_checkouts(self):
        real=B.git
        calls=[]
        sibling_paths={Path(r['ownerCheckout']) for r in V.read_json(ROOT/B.E/'labels.json')['repositories']}
        def without_siblings(checkout,*args):
            self.assertNotIn(Path(checkout),sibling_paths)
            calls.append((Path(checkout),args))
            return real(checkout,*args)
        with workspace() as root,patch.object(B,'git',side_effect=without_siblings):
            self.assertEqual((0,LABEL_PASS,''),invoke(L,['--root',str(root)]))
            for module in B.MODULES:
                self.assertIn((root/B.repo(module),('remote','get-url','origin')),calls)

    def test_approval_and_delivery_require_independent_affirmative_command_tokens(self):
        for instruction in ['do not approve','do not authorize','approve and authorize','authorize and approve','approve; authorize','approved','yes, approve']:
            receipt=approved(self.expected);receipt['exactApprovalInstruction']=instruction
            with self.subTest(approval=instruction),self.assertRaisesRegex(ValueError,'exact owner approve instruction'):
                V.check_approval(receipt,self.expected,True)
        register=V.read_json(ROOT/B.E/'labels.json');register['state']='integrated'
        repository=register['repositories'][0]
        for instruction in ['do not authorize','do not approve','approve and authorize','authorize and approve','approve; authorize','authorized','yes, authorize']:
            register['deliveryAuthorization']=dict(exactWords=instruction,source='fixture only',approvedOn='2026-11-16')
            with self.subTest(delivery=instruction),self.assertRaisesRegex(ValueError,'separate explicit authorize instruction'):
                L.check_delivery(ROOT,register,repository,b'',b'')
        V.check_approval(approved(self.expected),self.expected,True)

    def test_generator_interleaved_receipt_change_aborts_before_other_writes(self):
        for changed in ['approval.json','labels.json']:
            with self.subTest(receipt=changed),workspace() as root:
                writes=B.packet(root)
                snapshots={p:(root/p).read_bytes() for p in writes}
                real=B.packet
                def interleaved(checkout):
                    result=real(checkout)
                    path=checkout/B.E/changed
                    value=V.read_json(path)
                    if changed=='approval.json': value=approved(value)
                    else: value['deliveryAuthorization']={'exactWords':'authorize'}
                    path.write_text(json.dumps(value))
                    return result
                with patch.object(B,'ROOT',root),patch.object(B,'packet',side_effect=interleaved):
                    self.assertEqual((1,'','FAIL: refusing to overwrite receipt changed during packet derivation: '+changed+'\n'),invoke(B,[]))
                for path,data in snapshots.items():
                    if path!=B.E/changed: self.assertEqual(data,(root/path).read_bytes(),str(path))
                value=V.read_json(root/B.E/changed)
                self.assertEqual('approved',value['decision']) if changed=='approval.json' else self.assertIsNotNone(value['deliveryAuthorization'])

    def test_owner_off_origin_main_is_rejected_and_actual_guard_removal_detected(self):
        self.check_off_origin_main('owner',"    B.git(owner,'merge-base','--is-ancestor',revision,'origin/main')")

    def test_inventory_off_origin_main_is_rejected_and_actual_guard_removal_detected(self):
        self.check_off_origin_main('inventory',"    B.git(root,'merge-base','--is-ancestor',inv_revision,'origin/main')")

    def check_off_origin_main(self,which,line):
        with delivery_history(which) as arguments:
            def rejection():
                with self.assertRaisesRegex(ValueError,'git merge-base --is-ancestor .* origin/main failed'):
                    L.check_delivery(*arguments)
            rejection()
            without=remove_guard(L.check_delivery,line)
            with patch.object(L,'check_delivery',without):
                with self.assertRaises(AssertionError): rejection()

    def test_duplicate_workflow_fields_exact_streams_and_guard_removal(self):
        for kind in ['spec','sprint']:
            with self.subTest(kind=kind),workspace() as root:
                path,key=(root/B.SPEC,'status') if kind=='spec' else (root/B.ART/'sprint-status.yaml','  5-9-refresh-and-re-disposition-projects-and-frontcomposer-invent')
                path.write_text(path.read_text()+'\n'+key+': done\n')
                message='duplicate workflow status '+key.strip()
                for module in [V,L]:
                    self.assert_failure(root,message,module=module)
                    removed=remove_guard(V.completion_requested,"        require(len(found) <= 1,'duplicate workflow status '+key.strip())")
                    with patch.object(V,'completion_requested',removed):
                        with self.assertRaises(AssertionError): self.assert_failure(root,message,module=module)

    def test_pending_candidate_and_labels_exact_streams(self):
        with workspace() as root:
            self.assertEqual((0,PASS,''),invoke(V,['--root',str(root)]))
            self.assertEqual((0,LABEL_PASS,''),invoke(L,['--root',str(root)]))

    def test_real_entrypoints_and_completion_exact_streams(self):
        receipt = V.read_json(ROOT/B.E/'approval.json')
        completed = V.read_json(ROOT/B.E/'labels.json')['state'] == 'integrated' or V.completion_requested(ROOT,False)
        expected_pass = PASS.replace('owner decision: pending;',f'owner decision: {receipt["decision"]};')
        expected_labels = LABEL_PASS
        if completed:
            expected_pass = expected_pass.replace('candidate only; owner approval and integrated PS03/PS04/PS08/PS09 labels remain completion gates','approved completion verified')
            expected_labels = expected_labels.replace('candidate only; approval and delivery pending','integrated delivery verified')
        for name,expected in [('verify_amendment.py',expected_pass),('verify_labels.py',expected_labels)]:
            result = subprocess.run([sys.executable,'-I',str(HERE/name)],capture_output=True,text=True)
            self.assertEqual((0,expected,''),(result.returncode,result.stdout,result.stderr))
        result = subprocess.run([sys.executable,'-I',str(HERE/'verify_amendment.py'),'--approved-completion'],capture_output=True,text=True)
        expected_completion = (0,expected_pass,'') if completed else (1,'','FAIL: completion requires '+
            ('integrated PS03/PS04/PS08/PS09 labels' if receipt['decision'] == 'approved' else 'exact-byte owner approval and covered roles')+'\n')
        self.assertEqual(expected_completion,(result.returncode,result.stdout,result.stderr))

    def test_generator_is_byte_deterministic(self):
        first = B.packet(ROOT)
        self.assertEqual(first,B.packet(ROOT))
        for path,data in first.items():
            if path == B.E/'approval.json':
                self.assertEqual(json.loads(data),pending(V.read_json(ROOT/path)),str(path))
            elif path == B.E/'labels.json':
                self.assertEqual(json.loads(data),pending_labels(V.read_json(ROOT/path)),str(path))
            else:
                self.assertEqual(data,(ROOT/path).read_bytes(),str(path))

    def test_per_module_exact_accounting_and_every_disposition(self):
        for module,(old,new,entries,outcomes) in self.inputs.items():
            V.accounting(module,old,new,entries)
            V.check_rows(module,old,new,entries,outcomes,self.decl)
            self.assertEqual({'replace','defer','withdraw'} if module=='projects' else {'defer','withdraw'},
                             {V.fields(r)['Amendment disposition'] for r in new.values()})
            for key in old:
                damaged = copy.deepcopy(new); damaged.pop(key)
                with self.assertRaisesRegex(ValueError,re.escape(module+': predecessor/AD-23 entry accounting mismatch')):
                    V.accounting(module,old,damaged,entries)

    def test_duplicate_and_missing_rows_exact_streams(self):
        for module,key in [('projects','T01'),('frontcomposer','D13')]:
            with self.subTest(module=module),workspace() as root:
                m = B.MODULES[module]; path = root/m['new']; text = path.read_text()
                row = B.parse(text,module)[key]['text']
                path.write_text(text.replace(row,row+'\n'+row))
                self.assert_failure(root,f'{module}:{key}: duplicate entry')
            with workspace() as root:
                path = root/B.MODULES[module]['new']; text = path.read_text(); row = B.parse(text,module)[key]['text']
                path.write_text(text.replace(row+'\n',''))
                self.assert_failure(root,f"{module}: predecessor/AD-23 entry accounting mismatch (missing=['{key}'], extra=[])")

    def test_matrix_disposition_class_route_loss_gap_drift_and_gate_exact_streams(self):
        cases = [
            ('projects','R01','Amendment coverage','exclude','include requires replace and replace requires include'),
            ('projects','M01','Amendment disposition','defer','disposition contradicts class/approved target decision'),
            ('projects','T02','Exact replacement','Invented.Query; wire=wrong','exact decorated type/wire/Gateway route/eligibility or replacement experience mismatch'),
            ('projects','R05','Amendment rationale or gap','Owner rationale: docs. Replacement experience: README.','withdrawal lacks rationale, replacement experience or accepted loss'),
            ('projects','R06','Amendment rationale or gap','No contract. Owner Projects.','deferral lacks named gap or owner'),
            ('projects','V09','Amendment rationale or gap','Open gap: missing handler.','task/actor channel gap missing'),
            ('projects','V01','Amendment rationale or gap',B.READ_GAPS+' '+B.LOSSES,'K03/AD-20 Payload/Envelope conformity gap missing'),
            ('projects','G6','Amendment rationale or gap','Open gap: FK01 must move.','coupled FK01–FK04/K12/K13 retirement gate missing',True),
            ('frontcomposer','G4','Amendment rationale or gap','Open gap: FK01 must move.','coupled FK01–FK04/K12/K13 retirement gate missing',True),
            ('frontcomposer','C01','Amendment rationale or gap','Owner rationale: compiler. Replacement experience: retained. Accepted loss: migration scope.','K13 retained exemption missing'),
            ('projects','V05','Amendment rationale or gap','Owner rationale: restricted. Replacement experience: UI. Accepted loss: agent write.','K12 confidential UI evidence gate missing'),
            ('frontcomposer','V01','Drift','unchanged','drift status missing or incorrect'),
            ('frontcomposer','H02','Amendment disposition','replace','disposition contradicts class/approved target decision',True),
        ]
        for item in cases:
            module,key,column,value,message,*special = item
            with self.subTest(module=module,key=key,column=column),workspace() as root:
                replace_cell(root,module,key,column,value)
                if column == 'Amendment disposition':
                    replace_cell(root,module,key,'Amendment coverage','include' if value=='replace' else 'exclude')
                klass = self.inputs[module][2][key]
                # The coupled gate has an earlier exact-rationale guard by design.
                if key.startswith('G'): message='required owner/gap/loss changed'
                self.assert_failure(root,f'{module}:{key} ({klass}): {message}')

    def test_frontcomposer_invented_replace_without_parity_is_rejected(self):
        with workspace() as root:
            replace_cell(root,'frontcomposer','H02','Amendment disposition','replace')
            replace_cell(root,'frontcomposer','H02','Amendment coverage','include')
            self.assert_failure(root,'frontcomposer:H02 (K01): disposition contradicts class/approved target decision')

    def test_absent_or_undecorated_type_and_wire_domain_projection_guards(self):
        for key in B.TARGETS:
            for field,needle in [('source','[HexalithQuery('),('wire',self.decl[key]['wire']),('aggregate',self.decl[key]['aggregate'])]:
                with self.subTest(key=key,field=field):
                    decl = copy.deepcopy(self.decl)
                    decl[key][field] = decl[key][field].replace(needle,'wrong')
                    message = 'absent or undecorated replacement type' if field=='source' else 'decorated canonical name/wire/domain mismatch' if field=='wire' else 'aggregate or projection route mismatch'
                    with self.assertRaisesRegex(ValueError,re.escape('projects:'+key+': '+message)):
                        V.check_declarations(ROOT,decl)

    def test_anchor_identity_and_unresolvable_anchor(self):
        old,new,entries,outcomes = self.inputs['projects']
        damaged = copy.deepcopy(new)
        i = damaged['R01']['headers'].index('Pinned evidence')
        damaged['R01']['cells'][i] = '`src/Hexalith.Projects.Mcp/ProjectsMcpResourceReader.cs:999999`'
        with self.assertRaisesRegex(ValueError,'projects:R01: pinned anchor identity mismatch'):
            V.check_anchors(ROOT,'projects',old,damaged,self.decl)
        original = B.evidence
        with patch.object(B,'evidence',side_effect=lambda root,module,key,row,decl: ['src/Hexalith.Projects.Mcp/ProjectsMcpResourceReader.cs:999999'] if key=='R01' else original(root,module,key,row,decl)):
            with self.assertRaisesRegex(ValueError,'projects:R01: unresolvable anchor'):
                V.check_anchors(ROOT,'projects',old,damaged,self.decl)

    def test_protected_predecessor_and_authority_bytes(self):
        for module in B.MODULES:
            with workspace() as root:
                path = root/B.MODULES[module]['old']; path.write_bytes(path.read_bytes()+b'\n')
                self.assert_failure(root,'preserved authority changed: '+str(B.MODULES[module]['old']))

    def test_committed_predecessor_prose_keeps_exact_approved_snapshot(self):
        with workspace() as root:
            relative = B.MODULES['projects']['old']
            path = root/relative
            observed = path.read_bytes()+b'\nCommitted editorial fixture; no row changes.\n'
            path.write_bytes(observed)
            real = B.git
            def current_head(checkout,*args):
                if Path(checkout)==root and args==('show',f'HEAD:{relative}'): return observed
                return real(checkout,*args)
            with patch.object(B,'git',side_effect=current_head):
                self.assertEqual((0,PASS,''),invoke(V,['--root',str(root)]))
                self.assertEqual(self.expected['artifacts'][str(relative)],B.sha(B.predecessor_bytes(root,'projects')))
                self.assertEqual((ROOT/B.MODULES['projects']['new']).read_bytes(),B.candidate(root,'projects'))

    def test_committed_predecessor_row_changes_still_fail(self):
        with workspace() as root:
            relative = B.MODULES['projects']['old']
            path = root/relative
            row = B.parse(path.read_text(),'projects')['T01']['text']
            observed = path.read_text().replace(row,row.replace('projects.list','projects.changed',1)).encode()
            path.write_bytes(observed)
            real = B.git
            def current_head(checkout,*args):
                if Path(checkout)==root and args==('show',f'HEAD:{relative}'): return observed
                return real(checkout,*args)
            with patch.object(B,'git',side_effect=current_head):
                self.assert_failure(root,'projects: committed predecessor rows differ from the approved baseline')

    def test_approval_hash_delta_roles_and_pending_claims(self):
        V.check_approval(self.expected,self.expected,False)
        receipt = approved(self.expected)
        V.check_approval(receipt,self.expected,True)
        for key in ['artifacts','pinnedArtifacts','amendments','supersedes','requiredApprovalRoles','limits']:
            damaged = copy.deepcopy(receipt); damaged[key] = []
            with self.assertRaisesRegex(ValueError,'approval '+key+' hash/authority/delta binding mismatch'):
                V.check_approval(damaged,self.expected,False)
        for key in ['approver','exactApprovalInstruction','approvalSource','approvedOn','rolesCovered']:
            damaged = copy.deepcopy(receipt); damaged.pop(key)
            with self.assertRaises(ValueError): V.check_approval(damaged,self.expected,True)
        pending = copy.deepcopy(self.expected); pending['approver']='false owner'
        with self.assertRaisesRegex(ValueError,'pending receipt must not claim owner approval'):
            V.check_approval(pending,self.expected,False)

    def test_completion_triggers_from_spec_sprint_and_integrated_label(self):
        for kind in ['flag','spec','sprint','labels']:
            with self.subTest(kind=kind),workspace() as root:
                if kind == 'spec':
                    path=root/B.SPEC
                    text,count = re.subn(r'^status:[^\n]*','status: done',path.read_text(),flags=re.M)
                    self.assertEqual(1,count)
                    path.write_text(text)
                if kind == 'sprint':
                    path=root/B.ART/'sprint-status.yaml'
                    path.write_text(re.sub(r'^(  5-9-refresh-and-re-disposition-projects-and-frontcomposer-invent):[^\n]*',r'\1: done',path.read_text(),flags=re.M))
                if kind == 'labels':
                    path=root/B.E/'labels.json'; value=V.read_json(path);value['state']='integrated';path.write_text(json.dumps(value))
                self.assert_failure(root,'completion requires exact-byte owner approval and covered roles',args=['--approved-completion'] if kind=='flag' else [])

    def test_approved_owner_still_needs_integrated_labels(self):
        with workspace() as root:
            path=root/B.E/'approval.json';path.write_text(json.dumps(approved(V.read_json(path))))
            self.assert_failure(root,'completion requires integrated PS03/PS04/PS08/PS09 labels',args=['--approved-completion'])

    def test_label_chain_duplicate_hash_path_gate_and_non_readme_patch(self):
        for kind,message in [
            ('chain','Story 5.8 label predecessor chain mismatch'),
            ('rows','label row coverage/duplicate mismatch'),
            ('repository','label repository coverage/duplicate mismatch'),
            ('citation','PS08: successor citation/hash/anchor/surface/removal gate mismatch'),
            ('patch','label artifact hash mismatch: '+str(B.E/'upstream/projects/README.patch')),
            ('path','projects: owner/base/README patch register mismatch'),
        ]:
            with self.subTest(kind=kind),workspace() as root:
                path=root/B.E/'labels.json';value=V.read_json(path)
                if kind=='chain': value['predecessor']['sha256']='0'*64
                if kind=='rows': value['rows'].append(value['rows'][0])
                if kind=='repository': value['repositories'].append(value['repositories'][0])
                if kind=='citation': next(r for r in value['rows'] if r['id']=='PS08')['label']['text']='invented'
                if kind=='patch': (root/B.E/'upstream/projects/README.patch').write_text('--- a/other.txt\n+++ b/other.txt\n')
                if kind=='path': value['repositories'][0]['patch']['path']='../escape'
                path.write_text(json.dumps(value))
                self.assert_failure(root,message,module=L)

    def test_delivery_requires_independent_authorization_and_current_origin_main(self):
        expected,_=B.label_candidate(ROOT,{str(m['new']):B.sha((ROOT/m['new']).read_bytes()) for m in B.MODULES.values()})
        repository=expected['repositories'][0]
        before=B.blob(ROOT,'projects','README.md')
        after=before.replace((ROOT/Path(repository['before']['path'])).read_bytes(),(ROOT/Path(repository['after']['path'])).read_bytes())
        expected['state']='integrated'
        with self.assertRaisesRegex(ValueError,'separate explicit authorize instruction'):
            L.check_delivery(ROOT,expected,repository,before,after)
        expected['deliveryAuthorization']=dict(exactWords='authorize',source='test fixture',approvedOn='2026-11-16')
        with self.assertRaisesRegex(ValueError,'canonical integrated label commit'):
            L.check_delivery(ROOT,expected,repository,before,after)
        repository['integration']=dict(commit='a'*40,commitSha256=B.sha(b'commit'))
        def fake_git(root,*args):
            if args==('show','a'*40+':README.md'): return after
            if args==('merge-base','--is-ancestor','a'*40,'origin/main'): return b''
            if args==('diff','--name-only','a'*40+'^','a'*40): return b'README.md\n'
            if args==('cat-file','commit','a'*40): return b'commit'
            if args==('show','origin/main:README.md'): return before
            raise AssertionError(args)
        with patch.object(B,'git',side_effect=fake_git):
            with self.assertRaisesRegex(ValueError,'current origin/main does not cite exact successor labels'):
                L.check_delivery(ROOT,expected,repository,before,after)

    def test_synthetic_approved_and_authorized_completion_runs_every_delivery_check(self):
        with workspace() as root:
            approval_path=root/B.E/'approval.json'
            approval_path.write_text(json.dumps(approved(V.read_json(approval_path))))
            path=root/B.E/'labels.json';register=V.read_json(path)
            register.update(state='integrated',inventoryRevision='b'*40,
                            deliveryAuthorization=dict(exactWords='authorize',source='unit-test fixture only',approvedOn='2026-11-16'))
            readmes={}
            for i,repository in enumerate(register['repositories']):
                revision=('a' if i==0 else 'c')*40
                repository['integration']=dict(commit=revision,commitSha256=B.sha(('commit-'+str(i)).encode()))
                before=B.blob(root,repository['name'],'README.md')
                readmes[str(Path(repository['ownerCheckout']))]=(revision,before.replace((root/Path(repository['before']['path'])).read_bytes(),(root/Path(repository['after']['path'])).read_bytes()),('commit-'+str(i)).encode())
            path.write_text(json.dumps(register))
            real_git=B.git
            observed=[]
            def integrated_git(checkout,*args):
                owner=str(Path(checkout))
                if owner in readmes:
                    revision,after,commit=readmes[owner]
                    if args in [('show',revision+':README.md'),('show','origin/main:README.md')]: observed.append((owner,args));return after
                    if args==('cat-file','commit',revision): observed.append((owner,args));return commit
                    if args==('merge-base','--is-ancestor',revision,'origin/main'): observed.append((owner,args));return b''
                    if args==('diff','--name-only',revision+'^',revision): observed.append((owner,args));return b'README.md\n'
                if Path(checkout)==root:
                    if args==('merge-base','--is-ancestor','b'*40,'origin/main'): observed.append((owner,args));return b''
                    if len(args)==2 and args[0]=='show' and (args[1].startswith('b'*40+':') or args[1].startswith('origin/main:')):
                        observed.append((owner,args));return (root/args[1].split(':',1)[1]).read_bytes()
                return real_git(checkout,*args)
            expected=PASS.replace('owner decision: pending; candidate only; owner approval and integrated PS03/PS04/PS08/PS09 labels remain completion gates','owner decision: approved; approved completion verified')
            with patch.object(B,'git',side_effect=integrated_git):
                self.assertEqual((0,expected,''),invoke(V,['--root',str(root),'--approved-completion']))
            self.assertEqual(2,len({owner for owner,args in observed if args==('show','origin/main:README.md')}))
            for repository in register['repositories']:
                revision=repository['integration']['commit'];owner=repository['ownerCheckout']
                self.assertIn((owner,('cat-file','commit',revision)),observed)
                self.assertIn((owner,('diff','--name-only',revision+'^',revision)),observed)

    def test_completion_rejects_each_missing_role_and_each_missing_label_independently(self):
        for role in B.ROLES:
            with self.subTest(role=role),workspace() as root:
                path=root/B.E/'approval.json';value=approved(V.read_json(path));value['rolesCovered'].remove(role)
                path.write_text(json.dumps(value))
                self.assert_failure(root,'approval lacks explicitly covered single-maintainer roles',args=['--approved-completion'])
        for key in ['PS03','PS04','PS08','PS09']:
            with self.subTest(label=key),workspace() as root:
                path=root/B.E/'approval.json';path.write_text(json.dumps(approved(V.read_json(path))))
                path=root/B.E/'labels.json';value=V.read_json(path);value['rows']=[r for r in value['rows'] if r['id']!=key]
                path.write_text(json.dumps(value))
                self.assert_failure(root,'label row coverage/duplicate mismatch',args=['--approved-completion'])

    def test_generator_refuses_approved_authorized_and_symlink_outputs(self):
        for kind,message in [('approval','refusing to overwrite approved or unknown-state packet'),
                             ('authorization','refusing to overwrite authorized, integrated or unknown-state labels'),
                             ('symlink','refusing symlink output destination: '+str(B.MODULES['projects']['new']))]:
            with self.subTest(kind=kind),workspace() as root:
                if kind=='approval':
                    path=root/B.E/'approval.json';path.write_text(json.dumps(approved(V.read_json(path))))
                if kind=='authorization':
                    path=root/B.E/'labels.json';r=V.read_json(path);r['deliveryAuthorization']={'exactWords':'authorize'};path.write_text(json.dumps(r))
                if kind=='symlink':
                    path=root/B.MODULES['projects']['new'];path.unlink();path.symlink_to(ROOT/B.MODULES['projects']['new'])
                outputs=[*[m['new'] for m in B.MODULES.values()],B.E/'approval.json',B.E/'labels.json']
                outputs += [Path(r[k]['path']) for r in V.read_json(root/B.E/'labels.json')['repositories'] for k in ['before','after','patch']]
                snapshots={p:(root/p).read_bytes() for p in outputs}
                with patch.object(B,'ROOT',root):
                    if kind in {'approval','authorization'}:
                        with patch.object(B,'packet',side_effect=AssertionError('packet must not be derived or written')):
                            self.assertEqual((1,'','FAIL: '+message+'\n'),invoke(B,[]))
                    else:
                        self.assertEqual((1,'','FAIL: '+message+'\n'),invoke(B,[]))
                self.assertEqual(snapshots,{p:(root/p).read_bytes() for p in outputs})

    def test_duplicate_json_and_unknown_states(self):
        with workspace() as root:
            path=root/B.E/'approval.json';path.write_text('{"decision":"pending","decision":"approved"}')
            self.assert_failure(root,'duplicate JSON member decision')
        with workspace() as root:
            path=root/B.E/'labels.json';r=V.read_json(path);r['state']='unknown';path.write_text(json.dumps(r))
            self.assert_failure(root,'invalid label register state',module=L)

    def test_guard_removal_controls_detect_missing_accounting_approval_anchor_and_delivery_guards(self):
        # Disable each actual guard in its live module. The same rejection assertion
        # must fail, demonstrating that a missing guard is detected by this suite.
        def rejection(call,message):
            with self.assertRaisesRegex(ValueError,re.escape(message)): call()
        old,new,entries,outcomes=self.inputs['projects']
        damaged=copy.deepcopy(new);damaged.pop('T01')
        cases=[
            (V,'accounting',lambda:V.accounting('projects',old,damaged,entries),'projects: predecessor/AD-23 entry accounting mismatch'),
            (V,'check_approval',lambda:V.check_approval(self.expected,self.expected,True),'completion requires exact-byte owner approval and covered roles'),
            (V,'check_anchors',lambda:V.check_anchors(ROOT,'projects',old,{},self.decl),'anchor removal fixture'),
        ]
        # Anchor control uses an actual damaged cell, independently of regenerated bytes.
        changed=copy.deepcopy(new);i=changed['T01']['headers'].index('Pinned evidence');changed['T01']['cells'][i]='`missing:1`'
        cases[2]=(V,'check_anchors',lambda:V.check_anchors(ROOT,'projects',old,changed,self.decl),'projects:T01: pinned anchor identity mismatch')
        for module,name,call,message in cases:
            with self.subTest(guard=name):
                rejection(call,message)
                with patch.object(module,name,return_value=None):
                    with self.assertRaises(AssertionError): rejection(call,message)
        register=pending_labels(V.read_json(ROOT/B.E/'labels.json'));repository=register['repositories'][0]
        call=lambda:L.check_delivery(ROOT,register,repository,b'',b'')
        rejection(call,'completion requires integrated PS03/PS04/PS08/PS09 labels')
        with patch.object(L,'check_delivery',return_value=None):
            with self.assertRaises(AssertionError): rejection(call,'completion requires integrated PS03/PS04/PS08/PS09 labels')


if __name__ == '__main__':
    unittest.main()
