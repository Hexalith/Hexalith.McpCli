"""Exact-stream damaged-input tests and live-global guard-removal controls."""
import contextlib
import copy
import importlib.util
import io
import json
import os
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


V = load('verify58tests','verify_amendment.py')
L = load('labels58tests','verify_labels.py')
B = V.B
PASS = ('PASS: folders: 161 entries, pinned declarations/anchors/drift, AD-23 dispositions and complete hash chain\n'
        'PASS: owner decision: pending; candidate only; approval and integrated PS10/PS11 labels remain completion gates\n')
LABEL_PASS = 'PASS: Story 5.7 register chain; PS10/PS11 Folders 1.1.0 README-only citation patch; candidate only; owner approval and delivery pending\n'


def invoke(module,args=None):
    out,err = io.StringIO(),io.StringIO()
    with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
        code = module.main(args or [])
    return code,out.getvalue(),err.getvalue()


def pending_approval(receipt):
    """Derive a pending fixture without changing the real exact-byte approval."""
    receipt = copy.deepcopy(receipt)
    receipt['decision'] = 'pending'
    for key in ['approver','exactApprovalInstruction','approvalSource','approvedOn','rolesCovered']:
        receipt.pop(key,None)
    return receipt


def pending_inputs(root):
    """Reset only copied lifecycle state; candidate and authority bytes stay exact."""
    path = root/B.E/'approval.json'
    path.write_text(json.dumps(pending_approval(V.read_json(path)),indent=2)+'\n')
    path = root/B.E/'labels.json'
    register = V.read_json(path)
    register.update(state='candidate-pending-owner-approval-and-delivery',inventoryRevision=None,deliveryAuthorization=None)
    register['repository']['integration'] = None
    path.write_text(json.dumps(register,indent=2)+'\n')
    for path,key in [(root/B.SPEC,'status'),(root/B.ART/'sprint-status.yaml','  5-8-refresh-and-re-disposition-the-folders-inventory')]:
        workflow_status(path,key,'in-progress')


def workflow_status(path,key,value):
    text,count = re.subn(r'^'+re.escape(key)+r':[^\n]*',key+': '+value,path.read_text(),flags=re.M)
    if count != 1:
        raise AssertionError('fixture requires one workflow status: '+str(path))
    path.write_text(text)


def registered_owner():
    return V.read_json(ROOT/B.E/'labels.json')['repository']['ownerCheckout']


def pinned_observation(run):
    """Keep a pending fixture's current-owner observation at its historical base."""
    owner = registered_owner()
    def current(command,*args,**kwargs):
        if isinstance(command,list) and command[:3] == ['git','-C',owner] and command[3:] == ['show','origin/main:README.md']:
            command = [*command[:-1],B.LABEL_PIN+':README.md']
        return run(command,*args,**kwargs)
    return current


def fixture_process(script,*args):
    # Pin only the observational current-owner read in the child as well. Every
    # source/hash/ancestry guard still executes through the actual entrypoint.
    runner = '''import runpy, subprocess, sys
run = subprocess.run
pin = sys.argv[1]
owner = sys.argv[2]
def historical(command, *args, **kwargs):
    if isinstance(command, list) and command[:3] == ['git', '-C', owner] and command[3:] == ['show', 'origin/main:README.md']:
        command = [*command[:-1], pin + ':README.md']
    return run(command, *args, **kwargs)
subprocess.run = historical
script = sys.argv[3]
sys.argv = sys.argv[3:]
runpy.run_path(script, run_name='__main__')
'''
    return subprocess.run([sys.executable,'-I','-c',runner,B.LABEL_PIN,registered_owner(),str(script),*args],capture_output=True,text=True)


@contextlib.contextmanager
def workspace_view(*,pending=True):
    """Copy documentary inputs, sharing only read-only repository objects/source."""
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        for name in ['.git','.gitmodules','references','src']:
            (root/name).symlink_to(ROOT/name,target_is_directory=(ROOT/name).is_dir())
        art = root/B.ART; art.mkdir(parents=True)
        shutil.copytree(ROOT/B.AD,root/B.AD)
        for path in (ROOT/B.ART).iterdir():
            if path.is_file(): shutil.copyfile(path,art/path.name)
        (art/'evidence').mkdir()
        for story in (ROOT/B.ART/'evidence').iterdir():
            if story.name in {'story-5-2','story-5-8'}:
                shutil.copytree(story,art/'evidence'/story.name,ignore=shutil.ignore_patterns('__pycache__'))
            else:
                (art/'evidence'/story.name).symlink_to(story,target_is_directory=story.is_dir())
        if pending:
            pending_inputs(root)
        yield root


def tearDownModule():
    if __cached__ is not None:
        cached = Path(__cached__)
        cached.unlink(missing_ok=True)
        try: cached.parent.rmdir()
        except OSError: pass


