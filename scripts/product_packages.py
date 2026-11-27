"""Product-only package byte checks and isolated-consumer primitives."""

import hashlib
import json
from pathlib import Path
import re
import subprocess

from evidence_redaction import sanitized

ROOT = Path(__file__).resolve().parents[1]
PAIR = ["Hexalith.McpCli.Abstractions", "Hexalith.McpCli"]


def git(*args, cwd=None):
    """Read Git metadata; keep every caller in this module with literal operands."""
    return subprocess.run(['git', *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def source_sha(*, cwd=None):
    return git('rev-parse', 'HEAD', cwd=cwd)


def source_changes(*, cwd=None):
    # Qualified submodule worktrees can differ from the root gitlinks. Staged gitlink edits still change the root.
    return (git('status', '--porcelain', '--untracked-files=normal', '--ignore-submodules=all', cwd=cwd)
            or git('diff', '--cached', '--name-only', '--ignore-submodules=none', '--', cwd=cwd))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical_digest(payload: dict) -> str:
    """Hash a deterministic JSON representation without its outer digest key."""
    canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(canonical).hexdigest()


def read_json_with_digest(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('Evidence must be a regular file.')
    content = path.read_bytes()
    document = json.loads(content.decode('utf-8'))
    if not isinstance(document, dict):
        raise ValueError('Evidence must contain a JSON object.')
    return document, hashlib.sha256(content).hexdigest()


def read_json(path):
    return read_json_with_digest(path)[0]


def write_new(path, value):
    path = Path(path)
    with path.open('x', encoding='utf-8', newline='\n') as output:
        json.dump(value, output, indent=2, sort_keys=True)
        output.write('\n')


def packages(staging, version):
    validate_version(version)
    staging = Path(staging)
    expected = {f'{package}.{version}.nupkg' for package in PAIR}
    if staging.is_symlink() or not staging.is_dir() or {p.name for p in staging.iterdir()} != expected:
        raise ValueError('Staging must contain exactly the manifest pair and no other files.')
    for path in staging.iterdir():
        if path.is_symlink() or not path.is_file():
            raise ValueError('Staged packages must be regular files.')
    return {name: digest(staging / name) for name in sorted(expected)}


def check_prepared(staging, receipt):
    receipt = Path(receipt)
    if not receipt.is_file() or receipt.is_symlink():
        raise ValueError('Preparation receipt must be a regular file.')
    receipt = json.loads(receipt.read_text(encoding='utf-8'))
    if (not isinstance(receipt, dict) or receipt.get('schema') not in ('mcpcli-product-packages/v1', 'mcpcli-paired-preparation/v1')
            or not isinstance(receipt.get('source_sha'), str)
            or re.fullmatch('[0-9a-f]{40}', receipt['source_sha']) is None
            or not isinstance(receipt.get('version'), str)
            or receipt.get('packages') != packages(staging, receipt['version'])):
        raise ValueError('Preparation receipt does not bind these package bytes and source.')
    return receipt


def validate_version(version: str) -> None:
    # NuGet drops build metadata from package identity; semantic-release emits none.
    numeric = r"(?:0|[1-9][0-9]*)"
    identifier = rf"(?:{numeric}|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
    if re.fullmatch(rf"{numeric}\.{numeric}\.{numeric}(?:-{identifier}(?:\.{identifier})*)?", version) is None:
        raise ValueError(f"Invalid release version: {version}")
    if any(len(component) > 10 or int(component) > 2_147_483_647
           for component in version.split('-', 1)[0].split('.')):
        raise ValueError(f"Invalid release version: {version}; numeric components exceed the NuGet limit")


def bootstrap_target_framework(version):
    """Bind bootstrap package and consumer checks to the checked-out source."""
    project = 'src/Hexalith.McpCli.Abstractions/Hexalith.McpCli.Abstractions.csproj'
    result = subprocess.run(['dotnet', 'msbuild', project, '-nologo', '-tl:off', '-p:Configuration=Release',
                             f'-p:Version={version}', '-getProperty:TargetFramework,TargetFrameworks'],
                            check=True, capture_output=True, text=True)
    properties = json.loads(result.stdout)['Properties']
    framework = properties['TargetFramework']
    if framework not in ('net10.0', 'net11.0') or properties['TargetFrameworks']:
        raise ValueError('Bootstrap source must target only net10.0 or net11.0.')
    return framework


def failure_detail(error):
    detail = str(error)
    if isinstance(error, subprocess.CalledProcessError) and error.stderr:
        stderr = error.stderr.decode('utf-8', errors='replace') if isinstance(error.stderr, bytes) else error.stderr
        detail += f"\n{stderr.strip()}"
    detail = sanitized(detail)
    return re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", detail)
