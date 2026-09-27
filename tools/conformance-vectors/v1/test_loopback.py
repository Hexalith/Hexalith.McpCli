"""Focused checks for the process runner's request and document comparison rules."""

from __future__ import annotations

import base64
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from run_loopback import _assert_result, _expect_fields, _mask, _mask_result, _verify_artifact_in_host
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
        _expect_fields({"body": {"payload": {"id": "A"}, "tenant": "t", "unused": None}},
                       {"body": {"payload": {"id": "A"}, "tenant": "t"}}, "request")
        with self.assertRaisesRegex(VectorError, "/payload"):
            _expect_fields({"body": {"payload": {"id": "A", "unexpected": True}}},
                           {"body": {"payload": {"id": "A"}}}, "request")

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

    def test_host_restored_artifact_hash_must_match(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            host = Path(directory) / "Host.dll"
            artifact = Path(directory) / "sample.nupkg"
            artifact.write_bytes(b"immutable artifact")
            identity = "Hexalith.McpCli.Sample.Contracts/1.0.0"
            digest = "sha512-" + base64.b64encode(hashlib.sha512(artifact.read_bytes()).digest()).decode()
            deps = host.with_suffix(".deps.json")
            deps.write_text(json.dumps({"libraries": {identity: {"type": "package", "sha512": digest}}}), encoding="utf-8")
            _verify_artifact_in_host(host, artifact, ("Hexalith.McpCli.Sample.Contracts", "1.0.0"))
            artifact.write_bytes(b"changed artifact")
            with self.assertRaisesRegex(VectorError, "hash differs"):
                _verify_artifact_in_host(host, artifact, ("Hexalith.McpCli.Sample.Contracts", "1.0.0"))


if __name__ == "__main__":
    unittest.main()