class FixtureTests(unittest.TestCase):
    def test_pinned_observation_only_rewrites_registered_owner(self):
        owner = registered_owner()
        calls = []
        def run(command,**kwargs):
            calls.append((command,kwargs))
            return 'captured'
        observe = pinned_observation(run)
        for checkout in [owner,str(ROOT)]:
            self.assertEqual('captured',observe(['git','-C',checkout,'show','origin/main:README.md'],capture_output=True))
        self.assertEqual([
            (['git','-C',owner,'show',B.LABEL_PIN+':README.md'],{'capture_output':True}),
            (['git','-C',str(ROOT),'show','origin/main:README.md'],{'capture_output':True}),
        ],calls)

    def test_fixture_process_only_rewrites_registered_owner(self):
        owner = registered_owner()
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            git = directory/'git'
            git.write_text('#!'+sys.executable+'\nimport json, sys\nprint(json.dumps(sys.argv[1:]))\n')
            git.chmod(0o700)
            script = directory/'observe.py'
            script.write_text('import subprocess\nfor owner in '+repr([owner,str(ROOT)])+':\n'
                              '    result = subprocess.run(["git", "-C", owner, "show", "origin/main:README.md"], capture_output=True, text=True)\n'
                              '    print(result.stdout, end="")\n')
            with patch.dict(os.environ,{'PATH':str(directory)+os.pathsep+os.environ.get('PATH','')}):
                result = fixture_process(script)
        expected = '\n'.join(json.dumps(command) for command in [
            ['-C',owner,'show',B.LABEL_PIN+':README.md'],
            ['-C',str(ROOT),'show','origin/main:README.md'],
        ])+'\n'
        self.assertEqual((0,expected,''),(result.returncode,result.stdout,result.stderr))

    def test_pending_inputs_reject_duplicate_workflow_statuses(self):
        for path,key in [(B.SPEC,'status'),(B.ART/'sprint-status.yaml','  5-8-refresh-and-re-disposition-the-folders-inventory')]:
            with self.subTest(path=path),workspace_view(pending=False) as root:
                target = root/path
                duplicated = target.read_text()+'\n'+key+': done\n'
                target.write_text(duplicated)
                with self.assertRaisesRegex(AssertionError,re.escape('fixture requires one workflow status: '+str(target))):
                    pending_inputs(root)
                self.assertEqual(duplicated,target.read_text())

    def test_lifecycle_proof_binds_local_captures_and_replay(self):
        proof = load('lifecycle58proof','delivery/lifecycle-proof.py')
        run = subprocess.run
        command = [sys.executable,'-I','-m','unittest','discover','-v','-s',str(B.E),'-p','test_*.py']
        output,error = b'fixture stdout\n',b'fixture stderr\n'
        def child(arguments,**kwargs):
            if arguments == command:
                fixture = kwargs['cwd']
                self.assertEqual('approved',V.read_json(fixture/B.E/'approval.json')['decision'])
                self.assertEqual('integrated',V.read_json(fixture/B.E/'labels.json')['state'])
                self.assertTrue(V.completion_requested(fixture,False))
                self.assertEqual({'cwd':fixture,'capture_output':True},kwargs)
                return subprocess.CompletedProcess(arguments,0,output,error)
            return run(arguments,**kwargs)
        with tempfile.TemporaryDirectory() as temp,patch.object(subprocess,'run',side_effect=child),contextlib.redirect_stdout(io.StringIO()):
            delivery = Path(temp)
            self.assertEqual(0,proof.main(delivery=delivery))
            summary = V.read_json(delivery/'lifecycle-integrated.json')
            self.assertEqual({'command':command,'cwd':'.','cwdBase':'isolated synthetic lifecycle workspace created by this helper'},summary['child'])
            self.assertEqual({'command':['python3','-B','-I',str(B.E/'delivery/lifecycle-proof.py')],
                              'cwd':'.','cwdBase':'repository root containing this retained script'},summary['helper'])
            self.assertEqual('Suite independence from synthetic lifecycle metadata; real approved-completion is verified separately.',summary['claim'])
            self.assertTrue(summary['realInputsUnchanged'])
            for stream,data in [('stdout',output),('stderr',error)]:
                name = 'lifecycle-integrated.'+stream+'.txt'
                self.assertEqual(data,(delivery/name).read_bytes())
                self.assertEqual({'path':name,'sha256':B.sha(data)},summary[stream])
            self.assertNotIn(temp,json.dumps(summary))

    def test_lifecycle_proof_rejects_duplicate_workflow_statuses(self):
        proof = load('lifecycle58duplicates','delivery/lifecycle-proof.py')
        module = proof.load_tests(ROOT)
        workspace = module.workspace_view
        for path,key in [(B.SPEC,'status'),(B.ART/'sprint-status.yaml','  5-8-refresh-and-re-disposition-the-folders-inventory')]:
            @contextlib.contextmanager
            def duplicated_workspace(**kwargs):
                with workspace(**kwargs) as fixture:
                    target = fixture/path
                    duplicated = target.read_text()+'\n'+key+': done\n'
                    target.write_text(duplicated)
                    try:
                        yield fixture
                    finally:
                        self.assertEqual(duplicated,target.read_text())
            with self.subTest(path=path),tempfile.TemporaryDirectory() as temp,patch.object(proof,'load_tests',return_value=module),patch.object(module,'workspace_view',side_effect=duplicated_workspace):
                with self.assertRaisesRegex(AssertionError,'fixture requires one workflow status:'):
                    proof.main(delivery=Path(temp))
                self.assertEqual([],list(Path(temp).iterdir()))


class PendingCase(unittest.TestCase):
    def setUp(self):
        stack = contextlib.ExitStack()
        self.addCleanup(stack.close)
        self.root = stack.enter_context(workspace_view())
        for module in [V,L,L.V,B]:
            stack.enter_context(patch.object(module,'ROOT',self.root))
        stack.enter_context(patch.object(subprocess,'run',side_effect=pinned_observation(subprocess.run)))


