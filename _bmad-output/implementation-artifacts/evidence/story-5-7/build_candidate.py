#!/usr/bin/env python3
"""Prepare additive Story 5.7 candidates and isolated README patches; never deliver them.

Run from the McpCli root. Refuses to overwrite an approved packet. Owner checkouts
are read only, including their index and worktree; Git object reads use exact pins.
"""
import difflib
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
E = ART / 'evidence/story-5-7'
AD = Path('_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22')
BASELINE = '48076b1bd041b45250597937da82594e202985f3'
VERSIONS = {'eventstore-admin': '1.0.2', 'technical-tools': '1.0.3'}
APPROVAL = '[A2](#a2-amendment-approval-pending)'
EXTRA_HEADERS = ['Capability class', 'Adopted outcome', 'Amendment disposition',
                 'Amendment rationale or gap', 'Amendment owner', 'Governance', 'Exact replacement']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(repo, *args):
    return subprocess.run(['git', '-C', str(repo), *args], check=True, capture_output=True).stdout


def write(path, data):
    path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data if isinstance(data, bytes) else data.encode('utf-8'))


def js(path, value):
    write(path, json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def load_parser():
    spec = importlib.util.spec_from_file_location('classmap', ROOT / ART / 'evidence/story-5-2/verify_class_map.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source_fact(module, cell):
    """Quote only Admin's literal authentication scheme; retain factual text."""
    return re.sub(r'\bBearer(?=\s)', '`Bearer`', cell) if module == 'eventstore-admin' else cell


def compatibility_section(data):
    lines = data.decode('utf-8').splitlines(keepends=True)
    start = next(i for i, line in enumerate(lines) if line.rstrip('\r\n') == '## Legacy compatibility surfaces')
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith('#')), len(lines))
    return ''.join(lines[start:end]).encode()


ADMIN_UI = ('Withdraw from the public McpCli migration target under adopted AD-23 D1. '
            'Confidential UI coverage is required before legacy-head retirement: authenticated human admission, '
            'tenant/platform-scope denials, bounded behavior, safe audit/output/errors and persisted effects. '
            'Retain G4: AV10 platform-scope/optional-tenant denials, AV11 route mismatch, raw-token JSON and '
            'complete-short-token display, AV05 invalid-URL and AV04 base-address disclosure; no Admin replacement admitted.')
LOSSES = {
    'A5': 'Accept loss of process-local investigation context, remembered filters and legacy context result documents; these confer no authority.',
    'A6': 'Accept loss of unavailable backup spellings and their stderr/exit-2 stub contract; no working backup is withdrawn.',
    'A7': 'Accept loss of Admin profile/configuration dialect, fallback and token display; destructive overwrite/deletion, corrupt-store replacement, link-following non-atomic saves, post-write permissions and output-file overwrite are not copied. Never read or migrate Admin profiles.json credentials to mcpcli.json.',
    'A8': 'Accept loss of shell completion and its scripts; shell completion remains outside McpCli v1.',
    'K15': 'Accept loss of legacy parser/help/aliases, preview/wizard conventions and wrapper output/exit dialects; McpCli retains its own documented contracts.',
    'K07': 'Accept loss of resource URIs, Markdown rendering, subscriptions and schema negotiation; documentation remains in packages, README and AI.Tools. No MCP resources or prompts are added.',
    'K08': 'Accept loss of synthetic timed_out/needs_review, in-memory history, expiry/eviction, long-poll and subscriptions. Gateway acceptance is not completion; only independently decorated business Queries may observe effects.',
}
COMPILER = ('Retain local compiler tooling under merged AI.Tools plan 1.2.0 (10b709b86f9c9148e5a18177e8d11fad79ae2c0b); '
            'withdraw only from migration scope, never count it as retired. Preserve explicit build choice/no-build freshness, '
            'selectors, drift/hash and path safety, sequential partial writes/applied:false, import warnings and parser/output privacy limits. No Gateway exposure or execution permission.')
OPERATOR = ('Retain owner-held local exemption under merged AI.Tools plan 1.2.0 (10b709b86f9c9148e5a18177e8d11fad79ae2c0b). '
            'Account for --dry-run, --live, --rollback and --abort; Story 5.10 still owes the operation-level inventory and '
            'independent safety evidence: tenant/credential/custody, consent, no-write dry-run, rollback/abort, denial and audit proof. No agent exposure or retirement.')
