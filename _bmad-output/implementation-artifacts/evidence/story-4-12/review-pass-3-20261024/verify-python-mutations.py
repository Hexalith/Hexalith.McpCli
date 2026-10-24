import hashlib, json, pathlib, shutil, subprocess, tempfile
root=pathlib.Path('/home/administrator/projects/hexalith/mcpcli')
evidence=root/'_bmad-output/implementation-artifacts/evidence/story-4-12/review-pass-3-20261024'
source=root/'tools/live-topology'
original=(source/'run-isolated.py').read_text()
mutations=[]
for variable in ('NAMESPACE','DAPR_CONTROLPLANE_TRUST_DOMAIN','DAPR_CONTROLPLANE_NAMESPACE'):
    statement="    environment['"+variable+"'] = '"+('public' if variable.endswith('TRUST_DOMAIN') else 'default')+"'\n"
    mutated=original.replace(statement,'',1)
    if variable == 'NAMESPACE': mutated=mutated.replace("                    'NAMESPACE': 'default',\n",'')
    mutations.append((variable.lower(),mutated,'test_wrapper_pins_the_effective_child_environment_to_private_services'))
for variable,file in [('DAPR_TRUST_ANCHORS','ca.crt'),('DAPR_CERT_CHAIN','issuer.crt'),('DAPR_CERT_KEY','issuer.key')]:
    statement="                    '"+variable+"': (certificate_dir / '"+file+"').read_text(),\n"
    mutations.append((variable.lower(),original.replace(statement,'',1),'test_wrapper_pins_the_effective_child_environment_to_private_services'))
mutations.append(('wrong-placement-port',original.replace("'HEXALITH_EVENTSTORE_TEST_PLACEMENT_PORT': '6050'","'HEXALITH_EVENTSTORE_TEST_PLACEMENT_PORT': '50005'"),'test_wrapper_pins_the_effective_child_environment_to_private_services'))
for label,statement in [
    ('missing-sentry-exit-guard',"                    if process.poll() is not None:\n                        raise RuntimeError(f'Sentry exited before generating certificates: {process.returncode}')\n"),
    ('missing-certificate-timeout',"                    if time.monotonic() >= deadline:\n                        raise TimeoutError('Private Sentry certificates were not ready')\n"),
    ('missing-daemon-exit-guard',"                for name, process in processes.items():\n                    if process.poll() is not None:\n                        raise RuntimeError(f'{name} exited before prerequisites were ready: {process.returncode}')\n"),
    ('missing-port-timeout',"                    if time.monotonic() >= deadline:\n                        raise TimeoutError(f'Private prerequisite port {port} did not become reachable')\n"),
]:
    mutations.append((label,original.replace(statement,'',1),'test_wrapper_refuses_readiness_failures_before_starting_the_child'))
results=[]
for label,mutated,test in mutations:
    if mutated == original: raise RuntimeError('No mutation applied: '+label)
    with tempfile.TemporaryDirectory(prefix='mcpcli-pass3-mutation-') as directory:
        target=pathlib.Path(directory)
        for filename in ('bootstrap-runtime.py','binaries.json','test_runtime.py'):
            shutil.copyfile(source/filename,target/filename)
        (target/'run-isolated.py').write_text(mutated)
        command=['python3',str(target/'test_runtime.py'),'RuntimeTests.'+test]
        result=subprocess.run(command,text=True,capture_output=True,timeout=25)
        (evidence/(label+'.mutation.stdout.txt')).write_text(result.stdout)
        (evidence/(label+'.mutation.stderr.txt')).write_text(result.stderr)
        results.append({'mutation':label,'command':command,'mutatedWrapperSha256':hashlib.sha256(mutated.encode()).hexdigest(),'test':test,'exitCode':result.returncode,'rejected':result.returncode!=0,'stdout':label+'.mutation.stdout.txt','stderr':label+'.mutation.stderr.txt'})
        if result.returncode == 0: raise RuntimeError('Mutation survived: '+label)
(evidence/'python-mutation-controls.json').write_text(json.dumps(results,indent=2)+'\n')
print(f'{len(results)} of {len(results)} Python guard mutations rejected in temporary tool copies.')
