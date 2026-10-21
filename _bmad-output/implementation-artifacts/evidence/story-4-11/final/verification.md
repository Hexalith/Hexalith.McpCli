# Story 4.11 local verification after review

The local harness is implemented and reviewed. Full Story 4.11 remains in
progress: the actual production manifest contains Parties 1.5.1 with seven
operations; Tenants is not enrolled. Both strict gates fail only for missing
`tenants`, and both retain `fullV1Accepted: false`.

Final verification passed 139 Python tests and 1,356 .NET tests across all six
projects, with four existing Windows-only skips. The Release build had zero
warnings and errors. Both sample scripts passed, including packaged sample
replay, combined Parties/sample replay, extension preservation, Core depth
boundaries, rejected inventory and false semantic assertions. Direct execution
of both Python test files also includes the added classes.

The final local benchmark measured 115.0074 ms; the strict attempt measured 127.8717 ms
and failed only for missing Tenants. These are available-population measurements,
not acceptance of the future two-module population. The benchmark uses a fresh
process, the actual production manifest and exactly one Ulid sample. Core.Tests
also ran the isolated String-kind test, exact 500 ms boundary and over-limit
cases, and early-failure evidence invalidation cases.

Three independent review layers completed before triage. All ten correction
groups are verified; separate orchestration and timeout proposals were rejected
as low-impact complexity. The review added no deferred-work entry. Eight isolated
removal mutations failed their protecting tests, including retained-vector
hashes, discovered module binding, generated message reuse and partial failure
observations. See `parent-mutation-audit.json` and the spec's individual triage
rows.

| Check | Result | Logs |
| --- | --- | --- |
| `python` | Passed | `python.stdout.txt`, `python.stderr.txt` |
| `python-direct-loopback` | Passed | `python-direct-loopback.stdout.txt`, `python-direct-loopback.stderr.txt` |
| `python-direct-validate` | Passed | `python-direct-validate.stdout.txt`, `python-direct-validate.stderr.txt` |
| `restore` | Passed | `restore.stdout.txt`, `restore.stderr.txt` |
| `release-build` | Passed | `release-build.stdout.txt`, `release-build.stderr.txt` |
| `abstractions-tests` | Passed | `abstractions-tests.stdout.txt`, `abstractions-tests.stderr.txt` |
| `analyzers-tests` | Passed | `analyzers-tests.stdout.txt`, `analyzers-tests.stderr.txt` |
| `core-tests` | Passed | `core-tests.stdout.txt`, `core-tests.stderr.txt` |
| `manifest-tests` | Passed | `manifest-tests.stdout.txt`, `manifest-tests.stderr.txt` |
| `cli-tests` | Passed | `cli-tests.stdout.txt`, `cli-tests.stderr.txt` |
| `mcp-tests` | Passed | `mcp-tests.stdout.txt`, `mcp-tests.stderr.txt` |
| `sample-validation` | Passed | `sample-validation.stdout.txt`, `sample-validation.stderr.txt` |
| `sample-loopback` | Passed | `sample-loopback.stdout.txt`, `sample-loopback.stderr.txt` |
| `restore-after-loopback` | Passed | `restore-after-loopback.stdout.txt`, `restore-after-loopback.stderr.txt` |
| `production-gate` | Expected exit 1: missing tenants only | `production-gate.stdout.txt`, `production-gate.stderr.txt` |
| `benchmark-local` | Passed | `benchmark-local.stdout.txt`, `benchmark-local.stderr.txt` |
| `benchmark-strict` | Expected exit 1: missing tenants only | `benchmark-strict.stdout.txt`, `benchmark-strict.stderr.txt` |

`checks.json` records every exact command, exit code and duration.
`verification-summary.json` records test counts and the uncommitted source hashes.
`production/` retains package, approval, vector, discovery and request/result
observations. Its `.nupkg` archive is present locally but ignored by Git; restore
the published package by its exact recorded identity/hash when reconstructing
committed evidence.

| Approved matrix row | Executed evidence |
| --- | --- |
| Missing/duplicate/stale vector; wrong step kind/schema | Shared validator identity/coverage tests; all-position Core process negatives; batch-ordering regression |
| Payload depth 64/65 | Offline boundary tests; real Core 64 reaches schema and 65 fails parsing; depth 500 returns a located finding |
| Supplied/omitted correlation and idempotency key | Result contract and request-binding negatives; generated/default correlation tests; full sample and production replay |
| Extra request field, wrong paging, equal missing result fields | Complete-request negatives, required-result execution tests and actual captured request comparisons |
| Validation or Gateway failure | Exact malformed-payload documents, SDK 200/204/304/Problem Details cases, complete error metadata, retained failing-head observations and actual Gateway-error replay |
| Valid extensions | Isolated allowlist test and real packaged replay with `trace-id` value preservation |
| Missing v1 Module or construction over 500 ms | Strict scope failures, discovered-module binding negatives, 500/500.0001 ms cases, fresh-process benchmark and stale-evidence tests |

All matrix rows have executed local coverage. Full-v1 acceptance criteria remain
open until an exact decorated Tenants candidate receives the required publication
approval, is published/enrolled with release-bound evidence, and both production
Modules pass strict replay and the benchmark on ubuntu-latest. No live
semantic/security or retirement proof is claimed by this loopback lane.
