---
title: '5.25 Fail Fast and Reorder Product CI Gates'
type: 'feature'
created: '2026-11-27'
status: 'in-progress'
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
- [ ] `scripts/product_ci.py` -- Split `linux_checks()` into `linux_packages()` and `linux_conformance()` and expose both CLI phases alongside `linux` -- unlocks fast package validation/upload before live prep.
- [ ] `tools/live-topology/run-vectors.py` -- Implement `--max-failures` (default `2`), immediate exit-`124`/init abort, `skipped-fail-fast` status, and fail-closed `fullLiveAccepted` -- caps broken vector runs to minutes.
- [ ] `tools/live-topology/ci.py` & `tools/live-topology/README.md` -- Add `run-boundary` / `run-remaining` with hash-bound `boundary-receipt.json` and provenance checks, surface `skippedFailFast`, preserve `run`, and update README -- enables early `boundary` gating without weakening acceptance.
- [ ] `.github/actions/after-unit-tests/action.yml` -- Reorder composite steps and timeouts to run packages, `prepare-ci.sh`, and `run-boundary` before `linux-conformance` and `run-remaining`, preserving both artifact uploads -- surfaces failures within ~15 min.
- [ ] `tests/Hexalith.McpCli.Integration.Tests/IsolatedTopologyLifecycle.cs` & `AspireTopologyFixture.cs` -- Watch declared `Resources` for `FailedToStart`/`Exited`/`Finished`/`RuntimeUnhealthy` across Running, URL, `/alive`, and sidecar readiness waits, throwing `InvalidOperationException` with resource identity -- eliminates 2m–15m crash hangs.
- [ ] `scripts/tests/test_product_ci.py`, `tools/live-topology/test_lane.py`, `tools/live-topology/test_ci.py`, & `tests/Hexalith.McpCli.Manifest.Tests/IsolatedTopologyLifecycleTests.cs` -- Add tests for every I/O Matrix case and guard removal -- proves fail-fast and split-gate safety.

**Acceptance Criteria:**
- Given a Release build, when `.github/actions/after-unit-tests/action.yml` is checked by `references/Hexalith.Builds/check.py`, then `linux-packages` + package upload, `prepare-ci.sh`, and `ci.py run-boundary` precede `linux-conformance` and `ci.py run-remaining`, and guard policy passes.
- Given a failing live-vector run, when 2 normal failures occur or any vector exits `124` or fails wrapper/fixture init, then `run-vectors.py` stops early, marks remaining entries `skipped-fail-fast`, sets `fullLiveAccepted: false`, and exits `1`.
- Given an Aspire startup where any declared resource enters `FailedToStart`, `Exited`, `Finished`, or `RuntimeUnhealthy`, when waiting for Running, URL, `/alive`, or `WaitForReadinessAsync`, then startup aborts immediately with `InvalidOperationException` naming the resource and runs cleanup.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Verification

**Commands:**
- `dotnet restore Hexalith.McpCli.slnx && dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror` -- expected: exit 0.
- `dotnet test tests/Hexalith.McpCli.Manifest.Tests --no-build --configuration Release` -- expected: all tests pass including new `IsolatedTopologyLifecycleTests`.
- `python3 -m unittest discover -v -s scripts/tests -p 'test_*.py'` & `python3 -m unittest -v tools/live-topology/test_lane.py` & `python3 -m unittest -v tools/live-topology/test_ci.py` -- expected: all pass.
- `python3 tools/live-topology/run-vectors.py --output /tmp/mcpcli-525-preflight --preflight-only` -- expected: exit 0.
- `dotnet tests/Hexalith.McpCli.Integration.Tests/bin/Release/net11.0/Hexalith.McpCli.Integration.Tests.dll -preEnumerateTheories -list tests` -- expected: exact companion-plan live vectors + `GatewaySmokeTests` + `SharedHeadBoundaryTests`.
- `python3 references/Hexalith.Builds/check.py` -- expected: exit 0.
