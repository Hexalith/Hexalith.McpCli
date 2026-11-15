#!/usr/bin/env python3
"""Remove each require guard in an isolated copy and run the process suite.

All disposable repository copies respect TMPDIR; give the run a private one,
as the portable recipe in this folder's README does. (`run-with-temp` is an
untracked helper on the recording workstation only.)
Only the requested output packet survives, including each unittest transcript.
No source inspection assertion is added to the behavioral process tests.
"""

import argparse
import ast
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=4, choices=range(1, 9))
    parser.add_argument("--timeout-seconds", type=float, default=120)
    args = parser.parse_args()
    if args.timeout_seconds <= 0:
        parser.error("--timeout-seconds must be positive")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    evidence = Path(__file__).resolve().parent.parent
    root = evidence.parents[3]
    script = evidence / "verify_class_map.py"
    tests = evidence / "test_verify_class_map.py"
    # Resolve every input from the packet itself, without module names/counts.
    map_path = Path("_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/AD-23-capability-class-map.json")
    map_bytes = (root / map_path).read_bytes()
    document = json.loads(map_bytes)
    inputs = [script.relative_to(root), tests.relative_to(root),
              (evidence / "verifier.stdout.txt").relative_to(root), map_path,
              Path(document["decision"]["path"]), Path(document["approvalPath"]),
              *[Path(item["path"]) for item in document["inventories"]]]
    # Capture each source once. Receipts and mutations describe these bytes,
    # even if a live workspace input changes while the subprocesses run.
    snapshot = {path: map_bytes if path == map_path else (root / path).read_bytes() for path in inputs}
    command = [sys.executable, "-I", "-B", tests.relative_to(root).as_posix(), "-v"]
    started = datetime.now(timezone.utc).isoformat()

    def execute(job_root, label):
        before = time.monotonic()
        returncode, timed_out, process_error = None, False, None
        try:
            result = subprocess.run(command, cwd=job_root, capture_output=True,
                                    check=False, timeout=args.timeout_seconds)
            stdout, stderr, returncode = result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired as error:
            stdout, stderr = error.stdout or b"", error.stderr or b""
            timed_out = True
            process_error = f"process timed out after {args.timeout_seconds} seconds"
        except OSError as error:
            stdout, stderr, process_error = b"", b"", str(error)
        stdout_path, stderr_path = output / f"{label}.stdout.txt", output / f"{label}.stderr.txt"
        stdout_path.write_bytes(stdout)
        stderr_path.write_bytes(stderr)
        lines = stderr.decode("utf-8", errors="replace").splitlines()
        return {"returncode": returncode, "seconds": round(time.monotonic() - before, 3),
                "timedOut": timed_out, "processError": process_error,
                "stdout": stdout_path.name, "stderr": stderr_path.name,
                "stdoutSha256": digest(stdout_path), "stderrSha256": digest(stderr_path),
                "assertionFailures": [line for line in lines if line.startswith("FAIL: ")],
                "testErrors": [line for line in lines if line.startswith("ERROR: ")],
                "completedSuite": any(re.fullmatch(r"Ran \d+ tests? in .+s", line) for line in lines),
                "failedSuite": any(line.startswith("FAILED (") for line in lines)}

    with tempfile.TemporaryDirectory(prefix="story-5-2-guard-removal-") as temporary:
        scratch = Path(temporary)
        template = scratch / "template"
        for relative, data in snapshot.items():
            target = template / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        input_hashes = {path.as_posix(): digest(template / path) for path in inputs}
        text = (template / script.relative_to(root)).read_text()
        guards = sorted(
            (node for node in ast.walk(ast.parse(text)) if isinstance(node, ast.Expr)
             and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name)
             and node.value.func.id == "require"), key=lambda node: node.lineno,
        )
        baseline_root = scratch / "baseline"
        shutil.copytree(template, baseline_root)
        baseline = execute(baseline_root, "baseline")
        baseline_passed = (baseline["returncode"] == 0 and baseline["completedSuite"]
                           and not baseline["assertionFailures"] and not baseline["testErrors"]
                           and baseline["processError"] is None)

        def mutate(index_and_node):
            index, node = index_and_node
            label = f"guard-{index:02d}-line-{node.lineno}"
            job_root = scratch / label
            shutil.copytree(template, job_root)
            lines = text.splitlines(keepends=True)
            lines[node.lineno - 1] = " " * node.col_offset + "pass\n"
            for line in range(node.lineno, node.end_lineno):
                lines[line] = "\n"
            (job_root / script.relative_to(root)).write_text("".join(lines))
            result = execute(job_root, label)
            result.update(id=label, line=node.lineno, endLine=node.end_lineno,
                          guard=ast.get_source_segment(text, node))
            completed = result["completedSuite"] and result["processError"] is None and not result["testErrors"]
            result["outcome"] = (
                "killed" if completed and result["returncode"] == 1 and result["failedSuite"]
                and result["assertionFailures"] else "survived" if completed and result["returncode"] == 0
                and not result["assertionFailures"] else "error"
            )
            shutil.rmtree(job_root)
            print(f"{label}: {result['outcome']}", flush=True)
            return result

        results = []
        if baseline_passed:
            with ThreadPoolExecutor(max_workers=args.jobs) as executor:
                results = list(executor.map(mutate, enumerate(guards, 1)))

    summary = {"guardCount": len(guards),
               **{outcome: sum(item["outcome"] == outcome for item in results)
                  for outcome in ("killed", "survived", "error")}}
    receipt = {"startedAt": started, "finishedAt": datetime.now(timezone.utc).isoformat(),
               "command": command, "cwd": "private temporary repository copy", "jobs": args.jobs,
               "mutation": "Replace one complete require(...) expression statement with pass; keep line numbering.",
               "inputs": input_hashes, "inputSource": "frozen template before execution",
               "timeoutSeconds": args.timeout_seconds, "baselinePassed": baseline_passed,
               "baseline": baseline, "summary": summary, "guards": results}
    (output / "results.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(summary), flush=True)
    return 0 if baseline_passed and summary["survived"] == summary["error"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
