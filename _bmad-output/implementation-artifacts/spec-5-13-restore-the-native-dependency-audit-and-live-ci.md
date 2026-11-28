---
title: 'Restore the native dependency audit and live CI'
type: 'bugfix'
created: '2026-11-27'
status: 'done'
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
- [x] `tools/live-topology/native_audit.py` -- Implement metadata/header/timestamp capture, semantic diff against restored package IDs, classification, diagnostic output, and <=1 fresh isolated retry in `audit_project` -- satisfies AC1 and AC2.
- [x] `tools/live-topology/ci.py` -- Pass restored package graphs to advisory proof, perform <=1 fresh isolated source re-restore on `confirmed_rotation`, re-verify policy/coverage/advisories, save diagnostics in `evidence`, and bind winning caches to builds and `run_lane()` -- ensures only fully verified restores pass.
- [x] `tools/live-topology/test_native_audit.py` -- Test every I/O matrix row and guard-removal case (stable, rotation, unchanged-ID drift, regressed `@updated`, 2nd-mismatch refusal, outage/304/503/bad-JSON/foreign-origin, `NU1900`–`NU1904`, `audit_project` 1× retry) -- pins all guards.
- [x] `tools/live-topology/test_ci.py` -- Test `prepare()` source rotation recovery (fresh caches flowing to builds, `readerAudit`, and `run-ci.sh`), 2nd-rotation refusal, unavailable feed, and `NU1902` failure -- proves hook wiring offline.
- [x] `tools/live-topology/README.md` -- Document advisory diagnostics and 1× fresh isolated restore -- keeps docs aligned.
- [x] `_bmad-output/implementation-artifacts/sprint-status.yaml` -- Set `5-13-restore-the-native-dependency-audit-and-live-ci` to `in-progress` with a concise comment noting AC1/AC2 local completion and pending AC3 hosted CI qualification.

**Acceptance Criteria:**
- Given any advisory comparison in preparation or module audit, when it finishes or fails, then a diagnostic record captures page identities, HTTP status/headers, cache/online UTC retrieval times, semantic diff with restored-package intersection, and exact classification.
- Given confirmed rotation, when preparation runs, then <=1 fresh isolated restore executes in new caches and passes only after full policy, byte-coverage, and live-advisory verification; any second mismatch, unavailable feed, or vulnerable/policy-violating dependency fails closed.
- Given this local-only build scope, when local verification completes, then `sprint-status.yaml` stays `in-progress` (never `done`) with no git commit/push, explicitly recording AC3 (exact-SHA hosted Linux live lane + Windows + macOS pass) as remaining for post-push qualification.

## Implementation Notes

- Implemented advisory page identity (`@name`, `@id`, `@updated`, SHA-256, HTTP status/headers with sensitive-header stripping), cache/online UTC timestamps, sub-microsecond ISO-8601 `@updated` comparison, package-level semantic diff with restored-package intersection, exact classification (`match`, `confirmed_rotation`, `unavailable`, `persistent_mismatch`, `advisory_affecting_graph`), `NU1900`–`NU1904` policy/restore classification, diagnostic writing, and bounded 1× fresh isolated retry (`module-audit-<i>-retry-1`) in `tools/live-topology/native_audit.py`. Removed cache-reusing curl retry loops in `online_advisories` and added live verification on forward-rotation snapshot drift against `proven_advisories`.
- Wired `tools/live-topology/ci.py` to pass restored source package graphs to `prove_source_advisories`, execute at most one fresh isolated source re-restore (`packages-retry-1`, `source-http-retry-1`, `source-advisories-retry-1`) with `--force` and full policy/byte-coverage/live-equality verification on `confirmed_rotation`, persist diagnostics under `evidence` (`source-advisories-diagnostic.json`, `source-advisories-attempt-0-diagnostic.json`, `module-audit-<i>-advisory-diagnostic.json`), escalate second mismatches to `persistent_mismatch` without a 2nd retry, and bind winning `nugetPackages`/`nugetHttpCache` to builds, `readerAudit`, `require_prepared_provenance`, and `load_prepared_context`.
- Added unit and hook tests covering every I/O matrix row and guard-removal case in `tools/live-topology/test_native_audit.py` and `tools/live-topology/test_ci.py`, updated `tools/live-topology/README.md`, and left `5-13` at `in-progress` in `_bmad-output/implementation-artifacts/sprint-status.yaml` pending AC3 hosted CI qualification.
- Local verification passed: `python3 -m unittest discover -v -s tools/live-topology -p 'test_*.py'` (309 tests OK), `python3 -m unittest discover -v -s scripts/tests -p 'test_*.py'` (73 tests OK), `dotnet restore Hexalith.McpCli.slnx && dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror && dotnet test tests/Hexalith.McpCli.Manifest.Tests --no-build --configuration Release` (0 warnings, 430/430 passed), and `python3 references/Hexalith.Builds/check.py` (exit 0).
- Note: while local verification was running, external commits (`e3a5080a` and `670319a8`) landed on `main` capturing the workspace changes; this agent performed no git commit or push. AC3 (exact-SHA hosted Linux live lane + Windows + macOS qualification) remains pending hosted CI confirmation.
- Review pass 1 patches applied (unchanged-`@updated` `@id` drift guard, `proven`-mode corrupt-page handling and non-inverted diagnostics, `validate_advisory_index`/`parse_iso8601_utc`/`_is_official_page_url`/`parse_advisory_page`/`require_policy`/`parse_http_headers` hardening, dead `refuse_advisory_mismatch` removal, `priorRotationDiagnostic` preservation across all attempt-1 failures, `prove_source_advisories` missing-index diagnostic routing, `require_prepared_provenance`/`load_prepared_context` symlink & containment guards, `README.md` sealing wording, and all missing unit/hook tests). Concurrent Story 5.25 split-lane `ci.py` findings deferred to `deferred-work.md`.
- Post-patch verification passed: Release restore + `-warnaserror` build (0 warnings), `Manifest.Tests` (430/430 passed), `scripts/tests` (OK), and `tools/live-topology` (`Ran 317 tests`, OK). `python3 references/Hexalith.Builds/check.py` requires a committed working tree before push (expected under local-only scope; no commit/push performed, `sprint-status.yaml` kept at `in-progress`).