GATES = {
    'PS01': 'Admin 1.0.2 G1–G6: confidential UI coverage and authorization/effect proof; retained G4 safety fixes before retirement',
    'PS02': 'Admin 1.0.2 G1–G6: confidential UI coverage and authorization/effect proof; retained G4 safety fixes before retirement',
    'PS03': 'Retained local compiler exemption under merged AI.Tools plan 1.2.0; no retirement or Gateway replacement',
    'PS14': 'Retained owner-held vector-migration exemption under merged AI.Tools plan 1.2.0; four-mode inventory and independent safety gates remain',
}
PREREQUISITES = {
    'eventstore-admin': {
        'G1': 'Predecessor inventory review is complete under immutable A1; this A2 successor still requires exact-byte owner approval with all named roles. Prior approval does not cover these new dispositions.',
        'G2': 'Historical generic administration contract decision is superseded by adopted AD-23 D1: A1–A4 are confidential UI only, withdrawn from the public migration target; no Admin replacement or non-Gateway transport is admitted. UI coverage and authorization/effect evidence before retirement remain open.',
        'G3': 'AD-23 D1 resolves the former destructive/confirmation treatment choice to confidential UI only. Human admission, direct/chained public-agent denial and zero unauthorized effects remain required; caller confirmation is not authority. AM01 backup engine/manifest evidence remains unproved.',
        'G4': 'Retained safety prerequisite: AV10 platform-scope/optional-tenant denials, AV11 route mismatch, AC26/AC27/AC30 raw-token JSON and complete-short-token display, AV05 invalid-URL and AV04 base-address disclosure need upstream fixes or explicit owner resolution before future Admin parity. No disclosure is copied as target behavior.',
        'G5': 'Both Admin heads remain versioned compatibility surfaces, not retired and outside Platform compositions. AD-23 replaces the historical generic-contract gate with confidential UI coverage plus human/tenant/scope authorization, bounded behavior, audit/effect and release/rollback proof; G4 safety fixes and independent consumer-removal authority remain. Candidate disposition approval does not prove retirement.',
        'G6': 'AD-23 withdraws A7 and the unsafe profile/output-file variants, accepting their losses instead of migrating them. Never read or copy Admin profiles.json credentials; no automatic store conversion, overwrite or deletion. Independent McpCli profile isolation, atomicity/link/permission, actor and cross-environment safeguards remain binding.',
    },
    'technical-tools': {
        'G1': 'Predecessor A1 review covers the historical 65-row approval and separately approved 68-row amendment only. A2 needs fresh exact-byte approval for all current 68 rows and named owner roles; no prior session or inventory approval is extended by implication.',
        'G2': 'Former Story 5.2 decision prerequisite is resolved by adopted AD-23: K07 documentation/resource delivery and K08 synthetic lifecycle are withdrawn with accepted losses; K13 compiler tooling is a retained local exemption under merged AI.Tools plan 1.2.0. Exact consumer Contracts/handler/eligibility gaps for K01/K02 and approved shared HTTP authority for K10 remain deferred; no generic non-Gateway transport is admitted.',
        'G3': 'Still open: companion inventory refreshes and consumer accounting remain owned by Projects, Memories, Folders and ChatBot maintainers. PS14 retains four-mode --dry-run/--live/--rollback/--abort accounting and Story 5.10 operation-level inventory plus independent owner-held safety evidence; exemption does not close those gates.',
        'G4': 'Current applicability: Admin PS01/PS02 require confidential UI coverage and authorization/effect proof plus retained G4 safety fixes, rather than the historical generic-contract decision. PS03 stays retained local compiler tooling; PS14 stays an owner-held local exemption, never retired, with independent four-mode safety/inventory gates; forwarded identity does not make PS14 agent-safe. Memories heads PS06/PS07 still require forwarded per-user identity, necessary but not sufficient for retirement. FrontComposer host and Projects plug-in retire together. All remaining selected-environment, behavior, audit, output/exit, freshness/redaction/context/paging, idempotency, routing/removal, release/rollback and module gates remain; Parties is retirement-blocked with G01–G06.',
        'G5': 'The no-new-proprietary-surface CI gate is delivered by Story 5.6; its separately approved census and exception/expiry policy remain authoritative and unchanged. AD-23 exemptions do not automatically reclassify that census or authorize new per-module tools. No new CI implementation or census amendment is claimed here.',
    },
}


