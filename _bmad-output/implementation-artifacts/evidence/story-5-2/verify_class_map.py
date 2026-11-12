#!/usr/bin/env python3
"""Verify a documentary partition against policy bound by its decision.

Inventory identities, class outcomes, restrictions, record eligibility and
approval roles come from the decision, never from module names/counts in code.
The separate receipt determines effective adoption without rewriting artifacts.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


OUTCOMES = frozenset({
    "decorated-gateway-contract", "generic-authenticated-transport",
    "exempt-local-tooling", "confidential-ui-only", "withdrawal",
    "continued-deferral",
})
RESTRICTED_OUTCOMES = frozenset({
    "confidential-ui-only", "exempt-local-tooling", "withdrawal",
})
ROW_ID = re.compile(r"([A-Z]+[0-9]+)(?:\s*/.*)?\Z")
RESTRICTED = re.compile(
    r"\b(?:ui-only|confirmation-required|destructive|privacy-destructive|local file mutation)\b",
    re.IGNORECASE,
)
POLICY = re.compile(
    r"<!-- capability-verifier-policy -->\s*```json\n(.*?)\n```\s*"
    r"<!-- /capability-verifier-policy -->", re.DOTALL,
)


class InvalidMap(ValueError):
    """A damaged or incomplete documentary partition."""


def require(condition, message):
    """Fail with an actionable diagnostic."""
    if not condition:
        raise InvalidMap(message)


def nonblank(value):
    """Require text, not merely a truthy JSON value."""
    return isinstance(value, str) and bool(value.strip())


def sha256(path):
    """Hash exact bytes."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def parse_json(text):
    """Reject duplicate members instead of silently keeping the last."""
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, f"duplicate JSON member {key}")
            result[key] = value
        return result
    return json.loads(text, object_pairs_hook=unique_object)


def read_json(path):
    """Read a JSON artifact without duplicate keys."""
    return parse_json(Path(path).read_text(encoding="utf-8"))


def local_path(root, value):
    """Resolve repository-relative inputs before identity/duplicate checks."""
    require(nonblank(value), "missing input path")
    path = Path(value)
    require(not path.is_absolute(), f"absolute input path: {value}")
    resolved = (root / path).resolve()
    require(resolved.is_relative_to(root), f"input path escapes root: {value}")
    require(resolved.is_file(), f"missing input: {value}")
    return resolved


def path_key(root, value):
    """Use one identity for ./, .. and symlink aliases within the root."""
    return local_path(root, value).relative_to(root).as_posix()


def indexed(items, label, key="id"):
    """Index declarations without accepting duplicates."""
    require(isinstance(items, list), f"{label}: expected array")
    result = {}
    for item in items:
        identity = item.get(key)
        require(nonblank(identity), f"{label}: missing {key}")
        require(identity not in result, f"{label}: duplicate {identity}")
        result[identity] = item
    return result


def inventory_rows(path):
    """Derive every ID-first source row, excluding cross-reference tables."""
    text = path.read_text(encoding="utf-8")
    version = re.search(r"^inventory_version:\s*['\"]?([^'\"\s]+)", text, re.MULTILINE)
    require(version is not None, f"{path.name}: inventory_version missing")
    rows, headers = {}, []
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.startswith("|"):
            headers = []
            continue
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", line)[1:-1]]
        if not cells or all(re.fullmatch(r":?-+:?", c.replace(" ", "")) for c in cells):
            continue
        match = ROW_ID.fullmatch(cells[0])
        if match is None:
            headers = cells
            continue
        if not headers or headers[0] not in {"ID", "Gate", "Gap", "ID / legacy rows"}:
            continue
        row_id = match[1]
        require(row_id not in rows, f"{path.name}: duplicate source row {row_id}")
        rows[row_id] = {"cells": cells, "headers": headers[:], "text": line, "line": line_number}
    require(bool(rows), f"{path.name}: no inventory rows")
    return version[1], rows


def restricted_source(row):
    """Read affirmative Effect/Confirmation/Security classes, not names."""
    for header, cell in zip(row["headers"], row["cells"]):
        header = header.lower()
        if ("security class" in header or header in {"effect", "confirmation"}) and RESTRICTED.search(cell):
            return True
    return False


