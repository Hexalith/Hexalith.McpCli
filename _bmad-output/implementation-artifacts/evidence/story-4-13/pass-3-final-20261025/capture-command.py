import json,os,subprocess,sys,time
from pathlib import Path
root=Path('/home/administrator/projects/hexalith/mcpcli')
evidence=root/'_bmad-output/implementation-artifacts/evidence/story-4-13/pass-3-final-20261025'
name,*command=sys.argv[1:]
started=time.time()
with (evidence/(name+'.stdout.txt')).open('w') as stdout, (evidence/(name+'.stderr.txt')).open('w') as stderr:
    result=subprocess.run(command,cwd=root,stdout=stdout,stderr=stderr)
receipt=dict(command=command,exitCode=result.returncode,elapsedSeconds=round(time.time()-started,3))
(evidence/(name+'.command.json')).write_text(json.dumps(receipt,indent=2)+'\n')
print(name+': '+json.dumps(receipt),flush=True)
sys.exit(result.returncode)
