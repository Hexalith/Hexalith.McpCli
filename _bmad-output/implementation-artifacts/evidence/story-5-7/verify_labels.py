#!/usr/bin/env python3
"""Verify the successor label register and seven README-only patches without delivery.

Completion requires explicit delivery authorization, exact owner-approved inventory
bytes integrated into McpCli, and exact README blobs integrated on every upstream
origin/main. Remote state is read from existing local refs; this tool never fetches.
"""
import argparse
import difflib
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urlsplit

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[4]
ART = Path('_bmad-output/implementation-artifacts')
E = ART / 'evidence/story-5-7'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    def unique(pairs):
        result = {}
        for k, v in pairs:
            require(k not in result, f'duplicate JSON member {k}')
            result[k] = v
        return result
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique)


def git(repo, *args):
    result = subprocess.run(['git', '-C', str(repo), *args], capture_output=True)
    require(result.returncode == 0, f'git {" ".join(args)} failed for label evidence')
    return result.stdout


def checked_file(root, item):
    path = (root / item['path']).resolve()
    require(not Path(item['path']).is_absolute() and path.is_relative_to(root.resolve()), 'label path escapes repository')
    data = path.read_bytes()
    require(sha(data) == item['sha256'], f'label artifact hash mismatch: {item["path"]}')
    return data


def compatibility_section(data):
    lines = data.decode('utf-8').splitlines(keepends=True)
    headings = [i for i, line in enumerate(lines) if line.rstrip('\r\n') == '## Legacy compatibility surfaces']
    require(len(headings) == 1, 'README must have exactly one compatibility section')
    start = headings[0]
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith('#')), len(lines))
    return ''.join(lines[start:end]).encode()


def github_repository(url):
    """Normalize standard GitHub HTTPS/SSH/git origin URL spellings."""
    value = url.strip()
    scp = re.fullmatch(r'(?:git@)?github\.com:([^\s]+)', value, re.I)
    if scp:
        path = scp[1]
    else:
        parsed = urlsplit(value)
        require(parsed.scheme.lower() in {'https', 'http', 'ssh', 'git'} and
                parsed.hostname is not None and parsed.hostname.lower() == 'github.com' and
                not parsed.query and not parsed.fragment, 'origin is not a standard GitHub repository URL')
        path = parsed.path.lstrip('/')
    path = path.rstrip('/').lower().removesuffix('.git')
    require(re.fullmatch(r'[a-z0-9_.-]+/[a-z0-9_.-]+', path) is not None, 'origin lacks a GitHub owner/repository identity')
    return path


