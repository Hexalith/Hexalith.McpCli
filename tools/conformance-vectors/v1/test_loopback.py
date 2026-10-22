"""Focused checks for the process runner's request and document comparison rules."""

from __future__ import annotations

import base64
import copy
import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from run_loopback import (
    _assert_discovery_parity,
    _assert_document_parity,
    _assert_error_parity,
    _assert_request_parity,
    _assert_result,
    _expect_fields,
    _json_equal,
    _mask,
    _mask_result,
    _verify_artifact_in_host,
)
from validate import VectorError


HERE = Path(__file__).parent


def runtime_package(artifact, host):
    asset = 'lib/net10.0/Fixture.Contracts.dll'
    with zipfile.ZipFile(artifact, 'w') as archive:
        archive.writestr(asset, b'exact selected runtime DLL bytes')
    (host.parent / Path(asset).name).write_bytes(b'exact selected runtime DLL bytes')
    return {asset: {}}


class LoopbackRulesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.command = json.loads((HERE / "sample-command.json").read_text(encoding="utf-8"))["invocation"]
        self.rename = json.loads((HERE / "sample-rename.json").read_text(encoding="utf-8"))["invocation"]

    def test_generated_ids_are_masked_but_supplied_correlation_and_key_remain_exact(self) -> None:
        body = {"messageId": "01J9MZHXT3RKM0VWXRXGSJDATP", "correlationId": "01J9MZHXT3RKM0VWXRXGSJDATK",
                "idempotencyKey": "01J9MZHXT3RKM0VWXRXGSJDATM"}
        self.assertEqual({"messageId": "<generated>", "correlationId": body["correlationId"],
                          "idempotencyKey": body["idempotencyKey"]}, _mask(body, self.command, "request"))
        self.assertEqual({"messageId": "<generated>", "correlationId": "<generated>"},
                         _mask({"messageId": body["messageId"], "correlationId": body["messageId"]},
                               self.rename, "request"))

    def test_generated_id_must_be_a_ulid(self) -> None:
        with self.assertRaisesRegex(VectorError, "not a ULID"):
            _mask({"messageId": "not-a-ulid"}, self.command, "request")

    def test_command_result_masks_only_generated_identifiers(self) -> None:
        result = {"messageId": "01J9MZHXT3RKM0VWXRXGSJDATP",
                  "correlationId": "01J9MZHXT3RKM0VWXRXGSJDATK",
                  "idempotencyKey": "01J9MZHXT3RKM0VWXRXGSJDATM"}
        self.assertEqual("<generated>", _mask_result(result, self.command, "result")["messageId"])
        self.assertEqual(result["correlationId"], _mask_result(result, self.command, "result")["correlationId"])
        self.assertEqual(result["idempotencyKey"], _mask_result(result, self.command, "result")["idempotencyKey"])

    def test_expected_gateway_payload_and_paging_are_exact(self) -> None:
        _expect_fields({"body": {"payload": {"id": "A"}, "tenant": "t"}},
                       {"body": {"payload": {"id": "A"}, "tenant": "t"}}, "request")
        with self.assertRaisesRegex(VectorError, "/unused"):
            _expect_fields({"body": {"payload": {"id": "A"}, "tenant": "t", "unused": None}},
                           {"body": {"payload": {"id": "A"}, "tenant": "t"}}, "request")
        with self.assertRaisesRegex(VectorError, "/payload"):
            _expect_fields({"body": {"payload": {"id": "A", "unexpected": True}}},
                           {"body": {"payload": {"id": "A"}}}, "request")

    def test_json_equality_preserves_types_recursively_but_unifies_number_encodings(self) -> None:
        self.assertTrue(_json_equal({"items": [1, 2.0, {"value": 3}]},
                                    {"items": [1.0, 2, {"value": 3.0}]}))
        self.assertFalse(_json_equal({"items": [True]}, {"items": [1]}))
        self.assertFalse(_json_equal({"value": False}, {"value": 0.0}))
        self.assertFalse(_json_equal([1], {"0": 1}))

    def test_gateway_expectations_use_recursive_json_equality(self) -> None:
        _expect_fields({"body": {"payload": {"items": [1, 2.0]}}},
                       {"body": {"payload": {"items": [1.0, 2]}}}, "request")
        with self.assertRaisesRegex(VectorError, "/payload/items/0"):
            _expect_fields({"body": {"payload": {"items": [True]}}},
                           {"body": {"payload": {"items": [1]}}}, "request")

    def test_gateway_mismatch_locations_escape_json_pointer_tokens(self) -> None:
        with self.assertRaises(VectorError) as caught:
            _expect_fields({"body": {"odd~/field": True}}, {"body": {"odd~/field": 1}}, "request")
        self.assertIn("request/body/odd~0~1field:", str(caught.exception))
        with self.assertRaises(VectorError) as caught:
            _expect_fields({"body": {"unexpected~/field": True}}, {"body": {}}, "request")
        self.assertIn("request/body/unexpected~0~1field:", str(caught.exception))

    def test_all_cross_head_parity_layers_use_json_semantics(self) -> None:
        layers = (
            ("discovery", lambda actual, expected: _assert_discovery_parity(
                0, False, actual, expected, "discovery")),
            ("document", lambda actual, expected: _assert_document_parity(
                actual, expected, "document")),
            ("error", lambda actual, expected: _assert_error_parity(
                actual, expected, "error")),
            ("captured-request", lambda actual, expected: _assert_request_parity(
                actual, expected, "request")),
        )
        numerically_equal = ({"nested": [1, {"value": 2.0}]}, {"nested": [1.0, {"value": 2}]})
        type_mismatch = ({"nested": [{"value": True}]}, {"nested": [{"value": 1}]})
        for layer, compare in layers:
            with self.subTest(layer=layer, case="numbers"):
                compare(*numerically_equal)
            with self.subTest(layer=layer, case="boolean-number"), self.assertRaises(VectorError):
                compare(*type_mismatch)

    def test_semantic_assertion_vocabulary(self) -> None:
        result = {"document": {"items": [{"id": "A"}, {"id": "B"}], "title": "Hello world"}}
        for assertion in (
            {"path": "/document/items", "operator": "arrayLength", "value": 2},
            {"path": "/document/items", "operator": "contains", "value": {"id": "B"}},
            {"path": "/document/title", "operator": "contains", "value": "world"},
            {"path": "/document/missing", "operator": "exists", "value": False},
        ):
            _assert_result(result, assertion, "result")
        with self.assertRaisesRegex(VectorError, "assertion equals"):
            _assert_result(result, {"path": "/document/title", "operator": "equals", "value": "Wrong"}, "result")

    def test_equals_and_contains_assertions_use_recursive_json_equality(self) -> None:
        result = {"document": {"value": {"items": [1.0]}, "items": [{"count": 1.0}]}}
        _assert_result(result, {"path": "/document/value", "operator": "equals",
                                "value": {"items": [1]}}, "result")
        _assert_result(result, {"path": "/document/items", "operator": "contains",
                                "value": {"count": 1}}, "result")
        _assert_result(result, {"path": "/document/value", "operator": "contains",
                                "value": {"items": [1]}}, "result")
        for path, operator, value in (
            ("/document/value", "equals", {"items": [True]}),
            ("/document/items", "contains", {"count": True}),
            ("/document/value", "contains", {"items": [True]}),
        ):
            with self.subTest(operator=operator, value=value), self.assertRaises(VectorError):
                _assert_result(result, {"path": path, "operator": operator, "value": value}, "result")

    def test_host_signed_archive_matches_restore_content_hash_independently(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            host = root / "host/bin/Release/net10.0/Host.dll"
            host.parent.mkdir(parents=True)
            artifact = root / "immutable.nupkg"
            runtime = runtime_package(artifact, host)
            cached = root / "packages/sample.contracts/1.0.0/sample.contracts.1.0.0.nupkg"
            cached.parent.mkdir(parents=True)
            cached.write_bytes(artifact.read_bytes())
            raw_hash = base64.b64encode(hashlib.sha512(artifact.read_bytes()).digest()).decode()
            content_hash = base64.b64encode(hashlib.sha512(b"NuGet restore content").digest()).decode()
            (cached.parent / ".nupkg.metadata").write_text(json.dumps({"contentHash": content_hash}))
            cached.with_suffix(".nupkg.sha512").write_text(raw_hash)
            assets = root / "host/obj/project.assets.json"
            assets.parent.mkdir(parents=True)
            assets.write_text(json.dumps({
                "libraries": {"Sample.Contracts/1.0.0": {
                    "type": "package", "path": "sample.contracts/1.0.0", "sha512": content_hash}},
                "packageFolders": {str(root / "packages"): {}},
                "targets": {"net10.0": {"Sample.Contracts/1.0.0": {"runtime": runtime}}}}))
            host.with_suffix(".deps.json").write_text(json.dumps({
                "runtimeTarget": {"name": "net10.0"},
                "targets": {"net10.0": {"Sample.Contracts/1.0.0": {"runtime": runtime}}},
                "libraries": {"Sample.Contracts/1.0.0": {"type": "package", "sha512": "sha512-" + content_hash}}}))
            _verify_artifact_in_host(host, artifact, ("Sample.Contracts", "1.0.0"))
            for changed in (artifact, cached, cached.with_suffix(".nupkg.sha512"), cached.parent / ".nupkg.metadata", assets, host.with_suffix(".deps.json")):
                original = changed.read_bytes()
                with self.subTest(changed=changed.name):
                    if changed == cached.parent / ".nupkg.metadata":
                        changed.write_text(json.dumps({"contentHash": raw_hash}))
                    elif changed == assets:
                        doc = json.loads(original)
                        doc["libraries"]["Sample.Contracts/1.0.0"]["sha512"] = raw_hash
                        changed.write_text(json.dumps(doc))
                    elif changed == host.with_suffix(".deps.json"):
                        doc = json.loads(original)
                        doc["libraries"]["Sample.Contracts/1.0.0"]["sha512"] = "sha512-" + raw_hash
                        changed.write_text(json.dumps(doc))
                    else:
                        changed.write_bytes(b"changed archive or sidecar")
                    with self.assertRaises(VectorError):
                        _verify_artifact_in_host(host, artifact, ("Sample.Contracts", "1.0.0"))
                changed.write_bytes(original)
            deps = host.with_suffix('.deps.json')
            original = deps.read_bytes()
            for mutation in ['empty-runtime', 'unknown-runtime-target', 'unrestored-dll']:
                with self.subTest(runtime_selection=mutation):
                    doc = json.loads(original)
                    if mutation == 'empty-runtime':
                        doc['targets']['net10.0']['Sample.Contracts/1.0.0']['runtime'] = {}
                    elif mutation == 'unknown-runtime-target':
                        doc['runtimeTarget']['name'] = 'unrestored-target'
                    else:
                        doc['targets']['net10.0']['Sample.Contracts/1.0.0']['runtime'] = {
                            'lib/net10.0/Unrestored.Contracts.dll': {}}
                    try:
                        deps.write_text(json.dumps(doc))
                        with self.assertRaisesRegex(VectorError, 'selected package runtime DLL assets differ'):
                            _verify_artifact_in_host(host, artifact, ('Sample.Contracts', '1.0.0'))
                    finally:
                        deps.write_bytes(original)
            dll = host.parent / 'Fixture.Contracts.dll'
            dll.write_bytes(b'changed output DLL; archive, deps and assets unchanged')
            with self.assertRaisesRegex(VectorError, 'host runtime DLL bytes differ from immutable artifact entry'):
                _verify_artifact_in_host(host, artifact, ('Sample.Contracts', '1.0.0'))

    def test_host_restored_artifact_hash_must_match(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            host = root / "host/bin/Release/net10.0/Host.dll"
            host.parent.mkdir(parents=True)
            artifact = root / "sample.nupkg"
            runtime = runtime_package(artifact, host)
            identity = "Hexalith.McpCli.Sample.Contracts/1.0.0"
            digest = "sha512-" + base64.b64encode(hashlib.sha512(artifact.read_bytes()).digest()).decode()
            cached = root / "packages/hexalith.mcpcli.sample.contracts/1.0.0/hexalith.mcpcli.sample.contracts.1.0.0.nupkg"
            cached.parent.mkdir(parents=True)
            cached.write_bytes(artifact.read_bytes())
            assets = root / "host/obj/project.assets.json"
            assets.parent.mkdir(parents=True)
            assets.write_text(json.dumps({"libraries": {identity: {
                "type": "package", "path": "hexalith.mcpcli.sample.contracts/1.0.0", "sha512": digest}},
                "packageFolders": {str(root / "packages"): {}},
                "targets": {"net10.0": {identity: {"runtime": runtime}}}}))
            deps = host.with_suffix(".deps.json")
            deps.write_text(json.dumps({"runtimeTarget": {"name": "net10.0"},
                                       "targets": {"net10.0": {identity: {"runtime": runtime}}},
                                       "libraries": {identity: {"type": "package", "sha512": digest}}}), encoding="utf-8")
            _verify_artifact_in_host(host, artifact, ("Hexalith.McpCli.Sample.Contracts", "1.0.0"))
            artifact.write_bytes(b"changed artifact")
            with self.assertRaisesRegex(VectorError, "hash differs"):
                _verify_artifact_in_host(host, artifact, ("Hexalith.McpCli.Sample.Contracts", "1.0.0"))

    def test_host_requires_explicit_assets_when_project_path_cannot_be_inferred(self) -> None:
        host = Path("Host.dll")
        deps = {"libraries": {"Sample.Contracts/1.0.0": {"type": "package"}}}
        with patch.object(Path, "read_text", return_value=json.dumps(deps)):
            with self.assertRaises(VectorError) as caught:
                _verify_artifact_in_host(host, Path("immutable.nupkg"), ("Sample.Contracts", "1.0.0"))
        self.assertEqual("Host.dll: restore assets are required; supply --assets", str(caught.exception))

    def test_host_reports_unavailable_restore_assets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            host = root / "Host.dll"
            host.with_suffix(".deps.json").write_text(json.dumps({"libraries": {
                "Sample.Contracts/1.0.0": {"type": "package"}}}))
            assets = root / "missing/project.assets.json"
            with self.assertRaises(VectorError) as caught:
                _verify_artifact_in_host(host, root / "immutable.nupkg", ("Sample.Contracts", "1.0.0"), assets)
            self.assertEqual(f"{assets}: restore assets are unavailable; supply --assets", str(caught.exception))

    def test_host_requires_matching_package_library_in_restore_assets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            host = root / "Host.dll"
            identity = "Sample.Contracts/1.0.0"
            host.with_suffix(".deps.json").write_text(json.dumps({"libraries": {identity: {"type": "package"}}}))
            assets = root / "project.assets.json"
            for libraries in [{}, {identity: None}, {identity: []}, {identity: {"type": "project"}}]:
                with self.subTest(libraries=libraries):
                    assets.write_text(json.dumps({"libraries": libraries}))
                    with self.assertRaises(VectorError) as caught:
                        _verify_artifact_in_host(host, root / "immutable.nupkg", ("Sample.Contracts", "1.0.0"), assets)
                    self.assertEqual(f"{assets}: restored package does not match {identity}", str(caught.exception))

class Story411CompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.command = json.loads((HERE / 'sample-command.json').read_text())['invocation']
        self.query = json.loads((HERE / 'sample-query.json').read_text())['invocation']

    def test_equal_documents_cannot_hide_required_result_fields(self):
        from run_loopback import _assert_result_contract
        command = {'operation': self.command['operation'], 'tenant': 'sample-tenant',
                   'aggregateId': '01ARZ3NDEKTSV4RRFFQ69G5FAV', 'status': 'accepted',
                   'messageId': '01J9MZHXT3RKM0VWXRXGSJDATP',
                   'correlationId': self.command['envelope']['correlationId'],
                   'idempotencyKey': self.command['envelope']['idempotencyKey'],
                   'result': {'accepted': True}}
        query = {'operation': self.query['operation'], 'tenant': 'sample-tenant',
                 'document': {'title': 'Conformance item'}}
        for step, document in [(self.command, command), (self.query, query)]:
            _assert_result_contract(document, step, 'result')
            for field in document:
                with self.subTest(kind=step['kind'], field=field):
                    missing = dict(document)
                    missing.pop(field)
                    _assert_document_parity(missing, missing, 'equal heads')
                    with self.assertRaises(VectorError):
                        _assert_result_contract(missing, step, 'result')

    def test_supplied_ids_and_key_omission_are_independent_of_head_equality(self):
        from run_loopback import _assert_result_contract
        import copy
        step = copy.deepcopy(self.command)
        step['envelope'].pop('idempotencyKey')
        document = {'operation': step['operation'], 'tenant': 'sample-tenant',
                    'aggregateId': '01ARZ3NDEKTSV4RRFFQ69G5FAV', 'status': 'accepted',
                    'messageId': '01J9MZHXT3RKM0VWXRXGSJDATP',
                    'correlationId': step['envelope']['correlationId'], 'result': {'accepted': True}}
        _assert_result_contract(document, step, 'result')
        for field, value in [('correlationId', '01J9MZHXT3RKM0VWXRXGSJDATP'),
                             ('idempotencyKey', '01J9MZHXT3RKM0VWXRXGSJDATM')]:
            with self.subTest(field=field), self.assertRaises(VectorError):
                _assert_result_contract(dict(document, **{field: value}), step, 'result')

    def test_every_step_kind_is_checked_before_core_preflight(self):
        from run_loopback import _preflight_vectors
        from unittest.mock import Mock
        import copy
        for group in ['prerequisites', 'postconditions']:
            with tempfile.TemporaryDirectory() as directory:
                vector = json.loads((HERE / 'sample-command.json').read_text())
                bad = copy.deepcopy(vector['invocation'])
                bad['operation'] = 'sample.get-item'
                vector[group] = [bad]
                source = Path(directory) / 'case.json'
                source.write_text(json.dumps(vector))
                with patch('run_loopback.subprocess.run') as process, self.assertRaisesRegex(VectorError, group + '/0/operation'):
                    _preflight_vectors(Mock(), [source], {'sample.create-item': 'write', 'sample.get-item': 'read'})
                process.assert_not_called()

    def test_core_failure_blocks_replay_with_source_and_step_location(self):
        from run_loopback import _preflight_vectors
        from unittest.mock import Mock
        import subprocess
        source = HERE / 'sample-query.json'
        diagnostic = f'{source}:/invocation: Core compatibility failed: invalid payload'
        with patch('run_loopback.subprocess.run', return_value=subprocess.CompletedProcess([], 1,
                   json.dumps({'findings': [diagnostic], 'requests': []}), '')):
            with self.assertRaisesRegex(VectorError, '/invocation: Core compatibility failed'):
                _preflight_vectors(Mock(_base=Mock(return_value=[])), [source], {'sample.get-item': 'read'})

    def test_preflight_compares_complete_request_and_rejects_missing_steps(self):
        from run_loopback import _preflight_vectors
        from unittest.mock import Mock
        import subprocess
        import copy
        source = HERE / 'sample-query.json'
        body = self.query['expectedGateway']['body']
        for mutation in ['extra-field', 'wrong-paging', 'missing-step']:
            requests = [{'source': str(source), 'pointer': '/invocation', 'body': copy.deepcopy(body)}]
            if mutation == 'extra-field':
                requests[0]['body']['unexpected'] = True
            elif mutation == 'wrong-paging':
                requests[0]['body']['paging']['pageSize'] = 24
            else:
                requests = []
            head = Mock(_base=Mock(return_value=[]))
            with self.subTest(mutation=mutation), patch('run_loopback.subprocess.run', return_value=subprocess.CompletedProcess([], 0,
                    json.dumps({'findings': [], 'requests': requests}), '')), self.assertRaises(VectorError):
                _preflight_vectors(head, [source], {'sample.get-item': 'read'})
            head.allow_extensions.assert_not_called()

    def test_extension_allowlist_is_isolated_and_exact(self):
        from run_loopback import HeadProcess
        import os
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'EVENTSTORE_TENANT': 'outside'}):
            head = HeadProcess(Path('Host.dll'), directory, 15)
            head.allow_extensions({'trace-id', 'task-id'})
            self.assertNotIn('EVENTSTORE_TENANT', head.env)
            profile = json.loads((Path(directory) / 'mcpcli.json').read_text())
            self.assertEqual(['task-id', 'trace-id'], profile['profiles']['conformance']['allowedExtensions'])
            self.assertEqual(str(Path(directory) / 'mcpcli.json'), head.env['MCPCLI_CONFORMANCE_PROFILE_PATH'])