## Spec Change Log

## Review Triage Log

### Review pass 1 (2026-11-27)

Layers: Blind Hunter (BH1–BH12), Verification Gap (VG1–VG5, VGO1–VGO2), Edge Case Hunter (ECH1–ECH16). Code-only diff from `56176163` covering Story 5.13 files (`native_audit.py`, `ci.py`, `test_native_audit.py`, `test_ci.py`, `README.md`); concurrent Story 5.25 hunks in `ci.py`/`test_ci.py` from `e3a5080a` are outside Story 5.13.

| # | Finding | Verdict | Evidence | Route |
| --- | --- | --- | --- | --- |
| BH1 | Unchanged `@updated` with altered `@id` + mismatched bytes misclassified as `confirmed_rotation` when another page advances; `added_pages` omitted from `offending` (`native_audit.py:627-631,674-678`) | high | Verified: line 629 checks `c_meta['@id'] == o_meta['@id']`, letting an unversioned `@id`+content mutation trigger a retry when another page advances; `added_pages` falls back to `['index']`. | patch |
| BH2 | Corrupt/missing cached page in `proven` path raises unhandled `ValueError` without diagnostic (`native_audit.py:604-605,858-868`) | high | Verified: `o_bytes` (`cached_page_bytes`) calls `parse_advisory_page` without catching `ValueError`, and `missing_or_invalid_cached` ignores `o_bytes`. | patch |
| BH3 | `cached*`/`online*` page fields and `semanticDiff` direction inverted in `proven`-mode diagnostics (`native_audit.py:858-966`) | high | Verified: `proven` is passed as `older_*` (`cached*`) and local cache as `newer_*` (`online*`), inverting page metadata and `addedPackages`/`removedPackages`. | patch |
| BH4 | Diagnostic files not hash-sealed in `preparation.json`/`native-reader-audit.json`, contradicting `README.md:264` | medium | Verified: `README.md:264` overclaims diagnostic sealing; proven advisory snapshots are sealed while diagnostics are retained evidence paths. Direct wording fix. | patch |
| BH5 | `priorRotationDiagnostic` dropped on non-rotation attempt-1 failures (`ci.py:1024-1051`, `native_audit.py:1318-1372`) and `shutil.rmtree(snapshot)` in `ci.py:535` | medium | Verified: attempt-1 `NU19xx`/policy/`curl`/non-rotation failures overwrite diagnostics with `priorRotationDiagnostic: None`. (`shutil.rmtree` was pre-existing.) | patch |
| BH6 | `@name == 'diagnostic'` collides with `diagnostic.json`; `_is_official_page_url` allows encoded traversal/backslashes; `curl --location` redirect check (`native_audit.py:89-125,700`) | medium | Verified: `name == 'diagnostic'` collides with new `output / 'diagnostic.json'` and `_is_official_page_url` checks un-decoded path segments. (`curl --location` is pre-existing.) | patch |
| BH7 | `prove_source_advisories` pre-check raises bare `ValueError` when `required=True` and `vuln_index.dat` missing (`ci.py:508-513`) | medium | Verified: skips `online_advisories` `unavailable` diagnostic handler when `required=True`. | patch |
| BH8 | `require_policy` `None` `level`/`code` handling, non-dict advisory entries, unused `cached_index`/`online_index`, policy violation classification (`native_audit.py:127-209,325-395`) | low | Verified: `None` `level`/`code` crashes or yields `'NONE'`, advisory list elements unchecked, unused params exist; 5-way classification enum with `policyViolation: true` matches frozen spec. | patch |
| BH9 | `require_prepared_provenance` misses symlink/name/non-empty/`match` checks on advisory proof; `load_prepared_context` accepts `private_root` itself (`ci.py:617-626,1221-1227`) | medium | Verified: tampered `preparation.json` can point to `private_root`, a symlinked page JSON, or a traversal page name. | patch |
| BH10 | Partial live-fetch diagnostics hardcode `bytesMatch: False`; proxy `200 Connection established` recorded as `httpStatus: 200`; narrow `_REDACTED_HEADERS` (`native_audit.py:144-171,1002,1106`) | low | Verified: partial failure misreports matching earlier pages as `bytesMatch: False`; direct fix for status parsing and sensitive headers. | patch |
| BH11 | Story 5.25 hunks in `ci.py`: `execute_vectors_and_post_cases` bool-as-int on `passed`/`failed`/`exitCode`, `verify_boundary_receipt` `outside.is_symlink()` order, `run_boundary` overwriting `ci-live.json` early | medium | Verified in Story 5.25 code (`e3a5080a`), not caused by Story 5.13. | defer |
| BH12 | Missing tests for Story 5.25 guards (`verify_boundary_receipt`/`run_remaining`/`run`/`IndependentCaseTests`) and Story 5.13 symlinked-cache/module-retry guards | medium | Verified: Story 5.13 symlinked-cache guard test is missing (patch); Story 5.25 tests belong to Story 5.25 (reject). | patch |
| VG1 | `prepare()` retry guard `if error.classification != CONFIRMED_ROTATION or 'sourceAdvisories' in receipt: raise` (`ci.py:1011-1013`) untested on re-raise branch | high | Pre-verified gap: deleting lines 1012-1013 passes all tests, letting non-rotation or post-source failures trigger a source retry. | patch |
| VG2 | `prove_source_advisories` `latest_proven = audited_snapshot` chaining (`ci.py:560-562`) unasserted | medium | Pre-verified gap: deleting lines 560-562 passes all tests. | patch |
| VG3 | `prepare()` retry failure handler omits `priorRotationDiagnostic` on non-rotation retry failures (`ci.py:1031-1051`) | medium | Pre-verified gap: matches BH5; untested and drops `priorRotationDiagnostic`. | patch |
| VG4 | `audit_project` non-rotation retry enrichment (`native_audit.py:1368-1372`) has no test coverage | medium | Pre-verified gap: deleting lines 1368-1371 passes all tests. | patch |
| VG5 | Post-restore `require_policy` and retry `package_graph` in `restore_source_fixtures` (`ci.py:992-998`) untested on failure | medium | Pre-verified gap: deleting lines 992-998 passes all tests. | patch |
| VGO1 | Corrupt `vuln_data_<name>.dat` in `proven` path raises raw `ValueError` without diagnostic (`native_audit.py:604-605`) | high | Verified: same defect as BH2. | patch |
| VGO2 | `proven` comparison inverts `cached*`/`online*` and `semanticDiff` in module diagnostics (`native_audit.py:858-868`) | high | Verified: same defect as BH3. | patch |
| ECH1 | `validate_advisory_index` calls `set(names)` before `isinstance(name, str)`, raising `TypeError` on unhashable `@name` (`native_audit.py:116-119`) | medium | Verified: unhashable `@name` bypasses `ValueError` handler and diagnostic persistence. | patch |
| ECH2 | `parse_iso8601_utc` raises uncaught `OverflowError` near year 0001/9999 with offset (`native_audit.py:83-85`) | low | Verified: `astimezone(timezone.utc)` can raise `OverflowError`; trivial `try/except` to `ValueError`. | patch |
| ECH3 | Corrupt/non-object cached advisory page under `proven` raises uncaught `ValueError` (`native_audit.py:604-605`) | high | Verified: same defect as BH2. | patch |
| ECH4 | Unchanged `@updated` with changed `@id`+bytes misclassified as `confirmed_rotation` (`native_audit.py:627-631`) | high | Verified: same defect as BH1. | patch |
| ECH5 | `proven` comparison swaps `cached*`/`online*` and `semanticDiff` (`native_audit.py:858-868`) | high | Verified: same defect as BH3. | patch |
| ECH6 | Stray `vuln_data_<added>.dat` read for live-added page not in `cached_pages` (`native_audit.py:1061-1068`) | low | Verified: reloading `vuln_data_<name>.dat` for live-only page names can pull in an unreferenced cache file; guard with `name in cached_page_names`. | patch |
| ECH7 | Missing/duplicate `vuln_index.dat` when `required=True` raises bare `ValueError` without diagnostic (`ci.py:508-513`) | medium | Verified: same defect as BH7. | patch |
| ECH8 | Source retry attempt 1 fails with `NU19xx`/policy/`curl`/non-rotation drops `priorRotationDiagnostic` (`ci.py:1024-1051`) | medium | Verified: same defect as BH5/VG3. | patch |
| ECH9 | Module audit retry attempt 1 fails during restore/`require_policy`/`curl` drops `priorRotationDiagnostic` (`native_audit.py:1318-1372`) | medium | Verified: same defect as BH5. | patch |
| ECH10 | Tampered `preparation.json` with symlinked page file, traversal page name, or non-string directory (`ci.py:617-626`) | medium | Verified: same defect as BH9. | patch |
| ECH11 | Pre-existing symlinked `ci-live.json` overwritten by `run_remaining` (`ci.py:1543-1550`) | medium | Verified in Story 5.25 code (`e3a5080a`), not caused by Story 5.13. | defer |
| ECH12 | Failed `dotnet restore` stdout/stderr exceeding 4 MiB omission limit misses `NU19xx` in `classify_restore_failure` (`native_audit.py:419-427`) | low | Verified in principle, but single-project restore logs do not exceed 4 MiB in everyday use and fixing requires extra parameters/fallback complexity. | reject |
| ECH13 | Forged `live-lane.json` bool-as-int for `passed`/`failed`/`exitCode` (`ci.py:1299-1307`) | medium | Verified in Story 5.25 code (`e3a5080a`), not caused by Story 5.13. | defer |
| ECH14 | `refuse_advisory_mismatch` (`native_audit.py:503-505`) is newly dead code with zero callers | low | Verified by repo-wide grep; direct deletion. | patch |
| ECH15 | AC1 claim violated by `prove_source_advisories` pre-check and `proven`-path corrupt cached page (`ci.py:508-513`, `native_audit.py:604-605`) | high | Verified: same defects as BH2 and BH7. | patch |
| ECH16 | AC1 claim violated by inverted `proven`-mode diagnostics (`native_audit.py:858-966`) | high | Verified: same defect as BH3. | patch |

