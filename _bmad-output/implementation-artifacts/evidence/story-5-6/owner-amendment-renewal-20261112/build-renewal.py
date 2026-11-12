"""Build the census 1.0.5 renewal draft at the current root pins; nothing here grants approval.

The draft renews only what the source report names: revision-bound exclusions whose pin moved,
and allowances whose bound source bytes changed. Each entry keeps its row, classification and
signal set. Any unexpected root, chain, observation, error, path or hash difference stops the build.
Git reads use the census's own isolated helper.
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
OWNER = 'Requesting user, owning maintainer'
canonical = lambda value: json.dumps(value, sort_keys=True, separators=(',', ':'))
sha = lambda raw: hashlib.sha256(raw).hexdigest()
spec = importlib.util.spec_from_file_location('census', V1 / 'check.py')
census = importlib.util.module_from_spec(spec); spec.loader.exec_module(census)


def fail(message):
    sys.exit(f'renewal-build-refused: {message}')


report = json.loads(REPORT.read_text())
head = census.git(ROOT, 'rev-parse', '--verify', 'HEAD^{commit}')
if report['parentRevision'] != head:
    fail('report parent revision is not HEAD')
parent = census.Tree(ROOT, head)
declared = census.declarations(parent)
pins = {row['repository']: row['gitlink'] for row in report['repositories']}
if pins != declared:
    fail('the report does not cover exactly the root declarations and gitlinks at HEAD')

# Active policy: baseline plus every indexed amendment; the index must be the report's chain ending at 1.0.4.
index = json.loads((V1 / 'amendments.json').read_text())
if [item['sha256'] for item in index] != [item['sha256'] for item in report['policy']['amendments']] \
        or report['policy']['version'] != '1.0.4' or index[-1]['path'] != 'amendments/1.0.4.json':
    fail('the amendment index is not the report chain ending at 1.0.4')
policy = json.loads((V1 / 'baseline.json').read_text())
active, chain_exclusions = list(policy['allowances']), list(policy['exclusions'])
for item in index:
    raw = (V1 / item['path']).read_bytes()
    if sha(raw) != item['sha256']:
        fail(f'{item["path"]} does not match its index hash')
    amendment = json.loads(raw)
    removed = {canonical(surface) for surface in amendment['removeAllowances']}
    active = [entry for entry in active if canonical(entry['surface']) not in removed] + amendment['addAllowances']
    chain_exclusions += amendment.get('addExclusions', [])

# Reviewed byte changes; every other renewed exclusion must keep the bytes of its latest approval.
CHANGED = {
    ('references/Hexalith.FrontComposer', '.github/workflows/quality.yml'):
        'Reviewed change: SDK 11.0.100 with the supported range gate moved to [11.0.100, 11.0.200); '
        'Builds initialize-dotnet pinned from @main to a commit; an extra setup-dotnet 10.0.404 install and .NET 10 '
        'runtime step; Aspire CLI 13.6.5; and a test artifact flag. No publication, packing or container step added.',
    ('references/Hexalith.Projects', '.github/workflows/ci.yml'):
        'Reviewed change: Builds pins and Dapr 1.19.1 bumps, additional SDK 10.0.404, Aspire CLI 13.6.5, extra unit '
        'tests, an EventStore --unshallow history fetch, the G6 policy moved to the repository-local '
        'tools/qualification/g6-current-policy-2026-11-12-dapr-net1191.json, and the source-mapping step now builds the '
        'Builds hexalith-module CLI and runs the built DLL. No publication target added.',
}
drifted = [error for error in report['errors'] if error.get('rule') == 'excluded-source-revision-drift:' + error.get('path', '')]
if len(drifted) != 20 or len(report['errors']) != 20:
    fail('the report errors are not exactly the 20 expected revision-bound exclusion renewals')

exclusions = []
for error in sorted(drifted, key=lambda e: (e['repository'], e['path'])):
    repository, path = error['repository'], error['path']
    approved = [entry for entry in chain_exclusions if entry['repository'] == repository and entry['prefix'] == path
                and entry.get('scope') == 'file' and 'sourceRevision' in entry]
    if not approved or len({(entry['row'], entry['classification']) for entry in approved}) != 1:
        fail(f'{repository} {path} has no single approved revision-bound classification')
    latest = approved[-1]
    current = sha(census.Tree(ROOT / repository, pins[repository]).blob(path))
    unchanged = current in {latest['sha256'], *latest.get('additionalSha256', [])}
    if unchanged == ((repository, path) in CHANGED):
        fail(f'{repository} {path} byte change does not match the reviewed list')
    reason = (f'Renewal at the current root pin of the {latest["row"]} {latest["classification"]} exclusion last bound '
              f'to {latest["sourceRevision"]}. ')
    reason += CHANGED.get((repository, path), 'Bytes unchanged since that entry.')
    exclusions.append({'repository': repository, 'prefix': path, 'row': latest['row'], 'classification': latest['classification'],
                       'owner': OWNER, 'reason': reason, 'scope': 'file', 'sha256': current, 'sourceRevision': pins[repository]})
if set(CHANGED) - {(entry['repository'], entry['prefix']) for entry in exclusions}:
    fail('a reviewed change names a file the report does not renew')

COMPOSITION = 'src/Hexalith.Platform.Composition/Hexalith.Platform.Composition.csproj'
REVIEWED_CLOSURE = {'changed': ['src/Hexalith.Platform.Composition/WorksPreviewModel.cs'],
                    'added': ['src/Hexalith.Platform.Composition/WorksPreviewManagedRuntime.cs']}
rejected = [entry for entry in report['surfaces'] if entry['status'] == 'rejected']
expected = {('references/Hexalith.Memories', 'tools/release-containers.json', 'publication', 'mcp'),
            ('references/Hexalith.Platform', COMPOSITION, 'project', 'Hexalith.Platform.Composition')}
if {tuple(entry['surface'][k] for k in ('repository', 'path', 'kind', 'identity')) for entry in rejected} != expected:
    fail('rejected observations are not exactly the two expected source renewals')

workspace = census.Workspace(ROOT, parent, declared)
add, remove = [], []
for entry in sorted(rejected, key=lambda e: canonical(e['surface'])):
    if entry.get('reason') != 'allowance-signal-or-source-drift' or entry.get('unexpectedSignals'):
        fail(f'{entry["surface"]} is not a source-only drift')
    matching = [allowance for allowance in active if canonical(allowance['surface']) == canonical(entry['surface'])]
    if len(matching) != 1 or sorted(matching[0]['signals']) != sorted(entry['signals']):
        fail(f'{entry["surface"]} has no single active allowance with the same signal set')
    renewed = json.loads(canonical(matching[0]))
    repository, project = entry['surface']['repository'], entry['surface']['path']
    tree = census.Tree(ROOT / repository, pins[repository])
    if renewed.get('compilationClosure'):
        closure = census.compilation_closure(tree, project, census.Resolver(workspace, repository, tree))
        approved_hashes = {source['path']: source['sha256'] for source in renewed['sources']}
        delta = {'changed': sorted(s['path'] for s in closure if s['path'] in approved_hashes and approved_hashes[s['path']] != s['sha256']),
                 'added': sorted(s['path'] for s in closure if s['path'] not in approved_hashes)}
        removed_members = sorted(set(approved_hashes) - {s['path'] for s in closure})
        # The closure delta must be exactly the reviewed eff9e909 change, and the report must name it.
        if project != COMPOSITION or delta != REVIEWED_CLOSURE or removed_members \
                or sorted(delta['changed'] + delta['added']) != sorted(entry['changedSources']):
            fail(f'{project} compilation closure delta differs from the reviewed eff9e909 change')
        renewed['sources'] = closure
        detail = ('Compilation closure renewed at the current Platform pin after the reviewed eff9e909 change: it adds '
                  'the internal WorksPreviewManagedRuntime.cs helper, which runs dotnet --list-runtimes to align Works '
                  'development hosts with the qualified runtime, and updates WorksPreviewModel.cs. Same signal set; '
                  'no MCP, CLI or publication capability.')
    else:
        sources = [{'path': source['path'], 'sha256': sha(tree.blob(source['path']))} for source in renewed['sources']]
        if [s['path'] for s, old in zip(sources, renewed['sources']) if s['sha256'] != old['sha256']] != ['tools/release-containers.json'] \
                or entry['changedSources'] != ['tools/release-containers.json']:
            fail(f'{project} changed sources differ from the reviewed buildsSha update')
        renewed['sources'] = sources
        detail = ('Source hash renewed at the current Memories pin; the reviewed change only updates the recorded '
                  'buildsSha, with the same publication entries and signal set.')
    renewed['owner'] = OWNER
    renewed['reason'] = f'Renewal of the {renewed["row"]} {renewed["classification"]} allowance. ' + detail
    remove.append(matching[0]['surface'])
    add.append(renewed)

authorization = {'addAllowances': add, 'removeAllowances': remove, 'addExceptions': [], 'removeExceptions': [],
                 'addExclusions': exclusions}
(OUT / 'authorization.draft.json').write_text(json.dumps(authorization, indent=2, sort_keys=True) + '\n')
(OUT / 'source-checker.json').write_text(json.dumps({'path': 'tools/proprietary-surfaces/v1/check.py',
    'sha256': sha((V1 / 'check.py').read_bytes()), 'sourceReportSha256': sha(REPORT.read_bytes())}, indent=2, sort_keys=True) + '\n')
print('allowance renewals', len(add), 'exclusion renewals', len(exclusions),
      'changed files', sum(1 for e in exclusions if 'Reviewed change' in e['reason']))
print('authorization canonical sha256', sha(canonical(authorization).encode()))
