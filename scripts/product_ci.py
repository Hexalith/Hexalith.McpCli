#!/usr/bin/env python3
"""Product checks over the shared Release build and one source-bound CI package pair."""
from __future__ import annotations
import argparse
import configparser
import json
import os
import platform
import re
import signal
import shutil
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile

from product_process import run as run_owned
from evidence_redaction import require_evidence_credentials
from product_packages import (canonical_digest, check_prepared, digest, failure_detail, git, packages, read_json,
                              read_json_with_digest, source_changes, source_sha, validate_version, write_new)

ROOT = Path(__file__).resolve().parents[1]


def execute(command, *, timeout=900, cwd: Path = ROOT, environment=None):
    print('Product check:', *map(str, command), flush=True)
    output = staging_root() / 'diagnostics' / ('command-' + __import__('uuid').uuid4().hex)
    return run_owned(command, cwd=cwd, output=output, timeout=timeout, environment=environment)


def staging_root() -> Path:
    directory = os.environ.get('RUNNER_TEMP')
    if not directory:
        raise ValueError('Product CI requires its runner-owned temporary directory.')
    return Path(directory).resolve() / 'mcpcli-product'


def require_source(receipt: dict) -> None:
    if receipt['source_sha'] != source_sha(cwd=ROOT) or source_changes(cwd=ROOT):
        raise ValueError('Product checks require this exact clean checkout SHA; tracked or untracked source drift is refused.')


def stage_packages() -> None:
    source = source_sha(cwd=ROOT)
    require_source({'source_sha': source})
    directory = staging_root() / 'staged'
    directory.mkdir(parents=True, exist_ok=False)
    staging = directory / 'packages'
    staging.mkdir()
    result = execute(['dotnet', 'msbuild', 'src/Hexalith.McpCli/Hexalith.McpCli.csproj',
                             '-nologo', '-p:Configuration=Release', '-p:UseHexalithProjectReferences=false', '-getProperty:Version'],
                            timeout=60)
    version = result.stdout.strip()
    validate_version(version)
    built = execute(['dotnet', 'src/Hexalith.McpCli/bin/Release/net11.0/Hexalith.McpCli.dll', '--version'],
                           timeout=30)
    tool_version = built.stdout.strip()
    if built.stderr or tool_version not in (version, version + '+' + source):
        raise ValueError('The existing built tool version does not match this source/package version.')
    manifest = json.loads((ROOT / 'tools/release-packages.json').read_text())['packages']
    if [item['id'] for item in manifest] != ['Hexalith.McpCli.Abstractions', 'Hexalith.McpCli']:
        raise ValueError('Product CI requires exactly the approved Abstractions/tool pair.')
    for item in manifest:
        execute(['dotnet', 'pack', item['project'], '--configuration', 'Release', '--no-build', '--no-restore',
                 '-p:UseHexalithProjectReferences=false', '-p:PackageVersion=' + version,
                 '-p:RepositoryCommit=' + source, '--output', staging], timeout=300)
    execute([sys.executable, ROOT / 'scripts/validate-release-packages.py', staging, version, 'paired', '--source-sha', source])
    require_source({'source_sha': source})
    write_new(directory / 'prepared.json', {'schema': 'mcpcli-product-packages/v1', 'source_sha': source,
               'version': version, 'tool_version': tool_version, 'packages': packages(staging, version)})
    print('Staged CI fixture packages; real release publication remains the central release responsibility.', flush=True)


def discovery_bytes(directory: Path) -> dict[str, bytes]:
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError('Product discovery captures require a regular directory.')
    entries = sorted(directory.iterdir())
    if not entries or any(path.is_symlink() or not path.is_file() for path in entries):
        raise ValueError('Product discovery captures require a complete flat regular file set.')
    return {path.name: path.read_bytes() for path in entries}


def bind_linux_discovery(receipt_path: Path, captures: Path) -> None:
    receipt = check_prepared(receipt_path.parent / 'packages', receipt_path)
    require_source(receipt)
    source = discovery_bytes(captures)
    destination = receipt_path.parent / 'discovery'
    destination.mkdir()
    for name, data in source.items(): (destination / name).write_bytes(data)
    write_new(receipt_path.parent / 'linux-discovery.json', {'schema': 'mcpcli-product-discovery/v1',
        'source_sha': receipt['source_sha'], 'version': receipt['version'], 'packages': receipt['packages'],
        'preparation_sha256': digest(receipt_path), 'captures': {name: digest(destination / name) for name in source}})