class ProductionReplayOrderingTests(unittest.TestCase):
    def test_unselected_exposed_operation_fails_before_core_preflight_or_gateway(self):
        import subprocess
        from unittest.mock import Mock
        from run_loopback import run_catalog
        modules = {'modules': [{'name': 'sample'}]}
        listed = {'operations': [{'name': 'sample.get-item', 'kind': 'read'},
                                 {'name': 'sample.unselected', 'kind': 'read'}]}
        head = Mock(_base=Mock(return_value=[]), env={}, timeout=15)
        head.cli.side_effect = [(0, modules), (0, listed)]
        head.mcp.side_effect = [(False, modules), (False, listed)]
        with patch('run_loopback._verify_artifact_in_host'), patch('run_loopback.validate_vectors', return_value=[]), \
                patch('run_loopback._manifest_operations', return_value={'sample.get-item': 'query'}), \
                patch('run_loopback.HeadProcess', return_value=head), \
                patch('run_loopback._preflight_vectors', side_effect=AssertionError('Core preflight must not run')) as preflight, \
                patch('run_loopback.ReplayGateway') as gateway, \
                patch('run_loopback.subprocess.run', return_value=subprocess.CompletedProcess([], 2, '{"error":{"code":"invalid_arguments"}}', '')):
            with self.assertRaisesRegex(VectorError, r"complete production Catalog contains uncovered operations: \['sample.unselected'\]"):
                run_catalog(Path('Host.dll'), [(Path('sample.nupkg'), ('Sample.Contracts', '1.0.0'), [HERE / 'sample-query.json'])])
        self.assertEqual([(['modules', '--strict'],), (['operations', 'sample', '--strict'],)],
                         [call.args for call in head.cli.call_args_list])
        preflight.assert_not_called()
        gateway.assert_not_called()

    def test_mcp_process_starts_with_strict_catalog_validation(self):
        from unittest.mock import Mock
        from run_loopback import HeadProcess
        document = {'modules': []}
        client = Mock()
        client.request.return_value = {'result': {'structuredContent': document,
                                                 'content': [{'text': json.dumps(document)}]}}
        with tempfile.TemporaryDirectory() as directory, \
                patch('run_loopback.subprocess.Popen') as process, \
                patch('run_loopback._JsonRpcClient', return_value=client):
            head = HeadProcess(Path('Host.dll'), directory, 15)
            self.assertEqual((False, document), head.mcp('list_modules', {}))
        self.assertEqual(['dotnet', 'Host.dll', 'mcp', '--transport', 'stdio', '--strict'],
                         process.call_args.args[0])

    def test_identical_malformed_payload_errors_cannot_change_the_required_message(self):
        import subprocess
        from unittest.mock import Mock, MagicMock
        from run_loopback import run_catalog
        source = HERE / 'sample-query.json'
        step = json.loads(source.read_text())['invocation']
        modules = {'modules': [{'name': 'sample'}]}
        listed = {'operations': [{'name': step['operation'], 'kind': 'read'}]}
        success = {'operation': step['operation'], 'tenant': 'sample-tenant',
                   'document': {'title': 'Conformance item'}}
        malformed = {'error': {'code': 'validation_failed', 'operation': step['operation'],
                               'violations': [{'path': '/', 'message': 'Changed validation message'}]}}
        head = Mock(_base=Mock(return_value=[]), env={}, timeout=15)
        head.cli.side_effect = [(0, modules), (0, listed), (0, {'name': step['operation']}), (2, malformed)]
        head.mcp.side_effect = [(False, modules), (False, listed), (False, {'name': step['operation']}), (True, malformed)]
        gateway = MagicMock()
        gateway.__enter__.return_value = gateway
        gateway.assert_consumed = Mock()
        gateway.captured = [{key: copy.deepcopy(step['expectedGateway'][key])
                             for key in ['method', 'path', 'body']}]

        def run_step(*args, evidence, **kwargs):
            evidence.append(copy.deepcopy(success))
            return success, False

        with patch('run_loopback._verify_artifact_in_host'), patch('run_loopback.validate_vectors', return_value=[]), \
                patch('run_loopback._manifest_operations', return_value={step['operation']: 'query'}), \
                patch('run_loopback._preflight_vectors'), patch('run_loopback.HeadProcess', return_value=head), \
                patch('run_loopback._run_step', side_effect=run_step), \
                patch('run_loopback.ReplayGateway', return_value=gateway), \
                patch('run_loopback.subprocess.run', return_value=subprocess.CompletedProcess([], 2, '{"error":{"code":"invalid_arguments"}}', '')):
            with self.assertRaisesRegex(VectorError, 'required malformed-Payload error document differs'):
                run_catalog(Path('Host.dll'), [(Path('sample.nupkg'), ('Sample.Contracts', '1.0.0'), [source])])
        self.assertEqual(['describe', step['operation'], '--strict'], head.cli.call_args_list[2].args[0])

    def test_incompatible_last_vector_stops_every_gateway_before_replay(self):
        import subprocess
        from unittest.mock import Mock
        from run_loopback import run_catalog
        first = HERE / 'sample-command.json'
        last = HERE / 'sample-query.json'
        operations = {'sample.create-item': 'command', 'sample.get-item': 'query'}
        modules = {'modules': [{'name': 'sample'}]}
        listed = {'operations': [{'name': name, 'kind': 'write' if kind == 'command' else 'read'}
                                  for name, kind in operations.items()]}
        head = Mock(_base=Mock(return_value=[]), env={}, timeout=15)
        head.cli.side_effect = [(0, modules), (0, listed)]
        head.mcp.side_effect = [(False, modules), (False, listed)]
        malformed = subprocess.CompletedProcess([], 2, '{"error":{"code":"invalid_arguments"}}', '')
        incompatible = subprocess.CompletedProcess([], 1, json.dumps({
            'findings': [f'{last}:/postconditions/0: Core compatibility failed: schema mismatch'], 'requests': []}), '')
        with patch('run_loopback._verify_artifact_in_host'), patch('run_loopback.validate_vectors', return_value=[]), \
             patch('run_loopback._manifest_operations', return_value=operations), \
             patch('run_loopback.HeadProcess', return_value=head), \
             patch('run_loopback.subprocess.run', side_effect=[malformed, incompatible]), \
             patch('run_loopback.ReplayGateway') as gateway:
            with self.assertRaisesRegex(VectorError, 'sample-query.json:/postconditions/0: Core compatibility failed'):
                run_catalog(Path('Host.dll'), [(Path('module.nupkg'), ('Sample.Contracts', '1.0.0'), [first, last])])
        gateway.assert_not_called()

    def test_fixed_response_message_id_stays_unmasked_and_binds_to_result(self):
        from run_loopback import _assert_result_request_binding
        step = json.loads((HERE / 'sample-command.json').read_text())['invocation']
        supplied = '01J9MZHXT3RKM0VWXRXGSJDATK'
        step['scriptedResponse']['body']['messageId'] = supplied
        step['scriptedResponse']['echoRequestFields'].remove('messageId')
        document = {'messageId': supplied, 'correlationId': supplied}
        request = {'messageId': '01J9MZHXT3RKM0VWXRXGSJDATP', 'correlationId': supplied}
        self.assertEqual(supplied, _mask_result(document, step, 'result')['messageId'])
        _assert_result_request_binding(document, request, step, 'result')
        with self.assertRaisesRegex(VectorError, 'submitted/returned identifier'):
            _assert_result_request_binding(dict(document, correlationId=request['messageId']), request, step, 'result')

    def test_generated_correlation_is_bound_to_its_message_before_masking(self):
        step = json.loads((HERE / 'sample-rename.json').read_text())['invocation']
        with self.assertRaisesRegex(VectorError, 'default correlation must equal'):
            _mask({'messageId': '01J9MZHXT3RKM0VWXRXGSJDATP',
                   'correlationId': '01J9MZHXT3RKM0VWXRXGSJDATK'}, step, 'request')

