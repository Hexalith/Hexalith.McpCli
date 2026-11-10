#!/usr/bin/env python3
"""Independent read-back of the Story 5.5 labels from each committed label blob.

It reads only the label commit of each repository (`--rev`, default HEAD), that commit's parent and the McpCli
inventory bytes. It does not import build-labels.py, so a generator mistake cannot verify itself. Usage:

    python3 verify-labels.py --worktrees <root> [--path <repo>=<dir> ...] [--rev <repo>=<sha> ...]
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

MCPCLI = Path(__file__).resolve().parents[4]
INVENTORY = MCPCLI / '_bmad-output/implementation-artifacts/technical-tools-migration-inventory-v1.md'
PIN = 'c70ca9784da393cb1929741c6a6c9564717eace5'
OWNER_APPROVAL = (f'https://github.com/Hexalith/Hexalith.McpCli/blob/{PIN}/_bmad-output/implementation-artifacts/'
                  'evidence/story-5-4-owner-approval/owner-approval.json')
LINK = f'(https://github.com/Hexalith/Hexalith.McpCli/blob/{PIN}/_bmad-output/implementation-artifacts/'
TECHNICAL_TOOLS = '[technical-tools inventory 1.0.2]' + LINK + 'technical-tools-migration-inventory-v1.md)'
ADMIN = ('EventStore Admin inventory 1.0.1', 'eventstore-admin-migration-inventory-v1.md')
FRONTCOMPOSER = ('FrontComposer inventory 1.0.0', 'frontcomposer-migration-inventory-v1.md')
MEMORIES = ('Memories inventory 1.0.0', 'memories-migration-inventory-v1.md')
PROJECTS = ('Projects inventory 1.0.0', 'projects-migration-inventory-v1.md')
FOLDERS = ('Folders inventory 1.0.0', 'folders-migration-inventory-v1.md')
CHATBOT = ('ChatBot inventory 1.0.0', 'chatbot-migration-inventory-v1.md')
# repository -> row -> (surface, (module inventory title, its file at the pin))
EXPECTED = {
    'eventstore': {'PS01': ('Hexalith.EventStore.Admin.Cli', ADMIN), 'PS02': ('Hexalith.EventStore.Admin.Mcp', ADMIN)},
    'frontcomposer': {'PS03': ('Hexalith.FrontComposer.Cli', FRONTCOMPOSER),
                      'PS04': ('Hexalith.FrontComposer.Mcp', FRONTCOMPOSER)},
    'parties': {'PS05': ('Hexalith.Parties.Mcp', ('Parties inventory 1.2.0', 'parties-migration-inventory-v1.md'))},
    'memories': {'PS06': ('Hexalith.Memories.Cli', MEMORIES), 'PS07': ('Hexalith.Memories.Mcp', MEMORIES),
                 'PS14': ('tools/MigrateEmbeddingVectors', MEMORIES)},
    'projects': {'PS08': ('Hexalith.Projects.Cli', PROJECTS), 'PS09': ('Hexalith.Projects.Mcp', PROJECTS)},
    'folders': {'PS10': ('Hexalith.Folders.Cli', FOLDERS), 'PS11': ('Hexalith.Folders.Mcp', FOLDERS)},
    'chatbot': {'PS12': ('Hexalith.ChatBot.Cli', CHATBOT), 'PS13': ('Hexalith.ChatBot.Mcp', CHATBOT)},
}
DESCRIPTIONS = {
    'eventstore': ['src/Hexalith.EventStore.Admin.Cli/Hexalith.EventStore.Admin.Cli.csproj'],
    # FrontComposer is README-only: its dependency policy seals every tracked .csproj digest, so any
    # .csproj change there is reported as an unexpected changed file (user decision, 2026-11-10).
    'memories': ['src/Hexalith.Memories.Cli/Hexalith.Memories.Cli.csproj',
                 'src/Hexalith.Memories.Mcp/Hexalith.Memories.Mcp.csproj'],
    'folders': ['src/Hexalith.Folders.Cli/Hexalith.Folders.Cli.csproj'],
}
PREFIX = 'Compatibility binary, not retired; see "Legacy compatibility surfaces" in the repository README for its removal gate. '
INTRO = 'These are versioned compatibility binaries. They are not retired and stay outside every Hexalith.Platform composition.'
REPLACEMENT_CLAIMS = ('mcpcli is the replacement', 'replaced by mcpcli', 'use mcpcli')


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n', 1)[0])
    parser.add_argument('--worktrees', required=True, type=Path)
    parser.add_argument('--path', action='append', default=[], help='<repo>=<checkout>; default <worktrees>/<repo>')
    parser.add_argument('--rev', action='append', default=[], help='<repo>=<commit>; default HEAD')
    args = parser.parse_args()
    revs = dict(item.split('=', 1) for item in args.rev)
    paths = {repo: Path(path) for repo, path in (item.split('=', 1) for item in args.path)}

    def git(repo, *command, binary=False):
        out = subprocess.run(['git', *command], cwd=paths.get(repo, args.worktrees / repo), check=True,
                             capture_output=True).stdout
        return out if binary else out.decode('utf-8')

    cells = {}
    for line in INVENTORY.read_text(encoding='utf-8').split('\n'):
        match = re.match(r'^\| (PS\d\d) \|', line)
        if match:
            cells[match.group(1)] = line.strip().strip('|').split('|')[7].strip()
    failures, report, labeled = [], [], set()
    for repo, rows in EXPECTED.items():
        commit = git(repo, 'rev-parse', revs.get(repo, 'HEAD')).strip()
        parent = f'{commit}^'
        readme = git(repo, 'show', f'{commit}:README.md').split('\n')
        headings = [i for i, l in enumerate(readme) if l == '## Legacy compatibility surfaces']
        if len(headings) != 1:
            failures.append(f'{repo}: {len(headings)} section headings')
            continue
        start = headings[0]
        end = next((i for i in range(start + 1, len(readme)) if readme[i].startswith('#')), len(readme))
        section = readme[start:end]
        if section[1:4] != ['', INTRO, '']:
            failures.append(f'{repo}: intro sentence missing or moved')
        bullets = [l for l in section if l.startswith('- ')]
        if len(bullets) != len(rows):
            failures.append(f'{repo}: {len(bullets)} bullets for {len(rows)} rows')
        for ps, (surface, (inventory, inventory_file)) in rows.items():
            mine = [b for b in bullets if b.startswith(f'- `{surface}`')]
            elsewhere = [l for l in readme if ps in l and l not in mine]
            if len(mine) != 1 or elsewhere:
                failures.append(f'{ps}: {len(mine)} labels, {len(elsewhere)} other lines naming {ps}')
                continue
            label = mine[0]
            gate = re.search(r'removal gate "([^"]*)"', label)
            checks = {
                'gateByteEqual': bool(gate) and gate.group(1).encode('utf-8') == cells[ps].encode('utf-8'),
                # Each citation is compared as a whole link, title and target file, so a wrong path fails.
                'technicalToolsCited': f'{TECHNICAL_TOOLS} {ps};' in label,
                'moduleInventoryCited': f'[{inventory}]{LINK}{inventory_file})' in label,
                'noReplacementClaim': not any(claim in label.lower() for claim in REPLACEMENT_CLAIMS),
            }
            if repo == 'memories':
                checks['identityNecessaryNotSufficient'] = 'Forwarded per-user identity is necessary but not sufficient' in label
            if ps in ('PS04', 'PS09'):
                checks['retireTogether'] = 'retire together.' in label and ('Hexalith.Projects.Mcp' in label if ps == 'PS04' else 'Hexalith.FrontComposer.Mcp' in label)
            if ps == 'PS05':
                checks['verdictAndGapsLinked'] = ('Story 5.4 verdict is `retirement-blocked`, with G01–G06 open '
                                                  f'([owner approval]({OWNER_APPROVAL})).') in label
            if not all(checks.values()):
                failures.append(f'{ps}: {checks}')
            labeled.add(ps)
            report.append((ps, repo, readme.index(label) + 1, checks))
        numstat = git(repo, 'diff', '--numstat', parent, commit).strip().split('\n')
        allowed = {'README.md', *DESCRIPTIONS.get(repo, [])}
        for row in numstat:
            added, deleted, path = row.split('\t')
            if path not in allowed:
                failures.append(f'{repo}: unexpected changed file {path}')
            elif path != 'README.md' and (added, deleted) not in (('1', '1'), ('1', '0')):
                failures.append(f'{repo}: {path} changes {added}/{deleted} lines')
        before = git(repo, 'show', f'{parent}:README.md', binary=True)
        after = git(repo, 'show', f'{commit}:README.md', binary=True)
        if repo == 'projects':
            # The base README has no final newline; the label commit may only add one, then append the section.
            if before != b'# Hexalith.Projects' or not after.startswith(before + b'\n\n## Legacy compatibility surfaces\n'):
                failures.append('projects: title line changed beyond the added final newline')
        else:
            removed = [l for l in git(repo, 'diff', '-U0', parent, commit, '--', 'README.md').split('\n')
                       if l.startswith('-') and not l.startswith('---')]
            if removed or not before.endswith(b'\n'):
                failures.append(f'{repo}: README lines removed {removed}')
        for csproj in DESCRIPTIONS.get(repo, []):
            body = git(repo, 'show', f'{commit}:{csproj}')
            base = git(repo, 'show', f'{parent}:{csproj}')
            if body.count('<Description>' + PREFIX) != 1 or body.replace(PREFIX, '', 1) != base:
                failures.append(f'{csproj}: prefix is not the only change')
    if labeled != set(cells):
        failures.append(f'labeled {sorted(labeled)} != inventory {sorted(cells)}')
    for ps, repo, line, checks in sorted(report):
        print(ps, repo, f'README.md:{line}', 'ok' if all(checks.values()) else 'FAIL', ','.join(k for k, v in checks.items() if v))
    print('FAILURES' if failures else 'all label checks passed', json.dumps(failures, ensure_ascii=False))
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
