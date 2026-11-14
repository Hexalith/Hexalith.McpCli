#!/usr/bin/env python3
"""Capture Story 5.8 gates and audit their exact streams and protected bytes.

Run from the repository root with a UTF-8 locale:
python3 -B -I _bmad-output/implementation-artifacts/evidence/story-5-8/review-pass4-20261114/verify_packet.py
Use --audit-only to validate retained captures without rerunning the gates.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import unittest

sys.dont_write_bytecode = True
SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parents[5]
OUT = SCRIPT.parent
E = Path('_bmad-output/implementation-artifacts/evidence/story-5-8')
ART = E.parents[1]
AD = Path('_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22')
BASELINE = 'a92a2969db6903b8c6cca7e437446167e135ec9d'
NEW = ART/'folders-migration-inventory-v1.1.0.md'
SPEC = ART/'spec-5-8-refresh-and-re-disposition-the-folders-inventory.md'
INPUTS = [E/name for name in ['build_candidate.py','verify_amendment.py','verify_labels.py',
          'test_verify_amendment.py','delivery/lifecycle-proof.py']]+[
    ART/'evidence/story-5-2/verify_class_map.py',
    ART/'evidence/story-5-7/verify_labels.py',ART/'evidence/story-5-7/verify_amendments.py',
    Path('scripts/scan-evidence-secrets.py'),Path('scripts/evidence_redaction.py'),SCRIPT.relative_to(ROOT)]
PROTECTED = [NEW,E/'approval.json',E/'labels.json',ART/'folders-migration-inventory-v1.md',
    AD/'AD-23-non-gateway-capability-classes.md',AD/'AD-23-capability-class-map.json',
    ART/'evidence/story-5-2/approval.json',ART/'evidence/story-5-2/main-integration.json',
    ART/'technical-tools-migration-inventory-v1.0.3.md',ART/'evidence/story-5-7/approval.json',
    ART/'evidence/story-5-7/labels.json',*[E/'upstream/folders'/name for name in
        ['README.before.section.md','README.after.section.md','README.patch']]]
SYMLINK_TESTS = ['test_label_artifact_path_guards_and_removal',
    'test_completion_rejects_rewritten_published_artifacts_and_half_removal',
    'test_completion_reports_later_owner_compatibility_drift',
    'test_lifecycle_proof_rejects_child_candidate_mutation_without_writes',
    'test_lifecycle_proof_rejects_child_workflow_mutation_without_writes',
    'test_lifecycle_proof_rejects_each_damaged_setup_without_writes']
INVENTORY_PASS = ('PASS: folders: 161 entries, pinned declarations/anchors/drift, AD-23 dispositions and complete hash chain\n'
                  'PASS: owner decision: approved; approved completion verified\n').encode()
LABEL_PASS = b'PASS: Story 5.7 register chain; PS10/PS11 Folders 1.1.0 README-only citation patch; integrated delivery verified\n'
AD23_PASS = ''.join('PASS: '+str(ART/name)+': '+counts+'\n' for name,counts in [
    ('eventstore-admin-migration-inventory-v1.md','71 classified rows + 20 non-operation records = 91'),
    ('technical-tools-migration-inventory-v1.md','28 classified rows + 40 non-operation records = 68'),
    ('folders-migration-inventory-v1.md','103 classified rows + 58 non-operation records = 161'),
    ('projects-migration-inventory-v1.md','46 classified rows + 6 non-operation records = 52'),
    ('frontcomposer-migration-inventory-v1.md','26 classified rows + 4 non-operation records = 30'),
    ('chatbot-migration-inventory-v1.md','39 classified rows + 9 non-operation records = 48'),
    ('memories-migration-inventory-v1.md','39 classified rows + 12 non-operation records = 51'),
    ('parties-migration-inventory-v1.md','20 classified rows + 4 non-operation records = 24'),
]).encode()+b'PASS: exact-byte partition verified; effective decision status: adopted; parity remains a separate gate\n'
MATRIX = {
    'Complete candidate': ['test_deterministic_candidate_and_all_disposition_branches','test_real_candidate_and_completion_process_streams'],
    'Invented or undecorated replacement': ['test_real_process_rejects_damaged_rows_and_invented_replacement','test_decorated_type_wire_route_key_and_owner_eligibility_guards'],
    'Damaged row, anchor, drift, class, gap or chain': ['test_duplicate_and_damaged_rows_rejected_with_guard_controls','test_anchor_and_drift_guards','test_k12_catalog_hold_diagnostics_and_empty_gap_owner','test_pending_approved_role_and_chain_controls','test_approval_receipt_conjuncts_and_partial_removal'],
    'Completion without approval or label': ['test_standalone_completion_does_not_bypass_owner_approval','test_completion_requires_label_integration_after_owner_approval','test_completion_chain_and_exact_delivery_bytes','test_pending_delivery_conjuncts_and_partial_removal','test_row_binding_conjuncts_and_partial_removal'],
}


def require(condition,message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path,value):
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def git(*args):
    return subprocess.run(['git','-c','core.commitGraph=false',*args],cwd=ROOT,check=True,capture_output=True).stdout


def input_hashes():
    return {str(path):sha((ROOT/path).read_bytes()) for path in INPUTS}


def test_names():
    suite = unittest.TestLoader().discover(str(ROOT/E),pattern='test_*.py')
    def leaves(items):
        for item in items:
            if isinstance(item,unittest.TestSuite): yield from leaves(item)
            else: yield str(item)
    return list(leaves(suite))


def check_tests(data,names,label):
    # Only the runtime is variable. Every test name, outcome, separator and
    # summary byte must match; errors, skips and extra diagnostics are refused.
    prefix = ''.join(name+' ... ok\n' for name in names)+'\n'+'-'*70+'\n'
    expected = re.escape(prefix)+r'Ran '+str(len(names))+r' tests in [0-9]+\.[0-9]+s\n\nOK\n'
    require(re.fullmatch(expected,data.decode('utf-8')) is not None,label+': exact unittest stderr mismatch')


def commands():
    python = ['python3','-B','-I']
    tests = python+['-m','unittest','discover','-v','-s',str(E),'-p','test_*.py']
    lifecycle = ("from pathlib import Path; import importlib.util; p=Path("+repr(str(E/'delivery/lifecycle-proof.py'))+
        "); s=importlib.util.spec_from_file_location('lifecycle58pass4',p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); raise SystemExit(m.main(delivery=Path("+repr(str(OUT.relative_to(ROOT)))+")))")
    untracked = """import subprocess