## Verification

**Commands:**
- `python3 -m unittest discover -v -s tools/live-topology -p 'test_*.py'` -- expected: all live-topology tests pass.
- `python3 -m unittest discover -v -s scripts/tests -p 'test_*.py'` -- expected: all scripts tests pass.
- `dotnet restore Hexalith.McpCli.slnx && dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror && dotnet test tests/Hexalith.McpCli.Manifest.Tests --no-build --configuration Release` -- expected: 0 warnings, Manifest tests pass.
- `python3 references/Hexalith.Builds/check.py` -- expected: exit 0 before any push.

### Hosted qualification, 2026-11-28

Candidate `14b2ffb43ab04f69528a4f5d1e82d9a93f0925e7` passed all three hosted jobs in CI run `46068136287`. The Linux artifact binds preparation to that commit and records `match` for the source and all four module advisory comparisons. The live receipt records `fullLiveAccepted: true` with 22 passed, zero failed and zero skipped. Each runtime outcome below was checked against the candidate's approved vectors with active companion plans. [CI run](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/46068136287) · [Linux evidence](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/46068136287/artifacts/15239058484)

| Live cases | Outcome | Executed operations |
| --- | --- | --- |
| Parties | 7 passed | `parties.create-party`, `parties.deactivate-party`, `parties.get-party`, `parties.list-parties`, `parties.reactivate-party`, `parties.search-parties`, `parties.update-party` |
| Projects | 1 passed | `projects.list` |
| Tenants | 14 passed | `tenants.add-user-to-tenant`, `tenants.change-user-role`, `tenants.create-tenant`, `tenants.disable-tenant`, `tenants.enable-tenant`, `tenants.get-tenant`, `tenants.get-tenant-audit`, `tenants.get-tenant-users`, `tenants.get-user-tenants`, `tenants.list-tenants`, `tenants.remove-tenant-configuration`, `tenants.remove-user-from-tenant`, `tenants.set-tenant-configuration`, `tenants.update-tenant` |
| Independent | 2 passed | `boundary`, `smoke` |

The Windows and macOS product jobs both passed on the same candidate. [Windows job](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/46068136287/job/140797761952) · [macOS job](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/46068136287/job/140797762005)
