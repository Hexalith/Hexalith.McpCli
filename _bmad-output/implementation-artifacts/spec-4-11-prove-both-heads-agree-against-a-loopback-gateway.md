---
title: '4.11 Prove both heads agree against a loopback gateway'
type: 'feature'
created: '2026-10-21'
status: 'in-progress'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 'fce41d05e25b8c2076cc02266608460ec86ed635'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-4-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Enrolled replay rebuilds each package alone, so it does not prove
parity for the combined production Catalog. Compatibility preflight, required
result checks and the 500 ms construction gate are incomplete.

**Approach:** Reuse the approved v1 validator and replay machinery against the
built production manifest, covering every exposed operation through separate
CLI and MCP processes. Benchmark the v1 Catalog plus one synthetic Module.

## Boundaries & Constraints

**Always:** Bind approved vectors to exact restored package identities and bytes.
Preflight every prerequisite, invocation and postcondition before replay.
Compare discovery, success/error documents and complete captured requests with
type-preserving JSON equality. Mask only generated message/correlation IDs;
verify supplied correlation/idempotency values and key omission independently
of cross-head equality. Reset scripts between heads. Preserve complete vectors,
strict discovery, lint exceptions, inventory gates and retained failure evidence.

Require both v1 Modules for full acceptance. Benchmark the first
`CatalogBuilder.Build` in a fresh process, excluding process startup and assembly
loading, with exactly one Ulid sample Module; retain isolated String coverage.

**Never:** Add module-specific setup branches, production test hooks, retries,
runtime plugins or extra benchmark Modules. Edit reference contents or infer
approval. Replay establishes transport parity; live authorization, privacy
sanitization and persisted effects remain Story 4.13/retirement gates.

**Sequencing decision (2026-10-21, requesting user):** Implement and verify the
local harness first using available production packages and synthetic fixtures.
Reuse existing components. Tenants publication/enrollment follows as a required
completion step, outside the local implementation phase. Prepare its exact
candidate for approval before publication. Keep Story 4.11 open until both
production Modules pass replay and the benchmark; local green checks cannot
substitute for that evidence. Do not weaken the required-module gate.

## I/O & Edge-Case Matrix

| Input/state | Expected behavior |
| --- | --- |
| Missing/duplicate/stale vector or wrong step kind/schema | Reject before replay, naming source and location |
| Payload depth 64/65 | Apply Core parser/schema rules consistently; reject excess depth before replay |
| Supplied/omitted correlation and idempotency key | Preserve exact supplied values and required presence/absence |
| Extra request field, wrong paging, equal missing result fields | Fail independently of head agreement |
| Validation failure or scripted Gateway failure | Equal full error documents, correct exit/isError and request count |
| Valid extensions | Configure an isolated profile allowlist and preserve request values |
| Missing v1 Module or construction over 500 ms | Fail the full-v1 gate explicitly |

</frozen-after-approval>

## Code Map

- `tools/conformance-vectors/v1/{check_enrolled,verify_artifact,run_loopback}.py`:
  reuse receipt binding and reset replay; current verifier strips production
  references and builds a single-package host.
- `tests/Hexalith.McpCli.ConformanceHost/Program.cs`: test-only manifest inspection
  and real CLI composition; reuse Core `PayloadValidator` for compatibility.
- `tests/Hexalith.McpCli.Core.Tests/EnrolledModuleCoverageTests.cs`: production
  manifest selection; `CatalogTests.StringIdentifierKindDoesNotApplyUlidPattern`
  supplies isolated String coverage.
  `tests/Hexalith.McpCli.Sample.Contracts/Module.cs` declares Ulid.

## Tasks & Acceptance

**Execution:**
- [x] `tools/conformance-vectors/v1/{check_enrolled,run_loopback}.py`,
  `tests/Hexalith.McpCli.ConformanceHost/{Program.cs,Hexalith.McpCli.ConformanceHost.csproj}`
  — inspect and exercise the complete production manifest without injecting the
  sample; retain per-artifact verification as an independent gate.
