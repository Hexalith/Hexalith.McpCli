#!/usr/bin/env python3
"""Check the Story 5.7 candidate; --approved-completion also requires owner and delivery evidence.

This documentary gate never executes legacy operations. Immutable approved source
rows preserve Story 5.1's registration/destructive/confirmation checks. Source
anchors are re-read at their original committed pins, not moving reference HEADs.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[4]
ART = Path('_bmad-output/implementation-artifacts')
PACKET = ART / 'evidence/story-5-7'
AD = Path('_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22')
BASELINE = '48076b1bd041b45250597937da82594e202985f3'
SUCCESSORS = {'eventstore-admin': '1.0.2', 'technical-tools': '1.0.3'}
EXTRA = ['Capability class', 'Adopted outcome', 'Amendment disposition',
         'Amendment rationale or gap', 'Amendment owner', 'Governance', 'Exact replacement']
APPROVAL = '[A2](#a2-amendment-approval-pending)'
REQUIRED_ROLES = ['McpCli product/architecture owner', 'McpCli maintainer',
                  'McpCli security and contract/transport maintainer',
                  'Platform architecture/security and platform/operator maintainer',
                  'EventStore owning maintainer', 'FrontComposer owning maintainer',
                  'Projects owning maintainer', 'Folders owning maintainer',
                  'ChatBot owning maintainer', 'Memories owning maintainer',
                  'Parties owning maintainer', 'AI.Tools owning maintainer']
PREREQUISITE_TOKENS = {
    'eventstore-admin': {
        'G1': ('complete under immutable A1', 'A2 successor still requires exact-byte owner approval'),
        'G2': ('decision is superseded by adopted AD-23 D1', 'confidential UI only', 'no Admin replacement', 'before retirement remain open'),
        'G3': ('resolves the former destructive/confirmation treatment choice', 'confidential UI only', 'zero unauthorized effects', 'backup engine/manifest'),
        'G4': ('AV10', 'AV11', 'AC26/AC27/AC30', 'raw-token', 'complete-short-token', 'AV05 invalid-URL', 'AV04 base-address', 'before future Admin parity'),
        'G5': ('not retired', 'replaces the historical generic-contract gate with confidential UI coverage', 'release/rollback', 'G4 safety fixes', 'consumer-removal'),
        'G6': ('withdraws A7', 'unsafe profile/output-file variants', 'Never read or copy Admin profiles.json', 'Independent McpCli profile isolation'),
    },
    'technical-tools': {
        'G1': ('historical 65-row approval', '68-row amendment', 'A2 needs fresh exact-byte approval'),
        'G2': ('decision prerequisite is resolved by adopted AD-23', 'K07', 'K08', 'withdrawn', 'K13', 'retained local exemption', 'K01/K02', 'K10 remain deferred'),
        'G3': ('Still open', 'companion inventory refreshes', 'PS14', '--dry-run/--live/--rollback/--abort', 'Story 5.10', 'independent owner-held safety'),
        'G4': ('Admin PS01/PS02 require confidential UI coverage', 'rather than the historical generic-contract decision', 'PS03 stays retained local compiler',
               'PS14 stays an owner-held local exemption', 'forwarded identity does not make PS14 agent-safe', 'Memories heads PS06/PS07 still require forwarded per-user identity',
               'necessary but not sufficient', 'host and Projects plug-in retire together', 'Parties is retirement-blocked with G01–G06'),
        'G5': ('delivered by Story 5.6', 'census and exception/expiry policy', 'remain authoritative and unchanged', 'do not automatically reclassify'),
    },
}


class InvalidAmendment(ValueError):
    """An actionable candidate or completion failure."""


def require(condition, message):
    if not condition:
        raise InvalidAmendment(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def nonblank(value):
    return isinstance(value, str) and bool(value.strip())


def metadata(text):
    require(text.startswith('---\n'), 'inventory frontmatter missing')
    values = {}
    for line in text.split('---', 2)[1].splitlines():
        if not line:
            continue
        key, separator, value = line.partition(':')
        require(bool(separator) and key not in values, f'damaged or duplicate metadata field {key}')
        values[key] = value.strip().strip("'\"")
    return values


def check_metadata(module, version, old_text, new_text):
    old, new = metadata(old_text), metadata(new_text)
    expected = dict(old, inventory_version=version, status='pending', approval_status='pending',
                    external_maintainer_approval='pending', approval_ref='#a2-amendment-approval-pending',
                    approval_authority='pending-exact-byte-owner-approval',
                    source_spec=str(ART / 'spec-5-7-re-disposition-eventstore-admin-and-technical-tool-inventories.md'),
                    predecessor=str(ART / f'{module}-migration-inventory-v1.md'))
    require(new == expected, f'{module}: metadata/pin/scope/approval state differs from candidate policy')


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f'duplicate JSON member {key}')
        result[key] = value
    return result


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=unique)


def local(root, value):
    require(nonblank(value) and not Path(value).is_absolute(), 'expected repository-relative path')
    resolved = (root / value).resolve()
    require(resolved.is_relative_to(root.resolve()) and resolved.is_file(), f'missing or escaping input: {value}')
    return resolved


def git(repo, *args):
    result = subprocess.run(['git', '-C', str(repo), *args], capture_output=True)
    require(result.returncode == 0, f'git {" ".join(args)} failed: {result.stderr.decode(errors="replace").strip()}')
    return result.stdout


def load(root, name, path):
    spec = importlib.util.spec_from_file_location(name, root / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def policy(root):
    module = load(root, 'ad23', ART / 'evidence/story-5-2/verify_class_map.py')
    counts, state = module.verify(root, root / AD / 'AD-23-capability-class-map.json')
    require(state == 'adopted', 'AD-23 exact-byte owner adoption is required')
    return module, read_json(root / AD / 'AD-23-capability-class-map.json')


def source_pins(root):
    evidence = (root / ART / 'evidence/story-5-1/verification.md').read_text()
    pins = dict(re.findall(r'^\| `(references/[^`]+)` \| `([0-9a-f]{40})` \|', evidence, re.M))
    declared = re.findall(r'path = (references/\S+)', (root / '.gitmodules').read_text())
    require(set(pins) == set(declared), 'original source-pin coverage differs from root .gitmodules')
    return pins


def anchor_evidence(root, module, rows, pins):
    count = 0
    cache = {}
    admin = {'Cli': 'src/Hexalith.EventStore.Admin.Cli', 'Mcp': 'src/Hexalith.EventStore.Admin.Mcp',
             'Server': 'src/Hexalith.EventStore.Admin.Server', 'UI': 'src/Hexalith.EventStore.Admin.UI',
             'Contracts': 'src/Hexalith.EventStore.Contracts', 'ServiceDefaults': 'src/Hexalith.EventStore.ServiceDefaults',
             'CliTests': 'tests/Hexalith.EventStore.Admin.Cli.Tests', 'McpTests': 'tests/Hexalith.EventStore.Admin.Mcp.Tests',
             'ServerTests': 'tests/Hexalith.EventStore.Admin.Server.Tests'}
    tech = {'Cli': 'src/Hexalith.FrontComposer.Cli', 'Mcp': 'src/Hexalith.FrontComposer.Mcp',
            'Corpus': 'docs/skills/frontcomposer'}
    for key, row in rows.items():
        current = None
        # Original cells contain all source anchors; appended prose is not authority.
        for match in re.finditer(r'`(?:([^`\s:]+(?:\.(?:cs|csproj|md|json|yaml|yml|ps1|props)|CODEOWNERS))|):(\d+)`', row['text']):
            if match[1]:
                current = match[1]
            require(current is not None, f'{module}:{key}: source anchor continuation has no path')
            number = int(match[2])
            prefix, _, suffix = current.partition('/')
            aliases = admin if module == 'eventstore-admin' else tech
            if current.startswith('references/'):
                parts = current.split('/', 2)
                repo, source = '/'.join(parts[:2]), parts[2]
            elif prefix in aliases:
                repo = 'references/Hexalith.EventStore' if module == 'eventstore-admin' else 'references/Hexalith.FrontComposer'
                source = aliases[prefix] + '/' + suffix
            elif current.startswith('samples/'):
                repo, source = 'references/Hexalith.FrontComposer', current
            elif current.startswith(('src/Hexalith.', 'tests/Hexalith.')):
                repo = 'references/' + '.'.join(current.split('/')[1].split('.')[:2])
                source = current
            elif current == '.github/CODEOWNERS':
                declared_repo = re.search(r'`(references/Hexalith\.[^`/]+)`', row['text'])
                require(declared_repo is not None, f'{key}: CODEOWNERS lacks repository context')
                repo, source = declared_repo[1], current
            else:
                raise InvalidAmendment(f'{module}:{key}: unresolved source anchor {current}')
            require(repo in pins and not source.endswith('/SKILL.md'), f'{key}: source outside declared ordinary files')
            token = (repo, source)
            if token not in cache:
                cache[token] = git(root / repo, 'show', f'{pins[repo]}:{source}').decode('utf-8').splitlines()
            lines = cache[token]
            require(0 < number <= len(lines) and lines[number - 1].strip(), f'{module}:{key}: damaged anchor {current}:{number}')
            count += 1
    return count


def check_replacement(class_id, outcome, action, replacement):
    """Admission branch is explicit: Story 5.7 has no proved decorated replacement."""
    require(action != 'replace' or outcome == 'decorated-gateway-contract',
            f'{class_id}: restricted or non-Gateway replacement is forbidden')
    require(action != 'replace', f'{class_id}: replacement lacks exact decorated type at source pin and agent eligibility')
    require(replacement == 'none', f'{class_id}: invented replacement; pinned decorated type/eligibility not established')


def source_fact(module, cell):
    """Require exact source text with only the Admin scheme's code typography."""
    return re.sub(r'\bBearer(?=\s)', '`Bearer`', cell) if module == 'eventstore-admin' else cell


