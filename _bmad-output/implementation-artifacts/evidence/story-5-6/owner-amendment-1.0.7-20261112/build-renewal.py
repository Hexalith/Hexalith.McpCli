"""Build the census 1.0.7 owner re-approval draft at the current root pins; nothing here grants approval.

1.0.7 re-adds, byte for byte, entries the owner already approved in the hash-only owner amendments
1.0.5 (archived upstream as unverified history) and 1.0.6 (never pushed). Each entry is included only when
its active classification rests solely on waiver amendments, its classification is unchanged, and the
current bytes are among those the owner approved. Everything else stays waiver-only and is listed in
remaining-waiver-only.json. Any unexpected chain, report, count or byte difference stops the build.
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
V1 = ROOT / 'tools/proprietary-surfaces/v1'
REPORT = OUT / 'source-census.json'
WAIVER = {'amendments/1.0.3.json', 'amendments/1.0.4.json', 'amendments/1.0.5.json', 'amendments/1.0.6.json'}
ARCHIVE = 'evidence/release-maintenance-20261112/foreign-1.0.5-assertions'
OUT_REL = str(OUT.relative_to(ROOT))
# The owner-approved amendments, their receipts, and the canonical authorization hashes the owner approved.
PRIOR = [
    {'version': '1.0.5', 'amendment': (f'{ARCHIVE}/1.0.5.json', 'd26229036f26d1354f0f174a978319b75fef0cac03d72ae5a4418b7f716a6d0e'),
     'receipt': f'{ARCHIVE}/1.0.5-approval.json',
     'authorizationSha256': '46167f41a77406075acc9e396308c75b138ac32c5382a756b27bfc7a65452345'},
    {'version': '1.0.6', 'amendment': (f'{OUT_REL}/prior-owner-1.0.6/1.0.6.json', 'f74ddbb7ccce917f32905fca3f48767d63678003e34ca0959b6630804ac29d6b'),
     'receipt': f'{OUT_REL}/prior-owner-1.0.6/1.0.6-approval.json',
     'authorizationSha256': '77457c135044faba86145c04944eec47394fe3143a693d609a00485975caac4f'},
]
EXPECTED = {'exclusions': 20, 'allowances': 1}
canonical = lambda value: json.dumps(value, sort_keys=True, separators=(',', ':'))
sha = lambda raw: hashlib.sha256(raw).hexdigest()
spec = importlib.util.spec_from_file_location('census', V1 / 'check.py')
census = importlib.util.module_from_spec(spec); spec.loader.exec_module(census)


def fail(message):
    sys.exit(f'renewal-build-refused: {message}')


report = json.loads(REPORT.read_text())
head = census.git(ROOT, 'rev-parse', '--verify', 'HEAD^{commit}')
parent = census.Tree(ROOT, head)
pins = {row['repository']: row['gitlink'] for row in report['repositories']}
if report['parentRevision'] != head or pins != census.declarations(parent):
    fail('the report is not the root declarations and gitlinks at HEAD')
if report['errors'] or any(entry['status'] == 'rejected' for entry in report['surfaces']):
    fail('the source report is not clean')
index = json.loads((V1 / 'amendments.json').read_text())
if [item['sha256'] for item in index] != [item['sha256'] for item in report['policy']['amendments']] \
        or report['policy']['version'] != '1.0.6' or index[-1]['path'] != 'amendments/1.0.6.json':
    fail('the amendment index is not the report chain ending at 1.0.6')

# Active policy, remembering which amendment last approved each entry.
policy = json.loads((V1 / 'baseline.json').read_text())
allowances = [('baseline', entry) for entry in policy['allowances']]
exclusions = [('baseline', entry) for entry in policy['exclusions']]
for item in index:
    raw = (V1 / item['path']).read_bytes()
    if sha(raw) != item['sha256']:
        fail(f'{item["path"]} does not match its index hash')
    amendment = json.loads(raw)
    removed = {canonical(surface) for surface in amendment['removeAllowances']}
    allowances = [(s, e) for s, e in allowances if canonical(e['surface']) not in removed] + [(item['path'], e) for e in amendment['addAllowances']]
    exclusions += [(item['path'], e) for e in amendment.get('addExclusions', [])]

# Prior owner approvals: exact amendment bytes, receipt binding, label, and the approved authorization hash.
prior_allowances, prior_exclusions, provenance = {}, {}, []
for prior in PRIOR:
    path, expected = prior['amendment']
    raw = (ROOT / path).read_bytes()
    receipt_raw = (ROOT / prior['receipt']).read_bytes()
    amendment, receipt = json.loads(raw), json.loads(receipt_raw)
    authorization = {key: amendment[key] for key in ('addAllowances', 'removeAllowances', 'addExceptions', 'removeExceptions', 'addExclusions')}
    if sha(raw) != expected or amendment['approval']['evidence']['sha256'] != sha(receipt_raw) \
            or canonical(receipt['authorization']) != canonical(authorization) \
            or sha(canonical(authorization).encode()) != prior['authorizationSha256'] \
            or receipt['owner'] != 'Requesting user, owning maintainer' or not receipt.get('approvalLabel', '').strip():
        fail(f'prior owner {prior["version"]} is not the exact approved bytes')
    for entry in amendment['addAllowances']:
        prior_allowances[canonical(entry['surface'])] = (prior['version'], entry)
    for entry in amendment['addExclusions']:
        if entry.get('scope') != 'file' or 'sourceRevision' in entry:
            fail(f'prior owner {prior["version"]} has a non hash-only exclusion')
        prior_exclusions.setdefault((entry['repository'], entry['prefix']), []).append((prior['version'], entry))
    provenance.append({'version': prior['version'], 'amendment': {'path': path, 'sha256': expected},
                       'receipt': {'path': prior['receipt'], 'sha256': sha(receipt_raw)},
                       'approvalLabel': receipt['approvalLabel'], 'authorizationSha256': prior['authorizationSha256']})

# Exclusions: every waiver-only file target, re-added verbatim from the latest owner entry covering its current bytes.
targets = {}
for source, entry in exclusions:
    targets.setdefault((entry['repository'], entry['prefix'], entry.get('scope', 'directory')), []).append((source, entry))
add_exclusions, remaining = [], {'allowances': [], 'exclusions': []}
for (repository, prefix, scope), entries in sorted(targets.items()):
    waiver_only = all(source in WAIVER for source, _ in entries)
    # A file whose current bytes were approved only by a waiver entry is also waiver-only for those bytes.
    current = sha(census.Tree(ROOT / repository, pins[repository]).blob(prefix)) if scope == 'file' else None
    covering = [s for s, e in entries if current and current in {e.get('sha256'), *e.get('additionalSha256', [])}
                and e.get('sourceRevision', pins[repository]) == pins[repository]]
    if not waiver_only and not (covering and all(s in WAIVER for s in covering)):
        continue
    classes = {(e['row'], e['classification']) for _, e in entries}
    owner = [(v, e) for v, e in prior_exclusions.get((repository, prefix), [])
             if current in {e['sha256'], *e.get('additionalSha256', [])}]
    if len(classes) == 1 and owner and {(e['row'], e['classification']) for _, e in owner} == classes:
        version, entry = owner[-1]
        add_exclusions.append(entry)
        continue
    row, classification = sorted(classes)[-1]
    remaining['exclusions'].append({'repository': repository, 'prefix': prefix, 'row': row, 'classification': classification,
                                    'approvedBy': sorted({s for s, _ in entries}),
                                    'why': 'owner approved a different classification or other bytes' if prior_exclusions.get((repository, prefix))
                                           else 'never owner-approved'})

# Allowances: a waiver allowance is re-added only when an owner entry has identical content apart from owner and reason.
add_allowances, remove_allowances = [], []
for source, entry in sorted(allowances, key=lambda pair: canonical(pair[1]['surface'])):
    if source not in WAIVER:
        continue
    prior = prior_allowances.get(canonical(entry['surface']))
    strip = lambda value: {k: v for k, v in value.items() if k not in ('owner', 'reason')}
    if prior and canonical(strip(prior[1])) == canonical(strip(entry)):
        add_allowances.append(prior[1])
        remove_allowances.append(entry['surface'])
        continue
    remaining['allowances'].append({'surface': entry['surface'], 'row': entry['row'], 'classification': entry['classification'],
                                    'approvedBy': source,
                                    'why': 'owner approved other source bytes' if prior else 'never owner-approved'})

if len(add_exclusions) != EXPECTED['exclusions'] or len(add_allowances) != EXPECTED['allowances']:
    fail(f'expected {EXPECTED} owner re-approvals, found {len(add_exclusions)} exclusions and {len(add_allowances)} allowances')

authorization = {'addAllowances': add_allowances, 'removeAllowances': remove_allowances, 'addExceptions': [],
                 'removeExceptions': [], 'addExclusions': add_exclusions}
(OUT / 'authorization.draft.json').write_text(json.dumps(authorization, indent=2, sort_keys=True) + '\n')
(OUT / 'prior-owner-approvals.json').write_text(json.dumps(provenance, indent=2, sort_keys=True) + '\n')
(OUT / 'remaining-waiver-only.json').write_text(json.dumps(remaining, indent=2, sort_keys=True) + '\n')
(OUT / 'source-checker.json').write_text(json.dumps({'path': 'tools/proprietary-surfaces/v1/check.py',
    'sha256': sha((V1 / 'check.py').read_bytes()), 'sourceReportSha256': sha(REPORT.read_bytes())}, indent=2, sort_keys=True) + '\n')
print('owner re-approvals: exclusions', len(add_exclusions), 'allowances', len(add_allowances))
print('remaining waiver-only: exclusions', len(remaining['exclusions']), 'allowances', len(remaining['allowances']))
print('authorization canonical sha256', sha(canonical(authorization).encode()))