class RequiredResultExecutionTests(unittest.TestCase):
    def test_both_heads_missing_the_same_required_field_fail_before_semantic_assertions(self):
        from run_loopback import _run_step
        from unittest.mock import Mock
        step = json.loads((HERE / 'sample-query.json').read_text())['invocation']
        step['assertions'] = [{'path': '/document/title', 'operator': 'equals', 'value': 'Conformance item'}]
        document = {'tenant': 'sample-tenant', 'document': {'title': 'Conformance item'}}
        head = Mock()
        head.cli.return_value = (0, document)
        head.mcp.return_value = (False, document)
        for label in ['CLI', 'MCP']:
            with self.subTest(head=label), self.assertRaisesRegex(VectorError, '/operation: required result'):
                _run_step(head, step, 'http://127.0.0.1/', label)

class RequiredErrorExecutionTests(unittest.TestCase):
    def test_scripted_gateway_errors_require_status_code_and_preserved_detail_on_both_heads(self):
        from run_loopback import _run_step
        from unittest.mock import Mock
        step = json.loads((HERE / 'sample-query.json').read_text())['invocation']
        step['scriptedResponse'] = {'statusCode': 503, 'body': {'detail': 'scripted failure'}, 'echoRequestFields': []}
        full = {'code': 'gateway_error', 'status': 503, 'detail': 'scripted failure'}
        for field in full:
            missing = dict(full)
            missing.pop(field)
            head = Mock()
            head.cli.return_value = (2, {'error': missing})
            head.mcp.return_value = (True, {'error': missing})
            for label in ['CLI', 'MCP']:
                with self.subTest(field=field, head=label), self.assertRaises(VectorError):
                    _run_step(head, step, 'http://127.0.0.1/', label, verify_assertions=False)