def disposition(entry, classes, module, row):
    cid = entry.get('classId', 'record')
    governance = json.dumps({k: entry[k] for k in ('kind', 'governedBy', 'governingRule') if k in entry}, ensure_ascii=False, separators=(',', ':'))
    owner = next((c for h, c in zip(row['headers'], row['cells']) if 'owner' in h.lower() or h == 'Owning maintainer role'),
                 'EventStore and Platform owning maintainers' if module == 'eventstore-admin' else 'FrontComposer and relevant census owning maintainers')
    if cid == 'record':
        reason = PREREQUISITES[module].get(entry['id'], entry['reason'] + ' Retain the source record governance and unresolved behavior/retirement evidence; AD-23 does not prove them completed.')
        return [cid, 'governance-record', 'retain', reason, owner, governance, 'none']
    outcome = classes[cid]['outcome']
    if outcome == 'confidential-ui-only':
        reason, action = ADMIN_UI, 'withdraw'
    elif outcome == 'withdrawal':
        reason, action = LOSSES[cid], 'withdraw'
    elif outcome == 'exempt-local-tooling':
        reason, action = (COMPILER if cid == 'K13' else OPERATOR), 'withdraw'
    elif outcome == 'continued-deferral':
        reason, action, owner = classes[cid]['gap'], 'defer', classes[cid]['ownerRole']
    else:
        reason, action = ('No exact decorated consumer Contracts type, handler and agent eligibility is established at the preserved pin; '
                          'the owning module must supply pinned declaration, admission and behavior proof. No dynamic plug-in/REST fallback. '
                          'Preserve deny-before-dispatch, hidden-tool, 32 KiB/visible-catalog/schema-fingerprint limits (FH02/FV04) '
                          'and bounded projection/freshness/filter/Markdown differences (FH03/FV05) until owner-approved reconciliation.'), 'defer'
    return [cid, outcome, action, reason, owner, governance if governance != '{}' else 'AD-23 rowClasses; cross-cutting authorization and parity gates remain', 'none']