def validated_approval(root):
    """Reuse the full owner/role/artifact/delta checks without recursing into labels."""
    spec = importlib.util.spec_from_file_location('owner57', root / E / 'verify_amendments.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _, _, receipt_bytes = module.verify_owner_packet(root, completion=True)
    return receipt_bytes


def verify(root, completion=False):
    root = Path(root).resolve()
    register = read_json(root / E / 'labels.json')
    require(register.get('schemaVersion') == '1.0.0', 'unsupported label register schema')
    if register.get('state') == 'integrated':
        completion = True
    approval_bytes = validated_approval(root) if completion else None
    prior_path = ART / 'evidence/story-5-5/labels.json'
    require(register['predecessor'] == {'path': str(prior_path), 'sha256': sha((root / prior_path).read_bytes())}, 'Story 5.5 label predecessor chain mismatch')
    prior = read_json(root / prior_path)
    expected_ids = {r['id'] for r in prior['rows']}
    rows = register['rows']
    require(len(rows) == len(expected_ids) and {r['id'] for r in rows} == expected_ids, 'label row coverage/duplicate mismatch')
    repos = register['repositories']
    require(len(repos) == len(prior['commits']) and {r['name'] for r in repos} == set(prior['commits']), 'label repository coverage/duplicate mismatch')
    inventories = {str(ART / f'{name}-migration-inventory-v{version}.md'): sha((root / ART / f'{name}-migration-inventory-v{version}.md').read_bytes())
                   for name, version in [('technical-tools', '1.0.3'), ('eventstore-admin', '1.0.2')]}
    require(register['inventoryArtifacts'] == inventories, 'labels bind wrong inventory hashes')
    tech = (root / ART / 'technical-tools-migration-inventory-v1.0.3.md').read_text()
    gates = {m[1]: m[2].split('|')[6].strip() for m in re.finditer(r'^\| (PS\d+) \|(.*)$', tech, re.M)}
    url = 'https://github.com/Hexalith/Hexalith.McpCli/blob/main/' + str(ART) + '/'
    for repo in repos:
        name = repo['name']
        require(repo['repository'] == prior['commits'][name]['repository'], f'{name}: wrong owning repository')
        owner = Path(repo['ownerCheckout'])
        origin = git(owner, 'remote', 'get-url', 'origin').decode('utf-8').strip()
        require(github_repository(origin) == github_repository(repo['repository']), f'{name}: checkout origin does not match owning repository')
        require(re.fullmatch('[0-9a-f]{40}', repo['baseRevision']) is not None, f'{name}: noncanonical base revision')
        before_section, after_section, patch = (checked_file(root, repo[k]) for k in ('before', 'after', 'patch'))
        before = git(owner, 'show', f'{repo["baseRevision"]}:README.md')
        require(sha(before) == repo['readme']['beforeSha256'] and compatibility_section(before) == before_section,
                f'{name}: before snapshot differs from committed base')
        mine = [r for r in rows if r['repository'] == name]
        expected_mine = [r for r in prior['rows'] if r['repository'] == repo['repository']]
        require({r['id'] for r in mine} == {r['id'] for r in expected_mine}, f'{name}: labels assigned to wrong owner')
        candidate = before.decode()
        for row in mine:
            old = next(r for r in expected_mine if r['id'] == row['id'])['label']['text']
            require(candidate.count(old) == 1, f'{row["id"]}: prior committed label missing')
            require('\n' not in row['label']['text'] and '\r' not in row['label']['text'], f'{row["id"]}: label must be one line')
            candidate = candidate.replace(old, row['label']['text'])
        after = candidate.encode()
        require(sha(after) == repo['readme']['afterSha256'] and compatibility_section(after) == after_section,
                f'{name}: candidate reconstruction/section hash mismatch')
        expected_patch = ''.join(difflib.unified_diff(before.decode().splitlines(keepends=True), after.decode().splitlines(keepends=True),
                                                     fromfile='a/README.md', tofile='b/README.md', n=0)).encode()
        require(patch == expected_patch and patch.startswith(b'--- a/README.md\n+++ b/README.md\n'), f'{name}: patch bytes are not the isolated README diff')
        for row in mine:
            key, label = row['id'], row['label']
            old = next(r for r in expected_mine if r['id'] == key)
            require(row['surface'] == old['surface'], f'{key}: surface mismatch')
            text = label['text']
            require(text.startswith(f'- `{old["surface"]}` '), f'{key}: displayed surface differs from historical identity')
            require(label['file'] == 'README.md' and label['sha256'] == sha(text.encode()), f'{key}: label hash/file mismatch')
            lines = after.decode().splitlines()
            require(isinstance(label['line'], int) and 0 < label['line'] <= len(lines) and lines[label['line'] - 1] == text and lines.count(text) == 1,
                    f'{key}: label anchor mismatch or duplicate')
            require(row['gate'] == gates[key] and f'removal gate "{gates[key]}"' in text, f'{key}: removal gate differs from successor inventory')
            require(f'[technical-tools inventory 1.0.3]({url}technical-tools-migration-inventory-v1.0.3.md) {key};' in text,
                    f'{key}: technical citation version/path mismatch')
            require('Technical inventory SHA-256: `' + inventories[str(ART / 'technical-tools-migration-inventory-v1.0.3.md')] + '`.' in text,
                    f'{key}: cited technical hash mismatch')
            if key in ('PS01', 'PS02'):
                require(f'[EventStore Admin inventory 1.0.2]({url}eventstore-admin-migration-inventory-v1.0.2.md)' in text and
                        'Admin inventory SHA-256: `' + inventories[str(ART / 'eventstore-admin-migration-inventory-v1.0.2.md')] + '`.' in text,
                        f'{key}: Admin citation/hash mismatch')
                require(all(s in text for s in ('confidential UI coverage', 'G4 safety fixes', 'No Admin Gateway replacement')), f'{key}: Admin gate semantics missing')
            else:
                old_module = re.findall(r'\[[^]]+ inventory [^]]+\]\([^)]*\)', old['label']['text'])[-1]
                require(old_module in text, f'{key}: independent module citation changed')
            if key == 'PS03':
                require(all(s in text for s in ('Retained local compiler', 'merged AI.Tools plan 1.2.0', 'never counted as retired', 'independent')), 'PS03: retained compiler exemption/gates missing')
            if key == 'PS14':
                require(all(s in text for s in ('Retained owner-held local exemption', 'merged AI.Tools plan 1.2.0', '--dry-run', '--live', '--rollback', '--abort', 'Story 5.10', 'independent', 'Never counted as retired', 'does not make this owner-held tool agent-safe')), 'PS14: exemption/four-mode/independent safety gate missing')
            if key in ('PS04', 'PS09'):
                require('retire together.' in text, f'{key}: paired host/plugin gate missing')
            if key in ('PS06', 'PS07'):
                require('Forwarded per-user identity is necessary but not sufficient for retirement.' in text, f'{key}: forwarded-authority gate lost')
            if key == 'PS05':
                require('Story 5.4 verdict is `retirement-blocked`, with G01–G06 open' in text and 'owner-approval.json' in text, 'PS05: Parties blocked verdict missing')
            require(not any(s in text.lower() for s in ('mcpcli is the replacement', 'replaced by mcpcli', 'use mcpcli')), f'{key}: unsupported replacement claim')
        require('These are versioned compatibility binaries. They are not retired and stay outside every Hexalith.Platform composition.' in after.decode(), f'{name}: compatibility intro missing')
        if completion:
            integration = repo.get('integration')
            require(isinstance(integration, dict), f'{name}: completion requires integrated upstream label evidence')
            revision = integration.get('commit', '')
            require(re.fullmatch('[0-9a-f]{40}', revision) is not None, f'{name}: missing integrated commit')
            require(git(owner, 'show', f'{revision}:README.md') == after, f'{name}: integrated label bytes mismatch')
            git(owner, 'merge-base', '--is-ancestor', revision, 'origin/main')
            current_readme = git(owner, 'show', 'origin/main:README.md')
            try:
                current_section = compatibility_section(current_readme)
            except ValueError:
                current_section = None
            if current_section != after_section:
                print(f'reported: {name}: current origin/main compatibility labels differ from delivered candidate', file=sys.stderr)
            require(git(owner, 'diff', '--name-only', repo['baseRevision'], revision).decode().splitlines() == ['README.md'], f'{name}: delivered change is not README-only')
            commit = git(owner, 'cat-file', 'commit', revision)
            require(integration.get('commitSha256') == sha(commit), f'{name}: integrated commit byte hash mismatch')
    if completion:
        require(register.get('state') == 'integrated', 'label register must designate integrated successor state')
        authorization = register.get('deliveryAuthorization')
        require(isinstance(authorization, dict) and all(isinstance(authorization.get(k), str) and authorization[k].strip() for k in ('exactWords', 'source', 'approvedOn')), 'completion requires explicit upstream delivery authorization')
        revision = register.get('inventoryRevision') or ''
        require(re.fullmatch('[0-9a-f]{40}', revision) is not None, 'completion requires integrated inventory revision')
        git(root, 'merge-base', '--is-ancestor', revision, 'origin/main')
        published = {**inventories, str(E / 'approval.json'): sha(approval_bytes)}
        for path, digest in published.items():
            require(sha(git(root, 'show', f'{revision}:{path}')) == digest, f'{path}: published inventory differs from approved candidate')
            require(sha(git(root, 'show', f'origin/main:{path}')) == digest, f'{path}: current origin/main artifact differs from approved candidate')
    else:
        require(register.get('state') in {'candidate-pending-owner-approval-and-delivery', 'integrated'}, 'invalid successor label state')
    return len(rows), len(repos), completion


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--approved-completion', action='store_true')
    args = parser.parse_args(argv)
    try:
        rows, repos, completed = verify(args.root, args.approved_completion)
    except (ValueError, KeyError, TypeError, OSError, IndexError) as error:
        print(f'FAIL: {error}', file=sys.stderr)
        return 1
    print(f'PASS: successor register, {rows} labels in {repos} README-only patches; ' +
          ('integrated delivery verified' if completed else 'candidate only; integrated delivery remains a completion gate'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