class OptionalResultContractTests(unittest.TestCase):
    def test_null_optional_paging_fields_are_omitted_and_extra_results_are_rejected(self):
        from run_loopback import _assert_result_contract
        step = json.loads((HERE / 'sample-query.json').read_text())['invocation']
        step['scriptedResponse']['body']['metadata'] = {'paging': {'pageSize': 25, 'offset': None, 'hasMore': False}}
        document = {'operation': step['operation'], 'tenant': 'sample-tenant',
                    'document': {'title': 'Conformance item'}, 'paging': {'pageSize': 25, 'hasMore': False}}
        _assert_result_contract(document, step, 'result')
        with self.assertRaisesRegex(VectorError, 'unexpected result field'):
            _assert_result_contract(dict(document, unexpected=True), step, 'result')


class SdkErrorOutcomeTests(unittest.TestCase):
    def test_supported_sdk_errors_are_exact_and_cannot_lose_or_invent_metadata(self):
        from run_loopback import _run_step
        from unittest.mock import Mock
        import copy
        correlation = '01J9MZHXT3RKM0VWXRXGSJDATK'
        cases = [
            (409, {}, {'code': 'gateway_error', 'status': 409, 'detail': 'Conflict'}),
            (409, {'title': ' ', 'detail': ' '}, {'code': 'gateway_error', 'status': 409, 'detail': 'Gateway request failed.'}),
            (304, {}, {'code': 'gateway_error', 'status': 502,
                       'detail': 'Not-modified query response requires projection-backed provenance and a strong ETag.'}),
            (409, {'status': 422, 'title': 'Conflict', 'detail': 'safe conflict', 'reasonCode': 'duplicate',
                   'retryable': False, 'clientAction': 'inspect', 'retryAfter': '25', 'correlationId': correlation},
                  {'code': 'gateway_error', 'status': 422, 'detail': 'safe conflict', 'reason': 'duplicate',
                   'retryable': False, 'clientAction': 'inspect', 'retryAfter': '25', 'correlationId': correlation}),
            (200, {'success': False, 'errorMessage': 'Access denied.', 'correlationId': correlation},
                  {'code': 'gateway_error', 'status': 200, 'detail': 'Access denied.', 'correlationId': correlation}),
            (204, {}, {'code': 'gateway_error', 'status': 204, 'detail': 'Query response body could not be parsed.'}),
        ]
        for status, body, expected in cases:
            step = json.loads((HERE / 'sample-query.json').read_text())['invocation']
            step['scriptedResponse'] = {'statusCode': status, 'body': body, 'echoRequestFields': []}
            step['assertions'] = [{'path': '/error', 'operator': 'equals', 'value': expected}]
            for label in ['CLI', 'MCP']:
                def execute(error):
                    head = Mock()
                    head.cli.return_value = (2, {'error': error})
                    head.mcp.return_value = (True, {'error': error})
                    return _run_step(head, step, 'http://127.0.0.1/', label, verify_assertions=False)[0]
                with self.subTest(status=status, head=label):
                    self.assertEqual({'error': expected}, execute(expected))
                for field in expected:
                    broken = copy.deepcopy(expected)
                    broken.pop(field)
                    with self.subTest(status=status, head=label, missing=field), self.assertRaises(VectorError):
                        execute(broken)
                for field, value in [('reason', 'invented'), ('correlationId', correlation),
                                     ('retryable', False), ('clientAction', 'invented'), ('retryAfter', '25')]:
                    if field not in expected:
                        with self.subTest(status=status, head=label, extra=field), self.assertRaises(VectorError):
                            execute(dict(expected, **{field: value}))

    def test_problem_metadata_precedence_and_blank_or_invalid_values_are_omitted(self):
        from run_loopback import _assert_result_contract
        step = json.loads((HERE / 'sample-query.json').read_text())['invocation']
        step['scriptedResponse'] = {'statusCode': 409, 'echoRequestFields': [], 'body': {
            'detail': 'safe conflict', 'reasonCode': ' ', 'code': 'preferred-code', 'reason': 'fallback',
            'clientAction': ' ', 'retryAfter': '', 'retryable': None, 'correlationId': 'invalid'}}
        expected = {'error': {'code': 'gateway_error', 'status': 409, 'detail': 'safe conflict', 'reason': 'preferred-code'}}
        _assert_result_contract(expected, step, 'result')
        for field, value in [('reason', 'fallback'), ('clientAction', ' '), ('retryAfter', ''),
                             ('retryable', None), ('correlationId', 'invalid')]:
            broken = {'error': dict(expected['error'], **{field: value})}
            with self.subTest(field=field), self.assertRaises(VectorError):
                _assert_result_contract(broken, step, 'result')


