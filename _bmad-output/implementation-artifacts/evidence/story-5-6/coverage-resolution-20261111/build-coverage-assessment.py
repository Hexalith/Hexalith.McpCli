"""Account for every prior coverage error and retain exact committed sources."""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re

ROOT = Path.cwd()
PACKET = Path(__file__).resolve().parent
PRIOR = PACKET.parent / 'implementation-resume-20261111'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
canonical = lambda value: json.dumps(value, sort_keys=True, separators=(',', ':'))


def write(name, value):
    (PACKET / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


spec = importlib.util.spec_from_file_location('census', ROOT / 'tools/proprietary-surfaces/v1/check.py')
census = importlib.util.module_from_spec(spec)
spec.loader.exec_module(census)
before = json.loads((PRIOR / 'census.json').read_text())
after = json.loads((PACKET / 'census.json').read_text())
prior_blockers = json.loads((PRIOR / 'acceptance-blockers.json').read_text())
current_blockers = json.loads((PACKET / 'acceptance-blockers.json').read_text())
prior_by_observation = {canonical(row['observation']): row for row in prior_blockers['decisions']
                        if row['category'] == 'inspection-error'}
current_errors = {canonical(row): row for row in after['errors']}
assert len(prior_by_observation) == len(before['errors']) == 111
assert {row['repository']: row['gitlink'] for row in before['repositories']} == {
    row['repository']: row['gitlink'] for row in after['repositories']}
trees = {}


def bindings(entry):
    surface = entry.get('surface', {})
    repository = surface.get('repository', entry.get('repository'))
    revision = entry['gitlink']
    tree = trees.setdefault((repository, revision), census.Tree(ROOT / repository, revision))
    paths = {entry.get('path'), surface.get('path'), *entry.get('sources', [])} - {None}
    rule = entry.get('rule', '')
    paths.update(path for path in tree.entries if rule.endswith(':' + path) or ':' + path + ':' in rule)
    for path in list(paths):
        if census.PROJECT.search(path):
            for name in ('Directory.Build.props', 'Directory.Build.targets'):
                candidates = [(ancestor / name).as_posix() for ancestor in PurePosixPath(path).parents]
                nearest = next((candidate for candidate in candidates if candidate in tree.entries), None)
                if nearest:
                    paths.add(nearest)
    # Preserve locally declared property provenance without interpreting or
    # opening a nested/external import. Exact blobs, rather than snippets, bind it.
    metadata = [path for path, entry in tree.entries.items()
                if entry[0] in ('100644', '100755') and path.lower().endswith(('.props', '.targets'))]
    for _ in range(8):
        names = {name.lower() for path in paths if path in tree.entries and tree.entries[path][0] in ('100644', '100755')
                 for name in re.findall(r'\$\(([A-Za-z_][\w.]*)\)', tree.text(path))}
        additions = {path for path in metadata if any(re.search(r'<\s*' + re.escape(name) + r'(?:\s|>)', tree.text(path), re.I)
                                                    for name in names)}
        if additions <= paths:
            break
        paths.update(additions)
    return [dict(path=path, gitBlob=tree.entries[path][2], sha256=sha(tree.blob(path)))
            if path in tree.entries and tree.entries[path][0] in ('100644', '100755')
            else dict(path=path, regularCommittedSource=False) for path in sorted(paths)]


definitions = {
    'external-import-layout': ('protected-source-boundary',
        'Inherited import alternatives escape the owning committed root; local source does not prove the external file or its classification.',
        'Keep refusal. The owning maintainer should provide root-contained committed metadata, or propose a separately approved generic cross-root import contract. Do not inspect nested or sibling worktrees.'),
    'nested-publication-target': ('protected-source-boundary',
        'Committed script resolves an exact target under a nested gitlink, which is deliberately unopened.',
        'Keep refusal. Move ownership/verification to the owning root or obtain an explicit source-boundary design decision; do not initialize the nested repository.'),
    'external-compile-source': ('protected-source-boundary',
        'Compile metadata selects nested, external or unresolved property-selected source; committed local bytes do not establish its compilation closure.',
        'Keep refusal. Supply an approved root-contained committed source closure or redesign the upstream qualification source selection.'),
    'runtime-generated-target': ('protected-source-boundary',
        'The project is generated in a runtime temporary directory; the committed source does not provide the actual project/blob closure.',
        'Keep refusal. The owning maintainer should check in an inspectable fixture or propose an explicit generic generated-source contract; a historical fixture label grants no exemption.'),
    'powershell-target-evaluation': ('scanner-limitation',
        'Source uses PowerShell variables, cmdlets, property access, functions or collection iteration outside the supported shell resolver.',
        'Add a separately tested bounded PowerShell model only if it preserves assignment order, scope, alias/builtin overrides and provider/ref state writes; otherwise retain this coverage error.'),
    'dynamic-publication-dataflow': ('scanner-limitation',
        'Target selection depends on runtime inputs, external commands or dynamic manifest/control-flow evaluation outside the committed literal subset.',
        'Implement a narrowly specified static committed-manifest selector where complete provenance can be proved; otherwise request upstream explicit committed target declarations. Execute no inspected helper.'),
    'heredoc-substitution': ('scanner-limitation',
        'An executable heredoc expansion remains outside bounded static resolution in a source that also contains publication commands.',
        'Keep refusal until a generic lexical expansion model proves every executed substitution or upstream source uses literal quoted heredocs.'),
    'bounded-lexical-command': ('resolved-scanner-limitation',
        'The previous target came only from a comment or quoted diagnostic string; lexical command recognition no longer treats it as an executable.',
        'No disposition is inferred. Preserve the new lexical regression and continue other observations from this root.'),
    'bounded-source-locator': ('resolved-scanner-limitation',
        'A finite committed script locator and aliases now identify exact local publication targets without executing cd, dirname or pwd.',
        'Assess the resulting exact observation against existing allowances; resolution supplies no owner approval.'),
    'nonpublication-control-flow': ('resolved-scanner-limitation',
        'The source has no recognized project-publication signal; its unrelated loops/heredocs no longer create a project-target coverage error.',
        'No arbitrary runtime behavior is qualified. Continue the separately detected configuration/container/source signals.'),
    'redirected-loop-boundary': ('resolved-scanner-limitation',
        'A redirected done terminator no longer consumes subsequent publication commands as part of an unknown loop.',
        'Retain any independent unresolved directory/target error after the now-correct loop boundary.'),
    'json-object-array': ('resolved-scanner-limitation',
        'The committed file is a finite JSON object array, whose nested manifest-shaped objects are now inspected rather than rejecting its container type.',
        'No fixture exemption is inferred. Preserve discovered embedded entries and refuse unsupported scalar/deep/oversized structures.'),
}


def group(error):
    rule, path = error['rule'].split(':', 1)[0], error['path']
    if rule == 'unsafe-import-path':
        return 'external-import-layout'
    if rule == 'nested-publication-target':
        return 'nested-publication-target'
    if rule in ('unsafe-or-nested-compile-source', 'unresolved-compile-source'):
        return 'external-compile-source'
    if path.endswith(('.ps1', '.PS1')) and rule == 'unresolved-publication-target':
        return 'bounded-lexical-command' if not any(e['repository'] == error['repository'] and e['path'] == path for e in after['errors']) else 'powershell-target-evaluation'
    if rule == 'malformed-publication':
        return 'json-object-array'
    if rule == 'unsupported-inline-publication-control-flow' or (rule == 'unresolved-heredoc-substitution' and 'quarantine-governance' in path):
        return 'nonpublication-control-flow'
    if rule == 'unresolved-heredoc-substitution':
        return 'heredoc-substitution'
    if rule == 'unbounded-publication-control-flow' and path.endswith('publish-partial-release.sh'):
        return 'redirected-loop-boundary'
    if path.endswith(('verify-story414-sdk-candidate.sh', 'verify-story415-sdk-candidate.sh')):
        return 'runtime-generated-target'
    if path.endswith(('verify-cli-pack.sh', 'run-tenant-audit-performance.sh')):
        return 'bounded-source-locator'
    if path.endswith('prepare-aspire-runtime-hosts.sh'):
        return 'bounded-lexical-command'
    return 'dynamic-publication-dataflow'


rows = []
for index, error in enumerate(before['errors'], 1):
    related = [entry for entry in after['errors'] if entry['repository'] == error['repository'] and entry['path'] == error['path']]
    original = prior_by_observation[canonical(error)]
    group_id = group(error)
    classification, proof, action = definitions[group_id]
    unchanged = canonical(error) in current_errors
    rows.append(dict(id=f'C{index:03}', rootCause=group_id, classification=classification,
        before=error, priorSourceBindings=original['sourceBindings'], currentSourceBindings=bindings(error),
        committedSourceProves=proof, outcome='retained' if unchanged else 'diagnostic-resolved-source-still-partial' if related else 'resolved',
        currentErrors=related, recommendation=action, newAuthority=None))
assert len(rows) == len({canonical(row['before']) for row in rows}) == 111
counts = Counter(row['rootCause'] for row in rows)
groups = [dict(id=key, classification=definitions[key][0], priorErrorCount=count,
               outcomes=dict(Counter(row['outcome'] for row in rows if row['rootCause'] == key)),
               committedSourceProves=definitions[key][1], recommendation=definitions[key][2]) for key, count in sorted(counts.items())]
new_errors = [entry for entry in after['errors'] if canonical(entry) not in prior_by_observation]
write('coverage-assessment.json', dict(schema='mcpcli-census-coverage-resolution/v1',
    parentRevision=after['parentRevision'], priorReportSha256=sha((PRIOR / 'census.json').read_bytes()),
    currentReportSha256=sha((PACKET / 'census.json').read_bytes()), originalErrorCount=111,
    outcomes=dict(Counter(row['outcome'] for row in rows)), groups=groups, errors=rows,
    newlyReportedErrors=[dict(observation=entry, sourceBindings=bindings(entry),
        classification='source-data-ambiguity' if entry['rule'].startswith('malformed-') else 'scanner-limitation',
        recommendation='Retain refusal. Inspect the exact committed data/control-flow context; establish whether this is active metadata, caller-owned composition, or deliberately partial test/evidence data before proposing any qualification.',
        newAuthority=None) for entry in new_errors]))

prior_receipt = json.loads((PRIOR / 'secret-scan.json').read_text())
integrity = [dict(path=row['path'], beforeSha256=row['sha256'], afterSha256=sha((PRIOR / row['path']).read_bytes()),
                  unchanged=row['sha256'] == sha((PRIOR / row['path']).read_bytes())) for row in prior_receipt['files']]
assert all(row['unchanged'] for row in integrity)
write('prior-evidence-integrity.json', dict(result='passed', receiptPath=str((PRIOR / 'secret-scan.json').relative_to(ROOT)),
    receiptSha256=sha((PRIOR / 'secret-scan.json').read_bytes()), files=integrity))
write('remaining-decisions.json', dict(schema='mcpcli-census-remaining-decisions/v1', acceptance='failed',
    scannerLimitations=[row for row in groups if row['classification'] == 'scanner-limitation'],
    protectedSourceBoundaries=[row for row in groups if row['classification'] == 'protected-source-boundary'],
    upstreamSourceDefects=[],
    upstreamSourceDefectAssessment='No active upstream source defect is established solely by these coverage errors. External-layout alternatives, generated fixtures, caller-owned action targets and partial test data require contextual owning-maintainer assessment.',
    sourceDataAmbiguities=[dict(observation=entry, sourceBindings=bindings(entry), newAuthority=None) for entry in new_errors if entry['rule'].startswith('malformed-')],
    exactOwnerDisposition=[dict(**entry, contextualLimit='An unapproved observation is not proof that a new tool was created. Compare the exact identity/signals/source bytes with retained inventory and source intent before requesting a versioned disposition.')
        for entry in current_blockers['decisions'] if entry['category'] == 'rejected-observation'],
    authority='No allowance, approval, exemption, exception, source pin or scope change is authorized by this packet.'))
print(json.dumps(dict(originalErrors=len(rows), outcomes=dict(Counter(row['outcome'] for row in rows)), groups=len(groups), newlyReportedErrors=len(new_errors)), sort_keys=True))