class AmendmentTests(PendingCase):
    @classmethod
    def setUpClass(cls):
        cls.old = V.parse((ROOT/B.OLD).read_text())
        cls.new = V.parse((ROOT/B.NEW).read_text())
        mapping = V.read_json(ROOT/B.AD/'AD-23-capability-class-map.json')
        cls.inventory = next(i for i in mapping['inventories'] if i['path'] == str(B.OLD))
        cls.classes = {c['id']:c for c in mapping['classes']}
        cls.decl,cls.surface = B.declarations(ROOT),B.surfaces(ROOT)
        cls.receipt = pending_approval(V.read_json(HERE/'approval.json'))

    def changed(self,key,header,value):
        rows = copy.deepcopy(self.new)
        rows[key]['cells'][rows[key]['headers'].index(header)] = value
        return rows

    def rows(self,rows):
        V.check_rows(ROOT,self.old,rows,self.inventory,self.classes,self.decl)

    def run_check(self,check):
        def verify(*args):
            check()
            return 'pending',False
        with patch.object(V,'verify',side_effect=verify):
            return invoke(V)

    def reject(self,check,message):
        self.assertEqual((1,'','FAIL: '+message+'\n'),self.run_check(check))

    def guard(self,check,message,*,source_guard=False):
        """Disable the exact live global guard and prove this corruption then escapes.

        Rebinding a copied module or a caller-local helper would not affect the
        function-under-test globals and would make the positive control fail.
        """
        self.reject(check,message)
        original = V.require
        def removed(condition,actual):
            same_guard = actual.endswith(message.split(': ',2)[-1]) if source_guard else actual == message
            if not same_guard:
                original(condition,actual)
        self.assertIs(V.check_rows.__globals__,V.__dict__)
        with patch.object(V,'require',side_effect=removed):
            self.assertEqual((0,PASS,''),self.run_check(check))

    def test_real_candidate_and_completion_process_streams(self):
        for name,flags,expected in [
            ('verify_amendment.py',[],(0,PASS,'')),
            ('verify_labels.py',[],(0,LABEL_PASS,'')),
            ('verify_amendment.py',['--approved-completion'],(1,'','FAIL: completion requires exact-byte owner approval and covered Folders roles\n')),
            ('verify_labels.py',['--approved-completion'],(1,'','FAIL: completion requires exact-byte owner approval and covered Folders roles\n')),
        ]:
            with self.subTest(script=name,flags=flags):
                r = fixture_process(HERE/name,'--root',str(self.root),*flags)
                self.assertEqual(expected,(r.returncode,r.stdout,r.stderr))

    def test_deterministic_candidate_and_all_disposition_branches(self):
        self.assertEqual((ROOT/B.NEW).read_bytes(),B.candidate(ROOT))
        V.accounting(self.old,self.new,self.inventory)
        self.rows(self.new)
        actions = {k:V.fields(r)['Amendment disposition'] for k,r in self.new.items()}
        self.assertEqual({'replace','withdraw','defer'},set(actions.values()))
        self.assertEqual({'C01','C10','M01','M02','M04','M13','L10','L24','L25','L26'},B.K12)
        self.assertTrue(all(actions[k]=='defer' for k in B.K12|B.DIAGNOSTICS))
        self.assertEqual(39,sum(actions[k]=='replace' for k in actions if k[0] in 'CQ'))
        self.assertEqual({'V04','V09','V10','N01','N02'},{k for k,a in actions.items() if a=='withdraw'})
        for k in ('R01','R02','V01','V02','V03','V06','V07','V08'):
            self.assertEqual('replace',actions[k])

    def test_duplicate_and_damaged_rows_rejected_with_guard_controls(self):
        text = (ROOT/B.NEW).read_text()
        self.reject(lambda:V.parse(text+'\n'+self.new['M01']['text']), 'folders:M01: duplicate entry')
        damaged = text.replace(self.new['M01']['text'],self.new['M01']['text'].replace(' | defer |',' | |',1))
        self.reject(lambda:V.parse(damaged),'folders:M01: damaged row or empty cell')
        changed = copy.deepcopy(self.new); del changed['M01']
        self.guard(lambda:V.accounting(self.old,changed,self.inventory),'folders: 161-entry AD-23 accounting mismatch')

    def test_class_outcome_and_loss_owner_guards(self):
        for key,header,value,message in [
            ('M03','Capability class','K01','AD-23 class mismatch'),
            ('M03','Adopted outcome','confidential-ui-only','adopted outcome mismatch'),
            ('V09','Amendment rationale or gap','Accept human output only','required gap/loss or owning role changed'),
            ('V05','Amendment owner','Unassigned','required gap/loss or owning role changed'),
            ('M03','Approval reference','[A1](#a1)','A2 approval reference missing'),
            ('M03','Exact replacement','Invented.Commands.Type; wire invented; route REST','exact replacement type/wire/route or experience mismatch'),
        ]:
            with self.subTest(key=key,header=header):
                rows = self.changed(key,header,value)
                self.guard(lambda:self.rows(rows),f'folders:{key}: {message}')

    def test_replace_include_equivalence_and_each_required_action(self):
        rows = self.changed('V07','Amendment coverage','exclude')
        rows['V07']['cells'][2] = 'replace / exclude'
        self.guard(lambda:self.rows(rows),'folders:V07: include requires replace and replace requires include')
        for key,decision,message in [('V05','withdraw','required deferral changed'),('V04','defer','required withdrawal changed'),('V07','defer','eligible replacement disposition changed')]:
            with self.subTest(key=key):
                rows = self.changed(key,'Amendment disposition',decision)
                rows[key]['cells'][rows[key]['headers'].index('Amendment coverage')] = 'exclude'
                rows[key]['cells'][2] = decision+' / exclude'
                self.guard(lambda:self.rows(rows),f'folders:{key}: {message}')

    def test_k12_catalog_hold_diagnostics_and_empty_gap_owner(self):
        rows = self.changed('C01','Amendment rationale or gap','Owner decorates this so expose it')
        self.reject(lambda:self.rows(rows),'folders:C01: K12 reconciliation and catalog hold missing')
        for key in B.DIAGNOSTICS:
            with self.subTest(key=key):
                self.assertIn('C13 not-applicable',V.fields(self.new[key])['Amendment rationale or gap'])
        for header in ['Amendment rationale or gap','Amendment owner']:
            rows = self.changed('V05',header,' ')
            self.reject(lambda:self.rows(rows),'folders:V05: gap/rationale and owner required')

    def test_k12_and_diagnostic_disposition_guard_removal(self):
        for key,message in [('C01','K12 reconciliation and catalog hold missing'),('Q04','required deferral changed')]:
            with self.subTest(key=key):
                rows = self.changed(key,'Amendment disposition','replace')
                rows[key]['cells'][rows[key]['headers'].index('Amendment coverage')] = 'include'
                # Isolate this row's safety guard; accounting is exercised separately.
                self.guard(lambda:self.rows({key:rows[key]}),f'folders:{key}: {message}')

    def test_anchor_and_drift_guards(self):
        rows = self.changed('M03','Pinned evidence','`src/Hexalith.Folders.Mcp/Tools/FolderTools.cs:1`')
        self.guard(lambda:V.check_anchors(ROOT,self.old,rows,self.decl,self.surface),'folders:M03: pinned anchor identity mismatch')
        for key in ['M01','M21','M37','G1','G4','G5','V05','N04','M03']:
            with self.subTest(key=key):
                rows = self.changed(key,'Drift','unchanged' if key!='M03' else 'changed without detail')
                self.guard(lambda:V.check_drift(rows,self.decl),f'folders:{key}: source drift missing or incorrect')

    def test_decorated_type_wire_route_key_and_owner_eligibility_guards(self):
        for key,old,new,diagnostic in [
            ('C02','[HexalithCommand(','[Undecorated(', 'folders:M03: C02 replacement is absent, undecorated or owner-ineligible'),
            ('C02','public sealed record BindRepository(','public sealed record Invented(', 'folders:M03: C02 replacement is absent, undecorated or owner-ineligible'),
            ('C02','WireType = "Hexalith.Folders.Commands.BindRepository"','WireType = "Invented"','folders:M03: C02 decorated wire/domain mismatch'),
            ('C02','AggregateIdProperty = nameof(FolderId)','AggregateIdProperty = nameof(TenantId)','folders:M03: C02 aggregate route mismatch'),
            ('Q02','ProjectionType = "get-branch-ref-policy"','ProjectionType = "invented"','folders:M16: Q02 projection route mismatch'),
            ('C02','IdempotencyKeyProperty = nameof(IdempotencyKey)','IdempotencyKeyProperty = nameof(MessageId)','folders:M03: C02 required caller key declaration missing'),
        ]:
            with self.subTest(key=key,diagnostic=diagnostic):
                decl = copy.deepcopy(self.decl)
                self.assertIn(old,decl[key]['source'])
                decl[key]['source'] = decl[key]['source'].replace(old,new)
                self.guard(lambda:V.check_declarations(ROOT,self.old,self.new,decl,self.surface),diagnostic,source_guard=True)
        decl = copy.deepcopy(self.decl); decl['C02']['eligibility'] = 'excluded'
        self.reject(lambda:V.check_declarations(ROOT,self.old,self.new,decl,self.surface),'folders: 48-candidate/41-decoration owner set mismatch')

    def test_story_status_and_metadata_corrections(self):
        rows = self.changed('G4','Gap and required evidence','Folders Story 5.14: done at the pin.')
        self.guard(lambda:self.rows(rows),'folders:G4: story/status or corrected prerequisite premise mismatch')
        text = (ROOT/B.NEW).read_text().replace(B.PIN,'0'*40,1)
        self.guard(lambda:V.check_metadata(text),'folders: candidate metadata/pin/approval state mismatch')

    def approval(self,receipt,complete=False):
        V.check_approval(receipt,self.receipt['artifacts'],self.receipt['pinnedArtifacts'],self.receipt['amendment'],complete)

    def approved(self):
        return dict(copy.deepcopy(self.receipt),decision='approved',approver='Fixture owner',exactApprovalInstruction='Fixture approval',approvalSource='Test fixture only',approvedOn='2026-11-13',rolesCovered=B.ROLES[:])

    def test_pending_approved_role_and_chain_controls(self):
        self.approval(self.receipt)
        self.approval(self.approved(),True)
        cases = [('schemaVersion','9','approval schema/baseline/pin mismatch'),('artifacts',{},'approval artifact/hash-chain binding mismatch'),('pinnedArtifacts',{},'approval artifact/hash-chain binding mismatch'),('amendment',{},'approval predecessor/successor row delta mismatch'),('supersedes','A0','approval must supersede A1'),('requiredApprovalRoles',[],'approval required Folders roles mismatch'),('limits',[],'approval authority limits changed')]
        for key,value,message in cases:
            with self.subTest(field=key):
                r = copy.deepcopy(self.receipt); r[key] = value
                self.guard(lambda:self.approval(r),message)
        r = self.approved(); r['rolesCovered'] = ['Folders owning maintainer']
        self.guard(lambda:self.approval(r,True),'owner approval lacks required covered Folders roles')
        r = self.approved(); r['exactApprovalInstruction'] = ''
        self.guard(lambda:self.approval(r,True),'owner approval lacks identity, exact words, source or date')
        r = dict(self.receipt,approver='Invented')
        self.guard(lambda:self.approval(r),'pending receipt must not claim owner approval')
        self.guard(lambda:self.approval(self.receipt,True),'completion requires exact-byte owner approval and covered Folders roles')

    def test_builder_refuses_approved_packet_before_any_write(self):
        read = Path.read_bytes
        def approved(path,*args,**kwargs):
            return json.dumps(self.approved()).encode() if path == self.root/B.E/'approval.json' else read(path,*args,**kwargs)
        with patch.object(Path,'read_bytes',approved),patch.object(Path,'write_bytes',side_effect=AssertionError('unexpected write')):
            self.assertEqual((1,'','FAIL: refusing to overwrite an approved or unknown-state packet\n'),invoke(B))

    def test_source_drift_fields_are_proved_against_both_git_pins(self):
        V.check_source_drift(ROOT,self.surface)
        original = B.source
        path = 'src/Hexalith.Folders.Client/Generated/HexalithFoldersClient.g.cs'
        def missing(root,name,pin=B.PIN):
            text = original(root,name,pin)
            return text.replace('JsonProperty("expectedFileVersion"','JsonProperty("removedExpectedVersion"') if name == path and pin == B.PIN else text
        with patch.object(B,'source',side_effect=missing):
            self.guard(lambda:V.check_source_drift(ROOT,self.surface),'folders: source drift FileMutationRequest.expectedFileVersion is not evidenced at both pins')

    def test_owner_file_id_drift_semantics_and_both_pin_controls(self):
        for key in ['M01','M04','M13','L24','L25','L26','C10']:
            self.assertIn('ownerFileId',V.fields(self.new[key])['Drift'])
            self.assertIn('optional explicit owner incarnation',V.fields(self.new[key])['Drift'])
            self.assertIn('HexalithFoldersClient.g.cs:',V.fields(self.new[key])['Pinned evidence'])
        source = B.source
        path = 'src/Hexalith.Folders.Client/Generated/HexalithFoldersClient.g.cs'
        def missing(root,name,pin=B.PIN):
            text = source(root,name,pin)
            return text.replace('JsonProperty("ownerFileId"','JsonProperty("removedOwnerFileId"') if name == path and pin == B.PIN else text
        with patch.object(B,'source',side_effect=missing):
            self.guard(lambda:V.check_source_drift(ROOT,self.surface),'folders: source drift FileMutationRequest.ownerFileId is not evidenced at both pins')
        def required(root,name,pin=B.PIN):
            text = source(root,name,pin)
            return text.replace('JsonProperty("ownerFileId", Required = Newtonsoft.Json.Required.DisallowNull','JsonProperty("ownerFileId", Required = Newtonsoft.Json.Required.Always') if name == path and pin == B.PIN else text
        with patch.object(B,'source',side_effect=required):
            self.guard(lambda:V.check_source_drift(ROOT,self.surface),'folders: ownerFileId optional owner-incarnation semantics missing')

    def test_idempotency_key_own_jsonrequired_attribute_control(self):
        decl = copy.deepcopy(self.decl)
        # Other required properties deliberately retain their JsonRequired attributes.
        import re
        decl['C02']['source'],count = re.subn(r'(\[property:[^\]]*JsonPropertyName\("idempotencyKey"\)[^\]]*), JsonRequired(?=,)',r'\1',decl['C02']['source'],count=1)
        self.assertEqual(1,count)
        self.assertIn('JsonRequired',decl['C02']['source'])
        self.guard(lambda:V.check_declarations(ROOT,self.old,self.new,decl,self.surface),'folders:M03: C02 required caller key declaration missing',source_guard=True)

    def test_actual_client_calls_and_upload_kinds_are_checked(self):
        source = B.source
        cases = [
            ('src/Hexalith.Folders.Mcp/Tools/FolderTools.cs','client.GetBranchRefPolicyAsync(','client.GetCommitEvidenceAsync(','M16'),
            ('src/Hexalith.Folders.Mcp/Tools/FileTools.cs','=> Upload(pipeline, FileMutationRequestFileOperationKind.Add,','=> Upload(pipeline, FileMutationRequestFileOperationKind.Change,','M01'),
            ('src/Hexalith.Folders.Cli/Commands/File/FileCommand.cs','"Add a file (mutating).", FileMutationRequestFileOperationKind.Add','"Add a file (mutating).", FileMutationRequestFileOperationKind.Change','L24'),
            ('src/Hexalith.Folders.Cli/Commands/File/FileCommand.cs','client.RemoveFileAsync(','client.ChangeFileAsync(','L26'),
        ]
        for path,before,after,key in cases:
            with self.subTest(key=key):
                self.assertIn(before,source(ROOT,path))
                def changed(root,name,pin=B.PIN):
                    text = source(root,name,pin)
                    return text.replace(before,after,1) if name == path and pin == B.PIN else text
                with patch.object(B,'source',side_effect=changed):
                    surface = B.surfaces(ROOT)
                    self.guard(lambda:V.check_declarations(ROOT,self.old,self.new,self.decl,surface),f'folders:{key}: pinned client call/kind or operation-to-target mapping mismatch')
        # Verify the shared SDK helper's kind-to-client branch as well as each adapter.
        path = 'src/Hexalith.Folders.Client/Convenience/FoldersFileUploadExtensions.cs'
        def reversed_branch(root,name,pin=B.PIN):
            text = source(root,name,pin)
            return text.replace('.AddFileAsync(descriptor.FolderId,','.ChangeFileAsync(descriptor.FolderId,',1) if name == path and pin == B.PIN else text
        with patch.object(B,'source',side_effect=reversed_branch):
            operations = B.upload_operations(ROOT)
            self.assertEqual('ChangeFile',operations['Add'])
            self.reject(lambda:V.check_declarations(ROOT,self.old,self.new,self.decl,B.surfaces(ROOT)),'folders:M01: pinned client call/kind or operation-to-target mapping mismatch')

    def test_new_root_group_is_not_ignored(self):
        source = B.source
        path = 'src/Hexalith.Folders.Cli/CliApplication.cs'
        def extra(root,name,pin=B.PIN):
            text = source(root,name,pin)
            return text.replace('return root;','root.Subcommands.Add(NewGroupCommand.Create(pipeline, global));\n        return root;') if name == path and pin == B.PIN else text
        with patch.object(B,'source',side_effect=extra):
            self.reject(lambda:B.surfaces(ROOT),'unaccounted pinned CLI root registration: NewGroupCommand.Create(pipeline, global)')

    def test_protected_json_duplicates_and_shapes_fail_before_writes(self):
        cases = [
            ('approval.json','{"decision":"approved","decision":"pending"}','duplicate JSON member decision'),
            ('labels.json','{"state":"integrated","state":"candidate-pending-owner-approval-and-delivery","repository":{}}','duplicate JSON member state'),
            ('approval.json','null','JSON document must be an object: approval.json'),
            ('approval.json','[]','JSON document must be an object: approval.json'),
            ('labels.json','null','JSON document must be an object: labels.json'),
            ('labels.json','[]','JSON document must be an object: labels.json'),
        ]
        for name,data,message in cases:
            with self.subTest(name=name,data=data),tempfile.TemporaryDirectory() as temp:
                root = Path(temp);e = root/B.E;e.mkdir(parents=True)
                shutil.copyfile(HERE/'build_candidate.py',e/'build_candidate.py')
                (e/'approval.json').write_text('{"decision":"pending"}')
                (e/'labels.json').write_text('{"state":"candidate-pending-owner-approval-and-delivery","repository":{}}')
                (e/name).write_text(data)
                before = {p.name:p.read_bytes() for p in e.iterdir()}
                r = fixture_process(e/'build_candidate.py')
                self.assertEqual((1,'','FAIL: '+message+'\n'),(r.returncode,r.stdout,r.stderr))
                self.assertEqual(before,{p.name:p.read_bytes() for p in e.iterdir()})

    def test_malformed_json_shapes_use_controlled_entrypoint_streams(self):
        with workspace_view() as root:
            approval = (root/B.E/'approval.json').read_bytes()
            labels = (root/B.E/'labels.json').read_bytes()
            for name,values in [('approval.json',[None,[]]),('labels.json',[None,[]])]:
                for value in values:
                    for script in (['verify_amendment.py'] if name == 'approval.json' else ['verify_amendment.py','verify_labels.py']):
                        with self.subTest(name=name,value=value,script=script):
                            (root/B.E/name).write_text(json.dumps(value))
                            r = fixture_process(HERE/script,'--root',str(root))
                            self.assertEqual((1,'',f'FAIL: JSON document must be an object: {name}\n'),(r.returncode,r.stdout,r.stderr))
                    (root/B.E/name).write_bytes(approval if name == 'approval.json' else labels)
            for value in [None,[]]:
                data = json.loads(labels);data['repository'] = value
                (root/B.E/'labels.json').write_text(json.dumps(data))
                for script in ['verify_amendment.py','verify_labels.py','build_candidate.py']:
                    with self.subTest(repository=value,script=script):
                        # Builder obtains the isolated root from its own copied entrypoint.
                        args = ['--root',str(root)] if script != 'build_candidate.py' else []
                        r = fixture_process(root/B.E/script,*args)
                        self.assertEqual((1,'','FAIL: Folders label repository must be an object\n'),(r.returncode,r.stdout,r.stderr))

    def test_spec_and_sprint_done_default_entrypoint_controls(self):
        read,load_module = Path.read_text,V.load
        paths = [(self.root/B.SPEC,'status: done\n'),(self.root/B.ART/'sprint-status.yaml','  5-8-refresh-and-re-disposition-the-folders-inventory: done\n')]
        for path,done in paths:
            with self.subTest(path=path):
                def status(candidate,*args,**kwargs):
                    return done if candidate == path else read(candidate,*args,**kwargs)
                with patch.object(Path,'read_text',status),patch.object(V,'load',side_effect=lambda root,name,file:L if file == B.E/'verify_labels.py' else load_module(root,name,file)):
                    expected = (1,'','FAIL: completion requires exact-byte owner approval and covered Folders roles\n')
                    self.assertEqual(expected,invoke(V))
                    self.assertEqual(expected,invoke(L))
                    # Both imports of the same trigger are disabled, as deleting
                    # its source would affect the owner and standalone label gate.
                    with patch.object(V,'completion_requested',side_effect=lambda root,requested:requested),patch.object(L.V,'completion_requested',side_effect=lambda root,requested:requested):
                        self.assertEqual((0,PASS,''),invoke(V))
                        self.assertEqual((0,LABEL_PASS,''),invoke(L))

    def test_unresolvable_anchor_and_wrong_g_story_status_controls(self):
        rows = self.changed('M03','Pinned evidence','`src/Hexalith.Folders.Mcp/Tools/FolderTools.cs:999999`')
        rows['M03']['cells'][7] = V.fields(rows['M03'])['Pinned evidence']
        evidence = B.evidence
        with patch.object(B,'evidence',side_effect=lambda root,key,*args:'src/Hexalith.Folders.Mcp/Tools/FolderTools.cs:999999' if key == 'M03' else evidence(root,key,*args)):
            self.guard(lambda:V.check_anchors(ROOT,self.old,rows,self.decl,self.surface),'folders:M03: unresolvable pinned anchor src/Hexalith.Folders.Mcp/Tools/FolderTools.cs:999999')
        source = B.source
        def done(root,path,pin=B.PIN):
            text = source(root,path,pin)
            return text.replace('5-14-serve-folders-reads-through-gateway-query-handlers: backlog','5-14-serve-folders-reads-through-gateway-query-handlers: done') if path == '_bmad-output/implementation-artifacts/sprint-status.yaml' else text
        with patch.object(B,'source',side_effect=done):
            # Same logical status invariant is applied to G4 and G5.
            self.guard(lambda:V.check_anchors(ROOT,self.old,self.new,self.decl,self.surface),'folders:G4: Folders story status differs at pin',source_guard=True)

    def test_real_process_rejects_damaged_rows_and_invented_replacement(self):
        """Use a task-owned read-only view of repository objects and real entrypoints."""
        cases = [
            ('M03','Exact replacement','Invented.Commands.Type; wire Invented; route REST','folders:M03: exact replacement type/wire/route or experience mismatch'),
            ('M03','Capability class','K12','folders:M03: AD-23 class mismatch'),
            ('M03','Pinned evidence','`src/Hexalith.Folders.Mcp/Tools/FolderTools.cs:999999`','folders:M03: pinned anchor identity mismatch'),
        ]
        for key,header,value,message in cases:
            with self.subTest(field=header),workspace_view() as root:
                rows = self.changed(key,header,value)
                text = (ROOT/B.NEW).read_text().replace(self.new[key]['text'],'| '+' | '.join(rows[key]['cells'])+' |')
                (root/B.NEW).write_text(text)
                result = fixture_process(HERE/'verify_amendment.py','--root',str(root))
                self.assertEqual((1,'','FAIL: '+message+'\n'),(result.returncode,result.stdout,result.stderr))


