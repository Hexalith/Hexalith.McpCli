---
title: '4.11 Prove both heads agree against a loopback gateway'
type: 'feature'
created: '2026-10-21'
status: 'done'
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

Current release/enrollment preparation is recorded in
[the continuation status](evidence/story-4-11/publication-20261021/continuation-status-current.json).
The dated local-phase results below remain historical; they do not describe the
current two-module enrollment or grant full-v1 acceptance.

### Local-phase history — 2026-10-21

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

### Tenants prerequisite candidate prepared, 2026-10-21

The continuation began from the already-committed local harness at
`7f4a08cb4b7ff9402d1dcf0826ad45ab0256ba65`. The
[pending candidate and prerequisite plan](evidence/story-4-11/tenants-candidate/approval-plan.md)
binds current Tenants source `2cd3cc270e88d3cdbb47a1a938fd6a0951b6f0d4`,
mechanically version-rebound 5.10.0 vectors, a pending release inventory, exact
local package bytes and the proposed dependency/enrollment delta.

The current unmodified Tenants package build fails with CS0246 because published
EventStore.Contracts 3.126.0 lacks `NativeSourceProof`. Isolated committed-source
EventStore.Contracts/Client 3.126.1 packages from
`b6d1807035fba2e485c8587ac3581d669d1036e5` repair that package proof without
changing original source or reference trees. They are unpublished prerequisites,
not a qualified fourteen-package/container EventStore release. The resulting
Tenants candidate passes all fourteen independent vector replays and the complete
21-operation Parties/Tenants candidate replay. The proposed dependency policy
passes 98 tests; isolated String coverage passes; the cold Catalog plus exactly
one Ulid sample measured 148.0593 ms. Every candidate summary explicitly retains
`fullV1Accepted: false` and `productionAccepted: false`.

An independent reviewer given only this candidate's public discovery documents
completed the [fresh-context description check](evidence/story-4-11/tenants-candidate/description-review.md):
pass with one low-severity wording advisory and no blocking findings. The parent
independently verified all three package hashes, all fourteen mechanical vector
rebindings and the retained evidence hashes.

At candidate preparation, the 20 proposed inventory decisions were pending and
the real inventory checker rejected them. Publication needs owner-approved upstream source, the
existing full EventStore and Tenants release gates, committed owning Builds
pins/gitlinks, refreshed exact-release verification and genuine release-bound
approvals before production enrollment. Neither publication nor enrollment was
performed. Both strict production gates and this spec/sprint's `in-progress`
status remain intact; see the linked plan for exact scope and commands.

### Candidate scope and vector approval recorded, 2026-10-21

The requesting user answered **"I approve"** to the explicit question approving
the candidate's fourteen vectors and twenty inventory decisions (fourteen
included operations and six exclusions). The
[owner approval](evidence/story-4-11/owner-approval/approval.json) binds the exact
sealed candidate packet, artifact, source commit and vector hashes. The pending
candidate packet remains unchanged as historical evidence. The new
[approved inventory](evidence/story-4-11/owner-approval/approved-inventory.json)
changes only each row's approval status/reference; the actual combined-host
inventory checker now exits 0 with `[]` on stdout and empty stderr. Its exact
command and result are retained in
[inventory verification](evidence/story-4-11/owner-approval/inventory-verification.json).

This approval resolves the candidate vectors and inventory decisions, including
the `ResolveTenantReadAuthority` exclusion. Do not ask for those decisions again.
It does not authorize the broader EventStore fourteen-package/container and
Tenants five-package/container publication workflows, transfer approval to new
artifact/source identities, or grant production/full-v1 acceptance.

Continue the reversible prerequisite preparation described in the candidate
plan. Inspect current committed upstream source and preserve existing changes;
both owning repositories have advanced since the approved package snapshots.
Use isolated source snapshots outside `references/` for complete local release
package qualification and relevant tests. Retain the original approved source
and bytes separately from any refreshed candidate, with exact source/package
differences and commands. Prepare the full required release scope and identify
the remaining exact-source CI/protected-publication gates before requesting a
publication decision. Do not publish or push unrelated upstream work. Keep the
strict production gates and this story/sprint `in-progress` until the original
acceptance conditions are met.

### Protected release chain authorized, 2026-10-21

The requesting user answered **"yes"** to the explicit question authorizing the
protected EventStore fourteen-package/container release followed by the Tenants
five-package/container release after their required gates pass. The
[publication authorization](evidence/story-4-11/owner-approval/publication-authorization.json)
binds the [sealed release preparation](evidence/story-4-11/release-preparation-20261021/approval-plan.md),
its exact reviewed Builds/Tenants proposals and the full publication scopes.
The earlier vector/inventory approval remains valid. Do not request either
approval again for this chain.

This is the explicitly authorized publication/enrollment continuation outside
the completed local harness phase. The user's later authorization permits the
necessary owning-repository changes, commits, pushes, normal PR/CI operations,
protected workflow dispatch and permitted protected-environment approvals. It
supersedes the local implementation workflow's no-push/no-remote restriction
for this continuation, while all normal source, CI, protected publication,
commitlint, package/OCI validation and final-byte binding gates remain binding.
Do not bypass protections or overwrite unrelated work.

Execute the remaining chain through completion: inspect current sources and
normal workflow controls; apply and verify the shared Builds target/tests and
Tenants import/publisher pin in their owning repositories; commit/push through
normal validated procedures; qualify actual final EventStore source, publish its
normal full scope only when exact-source gates pass, update the owning Builds
dependency pin and root gitlinks, then qualify/publish Tenants' normal full scope.
Capture actual final versions and canonical source commits from tooling, compare
and verify final immutable artifacts and public discovery against approved
vectors/inventory, and enroll only authentic published Contracts. Then run all
required McpCli checks and the unchanged strict two-module replay and cold Catalog
benchmark on ubuntu-latest. Keep the story/sprint open until acceptance is met.

The approved package snapshots are retained historical evidence, not a substitute
for final-source qualification. Current upstreams have continued advancing; use
fresh exact-source CI and registry/source preflight before each release. Preserve
any unrelated uncommitted upstream edits. If CI fails, investigate and fix the
necessary release prerequisite in the owning repository without weakening gates.

## Spec Change Log

## Review Triage Log

### Resumed pass 4 independent review — 2026-10-22

All three context-free layers completed before triage. The parent reproduced
all eight SDK/oracle outcomes in
[response probes](evidence/story-4-11/review-pass4/parent-response-probes.json)
and inspected the original baseline for inherited helper/receipt behavior.
Each filed finding has an individual verdict below; shared carried rulings
retain their original route.

