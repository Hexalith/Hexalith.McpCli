#!/usr/bin/env python3
"""Read-only gate audit before a normal squash merge with privileged credentials."""
import argparse
import datetime
import json
from pathlib import Path
import subprocess


def api(endpoint):
    result = subprocess.run(["gh", "api", endpoint], capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


parser = argparse.ArgumentParser()
parser.add_argument("repository")
parser.add_argument("number", type=int)
parser.add_argument("expected_head")
parser.add_argument("output", type=Path)
parser.add_argument("--required-workflow", action="append", default=[])
args = parser.parse_args()
prefix = "repos/" + args.repository
pull = api(f"{prefix}/pulls/{args.number}")
live = api(f"{prefix}/git/ref/heads/main")["object"]["sha"]
rules = api(f"{prefix}/rules/branches/main")
legacy_result = subprocess.run(["gh", "api", f"{prefix}/branches/main/protection"], capture_output=True, text=True)
legacy = json.loads(legacy_result.stdout)
checks = api(f"{prefix}/commits/{args.expected_head}/check-runs?per_page=100")
statuses = api(f"{prefix}/commits/{args.expected_head}/status?per_page=100")
comparison = api(f"{prefix}/compare/{live}...{args.expected_head}")
runs = api(f"{prefix}/actions/runs?head_sha={args.expected_head}&event=pull_request&per_page=100")
rollup = json.loads(subprocess.check_output([
    "gh", "pr", "view", str(args.number), "--repo", args.repository,
    "--json", "mergeStateStatus,reviewDecision,statusCheckRollup",
], text=True))
findings = []
if legacy_result.returncode == 0 or legacy.get("status") != "404":
    findings.append("Legacy branch protection requires separate complete verification")
if pull["state"] != "open" or pull["draft"] or pull["head"]["sha"] != args.expected_head:
    findings.append("PR state/draft/head differs from the reviewed candidate")
if pull["base"]["ref"] != "main" or pull["base"]["sha"] != live or comparison["behind_by"] != 0:
    findings.append("PR is not up to date with exact live main")
if checks["total_count"] > len(checks["check_runs"]) or runs["total_count"] > len(runs["workflow_runs"]):
    findings.append("Pagination prevents a complete bounded gate audit")
required = []
for rule in rules:
    if rule["type"] == "required_status_checks":
        for item in rule["parameters"]["required_status_checks"]:
            candidates = [check for check in checks["check_runs"] if
                          check["name"] == item["context"] and
                          check["app"]["id"] == item["integration_id"]]
            latest = max(candidates, key=lambda check: check["id"]) if candidates else None
            passed = bool(latest and latest["status"] == "completed" and latest["conclusion"] == "success")
            required.append({**item, "passed": passed, "check": latest})
            if not passed:
                findings.append("Required context/app not successful: " + item["context"])
    if rule["type"] == "pull_request" and rule["parameters"]["required_approving_review_count"]:
        if rollup["reviewDecision"] != "APPROVED":
            findings.append("Required reviews are not approved")
paths = [".github/workflows/ci.yml", *args.required_workflow]
for path in paths:
    candidates = [run for run in runs["workflow_runs"] if run["path"] == path]
    latest = max(candidates, key=lambda run: (run["id"], run["run_attempt"])) if candidates else None
    if not latest or latest["status"] != "completed" or latest["conclusion"] != "success":
        findings.append("Ordinary exact-head PR qualification not successful: " + path)
# Title edits and normal reruns may leave cancelled checks beside their later
# replacements on the same source. Keep every attempt in evidence, but evaluate
# the latest exact context/app rather than treating superseded attempts as live.
latest_checks = {}
for check in checks["check_runs"]:
    identity = (check["name"], check["app"]["id"])
    if identity not in latest_checks or check["id"] > latest_checks[identity]["id"]:
        latest_checks[identity] = check
for check in latest_checks.values():
    if check["status"] != "completed" or check["conclusion"] not in ("success", "neutral", "skipped"):
        findings.append("Unsettled or nonpassing latest PR check: " + check["name"])
if statuses["state"] not in ("success", "pending") or (statuses["state"] == "pending" and statuses["statuses"]):
    findings.append("Commit status API reports nonpassing contexts")
if rollup["mergeStateStatus"] != "CLEAN" or pull["mergeable"] is not True:
    findings.append("GitHub does not report a clean merge state")
report = {
    "checkedAtUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "result": "ready" if not findings else "pending", "findings": findings,
    "readOnly": True, "repository": args.repository, "number": args.number,
    "expectedHead": args.expected_head, "liveMain": live, "pull": pull,
    "effectiveRules": rules, "legacyProtectionResponse": legacy, "requiredContexts": required, "checkRuns": checks,
    "commitStatuses": statuses, "workflowRuns": runs, "rollup": rollup,
    "latestChecksByExactContextAndApp": list(latest_checks.values()),
    "comparison": {name: comparison[name] for name in ("status", "ahead_by", "behind_by")},
}
args.output.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"result": report["result"], "findings": findings, "liveMain": live}))
raise SystemExit(bool(findings))
