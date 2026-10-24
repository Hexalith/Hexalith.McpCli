import datetime, json, pathlib, shlex, subprocess, sys, time
root = pathlib.Path('/home/administrator/projects/hexalith/mcpcli')
evidence = root / '_bmad-output/implementation-artifacts/evidence/story-4-12/review-pass-3-20261024'
evidence.mkdir(exist_ok=True)
label = sys.argv[1]
command = sys.argv[2:]
started = time.monotonic()
with (evidence / (label + '.stdout.txt')).open('wb') as output, (evidence / (label + '.stderr.txt')).open('wb') as error:
    result = subprocess.run(command, cwd=root, stdout=output, stderr=error, timeout=1200)
receipt = {'label': label, 'command': command, 'displayCommand': shlex.join(command), 'cwd': str(root), 'exitCode': result.returncode, 'elapsedSeconds': round(time.monotonic()-started,3), 'recordedAtUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'stdout': label+'.stdout.txt', 'stderr': label+'.stderr.txt'}
(evidence / (label+'.json')).write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
for channel in ('stdout','stderr'):
    content=(evidence / (label+'.'+channel+'.txt')).read_text()
    if content: print(channel+':\n'+content[-3000:])
sys.exit(result.returncode)
