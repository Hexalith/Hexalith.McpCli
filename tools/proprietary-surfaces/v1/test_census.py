"""Disposable committed Git trees exercise census acceptance and refusal paths."""
import contextlib
import copy
from datetime import date
import importlib.util
import io
import json
import os
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
        self.write(self.root, 'approval.json', json.dumps({'decision':'approved','source_revisions':{'references/opaque':self.git(self.repo,'rev-parse','HEAD')}}))
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
        self.write(self.repo, path, '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><IsPackable>false</IsPackable>' + metadata + '</PropertyGroup></Project>')
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
        amendment = dict(schema=census.SCHEMA, fromVersion='1.0.0', toVersion='1.0.1', previousSha256=census.digest(self.baseline.read_bytes()),
            approval=dict(owner='fixture owner', reason='Scoped qualification fixture', decision='approved', date='2026-11-10', evidence={}),
            addAllowances=additions or [], removeAllowances=removals or [], addExceptions=[], removeExceptions=[])
        authorization={key:amendment.get(key,[]) for key in ('addAllowances','removeAllowances','addExceptions','removeExceptions','addExclusions')}
        receipt=dict(schema='mcpcli-census-amendment-approval/v2',decision='approved',owner='fixture owner',
            authority=[dict(path='approval.json',sha256=census.digest((self.root/'approval.json').read_bytes()))],authorization=authorization)
        self.write(self.root,'decision.json',json.dumps(receipt))
        amendment['approval']['evidence']=dict(path='decision.json',sha256=census.digest((self.root/'decision.json').read_bytes()))
        target=self.baseline.parent/'amendment.json'
        target.write_text(json.dumps(amendment))
        self.index.write_text(json.dumps([dict(path=target.name,sha256=census.digest(target.read_bytes()))]))
        return target,amendment

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
        self.assertTrue(any(s['signals'] == ['packed-tool','tool-command'] for s in entries))

    def test_named_external_tool_exemption_is_data_and_does_not_allow_other_tools(self):
        self.policy['toolIdentities']=[dict(identity='External.Cli', classification='external-developer-tool', row='PE06',owner='owner',reason='Approved developer tool')]
        self.save()
        self.write(self.repo,'.github/workflows/ci.yml','jobs:\n  test:\n    steps:\n      - run: dotnet tool install External.Cli\n')
        self.commit(self.repo);self.pin()
        self.assertEqual(self.run_cli(0)['surfaces'][0]['classification'],'external-developer-tool')
        self.write(self.repo,'.github/workflows/ci.yml','jobs:\n  test:\n    steps:\n      - run: dotnet tool install Unknown.Cli\n')
        self.commit(self.repo);self.pin();self.run_cli(1)

    def test_mcp_dependency_and_linked_registration_are_associated_with_project(self):
        self.write(self.repo, 'eng/Inherited.props', '<Project><ItemGroup><Compile Include="$(MSBuildThisFileDirectory)Linked.cs" /></ItemGroup></Project>')
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


    def test_literal_glob_import_finds_neutral_executable_and_dependency(self):
        self.write(self.repo,'eng/neutral.props','<Project><PropertyGroup><OutputType>Exe</OutputType></PropertyGroup><ItemGroup><PackageReference Include="System.CommandLine" /></ItemGroup></Project>')
        self.write(self.repo,'Directory.Build.props','<Project><Import Project="eng/*.props" /></Project>')
        self.project(metadata='')
        project=next(s for s in self.run_cli(1)['surfaces'] if s['surface']['kind']=='project')
        self.assertEqual(project['signals'],['command-line-dependency','executable-project'])

    def test_unresolved_directory_glob_cannot_hide_executable_metadata(self):
        self.write(self.repo,'Directory.Build.props','<Project><Import Project="$(ExternalDir)/*.props"/></Project>')
        self.write(self.repo,'eng/Hidden.props','<Project><PropertyGroup><OutputType>Exe</OutputType></PropertyGroup></Project>')
        self.project(metadata='')
        self.assertEqual(self.run_cli(1)['surfaces'],[dict(surface=self.binding(),
            signals=['executable-project'],sources=[PROJECT],gitlink=self.git(self.repo,'rev-parse','HEAD'),
            status='rejected',classification='unapproved',reason='new-proprietary-surface')])

    def test_unresolved_directory_glob_cannot_hide_mcp_or_cli_references(self):
        self.write(self.repo,'Directory.Build.props','<Project><Import Project="$(ExternalDir)/*.props"/></Project>')
        self.project(metadata='')
        for reference in ['<PackageReference Include="ModelContextProtocol"/>','<PackageReference Include="system.commandline"/>',
                '<ProjectReference Include="../Neutral.Mcp/Neutral.Mcp.csproj"/>']:
            with self.subTest(reference=reference):
                self.write(self.repo,'eng/Hidden.props','<Project><ItemGroup>'+reference+'</ItemGroup></Project>')
                self.commit(self.repo);self.pin()
                entry=self.run_cli(1)['surfaces'][0]
                self.assertEqual(entry['surface'],self.binding())
                self.assertEqual(entry['signals'],['command-line-dependency'] if 'system.commandline' in reference else ['mcp-or-cli-dependency'])

    def test_case_insensitive_properties_and_aliased_reference_identities(self):
        self.write(self.repo,PROJECT,'<Project><PropertyGroup><KiNd>Exe</KiNd><outputTYPE>$(kInD)</outputTYPE><protocol>ModelContextProtocol</protocol><target>../Opaque.Mcp/Opaque.Mcp.csproj</target></PropertyGroup><ItemGroup><packageREFERENCE include="$(PROTOCOL)"/><PROJECTreference Include="$(TARGET)"/></ItemGroup></Project>')
        self.commit(self.repo);self.pin()
        project=next(s for s in self.run_cli(1)['surfaces'] if s['surface']['kind']=='project')
        self.assertEqual(project['signals'],['executable-project','mcp-or-cli-dependency'])

    def test_symbolic_publication_identities_expand_and_renames_are_rejected(self):
        for property_name,prefix in [('packageID','package:'),('toolCOMMANDname','tool:'),('containerREPOSITORY','container:')]:
            with self.subTest(property=property_name):
                self.policy['allowances']=[];self.save()
                self.project(metadata='<outputtype>Exe</outputtype><'+property_name+'>old-$(msbuildPROJECTname)</'+property_name+'>')
                for candidate in self.run_cli(1)['surfaces']:
                    self.allowance(surface=candidate['surface'],signals=candidate['signals'])
                self.run_cli(0)
                self.project(metadata='<outputtype>Exe</outputtype><'+property_name+'>new-$(MSBuildProjectName)</'+property_name+'>')
                rejected=[s for s in self.run_cli(1)['surfaces'] if s['status']=='rejected']
                self.assertEqual([s['surface']['identity'] for s in rejected],[prefix+'new-Runner'])

    def test_unresolved_classification_property_or_reference_fails_safely(self):
        for metadata in ['<OutputType>$(Unknown)</OutputType>','<PackageId>$(Unknown)</PackageId>']:
            self.project(metadata=metadata)
            self.assertIn('unresolved-classification-metadata',self.run_cli(1)['errors'][0]['rule'])
        self.write(self.repo,PROJECT,'<Project><ItemGroup><PackageReference Include="$(Unknown)"/></ItemGroup></Project>')
        self.commit(self.repo);self.pin()
        self.assertIn('unresolved-classification-metadata',self.run_cli(1)['errors'][0]['rule'])

    def test_structure_discovers_neutral_json_packages_and_server_configuration(self):
        self.write(self.repo,'release.json','{"packages":[{"id":"neutral"}]}')
        self.write(self.repo,'settings.json','{"mcpServers":{"neutral":{"command":"neutral","args":[]}}}')
        self.commit(self.repo);self.pin()
        entries=self.run_cli(1)['surfaces']
        self.assertEqual({s['surface']['path'] for s in entries},{'release.json','settings.json'})
        self.assertEqual(next(s for s in entries if s['surface']['path']=='release.json')['surface']['identity'],'neutral')

    def test_orphan_neutral_dotnet_publish_pack_and_run_are_candidates(self):
        for verb in ('publish','pack','run'):
            self.write(self.repo,'scripts/ship.sh',f'dotnet {verb} missing/Neutral.csproj\n'.replace('\\n','\n'))
            self.commit(self.repo);self.pin()
            entries=self.run_cli(1)['surfaces']
            self.assertEqual(entries[0]['surface']['identity'],'missing/Neutral.csproj')
            self.assertEqual(entries[0]['signals'],['orphan-project-reference'])

    def test_literal_neutral_tool_install_and_container_commands_bind_exact_identity(self):
        for command in ['dotnet tool install --global {name}','docker build -t registry.invalid/{name}:1 .','docker push registry.invalid/{name}:1']:
            with self.subTest(command=command):
                self.policy['allowances']=[];self.save()
                self.write(self.repo,'scripts/ship.sh',command.format(name='neutral'))
                self.commit(self.repo);self.pin()
                for candidate in self.run_cli(1)['surfaces']:
                    self.allowance(surface=candidate['surface'],signals=candidate['signals'])
                self.run_cli(0)
                self.write(self.repo,'scripts/ship.sh',command.format(name='renamed'))
                self.commit(self.repo);self.pin()
                rejected=[s for s in self.run_cli(1)['surfaces'] if s['status']=='rejected']
                self.assertEqual(len(rejected),1)
                self.assertIn('renamed',rejected[0]['surface']['identity'])

    def test_rejected_unrelated_nonjson_and_wrong_scope_approval_cannot_authorize(self):
        self.project()
        entry=dict(surface=self.binding(),signals=['executable-project'],classification='test-fixture',row='PE05',owner='fixture owner',reason='Exact approved fixture')
        for mutation in ('decision','receipt-rejected','unrelated','not-json','wrong-identity','wrong-sources','wrong-exception'):
            with self.subTest(mutation=mutation):
                target,amendment=self.amendment([entry])
                receipt=json.loads((self.root/'decision.json').read_text())
                if mutation=='decision':amendment['approval']['decision']='rejected'
                elif mutation=='receipt-rejected':receipt['decision']='rejected'
                elif mutation=='unrelated':receipt={'decision':'approved','owner':'unrelated'}
                elif mutation=='wrong-identity':receipt['authorization']['addAllowances'][0]['surface']['identity']='another'
                elif mutation=='wrong-sources':receipt['authorization']['addAllowances'][0]['sources']=[{'path':'other.cs','sha256':'0'*64}]
                elif mutation=='wrong-exception':receipt['authorization']['addExceptions']=[dict(surface=self.binding(),owner='owner',reason='reason',expires='2026-12-01')]
                (self.root/'decision.json').write_text('unrelated non-json' if mutation=='not-json' else json.dumps(receipt))
                amendment['approval']['evidence']['sha256']=census.digest((self.root/'decision.json').read_bytes())
                target.write_text(json.dumps(amendment));self.index.write_text(json.dumps([dict(path=target.name,sha256=census.digest(target.read_bytes()))]))
                self.run_cli(1)

    def test_compilation_closure_binds_inherited_imported_linked_and_added_source(self):
        self.write(self.repo,'Directory.Build.props','<Project><Import Project="shared/*.props"/></Project>')
        self.write(self.repo,'shared/local.props','<Project><ItemGroup><Compile Include="$(MSBuildThisFileDirectory)*.cs"/></ItemGroup></Project>')
        self.write(self.repo,'shared/Secondary.cs','class Secondary {}')
        self.project()
        tree=census.Tree(self.repo,self.git(self.repo,'rev-parse','HEAD'))
        entry=self.allowance(sources=census.compilation_closure(tree,PROJECT),classification='non-surface-qualification-fixture',row='PA02')
        entry.update(sourcePrefix=str(Path(PROJECT).parent),compilationClosure=True);self.save()
        self.run_cli(0)
        for path,original,changed in [('Directory.Build.props','<Project><Import Project="shared/*.props"/></Project>','<Project><Import Project="shared/*.props"/><PropertyGroup><Marker>changed</Marker></PropertyGroup></Project>'),('shared/local.props','<Project><ItemGroup><Compile Include="$(MSBuildThisFileDirectory)*.cs"/></ItemGroup></Project>','<Project><ItemGroup><Compile Include="$(MSBuildThisFileDirectory)*.cs"/></ItemGroup><PropertyGroup><Marker>changed</Marker></PropertyGroup></Project>'),('shared/Secondary.cs','class Secondary {}','class Secondary { int Changed; }')]:
            self.write(self.repo,path,changed);self.commit(self.repo);self.pin()
            self.assertIn(path,self.run_cli(1)['surfaces'][0]['changedSources'])
            self.write(self.repo,path,original)
        self.write(self.repo,'shared/Added.cs','class Added {}');self.commit(self.repo);self.pin()
        self.assertIn('shared/Added.cs',self.run_cli(1)['surfaces'][0]['changedSources'])

    def test_test_like_paths_do_not_grant_executable_or_metadata_authority(self):
        self.project('tests/Neutral/Neutral.csproj')
        self.project('perf/NeutralTests/NeutralTests.csproj')
        self.write(self.repo,'tests/fixtures/settings.json','{"mcpServers":{"neutral":{"command":"neutral"}}}')
        self.write(self.repo,'tests/fixtures/release.json','{"packages":[{"id":"neutral"}]}')
        self.write(self.repo,'tests/fixtures/test-tool.sh','dotnet tool install neutral')
        self.write(self.repo,'tests/fixtures/.config/dotnet-tools.json','{"tools":{"neutral":{"version":"1"}}}')
        self.commit(self.repo);self.pin()
        entries=self.run_cli(1)['surfaces']
        paths={s['surface']['path'] for s in entries}
        self.assertEqual(paths,{'tests/Neutral/Neutral.csproj','perf/NeutralTests/NeutralTests.csproj','tests/fixtures/settings.json','tests/fixtures/release.json','tests/fixtures/test-tool.sh','tests/fixtures/.config/dotnet-tools.json'})
        self.assertTrue(all(s['status']=='rejected' for s in entries))

    def test_image_mapping_binds_repository_and_never_a_following_key(self):
        path='deploy/image.yaml'
        self.write(self.repo,path,'image:\n  repository: registry.invalid/neutral\n  tag: one\n'.replace('\\n','\n'))
        self.commit(self.repo);self.pin()
        candidate=self.run_cli(1)['surfaces'][0]
        self.assertEqual(candidate['surface']['identity'],'registry.invalid/neutral')
        self.allowance(surface=candidate['surface'],signals=candidate['signals']);self.run_cli(0)
        self.write(self.repo,path,'image:\n  repository: registry.invalid/renamed\n  tag: one\n'.replace('\\n','\n'))
        self.commit(self.repo);self.pin()
        self.assertEqual(self.run_cli(1)['surfaces'][0]['surface']['identity'],'registry.invalid/renamed')
        self.write(self.repo,path,'image:\nother: value\n'.replace('\\n','\n'));self.commit(self.repo);self.pin()
        self.assertEqual(self.run_cli(0)['surfaces'],[])

    def test_every_committed_root_is_accounted_for_and_later_root_rejects(self):
        later=self.root/'references/zeta';later.mkdir()
        self.git(later,'init','-q')
        self.write(later,'src/Neutral/Neutral.csproj','<Project><PropertyGroup><OutputType>Exe</OutputType></PropertyGroup></Project>')
        pin=self.commit(later)
        with (self.root/'.gitmodules').open('a') as output:output.write('[submodule "zeta"]\n path = references/zeta\n url = https://example.invalid/zeta.git\n'.replace('\\n','\n'))
        self.git(self.root,'add','.gitmodules');self.git(self.root,'update-index','--add','--cacheinfo',f'160000,{pin},references/zeta');self.git(self.root,'commit','-q','-m','test: add second committed census root')
        self.policy['roots'].append(dict(repository='references/zeta',gitlink=pin,classification='PN02',owner='fixture owner'))
        approval=json.loads((self.root/'approval.json').read_text());approval['source_revisions']['references/zeta']=pin
        self.write(self.root,'approval.json',json.dumps(approval));self.git(self.root,'add','approval.json');self.git(self.root,'commit','-q','-m','test: bind complete authority roots')
        self.policy['provenance'][1]['sha256']=census.digest((self.root/'approval.json').read_bytes());self.save()
        report=self.run_cli(1)
        self.assertEqual([r['repository'] for r in report['repositories']],['references/opaque','references/zeta'])
        self.assertEqual({s['surface']['repository'] for s in report['surfaces']},{'references/zeta'})

    def test_toml_servers_require_exact_approval_and_malformed_toml_fails(self):
        path='.codex/config.toml';original='[mcp_servers.neutral]\ncommand="neutral"\nargs=["old"]\n'.replace('\\n','\n')
        self.write(self.repo,path,original);self.commit(self.repo);self.pin()
        candidate=self.run_cli(1)['surfaces'][0]
        self.allowance(surface=candidate['surface'],signals=candidate['signals'],row='PE06',classification='external-developer-configuration');self.run_cli(0)
        for content in [original.replace('command="neutral"','command="renamed"'),original.replace('"old"','"new"')]:
            self.write(self.repo,path,content);self.commit(self.repo);self.pin();self.run_cli(1)
        self.write(self.repo,path,'[mcp_servers.neutral');self.commit(self.repo);self.pin()
        self.assertIn('malformed-server-configuration',self.run_cli(1)['errors'][0]['rule'])

    def test_boundary_redacts_canary_from_stdout_stderr_and_saved_json(self):
        canary='census-boundary-credential-canary-74923'
        self.write(self.repo,'tools/release.json',json.dumps({'packages':[{'id':canary}]}));self.commit(self.repo);self.pin()
        output=self.root/'canary.json';stdout,stderr=io.StringIO(),io.StringIO()
        with patch.dict(os.environ,{'MCPCLI_TEST_SECRET':canary}),contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
            self.assertEqual(census.main(['--workspace',str(self.root),'--baseline',str(self.baseline),'--amendments',str(self.index),'--output',str(output)]),1)
        self.assertNotIn(canary,stdout.getvalue());self.assertNotIn(canary,stderr.getvalue());self.assertNotIn(canary,output.read_text())
        self.assertIn('[REDACTED]',stdout.getvalue());self.assertIn('[REDACTED]',stderr.getvalue());self.assertIn('[REDACTED]',output.read_text())


    def test_exact_metadata_fixture_exclusion_is_hash_bound_and_has_no_directory_authority(self):
        path='tests/fixtures/release.json'
        self.write(self.repo,path,'{"packages":"intentionally invalid fixture"}')
        self.commit(self.repo);self.pin();self.run_cli(1)
        target,amendment=self.amendment()
        exclusion=dict(repository='references/opaque',prefix=path,row='PE05',classification='approved-test-metadata-fixture',owner='fixture owner',reason='Exact approved existing fixture',scope='file',sha256=census.digest((self.repo/path).read_bytes()))
        amendment['addExclusions']=[exclusion]
        receipt=json.loads((self.root/'decision.json').read_text());receipt['authorization']['addExclusions']=[exclusion]
        (self.root/'decision.json').write_text(json.dumps(receipt));amendment['approval']['evidence']['sha256']=census.digest((self.root/'decision.json').read_bytes())
        target.write_text(json.dumps(amendment));self.index.write_text(json.dumps([dict(path=target.name,sha256=census.digest(target.read_bytes()))]))
        self.run_cli(0)
        self.write(self.repo,'tests/fixtures/new.json','{"packages":[{"id":"new-neutral"}]}');self.commit(self.repo);self.pin()
        self.assertEqual(self.run_cli(1)['surfaces'][0]['surface']['identity'],'new-neutral')
        self.write(self.repo,path,'{"packages":[{"id":"changed-neutral"}]}');self.commit(self.repo);self.pin()
        self.assertIn('excluded-fixture-source-drift',self.run_cli(1)['errors'][0]['rule'])

    def test_preserved_legacy_receipt_authorizes_only_its_exact_fixture_scope(self):
        self.project()
        sources=[dict(path=PROJECT,sha256=census.digest((self.repo/PROJECT).read_bytes()))]
        entry=dict(surface=self.binding(),signals=['executable-project'],classification='non-surface-qualification-fixture',row='PA01',owner='fixture owner',reason='Existing exact fixture',sourcePrefix=str(Path(PROJECT).parent),sources=sources)
        target,amendment=self.amendment([entry])
        receipt=dict(schema='mcpcli-census-amendment-approval/v1',decision='approved',owner='fixture owner',fixtures=[dict(repository='references/opaque',gitlink=self.git(self.repo,'rev-parse','HEAD'),project=PROJECT,sourceClosure=dict(prefix=str(Path(PROJECT).parent),sources=sources))])
        (self.root/'decision.json').write_text(json.dumps(receipt));amendment['approval']['evidence']['sha256']=census.digest((self.root/'decision.json').read_bytes())
        self.git(self.root,'add','decision.json');self.git(self.root,'commit','-q','-m','test: preserve legacy receipt before correction')
        self.write(self.baseline.parent,'legacy-receipts.json',json.dumps(dict(schema='mcpcli-census-legacy-receipts/v1',baselineSha256=census.digest(self.baseline.read_bytes()),receipts=[amendment['approval']['evidence']])))
        target.write_text(json.dumps(amendment));self.index.write_text(json.dumps([dict(path=target.name,sha256=census.digest(target.read_bytes()))]))
        self.run_cli(0)
        registry_path=self.baseline.with_name('legacy-receipts.json')
        registry=json.loads(registry_path.read_text())
        invalid=[dict(registry,schema='other'),dict(registry,baselineSha256='0'*64),
                 dict(registry,receipts={}),dict(registry,receipts=[{}]),
                 dict(registry,receipts=[dict(path='decision.json',sha256='invalid')]),
                 dict(registry,receipts=registry['receipts']*2)]
        for value in invalid:
            registry_path.write_text(json.dumps(value))
            self.assertEqual(self.run_cli(1)['errors'],[{'rule':'invalid-legacy-receipt-registry'}])
        registry_path.write_text(json.dumps(dict(registry,receipts=[dict(path='../outside.json',sha256='0'*64)])))
        self.assertEqual(self.run_cli(1)['errors'],[{'rule':'unsafe-path'}])
        registry_path.unlink()
        self.assertEqual(self.run_cli(1)['errors'],[{'rule':'legacy-receipt-registry-required'}])
        registry_copy=self.root/'retained-registry.json';registry_copy.write_text(json.dumps(registry))
        registry_path.symlink_to(registry_copy)
        self.assertEqual(self.run_cli(1)['errors'],[{'rule':'legacy-receipt-registry-required'}])
        registry_path.unlink();registry_path.write_text(json.dumps(registry))
        amendment['addAllowances'][0]['surface']['identity']='unrelated'
        target.write_text(json.dumps(amendment));self.index.write_text(json.dumps([dict(path=target.name,sha256=census.digest(target.read_bytes()))]))
        self.assertEqual(self.run_cli(1)['errors'],[{'rule':'amendment-authorization-scope-mismatch'}])

    def test_committed_correction_data_preserves_previous_chain_and_exact_receipt_scope(self):
        directory=Path(__file__).parent
        previous=census.digest((directory/'baseline.json').read_bytes())
        for item in json.loads((directory/'amendments.json').read_text()):
            raw=(directory/item['path']).read_bytes();self.assertEqual(census.digest(raw),item['sha256'])
            amendment=json.loads(raw);self.assertEqual(amendment['previousSha256'],previous)
            binding=amendment['approval']['evidence'];receipt_path=census.ROOT/binding['path']
            self.assertEqual(census.digest(receipt_path.read_bytes()),binding['sha256'])
            receipt=json.loads(receipt_path.read_text());self.assertEqual(receipt['decision'],'approved')
            if receipt['schema'].endswith('/v2'):
                self.assertEqual(receipt['authorization'],{key:amendment.get(key,[]) for key in ('addAllowances','removeAllowances','addExceptions','removeExceptions','addExclusions')})
            previous=item['sha256']

    def test_amendment_authority_must_belong_to_validated_lineage(self):
        self.project()
        entry=dict(surface=self.binding(),signals=['executable-project'],classification='test-fixture',
                   row='PE05',owner='fixture owner',reason='Exact fixture')
        for authority in ({'decision':'approved','source_revisions':{}},
                          {'schema':'mcpcli-census-amendment-approval/v2','decision':'approved'},
                          {'decision':'approved','source_revisions':{'references/opaque':self.git(self.repo,'rev-parse','HEAD')}}):
            with self.subTest(authority=authority):
                target, amendment=self.amendment([entry])
                self.write(self.root,'fabricated.json',json.dumps(authority))
                receipt=json.loads((self.root/'decision.json').read_text())
                receipt['authority']=[dict(path='fabricated.json',sha256=census.digest((self.root/'fabricated.json').read_bytes()))]
                self.write(self.root,'decision.json',json.dumps(receipt))
                amendment['approval']['evidence']['sha256']=census.digest((self.root/'decision.json').read_bytes())
                target.write_text(json.dumps(amendment));self.index.write_text(json.dumps([dict(path=target.name,sha256=census.digest(target.read_bytes()))]))
                self.assertEqual(self.run_cli(1)['errors'],[{'rule':'untrusted-amendment-authority'}])

    def test_inventory_authority_requires_complete_approved_root_scope(self):
        for revisions in ({}, {'references/opaque':'0'*40}, {'other/root':'0'*40}):
            with self.subTest(revisions=revisions):
                self.write(self.root,'approval.json',json.dumps(dict(decision='approved',source_revisions=revisions)))
                self.git(self.root,'add','approval.json');self.git(self.root,'commit','-q','-m','test: malformed authority scope')
                self.policy['provenance'][1]['sha256']=census.digest((self.root/'approval.json').read_bytes());self.save()
                self.assertEqual(self.run_cli(1)['errors'],[{'rule':'invalid-inventory-authority-scope'}])

    def test_sdk_comments_do_not_suppress_neutral_executables(self):
        for sdk in ('Microsoft.NET.Sdk.Web','Aspire.AppHost.Sdk'):
            with self.subTest(sdk=sdk):
                path='src/Neutral/Neutral.csproj'
                self.project(path)
                self.write(self.repo,path,(self.repo/path).read_text().replace('<Project ',f'<!-- {sdk} --><Project ',1))
                self.commit(self.repo);self.pin()
                self.assertEqual(self.run_cli(1)['surfaces'][0]['signals'],['executable-project'])
        self.write(self.repo,path,'<Project><Sdk Name="Microsoft.NET.Sdk.Web"/><PropertyGroup><OutputType>Exe</OutputType><IsPackable>false</IsPackable></PropertyGroup></Project>')
        self.commit(self.repo);self.pin();self.assertEqual(self.run_cli(0)['surfaces'],[])

    def test_import_xml_and_uppercase_extensions_are_metadata_and_closure(self):
        for imported in ('eng/runtime.xml','eng/Hidden.PROPS'):
            with self.subTest(imported=imported):
                self.write(self.repo,imported,'<Project><PropertyGroup><OutputType>Exe</OutputType></PropertyGroup></Project>')
                self.write(self.repo,'Directory.Build.props',f'<Project><Import Project="{imported}"/></Project>')
                self.project(metadata='')
                report=self.run_cli(1)
                project=next(surface for surface in report['surfaces'] if surface['surface']['kind']=='project')
                self.assertEqual(project['signals'],['executable-project'])
                tree=census.Tree(self.repo,self.git(self.repo,'rev-parse','HEAD'))
                self.assertIn(imported,{source['path'] for source in census.compilation_closure(tree,PROJECT)})
                self.write(self.repo,imported,'<Project>');self.commit(self.repo);self.pin()
                self.assertIn('malformed-project-metadata:'+imported,self.run_cli(1)['errors'][0]['rule'])
                self.write(self.repo,imported,'<Project/>')

    def test_targets_import_uses_project_defined_properties(self):
        self.write(self.repo,'Directory.Build.targets','<Project><Import Project="$(HostDir)/*.xml"/></Project>')
        self.write(self.repo,'eng/host/actual.xml','<Project><PropertyGroup><OutputType>$(HostKind)</OutputType></PropertyGroup></Project>')
        self.write(self.repo,'unrelated/other.xml','<Project/>')
        self.project(metadata='<HostDir>eng/host</HostDir><HostKind>Exe</HostKind>')
        self.assertEqual(self.run_cli(1)['surfaces'][0]['signals'],['executable-project'])
        tree=census.Tree(self.repo,self.git(self.repo,'rev-parse','HEAD'))
        paths={source['path'] for source in census.compilation_closure(tree,PROJECT)}
        self.assertIn('eng/host/actual.xml',paths)
        self.assertNotIn('unrelated/other.xml',paths)

    def test_effective_sdk_package_identity_cannot_be_renamed_through_assembly(self):
        self.write(self.repo,PROJECT,'<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><PackageId>old</PackageId></PropertyGroup></Project>')
        self.commit(self.repo);self.pin()
        for candidate in self.run_cli(1)['surfaces']:
            self.allowance(surface=candidate['surface'],signals=candidate['signals'])
        self.run_cli(0)
        self.write(self.repo,PROJECT,'<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><AssemblyName>new</AssemblyName></PropertyGroup></Project>')
        self.commit(self.repo);self.pin()
        report=self.run_cli(1)
        self.assertEqual([surface['surface']['identity'] for surface in report['surfaces'] if surface['status']=='rejected'],['package:new'])
        self.assertEqual([surface['surface']['identity'] for surface in report['stale']],['package:old'])
        self.write(self.repo,PROJECT,'<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType></PropertyGroup></Project>')
        self.commit(self.repo);self.pin()
        self.assertIn('package:Runner',[surface['surface']['identity'] for surface in self.run_cli(1)['surfaces']])

    def test_fsharp_vb_attributes_and_direct_construction_add_registration_signal(self):
        self.write(self.repo,PROJECT,'<Project><ItemGroup><PackageReference Include="ModelContextProtocol"/></ItemGroup></Project>')
        self.commit(self.repo);self.pin();self.allowance(signals=['mcp-or-cli-dependency'],classification='dependency-consumer',row='FK03')
        cases=[('Tools.fs','[<McpServerTool>]'),('Tools.vb','<McpServerTool>'),
               ('Tools.cs','McpServer.Create(new StdioServerTransport(options), options); server.RunAsync();'),
               ('Tools.cs','McpServer.Create(transport, options);'),('Tools.vb','<mcpservertool>'),
               ('Tools.cs','new StdioServerTransport(options);')]
        for filename,source in cases:
            with self.subTest(source=source):
                for previous,_ in cases:
                    (self.repo/Path(PROJECT).parent/previous).unlink(missing_ok=True)
                self.write(self.repo,str(Path(PROJECT).parent/filename),source);self.commit(self.repo);self.pin()
                self.assertEqual(self.run_cli(1)['surfaces'][0]['unexpectedSignals'],['mcp-registration'])

    def test_recursive_globs_include_zero_directory_sources_and_imports(self):
        self.write(self.repo,'Directory.Build.props','<Project><Import Project="eng/**/*.xml"/></Project>')
        self.write(self.repo,'eng/root.xml','<Project/>')
        self.write(self.repo,'eng/nested/root.xml','<Project><PropertyGroup><OutputType>Exe</OutputType></PropertyGroup><ItemGroup><Compile Include="$(MSBuildThisFileDirectory)../../shared/**/*.cs"/></ItemGroup></Project>')
        self.write(self.repo,'shared/Root.cs','class Root {}')
        self.project(metadata='')
        tree=census.Tree(self.repo,self.git(self.repo,'rev-parse','HEAD'))
        entry=self.allowance(sources=census.compilation_closure(tree,PROJECT),classification='non-surface-qualification-fixture',row='PA02')
        self.assertTrue({'eng/root.xml','eng/nested/root.xml','shared/Root.cs'} <= {source['path'] for source in entry['sources']})
        entry.update(sourcePrefix=str(Path(PROJECT).parent),compilationClosure=True);self.save();self.run_cli(0)
        self.write(self.repo,'shared/Root.cs','class Root { int Changed; }');self.commit(self.repo);self.pin()
        self.assertEqual(self.run_cli(1)['surfaces'][0]['changedSources'],['shared/Root.cs'])
        self.write(self.repo,'shared/Root.cs','class Root {}')
        self.write(self.repo,'shared/nested/deeper/Added.cs','class Added {}');self.commit(self.repo);self.pin()
        self.assertEqual(self.run_cli(1)['surfaces'][0]['changedSources'],['shared/nested/deeper/Added.cs'])

    def test_imported_compile_paths_are_relative_to_consuming_project(self):
        project='tests/Neutral/Neutral.csproj'
        self.write(self.repo,'Directory.Build.props','<Project><Import Project="eng/linked.xml"/></Project>')
        self.write(self.repo,'eng/linked.xml','<Project><ItemGroup><Compile Include="../../shared/Secondary.cs"/></ItemGroup></Project>')
        self.write(self.repo,'shared/Secondary.cs','class Secondary {}');self.project(project)
        tree=census.Tree(self.repo,self.git(self.repo,'rev-parse','HEAD'))
        sources=census.compilation_closure(tree,project)
        self.assertIn('shared/Secondary.cs',{source['path'] for source in sources})
        entry=self.allowance(surface=self.binding(project,identity='Neutral'),sources=sources)
        entry.update(sourcePrefix='tests/Neutral',compilationClosure=True);self.save();self.run_cli(0)
        self.write(self.repo,'shared/Secondary.cs','class Secondary { int Changed; }');self.commit(self.repo);self.pin()
        self.assertEqual(self.run_cli(1)['surfaces'][0]['changedSources'],['shared/Secondary.cs'])

    def test_conditional_alias_alternatives_cannot_hide_release_executable(self):
        self.project(metadata='<Kind Condition="Release">Exe</Kind><Kind Condition="Debug">Library</Kind><OutputType>$(Kind)</OutputType>')
        self.assertEqual(self.run_cli(1)['surfaces'][0]['signals'],['executable-project'])

    def test_unconsumed_metadata_expands_local_classification_aliases(self):
        self.write(self.repo,'Directory.Build.props','<Project/>')
        self.write(self.repo,'eng/Hidden.props','<Project><PropertyGroup><Kind>Exe</Kind><OutputType>$(Kind)</OutputType></PropertyGroup></Project>')
        self.project(metadata='')
        self.assertEqual(self.run_cli(1)['surfaces'][0]['signals'],['unresolved-tool-metadata'])

    def test_both_json_server_sections_are_validated_and_inspected(self):
        self.write(self.repo,'settings.json',json.dumps(dict(mcpServers={},servers={'neutral':{'command':'neutral'}})))
        self.commit(self.repo);self.pin()
        self.assertEqual(self.run_cli(1)['surfaces'][0]['signals'],['developer-server-configuration'])
        self.write(self.repo,'settings.json',json.dumps(dict(mcpServers={},servers=[])))
        self.commit(self.repo);self.pin()
        self.assertIn('malformed-server-configuration:settings.json',self.run_cli(1)['errors'][0]['rule'])

    def test_container_action_and_supported_yaml_structures_bind_each_identity(self):
        cases=[('.github/workflows/ship.yml','jobs:\n  ship:\n    steps:\n      - uses: docker/build-push-action@v6\n        with:\n          push: true\n          tags: |\n            registry.invalid/neutral:latest\n            registry.invalid/second:latest\n',{'registry.invalid/neutral:latest','registry.invalid/second:latest'}),
               ('deploy/pod.yaml','containers: [{name: neutral, image: registry.invalid/neutral:latest}]',{'registry.invalid/neutral:latest'}),
               ('compose.yaml','services: {neutral: {image: registry.invalid/neutral:latest}}',{'registry.invalid/neutral:latest'}),
               ('kustomization.yaml','images:\n  - name: neutral\n    newName: registry.invalid/neutral\n',{'registry.invalid/neutral'}),
               ('deploy/quoted.yaml','{"containers": [{"image": "registry.invalid/neutral:latest"}]}',{'registry.invalid/neutral:latest'}),
               ('deploy/helm.yaml','image: {repository: registry.invalid/neutral, tag: latest}',{'registry.invalid/neutral'})]
        for path,content,identities in cases:
            with self.subTest(path=path):
                self.write(self.repo,path,content);self.commit(self.repo);self.pin()
                entries=[entry for entry in self.run_cli(1)['surfaces'] if entry['surface']['path']==path]
                self.assertEqual({entry['surface']['identity'] for entry in entries},identities)

    def test_docker_equals_tags_and_extensionless_executable_scripts(self):
        for command in ('docker build --tag=registry.invalid/neutral:1 .',
                        'docker buildx build --tag=registry.invalid/neutral:1 --push .',
                        'docker push registry.invalid/neutral:1','dotnet tool install neutral'):
            with self.subTest(command=command):
                self.write(self.repo,'scripts/ship','#!/usr/bin/env bash\n'+command+'\n')
                (self.repo/'scripts/ship').chmod(0o755);self.commit(self.repo);self.pin()
                entry=self.run_cli(1)['surfaces'][0]
                self.assertEqual(entry['surface']['identity'],'neutral' if 'tool install' in command else 'registry.invalid/neutral:1')
                self.assertEqual(entry['signals'],['tool-install'] if 'tool install' in command else ['container-image'])

    def test_container_identity_alone_has_project_and_publication_candidates(self):
        self.project(metadata='<ContainerRepository>neutral-mcp</ContainerRepository>')
        entries=self.run_cli(1)['surfaces']
        self.assertEqual([(entry['surface']['kind'],entry['surface']['identity'],entry['signals']) for entry in entries],
                         [('project','Runner',['container-identity']),('publication','container:neutral-mcp',['container-metadata'])])

    def test_each_project_language_executable_and_orphan_reference_is_inspected(self):
        for suffix in ('csproj','fsproj','vbproj'):
            with self.subTest(suffix=suffix):
                path=f'outside/Neutral/Neutral.{suffix}';self.project(path)
                self.write(self.repo,'scripts/ship.sh',f'dotnet publish missing/Orphan.{suffix}');self.commit(self.repo);self.pin()
                entries=self.run_cli(1)['surfaces']
                self.assertTrue(any(entry['surface']['path']==path and entry['signals']==['executable-project'] for entry in entries))
                self.assertTrue(any(entry['surface']['identity']==f'missing/Orphan.{suffix}' and entry['signals']==['orphan-project-reference'] for entry in entries))

    def test_unsafe_and_unresolved_publication_paths_fail_with_context(self):
        for target in ('/tmp/Neutral.csproj','../Neutral.csproj',r'C:\tmp\Neutral.csproj',r'C:tmp\Neutral.csproj'):
            self.write(self.repo,'scripts/ship.sh','dotnet publish '+target);self.commit(self.repo);self.pin()
            self.assertIn('unsafe-publication-path:scripts/ship.sh',self.run_cli(1)['errors'][0]['rule'])

    def test_workflow_matrix_project_publications_cannot_hide_orphan_projects(self):
        for matrix in ('project: [missing/Neutral.csproj, missing/Second.fsproj]',
                       'project:\n          - missing/Neutral.csproj\n          - missing/Second.fsproj',
                       'include:\n          - project: missing/Neutral.csproj\n          - project: missing/Second.fsproj'):
            with self.subTest(matrix=matrix):
                self.write(self.repo,'.github/workflows/ship.yml','jobs:\n  ship:\n    strategy:\n      matrix:\n        '+matrix+'\n    steps:\n      - run: dotnet publish ${{ matrix.project }}\n')
                self.commit(self.repo);self.pin()
                self.assertEqual({entry['surface']['identity'] for entry in self.run_cli(1)['surfaces']},{'missing/Neutral.csproj','missing/Second.fsproj'})
        self.write(self.repo,'.github/workflows/ship.yml','jobs:\n  ship:\n    steps:\n      - run: dotnet publish ${{ matrix.unknown }}\n');self.commit(self.repo);self.pin()
        self.assertIn('unresolved-publication-target:.github/workflows/ship.yml',self.run_cli(1)['errors'][0]['rule'])

    def test_workflow_non_target_expressions_do_not_obscure_literal_projects(self):
        self.write(self.repo,'.github/workflows/ship.yml','jobs:\n  ship:\n    steps:\n      - run: dotnet publish missing/Neutral.csproj -c ${{ inputs.configuration }} -p:Version=${{ inputs.version }}\n')
        self.commit(self.repo);self.pin()
        report=self.run_cli(1)
        self.assertEqual(report['errors'],[])
        self.assertEqual([entry['surface']['identity'] for entry in report['surfaces']],['missing/Neutral.csproj'])

    def test_superseded_unconditional_assembly_name_does_not_add_default_package(self):
        self.write(self.repo,'Directory.Build.props','<Project><PropertyGroup><AssemblyName>Old</AssemblyName></PropertyGroup></Project>')
        self.write(self.repo,PROJECT,'<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><AssemblyName>Current</AssemblyName><OutputType>Exe</OutputType></PropertyGroup></Project>')
        self.commit(self.repo);self.pin()
        self.assertEqual([entry['surface']['identity'] for entry in self.run_cli(1)['surfaces']],['Runner','package:Current'])

    def test_new_legacy_receipt_cannot_create_untracked_authority(self):
        self.project()
        sources=[dict(path=PROJECT,sha256=census.digest((self.repo/PROJECT).read_bytes()))]
        entry=dict(surface=self.binding(),signals=['executable-project'],classification='non-surface-qualification-fixture',
                   row='PA01',owner='fixture owner',reason='Exact fixture',sourcePrefix=str(Path(PROJECT).parent),sources=sources)
        target,amendment=self.amendment([entry])
        receipt=dict(schema='mcpcli-census-amendment-approval/v1',decision='approved',owner='fixture owner',
                     fixtures=[dict(repository='references/opaque',gitlink=self.git(self.repo,'rev-parse','HEAD'),
                                    project=PROJECT,sourceClosure=dict(prefix=str(Path(PROJECT).parent),sources=sources))])
        self.write(self.root,'decision.json',json.dumps(receipt))
        amendment['approval']['evidence']['sha256']=census.digest((self.root/'decision.json').read_bytes())
        target.write_text(json.dumps(amendment));self.index.write_text(json.dumps([dict(path=target.name,sha256=census.digest(target.read_bytes()))]))
        self.assertEqual(self.run_cli(1)['errors'],[{'rule':'legacy-amendment-evidence-not-committed'}])
        self.git(self.root,'add','decision.json');self.git(self.root,'commit','-q','-m','test: preserve legacy receipt before correction')
        self.write(self.baseline.parent,'legacy-receipts.json',json.dumps(dict(schema='mcpcli-census-legacy-receipts/v1',baselineSha256=census.digest(self.baseline.read_bytes()),receipts=[])))
        self.assertEqual(self.run_cli(1)['errors'],[{'rule':'untrusted-legacy-amendment-evidence'}])

    def test_unknown_compile_directory_binds_all_local_suffix_matches(self):
        self.write(self.repo,'shared/Secondary.cs','class Secondary {}')
        self.write(self.repo,PROJECT,'<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><IsPackable>false</IsPackable></PropertyGroup><ItemGroup><Compile Include="$(ExternalDir)/shared/**/*.cs"/></ItemGroup></Project>')
        self.commit(self.repo);self.pin()
        tree=census.Tree(self.repo,self.git(self.repo,'rev-parse','HEAD'))
        entry=self.allowance(sources=census.compilation_closure(tree,PROJECT))
        entry.update(sourcePrefix=str(Path(PROJECT).parent),compilationClosure=True);self.save();self.run_cli(0)
        self.write(self.repo,'shared/Secondary.cs','class Secondary { int Changed; }');self.commit(self.repo);self.pin()
        self.assertEqual(self.run_cli(1)['surfaces'][0]['changedSources'],['shared/Secondary.cs'])

    def test_sdk_default_assembly_name_is_available_to_package_aliases(self):
        self.write(self.repo,PROJECT,'<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><PackageId>$(AssemblyName)</PackageId></PropertyGroup></Project>')
        self.commit(self.repo);self.pin()
        report=self.run_cli(1)
        self.assertEqual(report['errors'],[])
        self.assertEqual([entry['surface']['identity'] for entry in report['surfaces']],['Runner','package:Runner'])

    def test_conditional_sdk_import_cannot_suppress_executable(self):
        for sdk in ('Microsoft.NET.Sdk.Web','Aspire.AppHost.Sdk'):
            with self.subTest(sdk=sdk):
                self.write(self.repo,PROJECT,'<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><IsPackable>false</IsPackable></PropertyGroup>'
                           f'<Import Project="Sdk.props" Sdk="{sdk}" Condition="false"/></Project>')
                self.commit(self.repo);self.pin()
                self.assertEqual(self.run_cli(1)['surfaces'][0]['signals'],['executable-project'])

    def test_empty_package_assignment_reapplies_sdk_default(self):
        self.write(self.repo,PROJECT,'<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><PackageId>old</PackageId></PropertyGroup></Project>')
        self.commit(self.repo);self.pin()
        for entry in self.run_cli(1)['surfaces']:
            self.allowance(surface=entry['surface'],signals=entry['signals'])
        self.run_cli(0)
        self.write(self.repo,PROJECT,'<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><PackageId>old</PackageId><PackageId/></PropertyGroup></Project>')
        self.commit(self.repo);self.pin()
        report=self.run_cli(1)
        self.assertEqual([entry['surface']['identity'] for entry in report['surfaces'] if entry['status']=='rejected'],['package:Runner'])
        self.assertEqual([entry['surface']['identity'] for entry in report['stale']],['package:old'])

    def test_default_tool_command_tracks_assembly_and_target_name(self):
        def write_tool(name,target=''):
            self.write(self.repo,PROJECT,'<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><PackAsTool>true</PackAsTool><PackageId>fixed</PackageId>'
                       f'<AssemblyName>{name}</AssemblyName>{target}</PropertyGroup></Project>')
            self.commit(self.repo);self.pin()
        write_tool('old')
        for entry in self.run_cli(1)['surfaces']:
            self.allowance(surface=entry['surface'],signals=entry['signals'])
        self.run_cli(0)
        write_tool('new')
        self.assertEqual([entry['surface']['identity'] for entry in self.run_cli(1)['surfaces'] if entry['status']=='rejected'],['tool:new'])
        write_tool('new','<TargetName>target</TargetName>')
        self.assertEqual([entry['surface']['identity'] for entry in self.run_cli(1)['surfaces'] if entry['status']=='rejected'],['tool:target'])

    def test_reference_item_lists_split_before_classification(self):
        for items in ('<PackageReference Include="Neutral;System.CommandLine"/>',
                      '<ProjectReference Include="../Neutral/Neutral.csproj;../Hidden.Mcp/Hidden.Mcp.csproj"/>'):
            self.write(self.repo,PROJECT,'<Project><ItemGroup>'+items+'</ItemGroup></Project>')
            self.commit(self.repo);self.pin()
            expected='command-line-dependency' if 'PackageReference' in items else 'mcp-or-cli-dependency'
            self.assertEqual(self.run_cli(1)['surfaces'][0]['signals'],[expected])

    def test_unresolved_compile_item_alias_fails_with_context(self):
        self.write(self.repo,'shared/Extra.cs','class Extra {}')
        self.write(self.repo,PROJECT,'<Project><ItemGroup><SharedSource Include="../../../shared/Extra.cs"/><Compile Include="@(SharedSource)"/></ItemGroup></Project>')
        self.commit(self.repo);self.pin()
        self.assertEqual(self.run_cli(1)['errors'][0]['rule'],'unresolved-classification-metadata:'+PROJECT)

    def test_unresolved_xml_directory_glob_includes_local_executable_metadata(self):
        self.write(self.repo,'eng/Hidden.xml','<Project><PropertyGroup><OutputType>Exe</OutputType></PropertyGroup></Project>')
        self.project(metadata='')
        self.write(self.repo,PROJECT,'<Project><Import Project="$(ExternalDir)/*.xml"/></Project>')
        self.commit(self.repo);self.pin()
        self.assertEqual(self.run_cli(1)['surfaces'][0]['signals'],['executable-project'])

    def test_import_conditions_preserve_release_and_debug_alternatives(self):
        self.write(self.repo,'eng/Release.xml','<Project><PropertyGroup><OutputType>Exe</OutputType></PropertyGroup></Project>')
        self.write(self.repo,'eng/Debug.xml','<Project><PropertyGroup><OutputType>Library</OutputType></PropertyGroup></Project>')
        self.write(self.repo,PROJECT,'<Project><Import Project="../../../eng/Release.xml" Condition="Release"/>'
                   '<Import Project="../../../eng/Debug.xml" Condition="Debug"/></Project>')
        self.commit(self.repo);self.pin()
        self.assertEqual(self.run_cli(1)['surfaces'][0]['signals'],['executable-project'])

    def test_continued_container_commands_and_push_options_bind_images(self):
        for command in ('docker build \\\n  --tag registry.invalid/neutral:1 .',
                        'docker buildx build \\\n  --tag=registry.invalid/neutral:1 --push .',
                        'docker push --all-tags registry.invalid/neutral:1',
                        'docker push -a --quiet registry.invalid/neutral:1'):
            with self.subTest(command=command):
                self.write(self.repo,'scripts/ship.sh',command);self.commit(self.repo);self.pin()
                entries=self.run_cli(1)['surfaces']
                self.assertEqual([(entry['surface']['identity'],entry['signals']) for entry in entries],
                                 [('registry.invalid/neutral:1',['container-image'])])

    def test_quoted_project_targets_preserve_full_path_identity(self):
        for filename,prefix in (('scripts/ship.sh',''),('.github/workflows/ship.yml','jobs:\n  ship:\n    steps:\n      - run: ')):
            with self.subTest(filename=filename):
                self.write(self.repo,filename,prefix+'dotnet publish "missing/Old Runner.csproj"')
                self.commit(self.repo);self.pin()
                candidates=[entry for entry in self.run_cli(1)['surfaces'] if entry['surface']['path']==filename]
                self.assertEqual([entry['surface']['identity'] for entry in candidates],['missing/Old Runner.csproj'])
                self.allowance(surface=candidates[0]['surface'],signals=candidates[0]['signals'])
                self.write(self.repo,filename,prefix+'dotnet publish "missing/New Runner.csproj"')
                self.commit(self.repo);self.pin()
                entries=[entry for entry in self.run_cli(1)['surfaces'] if entry['surface']['path']==filename and entry['status']=='rejected']
                self.assertEqual([entry['surface']['identity'] for entry in entries],['missing/New Runner.csproj'])


if __name__=='__main__':
    unittest.main()
