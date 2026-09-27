"""Contract compatibility tests requiring no Gateway or production dependency."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from validate import validate_vectors


HERE = Path(__file__).parent
PACKAGE = ("Hexalith.McpCli.Sample.Contracts", "1.0.0")
POSITIONS = ("invocation", "prerequisites", "postconditions")


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

    def _step_at(self, template: dict, position: str) -> tuple[dict, dict, str]:
        document = copy.deepcopy(template)
        if position == "invocation":
            return document, document["invocation"], "/invocation"
        document[position] = [copy.deepcopy(template["invocation"])]
        return document, document[position][0], f"/{position}/0"

    def _cli(self, paths: list[Path], expected: tuple[str, str] = PACKAGE) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(HERE / "validate.py"), "--artifact", str(self.artifact),
             "--expected-package-id", expected[0], "--expected-package-version", expected[1],
             *map(str, paths)], capture_output=True, text=True, check=False,
        )

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

    def test_caller_correlation_id_cannot_be_masked(self) -> None:
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

    def test_contract_owned_objects_are_closed_at_every_call_position(self) -> None:
        for field in (None, "package"):
            with self.subTest(field=field):
                document = copy.deepcopy(self.command)
                target = document if field is None else document[field]
                target["unknown"] = True
                self._assert_rejected(document, "/unknown" if field is None else f"/{field}/unknown")
        for position in POSITIONS:
            for field in (None, "envelope", "expectedGateway", "scriptedResponse", "assertions"):
                with self.subTest(position=position, field=field):
                    document, step, pointer = self._step_at(self.command, position)
                    target = step if field is None else step[field]
                    if field == "assertions":
                        target = target[0]
                    target["unknown"] = True
                    suffix = "" if field is None else "/" + field + ("/0" if field == "assertions" else "")
                    self._assert_rejected(document, f"{pointer}{suffix}/unknown")

    def test_operation_names_reject_malformed_parts_at_every_call_position(self) -> None:
        for name in ("sample", "sample.get.item", "Sample.get-item", "sample.get_item",
                     ".get-item", "sample.", "-sample.get-item", "sample.get-item-",
                     "sample.get--item", "sample.get-item\n", "sample.get-item\r\n", " sample.get-item"):
            for position in POSITIONS:
                with self.subTest(name=name, position=position):
                    document, step, pointer = self._step_at(self.command, position)
                    step["operation"] = name
                    self._assert_rejected(document, f"{pointer}/operation")
            document = copy.deepcopy(self.command)
            document["operation"] = name
            self._assert_rejected(document, "/operation")

    def test_digit_leading_and_single_character_operation_parts_are_valid(self) -> None:
        for name in ("0.1", "a.b", "1-sample.2-get-item", "sample1.get-item2"):
            with self.subTest(name=name):
                document = copy.deepcopy(self.command)
                document["operation"] = document["invocation"]["operation"] = name
                self.assertEqual([], self._validate(document))

    def test_package_patterns_require_complete_strings(self) -> None:
        for field, values in (
            ("id", ("", " ", PACKAGE[0] + "\n", "-Owner.Contracts", "Owner/Contracts")),
            ("version", ("", " ", "1.0", "1.0.0\n", "1.0.0\r\n", "v1.0.0")),
        ):
            for value in values:
                with self.subTest(field=field, value=value):
                    document = copy.deepcopy(self.command)
                    document["package"][field] = value
                    self._assert_rejected(document, f"/package/{field}")

    def test_nonblank_envelope_strings_at_every_call_position(self) -> None:
        for position in POSITIONS:
            for field in ("tenant", "actor", "aggregateId", "entityId", "cursor"):
                for value in ("", " \t\r\n", "\u2003"):
                    with self.subTest(position=position, field=field, value=value):
                        document, step, pointer = self._step_at(self.query, position)
                        step["envelope"][field] = value
                        self._assert_rejected(document, f"{pointer}/envelope/{field}")

    def test_nonblank_gateway_routing_at_every_call_position(self) -> None:
        for template in (self.command, self.query):
            for position in POSITIONS:
                for field in ("domain", "aggregateId", "commandType" if template["kind"] == "command" else "queryType"):
                    for value in (None, False, 42, "", " \t\n", "\u2003"):
                        with self.subTest(kind=template["kind"], position=position, field=field, value=value):
                            document, step, pointer = self._step_at(template, position)
                            step["expectedGateway"]["body"][field] = value
                            self._assert_rejected(document, f"{pointer}/expectedGateway/body/{field}: required nonblank")

    def test_ulids_reject_invalid_alphabet_overflow_and_trailing_newlines(self) -> None:
        for position in POSITIONS:
            for field in ("correlationId", "idempotencyKey"):
                for value in ("", "01J9MZHXT3RKM0VWXRXGSJDATK\n", "8" + "0" * 25,
                              "0" * 25, "0" * 27, "0" * 25 + "I", "0" * 25 + "O", "0" * 25 + "U"):
                    with self.subTest(position=position, field=field, value=value):
                        document, step, pointer = self._step_at(self.command, position)
                        step["envelope"][field] = value
                        self._assert_rejected(document, f"{pointer}/envelope/{field}")

    def test_ulid_and_paging_boundaries_are_valid(self) -> None:
        for value in ("0" * 26, "7" + "Z" * 25):
            document = copy.deepcopy(self.command)
            for field in ("correlationId", "idempotencyKey"):
                document["invocation"]["envelope"][field] = value
                document["invocation"]["expectedGateway"]["body"][field] = value
            self.assertEqual([], self._validate(document))
        for paging in ({"pageSize": 1, "offset": 0}, {"pageSize": 200, "cursor": "x" * 4096}):
            document = copy.deepcopy(self.query)
            document["invocation"]["envelope"].update(paging)
            document["invocation"]["expectedGateway"]["body"]["paging"] = paging
            self.assertEqual([], self._validate(document))

    def test_paging_outside_bounds_is_rejected(self) -> None:
        for field, values in (("pageSize", (0, 201, True)), ("offset", (-1, True)), ("cursor", ("x" * 4097,))):
            for value in values:
                with self.subTest(field=field, value=value):
                    document = copy.deepcopy(self.query)
                    document["invocation"]["envelope"][field] = value
                    self._assert_rejected(document, f"/invocation/envelope/{field}")

    def test_nonfinite_json_is_rejected_with_escaped_locations_in_all_data_areas(self) -> None:
        for position in POSITIONS:
            for area in ("payload", "expectedGateway", "scriptedResponse", "assertions"):
                for number in ("NaN", "Infinity", "-Infinity", "1e400", "-1e400"):
                    with self.subTest(position=position, area=area, number=number):
                        document, step, pointer = self._step_at(self.command, position)
                        if area == "assertions":
                            target = step[area][0]
                            target["value"] = ["NONFINITE"]
                            suffix = "/assertions/0/value/0"
                        else:
                            target = step[area] if area == "payload" else step[area]["body"]
                            target["odd~/field"] = ["NONFINITE"]
                            suffix = f"/{area}" + ("" if area == "payload" else "/body") + "/odd~0~1field/0"
                        source = self._write(document)
                        source.write_text(source.read_text(encoding="utf-8").replace('"NONFINITE"', number), encoding="utf-8")
                        findings = validate_vectors([source], self.artifact, PACKAGE)
                        self.assertTrue(any(f"{source}:{pointer}{suffix}: nonfinite JSON number" in item for item in findings), findings)

    def test_module_owned_json_remains_open_and_preserves_finite_values(self) -> None:
        document = copy.deepcopy(self.command)
        step = document["invocation"]
        data = {"unfamiliar": [None, True, False, -1, 1.25, 1e300, "NaN", {"~name/": ""}]}
        step["payload"]["custom"] = data
        step["expectedGateway"]["body"]["custom"] = data
        step["scriptedResponse"]["body"]["custom"] = data
        step["assertions"].append({"path": "", "operator": "equals", "value": data})
        self.assertEqual([], self._validate(document))

    def test_wrong_kind_inputs_at_every_call_position(self) -> None:
        cases = (
            (self.command, {"entityId": "entity", "pageSize": 1, "offset": 0, "cursor": "next"}),
            (self.query, {"correlationId": "0" * 26, "idempotencyKey": "0" * 26, "extensions": {}}),
        )
        for template, fields in cases:
            for position in POSITIONS:
                for field, value in fields.items():
                    with self.subTest(kind=template["kind"], position=position, field=field):
                        document, step, pointer = self._step_at(template, position)
                        step["envelope"][field] = value
                        self._assert_rejected(document, f"{pointer}/envelope/{field}")

    def test_supplied_extensions_must_match_expected_request_at_every_call_position(self) -> None:
        for position in POSITIONS:
            for expected in (None, {}, {"custom": "different"}, {"custom": 1}, {"custom": "value"}):
                with self.subTest(position=position, expected=expected):
                    document, step, pointer = self._step_at(self.command, position)
                    step["envelope"]["extensions"] = {"custom": "value"}
                    if expected is not None:
                        step["expectedGateway"]["body"]["extensions"] = expected
                    if expected == {"custom": "value"}:
                        self.assertEqual([], self._validate(document))
                    else:
                        self._assert_rejected(document, f"{pointer}/expectedGateway/body/extensions")

    def test_query_response_cannot_echo_request_identifiers_at_every_call_position(self) -> None:
        for position in POSITIONS:
            for fields in (["messageId"], ["correlationId"], ["messageId", "correlationId"]):
                with self.subTest(position=position, fields=fields):
                    document, step, pointer = self._step_at(self.query, position)
                    step["scriptedResponse"]["echoRequestFields"] = fields
                    self._assert_rejected(document, f"{pointer}/scriptedResponse/echoRequestFields: query request")

    def test_existing_script_consistency_rules_apply_at_every_call_position(self) -> None:
        for position in POSITIONS:
            for field, value in (("tenant", "wrong"), ("payload", []), ("correlationId", "0" * 26),
                                 ("idempotencyKey", "0" * 26), ("messageId", "0" * 26)):
                with self.subTest(position=position, field=field):
                    document, step, pointer = self._step_at(self.command, position)
                    step["expectedGateway"]["body"][field] = value
                    self._assert_rejected(document, f"{pointer}/expectedGateway/body/{field}")
            document, step, pointer = self._step_at(self.command, position)
            step["scriptedResponse"]["echoRequestFields"] = []
            self._assert_rejected(document, f"{pointer}/scriptedResponse/echoRequestFields")
            document, step, pointer = self._step_at(self.query, position)
            step["expectedGateway"]["body"]["paging"] = {"pageSize": 10}
            self._assert_rejected(document, f"{pointer}/expectedGateway/body/paging")

    def test_assertion_operators_paths_and_values_at_every_call_position(self) -> None:
        invalid = (
            {"path": "/status", "operator": "execute", "value": "accepted"},
            {"path": "status", "operator": "equals", "value": "accepted"},
            {"path": "/bad~2escape", "operator": "equals", "value": 1},
            {"path": "/trailing~", "operator": "equals", "value": 1},
            {"path": "\n", "operator": "equals", "value": 1},
            {"path": "/status", "operator": "exists", "value": "true"},
            {"path": "/status", "operator": "exists", "value": 1},
            {"path": "/status", "operator": "arrayLength", "value": -1},
            {"path": "/status", "operator": "arrayLength", "value": 1.5},
            {"path": "/status", "operator": "arrayLength", "value": True},
            *({"path": "", "operator": operator} for operator in ("equals", "contains", "exists", "arrayLength")),
        )
        for position in POSITIONS:
            for assertion in invalid:
                with self.subTest(position=position, assertion=assertion):
                    document, step, pointer = self._step_at(self.command, position)
                    step["assertions"] = [assertion]
                    self._assert_rejected(document, f"{pointer}/assertions/0")

    def test_valid_assertion_boundaries(self) -> None:
        self.command["invocation"]["assertions"] = [
            {"path": "", "operator": "equals", "value": None},
            {"path": "/", "operator": "exists", "value": False},
            {"path": "/a~1b/~0/0", "operator": "arrayLength", "value": 0},
            {"path": "/line\n", "operator": "contains", "value": {"field": [True, 1]}},
        ]
        self.assertEqual([], self._validate(self.command))

    def test_package_ids_are_case_insensitive_for_vectors_artifacts_and_runners(self) -> None:
        self.command["package"]["id"] = PACKAGE[0].lower()
        self.assertEqual([], self._validate(self.command, (PACKAGE[0].upper(), PACKAGE[1])))

    def test_package_id_and_exact_version_mismatches_are_rejected(self) -> None:
        for field, value in (("id", "Other.Contracts"), ("version", "1.0.1"), ("version", "1.0.0.0")):
            with self.subTest(field=field):
                document = copy.deepcopy(self.command)
                document["package"][field] = value
                self._assert_rejected(document, "/package: vector")
        for expected in (("Other.Contracts", "1.0.0"), (PACKAGE[0], "1.0.1")):
            findings = self._validate(self.command, expected)
            self.assertTrue(any(f"{self.artifact}:/metadata:" in item for item in findings), findings)
        self.artifact = self._package(PACKAGE[0], "1.0.0-RC")
        self.command["package"]["version"] = "1.0.0-rc"
        self._assert_rejected(self.command, "/package: vector")

    def test_vector_header_must_match_invocation(self) -> None:
        for field, value in (("operation", "sample.other"), ("kind", "query")):
            document = copy.deepcopy(self.command)
            document[field] = value
            self._assert_rejected(document, "/invocation: operation and kind must match")

    def test_unsupported_format_values_and_missing_version_are_rejected(self) -> None:
        for version in (0, -1, 2, "1", True, None):
            with self.subTest(version=version):
                document = copy.deepcopy(self.command)
                document["formatVersion"] = version
                self._assert_rejected(document, "/formatVersion")
        del self.command["formatVersion"]
        self._assert_rejected(self.command, "'formatVersion' is a required property")

    def test_unreadable_or_invalid_artifact_is_reported_without_loading_assemblies(self) -> None:
        self.artifact.write_bytes(b"not a zip")
        self._assert_rejected(self.command, "cannot read NuGet release artifact")
        with zipfile.ZipFile(self.artifact, "w") as archive:
            archive.writestr("nested/sample.nuspec", "<package/>")
        self._assert_rejected(self.command, "expected exactly one root .nuspec")

    def test_cli_accepts_all_three_samples(self) -> None:
        result = self._cli([HERE / "sample-command.json", HERE / "sample-query.json", HERE / "sample-rename.json"])
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Validated 3 vector(s)", result.stdout)
        self.assertEqual("", result.stderr)

    def test_cli_and_reusable_entry_point_return_identical_located_rejections(self) -> None:
        cases = []
        malformed = copy.deepcopy(self.command)
        malformed["postconditions"][0]["scriptedResponse"]["echoRequestFields"] = ["messageId"]
        cases.append((malformed, PACKAGE))
        unsupported = copy.deepcopy(self.command)
        unsupported["formatVersion"] = 2
        cases.append((unsupported, PACKAGE))
        nonfinite = copy.deepcopy(self.command)
        nonfinite["invocation"]["payload"]["amount"] = float("nan")
        cases.append((nonfinite, PACKAGE))
        incompatible = copy.deepcopy(self.command)
        incompatible["package"]["id"] = "Other.Contracts"
        cases.append((incompatible, PACKAGE))
        cases.append((self.command, (PACKAGE[0], "1.0.1")))
        cases.append((self.command, ("", PACKAGE[1])))
        for document, expected in cases:
            with self.subTest(document=document, expected=expected):
                source = self._write(document)
                findings = validate_vectors([source], self.artifact, expected)
                result = self._cli([source], expected)
                self.assertEqual(1, result.returncode, result.stderr)
                self.assertEqual("", result.stdout)
                self.assertEqual(findings, result.stderr.splitlines())
                self.assertTrue(all(item.startswith((str(source) + ":/", str(self.artifact) + ":/")) for item in findings), findings)


if __name__ == "__main__":
    unittest.main()
