# Story 4.3 candidate verification

Run this entire block from the McpCli root with Python 3 and Git. It reads only
the two pinned upstream checkouts, local candidates and ordinary FrontComposer
documentation resource metadata. It never discovers or loads agent `SKILL.md`
manifests, restores packages, runs legacy tools or changes a reference checkout.

These are **candidate completeness checks**. Passing with pending approval is
intentional and cannot pass the story's final approval gate. After actual scope
approval, finalization must replace the pending-approval assertions with checks
of the recorded decision/version/authority and rerun the evidence. No static
checker supplies an external maintainer approval, package closure, Catalog
coverage, Gateway behavior, security parity or retirement readiness.

```bash
set -e
python3 - <<'PY'
from pathlib import Path
from collections import Counter
import re
import subprocess

root = Path.cwd()
base = root / '_bmad-output/implementation-artifacts'
spec_name = 'spec-4-3-approve-projects-and-frontcomposer-migration-inventories.md'
spec = (base / spec_name).read_text()
assert "status: 'draft'" in spec and '## Open Questions' in spec
assert '4-3-approve-projects-and-frontcomposer-migration-inventories: backlog' in (base / 'sprint-status.yaml').read_text()
pins = {
    'projects': ('Hexalith.Projects', '3d256e632a7645bc2261e668ac7c74be81155f58'),
    'frontcomposer': ('Hexalith.FrontComposer', '81a440a8890a17edb39924bd0cf676eb6f6b5c25'),
}
documents = {}
for module, (repo, sha) in pins.items():
    up = root / 'references' / repo
    git = lambda *args: subprocess.check_output(['git', '-C', str(up), *args], text=True).strip()
    assert git('rev-parse', 'HEAD') == sha, module
    assert not git('status', '--porcelain'), module
    text = (base / f'{module}-migration-inventory-v1.md').read_text()
    documents[module] = text
    for literal in ["inventory_version: '1.0.0-candidate.1'", 'status: draft',
                    'approval_status: pending', "approval_ref: '#a0-approval-pending'",
                    f"source_revision: '{sha}'", f"source_spec: '_bmad-output/implementation-artifacts/{spec_name}'",
                    '## A0 Approval pending']:
        assert literal in text, (module, literal)
    assert 'status: approved' not in text and 'maintainer_approval_ref:' not in text

def rows(text, widths):
    result = {}
    for line in text.splitlines():
        if not re.match(r'^\| [RMLVGHDC]\d{1,2} \|', line):
            continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        key = cells[0]
        assert key not in result, key
        assert len(cells) == widths[key[0]] and all(cells), line
        assert cells[-1] == '[A0](#a0-approval-pending)', key
        if key[0] == 'V':
            assert cells[2] == 'defer / exclude', key
        elif key[0] != 'G':
            offset = 3 if key[0] in 'LD' else 2
            assert cells[offset:offset+2] == ['defer', 'exclude'], key
        result[key] = cells
    for prefix, count in Counter(k[0] for k in result).items():
        expected = {f'{prefix}{i}' if prefix == 'G' else f'{prefix}{i:02d}' for i in range(1, count+1)}
        assert {k for k in result if k.startswith(prefix)} == expected
    return result

p = rows(documents['projects'], dict(R=8, M=8, L=8, V=6, G=4))
f = rows(documents['frontcomposer'], dict(H=8, D=8, C=8, V=6, G=4))
assert Counter(k[0] for k in p) == dict(R=11, M=5, L=18, V=12, G=6)
assert Counter(k[0] for k in f) == dict(H=3, D=13, C=2, V=8, G=4)

projects = root / 'references/Hexalith.Projects'
front = root / 'references/Hexalith.FrontComposer'
descriptor = (projects / 'src/Hexalith.Projects.Mcp/ProjectsMcpDescriptors.cs').read_text()
resource_block = descriptor.split('ResourceNames =', 1)[1].split('];', 1)[0]
resources = re.findall(r'"(projects\.[^"]+)"', resource_block)
assert len(resources) == len(set(resources)) == 11
assert resources == [p[f'R{i:02d}'][1].strip('`') for i in range(1,12)]
assert set(resources) == set(re.findall(r'Resource\("([^"]+)"', descriptor))
actions = re.findall(r'ProjectMaintenanceActions\.(\w+)', descriptor.split('MaintenanceActionNames =',1)[1].split('];',1)[0])
constants = (projects / 'src/Hexalith.Projects.Contracts/Ui/ProjectMaintenanceActionProjection.cs').read_text().split('public static class ProjectMaintenanceActions',1)[1]
tools = ['projects.' + re.search(rf'const string {name} = "([^"]+)"',constants)[1] for name in actions]
assert len(tools) == len(set(tools)) == 5
assert tools == [p[f'M{i:02d}'][1].strip('`') for i in range(1,6)]
assert 'ProtocolName: $"projects.{action}"' in descriptor
assert 'ProtocolUri: $"frontcomposer://Projects/projections/{name}"' in descriptor

parser = (projects / 'src/Hexalith.Projects.Cli/ProjectsCliParser.cs').read_text()
spellings = []
for name in ['ReadCommands', 'MutationCommands']:
    spellings += re.findall(r'"([^"]+)"', parser.split(name+' =',1)[1].split('};',1)[0])
