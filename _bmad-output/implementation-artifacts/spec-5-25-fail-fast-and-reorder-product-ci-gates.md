---
title: '5.25 Fail Fast and Reorder Product CI Gates'
type: 'feature'
created: '2026-11-27'
status: 'in-review'
baseline_commit: '38eedb2e9343ddaffcb4baa90a06d3a108e1637c'
story_key: '5-25-fail-fast-and-reorder-product-ci-gates'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-5-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Linux CI waits ~60 minutes inside `product_ci.py` before reaching live `prepare`/`boundary`, `run-vectors.py` loops across every vector for up to 3h 08m despite broken infrastructure or fixture init, and `AspireTopologyFixture` waits out 2m–15m timeouts when a required Aspire resource crashes.

**Approach:** Reorder `.github/actions/after-unit-tests/action.yml` to run fast package staging/smoke (~25s), `prepare-ci.sh`, and `boundary` ahead of slower conformance and remaining live vectors/smoke; add bounded fail-fast (`--max-failures 2`, immediate abort on exit `124` or init failure, remainder `skipped-fail-fast`) to `run-vectors.py`; and abort startup immediately in `IsolatedTopologyLifecycle` / `AspireTopologyFixture` when any declared resource enters a terminal failure state.

## Boundaries & Constraints

**Always:**
- Keep `mcpcli-product-packages` (`staged/` including `discovery/` and `linux-discovery.json`), `mcpcli-linux-product-diagnostics` (`if: always()`), SHA-pinned actions, and `references/Hexalith.Builds/check.py` passing.
- Keep `fullLiveAccepted: false` on any failure, `skipped-fail-fast`, partial run, or pre-completion split phase; preserve `product_ci.py linux` and `tools/live-topology/run-ci.sh` (`ci.py run`) compatibility.
- Re-verify prepared provenance and hash-bound `boundary-receipt.json` before running vectors + `smoke` after conformance.
- Watch only declared `Resources` for terminal failure states so `.WithExplicitStart()` `*-catalog-source` clones in `NotStarted` never false-trigger.
- Keep `Hexalith.McpCli.Integration.Tests` test count unchanged (`discover_integration` rejects extra tests); add lifecycle unit tests to `IsolatedTopologyLifecycleTests.cs` in `Manifest.Tests`.

**Never:**
- Edit `Hexalith.CiCd`-owned files (`.github/workflows/**`, `.github/hexalith-ci.json`, `.github/dependabot.yml`, `references/**`) or `src/**`.
- Remove `tools/live-topology` unittest from `product_ci.py` or trim live plans (Stories 5.26/5.27).
- Weaken `fullLiveAccepted`, mask failures, or skip `smoke` after vector failures in `ci.py`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|---|---|---|---|
| Fast package gate | `product_ci.py linux-packages` | Stages pair, validates, runs tool + consumer smoke, writes `linux-discovery.json` before package artifact upload | Non-zero exit stops hook before `prepare-ci.sh` |
| Split live gate | `ci.py run-boundary` -> `linux-conformance` -> `ci.py run-remaining` | `run-boundary` writes hash-bound `boundary-receipt.json` (`fullLiveAccepted: false`); `run-remaining` verifies receipt, provenance, and fresh-runtime count, runs vectors + `smoke`, sets `fullLiveAccepted: true` | Missing/tampered receipt or post-conformance drift fails closed (`fullLiveAccepted: false`) |
| Threshold fail-fast | `--max-failures 2` (default); 2 normal vector failures | Aborts after 2nd failure; remaining vectors marked `skipped-fail-fast`; `failFastTriggered: true`, `fullLiveAccepted: false`, exit `1` | `ci.py` logs failed + skipped-fail-fast summary, runs `smoke`, exits `1` |
| Immediate fail-fast | Exit `124`, wrapper init failure (`prerequisitesReady != true` / missing receipt / `error`), or fixture init failure (missing/bad `tests.xml` or `errors != 0`) | Aborts on 1st failure; remaining vectors `skipped-fail-fast`; records `failFastReason` | `fullLiveAccepted: false`, exit `1` |
| Flag boundaries | `--max-failures 0` vs `--max-failures -1` | `0` disables fail-fast; `-1` fails before preflight with `VectorError` | Failed receipt, exit `1` |
| Aspire resource crash | Declared resource enters `FailedToStart`, `Exited`, `Finished`, or `RuntimeUnhealthy` during Running, URL, `/alive`, or sidecar readiness wait | Aborts immediately without waiting 2m/6m timeouts | Throws `InvalidOperationException` naming resource, state, and exit code; runs `CleanupAsync` |
| Undeclared `NotStarted` | `*-catalog-source` stays `NotStarted` while declared resources run | Ignored; startup succeeds | N/A |