| Finding | Verdict and evidence | Route |
| --- | --- | --- |
| PBH1: timestamp empty fraction before a timezone | Low. The real SDK accepts `.Z` and `.+02:00`; the regex refuses both. Python's existing datetime check accepts both, so changing the existing fractional digit bound directly repairs the false refusal. | Patch; grammar and real-SDK regressions |
| PBH2: U+001C–U+001F whitespace | Low; carried from pass 4's logged whitespace ruling at `run_loopback.py:412`. Parent probes reconfirm the same fail-closed discrepancy; the required whitespace helper remains disproportionate for these unusual controls. | Keep carried rejection |
| PBH3: lone-surrogate response values | Low. Parent reproduced typed-string parse errors and opaque-payload serialization errors while the oracle predicts success. These invalid Unicode strings are unlikely in maintained vectors; handling multiple parsing/serialization boundaries adds branches and policy beyond a direct correction. | Reject low, nontrivial boundary handling |
| PBH4: quoted integers with 5,000 leading zeroes | Low. Parent reproduced SDK pageSize 7 while Python's integer digit cap predicts parse failure. Removing redundant leading zeroes in the existing conversion directly fixes it without changing ranges or accepted signs. | Patch; conversion and real-SDK regressions |
| PBH5: binary floating-point result comparison | Medium, pre-existing. Parent confirmed distinct decimal tokens collapse under the unchanged JSON loader before equality. The representation/precision limitation is already tracked. | Already tracked (`deferred-work.md:138`); no duplicate entry |
| PBH6: duplicate output JSON members | Low, pre-existing. `HeadProcess` uses ordinary `json.loads`, which retains the last occurrence. The shipped serializers emit unique members; reaching this needs an invalid head response, and strict parsing adds new refusal behavior to three protocol boundaries. | Reject low, nontrivial parser guards |
| PBH7: MCP stderr pipe saturation | Low, pre-existing. The unchanged helper does not drain its pipe during the request; sufficiently large diagnostics can block a writer. Unlike the already-tracked lost-stderr claim, this is a separate blocking outcome. No normal per-call host flooding was shown; a concurrent drain adds lifecycle machinery. | Reject low, nontrivial process machinery |
| PBH8: malformed MCP content/isError envelope | Low, pre-existing. The helper reads the text member without checking content type and coerces isError. The pinned SDK emits the specified types; the demonstrated fake responder is invalid and the fix adds new protocol guards. | Reject low, nontrivial protocol guards |
| PBH9: later package failure omits completed packages from root results | Low, pre-existing in the original baseline loop. Root status receives results only after all packages finish. Individual child receipts retain the evidence, but root-level diagnosis loses completed-package progress. | Defer inherited receipt aggregation |
| PBH10: standalone artifact replay lacks observation files | Low, pre-existing. The standalone invocation retains channel logs but passes no observation directory; the new combined phase retains the complete documents/requests required for production acceptance. Extending the standalone CLI and multiple signatures adds machinery for duplicated successful-run evidence. | Reject low, nontrivial observation plumbing |
| PEC1: U+001C–U+001F detail | Low; carried from pass 4's logged whitespace ruling. Same `_nonblank` location and fail-closed outcome as PBH2. | Keep carried rejection |
| PEC2: truncated benchmark evidence | Low; carried from REC2 and pass 4's `RetainFailure` ruling. Normal writers produce complete JSON; recovering interrupted partial writes requires another failure branch. | Keep carried rejection |
| PVG1: synthetic 503 message-ID freshness call lacks a regression | Medium, pre-verified. The reviewer removed only the error-loop freshness invocation; all 157 tests stayed green. A runner fixture reusing a normal request ID only for 503 calls fails with the guard and passes without it. | Patch; complete-run negative regression |

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

### Final enrollment review — 2026-10-22

All three context-free review layers completed before parent triage. The parent independently reproduced all response/default/paging/parser cases against the built real SDK host, the command-204 binding refusal, the complete-Catalog guard-removal gap, changed-runtime-DLL preflight acceptance and missing structured failure progress. Exact observations are retained in [response probes](evidence/story-4-11/publication-20261021/parent-final-review-response-probes.json) and [other probes](evidence/story-4-11/publication-20261021/parent-final-review-other-probes.json). The successful Ubuntu head recorded in the continuation remains valid historical evidence; current completion awaits these bounded corrections and final verification.

| Finding | Verdict and evidence | Route |
| --- | --- | --- |
| BH11: response property casing | Medium. A schema-valid `Success:true` query succeeds in the pinned real SDK but the raw case-sensitive oracle requires semantic failure. Parent reproduced it. | Patch; typed response normalization |
| BH12: paging defaults and unknown members | Medium. Actual SDK projects offset-only paging to include pageSize 0 and drops an unknown member; both valid query documents fail the raw-response oracle. Parent reproduced both. | Patch; same normalization root cause |
| BH13: typed/deep response parse failures | Medium. Schema-valid depth-65 payload and string-valued success produce correct SDK parse errors at HTTP 200, which the oracle mistakes for success. Parent reproduced both. | Patch; same normalization root cause |
| BH14: malformed open metadata crashes receipt orchestration | Medium. Schema-valid paging `[]` produces an SDK parse error but raises AttributeError in the oracle; the outer enrollment handler does not catch it, leaving its prior pending receipt. Parent reproduced the shape failure. | Patch; same normalization root cause |
| BH15: uncovered complete-Catalog guard has no negative test | Medium. Parent removed only the uncovered-operation refusal in memory; all 34 loopback tests still passed. No existing test supplies an exposed unselected operation. | Patch; direct negative regression |
| BH16: separate MCP processes cannot detect per-session cached IDs | Low. This is a real limitation of the pre-existing per-call process lifecycle, rather than an observed product reuse defect. The actual repeated-same-executor distinct-ID test passed. A persistent-session runner adds orchestration for an unobserved cache state, beyond a direct correction. | Reject low, nontrivial session machinery |
| BH17: successful replay calls do not retain stderr | Low. The unchanged baseline helper parses successful CLI stdout then drops stderr; normal MCP shutdown closes its stderr pipe. Existing channel tests still protect product guards, but replay observations do not retain those diagnostics. | Defer pre-existing helper limitation |
| BH18: a successful no-op benchmark probe could leave pending evidence | False. The parent launches the exact measured Fact with MCPCLI_BENCHMARK_PROBE=1; that selected path must write measured evidence or fail. The ordinary non-probe Fact return is not the child path. No reachable zero-exit/no-op state was shown, and the actual CI measurement is present. | Reject on refutation |
| BH19: output Contracts DLL is not bound to the approved archive | Medium. Parent isolated the actual production deps/assets and approved signed archive, changed only the copied output DLL bytes, and the host-artifact preflight still passed. This exposes an exact-runtime-byte gap in the new combined lane. | Patch; compare selected runtime asset bytes with archive entries |
| BH20: structured production failure progress is lost | Low. Parent forced restore exit 19: full channel logs remain, but the locally accumulated command/exit list never reaches enrolled.json when production_replay raises. The failed combined phase therefore lacks the structured progress the independent phase retains. | Patch; direct progress retention |
| EC3: omitted optional query success is treated as false | Medium. Parent reproduced an actual successful query with omitted success rejected as semantic failure; the pinned SDK defaults it to true. | Patch; same normalization root cause as BH11–BH14 |
| EC4: parent cancellation can leave a late-writing benchmark child | Low. Source permits a child to finish after cancellation directed only at the parent; the reviewer did not reproduce a runner trigger. This has a short measurement window, and required job/source binding prevents a cancelled job from granting full acceptance. It needs added process-lifecycle machinery rather than a direct correction. | Reject low, nontrivial cleanup machinery |
| VG3: command 204 errors incorrectly require echoed correlation | Medium. Parent validated the complete modified vector and reproduced the correct SDK parse error without correlation, then the binding helper rejected it. Masking independently makes the same error. Correlation must be required/bound only when the expected SDK error actually contains it. | Patch; error correlation binding and masking |

The five correction groups are typed SDK outcome normalization (BH11–BH14/EC3), command parse-error correlation (VG3), complete-Catalog negative coverage (BH15), selected runtime byte binding (BH19), and structured production progress (BH20). No frozen intent or public product surface changes are required. Each filed claim has its own verdict above; the earlier local triage was checked and no claim here has the same location and bad outcome as a carried row.

The same implementation agent applied all five correction groups. The parent verified every focused source/log hash, the real SDK batch, and both guard-removal failures; the deepest response reachable through the Core vector-file parser also returns the expected SDK parse classification. Full mandatory verification is running, and a new normal Ubuntu run on the corrected source is still required. The one pre-existing stderr-retention limitation is tracked in `deferred-work.md:568`.

