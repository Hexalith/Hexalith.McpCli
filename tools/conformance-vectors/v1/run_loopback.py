#!/usr/bin/env python3
"""Run approved vectors through separate CLI and MCP stdio processes against a reset HTTP Gateway."""

from __future__ import annotations

import argparse
import base64
import copy
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
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from validate import VectorError, validate_vectors


ULID = re.compile(r"^[0-7][0-9A-HJKMNP-TV-Z]{25}$")


def _fail(message: str) -> None:
    raise VectorError(message)


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _json_equal(actual: Any, expected: Any) -> bool:
    if type(actual) in (int, float) and type(expected) in (int, float):
        return actual == expected
    if type(actual) is not type(expected):
        return False
    if isinstance(actual, dict):
        return actual.keys() == expected.keys() and all(
            _json_equal(actual[key], expected[key]) for key in actual)
    if isinstance(actual, list):
        return len(actual) == len(expected) and all(
            _json_equal(actual_item, expected_item) for actual_item, expected_item in zip(actual, expected))
    return actual == expected


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
    for pointer in step["expectedGateway"]["maskGenerated"]:
        field = pointer[1:]
        value = normalized.get(field)
        if not isinstance(value, str) or ULID.fullmatch(value) is None:
            _fail(f"{location}/{field}: generated identifier is not a ULID: {value!r}")
        normalized[field] = "<generated>"
    return normalized


def _mask_result(document: dict[str, Any], step: dict[str, Any], location: str) -> dict[str, Any]:
    normalized = copy.deepcopy(document)
    if step["kind"] == "command" and "error" not in normalized:
        for field in ("messageId", "correlationId"):
            if field == "messageId" or "correlationId" not in step["envelope"]:
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
            _fail(f"{location}/{key}: unexpected Gateway field")
        for key, value in expected.items():
            if key not in actual:
                _fail(f"{location}/{key}: expected Gateway field is missing")
            if not _json_equal(actual[key], value):
                _expect_fields(actual[key], value, f"{location}/{key}")
    elif isinstance(expected, list) and isinstance(actual, list):
        if len(actual) != len(expected):
            _fail(f"{location}: expected {_canonical(expected)}, got {_canonical(actual)}")
        for index, (actual_item, expected_item) in enumerate(zip(actual, expected)):
            if not _json_equal(actual_item, expected_item):
                _expect_fields(actual_item, expected_item, f"{location}/{index}")
    else:
        _fail(f"{location}: expected {_canonical(expected)}, got {_canonical(actual)}")


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
        self.env["MCPCLI_CONFORMANCE_PROFILE_PATH"] = str(Path(home) / "mcpcli.json")

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
        command = self._base() + ["mcp", "--transport", "stdio"]
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
              verify_assertions: bool = True) -> tuple[dict[str, Any], dict[str, Any]]:
    cli_args, tool, mcp_args = _call_args(step)
    envelope = step["envelope"]
    if label == "CLI":
        exit_code, document = head.cli(cli_args, url, envelope["tenant"], envelope.get("actor"))
        if exit_code not in (0, 2) or (exit_code == 0) == ("error" in document):
            _fail(f"{label} {step['operation']}: inconsistent exit {exit_code} and result {document!r}")
    else:
        is_error, document = head.mcp(tool, mcp_args, url, envelope["tenant"], envelope.get("actor"))
        if is_error != ("error" in document):
            _fail(f"{label} {step['operation']}: inconsistent isError and result {document!r}")
    if verify_assertions:
        for index, assertion in enumerate(step["assertions"]):
            _assert_result(document, assertion, f"{label} {step['operation']}/assertions/{index}")
    return document, {}


def _verify_artifact_in_host(host: Path, artifact: Path, package: tuple[str, str]) -> None:
    deps = host.with_suffix(".deps.json")
    data = json.loads(deps.read_text(encoding="utf-8"))
    package_id, version = package
    matches = [(name, metadata) for name, metadata in data["libraries"].items()
               if name.rsplit("/", 1)[0].casefold() == package_id.casefold() and metadata.get("type") == "package"]
    if len(matches) != 1 or matches[0][0].rsplit("/", 1)[1] != version:
        _fail(f"{deps}: restored flagged package does not match {package_id}@{version}: {[name for name, _ in matches]}")
    actual_hash = "sha512-" + base64.b64encode(hashlib.sha512(artifact.read_bytes()).digest()).decode("ascii")
    if matches[0][1].get("sha512") != actual_hash:
        _fail(f"{deps}: restored package hash differs from immutable artifact {artifact}")


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


