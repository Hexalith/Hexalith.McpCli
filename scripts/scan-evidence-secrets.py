#!/usr/bin/env python3
"""Scan a complete evidence directory and bind the result to its exact file bytes."""

import argparse
from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys

from evidence_redaction import (
    REDACTION_POLICY, ShortEvidenceCredentialError, known_credentials, require_evidence_credentials, sanitized, sanitized_xml,
)

SCHEMA = 'mcpcli-evidence-secret-scan/v1'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def serialized(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(',', ':')).encode('utf-8')


def reached_through_link_or_parent(root):
    """True when an absolute, unnormalized root names a parent step or passes through a linked ancestor."""
    return '..' in root.parts or any(ancestor.is_symlink() for ancestor in root.parents)


def open_root(root, flags):
    """Open the whole absolute path one component at a time without following links."""
    components = root.parts[1:]
    # Ancestors need search permission. Only the packet root needs to be listed.
    search_flags = flags | getattr(os, 'O_SEARCH', getattr(os, 'O_PATH', 0))
    descriptor = os.open(root.anchor, search_flags if components else flags)
    for index, component in enumerate(components, 1):
        try:
            child = os.open(component, flags if index == len(components) else search_flags, dir_fd=descriptor)
        finally:
            os.close(descriptor)
        descriptor = child
    return descriptor


def scan(root, *, environment=None, receipt=None, retain_root=None):
    """Return a deterministic receipt; never include source snippets or credential values."""
    root = Path(root).absolute()
    environment = dict(os.environ if environment is None else environment)
    require_evidence_credentials(environment)
    files, findings, errors = [], [], []

    def label(path):
        return sanitized(Path(path).relative_to(root).as_posix(), environment=environment)

    def error(path, rule):
        errors.append({'path': label(path), 'rule': rule})

    def scan_file(directory, name, path):
        relative = path.relative_to(root).as_posix()
        try:
            mode = os.stat(name, dir_fd=directory, follow_symlinks=False).st_mode
            if not stat.S_ISREG(mode):
                error(path, 'regular-file-required-no-links')
                return
            descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
            with os.fdopen(descriptor, 'rb') as source:
                if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
                    error(path, 'regular-file-required-no-links')
                    return
                data = source.read()
        except OSError:
            error(path, 'file-unreadable')
            return
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
            return
        try:
            if sanitized_xml(text, environment=environment) != text:
                findings.append({'path': entry['path'], 'rule': 'redaction-required'})
        except (ValueError, RecursionError, OverflowError):
            error(path, 'redaction-failed')

    def scan_directory(directory, path, flags):
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    child_path = path / entry.name
                    if entry.is_dir(follow_symlinks=False):
                        try:
                            child = os.open(entry.name, flags, dir_fd=directory)
                        except OSError:
                            error(child_path, 'directory-unreadable')
                            continue
                        try:
                            scan_directory(child, child_path, flags)
                        finally:
                            os.close(child)
                    elif entry.is_symlink() and entry.is_dir():
                        error(child_path, 'symlink-refused')
                    else:
                        scan_file(directory, entry.name, child_path)
        except (OSError, RecursionError):
            error(path, 'directory-unreadable')

    if root.is_symlink() or not root.is_dir():
        error(root, 'directory-required-no-links')
    elif reached_through_link_or_parent(root):
        error(root, 'root-path-not-canonical')
    elif not all(hasattr(os, flag) for flag in ('O_DIRECTORY', 'O_NOFOLLOW', 'O_NONBLOCK')):
        error(root, 'directory-unreadable')
    else:
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        try:
            directory = open_root(root, flags)
        except OSError:
            error(root, 'root-path-not-canonical')
        else:
            try:
                if retain_root is not None:
                    retain_root(directory)
                scan_directory(directory, root, flags)
            finally:
                os.close(directory)
        if not files and not errors:
            error(root, 'empty-evidence')

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


def write_packet_receipt(packet, directory, relative, output):
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    if '..' in relative.parts or not relative.name:
        raise OSError('Invalid packet receipt path')
    with ExitStack() as handles:
        current = open_root(packet, flags)
        handles.callback(os.close, current)
        if not os.path.samestat(os.fstat(current), os.fstat(directory)):
            raise OSError('Packet directory changed during scanning')
        for component in relative.parts[:-1]:
            try:
                os.mkdir(component, dir_fd=directory)
            except FileExistsError:
                pass
            directory = os.open(component, flags, dir_fd=directory)
            handles.callback(os.close, directory)
        descriptor = os.open(relative.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                             mode=0o666, dir_fd=directory)
        with os.fdopen(descriptor, 'w', encoding='utf-8', newline='\n') as destination:
            destination.write(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evidence', type=Path, help='Complete evidence packet directory')
    parser.add_argument('--receipt', required=True, type=Path, help='New JSON receipt path (must not exist)')
    args = parser.parse_args()
    if args.receipt.exists() or args.receipt.is_symlink():
        print('Secret scan refused: receipt destination must be new.', file=sys.stderr)
        return 2
    packet, receipt = args.evidence.absolute(), args.receipt.absolute()
    in_packet = receipt.is_relative_to(packet)
    with ExitStack() as handles:
        scanned_directory = None

        def retain(directory):
            nonlocal scanned_directory
            scanned_directory = os.dup(directory)
            handles.callback(os.close, scanned_directory)

        try:
            report = scan(packet, receipt=receipt, retain_root=retain if in_packet else None)
        except ShortEvidenceCredentialError as error:
            print(sanitized(f'Secret scan refused: {error}'), file=sys.stderr)
            return 2
        output = json.dumps(report, sort_keys=True, indent=2) + '\n'
        try:
            if scanned_directory is not None:
                write_packet_receipt(packet, scanned_directory, receipt.relative_to(packet), output)
            else:
                receipt.parent.mkdir(parents=True, exist_ok=True)
                with receipt.open('x', encoding='utf-8', newline='\n') as destination:
                    destination.write(output)
        except OSError:
            print('Secret scan failed: receipt could not be written.', file=sys.stderr)
            return 2
    sys.stdout.write(output)
    return report['exitCode']


if __name__ == '__main__':
    sys.exit(main())
