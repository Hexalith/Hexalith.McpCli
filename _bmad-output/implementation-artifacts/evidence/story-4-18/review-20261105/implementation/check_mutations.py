import hashlib, importlib.util, io, json, pathlib, sys, types, unittest
from unittest.mock import patch
root=pathlib.Path('/home/administrator/projects/hexalith/mcpcli')
sys.path[:0]=[str(root/'scripts/tests'),str(root/'scripts')]
import test_paired_publication as tests
import test_bootstrap_release as shell
from paired_release import module
source_path=root/'scripts/verify-paired-publication.py'
source=source_path.read_text()
results=[]
for name, old, new, method in [
 ('recording-credential-guard-removed','if redact_operator(serialized) != serialized:', 'if False:', 'test_fresh_credentials_are_refused_and_redacted_without_changing_originals'),
 ('retention-redaction-removed','retained = redact_operator(normalized) if redacted else decoded','retained = normalized if redacted else decoded','test_fresh_credentials_are_refused_and_redacted_without_changing_originals'),
 ('historical-system-read-reintroduced',"tenant.get('tenant') != session['selected_tenant'] or", "tenant.get('tenant') != 'system' or",'test_complete_preflight_and_exact_byte_two_pushes_verify_signed_public_contents'),
 ('tenant-read-equality-removed',"tenant.get('tenant') != session['selected_tenant'] or ", '', 'test_operator_decision_requires_fresh_complete_hash_bound_actual_sessions'),
]:
 assert source.count(old)==1,name
 mutant=types.ModuleType('verify_paired_publication'); mutant.__file__=str(source_path)
 exec(compile(source.replace(old,new),str(source_path),'exec'),mutant.__dict__)
 def modules(filename): return mutant if filename=='verify-paired-publication' else module(filename)
 cls=tests.PublicationTests if method.startswith(('test_complete','test_operator_decision')) else tests.PublicationBoundaryTests
 stream=io.StringIO()
 with patch.object(tests,'module',side_effect=modules):
  result=unittest.TextTestRunner(stream=stream,verbosity=2).run(cls(method))
 detected=not result.wasSuccessful()
 results.append({'mutation':name,'detected':detected,'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors)})
 print(name, 'DETECTED' if detected else 'MISSED')
 assert detected,name
original=shell.BootstrapReleaseTests.paired_controls
roots=[]
def broken_selector(instance,*args):
 original(instance,*args)
 path=instance.root/'scripts/release-publish.sh'
 code=path.read_text(); old='if [ "$release_phase" = paired ]; then'; assert code.count(old)==1
 path.write_text(code.replace(old,'if [ "$release_phase" = broken-paired ]; then'))
 roots.append(instance.root)
case=tests.PublicationTests('test_configured_shell_hooks_publish_both_exact_archives_and_complete_outcome')
case.setUp(); detected=False
try:
 with patch.object(shell.BootstrapReleaseTests,'paired_controls',new=broken_selector):
  try: case.test_configured_shell_hooks_publish_both_exact_archives_and_complete_outcome()
  except AssertionError as error:
   assert 'publishCmd:' in str(error),str(error)
   detected=True
 assert detected
 log=roots[0]/'dotnet.log'
 calls=[json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
 assert not calls,calls
 results.append({'mutation':'real-paired-publish-shell-selector-broken','detected':True,'fake_pushes':len(calls),'real_network':False,'real_pushes':0})
 print('real-paired-publish-shell-selector-broken DETECTED (zero fake pushes)')
finally: case.doCleanups()
output=pathlib.Path(__file__).with_name('mutations.json')
output.write_text(json.dumps({'source_sha256':hashlib.sha256(source.encode()).hexdigest(),'results':results},indent=2)+'\n')