### Resumed build independent review — 2026-10-22

All three context-free layers completed before triage. Verification Gap found
no gaps. The parent reproduced ten SDK/oracle disagreements against the actual
production host in [response probes](evidence/story-4-11/review-pass3/parent-response-review-probes.json).
Each filed claim has its own verdict below; the original approved vectors,
inventory and frozen intent remain unchanged.

| Finding | Verdict and evidence | Route |
| --- | --- | --- |
| RBH1: quoted positive paging integers | Medium. The pinned SDK accepts `"+7"` and returns 7, but the new oracle predicts a parse failure; parent reproduced it. | Patch; numeric-string grammar |
| RBH2: broader Python timestamp grammar | Medium. Week dates, a space separator and comma fractions pass `fromisoformat` but the real SDK returns the exact query parse error; parent reproduced all three. | Patch; SDK timestamp grammar |
| RBH3: invalid earlier case-variant property | Medium. `success:"false", Success:true` loses the invalid earlier value in the oracle's dictionary, while SDK parsing fails before reading the later value; parent reproduced it. | Patch; ordered typed-property validation |
| RBH4: Unicode case folding | Medium. The oracle maps long-s `ſuccess` to `success`, while the SDK ignores it; parent reproduced the resulting incorrect semantic-failure expectation. | Patch; matching property-name comparison |
| RBH5: malformed Problem Details status | Medium. Quoted, null and boolean `status` values produce the real head's `internal_error`, while the oracle invents a Gateway error; parent reproduced all three. | Patch; preserve demonstrated SDK error outcomes |
| RBH6: missing query payload differs from null | Medium. An omitted payload produces an internal serialization error, while explicit null is a valid JSON value; parent reproduced the missing-payload outcome rejected by the oracle. | Patch; preserve missing versus null |
| RBH7: full replay binding invocation is unprotected | Medium. Removing only the full-run `_assert_result_request_binding` call leaves all 148 Python tests green. Direct helper tests do not protect the invocation. | Patch; full-run negative binding regression |
| RBH8: maintained real-SDK fixture omits established error mappings | Low. 304, semantic HTTP-200 failure and Problem Details status override have unit/historical coverage but no maintained SDK fixture cases. Adding cases to the existing fixture directly protects the oracle's dependency assumptions. | Patch; extend existing fixture |
| RBH9: successful-process stderr is discarded | Low, carried from BH17 and `deferred-work.md:568`: same unchanged helper location and bad outcome. | Already tracked; no duplicate deferral |
| RBH10: MCP shutdown exit status is ignored | Low. The pre-existing helper waits after a valid tool response but ignores the eventual process status. No actual product shutdown failure was shown; a new lifecycle/status policy and guard add complexity for an unlikely fault. | Reject low, nontrivial lifecycle guard |
| REC1: typed response oracle discrepancies | Medium. Independently confirms RBH1/RBH2/RBH5/RBH6, with the same parent-reproduced outcomes. | Same patches; preserve every demonstrated outcome |
| REC2: truncated benchmark evidence masks original failure | Low, carried from the prior code-review rejection of `RetainFailure`: every normal writer emits complete JSON, and only a kill mid-write reaches the proposed guard. | Keep prior rejection; no new patch or deferral |

All nine surviving filed claims above are corrected and verified. The final
[parent acceptance/matrix audit](evidence/story-4-11/review-pass3-corrections/parent-acceptance-matrix-audit.json)
confirms the complete local gate run, actual named matrix coverage, unchanged
source inputs and all ten parent-reproduced SDK outcomes. No new deferral was
added; carried decisions and the original frozen intent are preserved.

## Original design context — 2026-10-21

The following paragraph records the initial local-phase design context.

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

## 2026-10-22 continuation: authentic owner releases (in progress)

Owner releases now exist: EventStore 3.126.1 at `1748b16b11fb63b885dfa2fd4a9c7a420ea103a9` and Tenants 5.10.0 at `82c2e9ad51f4d9ceeae9dcde33d7e0273524a105`. All nineteen actual NuGet archives match immutable registry hashes and pass signature verification. The signed Tenants Contracts artifact passes the original fourteen vector bytes, approved twenty inventory decisions and exact lint approvals; its Contracts and Client source trees equal the approved snapshot. These are new observations; historical candidate hashes and results remain unchanged. Evidence is under `evidence/story-4-11/publication-20261021/owner-published-*`.

The normal EventStore release/source and OCI provenance qualify. Tenants 5.10.0 used the old publisher and retains eight incorrect or missing source-label values across the two container RIDs. It does not satisfy the specifically authorized repaired full release chain. Continue the approved shared-target import/publisher repair from current Tenants source, exact-source CI and normal semantic follow-up; no redundant EventStore release is required. The earlier unmerged EventStore qualification PR is diagnostic rather than a prerequisite of the completed normal owner release.

Builds main `25ba30d666284a32b3361272dd0f5c59a7964679` already contains both published declarations. Refresh their deterministic audit in a normal audit-only squash PR bound to that real ancestor, preserving every other family and the truthful unresolved nonpackable UI row. The unanswered merge-policy proposal remains unapplied. Story and sprint remain in progress; both strict production gates and the authentic Ubuntu combined replay/cold-Catalog acceptance requirements remain binding.


### 02:31 UTC: current Builds fixture prerequisite

The first audit-only PR head `85290197d2a4324b50560630e8992d71c3318784` failed its ordinary module suite: 112 cases reached the exact-pin refusal because valid fixtures and the shipped v1 schema still selected EventStore 3.126.0 while the authoritative catalog selected 3.126.1. That failure and the original one-file audit proof remain historical evidence.