- [x] `tests/Hexalith.McpCli.ConformanceHost/VectorCompatibilityValidator.cs`,
  `tools/conformance-vectors/v1/{validate,run_loopback}.py` — preflight all calls
  using Core-compatible validation; enforce result contracts and isolated
  extension settings without changing the v1 vector shape.
- [x] `tools/conformance-vectors/v1/{test_validate,test_loopback,test_enrolled,test_process_fixture}.py`,
  `run_packaged_process_fixture.py` — protect the matrix with meaningful negative
  and process cases, including combined-manifest behavior and removed-guard failures.
- [x] `tests/Hexalith.McpCli.Core.Tests/CatalogPerformanceTests.cs`,
  `tools/conformance-vectors/v1/v1-scope.json`, `.github/workflows/ci.yml` — declare
  required production scope as configuration; wire the fresh-process benchmark
  into ubuntu-latest CI and retain population, elapsed time and failure diagnostics.
- [x] `README.md`, `tools/conformance-vectors/v1/README.md`,
  `_bmad-output/implementation-artifacts/evidence/story-4-11/` — document exact
  commands and evidence limits; retain local verification and the outstanding
  Tenants prerequisite separately from full-v1 acceptance.

**Acceptance Criteria:**
- Given both approved v1 releases, when production replay runs, then every
  exposed operation passes discovery, success/error and complete request parity.
- Given any incompatible vector step, when preflight runs, then replay does not
  start and a deterministic diagnostic identifies the source and violation.
- Given v1 Modules plus exactly one sample, when CI constructs the Catalog,
  then construction takes at most 500 ms and isolated alternate-kind tests pass.

## Implementation Notes

The requesting user approved this spec and continued implementation on
2026-10-21. Execute the local harness phase first; the approved sequencing keeps
full-v1 acceptance open until the Tenants prerequisite is completed.

Local implementation and independent review are complete. The authoritative
[final verification and matrix audit](evidence/story-4-11/final/verification.md)
records 139 Python tests, 1,356 .NET tests passed, four existing Windows-only
skips, both sample gates and complete seven-operation production replay. The
final available-population benchmark measured 115.0074 ms. All ten review
correction groups passed verification; eight guard-removal mutations were
detected. No new deferred-work entry was needed.

Acceptance criteria requiring both published v1 Modules remain unsatisfied:
`check_enrolled.py --output <directory>` and the benchmark with
`MCPCLI_BENCHMARK_REQUIRE_V1=true` exit 1 solely for missing `tenants`.
Both record `fullV1Accepted: false`. The user-approved sequencing therefore
keeps this spec and sprint entry `in-progress`; the workflow's completion and
commit step is not entered. Changes remain local and uncommitted. The next
phase must prepare the exact decorated Tenants candidate for approval, then
publish/enroll it with release-bound vectors, receipt and inventory before
rerunning the strict two-module gates. Earlier evidence outside `final/`
records the initial implementation and is retained as history.

## Spec Change Log

## Review Triage Log

### Local implementation review, 2026-10-21

All three independent layers completed before triage. Each finding below is
classified separately; shared causes are grouped only for correction.

