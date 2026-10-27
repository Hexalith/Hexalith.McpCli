import json, os, pathlib, subprocess, sys, time
root = pathlib.Path('/home/administrator/projects/hexalith/mcpcli')
evidence = root / '_bmad-output/implementation-artifacts/evidence/story-4-14/review-patches-20261027'
environment = os.environ.copy()
# Exercise the real first-install path without changing any installed launcher.
environment['PATH'] = os.pathsep.join(directory for directory in environment['PATH'].split(os.pathsep)
                                       if not (pathlib.Path(directory) / 'aspire').is_file())
environment['ASPIRE_EVIDENCE_PATH'] = 'TestResults/live-ci-review-patches-20261027'
for name in ('MCPCLI_CI_PREPARATION', 'GITHUB_ENV', 'GITHUB_ACTIONS', 'RUNNER_ENVIRONMENT'):
    environment.pop(name, None)
records = []
for name, script in [('prepare', 'prepare-ci.sh'), ('run', 'run-ci.sh')]:
    started = time.time()
    print('Starting exact CI hook: ' + script, flush=True)
    with (evidence / ('live-' + name + '.stdout.txt')).open('w') as stdout, (evidence / ('live-' + name + '.stderr.txt')).open('w') as stderr:
        result = subprocess.run(['bash', 'tools/live-topology/' + script], cwd=root, env=environment,
                                stdout=stdout, stderr=stderr)
    records.append({'command': ['bash', 'tools/live-topology/' + script],
                    'environment': {'ASPIRE_EVIDENCE_PATH': environment['ASPIRE_EVIDENCE_PATH'],
                                    'existingAspireHiddenFromPath': True},
                    'exitCode': result.returncode, 'elapsedSeconds': round(time.time() - started, 3)})
    (evidence / 'live-commands.json').write_text(json.dumps(records, indent=2) + '\n')
    print(script + ' exited ' + str(result.returncode), flush=True)
    if result.returncode: sys.exit(result.returncode)
