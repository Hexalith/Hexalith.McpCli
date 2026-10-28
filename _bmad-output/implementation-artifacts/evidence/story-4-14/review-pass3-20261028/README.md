# Story 4.14 pass-3 corrections — 2026-10-28

This packet qualifies the six pass-3 patches against McpCli baseline
`5aa3ee23ef4b395a4500453a50d4815e9837dd07`. No Git remote operation, publication,
commit, or change to reference contents was performed.

- D1: Explain that published EventStore 3.128.3 now includes routing contracts;
  Tenants deliberately uses the same EventStore source as the root server under
  test under the already-approved exception. Build switches are unchanged.
- P1: Report `running` vector outcomes as interrupted Operations in stderr and
  `ci-live.json`, retaining failed Operations separately. A pending receipt from
  an aggregate deadline still permits the independent smoke attempt. A direct
  hook cancellation retains available vector diagnostics and propagates its
  original control exception without starting smoke.
- P2: Align the commitlint workflow to the selected Builds gitlink
  `3d7f49a5430294da5bcd437cbdace85c62c42027`. Check every Builds reference in all
  `.yml`/`.yaml` workflows against the gitlink recorded in `HEAD`.
- P3: Add Docker-daemon-unavailable prerequisite coverage and prove that removing
  the readiness check fails the test before source builds.
- P4: Correct both README cancellation bounds to 25 seconds after TERM and at
  most one further second waiting for the supervisor after killing its group.
- P5: Combine vector/smoke failures only for ordinary exceptions. Real SIGTERM
  during smoke after a vector failure exits 143 and retains `SystemExit: 143`;
  a focused regression also preserves `KeyboardInterrupt` and exception identity.

Executed checks:

| Check | Result | Evidence |
| --- | --- | --- |
| Six focused regression methods before corrections | Expected failures: missing interrupted metadata, relabelled cancellation/control exceptions, stale commitlint pin | `regressions-before.txt` |
| Same six methods after corrections | 6 passed | `regressions-after.txt` |
| `python3 -m unittest discover -v -s tools/live-topology -p 'test_*.py'` | 155 passed, zero skips, 154.724 seconds | `python-tests.txt` |
| `python3 _bmad-output/implementation-artifacts/evidence/story-4-14/review-pass3-20261028/check-mutations.py` | All 8 mutations detected in disposable fixtures | `mutation-results.json`, `mutation-checks.txt` |
| `bash -n tools/live-topology/prepare-ci.sh tools/live-topology/run-ci.sh` | Exit 0 | `verification.json` |
| `actionlint .github/workflows/ci.yml .github/workflows/commitlint.yml` | Exit 0 | `verification.json` |
| Scoped `git diff --check` | Exit 0 | `verification.json` |
| AST and protected-path comparison with baseline | Successful execution/acceptance, preparation, cleanup, Contracts, vectors, dependency policy, publication refusal and .NET/build inputs unchanged | `scope-verification.json` |

The removal checks cover Docker readiness, interrupted-Operation reporting,
direct vector cancellation capture and smoke control-exception preservation.
Drift checks cover the CI caller pin, commitlint pin, gitlink, and an additional
workflow referring to Builds at `main`. They run against disposable fixtures;
production files are not mutated. `source-hashes.json` binds the six relevant
source/document files to this verification.

No fresh full native, hosted, or .NET run is claimed for these failure-path,
test, workflow-pin and wording corrections. The earlier qualification remains
in [the pass-2 final packet](../review-pass2-20261028/final/README.md): all 21 live
vectors, independent authenticated smoke, 22 owned cleanup receipts, a fresh
Release build and 1,531 passing .NET tests with five existing non-live skips.
The spec separately records hosted acceptance of the selected Builds pin in
run `40658496696`. The parent independently re-audited the historical native
archive and will complete the final spec/sprint update and required review.