def main():
    prior = ROOT / E / 'approval.json'
    if prior.exists() and json.loads(prior.read_text())['decision'] != 'pending':
        raise SystemExit('Refusing to overwrite an owner-approved packet')
    parser = load_parser()
    mapping = json.loads((ROOT / AD / 'AD-23-capability-class-map.json').read_text())
    classes = {c['id']: c for c in mapping['classes']}
    authorities = [AD / 'AD-23-non-gateway-capability-classes.md', AD / 'AD-23-capability-class-map.json',
                   ART / 'evidence/story-5-2/approval.json', ART / 'evidence/story-5-2/main-integration.json',
                   ART / 'evidence/story-5-1/approval/approval.json', ART / 'evidence/story-5-1/verification.md',
                   ART / 'evidence/story-5-5/labels.json']
    artifacts = {str(p): sha((ROOT / p).read_bytes()) for p in authorities}
    amendments = []
    for module, version in VERSIONS.items():
        old_path = ART / f'{module}-migration-inventory-v1.md'
        new_path = ART / f'{module}-migration-inventory-v{version}.md'
        previous = ROOT / old_path
        old_version, source_rows = parser.inventory_rows(previous)
        policy = next(i for i in mapping['inventories'] if i['path'] == str(old_path))
        entries = {e['id']: e for e in policy['rows'] + policy['records']}
        meta = previous.read_text().split('---', 2)[1]
        meta = re.sub(r"inventory_version: .*", f"inventory_version: '{version}'", meta)
        for field in ('status', 'approval_status', 'external_maintainer_approval'):
            meta = re.sub(rf'^{field}: .*', f'{field}: pending', meta, flags=re.M)
        meta = re.sub(r'^approval_ref: .*', "approval_ref: '#a2-amendment-approval-pending'", meta, flags=re.M)
        meta = re.sub(r'^approval_authority: .*', 'approval_authority: pending-exact-byte-owner-approval', meta, flags=re.M)
        meta = re.sub(r'^source_spec: .*', "source_spec: '_bmad-output/implementation-artifacts/spec-5-7-re-disposition-eventstore-admin-and-technical-tool-inventories.md'", meta, flags=re.M)
        historical_summary = ("Technical 1.0.0's original **65-row** approval remains historical; technical 1.0.2\n"
                              "and this current summary cover **68 rows**, including PS14, PE08 and PE09.\n") if module == 'technical-tools' else ''
        intro = f'''---{meta}predecessor: '{old_path}'
---

# {module} migration inventory {version}

Candidate amendment **{version}**, pending exact-byte owner approval. This successor
accounts for **{len(source_rows)} rows** at the unchanged predecessor source pins.
The immutable [{old_version} predecessor]({old_path.name}) retains its own approval.
{historical_summary}All original registration, route, behavior, effect/destructive, confirmation,
security, packaging and source-evidence fields below are preserved. The added
columns give the adopted class, sole outcome, disposition, rationale, owner and
governance. Accounting records are not invented operations.
Original replacement-gap, required-handoff and prerequisite text records the
predecessor's historical gate. Amendment columns state current applicability and dispositions;
unperformed authorization, behavior, inventory and release evidence stays open.

## A2 Amendment approval pending

The specification's "approve and continue" approves intent only. The
[candidate receipt](evidence/story-5-7/approval.json) binds predecessors,
AD-23, adoption/exemption authority, exact candidate bytes and every changed row.
No new approver, exact approving words or covered roles are claimed before
the owner approves this packet. Approval grants disposition authority only;
it grants no execution, enrollment, publication, parity or retirement authority.
Neither legacy head is retired. Candidate label patches remain undelivered.

## Disposition and retained gates

Adopted AD-23 is effective through its separate Story 5.2 receipt; its historical
proposed frontmatter is immutable. Remote Admin A1–A4 withdrawals require
confidential UI coverage before retirement, including bounded/inconclusive/
truncated/retention semantics and direct/chained public-agent denial with zero
unauthorized effects. G4 retains AV10, AV11, raw-token JSON/complete-short-token
display and both URL-disclosure fixes as future Admin parity prerequisites.
No Admin replacement is admitted. AM01 still has a deferred backup backend.
Local Admin withdrawals accept parser/output/profile/context/completion losses,
including unsafe file/profile overwrite and link behavior. Never copy credentials
from Admin profiles.json. Documentation/resource and synthetic lifecycle losses
are explicit per row; Gateway acceptance never proves completion.

Compiler and PS14 exemptions rely on merged AI.Tools plan 1.2.0, main commit
10b709b86f9c9148e5a18177e8d11fad79ae2c0b, bound by Story 5.2 main-integration.json.
They remain local, retained and outside agent discovery/submission. PS14's four
modes still need Story 5.10's detailed inventory and independent safety evidence.
Companion inventory updates, forwarded authority, release/rollback, selected
environment authorization, audit, output/exit, freshness/redaction/context/paging,
idempotency and independent module gates remain open. FrontComposer host and
Projects plug-in retire together; Parties remains retirement-blocked with G01–G06.
This amendment changes no census, dependency, source pin, gitlink or production code.

## Source notation

Source abbreviations and evidence use the predecessor's exact pins, never current
HEAD: Admin Cli/Mcp/Server/UI/Contracts/ServiceDefaults and matching test projects
are under Hexalith.EventStore/src or tests; technical Cli/Mcp are under
Hexalith.FrontComposer/src and Corpus is docs/skills/frontcomposer. Explicit
references/ paths identify the root-declared source repository. The predecessor's
authority model, cross-head differences and static source observations remain
binding; these copied source facts do not establish execution or parity.

'''
        # Preserve factual text; only Admin's literal scheme gets code typography.
        chunks = [intro]
        current_heading = ''
        emitted = set()
        for line in previous.read_text().splitlines():
            if line.startswith(('## ', '### ')):
                current_heading = line
            cells = [c.strip() for c in line.split('|')[1:-1]]
            if cells and cells[0] in source_rows:
                row_id = cells[0]
                if row_id in emitted:
                    continue  # informational cross-head tables have different headers
                row = source_rows[row_id]
                if cells != row['cells']:
                    continue
                if not emitted or chunks[-1].endswith('\n\n') or row['headers'] != last_headers:
                    chunks.append('\n' + current_heading + '\n\n')
                    chunks.append('| ' + ' | '.join(row['headers'] + EXTRA_HEADERS) + ' |\n')
                    chunks.append('| ' + ' | '.join(['---'] * (len(row['headers']) + len(EXTRA_HEADERS))) + ' |\n')
                extra = disposition(entries[row_id], classes, module, row)
                cells = [source_fact(module, cell) for cell in cells]
                for idx, header in enumerate(row['headers']):
                    if header == 'Disposition':
                        cells[idx] = extra[2]
                    elif header in ('Disposition / coverage', 'Disposition/coverage'):
                        cells[idx] = extra[2] + ' / exclude'
                    elif header == 'Approval':
                        cells[idx] = APPROVAL
                if module == 'technical-tools' and row_id in ('PS01', 'PS02'):
                    cells[5] = cells[5].replace('inventory 1.0.0', 'inventory 1.0.2').replace('eventstore-admin-migration-inventory-v1.md', 'eventstore-admin-migration-inventory-v1.0.2.md')
                if module == 'technical-tools' and row_id in GATES:
                    cells[7] = GATES[row_id]
                chunks.append('| ' + ' | '.join(cells + extra) + ' |\n')
                emitted.add(row_id)
                last_headers = row['headers']
        write(new_path, ''.join(chunks))
        _, new_rows = parser.inventory_rows(ROOT / new_path)
        changes = [{'id': k, 'fromSha256': sha(source_rows[k]['text'].encode()), 'toSha256': sha(new_rows[k]['text'].encode())} for k in source_rows if source_rows[k]['text'] != new_rows[k]['text']]
        artifacts[str(old_path)] = sha(previous.read_bytes())
        artifacts[str(new_path)] = sha((ROOT / new_path).read_bytes())
        amendments.append({'module': module, 'fromPath': str(old_path), 'fromVersion': old_version,
                           'fromSha256': artifacts[str(old_path)], 'toPath': str(new_path), 'toVersion': version,
                           'toSha256': artifacts[str(new_path)], 'changedRows': changes, 'addedRows': [], 'removedRows': []})
    receipt = {'schemaVersion': '1.0.0', 'decision': 'pending', 'baselineCommit': BASELINE,
               'requiredRolesSource': str(AD / 'AD-23-non-gateway-capability-classes.md') + '#normative-verifier-policy',
               'requiredApprovalRoles': json.loads(parser.POLICY.findall((ROOT / AD / 'AD-23-non-gateway-capability-classes.md').read_text())[0])['requiredApprovalRoles'],
               'artifacts': artifacts, 'amendments': amendments,
               'limits': ['Disposition authority only; no execution, enrollment, publication, parity or retirement authority.',
                          'Completion requires exact-byte owner approval and upstream integrated labels.',
                          'Commits, pushes and merges require separate explicit authorization.']}
    js(E / 'approval.json', receipt)
    prepare_labels(parser, artifacts)
    print('Prepared two pending inventories; approval and delivery not granted.')


