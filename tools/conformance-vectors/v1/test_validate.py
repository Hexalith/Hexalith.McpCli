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

    def test_query_accepts_every_finite_json_root_at_every_call_position(self) -> None:
        values = ({"field": [1, True, None]}, [1, "two", False], "value", 0, 1.5, True, False, None)
        for position in POSITIONS:
            for value in values:
                with self.subTest(position=position, value=value):
                    document, step, _ = self._step_at(self.query, position)
                    step["payload"] = copy.deepcopy(value)
                    if value is None:
                        step["expectedGateway"]["body"].pop("payload", None)
                    else:
                        step["expectedGateway"]["body"]["payload"] = copy.deepcopy(value)
                    self.assertEqual([], self._validate(document))

    def test_command_rejects_non_object_json_roots_at_every_call_position(self) -> None:
        for position in POSITIONS:
            for value in ([1], "value", 0, 1.5, True, False, None):
                with self.subTest(position=position, value=value):
                    document, step, pointer = self._step_at(self.command, position)
                    step["payload"] = value
                    self._assert_rejected(document, f"{pointer}/payload")

    def test_query_payload_wire_presence_matches_nullness_at_every_call_position(self) -> None:
        for position in POSITIONS:
            document, step, pointer = self._step_at(self.query, position)
            step["expectedGateway"]["body"]["payload"] = None
            self._assert_rejected(document, f"{pointer}/expectedGateway/body/payload: JSON null Query payload must be omitted")
            document, step, pointer = self._step_at(self.query, position)
            step["payload"] = []
            step["expectedGateway"]["body"].pop("payload", None)
            self._assert_rejected(document, f"{pointer}/expectedGateway/body/payload: non-null Query payload must be emitted")

    def test_non_object_query_payload_must_match_wire_payload_at_every_call_position(self) -> None:
        mismatches = (
            ([{"value": True}], [{"value": 1}]),
            ([1, {"nested": [False]}], [1.0, {"nested": [0]}]),
            ("input", "different"),
            (1, None),
            (True, 1),
        )
        for position in POSITIONS:
            for payload, expected in mismatches:
                with self.subTest(position=position, payload=payload, expected=expected):
                    document, step, pointer = self._step_at(self.query, position)
                    step["payload"] = payload
                    step["expectedGateway"]["body"]["payload"] = expected
                    self._assert_rejected(
                        document,
                        f"{pointer}/expectedGateway/body/payload: non-object Query payload must equal the input Payload")

    def test_non_object_query_payload_treats_integer_and_float_encodings_as_numbers(self) -> None:
        for position in POSITIONS:
            for payload, expected in ((1, 1.0), (1.0, 1), ([1, {"nested": [2.0]}], [1.0, {"nested": [2]}])):
                with self.subTest(position=position, payload=payload, expected=expected):
                    document, step, _ = self._step_at(self.query, position)
                    step["payload"] = payload
                    step["expectedGateway"]["body"]["payload"] = expected
                    self.assertEqual([], self._validate(document))

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
        for raw, field in (('{"formatVersion":1,"formatVersion":1}', "formatVersion"),
                           ('{"invocation":{"payload":{"name":1,"name":2}}}', "name")):
            with self.subTest(field=field):
                source.write_text(raw, encoding="utf-8")
                findings = validate_vectors([source], self.artifact, PACKAGE)
                self.assertEqual([f"{source}:/: duplicate JSON field {field!r}"], findings)
                result = self._cli([source])
                self.assertEqual(1, result.returncode, result.stderr)
                self.assertEqual("", result.stdout)
                self.assertEqual(findings, result.stderr.splitlines())
                self.assertNotIn("Traceback", result.stderr)

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

    def test_multiple_unknown_gateway_fields_are_each_reported_at_escaped_locations(self) -> None:
        document = copy.deepcopy(self.command)
        body = document["invocation"]["expectedGateway"]["body"]
        body["odd~/field"] = True
        body["second/field~"] = False
        findings = self._validate(document)
        self.assertTrue(any("/invocation/expectedGateway/body/odd~0~1field:" in item for item in findings), findings)
        self.assertTrue(any("/invocation/expectedGateway/body/second~1field~0:" in item for item in findings), findings)
        self.assertEqual(2, sum("additional property" in item for item in findings), findings)

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
                            self._assert_rejected(document, f"{pointer}/expectedGateway/body/{field}")

    def test_gateway_request_bodies_require_every_emitted_field_at_every_call_position(self) -> None:
        required = (
            (self.command, ("messageId", "tenant", "domain", "aggregateId", "commandType", "payload", "correlationId")),
            (self.query, ("tenant", "domain", "aggregateId", "queryType", "projectionType")),
        )
        for template, fields in required:
            for position in POSITIONS:
                for field in fields:
                    with self.subTest(kind=template["kind"], position=position, field=field):
                        document, step, pointer = self._step_at(template, position)
                        del step["expectedGateway"]["body"][field]
                        self._assert_rejected(document, f"{pointer}/expectedGateway/body/{field}")

    def test_gateway_request_bodies_reject_unknown_and_mistyped_fields_at_every_call_position(self) -> None:
        mistyped = (
            (self.command, (("messageId", True), ("tenant", 1), ("payload", []), ("correlationId", False))),
            (self.query, (("tenant", 1), ("projectionType", True), ("paging", []))),
        )
        for template, cases in mistyped:
            for position in POSITIONS:
                document, step, pointer = self._step_at(template, position)
                step["expectedGateway"]["body"]["bogus"] = "impossible"
                self._assert_rejected(document, f"{pointer}/expectedGateway/body/bogus")
                for field, value in cases:
                    with self.subTest(kind=template["kind"], position=position, field=field):
                        document, step, pointer = self._step_at(template, position)
                        step["expectedGateway"]["body"][field] = value
                        self._assert_rejected(document, f"{pointer}/expectedGateway/body/{field}")

    def test_query_projection_type_uses_runtime_slug_grammar_at_every_call_position(self) -> None:
        invalid = (None, False, 42, "", "Sample-items", "-sample", "sample-", "a" * 65)
        for position in POSITIONS:
            for value in invalid:
                with self.subTest(position=position, value=value):
                    document, step, pointer = self._step_at(self.query, position)
                    step["expectedGateway"]["body"]["projectionType"] = value
                    self._assert_rejected(document, f"{pointer}/expectedGateway/body/projectionType")

    def test_gateway_domains_use_runtime_slug_grammar_at_every_call_position(self) -> None:
        invalid = ("", "UPPER", "-leading", "trailing-", "under_score", "contains space", "a" * 65)
        valid = ("a", "two--hyphens", "a" + "-" * 62 + "z")
        for template in (self.command, self.query):
            for position in POSITIONS:
                for value in invalid:
                    with self.subTest(kind=template["kind"], position=position, value=value):
                        document, step, pointer = self._step_at(template, position)
                        step["expectedGateway"]["body"]["domain"] = value
                        self._assert_rejected(document, f"{pointer}/expectedGateway/body/domain")
                for value in valid:
                    with self.subTest(kind=template["kind"], position=position, value=value):
                        document, step, _ = self._step_at(template, position)
                        step["expectedGateway"]["body"]["domain"] = value
                        self.assertEqual([], self._validate(document))

    def test_gateway_identifiers_use_runtime_grammar_at_every_call_position(self) -> None:
        invalid = ("", "-leading", "trailing-", ".leading", "trailing_", "contains/slash", "contains space", "a" * 257)
        valid = ("a", "A.b_c-9", "A" + "." * 254 + "9")
        for template in (self.command, self.query):
            for position in POSITIONS:
                for value in invalid:
                    with self.subTest(kind=template["kind"], position=position, field="aggregateId", value=value):
                        document, step, pointer = self._step_at(template, position)
                        step["envelope"]["aggregateId"] = value
                        step["expectedGateway"]["body"]["aggregateId"] = value
                        self._assert_rejected(document, f"{pointer}/expectedGateway/body/aggregateId")
                for value in valid:
                    with self.subTest(kind=template["kind"], position=position, field="aggregateId", value=value):
                        document, step, _ = self._step_at(template, position)
                        step["envelope"]["aggregateId"] = value
                        step["expectedGateway"]["body"]["aggregateId"] = value
                        self.assertEqual([], self._validate(document))
        for position in POSITIONS:
            for value in invalid:
                with self.subTest(position=position, field="entityId", value=value):
                    document, step, pointer = self._step_at(self.query, position)
                    step["envelope"]["entityId"] = value
                    step["expectedGateway"]["body"]["entityId"] = value
                    self._assert_rejected(document, f"{pointer}/expectedGateway/body/entityId")
            for value in valid:
                with self.subTest(position=position, field="entityId", value=value):
                    document, step, _ = self._step_at(self.query, position)
                    step["envelope"]["entityId"] = value
                    step["expectedGateway"]["body"]["entityId"] = value
                    self.assertEqual([], self._validate(document))

    def test_gateway_wire_types_use_kind_specific_runtime_grammar_at_every_call_position(self) -> None:
        common_invalid = ("", " \t", "bad<type", "bad>type", "bad&type", "bad'type", 'bad"type',
                          "prefix-JavaScript :suffix", "prefix-onload =suffix", "a" * 257)
        cases = (
            (self.command, "commandType", common_invalid, ("a", "command:type", "a" * 256)),
            (self.query, "queryType", (*common_invalid, "query:type"), ("a", "query-type", "a" * 256)),
            (self.query, "projectionActorType", (*common_invalid, "actor:type", "a" * 65),
             ("a", "projection-actor", "a" * 64)),
        )
        for template, field, invalid, valid in cases:
            for position in POSITIONS:
                for value in invalid:
                    with self.subTest(kind=template["kind"], position=position, field=field, value=value):
                        document, step, pointer = self._step_at(template, position)
                        step["expectedGateway"]["body"][field] = value
                        self._assert_rejected(document, f"{pointer}/expectedGateway/body/{field}")
                for value in valid:
                    with self.subTest(kind=template["kind"], position=position, field=field, value=value):
                        document, step, _ = self._step_at(template, position)
                        step["expectedGateway"]["body"][field] = value
                        self.assertEqual([], self._validate(document))

    def test_tenant_runtime_slug_grammar_and_agreement_apply_at_every_call_position(self) -> None:
        invalid = ("", "UPPER", "-leading", "trailing-", "contains space", "a" * 65)
        for template in (self.command, self.query):
            for position in POSITIONS:
                for area in ("envelope", "expectedGateway"):
                    for value in invalid:
                        with self.subTest(kind=template["kind"], position=position, area=area, value=value):
                            document, step, pointer = self._step_at(template, position)
                            if area == "envelope":
                                step["envelope"]["tenant"] = value
                                location = f"{pointer}/envelope/tenant"
                            else:
                                step["expectedGateway"]["body"]["tenant"] = value
                                location = f"{pointer}/expectedGateway/body/tenant"
                            self._assert_rejected(document, location)
                document, step, pointer = self._step_at(template, position)
                step["expectedGateway"]["body"]["tenant"] = "other-tenant"
                self._assert_rejected(document, f"{pointer}/expectedGateway/body/tenant: must equal envelope tenant")
        for value in ("a", "a-b1", "a" + "-" * 62 + "z"):
            for template in (self.command, self.query):
                with self.subTest(kind=template["kind"], value=value):
                    document = copy.deepcopy(template)
                    document["invocation"]["envelope"]["tenant"] = value
                    document["invocation"]["expectedGateway"]["body"]["tenant"] = value
                    self.assertEqual([], self._validate(document))

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
        for paging in ({"pageSize": 1, "offset": 0}, {"offset": 2147483647},
                       {"pageSize": 200, "cursor": "x" * 4096}):
            document = copy.deepcopy(self.query)
            document["invocation"]["envelope"].pop("pageSize", None)
            document["invocation"]["envelope"].update(paging)
            document["invocation"]["expectedGateway"]["body"]["paging"] = paging
            self.assertEqual([], self._validate(document))

    def test_paging_outside_bounds_is_rejected(self) -> None:
        for position in POSITIONS:
            for field, values in (("pageSize", (0, 201, True)), ("offset", (-1, True, 2147483648)),
                                  ("cursor", ("x" * 4097,))):
                for value in values:
                    with self.subTest(position=position, field=field, value=value):
                        document, step, pointer = self._step_at(self.query, position)
                        step["envelope"][field] = value
                        self._assert_rejected(document, f"{pointer}/envelope/{field}")

    def test_contract_integer_fields_reject_floats_and_booleans_at_every_call_position(self) -> None:
        for position in POSITIONS:
            for area, field, integer in (("envelope", "pageSize", 1), ("envelope", "offset", 0),
                                         ("scriptedResponse", "statusCode", 202)):
                for value in (float(integer), bool(integer)):
                    with self.subTest(position=position, field=field, value=value):
                        document, step, pointer = self._step_at(self.query, position)
                        step[area][field] = value
                        self._assert_rejected(document, f"{pointer}/{area}/{field}")
            for value in (0.0, 1.0, True, False):
                with self.subTest(position=position, value=value):
                    document, step, pointer = self._step_at(self.query, position)
                    step["assertions"] = [{"path": "", "operator": "arrayLength", "value": value}]
                    self._assert_rejected(document, f"{pointer}/assertions/0/value")

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
        data = {"unfamiliar": [None, True, False, -1, 1.0, 1.25, 1e300, "NaN", {"~name/": ""}]}
        step["payload"]["custom"] = data
        step["expectedGateway"]["body"]["payload"]["custom"] = data
        step["scriptedResponse"]["body"]["custom"] = data
        step["assertions"].append({"path": "", "operator": "equals", "value": data})
        self.assertEqual([], self._validate(document))

    def test_wrong_kind_inputs_at_every_call_position(self) -> None:
        cases = (
            (self.command, {"entityId": "entity", "pageSize": 1, "offset": 0, "cursor": "next"}),
            (self.query, {"correlationId": "0" * 26, "idempotencyKey": "0" * 26, "extensions": {"custom": "value"}}),
        )
        for template, fields in cases:
            for position in POSITIONS:
                for field, value in fields.items():
                    with self.subTest(kind=template["kind"], position=position, field=field):
                        document, step, pointer = self._step_at(template, position)
                        step["envelope"][field] = value
                        self._assert_rejected(document, f"{pointer}/envelope/{field}")

    def test_supplied_extensions_cannot_be_empty_at_every_call_position(self) -> None:
        # The CLI sends no extension flags for an empty map while MCP forwards {}; omission is the only portable form.
        for position in POSITIONS:
            for expected in (None, {}):
                with self.subTest(position=position, expected=expected):
                    document, step, pointer = self._step_at(self.command, position)
                    step["envelope"]["extensions"] = {}
                    if expected is not None:
                        step["expectedGateway"]["body"]["extensions"] = expected
                    self._assert_rejected(document, f"{pointer}/envelope/extensions: {{}} should be non-empty")

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

    def test_absent_optional_inputs_cannot_have_expected_request_values(self) -> None:
        for template, field, values in ((self.command, "extensions", (None, {}, {"custom": "value"})),
                                        (self.query, "paging", (None, {}, {"pageSize": 1})),
                                        (self.query, "entityId", (None, "", "entity"))):
            for position in POSITIONS:
                for value in values:
                    with self.subTest(position=position, field=field, value=value):
                        document, step, pointer = self._step_at(template, position)
                        for optional in ("extensions", "entityId", "pageSize", "offset", "cursor"):
                            step["envelope"].pop(optional, None)
                        step["expectedGateway"]["body"][field] = value
                        self._assert_rejected(document, f"{pointer}/expectedGateway/body/{field}")

    def test_supplied_entity_id_is_valid_at_every_call_position(self) -> None:
        for position in POSITIONS:
            for value in ("entity", "0" * 26):
                with self.subTest(position=position, value=value):
                    document, step, _ = self._step_at(self.query, position)
                    step["envelope"]["entityId"] = value
                    step["expectedGateway"]["body"]["entityId"] = value
                    self.assertEqual([], self._validate(document))

    def test_wrong_kind_expected_request_fields_at_every_call_position(self) -> None:
        cases = (
            (self.command, {"queryType": "get-item", "projectionType": "items", "projectionActorType": "item-actor",
                            "entityId": "entity", "paging": {"pageSize": 1}}),
            (self.query, {"commandType": "create-item", "messageId": "0" * 26,
                          "correlationId": "0" * 26, "idempotencyKey": "0" * 26, "extensions": {}}),
        )
        for template, fields in cases:
            for position in POSITIONS:
                for field, value in fields.items():
                    with self.subTest(kind=template["kind"], position=position, field=field):
                        document, step, pointer = self._step_at(template, position)
                        step["expectedGateway"]["body"][field] = value
                        self._assert_rejected(document, f"{pointer}/expectedGateway/body/{field}")

    def test_unsent_known_request_fields_at_every_call_position(self) -> None:
        fields = {"search": "text", "filters": [], "orderBy": [], "freshness": {}}
        for template in (self.command, self.query):
            for position in POSITIONS:
                for field, value in fields.items():
                    with self.subTest(kind=template["kind"], position=position, field=field):
                        document, step, pointer = self._step_at(template, position)
                        step["expectedGateway"]["body"][field] = value
                        self._assert_rejected(document, f"{pointer}/expectedGateway/body/{field}")

    def test_expected_paging_matches_integer_types_at_every_call_position(self) -> None:
        for position in POSITIONS:
            for field, integer in (("pageSize", 1), ("offset", 0), ("offset", 1)):
                for expected in (None, {}, {field: bool(integer)}, {field: float(integer)}, {field: integer}):
                    with self.subTest(position=position, field=field, expected=expected):
                        document, step, pointer = self._step_at(self.query, position)
                        step["envelope"].pop("pageSize", None)
                        step["envelope"][field] = integer
                        step["expectedGateway"]["body"]["paging"] = expected
                        if isinstance(expected, dict) and type(expected.get(field)) is int:
                            self.assertEqual([], self._validate(document))
                        else:
                            self._assert_rejected(document, f"{pointer}/expectedGateway/body/paging")

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
        for version in (0, -1, 2, "1", 1.0, True, None):
            with self.subTest(version=version):
                document = copy.deepcopy(self.command)
                document["formatVersion"] = version
                self._assert_rejected(document, "/formatVersion")
        del self.command["formatVersion"]
        self._assert_rejected(self.command, "'formatVersion' is a required property")

    def test_unreadable_or_invalid_artifact_is_reported_without_loading_assemblies(self) -> None:
        self.artifact.write_bytes(b"not a zip")
        self._assert_rejected(self.command, f"{self.artifact}:/: cannot read NuGet release artifact")
        with zipfile.ZipFile(self.artifact, "w") as archive:
            archive.writestr("nested/sample.nuspec", "<package/>")
        self._assert_rejected(self.command, f"{self.artifact}:/: expected exactly one root .nuspec")
        for nuspec, reason in (("<package/>", ".nuspec /metadata is missing"),
                               ("<package><metadata><id>Sample</id></metadata></package>",
                                ".nuspec /metadata/id and /metadata/version are required")):
            with self.subTest(reason=reason):
                with zipfile.ZipFile(self.artifact, "w") as archive:
                    archive.writestr("sample.nuspec", nuspec)
                self._assert_rejected(self.command, f"{self.artifact}:/metadata: {reason}")

    def test_cli_accepts_all_three_samples(self) -> None:
        result = self._cli([HERE / "sample-command.json", HERE / "sample-query.json", HERE / "sample-rename.json"])
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Validated 3 vector(s)", result.stdout)
        self.assertEqual("", result.stderr)

    def test_json_syntax_and_parser_limits_return_identical_cli_and_api_findings(self) -> None:
        cases = [
            ('{"formatVersion":', "line 1 column"),
            ('[1,]', "line 1 column"),
            ('[' * (sys.getrecursionlimit() + 100) + '0' + ']' * (sys.getrecursionlimit() + 100),
             "maximum recursion depth exceeded"),
        ]
        digit_limit = getattr(sys, "get_int_max_str_digits", lambda: 0)()
        if digit_limit:
            cases.append(('{"number":' + '9' * (digit_limit + 1) + '}', "integer string conversion"))
        source = self.directory / "malformed.json"
        for raw, reason in cases:
            with self.subTest(reason=reason):
                source.write_text(raw, encoding="utf-8")
                findings = validate_vectors([source], self.artifact, PACKAGE)
                self.assertEqual(1, len(findings), findings)
                self.assertTrue(findings[0].startswith(f"{source}:/:"), findings)
                self.assertIn(reason, findings[0])
                result = self._cli([source])
                self.assertEqual(1, result.returncode, result.stderr)
                self.assertEqual("", result.stdout)
                self.assertEqual(findings, result.stderr.splitlines())
                self.assertNotIn("Traceback", result.stderr)

    def test_cli_and_reusable_entry_point_return_identical_located_rejections(self) -> None:
        cases = []
        for version in (1.0, True):
            malformed = copy.deepcopy(self.command)
            malformed["formatVersion"] = version
            cases.append((malformed, PACKAGE))
        malformed = copy.deepcopy(self.query)
        malformed["invocation"]["envelope"]["pageSize"] = 1
        malformed["invocation"]["expectedGateway"]["body"]["paging"]["pageSize"] = True
        cases.append((malformed, PACKAGE))
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
