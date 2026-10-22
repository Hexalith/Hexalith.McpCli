#!/usr/bin/env python3
"""Run approved vectors through separate CLI and MCP stdio processes against a reset HTTP Gateway."""

from __future__ import annotations

import argparse
import base64
import copy
from datetime import datetime
import hashlib
import json
import os
import re
import select
import subprocess
import sys
import tempfile
import threading
import time
import zipfile
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from validate import VectorError, _json_equal, _load_json, validate_vectors
from verify_artifact import restored_package


ULID = re.compile(r"^[0-7][0-9A-HJKMNP-TV-Z]{25}$")


def _fail(message: str) -> None:
    raise VectorError(message)


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _escape_pointer_token(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _pointer(document: Any, path: str) -> tuple[bool, Any]:
    if path == "":
        return True, document
    current = document
    for token in path[1:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and token in current:
            current = current[token]
        elif isinstance(current, list) and token.isdecimal() and int(token) < len(current):
            current = current[int(token)]
        else:
            return False, None
    return True, current


def _assert_result(result: Any, assertion: dict[str, Any], location: str) -> None:
    present, actual = _pointer(result, assertion["path"])
    operator = assertion["operator"]
    expected = assertion["value"]
    if operator == "exists":
        passed = present is expected
    elif not present:
        passed = False
    elif operator == "equals":
        passed = _json_equal(actual, expected)
    elif operator == "arrayLength":
        passed = isinstance(actual, list) and len(actual) == expected
    else:
        passed = (isinstance(actual, list) and any(_json_equal(item, expected) for item in actual)
                  or isinstance(actual, str) and isinstance(expected, str) and expected in actual
                  or isinstance(actual, dict) and isinstance(expected, dict)
                  and all(key in actual and _json_equal(actual[key], value) for key, value in expected.items()))
    if not passed:
        _fail(f"{location}: assertion {operator} at {assertion['path'] or '/'} expected {expected!r}; got {actual!r}; result {_canonical(result)}")


def _mask(document: dict[str, Any], step: dict[str, Any], location: str) -> dict[str, Any]:
    normalized = copy.deepcopy(document)
    if step["kind"] == "command" and "correlationId" not in step["envelope"] \
            and normalized.get("correlationId") != normalized.get("messageId"):
        _fail(f"{location}/correlationId: default correlation must equal the generated messageId")
    for pointer in step["expectedGateway"]["maskGenerated"]:
        field = pointer[1:]
        value = normalized.get(field)
        if not isinstance(value, str) or ULID.fullmatch(value) is None:
            _fail(f"{location}/{field}: generated identifier is not a ULID: {value!r}")
        normalized[field] = "<generated>"
    return normalized


def _assert_fresh_message(request: dict, step: dict, seen: set[str], location: str) -> None:
    if step["kind"] != "command":
        return
    message = request["body"].get("messageId")
    if not isinstance(message, str) or ULID.fullmatch(message) is None:
        _fail(f"{location}/messageId: generated identifier is not a ULID: {message!r}")
    if message in seen:
        _fail(f"{location}/messageId: generated request messageId was reused across distinct calls")
    seen.add(message)


def _mask_result(document: dict[str, Any], step: dict[str, Any], location: str) -> dict[str, Any]:
    normalized = copy.deepcopy(document)
    if step["kind"] == "command" and "error" in normalized:
        expected = _expected_gateway_error(step, document)
        if expected is not None and "correlationId" in expected \
                and "correlationId" not in step["envelope"] \
                and "correlationId" in step["scriptedResponse"]["echoRequestFields"]:
            value = normalized["error"].get("correlationId")
            if not isinstance(value, str) or ULID.fullmatch(value) is None:
                _fail(f"{location}/error/correlationId: generated identifier is not a ULID: {value!r}")
            normalized["error"]["correlationId"] = "<generated>"
    if step["kind"] == "command" and "error" not in normalized:
        for field in ("messageId", "correlationId"):
            response = _sdk_response(step)
            generated = (response["messageId"] is None or "messageId" in step["scriptedResponse"]["echoRequestFields"]) \
                if field == "messageId" else "correlationId" not in step["envelope"]
            if generated:
                value = normalized.get(field)
                if not isinstance(value, str) or ULID.fullmatch(value) is None:
                    _fail(f"{location}/{field}: generated identifier is not a ULID: {value!r}")
                normalized[field] = "<generated>"
    return normalized


def _expect_fields(actual: Any, expected: Any, location: str) -> None:
    if _json_equal(actual, expected):
        return
    if isinstance(expected, dict) and isinstance(actual, dict):
        for key in sorted(actual.keys() - expected.keys()):
            _fail(f"{location}/{_escape_pointer_token(key)}: unexpected Gateway field")
        for key, value in expected.items():
            if key not in actual:
                _fail(f"{location}/{_escape_pointer_token(key)}: expected Gateway field is missing")
            if not _json_equal(actual[key], value):
                _expect_fields(actual[key], value, f"{location}/{_escape_pointer_token(key)}")
    elif isinstance(expected, list) and isinstance(actual, list):
        if len(actual) != len(expected):
            _fail(f"{location}: expected {_canonical(expected)}, got {_canonical(actual)}")
        for index, (actual_item, expected_item) in enumerate(zip(actual, expected)):
            if not _json_equal(actual_item, expected_item):
                _expect_fields(actual_item, expected_item, f"{location}/{index}")
    else:
        _fail(f"{location}: expected {_canonical(expected)}, got {_canonical(actual)}")


def _assert_discovery_parity(
    exit_code: int, mcp_error: bool, cli_document: Any, mcp_document: Any, location: str,
) -> None:
    if exit_code != 0 or mcp_error or not _json_equal(cli_document, mcp_document):
        _fail(f"{location}: CLI/MCP discovery differs: exit={exit_code}, isError={mcp_error}; "
              f"CLI={_canonical(cli_document)}; MCP={_canonical(mcp_document)}")


def _assert_document_parity(cli_document: Any, mcp_document: Any, location: str) -> None:
    if not _json_equal(cli_document, mcp_document):
        _fail(f"{location}: canonical CLI/MCP documents differ: "
              f"{_canonical(cli_document)} != {_canonical(mcp_document)}")


def _assert_error_parity(cli_document: Any, mcp_document: Any, location: str) -> None:
    if not _json_equal(cli_document, mcp_document):
        _fail(f"{location}: CLI/MCP error documents differ: "
              f"{_canonical(cli_document)} != {_canonical(mcp_document)}")


def _assert_request_parity(cli_request: Any, mcp_request: Any, location: str) -> None:
    if not _json_equal(cli_request, mcp_request):
        _fail(f"{location}: captured Gateway requests differ: "
              f"{_canonical(cli_request)} != {_canonical(mcp_request)}")


class ReplayGateway:
    def __init__(self, steps: list[dict[str, Any]]) -> None:
        self.steps = steps
        self.captured: list[dict[str, Any]] = []
        self.lock = threading.Lock()
        gateway = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                try:
                    if self.headers.get("Transfer-Encoding", "").lower() == "chunked":
                        chunks = bytearray()
                        while True:
                            size = int(self.rfile.readline().split(b";", 1)[0].strip(), 16)
                            if size == 0:
                                while self.rfile.readline().strip():
                                    pass
                                break
                            chunks.extend(self.rfile.read(size))
                            self.rfile.read(2)
                        raw = bytes(chunks)
                    else:
                        length = int(self.headers.get("Content-Length", "0"))
                        raw = self.rfile.read(length)
                    body = json.loads(raw)
                    with gateway.lock:
                        index = len(gateway.captured)
                        gateway.captured.append({"method": "POST", "path": self.path, "body": body})
                    if index >= len(gateway.steps):
                        status, response = 500, {"error": "unexpected Gateway request"}
                    else:
                        script = gateway.steps[index]["scriptedResponse"]
                        status, response = script["statusCode"], copy.deepcopy(script["body"])
                        for field in script["echoRequestFields"]:
                            response[field] = body[field]
                    encoded = json.dumps(response).encode("utf-8")
                    self.send_response(status)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(encoded)))
                    self.end_headers()
                    self.wfile.write(encoded)
                except (ValueError, KeyError) as exc:
                    gateway.failure = str(exc)
                    self.send_error(500, str(exc))

            def log_message(self, format: str, *args: Any) -> None:
                pass

        self.failure: str | None = None
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self) -> ReplayGateway:
        self.thread.start()
        return self

    def __exit__(self, *_: Any) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.server.server_address[1]}/"

    def assert_consumed(self, location: str) -> None:
        if self.failure is not None or len(self.captured) != len(self.steps):
            _fail(f"{location}: Gateway replay consumed {len(self.captured)}/{len(self.steps)} requests; {self.failure or ''}")


