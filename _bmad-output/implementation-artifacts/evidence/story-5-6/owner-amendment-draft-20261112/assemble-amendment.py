"""Assemble census amendment 1.0.3 and its v2 receipt around the unchanged draft authorization.

  --rehearse DIR   Build the amendment and a rehearsal receipt in an empty scratch workspace
                   outside the repository and load the chain with check.py's own load_policy.
                   Nothing is written inside the repository.
  --write LABEL    Only after exact-byte owner approval: write amendments/1.0.3.json, its receipt
                   and the amendments.json entry, recording LABEL verbatim.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
DRAFT = Path(__file__).resolve().parent
V1 = ROOT / 'tools/proprietary-surfaces/v1'
RECEIPT = 'tools/proprietary-surfaces/v1/amendments/1.0.3-approval.json'
OWNER = 'Requesting user, owning maintainer'
REASON = ('Owner disposition of the 30 rejected identities and the Builds audit snapshot drift reported by the Story 5.6 '
          'final-2 census at the recorded pins: exact identities, signal sets and file hashes only.')
canonical = lambda value: json.dumps(value, sort_keys=True, separators=(',', ':'))
sha = lambda raw: hashlib.sha256(raw).hexdigest()
pretty = lambda value: (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def documents(label, day):
    authorization = json.loads((DRAFT / 'authorization.draft.json').read_text())
    index = json.loads((V1 / 'amendments.json').read_text())
    previous = index[-1]
    if previous['path'] != 'amendments/1.0.2.json' or sha((V1 / previous['path']).read_bytes()) != previous['sha256']:
        sys.exit('assemble-refused: the chain does not end at the indexed 1.0.2 amendment')
    report = DRAFT.parent / 'guard-excuse-review-20261111/runs/final-2/census.json'
    receipt = {
        'schema': 'mcpcli-census-amendment-approval/v2', 'decision': 'approved', 'approvedOn': day, 'owner': OWNER,
        'approvalLabel': label, 'reason': REASON,
        # Only the approved inventory and receipts already validated in this lineage may authorize.
        'authority': [
            {'path': '_bmad-output/implementation-artifacts/evidence/story-5-1/approval/approval.json',
             'sha256': sha((ROOT / '_bmad-output/implementation-artifacts/evidence/story-5-1/approval/approval.json').read_bytes())},
            *[{'path': f'tools/proprietary-surfaces/v1/amendments/{version}-approval.json',
               'sha256': sha((V1 / f'amendments/{version}-approval.json').read_bytes())} for version in ('1.0.1', '1.0.2')]],
        'authorization': authorization,
        'sourceReport': {'path': str(report.relative_to(ROOT)), 'sha256': sha(report.read_bytes())},
        'sourcePins': {row['repository']: row['gitlink'] for row in json.loads(report.read_text())['repositories']},
    }
    receipt_raw = pretty(receipt)
    amendment = {'schema': 'mcpcli-proprietary-surface-census/v1', 'fromVersion': '1.0.2', 'toVersion': '1.0.3',
                 'previousSha256': previous['sha256'],
                 'approval': {'owner': OWNER, 'reason': REASON, 'decision': 'approved', 'date': day,
                              'evidence': {'path': RECEIPT, 'sha256': sha(receipt_raw)}},
                 **authorization}
    amendment_raw = pretty(amendment)
    return amendment_raw, receipt_raw, index + [{'path': 'amendments/1.0.3.json', 'sha256': sha(amendment_raw)}]


def rehearse(directory):
    work = Path(directory).resolve()
    if ROOT in (work, *work.parents) or (work.exists() and any(work.iterdir())):
        sys.exit('assemble-refused: rehearsal needs an empty directory outside the repository')
    amendment_raw, receipt_raw, index = documents('REHEARSAL - not an owner approval', datetime.datetime.now(datetime.UTC).date().isoformat())
    policy = work / 'tools/proprietary-surfaces/v1'
    shutil.copytree(V1, policy, ignore=shutil.ignore_patterns('__pycache__'))
    (policy / 'amendments/1.0.3.json').write_bytes(amendment_raw)
    (policy / 'amendments/1.0.3-approval.json').write_bytes(receipt_raw)
    (policy / 'amendments.json').write_bytes(pretty(index))
    # The retained v1 receipt validates its fixture trees through these root checkouts.
    for root in ('references/Hexalith.Builds', 'references/Hexalith.Conversations'):
        (work / root).parent.mkdir(parents=True, exist_ok=True)
        (work / root).symlink_to(ROOT / root)
    spec = importlib.util.spec_from_file_location('census', V1 / 'check.py')
    census = importlib.util.module_from_spec(spec); spec.loader.exec_module(census)
    parent = census.Tree(ROOT, census.git(ROOT, 'rev-parse', '--verify', 'HEAD^{commit}'))
    loaded = census.load_policy(work, parent, policy / 'baseline.json', policy / 'amendments.json',
                                datetime.datetime.now(datetime.UTC).date())
    _, _, allowed, exclusions, _, provenance = loaded
    print(json.dumps({'result': 'loaded', 'version': provenance['version'], 'amendments': provenance['amendments'],
                      'allowances': len(allowed), 'exclusions': len(exclusions)}, indent=2))


def write(label):
    if not label.strip():
        sys.exit('assemble-refused: the owner approval label is required verbatim')
    if (V1 / 'amendments/1.0.3.json').exists() or (ROOT / RECEIPT).exists():
        sys.exit('assemble-refused: 1.0.3 already exists')
    amendment_raw, receipt_raw, index = documents(label, datetime.datetime.now(datetime.UTC).date().isoformat())
    (ROOT / RECEIPT).write_bytes(receipt_raw)
    (V1 / 'amendments/1.0.3.json').write_bytes(amendment_raw)
    (V1 / 'amendments.json').write_bytes(pretty(index))
    print('wrote 1.0.3', sha(amendment_raw), 'receipt', sha(receipt_raw))


parser = argparse.ArgumentParser()
mode = parser.add_mutually_exclusive_group(required=True)
mode.add_argument('--rehearse', metavar='DIR')
mode.add_argument('--write', metavar='LABEL')
arguments = parser.parse_args()
rehearse(arguments.rehearse) if arguments.rehearse else write(arguments.write)