def compare_linux_discovery(receipt_path: Path, captures: Path) -> None:
    receipt = check_prepared(receipt_path.parent / 'packages', receipt_path)
    require_source(receipt)
    reference = receipt_path.parent / 'discovery'
    source = discovery_bytes(reference)
    manifest = read_json(receipt_path.parent / 'linux-discovery.json')
    expected = {'schema': 'mcpcli-product-discovery/v1', 'source_sha': receipt['source_sha'],
                'version': receipt['version'], 'packages': receipt['packages'], 'preparation_sha256': digest(receipt_path),
                'captures': {name: digest(reference / name) for name in source}}
    if manifest != expected:
        raise ValueError('The staged Linux discovery manifest, preparation binding or capture bytes changed.')
    if discovery_bytes(captures) != source:
        raise ValueError('Platform discovery filenames or raw capture bytes differ from Linux.')


def package_checks(*, platform_checks=False, expected_os=None) -> None:
    if platform_checks and (expected_os not in ('Windows', 'Darwin') or platform.system() != expected_os):
        raise ValueError('Platform product checks require the explicitly registered actual OS: ' + str(expected_os))
    directory = staging_root()
    staging, receipt_path = directory / 'staged/packages', directory / 'staged/prepared.json'
    receipt = check_prepared(staging, receipt_path)
    preparation_hash = digest(receipt_path)
    require_source(receipt)
    evidence = directory / ('platform' if platform_checks else 'linux')
    evidence.mkdir(parents=True, exist_ok=False)
    execute([sys.executable, ROOT / 'scripts/validate-release-packages.py', staging, receipt['version'], 'paired',
             '--source-sha', receipt['source_sha']])
    execute([sys.executable, ROOT / 'scripts/smoke-paired-tool.py', '--staging', staging, '--prepared', receipt_path, '--output', evidence / 'installed-tool'])
    if digest(receipt_path) != preparation_hash:
        raise ValueError('The immutable preparation receipt changed during installed-tool checks.')
    if platform_checks:
        compare_linux_discovery(receipt_path, evidence / 'installed-tool/discovery')
    else:
        bind_linux_discovery(receipt_path, evidence / 'installed-tool/discovery')
    execute([sys.executable, ROOT / 'scripts/smoke_bootstrap_consumer.py', receipt['version'], staging, evidence / 'consumer'])
    if platform_checks:
        execute([sys.executable, ROOT / 'scripts/run-paired-platform-tests.py', '--prepared', receipt_path, '--output', evidence / 'suites'], timeout=1800)
    check_prepared(staging, receipt_path)
    if digest(receipt_path) != preparation_hash:
        raise ValueError('The immutable preparation receipt changed during product checks.')
    require_source(receipt)


def linux_packages() -> None:
    stage_packages()
    package_checks()


def sealed_live_source(preparation_path: Path) -> tuple[dict, tuple[str, str, str]]:
    preparation, preparation_sha256 = read_json_with_digest(preparation_path)
    boundary_path = preparation_path.with_name('boundary-receipt.json')
    boundary, boundary_sha256 = read_json_with_digest(boundary_path)
    report, report_sha256 = read_json_with_digest(preparation_path.with_name('ci-live.json'))
    preparation_id = preparation.get('runId')
    boundary_id = boundary.get('boundaryRunId')
    payload = {key: value for key, value in boundary.items() if key != 'contentSha256'}
    if (preparation.get('result') != 'prepared'
            or not isinstance(preparation.get('source_sha'), str)
            or not isinstance(preparation_id, str) or re.fullmatch(r'[0-9a-f]{32}', preparation_id) is None
            or not isinstance(boundary_id, str) or re.fullmatch(r'[0-9a-f]{32}', boundary_id) is None
            or boundary.get('schema') != 'mcpcli-live-boundary/v1'
            or boundary.get('result') != 'passed'
            or boundary.get('fullLiveAccepted') is not False
            or boundary.get('contentSha256') != canonical_digest(payload)
            or boundary.get('preparationRunId') != preparation_id
            or boundary.get('preparationSha256') != preparation_sha256
            or report.get('phase') != 'boundary'
            or report.get('result') != 'boundary-passed'
            or report.get('fullLiveAccepted') is not False
            or report.get('preparationRunId') != preparation_id
            or report.get('runId') != boundary_id
            or report.get('boundaryReceipt') != {'path': str(boundary_path.resolve()), 'sha256': boundary_sha256}):
        raise ValueError('Split conformance requires the preparation receipt sealed by the passing live boundary.')
    return preparation, (preparation_sha256, boundary_sha256, report_sha256)


