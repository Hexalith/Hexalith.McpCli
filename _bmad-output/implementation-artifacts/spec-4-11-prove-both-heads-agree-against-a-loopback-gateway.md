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
