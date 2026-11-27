---
title: '5.25 Close the fail-fast CI review findings'
type: 'bugfix'
created: '2026-11-27'
status: 'in-review'
baseline_commit: '4aa663a9ed7a1c1b8066a7c26c857914a90d033f'
story_key: '5-25-fail-fast-and-reorder-product-ci-gates'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/spec-5-25-fail-fast-and-reorder-product-ci-gates.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

Close the eight open patches from the second review of Story 5.25. Tie split live acceptance to one clean McpCli checkout and intact boundary evidence. Preserve fail-fast diagnostics, the smoke attempt after vector failures, and the crashed resource's identity during fixture startup.

## Boundaries & Constraints

- Preserve standalone `product_ci.py linux`, `linux-conformance`, and `run-ci.sh` entry points, current gate order, and artifact uploads.
- Keep `fullLiveAccepted` false through partial or failed runs. Preserve the pre-vector check for a fresh boundary-only runtime and the final runtime-count gate.
- Watch only declared resources. Add fixture regression tests to Manifest.Tests and preserve Integration.Tests discovery.
- Scope changes to the open review patches. Defer advisory-cache, live-plan, and sidecar changes as already recorded. Leave shared CiCd files and submodules untouched.

## I/O & Edge-Case Matrix

| Scenario | Expected behavior |
| --- | --- |
| Root HEAD changes or the root checkout becomes dirty after preparation | The next split phase rejects drift before launching children. Drift during remaining execution blocks final acceptance. Split conformance checks the prepared SHA on entry and exit. |
| `ci-live.json` is a symbolic link, including a dangling link | Refuse the phase before launching children and preserve the link and destination. |
| Smoke changes the prior boundary XML, runtime receipt, namespace proof, or seal | Final acceptance fails after rechecking the sealed boundary artifacts. |
| A failed vector produces XML with an unknown encoding | Classify fixture initialization failure, mark remaining vectors `skipped-fail-fast`, and record the reason. |
| The failed vector receipt cannot be read | Keep the original vector error, attempt smoke, and retain failed acceptance. |
| Readiness fails before the watcher delivers a published terminal state | Report the declared resource, state, and exit code. Cleanup still runs. Preserve the readiness error when the latest snapshots show no terminal state. |

</frozen-after-approval>

## Code Map

- `tools/live-topology/ci.py` owns `prepare`, `verify_boundary_receipt`, `run_remaining`, and `execute_vectors_and_post_cases`. The boundary receipt already hashes `preparation.json` and each retained boundary artifact. Use the same artifact verification before vectors and before final acceptance.
- `scripts/product_ci.py` checks checkout cleanliness and SHA with `require_source`. The module-owned `.github/actions/after-unit-tests/action.yml` sequences conformance between the two live phases.
- `tools/live-topology/run-vectors.py` classifies failed children in `classify_immediate_fail_fast` before updating skipped outcomes.
- `tests/Hexalith.McpCli.Integration.Tests/IsolatedTopologyLifecycle.cs` wires the watcher into startup and cleanup. Manifest.Tests compiles the same lifecycle source.

## Tasks & Acceptance

- [x] `tools/live-topology/ci.py`, `scripts/product_ci.py`, `.github/actions/after-unit-tests/action.yml`, `tools/live-topology/README.md` — Seal the clean root SHA in preparation and explicitly pass the prepared evidence to split conformance. Check the sealed SHA at the phase boundaries and document the contract.
- [x] `tools/live-topology/ci.py` — Guard the report path before writing, recheck sealed boundary artifacts immediately before publishing full acceptance, and handle receipt read errors in the vector failure path.
- [x] `tools/live-topology/run-vectors.py` — Treat an unsupported XML encoding as malformed fixture output.
- [x] `tests/Hexalith.McpCli.Integration.Tests/IsolatedTopologyLifecycle.cs` — Check latest declared snapshots before rethrowing an operation error. Make startup and cleanup testable with a controlled application.
- [x] `tools/live-topology/test_ci.py`, `tools/live-topology/test_lane.py`, `scripts/tests/test_product_ci.py` — Exercise each runner failure above and assert the effective 11,280-second vector and 960-second independent case deadlines in the split run.
- [x] `tests/Hexalith.McpCli.Manifest.Tests/IsolatedTopologyLifecycleTests.cs` — Exercise delayed watcher delivery and the actual initialization and cleanup path, including cancellation of readiness when a declared resource exits.
- [ ] Close sprint tracking after the full Builds checker runs against a clean commit. The original Story 5.25 review checklist records all eight applied patches.

