"""Exercise documentary guards through the actual verifier process/channels."""

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("verify_class_map.py").resolve()
SPEC = importlib.util.spec_from_file_location("class_map_verifier", SCRIPT)
VERIFIER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFIER)
REPOSITORY = SCRIPT.parents[4]
MAP = Path("_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/AD-23-capability-class-map.json")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ProcessFixture(unittest.TestCase):
    """All rejection assertions inspect exit status, stdout and stderr."""

    def temporary_root(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def save(self, document=None, bind_receipt=True):
        document = self.document if document is None else document
        self.map_path.write_text(json.dumps(document), encoding="utf-8")
        if bind_receipt:
            artifacts = {
                document["decision"]["path"]: digest(self.root / document["decision"]["path"]),
                self.map_path.relative_to(self.root).as_posix(): digest(self.map_path),
                **{item["path"]: digest(self.root / item["path"]) for item in document["inventories"]},
            }
            self.receipt["artifacts"] = artifacts
        (self.root / document["approvalPath"]).write_text(json.dumps(self.receipt), encoding="utf-8")

    def process(self, text=True):
        return subprocess.run(
            [sys.executable, "-I", "-B", str(SCRIPT), "--root", str(self.root), "--map", str(self.map_path)],
            text=text, capture_output=True, check=False, timeout=30,
        )

    def run_map(self, document=None, bind_receipt=True):
        self.save(document, bind_receipt)
        return self.process()

    def reject_result(self, message, result):
        """Pin the whole failure document so a later guard cannot stand in."""
        self.assertEqual(1, result.returncode, result)
        self.assertEqual("", result.stdout)
        self.assertEqual(f"FAIL: {message}\n", result.stderr)

    def reject(self, message, document=None, bind_receipt=True):
        self.reject_result(message, self.run_map(document, bind_receipt))


class ClassMapTests(ProcessFixture):
    """Synthetic sources ensure policy is independent of names and counts."""

    def setUp(self):
        self.temporary_root()
        self.inventory = self.root / "inventory.md"
        self.inventory.write_text(
            "---\ninventory_version: '1.0.0'\n---\n\n"
            "| ID | Capability | Security class |\n| --- | --- | --- |\n"
            "| R1 | plain read with escaped \\| character | read |\n"
            "| R2 | protected action | UI-only |\n"
            "| R3 | protected action | Confirmation-required |\n"
            "| R4 | protected action | Destructive write |\n"
            "| R5 | local source apply | Local file mutation when applied |\n"
            "| V1 | explicit apply | variant |\n"
            "| N1 | absence finding | no executable capability |\n\n"
            "| Gate | Owner |\n| --- | --- |\n| G1 | owner role |\n\n"
            "| Gap | Owner |\n| --- | --- |\n| G2 | owner role |\n\n"
            "| ID / legacy rows | Observed behavior |\n| --- | --- |\n| C1 / R1 | compatibility |\n\n"
            "| Related row | Other row |\n| --- | --- |\n| R1 | R2 |\n",
            encoding="utf-8",
        )
        self.document = {
            "schemaVersion": "1.0.0", "decision": {"path": "decision.md", "sha256": ""},
            "approvalPath": "approval.json",
            "classes": [
                {"id": "read", "outcome": "decorated-gateway-contract"},
                {"id": "ui", "outcome": "confidential-ui-only"},
                {"id": "local", "outcome": "exempt-local-tooling"},
                {"id": "later", "outcome": "continued-deferral", "gap": "transport gap", "ownerRole": "product owner"},
            ],
            "inventories": [{
                "path": "inventory.md", "version": "1.0.0", "sha256": digest(self.inventory),
                "approvalLimit": "Session scope only.",
                "rows": [{"id": i, "classId": c} for i, c in [
                    ("R1", "read"), ("R2", "ui"), ("R3", "ui"), ("R4", "ui"),
                    ("R5", "local"), ("V1", "local"), ("C1", "read")]],
                "records": [{"id": i, "kind": "bookkeeping", "reason": "source absence or gap", "governingRule": "retained scope"}
                            for i in ("N1", "G1", "G2")],
                "restrictionEvidence": [{"id": "V1", "sourceText": "explicit apply"}],
            }],
        }
        self.policy = {
            "schemaVersion": "1.0.0", "mapPath": "map.json", "approvalPath": "approval.json",
            "requiredApprovalRoles": ["product owner", "security owner"],
            "classes": copy.deepcopy(self.document["classes"]),
            "inventories": [{
                **{key: self.document["inventories"][0][key] for key in ("path", "version", "sha256", "approvalLimit")},
                "rowClasses": {row["id"]: row["classId"] for row in self.document["inventories"][0]["rows"]},
                "eligibleRecords": [{key: value for key, value in r.items() if key != "reason"}
                                    for r in self.document["inventories"][0]["records"]],
                "requiredRestrictions": [{"id": "V1", "sourceText": "explicit apply"}],
            }],
        }
        self.receipt = {"decision": "pending", "approver": None, "exactApprovalInstruction": None, "rolesCovered": []}
        self.map_path = self.root / "map.json"
        self.save_policy()

    def save_policy(self):
        (self.root / "decision.md").write_text(
            "---\nstatus: proposed\n---\n\nEffective status comes only from the separate receipt.\n"
            "<!-- capability-verifier-policy -->\n```json\n" + json.dumps(self.policy) +
            "\n```\n<!-- /capability-verifier-policy -->\n", encoding="utf-8",
        )
        self.document["decision"]["sha256"] = digest(self.root / "decision.md")

    def bind_source(self):
        """Rebind only the synthetic source, leaving its version policy explicit."""
        for inventory in (self.document["inventories"][0], self.policy["inventories"][0]):
            inventory["sha256"] = digest(self.inventory)
        self.save_policy()

    def test_input_paths_require_nonblank_existing_files(self):
        for value, message in (("", "missing input path"), ("absent.md", "missing input: absent.md")):
            with self.subTest(value=value):
                damaged = copy.deepcopy(self.document)
                damaged["inventories"][0]["path"] = value
                self.reject(message, damaged, bind_receipt=False)

    def test_class_declarations_require_array_and_nonblank_ids(self):
        damaged = copy.deepcopy(self.document)
        damaged["classes"] = {}
        self.reject("classes: expected array", damaged)
        for value in (None, "", " "):
            with self.subTest(value=value):
                damaged = copy.deepcopy(self.document)
                damaged["classes"][0]["id"] = value
                self.reject("classes: missing id", damaged)

    def test_non_object_json_items_use_fail_channel(self):
        self.document["classes"][0] = "read"
        self.reject("'str' object has no attribute 'get'")
        self.save()
        self.map_path.write_text("null", encoding="utf-8")
        self.reject_result("'NoneType' object has no attribute 'get'", self.process())

    def test_inventory_source_requires_version_and_rows(self):
        original = self.inventory.read_text()
        self.inventory.write_text(original.replace("inventory_version:", "other_version:"))
        self.bind_source()
        self.reject("inventory.md: inventory_version missing")
        self.inventory.write_text("---\ninventory_version: '1.0.0'\n---\n")
        self.bind_source()
        self.reject("inventory.md: no inventory rows")

    def test_source_version_must_match_both_bound_versions(self):
        self.inventory.write_text(self.inventory.read_text().replace("'1.0.0'", "'9.0.0'"))
        self.bind_source()
        self.reject("inventory.md: inventory version mismatch")

    def test_rebound_inventory_hash_must_still_match_decision(self):
        self.inventory.write_bytes(self.inventory.read_bytes() + b"\n")
        self.document["inventories"][0]["sha256"] = digest(self.inventory)
        self.reject("inventory.md: inventory hash mismatch")

    def test_rebound_inventory_version_must_still_match_decision(self):
        self.inventory.write_text(self.inventory.read_text(encoding="utf-8").replace("'1.0.0'", "'9.0.0'"),
                                  encoding="utf-8")
        self.document["inventories"][0]["version"] = "9.0.0"
        self.bind_source()
        self.reject("inventory.md: inventory version mismatch")

    def test_map_and_policy_schema_versions_are_checked(self):
        damaged = copy.deepcopy(self.document)
        damaged["schemaVersion"] = "9.0.0"
        self.reject("unsupported map schemaVersion", damaged)
        self.policy["schemaVersion"] = "9.0.0"
        self.save_policy()
        self.reject("unsupported decision policy schemaVersion")

    def test_decision_requires_exactly_one_policy_block(self):
        self.save_policy()
        path = self.root / "decision.md"
        original = path.read_text()
        for text in ("no policy\n", original + original):
            with self.subTest(blocks=text.count("<!-- capability-verifier-policy -->")):
                path.write_text(text)
                self.document["decision"]["sha256"] = digest(path)
                self.reject("decision must bind exactly one verifier policy")

    def test_decision_map_and_approval_paths_must_match(self):
        for key, other_path, message in (
            ("mapPath", "other-map.json", "map path disagrees with decision"),
            ("approvalPath", "other-approval.json", "approval path disagrees with decision"),
        ):
            with self.subTest(key=key):
                prior = self.policy[key]
                try:
                    (self.root / other_path).write_text("{}")
                    self.policy[key] = other_path
                    self.save_policy()
                    self.reject(message)
                finally:
                    self.policy[key] = prior

    def test_empty_agreed_class_and_inventory_sets_are_rejected(self):
        original = copy.deepcopy(self.document)
        original_policy = copy.deepcopy(self.policy)
        self.document["classes"] = self.policy["classes"] = []
        self.save_policy()
        self.reject("no capability classes")
        self.document, self.policy = original, original_policy
        self.document["inventories"] = self.policy["inventories"] = []
        self.save_policy()
        self.reject("no inventories")

    def test_inventories_require_array(self):
        self.document["inventories"] = {}
        self.reject("inventories: expected array", bind_receipt=False)

    def test_policy_side_outcome_and_transport_are_rejected(self):
        for value in (None, [], ["withdrawal", "confidential-ui-only"], "invented", "generic-authenticated-transport"):
            with self.subTest(value=value):
                self.policy["classes"][0]["outcome"] = value
                self.save_policy()
                message = ("read: transport beyond v1" if value == "generic-authenticated-transport"
                           else f"read: invalid sole outcome {value!r}")
                self.reject(message)

    def test_decision_records_must_exist_in_source(self):
        self.policy["inventories"][0]["eligibleRecords"].append({"id": "Z99"})
        self.save_policy()
        self.reject("inventory.md: decision record absent from source")

    def test_decision_row_classes_must_match_source_operations(self):
        for value in ({}, []):
            with self.subTest(value=value):
                self.policy["inventories"][0]["rowClasses"] = value
                self.save_policy()
                self.reject("inventory.md: decision row class set disagrees with source operations")

    def test_decision_restrictions_require_known_rows_and_source_evidence(self):
        evidence = self.policy["inventories"][0]["requiredRestrictions"][0]
        evidence["id"] = "Z99"
        self.save_policy()
        self.reject("inventory.md: unknown restricted row Z99")
        evidence.update(id="V1", sourceText="invented")
        self.save_policy()
        self.reject("inventory.md: V1 restriction evidence missing from source")

    def test_supplementary_restriction_requires_known_source_row(self):
        self.document["inventories"][0]["restrictionEvidence"][0]["id"] = "Z99"
        self.reject("inventory.md: unknown restricted row Z99")

    def test_agreed_record_requires_governing_reference(self):
        for record in (self.document["inventories"][0]["records"][0],
                       self.policy["inventories"][0]["eligibleRecords"][0]):
            del record["governingRule"]
        self.save_policy()
        self.reject("inventory.md: N1: record lacks governing reference")

    def test_agreed_restricted_records_require_restricted_class(self):
        for row_id in ("R2", "V1"):
            for class_id in ("read", None):
                with self.subTest(row_id=row_id, class_id=class_id):
                    original, original_policy = copy.deepcopy(self.document), copy.deepcopy(self.policy)
                    try:
                        inventory, policy_inventory = self.document["inventories"][0], self.policy["inventories"][0]
                        inventory["rows"] = [r for r in inventory["rows"] if r["id"] != row_id]
                        del policy_inventory["rowClasses"][row_id]
                        record = {"id": row_id, "kind": "fixture", "reason": "fixture", "governingRule": "fixture"}
                        if class_id is not None:
                            record["classId"] = class_id
                        inventory["records"].append(record)
                        policy_inventory["eligibleRecords"].append({k: v for k, v in record.items() if k != "reason"})
                        self.save_policy()
                        message = (f"inventory.md: {row_id}: restricted row has no class" if class_id is None
                                   else f"inventory.md: {row_id}: restricted row leaks into read")
                        self.reject(message)
                    finally:
                        self.document, self.policy = original, original_policy

    def test_missing_explicit_record_has_record_set_diagnostic(self):
        self.document["inventories"][0]["records"].pop(0)
        self.reject("inventory.md: non-operation record set disagrees with decision; missing: N1; extra: ")

    def test_receipt_decision_rejects_unknown_values(self):
        for value in (None, "rejected", "", "ADOPTED"):
            with self.subTest(value=value):
                self.receipt["decision"] = value
                self.reject("invalid approval decision")

    def test_complete_partition_prints_inventory_counts(self):
        result = self.run_map()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(
            "PASS: inventory.md: 7 classified rows + 3 non-operation records = 10\n"
            "PASS: exact-byte partition verified; effective decision status: proposed; parity remains a separate gate\n",
            result.stdout,
        )
        self.assertEqual("", result.stderr)

    def test_missing_row_names_inventory_and_id(self):
        self.document["inventories"][0]["rows"].pop(0)
        self.reject("inventory.md: missing rows R1")

    def test_duplicate_row_and_cross_section_duplicate_are_rejected(self):
        for section in ("rows", "records"):
            with self.subTest(section=section):
                damaged = copy.deepcopy(self.document)
                damaged["inventories"][0][section].append({"id": "R1", "classId": "read"})
                self.reject("inventory.md: R1: duplicate mapped row", damaged)

    def test_unknown_row_names_inventory_and_id(self):
        self.document["inventories"][0]["rows"].append({"id": "Z99", "classId": "read"})
        self.reject("inventory.md: Z99: unknown row")

    def test_stale_inventory_hash_is_rejected(self):
        self.inventory.write_bytes(self.inventory.read_bytes() + b"changed\n")
        self.reject("inventory.md: inventory hash mismatch")

    def test_stale_version_and_decision_hash_are_rejected(self):
        damaged = copy.deepcopy(self.document)
        damaged["inventories"][0]["version"] = "9.0.0"
        self.reject("inventory.md: inventory version mismatch", damaged)
        self.document["decision"]["sha256"] = "0" * 64
        self.reject("decision hash mismatch")

    def test_zero_two_and_unlisted_outcomes_are_rejected(self):
        for value in (None, [], ["withdrawal", "confidential-ui-only"], "invented", "generic-authenticated-transport"):
            with self.subTest(value=value):
                damaged = copy.deepcopy(self.document)
                if value is None:
                    del damaged["classes"][0]["outcome"]
                else:
                    damaged["classes"][0]["outcome"] = value
                message = ("read: transport beyond v1" if value == "generic-authenticated-transport"
                           else f"read: invalid sole outcome {value!r}")
                self.reject(message, damaged)

    def test_outcome_and_required_class_set_must_match_decision(self):
        damaged = copy.deepcopy(self.document)
        damaged["classes"][3]["outcome"] = "withdrawal"
        self.reject("later: class outcome/deferral disagrees with decision", damaged)
        damaged["classes"].pop()
        self.reject("class set disagrees with decision", damaged)
        damaged["classes"].append({"id": "extra", "outcome": "withdrawal"})
        self.reject("class set disagrees with decision", damaged)

    def test_restricted_source_classes_and_variant_evidence_block_admission(self):
        for row_id in ("R2", "R3", "R4", "R5", "V1"):
            with self.subTest(row_id=row_id):
                damaged = copy.deepcopy(self.document)
                next(r for r in damaged["inventories"][0]["rows"] if r["id"] == row_id)["classId"] = "read"
                self.reject(f"inventory.md: {row_id}: restricted row leaks into read", damaged)

    def test_inherited_restriction_survives_deleted_map_owned_evidence(self):
        inventory = self.document["inventories"][0]
        del inventory["restrictionEvidence"]
        next(r for r in inventory["rows"] if r["id"] == "V1")["classId"] = "read"
        self.reject("inventory.md: V1: restricted row leaks into read")

    def test_restricted_row_cannot_take_decision_agreed_deferral(self):
        inventory, policy_inventory = self.document["inventories"][0], self.policy["inventories"][0]
        next(row for row in inventory["rows"] if row["id"] == "R2")["classId"] = "later"
        policy_inventory["rowClasses"]["R2"] = "later"
        self.save_policy()
        self.reject("inventory.md: R2: restricted row leaks into later")

    def test_effect_column_alone_requires_restricted_outcome(self):
        self.check_restriction_column("Effect", "Destructive write")

    def test_confirmation_column_alone_requires_restricted_outcome(self):
        self.check_restriction_column("Confirmation", "Confirmation-required")

    def check_restriction_column(self, column, classification):
        # R1 retains the decision's admitted class: only the source-column
        # guard can reject it, rather than the row-membership comparison.
        text = self.inventory.read_text().replace("Security class", column)
        text = text.replace("character | read |", f"character | {classification} |")
        self.inventory.write_text(text)
        for inventory in (self.document["inventories"][0], self.policy["inventories"][0]):
            inventory["sha256"] = digest(self.inventory)
        self.save_policy()
        self.reject("inventory.md: R1: restricted row leaks into read")

    def test_unrestricted_operation_cannot_be_laundered_as_record(self):
        inventory = self.document["inventories"][0]
        inventory["rows"] = [r for r in inventory["rows"] if r["id"] != "R1"]
        inventory["records"].append({"id": "R1", "kind": "bookkeeping", "reason": "fake", "governingRule": "fake"})
        self.reject("inventory.md: R1: not an eligible non-operation record")

    def test_restricted_operation_cannot_be_laundered_as_record(self):
        inventory = self.document["inventories"][0]
        inventory["rows"] = [r for r in inventory["rows"] if r["id"] != "R2"]
        inventory["records"].append({"id": "R2", "kind": "bookkeeping", "reason": "fake", "governingRule": "fake"})
        self.reject("inventory.md: R2: not an eligible non-operation record")

    def test_deferred_class_needs_nonblank_gap_and_owner_role(self):
        for field in ("gap", "ownerRole"):
            for value in (None, "", "  "):
                with self.subTest(field=field, value=value):
                    damaged = copy.deepcopy(self.document)
                    if value is None:
                        del damaged["classes"][3][field]
                    else:
                        damaged["classes"][3][field] = value
                    self.reject(f"later: deferral lacks {field}", damaged)

    def test_changed_deferral_owner_or_gap_disagrees_with_decision(self):
        for field in ("gap", "ownerRole"):
            with self.subTest(field=field):
                damaged = copy.deepcopy(self.document)
                damaged["classes"][3][field] = "another value"
                self.reject("later: class outcome/deferral disagrees with decision", damaged)

    def test_duplicate_inventory_class_and_unknown_class_are_rejected(self):
        damaged = copy.deepcopy(self.document)
        damaged["inventories"].append(copy.deepcopy(damaged["inventories"][0]))
        self.reject("duplicate inventory inventory.md", damaged)
        damaged = copy.deepcopy(self.document)
        damaged["classes"].append(copy.deepcopy(damaged["classes"][0]))
        self.reject("classes: duplicate read", damaged)
        self.document["inventories"][0]["rows"][0]["classId"] = "unknown"
        self.reject("inventory.md: R1: unknown class 'unknown'")

    def test_inventory_aliases_are_detected_after_normalization(self):
        (self.root / "subdir").mkdir()
        for alias in ("./inventory.md", "subdir/../inventory.md"):
            with self.subTest(alias=alias):
                damaged = copy.deepcopy(self.document)
                duplicate = copy.deepcopy(damaged["inventories"][0])
                duplicate["path"] = alias
                damaged["inventories"].append(duplicate)
                self.reject("duplicate inventory inventory.md", damaged)

    def test_whole_inventory_omission_and_extra_inventory_are_rejected(self):
        damaged = copy.deepcopy(self.document)
        damaged["inventories"] = []
        self.reject("inventory set disagrees with decision; missing: inventory.md; extra: ", damaged)
        (self.root / "extra.md").write_bytes(self.inventory.read_bytes())
        extra = copy.deepcopy(damaged)
        extra["inventories"] = [copy.deepcopy(self.document["inventories"][0])]
        extra["inventories"][0]["path"] = "extra.md"
        self.reject("inventory set disagrees with decision; missing: inventory.md; extra: extra.md", extra)

    def test_record_requires_reason_and_decision_governing_policy(self):
        damaged = copy.deepcopy(self.document)
        del damaged["inventories"][0]["records"][0]["reason"]
        self.reject("inventory.md: N1: incomplete non-operation record", damaged)
        self.document["inventories"][0]["records"][0]["governingRule"] = "changed rule"
        self.reject("inventory.md: N1: record governing policy disagrees with decision")

    def test_record_kind_must_match_decision(self):
        self.document["inventories"][0]["records"][0]["kind"] = "changed kind"
        self.reject("inventory.md: N1: record governing policy disagrees with decision")

    def test_declared_governing_reference_must_resolve(self):
        for record in (self.policy["inventories"][0]["eligibleRecords"][0], self.document["inventories"][0]["records"][0]):
            del record["governingRule"]
            record["governedBy"] = [{"inventory": "inventory.md", "id": "Z99"}]
        self.save_policy()
        self.reject("inventory.md: N1: unresolved governing reference ('inventory.md', 'Z99')")

    def test_record_cannot_be_reclassified_as_operation(self):
        inventory = self.document["inventories"][0]
        inventory["records"].pop(0)
        inventory["rows"].append({"id": "N1", "classId": "read"})
        self.reject("inventory.md: N1: decision requires a non-operation record")

    def test_restriction_evidence_must_exist_at_named_source_row(self):
        self.document["inventories"][0]["restrictionEvidence"][0]["sourceText"] = "invented evidence"
        self.reject("inventory.md: V1 restriction evidence missing from source")

    def test_duplicate_source_id_is_rejected_but_relation_table_is_not_a_row(self):
        self.inventory.write_text(self.inventory.read_text() + "\n| ID | Capability |\n| --- | --- |\n| R1 | duplicate |\n")
        for inventory in (self.document["inventories"][0], self.policy["inventories"][0]):
            inventory["sha256"] = digest(self.inventory)
        self.save_policy()
        self.reject("inventory.md: duplicate source row R1")

    def test_paths_cannot_escape_repository(self):
        for path in ("../inventory.md", str(self.inventory)):
            with self.subTest(path=path):
                damaged = copy.deepcopy(self.document)
                damaged["inventories"][0]["path"] = path
                message = (f"absolute input path: {path}" if Path(path).is_absolute()
                           else f"input path escapes root: {path}")
                self.reject(message, damaged, bind_receipt=False)

    def test_duplicate_json_members_are_rejected_by_process(self):
        self.save()
        self.map_path.write_text('{"outcome":"withdrawal","outcome":"confidential-ui-only"}')
        result = self.process()
        self.reject_result("duplicate JSON member outcome", result)

    def test_duplicate_decision_policy_members_are_rejected_by_process(self):
        path = self.root / "decision.md"
        path.write_text(path.read_text(encoding="utf-8").replace(
            '"schemaVersion": "1.0.0"', '"schemaVersion": "1.0.0", "schemaVersion": "1.0.0"', 1),
            encoding="utf-8")
        self.document["decision"]["sha256"] = digest(path)
        self.reject("duplicate JSON member schemaVersion")

    def test_duplicate_receipt_members_are_rejected_by_process(self):
        self.save()
        path = self.root / self.document["approvalPath"]
        path.write_text(path.read_text(encoding="utf-8").replace(
            '"decision": "pending"', '"decision": "pending", "decision": "pending"', 1),
            encoding="utf-8")
        self.reject_result("duplicate JSON member decision", self.process())

    def approve(self):
        self.receipt.update(decision="approved", approver="fixture owner", exactApprovalInstruction="approve fixture bytes",
                            rolesCovered=["product owner", "security owner"])

    def test_approval_requires_nonblank_typed_owner_and_instruction(self):
        self.approve()
        for field in ("approver", "exactApprovalInstruction"):
            for value in (None, "", " \t\n", True, ["owner"], 1):
                with self.subTest(field=field, value=value):
                    prior = self.receipt[field]
                    try:
                        self.receipt[field] = value
                        self.reject(f"adoption approval lacks nonblank {field}")
                    finally:
                        self.receipt[field] = prior

    def test_approval_requires_array_of_nonblank_roles_and_all_bound_roles(self):
        self.approve()
        for value in (None, "product owner", {"product owner": True}, [" "], [1], [True], ["product owner", ""]):
            with self.subTest(value=value):
                self.receipt["rolesCovered"] = value
                self.reject("adoption rolesCovered must be an array of nonblank strings")
        for value in ([], ["unrelated owner"], ["product owner"], ["security owner"]):
            with self.subTest(value=value):
                self.receipt["rolesCovered"] = value
                self.receipt["rolesRequiringConfirmation"] = value
                self.reject("adoption approval lacks required roles from decision")

    def test_pending_candidate_requires_nonblank_role_policy(self):
        for value in (None, [], "owner", {"owner": True}, [""], [" \t\n"], [True], [1]):
            with self.subTest(value=value):
                self.policy["requiredApprovalRoles"] = value
                self.save_policy()
                self.reject("decision lacks required approval roles")
        del self.policy["requiredApprovalRoles"]
        self.save_policy()
        self.reject("decision lacks required approval roles")

    def test_receipt_artifact_binding_is_required_for_pending_and_adopted(self):
        for state in ("pending", "approved"):
            with self.subTest(state=state):
                if state == "approved":
                    self.approve()
                self.receipt["artifacts"] = {}
                self.reject("approval artifact binding mismatch", bind_receipt=False)

    def test_effective_adoption_changes_only_receipt(self):
        result = self.run_map()
        self.assertEqual(0, result.returncode, result.stderr)
        before = {p: p.read_bytes() for p in (self.map_path, self.root / "decision.md")}
        self.approve()
        result = self.run_map()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stderr)
        self.assertIn("effective decision status: adopted", result.stdout)
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_map_cannot_declare_its_own_adoption_status(self):
        self.document["decision"]["status"] = "adopted"
        self.reject("decision status belongs only to the approval receipt")