def class_policy(item):
    """Select normative class fields independently bound in the decision."""
    outcome = item.get("outcome")
    require(isinstance(outcome, str) and outcome in OUTCOMES,
            f"{item['id']}: invalid sole outcome {outcome!r}")
    require(outcome != "generic-authenticated-transport", f"{item['id']}: transport beyond v1")
    result = {"outcome": outcome}
    if outcome == "continued-deferral":
        for field in ("gap", "ownerRole"):
            require(nonblank(item.get(field)), f"{item['id']}: deferral lacks {field}")
            result[field] = item[field]
    return result


def record_policy(root, entry):
    """Normalize the record's decision-owned kind and governing policy."""
    result = {field: entry[field] for field in ("kind", "classId", "governingRule") if field in entry}
    if "governedBy" in entry:
        result["governedBy"] = [
            {"inventory": path_key(root, link["inventory"]), "id": link["id"]}
            for link in entry["governedBy"]
        ]
    return result


def inventory_index(root, items, label):
    """Reject inventory aliases before comparing the expected set."""
    require(isinstance(items, list), f"{label}: expected array")
    result = {}
    for item in items:
        name = path_key(root, item["path"])
        require(name not in result, f"duplicate inventory {name}")
        result[name] = item
    return result


def verify(root, map_path):
    """Return per-input counts and the separate receipt's effective status."""
    root = Path(root).resolve()
    map_path = Path(map_path).resolve()
    document = read_json(map_path)
    require(document.get("schemaVersion") == "1.0.0", "unsupported map schemaVersion")
    decision = document["decision"]
    require("status" not in decision, "decision status belongs only to the approval receipt")
    decision_path = local_path(root, decision["path"])
    require(sha256(decision_path) == decision["sha256"], "decision hash mismatch")
    blocks = POLICY.findall(decision_path.read_text(encoding="utf-8"))
    require(len(blocks) == 1, "decision must bind exactly one verifier policy")
    policy = parse_json(blocks[0])
    require(policy.get("schemaVersion") == "1.0.0", "unsupported decision policy schemaVersion")
    required_roles = policy.get("requiredApprovalRoles")
    require(isinstance(required_roles, list) and required_roles and all(map(nonblank, required_roles)),
            "decision lacks required approval roles")
    require(path_key(root, policy["mapPath"]) == map_path.relative_to(root).as_posix(),
            "map path disagrees with decision")
    require(path_key(root, policy["approvalPath"]) == path_key(root, document["approvalPath"]),
            "approval path disagrees with decision")

    classes = indexed(document["classes"], "classes")
    expected_classes = indexed(policy["classes"], "decision classes")
    require(classes.keys() == expected_classes.keys(), "class set disagrees with decision")
    require(bool(classes), "no capability classes")
    for key, item in classes.items():
        require(class_policy(item) == class_policy(expected_classes[key]),
                f"{key}: class outcome/deferral disagrees with decision")

    inventories = inventory_index(root, document["inventories"], "inventories")
    expected_inventories = inventory_index(root, policy["inventories"], "decision inventories")
    missing = expected_inventories.keys() - inventories.keys()
    extra = inventories.keys() - expected_inventories.keys()
    require(not missing and not extra,
            f"inventory set disagrees with decision; missing: {', '.join(sorted(missing))}; extra: {', '.join(sorted(extra))}")
    require(bool(inventories), "no inventories")
    counts, all_entries, pending_links = [], {}, []
    for name, inventory in inventories.items():
        expected = expected_inventories[name]
        path = local_path(root, name)
        require(inventory["sha256"] == expected["sha256"] == sha256(path), f"{name}: inventory hash mismatch")
        version, source_rows = inventory_rows(path)
        require(inventory["version"] == expected["version"] == version, f"{name}: inventory version mismatch")
        require(nonblank(expected.get("approvalLimit")) and inventory.get("approvalLimit") == expected["approvalLimit"],
                f"{name}: approval limit disagrees with decision")
        records = indexed(expected["eligibleRecords"], f"{name} decision records")
        require(records.keys() <= source_rows.keys(), f"{name}: decision record absent from source")
        row_classes = expected["rowClasses"]
        require(isinstance(row_classes, dict) and row_classes.keys() == source_rows.keys() - records.keys(),
                f"{name}: decision row class set disagrees with source operations")
        restrictions = indexed(expected["requiredRestrictions"], f"{name} decision restrictions")
        for row_id, evidence in restrictions.items():
            require(row_id in source_rows, f"{name}: unknown restricted row {row_id}")
            quote = evidence.get("sourceText")
            require(nonblank(quote) and quote in source_rows[row_id]["text"],
                    f"{name}: {row_id} restriction evidence missing from source")
        # Map-owned evidence is only supplementary: deleting it never removes
        # a decision-required restriction or an affirmative source restriction.
        for evidence in inventory.get("restrictionEvidence", []):
            row_id = evidence["id"]
            require(row_id in source_rows, f"{name}: unknown restricted row {row_id}")
            require(nonblank(evidence.get("sourceText")) and evidence["sourceText"] in source_rows[row_id]["text"],
                    f"{name}: {row_id} restriction evidence missing from source")
            restrictions.setdefault(row_id, evidence)

        seen, actual_records = set(), set()
        for section in ("rows", "records"):
            for entry in inventory[section]:
                row_id = entry["id"]
                label = f"{name}: {row_id}"
                require(row_id in source_rows, f"{label}: unknown row")
                require(row_id not in seen, f"{label}: duplicate mapped row")
                seen.add(row_id)
                if section == "records":
                    require(row_id in records, f"{label}: not an eligible non-operation record")
                    require(nonblank(entry.get("kind")) and nonblank(entry.get("reason")),
                            f"{label}: incomplete non-operation record")
                    require(record_policy(root, entry) == record_policy(root, records[row_id]),
                            f"{label}: record governing policy disagrees with decision")
                    actual_records.add(row_id)
                else:
                    require(row_id not in records, f"{label}: decision requires a non-operation record")
                class_id = entry.get("classId")
                if section == "rows" or class_id is not None:
                    require(class_id in classes, f"{label}: unknown class {class_id!r}")
                    if restricted_source(source_rows[row_id]) or row_id in restrictions:
                        require(classes[class_id]["outcome"] in RESTRICTED_OUTCOMES,
                                f"{label}: restricted row leaks into {class_id}")
                    if section == "rows":
                        require(class_id == row_classes[row_id],
                                f"{label}: row class disagrees with decision")
                else:
                    require(entry.get("governedBy") or nonblank(entry.get("governingRule")),
                            f"{label}: record lacks governing reference")
                    require(row_id not in restrictions and not restricted_source(source_rows[row_id]),
                            f"{label}: restricted row has no class")
                all_entries[(name, row_id)] = entry
                for link in entry.get("governedBy", []):
                    pending_links.append((label, (path_key(root, link["inventory"]), link["id"])))
        missing_rows = source_rows.keys() - seen
        require(not missing_rows, f"{name}: missing rows {', '.join(sorted(missing_rows))}")
        require(actual_records == records.keys(), f"{name}: non-operation record set disagrees with decision")
        counts.append((name, len(inventory["rows"]), len(inventory["records"])))
    for label, target in pending_links:
        require(target in all_entries, f"{label}: unresolved governing reference {target}")

    receipt = read_json(local_path(root, policy["approvalPath"]))
    require(receipt.get("decision") in {"pending", "approved"}, "invalid approval decision")
    expected_artifacts = {decision_path.relative_to(root).as_posix(): sha256(decision_path),
                          map_path.relative_to(root).as_posix(): sha256(map_path),
                          **{name: item["sha256"] for name, item in inventories.items()}}
    require(receipt.get("artifacts") == expected_artifacts, "approval artifact binding mismatch")
    if receipt["decision"] == "approved":
        for field in ("approver", "exactApprovalInstruction"):
            require(nonblank(receipt.get(field)), f"adoption approval lacks nonblank {field}")
        roles = receipt.get("rolesCovered")
        require(isinstance(roles, list) and all(map(nonblank, roles)),
                "adoption rolesCovered must be an array of nonblank strings")
        require(set(required_roles) <= set(roles), "adoption approval lacks required roles from decision")
    return counts, "adopted" if receipt["decision"] == "approved" else "proposed"


def main(argv=None):
    """Buffer success output until all checks, including approval, pass."""
    root = Path(__file__).resolve().parents[4]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=root)
    parser.add_argument("--map", type=Path, default=root / "_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/AD-23-capability-class-map.json")
    args = parser.parse_args(argv)
    try:
        counts, status = verify(args.root, args.map)
    except (InvalidMap, KeyError, TypeError, ValueError, OSError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    for name, rows, records in counts:
        print(f"PASS: {name}: {rows} classified rows + {records} non-operation records = {rows + records}")
    print(f"PASS: exact-byte partition verified; effective decision status: {status}; parity remains a separate gate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
