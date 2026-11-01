#!/usr/bin/env python3
"""Authenticate original staging artifacts and candidate-specific operator approval."""

import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
from zipfile import BadZipFile, ZipFile
from xml.etree import ElementTree

from paired_release import ROOT, digest, module, packages, read_json, validate_source_evidence, write_new

ARTIFACTS = ('paired-preparation', 'paired-consumer-ubuntu-latest', 'paired-consumer-windows-latest',
             'paired-consumer-macos-latest', 'accepted-staging-only')
STAGING_JOBS = {
    'stage-pair': ['Require staging dispatch from main', 'Refuse staging recovery',
                   'Recheck full-v1 source gates and prepare exactly one pair',
                   'Retain the sole staged pair or explicit no-release result'],
    **{f'smoke-pair ({system})': ['Install the same local tool bytes and run offline smoke',
                                'Execute required Windows Core and CLI suites or macOS CLI suite',
                                'Retain actual platform receipts and raw captures']
       for system in ('ubuntu-latest', 'windows-latest', 'macos-latest')},
    'accept-staged-pair': ['Require source still eligible after platform execution',
                           'Require every receipt, named Windows test and identical raw discovery bytes'],
}
TIMING = '_bmad-output/implementation-artifacts/evidence/story-4-17/timing-attempts.json'
TOOLS = {'list_modules', 'list_operations', 'describe_operation', 'send_command', 'run_query'}
OPERATIONS = {'tenants.get-tenant', 'parties.create-party', 'parties.get-party'}


def api(endpoint, *parameters):
    return module('verify-release-source').github_json(endpoint, *parameters)


def authenticate_run(repository, run_id, sha):
    if not re.fullmatch(r'[1-9][0-9]*', str(run_id)) or re.fullmatch(r'[0-9a-f]{40}', sha) is None:
        raise ValueError('An exact staging run ID and source SHA are required.')
    workflow = api(f'repos/{repository}/actions/workflows/release.yml')
    run = api(f'repos/{repository}/actions/runs/{run_id}')
    if (run.get('id') != int(run_id) or run.get('workflow_id') != workflow['id']
            or run.get('path') != '.github/workflows/release.yml' or run.get('head_sha') != sha
            or run.get('head_branch') != 'main' or run.get('event') != 'workflow_dispatch'
            or run.get('head_repository', {}).get('full_name') != repository
            or run.get('status') != 'completed' or run.get('conclusion') != 'success'):
        raise ValueError('Original staging must be a successful exact-source main Release dispatch in this repository.')
    module('verify-release-source').verify_jobs(repository, run, STAGING_JOBS)
    artifacts = []
    page = 1
    while True:
        response = api(f'repos/{repository}/actions/runs/{run_id}/artifacts', '-f', 'per_page=100', '-f', f'page={page}')
        artifacts.extend(response['artifacts'])
        if len(artifacts) >= response['total_count']:
            break
        if not response['artifacts']:
            raise ValueError('Incomplete staging artifact metadata.')
        page += 1
    selected = []
    for name in ARTIFACTS:
        matches = [item for item in artifacts if item['name'] == name]
        if len(matches) != 1:
            raise ValueError(f'Exactly one original staging artifact is required: {name}.')
        artifact = matches[0]
        origin = artifact.get('workflow_run', {})
        if (artifact.get('expired') is not False or not isinstance(artifact.get('id'), int)
                or re.fullmatch(r'sha256:[0-9a-f]{64}', artifact.get('digest', '')) is None
                or origin.get('id') != int(run_id) or origin.get('head_sha') != sha or origin.get('head_branch') != 'main'):
            raise ValueError(f'Staging artifact is expired, unauthenticated or belongs to different source: {name}.')
        selected.append({key: artifact[key] for key in ('id', 'name', 'digest')})
    return {'repository': repository, 'staging_run_id': int(run_id), 'source_sha': sha,
            'run_attempt': run['run_attempt'], 'completed_at': run['updated_at'], 'artifacts': selected}


def extract(archive, target):
    with ZipFile(io.BytesIO(archive)) as zipped:
        names = set()
        for item in zipped.infolist():
            name = PurePosixPath(item.filename)
            if (not item.filename or item.filename in names or name.is_absolute() or '..' in name.parts
                    or '\\' in item.filename or re.match(r'^[A-Za-z]:', item.filename)
                    or (item.external_attr >> 16) & 0o170000 == 0o120000):
                raise ValueError('Unsafe or duplicate staging artifact member.')
            names.add(item.filename)
        zipped.extractall(target)


