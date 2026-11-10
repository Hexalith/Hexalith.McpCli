#!/usr/bin/env python3
"""Story 5.5 Platform composition census.

Runs read-only `git grep` against a Platform revision (default: the already-fetched origin/main), classifies every
hit and fails closed on an unclassified hit, an unresolved composition-area hit, or a declaration, tool manifest or
module manifest that names a PS surface. Usage:

    python3 platform-census.py --platform <platform checkout> --owners <dir of owner checkouts> --output <json>
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys

PROJECTS = {
    'PS01': 'Hexalith.EventStore.Admin.Cli', 'PS02': 'Hexalith.EventStore.Admin.Mcp',
    'PS03': 'Hexalith.FrontComposer.Cli', 'PS04': 'Hexalith.FrontComposer.Mcp',
    'PS05': 'Hexalith.Parties.Mcp', 'PS06': 'Hexalith.Memories.Cli', 'PS07': 'Hexalith.Memories.Mcp',
    'PS08': 'Hexalith.Projects.Cli', 'PS09': 'Hexalith.Projects.Mcp', 'PS10': 'Hexalith.Folders.Cli',
    'PS11': 'Hexalith.Folders.Mcp', 'PS12': 'Hexalith.ChatBot.Cli', 'PS13': 'Hexalith.ChatBot.Mcp',
    'PS14': 'MigrateEmbeddingVectors',
}
CONTAINERS = {'PS05': 'parties-mcp', 'PS07': 'memories-mcp'}
TOOL_COMMANDS = {'PS01': 'eventstore-admin', 'PS03': 'frontcomposer', 'PS06': 'memories', 'PS10': 'folders'}
# eventstore-admin is distinctive and is enumerated as a fixed string. The other three command names
# collide with module, server and directory names, so they are enumerated in invocation, installation
# and tool-manifest form; their bare-word composition-area occurrences are reported per file.
COMMAND_FORM = (r'(dotnet[ -]tool[ ]+(install|update|run|exec|restore)|dnx)[^|]*\b(eventstore-admin|frontcomposer|memories|folders)\b'
                r'|(^|[[:space:]`"\'(])(frontcomposer[[:space:]]+(inspect|migrate)'
                r'|memories[[:space:]]+(case|config|consistency|export|handlers|inspect|list|lookup|query|quickstart|repair|search|show|status|telemetry|tenant|verify|--version|--format|--help)'
                r'|folders[[:space:]]+(audit|commit|context|file|folder|provider|workspace|--version|--help|--format))\b')
OWNERS = {'references/Hexalith.EventStore': 'eventstore', 'references/Hexalith.Parties': 'parties',
          'references/Hexalith.Memories': 'memories', 'references/Hexalith.Projects': 'projects',
          'references/Hexalith.FrontComposer': 'frontcomposer', 'references/Hexalith.Folders': 'folders',
          'references/Hexalith.ChatBot': 'chatbot'}
EXCLUSIONS = {
    'references/**': None,  # reason built from the gitlinks below
    '**/evidence/**': 'Captured evidence (out of scope by spec).',
    'docs/implementation/**': 'Dated implementation evidence snapshots (source manifests, verification captures, installation observations); captured artifacts that ship nothing, as technical-tools inventory PE07 records.',
}
COMPOSITION_AREAS = ('apphost.cs', 'apphost.run.json', 'hexalith-platform.json', 'src/', 'deploy/',
                     'infrastructure/', 'templates/', 'DaprComponents/', 'config/')
PREVIEW = 'src/Hexalith.Platform.Composition/WorksPreviewModel.cs'
ADMIN_ACL = 'DaprComponents/accesscontrol.eventstore-admin.yaml'
ADMIN_SERVER = ('Dapr app ID and Aspire resource name eventstore-admin of EventStore Admin.Server '
                '(Hexalith.EventStore.Admin.Server.Host), not the PS01 eventstore-admin .NET tool')
APP_ID_EVIDENCE = [(PREVIEW, 48, 'Hexalith.EventStore.Admin.Server.Host.csproj'),
                   (PREVIEW, 166, 'AddProject("eventstore-admin", adminProject)')]
# Composition-area hit -> (resolving identity, evidence anchors that must contain the given text).
RESOLUTIONS = {
    (ADMIN_ACL, 4): ('ACL configuration loaded only by the Admin.Server sidecar', [(ADMIN_ACL, 1, 'for the Admin.Server sidecar')]),
    (ADMIN_ACL, 10): ('Dapr Configuration name of the Admin.Server sidecar ACL', [(ADMIN_ACL, 1, 'for the Admin.Server sidecar')]),
    ('DaprComponents/accesscontrol.eventstore-operations.yaml', 17): (
        'Caller policy for Admin.Server, the only caller allowed to query or mutate retained items',
        [('DaprComponents/accesscontrol.eventstore-operations.yaml', 2, 'Only Admin.Server may query or mutate')]),
    ('DaprComponents/accesscontrol.works.yaml', 57): ('Caller policy for the Admin.Server app ID', APP_ID_EVIDENCE),
    ('DaprComponents/accesscontrol.yaml', 53): (
        'Caller policy for Admin.Server on the EventStore receiver',
        [('DaprComponents/accesscontrol.yaml', 51, 'binds Admin.Server to its selected Admin API')]),
    ('DaprComponents/statestore.yaml', 30): ('State-store scope for the Admin.Server app ID', APP_ID_EVIDENCE),
    ('DaprComponents/reference/statestore.yaml', 30): (
        'State-store scope for the Admin.Server app ID in the reference composition',
        [(ADMIN_ACL, 4, 'Loaded only by the eventstore-admin sidecar; governs which CALLERS may invoke Admin.Server')]),
    ('config/works-production-profile.schema.json', 15): (
        'Production operator caller: the Admin.Server app ID',
        [(PREVIEW, 238, '"EventStoreOperations__AdminCallerAppId", "eventstore-admin"'), *APP_ID_EVIDENCE]),
    ('src/Hexalith.Platform.Composition/WorksProductionProfile.cs', 56): (
        'Production operator caller: the Admin.Server app ID',
        [(PREVIEW, 238, '"EventStoreOperations__AdminCallerAppId", "eventstore-admin"'), *APP_ID_EVIDENCE]),
    (PREVIEW, 79): ('ACL file of the Admin.Server sidecar', [(ADMIN_ACL, 1, 'for the Admin.Server sidecar')]),
    (PREVIEW, 166): ('Aspire project resource for Admin.Server.Host', [APP_ID_EVIDENCE[0]]),
    (PREVIEW, 190): ('Allowed workload caller: the Admin.Server app ID', APP_ID_EVIDENCE),
    (PREVIEW, 238): ('Admin caller app ID for the operations workload: the Admin.Server app ID', APP_ID_EVIDENCE),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n', 1)[0])
    parser.add_argument('--platform', required=True)
    parser.add_argument('--owners', required=True, help='directory holding the owner checkouts named in OWNERS')
    parser.add_argument('--revision', default='origin/main')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()

    def git(*command, cwd=args.platform):
        return subprocess.run(['git', *command], cwd=cwd, check=True, capture_output=True, text=True).stdout

    revision = git('rev-parse', args.revision).strip()

    def grep(options, pathspec):
        result = subprocess.run(['git', 'grep', '-n', '-z', '-I', *options, revision, '--', *pathspec], cwd=args.platform,
                                capture_output=True, text=True, encoding='utf-8', errors='surrogateescape')
        if result.returncode not in (0, 1):
            raise SystemExit(result.stderr)
        hits, prefix = [], revision + ':'
        for raw in result.stdout.split('\n'):
            if raw:
                path, line, text = raw.split('\0', 2)
                if not path.startswith(prefix):
                    raise SystemExit('unexpected git grep record')
                hits.append((path[len(prefix):], int(line), text))
        return hits

    def blob_lines(path):
        return git('show', f'{revision}:{path}').split('\n')

    fixed = [('-i', '-F', '-e', name) for name in PROJECTS.values()] + [('-F', '-e', name) for name in CONTAINERS.values()] \
        + [('-F', '-e', 'eventstore-admin')]
    searches = [(list(options), options[-1]) for options in fixed] + [(['-E', '-e', COMMAND_FORM], '<tool-command-form>')]

    def collect(pathspec):
        found = {}
        for options, term in searches:
            for path, line, text in grep(options, pathspec):
                found.setdefault((path, line), {'text': text, 'terms': set()})['terms'].add(term)
        return found

    exclude = [f':(exclude){pattern}' for pattern in EXCLUSIONS]
    hits, unclassified, composition, unresolved = [], [], [], []
    for (path, line), entry in sorted(collect(['.', *exclude]).items()):
        terms, text = entry['terms'], entry['text']
        record = {'path': path, 'line': line, 'terms': sorted(terms),
                  'lineSha256': hashlib.sha256(text.encode('utf-8')).hexdigest()}
        named = terms - {'<tool-command-form>'}
        if path == '_bmad-output/planning-artifacts/architecture/architecture-platform-2026-09-27/ARCHITECTURE-SPINE.md':
            verdict = ('governing-decision', 'AD-11 legacy-surfaces rule: names the surfaces only to keep them out of every Platform composition.')
        elif path.startswith('_bmad-output/') and not named:
            verdict = ('planning-or-review-record', 'Story text quoting a `dotnet tool run hexalith-module` invocation; the match is the word memories in its manifest path, not the memories tool.')
        elif path.startswith('_bmad-output/'):
            verdict = ('planning-or-review-record', 'Planning, architecture-review, story or ledger text that names a surface; not a composition input.')
        elif named == {'parties-mcp'} and path == 'tests/Hexalith.Platform.Composition.Tests/PartiesAdoptionTests.cs':
            verdict = ('negative-assertion', 'Asserts the composed server set does not contain parties-mcp.')
        elif named == {'memories-mcp'} and re.match(r'eng/(cluster-management|kubernetes-upgrade|timesheets-deployment)/', path):
            verdict = ('existing-cluster-runbook', 'Operator runbook record naming the existing cluster Deployment memories-mcp, which Memories deploys with its own manifests; Platform does not enroll, deploy, route or map it.')
        elif named == {'memories-mcp'} and path.startswith('eng/recovery-preparation/'):
            verdict = ('existing-cluster-observation', 'Synthetic-only, read-only measurement plan (no live entry point) that observes the existing cluster Deployment memories-mcp; it does not enroll, deploy, route or map it.')
        elif named == {'eventstore-admin'} and '<tool-command-form>' not in terms:
            # A line that also matches the tool-command form invokes or installs the PS01 tool, so it stays unclassified.
            verdict = ('admin-server-dapr-identity', 'eventstore-admin is the Dapr app ID, resource name or workload identity of EventStore Admin.Server (Hexalith.EventStore.Admin.Server.Host), not the PS01 eventstore-admin .NET tool.')
        else:
            unclassified.append(record)
            continue
        record['classification'], record['reason'] = verdict
        if path.startswith(COMPOSITION_AREAS):
            record['excerpt'] = text
            resolution = RESOLUTIONS.get((path, line)) if verdict[0] == 'admin-server-dapr-identity' else None
            if resolution is None:
                composition.append(record)
            else:
                identity, evidence = resolution
                anchors = []
                for evidence_path, evidence_line, needle in evidence:
                    if needle not in blob_lines(evidence_path)[evidence_line - 1]:
                        unresolved.append(f'{path}:{line} evidence {evidence_path}:{evidence_line}')
                    anchors.append({'anchor': f'{evidence_path}:{evidence_line}', 'contains': needle})
                record['resolvingIdentity'] = {'identity': f'{identity}; {ADMIN_SERVER}', 'evidence': anchors}
        hits.append(record)

    gitlinks = {}
    for row in git('ls-tree', revision, 'references/').splitlines():
        _mode, _kind, sha, path = row.split(None, 3)
        gitlinks[path] = sha
    unchecked = sorted(path for path in gitlinks if path not in OWNERS)
    reasons = dict(EXCLUSIONS)
    reasons['references/**'] = (
        'Root-declared submodules, recorded as gitlinks that git grep at a revision does not enter; excluded by spec. '
        'Only the module manifests at the gitlinks of the seven PS-owning repositories are checked below '
        f'({", ".join(sorted(OWNERS))}); the other {len(unchecked)} references are not read ({", ".join(unchecked)}).')
    excluded = {}
    for pattern, reason in reasons.items():
        pairs = collect([pattern])
        excluded[pattern] = {'reason': reason, 'files': len({path for path, _ in pairs}), 'lineHits': len(pairs)}

    bare = {}
    areas = [area if area.endswith(('.cs', '.json')) else area + '**' for area in COMPOSITION_AREAS]
    for ps, word in TOOL_COMMANDS.items():
        if word == 'eventstore-admin':
            continue
        files = {}
        for path, _line, _text in grep(['-w', '-F', '-e', word], areas):
            files[path] = files.get(path, 0) + 1
        bare[word] = {'surface': ps, 'compositionAreaFiles': [{'path': p, 'lineHits': n} for p, n in sorted(files.items())]}
    bare['memories']['classification'] = 'memories-module-identity'
    bare['memories']['reason'] = ('Every composition-area occurrence names the Memories module, its declared servers (memories, '
                                  'memories-access-telemetry, memories-access-telemetry-clock, memories-domain-service), their Dapr '
                                  'components, configuration keys, container images, embedding client or package-cohort names; none '
                                  'installs, invokes or routes the memories CLI, whose package identity Hexalith.Memories.Cli and '
                                  'invocation forms have no hit.')
    for word in ('frontcomposer', 'folders'):
        bare[word]['classification'] = 'none' if not bare[word]['compositionAreaFiles'] else 'review-required'

    manifest = json.loads(git('show', f'{revision}:.config/dotnet-tools.json'))
    declarations = {}
    for path in git('ls-tree', '--name-only', f'{revision}:src/Hexalith.Platform.Composition/Declarations').split():
        if path.endswith('.json'):
            data = json.loads(git('show', f'{revision}:src/Hexalith.Platform.Composition/Declarations/{path}'))
            servers = sorted({s.get('appId') for m in data.get('modules', []) for s in m.get('identity', {}).get('servers', [])} - {None})
            if servers:
                declarations[path] = servers
    ps_ids = {*CONTAINERS.values(), *(name.lower() for name in PROJECTS.values())}
    declared_ps = sorted(s for servers in declarations.values() for s in servers if s.lower() in ps_ids)

    pattern = re.compile('|'.join(re.escape(n) for n in [*PROJECTS.values(), *CONTAINERS.values()]), re.I)
    module_manifests = []
    for reference, repo in OWNERS.items():
        sha = gitlinks[reference]
        names = [n for n in git('ls-tree', '-r', '--name-only', sha, 'module/', cwd=f'{args.owners}/{repo}').split()
                 if n.endswith('.json') and 'manifest' in n]
        for name in names:
            blob = subprocess.run(['git', 'show', f'{sha}:{name}'], cwd=f'{args.owners}/{repo}', check=True,
                                  capture_output=True).stdout
            module_manifests.append({'reference': reference, 'gitlink': sha, 'path': name,
                                     'sha256': hashlib.sha256(blob).hexdigest(),
                                     'psSurfaceMentions': len(pattern.findall(blob.decode('utf-8')))})
        if not names:
            module_manifests.append({'reference': reference, 'gitlink': sha, 'path': None, 'psSurfaceMentions': 0,
                                     'note': 'No module manifest at this gitlink.'})

    spine = '_bmad-output/planning-artifacts/architecture/architecture-platform-2026-09-27/ARCHITECTURE-SPINE.md'
    ad11 = blob_lines(spine)[183]
    result = {
        'schema': 'mcpcli-story-5-5-platform-census/v1',
        'generator': '_bmad-output/implementation-artifacts/evidence/story-5-5/platform-census.py',
        'platformRepository': 'https://github.com/Hexalith/Hexalith.Platform',
        'platformRevision': revision,
        'revisionSource': 'already-fetched origin/main in the local Platform checkout; no fetch, worktree or checkout change',
        'governingDecision': {'path': spine, 'line': 184, 'lineSha256': hashlib.sha256(ad11.encode('utf-8')).hexdigest(),
                              'startsWith': ad11[:42], 'startsWithNote': 'exact leading characters, including the two-space indent'},
        'method': {
            'command': 'git grep -n -z -I <terms> <platformRevision> -- . <exclusions>',
            'projectIdentities': PROJECTS,
            'projectMatch': 'fixed string, case-insensitive (package IDs appear lowercase in tool manifests)',
            'containerNames': CONTAINERS,
            'toolCommands': TOOL_COMMANDS,
            'toolCommandMatch': 'eventstore-admin as a fixed string; frontcomposer, memories and folders in invocation, installation and tool-manifest form (extended regex below), plus per-file bare-word counts in composition areas',
            'toolCommandFormRegex': COMMAND_FORM,
            'compositionAreas': list(COMPOSITION_AREAS),
            'hitDefinition': 'one deduplicated (path, line) pair per matching line, whatever the number of terms it matches',
        },
        'exclusions': excluded,
        'exclusionCountDefinition': 'files: distinct paths; lineHits: deduplicated (path, line) pairs matching any census term (all fixed terms and the tool-command form) inside that exclusion alone',
        'hitCount': len(hits),
        'hits': hits,
        'unclassified': unclassified,
        'compositionHits': composition,
        'unresolvedEvidence': unresolved,
        'bareToolCommandWords': bare,
        'toolManifest': {'path': '.config/dotnet-tools.json', 'tools': sorted(manifest.get('tools', {})),
                         'psTools': sorted(t for t in manifest.get('tools', {}) if t in {n.lower() for n in PROJECTS.values()})},
        'declaredServers': {'source': 'src/Hexalith.Platform.Composition/Declarations/*.json', 'byDeclaration': declarations,
                            'psSurfaces': declared_ps},
        'moduleManifestsAtPlatformGitlinks': {
            'source': 'read with git show from each PS-owning repository object store at the Platform gitlink (read-only)',
            'scope': f'the seven PS-owning references only; not read: {", ".join(unchecked)}',
            'manifests': module_manifests,
        },
    }
    failures = []
    if unclassified:
        failures.append(f'{len(unclassified)} unclassified hit(s)')
    if composition:
        failures.append(f'{len(composition)} composition-area hit(s) without a resolved name-only identity')
    if unresolved:
        failures.append(f'{len(unresolved)} resolving-evidence anchor(s) do not hold the expected text')
    if declared_ps or result['toolManifest']['psTools'] or any(m['psSurfaceMentions'] for m in module_manifests):
        failures.append('a declaration, tool manifest or module manifest names a PS surface')
    if any(v.get('classification') == 'review-required' for v in bare.values()):
        failures.append('bare tool-command word in a composition area needs review')
    result['verdict'] = 'halt' if failures else 'no-platform-composition-of-a-ps-surface'
    result['failures'] = failures
    with open(args.output, 'w', encoding='utf-8', newline='\n') as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)
        handle.write('\n')
    print(result['verdict'], len(hits), 'hits', failures)
    for record in unclassified + composition:
        print('REVIEW', record['path'], record['line'], record['terms'])
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
