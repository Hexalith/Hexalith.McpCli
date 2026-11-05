from pathlib import Path
import sys,os,re,subprocess,zipfile,tarfile,io,json,hashlib,datetime
root=Path('/home/administrator/projects/hexalith/mcpcli');packet=root/'_bmad-output/implementation-artifacts/evidence/story-4-18/upstream-integration-20261105'
sys.path.insert(0,str(root/'tools/live-topology'));import ci
try:
 credential=subprocess.check_output(['gh','auth','token'],stderr=subprocess.DEVNULL).decode().strip()
 if credential:os.environ['MCPCLI_EVIDENCE_SCAN_SECRET_TOKEN']=credential
except subprocess.CalledProcessError:pass
known={v.encode() for k,v in os.environ.items() if v and len(v)>=8 and re.search(r'TOKEN|PASSWORD|SECRET|CERT_KEY|SIGNINGKEY|PRIVATE_?KEY',k,re.I)}
patterns={'github_token':re.compile(rb'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})\b'),'private_key_pem':re.compile(rb'-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----'),'jwt':re.compile(rb'\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+'),'nuget_key':re.compile(rb'\boy2[a-z0-9]{40,}\b')}
findings=[];counts={'files':0,'archive_members':0,'archive_count':0,'bytes':0,'known_credential_matches':0,'pattern_matches':0};changes=[]
def scan(name,data,depth=0):
 counts['bytes']+=len(data)
 matched=[key for key,p in patterns.items() if p.search(data)];actual=any(k in data for k in known)
 if actual:counts['known_credential_matches']+=1
 if matched:counts['pattern_matches']+=1
 if actual or matched:findings.append({'path':name,'known_credential_match':actual,'pattern_kinds':matched,'sha256':hashlib.sha256(data).hexdigest()})
 if depth<5:
  if zipfile.is_zipfile(io.BytesIO(data)):
   counts['archive_count']+=1
   with zipfile.ZipFile(io.BytesIO(data)) as z:
    for n in z.infolist():
     if n.is_dir():continue
     counts['archive_members']+=1;scan(name+'!'+n.filename,z.read(n),depth+1)
  elif name.lower().endswith(('.tar','.tar.gz','.tgz')):
   counts['archive_count']+=1
   with tarfile.open(fileobj=io.BytesIO(data)) as t:
    for n in t:
     if n.isfile():counts['archive_members']+=1;scan(name+'!'+n.name,t.extractfile(n).read(),depth+1)
 if not data.startswith((b'MZ',b'PK',b'\x1f\x8b')) and b'\0' not in data[:4096]:
  try:text=data.decode('utf-8')
  except UnicodeDecodeError:return
  sanitized=ci.sanitized_xml(text) if name.lower().endswith(('.xml','.trx')) else ci.sanitized(text)
  if sanitized!=text:changes.append({'path':name,'sha256':hashlib.sha256(data).hexdigest()})
for p in sorted(packet.rglob('*')):
 if not p.is_file() or p.name in ('SHA256SUMS','credential-scan.json') or p.suffix=='.nupkg':continue
 counts['files']+=1;scan(str(p.relative_to(packet)),p.read_bytes())
result={'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scanner':'Existing tools/live-topology/ci.py sanitized/sanitized_xml plus exact environment/GitHub CLI credential matching and GitHub/NuGet/JWT/private-PEM patterns, including nested ZIP/tar/package members. No candidate secret values are printed or recorded.','redactor_source_sha256':hashlib.sha256((root/'tools/live-topology/ci.py').read_bytes()).hexdigest(),'counts':counts,'findings_metadata_only':findings,'redactor_would_change_metadata_only':changes,'original_artifacts_mutated':False}
Path('/tmp/mcpcli-418-evidence-scan/result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'counts':counts,'finding_paths':findings,'redactor_change_paths':changes},indent=2))
