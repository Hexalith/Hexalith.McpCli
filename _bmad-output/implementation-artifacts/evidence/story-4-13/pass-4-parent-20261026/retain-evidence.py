"""Retain sanitized private receipts and compact duplicate immutable live inputs."""
import hashlib,json,re,shutil,tarfile
from pathlib import Path
root=Path('/home/administrator/projects/hexalith/mcpcli')
out=Path(__file__).resolve().parent
for name in ('live-inputs.tar.gz','runtime-diagnostics.tar.gz'):
    archive=out/name
    if archive.exists() or archive.is_symlink():
        raise SystemExit(f'Refusing to overwrite retained evidence: {archive}')
runtime=Path('/tmp/mcpcli-413-pass4-runtime-20261026/runtime')
lane=json.loads((out/'live/live-lane.json').read_text())
assert lane['result'] in ('passed','failed')
runs=set()
for vector in lane['vectors']:
    lines=(out/'live'/vector['output']/'child.stdout.txt').read_text().splitlines()
    runs.update(Path(line.removeprefix('Isolated run: ')) for line in lines if line.startswith('Isolated run: '))
lines=(out/'smoke.stdout.txt').read_text().splitlines()
runs.update(Path(line.removeprefix('Isolated run: ')) for line in lines if line.startswith('Isolated run: '))
assert len(runs)==22
secret_patterns=[re.compile(rb'-----BEGIN (?:RSA |EC )?PRIVATE KEY-----'),re.compile(rb'Bearer\s+[A-Za-z0-9_-]{16,}\.'),re.compile(rb'eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}')]
for run in sorted(runs):
    assert run.parent==runtime/'runs'
    receipt=json.loads((run/'result.json').read_text())
    assert receipt['ownedInfrastructureStopped']==dict(sentry=0,redis=0,placement=0,scheduler=0)
    target=out/'private-runtime-receipts'/run.name; target.mkdir(parents=True,exist_ok=True)
    for name in ['result.json','initial-empty.rdb','initial-redis-backup.json']:
        shutil.copyfile(run/name,target/name)
    logs=out/'runtime-diagnostics'/run.name; logs.mkdir(parents=True,exist_ok=True)
    for source in [run/'command.stdout.txt',run/'command.stderr.txt',*run.glob('*.log')]:
        if source.is_file():
            content=source.read_bytes()
            assert not any(pattern.search(content) for pattern in secret_patterns),str(source)
            shutil.copyfile(source,logs/source.name)
archives=[]
for name,files in [('live-inputs.tar.gz',sorted(path for path in out.rglob('*') if path.is_file() and 'inputs' in path.relative_to(out).parts)),('runtime-diagnostics.tar.gz',sorted((out/'runtime-diagnostics').rglob('*')))]:
    files=[path for path in files if path.is_file()]
    manifest={str(path.relative_to(out)):hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    archive=out/name
    with tarfile.open(archive,'w:gz') as tar:
        for path in files: tar.add(path,arcname=str(path.relative_to(out)),recursive=False)
    with tarfile.open(archive,'r:gz') as tar:
        actual={member.name:hashlib.sha256(tar.extractfile(member).read()).hexdigest() for member in tar.getmembers()}
    assert actual==manifest
    for path in files: path.unlink()
    archives.append(dict(path=name,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),files=manifest))
for path in out.rglob('*'):
    if path.is_file() and path.suffix in ('.txt','.json','.xml'):
        assert not any(pattern.search(path.read_bytes()) for pattern in secret_patterns),str(path)
(out/'retention-audit.json').write_text(json.dumps(dict(result='passed',privateRuns=22,credentialPatternMatches=0,archives=archives),indent=2)+'\n')
print('Retained 22 private ownership/backup receipts; archived and byte-verified immutable inputs and sanitized runtime diagnostics.')