| Finding | Verdict and evidence | Route |
| --- | --- | --- |
| BH1: recursive depth traversal | Medium. A 500-level object raises `RecursionError` in the new helper instead of the existing located depth finding; parent reproduced it. | Patch; shared with EC1 |
| BH2: HTTP status assumed to be client error status | Medium. The built production head maps a headerless Query 304 to Gateway error 502. The new contract rejects that supported result. | Patch; shared client-response classification |
| BH3: identical missing error metadata passes | Medium. Parent reproduced acceptance of a 503 error missing supplied correlation, reason and remediation fields. Core's existing failure tests establish their mapping. | Patch; shared with EC2 |
| BH4: independent artifact replay precedes later artifact checks | Low. Separate package gates can replay their own already-preflighted vectors before another package fails. Each uses a reset scripted local Gateway; the combined production run preflights the whole batch and cannot grant acceptance. An extra orchestration barrier adds phases without changing acceptance or external effects. | Reject low, nontrivial orchestration |
| BH5: required scope trusts receipt module labels | Medium. `modules` is populated from receipts, while the combined Catalog is available but not used for scope acceptance. The artifact inventory checker does not bind the receipt label itself. | Patch; bind discovered identities |
| BH6: retained vectors are not rebound between phases | Medium. Combined replay checks artifact bytes again but lacks the analogous vector-hash check against the independent verification receipt. Changed retained assertions could enter the added phase. | Patch; check recorded vector hashes before combined consumption |
| BH7: generated message reuse is masked | Medium. A constant canonical message ID can survive current masking across distinct submissions. The per-call identity requirement needs a uniqueness check on captured generated request IDs. | Patch |
| BH8: early benchmark failure can leave stale success | Medium. Evidence is written after scope parsing and construction; a failed repeated local run can leave the prior successful JSON at the documented output path. | Patch; invalidate and retain failure evidence |
| BH9: benchmark child timeout/cleanup | Low. The current finite Catalog builds pass; no hanging input or provider was demonstrated. A separate timeout policy and process-tree cleanup add machinery for a hypothetical future hang; CI retains its job execution limit. | Reject low, nontrivial timeout machinery |
| BH10: direct Python entry points precede new classes | Low. Direct execution stops at `unittest.main()` before defining the added classes; discovery is unaffected. Moving the existing guards is a direct correction. | Patch |
| EC1: depth 500 has no located diagnostic | Medium. Independently confirms BH1's reproduced recursion failure. | Same patch as BH1 |
| EC2: supplied error correlation/remediation can disappear | Medium. Independently confirms BH3; equality alone does not protect the supplied fields. | Same patch as BH3 |
| VG1: partial production failure observations lack a test | Medium, pre-verified. The existing failing fixture exercises per-artifact replay without `evidence_dir`, so deleting the `finally` retention writes is not detected. | Patch; add a failing combined-replay observation assertion |
| VG2: semantic HTTP-200 query failure rejected | Medium. Existing `SuccessfulHttpFailureHasNoResultAsync` and a parent production-head probe confirm error status 200 with `success:false`; the new contract incorrectly requires success fields. | Same client-response patch as BH2 |
| PF1: other supported client error mappings | Medium. Parent probes also confirm Problem Details status 422 overriding HTTP 409, and a Query 204 becoming a parse error with status 204. Both contradict the new status-only classification. Evidence: `evidence/story-4-11/parent-error-probes-before.json`. | Same client-response patch as BH2/VG2 |
| PF2: over-budget branch lacks negative protection | Medium. Existing benchmark tests measure an under-budget Catalog; removing only the 500 ms refusal has no failing boundary case. The repository requires a negative test for each new guard. | Patch; protect the exact 500 ms and over-limit boundary without adding production surface |

All patch rows above are resolved in the reviewed local candidate. Final checks
passed after the corrections, including the complete packaged process fixture.
The parent also replayed all four captured real client error outcomes through
the corrected contract checker and audited the retained inputs against approval.
The two rejected low-impact proposals remain rejected; no deferral was added.

## Design Notes

Tenants is absent from the production manifest, approval directories and release
inventories. Pinned 5.9.0 predates decoration; Story 4.8 approves only
`0.0.0-story48` and explicitly defers release/enrollment. Its existing approval
cannot authorize release bytes. Parties 1.5.1 has seven artifact-bound vectors.
The integral-floating paging deferral is already resolved by strict token typing.

## Verification

- `python3 -m unittest discover -s tools/conformance-vectors/v1 -p 'test_*.py'`
  — baseline: 112 passed; all regressions must pass.
- `dotnet restore Hexalith.McpCli.slnx`, then
  `dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror`;
  run each existing test project individually in Release.
- Run both sample conformance scripts, restore the solution afterwards, then
  run `check_enrolled.py --output /tmp/mcpcli-story411-evidence` and the new CI
  benchmark invocation. Full acceptance requires both v1 Modules.