class RetainedFailureEvidenceTests(unittest.TestCase):
    def test_failing_head_retains_full_document_and_captured_request(self):
        import copy
        import subprocess
        from unittest.mock import Mock, MagicMock
        from run_loopback import run_catalog
        source = HERE / 'sample-query.json'
        step = json.loads(source.read_text())['invocation']
        request = {'method': 'POST', 'path': '/api/v1/queries', 'body': copy.deepcopy(step['expectedGateway']['body'])}
        healthy = {'operation': step['operation'], 'tenant': 'sample-tenant', 'document': {'title': 'Conformance item'}}
        broken = {'operation': step['operation'], 'tenant': 'sample-tenant', 'document': {'title': 'broken', 'all': [False, None, 3]}}
        modules = {'modules': [{'name': 'sample'}]}
        listed = {'operations': [{'name': step['operation'], 'kind': 'read'}]}
        described = {'name': step['operation']}
        for failing, inconsistent in [('CLI', False), ('MCP', False), ('CLI', True), ('MCP', True)]:
            head = Mock(_base=Mock(return_value=[]), env={}, timeout=15)
            head.cli.side_effect = [(0, modules), (0, listed), (0, described), (2 if failing == 'CLI' and inconsistent else 0, broken if failing == 'CLI' else healthy)]
            head.mcp.side_effect = [(False, modules), (False, listed), (False, described), (inconsistent, broken)]
            gateway = MagicMock()
            gateway.__enter__.return_value = gateway
            gateway.captured = [request]
            gateway.assert_consumed = Mock()
            with tempfile.TemporaryDirectory() as directory, \
                    patch('run_loopback._verify_artifact_in_host'), patch('run_loopback.validate_vectors', return_value=[]), \
                    patch('run_loopback._manifest_operations', return_value={step['operation']: 'query'}), \
                    patch('run_loopback._preflight_vectors'), patch('run_loopback.HeadProcess', return_value=head), \
                    patch('run_loopback.ReplayGateway', return_value=gateway), \
                    patch('run_loopback.subprocess.run', return_value=subprocess.CompletedProcess([], 2, '{"error":{"code":"invalid_arguments"}}', '')):
                output = Path(directory)
                with self.subTest(head=failing, inconsistent=inconsistent), self.assertRaisesRegex(VectorError, 'inconsistent' if inconsistent else '/document: required result'):
                    run_catalog(Path('Host.dll'), [(Path('module.nupkg'), ('Sample.Contracts', '1.0.0'), [source])], evidence_dir=output)
                retained = json.loads((output / f"{step['operation']}.{failing}.json").read_text())
                self.assertEqual({'source': str(source), 'documents': [broken], 'requests': [request]}, retained)

    def test_reused_generated_request_ids_fail_before_masking_can_hide_them(self):
        from run_loopback import _assert_fresh_message
        step = json.loads((HERE / 'sample-command.json').read_text())['invocation']
        request = {'body': {'messageId': '01J9MZHXT3RKM0VWXRXGSJDATP'}}
        seen = set()
        _assert_fresh_message(request, step, seen, 'CLI first')
        with self.assertRaisesRegex(VectorError, 'reused across distinct calls'):
            _assert_fresh_message(request, step, seen, 'MCP second')