class HeadProcess:
    def __init__(self, host: Path, home: str, timeout: float) -> None:
        self.host = host
        self.timeout = timeout
        self.env = {key: value for key, value in os.environ.items()
                    if not key.startswith(("MCPCLI_", "EVENTSTORE_"))}
        self.profile = Path(home) / "mcpcli.json"
        self.env["MCPCLI_CONFORMANCE_PROFILE_PATH"] = str(self.profile)

    def allow_extensions(self, keys: set[str]) -> None:
        self.profile.write_text(json.dumps({"version": 1, "activeProfile": "conformance", "profiles": {
            "conformance": {"allowedExtensions": sorted(keys)}}}))

    def _base(self) -> list[str]:
        return ["dotnet", str(self.host)]

    def cli(self, args: list[str], url: str | None = None, tenant: str | None = None,
            actor: str | None = None) -> tuple[int, dict[str, Any]]:
        command = self._base() + args + ["--format", "json"]
        if url is not None:
            command += ["--url", url]
        if tenant is not None:
            command += ["--tenant", tenant]
        if actor is not None:
            command += ["--actor", actor]
        result = subprocess.run(command, capture_output=True, text=True, timeout=self.timeout, env=self.env, check=False)
        try:
            document = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            _fail(f"CLI {args}: exit {result.returncode}; invalid JSON stdout {result.stdout!r}; stderr {result.stderr!r}: {exc}")
        return result.returncode, document

    def mcp(self, tool: str, arguments: dict[str, Any], url: str | None = None,
            tenant: str | None = None, actor: str | None = None) -> tuple[bool, dict[str, Any]]:
        command = self._base() + ["mcp", "--transport", "stdio", "--strict"]
        if url is not None:
            command += ["--url", url]
        if tenant is not None:
            command += ["--tenant", tenant]
        if actor is not None:
            command += ["--actor", actor]
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, env=self.env, bufsize=0)
        try:
            client = _JsonRpcClient(process, self.timeout)
            client.request("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                          "clientInfo": {"name": "mcpcli-conformance", "version": "1"}})
            client.notify("notifications/initialized", {})
            reply = client.request("tools/call", {"name": tool, "arguments": arguments})
            result = reply["result"]
            structured = result.get("structuredContent")
            if not isinstance(structured, dict):
                _fail(f"MCP {tool}: missing structuredContent: {reply!r}")
            content = result.get("content", [])
            if len(content) != 1 or not _json_equal(json.loads(content[0]["text"]), structured):
                _fail(f"MCP {tool}: text and structuredContent differ")
            return bool(result.get("isError", False)), structured
        except (KeyError, ValueError, OSError) as exc:
            stderr = process.stderr.read(4096).decode("utf-8", errors="replace") if process.poll() is not None else ""
            _fail(f"MCP {tool}: {exc}; stderr {stderr!r}")
        finally:
            if process.stdin is not None:
                process.stdin.close()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)
            if process.stdout is not None:
                process.stdout.close()
            if process.stderr is not None:
                process.stderr.close()


