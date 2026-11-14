"""Exact-stream damaged-input tests and live-global guard-removal controls."""
import codecs
import contextlib
import copy
import importlib.util
import inspect
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
PUBLISHED_LABEL_REVISION = 'c3bd5b9a49b538282db14c5ee9780f63fe70c8b9'
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


def ascii_locale():
    """Interpreter flags and environment for a non-UTF-8 (ASCII) locale child."""
    return ['-X','utf8=0'],dict(os.environ,LC_ALL='C')


def fixture_process(script,*args,non_utf8=False):
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
    flags,env = ascii_locale() if non_utf8 else ([],None)
    return subprocess.run([sys.executable,'-I',*flags,'-c',runner,B.LABEL_PIN,registered_owner(),str(script),*args],capture_output=True,text=True,env=env)


@contextlib.contextmanager
def workspace_view(*,pending=True):
    """Copy documentary inputs, sharing only read-only repository objects/source."""
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp).resolve()
        for name in ['.git','.gitmodules','references','src','scripts']:
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
    def test_verifiers_reject_duplicate_workflow_statuses_and_deletion_control(self):
        guard = "            require(len(keys) <= 1, 'duplicate workflow status '+key.strip())\n"
        for path,key in [(B.SPEC,'status'),(B.ART/'sprint-status.yaml','  5-8-refresh-and-re-disposition-the-folders-inventory')]:
            for value in ['done','','[]']:
                with self.subTest(path=path,value=value),workspace_view() as root:
                    target = root/path
                    target.write_text(target.read_text()+'\n'+key+': '+value+'\n')
                    verifier = root/B.E/'verify_amendment.py'
                    source = verifier.read_text()
                    self.assertEqual(1,source.count(guard))
                    for script in ['verify_amendment.py','verify_labels.py']:
                        result = fixture_process(root/B.E/script,'--root',str(root))
                        self.assertEqual((1,'','FAIL: duplicate workflow status '+key.strip()+'\n'),
                                         (result.returncode,result.stdout,result.stderr))
                    verifier.write_text(source.replace(guard,''))
                    for script,output in [('verify_amendment.py',PASS),('verify_labels.py',LABEL_PASS)]:
                        result = fixture_process(root/B.E/script,'--root',str(root))
                        self.assertEqual((0,output,''),(result.returncode,result.stdout,result.stderr))

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

    def test_lifecycle_proof_rejects_changed_real_inputs_without_summary(self):
        proof = load('lifecycle58changed','delivery/lifecycle-proof.py')
        read,run = Path.read_bytes,subprocess.run
        protected = ROOT/B.NEW
        snapshots = 0
        def changed(path,*args,**kwargs):
            nonlocal snapshots
            data = read(path,*args,**kwargs)
            if path == protected:
                snapshots += 1
                if snapshots == 2:
                    return data+b'changed second snapshot\n'
            return data
        def child(command,**kwargs):
            if command[:5] == [sys.executable,'-I','-m','unittest','discover']:
                return subprocess.CompletedProcess(command,0,b'',b'')
            return run(command,**kwargs)
        with tempfile.TemporaryDirectory() as temp,patch.object(Path,'read_bytes',changed),patch.object(subprocess,'run',side_effect=child):
            delivery = Path(temp).resolve()
            with self.assertRaisesRegex(ValueError,'^real candidate/receipt/workflow bytes changed$'):
                proof.main(delivery=delivery)
            self.assertEqual(2,snapshots)
            self.assertEqual([],list(delivery.iterdir()))

    def test_lifecycle_proof_rejects_child_label_mutation_under_optimization(self):
        proof = load('lifecycle58childmutation','delivery/lifecycle-proof.py')
        # Execute the helper with assertions stripped, as Python -O does.
        exec(compile(Path(proof.__file__).read_text(),proof.__file__,'exec',optimize=1),proof.__dict__)
        run = subprocess.run
        def child(command,**kwargs):
            if command[:5] == [sys.executable,'-I','-m','unittest','discover']:
                path = kwargs['cwd']/B.E/'labels.json'
                labels = V.read_json(path)
                labels['state'] = 'candidate-pending-owner-approval-and-delivery'
                path.write_text(json.dumps(labels)+'\n')
                return subprocess.CompletedProcess(command,0,b'',b'')
            return run(command,**kwargs)
        with tempfile.TemporaryDirectory() as temp,patch.object(subprocess,'run',side_effect=child):
            delivery = Path(temp).resolve()
            with self.assertRaisesRegex(ValueError,'^synthetic lifecycle receipt or labels changed during child run$'):
                proof.main(delivery=delivery)
            self.assertEqual([],list(delivery.iterdir()))

    def test_lifecycle_proof_rejects_child_approval_mutation_without_writes(self):
        proof = load('lifecycle58approval','delivery/lifecycle-proof.py')
        run = subprocess.run
        def child(command,**kwargs):
            if command[:5] == [sys.executable,'-I','-m','unittest','discover']:
                path = kwargs['cwd']/B.E/'approval.json'
                receipt = V.read_json(path)
                receipt['decision'] = 'pending'
                path.write_text(json.dumps(receipt)+'\n')
                return subprocess.CompletedProcess(command,0,b'',b'')
            return run(command,**kwargs)
        with tempfile.TemporaryDirectory() as temp,patch.object(subprocess,'run',side_effect=child):
            delivery = Path(temp).resolve()
            with self.assertRaisesRegex(ValueError,'^synthetic lifecycle receipt or labels changed during child run$'):
                proof.main(delivery=delivery)
            self.assertEqual([],list(delivery.iterdir()))

    def test_lifecycle_proof_rejects_each_damaged_setup_without_writes(self):
        cases = [
            ('approval','synthetic lifecycle approval is not approved'),
            ('labels','synthetic lifecycle labels are not integrated'),
            ('workflow','synthetic lifecycle workflow is not done'),
            ('candidate','synthetic lifecycle candidate bytes changed'),
        ]
        for field,message in cases:
            with self.subTest(field=field):
                proof = load('lifecycle58setup','delivery/lifecycle-proof.py')
                module = proof.load_tests(ROOT)
                workflow,run = module.workflow_status,subprocess.run
                def damaged(path,key,value):
                    workflow(path,key,value)
                    if key == 'status': return
                    fixture = path.parents[2]
                    if field in {'approval','labels'}:
                        target = fixture/B.E/(field+'.json')
                        document = V.read_json(target)
                        document['decision' if field == 'approval' else 'state'] = 'pending'
                        target.write_text(json.dumps(document)+'\n')
                    elif field == 'workflow':
                        workflow(fixture/B.SPEC,'status','review')
                        workflow(path,key,'review')
                    else:
                        target = fixture/B.NEW
                        target.write_bytes(target.read_bytes()+b'Damaged setup.\n')
                def child(command,**kwargs):
                    if command[:5] == [sys.executable,'-I','-m','unittest','discover']:
                        return subprocess.CompletedProcess(command,0,b'',b'')
                    return run(command,**kwargs)
                with tempfile.TemporaryDirectory() as temp,patch.object(proof,'load_tests',return_value=module),patch.object(module,'workflow_status',side_effect=damaged),patch.object(subprocess,'run',side_effect=child):
                    delivery = Path(temp).resolve()
                    with self.assertRaisesRegex(ValueError,'^'+re.escape(message)+'$'):
                        proof.main(delivery=delivery)
                    self.assertEqual([],list(delivery.iterdir()))

    def test_lifecycle_proof_rejects_child_candidate_mutation_without_writes(self):
        proof = load('lifecycle58candidate','delivery/lifecycle-proof.py')
        run = subprocess.run
        def child(command,**kwargs):
            if command[:5] == [sys.executable,'-I','-m','unittest','discover']:
                path = kwargs['cwd']/B.NEW
                path.write_bytes(path.read_bytes()+b'Unapproved child prose.\n')
                return subprocess.CompletedProcess(command,0,b'',b'')
            return run(command,**kwargs)
        with tempfile.TemporaryDirectory() as temp,patch.object(subprocess,'run',side_effect=child):
            delivery = Path(temp).resolve()
            with self.assertRaisesRegex(ValueError,'^synthetic lifecycle candidate bytes changed during child run$'):
                proof.main(delivery=delivery)
            self.assertEqual([],list(delivery.iterdir()))

    def test_lifecycle_proof_rejects_child_workflow_mutation_without_writes(self):
        # Either status alone still satisfies completion_requested, so the
        # helper must compare both workflow files' bytes after the child.
        for path,key in [(B.ART/'sprint-status.yaml','  5-8-refresh-and-re-disposition-the-folders-inventory'),(B.SPEC,'status')]:
            with self.subTest(path=path):
                proof = load('lifecycle58workflow','delivery/lifecycle-proof.py')
                run = subprocess.run
                def child(command,**kwargs):
                    if command[:5] == [sys.executable,'-I','-m','unittest','discover']:
                        workflow_status(kwargs['cwd']/path,key,'review')
                        self.assertTrue(V.completion_requested(kwargs['cwd'],False))
                        return subprocess.CompletedProcess(command,0,b'',b'')
                    return run(command,**kwargs)
                with tempfile.TemporaryDirectory() as temp,patch.object(subprocess,'run',side_effect=child):
                    delivery = Path(temp).resolve()
                    with self.assertRaisesRegex(ValueError,'^synthetic lifecycle workflow changed during child run$'):
                        proof.main(delivery=delivery)
                    self.assertEqual([],list(delivery.iterdir()))


