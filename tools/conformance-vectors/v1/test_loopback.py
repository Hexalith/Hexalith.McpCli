"""Focused checks for the process runner's request and document comparison rules."""

from __future__ import annotations

import base64
import hashlib
import json
import tempfile
import unittest
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


class LoopbackRulesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.command = json.loads((HERE / "sample-command.json").read_text(encoding="utf-8"))["invocation"]
        self.rename = json.loads((HERE / "sample-rename.json").read_text(encoding="utf-8"))["invocation"]

    def test_generated_ids_are_masked_but_supplied_correlation_and_key_remain_exact(self) -> None:
        body = {"messageId": "01J9MZHXT3RKM0VWXRXGSJDATN", "correlationId": "01J9MZHXT3RKM0VWXRXGSJDATK",
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
        result = {"messageId": "01J9MZHXT3RKM0VWXRXGSJDATN",
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
            artifact.write_bytes(b"exact signed archive bytes")
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
                "packageFolders": {str(root / "packages"): {}}}))
            host.with_suffix(".deps.json").write_text(json.dumps({"libraries": {
                "Sample.Contracts/1.0.0": {"type": "package", "sha512": "sha512-" + content_hash}}}))
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

    def test_host_restored_artifact_hash_must_match(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            host = root / "host/bin/Release/net10.0/Host.dll"
            host.parent.mkdir(parents=True)
            artifact = root / "sample.nupkg"
            artifact.write_bytes(b"immutable artifact")
            identity = "Hexalith.McpCli.Sample.Contracts/1.0.0"
            digest = "sha512-" + base64.b64encode(hashlib.sha512(artifact.read_bytes()).digest()).decode()
            cached = root / "packages/hexalith.mcpcli.sample.contracts/1.0.0/hexalith.mcpcli.sample.contracts.1.0.0.nupkg"
            cached.parent.mkdir(parents=True)
            cached.write_bytes(artifact.read_bytes())
            assets = root / "host/obj/project.assets.json"
            assets.parent.mkdir(parents=True)
            assets.write_text(json.dumps({"libraries": {identity: {
                "type": "package", "path": "hexalith.mcpcli.sample.contracts/1.0.0", "sha512": digest}},
                "packageFolders": {str(root / "packages"): {}}}))
            deps = host.with_suffix(".deps.json")
            deps.write_text(json.dumps({"libraries": {identity: {"type": "package", "sha512": digest}}}), encoding="utf-8")
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


if __name__ == "__main__":
    unittest.main()