def prepare_labels(parser, artifacts):
    prior = json.loads((ROOT / ART / 'evidence/story-5-5/labels.json').read_text())
    _, technical = parser.inventory_rows(ROOT / ART / 'technical-tools-migration-inventory-v1.0.3.md')
    successor_url = 'https://github.com/Hexalith/Hexalith.McpCli/blob/main/' + str(ART) + '/'
    result = {'schemaVersion': '1.0.0', 'state': 'candidate-pending-owner-approval-and-delivery',
              'predecessor': {'path': str(ART / 'evidence/story-5-5/labels.json'),
                              'sha256': sha((ROOT / ART / 'evidence/story-5-5/labels.json').read_bytes())},
              'inventoryRevision': None, 'inventoryArtifacts': {p: h for p, h in artifacts.items() if p.endswith(('v1.0.2.md', 'v1.0.3.md'))},
              'citationPolicy': 'Versioned additive files on main; exact content SHA-256 below each label. Completion additionally binds an integrated inventoryRevision and its exact blobs. No unpublished link is claimed available.',
              'deliveryAuthorization': None, 'repositories': [], 'rows': []}
    for name in prior['commits']:
        owner = ROOT.parent / name
        base = git(owner, 'rev-parse', 'HEAD').decode().strip()
        before = git(owner, 'show', f'{base}:README.md')
        after = before.decode('utf-8')
        repo_rows = [r for r in prior['rows'] if r['repository'] == prior['commits'][name]['repository']]
        for row in repo_rows:
            key = row['id']
            old = row['label']['text']
            assert after.count(old) == 1, (name, key, 'historical label missing or duplicated; investigate before changing owner source')
            gate = technical[key]['cells'][7]
            new = re.sub(r'removal gate "[^"]*"', f'removal gate "{gate}"', old, count=1)
            new = re.sub(r'\[technical-tools inventory 1\.0\.2\]\([^)]*\)',
                         '[technical-tools inventory 1.0.3](' + successor_url + 'technical-tools-migration-inventory-v1.0.3.md)', new)
            if key in ('PS01', 'PS02'):
                new = re.sub(r'\[EventStore Admin inventory 1\.0\.1\]\([^)]*\)',
                             '[EventStore Admin inventory 1.0.2](' + successor_url + 'eventstore-admin-migration-inventory-v1.0.2.md)', new)
                new += ' Remote Admin capabilities are withdrawn from the public agent target; confidential UI coverage and retained G4 safety fixes precede retirement. No Admin Gateway replacement is admitted.'
            elif key == 'PS03':
                new += ' Retained local compiler tooling under merged AI.Tools plan 1.2.0; no agent exposure and never counted as retired. Its build/freshness, apply/drift/path, partial-write and output privacy gates remain independent.'
            elif key == 'PS14':
                new = new.replace('Forwarded per-user identity is necessary but not sufficient for retirement.', 'Forwarded per-user identity does not make this owner-held tool agent-safe.')
                new += ' Retained owner-held local exemption under merged AI.Tools plan 1.2.0; --dry-run, --live, --rollback and --abort still require Story 5.10 operation accounting and independent tenant/credential/custody, consent, no-write dry-run, denial, rollback/abort and audit evidence. Never counted as retired.'
            new += ' Technical inventory SHA-256: `' + artifacts[str(ART / 'technical-tools-migration-inventory-v1.0.3.md')] + '`.'
            if key in ('PS01', 'PS02'):
                new += ' Admin inventory SHA-256: `' + artifacts[str(ART / 'eventstore-admin-migration-inventory-v1.0.2.md')] + '`.'
            after = after.replace(old, new)
            result['rows'].append({'id': key, 'repository': name, 'surface': row['surface'],
                                   'label': {'file': 'README.md', 'line': after.splitlines().index(new) + 1,
                                             'text': new, 'sha256': sha(new.encode())}, 'gate': gate})
        target = E / 'upstream' / name
        after_bytes = after.encode()
        patch = ''.join(difflib.unified_diff(before.decode().splitlines(keepends=True), after.splitlines(keepends=True),
                                           fromfile='a/README.md', tofile='b/README.md', n=0)).encode()
        before_section, after_section = compatibility_section(before), compatibility_section(after_bytes)
        write(target / 'README.before.section.md', before_section)
        write(target / 'README.after.section.md', after_section)
        write(target / 'README.patch', patch)
        status = git(owner, 'status', '--porcelain=v1', '--untracked-files=all')
        result['repositories'].append({'name': name, 'repository': prior['commits'][name]['repository'],
                                       'ownerCheckout': str(owner), 'baseRevision': base,
                                       'before': {'path': str(target / 'README.before.section.md'), 'sha256': sha(before_section)},
                                       'after': {'path': str(target / 'README.after.section.md'), 'sha256': sha(after_section)},
                                       'readme': {'beforeSha256': sha(before), 'afterSha256': sha(after_bytes)},
                                       'patch': {'path': str(target / 'README.patch'), 'sha256': sha(patch)},
                                       'ownerState': {'branch': git(owner, 'branch', '--show-current').decode().strip(),
                                                      'statusSha256': sha(status), 'statusEntries': len(status.splitlines()),
                                                      'readmeSha256': sha((owner / 'README.md').read_bytes())},
                                       'integration': None})
    result['rows'].sort(key=lambda r: r['id'])
    js(E / 'labels.json', result)


if __name__ == '__main__':
    main()
