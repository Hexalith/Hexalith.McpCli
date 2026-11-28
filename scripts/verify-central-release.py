#!/usr/bin/env python3
"""Verify central Hexalith.Builds release candidates and post-publish package inventories.

Separates CI fixture package hashes (prepared.json), final ContinuousIntegrationBuild=true
archive hashes (release-manifest.json), and signed nuget.org archive hashes
(hexalith-package-publication.v1.json). Never publishes packages, tags, or releases.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from xml.etree import ElementTree
import zipfile

from evidence_redaction import ShortEvidenceCredentialError, require_evidence_credentials, sanitized, sanitized_values
from product_packages import PAIR, ROOT, digest, failure_detail, packages, source_changes, source_sha as git_source_sha, validate_version, write_new
from product_process import run as run_owned

MANIFEST_PATH = Path('tools/release-packages.json')
TIMING_PATH = Path('docs/release/operator-setup-timing-exception.json')
SORTED_PAIR = sorted(PAIR)
SHA40_RE = re.compile(r'[0-9a-f]{40}\Z')
SHA64_RE = re.compile(r'[0-9a-f]{64}\Z')
ARTIFACT_DIGEST_RE = re.compile(r'sha256:[0-9a-f]{64}\Z')
REPOSITORY = 'Hexalith/Hexalith.McpCli'
BOT_ACTORS = {'github-actions', 'dependabot', 'renovate', 'hexalith-bot'}
REQUIRED_SMOKE_CHECKS = {
    'version', 'offline-discovery', 'config', 'json-lf',
    'errors', 'mcp-protocol', 'output-file', 'table',
}
REQUIRED_PLATFORMS = {'Linux', 'Windows', 'Darwin'}
ACCEPTANCE_REQUIRED_KEYS = {
    'schema', 'decision', 'version', 'source_sha', 'final_packages',
    'ci_receipt_sha256', 'approved_by', 'decided_at_utc', 'timing_exception',
}
ACCEPTANCE_OPTIONAL_KEYS = {'readme_sha256', 'release_run_id', 'artifact_digest'}
MAX_ARCHIVE_BYTES = 2 * 1024 ** 3


def _unique_json_pairs(label: str):
    def hook(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f'{label}: duplicate JSON key {key!r}.')
            result[key] = value
        return result
    return hook


def _reject_json_constant(label: str):
    def parser(value):
        raise ValueError(f'{label}: invalid JSON constant {value!r}.')
    return parser


def read_strict_json(path: Path, label: str) -> tuple[dict, str]:
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError(f'{label}: expected an existing regular file at {path}.')
    raw = path.read_bytes()
    try:
        document = json.loads(
            raw.decode('utf-8'),
            object_pairs_hook=_unique_json_pairs(label),
            parse_constant=_reject_json_constant(label),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f'{label}: invalid UTF-8 JSON: {error}') from error
    if not isinstance(document, dict):
        raise ValueError(f'{label}: root JSON value must be an object.')
    require_evidence_credentials()
    if sanitized_values(document) != document:
        raise ValueError(f'{label}: contains a credential or private key; redact before verification.')
    return document, hashlib.sha256(raw).hexdigest()


def parse_utc_timestamp(value: object, label: str) -> datetime:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f'{label}: must be an ISO-8601 UTC timestamp string.')
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as error:
        raise ValueError(f'{label}: invalid timestamp {value!r}.') from error
    if parsed.utcoffset() != timedelta(0):
        raise ValueError(f'{label}: timestamp must include an explicit UTC timezone offset.')
    return parsed.astimezone(timezone.utc)


def validate_sha40(value: object, label: str) -> str:
    if not isinstance(value, str) or SHA40_RE.fullmatch(value) is None:
        raise ValueError(f'{label}: must be a 40-character lowercase hex SHA.')
    return value


def validate_sha64(value: object, label: str) -> str:
    if not isinstance(value, str) or SHA64_RE.fullmatch(value) is None:
        raise ValueError(f'{label}: must be a 64-character lowercase hex SHA-256.')
    return value


def validate_human_actor(actor: object, expected_actor: str | None = None) -> str:
    if (not isinstance(actor, str) or not actor or actor != actor.strip()
            or re.search(r'[\s\x00-\x1f\x7f]', actor) is not None):
        raise ValueError('Central acceptance approved_by must be a non-empty human actor identifier.')
    lowered = actor.lower()
    if lowered.endswith('[bot]') or lowered.endswith('-bot') or lowered in BOT_ACTORS:
        raise ValueError(f'Central acceptance approved_by refuses bot actor {actor!r}.')
    if expected_actor is not None and actor != expected_actor:
        raise ValueError(f'Central acceptance approved_by {actor!r} does not match expected actor {expected_actor!r}.')
    return actor


def safe_archive_path(name: str) -> bool:
    return (
        isinstance(name, str) and bool(name) and not name.startswith('/')
        and not any(char in name for char in ('\\', ':'))
        and all(part not in ('', '.', '..') for part in name.split('/'))
        and not any(ord(char) < 32 or 127 <= ord(char) <= 159 for char in name)
    )


def payload_map_from_nupkg(path: Path) -> dict[str, str]:
    """Compute sorted nonsignature member SHA-256 map matching Hexalith.Builds package_publication."""
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError(f'Package archive must be a regular file: {path}')
    if path.stat().st_size > MAX_ARCHIVE_BYTES:
        raise ValueError(f'Package archive exceeds size limit: {path}')
    try:
        with zipfile.ZipFile(path) as archive:
            seen: set[str] = set()
            result: dict[str, str] = {}
            total = 0
            for entry in archive.infolist():
                name = entry.filename.removesuffix('/') if entry.is_dir() else entry.filename
                if not safe_archive_path(name) or name.casefold() in seen:
                    raise ValueError(f'Package archive {path.name} has unsafe or duplicate member {entry.filename!r}.')
                seen.add(name.casefold())
                mode = (entry.external_attr >> 16) & 0o170000
                if mode not in (0, 0o040000 if entry.is_dir() else 0o100000) or entry.flag_bits & 1:
                    raise ValueError(f'Package archive {path.name} has non-regular or encrypted member {entry.filename!r}.')
                total += entry.file_size
                if entry.file_size > MAX_ARCHIVE_BYTES or total > MAX_ARCHIVE_BYTES:
                    raise ValueError(f'Package archive {path.name} payload exceeds size limit.')
                if not entry.is_dir() and name != '.signature.p7s':
                    result[name] = hashlib.sha256(archive.read(entry)).hexdigest()
            return dict(sorted(result.items()))
    except (zipfile.BadZipFile, OSError, RuntimeError, NotImplementedError) as error:
        raise ValueError(f'Invalid package archive {path.name}: {error}') from error


def inspect_final_archives(
    packages_dir: Path,
    version: str,
    source_sha: str,
    *,
    readme_path: Path | None = None,
    release_manifest_path: Path | None = None,
) -> tuple[dict[str, str], dict | None]:
    validate_version(version)
    validate_sha40(source_sha, 'source_sha')
    packages_dir = Path(packages_dir)
    actual_digests = packages(packages_dir, version)
    expected_readme = None
    if readme_path is not None:
        readme = Path(readme_path)
        if readme.is_symlink() or not readme.is_file():
            raise ValueError(f'Source README must be a regular file: {readme}')
        expected_readme = readme.read_bytes()

    for package_id in PAIR:
        filename = f'{package_id}.{version}.nupkg'
        archive_path = packages_dir / filename
        payload_map_from_nupkg(archive_path)
        with zipfile.ZipFile(archive_path) as archive:
            if any(name.casefold() == '.signature.p7s' for name in archive.namelist()):
                raise ValueError(f'Expected the original unsigned final archive for {filename}.')
            nuspecs = [name for name in archive.namelist() if name.endswith('.nuspec') and '/' not in name]
            if len(nuspecs) != 1:
                raise ValueError(f'{filename} must contain exactly one root .nuspec.')
            try:
                tree = ElementTree.fromstring(archive.read(nuspecs[0]))
            except ElementTree.ParseError as error:
                raise ValueError(f'{filename} has malformed .nuspec XML: {error}') from error
            metadata = tree.find('{*}metadata')
            if metadata is None:
                raise ValueError(f'{filename} .nuspec is missing metadata.')
            if metadata.findtext('{*}id') != package_id:
                raise ValueError(f'{filename} .nuspec id mismatch: expected {package_id}.')
            if metadata.findtext('{*}version') != version:
                raise ValueError(f'{filename} .nuspec version mismatch: expected {version}.')
            repository = metadata.find('{*}repository')
            commit = repository.get('commit') if repository is not None else None
            if commit != source_sha:
                raise ValueError(
                    f'Source SHA mismatch in {filename} .nuspec: expected {source_sha}, found {commit!r}.'
                )
            if expected_readme is not None:
                try:
                    packed_readme = archive.read('README.md')
                except KeyError as error:
                    raise ValueError(f'{filename} is missing packed README.md.') from error
                if packed_readme != expected_readme:
                    raise ValueError(f'{filename} packed README.md differs from source README.')

    manifest_summary = None
    if release_manifest_path is not None:
        manifest, manifest_sha = read_strict_json(release_manifest_path, 'release-manifest.json')
        if manifest.get('sha') != source_sha:
            raise ValueError(
                f"Source SHA mismatch in release-manifest.json: expected {source_sha}, found {manifest.get('sha')!r}."
            )
        if manifest.get('version') != version:
            raise ValueError(
                f"Version mismatch in release-manifest.json: expected {version}, found {manifest.get('version')!r}."
            )
        if manifest.get('containers') != []:
            raise ValueError('release-manifest.json must declare an empty containers list for McpCli.')
        entries = manifest.get('packages')
        if (not isinstance(entries, list) or len(entries) != len(SORTED_PAIR)
                or [item.get('id') for item in entries if isinstance(item, dict)] != SORTED_PAIR):
            raise ValueError(f'release-manifest.json packages must list exactly {SORTED_PAIR}.')
        for item in entries:
            pkg_id = item['id']
            expected_rel = f'packages/{pkg_id}.{version}.nupkg'
            if item.get('path') != expected_rel:
                raise ValueError(f'release-manifest.json path mismatch for {pkg_id}: expected {expected_rel!r}.')
            if item.get('verifyPublishedPackage') is not True:
                raise ValueError(f'release-manifest.json must set verifyPublishedPackage=true for {pkg_id}.')
            manifest_file = Path(release_manifest_path).parent / expected_rel
            if manifest_file.parent.is_symlink() or manifest_file.is_symlink() or not manifest_file.is_file():
                raise ValueError(f'release-manifest.json must reference an existing regular package file: {manifest_file}.')
            file_digest = digest(manifest_file)
            expected_digest = actual_digests[f'{pkg_id}.{version}.nupkg']
            if file_digest != expected_digest:
                raise ValueError(
                    f'Final package digest mismatch for {pkg_id}.{version}.nupkg: '
                    f'manifest path has {file_digest}, staged dir has {expected_digest}.'
                )
        manifest_summary = {'path': str(Path(release_manifest_path)), 'sha256': manifest_sha}

    return actual_digests, manifest_summary


def validate_timing_exception(timing: object, root: Path = ROOT) -> dict:
    if not isinstance(timing, dict):
        raise ValueError('Central acceptance timing_exception must be a JSON object.')
    reference = timing.get('reference')
    if isinstance(reference, str) and reference.startswith('_bmad-output/'):
        raise ValueError('Central acceptance timing_exception must not reference _bmad-output/.')
    status = timing.get('status')
    if status == 'accepted-existing-exception':
        timing_file = Path(root) / TIMING_PATH
        timing_doc, timing_sha = read_strict_json(timing_file, 'timing exception record')
        attempts = timing_doc.get('attempts')
        if not isinstance(attempts, list) or not attempts or not isinstance(attempts[0], dict):
            raise ValueError('Tracked timing exception file is missing attempts[0].')
        first = attempts[0]
        if (first.get('elapsedSeconds') != 685 or first.get('firstTimeOperator') is not False
                or first.get('unassistedSuccess') is not False or not first.get('assistance')):
            raise ValueError('Tracked timing exception file does not preserve the accepted 685 s assisted record.')
        expected = {
            'status': 'accepted-existing-exception',
            'reference': TIMING_PATH.as_posix(),
            'sha256': timing_sha,
            'elapsed_seconds': 685,
            'first_time_operator': False,
            'unassisted_success': False,
        }
        if timing != expected:
            raise ValueError(
                'Central acceptance timing_exception must match docs/release/operator-setup-timing-exception.json.'
            )
        return dict(timing)
    if status == 'superseded-by-fresh-measurement':
        if (not isinstance(reference, str) or not safe_archive_path(reference)
                or reference.startswith('_bmad-output/')):
            raise ValueError('Fresh timing_exception reference must be a safe tracked path outside _bmad-output/.')
        expected_sha = validate_sha64(timing.get('sha256'), 'timing_exception.sha256')
        ref_path = (Path(root) / reference).resolve()
        root_resolved = Path(root).resolve()
        if not ref_path.is_relative_to(root_resolved) or ref_path.is_symlink() or not ref_path.is_file():
            raise ValueError('Fresh timing_exception reference file is missing or outside repository root.')
        if digest(ref_path) != expected_sha:
            raise ValueError('Fresh timing_exception sha256 does not match the referenced file.')
        elapsed = timing.get('elapsed_seconds')
        if (type(elapsed) is not int or not 1 <= elapsed <= 900
                or timing.get('first_time_operator') is not True
                or timing.get('unassisted_success') is not True):
            raise ValueError('Fresh timing_exception must record a first-time unassisted run within 900 seconds.')
        return dict(timing)
    raise ValueError(f'Central acceptance has unsupported timing_exception status {status!r}.')


def validate_ci_fixture_prepared(ci_prepared_path: Path, source_sha: str) -> tuple[dict[str, str], str]:
    doc, doc_sha = read_strict_json(ci_prepared_path, 'CI fixture prepared.json')
    if doc.get('schema') != 'mcpcli-product-packages/v1':
        raise ValueError('CI fixture prepared.json must use schema mcpcli-product-packages/v1.')
    if doc.get('source_sha') != source_sha:
        raise ValueError(
            f"Source SHA mismatch in CI fixture prepared.json: expected {source_sha}, found {doc.get('source_sha')!r}."
        )
    ci_version = doc.get('version')
    if not isinstance(ci_version, str):
        raise ValueError('CI fixture prepared.json is missing version.')
    validate_version(ci_version)
    pkgs = doc.get('packages')
    expected_names = {f'{pkg}.{ci_version}.nupkg' for pkg in PAIR}
    if not isinstance(pkgs, dict) or set(pkgs) != expected_names:
        raise ValueError('CI fixture prepared.json must contain hashes for the exact manifest pair.')
    validated = {name: validate_sha64(sha, f'CI fixture {name}') for name, sha in sorted(pkgs.items())}
    return validated, doc_sha


def validate_ci_receipt(
    ci_receipt_path: Path,
    source_sha: str,
    ci_fixture_packages: dict[str, str],
) -> tuple[dict, str, datetime]:
    doc, doc_sha = read_strict_json(ci_receipt_path, '3-OS CI receipt')
    if doc.get('schema') != 'mcpcli-central-ci-receipt/v1':
        raise ValueError('3-OS CI receipt must use schema mcpcli-central-ci-receipt/v1.')
    if doc.get('source_sha') != source_sha:
        raise ValueError(
            f"Source SHA mismatch in 3-OS CI receipt: expected {source_sha}, found {doc.get('source_sha')!r}."
        )
    if doc.get('repository') != REPOSITORY:
        raise ValueError(f'3-OS CI receipt repository must be {REPOSITORY}.')
    if type(doc.get('ci_run_id')) is not int or doc['ci_run_id'] < 1:
        raise ValueError('3-OS CI receipt requires a positive integer ci_run_id.')
    if doc.get('status') != 'completed' or doc.get('conclusion') != 'success':
        raise ValueError('3-OS CI receipt must record status=completed and conclusion=success.')
    completed_at = parse_utc_timestamp(doc.get('completed_at_utc'), '3-OS CI receipt completed_at_utc')
    platforms = doc.get('platforms')
    if not isinstance(platforms, dict) or set(platforms) != REQUIRED_PLATFORMS:
        raise ValueError(f'3-OS CI receipt must cover exact platforms {sorted(REQUIRED_PLATFORMS)}.')
    for system, entry in platforms.items():
        if not isinstance(entry, dict) or entry.get('status') != 'passed':
            raise ValueError(f'3-OS CI receipt platform {system} did not pass.')
    receipt_fixtures = doc.get('ci_fixture_packages')
    if receipt_fixtures != ci_fixture_packages:
        raise ValueError('3-OS CI receipt ci_fixture_packages differs from CI fixture prepared.json.')
    return doc, doc_sha, completed_at


def _check_package_map(actual: dict[str, str], claimed: object, label: str) -> None:
    if not isinstance(claimed, dict) or set(claimed) != set(actual):
        raise ValueError(f'{label}: package map must cover exact pair {sorted(actual)}.')
    for name, expected_digest in actual.items():
        got = claimed.get(name)
        if got != expected_digest:
            raise ValueError(
                f'{label}: final package digest mismatch for {name}: expected {expected_digest}, found {got!r}.'
            )


def validate_validation_receipt(
    path: Path, source_sha: str, version: str, final_packages: dict[str, str]
) -> tuple[dict, str]:
    doc, doc_sha = read_strict_json(path, 'validator receipt')
    if doc.get('phase') != 'paired':
        raise ValueError('Validator receipt must record phase=paired.')
    if doc.get('source_sha') != source_sha:
        raise ValueError(
            f"Source SHA mismatch in validator receipt: expected {source_sha}, found {doc.get('source_sha')!r}."
        )
    if doc.get('version') != version:
        raise ValueError(f"Validator receipt version mismatch: expected {version}, found {doc.get('version')!r}.")
    _check_package_map(final_packages, doc.get('packages'), 'validator receipt')
    return doc, doc_sha


def validate_smoke_receipt(
    path: Path, source_sha: str, version: str, final_packages: dict[str, str]
) -> tuple[dict, str]:
    doc, doc_sha = read_strict_json(path, 'tool smoke receipt')
    if doc.get('schema') != 'mcpcli-paired-smoke/v1' or doc.get('status') != 'passed':
        raise ValueError('Tool smoke receipt must be a passing mcpcli-paired-smoke/v1 document.')
    if doc.get('source_sha') != source_sha:
        raise ValueError(
            f"Source SHA mismatch in tool smoke receipt: expected {source_sha}, found {doc.get('source_sha')!r}."
        )
    if doc.get('version') != version:
        raise ValueError(f"Tool smoke receipt version mismatch: expected {version}, found {doc.get('version')!r}.")
    _check_package_map(final_packages, doc.get('packages'), 'tool smoke receipt')
    checks = doc.get('checks')
    if not isinstance(checks, list) or set(checks) != REQUIRED_SMOKE_CHECKS:
        raise ValueError(
            f'Tool smoke receipt checks must cover {sorted(REQUIRED_SMOKE_CHECKS)}; found {checks!r}.'
        )
    discovery = doc.get('discovery')
    if (not isinstance(discovery, dict)
            or not {'modules.json', 'mcp-tools.json', 'mcp-modules.json'} <= set(discovery)
            or any(not isinstance(sha, str) or SHA64_RE.fullmatch(sha) is None for sha in discovery.values())):
        raise ValueError('Tool smoke receipt discovery hashes are incomplete or malformed.')
    return doc, doc_sha


def validate_consumer_receipt(
    path: Path, source_sha: str, version: str, final_packages: dict[str, str]
) -> tuple[dict, str]:
    doc, doc_sha = read_strict_json(path, 'consumer smoke receipt')
    if doc.get('schema') not in ('mcpcli-central-consumer/v1', 'mcpcli-paired-consumer/v1') or doc.get('status') != 'passed':
        raise ValueError('Consumer smoke receipt must be a passing consumer verification document.')
    if doc.get('source_sha') != source_sha:
        raise ValueError(
            f"Source SHA mismatch in consumer smoke receipt: expected {source_sha}, found {doc.get('source_sha')!r}."
        )
    if doc.get('version') != version:
        raise ValueError(f"Consumer smoke receipt version mismatch: expected {version}, found {doc.get('version')!r}.")
    _check_package_map(final_packages, doc.get('packages'), 'consumer smoke receipt')
    if doc['schema'] == 'mcpcli-paired-consumer/v1':
        validate_sha64(doc.get('compiler_sha256'), 'Consumer smoke receipt compiler_sha256')
        validate_sha64(doc.get('command_sha256'), 'Consumer smoke receipt command_sha256')
    elif type(doc.get('exit_code')) is not int or doc['exit_code'] != 0:
        raise ValueError('Consumer smoke receipt must record exit_code=0.')
    elif doc.get('warning_code') != 'MCPCLI001':
        raise ValueError('Consumer smoke receipt must record MCPCLI001.')
    return doc, doc_sha


def validate_central_acceptance(
    acceptance_path: Path,
    *,
    source_sha: str,
    version: str,
    final_packages: dict[str, str],
    ci_receipt_sha256: str,
    ci_completed_at: datetime,
    ci_fixture_digests: set[str],
    expected_actor: str | None = None,
    readme_path: Path | None = None,
    root: Path = ROOT,
    now: datetime | None = None,
) -> tuple[dict, str]:
    doc, doc_sha = read_strict_json(acceptance_path, 'central acceptance')
    # Reject any human-validation bypass attempt before other schema checks.
    if (doc.get('schema') == 'mcpcli-paired-automated-acceptance/v1'
            or doc.get('authorization') == 'user-requested-human-validation-bypass'
            or any('bypass' in str(key).lower() or 'user-requested-human-validation-bypass' in str(val).lower()
                   for key, val in doc.items())):
        raise ValueError(
            'Central acceptance error: user-requested-human-validation-bypass and legacy automated bypass '
            'schemas are forbidden for future candidates.'
        )
    missing = sorted(ACCEPTANCE_REQUIRED_KEYS - set(doc))
    extra = sorted(set(doc) - ACCEPTANCE_REQUIRED_KEYS - ACCEPTANCE_OPTIONAL_KEYS)
    if missing:
        raise ValueError(f'Central acceptance error: missing required fields {missing}.')
    if extra:
        raise ValueError(f'Central acceptance error: unexpected fields {extra}.')
    if doc['schema'] != 'mcpcli-central-release-acceptance/v1':
        raise ValueError(f"Central acceptance error: invalid schema {doc['schema']!r}.")
    if doc['decision'] != 'approved':
        raise ValueError(f"Central acceptance error: decision must be 'approved', found {doc['decision']!r}.")
    if doc['source_sha'] != source_sha:
        raise ValueError(
            f"Source SHA mismatch in central acceptance: expected {source_sha}, found {doc['source_sha']!r}."
        )
    if doc['version'] != version:
        raise ValueError(
            f"Central acceptance error: version mismatch: expected {version}, found {doc['version']!r}."
        )
    if doc['ci_receipt_sha256'] != ci_receipt_sha256:
        raise ValueError(
            'Central acceptance error: ci_receipt_sha256 does not bind the exact 3-OS CI receipt.'
        )
    validate_human_actor(doc['approved_by'], expected_actor=expected_actor)
    decided_at = parse_utc_timestamp(doc['decided_at_utc'], 'central acceptance decided_at_utc')
    current_time = now or datetime.now(timezone.utc)
    if decided_at < ci_completed_at:
        raise ValueError('Central acceptance error: decided_at_utc cannot precede 3-OS CI completion.')
    if decided_at > current_time:
        raise ValueError('Central acceptance error: decided_at_utc cannot be in the future.')

    claimed = doc['final_packages']
    if not isinstance(claimed, dict) or set(claimed) != set(final_packages):
        raise ValueError(
            f'Central acceptance error: final_packages must bind exact pair {sorted(final_packages)}.'
        )
    for name, expected_digest in final_packages.items():
        claimed_digest = validate_sha64(claimed.get(name), f'central acceptance final_packages[{name}]')
        if claimed_digest in ci_fixture_digests:
            raise ValueError(
                f'Fixture hash rejected for {name}: central acceptance binds CI fixture hash {claimed_digest} '
                f'instead of final archive hash {expected_digest}.'
            )
        if claimed_digest != expected_digest:
            raise ValueError(
                f'Final package digest mismatch for {name}: acceptance has {claimed_digest}, '
                f'actual archive has {expected_digest}.'
            )
    for name, actual_digest in final_packages.items():
        if actual_digest in ci_fixture_digests:
            raise ValueError(
                f'Fixture hash rejected for {name}: final archive hash {actual_digest} matches CI fixture prepared.json; '
                'CI fixture packages cannot substitute for ContinuousIntegrationBuild=true release archives.'
            )

    if 'readme_sha256' in doc:
        claimed_readme = validate_sha64(doc['readme_sha256'], 'central acceptance readme_sha256')
        if readme_path is not None and digest(readme_path) != claimed_readme:
            raise ValueError('Central acceptance error: readme_sha256 does not match source README.')
    if 'release_run_id' in doc and (type(doc['release_run_id']) is not int or doc['release_run_id'] < 1):
        raise ValueError('Central acceptance error: release_run_id must be a positive integer.')
    if 'artifact_digest' in doc and (
        not isinstance(doc['artifact_digest'], str) or ARTIFACT_DIGEST_RE.fullmatch(doc['artifact_digest']) is None
    ):
        raise ValueError('Central acceptance error: artifact_digest must match sha256:<64-hex>.')

    validate_timing_exception(doc['timing_exception'], root=root)
    return doc, doc_sha


def check_project_packaging(root: Path = ROOT, solution: str = 'Hexalith.McpCli.slnx') -> dict[str, dict[str, str]]:
    root = Path(root)
    manifest_file = root / MANIFEST_PATH
    manifest = json.loads(manifest_file.read_text(encoding='utf-8'))['packages']
    if [item['id'] for item in manifest] != list(PAIR):
        raise ValueError(f'Manifest {MANIFEST_PATH} must declare exact pair {list(PAIR)}.')
    manifest_by_path = {Path(item['project']).as_posix(): item['id'] for item in manifest}
    slnx = ElementTree.parse(root / solution).getroot()
    project_paths = [
        Path(node.attrib['Path'].replace('\\', '/')).as_posix()
        for node in slnx.findall('.//Project')
        if 'Path' in node.attrib
    ]
    if not project_paths:
        raise ValueError(f'No projects found in solution {solution}.')
    missing_from_solution = sorted(set(manifest_by_path) - set(project_paths))
    if missing_from_solution:
        raise ValueError(f'Manifest projects missing from {solution}: {missing_from_solution}.')

    evaluated: dict[str, dict[str, str]] = {}
    props = 'IsPackable,PackageId,HexalithVerifyPublishedPackage,IsTestProject'
    for rel_path in sorted(project_paths):
        result = subprocess.run(
            ['dotnet', 'msbuild', str(root / rel_path), '-nologo', '-tl:off',
             '-p:Configuration=Release', f'-getProperty:{props}'],
            check=True, capture_output=True, text=True, cwd=root,
        )
        values = json.loads(result.stdout)['Properties']
        packable = values.get('IsPackable', '').lower() == 'true'
        verify_pub = values.get('HexalithVerifyPublishedPackage', '').lower() == 'true'
        is_test = values.get('IsTestProject', '').lower() == 'true'
        pkg_id = values.get('PackageId', '')
        evaluated[rel_path] = {
            'IsPackable': str(packable).lower(),
            'PackageId': pkg_id,
            'HexalithVerifyPublishedPackage': str(verify_pub).lower(),
            'IsTestProject': str(is_test).lower(),
        }
        if rel_path in manifest_by_path:
            expected_id = manifest_by_path[rel_path]
            if not packable or is_test or pkg_id != expected_id:
                raise ValueError(
                    f'Manifest project {rel_path} must be a packable non-test project with PackageId={expected_id}.'
                )
            if not verify_pub:
                raise ValueError(f'Manifest project {rel_path} must set HexalithVerifyPublishedPackage=true.')
        else:
            if packable:
                raise ValueError(f'Non-manifest project {rel_path} must set IsPackable=false.')
            if verify_pub:
                raise ValueError(f'Non-manifest project {rel_path} must not set HexalithVerifyPublishedPackage=true.')
    return evaluated


def require_clean_source(root: Path, source_sha: str) -> None:
    actual_head = git_source_sha(cwd=root)
    if actual_head != source_sha:
        raise ValueError(f'Source SHA mismatch: git HEAD is {actual_head}, expected {source_sha}.')
    if source_changes(cwd=root):
        raise ValueError('Working tree has uncommitted changes; clean release source is required.')


def check_archives(
    *,
    packages_dir: Path,
    version: str,
    source_sha: str,
    release_manifest_path: Path,
    output: Path,
    root: Path = ROOT,
) -> None:
    require_clean_source(root, source_sha)
    packages_dir = packages_dir.absolute()
    output = output.absolute()
    if output.exists() or output.is_symlink():
        raise ValueError(f'Archive check output already exists: {output}')
    final_packages, _ = inspect_final_archives(
        packages_dir, version, source_sha,
        readme_path=root / 'README.md', release_manifest_path=release_manifest_path,
    )
    output.mkdir(parents=True)
    prepared = output / 'final-prepared.json'
    write_new(prepared, {
        'schema': 'mcpcli-paired-preparation/v1', 'source_sha': source_sha, 'version': version,
        'tool_version': f'{version}+{source_sha}', 'packages': final_packages,
    })
    scripts = root / 'scripts'
    run_owned(
        [sys.executable, scripts / 'validate-release-packages.py', packages_dir, version, 'paired',
         '--source-sha', source_sha, '--output', output / 'validation.json'],
        cwd=root, output=output / 'validate', timeout=300,
    )
    run_owned(
        [sys.executable, scripts / 'smoke-paired-tool.py', '--staging', packages_dir,
         '--prepared', prepared, '--output', output / 'smoke'],
        cwd=root, output=output / 'tool-check', timeout=900,
    )
    run_owned(
        [sys.executable, scripts / 'smoke_bootstrap_consumer.py', version, packages_dir, output / 'consumer'],
        cwd=root, output=output / 'consumer-check', timeout=300,
    )
    require_clean_source(root, source_sha)
    _check_package_map(packages(packages_dir, version), final_packages, 'archive checks')
    write_new(output / 'consumer.json', {
        'schema': 'mcpcli-central-consumer/v1', 'status': 'passed', 'source_sha': source_sha,
        'version': version, 'packages': final_packages, 'exit_code': 0, 'warning_code': 'MCPCLI001',
    })


def verify_candidate(
    *,
    packages_dir: Path,
    version: str,
    source_sha: str,
    validation_path: Path,
    smoke_path: Path,
    consumer_path: Path,
    ci_receipt_path: Path,
    acceptance_path: Path,
    output: Path,
    release_manifest_path: Path,
    ci_prepared_path: Path,
    readme_path: Path | None = None,
    expected_actor: str | None = None,
    require_clean_git: bool = False,
    check_projects: bool = False,
    root: Path = ROOT,
    now: datetime | None = None,
) -> dict:
    validate_version(version)
    validate_sha40(source_sha, 'source_sha')
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise ValueError(f'Verification receipt already exists and will not be overwritten: {output}')

    if require_clean_git:
        require_clean_source(root, source_sha)

    packaging = check_project_packaging(root=root) if check_projects else None

    final_packages, manifest_summary = inspect_final_archives(
        packages_dir, version, source_sha,
        readme_path=readme_path,
        release_manifest_path=release_manifest_path,
    )

    ci_fixture_packages, ci_prepared_sha = validate_ci_fixture_prepared(ci_prepared_path, source_sha)
    _, ci_receipt_sha, ci_completed_at = validate_ci_receipt(
        ci_receipt_path, source_sha, ci_fixture_packages,
    )

    _, validation_sha = validate_validation_receipt(validation_path, source_sha, version, final_packages)
    _, smoke_sha = validate_smoke_receipt(smoke_path, source_sha, version, final_packages)
    _, consumer_sha = validate_consumer_receipt(consumer_path, source_sha, version, final_packages)

    ci_fixture_digests = set(ci_fixture_packages.values())
    acceptance, acceptance_sha = validate_central_acceptance(
        acceptance_path,
        source_sha=source_sha,
        version=version,
        final_packages=final_packages,
        ci_receipt_sha256=ci_receipt_sha,
        ci_completed_at=ci_completed_at,
        ci_fixture_digests=ci_fixture_digests,
        expected_actor=expected_actor,
        readme_path=readme_path,
        root=root,
        now=now,
    )

    receipt = {
        'schema': 'mcpcli-central-release-verification/v1',
        'status': 'passed',
        'non_publishing': True,
        'source_sha': source_sha,
        'version': version,
        'ci_fixture_packages': ci_fixture_packages,
        'final_packages': final_packages,
        'signed_public_packages': {},
        'receipts': {
            'ci_prepared_sha256': ci_prepared_sha,
            'ci_receipt_sha256': ci_receipt_sha,
            'release_manifest_sha256': manifest_summary['sha256'],
            'validation_sha256': validation_sha,
            'smoke_sha256': smoke_sha,
            'consumer_sha256': consumer_sha,
            'acceptance_sha256': acceptance_sha,
        },
        'approved_by': acceptance['approved_by'],
        'decided_at_utc': acceptance['decided_at_utc'],
        'timing_exception': acceptance['timing_exception'],
    }
    for key in ('release_run_id', 'artifact_digest'):
        if key in acceptance:
            receipt[key] = acceptance[key]
    if packaging is not None:
        receipt['project_packaging'] = packaging
    _check_package_map(packages(packages_dir, version), final_packages, 'candidate archives')
    output.parent.mkdir(parents=True, exist_ok=True)
    write_new(output, receipt)
    return receipt


def verify_published(
    *,
    publication_path: Path,
    packages_dir: Path,
    source_sha: str,
    version: str,
    output: Path,
    candidate_receipt_path: Path,
    readme_path: Path | None = None,
) -> dict:
    validate_version(version)
    validate_sha40(source_sha, 'source_sha')
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise ValueError(f'Publication verification receipt already exists: {output}')

    final_packages, _ = inspect_final_archives(packages_dir, version, source_sha, readme_path=readme_path)

    candidate, candidate_sha = read_strict_json(candidate_receipt_path, 'candidate verification receipt')
    if candidate.get('schema') != 'mcpcli-central-release-verification/v1' or candidate.get('status') != 'passed':
        raise ValueError('Candidate verification receipt must be a passing mcpcli-central-release-verification/v1.')
    if candidate.get('source_sha') != source_sha:
        raise ValueError(
            f"Source SHA mismatch in candidate receipt: expected {source_sha}, found {candidate.get('source_sha')!r}."
        )
    if candidate.get('version') != version:
        raise ValueError(
            f"Version mismatch in candidate receipt: expected {version}, found {candidate.get('version')!r}."
        )
    _check_package_map(final_packages, candidate.get('final_packages'), 'candidate receipt')

    pub, pub_sha = read_strict_json(publication_path, 'hexalith-package-publication.v1.json')
    expected_fields = {
        'schema', 'repository', 'sha', 'version', 'artifactRun', 'artifactId', 'artifactDigest', 'packages',
    }
    if set(pub) != expected_fields or pub['schema'] != 'hexalith.package-publication.v1':
        raise ValueError('Post-publish inventory must match schema hexalith.package-publication.v1.')
    if pub['repository'] != REPOSITORY:
        raise ValueError(f'Post-publish inventory repository must be {REPOSITORY}.')
    if pub['sha'] != source_sha:
        raise ValueError(
            f"Source SHA mismatch in hexalith-package-publication.v1.json: expected {source_sha}, found {pub['sha']!r}."
        )
    if pub['version'] != version:
        raise ValueError(
            f"Version mismatch in hexalith-package-publication.v1.json: expected {version}, found {pub['version']!r}."
        )
    if any(type(pub[key]) is not int or pub[key] < 1 for key in ('artifactRun', 'artifactId')):
        raise ValueError('Post-publish inventory has invalid artifactRun or artifactId.')
    if not isinstance(pub['artifactDigest'], str) or ARTIFACT_DIGEST_RE.fullmatch(pub['artifactDigest']) is None:
        raise ValueError('Post-publish inventory has invalid artifactDigest.')
    for candidate_key, publication_key in (('release_run_id', 'artifactRun'), ('artifact_digest', 'artifactDigest')):
        if candidate_key in candidate and candidate[candidate_key] != pub[publication_key]:
            raise ValueError(f'Post-publish inventory {publication_key} differs from candidate receipt.')
    entries = pub['packages']
    if not isinstance(entries, list):
        raise ValueError('Post-publish inventory packages must be an array.')
    identities = [item.get('id') for item in entries if isinstance(item, dict)]
    if len(entries) != len(SORTED_PAIR) or identities != SORTED_PAIR:
        raise ValueError(f'Post-publish inventory packages must list exact sorted pair {SORTED_PAIR}.')

    signed_public_packages: dict[str, str] = {}
    for entry in entries:
        if set(entry) != {'id', 'archiveSha256', 'files'}:
            raise ValueError(f"Post-publish inventory entry for {entry.get('id')!r} has invalid keys.")
        pkg_id = entry['id']
        filename = f'{pkg_id}.{version}.nupkg'
        signed_sha = validate_sha64(entry['archiveSha256'], f'published {filename} archiveSha256')
        claimed_files = entry['files']
        if not isinstance(claimed_files, dict) or not claimed_files:
            raise ValueError(f'Post-publish inventory files map is empty for {pkg_id}.')
        seen_paths: set[str] = set()
        for name, file_sha in claimed_files.items():
            if not safe_archive_path(name) or name == '.signature.p7s' or name.casefold() in seen_paths:
                raise ValueError(f'Post-publish inventory has unsafe or duplicate file path {name!r} in {pkg_id}.')
            validate_sha64(file_sha, f'published {pkg_id}:{name}')
            seen_paths.add(name.casefold())
        local_files = payload_map_from_nupkg(Path(packages_dir) / filename)
        if claimed_files != local_files:
            raise ValueError(
                f'Post-publish nonsignature payload differs from final archive for {filename}.'
            )
        signed_public_packages[filename] = signed_sha

    receipt = {
        'schema': 'mcpcli-central-publication-verification/v1',
        'status': 'passed',
        'source_sha': source_sha,
        'version': version,
        'repository': pub['repository'],
        'artifact_run': pub['artifactRun'],
        'artifact_id': pub['artifactId'],
        'artifact_digest': pub['artifactDigest'],
        'ci_fixture_packages': candidate['ci_fixture_packages'],
        'final_packages': final_packages,
        'signed_public_packages': dict(sorted(signed_public_packages.items())),
        'publication_inventory_sha256': pub_sha,
        'candidate_receipt_sha256': candidate_sha,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    write_new(output, receipt)
    return receipt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest='command', required=True)

    checks = subparsers.add_parser('check-archives', help='Run local checks against the downloaded final archives.')
    checks.add_argument('--packages-dir', type=Path, required=True)
    checks.add_argument('--version', required=True)
    checks.add_argument('--source-sha', required=True)
    checks.add_argument('--release-manifest', type=Path, required=True)
    checks.add_argument('--output', type=Path, required=True)

    cand = subparsers.add_parser('verify-candidate', help='Verify final release candidate archives and receipts.')
    cand.add_argument('--packages-dir', type=Path, required=True)
    cand.add_argument('--version', required=True)
    cand.add_argument('--source-sha', required=True)
    cand.add_argument('--validation', type=Path, required=True)
    cand.add_argument('--smoke', type=Path, required=True)
    cand.add_argument('--consumer', type=Path, required=True)
    cand.add_argument('--ci-receipt', type=Path, required=True)
    cand.add_argument('--acceptance', type=Path, required=True)
    cand.add_argument('--output', type=Path, required=True)
    cand.add_argument('--release-manifest', type=Path, required=True)
    cand.add_argument('--ci-prepared', type=Path, required=True)
    cand.add_argument('--readme', type=Path)
    cand.add_argument('--expected-actor')
    cand.add_argument('--require-clean-git', action='store_true')
    cand.add_argument('--check-projects', action='store_true')

    pub = subparsers.add_parser('verify-published', help='Verify hexalith-package-publication.v1.json against final archives.')
    pub.add_argument('--publication', type=Path, required=True)
    pub.add_argument('--packages-dir', type=Path, required=True)
    pub.add_argument('--version', required=True)
    pub.add_argument('--source-sha', required=True)
    pub.add_argument('--output', type=Path, required=True)
    pub.add_argument('--candidate-receipt', type=Path, required=True)
    pub.add_argument('--readme', type=Path)

    proj = subparsers.add_parser('check-projects', help='Verify IsPackable and HexalithVerifyPublishedPackage across the solution.')
    proj.add_argument('--solution', default='Hexalith.McpCli.slnx')
    proj.add_argument('--output', type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        require_evidence_credentials()
        if args.command == 'check-archives':
            check_archives(
                packages_dir=args.packages_dir,
                version=args.version,
                source_sha=args.source_sha,
                release_manifest_path=args.release_manifest,
                output=args.output,
            )
        elif args.command == 'verify-candidate':
            verify_candidate(
                packages_dir=args.packages_dir,
                version=args.version,
                source_sha=args.source_sha,
                validation_path=args.validation,
                smoke_path=args.smoke,
                consumer_path=args.consumer,
                ci_receipt_path=args.ci_receipt,
                acceptance_path=args.acceptance,
                output=args.output,
                release_manifest_path=args.release_manifest,
                ci_prepared_path=args.ci_prepared,
                readme_path=args.readme,
                expected_actor=args.expected_actor,
                require_clean_git=args.require_clean_git,
                check_projects=args.check_projects,
            )
        elif args.command == 'verify-published':
            verify_published(
                publication_path=args.publication,
                packages_dir=args.packages_dir,
                source_sha=args.source_sha,
                version=args.version,
                output=args.output,
                candidate_receipt_path=args.candidate_receipt,
                readme_path=args.readme,
            )
        else:
            result = check_project_packaging(solution=args.solution)
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                write_new(args.output, {'schema': 'mcpcli-project-packaging/v1', 'status': 'passed', 'projects': result})
        return 0
    except ShortEvidenceCredentialError as error:
        print(sanitized(f'Central release verification failed: {error}'), file=sys.stderr)
        return 1
    except (ValueError, KeyError, TypeError, OSError, zipfile.BadZipFile, ElementTree.ParseError, subprocess.SubprocessError) as error:
        print(f'Central release verification failed: {failure_detail(error)}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
