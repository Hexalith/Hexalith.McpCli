#!/usr/bin/env python3
"""Run this repository's unchanged census against candidate policy and existing objects.

Scratch .git files provide read-only access to existing object stores; dependency
files are never checked out. This helper cannot establish hosted acceptance.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
import uuid


MEASURED_SCOPE = 'SHA-256 of existing HEAD, index, packed-refs and file contents beneath refs; no other Git files, objects, configuration or filesystem metadata'


def load_census():
    checker = Path(__file__).resolve().parents[2] / 'tools/proprietary-surfaces/v1/check.py'
    spec = importlib.util.spec_from_file_location('census', checker)
    census = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(census)
    return census


def measured_git_files(directory):
    paths = [directory / 'HEAD', directory / 'index', directory / 'packed-refs']
    paths += sorted((directory / 'refs').rglob('*')) if (directory / 'refs').is_dir() else []
    return {str(path.relative_to(directory)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in paths if path.is_file()}


def copy_receipts(census, owner, policy_root, overlay):
    index = census.json_bytes((policy_root / 'amendments.json').read_bytes(), 'amendment-index')
    census.require(isinstance(index, list), 'invalid-amendment-index')
    for item in index:
        census.require(isinstance(item, dict) and set(item) == {'path', 'sha256'}, 'invalid-amendment-index')
        relative = census.safe_path(item['path'])
        amendment_path = policy_root / relative
        census.require(not amendment_path.is_symlink() and amendment_path.is_file(), 'amendment-file-missing')
        amendment = census.json_bytes(amendment_path.read_bytes(), relative)
        relative = census.safe_path(amendment['approval']['evidence']['path'])
        source = owner / relative
        # Preserve load_policy's refusal instead of materializing a symlink's target.
        census.require(not source.is_symlink() and source.is_file(), 'amendment-approval-mismatch')
        destination = overlay / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)


def run_candidate(owner, source, output, census):
    owner, source, output = Path(owner), Path(source), Path(output)
    os.environ['GIT_OPTIONAL_LOCKS'] = '0'
    revision, roots, stores = None, {}, {}
    scan_returned, unchanged, checker_hash = False, None, None
    stage = 'prerequisites'
    provenance = {'mode': 'candidate-policy-overlay-against-committed-source-trees',
                  'attemptId': uuid.uuid4().hex,
                  'startedAtUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  'finalCommittedScan': False, 'hostedAcceptance': False,
                  'measuredGitFileContentScope': MEASURED_SCOPE}
    try:
        checker_hash = hashlib.sha256(Path(census.__file__).read_bytes()).hexdigest()
        owner, source = owner.resolve(), source.resolve()
        revision = census.git(owner, 'rev-parse', 'HEAD')
        parent = census.Tree(owner, revision)
        roots = census.declarations(parent)
        for repository in roots:
            census.safe_path(repository)
        stores = {repository: Path(census.git(source / repository, 'rev-parse', '--absolute-git-dir'))
                  for repository in roots}
        stores['.'] = Path(census.git(owner, 'rev-parse', '--absolute-git-dir'))
        before = {repository: measured_git_files(directory) for repository, directory in stores.items()}
        policy_root = owner / 'tools/proprietary-surfaces/v1'
        with tempfile.TemporaryDirectory(prefix='mcpcli-census-candidate-') as scratch:
            overlay = Path(scratch)
            (overlay / '.git').write_text('gitdir: ' + str(stores['.']) + '\n')
            for repository in roots:
                facade = overlay / repository
                facade.mkdir(parents=True)
                (facade / '.git').write_text('gitdir: ' + str(stores[repository]) + '\n')
            stage = 'receipt-preparation'
            copy_receipts(census, owner, policy_root, overlay)
            stage = 'census'
            report = census.scan(overlay, revision, policy_root / 'baseline.json',
                                 policy_root / 'amendments.json', datetime.datetime.now(datetime.timezone.utc).date())
            scan_returned = True
        stage = 'measured-git-files'
        after = {repository: measured_git_files(directory) for repository, directory in stores.items()}
        unchanged = before == after
        census.require(unchanged, 'measured-git-file-content-changed')
    except (census.CensusError, OSError, UnicodeError, TypeError, KeyError, AttributeError, ValueError) as error:
        report = {'schema': census.SCHEMA, 'status': 'failed', 'inspectionComplete': False,
                  'surfaces': [], 'errors': [{'rule': str(error) if isinstance(error, census.CensusError)
                                             else 'candidate-prerequisite-or-policy-failure'}]}
        provenance['failureStage'] = stage
    provenance.update(ownerRevision=revision, sourcePins=roots,
                      checkerSha256=checker_hash,
                      measuredGitFileContentsUnchanged=unchanged,
                      objectStores={repository: str(directory) for repository, directory in stores.items()},
                      scanReturned=scan_returned, inspectionSucceeded=report['status'] == 'passed',
                      status=report['status'])
    output.parent.mkdir(parents=True, exist_ok=True)
    rendered = census.sanitized(json.dumps(report, indent=2, sort_keys=True) + '\n')
    output.write_text(rendered)
    provenance['reportSha256'] = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_name(output.stem + '-provenance.json').write_text(
        census.sanitized(json.dumps(provenance, indent=2) + '\n'))
    print(census.sanitized(json.dumps({'status': report['status'], 'mode': provenance['mode'],
                                     'surfaces': len(report.get('surfaces', [])), 'errors': report.get('errors', []),
                                     'rejected': [row for row in report.get('surfaces', [])
                                                  if row['status'] == 'rejected']}, indent=2)))
    return 0 if report['status'] == 'passed' else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--owner', type=Path, required=True)
    parser.add_argument('--object-stores', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    return run_candidate(args.owner, args.object_stores, args.output, load_census())


if __name__ == '__main__':
    raise SystemExit(main())
