"""Bind unresolved census observations to committed source and prior authority.

This produces review evidence only. It never changes census policy or treats
an inventory classification as approval for an additional exact allowance.
Run from the repository root after the commands recorded in commands.json.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import re


ROOT = Path.cwd()
PACKET = Path(__file__).resolve().parent
PREVIOUS = PACKET.parent / 'patch-pass-2-20261110'
INVENTORY = '_bmad-output/implementation-artifacts/technical-tools-migration-inventory-v1.md'
APPROVAL = '_bmad-output/implementation-artifacts/evidence/story-5-1/approval/approval.json'
SPEC = importlib.util.spec_from_file_location('census', ROOT / 'tools/proprietary-surfaces/v1/check.py')
census = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(census)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def binding(path):
    return {'path': path, 'sha256': sha((ROOT / path).read_bytes())}


report = json.loads((PACKET / 'census.json').read_text())
parent = census.Tree(ROOT, report['parentRevision'])
roots = census.declarations(parent)
baseline_path = ROOT / 'tools/proprietary-surfaces/v1/baseline.json'
policy, baseline_roots, allowed, _, _, provenance = census.load_policy(
    ROOT, parent, baseline_path, baseline_path.with_name('amendments.json'),
    census.date.fromisoformat(report['utcDate']))
approval = json.loads((ROOT / APPROVAL).read_text())
inventory_lines = (ROOT / INVENTORY).read_text().splitlines()
assert sha(parent.blob(INVENTORY)) == binding(INVENTORY)['sha256']
assert sha(parent.blob(APPROVAL)) == binding(APPROVAL)['sha256']
row_lines = {match[1]: number for number, line in enumerate(inventory_lines, 1)
             if (match := re.match(r'^\| ((?:PS|PE|PN)\d+|G\d+) \|', line))}
trees = {}


def tree_at(repository, pin):
    if (repository, pin) not in trees:
        trees[(repository, pin)] = census.Tree(ROOT / repository, pin)
    return trees[(repository, pin)]


def source(repository, pin, path):
    tree = tree_at(repository, pin)
    if path not in tree.entries:
        return {'path': path, 'present': False}
    mode, kind, oid = tree.entries[path]
    assert mode in ('100644', '100755') and kind == 'blob'
    raw = tree.blob(path)
    return {'path': path, 'gitBlob': oid, 'sha256': sha(raw), 'bytes': len(raw)}


def historical_rows(repository, rows, limit):
    return {
        'inventory': binding(INVENTORY),
        'rows': [{'id': row, 'line': row_lines[row]} for row in rows],
        'approval': binding(APPROVAL),
        'approvedInventoryVersion': '1.0.2',
        'approvedGitlink': baseline_roots[repository]['gitlink'],
        'applicabilityLimit': limit,
        'approvalLimits': approval['limits'],
    }


observations = {}
for packet in (PREVIOUS / 'acceptance-blockers.json', PREVIOUS / 'verified-acceptance-blockers.json'):
    for item in json.loads(packet.read_text())['rejected']:
        observations[census.descriptor(item['surface'])] = (item, packet)
for item in report['surfaces']:
    if item['status'] == 'rejected':
        observations[census.descriptor(item['surface'])] = (item, PACKET / 'census.json')

decisions = []
for number, (key, (item, observed_in)) in enumerate(sorted(observations.items()), 1):
    repository, path, kind, identity = key
    pin = roots[repository]
    assert pin == item['gitlink']
    short = repository.rsplit('.', 1)[-1]
    if kind == 'configuration':
        rows = ['PE06']
        limit = 'PE06 classifies external Learn/Fluent UI clients at the approved pins; the current exact hashed configuration identity has no active allowance.'
        decision = 'The owning maintainer must confirm the exact observed client definition remains external developer tooling, then authorize its exact identity in a versioned amendment, or retain refusal. No blanket server-name exemption applies.'
    elif short == 'ChatBot':
        rows = ['PE05']
        limit = 'PE05 covers the named test project. Its active allowance lacks the now-observed mcp-registration signal.'
        decision = 'Review the hash-bound test source and confirm that this registration is confined to the approved fixture. Authorize only the exact signal correction through a versioned amendment, or retain refusal if it constitutes new hosting behavior.'
    elif short == 'Builds':
        rows = ['PE01']
        limit = 'PE01 explicitly names both packaging templates. These identities were rejected by an earlier scanner; the current root fails before returning complete results, and its standalone metadata probe emits no PackageId after the SDK-import handling correction.'
        decision = 'Complete generic SDK/import classification and the blocked root inspection before deciding whether the earlier package observation still exists. If it remains a candidate, confirm its exact named-template scope before authorizing any versioned data correction; if full inspection proves it absent, retain the prior observation as historical without adding an allowance.'
    elif short == 'EventStore':
        rows = ['PS01', 'G4']
        limit = 'PS01 covers the existing packed Admin CLI; it does not itself populate an exact package-metadata allowance.'
        decision = 'Confirm the default package identity is the existing PS01 compatibility binary and authorize that exact census identity through a versioned amendment. Keep all administration and retirement gates; this would grant no publication or execution authority.'
    elif short == 'Folders':
        rows = ['PS10', 'G4']
        limit = 'PS10 records a packed tool with IsPackable true. The project and tool command are allowed, but its separate package identity is absent.'
        decision = 'Confirm this is the existing PS10 packed CLI identity and authorize an exact versioned census correction, or retain refusal. Preserve the Folders inventory and retirement prerequisites.'
    elif short == 'Memories' and kind == 'publication' and identity.startswith('package:'):
        rows = ['PE09']
        limit = 'PE09 names this benchmark-vector generator as test-data tooling. Its independent effective package identity has no allowance.'
        decision = 'Confirm the package default has no shipped operator surface and authorize its exact test-data tooling identity through a versioned amendment, or retain refusal. A tooling directory alone confers no exemption.'
    elif short == 'Memories':
        rows = ['PS07', 'G4'] if identity.endswith('/memories-mcp') else ['G4']
        limit = ('PS07 and the deployment-routing narrative at inventory lines 330-342 cover the retained MCP route; the full registry-qualified image is not an allowed exact identity.'
                 if identity.endswith('/memories-mcp') else
                 'G4 requires explicit deployment routing accounting, but the ordinary memories image is not itself an inventoried proprietary surface. No exact census allowance or non-surface classification is recorded for this identity.')
        decision = ('Confirm the exact full MCP image identity is the already inventoried compatibility route, then authorize a versioned identity correction while preserving retirement gates.'
                    if identity.endswith('/memories-mcp') else
                    'Review whether the image resolves to the ordinary service rather than a proprietary MCP/CLI host. Choose a generic, test-protected project/image association fix or a specifically approved exact non-surface qualification; otherwise retain refusal. Do not classify it as PS07 based on its repository alone.')
    elif short == 'PolymorphicSerializations':
        rows = ['PE08', 'PN03']
        limit = 'PE08 explicitly names this example and PN03 records no proprietary runtime surface. The separate effective package identity is absent from active policy.'
        decision = 'Confirm the default package identity remains the approved example and authorize an exact versioned census correction, or retain refusal. PN03 alone is not a permanent root exemption.'
    else:
        raise AssertionError(key)
    paths = sorted(set(item.get('sources', [])) | {path})
    current_sources = [source(repository, pin, value) for value in paths]
    approved_pin = baseline_roots[repository]['gitlink']
    original_sources = [source(repository, approved_pin, value) for value in paths]
    metadata = {}
    if census.PROJECT.search(path):
        for label, metadata_pin in [('current', pin), ('inventoryPin', approved_pin)]:
            tree = tree_at(repository, metadata_pin)
            values, _, documents, _ = census.project_metadata(tree, path, census.metadata_files(tree))
            metadata[label] = {
                'properties': {name: sorted(values.get(name, set())) for name in census.PROPERTY_NAMES.values()},
                'committedMetadata': [source(repository, metadata_pin, value) for value in sorted(set(documents))],
            }
    same_path = [entry for allowed_key, entry in allowed.items() if allowed_key[:2] == key[:2]]
    present = any(census.descriptor(candidate['surface']) == key and candidate['status'] == 'rejected'
                  for candidate in report['surfaces'])
    decisions.append({
        'id': f'O{number:02}', 'category': 'rejected-observation',
        'surface': item['surface'], 'gitlink': pin,
        'signals': item['signals'], 'reason': item['reason'],
        'observationState': 'current-rejection' if present else 'prior-rejection-retained-root-inspection-incomplete',
        'observedReport': binding(observed_in.relative_to(ROOT).as_posix()),
        'committedSources': current_sources, 'inventoryPinSources': original_sources,
        'sameSourceBytesAtInventoryPin': all(a.get('sha256') == b.get('sha256') and b.get('present') is not False
                                            for a, b in zip(current_sources, original_sources)),
        'metadata': metadata, 'activeAllowancesAtSamePath': same_path,
        'standalonePackageIdentityPresent': (identity.removeprefix('package:') in metadata.get('current', {}).get('properties', {}).get('PackageId', [])
                                             if kind == 'publication' and identity.startswith('package:') else None),
        'historicalApproval': historical_rows(repository, rows, limit),
        'missingDecision': decision,
        'owner': baseline_roots[repository]['owner'],
        'proposedAuthority': None,
    })

error_data = {
    'Builds': (
        ['PE01'],
        'PE01 names the build/workspace tools and two packaging templates, not arbitrary runtime-derived application container projects in this composite action.',
        'The action computes a project path inside a shell function from runtime application inputs; the committed census cannot determine the actual caller project or image.',
        'Choose an approved generic static representation/resolution of caller project targets or explicitly scoped qualification of this exact build action. Keep unresolved arbitrary targets refused; do not exempt every build action.'),
    'EventStore': (
        ['PE08'],
        'PE08 names Sample.Api and other specific hosts, not the separate generated-code quality fixture; no exact allowance covers this dynamic Compile expression.',
        'The fixture compiles @(_SampleApiRestGeneratedCopy), populated by a Copy task from uncommitted generated obj output. No committed item value is available to the static scanner.',
        'Approve a specific source-bound qualification for this generated-code fixture or define generic static generated-source handling with negative controls. Do not execute its generator or silently ignore Compile item expressions.'),
    'Projects': (
        ['G5'],
        'G5 requires unsafe/unknown coverage to fail. No inventory row or census exception authorizes a parent-relative project publication path.',
        'The workflow changes into references/Hexalith.Conversations and invokes dotnet run --project ../Hexalith.Builds/...; the scanner refuses the literal parent-relative publication path.',
        'Have the owning repository supply a safe, statically resolvable target, or approve a generic working-directory-aware source interpretation with containment tests. Keep the current unsafe-path guard until that change is proved.'),
    'Tenants': (
        ['PN05'],
        'PN05 is a pinned no-proprietary-surface observation, not an exemption for future dynamic publication commands. No exact active allowance covers the shell-computed target.',
        'The workflow shell loop packs src/Hexalith.Tenants.${catalog_package}/Hexalith.Tenants.${catalog_package}.csproj for Contracts and Server; literal project discovery refuses its unresolved variable.',
        'Define and verify generic finite shell-loop target expansion or obtain an exact source-bound qualification for this workflow. Confirm the Contracts/Server library targets have no MCP/CLI surface; do not add a Tenants-specific checker branch.'),
    'Works': (
        ['PN07'],
        'PN07 records a historical no-surface root. It authorizes neither nested reference inspection nor this dynamic package-production script.',
        'The script changes into nested EventStore and Platform references and packs shell-computed project names; the current committed root census does not open those nested repositories.',
        'Choose an approved generic contract for statically enumerating local/nested package targets or obtain an exact source-bound qualification of this script. Preserve the no-nested-initialization boundary and refuse unresolved targets.'),
}
for number, item in enumerate(report['errors'], 1):
    repository, pin, rule = item['repository'], item['gitlink'], item['rule']
    path = rule.partition(':')[2]
    short = repository.rsplit('.', 1)[-1]
    rows, limit, explanation, decision = error_data[short]
    assert pin == roots[repository]
    approved_pin = baseline_roots[repository]['gitlink']
    decisions.append({
        'id': f'E{number:02}', 'category': 'inspection-error', 'repository': repository,
        'gitlink': pin, 'path': path, 'rule': rule,
        'committedSources': [source(repository, pin, path)],
        'inventoryPinSources': [source(repository, approved_pin, path)],
        'historicalApproval': historical_rows(repository, rows, limit),
        'explanation': explanation, 'missingDecision': decision,
        'owner': baseline_roots[repository]['owner'], 'proposedAuthority': None,
    })

packet = {
    'schema': 'mcpcli-census-unresolved-dispositions/v1',
    'status': 'owner-or-approved-source-resolution-required',
    'parentRevision': report['parentRevision'], 'utcDate': report['utcDate'],
    'report': binding((PACKET / 'census.json').relative_to(ROOT).as_posix()),
    'checker': binding('tools/proprietary-surfaces/v1/check.py'),
    'policy': provenance,
    'rootPins': roots,
    'currentRejectedCount': sum(item['status'] == 'rejected' for item in report['surfaces']),
    'retainedRejectedObservationCount': len(observations),
    'inspectionErrorCount': len(report['errors']),
    'limits': [
        'Evidence and missing decisions only; this document is not an approval receipt.',
        'Historical classifications and matching source bytes do not automatically create an exact allowance.',
        'Prior rejections from an error root remain unresolved; absent partial results do not prove removal.',
        'No policy, source pin, reference content, publication or retirement change is authorized here.',
    ],
    'decisions': decisions,
}
(PACKET / 'disposition-packet.json').write_text(json.dumps(packet, indent=2, sort_keys=True) + '\n')
print(json.dumps({key: packet[key] for key in ('currentRejectedCount', 'retainedRejectedObservationCount', 'inspectionErrorCount')}, sort_keys=True))
