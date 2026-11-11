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
import sys
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

    def test_unknown_compile_directory_refuses_incomplete_local_suffix_coverage(self):
        self.write(self.repo,'shared/Secondary.cs','class Secondary {}')
        self.write(self.repo,PROJECT,'<Project><ItemGroup><Compile Include="$(ExternalDir)/shared/**/*.cs"/></ItemGroup></Project>')
        self.commit(self.repo);self.pin()
        report=self.run_cli(1)
        self.assertEqual([e['rule'] for e in report['errors']],['unresolved-compile-source:'+PROJECT])
        self.assertEqual(report['surfaces'],[])

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

    def test_literal_compile_item_alias_resolves_committed_source(self):
        self.write(self.repo,'shared/Extra.cs','class Extra {}')
        self.write(self.repo,PROJECT,'<Project><ItemGroup><SharedSource Include="../../../shared/Extra.cs"/><Compile Include="@(SharedSource)"/></ItemGroup></Project>')
        self.commit(self.repo);self.pin()
        report=self.run_cli(0)
        self.assertEqual(report['errors'],[])
        tree=census.Tree(self.repo,self.git(self.repo,'rev-parse','HEAD'))
        self.assertEqual([s['path'] for s in census.compilation_closure(tree,PROJECT)],[PROJECT,'shared/Extra.cs'])

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

    def assert_source_errors(self, report, path, rules, targets=None):
        pin = self.git(self.repo, 'rev-parse', 'HEAD')
        self.assertEqual(report['errors'], [dict(repository='references/opaque', gitlink=pin,
            path=path, rule=rule + ':' + path, **({'target': target} if target else {}))
            for rule, target in zip(rules, targets or [None] * len(rules))])

    def test_literal_shell_variables_loops_functions_and_aliases_resolve_exact_targets(self):
        path = 'scripts/ship.sh'
        self.write(self.repo, path, '''root=missing
ship() {
  local flavor="$1"
  local project="${root}/${flavor}/${flavor}.csproj"
  dotnet publish "$project"
}
for flavor in First Second; do
  ship "$flavor"
done
''')
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assertEqual(report['errors'], [])
        self.assertEqual([(e['surface'], e['signals'], e['sources']) for e in report['surfaces']],
            [(self.binding(path, 'publication', f'missing/{name}/{name}.csproj'),
              ['orphan-project-reference'], [path]) for name in ('First', 'Second')])

    def test_finite_loop_present_libraries_have_no_proprietary_surface(self):
        for name in ('First', 'Second'):
            self.write(self.repo, f'src/{name}/{name}.csproj', '<Project Sdk="Microsoft.NET.Sdk"/>')
        self.write(self.repo, '.github/workflows/ci.yml', '''jobs:
  pack:
    steps:
      - run: |
          for package in First Second; do
            dotnet pack "src/${package}/${package}.csproj" -p:Version=${{ inputs.version }}
          done
''')
        self.commit(self.repo); self.pin()
        self.assertEqual(self.run_cli(0)['surfaces'], [])

    def test_shell_target_unknown_substitution_and_unsupported_parameters_refuse(self):
        path = 'scripts/ship.sh'
        for script in ('dotnet publish "$runtime"', 'target="$(printf missing/X.csproj)"\ndotnet publish "$target"',
                       'target=missing/X.csproj\ndotnet publish "${target:-missing/Y.csproj}"',
                       "target='$RUNTIME'\ndotnet publish \"$target\""):
            with self.subTest(script=script):
                self.write(self.repo, path, script); self.commit(self.repo); self.pin()
                report = self.run_cli(1)
                self.assertEqual(report['surfaces'], [])
                self.assert_source_errors(report, path, ['unresolved-publication-target'])

    def test_unbounded_shell_loop_refuses_and_retains_literal_observations(self):
        path = 'scripts/ship.sh'
        self.write(self.repo, path, 'while read package; do\n dotnet pack missing/Neutral.csproj\ndone')
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assert_source_errors(report, path, ['unbounded-publication-control-flow'])
        self.assertEqual([e['surface'] for e in report['surfaces']], [self.binding(path, 'publication', 'missing/Neutral.csproj')])

    def test_shell_iteration_and_expansion_limits_refuse(self):
        path = 'scripts/ship.sh'
        scripts = [
            'for item in ' + ' '.join('P' + str(i) for i in range(257)) + '; do\n dotnet pack "missing/${item}.csproj"\ndone',
            'target=missing/P0.csproj\nif true; then\n' + '\n'.join('target=missing/P' + str(i) + '.csproj' for i in range(1, 257)) + '\nfi\ndotnet pack "$target"',
        ]
        for script in scripts:
            with self.subTest(script=script[:30]):
                self.write(self.repo, path, script); self.commit(self.repo); self.pin()
                report = self.run_cli(1)
                self.assertEqual(report['surfaces'], [])
                self.assertIn('unresolved-publication-target:' + path, [e['rule'] for e in report['errors']])

    def test_shell_recursion_and_command_budgets_refuse(self):
        path = 'scripts/ship.sh'
        for script in ('ship() {\n dotnet publish missing/Neutral.csproj\n ship\n}\nship',
                       ':\n' * 8193 + 'dotnet publish missing/Neutral.csproj'):
            with self.subTest(script=script[:30]):
                self.write(self.repo, path, script); self.commit(self.repo); self.pin()
                report = self.run_cli(1)
                self.assert_source_errors(report, path, ['unbounded-publication-control-flow'])
                self.assertEqual([e['surface']['identity'] for e in report['surfaces']],
                                 ['missing/Neutral.csproj'] if script.startswith('ship') else [])

    def test_working_directory_parent_paths_and_subshell_restore_are_contained(self):
        path = 'scripts/ship.sh'
        self.write(self.repo, 'work/placeholder.txt', 'committed')
        self.write(self.repo, path, '(\n cd work\n dotnet pack ../missing/Inside.csproj\n)\ndotnet publish missing/Outside.csproj')
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assertEqual(report['errors'], [])
        self.assertEqual([e['surface']['identity'] for e in report['surfaces']], ['missing/Inside.csproj', 'missing/Outside.csproj'])
        self.write(self.repo, path, 'cd work\ndotnet publish ../../Escape.csproj'); self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assert_source_errors(report, path, ['unsafe-publication-path'])
        self.assertEqual(report['surfaces'], [])

    def test_yaml_working_directory_and_step_state_isolation(self):
        path = '.github/workflows/ci.yml'
        self.write(self.repo, 'work/placeholder.txt', 'committed')
        self.write(self.repo, path, '''jobs:
  pack:
    steps:
      - run: dotnet publish ../missing/Inside.csproj
        working-directory: work
      - run: |
          target=missing/StepOne.csproj
          dotnet publish "$target"
      - run: dotnet publish "$target"
''')
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assert_source_errors(report, path, ['unresolved-publication-target'])
        self.assertEqual([e['surface']['identity'] for e in report['surfaces']], ['missing/Inside.csproj', 'missing/StepOne.csproj'])

    def test_unknown_missing_and_conditional_working_directories_refuse(self):
        path = 'scripts/ship.sh'
        for script in ('cd "$runtime"\ndotnet publish missing/X.csproj',
                       'cd absent\ndotnet publish missing/X.csproj',
                       'if condition; then\n cd work\nfi\ndotnet publish missing/X.csproj'):
            with self.subTest(script=script):
                self.write(self.repo, 'work/placeholder.txt', 'committed')
                self.write(self.repo, path, script); self.commit(self.repo); self.pin()
                report = self.run_cli(1)
                self.assert_source_errors(report, path, ['unresolved-publication-directory'])
                self.assertEqual(report['surfaces'], [])

    def test_source_relative_root_locator_and_nested_targets_never_open_nested_repo(self):
        path = 'scripts/ship.sh'
        self.write(self.repo, path, '''repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
producer_root="$repository_root/dependencies/producer"
cd "$producer_root"
for package in First Second; do
 dotnet pack "src/${package}/${package}.csproj"
done
''')
        pin = self.git(self.repo, 'rev-parse', 'HEAD')
        self.git(self.repo, 'add', path)
        self.git(self.repo, 'update-index', '--add', '--cacheinfo', f'160000,{pin},dependencies/producer')
        self.git(self.repo, 'commit', '-q', '-m', 'test: retain nested target pin'); self.pin()
        # No nested worktree exists. Every Git read must stay at the root repo.
        original = census.git
        with patch.object(census, 'git', side_effect=lambda repo, *args, **kwargs: original(repo, *args, **kwargs)) as reads:
            report = self.run_cli(1)
        self.assertEqual([e['target'] for e in report['errors']],
                         ['dependencies/producer/src/First/First.csproj', 'dependencies/producer/src/Second/Second.csproj'])
        self.assertEqual({e['rule'] for e in report['errors']}, {'nested-publication-target:' + path})
        self.assertEqual(report['surfaces'], [])
        self.assertFalse((self.repo / 'dependencies/producer').exists())
        self.assertTrue(all(Path(call.args[0]) in (self.repo, self.root) for call in reads.call_args_list))

    def test_compile_item_aliases_bind_imported_properties_globs_and_registration(self):
        self.write(self.repo, 'shared/Root.cs', 'class Root {}')
        self.write(self.repo, 'shared/deep/Extra.cs', 'builder.Services.AddMcpServer();')
        self.write(self.repo, 'eng/items.xml', '<Project><PropertyGroup><SourceRoot>../../../shared</SourceRoot></PropertyGroup>'
                   '<ItemGroup><First Include="$(SourceRoot)/**/*.cs"/><Second Include="@(First)"/></ItemGroup></Project>')
        self.write(self.repo, PROJECT, '<Project><Import Project="../../../eng/items.xml"/>'
                   '<ItemGroup><Compile Include="@(Second)"/></ItemGroup></Project>')
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assertEqual(report['errors'], [])
        self.assertEqual([e['surface'] for e in report['surfaces']],
                         [self.binding(), self.binding('shared/deep/Extra.cs', 'source', 'shared/deep/Extra.cs')])
        self.assertEqual(report['surfaces'][0]['signals'], ['mcp-registration'])
        tree = census.Tree(self.repo, self.git(self.repo, 'rev-parse', 'HEAD'))
        self.assertEqual([s['path'] for s in census.compilation_closure(tree, PROJECT)],
                         ['eng/items.xml', PROJECT, 'shared/Root.cs', 'shared/deep/Extra.cs'])

    def test_generated_compile_task_output_refuses_with_producer_and_keeps_project(self):
        self.write(self.repo, PROJECT, '<Project><PropertyGroup><OutputType>Exe</OutputType></PropertyGroup>'
                   '<Target Name="Generate"><Copy SourceFiles="obj/*.g.cs" DestinationFolder="obj/copied">'
                   '<Output TaskParameter="DestinationFiles" ItemName="Generated"/></Copy>'
                   '<ItemGroup><Compile Include="@(Generated)"/></ItemGroup></Target></Project>')
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assertEqual([e['rule'] for e in report['errors']], ['dynamic-generated-compile-source:' + PROJECT + ':generated'])
        self.assertEqual([e['surface'] for e in report['surfaces']], [self.binding()])
        self.assertEqual(report['surfaces'][0]['signals'], ['executable-project'])

    def test_compile_item_cycles_unknown_aliases_and_transforms_refuse(self):
        variants = [('<First Include="@(Second)"/><Second Include="@(First)"/>', '@(First)', 'cyclic-compile-item:' + PROJECT + ':first'),
                    ('', '@(Unknown)', 'unresolved-compile-item:' + PROJECT + ':unknown'),
                    ('<First Include="../../../shared/Root.cs"/>', "@(First->'%(FullPath)')", 'unresolved-compile-source:' + PROJECT)]
        self.write(self.repo, 'shared/Root.cs', 'class Root {}')
        for definitions, value, rule in variants:
            with self.subTest(value=value):
                self.write(self.repo, PROJECT, '<Project><ItemGroup>' + definitions + '<Compile Include="' + value + '"/></ItemGroup></Project>')
                self.commit(self.repo); self.pin()
                report = self.run_cli(1)
                self.assertEqual([e['rule'] for e in report['errors']], [rule])
                self.assertEqual(report['surfaces'], [])

    def test_compile_item_depth_and_cardinality_are_bounded(self):
        self.write(self.repo, 'shared/Root.cs', 'class Root {}')
        definitions = ''.join(f'<Item{i} Include="@(Item{i+1})"/>' for i in range(33)) + '<Item33 Include="../../../shared/Root.cs"/>'
        self.write(self.repo, PROJECT, '<Project><ItemGroup>' + definitions + '<Compile Include="@(Item0)"/></ItemGroup></Project>')
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assertEqual([e['rule'] for e in report['errors']], ['cyclic-compile-item:' + PROJECT + ':item31'])
        for index in range(4097):
            self.write(self.repo, f'shared/Item{index}.cs', 'class Item {}')
        self.write(self.repo, PROJECT, '<Project><ItemGroup><Compile Include="../../../shared/*.cs"/></ItemGroup></Project>')
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assert_source_errors(report, PROJECT, ['unbounded-compile-items'])
        self.assertEqual(report['surfaces'], [])

    def test_compile_source_escape_missing_and_nested_inputs_refuse(self):
        pin = self.git(self.repo, 'rev-parse', 'HEAD')
        self.git(self.repo, 'update-index', '--add', '--cacheinfo', f'160000,{pin},dependencies/nested')
        self.git(self.repo, 'commit', '-q', '-m', 'test: retain nested compile pin'); self.pin()
        # An escape outside every root and a nested pin without a declared URL stay refused.
        for target, rule, label in (('../../../../Escape.cs', 'unsafe-or-nested-compile-source', '../Escape.cs'),
                                    ('../../../dependencies/nested/Code.cs', 'nested-pin-unresolvable', 'dependencies/nested/Code.cs'),
                                    ('../../../missing/Code.cs', 'unavailable-committed-compile-source', None)):
            with self.subTest(target=target):
                self.write(self.repo, PROJECT, '<Project><ItemGroup><Compile Include="' + target + '"/></ItemGroup></Project>')
                self.git(self.repo, 'add', PROJECT)
                self.git(self.repo, 'update-index', '--add', '--cacheinfo', f'160000,{pin},dependencies/nested')
                self.git(self.repo, 'commit', '-q', '-m', 'test: pin compile source refusal'); self.pin()
                report = self.run_cli(1)
                self.assert_source_errors(report, PROJECT, [rule], [label])
                self.assertEqual(report['surfaces'], [])

    def test_partial_root_keeps_other_projects_sources_and_publication_observations(self):
        self.write(self.repo, 'broken/Broken.csproj', '<Project>')
        self.write(self.repo, 'broken/Program.cs', 'builder.Services.AddMcpServer();')
        self.write(self.repo, 'shared/Standalone.cs', 'using System.CommandLine;')
        self.write(self.repo, 'release.json', '{"packages":"malformed"}')
        self.write(self.repo, 'scripts/ship.sh', 'dotnet publish missing/Orphan.csproj')
        self.project()
        report = self.run_cli(1)
        self.assertEqual([e['surface'] for e in report['surfaces']], [
            self.binding('broken/Program.cs', 'source', 'broken/Program.cs'), self.binding(),
            self.binding('scripts/ship.sh', 'publication', 'missing/Orphan.csproj'),
            self.binding('shared/Standalone.cs', 'source', 'shared/Standalone.cs')])
        self.assertEqual([(e['path'], e['rule']) for e in report['errors']],
                         [('broken/Broken.csproj', 'malformed-project-metadata:broken/Broken.csproj'),
                          ('release.json', 'malformed-publication:release.json')])
        self.assertFalse(report['repositories'][0]['inspectionComplete'])
        self.assertEqual(report['stale'], [])

    def test_literal_shell_loop_order_preserves_directory_state(self):
        path = 'scripts/ship.sh'
        self.write(self.repo, 'b/a/placeholder.txt', 'committed')
        self.write(self.repo, path, 'for segment in b a; do\n cd "$segment"\n dotnet publish Runner.csproj\ndone')
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assertEqual(report['errors'], [])
        self.assertEqual([e['surface']['identity'] for e in report['surfaces']], ['b/Runner.csproj', 'b/a/Runner.csproj'])

    def test_short_circuit_directory_state_cannot_select_an_approved_identity(self):
        path = 'scripts/ship.sh'
        self.write(self.repo, 'child/placeholder.txt', 'committed')
        self.allowance(self.binding(path, 'publication', 'child/Runner.csproj'), ['orphan-project-reference'])
        for script in ('false && cd child\ndotnet publish Runner.csproj',
                       'true || cd child\ndotnet publish Runner.csproj',
                       'false && target=child/Runner.csproj\ndotnet publish "$target"'):
            with self.subTest(script=script):
                self.write(self.repo, path, script); self.commit(self.repo); self.pin()
                report = self.run_cli(1)
                self.assertEqual(report['surfaces'], [])
                self.assertTrue(report['errors'])
                self.assertEqual(report['stale'], [])

    def test_workflow_and_job_default_directories_override_root_identity(self):
        path = '.github/workflows/ci.yml'
        self.write(self.repo, 'global/placeholder.txt', 'committed')
        self.write(self.repo, 'local/placeholder.txt', 'committed')
        self.allowance(self.binding(path, 'publication', 'Runner.csproj'), ['orphan-project-reference'])
        self.write(self.repo, path, """defaults:
  run:
    working-directory: global
jobs:
  first:
    steps:
      - run: dotnet publish Runner.csproj
  second:
    defaults:
      run:
        working-directory: local
    steps:
      - run: dotnet publish Runner.csproj
""")
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assertEqual(report['errors'], [])
        self.assertEqual([e['surface']['identity'] for e in report['surfaces']], ['global/Runner.csproj', 'local/Runner.csproj'])
        self.write(self.repo, path, """defaults:
  run:
    working-directory: ${{ inputs.directory }}
jobs:
  first:
    steps:
      - run: dotnet publish Runner.csproj
""")
        self.commit(self.repo); self.pin()
        self.assert_source_errors(self.run_cli(1), path, ['unresolved-publication-directory'])

    def test_allowance_closure_failure_keeps_later_candidates_and_suppresses_staleness(self):
        self.project()
        tree = census.Tree(self.repo, self.git(self.repo, 'rev-parse', 'HEAD'))
        entry = self.allowance(sources=census.compilation_closure(tree, PROJECT))
        entry.update(sourcePrefix=str(Path(PROJECT).parent), compilationClosure=True)
        self.allowance(self.binding('removed/Removed.csproj', 'project', 'Removed'))
        self.save()
        self.write(self.repo, 'scripts/ship.sh', 'dotnet publish missing/Later.csproj')
        self.commit(self.repo); self.pin()
        with patch.object(census, 'compilation_closure', side_effect=census.CensusError('unresolved-compile-source:' + PROJECT)):
            report = self.run_cli(1)
        self.assertEqual([e['surface'] for e in report['surfaces']], [self.binding(), self.binding('scripts/ship.sh', 'publication', 'missing/Later.csproj')])
        self.assertEqual(report['surfaces'][0]['reason'], 'allowance-source-inspection-failed')
        self.assert_source_errors(report, PROJECT, ['unresolved-compile-source'])
        self.assertFalse(report['repositories'][0]['inspectionComplete'])
        self.assertEqual(report['stale'], [])

    def test_finite_shell_call_depth_limit_refuses_before_unbounded_traversal(self):
        path = 'scripts/ship.sh'
        body = '\n'.join(f'f{i}() {{\n f{i+1}\n}}' for i in range(18))
        self.write(self.repo, path, body + '\nf18() {\n dotnet publish missing/TooDeep.csproj\n}\nf0')
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assert_source_errors(report, path, ['unbounded-publication-control-flow'])
        self.assertEqual([e['surface']['identity'] for e in report['surfaces']], ['missing/TooDeep.csproj'])

    def test_copy_output_provenance_binds_committed_bytes_without_running_copy(self):
        self.write(self.repo, 'shared/Original.cs', 'builder.Services.AddMcpServer();')
        self.write(self.repo, PROJECT, '<Project><Target Name="CopySource">'
                   '<Copy SourceFiles="../../../shared/Original.cs" DestinationFolder="obj/copied">'
                   '<Output TaskParameter="DestinationFiles" ItemName="Copied"/></Copy>'
                   '<ItemGroup><Compile Include="@(Copied)"/></ItemGroup></Target></Project>')
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assertEqual(report['errors'], [])
        self.assertEqual(report['surfaces'][0]['surface'], self.binding())
        self.assertEqual(report['surfaces'][0]['signals'], ['mcp-registration'])
        self.assertEqual(report['surfaces'][0]['sources'], ['shared/Original.cs'])
        self.assertFalse((self.repo / 'odd/location/Runner/obj').exists())
        tree = census.Tree(self.repo, self.git(self.repo, 'rev-parse', 'HEAD'))
        self.assertEqual([e['path'] for e in census.compilation_closure(tree, PROJECT)], [PROJECT, 'shared/Original.cs'])

    def test_function_global_assignments_and_local_shadowing_select_actual_target(self):
        path = 'scripts/ship.sh'
        self.allowance(self.binding(path, 'publication', 'missing/Original.csproj'), ['orphan-project-reference'])
        self.write(self.repo, path, """target=missing/Original.csproj
set_target() {
 target=missing/Global.csproj
}
local_target() {
 local target=missing/Local.csproj
 dotnet pack "$target"
}
set_target
local_target
dotnet publish "$target"
""")
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assertEqual(report['errors'], [])
        self.assertEqual([e['surface']['identity'] for e in report['surfaces']], ['missing/Global.csproj', 'missing/Local.csproj'])

    def test_directory_solution_and_implicit_targets_resolve_committed_projects(self):
        path = 'scripts/ship.sh'
        self.write(self.repo, 'apps/First/First.csproj', '<Project><PropertyGroup><OutputType>Exe</OutputType></PropertyGroup></Project>')
        self.write(self.repo, 'apps/Second/Second.csproj', '<Project/>')
        self.write(self.repo, 'Repo.slnx', '<Solution><Project Path="apps/First/First.csproj"/><Project Path="apps/Second/Second.csproj"/></Solution>')
        self.write(self.repo, path, 'dotnet publish apps/First\ndotnet run --project apps/Second\ndotnet pack Repo.slnx\ndotnet publish')
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assertEqual(report['errors'], [])
        self.assertEqual([e['surface'] for e in report['surfaces']],
                         [self.binding('apps/First/First.csproj', 'project', 'First'),
                          self.binding(path, 'publication', 'apps/First/First.csproj')])
        self.assertEqual(report['surfaces'][1]['signals'], ['project-publication-reference'])

    def test_missing_ambiguous_directory_and_unsupported_solution_targets_refuse(self):
        path = 'scripts/ship.sh'
        self.write(self.repo, 'apps/First.csproj', '<Project/>')
        self.write(self.repo, 'apps/Second.csproj', '<Project/>')
        for target in ('missing-directory', 'apps', 'missing.slnx', 'old.sln'):
            with self.subTest(target=target):
                self.write(self.repo, path, 'dotnet publish --project ' + target)
                self.commit(self.repo); self.pin()
                report = self.run_cli(1)
                self.assertEqual([e['rule'] for e in report['errors']], ['unresolved-publication-target:' + path])
                self.assertEqual([e['target'] for e in report['errors']], [target])
                self.assertEqual(report['surfaces'], [])

    def test_unresolved_and_unbounded_solution_metadata_refuse(self):
        path = 'scripts/ship.sh'
        for content in ('<Solution/>', '<Solution><Project Path="$(Runtime)"/></Solution>',
                        '<Solution>' + '<Project Path="missing/Runner.csproj"/>' * 4097 + '</Solution>'):
            with self.subTest(content=content[:50]):
                self.write(self.repo, 'Repo.slnx', content)
                self.write(self.repo, path, 'dotnet pack Repo.slnx')
                self.commit(self.repo); self.pin()
                report = self.run_cli(1)
                self.assertEqual([e['rule'] for e in report['errors']], ['unresolved-publication-solution:' + path])
                self.assertEqual(report['surfaces'], [])

    def test_unknown_task_output_cannot_supply_committed_compile_bytes(self):
        self.write(self.repo, PROJECT, '<Project><Target Name="Generate"><Exec Command="runtime-generator">'
                   '<Output TaskParameter="Output" ItemName="Runtime"/></Exec>'
                   '<ItemGroup><Compile Include="@(Runtime)"/></ItemGroup></Target></Project>')
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assertEqual([e['rule'] for e in report['errors']], ['dynamic-generated-compile-source:' + PROJECT + ':runtime'])
        self.assertEqual(report['surfaces'], [])

    def test_unterminated_loop_and_malformed_shell_target_refuse(self):
        path = 'scripts/ship.sh'
        for script, rule in (('for package in One Two; do\n dotnet publish missing/X.csproj', 'unbounded-publication-control-flow'),
                             ('dotnet publish "unterminated', 'unresolved-publication-target')):
            with self.subTest(script=script):
                self.write(self.repo, path, script); self.commit(self.repo); self.pin()
                report = self.run_cli(1)
                self.assert_source_errors(report, path, [rule])
                self.assertEqual(report['surfaces'], [])

    def test_single_quoted_target_and_external_state_cannot_select_approved_identity(self):
        path = 'scripts/ship.sh'
        self.allowance(self.binding(path, 'publication', 'missing/Allowed.csproj'), ['orphan-project-reference'])
        for script in ("target=missing/Allowed.csproj\ndotnet publish '$target'",
                       'target=missing/Allowed.csproj\nsource runtime.sh\ndotnet publish "$target"'):
            with self.subTest(script=script):
                self.write(self.repo, path, script); self.commit(self.repo); self.pin()
                report = self.run_cli(1)
                self.assert_source_errors(report, path, ['unresolved-publication-target'])
                self.assertEqual(report['surfaces'], [])

    def test_excluded_source_drift_keeps_unrelated_project_observations(self):
        path = 'captured/metadata.xml'
        self.write(self.repo, path, '<Project/>')
        self.policy['exclusions'] = [dict(repository='references/opaque', prefix=path, row='PE05',
            classification='test-fixture', owner='fixture owner', reason='Exact source', scope='file',
            sha256=census.digest(b'<Project/>'))]
        self.save()
        self.project()
        self.write(self.repo, path, '<Project Changed="true"/>'); self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assert_source_errors(report, path, ['excluded-fixture-source-drift'])
        self.assertEqual([e['surface'] for e in report['surfaces']], [self.binding()])
        self.assertFalse(report['repositories'][0]['inspectionComplete'])

    def test_missing_source_blob_keeps_other_committed_project_observations(self):
        path = 'bad/Bad.csproj'
        self.write(self.repo, path, '<Project/>')
        self.project()
        oid = self.git(self.repo, 'rev-parse', 'HEAD:' + path)
        (self.repo / '.git/objects' / oid[:2] / oid[2:]).unlink()
        report = self.run_cli(1)
        self.assertEqual(report['errors'], [dict(repository='references/opaque', gitlink=self.git(self.repo, 'rev-parse', 'HEAD'), path=path, rule='git-object-unavailable')])
        self.assertEqual([e['surface'] for e in report['surfaces']], [self.binding()])
        self.assertFalse(report['repositories'][0]['inspectionComplete'])

    def test_ambiguous_loop_word_cannot_become_a_sequential_approved_directory_list(self):
        path = 'scripts/ship.sh'
        for directory in ('a/b', 'b'):
            self.write(self.repo, directory + '/placeholder.txt', 'committed')
        for target in ('a/Runner.csproj', 'a/b/Runner.csproj'):
            self.allowance(self.binding(path, 'publication', target), ['orphan-project-reference'])
        self.write(self.repo, path, 'directory=a\nif runtime; then\n directory=b\nfi\n'
                   'for segment in "$directory"; do\n cd "$segment"\n dotnet publish Runner.csproj\ndone')
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assert_source_errors(report, path, ['unbounded-publication-control-flow', 'unresolved-publication-directory'])
        self.assertEqual(report['surfaces'], [])

    def test_review_s01_inline_loop_is_explicitly_refused(self):
        path = 'scripts/ship.sh'
        self.write(self.repo, path, 'for p in missing/One.csproj; do dotnet publish "$p"; done')
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assert_source_errors(report, path, ['unsupported-inline-publication-control-flow'])
        self.assertEqual(report['surfaces'], [])

    def test_review_s02_quoted_dotnet_retains_exact_project_target(self):
        path = 'scripts/ship.sh'
        for command in ('"dotnet" publish "missing/One Runner.csproj"', "'dotnet' publish 'missing/One Runner.csproj'"):
            with self.subTest(command=command):
                self.write(self.repo, path, command); self.commit(self.repo); self.pin()
                report = self.run_cli(1)
                self.assertEqual(report['errors'], [])
                self.assertEqual([e['surface'] for e in report['surfaces']], [self.binding(path, 'publication', 'missing/One Runner.csproj')])
                self.assertEqual(report['surfaces'][0]['signals'], ['orphan-project-reference'])

    def test_review_s03_container_global_options_and_image_subcommand(self):
        path = 'scripts/ship.sh'
        commands = ['docker --context production push attacker/neutral:latest',
                    'docker --context=production image push attacker/neutral:latest',
                    'docker image push attacker/neutral:latest',
                    'docker --host tcp://example.invalid --debug image push --all-tags attacker/neutral:latest']
        for command in commands:
            with self.subTest(command=command):
                self.write(self.repo, path, command); self.commit(self.repo); self.pin()
                report = self.run_cli(1)
                self.assertEqual(report['errors'], [])
                self.assertEqual([e['surface'] for e in report['surfaces']], [self.binding(path, 'publication', 'attacker/neutral:latest')])
                self.assertEqual(report['surfaces'][0]['signals'], ['container-image'])

    def test_review_s04_quoted_matrix_targets_keep_alternatives_paths_and_scope(self):
        path = '.github/workflows/ci.yml'
        for name in ('One', 'Two'):
            self.write(self.repo, f'src/{name}/{name}.csproj', '<Project/>')
        self.write(self.repo, path, '''jobs:
  ordinary:
    strategy:
      matrix:
        project: [src/One/One.csproj, src/Two/Two.csproj]
    steps:
      - run: dotnet publish "${{ matrix.project }}"
''')
        self.commit(self.repo); self.pin()
        self.assertEqual(self.run_cli(0)['surfaces'], [])
        self.write(self.repo, 'work/placeholder.txt', 'committed')
        self.write(self.repo, path, '''jobs:
  first:
    strategy:
      matrix:
        project: ["missing/One Runner.csproj", "missing/Two Runner.csproj"]
    steps:
      - run: dotnet publish "${{ matrix.project }}"
        working-directory: work
  second:
    strategy:
      matrix:
        project: [missing/Third.csproj]
    steps:
      - run: dotnet publish "${{ matrix.project }}"
''')
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assertEqual(report['errors'], [])
        self.assertEqual([e['surface']['identity'] for e in report['surfaces']],
                         ['missing/Third.csproj', 'work/missing/One Runner.csproj', 'work/missing/Two Runner.csproj'])
        self.assertEqual([e['signals'] for e in report['surfaces']], [['orphan-project-reference']] * 3)

        values = ', '.join(f'missing/Project{i}.csproj' for i in range(257))
        self.write(self.repo, path, 'jobs:\n  bounded:\n    strategy:\n      matrix:\n        project: [' + values + ']\n    steps:\n      - run: dotnet publish "${{ matrix.project }}"\n')
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assert_source_errors(report, path, ['unresolved-publication-target'])
        self.assertEqual(report['surfaces'], [])

    def test_review_s05_unquoted_heredoc_substitutions_refuse_without_executing(self):
        path = 'scripts/ship.sh'
        for substitution in ('$(dotnet publish missing/One.csproj)', '`dotnet publish missing/One.csproj`'):
            self.write(self.repo, path, 'cat <<EOF\n' + substitution + '\nEOF')
            self.commit(self.repo); self.pin()
            report = self.run_cli(1)
            self.assert_source_errors(report, path, ['unresolved-heredoc-substitution'])
            self.assertEqual(report['surfaces'], [])
        self.write(self.repo, path, 'cat <<\'EOF\'\n$(dotnet publish missing/One.csproj)\nEOF')
        self.commit(self.repo); self.pin()
        self.assertEqual(self.run_cli(0)['surfaces'], [])

    def test_review_s06_container_requires_complete_declared_provenance(self):
        path = 'scripts/ship.sh'
        project = 'src/Neutral/Neutral.csproj'
        self.write(self.repo, project, '<Project/>')
        self.write(self.repo, path, 'docker push attacker/neutral:latest')
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assertEqual(report['errors'], [])
        self.assertEqual([e['surface'] for e in report['surfaces']], [self.binding(path, 'publication', 'attacker/neutral:latest')])
        self.write(self.repo, project, '<Project><PropertyGroup><ContainerRepository>attacker/neutral:latest</ContainerRepository></PropertyGroup></Project>')
        self.commit(self.repo); self.pin()
        self.assertEqual(self.run_cli(0)['surfaces'], [])

    def test_review_s07_required_optional_sdk_and_nested_imports_are_distinct(self):
        for imports, expected, label in [('<Import Project="../../../missing.props"/>', 'unavailable-local-import', None),
                                         ('<Import Project="../../../../outside.props"/>', 'unsafe-import-path', '../outside.props'),
                                         ('<Import Project="../../../missing.props" Condition="Exists(\'../../../missing.props\')"/>', None, None),
                                         ('<Import Project="Sdk.props" Sdk="Microsoft.NET.Sdk"/>', None, None)]:
            with self.subTest(imports=imports):
                self.write(self.repo, PROJECT, '<Project>' + imports + '</Project>')
                self.commit(self.repo); self.pin()
                report = self.run_cli(1 if expected else 0)
                if expected:
                    self.assert_source_errors(report, PROJECT, [expected], [label])
                else:
                    self.assertEqual(report['errors'], [])
                self.assertEqual(report['surfaces'], [])
        # A nested import now needs a same-URL root; without a declaration it is refused, never opened.
        pin = self.git(self.repo, 'rev-parse', 'HEAD')
        self.write(self.repo, PROJECT, '<Project><Import Project="../../../nested/build.props"/></Project>')
        self.git(self.repo, 'add', PROJECT)
        self.git(self.repo, 'update-index', '--add', '--cacheinfo', f'160000,{pin},nested')
        self.git(self.repo, 'commit', '-q', '-m', 'test: retain unopened nested import'); self.pin()
        report = self.run_cli(1)
        self.assert_source_errors(report, PROJECT, ['nested-pin-unresolvable'], ['nested/build.props'])
        self.assertEqual(report['repositories'][0]['nestedGitlinks'], ['nested'])
        self.assertEqual(report['repositories'][0]['crossTreeReads'], [])
        self.assertFalse((self.repo / 'nested').exists())

    def test_review_s08_property_expansion_depth_is_a_safe_coverage_error(self):
        chain = ''.join(f'<P{i}>$(P{i+1})</P{i}>' for i in range(1100)) + '<P1100>Exe</P1100><OutputType>$(P0)</OutputType>'
        self.write(self.repo, PROJECT, '<Project><PropertyGroup>' + chain + '</PropertyGroup></Project>')
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assert_source_errors(report, PROJECT, ['property-expansion-depth'])
        self.assertEqual(report['surfaces'], [])

    def test_review_s09_local_tool_definition_cannot_borrow_consumption_exemption(self):
        identity = 'Approved.Tool'
        self.policy['toolIdentities'] = [dict(identity=identity, classification='exempt-build-tooling', row='PE01', owner='owner', reason='Approved consumption')]
        self.save()
        self.write(self.repo, 'package.json', json.dumps(dict(name=identity, bin='run.js')))
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assertEqual(report['errors'], [])
        self.assertEqual([e['surface'] for e in report['surfaces']], [self.binding('package.json', 'publication', identity)])
        self.assertEqual(report['surfaces'][0]['signals'], ['tool-manifest'])
        self.allowance(report['surfaces'][0]['surface'], ['tool-manifest'])
        self.run_cli(0)
        (self.repo / 'package.json').unlink()
        self.write(self.repo, 'scripts/use.sh', 'dotnet tool install ' + identity)
        self.commit(self.repo); self.pin()
        report = self.run_cli(0)
        self.assertEqual([e['classification'] for e in report['surfaces']], ['exempt-build-tooling'])

    def test_review_s10_nearest_default_metadata_and_explicit_imports(self):
        project = 'src/Neutral/Neutral.csproj'
        self.write(self.repo, 'Directory.Build.props', '<Project><PropertyGroup><OutputType>Exe</OutputType></PropertyGroup></Project>')
        self.write(self.repo, 'Directory.Build.targets', '<Project><PropertyGroup><PackAsTool>true</PackAsTool></PropertyGroup></Project>')
        self.write(self.repo, 'src/Directory.Build.props', '<Project/>')
        self.write(self.repo, 'src/Directory.Build.targets', '<Project/>')
        self.write(self.repo, project, '<Project/>')
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assertEqual(report['errors'], [])
        self.assertEqual([e['surface'] for e in report['surfaces']],
                         [self.binding(name, 'source', name) for name in ('Directory.Build.props', 'Directory.Build.targets')])
        self.assertEqual([e['signals'] for e in report['surfaces']], [['unresolved-tool-metadata']] * 2)
        self.write(self.repo, 'src/Directory.Build.props', '<Project><Import Project="../Directory.Build.props"/></Project>')
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assertEqual(report['errors'], [])
        self.assertEqual([e['surface'] for e in report['surfaces']],
                         [self.binding('Directory.Build.targets', 'source', 'Directory.Build.targets'), self.binding(project, 'project', 'Neutral')])
        self.assertEqual([e['signals'] for e in report['surfaces']], [['unresolved-tool-metadata'], ['executable-project']])

    def test_review_s11_conditional_loop_keeps_prebranch_target(self):
        path = 'scripts/ship.sh'
        self.allowance(self.binding(path, 'publication', 'missing/Approved.csproj'), ['orphan-project-reference'])
        self.write(self.repo, path, 'target=missing/New.csproj\nif runtime; then\n for x in One; do\n target=missing/Approved.csproj\n done\nfi\ndotnet pack "$target"')
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assertEqual(report['errors'], [])
        self.assertEqual([(e['surface']['identity'], e['status']) for e in report['surfaces']],
                         [('missing/Approved.csproj', 'approved'), ('missing/New.csproj', 'rejected')])

    def test_review_s12_unknown_loop_invalidates_changed_caller_directory(self):
        path = 'scripts/ship.sh'
        self.allowance(self.binding(path, 'publication', 'missing/Approved.csproj'), ['orphan-project-reference'])
        self.write(self.repo, 'child/placeholder.txt', 'committed')
        for loop in ('while runtime', 'until runtime'):
            self.write(self.repo, path, loop + '; do\n cd child\ndone\ndotnet publish missing/Approved.csproj')
            self.commit(self.repo); self.pin()
            report = self.run_cli(1)
            self.assert_source_errors(report, path, ['unresolved-publication-directory'])
            self.assertEqual(report['surfaces'], [])

    def test_review_s13_shell_state_commands_invalidate_trusted_targets(self):
        path = 'scripts/ship.sh'
        self.allowance(self.binding(path, 'publication', 'missing/Approved.csproj'), ['orphan-project-reference'])
        for statement in ('read -r target', 'unset target', 'declare target=missing/New.csproj'):
            with self.subTest(statement=statement):
                self.write(self.repo, path, 'target=missing/Approved.csproj\n' + statement + '\ndotnet publish "$target"')
                self.commit(self.repo); self.pin()
                report = self.run_cli(1)
                self.assert_source_errors(report, path, ['unresolved-publication-target'])
                self.assertEqual(report['surfaces'], [])

    def test_review_s14_single_quoted_function_argument_has_no_variable_authority(self):
        path = 'scripts/ship.sh'
        self.allowance(self.binding(path, 'publication', 'missing/Approved.csproj'), ['orphan-project-reference'])
        prefix = 'target=missing/Approved.csproj\nship() {\n dotnet pack "$1"\n}\n'
        self.write(self.repo, path, prefix + "ship '$target'")
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assert_source_errors(report, path, ['unresolved-publication-target'])
        self.assertEqual(report['surfaces'], [])
        self.write(self.repo, path, prefix + 'ship "$target"')
        self.commit(self.repo); self.pin()
        self.assertEqual(self.run_cli(0)['surfaces'][0]['surface']['identity'], 'missing/Approved.csproj')

    def test_review_s15_missing_executable_blob_retains_other_root_observations(self):
        path = 'scripts/ship'
        self.write(self.repo, path, '#!/bin/sh\ndotnet publish missing/One.csproj')
        (self.repo / path).chmod(0o755)
        self.project()
        oid = self.git(self.repo, 'rev-parse', 'HEAD:' + path)
        (self.repo / '.git/objects' / oid[:2] / oid[2:]).unlink()
        report = self.run_cli(1)
        self.assertEqual(report['errors'], [dict(repository='references/opaque', gitlink=self.git(self.repo, 'rev-parse', 'HEAD'), path=path, rule='git-object-unavailable')])
        self.assertEqual([e['surface'] for e in report['surfaces']], [self.binding()])
        self.assertFalse(report['repositories'][0]['inspectionComplete'])

    def test_review_s16_report_directory_and_file_write_failures_return_one(self):
        for method in ('mkdir', 'write_text'):
            with self.subTest(method=method):
                stdout, stderr = io.StringIO(), io.StringIO()
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr), patch.object(census.Path, method, side_effect=OSError('unsafe supplied value')):
                    status = census.main(['--workspace', str(self.root), '--baseline', str(self.baseline), '--amendments', str(self.index), '--output', str(self.root / 'failure/report.json')])
                self.assertEqual(status, 1)
                self.assertEqual(stdout.getvalue(), '')
                self.assertEqual(stderr.getvalue(), 'Proprietary surface census failed: report-write-failed\n')

    def test_review_s17_environment_prefix_keeps_publication_command_visible(self):
        path = 'scripts/ship.sh'
        for prefix in ('FLAG=value', 'FLAG=value SECOND="two words"'):
            self.write(self.repo, path, prefix + ' dotnet publish missing/New.csproj')
            self.commit(self.repo); self.pin()
            report = self.run_cli(1)
            self.assertEqual(report['errors'], [])
            self.assertEqual([e['surface'] for e in report['surfaces']], [self.binding(path, 'publication', 'missing/New.csproj')])
            self.assertEqual(report['surfaces'][0]['signals'], ['orphan-project-reference'])

    def test_review_s18_metadata_errors_and_full_output_ignore_hash_seed(self):
        self.write(self.repo, PROJECT, '<Project><PropertyGroup><Source Condition="A">$(Missing)/Unknown.cs</Source>'
                   '<Source Condition="B">../../../shared/Absent.cs</Source></PropertyGroup><ItemGroup><Compile Include="$(Source)"/><Compile Include="../../../shared/AlsoMissing.cs"/></ItemGroup></Project>')
        self.commit(self.repo); self.pin()
        captures = []
        for seed in ('1', '2', '3', '4'):
            output = self.root / 'seed-report.json'
            command = [sys.executable, census.__file__, '--workspace', str(self.root), '--baseline', str(self.baseline), '--amendments', str(self.index), '--output', str(output)]
            result = subprocess.run(command, capture_output=True, text=True, env={**os.environ, 'PYTHONHASHSEED': seed, 'PYTHONDONTWRITEBYTECODE': '1'})
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stdout, output.read_text())
            report = json.loads(result.stdout)
            self.assertEqual([e['rule'] for e in report['errors']], ['unavailable-committed-compile-source:' + PROJECT, 'unresolved-compile-source:' + PROJECT])
            self.assertEqual(report['surfaces'], [])
            self.assertEqual(result.stderr, ''.join('error: ' + json.dumps(e, sort_keys=True) + '\n' for e in report['errors']))
            captures.append((result.stdout, result.stderr))
        self.assertTrue(all(capture == captures[0] for capture in captures))

    def test_review_s19_forged_matrix_tokens_have_no_approved_target_authority(self):
        path = 'scripts/ship.sh'
        approved = 'missing/Approved.csproj'
        forged = '@matrix-projects:' + json.dumps([approved], separators=(',', ':')).encode().hex() + '@'
        self.allowance(self.binding(path, 'publication', approved), ['orphan-project-reference'])
        self.write(self.repo, path, 'dotnet publish "' + forged + '"')
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assertEqual(report['surfaces'], [])
        self.assertEqual(report['errors'], [dict(repository='references/opaque', gitlink=self.git(self.repo, 'rev-parse', 'HEAD'),
            path=path, rule='unresolved-publication-target:' + path, target=forged)])
        workflow = '.github/workflows/ci.yml'
        self.allowance(self.binding(workflow, 'publication', approved), ['orphan-project-reference'])
        self.write(self.repo, workflow, 'jobs:\n  ship:\n    strategy:\n      matrix:\n        project: [' + approved + ']\n'
                   '    steps:\n      - run: dotnet publish "${{ matrix.project }}"\n'
                   '      - run: dotnet publish "@census-expression-0@"\n')
        (self.repo / path).unlink()
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assertEqual([(e['surface'], e['status']) for e in report['surfaces']], [(self.binding(workflow, 'publication', approved), 'approved')])
        self.assertEqual(report['errors'], [dict(repository='references/opaque', gitlink=self.git(self.repo, 'rev-parse', 'HEAD'),
            path=workflow, rule='unresolved-publication-target:' + workflow, target='@census-expression-0@')])

    def test_review_s19_matrix_requires_a_whole_target_argument(self):
        path = '.github/workflows/ci.yml'
        self.write(self.repo, path, 'jobs:\n  ship:\n    strategy:\n      matrix:\n        project: [missing/One.csproj]\n'
                   '    steps:\n      - run: dotnet publish "prefix/${{ matrix.project }}"\n')
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assert_source_errors(report, path, ['unresolved-publication-target'])
        self.assertEqual(report['surfaces'], [])

    def test_review_s20_malformed_unconsumed_default_metadata_is_refused(self):
        for name in ('Directory.Build.props', 'Directory.Build.targets'):
            with self.subTest(name=name):
                self.write(self.repo, 'Directory.Build.props', '<Project/>')
                self.write(self.repo, 'Directory.Build.targets', '<Project/>')
                self.write(self.repo, name, '<Project><broken>')
                self.commit(self.repo); self.pin()
                report = self.run_cli(1)
                self.assert_source_errors(report, name, ['malformed-project-metadata'])
                self.assertEqual(report['surfaces'], [])

    def test_review_s20_unconsumed_executable_default_metadata_is_a_source_observation(self):
        for name in ('Directory.Build.props', 'Directory.Build.targets'):
            with self.subTest(name=name):
                self.write(self.repo, 'Directory.Build.props', '<Project/>')
                self.write(self.repo, 'Directory.Build.targets', '<Project/>')
                self.write(self.repo, name, '<Project><PropertyGroup><OutputType>Exe</OutputType></PropertyGroup></Project>')
                self.commit(self.repo); self.pin()
                report = self.run_cli(1)
                self.assertEqual(report['errors'], [])
                self.assertEqual([e['surface'] for e in report['surfaces']], [self.binding(name, 'source', name)])
                self.assertEqual(report['surfaces'][0]['signals'], ['unresolved-tool-metadata'])

    def test_review_s21_printf_variable_writes_cannot_reuse_old_approval(self):
        path = 'scripts/ship.sh'
        self.allowance(self.binding(path, 'publication', 'missing/Approved.csproj'), ['orphan-project-reference'])
        for statement in ("printf -v target '%s' missing/New.csproj", "printf -vtarget '%s' missing/New.csproj",
                          "builtin printf -vtarget '%s' missing/New.csproj", "printf -v \"$destination\" '%s' missing/New.csproj"):
            with self.subTest(statement=statement):
                self.write(self.repo, path, 'target=missing/Approved.csproj\n' + statement + '\ndotnet publish "$target"')
                self.commit(self.repo); self.pin()
                report = self.run_cli(1)
                self.assert_source_errors(report, path, ['unresolved-publication-target'])
                self.assertEqual(report['surfaces'], [])
        self.write(self.repo, path, 'target=missing/Approved.csproj\nprintf -- \"%s\" \"-vtarget\"\ndotnet publish "$target"')
        self.commit(self.repo); self.pin()
        self.assertEqual(self.run_cli(0)['surfaces'][0]['surface']['identity'], 'missing/Approved.csproj')

    def test_review_s22_multi_assignment_invalidates_every_written_variable(self):
        path = 'scripts/ship.sh'
        self.allowance(self.binding(path, 'publication', 'missing/Approved.csproj'), ['orphan-project-reference'])
        for statement in ('other=x target=missing/New.csproj', 'first="two words" second=y target=missing/New.csproj',
                          'other=x target+=missing/New.csproj'):
            with self.subTest(statement=statement):
                self.write(self.repo, path, 'target=missing/Approved.csproj\n' + statement + '\ndotnet publish "$target"')
                self.commit(self.repo); self.pin()
                report = self.run_cli(1)
                self.assert_source_errors(report, path, ['unresolved-publication-target'])
                self.assertEqual(report['surfaces'], [])

    def test_review_s23_complete_container_registry_repository_and_image_suffixes(self):
        path = 'scripts/ship.sh'
        project = 'src/Host/Host.csproj'
        digest = 'sha256:' + 'a' * 64
        for registry, repository in [('trusted.invalid', 'neutral'), ('trusted.invalid:5000', 'team/neutral')]:
            self.write(self.repo, project, '<Project Sdk="Microsoft.NET.Sdk.Web"><PropertyGroup><IsPackable>false</IsPackable>'
                       '<ContainerRegistry>' + registry + '</ContainerRegistry><ContainerRepository>' + repository + '</ContainerRepository></PropertyGroup></Project>')
            for suffix in (':latest', ':v2', '@' + digest, ':v2@' + digest):
                self.write(self.repo, path, 'docker push ' + registry + '/' + repository + suffix)
                self.commit(self.repo); self.pin()
                report = self.run_cli(0)
                self.assertEqual(report['errors'], [])
                self.assertEqual(report['surfaces'], [])
            for image in ('attacker/' + repository + ':latest', 'other.invalid/' + repository + ':latest',
                          registry + '/other/' + repository + ':latest', registry + '/' + repository + '-other:latest'):
                self.write(self.repo, path, 'docker push ' + image)
                self.commit(self.repo); self.pin()
                report = self.run_cli(1)
                self.assertEqual(report['errors'], [])
                self.assertEqual([e['surface'] for e in report['surfaces']], [self.binding(path, 'publication', image)])
                self.assertEqual(report['surfaces'][0]['signals'], ['container-image'])
        image = 'trusted.invalid:5000/team/neutral:latest'
        self.write(self.repo, 'src/Host/Program.cs', 'builder.Services.AddMcpServer();')
        self.write(self.repo, path, 'docker push ' + image)
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assertEqual(report['errors'], [])
        self.assertEqual([e['surface'] for e in report['surfaces']],
                         [self.binding(path, 'publication', image), self.binding(project, 'project', 'Host'),
                          self.binding(project, 'publication', 'container:team/neutral')])
        self.assertEqual([e['signals'] for e in report['surfaces']], [['container-image'], ['mcp-registration'], ['container-metadata']])

    def test_coverage_comments_and_diagnostic_strings_are_not_commands(self):
        path = 'scripts/ship.sh'
        self.write(self.repo, path, '# concurrent dotnet run launches are incremental\n'
                   'echo "dotnet pack $runtime_project failed"\n'
                   "printf '%s' 'dotnet publish absent/Diagnostic.csproj'\n")
        self.commit(self.repo); self.pin()
        report = self.run_cli(0)
        self.assertEqual(report['errors'], [])
        self.assertEqual(report['surfaces'], [])
        self.write(self.repo, path, '# dotnet pack ignored\n'
                   'dotnet publish "missing/Hash#Runner.csproj" # dotnet pack missing/Comment.csproj\n')
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assertEqual(report['errors'], [])
        self.assertEqual([e['surface'] for e in report['surfaces']],
                         [self.binding(path, 'publication', 'missing/Hash#Runner.csproj')])

    def test_coverage_unknown_wrappers_cannot_borrow_approved_identity(self):
        path = 'scripts/ship.sh'
        for wrapper in ('sudo', 'sudo -D elsewhere', 'nohup', 'env -i', 'time'):
            with self.subTest(wrapper=wrapper):
                self.write(self.repo, path, wrapper + ' dotnet publish missing/Old.csproj')
                self.commit(self.repo); self.pin()
                self.policy['allowances'] = []
                self.allowance(self.binding(path, 'publication', 'missing/Old.csproj'), ['orphan-project-reference'])
                report = self.run_cli(1)
                self.assert_source_errors(report, path, ['unsupported-publication-wrapper'])
                self.assertEqual([e['surface'] for e in report['surfaces']],
                                 [self.binding(path, 'publication', 'missing/Old.csproj')])

    def test_coverage_heredoc_quotes_do_not_hide_later_publication(self):
        path = 'scripts/ship.sh'
        self.write(self.repo, path, "cat <<'EOF'\nI'm literal data\nEOF\ndotnet publish missing/New.csproj\n")
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assertEqual(report['errors'], [])
        self.assertEqual([e['surface'] for e in report['surfaces']],
                         [self.binding(path, 'publication', 'missing/New.csproj')])
        self.assertEqual(len(list(census.dotnet_invocations((self.repo / path).read_text()))), 1)
        for prefix in ("# example <<'EOF'", "echo 'literal <<EOF'", 'echo "literal <<EOF"'):
            self.write(self.repo, path, prefix + '\ndotnet publish missing/New.csproj\n')
            self.commit(self.repo); self.pin()
            report = self.run_cli(1)
            self.assertEqual(report['errors'], [])
            self.assertEqual([e['surface'] for e in report['surfaces']],
                             [self.binding(path, 'publication', 'missing/New.csproj')])

    def test_coverage_backtick_substitution_inside_diagnostic_remains_executable(self):
        path = 'scripts/ship.sh'
        self.write(self.repo, path, 'printf \'%s\' "ignored `dotnet publish missing/New.csproj`"\n')
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assert_source_errors(report, path, ['unresolved-publication-target'])
        self.assertEqual(report['surfaces'], [])

    def test_coverage_source_relative_shell_locator_forms_resolve_without_execution(self):
        path = 'scripts/ship.sh'
        locators = ('root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)',
                    'script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\nroot="$(cd "$script_dir/.." && pwd)"',
                    'root="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"')
        for locator in locators:
            with self.subTest(locator=locator):
                self.write(self.repo, path, locator + '\ndotnet pack "$root/missing/Runner.csproj"\n')
                self.commit(self.repo); self.pin()
                report = self.run_cli(1)
                self.assertEqual(report['errors'], [])
                self.assertEqual([e['surface'] for e in report['surfaces']],
                                 [self.binding(path, 'publication', 'missing/Runner.csproj')])
        self.write(self.repo, path, 'root=$(cd "$runtime_root" && pwd)\ndotnet pack "$root/missing/Runner.csproj"\n')
        self.commit(self.repo); self.pin()
        self.assert_source_errors(self.run_cli(1), path, ['unresolved-publication-target'])

    def test_coverage_redirected_loop_end_does_not_consume_later_publication(self):
        path = 'scripts/ship.sh'
        self.write(self.repo, path, 'while read -r line; do\n  echo "$line"\ndone < runtime-input\n'
                   'dotnet publish missing/After.csproj\n')
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assertEqual(report['errors'], [])
        self.assertEqual([e['surface'] for e in report['surfaces']],
                         [self.binding(path, 'publication', 'missing/After.csproj')])

    def test_coverage_loop_redirection_substitutions_remain_executable(self):
        path = 'scripts/ship.sh'
        for suffix in ('< <(dotnet publish missing/Actual.csproj)',
                       '< "$(dotnet publish missing/Actual.csproj)"',
                       '< `dotnet publish missing/Actual.csproj`'):
            self.write(self.repo, path, 'while read -r value; do\n  echo "$value"\ndone ' + suffix + '\n')
            self.commit(self.repo); self.pin()
            report = self.run_cli(1)
            self.assert_source_errors(report, path, ['unresolved-loop-redirection'])
            self.assertEqual(report['surfaces'], [])

    def test_coverage_workflow_temporary_script_has_no_committed_locator_authority(self):
        path = '.github/workflows/ship.yml'
        self.write(self.repo, path, 'jobs:\n  ship:\n    steps:\n      - run: |\n'
                   '          root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"\n'
                   '          dotnet publish "$root/missing/New.csproj"\n')
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assert_source_errors(report, path, ['unresolved-publication-target'])
        self.assertEqual(report['surfaces'], [])

    def test_coverage_literal_repository_marker_cannot_borrow_locator_authority(self):
        path = 'scripts/ship.sh'
        self.allowance(self.binding(path, 'publication', 'missing/Old.csproj'), ['orphan-project-reference'])
        self.write(self.repo, path, "root='@repo'\ndotnet publish \"$root/missing/Old.csproj\"\n")
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assertEqual(report['errors'], [])
        self.assertEqual([e['surface'] for e in report['surfaces']],
                         [self.binding(path, 'publication', '@repo/missing/Old.csproj')])
        self.write(self.repo, path, "left='@re'\nright='po'\nroot=\"$left$right\"\ndotnet publish \"$root/missing/Old.csproj\"\n")
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assertEqual(report['errors'], [])
        self.assertEqual([e['surface'] for e in report['surfaces']],
                         [self.binding(path, 'publication', '@repo/missing/Old.csproj')])
        self.write(self.repo, path, "root='\x00repo'\ndotnet publish \"$root/missing/Old.csproj\"\n")
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assert_source_errors(report, path, ['unsafe-script-text'])
        self.assertEqual(report['surfaces'], [])

    def test_coverage_locator_builtin_overrides_and_source_mutations_refuse(self):
        path = 'scripts/ship.sh'
        for prefix in ('pwd() {\n  echo elsewhere\n}\n', 'alias cd=runtime\n', 'eval "$runtime"\n',
                       'source runtime.sh\n', 'unset BASH_SOURCE\n'):
            self.write(self.repo, path, prefix + 'root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"\n'
                       'dotnet publish "$root/missing/Old.csproj"\n')
            self.commit(self.repo); self.pin()
            report = self.run_cli(1)
            self.assert_source_errors(report, path, ['unresolved-publication-target'])
            self.assertEqual(report['surfaces'], [])

    def test_coverage_elif_does_not_leave_following_literal_assignment_conditional(self):
        path = 'scripts/ship.sh'
        self.write(self.repo, path, 'if test "$runtime"; then\n  echo yes\nelif test "$other"; then\n  echo other\nfi\n'
                   'target=missing/After.csproj\ndotnet pack "$target"\n')
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assertEqual(report['errors'], [])
        self.assertEqual([e['surface'] for e in report['surfaces']],
                         [self.binding(path, 'publication', 'missing/After.csproj')])

    def test_coverage_unrelated_loops_and_heredocs_create_no_publication_error(self):
        path = 'scripts/ordinary.sh'
        self.write(self.repo, path, 'for file in runtime/*; do cp "$file" output; done\n'
                   'cat <<EOF\n$(runtime_data)\nEOF\n')
        self.commit(self.repo); self.pin()
        report = self.run_cli(0)
        self.assertEqual(report['errors'], [])
        self.assertEqual(report['surfaces'], [])

    def test_coverage_json_object_arrays_preserve_nested_manifest_signals(self):
        path = 'tools/release.json'
        self.write(self.repo, path, json.dumps([{'case': 'observation', 'document': {'schema': 'release-result', 'outcome': 'published'}},
            {'document': {'packages': [{'id': 'neutral', 'project': 'missing/Runner.csproj'}]}},
            {'document': {'servers': {'local': {'command': 'neutral', 'args': ['one', 'two']}}}},
            {'image': 'registry.invalid/neutral:1'}]))
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assertEqual(report['errors'], [])
        self.assertEqual([(e['surface']['kind'], e['surface']['identity']) for e in report['surfaces']],
                         [('configuration', 'local:' + census.digest(json.dumps({'command': 'neutral', 'args': ['one', 'two']}, sort_keys=True, separators=(',', ':')).encode())),
                          ('publication', 'neutral'), ('publication', 'registry.invalid/neutral:1')])

    def test_coverage_json_array_scalar_roots_and_depth_are_refused(self):
        path = 'tools/release.json'
        for document in ('unclassified-package', ['unclassified-package'], [[['unclassified-package']]]):
            self.write(self.repo, path, json.dumps(document))
            self.commit(self.repo); self.pin()
            self.assert_source_errors(self.run_cli(1), path, ['malformed-publication'])
        document = {'packages': [{'id': 'neutral', 'project': 'missing/Runner.csproj'}]}
        for _ in range(34):
            document = {'document': document}
        self.write(self.repo, path, json.dumps(document))
        self.commit(self.repo); self.pin()
        self.assert_source_errors(self.run_cli(1), path, ['unbounded-publication-json'])
        self.write(self.repo, path, json.dumps([{} for _ in range(4097)]))
        self.commit(self.repo); self.pin()
        self.assert_source_errors(self.run_cli(1), path, ['unbounded-publication-json'])

    def test_coverage_json_schema_definitions_are_not_runtime_manifests(self):
        path = 'tools/release-schema.json'
        schema = {'$schema': 'https://json-schema.org/draft/2020-12/schema',
                  'properties': {'servers': {'type': 'array'}, 'packages': {'type': 'array'}}}
        self.write(self.repo, path, json.dumps(schema))
        self.commit(self.repo); self.pin()
        report = self.run_cli(0)
        self.assertEqual(report['errors'], [])
        self.assertEqual(report['surfaces'], [])
        schema['packages'] = [{'id': 'actual', 'project': 'missing/Actual.csproj'}]
        self.write(self.repo, path, json.dumps(schema))
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assertEqual(report['errors'], [])
        self.assertEqual([e['surface'] for e in report['surfaces']], [self.binding(path, 'publication', 'actual')])
        del schema['packages']
        schema['$schema'] = 'https://attacker.invalid/json-schema.org/draft/2020-12/schema'
        self.write(self.repo, path, json.dumps(schema))
        self.commit(self.repo); self.pin()
        self.assert_source_errors(self.run_cli(1), path, ['malformed-server-configuration'])

    def test_coverage_literal_heredoc_matrix_text_has_no_target_authority(self):
        path = '.github/workflows/ship.yml'
        self.write(self.repo, path, 'jobs:\n  ship:\n    steps:\n      - run: |\n'
                   "          cat <<'EOF'\n          dotnet publish ${{ matrix.unknown }}\n          EOF\n"
                   '          dotnet publish missing/Actual.csproj\n')
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assertEqual(report['errors'], [])
        self.assertEqual([e['surface'] for e in report['surfaces']], [self.binding(path, 'publication', 'missing/Actual.csproj')])
        self.write(self.repo, path, 'jobs:\n  ship:\n    strategy:\n      matrix:\n        project: [missing/Quoted.csproj]\n'
                   '    steps:\n      - run: \'dotnet publish ${{ matrix.project }}\'\n')
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assertEqual(report['errors'], [])
        self.assertEqual([e['surface'] for e in report['surfaces']], [self.binding(path, 'publication', 'missing/Quoted.csproj')])


    def manifest_fixture(self, entries=None, *, before='', body='dotnet pack "$target"', after='', selector=None, source='targets.json'):
        path = 'eng/ship.sh'
        if entries is None:
            entries = [{'label': 'second', 'target': 'missing/Second.csproj'},
                       {'label': 'first', 'target': 'missing/First.fsproj'}]
        selector = selector or '.payload.units | select(length == 2) | .[] | [.label, .target] | @tsv'
        self.write(self.repo, 'targets.json', json.dumps({'payload': {'units': entries}}))
        self.write(self.repo, path, before + '\nrows="$(jq -er \'' + selector + "' " + source + ')"\n' + after +
                   "\nwhile IFS=$'\\t' read -r label target; do\n" + body + '\ndone <<< "$rows"\n')
        self.commit(self.repo); self.pin()
        return path

    def assert_manifest_errors(self, report, path, rule, target='targets.json'):
        pin = self.git(self.repo, 'rev-parse', 'HEAD')
        expected = [dict(repository='references/opaque', gitlink=pin, path=path, rule=rule + ':' + path,
                         **({'target': target} if target is not None else {})),
                    dict(repository='references/opaque', gitlink=pin, path=path, rule='unbounded-publication-control-flow:' + path),
                    dict(repository='references/opaque', gitlink=pin, path=path, rule='unresolved-publication-target:' + path)]
        self.assertEqual(report['errors'], sorted(expected, key=lambda error: json.dumps(error, sort_keys=True)))
        self.assertEqual(report['surfaces'], [])

    def test_manifest_selector_retains_exact_orphan_observations_and_committed_input(self):
        path = self.manifest_fixture()
        self.write(self.repo, 'targets.json', '{"payload":{"units":[]}}')
        report = self.run_cli(1)
        self.assertEqual(report['errors'], [])
        pin = self.git(self.repo, 'rev-parse', 'HEAD')
        self.assertEqual(report['surfaces'], [dict(surface=self.binding(path, 'publication', target),
            signals=['orphan-project-reference'], sources=[path], gitlink=pin, status='rejected',
            classification='unapproved', reason='new-proprietary-surface')
            for target in ('missing/First.fsproj', 'missing/Second.csproj')])

    def test_manifest_selector_pairs_fields_and_preserves_iteration_directory_order(self):
        self.write(self.repo, 'start/ordinary.txt', 'directory\n')
        path = self.manifest_fixture([{'label': 'start', 'target': 'First.csproj'}, {'label': '..', 'target': 'Second.csproj'}],
                                     body='cd "$label"\ndotnet pack "$target"')
        report = self.run_cli(1)
        self.assertEqual(report['errors'], [])
        self.assertEqual([entry['surface'] for entry in report['surfaces']],
                         [self.binding(path, 'publication', target) for target in ('Second.csproj', 'start/First.csproj')])

    def test_manifest_selector_present_projects_require_metadata_and_registration_inspection(self):
        self.write(self.repo, 'one/First.csproj', '<Project Sdk="Microsoft.NET.Sdk"/>')
        self.write(self.repo, 'two/Second.vbproj', '<Project Sdk="Microsoft.NET.Sdk"/>')
        entries = [{'label': 'one', 'target': 'one/First.csproj'}, {'label': 'two', 'target': 'two/Second.vbproj'}]
        self.manifest_fixture(entries)
        self.assertEqual(self.run_cli(0)['surfaces'], [])
        self.write(self.repo, 'two/Program.vb', '<McpServerTool>\nPublic Function Execute()\nEnd Function')
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assertEqual(report['errors'], [])
        self.assertEqual([(entry['surface']['path'], entry['signals']) for entry in report['surfaces']],
                         [('eng/ship.sh', ['project-publication-reference']), ('two/Second.vbproj', ['mcp-registration']),
                          ('two/Second.vbproj', ['package-metadata'])])
        self.write(self.repo, 'one/First.csproj', '<Project')
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assertEqual(report['errors'], [dict(repository='references/opaque', gitlink=self.git(self.repo, 'rev-parse', 'HEAD'),
                                                path='one/First.csproj', rule='malformed-project-metadata:one/First.csproj')])

    def test_manifest_selector_unsupported_selectors_and_options_refuse(self):
        for selector in ('.payload.units[].target', '.payload.units | select(length > 0) | .[] | [.label, .target] | @tsv',
                         '.payload.units | select(length == 2) | .[] | [.label, (.target | ascii_downcase)] | @tsv'):
            with self.subTest(selector=selector):
                path = self.manifest_fixture(selector=selector)
                self.assert_manifest_errors(self.run_cli(1), path, 'unsupported-manifest-selector', None)
        path = self.manifest_fixture(source='--arg target runtime targets.json')
        self.assert_manifest_errors(self.run_cli(1), path, 'unsupported-manifest-selector', None)

    def test_manifest_selector_runtime_missing_malformed_and_duplicate_inputs_refuse(self):
        path = self.manifest_fixture(source='"$runtime"')
        self.assert_manifest_errors(self.run_cli(1), path, 'unresolved-manifest-input', None)
        path = self.manifest_fixture(source='generated.json')
        self.assert_manifest_errors(self.run_cli(1), path, 'regular-committed-blob-required', 'generated.json')
        for raw, rule in (('{', 'malformed-json'), ('{"payload":{},"payload":{}}', 'duplicate-json-key')):
            with self.subTest(rule=rule):
                self.manifest_fixture()
                self.write(self.repo, 'targets.json', raw); self.commit(self.repo); self.pin()
                self.assert_manifest_errors(self.run_cli(1), path, rule)

    def test_manifest_selector_collection_shape_and_length_refuse(self):
        for entries in ([], {}, [{'label': 'one', 'target': 'First.csproj'}], [None, None], [{}, {}]):
            with self.subTest(entries=entries):
                path = self.manifest_fixture(entries)
                self.assert_manifest_errors(self.run_cli(1), path, 'manifest-selector-shape')

    def test_manifest_selector_missing_collection_path_refuses(self):
        for document in ({}, {'payload': {}}, {'payload': None}, {'payload': []}):
            with self.subTest(document=document):
                path = self.manifest_fixture()
                self.write(self.repo, 'targets.json', json.dumps(document)); self.commit(self.repo); self.pin()
                self.assert_manifest_errors(self.run_cli(1), path, 'manifest-selector-shape')

    def test_manifest_selector_fields_cannot_forge_tsv_or_shell_provenance(self):
        for value in ('', None, 7, [], {}, 'a\tb', 'a\nb', 'a\rb', 'a\\b', '\x00', '\x7f',
                      '$old', '${old}', '$(helper)', '`helper`', '*.csproj', 'a?b', 'a[bc]'):
            with self.subTest(value=value):
                path = self.manifest_fixture([{'label': 'first', 'target': value}, {'label': 'next', 'target': 'Next.csproj'}])
                self.assert_manifest_errors(self.run_cli(1), path, 'manifest-selector-field')

    def test_manifest_selector_budgets_refuse(self):
        for selector in ('.payload.units | select(length == 257) | .[] | [.label, .target] | @tsv',
                         '.payload.units | select(length == 0) | .[] | [.label, .target] | @tsv',
                         '.payload.units | select(length == 2) | .[] | [' + ', '.join(['.target'] * 33) + '] | @tsv',
                         '.' + '.'.join(['a'] * 33) + ' | select(length == 2) | .[] | [.target] | @tsv'):
            with self.subTest(selector=selector):
                path = self.manifest_fixture(selector=selector)
                self.assert_manifest_errors(self.run_cli(1), path, 'manifest-selector-limit')
        path = self.manifest_fixture([{'label': 'unit', 'target': 'missing/Unit.csproj'}] * 257,
            selector='.payload.units | select(length == 257) | .[] | [.label, .target] | @tsv')
        self.assert_manifest_errors(self.run_cli(1), path, 'manifest-selector-limit')
        path = self.manifest_fixture(selector='.payload.units | select(length == ' + '9' * 5000 + ') | .[] | [.label, .target] | @tsv')
        self.assert_manifest_errors(self.run_cli(1), path, 'manifest-selector-limit')

    def test_manifest_selector_json_traversal_budgets_refuse(self):
        for kind in ('depth', 'nodes'):
            with self.subTest(kind=kind):
                path = self.manifest_fixture()
                document = json.loads((self.repo / 'targets.json').read_text())
                if kind == 'depth':
                    extra = {}
                    for _ in range(34):
                        extra = {'nested': extra}
                else:
                    extra = [{} for _ in range(4097)]
                document['other'] = extra
                self.write(self.repo, 'targets.json', json.dumps(document)); self.commit(self.repo); self.pin()
                self.assert_manifest_errors(self.run_cli(1), path, 'unbounded-publication-json')

    def test_manifest_selector_command_overrides_refuse(self):
        for before in ('alias jq=other', 'jq() {\n printf fake\n}', 'function jq {\n printf fake\n}',
                       'read() {\n target=fake\n}', 'enable -n read', 'builtin enable -n read',
                       'true; alias read=other', 'true; read() {\n :\n}',
                       'eval "$runtime"', 'source runtime.sh', '. runtime.sh'):
            with self.subTest(before=before):
                path = self.manifest_fixture(before=before)
                self.assert_manifest_errors(self.run_cli(1), path, 'unsupported-manifest-command-context', None)

    def test_manifest_selector_known_and_unknown_file_writes_refuse(self):
        for before in ('printf changed > targets.json', 'printf changed > "$runtime"', 'cp runtime targets.json',
                       'mv runtime targets.json', 'tee targets.json', 'sed -i s/a/b/ targets.json',
                       'command cp runtime targets.json', 'FLAG=value cp runtime targets.json',
                       'condition && cp runtime targets.json', 'perl -i -pe s/a/b/ targets.json',
                       'helper targets.json', 'generated="$(helper targets.json)"',
                       'printf "%s" "$(helper targets.json)"', 'find . -delete',
                       "find . -name '*.json' -delete", "find . -name '*.nupkg' -o -delete",
                       "find . -name '*.nupkg' -o -true -delete", 'find . -fprint targets.json',
                       'find . -fprintf targets.json changed', 'printf changed >| targets.json',
                       'printf changed &> targets.json', 'printf changed >& targets.json', ': <> targets.json',
                       'find . -name "$runtime" -delete', "find . -name '*[[:alpha:]]*' -delete",
                       'scratch+=$(cp runtime targets.json)', 'scratch="$(cd "$(touch targets.json)" && pwd)"'):
            with self.subTest(before=before):
                path = self.manifest_fixture(before=before)
                self.assert_manifest_errors(self.run_cli(1), path, 'mutable-manifest-input')

    def test_manifest_selector_literal_test_tokens_cannot_hide_later_writers(self):
        path = self.manifest_fixture(before='echo [[; cp runtime targets.json')
        self.assert_manifest_errors(self.run_cli(1), path, 'mutable-manifest-input')

    def test_manifest_selector_unknown_row_or_table_writes_cannot_keep_old_authority(self):
        for after in ('read -r rows', 'printf -v rows changed', 'rows+=changed', 'rows="$runtime"',
                      'mapfile -t rows', 'readarray rows', 'getopts flags rows', 'let rows=1',
                      '((rows=1))', 'rows[0]=changed', 'declare -n alias=rows\nalias=changed',
                      'if condition; then\n rows="$runtime"\nfi', 'condition && rows="$runtime"'):
            with self.subTest(after=after):
                path = self.manifest_fixture(after=after)
                report = self.run_cli(1)
                self.assertEqual(report['surfaces'], [])
                self.assert_source_errors(report, path, ['unbounded-publication-control-flow', 'unresolved-publication-target'])
        for body in ('read -r target\ndotnet pack "$target"', 'target+=$runtime\ndotnet pack "$target"',
                     'command read -r target\ndotnet pack "$target"',
                     'if condition; then\n target="$runtime"\nfi\ndotnet pack "$target"',
                     'condition && target="$runtime"\ndotnet pack "$target"'):
            with self.subTest(body=body):
                path = self.manifest_fixture(body=body)
                report = self.run_cli(1)
                self.assertEqual(report['surfaces'], [])
                self.assert_source_errors(report, path, ['unresolved-publication-target'])
        path = self.manifest_fixture(body='dotnet pack "$rows"')
        report = self.run_cli(1)
        self.assertEqual(report['surfaces'], [])
        self.assert_source_errors(report, path, ['unresolved-publication-target'])

    def test_manifest_selector_reader_shape_refuses_instead_of_using_wrong_fields(self):
        for names in ('label', 'label target other', 'target target'):
            with self.subTest(names=names):
                path = self.manifest_fixture()
                file = self.repo / path
                file.write_text(file.read_text().replace('read -r label target', 'read -r ' + names))
                self.commit(self.repo); self.pin()
                self.assert_source_errors(self.run_cli(1), path, ['unbounded-publication-control-flow',
                    'unresolved-publication-target', 'unsupported-manifest-reader'])

    def test_manifest_selector_conditional_and_unbounded_readers_refuse(self):
        for control, ending in (('if condition; then', 'fi'), ('while condition; do', 'done')):
            with self.subTest(control=control):
                path = self.manifest_fixture()
                file = self.repo / path
                file.write_text(file.read_text().replace("while IFS=", control + "\nwhile IFS=") + ending + '\n')
                self.commit(self.repo); self.pin()
                report = self.run_cli(1)
                self.assertEqual(report['surfaces'], [])
                self.assert_source_errors(report, path, ['unbounded-publication-control-flow', 'unresolved-publication-target'])

    def test_manifest_selector_eof_cannot_reuse_final_fields_and_zero_rows_refuse(self):
        path = self.manifest_fixture(body='printf "%s" "$target"')
        file = self.repo / path
        file.write_text(file.read_text() + 'dotnet pack "$target"\n')
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assertEqual(report['surfaces'], [])
        self.assert_source_errors(report, path, ['unresolved-publication-target'])
        path = self.manifest_fixture([], selector='.payload.units | select(length == 0) | .[] | [.label, .target] | @tsv',
                                     body='dotnet pack missing/Actual.csproj')
        report = self.run_cli(1)
        pin = self.git(self.repo, 'rev-parse', 'HEAD')
        self.assertEqual(report['errors'], [dict(repository='references/opaque', gitlink=pin, path=path,
            rule='manifest-selector-limit:' + path, target='targets.json'),
            dict(repository='references/opaque', gitlink=pin, path=path, rule='unbounded-publication-control-flow:' + path)])
        self.assertEqual([entry['surface'] for entry in report['surfaces']], [self.binding(path, 'publication', 'missing/Actual.csproj')])

    def test_manifest_selector_input_argv_and_safe_readonly_effects_are_proven(self):
        path = self.manifest_fixture(before='input="space targets.json"', source='"$input"')
        self.write(self.repo, 'space targets.json', (self.repo / 'targets.json').read_text())
        self.commit(self.repo); self.pin()
        self.assertEqual(self.run_cli(1)['errors'], [])
        path = self.manifest_fixture(before='input="space targets.json"', source='$input')
        self.assert_manifest_errors(self.run_cli(1), path, 'unresolved-manifest-input', None)
        path = self.manifest_fixture(before='input=targets.json', source="'$input'")
        self.assert_manifest_errors(self.run_cli(1), path, 'unresolved-manifest-input', None)
        path = self.manifest_fixture(before="printf 'Usage <input> <version>\\n' >&2\nfind \"$runtime\" -name '*.nupkg' -delete")
        report = self.run_cli(1)
        self.assertEqual(report['errors'], [])
        self.assertEqual(len(report['surfaces']), 2)

    def test_manifest_selector_unrelated_scalar_queries_have_no_table_authority(self):
        path = 'eng/ship.sh'
        self.write(self.repo, path, 'version="$(jq -r .version targets.json)"\n'
                   'dotnet pack missing/Actual.csproj -p:Version="$version"\n')
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assertEqual(report['errors'], [])
        self.assertEqual([entry['surface'] for entry in report['surfaces']], [self.binding(path, 'publication', 'missing/Actual.csproj')])

    def test_manifest_selector_unsafe_and_nested_sources_and_targets_refuse(self):
        for source in ('../targets.json', '/tmp/targets.json'):
            with self.subTest(source=source):
                path = self.manifest_fixture(source=source)
                self.assert_source_errors(self.run_cli(1), path, ['unbounded-publication-control-flow',
                                                               'unresolved-publication-target', 'unsafe-publication-path'])
        path = self.manifest_fixture(source='nested/targets.json')
        def nested_pin():
            self.git(self.repo, 'update-index', '--add', '--cacheinfo',
                     '160000,' + self.git(self.repo, 'rev-parse', 'HEAD') + ',nested')
            self.git(self.repo, 'commit', '-q', '-m', 'test: retain unopened nested boundary'); self.pin()
        nested_pin()
        self.assert_manifest_errors(self.run_cli(1), path, 'nested-manifest-input', 'nested/targets.json')
        path = self.manifest_fixture([{'label': 'one', 'target': 'nested/First.csproj'}, {'label': 'two', 'target': '../Other.csproj'}])
        nested_pin()
        report = self.run_cli(1)
        pin = self.git(self.repo, 'rev-parse', 'HEAD')
        self.assertEqual(report['surfaces'], [])
        self.assertEqual(report['errors'], [dict(repository='references/opaque', gitlink=pin, path=path,
            rule='nested-publication-target:' + path, target='nested/First.csproj'),
            dict(repository='references/opaque', gitlink=pin, path=path, rule='unsafe-publication-path:' + path)])

    # Nested-pin resolution. Sibling roots are committed repositories declared
    # by the parent; nested gitlinks are recorded without any nested worktree.
    def add_root(self, name, url=None):
        location = self.root / 'references' / name
        location.mkdir(parents=True, exist_ok=True)
        if not (location / '.git').exists():
            self.git(location, 'init', '-q')
        self.write(location, 'README.md', 'committed sibling\n')
        pin = self.commit(location)
        with (self.root / '.gitmodules').open('a') as output:
            output.write(f'[submodule "{name}"]\n path = references/{name}\n url = {url or f"https://example.invalid/{name}.git"}\n')
        self.policy['roots'].append(dict(repository=f'references/{name}', gitlink=pin, classification='PN02', owner='fixture owner'))
        approval = json.loads((self.root / 'approval.json').read_text())
        approval['source_revisions'][f'references/{name}'] = pin
        self.write(self.root, 'approval.json', json.dumps(approval))
        self.policy['provenance'][1]['sha256'] = census.digest((self.root / 'approval.json').read_bytes())
        self.save()
        self.pin_root(name, pin)
        return location

    def pin_root(self, name, sha=None):
        sha = sha or self.git(self.root / 'references' / name, 'rev-parse', 'HEAD')
        self.git(self.root, 'add', '.gitmodules', 'approval.json')
        self.git(self.root, 'update-index', '--add', '--cacheinfo', f'160000,{sha},references/{name}')
        self.git(self.root, 'commit', '-q', '--allow-empty', '-m', 'test: pin sibling census root')
        return sha

    def commit_with_gitlinks(self, gitlinks, repo=None):
        repo = repo or self.repo
        self.git(repo, 'add', '--all')
        for path, sha in gitlinks.items():
            self.git(repo, 'update-index', '--add', '--cacheinfo', f'160000,{sha},{path}')
        self.git(repo, 'commit', '-q', '--allow-empty', '-m', 'test: record unopened nested gitlinks')
        return self.git(repo, 'rev-parse', 'HEAD')

    def cross_read(self, requested, resolution, commit, path, text, repository='references/shared', gitlink=None):
        record = dict(requested=requested, resolution=resolution, repository=repository, commit=commit,
                      path=path, sha256=census.digest(text.encode()))
        if gitlink:
            record['nestedGitlink'] = gitlink
        return record

    def summaries(self, report):
        return {summary['repository']: summary for summary in report['repositories']}

    EXE = '<Project><PropertyGroup><OutputType>Exe</OutputType></PropertyGroup></Project>'
    LIB = '<Project><PropertyGroup><OutputType>Library</OutputType></PropertyGroup></Project>'
    NESTED = '[submodule "shared"]\n path = dependencies/shared\n url = {}\n'

    def test_nested_pin_workspace_import_reads_sibling_root_at_its_pin(self):
        shared = self.add_root('shared')
        self.write(shared, 'eng/Runner.props', self.EXE)
        pinned = self.pin_root('shared', self.commit(shared))
        # The sibling HEAD and worktree move; only the parent's gitlink is authority.
        self.write(shared, 'eng/Runner.props', self.LIB); self.commit(shared)
        self.write(shared, 'eng/Runner.props', 'invalid worktree metadata')
        self.write(self.repo, PROJECT, '<Project><Import Project="../../../../shared/eng/Runner.props"/></Project>')
        self.commit(self.repo); self.pin()
        original = census.git
        with patch.object(census, 'git', side_effect=lambda repo, *args, **kwargs: original(repo, *args, **kwargs)) as reads:
            report = self.run_cli(1)
        self.assertEqual(report['errors'], [])
        self.assertEqual([(s['surface'], s['signals'], s['sources'], s['status']) for s in report['surfaces']], [
            (self.binding(), ['executable-project'], [PROJECT], 'rejected'),
            (dict(repository='references/shared', path='eng/Runner.props', kind='source', identity='eng/Runner.props'),
             ['unresolved-tool-metadata'], ['eng/Runner.props'], 'rejected')])
        summaries = self.summaries(report)
        self.assertEqual(summaries['references/opaque']['crossTreeReads'], [self.cross_read(
            '../shared/eng/Runner.props', 'workspace', pinned, 'eng/Runner.props', self.EXE)])
        self.assertEqual(summaries['references/shared']['crossTreeReads'], [])
        self.assertNotIn('inspectionComplete', summaries['references/opaque'])
        # Only committed objects are read: no fetch, checkout, submodule or worktree command runs.
        self.assertEqual({call.args[1] for call in reads.call_args_list}, {'rev-parse', 'ls-tree', 'cat-file'})

    def test_nested_pin_exists_guarded_absent_escapes_are_optional_only_when_required(self):
        shared = self.add_root('shared')
        self.write(shared, 'eng/Present.props', '<Project/>')
        self.pin_root('shared', self.commit(shared))
        self.write(self.root, 'references/present.props', '<Project/>')
        self.write(self.root, 'references/present-dir/file.txt', 'parent tree only\n')
        self.git(self.root, 'add', 'references/present.props', 'references/present-dir/file.txt'); self.pin()
        absent = '../../../../absent/x.props'
        for project, condition in [
                (absent, f"Exists('{absent}')"),
                (absent, f"Exists('{absent}') And '$(Loaded)' != 'true'"),
                (absent, f"'$(Loaded)' != 'true' and Exists('{absent}') and ('$(A)' == 'a' or '$(B)' == 'b')"),
                (absent, f"Exists('{absent}') and '$(Mode)' == 'or'"),
                # A proven-absent Exists() on another path also makes the import unreachable.
                (absent, "Exists('../../../../absent/other.props')"),
                ('../../../../shared/eng/Missing.props', "Exists('../../../../shared/eng/Missing.props')")]:
            with self.subTest(condition=condition):
                self.write(self.repo, PROJECT, f'<Project><Import Project="{project}" Condition="{condition}"/></Project>')
                self.commit(self.repo); self.pin()
                report = self.run_cli(0)
                self.assertEqual((report['errors'], report['surfaces']), ([], []))
                self.assertEqual(self.summaries(report)['references/opaque']['crossTreeReads'], [])
        for project, condition, label in [
                (absent, '', '../absent/x.props'),
                (absent, f"Exists('{absent}') Or '$(Loaded)' == 'true'", '../absent/x.props'),
                (absent, f"!Exists('{absent}')", '../absent/x.props'),
                (absent, "Exists('../../../../shared/eng/Present.props')", '../absent/x.props'),
                (absent, f"Exists('{absent}') and '$(Loaded)", '../absent/x.props'),
                (absent, f"Exists('{absent}') and 'a' == 'a' ) or ( 'b' == 'b'", '../absent/x.props'),
                ('../../../../present-dir', "Exists('../../../../present-dir')", '../present-dir'),
                ('../../../../shared/eng/Missing.props', '', '../shared/eng/Missing.props'),
                ('../../../../present.props', "Exists('../../../../present.props')", '../present.props'),
                ('../../../../shared/eng', "Exists('../../../../shared/eng')", '../shared/eng'),
                ('../../../../shared', "Exists('../../../../shared')", '../shared'),
                ('../../../../opaque', "Exists('../../../../opaque')", '../opaque'),
                ('../../../../*.props', "Exists('../../../../*.props')", '../*.props'),
                ('../../../../absent/*.props', "Exists('../../../../absent/*.props')", '../absent/*.props'),
                ('../../../../../../outside.props', "Exists('../../../../../../outside.props')", '../../../outside.props')]:
            with self.subTest(project=project, condition=condition):
                self.write(self.repo, PROJECT, f'<Project><Import Project="{project}" Condition="{condition}"/></Project>')
                self.commit(self.repo); self.pin()
                report = self.run_cli(1)
                self.assert_source_errors(report, PROJECT, ['unsafe-import-path'], [label])
                self.assertEqual(report['surfaces'], [])
                self.assertEqual(self.summaries(report)['references/opaque']['crossTreeReads'], [])

    def test_nested_pin_local_exists_conjunction_is_optional_and_disjunction_is_required(self):
        missing = '../../../missing.props'
        for condition, expected in [(f"Exists('{missing}') And '$(Loaded)' != 'true'", None),
                                    (f"Exists('{missing}') Or '$(Loaded)' == 'true'", 'unavailable-local-import'),
                                    (f"!Exists('{missing}')", 'unavailable-local-import')]:
            with self.subTest(condition=condition):
                self.write(self.repo, PROJECT, f'<Project><Import Project="{missing}" Condition="{condition}"/></Project>')
                self.commit(self.repo); self.pin()
                report = self.run_cli(1 if expected else 0)
                if expected:
                    self.assert_source_errors(report, PROJECT, [expected])
                else:
                    self.assertEqual(report['errors'], [])
                self.assertEqual(report['surfaces'], [])

    def test_nested_pin_import_reads_same_url_root_at_the_nested_commit(self):
        shared = self.add_root('shared', 'https://example.invalid/team/shared.git')
        self.write(shared, 'eng/Runner.props', self.EXE)
        nested = self.commit(shared)
        self.write(shared, 'eng/Runner.props', self.LIB)
        pinned = self.pin_root('shared', self.commit(shared))
        self.assertNotEqual(nested, pinned)
        self.write(self.repo, '.gitmodules', self.NESTED.format('https://EXAMPLE.invalid/team/shared/'))
        self.write(self.repo, PROJECT, '<Project><Import Project="../../../dependencies/shared/eng/Runner.props"/></Project>')
        self.commit_with_gitlinks({'dependencies/shared': nested}); self.pin()
        original = census.git
        with patch.object(census, 'git', side_effect=lambda repo, *args, **kwargs: original(repo, *args, **kwargs)) as reads:
            report = self.run_cli(1)
        self.assertEqual(report['errors'], [])
        self.assertEqual([(s['surface'], s['signals'], s['sources']) for s in report['surfaces']],
                         [(self.binding(), ['executable-project'], [PROJECT])])
        summary = self.summaries(report)['references/opaque']
        self.assertEqual(summary['nestedGitlinks'], ['dependencies/shared'])
        self.assertEqual(summary['crossTreeReads'], [self.cross_read(
            'dependencies/shared/eng/Runner.props', 'nested', nested, 'eng/Runner.props', self.EXE, gitlink='dependencies/shared')])
        self.assertFalse((self.repo / 'dependencies/shared').exists())
        # The nested commit is read from the declared root's object store only.
        self.assertTrue(all(Path(call.args[0]) in (self.root, self.repo, shared) for call in reads.call_args_list))
        self.assertEqual({call.args[1] for call in reads.call_args_list}, {'rev-parse', 'ls-tree', 'cat-file'})

    def test_nested_pin_url_identity_requires_one_exact_absolute_declaration(self):
        shared = self.add_root('shared', 'https://example.invalid/team/shared.git')
        neutral = '<Project><PropertyGroup><Neutral>1</Neutral></PropertyGroup></Project>'
        self.write(shared, 'eng/Neutral.props', neutral)
        nested = self.pin_root('shared', self.commit(shared))
        self.write(self.repo, PROJECT, '<Project><Import Project="../../../dependencies/shared/eng/Neutral.props"/></Project>')
        for url in ('https://example.invalid/team/shared', 'https://example.invalid/team/shared.git/',
                    'https://Example.INVALID/team/shared.git', 'https://example.invalid/team/shared/'):
            with self.subTest(url=url):
                self.write(self.repo, '.gitmodules', self.NESTED.format(url))
                self.commit_with_gitlinks({'dependencies/shared': nested}); self.pin()
                report = self.run_cli(0)
                self.assertEqual((report['errors'], report['surfaces']), ([], []))
                self.assertEqual(self.summaries(report)['references/opaque']['crossTreeReads'], [self.cross_read(
                    'dependencies/shared/eng/Neutral.props', 'nested', nested, 'eng/Neutral.props', neutral, gitlink='dependencies/shared')])
        refusals = {
            'path-case': self.NESTED.format('https://example.invalid/Team/shared.git'),
            'double-suffix': self.NESTED.format('https://example.invalid/team/shared.git.git'),
            'double-slash': self.NESTED.format('https://example.invalid/team/shared.git//'),
            'other-host': self.NESTED.format('https://mirror.invalid/team/shared.git'),
            'relative': self.NESTED.format('../shared.git'),
            'dot-relative': self.NESTED.format('./shared'),
            'empty-declarations': '',
            'other-path': '[submodule "shared"]\n path = dependencies/other\n url = https://example.invalid/team/shared.git\n',
            'duplicate-path': self.NESTED.format('https://example.invalid/team/shared.git')
                + '[submodule "copy"]\n path = dependencies/shared\n url = https://example.invalid/team/shared.git\n',
            'malformed': 'not a declaration\n'}
        for case, declaration in refusals.items():
            with self.subTest(case=case):
                self.write(self.repo, '.gitmodules', declaration)
                self.commit_with_gitlinks({'dependencies/shared': nested}); self.pin()
                report = self.run_cli(1)
                self.assert_source_errors(report, PROJECT, ['nested-pin-unresolvable'], ['dependencies/shared/eng/Neutral.props'])
                self.assertEqual(self.summaries(report)['references/opaque']['crossTreeReads'], [])
        (self.repo / '.gitmodules').unlink()
        self.commit_with_gitlinks({'dependencies/shared': nested}); self.pin()
        self.assert_source_errors(self.run_cli(1), PROJECT, ['nested-pin-unresolvable'], ['dependencies/shared/eng/Neutral.props'])

    def test_nested_pin_ambiguous_and_relative_root_identities_refuse(self):
        shared = self.add_root('shared', 'https://example.invalid/team/shared.git')
        self.write(shared, 'eng/Runner.props', self.EXE)
        nested = self.pin_root('shared', self.commit(shared))
        self.write(self.repo, PROJECT, '<Project><Import Project="../../../dependencies/shared/eng/Runner.props"/></Project>')
        self.write(self.repo, '.gitmodules', self.NESTED.format('https://example.invalid/team/shared.git'))
        self.commit_with_gitlinks({'dependencies/shared': nested}); self.pin()
        shared_source = dict(repository='references/shared', path='eng/Runner.props', kind='source', identity='eng/Runner.props')
        report = self.run_cli(1)
        self.assertEqual(report['errors'], [])
        self.assertEqual([s['surface'] for s in report['surfaces']], [self.binding(), shared_source])
        # A second root with the same normalized remote makes the nested source ambiguous.
        self.add_root('mirror', 'https://example.invalid/team/shared/')
        self.pin()
        report = self.run_cli(1)
        self.assert_source_errors(report, PROJECT, ['nested-pin-unresolvable'], ['dependencies/shared/eng/Runner.props'])
        self.assertEqual([s['surface'] for s in report['surfaces']], [shared_source])
        # Identical relative URLs depend on different superproject remotes and never match.
        relative = self.add_root('relative', '../relative.git')
        self.write(relative, 'eng/Runner.props', self.EXE)
        relative_pin = self.pin_root('relative', self.commit(relative))
        self.write(self.repo, '.gitmodules', '[submodule "relative"]\n path = dependencies/relative\n url = ../relative.git\n')
        self.write(self.repo, PROJECT, '<Project><Import Project="../../../dependencies/relative/eng/Runner.props"/></Project>')
        self.commit_with_gitlinks({'dependencies/relative': relative_pin}); self.pin()
        report = self.run_cli(1)
        self.assert_source_errors(report, PROJECT, ['nested-pin-unresolvable'], ['dependencies/relative/eng/Runner.props'])
        self.assertEqual([s['surface'] for s in report['surfaces']], [
            dict(shared_source, repository='references/relative'), shared_source])

    def test_nested_pin_missing_nested_commit_is_unavailable(self):
        shared = self.add_root('shared', 'https://example.invalid/team/shared.git')
        with tempfile.TemporaryDirectory() as directory:
            stranger = Path(directory)
            self.git(stranger, 'init', '-q')
            self.write(stranger, 'eng/Runner.props', self.EXE)
            unavailable = self.commit(stranger)
        self.write(self.repo, '.gitmodules', self.NESTED.format('https://example.invalid/team/shared.git'))
        self.write(self.repo, PROJECT, '<Project><Import Project="../../../dependencies/shared/eng/Runner.props"/></Project>')
        self.commit_with_gitlinks({'dependencies/shared': unavailable}); self.pin()
        report = self.run_cli(1)
        self.assert_source_errors(report, PROJECT, ['nested-object-unavailable'], ['dependencies/shared/eng/Runner.props'])
        self.assertEqual(report['surfaces'], [])
        self.assertFalse((shared / 'dependencies').exists())

    def test_nested_pin_partial_clone_objects_are_never_fetched(self):
        with tempfile.TemporaryDirectory() as directory:
            server = Path(directory) / 'server'
            server.mkdir()
            self.git(server, 'init', '-q')
            self.git(server, 'config', 'uploadpack.allowFilter', 'true')
            self.git(server, 'config', 'uploadpack.allowAnySHA1InWant', 'true')
            self.write(server, 'README.md', 'published\n')
            self.commit(server)
            published = self.git(server, 'rev-parse', '--abbrev-ref', 'HEAD')
            # The nested commit exists only behind a ref a clone never fetches.
            self.git(server, 'checkout', '-q', '--orphan', 'hidden')
            self.write(server, 'eng/Runner.props', self.EXE)
            hidden = self.commit(server)
            self.git(server, 'update-ref', 'refs/hidden/nested', hidden)
            self.git(server, 'checkout', '-q', '-f', published)
            self.git(server, 'branch', '-q', '-D', 'hidden')
            location = self.root / 'references/shared'
            self.git(self.root / 'references', 'clone', '-q', '--filter=blob:none', '--no-checkout', server.as_uri(), 'shared')
            self.add_root('shared', 'https://example.invalid/team/shared.git')
            self.write(self.repo, '.gitmodules', self.NESTED.format('https://example.invalid/team/shared.git'))
            self.write(self.repo, PROJECT, '<Project><Import Project="../../../dependencies/shared/eng/Runner.props"/></Project>')
            self.commit_with_gitlinks({'dependencies/shared': hidden}); self.pin()
            report = self.run_cli(1)
            self.assert_source_errors(report, PROJECT, ['nested-object-unavailable'], ['dependencies/shared/eng/Runner.props'])
            self.assertEqual(report['surfaces'], [])
            missing = subprocess.run(['git', '-C', str(location), 'cat-file', '-e', hidden], capture_output=True,
                                     env={**os.environ, 'GIT_NO_LAZY_FETCH': '1'})
            self.assertNotEqual(missing.returncode, 0, 'the promisor object must not be fetched')

    def test_nested_pin_second_hop_escapes_and_substituted_gitlinks_refuse(self):
        other = self.add_root('other')
        self.write(other, 'eng/Exe.props', self.EXE)
        self.write(other, 'src/Tool.cs', 'builder.Services.AddMcpServer();')
        self.pin_root('other', self.commit(other))
        shared = self.add_root('shared', 'https://example.invalid/team/shared.git')
        self.write(shared, 'eng/Hop.props', '<Project><Import Project="$(MSBuildThisFileDirectory)../../other/eng/Exe.props"/></Project>')
        self.write(shared, 'eng/Back.props', '<Project><Import Project="../../opaque/eng/Local.props"/></Project>')
        self.write(shared, 'eng/Vendor.props', '<Project><Import Project="../vendor/v.props" Condition="Exists(\'../vendor/v.props\')"/></Project>')
        self.write(shared, 'eng/Compile.props', '<Project><ItemGroup><Compile Include="$(MSBuildThisFileDirectory)../../other/src/Tool.cs"/></ItemGroup></Project>')
        shared_pin = self.commit_with_gitlinks({'vendor': self.git(other, 'rev-parse', 'HEAD')}, shared)
        self.pin_root('shared', shared_pin)
        self.write(self.repo, 'eng/Local.props', self.EXE)
        self.write(self.repo, '.gitmodules', self.NESTED.format('https://example.invalid/team/shared.git'))
        for imported, current, rule, target in [
                ('../../../../shared/eng/Hop.props', '../shared/eng/Hop.props', 'unsafe-import-path', '../other/eng/Exe.props'),
                ('../../../../shared/eng/Back.props', '../shared/eng/Back.props', 'unsafe-import-path', 'eng/Local.props'),
                ('../../../../shared/eng/Vendor.props', '../shared/eng/Vendor.props', 'unsafe-import-path', '../shared/vendor/v.props'),
                ('../../../../shared/eng/Compile.props', '../shared/eng/Compile.props', 'unsafe-or-nested-compile-source', '../other/src/Tool.cs'),
                ('../../../dependencies/shared/eng/Hop.props', 'dependencies/shared/eng/Hop.props', 'unsafe-import-path', 'dependencies/other/eng/Exe.props')]:
            with self.subTest(imported=imported):
                self.write(self.repo, PROJECT, f'<Project><Import Project="{imported}"/></Project>')
                self.commit_with_gitlinks({'dependencies/shared': shared_pin}); self.pin()
                report = self.run_cli(1)
                pin = self.git(self.repo, 'rev-parse', 'HEAD')
                # Compile refusals name their declaring metadata file, as for local items.
                path = current if rule == 'unsafe-or-nested-compile-source' else PROJECT
                self.assertEqual(report['errors'], [dict(repository='references/opaque', gitlink=pin, path=path,
                                                         rule=rule + ':' + current, target=target)])
                self.assertEqual([s['surface'] for s in report['surfaces']], [
                    dict(repository='references/opaque', path='eng/Local.props', kind='source', identity='eng/Local.props'),
                    dict(repository='references/other', path='eng/Exe.props', kind='source', identity='eng/Exe.props'),
                    dict(repository='references/other', path='src/Tool.cs', kind='source', identity='src/Tool.cs')])
                self.assertFalse(self.summaries(report)['references/opaque']['inspectionComplete'])

    def test_nested_pin_substituted_links_are_not_regular_blobs(self):
        shared = self.add_root('shared')
        self.write(shared, 'eng/Runner.xml', self.EXE)
        (shared / 'eng/Link.xml').symlink_to('Runner.xml')
        self.pin_root('shared', self.commit(shared))
        self.write(self.repo, PROJECT, '<Project><Import Project="../../../../shared/eng/Link.xml"/></Project>')
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assert_source_errors(report, PROJECT, ['unsafe-import-path'], ['../shared/eng/Link.xml'])
        self.assertEqual((report['surfaces'], self.summaries(report)['references/opaque']['crossTreeReads']), ([], []))

    def test_nested_pin_substituted_compile_items_may_name_only_local_or_same_tree_sources(self):
        shared = self.add_root('shared')
        self.write(shared, 'eng/Compile.props', '<Project><ItemGroup><Compile Include="../../../shared-src/Local.cs"/>'
                   '<Compile Include="$(MSBuildThisFileDirectory)../src/Same.cs"/></ItemGroup></Project>')
        self.write(shared, 'src/Same.cs', 'builder.Services.AddMcpServer();')
        pinned = self.pin_root('shared', self.commit(shared))
        self.write(self.repo, 'shared-src/Local.cs', 'using System.CommandLine;')
        self.write(self.repo, PROJECT, '<Project><Import Project="../../../../shared/eng/Compile.props"/></Project>')
        self.commit(self.repo); self.pin()
        report = self.run_cli(1)
        self.assertEqual(report['errors'], [])
        self.assertEqual([(s['surface'], s['signals'], s['sources']) for s in report['surfaces']], [
            (self.binding(), ['command-line-source', 'mcp-registration'], ['../shared/src/Same.cs', 'shared-src/Local.cs']),
            (self.binding('shared-src/Local.cs', 'source', 'shared-src/Local.cs'), ['command-line-source'], ['shared-src/Local.cs']),
            (dict(repository='references/shared', path='src/Same.cs', kind='source', identity='src/Same.cs'), ['mcp-registration'], ['src/Same.cs'])])
        self.assertEqual(self.summaries(report)['references/opaque']['crossTreeReads'], [
            self.cross_read('../shared/eng/Compile.props', 'workspace', pinned, 'eng/Compile.props',
                            (shared / 'eng/Compile.props').read_text()),
            self.cross_read('../shared/src/Same.cs', 'workspace', pinned, 'src/Same.cs', 'builder.Services.AddMcpServer();')])

    def test_nested_pin_compile_sources_and_globs_resolve_with_provenance(self):
        shared = self.add_root('shared', 'https://example.invalid/team/shared.git')
        self.write(shared, 'src/Tool.cs', 'builder.Services.AddMcpServer();')
        nested = self.commit(shared)
        self.git(shared, 'rm', '-q', 'src/Tool.cs')
        self.write(shared, 'lib/Cli.cs', 'using System.CommandLine;')
        self.write(shared, 'lib/Plain.cs', 'class Plain {}')
        pinned = self.pin_root('shared', self.commit(shared))
        self.write(self.repo, '.gitmodules', self.NESTED.format('https://example.invalid/team/shared.git'))
        self.write(self.repo, PROJECT, '<Project><ItemGroup><Compile Include="../../../dependencies/shared/src/Tool.cs"/>'
                   '<Compile Include="../../../../shared/lib/*.cs"/></ItemGroup></Project>')
        self.commit_with_gitlinks({'dependencies/shared': nested}); self.pin()
        report = self.run_cli(1)
        self.assertEqual(report['errors'], [])
        self.assertEqual([(s['surface'], s['signals'], s['sources']) for s in report['surfaces']], [
            (self.binding(), ['command-line-source', 'mcp-registration'], ['../shared/lib/Cli.cs', 'dependencies/shared/src/Tool.cs']),
            (dict(repository='references/shared', path='lib/Cli.cs', kind='source', identity='lib/Cli.cs'), ['command-line-source'], ['lib/Cli.cs'])])
        self.assertEqual(self.summaries(report)['references/opaque']['crossTreeReads'], [
            self.cross_read('../shared/lib/Cli.cs', 'workspace', pinned, 'lib/Cli.cs', 'using System.CommandLine;'),
            self.cross_read('../shared/lib/Plain.cs', 'workspace', pinned, 'lib/Plain.cs', 'class Plain {}'),
            self.cross_read('dependencies/shared/src/Tool.cs', 'nested', nested, 'src/Tool.cs', 'builder.Services.AddMcpServer();',
                            gitlink='dependencies/shared')])
        # A glob cannot prove what an unopened gitlink below its directory contains.
        self.commit_with_gitlinks({'lib/vendor': nested}, shared)
        self.pin_root('shared')
        self.write(self.repo, PROJECT, '<Project><ItemGroup><Compile Include="../../../../shared/lib/*.cs"/></ItemGroup></Project>')
        self.commit_with_gitlinks({'dependencies/shared': nested}); self.pin()
        report = self.run_cli(1)
        self.assert_source_errors(report, PROJECT, ['unsafe-or-nested-compile-source'], ['../shared/lib/*.cs'])
        self.assertEqual(self.summaries(report)['references/opaque']['crossTreeReads'], [])

    def test_nested_pin_unavailable_workspace_root_object_refuses(self):
        shared = self.add_root('shared')
        self.write(shared, 'eng/Runner.props', self.EXE)
        self.commit(shared)
        self.write(self.repo, PROJECT, '<Project><Import Project="../../../../shared/eng/Runner.props"/></Project>')
        self.commit(self.repo); self.pin()
        pin = self.git(self.repo, 'rev-parse', 'HEAD')
        refused = dict(repository='references/opaque', gitlink=pin, path=PROJECT, rule='workspace-object-unavailable:' + PROJECT,
                       target='../shared/eng/Runner.props')
        self.pin_root('shared', 'e' * 40)
        report = self.run_cli(1)
        self.assertEqual(report['errors'], [refused, dict(repository='references/shared', gitlink='e' * 40, rule='git-object-unavailable')])
        self.assertEqual(report['surfaces'], [])
        # An uninitialized sibling cannot borrow the parent repository's objects.
        head = self.pin_root('shared', self.git(shared, 'rev-parse', 'HEAD'))
        shutil.move(shared / '.git', self.root / 'held-git')
        report = self.run_cli(1)
        self.assertEqual(report['errors'], [refused, dict(repository='references/shared', gitlink=head, rule='reference-root-uninitialized')])
        self.assertEqual(report['surfaces'], [])

    def test_nested_pin_local_closure_and_context_free_api(self):
        shared = self.add_root('shared')
        self.write(shared, 'eng/Runner.props', self.EXE)
        self.pin_root('shared', self.commit(shared))
        self.write(self.repo, PROJECT, '<Project><Import Project="../../../../shared/eng/Runner.props"/></Project>')
        self.commit(self.repo); self.pin()
        tree = census.Tree(self.repo, self.git(self.repo, 'rev-parse', 'HEAD'))
        parent = census.Tree(self.root, self.git(self.root, 'rev-parse', 'HEAD'))
        workspace = census.Workspace(self.root, parent, census.declarations(parent))
        sources = census.compilation_closure(tree, PROJECT, census.Resolver(workspace, 'references/opaque', tree))
        self.assertEqual(sources, [dict(path=PROJECT, sha256=census.digest((self.repo / PROJECT).read_bytes()))])
        entry = self.allowance(sources=sources, classification='non-surface-qualification-fixture', row='PA02')
        entry.update(sourcePrefix=str(Path(PROJECT).parent), compilationClosure=True); self.save()
        report = self.run_cli(1)
        self.assertEqual([(s['surface']['repository'], s['status']) for s in report['surfaces']],
                         [('references/opaque', 'approved'), ('references/shared', 'rejected')])
        self.assertEqual(len(self.summaries(report)['references/opaque']['crossTreeReads']), 1)
        # Substituted bytes are pinned by the parent; a signal they add is still drift.
        self.write(shared, 'eng/Runner.props', '<Project><PropertyGroup><OutputType>Exe</OutputType><PackAsTool>true</PackAsTool></PropertyGroup></Project>')
        self.pin_root('shared', self.commit(shared))
        drift = self.run_cli(1)['surfaces'][0]
        self.assertEqual((drift['reason'], drift['unexpectedSignals']), ('allowance-signal-or-source-drift', ['packed-tool']))
        # Without root declarations, cross-tree reads are refused rather than skipped.
        for imported, rule, target in [('../../../../shared/eng/Runner.props', 'unsafe-import-path', '../shared/eng/Runner.props'),
                                       ('../../../nested/eng/Runner.props', 'nested-pin-unresolvable', 'nested/eng/Runner.props')]:
            with self.subTest(imported=imported):
                self.write(self.repo, PROJECT, f'<Project><Import Project="{imported}"/></Project>')
                head = self.commit_with_gitlinks({'nested': self.git(shared, 'rev-parse', 'HEAD')})
                with self.assertRaises(census.CensusError) as refused:
                    census.compilation_closure(census.Tree(self.repo, head), PROJECT)
                self.assertEqual((str(refused.exception), refused.exception.target), (rule + ':' + PROJECT, target))

    # Exists() guard extension. FIRST is a nested path, SECOND a workspace path
    # present at its root pin and THIRD a parent-tree path outside every root,
    # which is refused whenever it is reached.
    FIRST = '$(MSBuildThisFileDirectory)../../../dependencies/shared/eng/{}'
    SECOND = '$(MSBuildThisFileDirectory)../../../../shared/eng/{}'
    THIRD = '$(MSBuildThisFileDirectory)../../../../../outside/{}'

    def guard_fixture(self):
        shared = self.add_root('shared', 'https://example.invalid/team/shared.git')
        self.write(shared, 'eng/Package.props', '<Project/>')
        self.write(shared, 'eng/Provenance.targets', '<Project/>')
        nested = self.commit(shared)
        self.write(shared, 'eng/Package.props', self.EXE)
        pinned = self.pin_root('shared', self.commit(shared))
        self.write(self.root, 'references/present.props', '<Project/>')
        self.git(self.root, 'add', 'references/present.props')
        self.write(self.repo, '.gitmodules', self.NESTED.format('https://example.invalid/team/shared.git'))
        return shared, nested, pinned

    def guarded(self, body, nested, expected, target=None):
        self.write(self.repo, PROJECT, '<Project>' + body + '</Project>')
        self.commit_with_gitlinks({'dependencies/shared': nested}); self.pin()
        report = self.run_cli(expected)
        if target:
            self.assert_source_errors(report, PROJECT, ['unsafe-import-path'], [target])
        else:
            self.assertEqual(report['errors'], [])
        return report

    def test_exists_guard_negated_present_fallback_import_is_not_visited(self):
        shared, nested, pinned = self.guard_fixture()
        layout = ('<PropertyGroup><First>' + self.FIRST.format('Package.props') + '</First><Second>' + self.SECOND.format('Package.props')
                  + '</Second><Third>' + self.THIRD.format('Package.props') + '</Third>'
                  "<Multi>$(Second)</Multi><Multi Condition=\"'$(Mode)' == 'b'\">$(Third)</Multi></PropertyGroup>"
                  '<Import Project="$(First)" Condition="Exists(\'$(First)\')"/>'
                  '<Import Project="$(Second)" Condition="!Exists(\'$(First)\') And Exists(\'$(Second)\')"/>')
        shared_source = dict(repository='references/shared', path='eng/Package.props', kind='source', identity='eng/Package.props')
        # The nested FIRST is never proven present; the workspace SECOND is, so the fallback is unreachable.
        for condition in ["!Exists('$(First)') And !Exists('$(Second)')",
                          "!Exists('$(MSBuildThisFileDirectory)Runner.csproj')",
                          "!Exists('$(MSBuildThisFileDirectory)')",
                          "Exists('" + self.FIRST.format('Missing.props') + "')",
                          "Exists('" + self.SECOND.format('Missing.props') + "')",
                          "Exists('" + self.THIRD.format('Missing.props') + "') and '$(Mode)' == 'a'"]:
            with self.subTest(condition=condition):
                report = self.guarded(layout + f'<Import Project="$(Third)" Condition="{condition}"/>', nested, 1)
                self.assertEqual([(s['surface'], s['signals']) for s in report['surfaces']],
                                 [(self.binding(), ['executable-project']), (shared_source, ['unresolved-tool-metadata'])])
                self.assertEqual(self.summaries(report)['references/opaque']['crossTreeReads'], [
                    self.cross_read('../shared/eng/Package.props', 'workspace', pinned, 'eng/Package.props', self.EXE),
                    self.cross_read('dependencies/shared/eng/Package.props', 'nested', nested, 'eng/Package.props', '<Project/>',
                                    gitlink='dependencies/shared')])
        with self.subTest(guard='ImportGroup'):
            self.guarded(layout + '<ImportGroup Condition="!Exists(\'$(Second)\')"><Import Project="$(Third)"/></ImportGroup>', nested, 1)
        # Every other guard proves nothing, so the fallback is reached and refused.
        for condition in ["!Exists('$(First)')",
                          "!Exists('$(Second)') Or '$(Mode)' == 'x'",
                          "!Exists('$(Unknown)')",
                          "Exists('$(Unknown)/Package.props')",
                          "!Exists('$(Multi)')",
                          "Exists('$(Multi)')",
                          "(!Exists('$(Second)'))",
                          "!(Exists('$(Second)'))",
                          "!Exists('$(MSBuildThisFileDirectory)../../../../present.props')",
                          "Exists('$(MSBuildThisFileDirectory)../../../../../../../above.props')",
                          "Exists('$(MSBuildThisFileDirectory)')",
                          "Exists('$(MSBuildThisFileDirectory)*.csproj')",
                          "!Exists('$(Second)') and '$(Mode)"]:
            with self.subTest(condition=condition):
                report = self.guarded(layout + f'<Import Project="$(Third)" Condition="{condition}"/>', nested, 1,
                                      '../../outside/Package.props')
                self.assertEqual([s['surface'] for s in report['surfaces']], [shared_source])
        with self.subTest(guard='Choose'):
            # Import cannot occur in When; a When-selected property keeps its conservative union.
            self.guarded(layout + "<Choose><When Condition=\"!Exists('$(Second)')\"><PropertyGroup><Late>$(Third)</Late>"
                         '</PropertyGroup></When></Choose><Import Project="$(Late)" Condition="\'$(Late)\' != \'\'"/>',
                         nested, 1, '../../outside/Package.props')

    def test_exists_guard_self_referential_property_fallback_chain_drops_unreachable_alternatives(self):
        shared, nested, pinned = self.guard_fixture()
        first, second, third = (pattern.format('Provenance.targets') for pattern in (self.FIRST, self.SECOND, self.THIRD))
        chain = ('<PropertyGroup><Targets>' + first + '</Targets>'
                 f"<Targets Condition=\"!Exists('$(Targets)') and Exists('{second}')\">{second}</Targets>"
                 f"<Targets Condition=\"!Exists('$(Targets)') and Exists('{third}')\">{third}</Targets></PropertyGroup>")
        reads = [self.cross_read('../shared/eng/Provenance.targets', 'workspace', pinned, 'eng/Provenance.targets', '<Project/>'),
                 self.cross_read('dependencies/shared/eng/Provenance.targets', 'nested', nested, 'eng/Provenance.targets',
                                 '<Project/>', gitlink='dependencies/shared')]
        # The nested first value is never present, so the workspace alternative stays; the
        # outside-root alternative is proven absent and contributes nothing.
        report = self.guarded(chain + '<Import Project="$(Targets)"/>', nested, 1)
        self.assertEqual(self.summaries(report)['references/opaque']['crossTreeReads'], reads)
        # A workspace-present value makes a later !Exists('$(P)') definition unreachable.
        present = ('<PropertyGroup><Targets>' + second + '</Targets>'
                   f"<Targets Condition=\"!Exists('$(Targets)')\">{third}</Targets></PropertyGroup>")
        report = self.guarded(present + '<Import Project="$(Targets)"/>', nested, 1)
        self.assertEqual(self.summaries(report)['references/opaque']['crossTreeReads'], reads[:1])
        dropped = ('<PropertyGroup><Targets>' + second + '</Targets></PropertyGroup>'
                   f"<PropertyGroup Condition=\"Exists('{third}')\"><Targets>{third}</Targets></PropertyGroup>")
        self.assertEqual(self.summaries(self.guarded(dropped + '<Import Project="$(Targets)"/>', nested, 1))
                         ['references/opaque']['crossTreeReads'], reads[:1])
        for body in [('<PropertyGroup><Targets>' + second + '</Targets>'
                      f"<Targets Condition=\"!Exists('$(Targets)') or '$(Mode)' == ''\">{third}</Targets></PropertyGroup>"),
                     ('<PropertyGroup><Targets>' + second + '</Targets></PropertyGroup>'
                      f"<Choose><When Condition=\"!Exists('$(Targets)')\"><PropertyGroup><Targets>{third}</Targets>"
                      '</PropertyGroup></When></Choose>'),
                     ('<PropertyGroup><Targets>' + second + '</Targets></PropertyGroup>'
                      f"<Target Name=\"Late\"><PropertyGroup><Targets Condition=\"!Exists('$(Targets)')\">{third}</Targets>"
                      '</PropertyGroup></Target>')]:
            with self.subTest(body=body):
                self.guarded(body + '<Import Project="$(Targets)"/>', nested, 1, '../../outside/Provenance.targets')
        # A dropped classification alternative leaves no executable signal; a bypassable one keeps it.
        for condition, signals in [(f"Exists('{third}')", []), (f"Exists('{third}') or '$(Mode)' == ''", ['executable-project'])]:
            with self.subTest(condition=condition):
                report = self.guarded(f'<PropertyGroup><OutputType>Library</OutputType><OutputType Condition="{condition}">Exe'
                                      '</OutputType></PropertyGroup>', nested, 1)
                self.assertEqual([s['signals'] for s in report['surfaces'] if s['surface'] == self.binding()],
                                 [signals] if signals else [])
        # Only PropertyGroup definitions are evaluated; other conditional values keep their union.
        report = self.guarded(f'<ItemGroup><Thing Include="a"><OutputType Condition="Exists(\'{third}\')">Exe</OutputType>'
                              '</Thing></ItemGroup>', nested, 1)
        self.assertEqual([s['signals'] for s in report['surfaces'] if s['surface'] == self.binding()], [['executable-project']])


if __name__=='__main__':
    unittest.main()