class _JsonRpcClient:
    def __init__(self, process: subprocess.Popen[bytes], timeout: float) -> None:
        self.process = process
        self.timeout = timeout
        self.next_id = 1
        self.pending = b""

    def notify(self, method: str, params: dict[str, Any]) -> None:
        self._write({"jsonrpc": "2.0", "method": method, "params": params})

    def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        request_id = self.next_id
        self.next_id += 1
        self._write({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        deadline = time.monotonic() + self.timeout
        while True:
            reply = self._read(deadline)
            if not _json_equal(reply.get("id"), request_id):
                continue
            if "error" in reply:
                _fail(f"JSON-RPC {method}: {reply['error']!r}")
            return reply

    def _write(self, message: dict[str, Any]) -> None:
        assert self.process.stdin is not None
        self.process.stdin.write((json.dumps(message, separators=(",", ":")) + "\n").encode("utf-8"))
        self.process.stdin.flush()

    def _read(self, deadline: float) -> dict[str, Any]:
        assert self.process.stdout is not None
        while b"\n" not in self.pending:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                _fail("MCP stdio response timed out")
            ready, _, _ = select.select([self.process.stdout], [], [], remaining)
            if not ready:
                _fail("MCP stdio response timed out")
            chunk = os.read(self.process.stdout.fileno(), 4096)
            if not chunk:
                _fail(f"MCP stdio closed before response; process exit {self.process.poll()}")
            self.pending += chunk
        line, self.pending = self.pending.split(b"\n", 1)
        return json.loads(line)


def _call_args(step: dict[str, Any], payload_override: str | None = None) -> tuple[list[str], str, dict[str, Any]]:
    envelope = step["envelope"]
    payload = payload_override if payload_override is not None else _canonical(step["payload"])
    cli = ["send" if step["kind"] == "command" else "query", step["operation"], "--payload", payload]
    mcp: dict[str, Any] = {"operation": step["operation"], "payload": payload}
    options = ("aggregateId", "correlationId", "idempotencyKey", "extensions") if step["kind"] == "command" else (
        "aggregateId", "entityId", "pageSize", "offset", "cursor")
    for option in options:
        if option not in envelope:
            continue
        mcp[option] = envelope[option]
        if option == "extensions":
            for key, value in envelope[option].items():
                cli += ["--extension", f"{key}={value}"]
        else:
            cli += ["--" + re.sub(r"[A-Z]", lambda match: "-" + match.group().lower(), option), str(envelope[option])]
    return cli, "send_command" if step["kind"] == "command" else "run_query", mcp


def _run_step(head: HeadProcess, step: dict[str, Any], url: str, label: str,
              verify_assertions: bool = True, evidence: list | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    cli_args, tool, mcp_args = _call_args(step)
    envelope = step["envelope"]
    if label == "CLI":
        exit_code, document = head.cli(cli_args, url, envelope["tenant"], envelope.get("actor"))
        if evidence is not None:
            evidence.append(document)
        if exit_code not in (0, 2) or (exit_code == 0) == ("error" in document):
            _fail(f"{label} {step['operation']}: inconsistent exit {exit_code} and result {document!r}")
    else:
        is_error, document = head.mcp(tool, mcp_args, url, envelope["tenant"], envelope.get("actor"))
        if evidence is not None:
            evidence.append(document)
        if is_error != ("error" in document):
            _fail(f"{label} {step['operation']}: inconsistent isError and result {document!r}")
    _assert_result_contract(document, step, f"{label} {step['operation']}")
    if verify_assertions:
        for index, assertion in enumerate(step["assertions"]):
            _assert_result(document, assertion, f"{label} {step['operation']}/assertions/{index}")
    return document, {}


def _nonblank(*values: Any) -> str | None:
    return next((value for value in values if isinstance(value, str) and value.strip()), None)


def _response_body(step: dict) -> dict:
    body = copy.deepcopy(step["scriptedResponse"]["body"])
    for field in step["scriptedResponse"]["echoRequestFields"]:
        body[field] = step["envelope"].get(field, "01J9MZHXT3RKM0VWXRXGSJDATN")
    return body


def _response_depth(value: Any) -> int:
    children = value.values() if isinstance(value, dict) else value if isinstance(value, list) else None
    return 0 if children is None else 1 + max((_response_depth(child) for child in children), default=0)


def _sdk_response(step: dict) -> dict | None:
    """Read the pinned SDK's typed envelope, leaving JsonElement payloads opaque.

    Web JSON names are case-insensitive; unknown members are skipped, but still
    count toward the serializer's depth limit. Invalid typed values fail the
    entire response before correlation or semantic-success handling.
    """
    body = _response_body(step)
    if _response_depth(body) > 64:
        return None

    def properties(value):
        if not isinstance(value, dict):
            raise ValueError("typed object required")
        return {key.casefold(): item for key, item in value.items()}

    def string(value):
        if value is not None and not isinstance(value, str):
            raise ValueError("typed string required")
        return value

    def boolean(value, nullable=True):
        if not (nullable and value is None) and type(value) is not bool:
            raise ValueError("typed boolean required")
        return value

    def integer(value, bits, nullable=True):
        if nullable and value is None:
            return None
        # JsonSerializerDefaults.Web permits quoted numbers, not bools/floats.
        if isinstance(value, str) and re.fullmatch(r"-?[0-9]+", value):
            value = int(value)
        if type(value) is not int or not -(2 ** (bits - 1)) <= value < 2 ** (bits - 1):
            raise ValueError("typed integer required")
        return value

    try:
        typed = properties(body)
        response = {"correlationId": string(typed.get("correlationid"))}
        if step["kind"] == "command":
            response.update(messageId=string(typed.get("messageid")), resultPayload=typed.get("resultpayload"))
            return response
        response.update(payload=typed.get("payload"), success=boolean(typed.get("success", True), False),
                        errorMessage=string(typed.get("errormessage")), paging=None)
        if typed.get("metadata") is not None:
            metadata = properties(typed["metadata"])
            for key in ("etag", "projectionversion"):
                string(metadata.get(key))
            for key in ("isnotmodified", "isstale", "isdegraded"):
                boolean(metadata.get(key))
            if metadata.get("servedat") is not None:
                datetime.fromisoformat(string(metadata["servedat"]).replace("Z", "+00:00"))
            warnings = metadata.get("warningcodes")
            if warnings is not None:
                if not isinstance(warnings, list):
                    raise ValueError("typed warning list required")
                for warning in warnings:
                    string(warning)
            if metadata.get("paging") is not None:
                paging = properties(metadata["paging"])
                response["paging"] = {
                    "pageSize": integer(paging.get("pagesize", 0), 32, False),
                    "offset": integer(paging.get("offset"), 32),
                    "nextCursor": string(paging.get("nextcursor")),
                    "totalCount": integer(paging.get("totalcount"), 64),
                    "hasMore": boolean(paging.get("hasmore")),
                }
                response["paging"] = {key: value for key, value in response["paging"].items() if value is not None}
        return response
    except (ValueError, TypeError):
        return None


def _expected_gateway_error(step: dict, document: dict) -> dict | None:
    """Model the pinned SDK error mapping, including its typed Query response outcomes."""
    script = step["scriptedResponse"]
    status, body = script["statusCode"], _response_body(step)
    special_detail = None
    problem = not 200 <= status < 300
    if step["kind"] == "query" and status == 304:
        status, special_detail = 502, "Not-modified query response requires projection-backed provenance and a strong ETag."
    elif not problem and (status == 204 or _sdk_response(step) is None):
        special_detail = ("Query" if step["kind"] == "query" else "Command") + " response body could not be parsed."
    elif not problem and not _nonblank(_sdk_response(step)["correlationId"]):
        special_detail = ("Query" if step["kind"] == "query" else "Command") + " response did not contain a valid correlationId."
    elif not problem and step["kind"] == "query" and not _sdk_response(step)["success"]:
        body = _sdk_response(step)
        status, special_detail = 200, _nonblank(body["errorMessage"], "Query semantic failure")
        error = {"code": "gateway_error", "status": status, "detail": special_detail}
        correlation = body.get("correlationId")
        if isinstance(correlation, str) and ULID.fullmatch(correlation) is not None:
            error["correlationId"] = correlation
        return error
    elif not problem:
        return None
    if special_detail is not None:
        return {"code": "gateway_error", "status": status, "detail": special_detail}
    if _response_depth(body) > 64:
        body = {}  # Problem JSON parse errors fall back to HTTP metadata.
    try:
        title = HTTPStatus(status).phrase
    except ValueError:
        title = None
    declared_status = body.get("status")
    if type(declared_status) is int and -(2 ** 31) <= declared_status < 2 ** 31:
        status = declared_status
    # The SDK uses HTTP reason only when title is null, then Core drops blank values.
    problem_title = body.get("title") if isinstance(body.get("title"), str) else title
    error = {"code": "gateway_error", "status": status,
             "detail": _nonblank(body.get("detail"), problem_title, "Gateway request failed.")}
    for target, value in {
        "reason": _nonblank(body.get("reasonCode"), body.get("code"), body.get("reason")),
        "clientAction": _nonblank(body.get("clientAction")),
        "retryAfter": _nonblank(body.get("retryAfter")),
    }.items():
        if value is not None:
            error[target] = value
    if type(body.get("retryable")) is bool:
        error["retryable"] = body["retryable"]
    correlation = body.get("correlationId")
    if isinstance(correlation, str) and ULID.fullmatch(correlation) is not None:
        if "correlationId" in script["echoRequestFields"] and "correlationId" not in step["envelope"]:
            actual = document.get("error", {}).get("correlationId")
            if not isinstance(actual, str) or ULID.fullmatch(actual) is None:
                _fail("required echoed Gateway correlationId is missing or invalid")
            correlation = actual
        error["correlationId"] = correlation
    return error


def _assert_result_contract(document: Any, step: dict[str, Any], location: str) -> None:
    if not isinstance(document, dict):
        _fail(f"{location}: result must be an object")
    expected_error = _expected_gateway_error(step, document)
    if expected_error is not None:
        if not _json_equal(document, {"error": expected_error}):
            _fail(f"{location}: required Gateway error document differs: expected {_canonical({'error': expected_error})}; got {_canonical(document)}")
        return
    envelope = step["envelope"]
    expected = {"operation": step["operation"], "tenant": envelope["tenant"]}
    if step["kind"] == "command":
        expected.update(aggregateId=step["expectedGateway"]["body"]["aggregateId"], status="accepted")
        for key in ("messageId", "correlationId"):
            if not isinstance(document.get(key), str) or ULID.fullmatch(document[key]) is None:
                _fail(f"{location}/{key}: required canonical ULID result is missing")
        expected["messageId"] = document["messageId"]
        expected["correlationId"] = envelope.get("correlationId", document["correlationId"])
        if "idempotencyKey" in envelope:
            expected["idempotencyKey"] = envelope["idempotencyKey"]
        elif "idempotencyKey" in document:
            _fail(f"{location}/idempotencyKey: unsupplied key must remain absent")
        response = _sdk_response(step)
        if response.get("resultPayload") is not None:
            expected["result"] = response["resultPayload"]
    else:
        response = _sdk_response(step)
        expected["document"] = response["payload"]
        if response["paging"] is not None:
            expected["paging"] = response["paging"]
    for field, value in expected.items():
        if field not in document or not _json_equal(document[field], value):
            _fail(f"{location}/{field}: required result must equal {_canonical(value)}")
    if document.keys() != expected.keys():
        _fail(f"{location}: unexpected result field(s): {sorted(document.keys() - expected.keys())}")


def _assert_result_request_binding(document: dict, request: dict, step: dict, location: str) -> None:
    if "error" in document:
        expected = _expected_gateway_error(step, document)
        if expected is not None and "correlationId" in expected \
                and "correlationId" in step["scriptedResponse"]["echoRequestFields"] \
                and document["error"].get("correlationId") != request.get("correlationId"):
            _fail(f"{location}/error/correlationId: result does not preserve the submitted identifier")
        return
    if step["kind"] != "command":
        return
    response = _sdk_response(step)
    expected_message = request["messageId"] if "messageId" in step["scriptedResponse"]["echoRequestFields"] \
        else response["messageId"] if response["messageId"] is not None else request["messageId"]
    for field, expected in (("messageId", expected_message), ("correlationId", request["correlationId"])):
        if document.get(field) != expected:
            _fail(f"{location}/{field}: result does not preserve the submitted/returned identifier")


def _steps(vector: dict[str, Any]):
    for group in ("prerequisites", "invocation", "postconditions"):
        if group == "invocation":
            yield "/invocation", vector[group]
        else:
            for index, step in enumerate(vector[group]):
                yield f"/{group}/{index}", step


def _preflight_vectors(head: HeadProcess, vectors: list[Path], catalog: dict[str, str], evidence_file: Path | None = None) -> None:
    documents = {str(source): _load_json(source) for source in vectors}
    for source, vector in documents.items():
        for pointer, step in _steps(vector):
            expected_kind = "write" if step["kind"] == "command" else "read"
            if catalog.get(step["operation"]) != expected_kind:
                _fail(f"{source}:{pointer}/operation: step kind/operation differs from the complete Catalog")
    result = subprocess.run(head._base() + ["--validate-vectors", *map(str, vectors)],
                            capture_output=True, text=True, timeout=head.timeout, env=head.env, check=False)
    try:
        compatibility = json.loads(result.stdout)
    except json.JSONDecodeError:
        _fail(f"Core vector compatibility adapter failed: {result.stdout!r}; {result.stderr!r}")
    if evidence_file is not None:
        evidence_file.parent.mkdir(parents=True, exist_ok=True)
        evidence_file.write_text(json.dumps(compatibility, indent=2) + "\n")
    if result.returncode != 0 or compatibility["findings"]:
        _fail("\n".join(compatibility["findings"]) or f"Core vector compatibility failed: {result.stderr}")
    expected_steps = {(source, pointer): step for source, vector in documents.items() for pointer, step in _steps(vector)}
    captured = set()
    for request in compatibility["requests"]:
        key = (request["source"], request["pointer"])
        if key not in expected_steps or key in captured:
            _fail(f"Core vector compatibility returned an unexpected/duplicate step: {key!r}")
        captured.add(key)
        step = expected_steps[key]
        normalized = _mask(request["body"], step, f"{key[0]}:{key[1]}/expectedGateway/body")
        _expect_fields(normalized, step["expectedGateway"]["body"], f"{key[0]}:{key[1]}/expectedGateway/body")
    if captured != expected_steps.keys():
        _fail("Core vector compatibility omitted validated steps")
    head.allow_extensions({key for vector in documents.values() for _, step in _steps(vector)
                           for key in step["envelope"].get("extensions", {})})


def _verify_artifact_in_host(host: Path, artifact: Path, package: tuple[str, str],
                             assets_path: Path | None = None) -> None:
    deps = host.with_suffix(".deps.json")
    data = json.loads(deps.read_text(encoding="utf-8"))
    package_id, version = package
    matches = [(name, metadata) for name, metadata in data["libraries"].items()
               if name.rsplit("/", 1)[0].casefold() == package_id.casefold() and metadata.get("type") == "package"]
    if len(matches) != 1 or matches[0][0].rsplit("/", 1)[1] != version:
        _fail(f"{deps}: restored flagged package does not match {package_id}@{version}: {[name for name, _ in matches]}")
    if assets_path is None:
        if len(host.parents) < 4:
            _fail(f"{host}: restore assets are required; supply --assets")
        assets_path = host.parents[3] / "obj/project.assets.json"
    if not assets_path.is_file():
        _fail(f"{assets_path}: restore assets are unavailable; supply --assets")
    assets = json.loads(assets_path.read_text(encoding="utf-8"))
    identity = matches[0][0]
    library = assets.get("libraries", {}).get(identity)
    if not isinstance(library, dict) or library.get("type") != "package":
        _fail(f"{assets_path}: restored package does not match {identity}")
    try:
        _, restored = restored_package(assets, identity, library)
    except RuntimeError as error:
        _fail(str(error))
    actual_hash = "sha512-" + base64.b64encode(hashlib.sha512(artifact.read_bytes()).digest()).decode("ascii")
    if restored["artifactHash"] != actual_hash:
        _fail(f"{deps}: restored package hash differs from immutable artifact {artifact}")
    if matches[0][1].get("sha512") != restored["assetsHash"]:
        _fail(f"{deps}: package restore content hash differs from {assets_path}")
    target = data.get("targets", {}).get(data.get("runtimeTarget", {}).get("name"), {})
    runtime = target.get(identity, {}).get("runtime", {})
    runtime_dlls = [name for name in runtime if name.endswith(".dll")]
    restored_runtime = {name for target in assets.get("targets", {}).values()
                        for name in target.get(identity, {}).get("runtime", {})}
    if not runtime_dlls or not set(runtime_dlls) <= restored_runtime:
        _fail(f"{deps}: selected package runtime DLL assets differ from {assets_path}")
    with zipfile.ZipFile(artifact) as archive:
        for asset in runtime_dlls:
            output = host.parent / Path(asset).name
            if asset not in archive.namelist() or not output.is_file() \
                    or output.read_bytes() != archive.read(asset):
                _fail(f"{output}: host runtime DLL bytes differ from immutable artifact entry {asset}")


def _manifest_operations(head: HeadProcess, package_id: str) -> dict[str, str]:
    process = subprocess.run(head._base() + ["--manifest-catalog"], capture_output=True, text=True,
                             timeout=head.timeout, env=head.env, check=False)
    if process.returncode != 0:
        _fail(f"test host manifest inspection failed: {process.stderr!r}")
    packages = json.loads(process.stdout)
    matching = [item for item in packages if item["packageId"].casefold() == package_id.casefold()]
    if len(matching) != 1:
        _fail(f"test host flagged manifest must contain exactly one {package_id} entry; found {len(matching)}")
    operations = matching[0]["operations"]
    names = [item["name"] for item in operations]
    if len(names) != len(set(names)) or not names:
        _fail(f"test host flagged manifest has duplicate or no Operations for {package_id}")
    return {item["name"]: item["kind"] for item in operations}


def run(host: Path, artifact: Path, package: tuple[str, str], vectors: list[Path], timeout: float = 15,
        assets_path: Path | None = None) -> None:
    run_catalog(host, [(artifact, package, vectors)], timeout, assets_path, complete=False)


def run_catalog(host: Path, selections: list[tuple[Path, tuple[str, str], list[Path]]], timeout: float = 15,
                assets_path: Path | None = None, complete: bool = True, evidence_dir: Path | None = None,
                expected_modules: dict[str, str] | None = None) -> dict:
    for artifact, package, vectors in selections:
        _verify_artifact_in_host(host, artifact, package, assets_path)
        findings = validate_vectors(vectors, artifact, package)
        if findings:
            _fail("\n".join(findings))
    vectors = [source for _, _, sources in selections for source in sources]
    with tempfile.TemporaryDirectory(prefix="mcpcli-conformance-home-") as home:
        head = HeadProcess(host, home, timeout)
        malformed = subprocess.run(head._base() + ["modules", "--bogus-secret"],
                                   capture_output=True, text=True, timeout=timeout, env=head.env, check=False)
        try:
            malformed_document = json.loads(malformed.stdout)
        except json.JSONDecodeError as exc:
            _fail(f"test host malformed-command stdout is not JSON: {exc}")
        if malformed.returncode != 2 or malformed.stderr or malformed_document.get("error", {}).get("code") != "invalid_arguments":
            _fail(f"test host bypasses checked CLI parsing: exit {malformed.returncode}, "
                  f"stdout {malformed.stdout!r}, stderr {malformed.stderr!r}")
        exit_code, modules = head.cli(["modules", "--strict"])
        mcp_error, mcp_modules = head.mcp("list_modules", {})
        _assert_discovery_parity(exit_code, mcp_error, modules, mcp_modules, "list_modules")
        catalog: dict[str, str] = {}
        for module in modules["modules"]:
            name = module["name"]
            exit_code, listed = head.cli(["operations", name, "--strict"])
            mcp_error, mcp_listed = head.mcp("list_operations", {"module": name})
            _assert_discovery_parity(exit_code, mcp_error, listed, mcp_listed, f"list_operations {name}")
            for operation in listed["operations"]:
                if operation["name"] in catalog:
                    _fail(f"duplicate operation in complete Catalog: {operation['name']}")
                catalog[operation["name"]] = operation["kind"]
        owned = {}
        package_modules = {}
        discovered_modules = {module["name"] for module in modules["modules"]}
        for artifact, package, sources in selections:
            operations = _manifest_operations(head, package[0])
            actual_modules = {name.split(".", 1)[0] for name in operations}
            if not actual_modules <= discovered_modules:
                _fail(f"{package[0]}: owning module is absent from the combined Catalog")
            if expected_modules is not None and actual_modules != {expected_modules[package[0]]}:
                _fail(f"{package[0]}: receipt module {expected_modules[package[0]]!r} differs from discovered module(s) {sorted(actual_modules)!r}")
            package_modules[package[0]] = sorted(actual_modules)
            for operation, kind in operations.items():
                if operation in owned or catalog.get(operation) != ("write" if kind == "command" else "read"):
                    _fail(f"flagged package {package[0]} operation {operation} differs from built combined Catalog")
                owned[operation] = kind
            findings = validate_vectors(sources, artifact, package, list(operations))
            if findings:
                _fail("\n".join(findings))
        if complete and set(owned) != set(catalog):
            _fail("complete production Catalog contains uncovered operations")
        _preflight_vectors(head, vectors, catalog, evidence_dir / "preflight.json" if evidence_dir is not None else None)
        seen_messages: set[str] = set()
        for source in vectors:
            vector = _load_json(source)
            operation = vector["operation"]
            if owned[operation] != vector["kind"]:
                _fail(f"{source}:/kind: differs from owning flagged package kind {owned[operation]}")
            exit_code, described = head.cli(["describe", operation, "--strict"])
            mcp_error, mcp_described = head.mcp("describe_operation", {"operation": operation})
            _assert_discovery_parity(
                exit_code, mcp_error, described, mcp_described, f"{source}: describe_operation")
            steps = vector["prerequisites"] + [vector["invocation"]] + vector["postconditions"]
            observations: dict[str, tuple[list[dict[str, Any]], list[dict[str, Any]]]] = {}
            for label in ("CLI", "MCP"):
                with ReplayGateway(steps) as gateway:
                    documents = []
                    try:
                        for index, step in enumerate(steps):
                            _run_step(head, step, gateway.url, label, evidence=documents)
                            if len(gateway.captured) != index + 1:
                                _fail(f"{source}:{label}/steps/{index}: expected exactly one Gateway request")
                            _assert_fresh_message(gateway.captured[index], step, seen_messages, f"{source}:{label}/steps/{index}")
                        gateway.assert_consumed(f"{source}:{label}")
                    finally:
                        if evidence_dir is not None:
                            evidence_dir.mkdir(parents=True, exist_ok=True)
                            (evidence_dir / f"{operation}.{label}.json").write_text(json.dumps(
                                {"source": str(source), "documents": documents, "requests": gateway.captured}, indent=2) + "\n")
                    observations[label] = (documents, gateway.captured)
            cli_docs, cli_requests = observations["CLI"]
            mcp_docs, mcp_requests = observations["MCP"]
            for index, step in enumerate(steps):
                for label, document, captured in (("CLI", cli_docs[index], cli_requests[index]),
                                                  ("MCP", mcp_docs[index], mcp_requests[index])):
                    _assert_result_request_binding(document, captured["body"], step, f"{source}:{label}/steps/{index}")
                cli_doc = _mask_result(cli_docs[index], step, f"{source}:CLI/steps/{index}")
                mcp_doc = _mask_result(mcp_docs[index], step, f"{source}:MCP/steps/{index}")
                _assert_document_parity(cli_doc, mcp_doc, f"{source}:/steps/{index}")
                expected = step["expectedGateway"]
                requests = []
                for label, captured in (("CLI", cli_requests[index]), ("MCP", mcp_requests[index])):
                    request = copy.deepcopy(captured)
                    request["body"] = _mask(request["body"], step, f"{source}:{label}/steps/{index}/gateway/body")
                    _expect_fields(request, {"method": expected["method"], "path": expected["path"],
                                             "body": expected["body"]}, f"{source}:{label}/steps/{index}/gateway")
                    if "idempotencyKey" not in step["envelope"] and "idempotencyKey" in request["body"]:
                        _fail(f"{source}:{label}/steps/{index}: unsupplied idempotency key appeared")
                    requests.append(request)
                _assert_request_parity(requests[0], requests[1], f"{source}:/steps/{index}")
            # Malformed Payload is a generic validation error and must never reach the Gateway.
            invalid = copy.deepcopy(vector["invocation"])
            cli_args, tool, mcp_args = _call_args(invalid, "{invalid")
            envelope = invalid["envelope"]
            with ReplayGateway([]) as gateway:
                cli_exit, cli_error = head.cli(cli_args, gateway.url, envelope["tenant"], envelope.get("actor"))
                mcp_error, mcp_document = head.mcp(tool, mcp_args, gateway.url,
                                                    envelope["tenant"], envelope.get("actor"))
                gateway.assert_consumed(f"{source}:malformed-Payload")
            expected_validation = {"error": {"code": "validation_failed", "operation": invalid["operation"], "violations": [
                {"path": "/", "message": "The payload must be valid JSON without duplicate properties."}]}}
            for label, document in (("CLI", cli_error), ("MCP", mcp_document)):
                if not _json_equal(document, expected_validation):
                    _fail(f"{source}:{label}: required malformed-Payload error document differs: {_canonical(document)}")
            _assert_error_parity(cli_error, mcp_document, f"{source}: malformed-Payload")
            if cli_exit != 2 or not mcp_error or cli_error.get("error", {}).get("code") != "validation_failed":
                _fail(f"{source}: malformed-Payload CLI/MCP error parity failed: {cli_error!r}, {mcp_document!r}")
            # Exercise the Gateway error mapping with a separate reset script for each Head.
            failure = copy.deepcopy(vector["invocation"])
            failure["scriptedResponse"] = {
                "statusCode": 503,
                "body": {"title": "Service Unavailable", "status": 503, "detail": "scripted Gateway failure"},
                "echoRequestFields": [],
            }
            failed: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
            for label in ("CLI", "MCP"):
                with ReplayGateway([failure]) as gateway:
                    documents = []
                    try:
                        document, _ = _run_step(head, failure, gateway.url, label, verify_assertions=False, evidence=documents)
                        gateway.assert_consumed(f"{source}:{label}/gateway-error")
                        _assert_fresh_message(gateway.captured[0], failure, seen_messages, f"{source}:{label}/gateway-error")
                        failed[label] = (document, gateway.captured[0])
                    finally:
                        if evidence_dir is not None:
                            (evidence_dir / f"{operation}.{label}.gateway-error.json").write_text(json.dumps(
                                {"source": str(source), "documents": documents, "requests": gateway.captured}, indent=2) + "\n")
            cli_error_document, cli_error_request = failed["CLI"]
            mcp_error_document, mcp_error_request = failed["MCP"]
            _assert_error_parity(cli_error_document, mcp_error_document, f"{source}: Gateway error")
            if cli_error_document.get("error", {}).get("code") != "gateway_error" \
                    or cli_error_document["error"].get("status") != 503:
                _fail(f"{source}: Gateway error document lost code or status: {cli_error_document!r}")
            expected = failure["expectedGateway"]
            normalized_error_requests = []
            for label, request in (("CLI", cli_error_request), ("MCP", mcp_error_request)):
                normalized = copy.deepcopy(request)
                normalized["body"] = _mask(normalized["body"], failure, f"{source}:{label}/gateway-error/body")
                _expect_fields(normalized, {"method": expected["method"], "path": expected["path"],
                                            "body": expected["body"]}, f"{source}:{label}/gateway-error")
                normalized_error_requests.append(normalized)
            _assert_request_parity(
                normalized_error_requests[0], normalized_error_requests[1], f"{source}: Gateway error")
            print(f"PASS {operation}: discovery, {len(steps)} reset Gateway step(s), documents, requests, validation/Gateway error parity")
        return {"modules": sorted(discovered_modules), "packageModules": package_modules}



def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", type=Path, required=True, help="built test-only ConformanceHost DLL")
    parser.add_argument("--artifact", type=Path, required=True, help="immutable Contracts .nupkg used by the host")
    parser.add_argument("--assets", type=Path, help="host restore assets; defaults to obj/project.assets.json under the host project")
    parser.add_argument("--expected-package-id", required=True)
    parser.add_argument("--expected-package-version", required=True)
    parser.add_argument("--timeout", type=float, default=15)
    parser.add_argument("vectors", nargs="+", type=Path)
    args = parser.parse_args(argv)
    try:
        run(args.host.resolve(), args.artifact.resolve(),
            (args.expected_package_id, args.expected_package_version), args.vectors, args.timeout, args.assets)
    except (VectorError, OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