class ActualPacketRegressionTests(ProcessFixture):
    """Reproduce review attacks against the actual proposed packet."""

    def setUp(self):
        self.temporary_root()
        self.document = json.loads((REPOSITORY / MAP).read_text(encoding="utf-8"))
        self.map_path = self.root / MAP
        for relative in [MAP.as_posix(), self.document["decision"]["path"], self.document["approvalPath"],
                         *[item["path"] for item in self.document["inventories"]]]:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPOSITORY / relative, target)
        self.receipt = json.loads((self.root / self.document["approvalPath"]).read_text(encoding="utf-8"))

    def inventory(self, prefix):
        return next(item for item in self.document["inventories"] if Path(item["path"]).name.startswith(prefix))

    def test_actual_packet_complete(self):
        result = self.process(text=False)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(b"", result.stderr)
        self.assertEqual(SCRIPT.with_name("verifier.stdout.txt").read_bytes(), result.stdout)

    def test_actual_admin_ac13_cannot_move_to_owner_held_migration_class(self):
        inventory = self.inventory("eventstore-admin-")
        next(row for row in inventory["rows"] if row["id"] == "AC13")["classId"] = "K14"
        self.reject(f"{inventory['path']}: AC13: row class disagrees with decision")

    def test_actual_folders_v04_cannot_bypass_staging_deferral(self):
        inventory = self.inventory("folders-")
        next(row for row in inventory["rows"] if row["id"] == "V04")["classId"] = "K01"
        self.reject(f"{inventory['path']}: V04: row class disagrees with decision")

    def test_actual_session_approval_cannot_claim_owning_maintainer(self):
        inventory = self.inventory("projects-")
        inventory["approvalLimit"] = "Approved owning-maintainer inventory."
        self.reject(f"{inventory['path']}: approval limit disagrees with decision")

    def test_actual_folders_c01_record_class_cannot_change(self):
        inventory = self.inventory("folders-")
        next(row for row in inventory["records"] if row["id"] == "C01")["classId"] = "K13"
        self.reject(f"{inventory['path']}: C01: record governing policy disagrees with decision")

    def test_actual_technical_ps09_governing_row_cannot_change(self):
        inventory = self.inventory("technical-tools-")
        next(row for row in inventory["records"] if row["id"] == "PS09")["governedBy"][0]["id"] = "L01"
        self.reject(f"{inventory['path']}: PS09: record governing policy disagrees with decision")

    def test_actual_whole_technical_inventory_omission_is_rejected(self):
        inventory = self.inventory("technical-tools-")
        self.document["inventories"].remove(inventory)
        self.reject(f"inventory set disagrees with decision; missing: {inventory['path']}; extra: ")

    def test_actual_ps14_cannot_be_admitted_after_removing_all_map_restrictions(self):
        for inventory in self.document["inventories"]:
            inventory.pop("restrictionEvidence", None)
        inventory = self.inventory("technical-tools-")
        next(row for row in inventory["rows"] if row["id"] == "PS14")["classId"] = "K01"
        self.reject(f"{inventory['path']}: PS14: restricted row leaks into K01")

    def test_actual_parties_t01_cannot_become_record(self):
        inventory = self.inventory("parties-")
        inventory["rows"] = [row for row in inventory["rows"] if row["id"] != "T01"]
        inventory["records"].append({"id": "T01", "kind": "bookkeeping", "reason": "fake", "governingRule": "fake"})
        self.reject(f"{inventory['path']}: T01: not an eligible non-operation record")

    def test_actual_k09_cannot_disagree_with_deferred_decision(self):
        next(item for item in self.document["classes"] if item["id"] == "K09")["outcome"] = "withdrawal"
        self.reject("K09: class outcome/deferral disagrees with decision")

    def test_actual_parties_mixed_variants_inherit_restrictions(self):
        for row_id in ("C03", "C04", "C05"):
            with self.subTest(row_id=row_id):
                damaged = copy.deepcopy(self.document)
                inventory = next(item for item in damaged["inventories"] if Path(item["path"]).name.startswith("parties-"))
                inventory.pop("restrictionEvidence", None)
                next(row for row in inventory["rows"] if row["id"] == row_id)["classId"] = "K01"
                self.reject(f"{inventory['path']}: {row_id}: restricted row leaks into K01", damaged)

    def test_actual_technical_path_alias_cannot_double_count(self):
        duplicate = copy.deepcopy(self.inventory("technical-tools-"))
        duplicate["path"] = "./" + duplicate["path"]
        self.document["inventories"].append(duplicate)
        self.reject(f"duplicate inventory {self.inventory('technical-tools-')['path']}")

    def test_actual_receipt_drives_adoption_without_mutating_candidate(self):
        self.save()
        candidates = [self.map_path, self.root / self.document["decision"]["path"]]
        before = [p.read_bytes() for p in candidates]
        policy = VERIFIER.parse_json(VERIFIER.POLICY.findall(candidates[1].read_text(encoding="utf-8"))[0])
        self.receipt.update(decision="approved", approver="synthetic regression owner",
                            exactApprovalInstruction="fixture only; no actual approval authority",
                            rolesCovered=policy["requiredApprovalRoles"])
        result = self.run_map()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stderr)
        self.assertIn("effective decision status: adopted", result.stdout)
        self.assertEqual(before, [p.read_bytes() for p in candidates])


if __name__ == "__main__":
    unittest.main()