def linux_conformance(live_preparation: Path | None = None) -> None:
    if live_preparation is None:
        source = {'source_sha': source_sha(cwd=ROOT)}
    else:
        live_preparation = ROOT / live_preparation
        source, sealed_evidence = sealed_live_source(live_preparation)
    require_source(source)
    # Unit tests start without the variables that locate the runner's workflow command files.
    execute(['env', '-u', 'GITHUB_ENV', '-u', 'GITHUB_PATH', '-u', 'GITHUB_OUTPUT', '-u', 'GITHUB_STATE',
             '-u', 'GITHUB_STEP_SUMMARY', sys.executable, '-m', 'unittest', 'discover', '-v', '-s', 'scripts/tests',
             '-p', 'test_*.py'], timeout=900)
    execute(['bash', ROOT / 'tools/conformance-vectors/v1/run-sample-validation.sh', 'Release'])
    execute(['bash', ROOT / 'tools/conformance-vectors/v1/run-sample-loopback.sh'], timeout=1800)
    execute([sys.executable, ROOT / 'tools/conformance-vectors/v1/check_enrolled.py', '--output',
             staging_root() / 'enrolled'], timeout=1800)
    execute(['env', '-u', 'GITHUB_ENV', '-u', 'GITHUB_PATH', '-u', 'GITHUB_OUTPUT', '-u', 'GITHUB_STATE',
             '-u', 'GITHUB_STEP_SUMMARY', sys.executable, '-m', 'unittest', 'discover', '-v', '-s', 'tools/live-topology',
             '-p', 'test_*.py'], timeout=3600)
    execute([sys.executable, ROOT / 'tools/live-topology/run-vectors.py', '--output', staging_root() / 'preflight', '--preflight-only'])
    require_source(source)
    if live_preparation is not None and sealed_live_source(live_preparation)[1] != sealed_evidence:
        raise ValueError('The sealed live boundary evidence changed during split conformance.')


def direct_submodule_paths(cwd: Path = ROOT) -> dict[str, str]:
    """Return sorted direct submodule path -> committed 160000 gitlink SHA map from HEAD."""
    raw = git('show', 'HEAD:.gitmodules', cwd=cwd)
    parser = configparser.ConfigParser(interpolation=None, strict=True)
    try:
        parser.read_string(raw)
    except configparser.Error as error:
        raise ValueError('Committed .gitmodules is malformed.') from error
    seen: set[str] = set()
    for section in parser.sections():
        if re.fullmatch(r'submodule "[^"\r\n]+"', section) is None:
            raise ValueError('Committed .gitmodules contains an invalid section: ' + section)
        value = parser.get(section, 'path', fallback='').strip()
        url = parser.get(section, 'url', fallback='')
        if (not value or re.search(r'[\x00-\x1f\x7f\\]', value) is not None
                or PurePosixPath(value).is_absolute() or any(part in ('', '.', '..') for part in value.split('/'))):
            raise ValueError('Committed .gitmodules contains an unsafe submodule path: ' + value)
        if not url.strip() or re.search(r'[\x00-\x1f\x7f]', url) is not None:
            raise ValueError('Committed .gitmodules contains an invalid submodule url for: ' + value)
        if value in seen:
            raise ValueError('Committed .gitmodules declares a duplicate submodule path: ' + value)
        if any(value.startswith(other + '/') or other.startswith(value + '/') for other in seen):
            raise ValueError('Committed .gitmodules declares overlapping submodule paths: ' + value)
        seen.add(value)
    if not seen:
        raise ValueError('Committed .gitmodules declares no direct submodules.')
    tree_listing = git('-c', 'core.quotePath=false', 'ls-tree', '-r', '--full-tree', 'HEAD', cwd=cwd)
    gitlinks: dict[str, str] = {}
    for line in tree_listing.splitlines():
        if not line:
            continue
        head, _, path = line.partition('\t')
        parts = head.split()
        if len(parts) == 3 and parts[0] == '160000' and parts[1] == 'commit' and re.fullmatch(r'[0-9a-f]{40}', parts[2]):
            gitlinks[path] = parts[2]
    missing_gitlinks = sorted(seen - set(gitlinks))
    if missing_gitlinks:
        raise ValueError('Committed HEAD is missing 160000 gitlink entries for: ' + ', '.join(missing_gitlinks))
    undeclared_gitlinks = sorted(set(gitlinks) - seen)
    if undeclared_gitlinks:
        raise ValueError('Committed HEAD has undeclared 160000 gitlink entries: ' + ', '.join(undeclared_gitlinks))
    return {path: gitlinks[path] for path in sorted(seen)}


