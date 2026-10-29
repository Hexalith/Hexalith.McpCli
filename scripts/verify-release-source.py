#!/usr/bin/env python3
"""Require exact, clean release source and independent bootstrap/commitlint results."""

import argparse
import json
import os
import re
import subprocess
import sys


def failure_detail(error):
    detail = str(error)
    if isinstance(error, subprocess.CalledProcessError) and error.stderr:
        detail += f"\n{error.stderr.strip()}"
    credentials = {os.environ.get(name, "") for name in
                   ("GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN", "NUGET_API_KEY")}
    for credential in sorted(credentials - {""}, key=len, reverse=True):
        detail = detail.replace(credential, "[REDACTED]")
    return re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", detail)


def github_json(endpoint: str, *parameters: str):
    result = subprocess.run(
        ["gh", "api", "--method", "GET", endpoint, *parameters],
        check=True, capture_output=True, text=True,
    )
    return json.loads(result.stdout)


# Job and step names are the executed blocking lanes in the pinned CI workflows.
STAGING_JOBS = {
    'ci / build-and-test': ['Unit tests (Tier 1, Microsoft.Testing.Platform)', 'Fail on blocking test failures'],
    'ci / aspire-tests': ['Prepare Aspire tier', 'Run Aspire hook'],
    'conformance-vector-contract': ['Pack and validate the shared vector contract without a Head or Gateway'],
    'conformance-vector-loopback': ['Run packaged Contracts through CLI and MCP against reset Gateway replay'],
    'enrolled-module-conformance': ['Restore and build exact production catalog', 'Benchmark first v1 Catalog construction in a fresh process', 'Validate approved artifacts, complete vectors and both heads'],
    'topology-vector-discovery': ['Build and discover every live vector plus the independent smoke without starting source services'],
}


STAGING_COMMITLINT_JOBS = {'commitlint / commitlint': ['Validate commit messages']}

def verify_jobs(repository, latest, required):
    jobs = []
    page = 1
    while True:
        response = github_json(f"repos/{repository}/actions/runs/{latest['id']}/attempts/{latest['run_attempt']}/jobs",
                               '-f', 'per_page=100', '-f', f'page={page}')
        jobs.extend(response['jobs'])
        if len(jobs) >= response['total_count']:
            break
        if not response['jobs']:
            raise ValueError('Incomplete workflow job results.')
        page += 1
    validate_jobs(jobs, required)
    return jobs


def validate_jobs(jobs, required):
    for name, steps in required.items():
        matches = [job for job in jobs if job['name'] == name]
        if len(matches) != 1 or matches[0]['status'] != 'completed' or matches[0]['conclusion'] != 'success':
            raise ValueError(f'Required job {name} was missing, skipped or unsuccessful.')
        for step in steps:
            found = [item for item in matches[0]['steps'] if item['name'] == step]
            if len(found) != 1 or found[0]['status'] != 'completed' or found[0]['conclusion'] != 'success':
                raise ValueError(f'Required step {name}: {step} was missing, skipped or unsuccessful.')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sha")
    parser.add_argument("ref")
    parser.add_argument("phase")
    parser.add_argument("--tagged-recovery", metavar="VERSION")
    parser.add_argument("--staging", action="store_true")
    parser.add_argument("--output", type=str)
    args = parser.parse_args()
    try:
        if args.phase != "bootstrap" and not (args.phase == "paired" and args.staging):
            raise ValueError("Only bootstrap releases are supported; paired release remains deferred.")
        if args.staging and (args.phase != "paired" or args.tagged_recovery or not args.output):
            raise ValueError("Paired staging requires fresh output and cannot recover a release.")
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
        if args.tagged_recovery is not None:
            tag = f"refs/tags/v{args.tagged_recovery}^{{commit}}"
            tagged_sha = subprocess.run(
                ["git", "rev-parse", "--verify", tag],
                check=True, capture_output=True, text=True,
            ).stdout.strip()
            if tagged_sha != args.sha:
                raise ValueError("Recovery tag does not match the exact checked-out release SHA.")
            remote_tag = github_json(
                f"repos/{repository}/git/ref/tags/v{args.tagged_recovery}")["object"]
            for _ in range(4):
                if remote_tag["type"] == "commit":
                    break
                if remote_tag["type"] != "tag":
                    raise ValueError("Remote recovery tag does not resolve to a commit.")
                remote_tag = github_json(
                    f"repos/{repository}/git/tags/{remote_tag['sha']}")["object"]
            if remote_tag["type"] != "commit" or remote_tag["sha"] != args.sha:
                raise ValueError("Remote recovery tag does not match the exact release SHA.")
            fetched_main = subprocess.run(
                ["git", "rev-parse", "origin/main"],
                check=True, capture_output=True, text=True,
            ).stdout.strip()
            if fetched_main != live_main:
                raise ValueError("Current main moved after recovery checkout; fetch and retry.")
            ancestor = subprocess.run(
                ["git", "merge-base", "--is-ancestor", args.sha, "origin/main"],
                check=False, capture_output=True, text=True,
            )
            if ancestor.returncode != 0:
                raise ValueError("Recovery tag is not an ancestor of current main.")
        elif args.sha != live_main:
            raise ValueError("Dispatch SHA is not the current main SHA; main may have moved during approval.")
        gates = {}
        workflows = ("ci.yml", "commitlint.yml") if args.staging else ("bootstrap-package.yml", "commitlint.yml")
        for workflow in workflows:
            response = github_json(
                f"repos/{repository}/actions/workflows/{workflow}/runs",
                "-f", "branch=main", "-f", "event=push", "-f", f"head_sha={args.sha}", "-f", "per_page=100",
            )
            runs = [run for run in response["workflow_runs"] if
                    run["head_sha"] == args.sha and run["head_branch"] == "main" and run["event"] == "push"]
            latest = max(runs, key=lambda run: (run["run_number"], run["run_attempt"])) if runs else None
            if latest is None or latest["status"] != "completed" or latest["conclusion"] != "success":
                raise ValueError(f"No successful latest {workflow} push run exists for {args.sha}.")
            if args.staging:
                required = STAGING_JOBS if workflow == 'ci.yml' else STAGING_COMMITLINT_JOBS
                jobs = verify_jobs(repository, latest, required)
                gates[workflow] = {'run_id': latest['id'], 'run_attempt': latest['run_attempt'],
                                   'url': latest['html_url'], 'source_sha': latest['head_sha'],
                                   'status': latest['status'], 'conclusion': latest['conclusion'], 'jobs': jobs}
            print(f"Verified {workflow}: {latest['html_url']}")
        if args.tagged_recovery is None:
            print(f"Verified current main source {args.sha}")
        else:
            print(f"Verified tagged recovery source {args.sha} on current main {live_main}")
        if args.staging:
            from paired_release import module, write_new
            prerequisites = module('verify-paired-prerequisites').verify()
            write_new(args.output, {'schema': 'mcpcli-paired-source/v1', 'source_sha': args.sha,
                                    'source_clean': True, 'current_main': live_main, 'gates': gates,
                                    'fr22': prerequisites})
        return 0
    except (ValueError, KeyError, TypeError, subprocess.CalledProcessError, OSError) as error:
        print(f"Release source gate failed: {failure_detail(error)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