assert 'command = "diagnostic export"' in parser
spellings.append('diagnostic export')
assert len(spellings) == len(set(spellings)) == 18
assert set(spellings) == {p[f'L{i:02d}'][1].strip('`') for i in range(1,19)}
expected_associations = ['R01','R02','R02, L02','V02','L04','R04','L06','R06',
                         'R08, R09','R10','R07','V04','V04','M01','M02','M03','M04','M05']
assert [p[f'L{i:02d}'][2] for i in range(1,19)] == expected_associations
assert '"trace-resolution" => "trace"' in parser
assert '"validate-references" => "validate"' in parser
contracts = '\n'.join(path.read_text() for path in (projects / 'src/Hexalith.Projects.Contracts').rglob('*.cs') if not {'obj','bin'} & set(path.parts))
assert not re.search(r'\[\s*(?:assembly:\s*)?Hexalith(?:Module|Command|Query)(?:Attribute)?\s*\(', contracts)

options = (front / 'src/Hexalith.FrontComposer.Mcp/FrontComposerMcpOptions.cs').read_text()
tool_name = re.search(r'LifecycleToolName.*?= "([^"]+)"',options)[1]
assert f['H01'][1].strip('`') == tool_name
registrar = (front / 'src/Hexalith.FrontComposer.Mcp/FrontComposerMcpServerOptionsConfigurator.cs').read_text()
assert 'foreach (McpResourceDescriptor descriptor in registry.Resources)' in registrar
assert 'skillProvider.CreateMcpResources()' in registrar
assert 'LifecycleUriPrefix' not in registrar
corpus = front / 'docs/skills/frontcomposer'
metadata = []
for path in sorted(corpus.rglob('*.md')):
    assert path.name != 'SKILL.md', 'Agent skills must not be inspected'
    content = path.read_text()
    doc_id = re.search(r'^id: (.+)$', content, re.M)[1].strip().strip('"\'')
    uri = re.search(r'^resourceUri: (.+)$', content, re.M)[1].strip().strip('"\'')
    assert uri.startswith('frontcomposer://skills/')
    metadata.append((doc_id,uri.removeprefix('frontcomposer://skills/')))
assert len(metadata) == len(set(metadata)) == 12
assert set(metadata) == {(f[f'D{i:02d}'][1].strip('`'),f[f'D{i:02d}'][2].strip('`')) for i in range(1,13)}
builder = (front / 'src/Hexalith.FrontComposer.Mcp/Skills/SkillCorpusAggregateManifestBuilder.cs').read_text()
provider = (front / 'src/Hexalith.FrontComposer.Mcp/Skills/FrontComposerSkillResourceProvider.cs').read_text()
assert 'frontcomposer://skills/manifest' in builder and '"skills-manifest"' in provider
assert [c.strip('`') for c in f['D13'][1:3]] == ['skills-manifest','manifest']
cli = (front / 'src/Hexalith.FrontComposer.Cli/CliApplication.cs').read_text()
assert set(re.findall(r'"(\w+)" => await \w+Command.RunAsync',cli)) == {f['C01'][1].strip('`'),f['C02'][1].strip('`')}

# Resolve every explicit path:line anchor. Shorthand :line continuations are
# contextual prose; this checks each independently named source location.
for module, text in documents.items():
    repo = pins[module][0]
    prefixes = {'Mcp':f'src/{repo}.Mcp', 'Cli':f'src/{repo}.Cli',
                'Contracts':f'src/{repo}.Contracts', 'Server':f'src/{repo}.Server',
                'Corpus':'docs/skills/frontcomposer'}
    for anchor in re.findall(r'`((?:Mcp|Cli|Contracts|Server|Corpus|src)/[^`\n]+:\d+)`',text):
        path, number = anchor.rsplit(':',1)
        if path.startswith('src/Hexalith.McpCli.'):
            location = root / path
        else:
            first, rest = path.split('/',1)
            location = root / 'references' / repo / (prefixes.get(first,first)+'/'+rest)
        lines = location.read_text().splitlines()
        assert 1 <= int(number) <= len(lines) and lines[int(number)-1].strip(), anchor
    for target in re.findall(r'\]\(([^)]+)\)',text):
        if not target.startswith('#'):
            assert (base / target.split('#',1)[0]).exists(), target

# Check that duplicate/missing rows and a wrong ordinary CLI association fail.
for damaged in [documents['projects'].replace('\n| R01 |', '\n| R02 |',1),
                '\n'.join(line for line in documents['projects'].splitlines() if not line.startswith('| R01 |'))]:
    try:
        candidate = rows(damaged,dict(R=8,M=8,L=8,V=6,G=4))
        assert Counter(k[0] for k in candidate) == dict(R=11,M=5,L=18,V=12,G=6)
    except AssertionError:
        pass
    else:
        raise AssertionError('Malformed inventory was accepted')
wrong = [*expected_associations]
wrong[0],wrong[1] = wrong[1],wrong[0]
assert [p[f'L{i:02d}'][2] for i in range(1,19)] != wrong
print('PASS: exact pins, clean sources, 34 Projects surfaces, host families, lifecycle, 13 documents, 2 compiler leaves, row references and source anchors.')
print('Approval pending: candidates are not approved; Story 4.3 remains incomplete.')
PY
git diff --check
```

No .NET build is required for this Markdown-only preparation. The historical
September inventory, runtime, dependency policy, upstream checkouts and sprint
status stay unchanged until the applicable approval/implementation transition.
