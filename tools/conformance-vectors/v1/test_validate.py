"""Contract compatibility tests requiring no Gateway or production dependency."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from validate import validate_vectors


HERE = Path(__file__).parent
PACKAGE = ("Hexalith.McpCli.Sample.Contracts", "1.0.0")


class VectorContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.artifact = self._package(*PACKAGE)
        self.command = json.loads((HERE / "sample-command.json").read_text(encoding="utf-8"))
        self.query = json.loads((HERE / "sample-query.json").read_text(encoding="utf-8"))

    def _package(self, package_id: str, version: str) -> Path:
        path = self.directory / f"{package_id}.{version}.nupkg"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr(f"{package_id}.nuspec", f"<package><metadata><id>{package_id}</id><version>{version}</version></metadata></package>")
        return path

    def _write(self, document: object, name: str = "vector.json") -> Path:
        path = self.directory / name
        path.write_text(json.dumps(document), encoding="utf-8")
        return path

    def _validate(self, document: object, expected_package: tuple[str, str] | None = PACKAGE) -> list[str]:
        return validate_vectors([self._write(document)], self.artifact, expected_package)

    def _assert_rejected(self, document: object, fragment: str) -> None:
        findings = self._validate(document)
        self.assertTrue(any(fragment in finding for finding in findings), findings)

    def test_synthetic_command_and_query_are_compatible_with_release_and_catalog(self) -> None:
        paths = [HERE / "sample-command.json", HERE / "sample-query.json", HERE / "sample-rename.json"]
        self.assertEqual([], validate_vectors(paths, self.artifact, PACKAGE,
                                              ["sample.create-item", "sample.get-item", "sample.rename-item"]))

    def test_unsupported_format_version_is_located(self) -> None:
        self.command["formatVersion"] = 2
        self._assert_rejected(self.command, "/formatVersion: unsupported format version 2")

    def test_unknown_nested_field_is_located(self) -> None:
        self.command["invocation"]["envelope"]["payloadTenant"] = "wrong"
        self._assert_rejected(self.command, "/invocation/envelope/payloadTenant")

    def test_invalid_input_and_gateway_route_are_located(self) -> None:
        self.query["invocation"]["envelope"]["pageSize"] = 201
        findings = self._validate(self.query)
        self.assertTrue(any("/invocation/envelope/pageSize" in finding for finding in findings), findings)
        self.query["invocation"]["envelope"]["pageSize"] = 25
        self.query["invocation"]["expectedGateway"]["path"] = "/api/v1/commands"
        self._assert_rejected(self.query, "/invocation/expectedGateway/path")

    def test_invalid_assertion_is_rejected(self) -> None:
        self.command["invocation"]["assertions"][0]["operator"] = "script"
        self._assert_rejected(self.command, "/invocation/assertions/0/operator")

    def test_submitted_payload_may_include_envelope_owned_values(self) -> None:
        self.command["invocation"]["expectedGateway"]["body"]["payload"]["Tenant"] = "sample-tenant"
        self.assertEqual([], self._validate(self.command))

    def test_caller_idempotency_key_cannot_be_masked(self) -> None:
        self.command["invocation"]["expectedGateway"]["maskGenerated"].append("/correlationId")
        self._assert_rejected(self.command, "caller-supplied correlationId cannot be masked")

    def test_artifact_package_identity_and_restored_version_are_checked(self) -> None:
        self.command["package"]["version"] = "1.0.1"
        self._assert_rejected(self.command, "/package: vector")
        findings = validate_vectors([HERE / "sample-command.json"], self.artifact, (PACKAGE[0], "1.0.1"))
        self.assertTrue(any("does not match restored package" in finding for finding in findings), findings)

    def test_duplicate_and_missing_operation_vectors_are_rejected(self) -> None:
        first = self._write(self.command, "first.json")
        second = self._write(copy.deepcopy(self.command), "second.json")
        findings = validate_vectors([first, second], self.artifact, PACKAGE, ["sample.create-item", "sample.get-item"])
        self.assertTrue(any("duplicate 'sample.create-item'" in finding for finding in findings), findings)
        self.assertTrue(any("missing conformance vector" in finding for finding in findings), findings)

    def test_query_cannot_mix_cursor_and_offset(self) -> None:
        self.query["invocation"]["envelope"]["cursor"] = "next"
        self.query["invocation"]["envelope"]["offset"] = 10
        self._assert_rejected(self.query, "/invocation/envelope/cursor: cursor cannot be combined")

    def test_duplicate_json_fields_are_rejected(self) -> None:
        source = self.directory / "duplicate.json"
        source.write_text('{"formatVersion":1,"formatVersion":1}', encoding="utf-8")
        findings = validate_vectors([source], self.artifact)
        self.assertTrue(any("duplicate JSON field 'formatVersion'" in finding for finding in findings), findings)


if __name__ == "__main__":
    unittest.main()
