"""Bind current unresolved observations to committed source, without granting authority."""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path.cwd()
PACKET = Path(__file__).resolve().parent
report = json.loads((PACKET / 'census.json').read_text())
baseline = json.loads((ROOT / 'tools/proprietary-surfaces/v1/baseline.json').read_text())
owners = {entry['repository']: entry['owner'] for entry in baseline['roots']}
spec = importlib.util.spec_from_file_location('census', ROOT / 'tools/proprietary-surfaces/v1/check.py')
census = importlib.util.module_from_spec(spec)
spec.loader.exec_module(census)
trees = {}
decisions = []
for category, entries in (
        ('rejected-observation', [entry for entry in report['surfaces'] if entry['status'] == 'rejected']),
        ('inspection-error', report['errors'])):
    for entry in entries:
        surface = entry.get('surface', {})
        repository = surface.get('repository', entry.get('repository'))
        if repository not in trees:
            trees[repository] = census.Tree(ROOT / repository, entry['gitlink'])
        tree = trees[repository]
        paths = set(entry.get('sources', []))
        if entry.get('path'):
            paths.add(entry['path'])
        if surface.get('path'):
            paths.add(surface['path'])
        rule = entry.get('rule', '')
        for path in tree.entries:
            if rule.endswith(':' + path) or ':' + path + ':' in rule:
                paths.add(path)
        bindings = []
        for path in sorted(paths):
            committed = tree.entries.get(path)
            if committed and committed[0] in ('100644', '100755'):
                bindings.append({'path': path, 'gitBlob': committed[2],
                                 'sha256': hashlib.sha256(tree.blob(path)).hexdigest()})
            else:
                bindings.append({'path': path, 'regularCommittedSource': False})
        decisions.append({'category': category, 'repository': repository,
                          'gitlink': entry['gitlink'], 'owner': owners[repository],
                          'observation': entry, 'sourceBindings': bindings,
                          'newAuthority': None,
                          'decisionRequired': 'Provide committed source proof or a specifically approved versioned disposition; retain refusal until resolved.'})
result = {'schema': 'mcpcli-census-acceptance-blockers/v1',
          'parentRevision': report['parentRevision'], 'utcDate': report['utcDate'],
          'reportSha256': hashlib.sha256((PACKET / 'census.json').read_bytes()).hexdigest(),
          'policy': report['policy'], 'decisions': decisions}
(PACKET / 'acceptance-blockers.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps({'rejected': sum(entry['category'] == 'rejected-observation' for entry in decisions),
                  'inspectionErrors': sum(entry['category'] == 'inspection-error' for entry in decisions)}))