def submodule_initialized(path: str, expected_sha: str, *, cwd: Path = ROOT) -> bool:
    """Return True only when `path` is a symlink-free initialized checkout containing `expected_sha`."""
    current = cwd.resolve()
    for part in PurePosixPath(path).parts:
        current = current / part
        if current.is_symlink():
            return False
    if not current.is_dir() or not (current / '.git').exists():
        return False
    try:
        top = git('rev-parse', '--show-toplevel', cwd=current)
        if not top or Path(top).resolve() != current.resolve():
            return False
        git('cat-file', '-e', expected_sha + '^{commit}', cwd=current)
    except subprocess.CalledProcessError:
        return False
    return True


def initialize_direct_submodules(*, cwd: Path = ROOT) -> list[str]:
    """Initialize only missing committed direct roots with recursion explicitly disabled."""
    declared = direct_submodule_paths(cwd=cwd)
    missing = [path for path, sha in declared.items() if not submodule_initialized(path, sha, cwd=cwd)]
    if missing:
        environment = {**os.environ, 'GIT_TERMINAL_PROMPT': '0'}
        execute(
            ['git', '--literal-pathspecs', '-c', 'protocol.file.allow=never', '-c', 'submodule.recurse=false',
             'submodule', 'update', '--init', '--checkout', '--', *missing],
            timeout=480, cwd=cwd, environment=environment,
        )
    still_missing = [path for path, sha in declared.items() if not submodule_initialized(path, sha, cwd=cwd)]
    if still_missing:
        raise ValueError('Direct submodules remain uninitialized after non-recursive init: ' + ', '.join(still_missing))
    return missing


def linux_census() -> None:
    source = {'source_sha': source_sha(cwd=ROOT)}
    require_source(source)
    initialize_direct_submodules(cwd=ROOT)
    execute([sys.executable, ROOT / 'tools/proprietary-surfaces/v1/check.py', '--output',
             staging_root() / 'diagnostics' / 'census.json'], timeout=300)
    require_source(source)


def linux_checks() -> None:
    linux_packages()
    linux_census()
    linux_conformance()


def main() -> int:
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('stage', 'linux', 'linux-packages', 'linux-census', 'linux-conformance', 'platform'))
    parser.add_argument('--expected-os', choices=('Windows', 'Darwin'))
    parser.add_argument('--live-preparation', type=Path, help='Check conformance against the SHA sealed by the live boundary.')
    arguments = parser.parse_args()
    if arguments.live_preparation is not None and arguments.phase != 'linux-conformance':
        parser.error('--live-preparation requires linux-conformance')
    try:
        # The GitHub-hosted Windows image exports this public default for its
        # disabled PostgreSQL service. The product checks do not use PostgreSQL.
        if (arguments.phase == 'platform' and arguments.expected_os == platform.system() == 'Windows'
                and os.environ.get('RUNNER_ENVIRONMENT') == 'github-hosted'
                and os.environ.get('PGUSER') == 'postgres' and os.environ.get('PGPASSWORD') == 'root'):
            del os.environ['PGPASSWORD']
        require_evidence_credentials()
        if arguments.phase != 'platform':
            prepared_python = os.environ.get('HEXALITH_CI_PYTHON')
            if not prepared_python or Path(prepared_python).absolute() != Path(sys.executable).absolute():
                raise ValueError('Linux product checks must use the shared prepared Python interpreter.')
            import importlib.metadata
            if importlib.metadata.version('jsonschema') != '4.26.0':
                raise ValueError('Linux product checks require prepared jsonschema 4.26.0.')
        if arguments.phase == 'stage': stage_packages()
        elif arguments.phase == 'linux': linux_checks()
        elif arguments.phase == 'linux-packages': linux_packages()
        elif arguments.phase == 'linux-census': linux_census()
        elif arguments.phase == 'linux-conformance': linux_conformance(arguments.live_preparation)
        else: package_checks(platform_checks=True, expected_os=arguments.expected_os)
        return 0
    except Exception as error:
        print(failure_detail(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