Given one clean checkout and complete passing evidence, when boundary, conformance, and remaining execute in order, then only the final report grants full live acceptance. Given the invalid evidence or startup conditions above, when the corresponding entry point runs, then it reports failure with the expected diagnostic and side effects.

## Implementation Notes

- Bound split conformance with `--live-preparation` and kept its standalone invocation. Included staged gitlink changes in the clean-root check while permitting independently qualified submodule worktrees.
- Verified the Release restore and build with zero warnings and errors. The six ordinary .NET projects passed with 2,232 successes and 15 skips, including all 435 Manifest.Tests. Product Python (74 tests), the vector runner (26 tests), 12 focused live CI checks, live-vector preflight, and exact discovery of all 24 integration cases passed.
- `run-with-temp python3 references/Hexalith.Builds/check.py` exited 1 with `module: commit all staged, modified and untracked inputs before checking`. Its pinned custom-action and audit checks passed directly. The full live Python suite and native Aspire execution remain unverified. Sprint status stays at `review`.

## Spec Change Log

## Review Triage Log

| Finding | Verdict | Evidence and disposition |
| --- | --- | --- |
| BH1 | high | Boundary parsed one preparation and sealed a later read. The disposable test accepted evidence across two checkout SHAs. Patch the snapshot binding. |
| BH2 | medium | Manual boundary and remaining runs can complete independently of conformance. The hosted hook already gates remaining on conformance success, and the original live-only entry point grants live acceptance independently. Reject a new completion receipt as outside the checkout-binding intent. |
| BH3 | medium | An explicitly failed, hash-matching boundary with absent run IDs passed split conformance. Patch receipt validation. |
| BH4 | medium | Conformance read each receipt separately for parsing and hashing and did not check the evidence on exit. Patch snapshot validation. |
| BH5 | high | A link installed after reading the prior report was followed at the first write. Patch report publication to avoid writing through links or special files. |
| BH6 | medium | Final diagnostic-copy failure replaced the vector error in the raised exception and report. Patch error preservation. |
| BH7 | medium | Excessive JSON nesting raised `RecursionError` before smoke. Patch the optional diagnostics read and cover the malformed receipt. |
| BH8 | medium | The normal initialization test exercised cancellation only at fixture-specific readiness. Patch coverage for Running, URL, and aliveness wiring. |
| BH9 | medium | Checkout drift during preparation and boundary execution lacked end-to-end tests. Patch coverage for both final checks. |
| ECH1 | high | Reproduced mixed-SHA acceptance through a changed preparation file during boundary. Patch the same snapshot binding as BH1. |
| ECH2 | high | Reproduced report target modification after the prior report read. Patch the same write path as BH5. |
| ECH3 | medium | A decoder recursion failure escaped diagnostics and prevented smoke. Patch the same read as BH7. |
| ECH4 | false | The declared topology uses one resource instance per name and neither fixture host configures replicas. Replica-specific handling does not affect this startup path. |
| ECH5 | medium | Matching hashes and missing IDs were enough to treat a failed receipt as a passing boundary. Patch the same validation as BH3. |
| VG1 | medium | Removing path resolution passed the absolute-path unit test and failed the actual repository-relative invocation. Patch the split handoff test. |
| VG2 | medium | Removing the boundary exit check passed the tested boundary scenarios. Patch the same coverage as BH9. |
| VG3 | medium | A stat error inside optional receipt loading had no regression test. Remove the redundant stat and cover receipt read failures. |
| VG4 | high | The test fixture granted acceptance after changing the SHA in the preparation during boundary. Patch the same snapshot binding as BH1. |
| VG5 | high | A symlink swapped in during the read was followed by the subsequent write. Patch the same write path as BH5. |

## Verification

- Run the focused Python product and live runner regressions through `run-with-temp`.
- Restore and build the Release solution, run Manifest.Tests, and enumerate Integration.Tests to verify unchanged discovery.
- Run live-vector preflight with disposable output and `python3 references/Hexalith.Builds/check.py`.