class GeneratedMessageReuseExecutionTests(unittest.TestCase):
    def test_matching_heads_cannot_return_an_identifier_different_from_the_captured_request(self):
        import subprocess
        from unittest.mock import Mock
        from run_loopback import run_catalog
        vector = json.loads((HERE / 'sample-command.json').read_text())
        vector['prerequisites'], vector['postconditions'] = [], []
        step = vector['invocation']
        state = {'gateway': None, 'counter': 0}
        observed = []

        class Gateway:
            url = 'http://unused.invalid/'
            def __init__(self, steps):
                self.steps, self.captured = steps, []
            def __enter__(self):
                state['gateway'] = self
                return self
            def __exit__(self, *_):
                pass
            def assert_consumed(self, location):
                if len(self.captured) != len(self.steps):
                    raise AssertionError(location)

        modules = {'modules': [{'name': 'sample'}]}
        listed = {'operations': [{'name': step['operation'], 'kind': 'write'}]}
        def execute(payload):
            if payload == '{invalid':
                return 2, {'error': {'code': 'validation_failed', 'operation': step['operation'],
                    'violations': [{'path': '/', 'message': 'The payload must be valid JSON without duplicate properties.'}]}}
            gateway = state['gateway']
            script = gateway.steps[len(gateway.captured)]
            state['counter'] += 1
            body = dict(step['expectedGateway']['body'], messageId=f"{state['counter']:026d}")
            gateway.captured.append({'method': 'POST', 'path': '/api/v1/commands', 'body': body})
            if script['scriptedResponse']['statusCode'] == 503:
                return 2, {'error': {'code': 'gateway_error', 'status': 503, 'detail': 'scripted Gateway failure'}}
            document = {'operation': step['operation'], 'tenant': step['envelope']['tenant'],
                'aggregateId': body['aggregateId'], 'status': 'accepted',
                'messageId': '01J9MZHXT3RKM0VWXRXGSJDATP', 'correlationId': body['correlationId'],
                'idempotencyKey': body['idempotencyKey'], 'result': {'accepted': True}}
            observed.append(document)
            return 0, document
        def cli(args, *unused):
            if args[0] == 'modules': return 0, modules
            if args[0] == 'operations': return 0, listed
            if args[0] == 'describe': return 0, {'name': step['operation']}
            return execute(args[args.index('--payload') + 1])
        def mcp(tool, args, *unused):
            if tool == 'list_modules': return False, modules
            if tool == 'list_operations': return False, listed
            if tool == 'describe_operation': return False, {'name': step['operation']}
            code, document = execute(args['payload'])
            return code == 2, document
        head = Mock(_base=Mock(return_value=[]), env={}, timeout=15)
        head.cli.side_effect, head.mcp.side_effect = cli, mcp
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'wrong-identifier.vector.json'
            source.write_text(json.dumps(vector))
            with patch('run_loopback._verify_artifact_in_host'), patch('run_loopback.validate_vectors', return_value=[]), \
                    patch('run_loopback._manifest_operations', return_value={step['operation']: 'command'}), \
                    patch('run_loopback._preflight_vectors'), patch('run_loopback.HeadProcess', return_value=head), \
                    patch('run_loopback.ReplayGateway', Gateway), \
                    patch('run_loopback.subprocess.run', return_value=subprocess.CompletedProcess([], 2, '{"error":{"code":"invalid_arguments"}}', '')):
                with self.assertRaisesRegex(VectorError, 'result does not preserve the submitted/returned identifier'):
                    run_catalog(Path('Host.dll'), [(Path('sample.nupkg'), ('Sample.Contracts', '1.0.0'), [source])])
        self.assertEqual(2, len(observed))
        self.assertEqual(observed[0], observed[1])

    def test_two_real_runner_calls_cannot_reuse_a_generated_request_message(self):
        import copy
        import subprocess
        from unittest.mock import Mock, MagicMock
        from run_loopback import run_catalog
        vector = json.loads((HERE / 'sample-rename.json').read_text())
        step = vector['invocation']
        vector['prerequisites'] = [copy.deepcopy(step)]
        message = '01J9MZHXT3RKM0VWXRXGSJDATP'
        body = copy.deepcopy(step['expectedGateway']['body'])
        body.update(messageId=message, correlationId=message)
        request = {'method': 'POST', 'path': '/api/v1/commands', 'body': body}
        document = {'operation': step['operation'], 'tenant': step['envelope']['tenant'],
                    'aggregateId': body['aggregateId'], 'status': 'accepted',
                    'messageId': message, 'correlationId': message}
        if step['scriptedResponse']['body'].get('resultPayload') is not None:
            document['result'] = step['scriptedResponse']['body']['resultPayload']
        gateway = MagicMock()
        gateway.__enter__.return_value = gateway
        gateway.captured = []
        modules = {'modules': [{'name': 'sample'}]}
        listed = {'operations': [{'name': step['operation'], 'kind': 'write'}]}
        head = Mock(_base=Mock(return_value=[]), env={}, timeout=15)
        def cli(args, *unused):
            if args[0] == 'modules':
                return 0, modules
            if args[0] == 'operations':
                return 0, listed
            if args[0] == 'describe':
                return 0, {'name': step['operation']}
            gateway.captured.append(copy.deepcopy(request))
            return 0, copy.deepcopy(document)
        head.cli.side_effect = cli
        head.mcp.side_effect = [(False, modules), (False, listed), (False, {'name': step['operation']})]
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'rename.vector.json'
            source.write_text(json.dumps(vector))
            with patch('run_loopback._verify_artifact_in_host'), patch('run_loopback.validate_vectors', return_value=[]), \
                    patch('run_loopback._manifest_operations', return_value={step['operation']: 'command'}), \
                    patch('run_loopback._preflight_vectors'), patch('run_loopback.HeadProcess', return_value=head), \
                    patch('run_loopback.ReplayGateway', return_value=gateway), \
                    patch('run_loopback.subprocess.run', return_value=subprocess.CompletedProcess([], 2, '{"error":{"code":"invalid_arguments"}}', '')):
                with self.assertRaisesRegex(VectorError, 'reused across distinct calls'):
                    run_catalog(Path('Host.dll'), [(Path('module.nupkg'), ('Sample.Contracts', '1.0.0'), [source])])
            self.assertEqual([request, request], gateway.captured)


class ReceiptModuleBindingTests(unittest.TestCase):
    def test_a_receipt_label_cannot_replace_the_package_discovered_module(self):
        import subprocess
        from unittest.mock import Mock
        from run_loopback import run_catalog
        modules = {'modules': [{'name': 'sample'}]}
        operations = {'operations': [{'name': 'sample.get-item', 'kind': 'read'}]}
        head = Mock(_base=Mock(return_value=[]), env={}, timeout=15)
        head.cli.side_effect = [(0, modules), (0, operations)]
        head.mcp.side_effect = [(False, modules), (False, operations)]
        with patch('run_loopback._verify_artifact_in_host'), patch('run_loopback.validate_vectors', return_value=[]), \
                patch('run_loopback._manifest_operations', return_value={'sample.get-item': 'query'}), \
                patch('run_loopback.HeadProcess', return_value=head), \
                patch('run_loopback._preflight_vectors') as preflight, patch('run_loopback.ReplayGateway') as gateway, \
                patch('run_loopback.subprocess.run', return_value=subprocess.CompletedProcess([], 2, '{"error":{"code":"invalid_arguments"}}', '')):
            with self.assertRaisesRegex(VectorError, "receipt module 'tenants' differs from discovered module"):
                run_catalog(Path('Host.dll'), [(Path('module.nupkg'), ('Sample.Contracts', '1.0.0'), [HERE / 'sample-query.json'])],
                            expected_modules={'Sample.Contracts': 'tenants'})
        preflight.assert_not_called()
        gateway.assert_not_called()