</frozen-after-approval>

## Code Map

- `.github/actions/after-unit-tests/action.yml` (L1–38) -- Reorder: `linux-packages` -> upload packages -> `prepare-ci.sh` -> `ci.py run-boundary` -> `linux-conformance` -> `ci.py run-remaining` -> `always()` upload diagnostics.
- `scripts/product_ci.py` (L136–180) & `scripts/tests/test_product_ci.py` -- Split `linux_checks()` into `linux_packages()` (`stage_packages` + `package_checks`) and `linux_conformance()`; add `linux-packages`/`linux-conformance` phases while keeping `linux`.
- `tools/live-topology/run-vectors.py` (L97–218) & `test_lane.py` (L192–230, L403–434) -- Add `--max-failures` (default `2`, `0` off), exit-`124`/init failure classification, `skipped-fail-fast`, `skipped`/`failFastTriggered`/`failFastReason`, and fail-closed `fullLiveAccepted`; pass `--max-failures 0` in the two all-21-failure selector tests.
- `tools/live-topology/ci.py` (L1032–1228), `test_ci.py` (L2029–2135), & `tools/live-topology/README.md` (L153–154) -- Add `run-boundary` and `run-remaining` with hash-bound `boundary-receipt.json` + provenance/runtime checks, surface `skippedFailFast`/`failFastReason`, keep `run` intact, update README note.
- `tests/Hexalith.McpCli.Integration.Tests/IsolatedTopologyLifecycle.cs` (L36–106), `AspireTopologyFixture.cs` (L22–81), & `tests/Hexalith.McpCli.Manifest.Tests/IsolatedTopologyLifecycleTests.cs` -- Add `internal static` `ResourceNotificationService` terminal-failure wait/watch helpers covering Running, URL, `/alive`, and `WaitForReadinessAsync`; test in `Manifest.Tests`.

## Tasks & Acceptance

**Execution:**
- [x] `scripts/product_ci.py` -- Split `linux_checks()` into `linux_packages()` and `linux_conformance()` and expose both CLI phases alongside `linux` -- unlocks fast package validation/upload before live prep.
- [x] `tools/live-topology/run-vectors.py` -- Implement `--max-failures` (default `2`), immediate exit-`124`/init abort, `skipped-fail-fast` status, and fail-closed `fullLiveAccepted` -- caps broken vector runs to minutes.
- [x] `tools/live-topology/ci.py` & `tools/live-topology/README.md` -- Add `run-boundary` / `run-remaining` with hash-bound `boundary-receipt.json` and provenance checks, surface `skippedFailFast`, preserve `run`, and update README -- enables early `boundary` gating without weakening acceptance.
- [x] `.github/actions/after-unit-tests/action.yml` -- Reorder composite steps and timeouts to run packages, `prepare-ci.sh`, and `run-boundary` before `linux-conformance` and `run-remaining`, preserving both artifact uploads -- surfaces failures within ~15 min.
- [x] `tests/Hexalith.McpCli.Integration.Tests/IsolatedTopologyLifecycle.cs` & `AspireTopologyFixture.cs` -- Watch declared `Resources` for `FailedToStart`/`Exited`/`Finished`/`RuntimeUnhealthy` across Running, URL, `/alive`, and sidecar readiness waits, throwing `InvalidOperationException` with resource identity -- eliminates 2m–15m crash hangs.
- [x] `scripts/tests/test_product_ci.py`, `tools/live-topology/test_lane.py`, `tools/live-topology/test_ci.py`, & `tests/Hexalith.McpCli.Manifest.Tests/IsolatedTopologyLifecycleTests.cs` -- Add tests for every I/O Matrix case and guard removal -- proves fail-fast and split-gate safety.

**Acceptance Criteria:**
- Given a Release build, when `.github/actions/after-unit-tests/action.yml` is checked by `references/Hexalith.Builds/check.py`, then `linux-packages` + package upload, `prepare-ci.sh`, and `ci.py run-boundary` precede `linux-conformance` and `ci.py run-remaining`, and guard policy passes.
- Given a failing live-vector run, when 2 normal failures occur or any vector exits `124` or fails wrapper/fixture init, then `run-vectors.py` stops early, marks remaining entries `skipped-fail-fast`, sets `fullLiveAccepted: false`, and exits `1`.
- Given an Aspire startup where any declared resource enters `FailedToStart`, `Exited`, `Finished`, or `RuntimeUnhealthy`, when waiting for Running, URL, `/alive`, or `WaitForReadinessAsync`, then startup aborts immediately with `InvalidOperationException` naming the resource and runs cleanup.

## Implementation Notes

