"""Removal-sensitive checks for strict plans and immutable vector assertions."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from live_plans import ROOT, check_dependencies, digest, execution_selection, freeze_input, load_plan, resolve, typed
from validate import VectorError


class PlanTests(unittest.TestCase):
    def test_execution_uses_frozen_bytes_and_rejects_approval_races(self):
        with tempfile.TemporaryDirectory() as directory:
            source, target = Path(directory) / 'source.json', Path(directory) / 'inputs' / 'frozen.json'
            source.write_text('{"approved":true}')
            expected = digest(source)
            frozen = freeze_input(source, target, expected)
            source.write_text('{"approved":false}')
            self.assertEqual('{"approved":true}', frozen.read_text())
            self.assertEqual(expected, digest(frozen))
            with self.assertRaisesRegex(VectorError, 'input changed after approval'):
                freeze_input(source, target, expected)
            self.assertEqual('{"approved":true}', frozen.read_text())

    def test_full_preflight_checks_all_calls_and_child_checks_only_selected_calls(self):
        selections = [{'operation': 'fixture.first'}, {'operation': 'fixture.second'}]
        self.assertEqual(selections, execution_selection(selections, None))
        self.assertEqual([selections[1]], execution_selection(selections, 'fixture.second'))
        with self.assertRaisesRegex(VectorError, 'Exactly one'):
            execution_selection(selections, 'missing')
        with self.assertRaisesRegex(VectorError, 'Exactly one'):
            execution_selection(selections + [selections[0]], 'fixture.first')

    def setUp(self):
        self.vector = ROOT / 'tools/conformance-vectors/v1/modules/Hexalith.Tenants.Contracts/get-tenant-users.vector.json'
        self.path = ROOT / 'tools/live-topology/plans/tenants.get-tenant-users.json'
        self.plan = json.loads(self.path.read_text())

    def reject(self, mutate, message):
        plan = copy.deepcopy(self.plan)
        mutate(plan)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'plan.json'
            path.write_text(json.dumps(plan))
            with self.assertRaisesRegex(VectorError, message):
                load_plan(path, self.vector)

    def test_all_21_approved_vectors_have_valid_plans(self):
        vectors = sorted((ROOT / 'tools/conformance-vectors/v1/modules').rglob('*.vector.json'))
        self.assertEqual(21, len(vectors))
        for vector in vectors:
            operation = json.loads(vector.read_text())['operation']
            with self.subTest(operation=operation):
                load_plan(ROOT / 'tools/live-topology/plans' / (operation + '.json'), vector)

    def test_unreviewed_or_stale_restored_package_fails_preflight(self):
        policy = {'baselinePackages': {'Gateway.Client': '1.0.0'}, 'modules': {'Example.Contracts': '2.0.0'}}
        approved = {'Gateway.Client/1.0.0': {'type': 'package'}, 'Example.Contracts/2.0.0': {'type': 'package'}}
        check_dependencies({'libraries': approved}, policy)
        for change in ['new-version', 'missing', 'extra']:
            libraries = approved.copy()
            if change == 'new-version':
                libraries.pop('Gateway.Client/1.0.0'); libraries['Gateway.Client/1.1.0'] = {'type': 'package'}
            elif change == 'missing': libraries.pop('Gateway.Client/1.0.0')
            else: libraries['Domain.Server/1.0.0'] = {'type': 'package'}
            with self.subTest(change=change), self.assertRaisesRegex(VectorError, 'dependency closure differs'):
                check_dependencies({'libraries': libraries}, policy)
        with self.assertRaisesRegex(VectorError, 'duplicate package'):
            check_dependencies({'libraries': {'Gateway.Client/0.9.0': {'type': 'package'}, **approved}}, policy)

    def test_unknown_fields_fail_closed(self):
        self.reject(lambda p: p.update(retryCommands=True), 'Additional properties')
        self.reject(lambda p: p['actions'][0].update(ignoreAssertions=True), 'not valid under any')

    def test_observation_assertion_operands_keep_strict_json_types(self):
        for operand in [True, False, 1.0, -1, '1']:
            with self.subTest(operator='arrayLength', operand=operand):
                self.reject(lambda p: p['actions'][1]['query']['assertions'][0].update(
                    operator='arrayLength', value=operand), 'arrayLength requires')
        for operand in [1, 0, 'true', None]:
            with self.subTest(operator='exists', operand=operand):
                self.reject(lambda p: p['actions'][1]['query']['assertions'][0].update(
                    operator='exists', value=operand), 'exists requires')

    def test_stale_vector_hash_rejects_plan(self):
        self.reject(lambda p: p.update(vectorSha256='0' * 64), 'stale vector')

    def test_duplicate_or_missing_steps_fail(self):
        self.reject(lambda p: p['actions'].append(p['actions'][0]), 'exactly once')
        self.reject(lambda p: p['actions'].pop(0), 'exactly once')

    def test_command_without_persisted_barrier_fails(self):
        self.reject(lambda p: p['actions'].pop(1), 'persisted read barrier')

    def test_cursor_assertion_cannot_be_dropped(self):
        action = next(i for i, a in enumerate(self.plan['actions']) if a.get('step') == '/invocation')
        self.reject(lambda p: p['actions'][action].pop('assertionBindings'), 'scripted assertion')

    def test_static_assertion_cannot_be_replaced(self):
        action = next(i for i, a in enumerate(self.plan['actions']) if a.get('step') == '/invocation')
        self.reject(lambda p: p['actions'][action]['assertionBindings'][0].update(index=0), 'cannot weaken static')

    def test_unresolved_cursor_is_rejected_before_execution(self):
        self.reject(lambda p: p['actions'][-1]['bindings'][0].update(capture='missing'), 'unresolved capture')

    def test_scripted_input_requires_explicit_binding(self):
        self.reject(lambda p: p['actions'][-1].pop('bindings'), 'no live binding')

    def test_input_binding_cannot_change_static_fields(self):
        self.reject(lambda p: p['actions'][-1]['bindings'][0].update(path='/payload/From'), 'time binding|static binding')

    def test_capture_types_are_checked_without_coercion(self):
        for value in [None, '', 2, True, []]:
            with self.subTest(value=value), self.assertRaises(VectorError):
                typed(value, 'string')
        for value in ['2026-01-01', 'not-a-date', '2026-01-01T00:00:00']:
            with self.subTest(value=value), self.assertRaises(VectorError):
                typed(value, 'timestamp')
        self.assertEqual('real-cursor', typed('real-cursor', 'string'))

    def test_real_typed_values_bind_existing_targets(self):
        call = {'envelope': {'cursor': 'scripted-cursor'}, 'payload': {'From': 'old'}}
        actual = resolve(call, [{'path': '/envelope/cursor', 'capture': 'cursor'},
                                {'path': '/payload/From', 'capture': 'time', 'offsetSeconds': -.001}],
                         {'cursor': 'real-cursor', 'time': '2026-01-01T00:00:00Z'})
        self.assertEqual('real-cursor', actual['envelope']['cursor'])
        self.assertEqual('2025-12-31T23:59:59.999000+00:00', actual['payload']['From'])
        self.assertEqual('scripted-cursor', call['envelope']['cursor'])
        with self.assertRaisesRegex(VectorError, 'Unresolved capture'):
            resolve(call, [{'path': '/envelope/cursor', 'capture': 'missing'}], {})
        with self.assertRaisesRegex(VectorError, 'does not exist'):
            resolve(call, [{'path': '/envelope/missing', 'capture': 'cursor'}], {'cursor': 'real'})

    def test_float_assertion_selector_reports_located_integer_failure(self):
        action = next(i for i, a in enumerate(self.plan['actions']) if a.get('step') == '/invocation')
        self.reject(lambda p: p['actions'][action]['assertionBindings'][0].update(index=6.0),
                    r'/actions/.*assertionBindings index requires a nonnegative integer token')

    def test_envelope_only_assertions_cannot_qualify_as_persisted_barriers(self):
        for assertions in [[{'path': '/operation', 'operator': 'equals', 'value': 'tenants.get-tenant'}],
                           [{'path': '/document/missing', 'operator': 'exists', 'value': False}]]:
            with self.subTest(assertions=assertions):
                self.reject(lambda p: p['actions'][1]['query'].update(assertions=assertions), 'persisted read barrier')

    def test_negative_party_predicates_and_complete_update_observation_are_retained(self):
        for name, fields in [('list-parties', {'Type', 'Active', 'CreatedAfter'}),
                             ('search-parties', {'Query', 'Type', 'Active'})]:
            plan = json.loads((ROOT / 'tools/live-topology/plans' / ('parties.' + name + '.json')).read_text())
            negatives = [action for action in plan['actions'] if action.get('label', '').startswith('nonmatching-')]
            self.assertEqual({field.lower() for field in fields}, {action['label'].removeprefix('nonmatching-') for action in negatives})
            for action in negatives:
                self.assertIn({'path': '/document/items', 'operator': 'arrayLength', 'value': 0}, action['query']['assertions'])
        plan = json.loads((ROOT / 'tools/live-topology/plans/parties.update-party.json').read_text())
        observation = next(action['query'] for action in plan['actions'] if action.get('label') == 'persisted-invocation')
        expected = {'/document/personDetails/lastName': 'Lovelace', '/document/type': 'Person',
                    '/document/contactChannels/0/id': 'email-story49', '/document/contactChannels/0/type': 'Email',
                    '/document/contactChannels/0/isPreferred': True}
        actual = {assertion['path']: assertion['value'] for assertion in observation['assertions'] if assertion['operator'] == 'equals'}
        self.assertEqual(expected, {key: actual[key] for key in expected})

    def test_actual_preflight_delegates_artifact_inventory_and_core_rejections(self):
        import live_plans
        from unittest.mock import patch
        host = ROOT / 'tests/Hexalith.McpCli.ConformanceHost/bin/Release/net10.0/Hexalith.McpCli.ConformanceHost.dll'
        for boundary in ['check_adapter_dependencies', 'artifact_for', '_verify_artifact_in_host', 'approved_inventory', '_preflight_vectors', 'validate_call']:
            with self.subTest(boundary=boundary), tempfile.TemporaryDirectory() as directory, \
                    patch.object(live_plans, 'check_adapter_dependencies'), \
                    patch.object(live_plans, boundary, side_effect=VectorError('delegated-rejection-' + boundary)) as delegated:
                with self.assertRaisesRegex(VectorError, 'delegated-rejection-' + boundary):
                    live_plans.preflight(host, Path(directory), operation='parties.list-parties')
                delegated.assert_called_once()

    def test_actual_inventory_coverage_and_vector_validator_rejections_stop_preflight(self):
        import live_plans
        import subprocess
        from unittest.mock import patch
        host = ROOT / 'tests/Hexalith.McpCli.ConformanceHost/bin/Release/net10.0/Hexalith.McpCli.ConformanceHost.dll'
        real_run = subprocess.run
        inventory_calls = []
        def run(arguments, **kwargs):
            if '--inventory' in arguments:
                inventory_calls.append(arguments)
                return subprocess.CompletedProcess(arguments, 0, '["inventory finding"]', '')
            return real_run(arguments, **kwargs)
        with tempfile.TemporaryDirectory() as directory, patch.object(live_plans, 'check_adapter_dependencies'), \
                patch.object(live_plans.subprocess, 'run', side_effect=run):
            with self.assertRaisesRegex(VectorError, 'inventory coverage failed'):
                live_plans.preflight(host, Path(directory), operation='parties.list-parties')
        self.assertEqual(1, len(inventory_calls))
        with tempfile.TemporaryDirectory() as directory, patch.object(live_plans, 'check_adapter_dependencies'), \
                patch.object(live_plans, 'validate_vectors', return_value=['vector validator finding']) as validate:
            with self.assertRaisesRegex(VectorError, 'vector validator finding'):
                live_plans.preflight(host, Path(directory), operation='parties.list-parties')
            validate.assert_called_once()

    def test_changed_companion_observations_pass_actual_core_validation(self):
        from live_plans import HeadProcess, validate_call
        host = ROOT / 'tests/Hexalith.McpCli.ConformanceHost/bin/Release/net10.0/Hexalith.McpCli.ConformanceHost.dll'
        with tempfile.TemporaryDirectory() as home:
            head = HeadProcess(host, home, 30)
            for name in ['parties.list-parties', 'parties.search-parties', 'parties.update-party']:
                plan = json.loads((ROOT / 'tools/live-topology/plans' / (name + '.json')).read_text())
                for action in plan['actions']:
                    if 'query' in action:
                        with self.subTest(operation=name, label=action['label']):
                            validate_call(head, action['query'])


class AdapterDependencyTests(unittest.TestCase):
    def test_actual_built_adapter_matches_restored_production_closure(self):
        import live_plans
        host = ROOT / 'tests/Hexalith.McpCli.ConformanceHost/bin/Release/net10.0/Hexalith.McpCli.ConformanceHost.dll'
        assets = json.loads((ROOT / 'src/Hexalith.McpCli/obj/project.assets.json').read_text())
        live_plans.check_adapter_dependencies(host, assets)

    def fixture(self, root):
        import base64
        import hashlib
        import zipfile
        root = Path(root)
        host = root / 'adapter.dll'
        host.write_bytes(b'fixture adapter')
        target = '.NETCoreApp,Version=v10.0'
        assets = {'libraries': {}, 'targets': {target: {}}, 'packageFolders': {str(root / 'cache'): {}}}
        deps = {'runtimeTarget': {'name': target}, 'libraries': {}, 'targets': {target: {}}}
        for name, filename in [('Gateway.Client', 'Gateway.Client.dll'), ('Example.Contracts', 'Example.Contracts.dll'),
                               ('Shared.Framework', 'System.Runtime.dll')]:
            identity = name + '/1.0.0'
            relative = name.lower() + '/1.0.0'
            package = root / 'cache' / relative / (name.lower() + '.1.0.0.nupkg')
            package.parent.mkdir(parents=True)
            content = (name + ' approved runtime assembly').encode()
            asset = 'lib/net10.0/' + filename
            with zipfile.ZipFile(package, 'w') as archive: archive.writestr(asset, content)
            content_hash = base64.b64encode(hashlib.sha512(package.read_bytes()).digest()).decode()
            assets['libraries'][identity] = {'type': 'package', 'path': relative, 'sha512': content_hash}
            assets['targets'][target][identity] = {'runtime': {asset: {}}}
            if name != 'Shared.Framework':
                (root / filename).write_bytes(content)
                deps['libraries'][identity] = {'type': 'package', 'sha512': 'sha512-' + content_hash}
                deps['targets'][target][identity] = {'runtime': {asset: {}}}
        host.with_suffix('.deps.json').write_text(json.dumps(deps))
        return host, assets, deps

    def test_adapter_closure_rejects_stale_private_bytes_and_dependency_metadata(self):
        import live_plans
        from unittest.mock import patch
        for defect in [None, 'bytes', 'identity', 'dependency-reference', 'content-hash', 'runtime-asset', 'shared-private-override']:
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as directory:
                host, assets, deps = self.fixture(directory)
                identity = 'Gateway.Client/1.0.0'
                if defect == 'bytes': (host.parent / 'Gateway.Client.dll').write_bytes(b'stale gateway client build')
                if defect == 'identity': deps['libraries']['Gateway.Client/0.9.0'] = deps['libraries'].pop(identity)
                if defect == 'dependency-reference': deps['targets'][deps['runtimeTarget']['name']][identity]['dependencies'] = {'Example.Contracts': '0.9.0'}
                if defect == 'content-hash': deps['libraries'][identity]['sha512'] = 'sha512-wrong'
                if defect == 'runtime-asset': deps['targets'][deps['runtimeTarget']['name']][identity]['runtime'] = {'lib/net9.0/Gateway.Client.dll': {}}
                if defect == 'shared-private-override': (host.parent / 'System.Runtime.dll').write_bytes(b'unreviewed private override')
                host.with_suffix('.deps.json').write_text(json.dumps(deps))
                with patch.object(live_plans, 'shared_runtime_assemblies', return_value={'System.Runtime.dll'}):
                    if defect:
                        with self.assertRaisesRegex((VectorError, RuntimeError), 'differ|missing'):
                            live_plans.check_adapter_dependencies(host, assets)
                    else:
                        live_plans.check_adapter_dependencies(host, assets)

    def test_genuine_stale_compiled_gateway_client_is_rejected_with_current_deps(self):
        import base64
        import hashlib
        import live_plans
        import shutil
        import subprocess
        import zipfile
        from unittest.mock import patch
        sdk = subprocess.run(['dotnet', '--list-sdks'], capture_output=True, text=True, timeout=30, check=True).stdout.splitlines()[-1]
        sdk_version, sdk_root = sdk.split(' ', 1)
        compiler = Path(sdk_root.strip('[]')) / sdk_version / 'Roslyn/bincore/csc.dll'
        runtime = next(line for line in subprocess.run(['dotnet', '--list-runtimes'], capture_output=True, text=True,
                       timeout=30, check=True).stdout.splitlines() if line.startswith('Microsoft.NETCore.App 10.'))
        _, runtime_version, runtime_root = runtime.split(maxsplit=2)
        corelib = Path(runtime_root.strip('[]')) / runtime_version / 'System.Private.CoreLib.dll'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            host, assets, deps = self.fixture(root)
            binaries = []
            for version in ['1.0.0.0', '0.9.0.0']:
                build = root / version
                build.mkdir()
                source = build / 'Client.cs'
                source.write_text('[assembly:System.Reflection.AssemblyVersion("' + version + '")] public class GatewayClient { public int Revision => ' + ('1' if version.startswith('1') else '0') + '; }')
                assembly = build / 'Gateway.Client.dll'
                subprocess.run(['dotnet', str(compiler), '-nologo', '-target:library', '-out:' + str(assembly),
                                '-reference:' + str(corelib), str(source)], capture_output=True, text=True, timeout=30, check=True)
                binaries.append(assembly)
            identity = 'Gateway.Client/1.0.0'
            package = root / 'cache/gateway.client/1.0.0/gateway.client.1.0.0.nupkg'
            with zipfile.ZipFile(package, 'w') as archive:
                archive.write(binaries[0], 'lib/net10.0/Gateway.Client.dll')
            content_hash = base64.b64encode(hashlib.sha512(package.read_bytes()).digest()).decode()
            assets['libraries'][identity]['sha512'] = content_hash
            deps['libraries'][identity]['sha512'] = 'sha512-' + content_hash
            host.with_suffix('.deps.json').write_text(json.dumps(deps))
            shutil.copyfile(binaries[0], host.parent / 'Gateway.Client.dll')
            with patch.object(live_plans, 'shared_runtime_assemblies', return_value={'System.Runtime.dll'}):
                live_plans.check_adapter_dependencies(host, assets)
                shutil.copyfile(binaries[1], host.parent / 'Gateway.Client.dll')
                with self.assertRaisesRegex(VectorError, 'Gateway.Client.dll.*private runtime DLL bytes differ'):
                    live_plans.check_adapter_dependencies(host, assets)
