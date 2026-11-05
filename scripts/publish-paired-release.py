#!/usr/bin/env python3
"""Import and publish an accepted immutable pair without building or automatic recovery."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

from paired_release import PAIR, digest, module, packages, read_json, write_new

IMPORTED = Path('nupkgs/paired')
OUTCOMES = Path('nupkgs/paired-publication')
MARKER = 'mcpcli-paired-publication-started'


def refuse_recovery():
    if os.environ.get('MCPCLI_RECOVERY_VERSION') or os.environ.get('RECOVERY_VERSION'):
        raise ValueError('Paired recovery is unsupported; preserve outcomes for evidence-based manual recovery.')


def preflight(candidate, operator, version, output):
    return module('verify-paired-publication').validate(candidate, operator, version, os.environ['DISPATCH_SHA'],
        os.environ['MCPCLI_STAGING_RUN_ID'], os.environ['GITHUB_ACTOR'], output)


def prepare(version):
    refuse_recovery()
    module('release-request').validate_request(version, 'paired')
    original = read_json(os.environ['MCPCLI_PAIRED_PREFLIGHT'])
    if original.get('schema') != 'mcpcli-paired-publication-preflight/v1' or original.get('status') != 'passed':
        raise ValueError('A successful hash-bound paired preflight receipt is required.')
    if IMPORTED.exists() or IMPORTED.is_symlink():
        raise ValueError('Paired import already exists; preserve it and use a fresh checkout.')
    operator = read_json(os.environ['MCPCLI_OPERATOR_ACCEPTANCE'])
    module('verify-paired-publication').require_sanitized_operator(operator)
    IMPORTED.mkdir(parents=True)
    # Copy original archives and the explicit operator decision, never repack.
    shutil.copytree(os.environ['MCPCLI_PAIRED_CANDIDATE'], IMPORTED / 'candidate', symlinks=True)
    shutil.copyfile(os.environ['MCPCLI_OPERATOR_ACCEPTANCE'], IMPORTED / 'operator.json')
    checked = preflight(IMPORTED / 'candidate', IMPORTED / 'operator.json', version, IMPORTED / 'preflight.json')
    bindings = ('source_sha', 'version', 'packages', 'origin', 'preparation_sha256', 'acceptance_sha256',
                'acceptance_source_sha256', 'operator_sha256', 'operator_actor', 'operator_decision')
    if any(original.get(key) != checked[key] for key in bindings):
        raise ValueError('Preflight bindings changed before import.')
    verifier = module('verify-paired-publication')
    with tempfile.TemporaryDirectory(prefix='mcpcli-import-') as temporary:
        verifier.extract((IMPORTED / 'candidate/paired-preparation.zip').read_bytes(), Path(temporary))
        shutil.copytree(Path(temporary) / 'packages', IMPORTED / 'packages')
    if packages(IMPORTED / 'packages', version) != checked['packages']:
        raise ValueError('Imported package bytes differ from authenticated staging.')
    write_new(IMPORTED / 'import.json', {'schema': 'mcpcli-paired-import/v1', **{key: checked[key] for key in bindings},
              'preflight_sha256': digest(IMPORTED / 'preflight.json')})


def reserve_version(version, sha):
    gate = module('verify-release-source')
    repository = os.environ['REPOSITORY']
    endpoint = f'repos/{repository}/git/matching-refs/tags/'
    global_refs = gate.github_json(endpoint + MARKER)
    if not isinstance(global_refs, list):
        raise ValueError('Uncertain paired-publication state marker.')
    global_refs = [item for item in global_refs if item.get('ref') == 'refs/tags/' + MARKER]
    if len(global_refs) > 1:
        raise ValueError('Duplicate paired-publication state marker.')
    version_marker = MARKER + '-v' + version
    if gate.github_json(endpoint + version_marker) != []:
        raise ValueError('This paired publication already started; automatic duplicate pushes are refused.')
    if not global_refs:
        subprocess.run(['gh', 'api', '--method', 'POST', f'repos/{repository}/git/refs',
                        '-f', 'ref=refs/tags/' + MARKER, '-f', 'sha=' + sha], check=True, capture_output=True)
    subprocess.run(['gh', 'api', '--method', 'POST', f'repos/{repository}/git/refs',
                    '-f', 'ref=refs/tags/' + version_marker, '-f', 'sha=' + sha], check=True, capture_output=True)


def consumer_digest(contents):
    return hashlib.sha256(json.dumps({name: hashlib.sha256(value).hexdigest() for name, value in sorted(contents.items())},
                                     sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def publish(version):
    refuse_recovery()
    module('release-request').validate_request(version, 'paired')
    # A prior outcome directory means this attempt has already begun, even if a push timed out.
    OUTCOMES.mkdir(parents=True, exist_ok=False)
    result = {'schema': 'mcpcli-paired-publication-outcome/v1', 'status': 'failed-before-push',
              'source_sha': os.environ.get('DISPATCH_SHA'), 'version': version,
              'staging_run_id': os.environ.get('MCPCLI_STAGING_RUN_ID'),
              'packages': {identity: {'status': 'not-attempted'} for identity in PAIR}}
    try:
        module('release-request').check_registry(version, 'paired')
        imported = read_json(IMPORTED / 'import.json')
        if imported.get('schema') != 'mcpcli-paired-import/v1':
            raise ValueError('A completed immutable paired import is required.')
        with tempfile.TemporaryDirectory(prefix='mcpcli-publication-snapshot-') as temporary:
            snapshot = Path(temporary) / 'pair'
            shutil.copytree(IMPORTED, snapshot, symlinks=True)
            checked = preflight(snapshot / 'candidate', snapshot / 'operator.json', version, OUTCOMES / 'snapshot-preflight.json')
            if (imported.get('preflight_sha256') != digest(snapshot / 'preflight.json')
                    or any(imported.get(key) != checked[key] for key in
                           ('source_sha', 'version', 'packages', 'origin', 'preparation_sha256', 'acceptance_sha256',
                            'acceptance_source_sha256', 'operator_sha256', 'operator_actor', 'operator_decision'))
                    or packages(snapshot / 'packages', version) != checked['packages']):
                raise ValueError('Imported archives, receipts or snapshot packages changed before publication.')
            result.update(preflight_sha256=digest(OUTCOMES / 'snapshot-preflight.json'), packages_sha256=checked['packages'],
                          operator_sha256=checked['operator_sha256'], operator_actor=checked['operator_actor'],
                          operator_decision=checked['operator_decision'], origin=checked['origin'])
            public = OUTCOMES / 'public'
            public.mkdir()
            recovery = module('recover-bootstrap-release')
            for index, identity in enumerate(PAIR):
                filename = f'{identity}.{version}.nupkg'
                package = snapshot / 'packages' / filename
                # Check availability and all fresh source/evidence gates immediately before each push.
                available = module('release-request').registry_versions(identity, allow_first_absence=True)
                if version.lower() in {item.lower() for item in available}:
                    raise ValueError(f'{identity} {version} became occupied before its push.')
                preflight(snapshot / 'candidate', snapshot / 'operator.json', version,
                          OUTCOMES / f'before-push-{index + 1}.json')
                if packages(snapshot / 'packages', version) != checked['packages']:
                    raise ValueError('Snapshot package bytes changed before push.')
                if index == 0:
                    reserve_version(version, checked['source_sha'])
                    write_new(OUTCOMES / 'publication-started.json', {'source_sha': checked['source_sha'],
                              'version': version, 'packages': checked['packages'], 'origin': checked['origin'],
                              'operator_sha256': checked['operator_sha256']})
                outcome = result['packages'][identity]
                outcome.update(status='push-uncertain', staged_sha256=digest(package))
                # Persist intent before invoking NuGet. A process kill cannot erase that a push may have happened.
                write_new(OUTCOMES / f'{index + 1}-push-intent.json', {'package_id': identity, 'version': version, **outcome})
                pushed = subprocess.run(['dotnet', 'nuget', 'push', str(package), '--source',
                                         'https://api.nuget.org/v3/index.json', '--api-key', os.environ['NUGET_API_KEY']],
                                        capture_output=True, text=True)
                sanitize = module('verify-release-source').failure_detail
                write_new(OUTCOMES / f'{index + 1}-push-result.json', {'package_id': identity, 'exit_code': pushed.returncode,
                          'stdout': sanitize(pushed.stdout), 'stderr': sanitize(pushed.stderr)})
                if pushed.returncode != 0:
                    raise ValueError(f'{identity} push failed or is uncertain (exit {pushed.returncode}); no automatic retry.')
                outcome['status'] = 'push-succeeded-public-unverified'
            # Both guarded pushes finish before waiting for NuGet indexing or comparing public contents.
            for index, identity in enumerate(PAIR):
                filename = f'{identity}.{version}.nupkg'
                package = snapshot / 'packages' / filename
                outcome = result['packages'][identity]
                downloaded = public / filename
                url = (f'https://api.nuget.org/v3-flatcontainer/{identity.lower()}/{version.lower()}/'
                       f'{identity.lower()}.{version.lower()}.nupkg')
                recovery.download_public_package(url, downloaded, pushed=True)
                with ZipFile(downloaded) as archive:
                    if len(archive.namelist()) != len(set(archive.namelist())):
                        raise ValueError('Public package has duplicate archive members.')
                staged_contents, public_contents = recovery.content(package), recovery.content(downloaded)
                if staged_contents != public_contents:
                    raise ValueError(f'{identity} public consumer contents differ from the immutable accepted archive.')
                outcome.update(status='public-verified', public_url=url, public_sha256=digest(downloaded),
                               consumer_content_sha256=consumer_digest(public_contents))
                write_new(OUTCOMES / f'{index + 1}-public-verification.json', {'package_id': identity, 'version': version, **outcome})
            result['status'] = 'paired-public-verified'
    except BaseException as error:
        result['reason'] = module('verify-release-source').failure_detail(error)
        if any(item['status'] != 'not-attempted' for item in result['packages'].values()):
            result['status'] = 'partial-or-uncertain'
        raise
    finally:
        write_new(OUTCOMES / 'outcome.json', result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'publish'])
    parser.add_argument('--version', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'prepare':
            prepare(args.version)
        else:
            publish(args.version)
        return 0
    except (ValueError, KeyError, TypeError, OSError, BadZipFile, ElementTree.ParseError, subprocess.CalledProcessError) as error:
        print(f'Paired {args.command} failed: {module("verify-release-source").failure_detail(error)}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