class GeneratedErrorCorrelationTests(unittest.TestCase):
    def test_valid_command_204_completes_runner_without_inventing_error_correlation(self):
        import subprocess
        from unittest.mock import Mock
        from run_loopback import run_catalog
        for supplied, reuse_503 in [(False, False), (True, False), (False, True), (True, True)]:
            vector = json.loads((HERE / 'sample-rename.json').read_text())
            vector['prerequisites'], vector['postconditions'] = [], []
            step = vector['invocation']
            if supplied:
                step['envelope']['correlationId'] = '01J9MZHXT3RKM0VWXRXGSJDATK'
                step['expectedGateway']['body']['correlationId'] = step['envelope']['correlationId']
                step['expectedGateway']['maskGenerated'].remove('/correlationId')
            step['scriptedResponse']['statusCode'] = 204
            step['assertions'] = [{'path': '/error/detail', 'operator': 'equals',
                                   'value': 'Command response body could not be parsed.'}]
            modules = {'modules': [{'name': 'sample'}]}
            listed = {'operations': [{'name': step['operation'], 'kind': 'write'}]}
            state = {'gateway': None, 'counter': 0, 'normal_message': None}

            class Gateway:
                url = 'http://unused.invalid/'
                def __init__(self, steps):
                    self.steps, self.captured = steps, []
                def __enter__(self):
                    state['gateway'] = self
                    return self
                def __exit__(self, *_):
                    pass
                def assert_consumed(self, location):
                    if len(self.captured) != len(self.steps):
                        raise AssertionError(location)

            def execute(payload):
                if payload == '{invalid':
                    return 2, {'error': {'code': 'validation_failed', 'operation': step['operation'],
                                        'violations': [{'path': '/', 'message': 'The payload must be valid JSON without duplicate properties.'}]}}
                gateway = state['gateway']
                script = gateway.steps[len(gateway.captured)]
                state['counter'] += 1
                message = f"{state['counter']:026d}"
                status = script['scriptedResponse']['statusCode']
                if status == 503 and reuse_503:
                    message = state['normal_message']
                elif state['normal_message'] is None:
                    state['normal_message'] = message
                body = copy.deepcopy(step['expectedGateway']['body'])
                body.update(messageId=message, correlationId=step['envelope'].get('correlationId', message))
                gateway.captured.append({'method': 'POST', 'path': '/api/v1/commands', 'body': body})
                return 2, {'error': {'code': 'gateway_error', 'status': status, 'detail':
                                    'Command response body could not be parsed.' if status == 204 else 'scripted Gateway failure'}}

            def cli(args, *unused):
                if args[0] == 'modules': return 0, modules
                if args[0] == 'operations': return 0, listed
                if args[0] == 'describe': return 0, {'name': step['operation']}
                return execute(args[args.index('--payload') + 1])

            def mcp(tool, args, *unused):
                if tool == 'list_modules': return False, modules
                if tool == 'list_operations': return False, listed
                if tool == 'describe_operation': return False, {'name': step['operation']}
                code, document = execute(args['payload'])
                return code == 2, document

            head = Mock(_base=Mock(return_value=[]), env={}, timeout=15)
            head.cli.side_effect, head.mcp.side_effect = cli, mcp
            with tempfile.TemporaryDirectory() as directory:
                source = Path(directory) / 'command-204.vector.json'
                source.write_text(json.dumps(vector))
                with self.subTest(supplied=supplied, reuse_503=reuse_503), patch('run_loopback._verify_artifact_in_host'), \
                        patch('run_loopback.validate_vectors', return_value=[]), \
                        patch('run_loopback._manifest_operations', return_value={step['operation']: 'command'}), \
                        patch('run_loopback.HeadProcess', return_value=head), \
                        patch('run_loopback._preflight_vectors'), patch('run_loopback.ReplayGateway', Gateway), \
                        patch('run_loopback.subprocess.run', return_value=subprocess.CompletedProcess([], 2, '{"error":{"code":"invalid_arguments"}}', '')):
                    if reuse_503:
                        with self.assertRaisesRegex(VectorError, 'gateway-error/messageId:.*reused across distinct calls'):
                            run_catalog(Path('Host.dll'), [(Path('sample.nupkg'), ('Sample.Contracts', '1.0.0'), [source])])
                    else:
                        self.assertEqual(['sample'], run_catalog(Path('Host.dll'), [
                            (Path('sample.nupkg'), ('Sample.Contracts', '1.0.0'), [source])])['modules'])

    def test_error_masks_only_a_generated_echo_and_preserves_a_supplied_correlation(self):
        from run_loopback import _assert_result_contract, _assert_result_request_binding
        step = json.loads((HERE / 'sample-rename.json').read_text())['invocation']
        message = '01J9MZHXT3RKM0VWXRXGSJDATP'
        step['scriptedResponse'] = {'statusCode': 409, 'body': {'detail': 'conflict'}, 'echoRequestFields': ['correlationId']}
        document = {'error': {'code': 'gateway_error', 'status': 409, 'detail': 'conflict', 'correlationId': message}}
        _assert_result_contract(document, step, 'result')
        _assert_result_request_binding(document, {'correlationId': message}, step, 'result')
        self.assertEqual('<generated>', _mask_result(document, step, 'result')['error']['correlationId'])
        step['envelope']['correlationId'] = message
        self.assertEqual(message, _mask_result(document, step, 'result')['error']['correlationId'])
        step['envelope'].pop('correlationId')
        step['scriptedResponse']['echoRequestFields'] = []
        step['scriptedResponse']['body']['correlationId'] = message
        self.assertEqual(message, _mask_result(document, step, 'result')['error']['correlationId'])

    def test_expected_error_correlation_still_cannot_be_missing_or_wrong(self):
        from run_loopback import _assert_result_contract, _assert_result_request_binding
        step = json.loads((HERE / 'sample-rename.json').read_text())['invocation']
        step['scriptedResponse'] = {'statusCode': 409, 'body': {'detail': 'conflict'}, 'echoRequestFields': ['correlationId']}
        expected = '01J9MZHXT3RKM0VWXRXGSJDATP'
        with self.assertRaisesRegex(VectorError, 'required echoed Gateway correlationId'):
            _assert_result_contract({'error': {'code': 'gateway_error', 'status': 409, 'detail': 'conflict'}}, step, 'result')
        wrong = {'error': {'code': 'gateway_error', 'status': 409, 'detail': 'conflict',
                           'correlationId': '01J9MZHXT3RKM0VWXRXGSJDATK'}}
        with self.assertRaisesRegex(VectorError, 'does not preserve the submitted identifier'):
            _assert_result_request_binding(wrong, {'correlationId': expected}, step, 'result')


