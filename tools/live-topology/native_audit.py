"""Audit exact restored package bytes in private fixtures, without restoring module outputs."""
from __future__ import annotations

import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

PACKAGE_SOURCE = 'https://api.nuget.org/v3/index.json'
ADVISORY_ORIGIN = 'https://data.nuget.org'
AUDIT_SOURCE = ADVISORY_ORIGIN + '/v3/index.json'
INDEX = ADVISORY_ORIGIN + '/v3/vulnerabilities/index.json'
PAGE_PREFIX = ADVISORY_ORIGIN + '/v3-vulnerabilities/'

CLASSIFICATION_MATCH = 'match'
CLASSIFICATION_CONFIRMED_ROTATION = 'confirmed_rotation'
CLASSIFICATION_UNAVAILABLE = 'unavailable'
CLASSIFICATION_PERSISTENT_MISMATCH = 'persistent_mismatch'
CLASSIFICATION_ADVISORY_AFFECTING_GRAPH = 'advisory_affecting_graph'

_ISO8601_RE = re.compile(
    r'^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?(Z|[+-]\d{2}:\d{2})$'
)
_REDACTED_HEADERS = frozenset({'authorization', 'proxy-authorization', 'cookie', 'set-cookie'})
_NU19_CODE_RE = re.compile(r'\b(NU190[0-4])\b', re.IGNORECASE)
_ADVISORY_ERROR_CODES = frozenset({'NU1901', 'NU1902', 'NU1903', 'NU1904'})


class AdvisoryVerificationError(ValueError):
    """Structured advisory verification failure carrying classification and diagnostic."""

    def __init__(self, message: str, classification: str, diagnostic: dict):
        super().__init__(message)
        self.classification = classification
        self.diagnostic = diagnostic


def write_restore_config(config: Path) -> None:
    """Use the official audit-only endpoint for both restores and advisory proof."""
    config.write_text('<configuration><packageSources><clear/><add key="nuget.org" value="' + PACKAGE_SOURCE
                      + '"/></packageSources><auditSources><clear/><add key="nuget.org" value="' + AUDIT_SOURCE
                      + '"/></auditSources></configuration>\n')


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _file_mtime_utc(path: Path | None) -> str | None:
    if path is None or not path.is_file():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()


def _bytes_sha256(payload: bytes | None) -> str | None:
    if payload is None:
        return None
    return hashlib.sha256(payload).hexdigest()


def _meta_summary(payload: bytes | None) -> str:
    if payload is None:
        return 'missing'
    return hashlib.sha256(payload).hexdigest() + '/' + str(len(payload))


def parse_iso8601_utc(value: object) -> tuple[int, int]:
    """Parse an ISO-8601 timezone-aware timestamp into comparable (epoch_seconds, nanoseconds)."""
    if not isinstance(value, str):
        raise ValueError('Advisory @updated timestamp must be a string.')
    match = _ISO8601_RE.fullmatch(value)
    if match is None:
        raise ValueError('Advisory @updated timestamp is not valid ISO-8601 UTC/offset format: ' + value)
    fraction = match.group(7) or ''
    if len(fraction) > 9:
        raise ValueError('Advisory @updated timestamp has unsupported fractional precision: ' + value)
    nanos = int(fraction.ljust(9, '0')) if fraction else 0
    base = value[:19] + ('+00:00' if match.group(8) == 'Z' else match.group(8))
    dt = datetime.fromisoformat(base).astimezone(timezone.utc)
    epoch = int(dt.timestamp())
    return epoch, nanos


def _is_official_page_url(url: object) -> bool:
    if not isinstance(url, str) or not url.startswith(PAGE_PREFIX):
        return False
    if any(ch.isspace() or ord(ch) < 32 for ch in url):
        return False
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or parsed.netloc != 'data.nuget.org':
        return False
    if not parsed.path.startswith('/v3-vulnerabilities/') or parsed.query or parsed.fragment:
        return False
    segments = parsed.path.split('/')
    if any(part in ('..', '.') for part in segments) or not segments[-1]:
        return False
    return True


def validate_advisory_index(raw_bytes: bytes, *, source_label: str = 'advisory') -> list[dict]:
    """Validate an official NuGet v3 vulnerability index document."""
    try:
        pages = json.loads(raw_bytes.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f'The native audit {source_label} index is not valid UTF-8 JSON.') from error
    if not isinstance(pages, list) or not pages or len(pages) > 16:
        raise ValueError('The native audit advisory index is incomplete.')
    if any(not isinstance(page, dict) for page in pages):
        raise ValueError('The native audit advisory index has invalid or ambiguous pages.')
    names = [page.get('@name', '') for page in pages]
    if len(set(names)) != len(names) or any(
            not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', name) or name == 'index'
            for name in names):
        raise ValueError('The native audit advisory index has invalid or ambiguous pages.')
    for page in pages:
        if not _is_official_page_url(page.get('@id')):
            raise ValueError('The native audit advisory page is not bound to its official source.')
        parse_iso8601_utc(page.get('@updated'))
    return pages


def parse_advisory_page(raw_bytes: bytes, *, name: str) -> dict[str, list]:
    """Parse and validate a NuGet v3 vulnerability page JSON object."""
    try:
        document = json.loads(raw_bytes.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f'The native audit advisory page is not valid UTF-8 JSON: {name}') from error
    if not isinstance(document, dict):
        raise ValueError(f'The native audit advisory page must be a JSON object: {name}')
    normalized: dict[str, list] = {}
    for package_id, advisories in document.items():
        if not isinstance(package_id, str) or not isinstance(advisories, list):
            raise ValueError(f'The native audit advisory page has malformed entries: {name}')
        key = package_id.lower()
        normalized.setdefault(key, []).extend(advisories)
    return normalized


def parse_http_headers(headers_path: Path | None) -> tuple[int | None, dict[str, str]]:
    """Extract the final HTTP response status code and sanitized headers from curl --dump-header."""
    if headers_path is None or not headers_path.is_file():
        return None, {}
    text = headers_path.read_text(errors='replace')
    lines = text.splitlines()
    last_status_index = None
    last_status = None
    for idx, line in enumerate(lines):
        match = re.match(r'^HTTP/\S+\s+(\d+)', line)
        if match:
            last_status_index = idx
            last_status = int(match.group(1))
    if last_status_index is None:
        return None, {}
    headers: dict[str, str] = {}
    for line in lines[last_status_index + 1:]:
        if not line.strip():
            break
        if ':' not in line:
            continue
        key, value = line.split(':', 1)
        lowered = key.strip().lower()
        if not lowered or lowered in _REDACTED_HEADERS:
            continue
        cleaned = value.strip()
        headers[lowered] = headers[lowered] + ', ' + cleaned if lowered in headers else cleaned
    return last_status, headers


def _normalize_restored_packages(restored_packages: dict | set[str] | list[str] | None) -> dict[str, list[str]]:
    """Map lowercase package ID -> sorted list of restored 'PackageId/Version' identities."""
    mapping: dict[str, set[str]] = {}
    if not restored_packages:
        return {}
    identities = restored_packages.keys() if isinstance(restored_packages, dict) else restored_packages
    for identity in identities:
        if not isinstance(identity, str) or not identity:
            continue
        package_id = identity.split('/', 1)[0].lower()
        mapping.setdefault(package_id, set()).add(identity)
    return {pkg: sorted(values) for pkg, values in sorted(mapping.items())}


