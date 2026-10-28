import importlib.util, io, json, pathlib, unittest
root=pathlib.Path('/home/administrator/projects/hexalith/mcpcli')
spec=importlib.util.spec_from_file_location('test_ci', root/'tools/live-topology/test_ci.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
cases=[
('platform', "sys.version_info < (3, 11, 4) or platform.system() != 'Linux' or platform.machine() != 'x86_64'", 'False', 'test_platform_and_python_patch_prerequisites_stop_before_commands'),
('compression', "not ctypes.util.find_library(library)", 'False', 'test_compression_libraries_are_required_before_commands'),
('dapr-cli', "not re.search(r'CLI version: 1\\.18\\.2\\s', tools['dapr'] + '\\n')", 'False', 'test_dapr_cli_and_initialized_runtime_are_independently_required'),
('daprd', 'not daprd.is_file()', 'False', 'test_dapr_cli_and_initialized_runtime_are_independently_required'),
('embedded-bundle', "not {'dcp/dcp', 'dashboard/Aspire.Dashboard'} <= set(expected_bundle)", 'False', 'test_incomplete_embedded_bundle_stops_before_builds'),
('source-git', " or not (checkout / '.git').exists()", '', 'test_missing_git_marker_and_symlinked_source_stop_before_builds'),
('source-symlink', ' or checkout.is_symlink()', '', 'test_missing_git_marker_and_symlinked_source_stop_before_builds'),
('diagnostic-run-symlink', ' and not run.is_symlink()', '', 'test_diagnostic_copy_excludes_symlinked_runs_and_files'),
('diagnostic-file-symlink', ' and not path.is_symlink()', '', 'test_diagnostic_copy_excludes_symlinked_runs_and_files'),
('smoke-count', 'len(runs) != 1', 'False', 'test_smoke_requires_exactly_one_runtime_receipt'),
]
for name, fragment in [('expected-count','len(expected) != 21 or '),('expected-unique','len(set(expected)) != 21 or '),('coverage',"lane.get('coverage') != expected"),('lane-result',"lane.get('result') != 'passed'"),('passed-count',"lane.get('passed') != 21"),('failed-count',"lane.get('failed') != 0"),('operation',"sorted(item.get('operation', '') for item in outcomes) != expected"),('exit'," or item.get('exitCode') != 0")]:
    cases.append((name,fragment,'' if fragment.endswith(' or ') or fragment.startswith(' or ') else 'False','test_each_vector_acceptance_field_is_independently_required'))
results=[]
for name, old,new,method in cases:
    class Mutant(m.CiHooksTests):
        def setUp(self):
            super().setUp()
            p=self.tools/'ci.py';s=p.read_text();assert old in s,old;p.write_text(s.replace(old,new,1))
    output=io.StringIO();r=unittest.TextTestRunner(stream=output).run(unittest.TestSuite([Mutant(method)]))
    results.append({'mutation':name,'detected':not r.wasSuccessful(),'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'output':output.getvalue()})
    print(name, 'DETECTED' if not r.wasSuccessful() else 'SURVIVED',flush=True)
pathlib.Path('/tmp/mcpcli-414-mutations.json').write_text(json.dumps(results,indent=2)+'\n')
raise SystemExit(any(not row['detected'] for row in results))
