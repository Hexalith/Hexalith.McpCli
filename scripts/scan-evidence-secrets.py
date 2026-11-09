#!/usr/bin/env python3
"""Scan a complete evidence directory and bind the result to its exact file bytes."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys

from evidence_redaction import REDACTION_POLICY, known_credentials, sanitized, sanitized_xml

SCHEMA = 'mcpcli-evidence-secret-scan/v1'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def serialized(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(',', ':')).encode('utf-8')


def scan(root, *, environment=None, receipt=None):
    """Return a deterministic receipt; never include source snippets or credential values."""
    root = Path(root).absolute()
    environment = dict(os.environ if environment is None else environment)
    files, findings, errors = [], [], []

    def label(path):
        return sanitized(Path(path).relative_to(root).as_posix(), environment=environment)

    def error(path, rule):
        errors.append({'path': label(path), 'rule': rule})

    if root.is_symlink() or not root.is_dir():
        errors.append({'path': '.', 'rule': 'directory-required-no-links'})
    else:
        paths = []
        def walk_error(failure):
            error(Path(failure.filename), 'directory-unreadable')
        for directory, directories, names in os.walk(root, followlinks=False, onerror=walk_error):
            for name in sorted(directories):
                path = Path(directory) / name
                if path.is_symlink():
                    error(path, 'symlink-refused')
                    directories.remove(name)
            paths.extend(Path(directory) / name for name in names)
        for path in sorted(paths, key=lambda entry: entry.relative_to(root).as_posix()):
            relative = path.relative_to(root).as_posix()
            try:
                mode = path.lstat().st_mode
                if not stat.S_ISREG(mode):
                    error(path, 'regular-file-required-no-links')
                    continue
                # Refuse links swapped into the tree after enumeration as well.
                descriptor = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
                with os.fdopen(descriptor, 'rb') as source:
                    if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
                        error(path, 'regular-file-required-no-links')
                        continue
                    data = source.read()
            except OSError:
                error(path, 'file-unreadable')
                continue
            entry = {'path': label(path), 'bytes': len(data), 'sha256': digest(data)}
            files.append(entry)
            if entry['path'] != relative:
                findings.append({'path': entry['path'], 'rule': 'sensitive-path'})
            try:
                encoding = 'utf-16' if data.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8-sig'
                text = data.decode(encoding)
                if re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', text) or data.startswith((
                        b'%PDF-', b'PK\x03\x04', b'PK\x05\x06', b'\x1f\x8b', b'!<arch>\n', b'!<thin>\n',
                        b'BZh', b'\xfd7zXZ\x00', b'7z\xbc\xaf\x27\x1c')) \
                        or data[257:262] == b'ustar':
                    raise ValueError('binary')
            except (UnicodeError, ValueError):
                error(path, 'unsupported-text-or-binary')
                continue
            try:
                if sanitized_xml(text, environment=environment) != text:
                    findings.append({'path': entry['path'], 'rule': 'redaction-required'})
            except (ValueError, RecursionError, OverflowError):
                error(path, 'redaction-failed')
        if not files and not errors:
            errors.append({'path': '.', 'rule': 'empty-evidence'})

    files.sort(key=lambda entry: (entry['path'], entry['sha256']))
    findings.sort(key=lambda entry: (entry['path'], entry['rule']))
    errors.sort(key=lambda entry: (entry['path'], entry['rule']))
    excluded = None
    if receipt is not None:
        try:
            excluded = label(Path(receipt).absolute())
        except ValueError:
            pass
    implementation = {}
    for name in ('scan-evidence-secrets.py', 'evidence_redaction.py'):
        implementation[name] = digest((Path(__file__).resolve().parent / name).read_bytes())
    result = 'scan-error' if errors else 'secrets-detected' if findings else 'clean'
    return {
        'schema': SCHEMA, 'policy': REDACTION_POLICY, 'result': result,
        'exitCode': 2 if errors else 1 if findings else 0,
        'implementationSha256': implementation,
        'knownCredentialCount': len(known_credentials(environment)),
        'scope': 'all regular files; UTF-8 or BOM-marked UTF-16; links and binary files refused',
        'receiptExcluded': excluded, 'files': files, 'fileCount': len(files),
        'manifestSha256': digest(serialized(files)), 'findings': findings, 'errors': errors,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evidence', type=Path, help='Complete evidence packet directory')
    parser.add_argument('--receipt', required=True, type=Path, help='New JSON receipt path (must not exist)')
    args = parser.parse_args()
    if args.receipt.exists() or args.receipt.is_symlink():
        print('Secret scan refused: receipt destination must be new.', file=sys.stderr)
        return 2
    report = scan(args.evidence, receipt=args.receipt)
    output = json.dumps(report, sort_keys=True, indent=2) + '\n'
    try:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        with args.receipt.open('x', encoding='utf-8', newline='\n') as destination:
            destination.write(output)
    except OSError:
        print('Secret scan failed: receipt could not be written.', file=sys.stderr)
        return 2
    sys.stdout.write(output)
    return report['exitCode']


if __name__ == '__main__':
    sys.exit(main())