def check_rows(module, old_rows, new_rows, inventory, classes):
    require(old_rows.keys() == new_rows.keys(), f'{module}: missing or extra row identities')
    entries = {e['id']: e for e in inventory['rows'] + inventory['records']}
    records = {e['id'] for e in inventory['records']}
    delta = []
    for key, old in old_rows.items():
        new = new_rows[key]
        require(new['headers'] == old['headers'] + EXTRA, f'{module}:{key}: changed source headers or missing amendment fields')
        require(len(new['cells']) == len(new['headers']) and all(new['cells']), f'{module}:{key}: incomplete row')
        fields = dict(zip(EXTRA, new['cells'][-len(EXTRA):]))
        cid = entries[key].get('classId', 'record')
        require(fields['Capability class'] == cid, f'{module}:{key}: class disagrees with adopted map')
        expected_outcome = classes[cid]['outcome'] if cid != 'record' else 'governance-record'
        require(fields['Adopted outcome'] == expected_outcome, f'{module}:{key}: outcome disagrees with adopted class')
        action = fields['Amendment disposition']
        check_replacement(cid, expected_outcome, action, fields['Exact replacement'])
        expected_action = ('retain' if cid == 'record' else 'defer' if expected_outcome in
                           {'decorated-gateway-contract', 'continued-deferral'} else 'withdraw')
        require(action == expected_action, f'{module}:{key}: invalid disposition for adopted outcome')
        for header, before, after in zip(old['headers'], old['cells'], new['cells']):
            expected = source_fact(module, before)
            if header == 'Approval':
                expected = APPROVAL
            elif header == 'Disposition':
                expected = action
            elif header == 'Disposition / coverage':
                expected = action + ' / exclude'
            elif module == 'technical-tools' and key in ('PS01', 'PS02') and header == 'Operation inventory':
                expected = before.replace('inventory 1.0.0', 'inventory 1.0.2').replace('eventstore-admin-migration-inventory-v1.md', 'eventstore-admin-migration-inventory-v1.0.2.md')
            elif module == 'technical-tools' and key in {'PS01', 'PS02', 'PS03', 'PS14'} and header == 'Removal gate':
                tokens = (('Admin 1.0.2 G1–G6', 'confidential UI coverage', 'authorization/effect proof', 'G4 safety fixes', 'before retirement')
                          if key in {'PS01', 'PS02'} else ('Retained local compiler exemption', 'merged AI.Tools plan 1.2.0', 'no retirement or Gateway replacement')
                          if key == 'PS03' else ('Retained owner-held vector-migration exemption', 'merged AI.Tools plan 1.2.0', 'four-mode inventory', 'independent safety gates remain'))
                require(all(token in after for token in tokens), f'{key}: lost adopted removal-gate semantics')
                continue  # independently checked by labels and required gate semantics below
            require(after == expected, f'{module}:{key}: changed protected source field {header}')
        reason, owner = fields['Amendment rationale or gap'], fields['Amendment owner']
        require(nonblank(reason) and nonblank(owner), f'{module}:{key}: missing rationale/gap or owner')
        original_owner = next((c for h, c in zip(old['headers'], old['cells']) if 'owner' in h.lower() or h == 'Owning maintainer role'),
                              'EventStore and Platform owning maintainers' if module == 'eventstore-admin' else 'FrontComposer and relevant census owning maintainers')
        if expected_outcome != 'continued-deferral':
            require(owner == original_owner, f'{module}:{key}: owning role differs from preserved source governance')
        if expected_outcome == 'continued-deferral':
            require(reason == classes[cid]['gap'] and owner == classes[cid]['ownerRole'], f'{key}: deferral gap/owner disagrees with AD-23')
        elif expected_outcome == 'decorated-gateway-contract':
            require('exact decorated' in reason and 'pin' in reason and 'handler' in reason and 'eligibility' in reason,
                    f'{key}: undeclared Gateway deferral lacks pinned Contracts/handler/eligibility gap')
        elif expected_outcome == 'confidential-ui-only':
            require(all(s in reason for s in ('Confidential UI coverage', 'before legacy-head retirement', 'G4', 'AV10', 'AV11', 'raw-token', 'URL', 'persisted effects')),
                    f'{key}: UI withdrawal loses coverage or G4 prerequisites')
        elif expected_outcome == 'withdrawal':
            require('Accept loss' in reason, f'{key}: withdrawal lacks accepted loss')
            if cid == 'A7':
                require(all(s in reason for s in ('profiles.json', 'link-following', 'overwrite', 'Never read or migrate')), f'{key}: lost profile withdrawal safety')
            if cid == 'K08':
                require(all(s in reason for s in ('timed_out/needs_review', 'acceptance is not completion', 'subscriptions')), f'{key}: lost lifecycle losses')
            if cid == 'K07':
                require(all(s in reason for s in ('resource URIs', 'schema negotiation', 'packages, README and AI.Tools')), f'{key}: lost documentation delivery losses')
        elif expected_outcome == 'exempt-local-tooling':
            require(all(s in reason for s in ('Retain', 'merged AI.Tools plan 1.2.0', '10b709b86f9c9148e5a18177e8d11fad79ae2c0b', 'local')),
                    f'{key}: exemption lacks merged authority or retained local limit')
            if cid == 'K14':
                require(all(s in reason for s in ('--dry-run', '--live', '--rollback', '--abort', 'Story 5.10', 'independent safety')),
                        f'{key}: lost PS14 four-mode accounting or safety gate')
        if key in records:
            governing = {k: entries[key][k] for k in ('kind', 'governedBy', 'governingRule') if k in entries[key]}
            require(json.loads(fields['Governance'], object_pairs_hook=unique) == governing, f'{module}:{key}: record governance differs from AD-23')
            if key in PREREQUISITE_TOKENS[module]:
                require(all(token in reason for token in PREREQUISITE_TOKENS[module][key]),
                        f'{module}:{key}: prerequisite applicability is not reconciled with adopted AD-23')
        else:
            require(fields['Governance'] == 'AD-23 rowClasses; cross-cutting authorization and parity gates remain', f'{key}: operation lost cross-cutting governance')
        delta.append({'id': key, 'fromSha256': sha(old['text'].encode()), 'toSha256': sha(new['text'].encode())})
    return delta