class LabelTests(PendingCase):
    def setUp(self):
        super().setUp()
        self.register = L.read_json(self.root/B.E/'labels.json')

    def invoke_register(self,register,complete=False):
        read = L.read_json
        with patch.object(L,'read_json',side_effect=lambda path:register if path == self.root/B.E/'labels.json' else read(path)):
            return invoke(L,['--approved-completion'] if complete else [])

    def reject(self,register,message):
        self.assertEqual((1,'','FAIL: '+message+'\n'),self.invoke_register(register))

    def test_register_chain_coverage_hash_citation_and_no_false_delivery(self):
        self.assertEqual((0,LABEL_PASS,''),self.invoke_register(self.register))
        cases = [('predecessor',{},'Story 5.7 label predecessor chain mismatch'),('rows',self.register['rows'][:1],'Folders PS10/PS11 label coverage/duplicate mismatch'),('inventoryArtifacts',{},'labels bind wrong Folders inventory hash'),('inventoryRevision','1'*40,'pending label packet must not claim integration or delivery authorization')]
        for key,value,message in cases:
            with self.subTest(key=key):
                r = copy.deepcopy(self.register); r[key] = value
                self.reject(r,message)
        r = copy.deepcopy(self.register); r['rows'][0]['label']['text'] = 'invented replacement'
        self.reject(r,'PS10: version/hash/anchor/citation differs from Folders 1.1.0')
        r = copy.deepcopy(self.register); r['rows'][0]['gate'] = 'retired'
        self.reject(r,'PS10: surface, owner or removal gate changed')
        r = copy.deepcopy(self.register); r['repository']['patch']['sha256'] = '0'*64
        self.reject(r,'label artifact hash mismatch: '+str(B.E/'upstream/folders/README.patch'))

    def test_current_owner_drift_is_report_only(self):
        git = L.B.git
        def drift(repo,*args):
            return b'# Later owner revision without a compatibility section\n' if args == ('show','origin/main:README.md') else git(repo,*args)
        with patch.object(L.B,'git',side_effect=drift):
            self.assertEqual((0,LABEL_PASS,'reported: folders: current origin/main compatibility labels differ from prepared base candidate\n'),self.invoke_register(self.register))

    def test_label_chain_hash_and_citation_guard_removal(self):
        cases = []
        r = copy.deepcopy(self.register); r['predecessor'] = {}
        cases.append((r,'Story 5.7 label predecessor chain mismatch'))
        r = copy.deepcopy(self.register); r['inventoryArtifacts'] = {}
        cases.append((r,'labels bind wrong Folders inventory hash'))
        r = copy.deepcopy(self.register); r['rows'][0]['label']['text'] = r['rows'][0]['label']['text'].replace('Folders inventory 1.1.0','Folders inventory 1.0.0')
        cases.append((r,'PS10: version/hash/anchor/citation differs from Folders 1.1.0'))
        original = L.require
        self.assertIs(L.verify.__globals__,L.__dict__)
        for register,message in cases:
            with self.subTest(message=message):
                self.reject(register,message)
                def removed(condition,actual):
                    if actual != message: original(condition,actual)
                with patch.object(L,'require',side_effect=removed):
                    self.assertEqual((0,LABEL_PASS,''),self.invoke_register(register))

    def test_standalone_completion_does_not_bypass_owner_approval(self):
        self.assertEqual((1,'','FAIL: completion requires exact-byte owner approval and covered Folders roles\n'),self.invoke_register(self.register,True))

    def test_completion_requires_label_integration_after_owner_approval(self):
        with patch.object(L.V,'verify_owner_packet',return_value=None):
            self.assertEqual((1,'','FAIL: completion requires integrated Folders PS10/PS11 labels\n'),self.invoke_register(self.register,True))

    def test_completion_chain_and_exact_delivery_bytes(self):
        register = copy.deepcopy(self.register)
        register.update(state='integrated',inventoryRevision='2'*40,deliveryAuthorization={'exactWords':'Fixture delivery','source':'Test only','approvedOn':'2026-11-13'})
        register['repository']['integration'] = {'commit':'1'*40,'commitSha256':L.B.sha(b'fixture commit')}
        owner = Path(register['repository']['ownerCheckout'])
        git = L.B.git
        before = git(owner,'show',B.LABEL_PIN+':README.md')
        after = before.replace(L.checked_file(ROOT,register['repository']['before']),L.checked_file(ROOT,register['repository']['after']))
        def delivered(repo,*args):
            if repo == owner and args == ('show','1'*40+':README.md'): return after
            if repo == owner and args == ('show','origin/main:README.md'): return after
            if args[0] == 'merge-base': return b''
            if repo == owner and args[0] == 'diff': return b'README.md\n'
            if repo == owner and args[:2] == ('cat-file','commit'): return b'fixture commit'
            if repo == self.root and args[0] == 'show': return (self.root/args[1].split(':',1)[1]).read_bytes()
            return git(repo,*args)
        integrated = LABEL_PASS.replace('candidate only; owner approval and delivery pending','integrated delivery verified')
        with patch.object(L.V,'verify_owner_packet',return_value=None),patch.object(L.B,'git',side_effect=delivered):
            self.assertEqual((0,integrated,''),self.invoke_register(register,True))
            broken = copy.deepcopy(register); broken['deliveryAuthorization'] = None
            self.assertEqual((1,'','FAIL: completion requires separate explicit label delivery authorization\n'),self.invoke_register(broken,True))
            broken = copy.deepcopy(register); broken['inventoryRevision'] = '2'*12
            self.assertEqual((1,'','FAIL: completion requires canonical integrated inventory revision\n'),self.invoke_register(broken,True))
            def other_file(repo,*args):
                return b'README.md\nsrc/Changed.cs\n' if args[0] == 'diff' else delivered(repo,*args)
            with patch.object(L.B,'git',side_effect=other_file):
                self.assertEqual((1,'','FAIL: folders: delivered commit is not README-only\n'),self.invoke_register(register,True))

    @contextlib.contextmanager
    def existing_graph_fixture(self,*,owner_outside=False,inventory_outside=False):
        """Use existing commit objects and temporary refs; create no commits/messages.

        Candidate README/publication bytes are fixtures, while ancestry and changed
        paths are queried from real existing graphs. That keeps unpublished
        artifact validation independent from these graph-specific controls.
        """
        original = L.B.git
        owner_source = Path(self.register['repository']['ownerCheckout'])
        delivery = B.LABEL_PIN
        source_commit = original(owner_source,'rev-parse',delivery+'^').decode().strip()
        historical = original(owner_source,'rev-parse',source_commit+'^').decode().strip()
        inventory = original(ROOT,'rev-parse','HEAD').decode().strip()
        inventory_parent = original(ROOT,'rev-parse','HEAD^').decode().strip()
        expected,files = L.B.label_candidate(ROOT,L.B.sha((ROOT/B.NEW).read_bytes()))
        before = original(owner_source,'show',B.LABEL_PIN+':README.md')
        after = before.replace(files['README.before.section.md'],files['README.after.section.md'])
        with tempfile.TemporaryDirectory() as temp:
            def graph(name,source,current,url):
                directory = Path(temp)/name;directory.mkdir()
                original(directory,'init','--quiet')
                objects = Path(original(source,'rev-parse','--git-path','objects').decode().strip())
                if not objects.is_absolute(): objects = source/objects
                (directory/'.git/objects/info/alternates').write_text(str(objects.resolve())+'\n')
                original(directory,'remote','add','origin',url)
                original(directory,'update-ref','refs/remotes/origin/main',current)
                return directory
            owner = graph('folders',owner_source,source_commit if owner_outside else delivery,'https://github.com/Hexalith/Hexalith.Folders.git')
            published = graph('mcpcli',ROOT,inventory_parent if inventory_outside else inventory,'https://github.com/Hexalith/Hexalith.McpCli.git')
            register = copy.deepcopy(self.register)
            register.update(state='integrated',inventoryRevision=inventory,deliveryAuthorization={'exactWords':'Fixture delivery','source':'Test fixture only','approvedOn':'2026-11-13'})
            register['repository'].update(ownerCheckout=str(owner),baseRevision=historical,integration={'commit':delivery,'commitSha256':L.B.sha(original(owner,'cat-file','commit',delivery))})
            expected['repository']['baseRevision'] = historical
            def committed(repo,*args):
                if repo == owner and args == ('show',historical+':README.md'): return before
                if repo == owner and args in [('show',delivery+':README.md'),('show','origin/main:README.md')]: return after
                if repo == self.root and args[0] == 'merge-base': return original(published,*args)
                if repo == self.root and args[0] == 'show' and args[1].split(':',1)[0] in {inventory,'origin/main'}:
                    return (self.root/args[1].split(':',1)[1]).read_bytes()
                return original(repo,*args)
            with patch.object(L.B,'LABEL_PIN',historical),patch.object(L.B,'label_candidate',return_value=(expected,files)),patch.object(L.V,'verify_owner_packet',return_value=None):
                yield register,committed,owner,published,delivery,inventory,original

    def test_source_commit_before_valid_readme_delivery_is_allowed(self):
        with self.existing_graph_fixture() as (register,committed,owner,published,delivery,inventory,original):
            # Historical base -> delivery contains an intervening source change;
            # delivery parent -> delivery changes only README.md.
            self.assertNotEqual(['README.md'],original(owner,'diff','--name-only',register['repository']['baseRevision'],delivery).decode().splitlines())
            self.assertEqual(['README.md'],original(owner,'diff','--name-only',delivery+'^',delivery).decode().splitlines())
            with patch.object(L.B,'git',side_effect=committed):
                self.assertEqual((0,LABEL_PASS.replace('candidate only; owner approval and delivery pending','integrated delivery verified'),''),self.invoke_register(register,True))

    def test_real_owner_label_commit_outside_origin_main_and_guard_removal(self):
        with self.existing_graph_fixture(owner_outside=True) as (register,committed,owner,published,delivery,inventory,original):
            with patch.object(L.B,'git',side_effect=committed):
                self.assertEqual((1,'',f'FAIL: git merge-base --is-ancestor {delivery} origin/main failed: (no stderr)\n'),self.invoke_register(register,True))
            def removed(repo,*args):
                return b'' if repo == owner and args == ('merge-base','--is-ancestor',delivery,'origin/main') else committed(repo,*args)
            with patch.object(L.B,'git',side_effect=removed):
                self.assertEqual((0,LABEL_PASS.replace('candidate only; owner approval and delivery pending','integrated delivery verified'),''),self.invoke_register(register,True))

    def test_real_inventory_commit_outside_origin_main_and_guard_removal(self):
        with self.existing_graph_fixture(inventory_outside=True) as (register,committed,owner,published,delivery,inventory,original):
            with patch.object(L.B,'git',side_effect=committed):
                self.assertEqual((1,'',f'FAIL: git merge-base --is-ancestor {inventory} origin/main failed: (no stderr)\n'),self.invoke_register(register,True))
            def removed(repo,*args):
                return b'' if repo == self.root and args == ('merge-base','--is-ancestor',inventory,'origin/main') else committed(repo,*args)
            with patch.object(L.B,'git',side_effect=removed):
                self.assertEqual((0,LABEL_PASS.replace('candidate only; owner approval and delivery pending','integrated delivery verified'),''),self.invoke_register(register,True))


if __name__ == '__main__':
    unittest.main()
