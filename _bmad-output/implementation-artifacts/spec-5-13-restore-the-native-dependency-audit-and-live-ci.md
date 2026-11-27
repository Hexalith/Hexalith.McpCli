---
title: 'Restore the native dependency audit and live CI'
type: 'bugfix'
created: '2026-11-27'
status: 'in-progress'
route: 'dispatch'
baseline_commit: '56176163c74f685982887ac8b369a1aff7de6811'
review_loop_iteration: 0
context:
  - '{project-root}/tools/live-topology/README.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `native_audit.online_advisories` retries HTTP fetches against the same unchanged NuGet HTTP cache and fails with opaque hashes whenever `data.nuget.org` advisory pages differ, lacking semantic diagnostics or rotation recovery and blocking exact-commit Linux/Windows/macOS qualification.

**Approach:** Add advisory page identity, retrieval timestamps, semantic diff against the restored package graph, and outcome classification (`match`, `confirmed_rotation`, `unavailable`, `persistent_mismatch`, `advisory_affecting_graph`) to `native_audit.py` and `ci.py`, with at most one fresh isolated restore and re-audit on confirmed rotation. Implement and verify locally without committing or pushing; leave `sprint-status.yaml` at `in-progress` with AC3 hosted CI qualification (Linux active live set + Windows + macOS on the exact candidate SHA) deferred until pushed (e.g., after Story 5.27 trims live plans to 8+2).

## Boundaries & Constraints

**Always:**
- Preserve unsuppressed `NuGetAudit=true`, `NuGetAuditMode=all`, `NuGetAuditLevel=low`, `TreatWarningsAsErrors=true`, empty `NoWarn`/`WarningsNotAsErrors`, exact package content/archive SHA-512 coverage, and official `https://data.nuget.org/v3-vulnerabilities/` origin checks.
- Confirm rotation only when cached and live indexes are valid official indexes, live index and every live page return HTTP 200 valid JSON, >=1 page `@updated` strictly advances with zero regressions, and every page with unchanged `@id` and `@updated` matches cache.
- Bound recovery to <=1 fresh isolated restore in new empty package and HTTP caches, verifying policy, package bytes, and live advisory equality before acceptance.
- Record page identities (`@name`, `@id`, `@updated`, SHA-256, HTTP status/headers), cache/online UTC retrieval times, semantic diff with restored-package intersection, classification, and recovery attempt in task-owned evidence.
- Fail closed on unavailable feeds, persistent mismatches, second mismatches after the single retry, or vulnerable/policy-violating dependencies (`NU1900`–`NU1904`); guard every new check with a removal-sensitive test.

**Never:**
- Edit `Hexalith.CiCd`-owned files (`.github/workflows/**`, `.github/hexalith-ci.json`, `.github/dependabot.yml`, `references/Hexalith.Builds`), `references/**`, `src/**`, `native-runtime*.json`, or approved vectors/plans.
- Retry in a reused cache, allow >1 recovery attempt, weaken audits, commit/push during this build, or accept preflight/discovery receipts as live qualification.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Stable feed | Cache matches live HTTP 200 feed (exact or equivalent JSON) | `match`; 0 retries; sealed in `preparation.json` and `native-reader-audit.json` | N/A |
| Confirmed rotation (source or module) | Live `@updated`/`@id` advances, unchanged pages match cache, all live pages HTTP 200 valid JSON | `confirmed_rotation`; diagnostic saved; 1 fresh isolated restore in new caches passes policy, coverage, and live equality | N/A |
| Persistent mismatch | Unchanged `@id`/`@updated` content drift, regressed `@updated`, or mismatch after 1 retry | `persistent_mismatch`; diagnostic records page IDs, timestamps, semantic diff; no 2nd retry | Raises `ValueError` (`persistent_mismatch` + page) |
| Unavailable feed | `curl` error, HTTP 304/404/500/503, bad JSON, foreign `@id`, or `NU1900` | `unavailable`; diagnostic saved; 0 retries | Raises `ValueError`/`RuntimeError` (`unavailable`) |
| Policy-violating dependency | Restore fails with `NU1901`–`NU1904` (authoritative version-range audit), `project.assets.json` logs advisory/warning, or weakened policy | `advisory_affecting_graph` / policy error; semantic diff notes intersecting restored package IDs | Fails closed naming advisory/policy violation |
| Module-audit snapshot drift | `module-audit-<i>` fresh restore sees newer live feed than `proven_advisories` | Verifies live feed: accepts confirmed forward rotation matching live feed, or <=1 fresh retry if behind live feed | Fails closed on mismatch/unavailable/violation |

</frozen-after-approval>

## Code Map