def check_approval(receipt, expected_artifacts, amendments, completion):
    require(receipt.get('schemaVersion') == '1.0.0' and receipt.get('baselineCommit') == BASELINE, 'approval schema/baseline mismatch')
    require(receipt.get('artifacts') == expected_artifacts, 'approval artifact/hash-chain binding mismatch')
    require(receipt.get('amendments') == amendments, 'amendment versions/changed-row delta/hash chain mismatch')
    require(receipt.get('requiredApprovalRoles') == REQUIRED_ROLES and receipt.get('requiredRolesSource') ==
            str(AD / 'AD-23-non-gateway-capability-classes.md') + '#normative-verifier-policy', 'approval required roles/source mismatch')
    require(receipt.get('limits') == [
        'Disposition authority only; no execution, enrollment, publication, parity or retirement authority.',
        'Completion requires exact-byte owner approval and upstream integrated labels.',
        'Commits, pushes and merges require separate explicit authorization.'], 'approval authority limits changed')
    require(receipt.get('decision') in {'pending', 'approved'}, 'unknown approval decision')
    roles = receipt.get('rolesCovered')
    if receipt['decision'] == 'approved':
        require(nonblank(receipt.get('approver')) and nonblank(receipt.get('exactApprovalInstruction')), 'owner approval lacks identity or exact words')
        require(isinstance(roles, list) and all(map(nonblank, roles)) and set(REQUIRED_ROLES) <= set(roles), 'owner approval lacks required named roles')
        require(nonblank(receipt.get('approvalSource')) and nonblank(receipt.get('approvedOn')), 'owner approval lacks source/date')
    else:
        require(not any(k in receipt for k in ('approver', 'exactApprovalInstruction', 'rolesCovered', 'approvedOn', 'approvalSource')),
                'pending packet must not claim owner words, identity or roles')
    if completion:
        require(receipt['decision'] == 'approved', 'completion requires exact-byte owner approval and all required roles')


