import datetime
import json
from pathlib import Path
import subprocess
import sys
import time

root = Path('/home/administrator/projects/hexalith/mcpcli')
evidence = root / '_bmad-output/implementation-artifacts/evidence/epic-4-retro-item-4-f4'
evidence.mkdir(parents=True, exist_ok=True)
name, *command = sys.argv[1:]
cwd = Path('/tmp') if name.endswith('focused-inventory') else root
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
tick = time.monotonic()
with (evidence / (name + '.stdout.txt')).open('w') as stdout, (evidence / (name + '.stderr.txt')).open('w') as stderr:
    result = subprocess.run(command, cwd=cwd, stdout=stdout, stderr=stderr)
receipt = dict(command=command, cwd=str(cwd), started_utc=started,
               exit_code=result.returncode, elapsed_seconds=round(time.monotonic() - tick, 3))
(evidence / (name + '.json')).write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt))
for stream in ('stdout', 'stderr'):
    lines = (evidence / (name + '.' + stream + '.txt')).read_text().splitlines()
    if lines:
        print(stream + ':\n' + '\n'.join(lines[-10:]))
sys.exit(result.returncode)
