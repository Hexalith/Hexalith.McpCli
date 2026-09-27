#!/usr/bin/env python3
"""Offline validator shared by vector authors and future conformance runners."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

try:
    from jsonschema import Draft202012Validator, validators
except ImportError as exc:
    raise SystemExit("Install test tooling with: python3 -m pip install -r tools/conformance-vectors/v1/requirements.txt") from exc


SCHEMA_PATH = Path(__file__).with_name("schema.json")
SUPPORTED_FORMAT_VERSIONS = (1,)
# Known SubmitQueryRequest fields that McpCli never sets for either operation kind.
UNSENT_REQUEST_FIELDS = ("search", "filters", "orderBy", "freshness")
# CLI integer arguments require integer JSON tokens, not integral floats or booleans.
VectorValidator = validators.extend(
    Draft202012Validator,
    type_checker=Draft202012Validator.TYPE_CHECKER.redefine("integer", lambda checker, value: type(value) is int),
)


class VectorError(ValueError):
    """A located incompatibility in a conformance vector or its release artifact."""


def _pointer(parts: Any) -> str:
    return "".join("/" + str(part).replace("~", "~0").replace("/", "~1") for part in parts) or "/"


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise VectorError(f"/: duplicate JSON field {key!r}")
        value[key] = item
    return value


def _check_finite_json(value: Any, parts: tuple[str | int, ...] = ()) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise VectorError(f"{_pointer(parts)}: nonfinite JSON number {value!r} is not supported")
    if isinstance(value, dict):
        for key, item in value.items():
            _check_finite_json(item, (*parts, key))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _check_finite_json(item, (*parts, index))


def _load_json(path: Path) -> Any:
    try:
        document = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_no_duplicate_keys)
        _check_finite_json(document)
        return document
    except VectorError as exc:
        raise VectorError(f"{path}:{exc}") from exc
    except (OSError, ValueError, RecursionError) as exc:
        raise VectorError(f"{path}:/: {exc}") from exc


def package_identity(artifact: Path) -> tuple[str, str]:
    """Read identity from the immutable nupkg, never from a project file."""
    try:
        with zipfile.ZipFile(artifact) as archive:
            nuspecs = [name for name in archive.namelist() if name.endswith(".nuspec") and "/" not in name]
            if len(nuspecs) != 1:
                raise VectorError(f"{artifact}:/: expected exactly one root .nuspec, found {len(nuspecs)}")
            root = ElementTree.fromstring(archive.read(nuspecs[0]))
    except (OSError, zipfile.BadZipFile, ElementTree.ParseError) as exc:
        raise VectorError(f"{artifact}:/: cannot read NuGet release artifact: {exc}") from exc
    metadata = next((node for node in root if node.tag.rsplit("}", 1)[-1] == "metadata"), None)
    if metadata is None:
        raise VectorError(f"{artifact}:/metadata: .nuspec /metadata is missing")
    fields = {node.tag.rsplit("}", 1)[-1]: (node.text or "").strip() for node in metadata}
    if not fields.get("id") or not fields.get("version"):
        raise VectorError(f"{artifact}:/metadata: .nuspec /metadata/id and /metadata/version are required")
    return fields["id"], fields["version"]


def _schema_errors(document: Any, source: Path, validator: Draft202012Validator) -> list[str]:
    findings: list[str] = []
    for error in sorted(validator.iter_errors(document), key=lambda item: (list(map(str, item.absolute_path)), item.message)):
        path = list(error.absolute_path)
        if error.validator == "additionalProperties":
            match = re.search(r"\('([^']+)' was unexpected\)", error.message)
            if match:
                path.append(match.group(1))
        findings.append(f"{source}:{_pointer(path)}: {error.message}")
    return findings


def _check_step(step: dict[str, Any], pointer: str, findings: list[str]) -> None:
    kind = step["kind"]
    envelope = step["envelope"]
    gateway = step["expectedGateway"]
    body = gateway["body"]
    path = "/api/v1/commands" if kind == "command" else "/api/v1/queries"
    if gateway["path"] != path:
        findings.append(f"{pointer}/expectedGateway/path: {kind} must use {path}")
    if kind == "command":
        for field in ("entityId", "pageSize", "offset", "cursor"):
            if field in envelope:
                findings.append(f"{pointer}/envelope/{field}: query-only input is invalid for a command")
        wrong_kind_fields = ("queryType", "projectionType", "projectionActorType", "entityId", "paging")
    else:
        for field in ("correlationId", "idempotencyKey", "extensions"):
            if field in envelope:
                findings.append(f"{pointer}/envelope/{field}: command-only input is invalid for a query")
        if "cursor" in envelope and "offset" in envelope:
            findings.append(f"{pointer}/envelope/cursor: cursor cannot be combined with offset")
        wrong_kind_fields = ("commandType", "messageId", "correlationId", "idempotencyKey", "extensions")
    for field in wrong_kind_fields:
        if field in body:
            findings.append(f"{pointer}/expectedGateway/body/{field}: request field is invalid for a {kind}")
    for field in UNSENT_REQUEST_FIELDS:
        if field in body:
            findings.append(f"{pointer}/expectedGateway/body/{field}: Core never sends this request field")
    if body.get("tenant") != envelope["tenant"]:
        findings.append(f"{pointer}/expectedGateway/body/tenant: must equal envelope tenant")
    for field in ("domain", "aggregateId", "commandType" if kind == "command" else "queryType"):
        if not isinstance(body.get(field), str) or not body[field].strip():
            findings.append(f"{pointer}/expectedGateway/body/{field}: required nonblank Gateway routing value")
    if not isinstance(body.get("payload"), dict):
        findings.append(f"{pointer}/expectedGateway/body/payload: expected submitted Payload object is required")
    for field in ("aggregateId", "entityId", "idempotencyKey", "extensions"):
        if field in envelope and body.get(field) != envelope[field]:
            findings.append(f"{pointer}/expectedGateway/body/{field}: must equal supplied envelope value")
    masks = gateway["maskGenerated"]
    if kind == "command" and "/messageId" not in masks:
        findings.append(f"{pointer}/expectedGateway/maskGenerated: command messageId must be marked generated")
    if "/correlationId" in masks and "correlationId" in envelope:
        findings.append(f"{pointer}/expectedGateway/maskGenerated: caller-supplied correlationId cannot be masked")
    if "/correlationId" not in masks and kind == "command" and "correlationId" not in envelope:
        findings.append(f"{pointer}/expectedGateway/maskGenerated: generated correlationId must be masked")
    if kind == "query" and masks:
        findings.append(f"{pointer}/expectedGateway/maskGenerated: query request has no generated identifiers")
    for field in masks:
        if body.get(field[1:]) != "<generated>":
            findings.append(f"{pointer}/expectedGateway/body{field}: generated identifier must use <generated> placeholder")
    if kind == "command" and "correlationId" in envelope and body.get("correlationId") != envelope["correlationId"]:
        findings.append(f"{pointer}/expectedGateway/body/correlationId: caller-supplied identifier must match exactly")
    if kind == "command" and "idempotencyKey" not in envelope and "idempotencyKey" in body:
        findings.append(f"{pointer}/expectedGateway/body/idempotencyKey: absent caller key must remain absent")
    if kind == "command" and "extensions" not in envelope and "extensions" in body:
        findings.append(f"{pointer}/expectedGateway/body/extensions: absent envelope extensions must remain absent")
    if kind == "command" and "correlationId" not in step["scriptedResponse"]["echoRequestFields"]:
        findings.append(f"{pointer}/scriptedResponse/echoRequestFields: command response must echo request correlationId")
    if kind == "query" and step["scriptedResponse"]["echoRequestFields"]:
        findings.append(f"{pointer}/scriptedResponse/echoRequestFields: query request has no identifiers to echo")
    if kind == "query":
        if "entityId" not in envelope and "entityId" in body:
            findings.append(f"{pointer}/expectedGateway/body/entityId: absent envelope entityId must remain absent")
        paging = {field: envelope[field] for field in ("pageSize", "offset", "cursor") if field in envelope}
        expected_paging = body.get("paging")
        if not paging and "paging" in body:
            findings.append(f"{pointer}/expectedGateway/body/paging: absent envelope paging must remain absent")
        elif paging and (not isinstance(expected_paging, dict) or expected_paging.keys() != paging.keys()
                         or any(type(expected_paging[field]) is not type(value) or expected_paging[field] != value
                                for field, value in paging.items())):
            findings.append(f"{pointer}/expectedGateway/body/paging: must equal supplied envelope paging")


def validate_vectors(
    paths: list[Path], artifact: Path, expected_package: tuple[str, str] | None = None,
    expected_operations: list[str] | None = None,
) -> list[str]:
    """Apply identical schema, semantic, artifact and optional Catalog coverage checks."""
    if not paths:
        return ["/: at least one vector path is required"]
    try:
        artifact_id, artifact_version = package_identity(artifact)
    except VectorError as exc:
        return [str(exc)]
    findings: list[str] = []
    if expected_package is not None:
        expected_id, expected_version = expected_package
        if (artifact_id.casefold(), artifact_version) != (expected_id.casefold(), expected_version):
            findings.append(f"{artifact}:/metadata: artifact {artifact_id}@{artifact_version} does not match restored package {expected_id}@{expected_version}")
    schema = _load_json(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    validator = VectorValidator(schema)
    seen: dict[str, Path] = {}
    for source in paths:
        try:
            document = _load_json(source)
        except VectorError as exc:
            findings.append(str(exc))
            continue
        if isinstance(document, dict) and "formatVersion" in document and document["formatVersion"] not in SUPPORTED_FORMAT_VERSIONS:
            findings.append(f"{source}:/formatVersion: unsupported format version {document['formatVersion']!r}; supported: {SUPPORTED_FORMAT_VERSIONS}")
        errors = _schema_errors(document, source, validator)
        findings.extend(errors)
        if errors or not isinstance(document, dict):
            continue
        package = document["package"]
        if (package["id"].casefold(), package["version"]) != (artifact_id.casefold(), artifact_version):
            findings.append(f"{source}:/package: vector {package['id']}@{package['version']} does not match release artifact {artifact_id}@{artifact_version}")
        operation = document["operation"]
        if operation in seen:
            findings.append(f"{source}:/operation: duplicate {operation!r}; first declared in {seen[operation]}")
        seen[operation] = source
        invocation = document["invocation"]
        if invocation["operation"] != operation or invocation["kind"] != document["kind"]:
            findings.append(f"{source}:/invocation: operation and kind must match the vector header")
        for group in ("prerequisites", "postconditions"):
            for index, step in enumerate(document[group]):
                _check_step(step, f"{source}:/{group}/{index}", findings)
        _check_step(invocation, f"{source}:/invocation", findings)
    if expected_operations is not None:
        declared = set(seen)
        expected = set(expected_operations)
        if len(expected_operations) != len(expected):
            findings.append("/operations: restored Catalog operation names contain duplicates")
        for operation in sorted(expected - declared):
            findings.append(f"/operations/{operation}: missing conformance vector")
        for operation in sorted(declared - expected):
            findings.append(f"{seen[operation]}:/operation: {operation!r} is absent from the restored Catalog")
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, required=True, help="immutable owning Contracts .nupkg")
    parser.add_argument("--expected-package-id", help="runner's restored flagged package ID")
    parser.add_argument("--expected-package-version", help="runner's restored flagged exact package version")
    parser.add_argument("--operations-file", type=Path, help="JSON array of canonical restored Catalog names for coverage")
    parser.add_argument("vectors", nargs="+", type=Path)
    args = parser.parse_args(argv)
    if (args.expected_package_id is None) != (args.expected_package_version is None):
        parser.error("--expected-package-id and --expected-package-version must be supplied together")
    operations = None
    if args.operations_file is not None:
        try:
            operations = _load_json(args.operations_file)
        except VectorError as exc:
            print(exc, file=sys.stderr)
            return 1
        if not isinstance(operations, list) or not all(isinstance(item, str) for item in operations):
            print(f"{args.operations_file}:/: expected an array of canonical operation names", file=sys.stderr)
            return 1
    expected = (args.expected_package_id, args.expected_package_version) if args.expected_package_id is not None else None
    findings = validate_vectors(args.vectors, args.artifact, expected, operations)
    if findings:
        print("\n".join(findings), file=sys.stderr)
        return 1
    print(f"Validated {len(args.vectors)} vector(s) against {args.artifact}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
