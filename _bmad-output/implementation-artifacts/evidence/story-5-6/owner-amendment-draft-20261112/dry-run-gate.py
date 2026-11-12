"""Coverage dry run: merge the active policy and the draft into a scratch baseline; no approval receipt is created.

Usage: dry-run-gate.py DIR, where DIR is an empty directory outside the repository. Then run
  python3 tools/proprietary-surfaces/v1/check.py --baseline DIR/baseline.json --amendments DIR/amendments.json --output DIR/census.json
The merge applies each indexed amendment as check.py's load_policy does: index hashes must match, and every
allowance or exception removal must name exactly one existing entry. Chain validity (header, receipt binding,
authorization equality and authority lineage) is rehearsed separately by assemble-amendment.py --rehearse.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
V1 = ROOT / 'tools/proprietary-surfaces/v1'
DRAFT = Path(__file__).resolve().parent / 'authorization.draft.json'
key = lambda value: json.dumps(value, sort_keys=True)

if len(sys.argv) != 2:
    sys.exit('usage: dry-run-gate.py DIR')
GATE = Path(sys.argv[1]).resolve()
if ROOT in (GATE, *GATE.parents) or (GATE.exists() and any(GATE.iterdir())):
    sys.exit('dry-run-refused: DIR must be an empty directory outside the repository')

policy = json.loads((V1 / 'baseline.json').read_text())
amendments = []
for item in json.loads((V1 / 'amendments.json').read_text()):
    raw = (V1 / item['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != item['sha256']:
        sys.exit(f'dry-run-refused: {item["path"]} does not match its index hash')
    amendments.append(json.loads(raw))
for amendment in amendments + [json.loads(DRAFT.read_text())]:
    for field, entries in (('removeAllowances', 'allowances'), ('removeExceptions', 'exceptions')):
        for removal in amendment[field]:
            if sum(key(entry['surface']) == key(removal) for entry in policy[entries]) != 1:
                sys.exit(f'dry-run-refused: {field} entry does not name exactly one existing entry')
        removed = {key(removal) for removal in amendment[field]}
        policy[entries] = [entry for entry in policy[entries] if key(entry['surface']) not in removed]
    policy['allowances'] += amendment['addAllowances']
    policy['exceptions'] += amendment['addExceptions']
    policy['exclusions'] += amendment.get('addExclusions', [])
GATE.mkdir(parents=True, exist_ok=True)
(GATE / 'baseline.json').write_text(json.dumps(policy, indent=2, sort_keys=True) + '\n')
(GATE / 'amendments.json').write_text('[]\n')
print(json.dumps({'allowances': len(policy['allowances']), 'exclusions': len(policy['exclusions']),
                  'exceptions': len(policy['exceptions']),
                  'baselineSha256': hashlib.sha256((GATE / 'baseline.json').read_bytes()).hexdigest()}))
