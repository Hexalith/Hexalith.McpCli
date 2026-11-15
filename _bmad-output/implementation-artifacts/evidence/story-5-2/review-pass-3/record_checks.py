#!/usr/bin/env python3
"""Record Story 5.2 code review pass 3 checks into a new evidence folder.

Runs the standalone verifier, the verifier process suite, the runner controls,
four focused sub-condition mutants (each against the prior and current suites)
and a fresh whole-guard sweep. Mutants run in a private snapshot; nothing in
the repository is modified except the requested new output folder. Give the
run a private TMPDIR, as the review-pass-1 README recipe does.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

EVIDENCE = Path(__file__).resolve().parent.parent
ROOT = EVIDENCE.parents[3]
SCRIPT = EVIDENCE / "verify_class_map.py"
TESTS = EVIDENCE / "test_verify_class_map.py"
MAP = Path("_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/AD-23-capability-class-map.json")
MUTATIONS = [
    {"id": "approval-limit-nonblank", "test": "test_agreed_approval_limit_must_be_nonblank",
     "before": 'require(nonblank(expected.get("approvalLimit")) and inventory.get("approvalLimit") == expected["approvalLimit"],',
     "after": 'require(inventory.get("approvalLimit") == expected["approvalLimit"],'},
    {"id": "map-owned-restriction-evidence", "test": "test_map_owned_restriction_evidence_alone_blocks_admission",
     "before": "            restrictions.setdefault(row_id, evidence)\n",
     "after": "            pass\n"},
    {"id": "fail-channel-keyerror", "test": "test_missing_member_uses_fail_channel",
     "before": "except (InvalidMap, KeyError, TypeError, ValueError, OSError, AttributeError)",
     "after": "except (InvalidMap, TypeError, ValueError, OSError, AttributeError)"},
    {"id": "fail-channel-typeerror", "test": "test_wrong_member_type_uses_fail_channel",
     "before": "except (InvalidMap, KeyError, TypeError, ValueError, OSError, AttributeError)",
     "after": "except (InvalidMap, KeyError, ValueError, OSError, AttributeError)"},
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def run(command, cwd, timeout):
    result = subprocess.run(command, cwd=cwd, capture_output=True, check=False, timeout=timeout)
    lines = result.stderr.decode("utf-8").splitlines()
    return {"command": [str(part) for part in command], "exitCode": result.returncode,
            "stdout": result.stdout.decode("utf-8"), "stderr": result.stderr.decode("utf-8"),
            "stdoutSha256": sha(result.stdout), "stderrSha256": sha(result.stderr),
            "completedSuite": any(re.fullmatch(r"Ran \d+ tests? in .+s", line) for line in lines),
            "suiteOk": "OK" in lines,
            "failedTests": [line.split()[1] for line in lines if line.startswith("FAIL: ")],
            "erroredTests": [line.split()[1] for line in lines if line.startswith("ERROR: ")]}


def killed(result, test):
    return (result["exitCode"] == 1 and result["completedSuite"] and not result["erroredTests"]
            and test in result["failedTests"])


def survived(result):
    return result["exitCode"] == 0 and result["completedSuite"] and result["suiteOk"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--prior-ref", required=True, help="commit whose test suite predates the new cases")
    parser.add_argument("--timeout-seconds", type=float, default=300)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    document = json.loads((ROOT / MAP).read_bytes())
    inputs = [SCRIPT.relative_to(ROOT), TESTS.relative_to(ROOT), (EVIDENCE / "verifier.stdout.txt").relative_to(ROOT),
              MAP, Path(document["decision"]["path"]), Path(document["approvalPath"]),
              *[Path(item["path"]) for item in document["inventories"]]]
    snapshot = {path: (ROOT / path).read_bytes() for path in inputs}
    prior_tests = subprocess.run(["git", "-C", str(ROOT), "show", f"{args.prior_ref}:{TESTS.relative_to(ROOT).as_posix()}"],
                                 capture_output=True, check=True).stdout
    python = [sys.executable, "-I", "-B"]
    suite = [*python, TESTS.relative_to(ROOT).as_posix(), "-v"]
    receipt = {"schema": "story-5-2-review-pass-3-checks/v1", "startedAt": started,
               "inputs": {path.as_posix(): sha(data) for path, data in snapshot.items()},
               "inputSource": "single exact-byte snapshot before execution",
               "recorderSha256": sha(Path(__file__).read_bytes()),
               "priorRef": args.prior_ref, "priorTestsSha256": sha(prior_tests)}

    verifier = run([*python, SCRIPT.relative_to(ROOT)], ROOT, args.timeout_seconds)
    verifier["stdoutByteIdenticalToAdoptedCapture"] = verifier["stdout"].encode("utf-8") == snapshot[inputs[2]]
    receipt["standaloneVerifier"] = verifier
    receipt["runnerControls"] = run([*python, (EVIDENCE / "review-pass-1/test_run_guard_removal.py").relative_to(ROOT), "-v"],
                                    ROOT, args.timeout_seconds)
    with tempfile.TemporaryDirectory(prefix="story-5-2-pass-3-") as temporary:
        template = Path(temporary) / "template"
        for path, data in snapshot.items():
            (template / path).parent.mkdir(parents=True, exist_ok=True)
            (template / path).write_bytes(data)
        receipt["currentSuite"] = run(suite, template, args.timeout_seconds)
        source = snapshot[inputs[0]].decode("utf-8")
        mutations = []
        for mutation in MUTATIONS:
            assert source.count(mutation["before"]) == 1, mutation["id"]
            mutant = source.replace(mutation["before"], mutation["after"]).encode("utf-8")
            job = Path(temporary) / mutation["id"]
            shutil.copytree(template, job)
            (job / inputs[0]).write_bytes(mutant)
            current = run(suite, job, args.timeout_seconds)
            (job / inputs[1]).write_bytes(prior_tests)
            prior = run(suite, job, args.timeout_seconds)
            mutations.append({**mutation, "mutatedScriptSha256": sha(mutant),
                              "priorSuite": prior, "priorSuiteSurvived": survived(prior),
                              "currentSuite": current, "currentSuiteKilled": killed(current, mutation["test"])})
        receipt["mutations"] = mutations
    sweep = output / "guard-sweep"
    receipt["guardSweep"] = run([*python, (EVIDENCE / "review-pass-1/run_guard_removal.py").relative_to(ROOT),
                                 "--output", sweep.relative_to(ROOT) if sweep.is_relative_to(ROOT) else sweep, "--jobs", "4"], ROOT, args.timeout_seconds * 4)
    sweep_summary = json.loads((sweep / "results.json").read_text(encoding="utf-8"))["summary"]
    receipt["guardSweep"].update(runnerSha256=sha((EVIDENCE / "review-pass-1/run_guard_removal.py").read_bytes()),
                                 results="guard-sweep/results.json", summary=sweep_summary)
    receipt["summary"] = {
        "standaloneVerifierPassed": verifier["exitCode"] == 0 and verifier["stderr"] == ""
        and verifier["stdoutByteIdenticalToAdoptedCapture"],
        "currentSuitePassed": survived(receipt["currentSuite"]),
        "runnerControlsPassed": survived(receipt["runnerControls"]),
        "mutantsSurvivingPriorSuite": sum(item["priorSuiteSurvived"] for item in mutations),
        "mutantsKilledByCurrentSuite": sum(item["currentSuiteKilled"] for item in mutations),
        "mutantCount": len(mutations),
        "guardSweep": sweep_summary,
    }
    receipt["finishedAt"] = datetime.now(timezone.utc).isoformat()
    (output / "checks.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    summary = receipt["summary"]
    print(json.dumps(summary), flush=True)
    passed = (summary["standaloneVerifierPassed"] and summary["currentSuitePassed"] and summary["runnerControlsPassed"]
              and summary["mutantsSurvivingPriorSuite"] == summary["mutantsKilledByCurrentSuite"] == len(mutations)
              and sweep_summary["survived"] == sweep_summary["error"] == 0
              and sweep_summary["killed"] == sweep_summary["guardCount"] > 0)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