class SdkTypedResponseTests(unittest.TestCase):
    def test_quoted_integer_signs_and_leading_zeroes_follow_the_sdk(self):
        from run_loopback import _sdk_response
        step = json.loads((HERE / 'sample-query.json').read_text())['invocation']
        for value, expected in [('+7', 7), ('007', 7), ('-0', 0), ('+0007', 7), ('-7', -7),
                                ('0' * 5000 + '7', 7), ('+' + '0' * 5000 + '7', 7),
                                ('-' + '0' * 5000 + '7', -7), ('-' + '0' * 5000, 0)]:
            step['scriptedResponse']['body']['metadata'] = {'paging': {'pageSize': value, 'offset': value, 'totalCount': value}}
            with self.subTest(value=value):
                self.assertEqual({'pageSize': expected, 'offset': expected, 'totalCount': expected}, _sdk_response(step)['paging'])
        for field, bits in [('pageSize', 32), ('offset', 32), ('totalCount', 64)]:
            for boundary in [-(2 ** (bits - 1)) - 1, -(2 ** (bits - 1)), 2 ** (bits - 1) - 1, 2 ** (bits - 1)]:
                value = ('-' if boundary < 0 else '+') + '0' * 5000 + str(abs(boundary))
                step['scriptedResponse']['body']['metadata'] = {'paging': {field: value}}
                with self.subTest(field=field, boundary=boundary):
                    response = _sdk_response(step)
                    if -(2 ** (bits - 1)) <= boundary < 2 ** (bits - 1):
                        self.assertEqual(boundary, response['paging'][field])
                    else:
                        self.assertIsNone(response)
        for value in [' 7', '7 ', '7.0', '7e0', '+', '--7']:
            step['scriptedResponse']['body']['metadata'] = {'paging': {'pageSize': value}}
            with self.subTest(value=value):
                self.assertIsNone(_sdk_response(step))

    def test_served_at_uses_the_sdk_calendar_timestamp_grammar(self):
        from run_loopback import _sdk_response
        step = json.loads((HERE / 'sample-query.json').read_text())['invocation']
        valid = ['2026-10-22', '2026-10-22T12:34', '2026-10-22T12:34Z',
                 '2026-10-22T12:34:56Z', '2026-10-22T12:34:56.1234567890123456+02:00',
                 '2026-10-22T12:34:56.Z', '2026-10-22T12:34:56.+02:00',
                 '2026-10-22T12:34:56', '2026-10-22T12:34:56+14:00']
        invalid = ['2026-W43-4T12:34:56Z', '2026-10-22 12:34:56Z', '2026-10-22T12:34:56,5Z',
                   '2026-10-22t12:34:56z', '2026-10-22T12:34:56.12345678901234567Z',
                   '2026-10-22T12:34:56+14:01', '2026-10-22T12:34:56+00:60', '2026-02-30T12:34:56Z']
        for value in valid + invalid:
            step['scriptedResponse']['body']['metadata'] = {'servedAt': value}
            with self.subTest(value=value):
                self.assertEqual(value in valid, _sdk_response(step) is not None)

    def test_case_variants_validate_each_typed_value_in_input_order(self):
        from run_loopback import _sdk_response
        step = json.loads((HERE / 'sample-query.json').read_text())['invocation']
        base = {'correlationId': '01J9MZHXT3RKM0VWXRXGSJDATK', 'payload': None}
        invalid = [dict(base, success='true', Success=True),
                   dict(base, correlationId=False, CorrelationId=base['correlationId']),
                   dict(base, metadata={'servedAt': 'not a date', 'ServedAt': '2026-10-22T12:34:56Z'}),
                   dict(base, metadata={'paging': {'pageSize': 'bad', 'PageSize': 7}})]
        for body in invalid:
            step['scriptedResponse']['body'] = body
            with self.subTest(body=body):
                self.assertIsNone(_sdk_response(step))
        step['scriptedResponse']['body'] = dict(base, success=False, Success=True)
        self.assertTrue(_sdk_response(step)['success'])
        step['scriptedResponse']['body'] = dict(base, **{'ſuccess': False})
        self.assertTrue(_sdk_response(step)['success'])

    def test_missing_payload_and_invalid_problem_status_preserve_actual_internal_errors(self):
        from run_loopback import _assert_result_contract
        step = json.loads((HERE / 'sample-query.json').read_text())['invocation']
        step['scriptedResponse']['body'] = {'correlationId': '01J9MZHXT3RKM0VWXRXGSJDATK'}
        for head, message in [('CLI', 'The CLI action failed.'), ('MCP', 'MCP tool invocation failed.')]:
            with self.subTest(head=head):
                _assert_result_contract({'error': {'code': 'internal_error', 'message': message}}, step, 'result', head=head)
                with self.assertRaises(VectorError):
                    _assert_result_contract({'operation': step['operation'], 'tenant': 'sample-tenant', 'document': None}, step, 'result', head=head)
        step['scriptedResponse']['body']['payload'] = None
        _assert_result_contract({'operation': step['operation'], 'tenant': 'sample-tenant', 'document': None}, step, 'result')
        for status in ['422', None, True]:
            step['scriptedResponse'] = {'statusCode': 503, 'body': {'status': status, 'detail': 'bad status'}, 'echoRequestFields': []}
            with self.subTest(status=status):
                _assert_result_contract({'error': {'code': 'internal_error', 'message': 'Operation execution failed.'}}, step, 'result')
                with self.assertRaises(VectorError):
                    _assert_result_contract({'error': {'code': 'gateway_error', 'status': 503, 'detail': 'bad status'}}, step, 'result')

    def test_query_defaults_case_insensitive_properties_and_typed_paging_preserve_payload(self):
        from run_loopback import _assert_result_contract
        opaque = {'MixedCase': [True, 1], 'payload': {'SUCCESS': 'true'}}
        correlation = '01J9MZHXT3RKM0VWXRXGSJDATK'
        cases = [
            ({'correlationId': correlation, 'payload': opaque}, None),
            ({'CORRELATIONID': correlation, 'PAYLOAD': opaque, 'SUCCESS': True,
              'METADATA': {'PAGING': {'OFFSET': None, 'unknown': True}}}, {'pageSize': 0}),
            ({'correlationId': correlation, 'payload': opaque, 'metadata': {'paging': {
                'pageSize': '7', 'offset': '2', 'totalCount': '3', 'hasMore': False,
                'nextCursor': None, 'unknown': 99}}}, {'pageSize': 7, 'offset': 2, 'totalCount': 3, 'hasMore': False}),
        ]
        for body, paging in cases:
            step = json.loads((HERE / 'sample-query.json').read_text())['invocation']
            step['scriptedResponse']['body'] = body
            document = {'operation': step['operation'], 'tenant': 'sample-tenant', 'document': opaque}
            if paging is not None: document['paging'] = paging
            with self.subTest(body=body):
                _assert_result_contract(document, step, 'result')
                broken = copy.deepcopy(document)
                broken['document']['MixedCase'][0] = 1
                with self.assertRaisesRegex(VectorError, '/document: required result'):
                    _assert_result_contract(broken, step, 'result')

    def test_typed_and_depth_parse_failures_require_exact_errors_instead_of_success_or_correlation(self):
        from run_loopback import _assert_result_contract
        correlation = '01J9MZHXT3RKM0VWXRXGSJDATK'
        base = {'correlationId': correlation, 'payload': {'title': 'Conformance item'}}
        nested = 0
        for _ in range(64): nested = {'nested': nested}
        bodies = [dict(base, success='true'), dict(base, success=None),
                  dict(base, metadata={'paging': []}), dict(base, metadata=[]),
                  dict(base, metadata={'paging': {'pageSize': True}}),
                  dict(base, metadata={'paging': {'pageSize': 1.0}}),
                  dict(base, metadata={'paging': {'pageSize': 2147483648}}),
                  dict(base, ignored=nested)]
        for body in bodies:
            step = json.loads((HERE / 'sample-query.json').read_text())['invocation']
            step['scriptedResponse']['body'] = body
            expected = {'error': {'code': 'gateway_error', 'status': 200,
                                  'detail': 'Query response body could not be parsed.'}}
            with self.subTest(body=body):
                _assert_result_contract(expected, step, 'result')
                with self.assertRaises(VectorError):
                    _assert_result_contract({'operation': step['operation'], 'tenant': 'sample-tenant',
                                             'document': base['payload']}, step, 'result')
                with self.assertRaises(VectorError):
                    _assert_result_contract({'error': dict(expected['error'], correlationId=correlation)}, step, 'result')
        step['scriptedResponse']['body'] = dict(base, ignored=nested['nested'])
        _assert_result_contract({'operation': step['operation'], 'tenant': 'sample-tenant',
                                 'document': base['payload']}, step, 'depth64')

    def test_command_result_properties_are_case_insensitive_but_result_payload_is_opaque(self):
        from run_loopback import _assert_result_contract, _assert_result_request_binding
        step = json.loads((HERE / 'sample-command.json').read_text())['invocation']
        message = '01J9MZHXT3RKM0VWXRXGSJDATP'
        opaque = {'MixedCase': [False, 0], 'RESULTPAYLOAD': {'Success': 'true'}}
        step['scriptedResponse']['body'] = {'MESSAGEID': message, 'RESULTPAYLOAD': opaque}
        step['scriptedResponse']['echoRequestFields'] = ['correlationId']
        document = {'operation': step['operation'], 'tenant': 'sample-tenant',
                    'aggregateId': step['expectedGateway']['body']['aggregateId'], 'status': 'accepted',
                    'messageId': message, 'correlationId': step['envelope']['correlationId'],
                    'idempotencyKey': step['envelope']['idempotencyKey'], 'result': opaque}
        _assert_result_contract(document, step, 'result')
        _assert_result_request_binding(document, {'messageId': '01J9MZHXT3RKM0VWXRXGSJDATM',
                                                 'correlationId': step['envelope']['correlationId']}, step, 'result')
        self.assertEqual(message, _mask_result(document, step, 'result')['messageId'])


if __name__ == "__main__":
    unittest.main()