def fetch(repository, run_id, sha, candidate):
    candidate = Path(candidate)
    # A failed attempt is retained; callers must choose a new destination.
    candidate.mkdir(parents=True, exist_ok=False)
    origin = authenticate_run(repository, run_id, sha)
    write_new(candidate / 'staging-origin.json', origin)
    for artifact in origin['artifacts']:
        response = subprocess.run(['gh', 'api', f'repos/{repository}/actions/artifacts/{artifact["id"]}/zip'],
                                  check=True, capture_output=True)
        if 'sha256:' + hashlib.sha256(response.stdout).hexdigest() != artifact['digest']:
            raise ValueError('Downloaded staging archive differs from GitHub artifact digest.')
        (candidate / (artifact['name'] + '.zip')).write_bytes(response.stdout)


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError('Operator evidence requires timestamp strings.')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('Operator evidence timestamps must include UTC offsets.')
    return parsed.astimezone(timezone.utc)


def credentials():
    return {os.environ.get(name, '') for name in ('GH_TOKEN', 'GITHUB_TOKEN', 'GH_ENTERPRISE_TOKEN',
            'GITHUB_ENTERPRISE_TOKEN', 'NUGET_API_KEY')} - {''}


def require_sanitized_operator(decision):
    serialized = json.dumps(decision, ensure_ascii=False)
    if any(value in serialized for value in credentials()):
        raise ValueError('Operator acceptance contains a GitHub or publication credential; redact the source evidence first.')


def record_operator(serialized, output):
    decision = json.loads(serialized)
    if not isinstance(decision, dict):
        raise ValueError('Operator acceptance must be a JSON object.')
    require_sanitized_operator(decision)
    write_new(output, decision)