def yaml_status(text, key):
    """Read supported quoted/unquoted status scalars, including inline comments."""
    values = re.findall(rf'^{re.escape(key)}:[ \t]*(.*)$', text, re.M)
    require(len(values) <= 1, f'duplicate workflow status {key.strip()}')
    if not values:
        return None
    scalar = re.fullmatch(r'''[ \t]*(?:"([^"\r\n]*)"|'([^'\r\n]*)'|([A-Za-z][\w-]*))[ \t]*(?:#.*)?''', values[0])
    require(scalar is not None, f'unsupported workflow status scalar {key.strip()}')
    return next(value for value in scalar.groups() if value is not None)


def verify_owner_packet(root, completion=False):
    """Validate the full inventory/owner chain without invoking label verification."""
    root = Path(root).resolve()
    parser, mapping = policy(root)
    classes = {c['id']: c for c in mapping['classes']}
    receipt_bytes = (root / PACKET / 'approval.json').read_bytes()
    receipt = json.loads(receipt_bytes, object_pairs_hook=unique)
    authorities = [AD / 'AD-23-non-gateway-capability-classes.md', AD / 'AD-23-capability-class-map.json',
                   ART / 'evidence/story-5-2/approval.json', ART / 'evidence/story-5-2/main-integration.json',
                   ART / 'evidence/story-5-1/approval/approval.json', ART / 'evidence/story-5-1/verification.md',
                   ART / 'evidence/story-5-5/labels.json']
    artifacts = {str(p): sha((root / p).read_bytes()) for p in authorities}
    for path in authorities:
        require(git(root, 'show', f'{BASELINE}:{path}') == (root / path).read_bytes(), f'preserved authority changed: {path}')
    require(git(root, 'show', f'{BASELINE}:.gitmodules') == (root / '.gitmodules').read_bytes(), 'root .gitmodules changed')
    integration = read_json(root / ART / 'evidence/story-5-2/main-integration.json')
    require(integration.get('merged') is True and integration.get('mainRevision') == '10b709b86f9c9148e5a18177e8d11fad79ae2c0b', 'exemption amendment is not integrated')
    pins, results, amendments = source_pins(root), [], []
    for module, version in SUCCESSORS.items():
        old_path = ART / f'{module}-migration-inventory-v1.md'
        new_path = ART / f'{module}-migration-inventory-v{version}.md'
        old = local(root, str(old_path))
        new = local(root, str(new_path))
        require(git(root, 'show', f'{BASELINE}:{old_path}') == old.read_bytes(), f'{module}: approved predecessor bytes changed')
        old_version, old_rows = parser.inventory_rows(old)
        new_version, new_rows = parser.inventory_rows(new)
        require(new_version == version, f'{module}: successor version mismatch')
        check_metadata(module, version, old.read_text(), new.read_text())
        inventory = next(i for i in mapping['inventories'] if i['path'] == str(old_path))
        delta = check_rows(module, old_rows, new_rows, inventory, classes)
        anchors = anchor_evidence(root, module, old_rows, pins)
        artifacts[str(old_path)], artifacts[str(new_path)] = sha(old.read_bytes()), sha(new.read_bytes())
        amendments.append({'module': module, 'fromPath': str(old_path), 'fromVersion': old_version,
                           'fromSha256': artifacts[str(old_path)], 'toPath': str(new_path), 'toVersion': version,
                           'toSha256': artifacts[str(new_path)], 'changedRows': delta, 'addedRows': [], 'removedRows': []})
        results.append(f'{module}: {len(new_rows)} rows, {anchors} pinned anchors, complete delta/hash chain')
    check_approval(receipt, artifacts, amendments, completion)
    return results, receipt, receipt_bytes


