#!/usr/bin/env python3
"""Require the current main SHA and its independent bootstrap/commitlint results."""

import argparse
import json
import os
import re
import subprocess
import sys


def github_json(endpoint: str, *parameters: str):
    result = subprocess.run(
        ["gh", "api", "--method", "GET", endpoint, *parameters],
        check=True, capture_output=True, text=True,
    )
    return json.loads(result.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sha")
    parser.add_argument("ref")
    parser.add_argument("phase")
    args = parser.parse_args()
    try:
        if args.phase != "bootstrap":
            raise ValueError("Only bootstrap releases are supported; paired release remains deferred.")
        if args.ref != "refs/heads/main":
            raise ValueError("Release must be dispatched from refs/heads/main.")
        if re.fullmatch(r"[0-9a-f]{40}", args.sha) is None:
            raise ValueError("Release requires an exact source SHA.")
        head = subprocess.run(["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
        if head != args.sha:
            raise ValueError("Checked-out HEAD does not match the exact release source SHA.")
        branch = subprocess.run(["git", "branch", "--show-current"], check=True, capture_output=True, text=True).stdout.strip()
        if branch not in ("", "main"):
            raise ValueError("Checked-out source must be main or its exact detached SHA.")
        changes = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=normal"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        if changes:
            raise ValueError("Release source has uncommitted changes.")
        repository = os.environ["REPOSITORY"]
        live_main = github_json(f"repos/{repository}/git/ref/heads/main")["object"]["sha"]
        if args.sha != live_main:
            raise ValueError("Dispatch SHA is not the current main SHA; main may have moved during approval.")
        for workflow in ("bootstrap-package.yml", "commitlint.yml"):
            response = github_json(
                f"repos/{repository}/actions/workflows/{workflow}/runs",
                "-f", "branch=main", "-f", "event=push", "-f", f"head_sha={args.sha}", "-f", "per_page=100",
            )
            runs = [run for run in response["workflow_runs"] if
                    run["head_sha"] == args.sha and run["head_branch"] == "main" and run["event"] == "push"]
            latest = max(runs, key=lambda run: (run["run_number"], run["run_attempt"])) if runs else None
            if latest is None or latest["status"] != "completed" or latest["conclusion"] != "success":
                raise ValueError(f"No successful latest {workflow} push run exists for {args.sha}.")
            print(f"Verified {workflow}: {latest['html_url']}")
        print(f"Verified current main source {args.sha}")
        return 0
    except (ValueError, KeyError, TypeError, subprocess.CalledProcessError, OSError) as error:
        print(f"Release source gate failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
