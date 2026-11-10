#!/usr/bin/env python3
"""Build the Story 5.5 label register (labels.json) from the committed upstream label blobs.

Every row, hash and anchor is read from the label commit of each repository (`--rev`, default HEAD), so the
register can be regenerated from the pushed commits after delivery. Usage:

    python3 build-labels.py --worktrees <root> [--path <repo>=<dir> ...] [--rev <repo>=<sha> ...]
        [--outcomes <file>] --output labels.json

`<root>/<repo>` is a checkout of each owning repository; `--path` replaces it for one repository. `--outcomes` is a
JSON object keyed by repository: {"status": "pushed" | "ci-red" | "push-rejected" | "merged-unreviewed",
"mergedCommit": <sha or null>, "mainCiRuns": [{"id": <run id>, "workflow": <name>, "conclusion": <conclusion>}] or
null, "note": <text>}. `merged-unreviewed` records a label commit that someone else's push merged into main before
the Build review; its mergedCommit is the origin/main commit that brought it in.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

MCPCLI = Path(__file__).resolve().parents[4]
PIN = 'c70ca9784da393cb1929741c6a6c9564717eace5'
ART = '_bmad-output/implementation-artifacts'
BASE = f'https://github.com/Hexalith/Hexalith.McpCli/blob/{PIN}/{ART}/'
TECH = 'technical-tools-migration-inventory-v1.md'
OWNER_APPROVAL = BASE + 'evidence/story-5-4-owner-approval/owner-approval.json'
HEADING = '## Legacy compatibility surfaces'
INTRO = ('These are versioned compatibility binaries. They are not retired and stay outside '
         'every Hexalith.Platform composition.')
DESCRIPTION_PREFIX = ('Compatibility binary, not retired; see "Legacy compatibility surfaces" in the '
                      'repository README for its removal gate. ')
IDENTITY = 'Forwarded per-user identity is necessary but not sufficient for retirement.'
MODULE_INVENTORIES = {
    'eventstore-admin': ('EventStore Admin inventory', '1.0.1', 'eventstore-admin-migration-inventory-v1.md'),
    'frontcomposer': ('FrontComposer inventory', '1.0.0', 'frontcomposer-migration-inventory-v1.md'),
    'parties': ('Parties inventory', '1.2.0', 'parties-migration-inventory-v1.md'),
    'memories': ('Memories inventory', '1.0.0', 'memories-migration-inventory-v1.md'),
    'projects': ('Projects inventory', '1.0.0', 'projects-migration-inventory-v1.md'),
    'folders': ('Folders inventory', '1.0.0', 'folders-migration-inventory-v1.md'),
    'chatbot': ('ChatBot inventory', '1.0.0', 'chatbot-migration-inventory-v1.md'),
}
# id, repository, surface, project, module inventory, extra sentence, Decision 4 csproj, NuGet visibility
SURFACES = [
    ('PS01', 'eventstore', '`Hexalith.EventStore.Admin.Cli` (.NET tool `eventstore-admin`)',
     'src/Hexalith.EventStore.Admin.Cli/Hexalith.EventStore.Admin.Cli.csproj', 'eventstore-admin', None, True, 'next'),
    ('PS02', 'eventstore', '`Hexalith.EventStore.Admin.Mcp` (stdio MCP server)',
     'src/Hexalith.EventStore.Admin.Mcp/Hexalith.EventStore.Admin.Mcp.csproj', 'eventstore-admin', None, False, None),
    ('PS03', 'frontcomposer', '`Hexalith.FrontComposer.Cli` (.NET tool `frontcomposer`)',
     # No Description prefix: FrontComposer seals every tracked .csproj digest (user decision, 2026-11-10).
     'src/Hexalith.FrontComposer.Cli/Hexalith.FrontComposer.Cli.csproj', 'frontcomposer', None, False, None),
    ('PS04', 'frontcomposer', '`Hexalith.FrontComposer.Mcp` (HTTP MCP host library)',
     'src/Hexalith.FrontComposer.Mcp/Hexalith.FrontComposer.Mcp.csproj', 'frontcomposer',
     'The FrontComposer host and the Projects plug-in (`Hexalith.Projects.Mcp`) retire together.', False, None),
    ('PS05', 'parties', '`Hexalith.Parties.Mcp` (container `parties-mcp`)',
     'src/Hexalith.Parties.Mcp/Hexalith.Parties.Mcp.csproj', 'parties',
     'Retirement is blocked: the McpCli Story 5.4 verdict is `retirement-blocked`, with G01–G06 open '
     f'([owner approval]({OWNER_APPROVAL})).', False, None),
    ('PS06', 'memories', '`Hexalith.Memories.Cli` (.NET tool `memories`)',
     'src/Hexalith.Memories.Cli/Hexalith.Memories.Cli.csproj', 'memories', IDENTITY, True, 'next'),
    ('PS07', 'memories', '`Hexalith.Memories.Mcp` (container `memories-mcp`)',
     'src/Hexalith.Memories.Mcp/Hexalith.Memories.Mcp.csproj', 'memories', IDENTITY, True, 'next'),
    ('PS08', 'projects', '`Hexalith.Projects.Cli` (CLI)',
     'src/Hexalith.Projects.Cli/Hexalith.Projects.Cli.csproj', 'projects', None, False, None),
    ('PS09', 'projects', '`Hexalith.Projects.Mcp` (FrontComposer MCP plug-in library)',
     'src/Hexalith.Projects.Mcp/Hexalith.Projects.Mcp.csproj', 'projects',
     'The Projects plug-in and the FrontComposer host (`Hexalith.FrontComposer.Mcp`) retire together.', False, None),
    ('PS10', 'folders', '`Hexalith.Folders.Cli` (.NET tool `folders`)',
     'src/Hexalith.Folders.Cli/Hexalith.Folders.Cli.csproj', 'folders', None, True, 'first'),
    ('PS11', 'folders', '`Hexalith.Folders.Mcp` (stdio MCP server)',
     'src/Hexalith.Folders.Mcp/Hexalith.Folders.Mcp.csproj', 'folders', None, False, None),
    ('PS12', 'chatbot', '`Hexalith.ChatBot.Cli` (CLI)',
     'src/Hexalith.ChatBot.Cli/Hexalith.ChatBot.Cli.csproj', 'chatbot', None, False, None),
    ('PS13', 'chatbot', '`Hexalith.ChatBot.Mcp` (stdio MCP server)',
     'src/Hexalith.ChatBot.Mcp/Hexalith.ChatBot.Mcp.csproj', 'chatbot', None, False, None),
    ('PS14', 'memories', '`tools/MigrateEmbeddingVectors` (operator CLI)',
     'tools/MigrateEmbeddingVectors/MigrateEmbeddingVectors.csproj', 'memories', IDENTITY, False, None),
]
REPOS = ['eventstore', 'frontcomposer', 'parties', 'memories', 'projects', 'folders', 'chatbot']
GITHUB = {repo: f'https://github.com/Hexalith/Hexalith.{name}' for repo, name in zip(
    REPOS, ['EventStore', 'FrontComposer', 'Parties', 'Memories', 'Projects', 'Folders', 'ChatBot'])}
VISIBILITY = {'next': 'after the next release of this package', 'first': 'on its first release (never published)'}
OWNER_CLI = ('owner checkout node_modules/.bin/commitlint (@commitlint/cli 21.2.4), run read-only; its lockfile '
             'and config are unchanged from origin/main')
WORKTREE_CLI = ('worktree node_modules/.bin/commitlint (@commitlint/cli 21.2.4) from npm ci --offline --ignore-scripts '
                'of the origin/main lockfile')
COMMITLINT = {
    'eventstore': OWNER_CLI, 'frontcomposer': OWNER_CLI, 'projects': OWNER_CLI,
    'parties': WORKTREE_CLI, 'folders': WORKTREE_CLI,
    'memories': WORKTREE_CLI + '; the commit-msg hook re-ran it',
    'chatbot': ('the Parties worktree node_modules/.bin/commitlint (@commitlint/cli 21.2.4) with --config '
                'commitlint.config.cjs (no extends); ChatBot pins no CLI'),
}
RELEASE_RULES = {
    'eventstore': '.releaserc.json: default @semantic-release/commit-analyzer rules; release.yml is workflow_dispatch only',
    'frontcomposer': '.releaserc.json: conventionalcommits preset, no releaseRules; release.yml is workflow_dispatch only',
    'parties': 'release.config.cjs: default commit-analyzer rules; release.yml is workflow_dispatch only',
    'memories': '.releaserc.json: default commit-analyzer rules; release.yml is workflow_dispatch only',
    'projects': 'release.config.cjs: default commit-analyzer rules; release.yml is workflow_dispatch only',
    'folders': '.releaserc.json: default commit-analyzer rules; release.yml is workflow_dispatch only',
    'chatbot': ('.releaserc.json: default commit-analyzer rules; release.yml runs on push to main, so its gates run, '
                'but semantic-release cuts no release for a docs commit'),
}
DELIVERY_PROCEDURE = [
    'Run only after the Build review passes, one repository at a time.',
    'Fetch origin. If origin/main moved past the recorded base, rebase the label commit onto it, revalidate the exact '
    'message with that repository\'s commitlint, and rerun its pinned README tests if the rebase changed README.md, '
    'a modified .csproj or a test that reads them. Parties already needs this: its origin/main is 64085d9f, not the '
    'recorded base 87a7b600.',
    'A repository whose label commit already reached main out of band (status merged-unreviewed; currently Folders, '
    'through the concurrent /pushall merge f1f63909) skips the rebase and the push: list and record the main runs for '
    'its mergedCommit and for the later main head as in the next step, then regenerate and re-verify as below.',
    'Push the label commit to main. If the push is rejected, record status push-rejected with the reason in the '
    'outcomes file, regenerate this register, and halt for the user.',
    'List every main run for the pushed commit with gh run list -R Hexalith/Hexalith.<Repo> --commit <sha> and wait '
    'for each to finish. Record each run id, workflow and conclusion. If any run does not conclude success, record '
    'status ci-red, regenerate this register, and halt for the user without patching around the failure.',
    'Regenerate this register with build-labels.py --rev <repo>=<pushed sha> --outcomes <file>. This re-records the '
    'base, the pushed commit, mergedCommit, every row\'s commit, the README blob and hashes, the label and Description '
    'anchors and hashes from the pushed blobs, and mainCiRuns.',
    'Rerun verify-labels.py with --rev <repo>=<pushed sha> for every repository, against the pushed commits.',
    'Rescan this directory into a new receipt.',
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def gate_cells():
    text = (MCPCLI / ART / TECH).read_text(encoding='utf-8')
    gates = {}
    for number, line in enumerate(text.split('\n'), 1):
        match = re.match(r'^\| (PS\d\d) \|', line)
        if match:
            cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
            if len(cells) != 9:
                raise SystemExit(f'unexpected cell count at {number}')
            gates[match.group(1)] = (number, cells[7])
    if sorted(gates) != sorted(s[0] for s in SURFACES):
        raise SystemExit('PS row set mismatch')
    return gates


def bullet(surface, gates):
    ps, _repo, name, _project, inventory, extra, _csproj, _visibility = surface
    title, version, path = MODULE_INVENTORIES[inventory]
    text = (f'- {name}: removal gate "{gates[ps][1]}" ([technical-tools inventory 1.0.2]({BASE}{TECH}) {ps}; '
            f'[{title} {version}]({BASE}{path})).')
    return text + (' ' + extra if extra else '')


def locate(blob, text):
    found = [i for i, line in enumerate(blob.decode('utf-8').split('\n'), 1) if line == text]
    if len(found) != 1:
        raise SystemExit(f'expected exactly one line {text[:60]!r}, found {len(found)}')
    return found[0]


def check_outcome(repo, commit, outcome, git):
    status = outcome.get('status')
    runs = outcome.get('mainCiRuns') or []
    conclusions = [run.get('conclusion') for run in runs]
    merged = outcome.get('mergedCommit') or ''

    def ancestor(older, newer):
        return subprocess.run(['git', 'merge-base', '--is-ancestor', older, newer], cwd=git,
                              capture_output=True).returncode == 0
    if status == 'pushed':
        ok = merged == commit and runs and all(c == 'success' for c in conclusions)
    elif status == 'ci-red':
        # A red main run after our own push, or after an out-of-band merge that contains the label commit.
        reached = merged == commit or (bool(outcome.get('note')) and bool(merged) and ancestor(commit, merged)
                                       and ancestor(merged, 'origin/main'))
        ok = reached and any(c != 'success' for c in conclusions)
    elif status == 'push-rejected':
        ok = outcome.get('mergedCommit') is None and bool(outcome.get('note'))
    elif status == 'merged-unreviewed':
        ok = bool(outcome.get('note')) and bool(merged) and ancestor(commit, merged) and ancestor(merged, 'origin/main') \
            and all(c == 'success' for c in conclusions)
    else:
        ok = False
    if not ok:
        raise SystemExit(f'{repo}: outcome {status!r} is inconsistent with commit {commit} and its runs')


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n', 1)[0])
    parser.add_argument('--worktrees', required=True, type=Path)
    parser.add_argument('--path', action='append', default=[], help='<repo>=<checkout>; default <worktrees>/<repo>')
    parser.add_argument('--rev', action='append', default=[], help='<repo>=<commit>; default HEAD')
    parser.add_argument('--outcomes', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    revs = dict(item.split('=', 1) for item in args.rev)
    paths = {repo: Path(path) for repo, path in (item.split('=', 1) for item in args.path)}
    outcomes = json.loads(args.outcomes.read_text(encoding='utf-8')) if args.outcomes else {}

    def checkout(repo):
        return paths.get(repo, args.worktrees / repo)

    def git(repo, *command, binary=False):
        out = subprocess.run(['git', *command], cwd=checkout(repo), check=True, capture_output=True).stdout
        return out if binary else out.decode('utf-8').strip()

    gates = gate_cells()
    inventories = {}
    tech = (MCPCLI / ART / TECH).read_bytes()
    for key, (title, version, path) in [('technical-tools', ('technical-tools inventory', '1.0.2', TECH)),
                                        *MODULE_INVENTORIES.items()]:
        data = (MCPCLI / ART / path).read_bytes()
        pinned = subprocess.run(['git', 'show', f'{PIN}:{ART}/{path}'], cwd=MCPCLI, check=True, capture_output=True).stdout
        if pinned != data:
            raise SystemExit(f'{path} differs from the pinned commit')
        inventories[key] = {'title': title, 'version': version, 'path': f'{ART}/{path}', 'sha256': sha(data),
                            'pinnedUrl': BASE + path}

    commits = {}
    for repo in REPOS:
        commit = git(repo, 'rev-parse', revs.get(repo, 'HEAD'))
        base = git(repo, 'rev-parse', f'{commit}^')
        origin = git(repo, 'rev-parse', 'origin/main')
        message = git(repo, 'log', '-1', '--format=%B', commit, binary=True).rstrip(b'\n') + b'\n'
        readme = git(repo, 'show', f'{commit}:README.md', binary=True)
        outcome = outcomes.get(repo)
        if outcome:
            check_outcome(repo, commit, outcome, checkout(repo))
        commits[repo] = {
            'repository': GITHUB[repo],
            'branch': 'docs/mcpcli-5-5-compatibility-labels',
            'localCommit': commit,
            'base': base,
            'originMainWhenRecorded': origin,
            'baseIsOriginMain': base == origin,
            'deliveryStatus': outcome['status'] if outcome else 'pendingPush',
            'mergedCommit': outcome.get('mergedCommit') if outcome else None,
            'mainCiRuns': outcome.get('mainCiRuns') if outcome else None,
            'deliveryNote': outcome.get('note') if outcome else None,
            'changedFiles': git(repo, 'diff', '--name-only', base, commit).split('\n'),
            'subject': message.decode('utf-8').split('\n', 1)[0],
            'messageSha256': sha(message),
            'commitlint': {'result': 'found 0 problems, 0 warnings', 'validator': COMMITLINT[repo]},
            'releaseRuleCheck': {'docsCommitCutsRelease': False, 'basis': RELEASE_RULES[repo]},
            'readme': {'path': 'README.md', 'blob': git(repo, 'rev-parse', f'{commit}:README.md'), 'sha256': sha(readme),
                       'sectionHeading': {'line': locate(readme, HEADING), 'text': HEADING},
                       'sectionIntro': {'line': locate(readme, INTRO), 'sha256': sha(INTRO.encode('utf-8')), 'text': INTRO}},
        }

    rows = []
    for surface in sorted(SURFACES, key=lambda item: item[0]):
        ps, repo, name, project, inventory, extra, csproj, visibility = surface
        commit = commits[repo]['localCommit']
        text = bullet(surface, gates)
        readme = git(repo, 'show', f'{commit}:README.md', binary=True)
        line = locate(readme, text)
        gate_line, gate = gates[ps]
        statements = {
            'versionedCompatibilityBinary': 'versioned compatibility binaries' in INTRO,
            'notRetired': 'They are not retired' in INTRO,
            'outsideEveryPlatformComposition': 'stay outside every Hexalith.Platform composition' in INTRO,
            'removalGateVerbatim': f'removal gate "{gate}"' in text,
        }
        if repo == 'memories':
            statements['forwardedIdentityNecessaryNotSufficient'] = IDENTITY in text
        if ps in ('PS04', 'PS09'):
            statements['hostAndPluginRetireTogether'] = 'retire together.' in text
        if ps == 'PS05':
            statements['story54VerdictAndOpenGaps'] = ('`retirement-blocked`, with G01–G06 open' in text
                                                       and OWNER_APPROVAL in text)
        if not all(statements.values()):
            raise SystemExit(f'{ps}: missing statement {statements}')
        row = {
            'id': ps, 'repository': GITHUB[repo], 'surface': name.split('`')[1], 'project': project,
            'commit': commit, 'deliveryStatus': commits[repo]['deliveryStatus'],
            'mergedCommit': commits[repo]['mergedCommit'],
            'label': {'file': 'README.md', 'line': line, 'anchor': f'README.md:{line}', 'sha256': sha(text.encode('utf-8')),
                      'text': text, 'sectionIntroLine': commits[repo]['readme']['sectionIntro']['line']},
            'requiredStatements': statements,
            'gate': {'text': gate, 'source': f'{ART}/{TECH}:{gate_line}', 'row': ps, 'inventoryVersion': '1.0.2',
                     'inventorySha256': inventories['technical-tools']['sha256']},
            'moduleInventory': {key: inventories[inventory][key] for key in ('title', 'version', 'path', 'sha256')},
            'description': None,
        }
        if ps == 'PS05':
            approval = MCPCLI / ART / 'evidence/story-5-4-owner-approval/owner-approval.json'
            row['verdictSource'] = {'path': f'{ART}/evidence/story-5-4-owner-approval/owner-approval.json',
                                    'pinnedUrl': OWNER_APPROVAL, 'sha256': sha(approval.read_bytes())}
        if csproj:
            lines = git(repo, 'show', f'{commit}:{project}', binary=True).decode('utf-8').split('\n')
            found = [i for i, value in enumerate(lines, 1) if '<Description>' + DESCRIPTION_PREFIX in value]
            if len(found) != 1:
                raise SystemExit(f'{ps}: Description prefix not found once')
            row['description'] = {'file': project, 'line': found[0], 'anchor': f'{project}:{found[0]}',
                                  'sha256': sha(lines[found[0] - 1].encode('utf-8')), 'prefix': DESCRIPTION_PREFIX,
                                  'added': False, 'nugetVisibility': VISIBILITY[visibility]}
        rows.append(row)

    pending = [repo for repo, value in commits.items() if value['deliveryStatus'] == 'pendingPush']
    result = {
        'schema': 'mcpcli-story-5-5-labels/v1',
        'sourceSpec': f'{ART}/spec-5-5-retire-legacy-packages-and-platform-routes.md',
        'generator': f'{ART}/evidence/story-5-5/build-labels.py',
        'register': ('Authoritative register of the PS01-PS14 compatibility labels. Each of the following updates the '
                     'owning upstream label and this register, with new sources and hashes, before it counts as '
                     'complete: a versioned amendment that changes a removal gate (Stories 5.7-5.10); a change of the '
                     'Story 5.4 verdict or of the status of any of G01-G06; and a newly approved version of a cited '
                     'technical-tools or module inventory.'),
        'deliveryState': '; '.join(
            [f'pendingPush ({", ".join(pending)}): the label commit exists only on the local branch '
             'docs/mcpcli-5-5-compatibility-labels of an isolated worktree'] * bool(pending)
            + [f'{repo}: {value["deliveryStatus"]} as {value["mergedCommit"]}' + (f' ({value["deliveryNote"]})' if value['deliveryNote'] else '')
               for repo, value in commits.items() if value['deliveryStatus'] != 'pendingPush']),
        'deliveryProcedure': DELIVERY_PROCEDURE,
        'mcpcliInventoryPin': {'commit': PIN, 'onOriginMain': True},
        'labelHashDefinition': ('Label sha256 covers the exact UTF-8 label line as committed, without a line terminator. '
                                'Description sha256 covers the committed line that holds the prefix, without a line '
                                'terminator. README sha256 covers the whole committed blob after Git normalization. '
                                'messageSha256 covers the commit message as git log -1 --format=%B prints it, with its '
                                'trailing newlines collapsed to exactly one.'),
        'labelTemplate': {'heading': HEADING, 'intro': INTRO, 'descriptionPrefix': DESCRIPTION_PREFIX},
        'inventories': inventories,
        'commits': commits,
        'rows': rows,
    }
    with open(args.output, 'w', encoding='utf-8', newline='\n') as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)
        handle.write('\n')
    print('rows', len(rows), 'repositories', len(commits), 'pending', len(pending))
    return 0


if __name__ == '__main__':
    sys.exit(main())
