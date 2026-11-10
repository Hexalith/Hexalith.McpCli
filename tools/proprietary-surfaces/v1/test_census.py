"""Disposable committed Git trees exercise census acceptance and refusal paths."""
import contextlib
import copy
from datetime import date
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('census', Path(__file__).with_name('check.py'))
census = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(census)
TODAY = date(2026, 11, 10)
PROJECT = 'odd/location/Runner/Runner.csproj'


class CensusTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root / 'references/opaque'
        self.repo.mkdir(parents=True)
        self.git(self.root, 'init', '-q')
        self.git(self.repo, 'init', '-q')
        self.write(self.repo, 'ordinary.txt', 'committed\n')
        self.commit(self.repo)
        self.write(self.root, '.gitmodules', '[submodule "opaque"]\n path = references/opaque\n url = https://example.invalid/opaque.git\n')
        self.write(self.root, 'inventory.txt', 'immutable inventory\n')
        self.write(self.root, 'approval.json', '{"decision":"approved"}\n')
        self.pin()
        self.baseline = self.root / 'policy/baseline.json'
        self.index = self.baseline.with_name('amendments.json')
        self.policy = {
            'schema': census.SCHEMA, 'version': '1.0.0',
            'provenance': [{'path': p, 'sha256': census.digest((self.root / p).read_bytes())} for p in ('inventory.txt', 'approval.json')],
            'roots': [{'repository': 'references/opaque', 'gitlink': self.git(self.repo, 'rev-parse', 'HEAD'), 'classification': 'PN01', 'owner': 'fixture owner'}],
            'allowances': [], 'exclusions': [], 'exceptions': [], 'toolIdentities': [],
        }
        self.save()

    def git(self, repo, *args):
        result = subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', '-c', 'user.name=Census Fixture',
            '-c', 'user.email=census@example.invalid', '-C', str(repo), *args], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, (args, result.stderr))
        return result.stdout.strip()

    def write(self, root, path, text):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')

    def commit(self, repo):
        self.git(repo, 'add', '--all')
        self.git(repo, 'commit', '-q', '--allow-empty', '-m', 'test: construct census fixture')
        return self.git(repo, 'rev-parse', 'HEAD')

    def pin(self):
        sha = self.git(self.repo, 'rev-parse', 'HEAD')
        self.git(self.root, 'add', '.gitmodules', 'inventory.txt', 'approval.json')
        self.git(self.root, 'update-index', '--add', '--cacheinfo', f'160000,{sha},references/opaque')
        self.git(self.root, 'commit', '-q', '--allow-empty', '-m', 'test: pin census fixture')
        return sha

    def save(self):
        self.baseline.parent.mkdir(exist_ok=True)
        self.baseline.write_text(json.dumps(self.policy, indent=2) + '\n')
        if not self.index.exists():
            self.index.write_text('[]\n')

    def project(self, path=PROJECT, metadata='<OutputType>Exe</OutputType>', source=None):
        self.write(self.repo, path, '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>' + metadata + '</PropertyGroup></Project>')
        if source is not None:
            self.write(self.repo, str(Path(path).parent / 'Program.cs'), source)
        self.commit(self.repo)
        self.pin()

    def binding(self, path=PROJECT, kind='project', identity='Runner'):
        return dict(repository='references/opaque', path=path, kind=kind, identity=identity)

    def allowance(self, surface=None, signals=None, classification='compatibility-surface', row='PS01', sources=None):
        entry = dict(surface=surface or self.binding(), signals=signals or ['executable-project'], classification=classification,
                     row=row, owner='fixture owner', reason='Exact approved fixture classification')
        if sources is not None:
            entry['sources'] = sources
        self.policy['allowances'].append(entry)
        self.save()
        return entry

    def scan(self, *, today=TODAY, revision='HEAD'):
        return census.scan(self.root, revision, self.baseline, self.index, today)

    def run_cli(self, expected):
        output = self.root / 'report.json'
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr), patch.object(census, 'datetime') as clock:
            clock.now.return_value.date.return_value = TODAY
            status = census.main(['--workspace', str(self.root), '--baseline', str(self.baseline),
                '--amendments', str(self.index), '--output', str(output)])
        self.assertEqual(status, expected)
        report = json.loads(output.read_text())
        self.assertEqual(stdout.getvalue(), output.read_text())
        expected_stderr = ''
        for entry in report.get('surfaces', []):
            if entry['status'] == 'rejected':
                surface = entry['surface']
                expected_stderr += f"rejected: {surface['repository']}@{entry['gitlink']} {surface['path']} [{surface['identity']}] signals={','.join(entry['signals'])}\n"
        for error in report.get('errors', []):
            expected_stderr += 'error: ' + json.dumps(error, sort_keys=True) + '\n'
        self.assertEqual(stderr.getvalue(), expected_stderr)
        self.assertEqual(report['status'], 'passed' if expected == 0 else 'failed')
        return report

    def amendment(self, additions=None, removals=None):
        self.write(self.root, 'decision.json', '{"decision":"approved","owner":"fixture owner"}\n')
        amendment = dict(schema=census.SCHEMA, fromVersion='1.0.0', toVersion='1.0.1', previousSha256=census.digest(self.baseline.read_bytes()),
            approval=dict(owner='fixture owner', reason='Scoped qualification fixture', decision='approved', date='2026-11-10',
                          evidence=dict(path='decision.json', sha256=census.digest((self.root / 'decision.json').read_bytes()))),
            addAllowances=additions or [], removeAllowances=removals or [], addExceptions=[], removeExceptions=[])
        target = self.baseline.parent / 'amendment.json'
        target.write_text(json.dumps(amendment))
        self.index.write_text(json.dumps([dict(path=target.name, sha256=census.digest(target.read_bytes()))]))
        return target, amendment

    def test_complete_clean_reference_is_accounted_for(self):
        report = self.run_cli(0)
        self.assertEqual(report['surfaces'], [])
        self.assertEqual([r['repository'] for r in report['repositories']], ['references/opaque'])
        self.assertEqual(report['repositories'][0]['gitlink'], self.git(self.repo, 'rev-parse', 'HEAD'))

    def test_renamed_executable_outside_src_fails_with_actionable_committed_evidence(self):
        self.project()
        report = self.run_cli(1)
        self.assertEqual(len(report['surfaces']), 1)
        self.assertEqual(report['surfaces'][0], dict(surface=self.binding(), signals=['executable-project'], sources=[PROJECT],
            gitlink=self.git(self.repo, 'rev-parse', 'HEAD'), status='rejected', classification='unapproved', reason='new-proprietary-surface'))

    def test_each_independent_project_signal_refuses_new_surface(self):
        fixtures = [
            ('src/Renamed.Mcp/Renamed.Mcp.csproj', '', None, 'project-identity'),
            ('src/Neutral/Neutral.csproj', '<PackageId>Opaque.Cli</PackageId>', None, 'package-identity'),
            ('src/Neutral/Neutral.csproj', '<PackAsTool>true</PackAsTool>', None, 'packed-tool'),
            ('src/Neutral/Neutral.csproj', '<ToolCommandName>neutral</ToolCommandName>', None, 'tool-command'),
            ('src/Neutral/Neutral.csproj', '', 'builder.Services.AddMcpServer();', 'mcp-registration'),
            ('src/Neutral/Neutral.csproj', '', '[McpServerTool(Name="read")] public void Read() {}', 'mcp-registration'),
            ('src/Neutral/Neutral.csproj', '', 'using System.CommandLine;', 'command-line-source'),
        ]
        for path, metadata, source, signal in fixtures:
            with self.subTest(signal=signal):
                self.project(path, metadata, source)
                report = self.run_cli(1)
                entry = next(s for s in report['surfaces'] if s['surface']['path'] == path)
                self.assertIn(signal, entry['signals'])

    def test_inherited_props_targets_and_imports_cannot_hide_tool(self):
        self.write(self.repo, 'Directory.Build.props', '<Project><Import Project="eng/Inherited.props" /></Project>')
        self.write(self.repo, 'eng/Inherited.props', '<Project><PropertyGroup><PackAsTool>true</PackAsTool><ToolCommandName>opaque</ToolCommandName></PropertyGroup><ItemGroup><PackageReference Include="System.CommandLine" /></ItemGroup></Project>')
        self.project(metadata='')
        report = self.run_cli(1)
        self.assertEqual(report['surfaces'][0]['signals'], ['command-line-dependency', 'packed-tool', 'tool-command'])

    def test_property_function_glob_and_unconsumed_local_tool_metadata_cannot_hide(self):
        self.write(self.repo, 'eng/Hidden.props', '<Project><PropertyGroup><PackAsTool>true</PackAsTool><ToolCommandName>hidden</ToolCommandName></PropertyGroup></Project>')
        self.project(metadata='')
        self.write(self.repo, 'Directory.Build.props', '<Project><Import Project="$(Unknown)/Hidden.props" /></Project>')
        self.commit(self.repo); self.pin()
        entry = next(s for s in self.run_cli(1)['surfaces'] if s['surface']['kind']=='project')
        self.assertEqual(entry['signals'], ['packed-tool','tool-command'])
        self.write(self.repo, 'Directory.Build.props', '<Project><Import Project="$(Unknown)/*.props" /></Project>')
        self.commit(self.repo); self.pin()
        entries = self.run_cli(1)['surfaces']
        self.assertTrue(any('unresolved-tool-metadata' in s['signals'] for s in entries))

    def test_named_external_tool_exemption_is_data_and_does_not_allow_other_tools(self):
        self.policy['toolIdentities']=[dict(identity='External.Cli', classification='external-developer-tool', row='PE06',owner='owner',reason='Approved developer tool')]
        self.save()
        self.write(self.repo,'.github/workflows/ci.yml','jobs:\n  test:\n    steps:\n      - run: dotnet tool install External.Cli\n')
        self.commit(self.repo);self.pin()
        self.assertEqual(self.run_cli(0)['surfaces'][0]['classification'],'external-developer-tool')
        self.write(self.repo,'.github/workflows/ci.yml','jobs:\n  test:\n    steps:\n      - run: dotnet tool install Unknown.Cli\n')
        self.commit(self.repo);self.pin();self.run_cli(1)

    def test_mcp_dependency_and_linked_registration_are_associated_with_project(self):
        self.write(self.repo, 'eng/Inherited.props', '<Project><ItemGroup><Compile Include="Linked.cs" /></ItemGroup></Project>')
        self.write(self.repo, 'eng/Linked.cs', 'services.AddNeutralMcp(); app.MapNeutralMcp();')
        self.write(self.repo, 'Directory.Build.props', '<Project><Import Project="eng/Inherited.props" /></Project>')
        self.project(metadata='')
        report = self.run_cli(1)
        entry = next(s for s in report['surfaces'] if s['surface']['kind'] == 'project')
        self.assertEqual(entry['surface'], self.binding())
        self.assertEqual(entry['signals'], ['mcp-registration'])
        self.assertEqual(entry['sources'], ['eng/Linked.cs'])

    def test_package_reference_under_opaque_project_name_is_detected(self):
        self.write(self.repo, PROJECT, '<Project><ItemGroup><PackageReference Include="ModelContextProtocol.AspNetCore" /></ItemGroup></Project>')
        self.commit(self.repo); self.pin()
        self.assertEqual(self.run_cli(1)['surfaces'][0]['signals'], ['mcp-or-cli-dependency'])

    def test_each_approved_classification_is_retained_without_broadening(self):
        self.project()
        classifications = [('PS01','compatibility-surface'), ('PE01','exempt-build-tooling'), ('PE02','exempt-evidence-tooling'),
            ('PE03','platform-qualification-tooling'), ('PE04','build-time-generator'), ('PE05','test-fixture'),
            ('PE08','sample-example-infrastructure'), ('PE09','qualification-evidence-tooling'),
            ('FK02','sample-mcp-host'), ('FK03','dependency-consumer'), ('FK04','test-consumer')]
        for row, classification in classifications:
            with self.subTest(row=row):
                self.policy['allowances'] = []
                self.allowance(classification=classification, row=row)
                entry = self.run_cli(0)['surfaces'][0]
                self.assertEqual((entry['row'],entry['classification'],entry['status']), (row,classification,'approved'))
        self.project('other/New/New.csproj')
        self.assertEqual([s['surface']['identity'] for s in self.run_cli(1)['surfaces'] if s['status']=='rejected'], ['New'])

    def test_allowed_project_cannot_rename_package_tool_or_container_identity(self):
        for property_name, prefix, signal in [('PackageId','package:','package-metadata'),
                ('ToolCommandName','tool:','tool-metadata'),('ContainerRepository','container:','container-metadata')]:
            with self.subTest(property=property_name):
                self.policy['allowances']=[]
                self.project(metadata='<OutputType>Exe</OutputType><'+property_name+'>old</'+property_name+'>')
                report=self.run_cli(1)
                for candidate in report['surfaces']:
                    self.allowance(surface=candidate['surface'],signals=candidate['signals'])
                self.run_cli(0)
                self.project(metadata='<OutputType>Exe</OutputType><'+property_name+'>new</'+property_name+'>')
                rejected=[s for s in self.run_cli(1)['surfaces'] if s['status']=='rejected']
                self.assertEqual([s['surface']['identity'] for s in rejected],[prefix+'new'])
                self.assertEqual(rejected[0]['signals'],[signal])

    def test_dependency_consumer_does_not_gain_server_authority(self):
        self.project(metadata='')
        self.write(self.repo, PROJECT, '<Project><ItemGroup><PackageReference Include="Opaque.Mcp" /></ItemGroup></Project>')
        self.commit(self.repo); self.pin()
        self.allowance(signals=['mcp-or-cli-dependency'], classification='dependency-consumer', row='FK03')
        self.run_cli(0)
        self.write(self.repo, str(Path(PROJECT).parent / 'Program.cs'), 'services.AddMcpServer();')
        self.commit(self.repo); self.pin()
        entry = self.run_cli(1)['surfaces'][0]
        self.assertEqual(entry['unexpectedSignals'], ['mcp-registration'])
        self.assertEqual(entry['reason'], 'allowance-signal-or-source-drift')

    def test_exact_scoped_captured_prefix_is_reported_and_does_not_cover_siblings(self):
        self.policy['exclusions'] = [dict(repository='references/opaque', prefix='captured/approved', row='PE07', classification='captured-evidence', owner='owner', reason='Approved snapshot')]
        self.save()
        self.project('captured/approved/Runner/Runner.csproj')
        report = self.run_cli(0)
        self.assertEqual(report['repositories'][0]['exclusions'], self.policy['exclusions'])
        self.project('captured/approved-new/Runner/Runner.csproj')
        self.assertEqual(self.run_cli(1)['surfaces'][0]['surface']['path'], 'captured/approved-new/Runner/Runner.csproj')

    def test_stale_allowances_are_reported_and_never_rewritten(self):
        self.allowance()
        original = self.baseline.read_bytes()
        report = self.run_cli(0)
        self.assertEqual(report['stale'], [dict(surface=self.binding(), row='PS01', classification='compatibility-surface')])
        self.assertEqual(self.baseline.read_bytes(), original)

    def test_versioned_amendment_adds_hash_bound_fixture_and_can_retire_stale_allowance(self):
        self.project()
        entry = self.allowance(sources=[dict(path=PROJECT,sha256=census.digest((self.repo/PROJECT).read_bytes()))])
        self.policy['allowances'] = []
        self.save()
        baseline = self.baseline.read_bytes()
        self.amendment([entry])
        self.assertEqual(self.run_cli(0)['policy']['version'], '1.0.1')
        self.assertEqual(self.baseline.read_bytes(), baseline)
        self.write(self.repo, PROJECT, (self.repo/PROJECT).read_text().replace('Exe','WinExe'))
        self.commit(self.repo);self.pin()
        self.assertEqual(self.run_cli(1)['surfaces'][0]['changedSources'],[PROJECT])
        self.policy['allowances'] = [entry]
        self.save()
        (self.repo/PROJECT).unlink();self.commit(self.repo);self.pin()
        self.amendment(removals=[self.binding()])
        self.assertEqual(self.run_cli(0)['stale'], [])

    def test_scoped_fixture_checks_changed_secondary_sources_and_added_files(self):
        self.project()
        secondary = str(Path(PROJECT).parent/'Secondary.cs')
        self.write(self.repo,secondary,'public class Secondary {}')
        self.commit(self.repo);self.pin()
        sources=[dict(path=path,sha256=census.digest((self.repo/path).read_bytes())) for path in (PROJECT,secondary)]
        entry=self.allowance(sources=sources,classification='non-surface-qualification-fixture',row='PA02')
        entry['sourcePrefix']=str(Path(PROJECT).parent);self.save()
        self.run_cli(0)
        self.write(self.repo,secondary,'public class Secondary { public void Change() {} }')
        self.commit(self.repo);self.pin()
        self.assertEqual(self.run_cli(1)['surfaces'][0]['changedSources'],[secondary])
        self.write(self.repo,secondary,'public class Secondary {}')
        added=str(Path(PROJECT).parent/'Added.cs');self.write(self.repo,added,'public class Added {}')
        self.commit(self.repo);self.pin()
        self.assertEqual(self.run_cli(1)['surfaces'][0]['changedSources'],[added])

    def test_invalid_policy_and_provenance_fail_before_scanning(self):
        mutations = [
            ('version', lambda p:p.update(version='1.0.1'), 'invalid-baseline-version'),
            ('hash', lambda p:p['provenance'][0].update(sha256='0'*64),'source-provenance-mismatch'),
            ('roots',lambda p:p['roots'].append(copy.deepcopy(p['roots'][0])),'invalid-root-provenance'),
            ('allowance',lambda p:p['allowances'].append({'surface':self.binding()}),'invalid-allowance'),
            ('path',lambda p:p['roots'][0].update(repository='../escape'),'unsafe-path'),
            ('exclusion',lambda p:p['exclusions'].append(dict(repository='references/opaque',prefix='../escape',row='PE07',classification='captured',owner='owner',reason='reason')),'unsafe-path'),
        ]
        original=copy.deepcopy(self.policy)
        for name, change, rule in mutations:
            with self.subTest(name=name):
                self.policy=copy.deepcopy(original);change(self.policy);self.save()
                self.assertEqual(self.run_cli(1)['errors'],[{'rule':rule}])

    def test_duplicate_allowances_and_json_keys_fail(self):
        entry=self.allowance();self.policy['allowances'].append(entry);self.save()
        self.assertEqual(self.run_cli(1)['errors'],[{'rule':'duplicate-allowance'}])
        self.baseline.write_text('{"schema":1,"schema":2}')
        self.assertEqual(self.run_cli(1)['errors'],[{'rule':'duplicate-json-key:baseline'}])

    def test_amendment_hash_chain_approval_and_schema_are_required(self):
        for name in ('bytes','chain','version','approval','schema','removal'):
            with self.subTest(name=name):
                target, document=self.amendment()
                if name=='bytes':target.write_text('{}')
                else:
                    if name=='chain':document['previousSha256']='0'*64
                    if name=='version':document['toVersion']='1.0.2'
                    if name=='approval':document['approval']['owner']=' '
                    if name=='schema':document['blanketExemption']=True
                    if name=='removal':document['removeAllowances']=[self.binding()]
                    target.write_text(json.dumps(document));self.index.write_text(json.dumps([dict(path=target.name,sha256=census.digest(target.read_bytes()))]))
                self.run_cli(1)

    def test_exception_is_exact_including_kind_identity_path_and_root(self):
        self.project()
        self.policy['exceptions']=[dict(surface=self.binding(),owner='owner',reason='Migration',expires='2026-11-10')];self.save()
        self.assertEqual(self.run_cli(0)['surfaces'][0]['status'],'exception')
        for field,value in [('path','other/Runner.csproj'),('identity','different'),('kind','source')]:
            with self.subTest(field=field):
                self.policy['exceptions'][0]['surface']=self.binding();self.policy['exceptions'][0]['surface'][field]=value;self.save()
                self.run_cli(1)
        self.policy['exceptions'][0]['surface']=self.binding();self.policy['exceptions'][0]['surface']['repository']='references/another';self.save()
        self.assertEqual(self.run_cli(1)['errors'],[{'rule':'invalid-exception'}])

    def test_invalid_exception_fails_even_when_target_is_already_allowed(self):
        self.project();self.allowance()
        valid=dict(surface=self.binding(),owner='owner',reason='Migration',expires='2026-11-10')
        for field,value in [('owner',''),('reason','  '),('expires','2026-1-1'),('expires','2026-11-09'),('expires',None)]:
            with self.subTest(field=field,value=value):
                entry=copy.deepcopy(valid);entry[field]=value;self.policy['exceptions']=[entry];self.save();self.run_cli(1)
        for field in ('owner','reason','expires'):
            entry=copy.deepcopy(valid);del entry[field];self.policy['exceptions']=[entry];self.save();self.run_cli(1)
        self.policy['exceptions']=[valid,valid];self.save();self.run_cli(1)

    def test_expiry_is_inclusive_and_production_uses_utc(self):
        self.project();self.policy['exceptions']=[dict(surface=self.binding(),owner='owner',reason='Migration',expires='2026-11-10')];self.save()
        self.assertEqual(self.scan(today=date(2026,11,9))['status'],'passed')
        self.assertEqual(self.scan(today=TODAY)['status'],'passed')
        with self.assertRaisesRegex(census.CensusError,'expired-exception'):self.scan(today=date(2026,11,11))
        with patch.object(census,'datetime') as clock,contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            clock.now.return_value.date.return_value=TODAY
            self.assertEqual(census.main(['--workspace',str(self.root),'--baseline',str(self.baseline),'--amendments',str(self.index),'--output',str(self.root/'utc.json')]),0)
            clock.now.assert_called_once_with(census.timezone.utc)

    def test_orphan_package_tool_container_and_workflow_publications_fail(self):
        fixtures=[
            ('tools/release-packages.json',{'packages':[{'id':'Opaque.Surface','project':'missing/Neutral.csproj'}]},'publication-entry'),
            ('tools/release-containers.json',{'images':[{'repository':'neutral-image'}]},'publication-entry'),
            ('.config/dotnet-tools.json',{'version':1,'tools':{'opaque-tool':{'version':'1.0.0'}}},'tool-manifest'),
        ]
        for path,document,signal in fixtures:
            with self.subTest(path=path):
                self.write(self.repo,path,json.dumps(document));self.commit(self.repo);self.pin()
                entries=self.run_cli(1)['surfaces'];entry=next(e for e in entries if e['surface']['path']==path)
                self.assertEqual(entry['signals'],[signal])
        self.write(self.repo,'.github/workflows/release.yml','jobs:\n  release:\n    steps:\n      - run: dotnet publish missing/Neutral.Mcp.csproj\n')
        self.commit(self.repo);self.pin()
        self.assertTrue(any('orphan-project-reference' in e['signals'] for e in self.run_cli(1)['surfaces']))

    def test_opaque_container_image_and_nonstandard_manifest_are_detected(self):
        self.write(self.repo, 'deploy/opaque.yaml', 'kind: Deployment\nspec:\n  image: registry.example.invalid/opaque-operator:1.0\n')
        self.write(self.repo, 'manifests/odd.json', '{"images":[{"repository":"another-operator"}]}')
        self.write(self.repo, 'tools/package.json', '{"name":"opaque-tool","bin":{"opaque":"run.js"}}')
        self.commit(self.repo); self.pin()
        entries = self.run_cli(1)['surfaces']
        self.assertEqual({s['surface']['identity'] for s in entries},
                         {'registry.example.invalid/opaque-operator:1.0','another-operator','opaque:run.js'})

    def test_approved_publication_does_not_approve_another_entry(self):
        self.write(self.repo,'tools/release-containers.json','{"images":[{"repository":"old-mcp"}]}');self.commit(self.repo);self.pin()
        self.allowance(surface=self.binding('tools/release-containers.json','publication','old-mcp'),signals=['publication-entry'],row='G4',classification='compatibility-publication-or-route')
        self.run_cli(0)
        self.write(self.repo,'tools/release-containers.json','{"images":[{"repository":"old-mcp"},{"repository":"new-mcp"}]}');self.commit(self.repo);self.pin()
        rejected=[e for e in self.run_cli(1)['surfaces'] if e['status']=='rejected']
        self.assertEqual([e['surface']['identity'] for e in rejected],['new-mcp'])

    def test_external_configuration_is_bound_to_exact_server_definition(self):
        self.write(self.repo,'.mcp.json','{"mcpServers":{"learn":{"url":"https://example.invalid/mcp"}}}');self.commit(self.repo);self.pin()
        candidate=self.run_cli(1)['surfaces'][0]
        self.allowance(surface=candidate['surface'],signals=candidate['signals'],row='PE06',classification='external-developer-configuration')
        self.run_cli(0)
        self.write(self.repo,'.mcp.json','{"mcpServers":{"learn":{"command":"dotnet","args":["run","--project","New.csproj"]}}}');self.commit(self.repo);self.pin()
        self.run_cli(1)

    def test_malformed_metadata_and_unsafe_xml_fail_instead_of_skipping(self):
        for text,rule in [('<Project>','malformed-project-metadata'),('<!DOCTYPE Project [<!ENTITY x "x">]><Project/>','unsafe-xml')]:
            self.write(self.repo,PROJECT,text);self.commit(self.repo);self.pin()
            self.assertIn(rule,self.run_cli(1)['errors'][0]['rule'])
        self.write(self.repo,PROJECT,'<Project/>');self.write(self.repo,'tools/release-containers.json','{"images":"bad"}');self.commit(self.repo);self.pin()
        self.assertIn('malformed-publication',self.run_cli(1)['errors'][0]['rule'])

    def test_root_declarations_and_gitlinks_are_from_one_parent_revision(self):
        revision=self.git(self.root,'rev-parse','HEAD')
        self.project()
        self.write(self.root,'.gitmodules','invalid working-tree declarations')
        self.write(self.repo,PROJECT,'invalid worktree metadata')
        self.assertEqual(self.scan(revision=revision)['surfaces'],[])
        self.assertEqual(self.scan()['status'],'failed')
        self.assertEqual(self.scan()['surfaces'][0]['surface'],self.binding())

    def test_reference_head_and_worktree_are_ignored(self):
        self.project();pinned=self.git(self.repo,'rev-parse','HEAD')
        self.write(self.repo,PROJECT,'<Project/>');self.commit(self.repo)
        self.write(self.repo,PROJECT,'invalid dirty metadata')
        report=self.run_cli(1)
        self.assertEqual(report['surfaces'][0]['gitlink'],pinned)
        self.assertEqual(report['surfaces'][0]['signals'],['executable-project'])

    def test_nested_gitlinks_are_reported_without_inspection_or_initialization(self):
        self.git(self.repo,'update-index','--add','--cacheinfo','160000,'+'f'*40+',references/missing')
        self.git(self.repo,'commit','-q','-m','test: record unavailable nested gitlink');self.pin()
        report=self.run_cli(0)
        self.assertEqual(report['repositories'][0]['nestedGitlinks'],['references/missing'])
        self.assertFalse((self.repo/'references/missing').exists())

    def test_reference_named_regular_directory_is_still_inspected(self):
        self.project('references/local/Neutral.csproj')
        report=self.run_cli(1)
        self.assertEqual(report['surfaces'][0]['surface']['path'],'references/local/Neutral.csproj')
        self.assertEqual(report['repositories'][0]['nestedGitlinks'],[])

    def test_missing_root_uninitialized_root_and_missing_committed_object_fail(self):
        moved=self.root/'held';shutil.move(self.repo,moved)
        self.run_cli(1)
        self.repo.mkdir();self.run_cli(1)
        shutil.rmtree(self.repo);shutil.move(moved,self.repo)
        self.git(self.root,'update-index','--cacheinfo','160000,'+'f'*40+',references/opaque')
        self.git(self.root,'commit','-q','-m','test: reference missing committed object')
        self.assertEqual(self.run_cli(1)['errors'][0]['rule'],'git-object-unavailable')

    def test_malformed_unsafe_undeclared_and_unapproved_roots_fail(self):
        initial=(self.root/'.gitmodules').read_text()
        for text in ['[submodule "x"]\n path = ../escape\n url = example\n','malformed','[submodule "x"]\n path = missing\n url = example\n']:
            self.write(self.root,'.gitmodules',text);self.git(self.root,'add','.gitmodules');self.git(self.root,'commit','-q','-m','test: malformed declarations');self.run_cli(1)
        self.write(self.root,'.gitmodules',initial);self.git(self.root,'add','.gitmodules')
        self.git(self.root,'update-index','--add','--cacheinfo','160000,'+'f'*40+',undeclared')
        self.git(self.root,'commit','-q','-m','test: undeclared gitlink');self.run_cli(1)

    def test_inspected_program_is_never_executed(self):
        marker=self.root/'executed'
        self.project(source=f'// would create {marker} if executed\nSystem.IO.File.WriteAllText("{marker}", "executed");')
        self.run_cli(1);self.assertFalse(marker.exists())

    def test_selected_guard_mutations_are_caught_by_negative_controls(self):
        self.project();self.policy['exceptions']=[dict(surface=self.binding(),owner='owner',reason='Migration',expires='2026-11-09')];self.save()
        original=census.require
        def without_expiry(condition,message):
            return None if message=='expired-exception' else original(condition,message)
        with patch.object(census,'require',side_effect=without_expiry):
            self.assertEqual(self.scan()['status'],'passed')
        self.run_cli(1)
        self.policy['exceptions']=[];self.allowance(signals=['executable-project'],classification='dependency-consumer')
        self.write(self.repo,str(Path(PROJECT).parent/'Program.cs'),'services.AddMcpServer();');self.commit(self.repo);self.pin()
        with patch.object(census,'REGISTRATION',new=__import__('re').compile(r'(?!)')):
            self.assertEqual(self.scan()['status'],'passed')
        self.assertEqual(self.run_cli(1)['surfaces'][0]['unexpectedSignals'],['mcp-registration'])


if __name__=='__main__':
    unittest.main()