def _canonical_advisory_key(entry: object) -> str:
    return json.dumps(entry, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def _merge_advisory_maps(page_maps: dict[str, dict[str, list]]) -> dict[str, dict[str, object]]:
    """Merge advisory maps across pages keyed by lowercase package ID -> {canonical_key: entry}."""
    merged: dict[str, dict[str, object]] = {}
    for page_map in page_maps.values():
        for package_id, entries in page_map.items():
            bucket = merged.setdefault(package_id, {})
            for entry in entries:
                bucket[_canonical_advisory_key(entry)] = entry
    return merged


def compute_semantic_diff(
    cached_index: list[dict] | None,
    online_index: list[dict] | None,
    cached_page_maps: dict[str, dict[str, list]],
    online_page_maps: dict[str, dict[str, list]],
    index_changes: dict,
    restored_packages: dict | set[str] | list[str] | None = None,
) -> dict:
    """Compute package/advisory-level semantic diff and intersection with restored packages."""
    restored_map = _normalize_restored_packages(restored_packages)
    cached_merged = _merge_advisory_maps(cached_page_maps)
    online_merged = _merge_advisory_maps(online_page_maps)

    cached_keys = set(cached_merged)
    online_keys = set(online_merged)
    added_packages = sorted(online_keys - cached_keys)
    removed_packages = sorted(cached_keys - online_keys)
    changed_packages: list[str] = []
    added_advisories_count = 0
    removed_advisories_count = 0
    per_package_deltas: dict[str, tuple[list, list]] = {}

    for pkg in added_packages:
        added_list = [online_merged[pkg][k] for k in sorted(online_merged[pkg])]
        added_advisories_count += len(added_list)
        per_package_deltas[pkg] = (added_list, [])

    for pkg in removed_packages:
        removed_list = [cached_merged[pkg][k] for k in sorted(cached_merged[pkg])]
        removed_advisories_count += len(removed_list)
        per_package_deltas[pkg] = ([], removed_list)

    for pkg in sorted(cached_keys & online_keys):
        c_entries = cached_merged[pkg]
        o_entries = online_merged[pkg]
        added_keys = sorted(set(o_entries) - set(c_entries))
        removed_keys = sorted(set(c_entries) - set(o_entries))
        if added_keys or removed_keys:
            changed_packages.append(pkg)
            added_list = [o_entries[k] for k in added_keys]
            removed_list = [c_entries[k] for k in removed_keys]
            added_advisories_count += len(added_list)
            removed_advisories_count += len(removed_list)
            per_package_deltas[pkg] = (added_list, removed_list)

    affected_package_ids = sorted(per_package_deltas)
    intersection = []
    for pkg in affected_package_ids:
        if pkg in restored_map:
            added_list, removed_list = per_package_deltas[pkg]
            intersection.append({
                'packageId': pkg,
                'restoredIdentities': restored_map[pkg],
                'addedAdvisories': added_list,
                'removedAdvisories': removed_list,
            })

    return {
        'indexChanges': index_changes,
        'addedPackages': added_packages,
        'removedPackages': removed_packages,
        'changedPackages': changed_packages,
        'affectedPackageIds': affected_package_ids,
        'addedAdvisoriesCount': added_advisories_count,
        'removedAdvisoriesCount': removed_advisories_count,
        'restoredPackageCount': sum(len(v) for v in restored_map.values()),
        'restoredPackageIntersection': intersection,
    }


def write_diagnostic(diagnostic: dict, *paths: Path | None) -> None:
    """Persist a diagnostic record to one or more task-owned paths."""
    serialized = json.dumps(diagnostic, indent=2) + '\n'
    written: set[Path] = set()
    for path in paths:
        if path is None:
            continue
        resolved = path.resolve()
        if resolved in written:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(serialized)
        written.add(resolved)


def package_graph(assets_path: Path) -> dict:
    """Bind every direct/transitive restored package to its content and archive hashes."""
    assets = json.loads(assets_path.read_text())
    graph = {}
    for identity, item in assets['libraries'].items():
        if item.get('type') != 'package':
            continue
        content = item.get('sha512', '')
        if not re.fullmatch(r'[A-Za-z0-9+/]{86}==', content):
            raise ValueError('The audited graph requires every package content hash: ' + identity)
        filename = identity.lower().replace('/', '.') + '.nupkg'
        archives = [Path(folder) / identity.lower() / filename for folder in assets['packageFolders']]
        archives = [path for path in archives if path.is_file() and not path.is_symlink()]
        if len(archives) != 1:
            raise ValueError('The audited graph requires one unambiguous package archive: ' + identity)
        graph[identity] = {'contentSha512': content,
                           'archiveSha512': base64.b64encode(hashlib.sha512(archives[0].read_bytes()).digest()).decode()}
    if not graph:
        raise ValueError('The audited package graph is empty.')
    return graph


def restored_package_identities(assets_path: Path) -> set[str]:
    """Extract restored package identities ('PackageId/Version') from project.assets.json."""
    if not assets_path.is_file():
        return set()
    try:
        assets = json.loads(assets_path.read_text())
    except (OSError, json.JSONDecodeError):
        return set()
    return {identity for identity, item in assets.get('libraries', {}).items()
            if isinstance(item, dict) and item.get('type') == 'package'}


def require_policy(assets_path: Path, *, diagnostic_path: Path | None = None,
                   restored_packages: dict | set[str] | list[str] | None = None,
                   recovery_attempt: int = 0) -> dict:
    assets = json.loads(assets_path.read_text())
    restore = assets['project']['restore']
    audit, warnings = restore.get('restoreAuditProperties', {}), restore.get('warningProperties', {})
    suppressed = [*warnings.get('noWarn', []), *warnings.get('warnNotAsError', []),
                  *(code for framework in assets['project'].get('frameworks', {}).values()
                    for package in framework.get('dependencies', {}).values() for code in package.get('noWarn', []))]
    logs = [item for item in assets.get('logs', []) if item.get('level', '').lower() in ('warning', 'error')]
    policy_violation = (
        any(audit.get(name) != value for name, value in
            {'enableAudit': 'true', 'auditLevel': 'low', 'auditMode': 'all'}.items())
        or bool(audit.get('suppressedAdvisories'))
        or warnings.get('allWarningsAsErrors') is not True
        or any(re.fullmatch(r'NU19\d{2}', code, re.IGNORECASE) for code in suppressed)
    )
    if policy_violation or logs:
        log_codes = sorted({str(item.get('code', '')).upper() for item in logs if item.get('code')})
        advisory_codes = [code for code in log_codes if code in _ADVISORY_ERROR_CODES]
        is_feed_outage = 'NU1900' in log_codes and not advisory_codes and not policy_violation
        classification = (
            CLASSIFICATION_ADVISORY_AFFECTING_GRAPH if advisory_codes
            else CLASSIFICATION_UNAVAILABLE if is_feed_outage
            else CLASSIFICATION_ADVISORY_AFFECTING_GRAPH
        )
        effective_packages = restored_packages if restored_packages is not None else restored_package_identities(assets_path)
        restored_map = _normalize_restored_packages(effective_packages)
        intersecting = []
        for item in logs:
            lib = str(item.get('libraryId', '')).lower()
            message = str(item.get('message', ''))
            matched_pkg = None
            if lib and lib in restored_map:
                matched_pkg = lib
            else:
                for pkg in restored_map:
                    if re.search(r"(?:^|['\"\s])" + re.escape(pkg) + r"(?:['\"\s/]|$)", message, re.IGNORECASE):
                        matched_pkg = pkg
                        break
            if matched_pkg is not None:
                intersecting.append({
                    'packageId': matched_pkg,
                    'restoredIdentities': restored_map[matched_pkg],
                    'code': str(item.get('code', '')).upper(),
                    'message': message,
                })
        diagnostic = {
            'schemaVersion': 1,
            'classification': classification,
            'source': 'assets_policy',
            'reason': 'policy_or_advisory_violation',
            'recoveryAttempt': recovery_attempt,
            'cacheRetrievedAtUtc': _file_mtime_utc(assets_path),
            'onlineRetrievedAtUtc': _utc_now_iso(),
            'pages': {},
            'semanticDiff': {
                'indexChanges': {'addedPages': [], 'removedPages': [], 'advancedPages': [],
                                 'regressedPages': [], 'unchangedMetadataDriftedPages': []},
                'addedPackages': [], 'removedPackages': [], 'changedPackages': [],
                'affectedPackageIds': sorted({entry['packageId'] for entry in intersecting}),
                'addedAdvisoriesCount': 0, 'removedAdvisoriesCount': 0,
                'restoredPackageCount': sum(len(v) for v in restored_map.values()),
                'restoredPackageIntersection': intersecting,
            },
            'advisoryCodes': log_codes,
            'logs': [{'code': item.get('code'), 'level': item.get('level'), 'libraryId': item.get('libraryId'),
                      'message': item.get('message')} for item in logs],
            'policyViolation': policy_violation,
            'offendingPages': [],
            'priorRotationDiagnostic': None,
        }
        write_diagnostic(diagnostic, diagnostic_path)
        detail = ''
        if advisory_codes:
            detail = f' ({CLASSIFICATION_ADVISORY_AFFECTING_GRAPH}: {", ".join(advisory_codes)})'
        elif is_feed_outage:
            detail = f' ({CLASSIFICATION_UNAVAILABLE}: NU1900)'
        elif log_codes:
            detail = f' ({classification}: {", ".join(log_codes)})'
        raise AdvisoryVerificationError(
            'The private native audit requires unsuppressed low-and-higher all-dependency audits with every warning fatal.' + detail,
            classification,
            diagnostic,
        )
    return {'audit': audit, 'warnings': warnings}


def classify_restore_failure(
    error: RuntimeError,
    evidence_stem: Path,
    *,
    diagnostic_path: Path | None = None,
    restored_packages: dict | set[str] | list[str] | None = None,
    recovery_attempt: int = 0,
) -> RuntimeError:
    """Inspect restore command logs for NU1900-NU1904, write diagnostic, and return an enriched error."""
    stdout_path = evidence_stem.parent / (evidence_stem.name + '.stdout.txt')
    stderr_path = evidence_stem.parent / (evidence_stem.name + '.stderr.txt')
    combined = ''
    for channel in (stdout_path, stderr_path):
        if channel.is_file():
            combined += channel.read_text(errors='replace') + '\n'
    codes = sorted({code.upper() for code in _NU19_CODE_RE.findall(combined)})
    if not codes:
        return error
    advisory_codes = [code for code in codes if code in _ADVISORY_ERROR_CODES]
    classification = (
        CLASSIFICATION_ADVISORY_AFFECTING_GRAPH if advisory_codes else CLASSIFICATION_UNAVAILABLE
    )
    restored_map = _normalize_restored_packages(restored_packages)
    matched_lines = [line.strip() for line in combined.splitlines() if _NU19_CODE_RE.search(line)]
    intersecting = []
    seen_pkgs: set[str] = set()
    for line in matched_lines:
        for match in re.finditer(r"Package\s+['\"]([^'\"]+)['\"]", line, re.IGNORECASE):
            pkg = match.group(1).lower()
            if pkg not in seen_pkgs:
                seen_pkgs.add(pkg)
                intersecting.append({
                    'packageId': pkg,
                    'restoredIdentities': restored_map.get(pkg, []),
                    'line': line,
                })
        for pkg in restored_map:
            if pkg not in seen_pkgs and re.search(r"(?:^|['\"\s])" + re.escape(pkg) + r"(?:['\"\s/]|$)", line, re.IGNORECASE):
                seen_pkgs.add(pkg)
                intersecting.append({
                    'packageId': pkg,
                    'restoredIdentities': restored_map[pkg],
                    'line': line,
                })
    diagnostic = {
        'schemaVersion': 1,
        'classification': classification,
        'source': 'restore',
        'reason': 'restore_failed_with_nu19xx',
        'recoveryAttempt': recovery_attempt,
        'cacheRetrievedAtUtc': None,
        'onlineRetrievedAtUtc': _utc_now_iso(),
        'pages': {},
        'semanticDiff': {
            'indexChanges': {'addedPages': [], 'removedPages': [], 'advancedPages': [],
                             'regressedPages': [], 'unchangedMetadataDriftedPages': []},
            'addedPackages': [], 'removedPackages': [], 'changedPackages': [],
            'affectedPackageIds': sorted(seen_pkgs),
            'addedAdvisoriesCount': 0, 'removedAdvisoriesCount': 0,
            'restoredPackageCount': sum(len(v) for v in restored_map.values()),
            'restoredPackageIntersection': intersecting,
        },
        'advisoryCodes': codes,
        'matchedLines': matched_lines[:20],
        'offendingPages': [],
        'priorRotationDiagnostic': None,
    }
    write_diagnostic(diagnostic, diagnostic_path)
    enriched = RuntimeError(
        f'The native audit restore failed ({classification}: {", ".join(codes)}): {error}'
    )
    enriched.classification = classification  # type: ignore[attr-defined]
    enriched.diagnostic = diagnostic  # type: ignore[attr-defined]
    return enriched


def require_coverage(expected: dict, actual: dict) -> None:
    """Every original transitive dependency must have the identical audited package bytes."""
    for identity, hashes in expected.items():
        if actual.get(identity) != hashes:
            raise ValueError('The native audit has incomplete or changed package-byte coverage: ' + identity)


def advisory_bytes_match(cached: bytes, online: bytes) -> bool:
    """Exact bytes, or equivalent JSON, prove the restore cache is the live advisory document."""
    if cached == online:
        return True
    try:
        return json.loads(cached) == json.loads(online)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return False


def refuse_advisory_mismatch(name: str, cached: bytes | None, online: bytes | None, status: str) -> None:
    raise ValueError('The native audit used stale, incomplete or cache-only advisory bytes: ' + name
                     + ' (cache=' + _meta_summary(cached) + ' online=' + _meta_summary(online) + ' status=' + status + ')')


def advisory_cache_index(cache: Path) -> Path:
    """Require the restore HTTP cache to contain exactly one NuGet advisory index."""
    indexes = list(cache.rglob('vuln_index.dat'))
    if len(indexes) != 1:
        raise ValueError('The native audit requires one complete freshly populated advisory cache.')
    return indexes[0]


def snapshot_matches_cache(cache: Path, snapshot: Path) -> bool:
    """True when the restore cache still equals an already-proven live advisory snapshot."""
    try:
        index = advisory_cache_index(cache)
    except ValueError:
        return False
    try:
        pages = json.loads(index.read_text())
    except (json.JSONDecodeError, OSError):
        return False
    files = {'index': index}
    if not isinstance(pages, list):
        return False
    for page in pages:
        name = page.get('@name') if isinstance(page, dict) else None
        if not isinstance(name, str):
            return False
        files[name] = index.with_name('vuln_data_' + name + '.dat')
    return all((snapshot / (name + '.json')).is_file() and path.is_file()
               and advisory_bytes_match(path.read_bytes(), (snapshot / (name + '.json')).read_bytes())
               for name, path in files.items())


def _evaluate_snapshot_comparison(
    older_index_bytes: bytes,
    older_pages: list[dict],
    older_page_bytes: dict[str, bytes | None],
    older_page_mtimes: dict[str, str | None],
    newer_index_bytes: bytes,
    newer_pages: list[dict],
    newer_page_bytes: dict[str, bytes | None],
    newer_page_times: dict[str, str | None],
    newer_page_statuses: dict[str, int | None],
    newer_page_headers: dict[str, dict[str, str]],
    *,
    older_index_mtime: str | None,
    newer_index_time: str | None,
    newer_index_status: int | None,
    newer_index_headers: dict[str, str],
    restored_packages: dict | set[str] | list[str] | None = None,
) -> tuple[str, dict, list[str]]:
    """Compare two validated official advisory snapshots and classify match / confirmed_rotation / persistent_mismatch."""
    older_by_name = {entry['@name']: entry for entry in older_pages}
    newer_by_name = {entry['@name']: entry for entry in newer_pages}
    all_names = sorted(set(older_by_name) | set(newer_by_name))

    index_match = advisory_bytes_match(older_index_bytes, newer_index_bytes)
    pages_diag: dict[str, dict] = {
        'index': {
            'name': 'index',
            'url': INDEX,
            'cachedSha256': _bytes_sha256(older_index_bytes),
            'cachedBytes': len(older_index_bytes),
            'cachedRetrievedAtUtc': older_index_mtime,
            'onlineSha256': _bytes_sha256(newer_index_bytes),
            'onlineBytes': len(newer_index_bytes),
            'onlineRetrievedAtUtc': newer_index_time,
            'httpStatus': newer_index_status,
            'headers': newer_index_headers,
            'bytesMatch': index_match,
        }
    }

    added_pages: list[str] = []
    removed_pages: list[str] = []
    advanced_pages: list[str] = []
    regressed_pages: list[str] = []
    unchanged_drifted_pages: list[str] = []
    missing_or_invalid_cached: list[str] = []

    cached_maps: dict[str, dict[str, list]] = {}
    online_maps: dict[str, dict[str, list]] = {}
    all_pages_match = True

    for name in all_names:
        c_meta = older_by_name.get(name)
        o_meta = newer_by_name.get(name)
        c_bytes = older_page_bytes.get(name)
        o_bytes = newer_page_bytes.get(name)

        if c_bytes is not None:
            try:
                cached_maps[name] = parse_advisory_page(c_bytes, name=name)
            except ValueError:
                missing_or_invalid_cached.append(name)
        elif c_meta is not None:
            missing_or_invalid_cached.append(name)

        if o_bytes is not None:
            online_maps[name] = parse_advisory_page(o_bytes, name=name)

        b_match = (c_bytes is not None and o_bytes is not None and advisory_bytes_match(c_bytes, o_bytes))
        if not b_match:
            all_pages_match = False

        if c_meta is None and o_meta is not None:
            direction = 'added'
            added_pages.append(name)
        elif c_meta is not None and o_meta is None:
            direction = 'removed'
            removed_pages.append(name)
        else:
            assert c_meta is not None and o_meta is not None
            c_ts = parse_iso8601_utc(c_meta['@updated'])
            o_ts = parse_iso8601_utc(o_meta['@updated'])
            if o_ts > c_ts:
                direction = 'advanced'
                advanced_pages.append(name)
            elif o_ts < c_ts:
                direction = 'regressed'
                regressed_pages.append(name)
            else:
                direction = 'unchanged'
                if c_meta['@id'] == o_meta['@id'] and not b_match:
                    unchanged_drifted_pages.append(name)

        pages_diag[name] = {
            '@name': name,
            'url': o_meta['@id'] if o_meta is not None else c_meta['@id'],
            'cachedId': c_meta['@id'] if c_meta is not None else None,
            'cachedUpdated': c_meta['@updated'] if c_meta is not None else None,
            'cachedSha256': _bytes_sha256(c_bytes),
            'cachedBytes': len(c_bytes) if c_bytes is not None else None,
            'cachedRetrievedAtUtc': older_page_mtimes.get(name),
            'onlineId': o_meta['@id'] if o_meta is not None else None,
            'onlineUpdated': o_meta['@updated'] if o_meta is not None else None,
            'onlineSha256': _bytes_sha256(o_bytes),
            'onlineBytes': len(o_bytes) if o_bytes is not None else None,
            'onlineRetrievedAtUtc': newer_page_times.get(name),
            'httpStatus': newer_page_statuses.get(name),
            'headers': newer_page_headers.get(name, {}),
            'updatedDirection': direction,
            'bytesMatch': b_match,
        }

    index_changes = {
        'addedPages': added_pages,
        'removedPages': removed_pages,
        'advancedPages': advanced_pages,
        'regressedPages': regressed_pages,
        'unchangedMetadataDriftedPages': unchanged_drifted_pages,
    }
    semantic_diff = compute_semantic_diff(
        older_pages, newer_pages, cached_maps, online_maps, index_changes, restored_packages=restored_packages
    )

    offending: list[str] = []
    if index_match and all_pages_match and not added_pages and not removed_pages and not missing_or_invalid_cached:
        classification = CLASSIFICATION_MATCH
    elif (not regressed_pages
          and not unchanged_drifted_pages
          and not missing_or_invalid_cached
          and not removed_pages
          and len(advanced_pages) >= 1):
        classification = CLASSIFICATION_CONFIRMED_ROTATION
        offending = list(advanced_pages)
    else:
        classification = CLASSIFICATION_PERSISTENT_MISMATCH
        offending = sorted(set(
            regressed_pages + unchanged_drifted_pages + missing_or_invalid_cached + removed_pages
        ))
        if not offending:
            offending = ['index']

    details = {'pages': pages_diag, 'semanticDiff': semantic_diff, 'indexChanges': index_changes}
    return classification, details, offending


def _load_cached_advisory_state(cache: Path) -> tuple[Path, bytes, list[dict], dict[str, bytes | None], dict[str, str | None]]:
    index_path = advisory_cache_index(cache)
    index_bytes = index_path.read_bytes()
    pages = validate_advisory_index(index_bytes, source_label='cached advisory')
    page_bytes: dict[str, bytes | None] = {}
    page_mtimes: dict[str, str | None] = {}
    for entry in pages:
        name = entry['@name']
        path = index_path.with_name('vuln_data_' + name + '.dat')
        page_bytes[name] = path.read_bytes() if path.is_file() else None
        page_mtimes[name] = _file_mtime_utc(path)
    return index_path, index_bytes, pages, page_bytes, page_mtimes


def _fetch_live_document(url: str, name: str, output: Path, bounded) -> tuple[bytes | None, int | None, dict[str, str], str, RuntimeError | None]:
    destination = output / (name + '.json')
    headers_path = output / (name + '.headers')
    curl_error: RuntimeError | None = None
    try:
        bounded(
            ['curl', '--fail', '--silent', '--show-error', '--location', '--compressed',
             '--connect-timeout', '15', '--max-time', '120',
             '--header', 'Cache-Control: no-cache', '--dump-header', str(headers_path),
             url, '-o', str(destination)],
            130,
            output / (name + '-fetch'),
        )
    except RuntimeError as error:
        curl_error = error
    retrieved_at = _utc_now_iso()
    http_status, parsed_headers = parse_http_headers(headers_path)
    payload = destination.read_bytes() if destination.is_file() else None
    return payload, http_status, parsed_headers, retrieved_at, curl_error


def _build_unavailable_diagnostic(
    reason: str,
    *,
    source: str,
    recovery_attempt: int,
    cache_retrieved_at: str | None,
    online_retrieved_at: str,
    pages_diag: dict,
    restored_packages: dict | set[str] | list[str] | None,
    offending_pages: list[str],
    error_detail: str | None = None,
) -> dict:
    restored_map = _normalize_restored_packages(restored_packages)
    return {
        'schemaVersion': 1,
        'classification': CLASSIFICATION_UNAVAILABLE,
        'source': source,
        'reason': reason,
        'errorDetail': error_detail,
        'recoveryAttempt': recovery_attempt,
        'cacheRetrievedAtUtc': cache_retrieved_at,
        'onlineRetrievedAtUtc': online_retrieved_at,
        'pages': pages_diag,
        'semanticDiff': {
            'indexChanges': {'addedPages': [], 'removedPages': [], 'advancedPages': [],
                             'regressedPages': [], 'unchangedMetadataDriftedPages': []},
            'addedPackages': [], 'removedPackages': [], 'changedPackages': [],
            'affectedPackageIds': [], 'addedAdvisoriesCount': 0, 'removedAdvisoriesCount': 0,
            'restoredPackageCount': sum(len(v) for v in restored_map.values()),
            'restoredPackageIntersection': [],
        },
        'advisoryCodes': [],
        'offendingPages': offending_pages,
        'priorRotationDiagnostic': None,
    }


def online_advisories(
    cache: Path,
    output: Path,
    bounded,
    proven: Path | None = None,
    *,
    restored_packages: dict | set[str] | list[str] | None = None,
    diagnostic_path: Path | None = None,
    recovery_attempt: int = 0,
) -> dict:
    """Reject cache-only/stale local data by comparing every page to a live or already-proven snapshot."""
    now_iso = _utc_now_iso()
    try:
        index_path, cached_index_bytes, cached_pages, cached_page_bytes, cached_page_mtimes = _load_cached_advisory_state(cache)
    except ValueError as error:
        diag = _build_unavailable_diagnostic(
            'invalid_cached_advisory_index',
            source='cache',
            recovery_attempt=recovery_attempt,
            cache_retrieved_at=None,
            online_retrieved_at=now_iso,
            pages_diag={},
            restored_packages=restored_packages,
            offending_pages=['index'],
            error_detail=str(error),
        )
        write_diagnostic(diag, diagnostic_path)
        raise AdvisoryVerificationError(f'{error} ({CLASSIFICATION_UNAVAILABLE})', CLASSIFICATION_UNAVAILABLE, diag) from error

    cache_retrieved_at = _file_mtime_utc(index_path)
    proven_drift_note: str | None = None

    if proven is not None:
        proven_index_path = proven / 'index.json'
        if not proven_index_path.is_file():
            diag = _build_unavailable_diagnostic(
                'missing_proven_index',
                source='proven',
                recovery_attempt=recovery_attempt,
                cache_retrieved_at=cache_retrieved_at,
                online_retrieved_at=now_iso,
                pages_diag={},
                restored_packages=restored_packages,
                offending_pages=['index'],
                error_detail='The native audit is missing the already-proven advisory page: index',
            )
            write_diagnostic(diag, diagnostic_path)
            raise AdvisoryVerificationError(
                f'The native audit is missing the already-proven advisory page: index ({CLASSIFICATION_UNAVAILABLE})',
                CLASSIFICATION_UNAVAILABLE,
                diag,
            )
        proven_index_bytes = proven_index_path.read_bytes()
        try:
            proven_pages = validate_advisory_index(proven_index_bytes, source_label='proven advisory')
        except ValueError as error:
            diag = _build_unavailable_diagnostic(
                'invalid_proven_index',
                source='proven',
                recovery_attempt=recovery_attempt,
                cache_retrieved_at=cache_retrieved_at,
                online_retrieved_at=now_iso,
                pages_diag={},
                restored_packages=restored_packages,
                offending_pages=['index'],
                error_detail=str(error),
            )
            write_diagnostic(diag, diagnostic_path)
            raise AdvisoryVerificationError(f'{error} ({CLASSIFICATION_UNAVAILABLE})', CLASSIFICATION_UNAVAILABLE, diag) from error

        proven_page_bytes: dict[str, bytes | None] = {}
        proven_page_mtimes: dict[str, str | None] = {}
        proven_page_headers: dict[str, dict[str, str]] = {}
        proven_index_status, proven_index_headers = parse_http_headers(proven / 'index.headers')
        if proven_index_status is None:
            proven_index_status = 200
        for entry in proven_pages:
            name = entry['@name']
            p_file = proven / (name + '.json')
            if not p_file.is_file():
                diag = _build_unavailable_diagnostic(
                    'missing_proven_page',
                    source='proven',
                    recovery_attempt=recovery_attempt,
                    cache_retrieved_at=cache_retrieved_at,
                    online_retrieved_at=now_iso,
                    pages_diag={},
                    restored_packages=restored_packages,
                    offending_pages=[name],
                    error_detail='The native audit is missing the already-proven advisory page: ' + name,
                )
                write_diagnostic(diag, diagnostic_path)
                raise AdvisoryVerificationError(
                    f'The native audit is missing the already-proven advisory page: {name} ({CLASSIFICATION_UNAVAILABLE})',
                    CLASSIFICATION_UNAVAILABLE,
                    diag,
                )
            proven_page_bytes[name] = p_file.read_bytes()
            proven_page_mtimes[name] = _file_mtime_utc(p_file)
            _, proven_page_headers[name] = parse_http_headers(proven / (name + '.headers'))

        # Compare proven (older) -> cached (newer) to distinguish exact match, forward rotation, or drift.
        proven_cls, proven_details, proven_offending = _evaluate_snapshot_comparison(
            proven_index_bytes, proven_pages, proven_page_bytes, proven_page_mtimes,
            cached_index_bytes, cached_pages, cached_page_bytes, cached_page_mtimes,
            {entry['@name']: 200 for entry in cached_pages},
            {entry['@name']: proven_page_headers.get(entry['@name'], {}) for entry in cached_pages},
            older_index_mtime=_file_mtime_utc(proven_index_path),
            newer_index_time=cache_retrieved_at,
            newer_index_status=proven_index_status,
            newer_index_headers=proven_index_headers,
            restored_packages=restored_packages,
        )
        if proven_cls == CLASSIFICATION_MATCH:
            output.mkdir()
            (output / 'index.json').write_bytes(proven_index_bytes)
            (output / 'index.headers').write_text(
                (proven / 'index.headers').read_text(errors='replace')
                if (proven / 'index.headers').is_file() else 'HTTP/2 200\n'
            )
            pages_receipt: dict[str, dict] = {
                'index': {
                    'url': INDEX,
                    'sha256': hashlib.sha256(proven_index_bytes).hexdigest(),
                    'httpStatus': 200,
                    'headers': proven_index_headers,
                    'cachedRetrievedAtUtc': cache_retrieved_at,
                    'onlineRetrievedAtUtc': _file_mtime_utc(proven_index_path),
                }
            }
            for entry in proven_pages:
                name = entry['@name']
                data = proven_page_bytes[name]
                assert data is not None
                (output / (name + '.json')).write_bytes(data)
                src_headers = proven / (name + '.headers')
                (output / (name + '.headers')).write_text(
                    src_headers.read_text(errors='replace') if src_headers.is_file() else 'HTTP/2 200\n'
                )
                pages_receipt[name] = {
                    '@name': name,
                    '@id': entry['@id'],
                    '@updated': entry['@updated'],
                    'url': entry['@id'],
                    'sha256': hashlib.sha256(data).hexdigest(),
                    'httpStatus': 200,
                    'headers': proven_page_headers.get(name, {}),
                    'cachedRetrievedAtUtc': cached_page_mtimes.get(name),
                    'onlineRetrievedAtUtc': proven_page_mtimes.get(name),
                }
            diagnostic = {
                'schemaVersion': 1,
                'classification': CLASSIFICATION_MATCH,
                'source': 'proven',
                'reason': 'cache_matches_proven_snapshot',
                'recoveryAttempt': recovery_attempt,
                'cacheRetrievedAtUtc': cache_retrieved_at,
                'onlineRetrievedAtUtc': _file_mtime_utc(proven_index_path),
                'pages': proven_details['pages'],
                'semanticDiff': proven_details['semanticDiff'],
                'advisoryCodes': [],
                'offendingPages': [],
                'priorRotationDiagnostic': None,
            }
            write_diagnostic(diagnostic, output / 'diagnostic.json', diagnostic_path)
            receipt = {
                'retrievedAtUtc': now_iso,
                'cacheRetrievedAtUtc': cache_retrieved_at,
                'onlineRetrievedAtUtc': _file_mtime_utc(proven_index_path),
                'classification': CLASSIFICATION_MATCH,
                'recoveryAttempt': recovery_attempt,
                'directory': str(output),
                'pages': pages_receipt,
                'index': proven_pages,
                'semanticDiff': diagnostic['semanticDiff'],
            }
            if diagnostic_path is not None:
                receipt['diagnosticPath'] = str(diagnostic_path)
            return receipt

        if proven_cls == CLASSIFICATION_CONFIRMED_ROTATION:
            # Module restore saw a strictly newer official feed than the proven snapshot.
            # Fall through to verify the cache directly against the live feed!
            proven_drift_note = 'forward_rotation_over_proven_verified_against_live'
        else:
            # Unchanged-metadata content drift, regression, or missing page vs proven snapshot:
            # fail closed immediately without touching the network.
            diagnostic = {
                'schemaVersion': 1,
                'classification': CLASSIFICATION_PERSISTENT_MISMATCH,
                'source': 'proven',
                'reason': 'cache_drifted_from_proven_snapshot',
                'recoveryAttempt': recovery_attempt,
                'cacheRetrievedAtUtc': cache_retrieved_at,
                'onlineRetrievedAtUtc': _file_mtime_utc(proven_index_path),
                'pages': proven_details['pages'],
                'semanticDiff': proven_details['semanticDiff'],
                'advisoryCodes': [],
                'offendingPages': proven_offending,
                'priorRotationDiagnostic': None,
            }
            write_diagnostic(diagnostic, diagnostic_path)
            first_page = proven_offending[0] if proven_offending else 'index'
            c_raw = cached_index_bytes if first_page == 'index' else cached_page_bytes.get(first_page)
            p_raw = proven_index_bytes if first_page == 'index' else proven_page_bytes.get(first_page)
            raise AdvisoryVerificationError(
                f'The native audit detected {CLASSIFICATION_PERSISTENT_MISMATCH} against proven snapshot for page '
                f'{first_page} (cache={_meta_summary(c_raw)} online={_meta_summary(p_raw)} status=200)',
                CLASSIFICATION_PERSISTENT_MISMATCH,
                diagnostic,
            )

    # Live verification against data.nuget.org (single fetch per URL, zero cache-reusing retries).
    output.mkdir()
    live_index_bytes, live_index_status, live_index_headers, live_index_time, index_curl_err = _fetch_live_document(
        INDEX, 'index', output, bounded
    )
    index_diag_entry = {
        'name': 'index',
        'url': INDEX,
        'cachedSha256': _bytes_sha256(cached_index_bytes),
        'cachedBytes': len(cached_index_bytes),
        'cachedRetrievedAtUtc': cache_retrieved_at,
        'onlineSha256': _bytes_sha256(live_index_bytes),
        'onlineBytes': len(live_index_bytes) if live_index_bytes is not None else None,
        'onlineRetrievedAtUtc': live_index_time,
        'httpStatus': live_index_status,
        'headers': live_index_headers,
        'bytesMatch': False,
    }
    if index_curl_err is not None:
        diag = _build_unavailable_diagnostic(
            'live_index_curl_error',
            source='live',
            recovery_attempt=recovery_attempt,
            cache_retrieved_at=cache_retrieved_at,
            online_retrieved_at=live_index_time,
            pages_diag={'index': index_diag_entry},
            restored_packages=restored_packages,
            offending_pages=['index'],
            error_detail=str(index_curl_err),
        )
        write_diagnostic(diag, output / 'diagnostic.json', diagnostic_path)
        wrapped = RuntimeError(
            f'The native audit advisory feed is {CLASSIFICATION_UNAVAILABLE} while fetching index: {index_curl_err}'
        )
        wrapped.classification = CLASSIFICATION_UNAVAILABLE  # type: ignore[attr-defined]
        wrapped.diagnostic = diag  # type: ignore[attr-defined]
        raise wrapped from index_curl_err

    if live_index_status != 200 or live_index_bytes is None:
        diag = _build_unavailable_diagnostic(
            'live_index_non_200',
            source='live',
            recovery_attempt=recovery_attempt,
            cache_retrieved_at=cache_retrieved_at,
            online_retrieved_at=live_index_time,
            pages_diag={'index': index_diag_entry},
            restored_packages=restored_packages,
            offending_pages=['index'],
            error_detail=f'HTTP {live_index_status}',
        )
        write_diagnostic(diag, output / 'diagnostic.json', diagnostic_path)
        raise AdvisoryVerificationError(
            f'The native audit advisory index is {CLASSIFICATION_UNAVAILABLE}: HTTP {live_index_status} '
            f'(cache={_meta_summary(cached_index_bytes)} online={_meta_summary(live_index_bytes)} status={live_index_status})',
            CLASSIFICATION_UNAVAILABLE,
            diag,
        )

    try:
        live_pages = validate_advisory_index(live_index_bytes, source_label='live advisory')
    except ValueError as error:
        diag = _build_unavailable_diagnostic(
            'invalid_live_advisory_index',
            source='live',
            recovery_attempt=recovery_attempt,
            cache_retrieved_at=cache_retrieved_at,
            online_retrieved_at=live_index_time,
            pages_diag={'index': index_diag_entry},
            restored_packages=restored_packages,
            offending_pages=['index'],
            error_detail=str(error),
        )
        write_diagnostic(diag, output / 'diagnostic.json', diagnostic_path)
        raise AdvisoryVerificationError(
            f'The native audit live advisory index is {CLASSIFICATION_UNAVAILABLE}: {error}',
            CLASSIFICATION_UNAVAILABLE,
            diag,
        ) from error

    live_page_bytes: dict[str, bytes | None] = {}
    live_page_times: dict[str, str | None] = {}
    live_page_statuses: dict[str, int | None] = {}
    live_page_headers: dict[str, dict[str, str]] = {}
    partial_pages_diag: dict[str, dict] = {'index': index_diag_entry}

    for entry in live_pages:
        name = entry['@name']
        url = entry['@id']
        payload, status, headers, fetched_at, curl_err = _fetch_live_document(url, name, output, bounded)
        live_page_bytes[name] = payload
        live_page_times[name] = fetched_at
        live_page_statuses[name] = status
        live_page_headers[name] = headers
        # Re-read cached page at verification time in case cache state changed.
        cached_path = index_path.with_name('vuln_data_' + name + '.dat')
        if cached_path.is_file():
            cached_page_bytes[name] = cached_path.read_bytes()
            cached_page_mtimes[name] = _file_mtime_utc(cached_path)
        else:
            cached_page_bytes[name] = None
            cached_page_mtimes[name] = None
        partial_pages_diag[name] = {
            '@name': name,
            'url': url,
            'onlineId': url,
            'onlineUpdated': entry['@updated'],
            'cachedSha256': _bytes_sha256(cached_page_bytes.get(name)),
            'cachedBytes': len(cached_page_bytes[name]) if cached_page_bytes.get(name) is not None else None,
            'cachedRetrievedAtUtc': cached_page_mtimes.get(name),
            'onlineSha256': _bytes_sha256(payload),
            'onlineBytes': len(payload) if payload is not None else None,
            'onlineRetrievedAtUtc': fetched_at,
            'httpStatus': status,
            'headers': headers,
            'bytesMatch': False,
        }
        if curl_err is not None:
            diag = _build_unavailable_diagnostic(
                'live_page_curl_error',
                source='live',
                recovery_attempt=recovery_attempt,
                cache_retrieved_at=cache_retrieved_at,
                online_retrieved_at=fetched_at,
                pages_diag=partial_pages_diag,
                restored_packages=restored_packages,
                offending_pages=[name],
                error_detail=str(curl_err),
            )
            write_diagnostic(diag, output / 'diagnostic.json', diagnostic_path)
            wrapped = RuntimeError(
                f'The native audit advisory feed is {CLASSIFICATION_UNAVAILABLE} while fetching page {name}: {curl_err}'
            )
            wrapped.classification = CLASSIFICATION_UNAVAILABLE  # type: ignore[attr-defined]
            wrapped.diagnostic = diag  # type: ignore[attr-defined]
            raise wrapped from curl_err

        if status != 200 or payload is None:
            diag = _build_unavailable_diagnostic(
                'live_page_non_200',
                source='live',
                recovery_attempt=recovery_attempt,
                cache_retrieved_at=cache_retrieved_at,
                online_retrieved_at=fetched_at,
                pages_diag=partial_pages_diag,
                restored_packages=restored_packages,
                offending_pages=[name],
                error_detail=f'HTTP {status}',
            )
            write_diagnostic(diag, output / 'diagnostic.json', diagnostic_path)
            raise AdvisoryVerificationError(
                f'The native audit advisory page {name} is {CLASSIFICATION_UNAVAILABLE}: HTTP {status} '
                f'(cache={_meta_summary(cached_page_bytes.get(name))} online={_meta_summary(payload)} status={status})',
                CLASSIFICATION_UNAVAILABLE,
                diag,
            )

        try:
            parse_advisory_page(payload, name=name)
        except ValueError as error:
            diag = _build_unavailable_diagnostic(
                'invalid_live_advisory_page',
                source='live',
                recovery_attempt=recovery_attempt,
                cache_retrieved_at=cache_retrieved_at,
                online_retrieved_at=fetched_at,
                pages_diag=partial_pages_diag,
                restored_packages=restored_packages,
                offending_pages=[name],
                error_detail=str(error),
            )
            write_diagnostic(diag, output / 'diagnostic.json', diagnostic_path)
            raise AdvisoryVerificationError(
                f'The native audit live advisory page {name} is {CLASSIFICATION_UNAVAILABLE}: {error}',
                CLASSIFICATION_UNAVAILABLE,
                diag,
            ) from error

    # Re-check every cached page file from cached_pages as well (covers removed/deleted files).
    for entry in cached_pages:
        name = entry['@name']
        cached_path = index_path.with_name('vuln_data_' + name + '.dat')
        if cached_path.is_file():
            cached_page_bytes[name] = cached_path.read_bytes()
            cached_page_mtimes[name] = _file_mtime_utc(cached_path)
        else:
            cached_page_bytes[name] = None
            cached_page_mtimes[name] = None

    classification, details, offending = _evaluate_snapshot_comparison(
        cached_index_bytes, cached_pages, cached_page_bytes, cached_page_mtimes,
        live_index_bytes, live_pages, live_page_bytes, live_page_times,
        live_page_statuses, live_page_headers,
        older_index_mtime=cache_retrieved_at,
        newer_index_time=live_index_time,
        newer_index_status=live_index_status,
        newer_index_headers=live_index_headers,
        restored_packages=restored_packages,
    )

    diagnostic = {
        'schemaVersion': 1,
        'classification': classification,
        'source': 'live',
        'reason': (
            proven_drift_note if classification == CLASSIFICATION_MATCH and proven_drift_note
            else 'cache_matches_live_feed' if classification == CLASSIFICATION_MATCH
            else 'live_feed_rotated_forward' if classification == CLASSIFICATION_CONFIRMED_ROTATION
            else 'advisory_mismatch_or_regression'
        ),
        'recoveryAttempt': recovery_attempt,
        'cacheRetrievedAtUtc': cache_retrieved_at,
        'onlineRetrievedAtUtc': live_index_time,
        'pages': details['pages'],
        'semanticDiff': details['semanticDiff'],
        'advisoryCodes': [],
        'offendingPages': offending,
        'priorRotationDiagnostic': None,
    }
    if proven_drift_note is not None:
        diagnostic['provenSnapshotDrift'] = proven_drift_note
    write_diagnostic(diagnostic, output / 'diagnostic.json', diagnostic_path)

    if classification == CLASSIFICATION_MATCH:
        pages_receipt = {
            'index': {
                'url': INDEX,
                'sha256': hashlib.sha256(live_index_bytes).hexdigest(),
                'httpStatus': 200,
                'headers': live_index_headers,
                'cachedRetrievedAtUtc': cache_retrieved_at,
                'onlineRetrievedAtUtc': live_index_time,
            }
        }
        for entry in live_pages:
            name = entry['@name']
            data = live_page_bytes[name]
            assert data is not None
            pages_receipt[name] = {
                '@name': name,
                '@id': entry['@id'],
                '@updated': entry['@updated'],
                'url': entry['@id'],
                'sha256': hashlib.sha256(data).hexdigest(),
                'httpStatus': 200,
                'headers': live_page_headers[name],
                'cachedRetrievedAtUtc': cached_page_mtimes.get(name),
                'onlineRetrievedAtUtc': live_page_times[name],
            }
        receipt = {
            'retrievedAtUtc': live_index_time,
            'cacheRetrievedAtUtc': cache_retrieved_at,
            'onlineRetrievedAtUtc': live_index_time,
            'classification': CLASSIFICATION_MATCH,
            'recoveryAttempt': recovery_attempt,
            'directory': str(output),
            'pages': pages_receipt,
            'index': live_pages,
            'semanticDiff': diagnostic['semanticDiff'],
        }
        if diagnostic_path is not None:
            receipt['diagnosticPath'] = str(diagnostic_path)
        return receipt

    if classification == CLASSIFICATION_CONFIRMED_ROTATION:
        raise AdvisoryVerificationError(
            f'The native audit detected {CLASSIFICATION_CONFIRMED_ROTATION} on advisory page(s): '
            f'{", ".join(offending)}',
            CLASSIFICATION_CONFIRMED_ROTATION,
            diagnostic,
        )

    first_page = offending[0] if offending else 'index'
    c_raw = cached_index_bytes if first_page == 'index' else cached_page_bytes.get(first_page)
    o_raw = live_index_bytes if first_page == 'index' else live_page_bytes.get(first_page)
    raise AdvisoryVerificationError(
        f'The native audit detected {CLASSIFICATION_PERSISTENT_MISMATCH} for advisory page {first_page} '
        f'(cache={_meta_summary(c_raw)} online={_meta_summary(o_raw)} status=200)',
        CLASSIFICATION_PERSISTENT_MISMATCH,
        diagnostic,
    )


def output_snapshot(project: Path) -> dict:
    paths = [project.parent / 'obj/project.assets.json']
    paths.extend(path for path in (project.parent / 'bin/Release').rglob('*') if path.is_file())
    return {str(path.relative_to(project.parent)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def _create_audit_fixture(target_dir: Path, expected: dict, sdk_policy: dict) -> tuple[Path, Path]:
    target_dir.mkdir()
    (target_dir / 'global.json').write_text(json.dumps({'sdk': sdk_policy}) + '\n')
    xml = ET.Element('Project', {'Sdk': 'Microsoft.NET.Sdk'})
    properties = ET.SubElement(xml, 'PropertyGroup')
    for name, value in {'TargetFramework': 'net11.0', 'ManagePackageVersionsCentrally': 'false',
                        'ImportDirectoryBuildProps': 'false', 'ImportDirectoryBuildTargets': 'false',
                        'RestoreEnablePackagePruning': 'false', 'NuGetAudit': 'true', 'NuGetAuditLevel': 'low',
                        'NuGetAuditMode': 'all', 'TreatWarningsAsErrors': 'true',
                        'NoWarn': '', 'WarningsNotAsErrors': ''}.items():
        ET.SubElement(properties, name).text = value
    references = ET.SubElement(xml, 'ItemGroup')
    for identity in sorted(expected):
        name, version = identity.split('/')
        ET.SubElement(references, 'PackageReference', {'Include': name, 'Version': '[' + version + ']'})
    fixture = target_dir / 'audit.csproj'
    ET.ElementTree(xml).write(fixture, encoding='utf-8', xml_declaration=True)
    config = target_dir / 'NuGet.Config'
    write_restore_config(config)
    return fixture, config


def audit_project(
    project: Path,
    private: Path,
    evidence: Path,
    sdk_policy: dict,
    bounded,
    proven_advisories: Path | None = None,
    *,
    diagnostic_path: Path | None = None,
) -> dict:
    """Restore only a distinct package-only fixture under fresh package/HTTP caches, with <=1 fresh retry on confirmed rotation."""
    assets_path = project.parent / 'obj/project.assets.json'
    original_bytes = assets_path.read_bytes()
    original_outputs = output_snapshot(project)
    expected = package_graph(assets_path)
    source = json.loads(original_bytes)
    frameworks = source['project']['frameworks']
    if set(frameworks) != {'net11.0'}:
        raise ValueError('The current native package audit requires the exact net11.0 graph.')

    diag_target = diagnostic_path if diagnostic_path is not None else evidence.with_name(evidence.name + '-advisory-diagnostic.json')
    prior_rotation_diag: dict | None = None

    try:
        for attempt in range(2):
            attempt_private = private if attempt == 0 else private.with_name(private.name + '-retry-1')
            attempt_evidence = evidence if attempt == 0 else evidence.with_name(evidence.name + '-retry-1')
            attempt_proven = proven_advisories if attempt == 0 else None
            attempt_diag_path = diag_target
            fixture, config = _create_audit_fixture(attempt_private, expected, sdk_policy)
            environment = dict(
                os.environ,
                NUGET_PACKAGES=str(attempt_private / 'packages'),
                NUGET_HTTP_CACHE_PATH=str(attempt_private / 'http'),
            )
            for key in ('CustomAfterMicrosoftCommonTargets', 'CustomBeforeMicrosoftCommonTargets',
                        'CustomAfterDirectoryBuildTargets', 'DirectoryBuildPropsPath',
                        'DirectoryBuildTargetsPath', 'NuGetAuditSuppress', 'RestoreIgnoreFailedSources'):
                environment.pop(key, None)

            try:
                bounded(
                    ['dotnet', 'restore', str(fixture), '--configfile', str(config), '--force', '-warnaserror',
                     '-p:NuGetAudit=true', '-p:NuGetAuditMode=all', '-p:NuGetAuditLevel=low',
                     '-p:TreatWarningsAsErrors=true', '-p:WarningsNotAsErrors=', '-p:NoWarn='],
                    300, attempt_evidence, cwd=attempt_private, environment=environment, require_complete_stdout=False,
                )
            except RuntimeError as error:
                raise classify_restore_failure(
                    error, attempt_evidence, diagnostic_path=attempt_diag_path,
                    restored_packages=expected, recovery_attempt=attempt,
                ) from error

            audited_path = attempt_private / 'obj/project.assets.json'
            policy = require_policy(
                audited_path, diagnostic_path=attempt_diag_path,
                restored_packages=expected, recovery_attempt=attempt,
            )
            actual = package_graph(audited_path)
            require_coverage(expected, actual)

            try:
                online = online_advisories(
                    attempt_private / 'http', attempt_private / 'advisories', bounded,
                    proven=attempt_proven, restored_packages=actual,
                    diagnostic_path=attempt_diag_path, recovery_attempt=attempt,
                )
            except AdvisoryVerificationError as error:
                if error.classification == CLASSIFICATION_CONFIRMED_ROTATION and attempt == 0:
                    prior_rotation_diag = error.diagnostic
                    write_diagnostic(
                        prior_rotation_diag,
                        evidence.with_name(evidence.name + '-attempt-0-advisory-diagnostic.json'),
                    )
                    continue
                if error.classification == CLASSIFICATION_CONFIRMED_ROTATION and attempt == 1:
                    escalated = dict(
                        error.diagnostic,
                        classification=CLASSIFICATION_PERSISTENT_MISMATCH,
                        reason='second_mismatch_after_retry',
                        priorRotationDiagnostic=prior_rotation_diag,
                    )
                    write_diagnostic(escalated, attempt_private / 'advisories/diagnostic.json', attempt_diag_path)
                    pages = ', '.join(escalated.get('offendingPages', [])) or 'index'
                    raise AdvisoryVerificationError(
                        f'The native audit encountered {CLASSIFICATION_PERSISTENT_MISMATCH} after single fresh retry '
                        f'(second mismatch on {pages}).',
                        CLASSIFICATION_PERSISTENT_MISMATCH,
                        escalated,
                    ) from error
                if prior_rotation_diag is not None:
                    enriched_diag = dict(error.diagnostic, priorRotationDiagnostic=prior_rotation_diag)
                    write_diagnostic(enriched_diag, attempt_private / 'advisories/diagnostic.json', attempt_diag_path)
                    error.diagnostic = enriched_diag
                raise

            if prior_rotation_diag is not None:
                final_diag_file = attempt_private / 'advisories/diagnostic.json'
                final_diag = json.loads(final_diag_file.read_text())
                final_diag['priorRotationDiagnostic'] = prior_rotation_diag
                write_diagnostic(final_diag, final_diag_file, attempt_diag_path)
                online['priorRotationDiagnostic'] = {
                    'classification': prior_rotation_diag['classification'],
                    'offendingPages': prior_rotation_diag['offendingPages'],
                    'cacheRetrievedAtUtc': prior_rotation_diag['cacheRetrievedAtUtc'],
                    'onlineRetrievedAtUtc': prior_rotation_diag['onlineRetrievedAtUtc'],
                }

            return {
                'sourceAssetsSha256': hashlib.sha256(original_bytes).hexdigest(),
                'sourceOutputs': original_outputs,
                'packages': expected,
                'auditedPackages': actual,
                'policy': policy,
                'advisories': online,
                'privateDirectory': str(attempt_private),
                'fixtureSha256': hashlib.sha256(fixture.read_bytes()).hexdigest(),
                'auditAssetsSha256': hashlib.sha256(audited_path.read_bytes()).hexdigest(),
                'recoveryAttempt': attempt,
                'diagnosticPath': str(attempt_diag_path),
            }
        raise AssertionError('Unreachable retry state in audit_project.')
    finally:
        if output_snapshot(project) != original_outputs or package_graph(assets_path) != expected:
            raise ValueError('The separate native audit changed module outputs, restore graph or package bytes.')


def require_audit(receipt: dict, project: Path) -> None:
    """Recheck sealed online coverage and both original and isolated fixture bytes before reuse."""
    private = Path(receipt['privateDirectory'])
    assets = private / 'obj/project.assets.json'
    if output_snapshot(project) != receipt['sourceOutputs'] \
            or hashlib.sha256((project.parent / 'obj/project.assets.json').read_bytes()).hexdigest() != receipt['sourceAssetsSha256'] \
            or package_graph(project.parent / 'obj/project.assets.json') != receipt['packages'] \
            or hashlib.sha256((private / 'audit.csproj').read_bytes()).hexdigest() != receipt['fixtureSha256'] \
            or hashlib.sha256(assets.read_bytes()).hexdigest() != receipt['auditAssetsSha256'] \
            or require_policy(assets) != receipt['policy'] or package_graph(assets) != receipt['auditedPackages']:
        raise ValueError('The separate native online audit or module input bytes changed after preparation.')
    require_coverage(receipt['packages'], receipt['auditedPackages'])
    for name, page in receipt['advisories']['pages'].items():
        if hashlib.sha256((private / 'advisories' / (name + '.json')).read_bytes()).hexdigest() != page['sha256']:
            raise ValueError('The separate native advisory proof changed after preparation.')
