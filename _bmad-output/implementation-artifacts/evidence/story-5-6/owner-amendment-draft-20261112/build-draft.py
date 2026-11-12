"""Build the census 1.0.3 owner-amendment draft from the final-2 report; nothing here grants approval.

Every pick names its exact expected identities, kinds and signals, every "already
approved" claim is checked against the active policy, and every exclusion hash is
read from the committed blob at the report's root pin. Any mismatch stops the build.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
V1 = ROOT / 'tools/proprietary-surfaces/v1'
REPORT = ROOT / '_bmad-output/implementation-artifacts/evidence/story-5-6/guard-excuse-review-20261111/runs/final-2/census.json'
canonical = lambda value: json.dumps(value, sort_keys=True, separators=(',', ':'))
sha = lambda raw: hashlib.sha256(raw).hexdigest()
git = lambda repo, *args: subprocess.run(['git', '-C', str(repo), *args], check=True, capture_output=True).stdout


def fail(message):
    sys.exit(f'draft-build-refused: {message}')


report = json.loads(REPORT.read_text())
pins = {row['repository']: row['gitlink'] for row in report['repositories']}
# The draft binds committed bytes at the report's pins; they must still be the parent's pins.
if report['parentRevision'] != git(ROOT, 'rev-parse', 'HEAD').decode().strip():
    fail('report parent revision is not HEAD')
for repository, gitlink in pins.items():
    if git(ROOT, 'ls-tree', 'HEAD', repository).decode().split()[2] != gitlink:
        fail(f'{repository} gitlink moved since the report')

# Active policy: baseline plus every indexed amendment, in order.
policy = json.loads((V1 / 'baseline.json').read_text())
active = list(policy['allowances'])
exclusion_rows = list(policy['exclusions'])
for item in json.loads((V1 / 'amendments.json').read_text()):
    raw = (V1 / item['path']).read_bytes()
    if sha(raw) != item['sha256']:
        fail(f'{item["path"]} does not match its index hash')
    amendment = json.loads(raw)
    removed = {canonical(surface) for surface in amendment['removeAllowances']}
    active = [entry for entry in active if canonical(entry['surface']) not in removed] + amendment['addAllowances']
    exclusion_rows += amendment.get('addExclusions', [])

rejected = {(s['surface']['repository'], s['surface']['path'], s['surface']['kind'], s['surface']['identity']): s
            for s in report['surfaces'] if s['status'] == 'rejected'}
owner = lambda repository: repository.split('/')[-1] + ' owning maintainer'
add, remove, exclusions = [], [], []


def same_path(repository, path, rows):
    """Require an active allowance on the same file with one of these rows; return it."""
    found = [entry for entry in active if entry['surface']['repository'] == repository
             and entry['surface']['path'] == path and entry['row'] in rows]
    if not found:
        fail(f'no active {rows} allowance on {repository} {path}')
    return found


def take(repo, path, kind, identity, signals):
    key = ('references/Hexalith.' + repo, path, kind, identity)
    if key not in rejected or sorted(rejected[key]['signals']) != sorted(signals):
        fail(f'unexpected rejected observation for {key}')
    rejected.pop(key)
    return key


def allow(key, row, classification, reason):
    signals = sorted(rejected_signals[key])
    add.append({'surface': dict(zip(('repository', 'path', 'kind', 'identity'), key)), 'row': row,
                'classification': classification, 'owner': owner(key[0]), 'reason': reason, 'signals': signals})


rejected_signals = {key: value['signals'] for key, value in rejected.items()}

# G4: package identities of approved PS compatibility projects (PS01, PS10).
for repo, path, identity, ps in [
        ('EventStore', 'src/Hexalith.EventStore.Admin.Cli/Hexalith.EventStore.Admin.Cli.csproj', 'package:Hexalith.EventStore.Admin.Cli', 'PS01'),
        ('Folders', 'src/Hexalith.Folders.Cli/Hexalith.Folders.Cli.csproj', 'package:Hexalith.Folders.Cli', 'PS10')]:
    same_path('references/Hexalith.' + repo, path, {ps})
    same_path('references/Hexalith.' + repo, path, {'G4'})
    allow(take(repo, path, 'publication', identity, ['package-metadata']), 'G4', 'compatibility-publication-or-route',
          f'Effective package identity of the approved {ps} compatibility project on this file, which already has approved '
          f'{ps} and G4 allowances; it stays a labeled compatibility publication until its retirement gate. Exact identity only.')
# G4: other identity spellings on Memories files whose approved G4 allowances route the Memories PS surfaces.
for path, identity, signals in [
        ('deploy/kubernetes/overlays/production/kustomization.yaml', 'registry.hexalith.com/memories-mcp', ['container-image']),
        ('tools/release-containers.json', 'mcp', ['publication-entry']),
        ('tools/verify-cli-pack.sh', 'src/Hexalith.Memories.Cli/Hexalith.Memories.Cli.csproj', ['project-publication-reference'])]:
    same_path('references/Hexalith.Memories', path, {'G4'})
    allow(take('Memories', path, 'publication', identity, signals), 'G4', 'compatibility-publication-or-route',
          'Another identity spelling on a file whose approved G4 compatibility-publication allowance routes a Memories PS '
          'surface; it stays a labeled compatibility publication until its retirement gate. Exact identity only.')
# PE01: Builds build tooling and the hexalith-module pack templates that row PE01 names.
for identity in ('HexalithApp/src/HexalithApp.ApiServer/HexalithApp.ApiServer.csproj',
                 'HexalithApp/src/HexalithApp.WebServer/HexalithApp.WebServer.csproj'):
    allow(take('Builds', 'Github/publish-container-to-registry/action.yml', 'publication', identity, ['orphan-project-reference']),
          'PE01', 'exempt-build-publication',
          "Builds publish-container-to-registry composite action: a CI template that publishes a consumer's HexalithApp "
          'API/Web server containers from that consumer\'s HexalithApp checkout; build tooling that invokes no module '
          'operation. Exact identity only.')
for template, identity in (('EventStore', 'package:Hexalith.Builds.Module.EventStoreHost'), ('Ui', 'package:Hexalith.Builds.Module.UiHost')):
    path = f'src/libraries/Hexalith.Builds.Module.Cli/pack/projects/{template}/Host.csproj'
    same_path('references/Hexalith.Builds', path, {'PE01'})
    allow(take('Builds', path, 'publication', identity, ['package-metadata']), 'PE01', 'exempt-build-publication',
          'Package identity of a hexalith-module pack template that inventory row PE01 names and that already has an '
          'approved PE01 allowance on this file. Exact identity only.')
# PE03: owner decision 2026-11-12, "Add as PE03 tooling".
allow(take('Platform', 'src/Hexalith.Platform.Composition/Hexalith.Platform.Composition.csproj', 'project',
           'Hexalith.Platform.Composition', ['executable-project']), 'PE03', 'platform-qualification-tooling',
      'Became an executable after inventory approval (Platform 3ad2f29a): a non-packable PlatformSourceStateWorker that '
      'reads a JSON path list on stdin and prints a source-state hash. No System.CommandLine, MCP package or tool '
      'packing; classified PE03 by the Platform owner on 2026-11-12. Exact identity and signal set only.')
# PE05: test and performance fixtures.
fixture = 'test/fixtures/release/Container/Release.Container.csproj'
for kind, identity, signals, classification in (('project', 'Release.Container', ['executable-project'], 'test-fixture'),
        ('publication', 'container:hexalith-release-create-disposable', ['container-metadata'], 'test-fixture-observation')):
    allow(take('Builds', fixture, kind, identity, signals), 'PE05', classification,
          'Disposable Builds release-create test fixture: its hosted test runs build it into draft releases that are '
          'deleted afterwards; it is not a shipped surface. Exact identity only.')
seed = 'scripts/run-tenant-audit-performance.sh'
same_path('references/Hexalith.Tenants', seed, {'PE05'})
allow(take('Tenants', seed, 'publication', 'tests/performance/tenant-audit/seed.csproj', ['project-publication-reference']),
      'PE05', 'performance-fixture-driver',
      'Full-path spelling of the tenant-audit performance seed driver that already has an approved PE05 allowance on '
      'this script. Exact identity only.')
chatbot_path = 'tests/Hexalith.ChatBot.Mcp.Tests/Hexalith.ChatBot.Mcp.Tests.csproj'
previous = [entry for entry in same_path('references/Hexalith.ChatBot', chatbot_path, {'PE05'})
            if entry['surface']['kind'] == 'project' and entry['signals'] == ['mcp-or-cli-dependency', 'project-identity']]
if len(previous) != 1:
    fail('the approved ChatBot Mcp.Tests allowance is not the expected single entry')
remove.append(previous[0]['surface'])
allow(take('ChatBot', chatbot_path, 'project', 'Hexalith.ChatBot.Mcp.Tests',
           ['mcp-or-cli-dependency', 'mcp-registration', 'project-identity']), 'PE05', 'test-fixture',
      'Replacement of the approved PE05 test-fixture allowance: tests/Hexalith.ChatBot.Mcp.Tests/ChatBotMcpServiceTests.cs '
      'adds an MCP registration signal inside the test project of the PS ChatBot MCP surface. Test fixture only; exact '
      'identity and signal set.')
# PE06: servers-section stdio entries that launch Microsoft's locally installed fluentui-mcp tool.
for repo, digest_value in (('ChatBot', '3c0ffdb9f97e6cedfbc5bc45acefe323575ae2f944c1c5ea2162214b0b3cd9bc'),
                           ('Folders', '889bfe4f3883a9628ad171a38d6baad10f088a1a0de76811a43e1f77c1c9e118'),
                           ('Projects', '4950609ec82e4efc8932b7079093494e61c0355bb1446529ee1f64d0f978e978'),
                           ('Timesheets', '889bfe4f3883a9628ad171a38d6baad10f088a1a0de76811a43e1f77c1c9e118')):
    repository = 'references/Hexalith.' + repo
    entry = json.loads(git(ROOT / repository, 'show', pins[repository] + ':.mcp.json'))['servers']['fluent-ui-blazor']
    if sha(canonical(entry).encode()) != digest_value or entry.get('command') != 'fluentui-mcp':
        fail(f'{repo} .mcp.json servers entry is not the expected fluentui-mcp command')
    allow(take(repo, '.mcp.json', 'configuration', 'fluent-ui-blazor:' + digest_value, ['developer-server-configuration']),
          'PE06', 'external-developer-configuration',
          'servers-section stdio entry that launches the locally installed fluentui-mcp command (the .NET tool '
          'microsoft.fluentui.aspnetcore.mcpserver, Microsoft Fluent UI Blazor MCP server); an external developer MCP '
          'server, not a Hexalith surface. Exact configuration identity only.')
# PE09: package identity of the approved Memories evidence tool.
bench = 'tools/GenerateBenchmarkVectors/GenerateBenchmarkVectors.csproj'
same_path('references/Hexalith.Memories', bench, {'PE09'})
allow(take('Memories', bench, 'publication', 'package:GenerateBenchmarkVectors', ['package-metadata']),
      'PE09', 'qualification-evidence-tooling',
      'Package identity of the GenerateBenchmarkVectors evidence tool, which already has an approved PE09 allowance on '
      'this project. Exact identity only.')
# PN09: the EventStore image pinned in seven retained Platform operator-setup packets.
image = 'registry.hexalith.com/eventstore@sha256:c14074f08cf990072912dd6284fc253a900f6a020a0cd11008195aa357528eed'
for packet in ('packet-20261031', 'packet-20261031-dns-review', 'packet-20261031-final', 'packet-20261031-gateway-api-review',
               'packet-20261031-recovery-final', 'packet-20261031-recovery-review', 'packet-20261031-review'):
    allow(take('Platform', f'eng/mcpcli-operator-setup/v1/{packet}/eventstore.yaml', 'publication', image, ['container-image']),
          'PN09', 'domain-service-publication',
          'EventStore domain-service image pinned by digest in a retained 2026-10-31 operator-setup packet; not an MCP '
          'or CLI surface. Same class as the approved Platform Timesheets image. Exact identity only.')
# PE07: the Conversations preparation-only proposal, excluded by its exact blob hash.
conversations = 'references/Hexalith.Conversations'
proposal = 'docs/release-evidence/conformance-oracle-tiering-eventstore-repair-v7-proposal.json'
hidden = ('Hexalith.EventStore.Client', 'Hexalith.EventStore.Contracts', 'Hexalith.EventStore.DomainService',
          'Hexalith.EventStore.ServiceDefaults')
for identity in hidden:
    take('Conversations', proposal, 'publication', identity, ['publication-entry'])
exclusions.append({'repository': conversations, 'prefix': proposal, 'row': 'PE07', 'classification': 'captured-evidence',
    'owner': owner(conversations), 'reason': 'Exact retained story 9.2 repair proposal marked preparation-only with no '
    'acceptance claimed: captured evidence whose package list (' + ', '.join(hidden) + ') names EventStore packages, '
    'not a Conversations publication manifest.', 'scope': 'file',
    'sha256': sha(git(ROOT / conversations, 'show', pins[conversations] + ':' + proposal))})
# PE07: refreshed bytes of the approved Builds audit snapshot; owner decision 2026-11-12, "Checker fix + new version".
builds, audit = 'references/Hexalith.Builds', 'Tools/package-version-audit.json'
approved = [row for row in exclusion_rows if row['repository'] == builds and row['prefix'] == audit]
drifted = [error for error in report['errors'] if error['repository'] == builds
           and error.get('rule') == 'excluded-fixture-source-drift:' + audit]
if len(approved) != 1 or len(drifted) != 1:
    fail('the Builds audit snapshot is not the single approved, drifted exclusion')
exclusions.append({'repository': builds, 'prefix': audit, 'row': approved[0]['row'],
    'classification': approved[0]['classification'], 'owner': owner(builds),
    'reason': 'Refreshed byte version of the approved retained package audit snapshot at the current Builds pin; '
    'approved captured-evidence scope, not a publication manifest.', 'scope': 'file',
    'sha256': sha(git(ROOT / builds, 'show', pins[builds] + ':' + audit))})

if rejected:
    fail('rejected observations left without a decision: ' + canonical(sorted(rejected)))
authorization = {'addAllowances': add, 'removeAllowances': remove, 'addExceptions': [], 'removeExceptions': [],
                 'addExclusions': exclusions}
(OUT / 'authorization.draft.json').write_text(json.dumps(authorization, indent=2, sort_keys=True) + '\n')
(OUT / 'not-included.json').write_text('[]\n')
print('allowances', len(add), 'removals', len(remove), 'exclusions', len(exclusions))
print('authorization canonical sha256', sha(canonical(authorization).encode()))
