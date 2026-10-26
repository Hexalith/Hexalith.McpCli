# Story 4.14 implementation evidence

The same `prepare-ci.sh` / `run-ci.sh` path configured for CI passed locally:
21 approved semantic vectors and the independent authenticated smoke, zero live
failures or skips, 22 fresh isolated runtime receipts with owned cleanup, and
`fullLiveAccepted: true`. The aggregate receipt is
`live-ci/ci-live.json` inside `live-ci.tar.gz`; its generation contains the vector aggregate, each full
semantic receipt, xUnit XML, bootstrap receipts and sanitized runtime diagnostics.
`live-ci/preparation.json` records exact source identities, tool versions/hashes,
the private runtime location and per-source build diagnostics.

`verification.json` records commands and results. Release restore/build passed;
all six non-live projects passed (counts in `focused-tests.json`). Core and CLI
have five existing platform skips in total; the live lane had none. The complete
Python suite passed 110 tests, including executable hook/stub cases and the
existing real-runner tests. Upstream workflow contracts passed 321 assertions.
Both workflow syntax checks, both shell syntax checks and whitespace validation
passed. Exact restore/build/test output is retained beside this document.

The Builds owner changed only its workflow, workflow documentation and contract
tests. Its qualified commit is
`833a58fa125fdc3a3135c16d0e04cca3f1b63264`, based on
`09af6ef818beb27490c87c00ed83dd581a7e6d8d`. `builds-hooks.patch` records the
change; `upstream-revision.json` records integration. The exact commit candidate
passed the owner's pinned commitlint before commit; its message and successful
validation output are retained. The local Builds gitlink was integrated using a
local Git bundle, without network Git operations. McpCli explicitly retains the
approved EventStore 3.127.0 package pin despite the newer Builds catalog default;
fresh Manifest.Tests passed with no dependency-policy or approved vector changes.

`aspire-fresh-bundle.json` and matching output prove real extraction of the
qualified CLI's embedded DCP/dashboard into a disposable directory. Preparation
uses bounded `aspire setup` when the usual bundle is absent, and executable
tests protect both successful provisioning and failed setup. This avoids relying
on a previously populated local bundle to satisfy a fresh hosted runner.

`live-ci.tar.gz` retains the complete final support-safe tree from
`TestResults/live-ci`; every archived file was SHA-256 compared with the original
after compression, with no mismatches. `verification.json` records its hash and
member count. Absolute paths in its receipts identify the
actual original run. The task-owned runtime remains at the path in preparation
for direct receipt/empty-genesis-backup inspection; private signing keys were
removed during cleanup. Runtime binaries, Redis RDB state, certificates and
scheduler data are not copied here. `files.sha256.json` binds the retained files.

Hosted proof is unavailable. The implementation stage prohibits pushes and
remote Git operations, so the qualified upstream commit has not been published;
the caller's pinned revision must become remotely available before hosted CI can
resolve it. No hosted run, branch-protection change or publication is claimed.
The paired-release refusal remains unchanged and belongs to Story 4.16.