def run(host: Path, artifact: Path, package: tuple[str, str], vectors: list[Path], timeout: float = 15) -> None:
    _verify_artifact_in_host(host, artifact, package)
    with tempfile.TemporaryDirectory(prefix="mcpcli-conformance-home-") as home:
        head = HeadProcess(host, home, timeout)
        exit_code, modules = head.cli(["modules"])
        mcp_error, mcp_modules = head.mcp("list_modules", {})
        if exit_code != 0 or mcp_error or not _json_equal(modules, mcp_modules):
            _fail("list_modules CLI/MCP discovery differs")
        catalog: dict[str, str] = {}
        for module in modules["modules"]:
            name = module["name"]
            exit_code, listed = head.cli(["operations", name])
            mcp_error, mcp_listed = head.mcp("list_operations", {"module": name})
            if exit_code != 0 or mcp_error or not _json_equal(listed, mcp_listed):
                _fail(f"list_operations {name} CLI/MCP discovery differs")
            for operation in listed["operations"]:
                catalog[operation["name"]] = operation["kind"]
        owned = _manifest_operations(head, package[0])
        for operation, kind in owned.items():
            if catalog.get(operation) != ("write" if kind == "command" else "read"):
                _fail(f"flagged package {package[0]} operation {operation} differs from built combined Catalog")
        findings = validate_vectors(vectors, artifact, package, list(owned))
        if findings:
            _fail("\n".join(findings))
        for source in vectors:
            vector = json.loads(source.read_text(encoding="utf-8"))
            operation = vector["operation"]
            if owned[operation] != vector["kind"]:
                _fail(f"{source}:/kind: differs from owning flagged package kind {owned[operation]}")
            exit_code, described = head.cli(["describe", operation])
            mcp_error, mcp_described = head.mcp("describe_operation", {"operation": operation})
            if exit_code != 0 or mcp_error or not _json_equal(described, mcp_described):
                _fail(f"{source}: describe_operation CLI/MCP discovery differs")
            steps = vector["prerequisites"] + [vector["invocation"]] + vector["postconditions"]
            observations: dict[str, tuple[list[dict[str, Any]], list[dict[str, Any]]]] = {}
            for label in ("CLI", "MCP"):
                with ReplayGateway(steps) as gateway:
                    documents = []
                    for index, step in enumerate(steps):
                        document, _ = _run_step(head, step, gateway.url, label)
                        documents.append(document)
                        if len(gateway.captured) != index + 1:
                            _fail(f"{source}:{label}/steps/{index}: expected exactly one Gateway request")
                    gateway.assert_consumed(f"{source}:{label}")
                    observations[label] = (documents, gateway.captured)
            cli_docs, cli_requests = observations["CLI"]
            mcp_docs, mcp_requests = observations["MCP"]
            for index, step in enumerate(steps):
                cli_doc = _mask_result(cli_docs[index], step, f"{source}:CLI/steps/{index}")
                mcp_doc = _mask_result(mcp_docs[index], step, f"{source}:MCP/steps/{index}")
                if not _json_equal(cli_doc, mcp_doc):
                    _fail(f"{source}:/steps/{index}: canonical CLI/MCP documents differ: {_canonical(cli_doc)} != {_canonical(mcp_doc)}")
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
                if not _json_equal(requests[0], requests[1]):
                    _fail(f"{source}:/steps/{index}: captured Gateway requests differ: {_canonical(requests[0])} != {_canonical(requests[1])}")
            # Malformed Payload is a generic validation error and must never reach the Gateway.
            invalid = copy.deepcopy(vector["invocation"])
            cli_args, tool, mcp_args = _call_args(invalid, "{invalid")
            envelope = invalid["envelope"]
            with ReplayGateway([]) as gateway:
                cli_exit, cli_error = head.cli(cli_args, gateway.url, envelope["tenant"], envelope.get("actor"))
                mcp_error, mcp_document = head.mcp(tool, mcp_args, gateway.url,
                                                    envelope["tenant"], envelope.get("actor"))
                gateway.assert_consumed(f"{source}:malformed-Payload")
            if cli_exit != 2 or not mcp_error or not _json_equal(cli_error, mcp_document) \
                    or cli_error.get("error", {}).get("code") != "validation_failed":
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
                    document, _ = _run_step(head, failure, gateway.url, label, verify_assertions=False)
                    gateway.assert_consumed(f"{source}:{label}/gateway-error")
                    failed[label] = (document, gateway.captured[0])
            cli_error_document, cli_error_request = failed["CLI"]
            mcp_error_document, mcp_error_request = failed["MCP"]
            if not _json_equal(cli_error_document, mcp_error_document) \
                    or cli_error_document.get("error", {}).get("code") != "gateway_error" \
                    or cli_error_document["error"].get("status") != 503:
                _fail(f"{source}: Gateway error documents differ or lost status: {cli_error_document!r}, {mcp_error_document!r}")
            expected = failure["expectedGateway"]
            normalized_error_requests = []
            for label, request in (("CLI", cli_error_request), ("MCP", mcp_error_request)):
                normalized = copy.deepcopy(request)
                normalized["body"] = _mask(normalized["body"], failure, f"{source}:{label}/gateway-error/body")
                _expect_fields(normalized, {"method": expected["method"], "path": expected["path"],
                                            "body": expected["body"]}, f"{source}:{label}/gateway-error")
                normalized_error_requests.append(normalized)
            if not _json_equal(normalized_error_requests[0], normalized_error_requests[1]):
                _fail(f"{source}: Gateway error requests differ between Heads")
            print(f"PASS {operation}: discovery, {len(steps)} reset Gateway step(s), documents, requests, validation/Gateway error parity")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", type=Path, required=True, help="built test-only ConformanceHost DLL")
    parser.add_argument("--artifact", type=Path, required=True, help="immutable Contracts .nupkg used by the host")
    parser.add_argument("--expected-package-id", required=True)
    parser.add_argument("--expected-package-version", required=True)
    parser.add_argument("--timeout", type=float, default=15)
    parser.add_argument("vectors", nargs="+", type=Path)
    args = parser.parse_args(argv)
    try:
        run(args.host.resolve(), args.artifact.resolve(),
            (args.expected_package_id, args.expected_package_version), args.vectors, args.timeout)
    except (VectorError, OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
