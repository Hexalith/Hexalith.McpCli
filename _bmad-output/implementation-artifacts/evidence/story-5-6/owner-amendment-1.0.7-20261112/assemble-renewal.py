"""Assemble census amendment 1.0.7 and its v2 receipt around the unchanged draft authorization.

  --rehearse DIR
      Build the amendment and a rehearsal receipt in an empty directory outside the repository,
      then load the chain with check.py's own load_policy. Nothing is written inside the repository.
  --write LABEL --approved-sha256 SHA [--approved-on YYYY-MM-DD]
      Only after exact-byte owner approval. Refuses unless the draft's canonical SHA-256 equals SHA
      and HEAD and every root pin still match the source report. Writes amendments/1.0.7.json, its
      receipt and the amendments.json entry atomically, records LABEL verbatim, then loads the
      written chain with load_policy.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
DRAFT = Path(__file__).resolve().parent
V1 = ROOT / 'tools/proprietary-surfaces/v1'
RECEIPT = 'tools/proprietary-surfaces/v1/amendments/1.0.7-approval.json'
OWNER = 'Requesting user, owning maintainer'
REASON = ('Owner re-approval, byte for byte, of 20 exact-file exclusions and 1 allowance whose classifications and '
          'current bytes the owner already approved in the hash-only owner amendments 1.0.5 and 1.0.6 (see '
          'priorOwnerApprovals), and which the active chain otherwise rests only on the waiver amendments 1.0.3-1.0.6. '
          'The exclusions are hash-only: they stay valid across pin moves until the file bytes change.')
canonical = lambda value: json.dumps(value, sort_keys=True, separators=(',', ':'))
sha = lambda raw: hashlib.sha256(raw).hexdigest()
pretty = lambda value: (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()
spec = importlib.util.spec_from_file_location('census', V1 / 'check.py')
census = importlib.util.module_from_spec(spec); spec.loader.exec_module(census)


def refuse(message):
    sys.exit(f'assemble-refused: {message}')


def current_report():
    """Require HEAD, every root pin and the checker to be the ones the draft was built from."""
    report_raw = (DRAFT / 'source-census.json').read_bytes()
    report = json.loads(report_raw)
    head = census.git(ROOT, 'rev-parse', '--verify', 'HEAD^{commit}')
    parent = census.Tree(ROOT, head)
    if report['parentRevision'] != head or {row['repository']: row['gitlink'] for row in report['repositories']} != census.declarations(parent):
        refuse('HEAD or a root pin moved since the source report')
    checker = json.loads((DRAFT / 'source-checker.json').read_text())
    if checker['sha256'] != sha((V1 / 'check.py').read_bytes()) or checker['sourceReportSha256'] != sha(report_raw):
        refuse('check.py or the source report changed since the draft was built')
    return report, report_raw, checker


def documents(label, day):
    report, report_raw, checker = current_report()
    authorization = json.loads((DRAFT / 'authorization.draft.json').read_text())
    index = json.loads((V1 / 'amendments.json').read_text())
    previous = index[-1]
    if previous['path'] != 'amendments/1.0.6.json' or sha((V1 / previous['path']).read_bytes()) != previous['sha256']:
        refuse('the chain does not end at the indexed 1.0.6 amendment')
    prior_raw = (DRAFT / 'prior-owner-approvals.json').read_bytes()
    prior = json.loads(prior_raw)
    for approval in prior:
        for binding in (approval['amendment'], approval['receipt']):
            if sha((ROOT / binding['path']).read_bytes()) != binding['sha256']:
                refuse(f'prior owner approval {binding["path"]} changed')
    receipt = {
        'schema': 'mcpcli-census-amendment-approval/v2', 'decision': 'approved', 'approvedOn': day, 'owner': OWNER,
        'approvalLabel': label, 'reason': REASON,
        # Owner lineage only: the approved inventory and the owner receipts 1.0.1 and 1.0.2, never a waiver receipt.
        'authority': [
            {'path': '_bmad-output/implementation-artifacts/evidence/story-5-1/approval/approval.json',
             'sha256': sha((ROOT / '_bmad-output/implementation-artifacts/evidence/story-5-1/approval/approval.json').read_bytes())},
            *[{'path': f'tools/proprietary-surfaces/v1/amendments/{version}-approval.json',
               'sha256': sha((V1 / f'amendments/{version}-approval.json').read_bytes())}
              for version in ('1.0.1', '1.0.2')]],
        'priorOwnerApprovals': prior,
        'authorization': authorization,
        'sourceReport': {'path': str((DRAFT / 'source-census.json').relative_to(ROOT)), 'sha256': sha(report_raw)},
        'sourceChecker': {'path': checker['path'], 'sha256': checker['sha256']},
        'sourcePins': {row['repository']: row['gitlink'] for row in report['repositories']},
        # This renewal accepts census classifications only.
        'runtimeAcceptance': False, 'migrationAcceptance': False,
    }
    receipt_raw = pretty(receipt)
    amendment = {'schema': 'mcpcli-proprietary-surface-census/v1', 'fromVersion': '1.0.6', 'toVersion': '1.0.7',
                 'previousSha256': previous['sha256'],
                 'approval': {'owner': OWNER, 'reason': REASON, 'decision': 'approved', 'date': day,
                              'evidence': {'path': RECEIPT, 'sha256': sha(receipt_raw)}},
                 **authorization}
    amendment_raw = pretty(amendment)
    return amendment_raw, receipt_raw, pretty(index + [{'path': 'amendments/1.0.7.json', 'sha256': sha(amendment_raw)}])


def load(workspace, policy):
    loaded = census.load_policy(workspace, census.Tree(ROOT, census.git(ROOT, 'rev-parse', '--verify', 'HEAD^{commit}')),
                                policy / 'baseline.json', policy / 'amendments.json', datetime.datetime.now(datetime.UTC).date())
    _, _, allowed, exclusions, _, provenance = loaded
    return {'result': 'loaded', 'version': provenance['version'], 'amendments': provenance['amendments'],
            'allowances': len(allowed), 'exclusions': len(exclusions)}


def rehearse(directory):
    work = Path(directory).resolve()
    if ROOT in (work, *work.parents) or (work.exists() and (not work.is_dir() or any(work.iterdir()))):
        refuse('rehearsal needs an empty directory outside the repository')
    amendment_raw, receipt_raw, index_raw = documents('REHEARSAL - not an owner approval', datetime.datetime.now(datetime.UTC).date().isoformat())
    policy = work / 'tools/proprietary-surfaces/v1'
    shutil.copytree(V1, policy, ignore=shutil.ignore_patterns('__pycache__'))
    (policy / 'amendments/1.0.7.json').write_bytes(amendment_raw)
    (policy / 'amendments/1.0.7-approval.json').write_bytes(receipt_raw)
    (policy / 'amendments.json').write_bytes(index_raw)
    for source in ('_bmad-output/implementation-artifacts/evidence/story-5-1/approval/approval.json',):
        (work / source).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / source, work / source)
    # The retained v1 receipt validates its fixture trees through these root checkouts.
    for root in ('references/Hexalith.Builds', 'references/Hexalith.Conversations'):
        (work / root).parent.mkdir(parents=True, exist_ok=True)
        (work / root).symlink_to(ROOT / root)
    print(json.dumps(load(work, policy), indent=2))


def write(label, approved, day):
    if not label.strip():
        refuse('the owner approval label is required verbatim')
    draft = json.loads((DRAFT / 'authorization.draft.json').read_text())
    if sha(canonical(draft).encode()) != approved:
        refuse('the draft is not the approved canonical bytes')
    targets = [V1 / 'amendments/1.0.7.json', ROOT / RECEIPT]
    if any(target.exists() for target in targets):
        refuse('1.0.7 already exists')
    amendment_raw, receipt_raw, index_raw = documents(label, day)
    staged = [(ROOT / RECEIPT, receipt_raw), (V1 / 'amendments/1.0.7.json', amendment_raw), (V1 / 'amendments.json', index_raw)]
    original_index = (V1 / 'amendments.json').read_bytes()
    temporary = []
    try:
        for target, raw in staged:
            part = target.with_name(target.name + '.partial')
            part.write_bytes(raw)
            temporary.append(part)
        for (target, _), part in zip(staged, temporary):
            os.replace(part, target)
        result = load(ROOT, V1)
    except BaseException:
        for part in temporary:
            part.unlink(missing_ok=True)
        for target in targets:
            target.unlink(missing_ok=True)
        (V1 / 'amendments.json').write_bytes(original_index)
        raise
    print(json.dumps({**result, 'amendmentSha256': sha(amendment_raw), 'receiptSha256': sha(receipt_raw)}, indent=2))


parser = argparse.ArgumentParser()
mode = parser.add_mutually_exclusive_group(required=True)
mode.add_argument('--rehearse', metavar='DIR')
mode.add_argument('--write', metavar='LABEL')
parser.add_argument('--approved-sha256')
parser.add_argument('--approved-on', default=datetime.datetime.now(datetime.UTC).date().isoformat())
arguments = parser.parse_args()
if arguments.write is not None:
    if not arguments.approved_sha256:
        refuse('--approved-sha256 is required with --write')
    write(arguments.write, arguments.approved_sha256, arguments.approved_on)
else:
    rehearse(arguments.rehearse)
