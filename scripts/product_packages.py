"""Product-only package byte checks and isolated-consumer primitives."""

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess

from evidence_redaction import sanitized

ROOT = Path(__file__).resolve().parents[1]
PAIR = ["Hexalith.McpCli.Abstractions", "Hexalith.McpCli"]


def module(filename):
    spec = importlib.util.spec_from_file_location(filename.replace('-', '_'), Path(__file__).with_name(filename + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def run(arguments, **kwargs):
    return subprocess.run([str(arg) for arg in arguments], check=True, capture_output=True, **kwargs)


def git(*args):
    return run(['git', *args], text=True).stdout.strip()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('Evidence must be a regular file.')
    document = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(document, dict):
        raise ValueError('Evidence must contain a JSON object.')
    return document


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



def failure_detail(error):
    detail = str(error)
    if isinstance(error, subprocess.CalledProcessError) and error.stderr:
        stderr = error.stderr.decode('utf-8', errors='replace') if isinstance(error.stderr, bytes) else error.stderr
        detail += f"\n{stderr.strip()}"
    detail = sanitized(detail)
    return re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", detail)
