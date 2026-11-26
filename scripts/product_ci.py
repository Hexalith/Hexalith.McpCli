#!/usr/bin/env python3
"""Product checks over the shared Release build and one source-bound CI package pair."""
from __future__ import annotations
import argparse
import json
import os
import platform
import signal
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile

from product_process import run as run_owned
from evidence_redaction import require_evidence_credentials
from product_packages import (read_json, check_prepared, digest, failure_detail, packages, source_changes, source_sha,
                              validate_version, write_new)

ROOT = Path(__file__).resolve().parents[1]


def execute(command, *, timeout=900):
    print('Product check:', *map(str, command), flush=True)
    output = staging_root() / 'diagnostics' / ('command-' + __import__('uuid').uuid4().hex)
    return run_owned(command, cwd=ROOT, output=output, timeout=timeout)


def staging_root() -> Path:
    directory = os.environ.get('RUNNER_TEMP')
    if not directory:
        raise ValueError('Product CI requires its runner-owned temporary directory.')
    return Path(directory).resolve() / 'mcpcli-product'


def require_source(receipt: dict) -> None:
    if receipt['source_sha'] != source_sha() or source_changes():
        raise ValueError('Product checks require this exact clean checkout SHA; tracked or untracked source drift is refused.')


def stage_packages() -> None:
    source = source_sha()
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


def linux_checks() -> None:
    stage_packages()
    package_checks()
    execute([sys.executable, '-m', 'unittest', 'discover', '-v', '-s', 'scripts/tests', '-p', 'test_*.py'], timeout=900)
    execute(['bash', ROOT / 'tools/conformance-vectors/v1/run-sample-validation.sh', 'Release'])
    execute(['bash', ROOT / 'tools/conformance-vectors/v1/run-sample-loopback.sh'], timeout=1800)
    execute([sys.executable, ROOT / 'tools/conformance-vectors/v1/check_enrolled.py', '--output',
             staging_root() / 'enrolled'], timeout=1800)
    execute([sys.executable, '-m', 'unittest', 'discover', '-v', '-s', 'tools/live-topology', '-p', 'test_*.py'], timeout=3600)
    execute([sys.executable, ROOT / 'tools/live-topology/run-vectors.py', '--output', staging_root() / 'preflight', '--preflight-only'])


def main() -> int:
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('stage', 'linux', 'platform'))
    parser.add_argument('--expected-os', choices=('Windows', 'Darwin'))
    arguments = parser.parse_args()
    try:
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
        else: package_checks(platform_checks=True, expected_os=arguments.expected_os)
        return 0
    except Exception as error:
        print(failure_detail(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
