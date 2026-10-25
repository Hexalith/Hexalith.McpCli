import json,subprocess,sys
from pathlib import Path
root=Path('/home/administrator/projects/hexalith/mcpcli')
path=root/'tools/live-topology'
output=root/'_bmad-output/implementation-artifacts/evidence/story-4-13/pass-3-patches-20261025'
cases=[
('passing-binding-removed','test_live_runner','run_live',"report['binding'] = selection_binding(selected[0])","binding = selection_binding(selected[0])",'RunnerTests.test_successful_main_retains_bound_inputs_and_passing_phases'),
('subset-grants-full-acceptance','test_lane','lane',"not args.operation and report['failed'] == 0 and report['passed'] == len(report['coverage'])","report['failed'] == 0 and report['passed'] == len(report['vectors'])",'LaneTests.test_success_requires_fresh_binding_case_and_owned_cleanup'),
('diagnostic-omitted','test_live_runner','run_live',"print(report['error'].replace(token, '<redacted>') if token else report['error'])","pass",'RunnerTests.test_failing_preflight_invalidates_receipt_and_redacts_identity'),
('empty-selector-accepted','test_lane','lane',"if args.operation is not None:","if args.operation:",'LaneTests.test_unknown_or_empty_selector_starts_no_topology'),
('missing-runtime-preflights','test_lane','lane',"if not args.preflight_only and not os.environ.get('MCPCLI_ISOLATED_RUNTIME_DIR', '').strip():","if False:",'LaneTests.test_missing_runtime_fails_before_preflight_or_child')]
results=[]
for name,test_module,module_name,before,after,test in cases:
    script='''import pathlib,sys,unittest
sys.path.insert(0,sys.argv[1])
tests=__import__(sys.argv[2]); module=getattr(tests,sys.argv[3])
source=pathlib.Path(module.__file__).read_text(); before,after=sys.argv[4:6]
assert before in source
source=source.replace(before,after,1)
if sys.argv[6].endswith('test_successful_main_retains_bound_inputs_and_passing_phases'):
 source=source.replace("if expected != report['binding']:","if expected != binding:")
exec(compile(source,module.__file__,'exec'),module.__dict__)
suite=unittest.defaultTestLoader.loadTestsFromName(sys.argv[6],tests)
result=unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
'''
    command=[sys.executable,'-c',script,str(path),test_module,module_name,before,after,test]
    with (output/(name+'.stdout.txt')).open('w') as stdout,(output/(name+'.stderr.txt')).open('w') as stderr:
        completed=subprocess.run(command,cwd=root,stdout=stdout,stderr=stderr,timeout=60)
    results.append(dict(mutation=name,source=str(getattr(__import__('pathlib'),'Path')(path/('run-vectors.py' if module_name=='lane' else 'run_live.py')).relative_to(root)),before=before,after=after,test=test,exitCode=completed.returncode,detected=completed.returncode==1))
    assert completed.returncode==1,name
(output/'mutation-audit.json').write_text(json.dumps(dict(result='passed',mutations=results),indent=2)+'\n')
print('All five focused Python mutations detected; repository files and runtime binaries were unchanged.')