- Implemented in `3d63679d`: split `scripts/product_ci.py` (`linux-packages`, `linux-conformance`, preserving `linux`), reordered `.github/actions/after-unit-tests/action.yml`, added `--max-failures` / immediate fail-fast / `skipped-fail-fast` to `tools/live-topology/run-vectors.py`, added `run-boundary` / `run-remaining` with hash-bound `boundary-receipt.json` to `tools/live-topology/ci.py`, updated `tools/live-topology/README.md`, and wired `ResourceNotificationService` terminal-failure watching in `IsolatedTopologyLifecycle.cs` (propagated via `watchedToken` into `AspireTopologyFixture.WaitForReadinessAsync`, requiring no edits to `AspireTopologyFixture.cs`).
- Verified Release build (0 warnings), `Manifest.Tests` (414/414), `Integration.Tests` discovery (exact 24 cases unchanged), `scripts/tests` (72/72), `test_lane.py` (23/23), `test_ci.py` (127/127), `run-vectors.py --preflight-only`, and `Hexalith.Builds` guard policy.

## Spec Change Log

## Review Triage Log

- `[BH-1]` **high** (`patch`): Verified at `tools/live-topology/ci.py:1281-1285,1308-1311` — `tests_xml.is_symlink()` runs after `.resolve()` (always `False`), `entry['receipt']`/`outside.json`/`preparation.json` lack pre-resolve symlink checks, and `exists()` returns `False` for dangling symlinks in `run_boundary`.
- `[BH-2]` **high** (`patch`): Verified at `tools/live-topology/ci.py:1230-1233,1377-1383` — `verify_boundary_receipt` skips external `ci-live.json` (`prior_report`) digest binding whenever `ci-live.json` is missing, malformed, or not `boundary-passed`.
- `[BH-3]` **medium** (`patch`): Verified at `tools/live-topology/ci.py:1329-1373` — `run_boundary` calls `redact_generation` again in `finally` after hashing and sealing `tests.xml` into `boundary-receipt.json`.
- `[BH-4]` **medium** (`patch`): Verified at `.github/actions/after-unit-tests/action.yml:8-32` and `tools/live-topology/ci.py:1152-1154` — combined step timeouts total 368 min (> 360 min CI job budget) and `run_remaining` double-subtracts `boundary`'s 960s timeout.
- `[BH-5]` **high** (`patch`): Verified at `tools/live-topology/run-vectors.py:97-140` — `classify_immediate_fail_fast` misses real xUnit v3 `AspireTopologyFixture.InitializeAsync()` crashes (`errors="0" failed="1"`, `Xunit.Sdk.TestPipelineException`), `-failSkips` prerequisite skips (`skipped != "0"`), and incomplete `ownedInfrastructureStopped`.
- `[BH-6]` **medium** (`patch`): Verified at `tools/live-topology/run-vectors.py:161-162,261-280` — sets `failFastTriggered: true` even when zero vectors remain to skip (last vector or `--operation`) and omits `skipped` from initial/intermediate/preflight receipts.
- `[BH-7]` **medium** (`patch`): Verified at `tests/Hexalith.McpCli.Integration.Tests/IsolatedTopologyLifecycle.cs:144-188` — an unexpected `watchTask` fault never cancels `linked` and can overwrite an `operation` exception in `finally`; clean completion does not re-check `TryGetCurrentState`.
- `[BH-8]` **medium** (`patch`): Verified at `tests/Hexalith.McpCli.Manifest.Tests/IsolatedTopologyLifecycleTests.cs` — missing guard-removal tests for non-terminal exception/timeout propagation, `ExitCode == null`/`State == null` formatting, `IsTerminalFailureState` edge cases, and empty `watchedResources`.
- `[BH-9]` **maybe-false** (`defer`): `IsolatedTopologyLifecycle.InitializeAsync` watches only declared `Resources`, omitting `*-dapr`/`*-dapr-cli` sidecars; `WaitForReadinessAsync` already bounds sidecar discovery/health to 10s+30s, and live Aspire 17.0.0 + CommunityToolkit Dapr preview state-transition evidence is needed to verify sidecar terminal states never false-trigger.
- `[BH-10]` **medium** (`patch`): Verified at `scripts/product_ci.py:141-154` and `scripts/tests/test_product_ci.py:224-252` — standalone `linux_conformance()` omits `require_source(...)` clean-checkout check and `record_execute` silently drops unexpected commands.
- `[BH-11]` **medium** (`patch`): Verified at `tools/live-topology/test_ci.py` and `test_lane.py` — missing split-lane negative/fail-fast coverage (`run-remaining` fail-fast, missing/bad `ci-live.json`, recomputed-hash metadata tamper, `outside.json`/`preparation.json` tamper, symlinks, duplicate `run-boundary`, `--max-failures 1`, non-consecutive failures, `owned['commandExitCode']==124`).
- `[BH-12]` **low** (`patch` for README; spec/sprint-status sub-claims rejected): `tools/live-topology/README.md:366-380` omits `run-boundary`/`run-remaining`/`boundary-receipt.json` and retains stale `17700`/`15180` timeouts; spec Code Map edits are rejected per Step 4 rules and `sprint-status.yaml` transitions to `done` in Step 5.
- `[ECH-1]` **high** (`patch`): Same root cause as `[BH-1]` (`tools/live-topology/ci.py:1281-1285` post-resolve `is_symlink()`).
- `[ECH-2]` **high** (`patch`): Same root cause as `[BH-2]` (`tools/live-topology/ci.py:1230-1233` missing `else` on `prior_report` digest check).
- `[ECH-3]` **high** (`patch`): Same root cause as `[BH-1]` (`tools/live-topology/ci.py:1308-1309` dangling symlink bypass on `boundary-receipt.json`).
- `[ECH-4]` **medium** (`patch`): Verified at `tools/live-topology/ci.py:1361-1373` — an exception or SIGTERM in `finally` after `save(receipt_path, ...)` can leave `boundary-receipt.json` on disk while `ci-live.json` is `failed`.
- `[ECH-5]` **medium** (`patch`): Verified at `tools/live-topology/ci.py:1163` — Python `False == 0` and non-bool truthy `failFastTriggered` bypass `lane.get('failFastTriggered') is True or lane.get('skipped', 0) != 0`.
- `[ECH-6]` **medium** (`patch`): Same root cause as `[BH-7]` (`IsolatedTopologyLifecycle.cs:148-183` watcher fault/cancellation masking).
- `[ECH-7]` **low** (rejected): `IsolatedTopologyLifecycle.cs:124-138` — `watchedResources` only receives hardcoded non-empty literal `AspireResource.Name` values in production; adding a defensive guard on an unlikely internal-only defect is rejected per Step 4 low-finding rule.
- `[VG-1]` **high** (`patch`): Pre-verified by `verification-gap` — `test_lane.py` only tested synthetic `errors="1"` XML, missing real built-assembly xUnit v3 `AspireTopologyFixture.InitializeAsync()` failure output (same root cause as `[BH-5]`).
- `[VG-2]` **medium** (`patch`): Pre-verified by `verification-gap` — `'tampered-field'` in `test_ci.py` fails at `prior_report` digest check before reaching `contentSha256` and metadata-binding checks (same test-gap group as `[BH-11]`).
- `[VG-3]` **medium** (`patch`): Pre-verified by `verification-gap` — `'forged-fail-fast-passed'` sets both `failFastTriggered` and `skipped` together, leaving each guard individually unpinned (same test-gap group as `[BH-11]`).
- `[VG-4]` **medium** (`patch`): Pre-verified by `verification-gap` — `run_boundary` pre-execution guards for existing `boundary-receipt.json` and `runtime/runs` have no test coverage (same test-gap group as `[BH-11]`).
- `[VG-5]` **medium** (`patch`): Pre-verified by `verification-gap` — `RunWithTerminalFailureWatchAsync` non-terminal exception and timeout propagation is untested (same test-gap group as `[BH-8]`).
- `[VG-6]` **high** (`patch`): Verified directly against built `Hexalith.McpCli.Integration.Tests.dll` — xUnit v3 emits `AspireTopologyFixture.InitializeAsync()` crashes as `errors="0" failed="1"` with `Xunit.Sdk.TestPipelineException` (same root cause as `[BH-5]`).

## Verification

**Commands:**
- `dotnet restore Hexalith.McpCli.slnx && dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror` -- expected: exit 0.
- `dotnet test tests/Hexalith.McpCli.Manifest.Tests --no-build --configuration Release` -- expected: all tests pass including new `IsolatedTopologyLifecycleTests`.
- `python3 -m unittest discover -v -s scripts/tests -p 'test_*.py'` & `python3 -m unittest -v tools/live-topology/test_lane.py` & `python3 -m unittest -v tools/live-topology/test_ci.py` -- expected: all pass.
- `python3 tools/live-topology/run-vectors.py --output /tmp/mcpcli-525-preflight --preflight-only` -- expected: exit 0.
- `dotnet tests/Hexalith.McpCli.Integration.Tests/bin/Release/net11.0/Hexalith.McpCli.Integration.Tests.dll -preEnumerateTheories -list tests` -- expected: exact companion-plan live vectors + `GatewaySmokeTests` + `SharedHeadBoundaryTests`.
- `python3 references/Hexalith.Builds/check.py` -- expected: exit 0.
