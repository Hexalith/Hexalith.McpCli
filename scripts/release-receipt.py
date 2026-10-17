#!/usr/bin/env python3
"""Bind prepared package bytes to their source revision and clean working tree."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


def source_provenance():
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], check=True, capture_output=True, text=True).stdout.strip()
    if re.fullmatch(r'[0-9a-f]{40}', head) is None:
        raise ValueError('Preparation requires an exact source SHA.')
    changes = subprocess.run(['git', 'status', '--porcelain', '--untracked-files=normal'],
                             check=True, capture_output=True, text=True).stdout.strip()
    return {'source_sha': head, 'source_clean': not changes}


def prepared_receipt(before, package):
    after = source_provenance()
    if before['source_sha'] != after['source_sha']:
        raise ValueError('Preparation source HEAD changed during the build.')
    return {'sha256': hashlib.sha256(Path(package).read_bytes()).hexdigest(),
            'source_sha': before['source_sha'], 'source_clean': before['source_clean'] and after['source_clean']}


def verify_receipt(receipt, package, expected_sha):
    receipt = Path(receipt)
    if not receipt.is_file() or receipt.is_symlink():
        raise ValueError('The prepared bootstrap package hash receipt is missing or invalid.')
    try:
        recorded = json.loads(receipt.read_text())
        if (not isinstance(recorded, dict) or set(recorded) != {'sha256', 'source_sha', 'source_clean'}
                or re.fullmatch(r'[0-9a-f]{64}', recorded['sha256']) is None
                or re.fullmatch(r'[0-9a-f]{40}', recorded['source_sha']) is None
                or type(recorded['source_clean']) is not bool):
            raise ValueError()
    except (ValueError, TypeError):
        raise ValueError('The prepared bootstrap package hash receipt is invalid.') from None
    if recorded['source_clean'] is not True:
        raise ValueError('The preparation receipt records dirty source; prepare again from clean committed source.')
    if recorded['source_sha'] != expected_sha:
        raise ValueError('The preparation receipt source SHA does not match the exact release source SHA.')
    if recorded['sha256'] != hashlib.sha256(Path(package).read_bytes()).hexdigest():
        raise ValueError('The bootstrap package changed after preparation.')
    return recorded['sha256']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('capture')
    record = commands.add_parser('record')
    record.add_argument('provenance')
    record.add_argument('package')
    verify = commands.add_parser('verify')
    verify.add_argument('receipt')
    verify.add_argument('package')
    verify.add_argument('sha')
    args = parser.parse_args()
    try:
        if args.command == 'capture':
            print(json.dumps(source_provenance()))
        elif args.command == 'record':
            print(json.dumps(prepared_receipt(json.loads(args.provenance), args.package)))
        else:
            print(verify_receipt(args.receipt, args.package, args.sha))
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'Bootstrap receipt failed: {error}\n')


if __name__ == '__main__':
    main()