def retain_operator(paths, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    entries = []
    for index, path in enumerate(paths):
        path = Path(path)
        if not path.exists() and not path.is_symlink():
            continue
        if path.is_symlink() or not path.is_file():
            entries.append({'input_name': path.name, 'status': 'refused-nonregular-file'})
            continue
        raw = path.read_bytes()
        decoded = raw.decode('utf-8')
        # Decode JSON escapes before credential matching; keep exact approved bytes when safe.
        try:
            normalized = json.dumps(json.loads(decoded), ensure_ascii=False, indent=2) + '\n'
        except ValueError:
            normalized = decoded
        redacted = any(value in decoded or value in normalized for value in credentials())
        retained = normalized if redacted else decoded
        for value in sorted(credentials(), key=len, reverse=True):
            retained = retained.replace(value, '[REDACTED]')
        name = str(index + 1) + '-' + path.name
        (output / name).write_text(retained, encoding='utf-8', newline='')
        entries.append({'input_name': path.name, 'retained_name': name, 'original_sha256': hashlib.sha256(raw).hexdigest(),
                        'retained_sha256': digest(output / name), 'redacted': redacted})
    write_new(output / 'retention.json', {'schema': 'mcpcli-operator-retention/v1', 'entries': entries})


def operator_acceptance(path, prepared, accepted_path, origin, actor):
    decision = read_json(path)
    require_sanitized_operator(decision)
    accepted = read_json(accepted_path)
    bindings = {key: prepared[key] for key in ('source_sha', 'version', 'packages')}
    bindings.update(staging_run_id=origin['staging_run_id'], preparation_sha256=accepted['preparation_sha256'],
                    acceptance_sha256=digest(accepted_path), readme_sha256=digest(ROOT / 'README.md'))
    if (decision.get('schema') != 'mcpcli-paired-operator-acceptance/v1' or decision.get('decision') != 'approved'
            or not actor or actor.endswith('[bot]') or decision.get('approved_by') != actor
            or any(decision.get(key) != value for key, value in bindings.items())):
        raise ValueError('Explicit authenticated operator decision must bind this exact staging run, source, pair and README.')
    decided_at = timestamp(decision['decided_at_utc'])
    if decided_at > datetime.now(timezone.utc):
        raise ValueError('Operator decision cannot be in the future.')
    timing = decision.get('timing_exception', {})
    historical = read_json(ROOT / TIMING)['attempts'][0]
    if (timing != {'reference': TIMING, 'sha256': digest(ROOT / TIMING), 'elapsed_seconds': 685,
                   'first_time_operator': False, 'unassisted_success': False, 'decision': 'accepted-existing-exception'}
            or historical['elapsedSeconds'] != 685 or historical['firstTimeOperator'] is not False
            or historical['unassistedSuccess'] is not False or not historical['assistance']):
        raise ValueError('The accepted assisted 685-second timing exception must remain explicit.')
    sessions = decision.get('sessions', [])
    if (not isinstance(sessions, list) or len(sessions) != 3 or any(not isinstance(item, dict) for item in sessions)
            or {item.get('client') for item in sessions} != {'Claude Code', 'Claude Desktop', 'VS Code'}):
        raise ValueError('Three fresh actual client sessions are required.')
    party_ids = set()
    for session in sessions:
        if (session.get('status') != 'passed' or session.get('actual_client') is not True
                or any(session.get(key) != value for key, value in bindings.items())
                or any(not session.get(key) for key in ('operator', 'observer', 'os_version', 'client_version', 'harness',
                                                       'launch_environment', 'executable_path', 'selected_tenant', 'party_id'))
                or not isinstance(session.get('assistance'), list) or not isinstance(session.get('failures'), list)):
            raise ValueError('Each actual session must retain its identity, candidate bindings, failures and assistance.')
        started, ended = timestamp(session['started_at_utc']), timestamp(session['ended_at_utc'])
        approval = session.get('environment_approval', {})
        if not isinstance(approval, dict):
            raise ValueError('A session needs an approved environment record.')
        if (not timestamp(origin['completed_at']) <= started <= ended <= decided_at
                or approval.get('decision') != 'approved' or approval.get('ready') is not True
                or not approval.get('owner') or not approval.get('target') or not approval.get('namespace_uid')
                or not timestamp(approval['approved_at_utc']) <= started <= ended <= timestamp(approval['expires_at_utc'])
                or approval.get('tenant') != session['selected_tenant']):
            raise ValueError('Fresh sessions require their own approved ready environment and valid time window.')
        evidence = session.get('evidence', {})
        required = {'initialization', 'discovery', 'tenant_read', 'command', 'persisted_party', 'cleanup', 'environment_approval'}
        if not isinstance(evidence, dict) or set(evidence) != required:
            raise ValueError('Actual sanitized client and environment evidence is incomplete.')
        for record in evidence.values():
            if not isinstance(record, dict):
                raise ValueError('Each actual evidence excerpt needs content and its hash.')
            content = record.get('content')
            if (not isinstance(content, str) or not content.strip()
                    or hashlib.sha256(content.encode('utf-8')).hexdigest() != record.get('sha256')):
                raise ValueError('Operator evidence content differs from its bound hash.')
        if (session.get('server_identity') != {'name': 'hexalith', 'version': prepared['version']}
                or set(session.get('tools', [])) != TOOLS or set(session.get('modules', [])) != {'parties', 'tenants'}
                or set(session.get('described_operations', [])) != OPERATIONS
                or set(session.get('operation_lists', [])) != {'parties', 'tenants'}):
            raise ValueError('Actual initialization, both operation lists and three descriptions must be evidenced.')
        command = session.get('command_result', {})
        persisted = session.get('persisted_party', {})
        tenant = session.get('tenant_read', {})
        if not all(isinstance(record, dict) for record in (command, persisted, tenant)):
            raise ValueError('Actual session result documents are required.')
        ulid = r'[0-7][0-9A-HJKMNP-TV-Z]{25}'
        if (tenant.get('tenant') != 'system' or tenant.get('document_id') != session['selected_tenant']
                or tenant.get('is_active') is not True or tenant.get('membership_verified') is not True
                or command.get('status') != 'accepted' or command.get('tenant') != session['selected_tenant']
                or command.get('aggregate_id') != session['party_id']
                or any(re.fullmatch(ulid, command.get(key, '')) is None for key in ('message_id', 'correlation_id'))
                or persisted.get('tenant') != session['selected_tenant'] or persisted.get('id') != session['party_id']
                or persisted.get('isActive') is not True or persisted.get('isErased') is not False
                or not persisted.get('synthetic_fields_verified') or session['party_id'] in party_ids):
            raise ValueError('Client sessions must prove the approved command and matching persisted synthetic Party.')
        party_ids.add(session['party_id'])
    return decision


def validate_pair_content(staging, version, sha):
    for name in packages(staging, version):
        identity = name[:-len('.' + version + '.nupkg')]
        with ZipFile(Path(staging) / name) as archive:
            names = archive.namelist()
            if len(names) != len(set(names)) or any(
                    PurePosixPath(item).is_absolute() or '..' in PurePosixPath(item).parts or '\\' in item for item in names):
                raise ValueError('The immutable package has unsafe or duplicate members.')
            specs = [item for item in names if item.endswith('.nuspec')]
            if len(specs) != 1:
                raise ValueError('The immutable package must have one nuspec.')
            metadata = ElementTree.fromstring(archive.read(specs[0])).find('{*}metadata')
            if (metadata is None or metadata.findtext('{*}id') != identity
                    or metadata.findtext('{*}version') != version
                    or metadata.find('{*}repository') is None
                    or metadata.find('{*}repository').get('commit') != sha):
                raise ValueError('Package identity, shared version or source differs from the accepted pair.')
            if archive.read('README.md') != (ROOT / 'README.md').read_bytes():
                raise ValueError('The immutable package README differs from the current source README.')


def validate(candidate, operator_path, version, sha, run_id, actor, output):
    candidate = Path(candidate)
    recorded = read_json(candidate / 'staging-origin.json')
    origin = authenticate_run(os.environ['REPOSITORY'], run_id, sha)
    if recorded != origin:
        raise ValueError('Original staging run or artifact identities changed after retrieval.')
    expected = {'staging-origin.json', *(name + '.zip' for name in ARTIFACTS)}
    if candidate.is_symlink() or {item.name for item in candidate.iterdir()} != expected:
        raise ValueError('The candidate must contain only authenticated original staging archives.')
    with tempfile.TemporaryDirectory(prefix='mcpcli-publication-check-') as temporary:
        root = Path(temporary)
        for artifact in origin['artifacts']:
            archive = candidate / (artifact['name'] + '.zip')
            if archive.is_symlink() or not archive.is_file() or 'sha256:' + digest(archive) != artifact['digest']:
                raise ValueError('Original staging archive changed after authentication.')
            extract(archive.read_bytes(), root / artifact['name'])
        preparation = root / 'paired-preparation'
        prepared_path = preparation / 'prepared.json'
        prepared = read_json(prepared_path)
        if prepared.get('source_sha') != sha or prepared.get('version') != version:
            raise ValueError('Staging source or shared version differs from semantic-release selection.')
        accepted_path = root / 'accepted-staging-only/accepted-pair.json'
        recomputed = root / 'recomputed.json'
        module('compare-paired-evidence').compare(preparation / 'packages', prepared_path,
            [root / name for name in ARTIFACTS if name.startswith('paired-consumer-')], recomputed)
        if read_json(recomputed) != read_json(accepted_path):
            raise ValueError('Original staging acceptance does not equal recomputed acceptance.')
        acceptance_source = root / 'accepted-staging-only/acceptance-source.json'
        validate_source_evidence(read_json(acceptance_source), sha)
        validate_pair_content(preparation / 'packages', version, sha)
        operator_acceptance(operator_path, prepared, accepted_path, origin, actor)
        fresh_source = root / 'publication-source.json'
        subprocess.run([sys.executable, str(ROOT / 'scripts/verify-release-source.py'), '--output', str(fresh_source),
                        '--', sha, os.environ.get('DISPATCH_REF', ''), 'paired'], check=True, capture_output=True)
        validate_source_evidence(read_json(fresh_source), sha)
        receipt = {'schema': 'mcpcli-paired-publication-preflight/v1', 'status': 'passed',
                   'source_sha': sha, 'version': version, 'packages': packages(preparation / 'packages', version),
                   'origin': origin, 'preparation_sha256': digest(prepared_path),
                   'acceptance_sha256': digest(accepted_path), 'acceptance_source_sha256': digest(acceptance_source),
                   'operator_sha256': digest(operator_path), 'operator_actor': actor,
                   'source_evidence': read_json(fresh_source)}
        write_new(output, receipt)
        return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest='command', required=True)
    record = subparsers.add_parser('record-operator')
    record.add_argument('--output', type=Path, required=True)
    retain = subparsers.add_parser('retain-operator')
    retain.add_argument('--input', type=Path, action='append', required=True)
    retain.add_argument('--output', type=Path, required=True)
    download = subparsers.add_parser('fetch')
    download.add_argument('--repository', required=True)
    for command in (download, subparsers.add_parser('verify')):
        command.add_argument('--staging-run', required=True)
        command.add_argument('--source-sha', required=True)
        command.add_argument('--candidate', type=Path, required=True)
    verify = subparsers.choices['verify']
    verify.add_argument('--version', required=True)
    verify.add_argument('--operator', type=Path, required=True)
    verify.add_argument('--actor', required=True)
    verify.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'record-operator':
            record_operator(os.environ.get('OPERATOR_ACCEPTANCE', ''), args.output)
        elif args.command == 'retain-operator':
            retain_operator(args.input, args.output)
        elif args.command == 'fetch':
            fetch(args.repository, args.staging_run, args.source_sha, args.candidate)
        else:
            if os.environ.get('MCPCLI_RECOVERY_VERSION') or os.environ.get('RECOVERY_VERSION'):
                raise ValueError('Paired recovery is unsupported.')
            module('release-request').check_registry(args.version, 'paired')
            validate(args.candidate, args.operator, args.version, args.source_sha, args.staging_run, args.actor, args.output)
        return 0
    except (ValueError, KeyError, TypeError, OSError, BadZipFile, ElementTree.ParseError, subprocess.CalledProcessError) as error:
        detail = module('verify-release-source').failure_detail(error)
        if args.command in ('verify', 'record-operator'):
            failure = args.output.with_name(args.output.name + '.failure.json')
            write_new(failure, {'schema': 'mcpcli-paired-publication-refusal/v1', 'status': 'refused', 'reason': detail})
        print(f'Paired publication refused: {detail}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