class PendingCase(unittest.TestCase):
    def setUp(self):
        stack = contextlib.ExitStack()
        self.addCleanup(stack.close)
        self.root = stack.enter_context(workspace_view())
        for module in [V,L,L.V,B]:
            stack.enter_context(patch.object(module,'ROOT',self.root))
        stack.enter_context(patch.object(subprocess,'run',side_effect=pinned_observation(subprocess.run)))

    def removed_condition(self,module,function,condition):
        """Disable only one conjunct, preserving its sibling checks and globals."""
        source = inspect.getsource(getattr(module,function))
        self.assertEqual(1,source.count(condition))
        namespace = {}
        exec(source.replace(condition,'True'),module.__dict__,namespace)
        self.assertIs(namespace[function].__globals__,module.__dict__)
        return patch.object(module,function,namespace[function])


class PacketAuditTests(unittest.TestCase):
    @contextlib.contextmanager
    def audit_fixture(self):
        """Construct valid captures without executing gates or changing real evidence."""
        runner = load('packet58audit','review-pass4-20261114/verify_packet.py')
        # Lifecycle proof deliberately replaces these working-tree documents.
        # Audit fixtures instead observe their committed bytes, independently
        # of synthetic approval/label state, while retaining the real Git guard.
        read = Path.read_bytes
        pinned = {ROOT/B.E/name:B.git(ROOT,'show','HEAD:'+str(B.E/name)) for name in ['approval.json','labels.json']}
        def committed(path,*args,**kwargs):
            return pinned[path] if path in pinned else read(path,*args,**kwargs)
        with tempfile.TemporaryDirectory(dir=HERE,prefix='audit-fixture-') as temp,patch.object(runner,'OUT',Path(temp).resolve()),patch.object(Path,'read_bytes',committed):
            names = runner.test_names()
            def tests(selected):
                return (''.join(name+' ... ok\n' for name in selected)+'\n'+'-'*70+'\nRan '+str(len(selected))+' tests in 0.001s\n\nOK\n').encode()
            child = {'stdout':b'','stderr':tests(names)}
            summary = {
                'suiteExitCode':0,'claim':'Suite independence from synthetic lifecycle metadata; real approved-completion is verified separately.',
                'sourceFixture':'approved / integrated / spec done / sprint done','realInputsUnchanged':True,
                'candidateSha256':B.sha((ROOT/B.NEW).read_bytes()),
                'child':{'command':[sys.executable,'-I','-m','unittest','discover','-v','-s',str(B.E),'-p','test_*.py'],
                         'cwd':'.','cwdBase':'isolated synthetic lifecycle workspace created by this helper'},
                'helper':{'command':['python3','-B','-I',str(B.E/'delivery/lifecycle-proof.py')],
                          'cwd':'.','cwdBase':'repository root containing this retained script'},
            }
            for stream,data in child.items():
                name = 'lifecycle-integrated.'+stream+'.txt'
                (runner.OUT/name).write_bytes(data)
                summary[stream] = {'path':name,'sha256':B.sha(data)}
            runner.write(runner.OUT/'lifecycle-integrated.json',summary)
            manifest = {'head':B.git(ROOT,'rev-parse','HEAD').decode().strip(),'baselineCommit':B.BASELINE,
                        'inputs':runner.input_hashes(),'commands':[]}
            for name,command,environment in runner.commands():
                stdout,stderr = b'',b''
                if name == 'tests': stderr = tests(names)
                elif name == 'symlink-temp-tests':
                    stderr = tests([test for test in names if any(method in test for method in runner.SYMLINK_TESTS)])
                    environment = dict(environment,TMPDIR='/synthetic/link')
                elif name == 'lifecycle':
                    stdout = (json.dumps(summary,indent=2)+'\n'+'\n'.join(child['stderr'].decode().splitlines()[-5:])+'\n').encode()
                elif name.startswith('inventory'): stdout = runner.INVENTORY_PASS
                elif name.startswith('labels'): stdout = runner.LABEL_PASS
                elif name == 'ad23': stdout = runner.AD23_PASS
                row = {'name':name,'command':command,'cwd':str(ROOT),'environment':environment,'exitCode':0}
                for stream,data in [('stdout',stdout),('stderr',stderr)]:
                    path = runner.OUT/(name+'.'+stream+'.txt'); path.write_bytes(data)
                    row[stream] = {'path':str(path.relative_to(ROOT/B.E)),'sha256':B.sha(data)}
                manifest['commands'].append(row)
            runner.write(runner.OUT/'commands.json',manifest)
            yield runner,manifest

    def test_packet_audit_checks_exact_gate_streams_and_removal_controls(self):
        for stream,data in [('stdout',b'PASS: wrong claim\n'),('stderr',b'reported: unexpected owner drift\n')]:
            with self.subTest(stream=stream),self.audit_fixture() as (runner,manifest):
                row = next(row for row in manifest['commands'] if row['name'] == 'inventory')
                path = ROOT/B.E/row[stream]['path']; path.write_bytes(data)
                row[stream]['sha256'] = B.sha(data)
                runner.write(runner.OUT/'commands.json',manifest)
                message = 'inventory: exact '+stream+' mismatch'
                with self.assertRaisesRegex(ValueError,'^'+message+'$'):
                    runner.audit()
                original = runner.require
                def removed(condition,actual):
                    if actual != message: original(condition,actual)
                with patch.object(runner,'require',side_effect=removed),contextlib.redirect_stdout(io.StringIO()):
                    runner.audit()

    def test_packet_audit_covers_all_fourteen_protected_artifacts(self):
        with self.audit_fixture() as (runner,manifest),contextlib.redirect_stdout(io.StringIO()):
            runner.audit()
            result = runner.read(runner.OUT/'audit.json')
            expected = set(B.AUTHORITIES+[B.NEW,B.E/'approval.json',B.E/'labels.json',*[B.E/'upstream/folders'/name for name in ['README.before.section.md','README.after.section.md','README.patch']]])
            self.assertEqual(14,len(expected))
            self.assertEqual({str(path) for path in expected},set(result['protectedArtifacts']))
            self.assertEqual(10,result['commandsWithBothStreamHashesAndExactContentVerified'])
            read = Path.read_bytes
            for protected in expected:
                snapshots = 0
                def damaged(path,*args,**kwargs):
                    nonlocal snapshots
                    data = read(path,*args,**kwargs)
                    if path == ROOT/protected:
                        snapshots += 1
                        # Candidate hash also appears in the earlier lifecycle
                        # summary check; target the later protected-byte check.
                        if protected != B.NEW or snapshots >= 2:
                            return data+b'Unapproved protected bytes.\n'
                    return data
                with self.subTest(path=protected),patch.object(Path,'read_bytes',damaged):
                    with self.assertRaisesRegex(ValueError,'^'+re.escape(str(protected)+': protected bytes differ from HEAD')+'$'):
                        runner.audit()
                    snapshots = 0
                    original = runner.require
                    def removed(condition,actual):
                        if actual != str(protected)+': protected bytes differ from HEAD': original(condition,actual)
                    with patch.object(runner,'require',side_effect=removed):
                        runner.audit()

    def test_packet_audit_rejects_damaged_manifest_and_capture_bindings(self):
        cases = [
            ('manifest',['inputs'],{},'recorded executable inputs differ from current files'),
            ('manifest',['commands'],[],'gate manifest coverage/order mismatch'),
            ('manifest',['commands',0,'exitCode'],1,'tests: gate command/result mismatch'),
            ('manifest',['commands',0,'command'],[],'tests: gate command/result mismatch'),
            ('manifest',['commands',0,'cwd'],'.','tests: gate command/result mismatch'),
            ('manifest',['commands',0,'environment'],{'unexpected':'value'},'tests: environment mismatch'),
            ('manifest',['commands',7,'environment','TMPDIR'],'/unexpected','symlink TMPDIR missing'),
            ('manifest',['commands',0,'stdout','path'],'elsewhere.txt','tests: stream path mismatch'),
            ('manifest',['commands',0,'stdout','sha256'],'0'*64,'tests: stdout hash mismatch'),
            ('summary',['suiteExitCode'],1,'lifecycle summary differs from expected proof'),
            ('summary',['stdout','sha256'],'0'*64,'lifecycle child stdout binding mismatch'),
            ('stream',['tests','stdout'],b'Unexpected test output\n','tests: exact stdout mismatch'),
            ('stream',['tests','stderr'],b'Unexpected unittest result\n','tests: exact unittest stderr mismatch'),
            ('stream',['lifecycle','stdout'],b'Unexpected lifecycle output\n','lifecycle: exact stdout/stderr mismatch'),
            ('stream',['lifecycle','stderr'],b'reported: unexpected diagnostic\n','lifecycle: exact stdout/stderr mismatch'),
        ]
        for target,keys,value,message in cases:
            with self.subTest(target=target,keys=keys),self.audit_fixture() as (runner,manifest):
                if target == 'stream':
                    name,stream = keys
                    row = next(row for row in manifest['commands'] if row['name'] == name)
                    (ROOT/B.E/row[stream]['path']).write_bytes(value)
                    row[stream]['sha256'] = B.sha(value)
                    runner.write(runner.OUT/'commands.json',manifest)
                else:
                    document = manifest if target == 'manifest' else runner.read(runner.OUT/'lifecycle-integrated.json')
                    item = document
                    for key in keys[:-1]: item = item[key]
                    item[keys[-1]] = value
                    runner.write(runner.OUT/('commands.json' if target == 'manifest' else 'lifecycle-integrated.json'),document)
                with self.assertRaisesRegex(ValueError,'^'+re.escape(message)+'$'):
                    runner.audit()

    def test_packet_audit_rejects_changed_frozen_intent_and_missing_matrix_test(self):
        with self.audit_fixture() as (runner,manifest):
            read = Path.read_bytes
            def changed(path,*args,**kwargs):
                data = read(path,*args,**kwargs)
                return data.replace(b'human-owned intent',b'altered intent') if path == ROOT/B.SPEC else data
            with patch.object(Path,'read_bytes',changed):
                with self.assertRaisesRegex(ValueError,'^frozen intent changed$'):
                    runner.audit()
            with patch.dict(runner.MATRIX,{'Missing matrix row':['nonexistent_test_method']}):
                with self.assertRaisesRegex(ValueError,'^matrix test coverage missing$'):
                    runner.audit()

    def test_packet_capture_rejects_failed_gate_and_changed_inputs(self):
        with self.audit_fixture() as (runner,manifest),contextlib.redirect_stdout(io.StringIO()):
            with patch.object(runner,'commands',return_value=[('fixture',['fixture-command'],{})]):
                result = subprocess.CompletedProcess(['fixture-command'],1,b'',b'fixture failure\n')
                with patch.object(subprocess,'run',return_value=result),patch.object(runner,'git',return_value=b'fixture-head\n'):
                    with self.assertRaisesRegex(ValueError,'^fixture: gate failed; inspect retained streams$'):
                        runner.capture()
                result = subprocess.CompletedProcess(['fixture-command'],0,b'',b'')
                with patch.object(subprocess,'run',return_value=result),patch.object(runner,'git',return_value=b'fixture-head\n'),patch.object(runner,'input_hashes',side_effect=[{'source':'before'},{'source':'after'}]):
                    with self.assertRaisesRegex(ValueError,'^executable inputs changed during capture$'):
                        runner.capture()


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

    def test_legacy_identity_and_target_inheritance_guard_removal(self):
        rows = copy.deepcopy(self.new)
        rows['M03']['cells'][6] += ' altered security/freshness'
        self.guard(lambda:self.rows(rows),'folders:M03: legacy identity/mapping/security/freshness changed')
        class SelectedRows(dict):
            def items(self):
                return [('M03',self['M03'])]
        rows = SelectedRows(copy.deepcopy(self.new))
        rows['C02']['cells'][rows['C02']['headers'].index('Amendment disposition')] = 'defer'
        self.guard(lambda:self.rows(rows),'folders:M03: target disposition inheritance mismatch')

    def test_amendment_columns_and_legacy_disposition_guard_removal(self):
        rows = copy.deepcopy(self.new)
        rows['M03']['headers'][-1] = 'Drift note'
        self.guard(lambda:self.rows(rows),'folders:M03: amendment columns damaged')
        for key,header,value,message in [
            ('M03','Disposition','defer','legacy/amendment disposition mismatch'),
            ('M03','Coverage','exclude','legacy/amendment coverage mismatch'),
            ('V07','Disposition / coverage','defer / include','combined disposition mismatch'),
        ]:
            with self.subTest(key=key,header=header):
                rows = self.changed(key,header,value)
                self.guard(lambda:self.rows(rows),f'folders:{key}: {message}')

    def test_unknown_approval_decision_entrypoints_and_guard_removal(self):
        path = self.root/B.E/'approval.json'
        receipt = V.read_json(path)
        receipt['decision'] = 'rejected'
        path.write_text(json.dumps(receipt,indent=2)+'\n')
        expected = (1,'','FAIL: unknown approval decision\n')
        result = fixture_process(HERE/'verify_amendment.py','--root',str(self.root))
        self.assertEqual(expected,(result.returncode,result.stdout,result.stderr))
        self.assertEqual(expected,invoke(V))
        original = V.require
        def removed(condition,actual):
            if actual != 'unknown approval decision': original(condition,actual)
        with patch.object(V,'require',side_effect=removed):
            self.assertEqual((0,PASS.replace('owner decision: pending;','owner decision: rejected;'),''),invoke(V))

    def test_entrypoints_decode_utf8_under_non_utf8_locale(self):
        flags,env = ascii_locale()
        probe = subprocess.run([sys.executable,'-I',*flags,'-c','import locale; print(locale.getpreferredencoding(False))'],capture_output=True,text=True,env=env)
        self.assertNotEqual('utf-8',codecs.lookup(probe.stdout.strip()).name)
        self.assertIn('–',(ROOT/B.NEW).read_text(encoding='utf-8'))
        for name,expected in [('verify_amendment.py',PASS),('verify_labels.py',LABEL_PASS)]:
            with self.subTest(script=name):
                result = fixture_process(HERE/name,'--root',str(self.root),non_utf8=True)
                self.assertEqual((0,expected,''),(result.returncode,result.stdout,result.stderr))

    def test_preserved_authority_and_adoption_guard_removal(self):
        git = B.git
        path = B.AUTHORITIES[0]
        def damaged(repo,*args):
            data = git(repo,*args)
            return data+b'altered committed authority\n' if repo == self.root and args == ('show',f'{B.BASELINE}:{path}') else data
        with patch.object(B,'git',side_effect=damaged):
            self.guard(lambda:V.verify_owner_packet(self.root),f'preserved authority changed: {path}')
        load_module = V.load
        ad_fixture = type('AdoptionFixture',(),{'verify':staticmethod(lambda *args:({},'pending'))})()
        def pending(root,name,path):
            return ad_fixture if path == B.ART/'evidence/story-5-2/verify_class_map.py' else load_module(root,name,path)
        with patch.object(V,'load',side_effect=pending):
            self.guard(lambda:V.verify_owner_packet(self.root),'AD-23 exact-byte owner adoption is required')

    def test_candidate_prose_guard_removal_reaches_hash_chain_refusal(self):
        path = self.root/B.NEW
        path.write_bytes(path.read_bytes()+b'Unapproved factual prose.\n')
        message = 'folders: candidate prose/source premises differ from deterministic derivation'
        self.reject(lambda:V.verify_owner_packet(self.root),message)
        original = V.require
        def removed(condition,actual):
            if actual != message: original(condition,actual)
        with patch.object(V,'require',side_effect=removed):
            self.reject(lambda:V.verify_owner_packet(self.root),'approval artifact/hash-chain binding mismatch')

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

    def test_pinned_surface_sets_and_missing_target_guard_removal(self):
        for index,key,value,message in [
            (0,'invented-tool','invented.cs:1','folders: exact pinned 49-tool set mismatch'),
            (1,('invented-resource','invented://uri'),'invented.cs:1','folders: exact pinned two-resource set mismatch'),
            (2,'invented leaf',('Invented','invented.cs:1'),'folders: exact pinned 42-leaf set mismatch'),
        ]:
            with self.subTest(message=message):
                surface = copy.deepcopy(self.surface)
                surface[index][key] = value
                self.guard(lambda:V.check_declarations(ROOT,self.old,self.new,self.decl,surface),message)
        with patch.object(B,'variant_targets',return_value=[]):
            self.guard(lambda:V.check_declarations(ROOT,self.old,{'V07':self.new['V07']},self.decl,self.surface),
                       'folders:V07: replacement has no decorated target')

    def test_pinned_registration_and_module_guard_removal(self):
        source = B.source
        for path,before,after,message in [
            ('src/Hexalith.Folders.Mcp/Program.cs','.WithToolsFromAssembly()','.WithoutToolsFromAssembly()',
             'folders: pinned registration mismatch'),
            ('src/Hexalith.Folders.Contracts/FoldersModule.cs','IdentifierKind.String','IdentifierKind.Ulid',
             'folders: module domain/String identifier declaration mismatch'),
        ]:
            with self.subTest(message=message):
                self.assertIn(before,source(ROOT,path))
                def damaged(root,name,pin=B.PIN):
                    text = source(root,name,pin)
                    return text.replace(before,after) if name == path and pin == B.PIN else text
                with patch.object(B,'source',side_effect=damaged):
                    self.guard(lambda:V.check_declarations(ROOT,self.old,self.new,self.decl,self.surface),message)

    def test_story_status_and_metadata_corrections(self):
        rows = self.changed('G4','Gap and required evidence','Folders Story 5.14: done at the pin.')
        self.guard(lambda:self.rows(rows),'folders:G4: story/status or corrected prerequisite premise mismatch')
        text = (ROOT/B.NEW).read_text().replace(B.PIN,'0'*40,1)
        self.guard(lambda:V.check_metadata(text),'folders: candidate metadata/pin/approval state mismatch')
        text = (ROOT/B.NEW).read_text(encoding='utf-8')
        self.guard(lambda:V.check_metadata('\n'+text),'folders: inventory frontmatter missing')
        self.assertEqual(1,text.count('\nmodule: folders\n'))
        duplicated = text.replace('\nmodule: folders\n','\nmodule: folders\nmodule: folders\n',1)
        self.guard(lambda:V.check_metadata(duplicated),'folders: damaged or duplicate metadata')

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

    def test_approval_receipt_conjuncts_and_partial_removal(self):
        for key,value,condition,message in [
            ('baselineCommit','0'*40,"receipt.get('baselineCommit') == B.BASELINE",'approval schema/baseline/pin mismatch'),
            ('sourceRevision','0'*40,"receipt.get('sourceRevision') == B.PIN",'approval schema/baseline/pin mismatch'),
            ('rolesPolicy','Invented policy',"receipt.get('rolesPolicy') == 'Folders roles covered for this successor only; no cross-module authority is inferred.'",'approval required Folders roles mismatch'),
        ]:
            with self.subTest(field=key):
                receipt = copy.deepcopy(self.receipt); receipt[key] = value
                self.reject(lambda:self.approval(receipt),message)
                with self.removed_condition(V,'check_approval',condition):
                    self.assertEqual((0,PASS,''),self.run_check(lambda:self.approval(receipt)))

    def test_builder_refuses_approved_packet_before_any_write(self):
        for decision in ['approved','rejected']:
            with self.subTest(decision=decision):
                receipt = self.approved(); receipt['decision'] = decision
                (self.root/B.E/'approval.json').write_text(json.dumps(receipt)+'\n')
                before = {p:p.read_bytes() for p in [self.root/B.NEW,*(self.root/B.E).rglob('*')] if p.is_file()}
                expected = (1,'','FAIL: refusing to overwrite an approved or unknown-state packet\n')
                with patch.object(Path,'write_bytes',side_effect=AssertionError('unexpected write')):
                    self.assertEqual(expected,invoke(B))
                result = fixture_process(self.root/B.E/'build_candidate.py')
                self.assertEqual(expected,(result.returncode,result.stdout,result.stderr))
                self.assertEqual(before,{p:p.read_bytes() for p in [self.root/B.NEW,*(self.root/B.E).rglob('*')] if p.is_file()})

    def test_builder_refuses_existing_successor_with_missing_receipts(self):
        for missing in [('approval.json',),('labels.json',),('approval.json','labels.json')]:
            with self.subTest(missing=missing),workspace_view(pending=False) as root:
                for name in missing:
                    (root/B.E/name).unlink()
                def snapshot():
                    return {p:p.read_bytes() for p in [root/B.NEW,*(root/B.E).rglob('*')] if p.is_file()}
                before = snapshot()
                expected = (1,'','FAIL: refusing to overwrite an existing successor without approval and label receipts\n')
                with patch.object(B,'ROOT',root),patch.object(Path,'write_bytes',side_effect=AssertionError('unexpected write')):
                    self.assertEqual(expected,invoke(B))
                result = fixture_process(root/B.E/'build_candidate.py')
                self.assertEqual(expected,(result.returncode,result.stdout,result.stderr))
                self.assertEqual(before,snapshot())

    def test_builder_allows_receipt_free_initialization(self):
        with workspace_view() as root:
            for path in [B.NEW,B.E/'approval.json',B.E/'labels.json']:
                (root/path).unlink()
            shutil.rmtree(root/B.E/'upstream')
            result = fixture_process(root/B.E/'build_candidate.py')
            expected = 'Prepared Folders 1.1.0 pending candidate and PS10/PS11 README-only patch; no approval or delivery granted.\n'
            self.assertEqual((0,expected,''),(result.returncode,result.stdout,result.stderr))
            self.assertEqual((ROOT/B.NEW).read_bytes(),(root/B.NEW).read_bytes())
            self.assertEqual('pending',V.read_json(root/B.E/'approval.json')['decision'])
            self.assertEqual('candidate-pending-owner-approval-and-delivery',V.read_json(root/B.E/'labels.json')['state'])

    def test_integrated_labels_force_owner_approval_without_done_status(self):
        path = self.root/B.E/'labels.json'
        register = V.read_json(path)
        register['state'] = 'integrated'
        path.write_text(json.dumps(register)+'\n')
        self.assertFalse(V.completion_requested(self.root,False))
        expected = (1,'','FAIL: completion requires exact-byte owner approval and covered Folders roles\n')
        self.assertEqual(expected,invoke(V))
        result = fixture_process(HERE/'verify_amendment.py','--root',str(self.root))
        self.assertEqual(expected,(result.returncode,result.stdout,result.stderr))
        # Remove the actual trigger from the function, retaining its live module
        # globals. Isolate the downstream label gate, tested independently below.
        trigger = "    completion = completion or labels.get('state') == 'integrated'\n"
        source = inspect.getsource(V.verify)
        self.assertEqual(1,source.count(trigger))
        namespace = {}
        exec(source.replace(trigger,''),V.__dict__,namespace)
        self.assertIs(namespace['verify'].__globals__,V.__dict__)
        load_module = V.load
        with patch.object(V,'load',side_effect=lambda root,name,file:L if file == B.E/'verify_labels.py' else load_module(root,name,file)),patch.object(L,'verify',return_value=None):
            self.assertEqual(expected,invoke(V))
            with patch.object(V,'verify',namespace['verify']):
                self.assertEqual((0,PASS,''),invoke(V))

    def test_builder_refuses_integrated_labels_before_any_write(self):
        path = self.root/B.E/'labels.json'
        register = V.read_json(path)
        for state in ['integrated','withdrawn']:
            with self.subTest(state=state):
                register['state'] = state
                path.write_text(json.dumps(register)+'\n')
                before = {p:p.read_bytes() for p in [self.root/B.NEW,*(self.root/B.E).rglob('*')] if p.is_file()}
                expected = (1,'','FAIL: refusing to overwrite a delivered or unknown-state label packet\n')
                with patch.object(Path,'write_bytes',side_effect=AssertionError('unexpected write')):
                    self.assertEqual(expected,invoke(B))
                result = fixture_process(self.root/B.E/'build_candidate.py')
                self.assertEqual(expected,(result.returncode,result.stdout,result.stderr))
                self.assertEqual(before,{p:p.read_bytes() for p in [self.root/B.NEW,*(self.root/B.E).rglob('*')] if p.is_file()})

    def test_published_predecessor_tree_binding_and_guard_removal(self):
        git,run = B.git,subprocess.run
        def present(command,*args,**kwargs):
            if command == ['git','-C',str(ROOT/B.REPO),'rev-parse','--verify','--quiet',B.OLD_PIN+'^{commit}']:
                return subprocess.CompletedProcess(command,0,(B.OLD_PIN+'\n').encode(),b'')
            return run(command,*args,**kwargs)
        for pin,message in [
            (B.OLD_SOURCE_PIN,'folders: published predecessor src tree differs from recorded old pin'),
            (B.OLD_PIN,'folders: historical predecessor src tree differs from recorded old pin'),
        ]:
            with self.subTest(pin=pin):
                def changed(repo,*args):
                    if args == ('rev-parse',pin+':src'): return ('0'*40+'\n').encode()
                    if args == ('rev-parse',B.OLD_PIN+':src'): return (B.OLD_SOURCE_TREE+'\n').encode()
                    return git(repo,*args)
                # The optional original-object branch stays covered even after
                # that object has been pruned from this checkout.
                with patch.object(subprocess,'run',side_effect=present),patch.object(B,'git',side_effect=changed):
                    self.guard(lambda:V.check_source_drift(ROOT,self.surface),message)
        # A corrupt original object (exit 128) must not silently skip its tree binding.
        def corrupt(command,*args,**kwargs):
            if command == ['git','-C',str(ROOT/B.REPO),'rev-parse','--verify','--quiet',B.OLD_PIN+'^{commit}']:
                return subprocess.CompletedProcess(command,128,b'',b'fatal: corrupt')
            return run(command,*args,**kwargs)
        with patch.object(subprocess,'run',side_effect=corrupt):
            self.guard(lambda:V.check_source_drift(ROOT,self.surface),'folders: cannot inspect historical predecessor object')

    def test_published_predecessor_survives_missing_historical_commit(self):
        run,source = subprocess.run,B.source
        reads = []
        def pruned(command,*args,**kwargs):
            if command == ['git','-C',str(ROOT/B.REPO),'rev-parse','--verify','--quiet',B.OLD_PIN+'^{commit}']:
                return subprocess.CompletedProcess(command,1,b'',b'')
            return run(command,*args,**kwargs)
        def observed(root,path,pin=B.PIN):
            reads.append(pin)
            return source(root,path,pin)
        with patch.object(subprocess,'run',side_effect=pruned),patch.object(B,'source',side_effect=observed):
            self.assertEqual((0,PASS,''),self.run_check(lambda:V.check_source_drift(ROOT,self.surface)))
        self.assertIn(B.OLD_SOURCE_PIN,reads)
        self.assertNotIn(B.OLD_PIN,reads)

    def test_real_verifier_calls_source_drift_guard_and_deletion_control(self):
        with workspace_view() as root:
            builder = root/B.E/'build_candidate.py'
            source = builder.read_text()
            recorded = f"OLD_SOURCE_TREE = '{B.OLD_SOURCE_TREE}'"
            self.assertEqual(1,source.count(recorded))
            builder.write_text(source.replace(recorded,"OLD_SOURCE_TREE = '"+'0'*40+"'"))
            verifier = root/B.E/'verify_amendment.py'
            result = fixture_process(verifier,'--root',str(root))
            self.assertEqual((1,'','FAIL: folders: published predecessor src tree differs from recorded old pin\n'),(result.returncode,result.stdout,result.stderr))
            source = verifier.read_text()
            invocation = '    check_source_drift(root,surface)\n'
            self.assertEqual(1,source.count(invocation))
            verifier.write_text(source.replace(invocation,''))
            result = fixture_process(verifier,'--root',str(root))
            self.assertEqual((0,PASS,''),(result.returncode,result.stdout,result.stderr))

    def test_real_verifier_calls_declarations_guard_and_deletion_control(self):
        with workspace_view() as root:
            builder = root/B.E/'build_candidate.py'
            source = builder.read_text()
            source += '''\n_original_source_for_module_control = source
def source(root, path, pin=PIN):
    text = _original_source_for_module_control(root, path, pin)
    if path == 'src/Hexalith.Folders.Contracts/FoldersModule.cs' and pin == PIN:
        return text.replace('IdentifierKind.String', 'IdentifierKind.Ulid')
    return text
'''
            builder.write_text(source)
            verifier = root/B.E/'verify_amendment.py'
            result = fixture_process(verifier,'--root',str(root))
            self.assertEqual((1,'','FAIL: folders: module domain/String identifier declaration mismatch\n'),
                             (result.returncode,result.stdout,result.stderr))
            source = verifier.read_text()
            invocation = '    check_declarations(root,old,new,decl,surface)\n'
            self.assertEqual(1,source.count(invocation))
            verifier.write_text(source.replace(invocation,''))
            result = fixture_process(verifier,'--root',str(root))
            self.assertEqual((0,PASS,''),(result.returncode,result.stdout,result.stderr))

    def test_mcpcli_route_uses_committed_baseline_and_guard_removal(self):
        path = 'src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs'
        read,git = Path.read_text,B.git
        def working_tree(candidate,*args,**kwargs):
            if candidate == ROOT/path:
                raise AssertionError('route evidence read mutable working tree')
            return read(candidate,*args,**kwargs)
        with patch.object(Path,'read_text',working_tree):
            V.check_declarations(ROOT,self.old,self.new,self.decl,self.surface)
        def changed(repo,*args):
            data = git(repo,*args)
            return data.replace(b'new SubmitCommandRequest(',b'new InventedRequest(') if repo == ROOT and args == ('show',B.BASELINE+':'+path) else data
        with patch.object(B,'git',side_effect=changed):
            self.guard(lambda:V.check_declarations(ROOT,self.old,self.new,self.decl,self.surface),'folders: McpCli wire route evidence mismatch')

    def test_required_fence_attributes_and_guard_removal(self):
        source = B.source
        path = 'src/Hexalith.Folders.Client/Generated/HexalithFoldersClient.g.cs'
        for prop in ['expectedFileVersion','expectedLockFence']:
            with self.subTest(property=prop):
                before = f'JsonProperty("{prop}", Required = Newtonsoft.Json.Required.Always)'
                after = f'JsonProperty("{prop}", Required = Newtonsoft.Json.Required.DisallowNull)'
                self.assertIn(before,source(ROOT,path))
                def optional(root,name,pin=B.PIN):
                    text = source(root,name,pin)
                    return text.replace(before,after) if name == path and pin == B.PIN else text
                with patch.object(B,'source',side_effect=optional):
                    self.guard(lambda:V.check_source_drift(ROOT,self.surface),f'folders: FileMutationRequest.{prop} required fence semantics missing')

    def test_source_drift_fields_are_proved_against_both_git_pins(self):
        V.check_source_drift(ROOT,self.surface)
        original = B.source
        path = 'src/Hexalith.Folders.Client/Generated/HexalithFoldersClient.g.cs'
        def missing(root,name,pin=B.PIN):
            text = original(root,name,pin)
            return text.replace('JsonProperty("expectedFileVersion"','JsonProperty("removedExpectedVersion"') if name == path and pin == B.PIN else text
        with patch.object(B,'source',side_effect=missing):
            self.guard(lambda:V.check_source_drift(ROOT,self.surface),'folders: source drift FileMutationRequest.expectedFileVersion is not evidenced at both pins')

    def test_legacy_surface_drift_guard_removal(self):
        surface = copy.deepcopy(self.surface)
        surface[0]['invented-tool'] = 'invented.cs:1'
        self.guard(lambda:V.check_source_drift(ROOT,surface),'folders: source drift added, removed or renamed a legacy surface')

    def test_pinned_transport_defaults_and_internal_query_premise_guard_removal(self):
        source = B.source
        cases = [
            ('src/shared/AdapterCore/BearerTransportPolicy.cs','Uri.UriSchemeHttps','Uri.UriSchemeInvented',
             'folders: HTTPS/loopback credential source premise missing'),
            ('src/Hexalith.Folders.Server/FoldersServerServiceCollectionExtensions.cs',
             'IWorkspaceCommitExecutor, UnavailableWorkspaceCommitExecutor','IWorkspaceCommitExecutor, InventedExecutor',
             'folders: default implementation/commit-executor source premise missing'),
        ]
        for query in ['FolderFileOwnerRead','FolderFileReferenceRead','FolderOwnerRead']:
            cases.append((f'src/Hexalith.Folders.Server/Queries/{query}QueryHandler.cs','IDomainQueryHandler','IInventedQueryHandler',
                          f'folders: internal {query} query-handler premise missing'))
        for path,before,after,message in cases:
            with self.subTest(message=message):
                self.assertIn(before,source(ROOT,path))
                def damaged(root,name,pin=B.PIN):
                    text = source(root,name,pin)
                    return text.replace(before,after) if name == path and pin == B.PIN else text
                with patch.object(B,'source',side_effect=damaged):
                    self.guard(lambda:V.check_source_drift(ROOT,self.surface),message)

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
                root = Path(temp).resolve();e = root/B.E;e.mkdir(parents=True)
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

    def test_anchor_escape_and_source_anchor_guard_removal(self):
        evidence,source = B.evidence,B.source
        for escaped in ['../outside/FolderTools.cs','/outside/FolderTools.cs']:
            with self.subTest(path=escaped):
                anchor = escaped+':1'
                rows = self.changed('M03','Pinned evidence','`'+anchor+'`')
                rows['M03']['cells'][7] = '`'+anchor+'`'
                def resolved(root,path,pin=B.PIN):
                    # A reader that resolves the escaping path leaves only this guard.
                    return 'escaped source line\n' if path == escaped else source(root,path,pin)
                with patch.object(B,'evidence',side_effect=lambda root,key,*args:anchor if key == 'M03' else evidence(root,key,*args)),patch.object(B,'source',side_effect=resolved):
                    self.guard(lambda:V.check_anchors(ROOT,self.old,rows,self.decl,self.surface),'folders:M03: anchor path escapes source')
        rows = copy.deepcopy(self.new)
        rows['M03']['cells'][7] = '`src/Hexalith.Folders.Mcp/Tools/FolderTools.cs:1`'
        self.guard(lambda:V.check_anchors(ROOT,self.old,rows,self.decl,self.surface),'folders:M03: source anchor differs from pin')

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

    def guard(self,register,message,*,backstop=None):
        """Remove the live guard; a backstopped guard must yield its later refusal."""
        self.reject(register,message)
        original = L.require
        def removed(condition,actual):
            if actual != message: original(condition,actual)
        self.assertIs(L.verify.__globals__,L.__dict__)
        with patch.object(L,'require',side_effect=removed):
            expected = (0,LABEL_PASS,'') if backstop is None else (1,'','FAIL: '+backstop+'\n')
            self.assertEqual(expected,self.invoke_register(register))

    def test_register_schema_repository_base_and_readme_hash_guard_removal(self):
        cases = []
        register = copy.deepcopy(self.register); register['schemaVersion'] = '9.9.9'
        cases.append((register,'unsupported label register schema'))
        for key,value in [('baseRevision','0'*40),('repository','https://github.com/fixture-fork/Hexalith.Folders')]:
            register = copy.deepcopy(self.register); register['repository'][key] = value
            cases.append((register,'Folders label repository/base mismatch'))
        register = copy.deepcopy(self.register); register['repository']['readme']['beforeSha256'] = '0'*64
        cases.append((register,'folders: committed base or candidate README hash mismatch'))
        for register,message in cases:
            with self.subTest(message=message,repository=register['repository']):
                self.guard(register,message)

    def test_readme_section_conjuncts_and_partial_removal(self):
        message = 'folders: committed base or candidate README hash mismatch'
        for field,condition in [
            ('before',"before_section == files['README.before.section.md']"),
            ('after',"after_section == files['README.after.section.md']"),
        ]:
            with self.subTest(section=field):
                register = copy.deepcopy(self.register)
                item = register['repository'][field]
                path = self.root/item['path']
                original = path.read_bytes()
                data = original+b'Unapproved section prose.\n'
                path.write_bytes(data); item['sha256'] = B.sha(data)
                try:
                    self.reject(register,message)
                    with self.removed_condition(L,'verify',condition):
                        expected = ((0,LABEL_PASS,'') if field == 'after' else
                                    (1,'','FAIL: folders: compatibility retention semantics missing\n'))
                        self.assertEqual(expected,self.invoke_register(register))
                finally:
                    path.write_bytes(original)

    def test_row_binding_conjuncts_and_partial_removal(self):
        for row_index in [0,1]:
            for field,condition in [('repository',"row.get('repository') == 'folders'"),('surface',"row.get('surface') == old['surface']")]:
                with self.subTest(row=row_index,field=field):
                    register = copy.deepcopy(self.register)
                    row = register['rows'][row_index]; row[field] = 'Unrelated legacy surface'
                    self.reject(register,row['id']+': surface, owner or removal gate changed')
                    with self.removed_condition(L,'verify',condition):
                        self.assertEqual((0,LABEL_PASS,''),self.invoke_register(register))

    def test_unknown_register_state_entrypoints_and_guard_removal(self):
        register = copy.deepcopy(self.register); register['state'] = 'withdrawn'
        self.guard(register,'invalid label register state')
        (self.root/B.E/'labels.json').write_text(json.dumps(register,indent=2)+'\n')
        for script in ['verify_amendment.py','verify_labels.py']:
            with self.subTest(script=script):
                result = fixture_process(HERE/script,'--root',str(self.root))
                self.assertEqual((1,'','FAIL: invalid label register state\n'),(result.returncode,result.stdout,result.stderr))

    def test_standalone_integrated_register_forces_owner_approval_and_trigger_removal(self):
        register = copy.deepcopy(self.register); register['state'] = 'integrated'
        (self.root/B.E/'labels.json').write_text(json.dumps(register,indent=2)+'\n')
        self.assertFalse(V.completion_requested(self.root,False))
        expected = (1,'','FAIL: completion requires exact-byte owner approval and covered Folders roles\n')
        self.assertEqual(expected,invoke(L))
        script = self.root/B.E/'verify_labels.py'
        result = fixture_process(script,'--root',str(self.root))
        self.assertEqual(expected,(result.returncode,result.stdout,result.stderr))
        # Delete only the integrated-state trigger from the copied real entrypoint.
        source = script.read_text(encoding='utf-8')
        trigger = "register.get('state') == 'integrated' or "
        self.assertEqual(1,source.count(trigger))
        script.write_text(source.replace(trigger,''),encoding='utf-8')
        result = fixture_process(script,'--root',str(self.root))
        self.assertEqual((0,LABEL_PASS,''),(result.returncode,result.stdout,result.stderr))

    def test_label_artifact_path_guards_and_removal(self):
        register = copy.deepcopy(self.register); del register['repository']['before']['path']
        # Without its guard the damage is refused only by a non-actionable KeyError.
        self.guard(register,'label artifact path missing',backstop="'path'")
        item = self.register['repository']['before']
        with tempfile.TemporaryDirectory() as temp:
            outside = Path(temp).resolve()/'README.before.section.md'
            shutil.copyfile(self.root/item['path'],outside)
            # Both escapes name the exact approved bytes, so only the guard refuses them.
            for escaped in [str(self.root/item['path']),os.path.relpath(outside,self.root)]:
                with self.subTest(path=escaped):
                    register = copy.deepcopy(self.register); register['repository']['before']['path'] = escaped
                    self.guard(register,'label path escapes repository')

    def test_retained_authority_and_successor_hash_text_guard_removal(self):
        expected,files = L.B.label_candidate(self.root,B.sha((self.root/B.NEW).read_bytes()))
        row = self.register['rows'][0]
        for before,after in [('[technical-tools inventory 1.0.3]','[technical-tools inventory]'),
                             (row['gate'],'removal gate omitted'),
                             ('Folders inventory SHA-256: `','Folders inventory digest: `')]:
            with self.subTest(text=before):
                self.assertIn(before,row['label']['text'])
                register = copy.deepcopy(self.register)
                label = register['rows'][0]['label']
                label['text'] = label['text'].replace(before,after)
                # The builder target carries the same damage, so only this guard refuses it.
                target = copy.deepcopy(expected)
                next(r for r in target['rows'] if r['id'] == row['id'])['label'] = copy.deepcopy(label)
                with patch.object(L.B,'label_candidate',return_value=(target,files)):
                    self.guard(register,row['id']+': retained technical authority or successor hash missing')

    def test_exact_readme_patch_guard_removal(self):
        register = copy.deepcopy(self.register)
        item = register['repository']['patch']
        path = self.root/item['path']
        path.write_bytes(path.read_bytes()+b'--- a/src/Other.cs\n+++ b/src/Other.cs\n@@ -0,0 +1 @@\n+invented\n')
        item['sha256'] = B.sha(path.read_bytes())
        self.guard(register,'folders: patch is not exact README-only citation diff')

    def test_retention_semantics_guard_removal(self):
        register = copy.deepcopy(self.register)
        item = register['repository']['after']
        path = self.root/item['path']
        path.write_bytes(path.read_bytes().replace(b'They are not retired',b'They are retired'))
        item['sha256'] = B.sha(path.read_bytes())
        expected,files = L.B.label_candidate(self.root,B.sha((self.root/B.NEW).read_bytes()))
        files['README.after.section.md'] = path.read_bytes()
        with patch.object(L.B,'label_candidate',return_value=(expected,files)):
            self.guard(register,'folders: compatibility retention semantics missing')

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

    def test_pending_delivery_conjuncts_and_partial_removal(self):
        for field,value,condition in [
            ('inventoryRevision','1'*40,"register.get('inventoryRevision') is None"),
            ('deliveryAuthorization',{},"register.get('deliveryAuthorization') is None"),
            ('integration',{},"repo.get('integration') is None"),
        ]:
            with self.subTest(field=field):
                register = copy.deepcopy(self.register)
                target = register['repository'] if field == 'integration' else register
                target[field] = value
                self.reject(register,'pending label packet must not claim integration or delivery authorization')
                with self.removed_condition(L,'verify',condition):
                    self.assertEqual((0,LABEL_PASS,''),self.invoke_register(register))

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

    @contextlib.contextmanager
    def published_graph_fixture(self):
        """Read real published blobs/commits through an isolated owner Git graph.

        Only temporary refs and origin configuration are written. Neither owner
        source bytes nor root publication reads are substituted.
        """
        original = L.B.git
        register = json.loads(original(ROOT,'show',f'{PUBLISHED_LABEL_REVISION}:{B.E}/labels.json'))
        (self.root/B.E/'approval.json').write_bytes(original(ROOT,'show',f'{register["inventoryRevision"]}:{B.E}/approval.json'))
        owner_source = Path(register['repository']['ownerCheckout'])
        with tempfile.TemporaryDirectory() as temp:
            owner = Path(temp).resolve()
            original(owner,'init','--quiet')
            objects = Path(original(owner_source,'rev-parse','--git-path','objects').decode().strip())
            if not objects.is_absolute(): objects = owner_source/objects
            (owner/'.git/objects/info/alternates').write_text(str(objects.resolve())+'\n')
            original(owner,'remote','add','origin','https://github.com/Hexalith/Hexalith.Folders.git')
            original(owner,'update-ref','refs/remotes/origin/main',register['repository']['integration']['commit'])
            register['repository']['ownerCheckout'] = str(owner)
            yield register,owner,original

    def published_guard_control(self,register,message):
        expected = (1,'','FAIL: '+message+'\n')
        self.assertEqual(expected,self.invoke_register(register,True))
        original = L.require
        def removed(condition,actual):
            if actual != message: original(condition,actual)
        with patch.object(L,'require',side_effect=removed):
            integrated = LABEL_PASS.replace('candidate only; owner approval and delivery pending','integrated delivery verified')
            self.assertEqual((0,integrated,''),self.invoke_register(register,True))

    def test_real_publication_rejects_revision_before_inventory(self):
        with self.published_graph_fixture() as (register,owner,git):
            revision = git(ROOT,'rev-parse','85a5437b98d0e126147460ca1ee1fa6a36041a21^{commit}').decode().strip()
            register['inventoryRevision'] = revision
            message = f"git show {revision}:{B.NEW} failed: fatal: path '{B.NEW}' exists on disk, but not in '{revision}'"
            self.assertEqual((1,'','FAIL: '+message+'\n'),self.invoke_register(register,True))

    def test_real_publication_rejects_pending_receipt_and_guard_removal(self):
        with self.published_graph_fixture() as (register,owner,git):
            register['inventoryRevision'] = git(ROOT,'rev-parse','cab549c7b06fa4eef08e46cfcde038f62ea81fbf^{commit}').decode().strip()
            self.published_guard_control(register,f'{B.E}/approval.json: published artifact differs from owner-approved bytes')

    def test_real_delivery_rejects_old_readme_and_guard_removal(self):
        with self.published_graph_fixture() as (register,owner,git):
            register['repository']['integration'] = {'commit':B.LABEL_PIN,'commitSha256':B.sha(git(owner,'cat-file','commit',B.LABEL_PIN))}
            self.published_guard_control(register,'folders: integrated README bytes differ from candidate')

    def test_real_delivery_rejects_fork_origin_and_guard_removal(self):
        with self.published_graph_fixture() as (register,owner,git):
            git(owner,'remote','set-url','origin','https://github.com/fixture-fork/Hexalith.Folders.git')
            self.published_guard_control(register,'folders: checkout origin does not match owning repository')

    def test_real_delivery_rejects_commit_hash_and_guard_removal(self):
        with self.published_graph_fixture() as (register,owner,git):
            register['repository']['integration']['commitSha256'] = '0'*64
            self.published_guard_control(register,'folders: integrated commit byte hash mismatch')

    def test_real_delivery_rejects_abbreviated_commit_and_guard_removal(self):
        with self.published_graph_fixture() as (register,owner,git):
            register['repository']['integration']['commit'] = register['repository']['integration']['commit'][:12]
            self.published_guard_control(register,'folders: completion requires canonical integrated label commit')

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
            for authorization in [{},*[dict(register['deliveryAuthorization'],**{key:''}) for key in ['exactWords','source','approvedOn']]]:
                with self.subTest(authorization=authorization):
                    broken = copy.deepcopy(register); broken['deliveryAuthorization'] = authorization
                    self.assertEqual((1,'','FAIL: completion requires separate explicit label delivery authorization\n'),self.invoke_register(broken,True))
                    condition = "all(V.nonblank(auth.get(k)) for k in ['exactWords','source','approvedOn'])"
                    with self.removed_condition(L,'verify',condition):
                        self.assertEqual((0,integrated,''),self.invoke_register(broken,True))
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

    def test_completion_reports_later_owner_compatibility_drift(self):
        integrated = LABEL_PASS.replace('candidate only; owner approval and delivery pending','integrated delivery verified')
        with self.existing_graph_fixture() as (register,committed,owner,published,delivery,inventory,original):
            self.assertIn(b'They are not retired',committed(owner,'show','origin/main:README.md'))
            def relabelled(repo,*args):
                data = committed(repo,*args)
                return data.replace(b'They are not retired',b'They remain unretired') if repo == owner and args == ('show','origin/main:README.md') else data
            with patch.object(L.B,'git',side_effect=relabelled):
                self.assertEqual((0,integrated,'reported: folders: current origin/main compatibility labels differ from delivered candidate\n'),
                                 self.invoke_register(register,True))

    def test_source_commit_before_valid_readme_delivery_is_allowed(self):
        with self.existing_graph_fixture() as (register,committed,owner,published,delivery,inventory,original):
            # Historical base -> delivery contains an intervening source change;
            # delivery parent -> delivery changes only README.md.
            self.assertNotEqual(['README.md'],original(owner,'diff','--name-only',register['repository']['baseRevision'],delivery).decode().splitlines())
            self.assertEqual(['README.md'],original(owner,'diff','--name-only',delivery+'^',delivery).decode().splitlines())
            with patch.object(L.B,'git',side_effect=committed):
                self.assertEqual((0,LABEL_PASS.replace('candidate only; owner approval and delivery pending','integrated delivery verified'),''),self.invoke_register(register,True))

    def test_completion_rejects_rewritten_published_artifacts_and_half_removal(self):
        integrated = LABEL_PASS.replace('candidate only; owner approval and delivery pending','integrated delivery verified')
        halves = {'inventory':"B.sha(B.git(root,'show',f'{inv_revision}:{path}')) == digest",
                  'origin/main':"B.sha(B.git(root,'show',f'origin/main:{path}')) == digest"}
        condition = halves['inventory']+' and '+halves['origin/main']
        for path in [B.NEW,B.E/'approval.json']:
            for ref,half in halves.items():
                with self.subTest(path=path,ref=ref),self.existing_graph_fixture() as (register,committed,owner,published,delivery,inventory,original):
                    revision = inventory if ref == 'inventory' else 'origin/main'
                    def rewritten(repo,*args):
                        data = committed(repo,*args)
                        return data+b'rewritten after owner approval\n' if repo == self.root and args == ('show',f'{revision}:{path}') else data
                    with patch.object(L.B,'git',side_effect=rewritten):
                        self.assertEqual((1,'',f'FAIL: {path}: published artifact differs from owner-approved bytes\n'),self.invoke_register(register,True))
                        # Disable only this half; the other publication read stays enforced.
                        source = inspect.getsource(L.verify)
                        self.assertEqual(1,source.count(condition))
                        namespace = {}
                        exec(source.replace(condition,condition.replace(half,'True')),L.__dict__,namespace)
                        self.assertIs(namespace['verify'].__globals__,L.__dict__)
                        with patch.object(L,'verify',namespace['verify']):
                            self.assertEqual((0,integrated,''),self.invoke_register(register,True))

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