PR [Hexalith.Builds #130](https://github.com/Hexalith/Hexalith.Builds/pull/130) now includes the bounded schema/live-fixture alignment at `6dd10644de86dd0656df0653a8a1f143f07352cf`, preserving the original catalog declarations, other audit families, runtime C# source, historical qualification records and exact equality guards. Active synthetic corpus digests are explicitly rebound; previous 3.126.0 is an added refusal control, including jointly rehashed publisher evidence. Local focused checks, all three Builds test projects, affected publisher contracts and real ordinary-CI package qualification pass. Fresh exact-head remote CI remains required before normal merge and the final Tenants Builds pin. No repository protection or publication action was applied by this prerequisite repair; production/full-v1 acceptance remains pending. Current bindings and retained failures are in `evidence/story-4-11/publication-20261021/continuation-status-current.json` and the associated `builds-live-fixture-pin-*` receipts.

### 03:23 UTC: Builds prerequisite cleared; Tenants repair in normal PR qualification

Builds PR130 subsequently passed all four ordinary CI jobs and every required context/App identity. Its normal squash merge `c0cbbbd4366d512cc1731397f14dd53a7a01580d` has the exact checked `6dd10644de86dd0656df0653a8a1f143f07352cf` tree, the expected sole parent `25ba30d666284a32b3361272dd0f5c59a7964679`, and the explicitly supplied, pinned-commitlint-validated full message. Independent parent audit confirms the tree and unchanged squash-only protection. The temporary merge-policy proposal remains unanswered and unapplied.

Tenants [PR54](https://github.com/Hexalith/Hexalith.Tenants/pull/54), head `b021e6964c330c849276512b0650a3a2353b7a0b`, contains exactly the reviewed three repair blobs plus that qualified Builds gitlink. All seven local project runs on the checked Builds tree passed (9,492 tests); after binding the actual merge pin, every tracked regular-file/symlink byte in the five initialized checkouts remained equal, Contracts passed all 654 tests, and the four existing source-governance regression suites passed. Exact-source normal PR/main CI and the protected full five-package/container follow-up still remain required. These results do not grant production or full-v1 acceptance. The current release-consumption path and source/test bindings are retained in `evidence/story-4-11/publication-20261021/continuation-status-current.json` and `tenants-followup-*` receipts.

### 03:36 UTC: exact enrollment artifact selected; repaired full release remains required

The [version-selection assessment](evidence/story-4-11/publication-20261021/exact-enrollment-version-selection.md) records the chosen authentic Contracts 5.10.0 artifact at source `82c2e9ad51f4d9ceeae9dcde33d7e0273524a105` for enrollment after the repaired normal full follow-up release qualifies. This preserves all fourteen original vector bytes and the current qualified Builds `c0cbbbd4366d512cc1731397f14dd53a7a01580d` declarations. The spec and unchanged verifier require exact approved restored identities/bytes; neither requires the latest NuGet version or equality with the container version. The independent parent assessment agrees.

The repaired full five-package/container release remains mandatory and has its own exact source, semantic version, signed archives and OCI provenance. Its success cannot change the historical malformed 5.10.0 container. The enrollment receipt will instead bind the actual signed 5.10.0 Contracts archive/restore hashes and source, both existing user approvals, approved inventory and final verification. Production enrollment, full-v1 acceptance and the final Ubuntu gates remain pending. The original temporary Builds policy question remains unanswered and unapplied; this exact-version selection makes a new central pin or policy edit unnecessary for Story 4.11.

### 04:38 UTC: repaired full release qualified; final Ubuntu acceptance pending

Tenants PR54 merged normally at `205cbc5019343d344643b530fb03aee82af2840d`, with the exact checked four-path tree. Its normal exact-main CI succeeded under the existing advisory Aspire policy; the three advisory observations remain retained and were not converted into new release requirements or bypassed. The normal protected release [39721533752](https://github.com/Hexalith/Hexalith.Tenants/actions/runs/39721533752) published version 5.10.1. The [independent full-repair qualification](evidence/story-4-11/publication-20261021/parent-tenants-5.10.1-full-repair-qualified.json) binds all five public signed NuGet archives, normal source/protected controls, both OCI architecture/config digests, exact source/version labels, complete UTC creation timestamps and both digest-bound health smokes. This clears the separately mandatory repaired full-release prerequisite; it does not repair the historical 5.10.0 container.

Root enrollment uses the authentic Contracts 5.10.0 artifact at `82c2e9ad51f4d9ceeae9dcde33d7e0273524a105` with all fourteen original approved vector bytes, twenty inventory decisions and exact lint exceptions unchanged. The [new release-bound enrollment record](evidence/story-4-11/publication-20261021/tenants-5.10.0-release-bound-enrollment.json) links both existing user approvals, authentic signed archive and restore-content identities, the qualified full follow-up release and the unchanged public-description review. The qualified Builds gitlink remains `c0cbbbd4366d512cc1731397f14dd53a7a01580d`; no new version pin or repository-policy mutation was needed.

All six local root projects passed with 1,356 tests and four existing Windows-only skips; all 139 named Python tests, both Sample gates and six documented offline CLI commands passed. The final fresh task cache, assets, dependency document and shipped gateway/Contracts DLLs match the authentic approved archives. These local observations retain `productionAccepted: false` and `fullV1Accepted: false`. The story and sprint remain in progress pending actual Ubuntu strict 21-operation CLI/MCP replay, the first Catalog construction with exactly one Ulid sample at most 500 ms, isolated String coverage and the final independent acceptance review.

### 05:02 UTC: actual Ubuntu acceptance verified; final review pending

The [parent artifact and matrix audit](evidence/story-4-11/publication-20261021/parent-root-ubuntu-acceptance-audit.json) independently verifies actual normal CI [39724191822](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/39724191822) on `bf9c49afc7b81e30459b4c9c26074ac5a08d2ecd`. The actual PR checkout `a71233072b4f7e822f325af61b3d647c9fcf3e60` has the same full tree `ee3372fe9d9da62211b540a9e433c57306912623`. All four required jobs passed; all six ordinary projects produced 1,356 passed tests and four existing Windows-only skips, all 139 named Python tests passed, and both Sample gates passed.

| Acceptance criterion | Actual verification |
| --- | --- |
| Both approved production releases cover every operation through both heads | Authentic Parties 1.5.1 and Tenants 5.10.0 archives, original vectors and approved inventory/lint bytes match. Strict combined production replay passed all 21 operations and 78 preflight calls; parent rechecked 198 retained success/error documents and complete captured requests. |
| Incompatible vector steps fail before replay with located deterministic diagnostics | All-position kind/schema/identifier/depth process negatives and the complete named 139-test suite passed; every frozen matrix row has actual named passing coverage. |
| First Catalog construction with exactly one sample is at most 500 ms; alternate kind remains covered | Actual fresh-process Ubuntu measurement was 242.6181 ms, with exactly Parties, Tenants and one Ulid sample, no failures/missing modules/diagnostics. The isolated String test and 500/500.0001 ms boundary and failure-evidence cases actually passed in the ordinary native TRX. |

The unchanged strict gates now report `fullV1Accepted: true`. All execution tasks and acceptance criteria are verified. Story and sprint remain in progress for the next sequential BMAD independent review and completion record. No live authorization, sanitization, persisted effects or retirement acceptance is claimed.

## Completion — 2026-10-22

The five final-review correction groups are resolved. The [corrected-source Ubuntu acceptance audit](evidence/story-4-11/publication-20261021/parent-root-review-fixed-ubuntu-acceptance-audit.json) binds normal CI [39730145591](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/39730145591), reviewed source `c887634d4dad1f536bc888c7294d3e3ffa0da8f4`, its equal-tree actual PR checkout, all four required jobs and every acceptance/matrix row. It rechecks all 21 production operations, 78 preflight calls and 198 documents/requests; first Catalog construction with exactly one Ulid sample is 194.5002 ms. All 1,356 ordinary tests, 146 named Python cases, both Sample gates and the isolated String/budget/failure-evidence cases passed.

The [complete parent local re-verification](evidence/story-4-11/publication-20261021/parent-final-review-local-verification.json) also passed after the corrections. Both original approval records, fourteen Tenants vector bytes, twenty inventory decisions, exact lint exceptions and frozen intent remain unchanged. The separate normal Tenants 5.10.1 full release remains qualified; enrollment stays on authentic Contracts 5.10.0. The nine final patched claims are verified, three are rejected on their logged evidence, and the one pre-existing low stderr-retention limitation is tracked at `deferred-work.md:568`.

The spec is done and Story 4.11 is in sprint review under BMAD completion rules. Root [PR1](https://github.com/Hexalith/Hexalith.McpCli/pull/1) contains the implementation; no root merge or release is performed. This proves scripted transport parity and Catalog construction, while live authorization, privacy, persisted effects and retirement keep their later gates.

### Review Findings (code review pass 3, 2026-10-22)

Code review 2026-10-22 of the complete committed story range `fce41d0..2a2d88b` (`7f4a08c`, `f20a4e0`, `bf9c49a`, `c887634`, `2a2d88b`).

- **Code-only scope:** excludes `_bmad-output/` and the `references/Hexalith.Builds` gitlink move; includes the fourteen approved Tenants vectors and `tenants-approved.json`.
- **Size and mode:** 39 files, +6,476/−74, 7,240 diff lines, full mode, with `epic-4-context.md` as context.
- **Layers:** Blind Hunter (BH), Edge Case Hunter (EC), Verification Gap (VG) and Acceptance Auditor (AA). No layer failed.
- **Result:** 46 normalized findings. 26 survive as 16 patch and 2 defer entries; 20 are rejected. No decision is needed.

Parent checks during triage:
- With `MCPCLI_BENCHMARK_PROBE=1`, the built Core.Tests DLL run with `-method Hexalith.McpCli.Core.Tests.CatalogPerformanceTests.DoesNotExist` reports `Total: 0`, exits 0 and writes no evidence. This is the reachable zero-exit no-op state that the final enrollment review's BH18 refutation said had not been shown.
- Two complete local Core.Tests runs (14 cores, parallel classes) recorded the child at 146.2998 and 124.8679 ms (`local-only`). Six `mcpcli-catalog-*.json` files remained in `/tmp` afterwards.
- `validate.py:166` requires `expectedGateway.body.tenant` to equal the envelope tenant. `schema.json` bounds `pageSize` and `offset` to int32 and extension values to strings. `run_catalog` runs `validate_vectors` before every `--validate-vectors` call.
- Story 4.16 gates on "a green `main` source SHA" (`_bmad-output/planning-artifacts/epics.md:1537`), not on `enrolled.json`.

- [x] [Review][Patch] R1 — medium. The benchmark parent asserts only the child's exit code. xUnit v3 exits 0 when `-method` matches nothing, and outside the probe the child returns early as a pass. Either change leaves `catalog-benchmark.json` at `pending` while the unit tier and the strict CI step both pass, so the 500 ms gate disappears everywhere:
  - rename `MeasureFirstConstruction` (the filter at `:31` is a string literal);
  - rename the probe variable at only one of `:32` and `:51`.

  Fix: after exit 0, parse the evidence and require all of:
  - `result` equal to `passed` under `MCPCLI_BENCHMARK_REQUIRE_V1=true`, and `local-only` otherwise;
  - a numeric `elapsedMilliseconds` of at most 500;
  - a `processId` different from the parent's.

  Build the filter with `nameof`. The enrolled job's separate `-class` filter keeps the carried Story 4.10 ruling, because the `ci` job runs all of Core.Tests (VG, BH, EC). [tests/Hexalith.McpCli.Core.Tests/CatalogPerformanceTests.cs:38]
- [x] [Review][Patch] R2 — medium. No test reaches the benchmark's failure composition with a violation present. `ConstructionLimitIncludesOnlyAtMostFiveHundredMilliseconds` tests only `LimitViolation`, and the strict CI run always has both modules.
  - Deleting `:76` lets an over-500 ms construction write `result: passed` and exit 0. No other code enforces the limit.
  - Deleting `:77` lets a strict run without Tenants write `fullV1Accepted: true`.

  Fix: extract the failures, `result` and `fullV1Accepted` computation into a static helper that takes diagnostics, elapsed time, required and discovered modules, and `requireV1`. Cover it with a `[Theory]` for the over-limit, strict-missing and local-missing cases (VG, BH). [tests/Hexalith.McpCli.Core.Tests/CatalogPerformanceTests.cs:74]
- [x] [Review][Patch] R3 — low. No test protects the stale `production-observations/*.json` cleanup. VG deleted `:155-156` in a scratch copy, and all 46 `test_enrolled` tests still passed. A rerun into the README's fixed output path that fails before or during replay would keep the previous run's success documents. Fix: seed `production-observations/old.json`, run `main()` with `production_replay` failing, and assert the file is gone and `enrolled.json` reports `failed` (VG). [tools/conformance-vectors/v1/check_enrolled.py:155]
- [x] [Review][Patch] R4 — low. The same cleanup leaves `production-{restore,build,replay}.{stdout,stderr}.txt` from the previous run. When a rerun's restore fails, the old build log and the `PASS` replay lines stay next to the failed `enrolled.json`. Story 4.10 pass 3 rejected stale `inputs-*` copies and logs as carried. This case differs: this story added the cleanup to this function, and the fix unlinks six known names there (AA, EC). [tools/conformance-vectors/v1/check_enrolled.py:155]
- [x] [Review][Patch] R5 — low. Without `MCPCLI_BENCHMARK_OUTPUT`, every ordinary Core.Tests run writes `mcpcli-catalog-<random>.json` to the temp directory and never deletes it. Delete the default-path file in `finally` (VG, BH). [tests/Hexalith.McpCli.Core.Tests/CatalogPerformanceTests.cs:19]
- [x] [Review][Patch] R6 — low. Outside the probe, `MeasureFirstConstruction` returns early and counts as passed, which inflates the passed totals the evidence cites. Skip it with the probe condition instead (`Assert.SkipUnless`) (BH). [tests/Hexalith.McpCli.Core.Tests/CatalogPerformanceTests.cs:51]
- [x] [Review][Patch] R7 — low. The `scope`, `loading` and `construction` cases of `EarlyFailureInvalidatesPriorSuccessfulEvidence` all run the same synthetic throw, so none exercises a real phase. Collapse them into one `[Fact]` named for the wrapper behavior it proves (BH). [tests/Hexalith.McpCli.Core.Tests/CatalogPerformanceTests.cs:110]
- [x] [Review][Patch] R8 — low. `sample.GetCustomAttribute<HexalithModuleAttribute>()` and `JsonDocument.Parse` run before `Stopwatch.StartNew()`. They warm the attribute and System.Text.Json first-use paths that `CatalogBuilder.Build` uses (`CatalogBuilder.cs:31`, `:149`), so the measured first construction is slightly optimistic. Move both after `clock.Stop()` (AA). [tests/Hexalith.McpCli.Core.Tests/CatalogPerformanceTests.cs:64]
- [x] [Review][Patch] R9 — low. The tools README says "Process startup and assembly loading are excluded". Only the manifest's top-level assemblies and the sample load before timing. Their dependencies, such as Core's `JsonSchema.Net`, load on demand inside the measured `Build`. Say so (BH, EC). [tools/conformance-vectors/v1/README.md:202]
- [x] [Review][Patch] R10 — low. `_response_body` fills a missing echoed field with `01J9MZHXT3RKM0VWXRXGSJDATN`. Several tests and `run_packaged_process_fixture.py:80` use the same literal as the scripted message ID, so a regression that substitutes the placeholder for a scripted value keeps those checks green. Use a distinct scripted message ID in those tests (BH). [tools/conformance-vectors/v1/run_loopback.py:419]
- [x] [Review][Patch] R11 — low. No test pins the arguments `production_replay` passes to `run_catalog`: the retained artifact and vector copies, the ConformanceHost `obj/project.assets.json`, and the receipt-derived `expected_modules`. `CombinedConsumptionHashTests` asserts the call is not made, and `ProductionProgressTests` raises from a mock. Dropping `expected_modules` passes every unit and process test. Fix: assert the call arguments with a mocked `run_catalog` (BH). [tools/conformance-vectors/v1/check_enrolled.py:126]
- [x] [Review][Patch] R12 — low. The root README replaced the ordered list of the seven Parties operations with a count, and it names no Tenants operation. A reader can no longer see what ships without running the CLI. List both modules' operations in the order `operations <module> --strict` prints them, checked against the built CLI (BH). [README.md:99]
- [x] [Review][Patch] R13 — low. The root README sentence "The repaired normal Tenants 5.10.1 five-package/container release has qualified separately from the enrolled Contracts 5.10.0 artifact" does not say why 5.10.0 stays enrolled. Fix: say that 5.10.1 is the separately qualified release that repairs the container source labels, and that enrollment stays on 5.10.0 because the approved vectors and inventory bind its signed Contracts archive (BH). [README.md:101]
- [x] [Review][Patch] R14 — low. The packaged process fixture copies the host's `Directory.Packages.props` and overwrites it on the next line. Drop it from the copy list (BH). [tools/conformance-vectors/v1/run_packaged_process_fixture.py:122]
- [x] [Review][Patch] R15 — low. Prose problems in the tools README (BH): [tools/conformance-vectors/v1/README.md:73]
  - `:73` says Story 4.11 "implements" the rechecks but still says "It must also verify".
  - `:163-164` start two consecutive sentences with "It also proves".
  - `:167-168` leave a double blank line before the new heading.
- [x] [Review][Patch] R16 — low. `enrolled.json` and `catalog-benchmark.json` each set `fullV1Accepted` from their own gate only. CI runs the replay step after a failed benchmark (`if: ${{ !cancelled() }}`), so one uploaded run can hold `fullV1Accepted: true` in `enrolled.json` next to a failed benchmark. The job is red, and Story 4.16 gates on the green SHA, so no consumer is misled today. Fix: state that each flag covers only its own gate, and that full-v1 acceptance needs both flags plus the green job (AA). [tools/conformance-vectors/v1/README.md:195]
- [x] [Review][Defer] R17 — `maybe-false`; medium if true. `FirstConstructionStaysWithinFiveHundredMilliseconds` is a plain `[Fact]` in the ordinary unit tier (`.github/workflows/ci.yml:25`), and `LimitViolation` applies without `MCPCLI_BENCHMARK_REQUIRE_V1`. On ubuntu-latest the child competes for CPU with Core.Tests' parallel classes, which could make the 500 ms limit flake (BH, EC). [tests/Hexalith.McpCli.Core.Tests/CatalogPerformanceTests.cs:15] — deferred: unverified. Settle it by recording the unit-tier child's `elapsedMilliseconds` across several ubuntu-latest `ci` runs. Two local 14-core parallel runs measured 146.3 and 124.9 ms; the dedicated Ubuntu step measured 194.5 and 242.6 ms.
- [x] [Review][Defer] R18 — low. The agent instructions say to use `tests/Hexalith.McpCli.ConformanceHost` to reproduce isolated-module or empty-catalog behavior. The host now defaults to `ConformanceProduction=true` and loads the production manifest, so an isolated run needs `-p:ConformanceProduction=false` (AA, EC). [AGENTS.md:119] — deferred: the fix edits agent-context files.

#### Rejected (code review pass 3)

- `low` — The benchmark child, cancellation and `check_enrolled` restore/build have no timeouts, so a hang could hold the runner or orphan a late writer (BH, EC ×2). Carried from this spec's BH9/EC4 and Story 4.10 pass 3: no hang was shown, the CI job limit bounds it, and timeout/kill machinery is more than a direct correction.
- `false` — `VectorGatewayCapture` serializes with different JSON options from the real gateway client (BH, EC). Core sets no enum- or converter-typed request member today. Preflight compares the capture with exact equality against the same `expectedGateway` body that replay compares the real wire request with, so a divergence fails loudly in one of them and never passes falsely.
- `false` — The validator's catch filter misses `KeyNotFoundException` and `UnauthorizedAccessException`; zero paths exit 0; one `try` per vector loses later locations; the 256 framing depth is not Core's (BH, EC ×2, AA). `run_catalog` runs schema validation first. It requires the members, bounds paging to int32, requires string-valued extensions and has already read every file. Every selection also has complete, nonempty coverage. These exceptions and the empty call are therefore unreachable. The reachable framing-depth `JsonException` carries its JSON path and line. `_response_depth` runs only after this 256-depth preflight, well inside Python's recursion limit.
- `low` — The private `Entries` reflection is duplicated and unchecked (BH). Test-only; a generator change fails loudly; a shared helper is a refactor. Carried from Story 4.10 pass 3.
- `low` — `run_catalog` validates each selection twice and `_sdk_response` is recomputed (BH). The cost is negligible for 21 vectors, and the first pass fails before any host process starts. The related claim that `operationCount` comes from receipts is `false`: complete-coverage validation forces each receipt's operations to equal the replayed ones.
- `false` — The READMEs hard-code a one-off 194.5002 ms, and the evidence lacks OS and SHA context (BH). The statements are past tense and bound to the linked audit, which records the run, source and runner. The uploaded artifact belongs to a run that carries its commit and runner.
- `low` — The rationale of the approved Tenants inventory says "require fresh owning-maintainer approval", yet the status is `approved` (BH). The wording is confirmed, but the status and reference fields are authoritative. The bytes are owner-approved and bound by `inventorySha256`, so rewording needs a new approval cycle.
- `low` — `RetainFailure` throws on truncated or non-JSON output (EC). Every write path writes complete JSON, so only a kill mid-write reaches it, and the fix adds guards.
- `low` — The benchmark accepts an empty or duplicate `requiredModules` (EC). This needs a bad configuration edit, and `required_scope` rejects it in the same CI job.
- `low` — Malformed adapter output raises `KeyError` (EC). Only a stale host reaches it. `production_replay` always rebuilds the host, and the standalone path still exits nonzero.
- `low` — Retained vectors could change between the hash check and consumption (EC). The same process owns the output directory, and passing bytes would be a redesign.
- `false` — The README promises partial observations, but malformed-Payload and describe documents are never written (EC). The README scopes those files to success documents and captured requests. Those failures put both documents into the `_fail` diagnostic, which is retained in `production-replay.stderr.txt` and `enrolled.json`.
- `false` — The result oracle takes the expected tenant from the session tenant rather than the fixed module tenant (AA). `validate.py:166` requires `expectedGateway.body.tenant` to equal the envelope tenant, so the two comparisons are identical for every valid vector.
- `false` — MCP runs `send_command` and `run_query` with `--strict` but the CLI does not (AA). `strict` only refuses a Catalog with diagnostics (`OperationExecutor.cs:51`), and strict discovery of the same host has already failed on any diagnostic before execution.

### Review pass 3 implementation and local verification — 2026-10-22

All sixteen patch rows R1–R16 are implemented and locally verified. The
[verification record](evidence/story-4-11/review-pass3/verification.md) links exact
commands, retained channels, final source hashes, named passing cases and eleven
detected guard-removal probes, including actual zero-exit benchmark child no-ops.
Frozen intent, approved vector and inventory bytes, required module scope and
production package pins are unchanged.

Fresh restore and the warnings-as-errors Release build passed. All six ordinary
test projects passed with 1,367 successes and five skips: four existing Windows
cases and the measurement Fact's intentional non-probe skip. All 148 named Python
cases, both complete Sample gates, isolated String coverage and documented offline
CLI invocations passed. Strict production replay passed both modules, all 21
operations, 78 preflight calls, 198 retained documents and 198 complete captured
requests. The strict first Catalog construction with exactly one Ulid sample
measured 140.873 ms, below 500 ms, and default benchmark output left no leaked file.

R17 and R18 remain already tracked in the deferred-work ledger; no new deferral
was added. The spec remains `in-progress` for the parent workflow's next sequential
independent review and completion record. These local results do not claim a new
normal Ubuntu CI run. No commit, push, merge, release or publication was performed
in this implementation step.

### Resumed build completion — 2026-10-22

All R1–R16 corrections and the bounded independent-review patches are complete.
The [final verification record](evidence/story-4-11/review-pass3-corrections/verification.md)
links the parent audit and all exact commands/channels. All six .NET projects
passed (1,367 tests; five expected skips), all 153 named Python cases and both
sample gates passed, and strict production replay verified both approved modules,
21 operations, 78 preflight calls, 198 documents and 198 captured requests. The
fresh first Catalog construction with exactly one Ulid sample measured 217.6124 ms.
All 361 tracked source inputs stayed unchanged throughout the final 21 checks.

Three context-free review layers completed; nine additional filed claims were
patched, one carried limitation remains already tracked and two low claims keep
their logged rejection. The original R17/R18 deferrals remain unchanged. Approved
vectors, inventory, receipts, package pins and frozen intent are unchanged. The
spec is done and the sprint entry is review. These are complete local results;
no new Ubuntu CI result, push, root merge or publication is claimed.

### Review Findings (code review pass 4, 2026-10-22)

Code review 2026-10-22 of the complete committed story range `fce41d0..4b3e7ff` (`7f4a08c`, `f20a4e0`, `bf9c49a`, `c887634`, `2a2d88b`, `e924551` and their merges).

- **Code-only scope:** excludes `_bmad-output/` and every `references/` gitlink move; includes the fourteen approved Tenants vectors and `tenants-approved.json`.
- **Size and mode:** 39 files, +6,836/−79, 7,622 diff lines, full mode, with `epic-4-context.md` as context.
- **Layers:** Blind Hunter (BH), Edge Case Hunter (EC), Verification Gap (VG) and Acceptance Auditor (AA). No layer failed.
- **Result:** 54 normalized findings (BH 25, EC 16, VG 4, AA 9). 14 survive as 9 patch and 2 already-tracked defer entries; 40 are rejected. No decision is needed.

Parent checks during triage:
- Fresh `dotnet restore Hexalith.McpCli.slnx` and the warnings-as-errors Release build passed (0 warnings).
- `gh run view 39787913115`: the `main` push run on `4b3e7ff` succeeded in all four required jobs, `enrolled-module-conformance` included.
- `QueryExecutionTests.cs:63` covers the fixed tenant winning over session state. `VectorError` subclasses `ValueError` (`validate.py:31`), so `check_enrolled.main` catches replay failures.
- `run_packaged_process_fixture.py:274-286` replays the real production packages plus the sample inside the `conformance-vector-loopback` job, as the spec's combined-manifest task requires.

- [x] [Review][Patch] P1 — medium. No test covers the runtime-DLL selection guard. `_verify_artifact_in_host` rejects a host whose `deps.json` selects no runtime `.dll` for the package, or one the assets file lacks. Without that guard, the byte comparison at `:723-728` loops over nothing and passes, so the approved-bytes binding silently checks nothing. VG replaced the guard with `if False:` and all 45 `test_loopback` tests passed; AA reproduced it. Fix: in `test_host_signed_archive_matches_restore_content_hash_independently` (`test_loopback.py:146`), add subtests that empty the `deps.json` runtime map, rename `runtimeTarget` and list a DLL the assets lack. Each must raise `selected package runtime DLL assets differ` (VG, AA). [tools/conformance-vectors/v1/run_loopback.py:721]
- [x] [Review][Patch] P2 — low. No test asserts `fullV1Accepted: true` on a passing strict run. Every assertion on the flag in `test_enrolled.py` is `assertFalse` (`:403`, `:535`, `:547`, `:557`, `:847`), and the process fixture checks only `result`. VG hard-coded the flag to `False` and all 48 tests still passed. Fix: on the strict success path of `EnrolledPreflightTests.invoke`, assert `report['fullV1Accepted'] is True` and `report['missingRequiredModules'] == []` (VG). [tools/conformance-vectors/v1/check_enrolled.py:198]
- [x] [Review][Patch] P3 — low. No test protects keeping a measured failure. The child writes its measured `failed` evidence and then throws (`:97`); the early return in `RetainFailure` keeps that document. `FailureEvidenceWrapperInvalidatesPriorSuccessAndRetainsTheException` reaches `RetainFailure` only with `pending`. Without the return, an over-budget or missing-Tenants run uploads `elapsedMilliseconds: null` and keeps the population only inside exception text. Fix: add a `[Fact]` whose `measure` writes a measured `failed` document and then throws, and assert that its fields survive `RunWithFailureEvidence` (VG). [tests/Hexalith.McpCli.Core.Tests/CatalogPerformanceTests.cs:233]
- [x] [Review][Patch] P4 — low. No test protects the `--strict` flags this story added. They are on `modules`, `operations` and `describe` (`:772`, `:778`, `:812`) and on the MCP host command (`:281`). AA removed each in a scratch copy, and every Python test stayed green. The manifest-to-Catalog comparison, the benchmark's diagnostics check and `EnrolledModuleCoverageTests` backstop it. Fix: assert the `--strict` arguments on the mocked `head.cli` calls in `ProductionReplayOrderingTests`, and on the command `HeadProcess.mcp` builds (AA). [tools/conformance-vectors/v1/run_loopback.py:772]
- [x] [Review][Patch] P5 — low. No test protects the exact malformed-Payload document check. Replacing it with `if False:` leaves every Python test green. Cross-head parity and the `validation_failed` code check stay, so if both heads changed the path or message, nothing would fail. Fix: have mocked heads return an identical `validation_failed` document with a different message, and assert `required malformed-Payload error document differs` (AA). [tools/conformance-vectors/v1/run_loopback.py:863]
- [x] [Review][Patch] P6 — low. No test protects the empty-manifest refusal. Without it, `--local` on a manifest with no flagged packages exits 0 with `result: local-only`. Fix: call `EnrolledPreflightTests.invoke` with non-flag metadata so `packages` is empty, and assert exit 1, `result: failed` and the `Production manifest has no enrolled Contracts packages.` error (AA). [tools/conformance-vectors/v1/check_enrolled.py:188]
- [x] [Review][Patch] P7 — low. "complete production Catalog contains uncovered operations" does not say which operations are uncovered. Every owned operation is already proven to be in the Catalog, so the uncovered set is `sorted(set(catalog) - set(owned))`. Add it to the message; the regex at `test_loopback.py:371` still matches (BH). [tools/conformance-vectors/v1/run_loopback.py:804]
- [x] [Review][Patch] P8 — low. The benchmark evidence mixes property casing. `new { module.Name, … }` writes `"Name"` next to camelCase `identifierKind`, and `diagnostics = catalog.Diagnostics` is written in PascalCase, because the options set no naming policy. No code reads these fields. Fix: serialize with `JsonSerializerDefaults.Web` plus `WriteIndented` (BH). [tests/Hexalith.McpCli.Core.Tests/CatalogPerformanceTests.cs:90]
- [x] [Review][Patch] P9 — low. The 500 ms limit appears three times: in the evidence field (`:86`), the parent completion check (`:188`) and `LimitViolation` (`:205`). If the budget changed in one place only, the parent's check would disagree with the child's verdict. Use one `const double` (BH). [tests/Hexalith.McpCli.Core.Tests/CatalogPerformanceTests.cs:188]
- [x] [Review][Defer] D1 — `maybe-false`; medium if true. The 500 ms limit also runs in the parallel unit tier and could flake under CI load (BH, EC, VG other finding). [tests/Hexalith.McpCli.Core.Tests/CatalogPerformanceTests.cs:16] — deferred: already tracked (`deferred-work.md:575`).
- [x] [Review][Defer] D2 — low. The agent instructions omit the enrolled gate and the `ConformanceProduction` switch (BH). [AGENTS.md:83] — deferred: already tracked (`deferred-work.md:561`, `deferred-work.md:578`). The benchmark-command part is `false`: ordinary Core.Tests runs, which the instructions already prescribe, include the benchmark.

#### Rejected (code review pass 4)

Carried from earlier logged rulings, with the same location and bad outcome:
- `low` — No timeout or kill for the benchmark child or the `check_enrolled` restore/build (BH ×2, EC ×2). Carried from BH9/EC4 and pass 3.
- `low` — `RetainFailure` throws on truncated or non-JSON output (BH, EC). Carried from pass 3 and REC2.
- `false` — The validator's catch filter misses `KeyNotFoundException`; each file has one `try`; non-`command` kinds count as queries (BH, EC). Carried from pass 3: `run_catalog` runs schema validation first, and the schema requires these members and restricts `kind`.
- `low` — The benchmark accepts an empty `requiredModules` (EC). Carried from pass 3: `required_scope` rejects it in the same CI job.
- `false` — The evidence lacks a SHA and runner OS; the READMEs hard-code 194.5002 ms (BH). Carried from pass 3: the run carries its commit and runner, and the past-tense figure is bound to its linked audit.
- `low` — The approved Tenants inventory says "require fresh owning-maintainer approval" (BH). Carried from pass 3: the wording cannot change without re-approval.
- `false` — The README promises partial observations that are never written (EC). Carried from pass 3.

New rulings:
- `false` — The parent should require the child's PID (BH). `InvalidateOutput` writes `pending` to a fresh or configured path before the child starts, and only the child can write `passed`.
- `false` — The parent does not check `fullV1Accepted`, diagnostics or missing modules (BH). `ConstructionOutcome` (`:196-201`) makes `result: passed` imply all three, and strict mode requires `passed`.
- `false` — `RetainFailure` overwrites a measurement after a mode mismatch (BH). The child inherits the parent's `MCPCLI_BENCHMARK_REQUIRE_V1`, so no mismatch is reachable. A measured failure exits nonzero and keeps its `failed` document.
- `low` — The benchmark lists package IDs without versions (BH). The run's commit fixes the central pins, and `enrolled.json` records the restored versions.
- `false` — Replay never proves the fixed-tenant rule (BH). Core covers it (`QueryExecutionTests.cs:63`), and the spec limits replay to transport parity.
- `false` — No test covers preflight on bad envelope arguments (BH). Envelope failures take the same `outcome.Error` branch (`VectorCompatibilityValidator.cs:52-56`) that the fixture's payload mutations protect, and the vector schema runs first.
- `false` — Nothing ties the Python SDK model to the SDK version (BH). The model is independent of both heads, so any divergence fails replay loudly. The real-SDK `sdk_response_cases` run against the pinned SDK in `conformance-vector-loopback`.
- `low` — The sample loopback job depends on production enrollment (BH). The spec's process task requires the combined case. The coupling only duplicates a red signal, and decoupling needs a new fixture package.
- `false` — The Tenants receipt adds an unchecked `status` field (BH). No gate or reader consumes it; the hashes and `approvalReference` bind the approval.
- `false` — "Either required module" assumes two modules; the evidence path names Story 4.11 (BH). `v1-scope.json` declares exactly those two, and the path is only an example.
- `false` — The READMEs cite a benchmark from before the pass 3 corrections (AA). The sentence is past tense, bound to the linked c887634 audit, and HEAD's green run passes the same gate.
- `low` — The CI validation step still runs after a failed build (BH). The build step stays the first failed step, and a correct guard needs step IDs and conditions.
- `false` — The retained artifact is never re-hashed before production replay (BH). `_verify_artifact_in_host` hashes it against the host restore (`run_loopback.py:711-713`) and compares its DLL entries (`:723-728`).
- `low` — Variants such as `TRUE` or `1` for `MCPCLI_BENCHMARK_REQUIRE_V1` fall back to local mode (EC). CI sets `'true'`, the resulting evidence says `local-only`, and a fix would add a guard.
- `low` — An empty `MCPCLI_BENCHMARK_OUTPUT` throws before evidence is written (EC). The test fails loudly, there is no path to write to, and a fix would add a branch.
- `false` — `TypeError`/`AttributeError` leave `enrolled.json` at `pending` (EC). No reachable trigger was shown. Production progress still records `failed`, and the process exits nonzero.
- `low` — A command scripted with 304 and a body diverges, because .NET discards 304 content (EC). No vector scripts a command 304, the divergence fails closed, and a fix would add a branch.
- `low` — Python `strip()` and .NET whitespace differ for U+001C–U+001F (EC). Unlikely, fails closed, and a fix would add a helper.
- `low` — Python 3.10's `fromisoformat` grammar (EC). CI uses ubuntu-latest Python 3, the failure is loud, and a fix would add a version guard.
- `false` — A head omitting `correlationId` raises `KeyError` (EC). Core always sets correlation, and the failure is loud.
- `low` — A failed coverage test skips the benchmark step (EC, AA). The run is already red with the cause, and running the benchmark after a failed build needs separate step conditions.
- `false` — The README implies that local benchmark mode only records (EC). Neither README says the limit is skipped.
- `low` — Three more guards have no removal tests: the retained-vector map (`check_enrolled.py:117`), duplicate adapter steps (`run_loopback.py:675`) and duplicate Catalog operations (`run_loopback.py:782`) (AA). Each guarded state needs a bug in already-tested code, a later check backstops each one, and mocking those states adds test machinery.

### Review pass 4 implementation and local verification — 2026-10-22

All nine accepted patch rows P1–P9 are implemented and locally verified. The
[verification record](evidence/story-4-11/review-pass4/verification.md) links exact
commands and channels, source/evidence hashes, named frozen-matrix coverage and
ten detected guard/diagnostic removal probes. Frozen intent, both original owner
approvals, approved vector and inventory bytes, required scope and package pins
remain unchanged.

Fresh restore and warnings-as-errors Release builds passed. All six ordinary
projects passed with 1,368 successes and five expected skips; all 157 named Python
cases, both complete Sample gates and ten named Core matrix cases passed. Strict
production replay passed both modules, 21 operations, 78 preflight calls, 198
documents and 198 complete captured requests. First Catalog construction with
exactly one Ulid sample measured 193.1315 ms against the 500 ms limit; benchmark
module fields use camelCase. All 3,740 tracked source inputs remained identical
before and after the gates, and no default benchmark file leaked.

D1/D2 remain already tracked, with no new ledger entry. The spec remains
`in-progress` for the parent workflow's independent review and completion. These
are local results; no new Ubuntu CI result, commit, push, merge, release or
publication is claimed.

### Final pass 4 completion — 2026-10-22

All P1–P9 corrections and the three bounded independent-review patches are
complete. The [final corrected-source verification](evidence/story-4-11/review-pass4-corrections/verification.md)
and [parent acceptance audit](evidence/story-4-11/review-pass4-corrections/parent-acceptance-audit.json)
bind all 17 sequential successful checks, 1,368 .NET successes with five expected
skips, 157 named Python cases, both complete Sample gates, both approved
production Modules and all seven frozen matrix rows. Strict replay verified
21 operations, 78 preflight calls, 198 documents and 198 complete requests.
The fresh first Catalog construction with exactly one Ulid sample measured
157.3627 ms. All 3,740 source inputs stayed unchanged during final verification.

All thirteen independent-review claims have individual verdicts above: three
patches, two deferrals and eight rejections. Both deferrals describe inherited
behavior; decimal precision was already tracked, while incomplete root receipt
progress on a later package failure is newly recorded. D1/D2 retain their
existing dispositions. Approved vectors/inventories, owner approvals, frozen
intent, package pins and reference contents are unchanged.

- [x] [Review][Defer] PBH5 — decimal comparison precision: already tracked (`deferred-work.md:138`).
- [x] [Review][Defer] PBH9 — inherited root-receipt progress omission: recorded under this spec's resumed pass 4 review heading in `deferred-work.md`.

The spec is done and the sprint entry is review. These are complete local
results; no new normal Ubuntu CI result, push, merge or publication is claimed.
The required local workflow completion commit records this corrected source
and evidence. Live authorization, privacy, persisted effects and retirement
retain their later gates.
