"""Deterministically inspect inline/image/reference Markdown destinations, excluding fenced examples."""
from pathlib import Path
from urllib.parse import urlsplit
import re,json,hashlib,sys

def scan(raw):
 text=raw.decode('utf-8');links=[];fence=None
 for number,line in enumerate(text.splitlines(),1):
  marker=re.match(r'^\s{0,3}(`{3,}|~{3,})',line)
  if marker:
   value=marker[1]
   if fence is None:fence=value
   elif value[0]==fence[0] and len(value)>=len(fence):fence=None
   continue
  if fence is not None:continue
  destinations=[('inline',m.group(1).strip('<>')) for m in re.finditer(r'!?\[[^\]\n]*\]\(\s*(<[^>\n]+>|[^\s)]+)',line)]
  reference=re.match(r'^\s{0,3}\[[^\]]+\]:\s*(<[^>]+>|\S+)',line)
  if reference:destinations.append(('reference',reference[1].strip('<>')))
  for kind,destination in destinations:
   links.append(dict(line=number,kind=kind,destination=destination,relative=not destination.startswith('#') and not urlsplit(destination).scheme))
 return dict(schema='mcpcli-readme-link-scan/v1',readme_sha256=hashlib.sha256(raw).hexdigest(),destinations=links,relative_destinations=[v for v in links if v['relative']])
if __name__=='__main__':
 path=Path(sys.argv[1]);result=scan(path.read_bytes());Path(sys.argv[2]).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print('destinations',len(result['destinations']),'relative',len(result['relative_destinations']))