- `tools/live-topology/native_audit.py:13-244` -- Advisory verification, `require_policy`, `online_advisories`, `audit_project`, `require_audit`. Add header/UTC-timestamp capture, ISO-8601 `@updated` comparison, semantic diff with restored-package intersection, classifier, diagnostic writer, and <=1 fresh retry in `audit_project`.
- `tools/live-topology/ci.py:498-537,576-580,724-726,867-959,1097-1112` -- `prepare()`, `prove_source_advisories()`, `require_prepared_provenance()`, `run_lane()`. Wire <=1 fresh isolated source re-restore (`packages-retry-1`, `source-http-retry-1`), update `receipt['nugetPackages']`/`nugetHttpCache` and `source_environment`, save diagnostics under `evidence`, and bind winning caches to builds and execution.
- `tools/live-topology/test_native_audit.py:1-220` -- Unit tests for all matrix scenarios, diagnostics/diff assertions, guard-removal checks, and `audit_project` 1× recovery.
- `tools/live-topology/test_ci.py:99-184,991-1029` -- Fake `dotnet`/`curl` modes and `prepare()` tests for source rotation recovery, 2nd-rotation refusal, unavailable feed, and `NU1902` failure.
- `tools/live-topology/README.md:263-268` -- Document advisory rotation diagnostics and bounded single-attempt fresh isolated restore.
- `_bmad-output/implementation-artifacts/sprint-status.yaml:106` -- Update `5-13` status preserving comments.

## Tasks & Acceptance

**Execution:**
- [ ] `tools/live-topology/native_audit.py` -- Implement metadata/header/timestamp capture, semantic diff against restored package IDs, classification, diagnostic output, and <=1 fresh isolated retry in `audit_project` -- satisfies AC1 and AC2.
- [ ] `tools/live-topology/ci.py` -- Pass restored package graphs to advisory proof, perform <=1 fresh isolated source re-restore on `confirmed_rotation`, re-verify policy/coverage/advisories, save diagnostics in `evidence`, and bind winning caches to builds and `run_lane()` -- ensures only fully verified restores pass.
- [ ] `tools/live-topology/test_native_audit.py` -- Test every I/O matrix row and guard-removal case (stable, rotation, unchanged-ID drift, regressed `@updated`, 2nd-mismatch refusal, outage/304/503/bad-JSON/foreign-origin, `NU1900`–`NU1904`, `audit_project` 1× retry) -- pins all guards.
- [ ] `tools/live-topology/test_ci.py` -- Test `prepare()` source rotation recovery (fresh caches flowing to builds, `readerAudit`, and `run-ci.sh`), 2nd-rotation refusal, unavailable feed, and `NU1902` failure -- proves hook wiring offline.
- [ ] `tools/live-topology/README.md` -- Document advisory diagnostics and 1× fresh isolated restore -- keeps docs aligned.
- [ ] `_bmad-output/implementation-artifacts/sprint-status.yaml` -- Set `5-13-restore-the-native-dependency-audit-and-live-ci` to `in-progress` with a concise comment noting AC1/AC2 local completion and pending AC3 hosted CI qualification.

**Acceptance Criteria:**
- Given any advisory comparison in preparation or module audit, when it finishes or fails, then a diagnostic record captures page identities, HTTP status/headers, cache/online UTC retrieval times, semantic diff with restored-package intersection, and exact classification.
- Given confirmed rotation, when preparation runs, then <=1 fresh isolated restore executes in new caches and passes only after full policy, byte-coverage, and live-advisory verification; any second mismatch, unavailable feed, or vulnerable/policy-violating dependency fails closed.
- Given this local-only build scope, when local verification completes, then `sprint-status.yaml` stays `in-progress` (never `done`) with no git commit/push, explicitly recording AC3 (exact-SHA hosted Linux live lane + Windows + macOS pass) as remaining for post-push qualification.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Verification

**Commands:**
- `python3 -m unittest discover -v -s tools/live-topology -p 'test_*.py'` -- expected: all live-topology tests pass.
- `python3 -m unittest discover -v -s scripts/tests -p 'test_*.py'` -- expected: all scripts tests pass.
- `dotnet restore Hexalith.McpCli.slnx && dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror && dotnet test tests/Hexalith.McpCli.Manifest.Tests --no-build --configuration Release` -- expected: 0 warnings, Manifest tests pass.
- `python3 references/Hexalith.Builds/check.py` -- expected: exit 0 before any push.

**Manual checks (if no CLI):**
- On hosted CI for the candidate SHA, confirm Linux `ci / Build and tests` (all active live vectors + `smoke` + `boundary`), `windows-windows-product`, and `windows-macos-product` all succeed.