def verify(root, completion=False):
    root = Path(root).resolve()
    for path, key in [
        (root / ART / 'spec-5-7-re-disposition-eventstore-admin-and-technical-tool-inventories.md', 'status'),
        (root / ART / 'sprint-status.yaml', '  5-7-re-disposition-eventstore-admin-and-technical-tool-inventori'),
    ]:
        if path.exists() and yaml_status(path.read_text(), key) == 'done':
            completion = True
    results, receipt, _ = verify_owner_packet(root, completion)
    labels = load(root, 'labels57', PACKET / 'verify_labels.py')
    labels.verify(root, completion)
    return results, receipt['decision']


def main(argv=None):
    args_parser = argparse.ArgumentParser(description=__doc__)
    args_parser.add_argument('--root', type=Path, default=ROOT)
    args_parser.add_argument('--approved-completion', action='store_true')
    args = args_parser.parse_args(argv)
    try:
        results, decision = verify(args.root, args.approved_completion)
    except (ValueError, KeyError, TypeError, OSError, IndexError) as error:
        print(f'FAIL: {error}', file=sys.stderr)
        return 1
    for result in results:
        print(f'PASS: {result}')
    print(f'PASS: candidate verified; owner decision: {decision}; ' +
          ('approved completion verified' if args.approved_completion else 'completion requires owner approval and integrated labels'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
