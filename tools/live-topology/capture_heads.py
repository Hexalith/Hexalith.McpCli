#!/usr/bin/env python3
"""Retain read-only discovery and hashes from the exact compiled heads used by live CI."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/conformance-vectors/v1'))
from run_loopback import HeadProcess, _assert_discovery_parity


def digest(value) -> str:
    """Hash sorted-key compact UTF-8 JSON, preserving Unicode characters."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')).hexdigest()


def capture(host: Path) -> dict:
    """Compare both discovery heads, without submitting any Command or Query."""
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True, timeout=10).strip()
    if re.fullmatch(r'(?:[0-9a-f]{40}|[0-9a-f]{64})', commit) is None:
        raise ValueError('A full canonical candidate commit is required.')
    binaries = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted(host.parent.glob('*.dll')) if path.is_file()}
    if host.name not in binaries:
        raise ValueError('The compiled host is missing from its binary directory.')
    with tempfile.TemporaryDirectory(prefix='mcpcli-discovery-capture-') as home:
        head = HeadProcess(host, home, timeout=30)
        code, cli_modules = head.cli(['modules', '--strict'])
        error, modules = head.mcp('list_modules', {})
        _assert_discovery_parity(code, error, cli_modules, modules, 'list_modules')
        catalogs = {}
        for module in modules['modules']:
            name = module['name']
            if name in catalogs:
                raise ValueError('Duplicate module in discovery.')
            code, cli = head.cli(['operations', name, '--strict'])
            error, structured = head.mcp('list_operations', {'module': name})
            _assert_discovery_parity(code, error, cli, structured, 'list_operations ' + name)
            catalogs[name] = structured
        if not catalogs:
            raise ValueError('A nonempty compiled Catalog is required.')
    after = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
             for path in sorted(host.parent.glob('*.dll')) if path.is_file()}
    if after != binaries:
        raise ValueError('Head binaries changed during discovery capture.')
    return {'result': 'passed', 'algorithm': 'SHA-256(sorted-key compact UTF-8 JSON; ensure_ascii=false)',
            'sourceCommit': commit, 'host': host.name, 'binariesSha256': binaries, 'catalogSha256': digest(catalogs),
            'modules': {name: {'sha256': digest(content), 'structuredContent': content}
                        for name, content in sorted(catalogs.items())}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    receipt = capture(args.host.resolve())
    with args.output.open('x', encoding='utf-8') as output:
        output.write(json.dumps(receipt, indent=2, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
