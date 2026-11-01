"""Shared, fail-closed primitives for immutable paired release evidence."""

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess

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


def source():
    sha = git('rev-parse', 'HEAD')
    if re.fullmatch('[0-9a-f]{40}', sha) is None:
        raise ValueError('An exact source SHA is required.')
    return {'source_sha': sha, 'source_clean': not git('status', '--porcelain', '--untracked-files=normal')}


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


def validate_source_evidence(gate, sha):
    if (not isinstance(gate, dict) or gate.get('schema') != 'mcpcli-paired-source/v1' or gate.get('source_sha') != sha
            or gate.get('current_main') != sha or gate.get('source_clean') is not True
            or set(gate.get('gates', {})) != {'ci.yml', 'commitlint.yml'}):
        raise ValueError('Source evidence lacks exact current-main blocking gates.')
    fr22 = gate.get('fr22', {})
    if not isinstance(fr22, dict) or not isinstance(fr22.get('synchronization'), dict):
        raise ValueError('FR-22 evidence must contain synchronized instruction hashes.')
    sync = fr22['synchronization']
    if (fr22.get('source_sha') != sha or fr22.get('source_clean') is not True
            or any(not isinstance(fr22.get(key), str) or re.fullmatch('[0-9a-f]{40}', fr22[key]) is None
                   for key in ('baseline_revision', 'upstream_main'))
            or fr22.get('required_revision') != module('verify-paired-prerequisites').REQUIRED
            or set(sync) != {'AGENTS.md', 'CLAUDE.md', '.github/copilot-instructions.md'}
            or len(set(sync.values())) != 1
            or any(not isinstance(value, str) or re.fullmatch('[0-9a-f]{64}', value) is None for value in sync.values())):
        raise ValueError('FR-22 evidence is incomplete or belongs to different source.')
    verifier = module('verify-release-source')
    for workflow, required in [('ci.yml', verifier.STAGING_JOBS), ('commitlint.yml', verifier.STAGING_COMMITLINT_JOBS)]:
        run = gate['gates'][workflow]
        if run.get('source_sha') != sha or run.get('status') != 'completed' or run.get('conclusion') != 'success':
            raise ValueError('A required source workflow did not succeed at the exact SHA.')
        verifier.validate_jobs(run.get('jobs', []), required)


def write_new(path, value):
    path = Path(path)
    with path.open('x', encoding='utf-8', newline='\n') as output:
        json.dump(value, output, indent=2, sort_keys=True)
        output.write('\n')


def packages(staging, version):
    module('release-request').validate_version(version)
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
    if (receipt.get('schema') != 'mcpcli-paired-preparation/v1'
            or re.fullmatch('[0-9a-f]{40}', receipt.get('source_sha', '')) is None
            or receipt.get('packages') != packages(staging, receipt['version'])):
        raise ValueError('Preparation receipt does not bind these package bytes and source.')
    return receipt
