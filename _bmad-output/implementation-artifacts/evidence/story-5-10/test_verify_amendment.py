"""Exact-stream controls for candidate accounting, restrictions, approvals and label delivery."""
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


def load(name,file):
    spec = importlib.util.spec_from_file_location(name,HERE/file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V = load('verify510tests','verify_amendment.py')
L = load('labels510tests','verify_labels.py')
B = V.B
L.V,L.B = V,B
PASS = ('PASS: chatbot: 48 entries; memories: 55 entries (4 added PS14 modes); pinned anchors/drift, AD-23 dispositions and hash chains\n'
        'PASS: owner decision: pending; candidate only; owner approval and integrated PS06/PS07/PS12/PS13/PS14 labels remain completion gates\n')
APPROVED_PASS = (PASS.splitlines(keepends=True)[0]+
                 'PASS: owner decision: approved; candidate only; integrated PS06/PS07/PS12/PS13/PS14 labels remain a completion gate\n')
COMPLETION_PASS = PASS.splitlines(keepends=True)[0]+'PASS: owner decision: approved; approved completion verified\n'
LABEL_PREFIX = 'PASS: Story 5.9 register chain; PS06/PS07/PS12/PS13/PS14 in two README-only patches; '
LABEL_PASS = LABEL_PREFIX+'candidate only; owner decision: pending; approval and delivery integration pending\n'
LABEL_APPROVED_PASS = LABEL_PREFIX+'candidate only; owner decision: approved; delivery integration pending\n'
LABEL_COMPLETION_PASS = LABEL_PREFIX+'integrated delivery verified\n'


def invoke(module,args):
    out,err = io.StringIO(),io.StringIO()
    original = V.load
    def loader(root,name,path):
        return L if path == B.E/'verify_labels.py' else original(root,name,path)
    with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err),patch.object(V,'load',side_effect=loader):
        code = module.main(args)
    return code,out.getvalue(),err.getvalue()


@contextlib.contextmanager
def removed_source(module,name,snippet):
    """Remove one actual guard from a function while retaining its live entrypoint globals."""
    original = getattr(module,name)
    text = inspect.getsource(original)
    if text.count(snippet) != 1:
        raise AssertionError('guard-removal source must match exactly once: '+name)
    # Execute in the live module: downstream calls resolve the changed function,
    # rather than a detached copy whose internal globals still point at the original.
    try:
        exec(compile(text.replace(snippet,''),'<guard-removal:'+name+'>','exec'),module.__dict__)
        yield
    finally:
        setattr(module,name,original)


def pending_receipt(receipt):
    value=copy.deepcopy(receipt)
    value['decision']='pending'
    for key in ['approver','exactApprovalInstruction','approvalSource','approvedOn','rolesCovered']:
        value.pop(key,None)
    return value


def pending_labels(register):
    value=copy.deepcopy(register)
    value.update(state='candidate-pending-owner-approval-and-delivery',inventoryRevision=None,deliveryAuthorization=None)
    for repository in value['repositories']: repository['integration']=None
    return value


@contextlib.contextmanager
def workspace(*, pending=True):
    # TemporaryDirectory reliably cleans its scratch tree, including on test failure.
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
            if story.name in {'story-5-2','story-5-10'}:
                shutil.copytree(story,art/'evidence'/story.name,ignore=shutil.ignore_patterns('__pycache__'))
            else: (art/'evidence'/story.name).symlink_to(story,target_is_directory=True)
        if pending:
            for relative,normalize in [(B.E/'approval.json',pending_receipt),(B.E/'labels.json',pending_labels)]:
                path=root/relative
                path.write_text(json.dumps(normalize(V.read_json(path)),indent=2)+'\n')
        for path,key,value in [(root/B.SPEC,'status',"'in-progress'"),
                               (root/B.ART/'sprint-status.yaml','  5-10-refresh-and-re-disposition-chatbot-and-memories-inventories','in-progress')]:
            text,count = re.subn('^'+re.escape(key)+r':[^\n]*',key+': '+value,path.read_text(),flags=re.M)
            if count != 1: raise AssertionError('fixture requires exactly one '+key.strip())
            path.write_text(text)
        yield root


def replace_cell(root,module,key,column,value):
    path = root/B.MODULES[module]['new']
    text = path.read_text()
    row = B.parse(text,module)[key]
    cells = row['cells'][:]
    cells[row['headers'].index(column)] = value
    path.write_text(text.replace(row['text'],'| '+' | '.join(cells)+' |'))


def approved(receipt):
    value = copy.deepcopy(receipt)
    value.update(decision='approved',approver='Fixture owner',exactApprovalInstruction='approve',
                 approvalSource='unit-test fixture only',approvedOn='2026-11-16',rolesCovered=B.ROLES[:])
    return value


@contextlib.contextmanager
def integrated_workspace(corrupt=None,*,delivery_fault=None,moved_main=False):
    """Approved/delivered fixture; Git readback is synthetic, with no real receipt write."""
    with workspace(pending=True) as root:
        path=root/B.E/'approval.json';path.write_text(json.dumps(approved(V.read_json(path))))
        path=root/B.E/'labels.json';register=V.read_json(path)
        register.update(state='integrated',inventoryRevision='b'*40,
                        deliveryAuthorization=dict(exactWords='authorize',source='unit-test fixture only',approvedOn='2026-11-16'))
        readmes={}
        for i,r in enumerate(register['repositories']):
            revision=('a' if i==0 else 'c')*40;commit=('commit-'+str(i)).encode()
            r['integration']=dict(commit=revision,commitSha256=B.sha(commit))
            before=B.blob(root,r['name'],'README.md')
            parent=(b'Current owner build/test guidance.\n\n'+before) if moved_main else before
            after=parent.replace((root/r['before']['path']).read_bytes(),(root/r['after']['path']).read_bytes())
            readmes[r['ownerCheckout']]=(revision,parent,after,commit)
        path.write_text(json.dumps(register));real=B.git;observed=[]
        def integrated(checkout,*args):
            owner=str(Path(checkout))
            if owner in readmes:
                revision,parent,after,commit=readmes[owner];observed.append((owner,args))
                if args==('show',revision+'^:README.md'):
                    return parent.replace(b'## Legacy compatibility surfaces',b'## Legacy compatibility surfaces\nWrong parent section',1) if delivery_fault==('parent-section',owner) else parent
                if args==('show',revision+':README.md'):
                    if delivery_fault==('readme',owner): return after.replace(b'## Legacy compatibility surfaces',b'## Legacy compatibility surfaces\nWrong section bytes',1)
                    if delivery_fault==('outside-section',owner): return b'Unauthorized outside-section change\n'+after
                    return after
                if args==('show','origin/main:README.md'): return after
                if args==('cat-file','commit',revision): return commit
                if args==('merge-base','--is-ancestor',revision,'origin/main'): return b''
                if args==('diff','--name-only',revision+'^',revision): return b'README.md\n'
                if args==('remote','get-url','origin') and delivery_fault==('origin',owner):
                    return b'https://github.com/Hexalith/AnotherRepository.git\n'
            if Path(checkout)==root:
                if args==('merge-base','--is-ancestor','b'*40,'origin/main'):
                    observed.append((owner,args))
                    if delivery_fault==('inventory-ancestry',None):
                        raise ValueError('git merge-base --is-ancestor '+'b'*40+' origin/main failed: off-main inventory fixture')
                    return b''
                if len(args)==2 and args[0]=='show' and (args[1].startswith('b'*40+':') or args[1].startswith('origin/main:')):
                    observed.append((owner,args))
                    reference,path=args[1].split(':',1)
                    return b'corrupt published bytes' if corrupt==(reference,Path(path)) else (root/path).read_bytes()
            return real(checkout,*args)
        with patch.object(B,'git',side_effect=integrated),patch.object(V,'check_source_drift',return_value=None):
            yield root,register,observed


class AmendmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = {}
        for module,m in B.MODULES.items():
            old,new = B.parse(B.predecessor_bytes(ROOT,module).decode(),module),B.parse((ROOT/m['new']).read_text(),module)
            cls.inputs[module] = (old,new,*B.class_entries(ROOT,module))
        cls.expected = json.loads(B.packet(ROOT)[B.E/'approval.json'])

    def assert_failure(self,root,message,module=V,args=None):
        # Source drift has its own real baseline check; damaged documents do not
        # need to repeat hundreds of immutable Contracts Git reads for every case.
        with patch.object(V,'check_source_drift',return_value=None):
            self.assertEqual((1,'','FAIL: '+message+'\n'),invoke(module,['--root',str(root),*(args or [])]))

    def test_real_candidate_commands_have_exact_success_streams_and_completion_refusal(self):
        receipt,labels=V.read_json(ROOT/B.E/'approval.json'),V.read_json(ROOT/B.E/'labels.json')
        automatic=V.completion_requested(ROOT,False) or labels['state']=='integrated'
        def expected(completion):
            if completion and receipt['decision']=='pending':
                return (1,'','FAIL: completion requires exact-byte owner approval and covered roles\n')
            if completion and labels['state']!='integrated':
                return (1,'','FAIL: completion requires integrated PS06/PS07/PS12/PS13/PS14 labels\n')
            text = COMPLETION_PASS if completion else APPROVED_PASS if receipt['decision']=='approved' else PASS
            return (0,text,'')
        label_expected=(0,LABEL_COMPLETION_PASS if automatic else LABEL_APPROVED_PASS if receipt['decision']=='approved' else LABEL_PASS,'')
        if automatic and (receipt['decision']=='pending' or labels['state']!='integrated'): label_expected=expected(True)
        for file,args,result in [('verify_amendment.py',[],expected(automatic)),
                                 ('verify_labels.py',[],label_expected),
                                 ('verify_amendment.py',['--approved-completion'],expected(True))]:
            with self.subTest(file=file,args=args):
                process=subprocess.run([sys.executable,'-I',str(HERE/file),*args],capture_output=True,text=True)
                self.assertEqual(result,(process.returncode,process.stdout,process.stderr))

    def test_generator_is_deterministic_and_pending(self):
        first,second = B.packet(ROOT),B.packet(ROOT)
        self.assertEqual(first,second)
        self.assertEqual('pending',json.loads(first[B.E/'approval.json'])['decision'])
        for path,data in first.items():
            if path == B.E/'approval.json':
                V.check_approval(V.read_json(ROOT/path),json.loads(data),False)
            elif path == B.E/'labels.json':
                self.assertEqual(json.loads(data),pending_labels(V.read_json(ROOT/path)))
            else:
                self.assertEqual(data,(ROOT/path).read_bytes(),str(path))
        amendments = json.loads(first[B.E/'approval.json'])['amendments']
        self.assertEqual([48,51],[len(a['changedRows']) for a in amendments])
        self.assertEqual([[],['T01','T02','T03','T04']],[[r['id'] for r in a['addedRows']] for a in amendments])
        self.assertTrue(all(a['removedRows'] == [] for a in amendments))

    def test_readme_only_patches_apply_to_pinned_bytes_exactly(self):
        register=V.read_json(ROOT/B.E/'labels.json')
        for repository in register['repositories']:
            with self.subTest(repository=repository['name']),tempfile.TemporaryDirectory() as temp:
                directory=Path(temp)
                before=B.blob(ROOT,repository['name'],'README.md')
                expected=before.replace((ROOT/repository['before']['path']).read_bytes(),(ROOT/repository['after']['path']).read_bytes())
                (directory/'README.md').write_bytes(before)
                patch_bytes=(ROOT/repository['patch']['path']).read_bytes()
                for args in [['--check'],[]]:
                    result=subprocess.run(['git','apply',*args,'-'],input=patch_bytes,cwd=directory,capture_output=True)
                    self.assertEqual((0,b'',b''),(result.returncode,result.stdout,result.stderr))
                self.assertEqual(expected,(directory/'README.md').read_bytes())
                self.assertEqual(['README.md'],[p.name for p in directory.iterdir()])

    def test_corrected_source_facts_and_specific_openapi_semantics_are_retained(self):
        cases=[
            ('chatbot','M02','canonical_execution_unavailable'),
            ('chatbot','V08','not currently executable'),
            ('chatbot','V01','scheme-bound CreateHumanPolicy'),
            ('chatbot','V03','mixed-credential'),
            ('chatbot','M11','CanonicalRevision-bearing status never grants public retry'),
            ('chatbot','L11','malformed metadata becomes failed/generic_denial'),
            ('memories','V06','owned-<generation>-<guid>'),
            ('memories','V04','BM25 score descending then unique Redis key ascending'),
            ('memories','V05','invalid/stale documents consume raw positions'),
            ('memories','M03','returned neighbor edges exclude unpublished source versions'),
            ('memories','V08','package fallback configures fixed-domain'),
            ('memories','G3','absent/blank proof fails closed'),
        ]
        for module,key,text in cases:
            with self.subTest(module=module,key=key):
                row=self.inputs[module][1][key]
                self.assertIn(text,V.fields(row)['Amendment rationale or gap'])
                self.assertTrue(V.fields(row)['Drift'].startswith('changed:'))
        effect=V.fields(self.inputs['memories'][1]['T02'])['Effect']
        self.assertIn('Pre-cutover failures preserve active indexes',effect)
        self.assertIn('alias cutover precedes SetEmbeddingConfigAsync',effect)
        self.assertIn('manual rollback',effect)
        self.assertIn('RedisEmbeddingMigrationStore.cs',V.fields(self.inputs['memories'][1]['T02'])['Pinned evidence'])
        path='src/Hexalith.ChatBot.Contracts/openapi/hexalith.chatbot.v1.yaml'
        real=B.source
        def altered(root,module,file,pin=None):
            value=real(root,module,file,pin)
            if module=='chatbot' and file==path and pin is None:
                start=value.index('      operationId: GetOperationStatus')
                value=value[:start]+value[start:].replace('#/components/schemas/CommandId','#/components/schemas/OperationId',1)
            return value
        with patch.object(B,'source',side_effect=altered):
            with self.assertRaisesRegex(ValueError,'chatbot:M11: status/audit schema or authority semantic content changed'):
                B.evidence(ROOT,'chatbot','M11',self.inputs['chatbot'][0]['M11'])
        for key in ['M11','M12','L11','L12']:
            evidence=V.fields(self.inputs['chatbot'][1][key])['Pinned evidence']
            self.assertNotIn(path+':31`',evidence)

    def test_missing_duplicate_and_added_rows_include_governance_and_stubs(self):
        for module,key in [('chatbot','M01'),('chatbot','G1'),('chatbot','X03'),('memories','S04'),('memories','G6'),('memories','T04')]:
            with self.subTest(module=module,key=key),workspace(pending=True) as root:
                path = root/B.MODULES[module]['new'];row = B.parse(path.read_text(),module)[key]['text']
                path.write_text(path.read_text().replace(row+'\n',''))
                self.assert_failure(root,f"{module}: predecessor/AD-23 entry accounting mismatch (missing=['{key}'], extra=[])")
        with workspace(pending=True) as root:
            path=root/B.MODULES['memories']['new'];row=B.parse(path.read_text(),'memories')['S01']['text']
            path.write_text(path.read_text().replace(row,row+'\n'+row))
            self.assert_failure(root,'memories:S01: duplicate entry')
        with workspace(pending=True) as root:
            path=root/B.MODULES['chatbot']['new'];row=B.parse(path.read_text(),'chatbot')['X04']['text']
            path.write_text(path.read_text().replace(row,row+'\n'+row.replace('| X04 |','| X99 |',1)))
            self.assert_failure(root,"chatbot: predecessor/AD-23 entry accounting mismatch (missing=[], extra=['X99'])")

    def test_replace_include_and_plain_command_rest_openapi_readiness_are_rejected(self):
        for module,key in [('chatbot','M02'),('chatbot','V10'),('memories','M01'),('memories','T02')]:
            for column,value in [('Amendment disposition','replace'),('Amendment coverage','include')]:
                with self.subTest(module=module,key=key,column=column),workspace(pending=True) as root:
                    replace_cell(root,module,key,column,value)
                    klass=self.inputs[module][2][key]
                    self.assert_failure(root,f'{module}:{key} ({klass}): invented readiness; no decorated Gateway replacement at pin')
        for name in ['Plain Command ready','REST DTO ready','OpenAPI ready']:
            with self.subTest(name=name),workspace(pending=True) as root:
                replace_cell(root,'chatbot','M02','Exact replacement',name)
                self.assert_failure(root,'chatbot:M02 (K01): plain Command/REST DTO/OpenAPI cannot establish decorated readiness or replacement')

    def test_class_drift_missing_loss_gap_owner_drift_and_ui_gate(self):
        cases = [
            ('chatbot','V12','Capability class','K01','AD-23 class/outcome mismatch'),
            ('chatbot','V14','Amendment disposition','defer','disposition contradicts AD-23 class'),
            ('chatbot','X03','Amendment rationale or gap','Owner rationale: documentation. Replacement experience: README.','withdrawal lacks rationale, replacement experience or accepted loss'),
            ('memories','L10','Amendment rationale or gap','Owner rationale: restricted. Replacement experience: UI. Accepted loss: agent convenience.','confidential UI retirement prerequisite missing'),
            ('memories','T02','Amendment rationale or gap','Owner rationale: tooling. Replacement experience: retained. Accepted loss: scope.','retained owner-tooling exemption missing'),
            ('chatbot','M01','Amendment rationale or gap','Not ready.','deferral lacks named gap or owner'),
            ('chatbot','M01','Amendment owner','none','deferral lacks named gap or owner'),
            ('chatbot','M01','Amendment owner','-','required owner/gap/loss changed'),
            ('chatbot','V10','Drift','unchanged','drift status missing or incorrect'),
            ('memories','M01','Amendment rationale or gap','Open gap: Contracts missing.','module Contracts/handler/admission gap missing'),
        ]
        for module,key,column,value,message in cases:
            with self.subTest(module=module,key=key,column=column),workspace(pending=True) as root:
                replace_cell(root,module,key,column,value)
                self.assert_failure(root,f'{module}:{key} ({self.inputs[module][2][key]}): {message}')

    def test_every_identity_dependent_row_and_other_deferred_rows_retain_http_and_g2(self):
        old,new,entries,outcomes = self.inputs['memories']
        for key in [*sorted(B.IDENTITY),'L01','L03','L13','G2','G6','X01']:
            with self.subTest(key=key),workspace(pending=True) as root:
                why=V.fields(new[key])['Amendment rationale or gap']
                replace_cell(root,'memories',key,'Amendment rationale or gap',why.replace(B.HTTP_GATE,'HTTP alone is sufficient.'))
                self.assert_failure(root,f'memories:{key} ({entries[key]}): necessary-but-insufficient HTTP/user/tenant/administrative/semantic/release gate missing')
        with workspace(pending=True) as root:
            why=V.fields(new['L03'])['Amendment rationale or gap']
            replace_cell(root,'memories','L03','Amendment rationale or gap',why.replace('G2 remains open: ',''))
            self.assert_failure(root,'memories:L03 (K01): G2 identity gate missing')

    def test_context_k05_status_and_admin_scope_guards(self):
        for module,key,needle,message in [
            ('chatbot','M09',B.CONTEXT_GATE,'governed workflow or context-channel gap missing'),
            ('chatbot','M10','Module-side provider egress and pre-submit authority','K05 provider/pre-submit authority gap missing'),
            ('chatbot','V10','acceptance never proves completion','status Query/acceptance gap missing'),
            ('memories','L01','no checked admin-role','unscoped deployment metadata premise missing'),
            ('memories','L13','no checked admin-role','unscoped deployment metadata premise missing'),
        ]:
            with self.subTest(module=module,key=key),workspace(pending=True) as root:
                why=V.fields(self.inputs[module][1][key])['Amendment rationale or gap']
                replace_cell(root,module,key,'Amendment rationale or gap',why.replace(needle,'omitted'))
                self.assert_failure(root,f'{module}:{key} ({self.inputs[module][2][key]}): {message}')

    def test_every_ps14_mode_field_and_noninteractive_rule(self):
        for key in ['T01','T02','T03','T04']:
            for column in B.PS14_HEADERS[1:9]:
                with self.subTest(key=key,column=column),workspace(pending=True) as root:
                    replace_cell(root,'memories',key,column,'omitted')
                    self.assert_failure(root,f'memories:{key} (K14): PS14 required field changed: '+column)
        for key in ['T02','T03','T04']:
            text=V.fields(self.inputs['memories'][1][key])['Confirmation and refusal']
            self.assertIn('redirected input without --yes refuses',text)
            self.assertIn('--yes grants no agent authority',text)
        self.assertIn('No --yes or interactive confirmation required',V.fields(self.inputs['memories'][1]['T01'])['Confirmation and refusal'])

    def test_anchor_identity_unresolvable_and_prose_checks(self):
        with workspace(pending=True) as root:
            replace_cell(root,'chatbot','M01','Pinned evidence','`missing:999999`')
            self.assert_failure(root,'chatbot:M01: pinned anchor identity mismatch')
        old,new,_,_=self.inputs['chatbot'];changed=copy.deepcopy(new)
        changed['M01']['cells'][changed['M01']['headers'].index('Pinned evidence')]='`README.md:999999`'
        real=B.evidence
        with patch.object(B,'evidence',side_effect=lambda root,module,key,row: ['README.md:999999'] if key=='M01' else real(root,module,key,row)):
            with self.assertRaisesRegex(ValueError,'chatbot:M01: unresolvable anchor README.md:999999'):
                V.check_anchors(ROOT,'chatbot',old,changed)
        with workspace(pending=True) as root:
            path=root/B.MODULES['chatbot']['new'];path.write_bytes(path.read_bytes()+b'\nUnsupported prose.\n')
            self.assert_failure(root,'chatbot: prose/source premises differ from deterministic derivation')

    def test_protected_predecessors_and_authorities(self):
        for path in [B.MODULES['chatbot']['old'],B.MODULES['memories']['old'],B.AD/'AD-23-non-gateway-capability-classes.md',B.ART/'technical-tools-migration-inventory-v1.0.3.md']:
            with self.subTest(path=str(path)),workspace(pending=True) as root:
                item=root/path;item.write_bytes(item.read_bytes()+b'\n')
                self.assert_failure(root,'preserved authority changed: '+str(path))

    def test_mutable_authority_changes_affect_regeneration_only(self):
        with workspace(pending=True) as root:
            path=root/'Directory.Build.props'
            path.write_bytes(path.read_bytes()+b'\n<!-- later dependency update -->\n')
            before={path:(root/path).read_bytes() for path in B.packet(root)}
            with patch.object(V,'check_source_drift',return_value=None):
                self.assertEqual((0,PASS,''),invoke(V,['--root',str(root)]))
                self.assertEqual((0,LABEL_PASS,''),invoke(L,['--root',str(root)]))
            with patch.object(B,'ROOT',root):
                self.assertEqual((1,'','FAIL: preserved authority changed: Directory.Build.props\n'),invoke(B,[]))
            for path,data in before.items(): self.assertEqual(data,(root/path).read_bytes())

    def test_source_gitlink_decoration_and_registration_controls(self):
        V.check_source_drift(ROOT)
        real=B.git
        cases = [
            ('gitlink',lambda root,args: b'160000 commit '+b'0'*40+b'\treferences/Hexalith.ChatBot\n' if args==('ls-tree',B.BASELINE,str(B.repo('chatbot'))) else None,'chatbot: '+B.BASELINE+' root gitlink pin mismatch; halt'),
            ('decoration',lambda root,args: b'[HexalithQuery("invented")]' if args==('show',B.MODULES['chatbot']['pin']+':src/Hexalith.ChatBot.Contracts/ChatBotModuleInfo.cs') else None,'chatbot: unexpected decorated type at pin: src/Hexalith.ChatBot.Contracts/ChatBotModuleInfo.cs'),
        ]
        for name,alter,message in cases:
            def fake(root,*args):
                changed=alter(root,args)
                return changed if changed is not None else real(root,*args)
            with self.subTest(name=name),patch.object(B,'git',side_effect=fake):
                with self.assertRaisesRegex(ValueError,re.escape(message)): V.check_source_drift(ROOT)

    def test_every_source_premise_has_an_exact_stream_fake_git_and_guard_removal_control(self):
        c,m=B.MODULES['chatbot'],B.MODULES['memories']
        cp='src/Hexalith.ChatBot.Contracts/Hexalith.ChatBot.Contracts.csproj'
        mp='src/Hexalith.Memories.Contracts/Hexalith.Memories.Contracts.csproj'
        tools='src/Hexalith.ChatBot.Mcp/ChatBotMcpTools.cs'
        leaves='src/Hexalith.ChatBot.Cli/ChatBotCliCommands.cs'
        chost='src/Hexalith.ChatBot.Mcp/Program.cs'
        mhost='src/Hexalith.Memories.Mcp/McpCompositionRoot.cs'
        cases=[
            ('chatbot',('show',c['oldpin']+':'+cp),b'changed Contracts project','chatbot: Contracts project unexpectedly changed'),
            ('memories',('show',m['oldpin']+':'+mp),b'changed Contracts project','memories: Contracts project unexpectedly changed'),
            ('chatbot',('rev-parse',c['oldpin']+':'+B.OLD_SOURCE_TREE),b'0'*40+b'\n','chatbot: unpublished old src tree differs from published comparison'),
            ('chatbot',('merge-base','--is-ancestor',B.OLD_SOURCE_PIN,c['pin']),ValueError('git merge-base --is-ancestor '+B.OLD_SOURCE_PIN+' '+c['pin']+' failed: published comparison ancestry fixture'),'git merge-base --is-ancestor '+B.OLD_SOURCE_PIN+' '+c['pin']+' failed: published comparison ancestry fixture'),
            ('chatbot',('diff','--name-status',B.OLD_SOURCE_PIN,c['oldpin']),b'M\tsrc/other.cs\n','chatbot: historical source-only comparison premise changed'),
            ('chatbot',('diff','--name-only',c['oldpin'],c['pin'],'--',tools,leaves),b'changed.cs\n','chatbot: fixed tool/leaf declarations changed'),
            ('chatbot',('show',c['pin']+':'+tools),B.blob(ROOT,'chatbot',tools).replace(b'[McpServerTool(',b'[DifferentTool(',1),'chatbot: expected twelve registered tools'),
            ('chatbot',('show',c['pin']+':'+chost),B.blob(ROOT,'chatbot',chost)+b'\n// WithResources\n','chatbot: host tool/resource/prompt premise changed'),
            ('memories',('diff','--name-only',m['oldpin'],m['pin'],'--','src/Hexalith.Memories.Mcp/Tools','src/Hexalith.Memories.Cli/Commands','tools/MigrateEmbeddingVectors',B.SERVICE,B.EXITS),b'changed.cs\n','memories: fixed tools/leaves/stubs/operator source changed'),
            ('memories',('show',m['pin']+':'+mhost),B.blob(ROOT,'memories',mhost).replace(b'.WithTools<',b'.DifferentTools<',1),'memories: expected four registered tools and no resources/prompts'),
            ('memories',('show',m['pin']+':'+mhost),B.blob(ROOT,'memories',mhost).replace(b'ValidAlgorithms',b'OtherAlgorithms'),'memories: JWT algorithm drift missing'),
            ('memories',('show',m['pin']+':'+B.TOOL),B.blob(ROOT,'memories',B.TOOL).replace(b'selectedModes != 1',b'selectedModes != 2'),'memories: PS14 mode/confirmation/direct-access premise changed'),
            ('memories',('show',m['pin']+':'+B.SERVICE),B.blob(ROOT,'memories',B.SERVICE).replace(b'requires --tenant',b'requires another selector'),'memories: PS14 tenant/confirmation/effect premise changed'),
        ]
        source=inspect.getsource(V.check_source_drift)
        for module,args,value,message in cases:
            # Match the actual statement, including its indentation, rather than
            # replacing the checker with a stub that could never test a guard.
            snippet=("    B.git(root/B.repo('chatbot'),'merge-base','--is-ancestor',B.OLD_SOURCE_PIN,c['pin'])\n" if isinstance(value,ValueError)
                     else next(line for line in source.splitlines(keepends=True) if message.split(': ',1)[1] in line))
            with self.subTest(premise=message),workspace(pending=True) as root:
                real=B.git
                def fake(checkout,*actual):
                    if Path(checkout)==root/B.repo(module) and actual==args:
                        if isinstance(value,ValueError): raise value
                        return value
                    return real(checkout,*actual)
                expected=(1,'','FAIL: '+message+'\n')
                with patch.object(B,'git',side_effect=fake),patch.dict(B.RAW,{},clear=True):
                    self.assertEqual(expected,invoke(V,['--root',str(root)]))
                    with removed_source(V,'check_source_drift',snippet):
                        with self.assertRaises(AssertionError):
                            self.assertEqual(expected,invoke(V,['--root',str(root)]))

    def test_current_gitlink_moves_and_local_main_lag_affect_regeneration_only(self):
        for kind in ['gitlink','lag']:
            with self.subTest(kind=kind),workspace(pending=True) as root:
                real=B.git;observed=[]
                def moved(checkout,*args):
                    if Path(checkout)==root:
                        observed.append(args)
                        if args==('ls-tree','HEAD',str(B.repo('chatbot'))) and kind=='gitlink':
                            return b'160000 commit '+b'0'*40+b'\treferences/Hexalith.ChatBot\n'
                        if args==('merge-base','--is-ancestor','origin/main','HEAD') and kind=='lag':
                            raise ValueError('git merge-base --is-ancestor origin/main HEAD failed: local main lags fixture')
                    return real(checkout,*args)
                with patch.object(B,'git',side_effect=moved):
                    self.assertEqual((0,PASS,''),invoke(V,['--root',str(root)]))
                    self.assertEqual((0,LABEL_PASS,''),invoke(L,['--root',str(root)]))
                    self.assertNotIn(('ls-tree','HEAD',str(B.repo('chatbot'))),observed)
                    self.assertNotIn(('merge-base','--is-ancestor','origin/main','HEAD'),observed)
                    for name,m in B.MODULES.items():
                        self.assertIn(('ls-tree',B.BASELINE,str(B.repo(name))),observed)
                    message=('chatbot: HEAD root gitlink pin mismatch; halt' if kind=='gitlink'
                             else 'git merge-base --is-ancestor origin/main HEAD failed: local main lags fixture')
                    before={path:(root/path).read_bytes() for path in B.packet(root)}
                    with patch.object(B,'ROOT',root):
                        self.assertEqual((1,'','FAIL: '+message+'\n'),invoke(B,[]))
                    for path,data in before.items(): self.assertEqual(data,(root/path).read_bytes())

    def test_baseline_gitlinks_and_published_pin_ancestry_remain_required(self):
        for name,m in B.MODULES.items():
            for kind in ['baseline','pin-ancestry']:
                with self.subTest(module=name,kind=kind),workspace(pending=True) as root:
                    real=B.git
                    message=(f'{name}: {B.BASELINE} root gitlink pin mismatch; halt' if kind=='baseline'
                             else f'git merge-base --is-ancestor {m["pin"]} origin/main failed: unpublished pin fixture')
                    def invalid(checkout,*args):
                        if kind=='baseline' and Path(checkout)==root and args==('ls-tree',B.BASELINE,str(B.repo(name))):
                            return b'160000 commit '+b'0'*40+b'\t'+str(B.repo(name)).encode()+b'\n'
                        if kind=='pin-ancestry' and Path(checkout)==root/B.repo(name) and args==('merge-base','--is-ancestor',m['pin'],'origin/main'):
                            raise ValueError(message)
                        return real(checkout,*args)
                    with patch.object(B,'git',side_effect=invalid):
                        self.assertEqual((1,'','FAIL: '+message+'\n'),invoke(V,['--root',str(root)]))

    def test_receipt_bindings_roles_exact_words_and_pending_claims(self):
        V.check_approval(self.expected,self.expected,False)
        value=approved(self.expected);V.check_approval(value,self.expected,True)
        for field in ['artifacts','pinnedArtifacts','amendments','supersedes','requiredApprovalRoles','sourceRevisions']:
            changed=copy.deepcopy(value);changed[field]=[]
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'approval '+field+' hash/authority/delta binding mismatch'):
                V.check_approval(changed,self.expected,False)
        for role in B.ROLES:
            changed=copy.deepcopy(value);changed['rolesCovered'].remove(role)
            with self.subTest(role=role),self.assertRaisesRegex(ValueError,'approval lacks explicitly covered single-maintainer roles'):
                V.check_approval(changed,self.expected,True)
        for words in ['approve and stop','approved','authorize','approve later']:
            changed=copy.deepcopy(value);changed['exactApprovalInstruction']=words
            with self.subTest(words=words),self.assertRaisesRegex(ValueError,'approval requires exact owner approve instruction'):
                V.check_approval(changed,self.expected,True)
        for field in ['approver','exactApprovalInstruction','approvalSource','approvedOn']:
            changed=copy.deepcopy(value);changed.pop(field)
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'approval lacks identity, exact words, source or date'):
                V.check_approval(changed,self.expected,True)
        with workspace(pending=True) as root:
            path=root/B.E/'approval.json';value=V.read_json(path);value['approver']='false owner';path.write_text(json.dumps(value))
            self.assert_failure(root,'pending receipt must not claim owner approval')

    def test_completion_from_flag_spec_sprint_and_integrated_label_requires_approval(self):
        for kind in ['flag','spec','sprint','labels']:
            with self.subTest(kind=kind),workspace(pending=True) as root:
                if kind=='spec':
                    path=root/B.SPEC;path.write_text(re.sub(r'^status:[^\n]*','status: done',path.read_text(),flags=re.M))
                if kind=='sprint':
                    path=root/B.ART/'sprint-status.yaml';path.write_text(re.sub(r'^(  5-10-refresh-and-re-disposition-chatbot-and-memories-inventories):[^\n]*',r'\1: done',path.read_text(),flags=re.M))
                if kind=='labels':
                    path=root/B.E/'labels.json';value=V.read_json(path);value['state']='integrated';path.write_text(json.dumps(value))
                self.assert_failure(root,'completion requires exact-byte owner approval and covered roles',args=['--approved-completion'] if kind=='flag' else [])
        with workspace(pending=True) as root:
            path=root/B.E/'approval.json';path.write_text(json.dumps(approved(V.read_json(path))))
            self.assert_failure(root,'completion requires integrated PS06/PS07/PS12/PS13/PS14 labels',args=['--approved-completion'])

    def test_label_chain_rows_hash_path_and_readme_only_patch(self):
        for kind,message in [
            ('chain','Story 5.9 label predecessor chain mismatch'),
            ('rows','label row coverage/duplicate mismatch'),
            ('repositories','label repository coverage/duplicate mismatch'),
            ('citation','PS12: successor citation/hash/anchor/surface/removal gate mismatch'),
            ('patch','label artifact hash mismatch: '+str(B.E/'upstream/chatbot/README.patch')),
            ('path','chatbot: owner/base/README patch register mismatch'),
        ]:
            with self.subTest(kind=kind),workspace(pending=True) as root:
                path=root/B.E/'labels.json';value=V.read_json(path)
                if kind=='chain': value['predecessor']['sha256']='0'*64
                if kind=='rows': value['rows'].append(value['rows'][0])
                if kind=='repositories': value['repositories'].append(value['repositories'][0])
                if kind=='citation': next(r for r in value['rows'] if r['id']=='PS12')['label']['text']='invented'
                if kind=='patch': (root/B.E/'upstream/chatbot/README.patch').write_text('--- a/other.txt\n+++ b/other.txt\n')
                if kind=='path': value['repositories'][0]['patch']['path']='../escape'
                path.write_text(json.dumps(value))
                self.assert_failure(root,message,module=L)
        for key in ['PS06','PS07','PS12','PS13','PS14']:
            with self.subTest(key=key),workspace(pending=True) as root:
                path=root/B.E/'labels.json';value=V.read_json(path);value['rows']=[r for r in value['rows'] if r['id']!=key];path.write_text(json.dumps(value))
                self.assert_failure(root,'label row coverage/duplicate mismatch',module=L)

    def test_approved_authorized_completion_exercises_actual_delivery_checks(self):
        with integrated_workspace() as (root,register,observed):
            self.assertEqual((0,COMPLETION_PASS,''),invoke(V,['--root',str(root),'--approved-completion']))
            self.assertEqual((0,LABEL_COMPLETION_PASS,''),invoke(L,['--root',str(root),'--approved-completion']))
            self.assertEqual(2,len({owner for owner,args in observed if args==('show','origin/main:README.md')}))
            for repository in register['repositories']:
                self.assertIn((repository['ownerCheckout'],('cat-file','commit',repository['integration']['commit'])),observed)
                self.assertIn((repository['ownerCheckout'],('diff','--name-only',repository['integration']['commit']+'^',repository['integration']['commit'])),observed)
            for path in [*[m['new'] for m in B.MODULES.values()],B.E/'approval.json']:
                for revision in ['b'*40,'origin/main']:
                    self.assertIn((str(root),('show',f'{revision}:{path}')),observed)

    def test_delivery_accepts_moved_owner_readmes_and_rejects_extra_changes_for_both_modules(self):
        with integrated_workspace(moved_main=True) as (root,register,_):
            for entrypoint,output in [(V,COMPLETION_PASS),(L,LABEL_COMPLETION_PASS)]:
                self.assertEqual((0,output,''),invoke(entrypoint,['--root',str(root),'--approved-completion']))
            for repository in register['repositories']:
                delivered=B.git(Path(repository['ownerCheckout']),'show',repository['integration']['commit']+':README.md')
                self.assertNotEqual(repository['readme']['afterSha256'],B.sha(delivered))
        for repository in V.read_json(ROOT/B.E/'labels.json')['repositories']:
            for kind,message in [
                ('outside-section',repository['name']+': integrated README bytes mismatch; expected only the authorized section swap'),
                ('parent-section',repository['name']+': parent compatibility section differs from authorized before bytes'),
            ]:
                with self.subTest(module=repository['name'],kind=kind),integrated_workspace(moved_main=True,delivery_fault=(kind,repository['ownerCheckout'])) as (root,_,_):
                    for entrypoint in [V,L]:
                        self.assertEqual((1,'','FAIL: '+message+'\n'),invoke(entrypoint,['--root',str(root),'--approved-completion']))

    def test_approved_undelivered_candidate_is_valid_but_generation_and_completion_refuse(self):
        with workspace(pending=True) as root:
            path=root/B.E/'approval.json';path.write_text(json.dumps(approved(V.read_json(path))))
            with patch.object(V,'check_source_drift',return_value=None):
                self.assertEqual((0,APPROVED_PASS,''),invoke(V,['--root',str(root)]))
                self.assertEqual((0,LABEL_APPROVED_PASS,''),invoke(L,['--root',str(root)]))
            self.assert_failure(root,'completion requires integrated PS06/PS07/PS12/PS13/PS14 labels',args=['--approved-completion'])
            before=path.read_bytes()
            with patch.object(B,'ROOT',root):
                self.assertEqual((1,'','FAIL: refusing to overwrite approved or unknown-state packet\n'),invoke(B,[]))
            self.assertEqual(before,path.read_bytes())

    def test_each_published_inventory_and_approval_copy_is_required_with_exact_streams(self):
        for relative in [*[m['new'] for m in B.MODULES.values()],B.E/'approval.json']:
            for revision in ['b'*40,'origin/main']:
                with self.subTest(path=str(relative),revision=revision),integrated_workspace((revision,relative)) as (root,_,_):
                    expected=(1,'',f'FAIL: {relative}: published bytes differ from approved candidate\n')
                    self.assertEqual(expected,invoke(L,['--root',str(root),'--approved-completion']))

    def test_guard_removal_of_published_byte_comparisons_is_detected(self):
        # Remove only the publication-byte loop from a copy of the actual function;
        # the same exact-stream rejection assertion must then fail.
        text=inspect.getsource(L.check_delivery)
        text=text[:text.index('    for path in [')]
        namespace=dict(L.__dict__)
        exec(compile(text,'<publication-guard-removal>','exec'),namespace)
        relative=B.MODULES['memories']['new']
        with integrated_workspace(('origin/main',relative)) as (root,_,_):
            expected=(1,'',f'FAIL: {relative}: published bytes differ from approved candidate\n')
            self.assertEqual(expected,invoke(L,['--root',str(root),'--approved-completion']))
            with patch.object(L,'check_delivery',namespace['check_delivery']):
                with self.assertRaises(AssertionError):
                    self.assertEqual(expected,invoke(L,['--root',str(root),'--approved-completion']))

    def test_delivery_readme_and_inventory_ancestry_guards_have_entrypoint_removal_controls(self):
        guards=[
            ('readme',"    require(B.compatibility_section(delivered) == after_section and delivered == parent.replace(before_section,after_section,1),\n"
             "            f'{name}: integrated README bytes mismatch; expected only the authorized section swap')\n"),
            ('inventory-ancestry',"    B.git(root,'merge-base','--is-ancestor',inv_revision,'origin/main')\n"),
        ]
        for kind,snippet in guards:
            owners=[r['ownerCheckout'] for r in V.read_json(ROOT/B.E/'labels.json')['repositories']] if kind=='readme' else [None]
            for owner in owners:
                with self.subTest(guard=kind,owner=owner),integrated_workspace(delivery_fault=(kind,owner)) as (root,register,_):
                    name=next((r['name'] for r in register['repositories'] if r['ownerCheckout']==owner),None)
                    message=(f'{name}: integrated README bytes mismatch; expected only the authorized section swap' if kind=='readme'
                             else 'git merge-base --is-ancestor '+'b'*40+' origin/main failed: off-main inventory fixture')
                    expected=(1,'','FAIL: '+message+'\n')
                    for entrypoint in [V,L]:
                        with self.subTest(entrypoint=entrypoint.__name__):
                            args=['--root',str(root),'--approved-completion']
                            self.assertEqual(expected,invoke(entrypoint,args))
                            with removed_source(L,'check_delivery',snippet):
                                # A surviving exact-byte/ancestry assertion must reject
                                # its corrupted fixture; removing it makes that assertion fail.
                                with self.assertRaises(AssertionError):
                                    self.assertEqual(expected,invoke(entrypoint,args))

    def test_delivery_words_revisions_and_commit_hash_have_exact_stream_guard_controls(self):
        source=inspect.getsource(L.check_delivery)
        cases=[]
        for words in ['approve','authorized','authorize and stop','authorize later']:
            cases.append(('authorization',words,'completion requires separate explicit authorize instruction for label delivery'))
        for key in ['commit','inventoryRevision']:
            for value in ['main','a'*7]:
                cases.append((key,value,'chatbot: completion requires canonical integrated label commit' if key=='commit' else 'completion requires canonical integrated inventory revision'))
        cases.append(('commitSha256','0'*64,'chatbot: integrated commit hash mismatch'))
        for key,value,message in cases:
            if key=='authorization':
                snippet="    require(isinstance(auth,dict) and all(V.nonblank(auth.get(k)) for k in ['exactWords','source','approvedOn'])\n"+\
                        "            and auth['exactWords'].strip().casefold() == 'authorize',\n"+\
                        "            'completion requires separate explicit authorize instruction for label delivery')\n"
            elif key=='commit':
                snippet="    require(isinstance(integration,dict) and re.fullmatch('[0-9a-f]{40}',integration.get('commit','')) is not None,\n"+\
                        "            f'{name}: completion requires canonical integrated label commit')\n"
            else:
                snippet=next(line for line in source.splitlines(keepends=True) if message.split(': ',1)[-1] in line)
            with self.subTest(field=key,value=value),integrated_workspace() as (root,register,_):
                if key=='authorization': register['deliveryAuthorization']['exactWords']=value
                elif key=='inventoryRevision': register[key]=value
                else: register['repositories'][0]['integration'][key]=value
                (root/B.E/'labels.json').write_text(json.dumps(register))
                expected=(1,'','FAIL: '+message+'\n')
                for entrypoint in [V,L]:
                    args=['--root',str(root),'--approved-completion']
                    self.assertEqual(expected,invoke(entrypoint,args))
                    with removed_source(L,'check_delivery',snippet):
                        with self.assertRaises(AssertionError): self.assertEqual(expected,invoke(entrypoint,args))

    def test_pending_label_claims_and_wrong_owner_origin_have_exact_stream_controls(self):
        pending_guard="        else:\n            require(register.get('deliveryAuthorization') is None and register.get('inventoryRevision') is None and repository.get('integration') is None,'pending labels must not claim authorization or integration')\n"
        for field,value in [('deliveryAuthorization',dict(exactWords='authorize')),('inventoryRevision','b'*40),('integration',dict(commit='a'*40))]:
            with self.subTest(field=field),workspace(pending=True) as root:
                path=root/B.E/'labels.json';register=V.read_json(path)
                if field=='integration': register['repositories'][0][field]=value
                else: register[field]=value
                path.write_text(json.dumps(register))
                expected=(1,'','FAIL: pending labels must not claim authorization or integration\n')
                self.assertEqual(expected,invoke(L,['--root',str(root)]))
                with removed_source(L,'verify',pending_guard):
                    with self.assertRaises(AssertionError): self.assertEqual(expected,invoke(L,['--root',str(root)]))
        origin_guard="        require(L57.github_repository(origin) == L57.github_repository(repository['repository']),f'{name}: checkout origin differs from owning repository')\n"
        for repository in V.read_json(ROOT/B.E/'labels.json')['repositories']:
            with self.subTest(module=repository['name']),integrated_workspace(delivery_fault=('origin',repository['ownerCheckout'])) as (root,_,_):
                expected=(1,'','FAIL: '+repository['name']+': checkout origin differs from owning repository\n')
                for entrypoint in [V,L]:
                    args=['--root',str(root),'--approved-completion']
                    self.assertEqual(expected,invoke(entrypoint,args))
                    with removed_source(L,'verify',origin_guard):
                        with self.assertRaises(AssertionError): self.assertEqual(expected,invoke(entrypoint,args))

    def test_label_entrypoint_handles_missing_and_malformed_approval_without_traceback(self):
        for kind in ['missing','malformed','missing-decision']:
            with self.subTest(kind=kind),workspace(pending=True) as root:
                path=root/B.E/'approval.json'
                if kind=='missing':
                    path.unlink();message=f"[Errno 2] No such file or directory: '{path}'"
                elif kind=='malformed':
                    path.write_text('{"decision":');message='Expecting value: line 1 column 13 (char 12)'
                else:
                    path.write_text('{}');message="'decision'"
                self.assertEqual((1,'','FAIL: '+message+'\n'),invoke(L,['--root',str(root)]))

    def test_delivery_rejects_missing_authorization_stale_origin_non_readme_and_off_main(self):
        register,_=B.label_candidate(ROOT,{str(m['new']):B.sha((ROOT/m['new']).read_bytes()) for m in B.MODULES.values()})
        r=register['repositories'][0];before=B.blob(ROOT,r['name'],'README.md')
        after=before.replace((ROOT/r['before']['path']).read_bytes(),(ROOT/r['after']['path']).read_bytes())
        register['state']='integrated'
        with self.assertRaisesRegex(ValueError,'separate explicit authorize instruction'): L.check_delivery(ROOT,register,r,before,after)
        register['deliveryAuthorization']=dict(exactWords='authorize',source='fixture only',approvedOn='2026-11-16')
        r['integration']=dict(commit='a'*40,commitSha256=B.sha(b'commit'));register['inventoryRevision']='b'*40
        for kind,message in [('stale','current origin/main does not cite exact successor labels'),('otherfile','delivered commit is not README-only'),('offmain','git merge-base --is-ancestor')]:
            def fake(root,*args):
                if args==('show','a'*40+'^:README.md'): return before
                if args==('show','a'*40+':README.md'): return after
                if args==('merge-base','--is-ancestor','a'*40,'origin/main'):
                    if kind=='offmain': raise ValueError('git merge-base --is-ancestor failed: off-main fixture')
                    return b''
                if args==('diff','--name-only','a'*40+'^','a'*40): return b'README.md\nother.txt\n' if kind=='otherfile' else b'README.md\n'
                if args==('cat-file','commit','a'*40): return b'commit'
                if args==('show','origin/main:README.md'): return before
                raise AssertionError(args)
            with self.subTest(kind=kind),patch.object(B,'git',side_effect=fake):
                with self.assertRaisesRegex(ValueError,message): L.check_delivery(ROOT,register,r,before,after)

    def test_generator_refuses_approved_authorized_symlink_and_approval_race(self):
        for kind,message in [('approval','refusing to overwrite approved or unknown-state packet'),
                             ('authorization','refusing to overwrite authorized, integrated or unknown-state labels'),
                             ('symlink','refusing symlink output destination: '+str(B.MODULES['chatbot']['new'])),
                             ('race','refusing to overwrite receipt changed during generation: approval.json')]:
            with self.subTest(kind=kind),workspace(pending=True) as root:
                approval=root/B.E/'approval.json';labels=root/B.E/'labels.json'
                if kind=='approval': approval.write_text(json.dumps(approved(V.read_json(approval))))
                if kind=='authorization':
                    value=V.read_json(labels);value['deliveryAuthorization']={'exactWords':'authorize'};labels.write_text(json.dumps(value))
                if kind=='symlink':
                    path=root/B.MODULES['chatbot']['new'];path.unlink();path.symlink_to(ROOT/B.MODULES['chatbot']['new'])
                packet=B.packet
                def race_packet(path,*,regeneration=False):
                    result=packet(path,regeneration=regeneration);approval.write_text(json.dumps(approved(V.read_json(approval))));return result
                before={p:(root/p).read_bytes() for p in packet(root)}
                with patch.object(B,'ROOT',root),patch.object(B,'packet',side_effect=race_packet if kind=='race' else packet):
                    self.assertEqual((1,'','FAIL: '+message+'\n'),invoke(B,[]))
                for path,data in before.items():
                    if kind=='race' and path==B.E/'approval.json': continue
                    self.assertEqual(data,(root/path).read_bytes(),str(path))

    def test_generator_rejects_symlinked_output_parent_without_writes_and_detects_ancestor_guard_removal(self):
        with workspace(pending=True) as root,tempfile.TemporaryDirectory() as temp:
            generated=B.packet(root)
            parent=root/B.E/'upstream/chatbot';external=Path(temp)
            shutil.copytree(parent,external,dirs_exist_ok=True)
            shutil.rmtree(parent)
            parent.symlink_to(external,target_is_directory=True)
            target=external/'README.patch'
            target.write_bytes(b'external patch must stay unchanged\n')
            (external/'unrelated.txt').write_bytes(b'external unrelated file\n')
            def repository_outputs(): return {path:(root/path).read_bytes() for path in generated}
            def external_files(): return {path.relative_to(external):path.read_bytes() for path in external.rglob('*') if path.is_file()}
            before_outputs,before_external=repository_outputs(),external_files()
            expected=(1,'','FAIL: refusing symlink output destination: '+str(B.E/'upstream/chatbot/README.before.section.md')+'\n')
            def rejects_without_writes():
                self.assertEqual(expected,invoke(B,[]))
                self.assertEqual(before_outputs,repository_outputs())
                self.assertEqual(before_external,external_files())
            with patch.object(B,'ROOT',root):
                rejects_without_writes()
                self.assertTrue(parent.is_symlink())
                self.assertEqual(external,parent.resolve())
                # Remove the actual ancestor expansion, retaining the leaf check.
                with removed_source(B,'main',',*destination.parents'):
                    with self.assertRaises(AssertionError): rejects_without_writes()
                self.assertEqual(generated[B.E/'upstream/chatbot/README.patch'],target.read_bytes())
                self.assertNotEqual(before_external[Path('README.patch')],target.read_bytes())

    def test_approval_after_first_successor_write_is_preserved_and_later_writes_stop(self):
        with workspace(pending=True) as root:
            generated=B.packet(root)
            first=B.MODULES['chatbot']['new'];approval=root/B.E/'approval.json'
            (root/first).write_bytes(b'older pending candidate')
            owner_bytes=(json.dumps(approved(json.loads(generated[B.E/'approval.json'])),indent=2)+'\n').encode()
            real=Path.write_bytes;written=[]
            def inject(path,data):
                result=real(path,data);written.append(path)
                if path==root/first: real(approval,owner_bytes)
                return result
            with patch.object(B,'ROOT',root),patch.object(Path,'write_bytes',new=inject):
                self.assertEqual((1,'','FAIL: refusing to overwrite receipt changed during generation: approval.json\n'),invoke(B,[]))
            self.assertEqual(owner_bytes,approval.read_bytes())
            self.assertEqual([root/first],written)

    def test_unchanged_pending_destinations_are_not_rewritten(self):
        with workspace(pending=True) as root:
            # Normalize only this explicit pending fixture to deterministic bytes.
            for path,data in B.packet(root).items(): (root/path).write_bytes(data)
            with patch.object(B,'ROOT',root),patch.object(Path,'write_bytes',side_effect=AssertionError('unchanged destination rewritten')):
                result=invoke(B,[])
            self.assertEqual(0,result[0]);self.assertEqual('',result[2])

    def test_duplicate_json_unknown_state_and_missing_metadata(self):
        with workspace(pending=True) as root:
            (root/B.E/'approval.json').write_text('{"decision":"pending","decision":"approved"}')
            self.assert_failure(root,'duplicate JSON member decision')
        with workspace(pending=True) as root:
            path=root/B.E/'labels.json';value=V.read_json(path);value['state']='unknown';path.write_text(json.dumps(value))
            self.assert_failure(root,'invalid label register state',module=L)
        with workspace(pending=True) as root:
            path=root/B.MODULES['chatbot']['new'];path.write_text(path.read_text().replace('status: pending','status: approved',1))
            self.assert_failure(root,'chatbot: metadata/pin/approval-state mismatch')

    def test_guard_removal_controls_detect_missing_accounting_row_anchor_approval_and_delivery_guards(self):
        controls=[
            (V,'accounting',
             "    require(set(new) == set(entries) == expected and set(old) == expected-{f'T{i:02d}' for i in range(1,5)},\n"
             "            f'{module}: predecessor/AD-23 entry accounting mismatch (missing={sorted(expected-set(new))}, extra={sorted(set(new)-expected)})')\n",
             "chatbot: predecessor/AD-23 entry accounting mismatch (missing=['M01'], extra=[])"),
            (V,'check_rows',
             "        require(d != 'replace' and coverage != 'include',prefix+': invented readiness; no decorated Gateway replacement at pin')\n",
             'chatbot:M01 (K01): invented readiness; no decorated Gateway replacement at pin'),
            (V,'check_anchors',
             "        require(cell == '`'+'`; `'.join(expected)+'`',f'{module}:{key}: pinned anchor identity mismatch')\n",
             'chatbot:M01: pinned anchor identity mismatch'),
            (V,'check_approval',
             "    if completion:\n        require(receipt['decision'] == 'approved','completion requires exact-byte owner approval and covered roles')\n",
             'completion requires exact-byte owner approval and covered roles'),
            (L,'check_delivery',
             "    require(register.get('state') == 'integrated','completion requires integrated PS06/PS07/PS12/PS13/PS14 labels')\n",
             'completion requires integrated PS06/PS07/PS12/PS13/PS14 labels'),
        ]
        for module,name,snippet,message in controls:
            with self.subTest(guard=name),workspace(pending=True) as root:
                args=[]
                if name=='accounting':
                    path=root/B.MODULES['chatbot']['new'];row=B.parse(path.read_text(),'chatbot')['M01']['text']
                    path.write_text(path.read_text().replace(row+'\n',''))
                elif name=='check_rows': replace_cell(root,'chatbot','M01','Amendment disposition','replace')
                elif name=='check_anchors': replace_cell(root,'chatbot','M01','Pinned evidence','`README.md:1`')
                else:
                    args=['--approved-completion']
                    if name=='check_delivery':
                        path=root/B.E/'approval.json';path.write_text(json.dumps(approved(V.read_json(path))))
                self.assert_failure(root,message,args=args)
                with removed_source(module,name,snippet):
                    with self.assertRaises(AssertionError): self.assert_failure(root,message,args=args)


if __name__ == '__main__':
    unittest.main()