prefix = ['git', '-c', 'core.commitGraph=false']
paths = subprocess.run(prefix+['ls-files', '--others', '--exclude-standard', '-z'], check=True, capture_output=True).stdout.split(b'\\0')
for path in paths:
    if path:
        result = subprocess.run(prefix+['diff', '--no-index', '--check', '--', '/dev/null', path.decode()], capture_output=True)
        if result.returncode or result.stdout or result.stderr:
            raise SystemExit('untracked whitespace check failed: '+path.decode())
"""
    return [
        ('tests',tests,{}),('lifecycle',python+['-c',lifecycle],{}),
        ('inventory',python+[str(E/'verify_amendment.py')],{}),
        ('labels',python+[str(E/'verify_labels.py')],{}),
        ('inventory-ascii-locale',python+['-X','utf8=0',str(E/'verify_amendment.py')],{'LC_ALL':'C'}),
        ('labels-ascii-locale',python+['-X','utf8=0',str(E/'verify_labels.py')],{'LC_ALL':'C'}),
        ('ad23',python+[str(ART/'evidence/story-5-2/verify_class_map.py')],{}),
        ('symlink-temp-tests',tests+[item for name in SYMLINK_TESTS for item in ['-k',name]],{}),
        ('whitespace',['git','-c','core.commitGraph=false','diff','--check',BASELINE],{}),
        ('untracked-whitespace',python+['-c',untracked],{}),
    ]


def capture():
    before = input_hashes()
    manifest = {'head':git('rev-parse','HEAD').decode().strip(),'baselineCommit':BASELINE,'inputs':before,'commands':[]}
    for name,command,environment in commands():
        with tempfile.TemporaryDirectory() as temp:
            if name == 'symlink-temp-tests':
                directory = Path(temp); (directory/'real').mkdir()
                (directory/'link').symlink_to(directory/'real',target_is_directory=True)
                environment = dict(environment,TMPDIR=str(directory/'link'))
            started = time.monotonic()
            result = subprocess.run(command,cwd=ROOT,capture_output=True,env=dict(os.environ,**environment))
        entry = {'name':name,'command':command,'cwd':str(ROOT),'environment':environment,
                 'exitCode':result.returncode,'elapsedSeconds':round(time.monotonic()-started,3)}
        for stream in ['stdout','stderr']:
            data = getattr(result,stream)
            path = OUT/(name+'.'+stream+'.txt'); path.write_bytes(data)
            entry[stream] = {'path':str(path.relative_to(ROOT/E)),'sha256':sha(data)}
        manifest['commands'].append(entry)
        write(OUT/'commands.json',manifest)
        print(name+': exit '+str(result.returncode),flush=True)
        require(result.returncode == 0,name+': gate failed; inspect retained streams')
    require(input_hashes() == before,'executable inputs changed during capture')


def audit():
    manifest = read(OUT/'commands.json')
    require(manifest['inputs'] == input_hashes(),'recorded executable inputs differ from current files')
    expected_commands = commands()
    require([row['name'] for row in manifest['commands']] == [row[0] for row in expected_commands],'gate manifest coverage/order mismatch')
    names = test_names()
    streams = {}
    for row,(name,command,environment) in zip(manifest['commands'],expected_commands):
        require(row['exitCode'] == 0 and row['command'] == command and row['cwd'] == str(ROOT),name+': gate command/result mismatch')
        expected_environment = dict(environment)
        if name == 'symlink-temp-tests':
            require(isinstance(row['environment'].get('TMPDIR'),str) and row['environment']['TMPDIR'].endswith('/link'),'symlink TMPDIR missing')
            expected_environment['TMPDIR'] = row['environment']['TMPDIR']
        require(row['environment'] == expected_environment,name+': environment mismatch')
        streams[name] = {}
        for stream in ['stdout','stderr']:
            item = row[stream]
            expected_path = OUT/(name+'.'+stream+'.txt')
            require(item['path'] == str(expected_path.relative_to(ROOT/E)),name+': stream path mismatch')
            data = expected_path.read_bytes()
            require(sha(data) == item['sha256'],name+': '+stream+' hash mismatch')
            streams[name][stream] = data
        stdout,stderr = streams[name]['stdout'],streams[name]['stderr']
        if name in {'tests','symlink-temp-tests'}:
            require(stdout == b'',name+': exact stdout mismatch')
            selected = names if name == 'tests' else [test for test in names if any(method in test for method in SYMLINK_TESTS)]
            require(bool(selected),name+': no test methods selected')
            check_tests(stderr,selected,name)
        elif name != 'lifecycle':
            expected_stdout = INVENTORY_PASS if name.startswith('inventory') else LABEL_PASS if name.startswith('labels') else AD23_PASS if name == 'ad23' else b''
            require(stdout == expected_stdout,name+': exact stdout mismatch')
            require(stderr == b'',name+': exact stderr mismatch')
    summary = read(OUT/'lifecycle-integrated.json')
    child_streams = {}
    for stream in ['stdout','stderr']:
        path = OUT/('lifecycle-integrated.'+stream+'.txt')
        child_streams[stream] = path.read_bytes()
        require(summary[stream] == {'path':path.name,'sha256':sha(child_streams[stream])},'lifecycle child '+stream+' binding mismatch')
    require(child_streams['stdout'] == b'','lifecycle child: exact stdout mismatch')
    check_tests(child_streams['stderr'],names,'lifecycle child')
    expected_summary = {
        'suiteExitCode':0,'claim':'Suite independence from synthetic lifecycle metadata; real approved-completion is verified separately.',
        'sourceFixture':'approved / integrated / spec done / sprint done','realInputsUnchanged':True,
        'candidateSha256':sha((ROOT/NEW).read_bytes()),
        'child':{'command':[sys.executable,'-I','-m','unittest','discover','-v','-s',str(E),'-p','test_*.py'],
                 'cwd':'.','cwdBase':'isolated synthetic lifecycle workspace created by this helper'},
        'helper':{'command':['python3','-B','-I',str(E/'delivery/lifecycle-proof.py')],
                  'cwd':'.','cwdBase':'repository root containing this retained script'},
        **{stream:summary[stream] for stream in ['stdout','stderr']},
    }
    require(summary == expected_summary,'lifecycle summary differs from expected proof')
    expected_stdout = (json.dumps(expected_summary,indent=2)+'\n'+'\n'.join(child_streams['stderr'].decode('utf-8').splitlines()[-5:])+'\n').encode()
    require(streams['lifecycle'] == {'stdout':expected_stdout,'stderr':b''},'lifecycle: exact stdout/stderr mismatch')
    protected = {}
    for path in PROTECTED:
        data = (ROOT/path).read_bytes()
        require(data == git('show','HEAD:'+str(path)),str(path)+': protected bytes differ from HEAD')
        protected[str(path)] = {'sha256':sha(data),'equalsHead':True}
    def frozen(data):
        return data.split(b'<frozen-after-approval',1)[1].split(b'</frozen-after-approval>',1)[0]
    require(frozen((ROOT/SPEC).read_bytes()) == frozen(git('show',BASELINE+':'+str(SPEC))),'frozen intent changed')
    passed = {name.split(' ',1)[0] for name in names}
    coverage = {scenario:{name:name in passed for name in methods} for scenario,methods in MATRIX.items()}
    require(all(all(methods.values()) for methods in coverage.values()),'matrix test coverage missing')
    result = {'baselineCommit':BASELINE,'headAtCapture':manifest['head'],
        'commandsInManifest':len(manifest['commands']),'commandsWithBothStreamHashesAndExactContentVerified':len(streams),
        'executableInputHashesRecorded':len(manifest['inputs']),'executableInputsEqualCurrent':True,
        'suiteTestsRan':len(names),'suiteSkips':0,'lifecycleSuiteTestsRan':len(names),
        'lifecycleRealInputsUnchanged':True,'symlinkTempTestsRan':len(SYMLINK_TESTS),
        'matrixCoverage':coverage,'matrixRowsAllPassed':True,'protectedArtifacts':protected,
        'protectedArtifactsAllEqualHead':True,'frozenIntentUnchanged':True}
    write(OUT/'audit.json',result)
    print('PASS: '+str(len(streams))+' exact gate streams, '+str(len(PROTECTED))+' protected artifacts, '+str(len(names))+' tests and synthetic lifecycle verified')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit-only',action='store_true')
    args = parser.parse_args()
    try:
        if not args.audit_only: capture()
        audit()
    except (ValueError,OSError,KeyError,subprocess.CalledProcessError) as error:
        print('FAIL: '+str(error),file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
