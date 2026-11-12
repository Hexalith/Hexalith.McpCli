"""Pin-move control: simulate a pin move for the 20 re-approved files without changing their bytes.

Usage: pin-move-control.py GATE OUT, where GATE is the dry-run-gate.py directory (active chain plus the draft)
and OUT is an empty directory outside the repository. Every revision-bound exclusion for a draft file is rebound
to a revision that no pin has, which is what a pin move does to it. Two scratch policies are written:
  OUT/with-draft     the merged policy with the draft's hash-only owner entries; the census should still pass
  OUT/without-draft  the same policy without those entries; the census should fail with one
                     excluded-source-revision-drift error per file
Then run check.py --baseline OUT/<variant>/baseline.json --amendments OUT/<variant>/amendments.json for each.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
DRAFT = Path(__file__).resolve().parent / 'authorization.draft.json'
MOVED = '0' * 40

if len(sys.argv) != 3:
    sys.exit('usage: pin-move-control.py GATE OUT')
gate, out = (Path(value).resolve() for value in sys.argv[1:])
if ROOT in (out, *out.parents) or (out.exists() and any(out.iterdir())):
    sys.exit('control-refused: OUT must be an empty directory outside the repository')
policy = json.loads((gate / 'baseline.json').read_text())
draft = json.loads(DRAFT.read_text())['addExclusions']
targets = {(entry['repository'], entry['prefix']) for entry in draft}
rebound = 0
for entry in policy['exclusions']:
    if (entry['repository'], entry['prefix']) in targets and 'sourceRevision' in entry:
        entry['sourceRevision'] = MOVED
        rebound += 1
variants = {'with-draft': policy['exclusions'],
            'without-draft': [entry for entry in policy['exclusions'] if entry not in draft]}
for name, exclusions in variants.items():
    (out / name).mkdir(parents=True)
    (out / name / 'baseline.json').write_text(json.dumps({**policy, 'exclusions': exclusions}, indent=2, sort_keys=True) + '\n')
    (out / name / 'amendments.json').write_text('[]\n')
print(json.dumps({'files': len(targets), 'reboundEntries': rebound,
                  'exclusions': {name: len(exclusions) for name, exclusions in variants.items()}}))
