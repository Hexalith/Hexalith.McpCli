---
title: '4.10 Add Parties queries and pin complete coverage'
type: 'feature'
created: '2026-10-20'
status: 'in-progress'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: '9354dc08176744c75c2ddb61d924c0948b373b98'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/parties-migration-inventory-v1.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The approved Parties reads lack public decorated Contracts. Existing
read behavior needs privacy and paging corrections before complete coverage can
be pinned in McpCli.

**Approach:** Deliver the three Queries upstream, verify the complete seven-operation
artifact and vectors, then enroll its published version behind generic coverage
and dependency gates. Scratch evidence alone does not complete this story.

## Boundaries & Constraints

**Always:** Follow inventory A1/T01–T07: String identifiers, envelope tenant,
domain `party`; GetParty routes `PartyDetail`/`party-detail` with root `PartyId`;
list/search route `PartyIndex`/`PartySearch`, `party-index`, aggregate `parties`.
Retain declared actor compatibility names while verifying actual SDK handler
dispatch. Describe all exposed members and provide schema-valid examples.

List exposes Type/Active and four inclusive created/modified bounds; search
exposes Query/Type/Active and display-name semantics. Reject unsupported search
filters/modes instead of ignoring them. Validate dates/ranges and reject duplicate
case aliases. Preserve legacy payload page handling when envelope paging is absent.
When present, envelope paging alone governs: default size 20/start 0, maximum
100, existing page-aligned offsets and scoped cursors; return effective metadata.
New Query DTOs contain no payload paging members. Erased details are suppressed
like missing details; erased entries never affect returned rows or totals.

Bind all seven vectors to the exact artifact; preserve Story 4.9 wording fixes
and historical approvals. Obtain fresh maintainer approval for the complete
artifact/vectors and release inventory. Review descriptions from the Catalog
without source context. Use the owning protected release workflow after the
candidate is reviewable; published bytes must pass validation again before enrollment.

**Never:** Edit `references/` contents, bypass release gates, invent approvals,
add module-specific McpCli code, expand the seven-operation scope, retire the
legacy host, convert IDs, or claim live authorization/effects from replay.
Existing C06–C08 and Stories 4.11/4.13 remain downstream gates.

## I/O & Edge-Case Matrix

| Scenario | Input/state | Expected behavior |
| --- | --- | --- |
| Detail | Existing / missing / erased ID | Visible detail / same safe missing result |
| Identity | EntityId absent / matching / mismatching | Aggregate fallback / success / reject before read |
| Filters | Mixed types, statuses, dates and erased rows | Filter before paging; accurate totals; invalid inputs rejected |
| Paging | Size 2, continuation, conflicting payload page | Correct pages and metadata; envelope wins; invalid cursor/offset rejected |
| Compatibility | Legacy page payload without envelope | Existing page/default behavior retained |
| Coverage | Missing/extra/wrong type or absent approval | Blocking generic gate failure |

</frozen-after-approval>

## Code Map

`P:` means `/home/administrator/projects/hexalith/parties`; other paths are McpCli-relative.

- `P:src/Hexalith.Parties.Contracts/Module.cs`, `Queries/`,
  `P:src/Hexalith.Parties.Client/HttpPartiesQueryClient.cs`: marker and existing routes.
- `P:src/Hexalith.Parties/Queries/{PartySdkQueryService,PartyIndexProjectionQueryActor}.cs`:
  SDK execution, parsing, cursor scopes and payload-paging leakage.
- `P:src/Hexalith.Parties/Search/{PartySearchResultsBuilder,LocalFuzzyPartySearchProvider}.cs`:
  existing filtering, display-name matching and totals; reuse these semantics.
- `tests/Hexalith.McpCli.Core.Tests/InventoryCoverageGate.cs`: existing exact
  public-name/internal-type comparison; currently wired only to a sample.
- `tools/conformance-vectors/v1/`: shared validator/replay;
  `evidence/story-4-9/review-pass-2/` beside this spec: reusable scratch verification.

## Tasks & Acceptance

**Execution:**
- [x] `P:src/Hexalith.Parties.Contracts/Queries/{GetParty,ListParties,SearchParties}.cs`
  — add exactly three declarations with explicit routing and descriptions.
- [x] `P:src/Hexalith.Parties/Queries/` — implement the matrix, retaining SDK
  dispatch and existing privacy/cache safeguards; keep one type per file.
- [x] `P:tests/Hexalith.Parties.Contracts.Tests/McpCliDecorationTests.cs`,
  `Package/`, `P:tests/Hexalith.Parties.Tests/Gateway/PartySdkQueryHandlerTests.cs`
  — pin seven declarations, package API and every matrix behavior; retain client tests.
- [x] `P:tests/conformance-vectors/mcpcli-v1/*.json`, `P:README.md`,
  `P:docs/api-contracts.md` — three read vectors, four rebound write vectors,
  prerequisites, semantic assertions and documented paging/filter behavior.
- [x] `tools/inventory-coverage/v1/`, `tests/Hexalith.McpCli.Core.Tests/` —
  transcribe approved release scope and enforce coverage for every enrolled
  module generically, including missing-inventory regression tests.
- [x] `.github/workflows/ci.yml`, `tools/conformance-vectors/v1/` — automate
  complete Catalog, lint, inventory and vector checks against exact artifacts.
- [x] `evidence/story-4-10/` beside this spec — retain artifact/source hashes,
  actual routing evidence, independent description review and fresh approvals.
- [x] Owning Parties release workflow; owning Builds
  `/home/administrator/projects/hexalith/builds/Props/Directory.Packages.props`
  — deliver verified publication and its central pin through normal owner gates.
- [x] `src/Hexalith.McpCli/Hexalith.McpCli.csproj`, `tools/dependency-policy.json`,
  root Builds gitlink, `README.md` — enroll the published Contracts version,
  reconcile restored closure and document/test shipped discovery behavior.

**Acceptance Criteria:**
- Given complete Contracts, when Catalog/strict discovery/lint run, then exactly
  seven approved operations have valid examples and reviewed descriptions.
- Given seven artifact-bound vectors, when shared validation and replay run,
  then all pass with original Query postconditions retained.
- Given approved scope and enrollment, when CI runs, then missing inventories,
  coverage mismatches and forbidden dependencies fail independently.
- Given the published package, when fresh restore and built discovery run,
  then its exact version/hash is verified and all seven Parties operations appear.

## Implementation Notes

Current state: implementation, protected Parties 1.5.1 publication, owning Builds
integration and production enrollment are verified. Final independent workflow
review and all required verification have passed, with no deferred findings.
The dated sections below retain the historical decisions
and intermediate states; [current verification](evidence/story-4-10/release-readiness/approved-dependency-continuation/verification.md)
records the complete release/enrollment and review result.

Approved for implementation by the requesting user on 2026-10-20.
The implementation step requires sequential execution, no pushes and no remote
operations. Prepare and verify the complete local candidate first; return its
exact artifact and remaining release prerequisites for review before crossing
the protected publication boundary. Keep release/enrollment tasks open until
their published-artifact acceptance criteria actually pass.

### Exact candidate approval and release continuation (2026-10-20)

The requesting user replied **"I approve."** directly to the request for approval
of the exact final candidate, seven vectors and release inventory linked through
`pending-approval.json`. [Candidate approval](evidence/story-4-10/candidate-approval.json)
records that decision, its exact artifact and input hashes, and its limits without
inventing a separate external signatory. The original pending receipt and inventory
remain historical inputs. `tools/inventory-coverage/v1/parties-approved.json`
transcribes the approved release decisions and references that actual session
evidence. Scope approval does not establish live authorization or retirement proof.

This approval resumes the protected release/enrollment phase described in the
frozen intent, after the implementation phase's local-only handoff. Publication
still requires green owning CI at the exact source, the protected production
workflow, and verification of the published bytes; no gate may be bypassed.

An external process advanced Parties beyond the earlier verification baseline
and committed the query work. The recorded artifact, vectors and all verifier
inputs still matched at approval recording. Only Parties README bytes differed
among the approved source inputs; that later workspace drift is recorded in the
approval receipt. Preserve those external changes. Before publication, reassess
the current source and previously failing fitness checks, keeping the pinned
module tool as the sole source-selection authority and retaining meaningful
package/source graph checks. Do not restore obsolete repository autodetection
or remove dependency checks to make CI pass.

### Release prerequisite follow-up plan

The owning main checkout is being changed by another process. Perform the
fitness/receipt correction in the isolated Parties worktree
`/tmp/hexalith-parties-story410-release`, initially fixed at
`e55da59006f55410b9390403c67253b4f8423e18`. Its root-declared dependencies are
local clones checked out at that commit's exact gitlinks; no nested dependencies
are initialized. Do not edit the live owning checkout or any reference contents.
Keep this correction separate from the approved artifact; Contracts and vectors
must remain byte-identical to the approved candidate inputs.

- [x] In the isolated worktree, correct
  `tests/Hexalith.Parties.Tests/FitnessTests/PlatformApiPrerequisitesTests.cs`
  and `_bmad-output/implementation-artifacts/story-8-3-platform-api-prerequisite-matrix.md`
  to reflect the already-adopted pinned-tool source mapping and current committed
  source selection. Preserve historical parity/approval receipts. The current
  Tenants gitlink is `9a94131a26d0c5d80d5540706e267ee123d54b68`, described as
  `v5.9.0-24-g9a94131a`; verify all present-tense rows against the fixed worktree.
- [x] Keep meaningful evaluated consumer graph checks. Ordinary Release builds
  use packages, including Commons HTTP. Source-mode consumer checks must receive
  explicit root/FromSource inputs representing the pinned tool's mapping;
  `UseHexalithProjectReferences=true` alone no longer selects roots. Retain the
  upstream negative sibling-layout test and add coverage proving explicitly
  mapped McpCli roots select only Abstractions in both supported layouts.
  Never restore obsolete autodetection or add a test-only production dependency.
- [x] Run only focused fitness verification in the implementation handoff;
  parent verification then runs the full affected domain project. Record exact
  commands/results under `evidence/story-4-10/release-readiness/` in McpCli.
  The implementation handoff must not commit, push or dispatch a release.
- [x] The exact remote owner CI run for `35d891d2` also failed
  `tests/Hexalith.Parties.Sample.Tests/SampleOnboardingGuardrailTests.cs`:
  `GettingStartedRunnableSnippets_UseAcceptedGatewayShape` still expects the
  pre-adoption submodule command and warning wording. Update that existing guard
  to protect the already-adopted pinned module-tool start/stop commands, declared
  direct reference initialization and prohibition of nested/recursive updates.
  Retain its command/query, privacy and retained legacy-host checks. Avoid a
  fragile requirement that harmless reference-list ordering or warning prose
  remain identical. No documentation or runtime behavior needs changing for
  this stale test. Run the focused sample guardrail class; parent later runs
  the full Sample.Tests project. The two Client failures in that older CI run
  are already corrected by the approved query commit; do not duplicate that fix.

The first isolated full domain/Sample runs pass 2,074/58 with zero skips. During
that correction, external work advanced main to
`ea926163fb51033b226541f069ebf6a5941922af`, including root dependency pointer
changes and unrelated health work. The parent carried the same three-file
correction onto that committed source, refreshed only current identities and
describe values, and retained the original isolated evidence. The current
worktree now uses that newer source and its exact root gitlinks; historical
matrix bytes remain unchanged. Approved Contracts and vectors did not change.

The release-readiness review requires direct test/helper corrections below.
The existing test-only `EvaluatedProjectGraph` carrier may retain effective
package versions; no production surface or dependency is added. Keep source
evaluation accurately described as consumer property fixtures rather than a
qualification of the tool's generated imports, mapping hash or validation targets.

Focused implementation handoff: [release-readiness evidence](evidence/story-4-10/release-readiness/verification.md)
records 37/37 fitness and 7/7 onboarding guardrails passing after focused Release
restores/builds. Exactly three isolated files changed; Contracts/vectors,
historical matrix receipts and reference contents remain unchanged. Parent full
verification and all protected publication/enrollment gates remain open.

## Spec Change Log

## Review Triage Log

### Published enrollment review (2026-10-21)

All three independent layers completed before classification. They reviewed
`/tmp/story410-final-implementation-amo4kk4x.diff`; only the edge layer received
this spec. Each finding below was assessed before grouping. Earlier triage rows
do not describe these remaining states: the earlier diagnostic patch prints
captured output, and the earlier stale-success patch covers `verify`, whereas
the new findings concern durable CI uploads and enrollment preflight.

| Finding | Verdict and evidence | Route |
| --- | --- | --- |
| FB1: approved inventory digest is not enforced | Medium. `check_enrolled` supplies the current inventory without comparing its bytes to the approved digest; the verifier records whichever bytes it receives. A structurally valid edited scope could reuse the artifact approval. Bind the existing exact approved inventory digest in the generic enrollment receipt and enforce it before verification. | Patch |
| FB2: artifact/vector paths are reread after hashing | Medium. `verify` hashes the original paths before restore/build, then rereads them for restore, validation and replay. Editing a vector during those long subprocesses can make the replay differ from the recorded hash. Capture immutable local inputs once and use them for every later read, retaining the original source names in evidence and preserving enrollment's approved vector binding. | Patch, grouped with FE2 |
| FB3: signed dependency archive sidecar is optional | Medium. A local reproduction supplied matching assets/metadata content hashes with changed archive bytes and no sidecar; `resolved_packages` returned success with different archive and content hashes. Require the independent archive binding when those hashes differ. | Patch, grouped with FE1 |
| FB4: enrollment preflight leaves successful child receipts | Medium. `main` resets only `enrolled.json`; artifact/receipt/vector rejection happens before `verify` invalidates the existing package result. The old child `verification.json` and `artifact.sha512` remain successful. Invalidate prior child success before preflight. | Patch |
| FB5: malformed receipt root leaves a pending result | Medium. `_load_json` can return an array, then `artifact_for` calls `.get`; the uncaught `AttributeError` bypasses the failed enrollment receipt. Validate the receipt's object root and report deterministic failure. | Patch |
| FB6: case variants of a package ID are rejected | Low. A local reproduction with `Module.Contracts` and `module.contracts` rejects the same NuGet identity; directory selection also uses case-sensitive spelling. Correct both identity comparison and existing approval-directory lookup. | Direct correction |
| FB7: operation-level lint cannot receive an acceptance | Low. Both implementations intentionally require a nonempty property, so a root finding cannot match an exception. Existing acceptances are only the eight approved member findings; no current approval is blocked. State that operation-level findings require correcting Contracts, rather than adding a new acceptance representation. | Direct documentation patch |
| FB8: complete CI evidence is discarded with the runner | Medium. The enrolled job retains full diagnostics and receipts only in `RUNNER_TEMP`; the existing failure path prints at most the final 16,000 characters and there is no upload. Preserve the evidence directory with an always-running, pinned artifact step. | Patch |
| FB9: automate a shipped CLI/MCP composition smoke | Low. Current shipped entry points were executed successfully for modules, all seven operations/descriptions and stdio MCP parity in `production-discovery/checks.json`; the production manifest is also checked automatically, while existing process tests cover CLI/MCP composition with fixture manifests. Adding another process orchestration path would protect a hypothetical future composition regression, not a demonstrated current failure. | Reject low, nontrivial extra orchestration |
| FB10: add cursor continuation to approved vectors | Low. These scripts deliberately cover exact routing, results and nondefault paging; their single-page shape does not test domain cursor execution. Actual continuation, effective metadata and scope rejection are exercised by the unfiltered upstream domain tests recorded in `matrix-test-audit-current.json`. Expanding the already approved scripts adds another scripted response and requires changing approved inputs without establishing a missing current runtime behavior. | Reject low, nontrivial change to approved vectors |
| FE1: missing sidecar permits changed signed dependency | Medium. Independently reproduced as FB3: matching metadata/assets plus a missing archive sidecar accepts changed archive bytes. | Patch, grouped with FB3 |
| FE2: vector edits after hashing change the replay input | Medium. Validation and replay use the original vector paths after restore/build, confirming FB2's receipt/input race. | Patch, grouped with FB2 |
| FV1: rejected inventory is not protected at the process boundary | Medium. Pre-verified gap: direct checker tests reject pending approval, but both automated process cases use a valid inventory. Replacing the adapter's conditional exit with zero leaves those cases green and could produce successful artifact evidence despite inventory findings. Add a real pending-inventory negative case using valid vectors; assert the inventory diagnostic/check failure and absence of a successful artifact hash. | Patch |
| FP1: snapshot map could hide a duplicate vector path | Medium. Parent inspection of the review patch found that a dictionary keyed by resolved path collapses repeated inputs before the existing duplicate-vector validation. Reject duplicate captured paths before restore and retain a regression that fails if that rejection is removed. | Patch |
| FP2: ambiguity test assumes a case-sensitive filesystem | Low. Creating both `Module.Contracts` and `module.contracts` raises `FileExistsError` on a case-insensitive filesystem before testing the guard. Use a synthetic directory listing for this case so it remains deterministic without an OS skip. | Direct test correction |

The patch routes change generic verification and CI evidence handling only.
Approved Contracts, vector bytes, release inventory and upstream publication
remain unchanged. All 13 patch findings, including the two parent corrections,
are resolved; the two low findings retain their dispositions above. No finding
is deferred. [Final review evidence](evidence/story-4-10/release-readiness/approved-dependency-continuation/final-review/review.json)
retains the reviewed diff identity, exact protected-input hashes and all ten
detected guard-removal mutations. Independent parent verification passes both
sample gates, Release restore/build with zero warnings/errors, all six McpCli
projects (1,339 passed, zero failed, four existing Windows-only skips), and all
100 Python regressions. Fresh production verification again passes all seven
vectors, clean inventory/lint and strict discovery without dependency overrides;
all seven description documents match the independently reviewed artifact.
[Exact commands and results](evidence/story-4-10/release-readiness/approved-dependency-continuation/final-review/checks.json)
and [final integrity audit](evidence/story-4-10/release-readiness/approved-dependency-continuation/final-review/integrity.json)
retain those observations. The unchanged upstream tests and source-equivalence
proof continue to cover every frozen matrix row. New CI evidence upload syntax
and its pinned action were checked locally; this working tree has not been
submitted as a McpCli CI run.

### Local candidate review, pass 1 (2026-10-20)

All three context-free code layers completed before triage. Their review used
`/tmp/story410-review-uxaw8oki/review.diff`; the spec was supplied only to the
edge-case layer. The original complete diff is retained beside that review file.
First-candidate bytes and evidence are preserved in `evidence/story-4-10/review-pass-1/`.

| Finding | Verdict and evidence | Route |
| --- | --- | --- |
| BH1: invalid Unicode escapes throw | Medium. Reading property names or writing values during normalization can throw InvalidOperationException; both parsers omit it from their catch filters. Reproduced by two independent reviewers against the built assembly. | Patch, grouped with EC1 |
| BH2: Type schema includes Unknown | Low. This is the existing PartyType enum's serializer-derived representation; both new descriptions explicitly say Unknown rejects. Narrowing it requires another public enum/converter or a generic declaration change. The documented domain restriction makes the proposed extra surface disproportionate. | Reject low, nontrivial fix |
| BH3: Query schemas include root null | Low. AD-7 deliberately preserves serializer-derived Query roots; null reaches the handler and receives the existing safe invalid-envelope result. Tightening it requires changing that generic convention or the public contract shape. No successful null read or data disclosure occurs. | Reject low, nontrivial fix |
| BH4: malformed Python lint roots pass | Medium. check_lint([], {}) and check_lint([], "") iterate zero elements and pass; the C# checker rejects non-arrays. | Patch |
| BH5: date fixtures do not discriminate | Medium. Existing SDK coverage distinguishes CreatedAfter, but the new paged mixed-row fixture cannot detect loss of the other forwarded date bounds. Add one independently excluded row per bound. | Patch |
| BH6: nonempty enrollment orchestration untested | Medium. Helper tests do not invoke main or verify; the empty production manifest cannot exercise that composition. | Patch, grouped with VG1 |
| BH7: CI drops captured failure diagnostics | Medium. Subprocess output is captured under RUNNER_TEMP and the failure reports only that path; no upload or diagnostic printing preserves it. | Patch |
| BH8: stale success survives failed verification | Medium. The initial hash refusal occurs before replacing an old passed receipt and artifact hash. The process fails correctly, but a reviewer can read stale successful evidence. | Patch |
| BH9: approval inputs lack receipt digests | Medium. Vectors are hashed; inventory and accepted-lint inputs are represented only by a path or not represented. The receipt cannot identify their verified bytes. | Patch |
| BH10: resolved graph disappears | Medium. Nuspec ranges and overrides do not identify the actual restored closure. Retain resolved package identities and hashes before deleting scratch assets. | Patch |
| EC1: malformed Unicode escapes parser boundary | Medium. Same demonstrated InvalidOperationException as BH1, before the safe query error boundary. | Patch, grouped with BH1 |
| VG1: replay removal leaves CI green | Medium. Pre-verified gap: no automated caller reaches verify() through replay while production enrollment is empty. A packaged-sample process check must reject a deliberately failing result assertion. | Patch, grouped with BH6 |
| DR1: continuation guidance incomplete | Low. Built list/search descriptions do not name paging.nextCursor, unchanged cursor scope, or the cursor/offset exclusion. The runtime rules already exist. | Direct wording patch |
| DR2: replacement defaults implicit | Low. Existing update descriptions say complete replacement but omit null/default behavior of optional nested members. The aggregate consumes the supplied replacement object. | Direct wording patch |
| P1: read vectors omit identity assertions | Low. List/search scripts return the expected party but assertions check counts, erasure and paging without pinning its ID, type or active status. Add direct semantic assertions. | Direct vector patch |
| P2: signed archive and restore hashes differ | Medium. The real process fixture exposed that signed NuGet archives can have a different raw hash from the assets content hash. Verify the restore metadata against assets and the archive against its cache sidecar; retain both meanings and continue matching approved raw bytes exactly. | Direct verifier patch |

The two rejected schema findings preserve AD-7 and the approved public DTOs.
No new human intent gap or frozen-boundary change is required. Publication and
fresh approval remain open; this review does not certify the release inventory.

All patch routes above are implemented and verified. The malformed Unicode cases
now assert the full safe result and rejection before a store read; four distinct
rows protect all forwarded timestamp bounds. The nonempty packaged process test
exercises actual enrollment through replay and proves a false semantic assertion
fails with diagnostics and invalidates stale success. Python regressions protect
the receipt lifecycle, malformed lint inputs, frozen input hashes and signed
package hash distinction. The final Catalog-only reviewer reports no remaining
wording gaps in [the exact seven documents](evidence/story-4-10/description-review-final.json).
The two low schema findings retain the documented dispositions above. No new
deferred-work entry was created.

### Release prerequisite review (2026-10-20)

Three independent context-free layers read
`/tmp/story410-release-readiness-review.diff`, with current spec claims supplied
only to the edge layer. Edge-case and verification-gap layers reported no
findings. The blind layer's seven findings were assessed individually below.
These corrections remain in the isolated owning worktree; approved Contracts
and vectors are unchanged.

| Finding | Verdict and evidence | Route |
| --- | --- | --- |
| RF1: default Release is overridden | Medium. Every package graph explicitly sets the global mode false, so it cannot detect an unexpected source default. Evaluate ordinary Release without that override. | Patch |
| RF2: no bare-switch negatives for EventStore/Commons | Medium. The new no-autodetection claim is protected for McpCli only. A source selector activated by the global switch could escape the two other consumer loops. Add unmapped Debug cases for those consumers. | Patch |
| RF3: fixture described as tool-equivalent mapping | Low. Direct MSBuild properties exercise consumer conditions, not generated imports, hashes or validation targets. Narrow the current observation to that evidence. | Direct wording patch |
| RF4: nonexistent source projects pass evaluation | Medium. `-getItem` lists project references without checking file existence. Require every selected source project path to exist. | Patch |
| RF5: discovery depends on the selector being checked | Medium. Removing/misspelling a selector removes a project from the consumer loop; the reused detector cannot support the changed complete-consumer claim. Discover consumers from package/project identities independently of that selector. | Patch |
| RF6: effective versions are discarded | Medium. Catalog property equality plus package identity misses a per-reference VersionOverride. The reused helper cannot support the changed current-version claim. Retain and check effective package metadata against the expected selected versions. | Patch |
| RF7: Git global options evade command scanning | Medium. The new scanner recognizes only lines starting `git submodule update`; `git -c ... submodule update --recursive --init --remote` is omitted and passes. Scan all shell Git submodule-update forms and reject recursive/remote updates regardless of option order. | Patch |

All seven release-prerequisite findings are corrected. Independent final checks
on current main base `defb8d2f9a8b2c8732226227413c1808f3d7cafb` pass both Release
builds, 2,119 domain tests and 66 Sample tests with zero skips. The reviewed
three-file correction is upstream commit
`9a4a0657e6c928fbf923fceb9550b28e0b1c571c`, delivered as
[Parties PR #56](https://github.com/Hexalith/Hexalith.Parties/pull/56).
[Final prerequisite evidence](evidence/story-4-10/release-readiness/parent-verification.md)
retains exact commands, integrity checks and successful pinned commitlint validation.
Approved Contracts/vectors and historical matrix bytes remain unchanged. No new
deferral was filed. Required remote CI and the separate nine-pointer owner
sign-off in `RELEASE-CHECKLIST.md` remain publication gates; no sign-off was invented.

### Owning CI timeout correction

The prerequisite PR's build-and-test job passed all 4,846 tests across 14
projects, plus declaration, accessibility, commitlint, dependency and security
checks. Its final blocking Aspire job exhausted the existing ten-minute whole-job
limit: setup/build consumed 470 seconds, and no final TRX was produced before
GitHub cancelled execution. [Exact timeout evidence](evidence/story-4-10/release-readiness/pr-56-aspire-timeout.json)
retains the job annotation, log and green project results.

Use the pinned reusable workflow's existing `aspire-timeout-minutes: 30` input
in the isolated Parties `.github/workflows/ci.yml`. This bounded job allowance
leaves the test selection, failure policy, immutable execution pin and package/
source graph intact. Keep `aspire-continue-on-error: false`; no gate is waived.
Run the existing focused workflow tests, then parent verifies the complete
Ci.Tests project and actual remote CI. Contracts and vectors stay unchanged.

The one-line timeout input is delivered in
`df8173f04bd65cb86bc0d060dc75914e421f7640` on PR #56. Focused workflow tests pass
48/48; after generating the required solution/UI outputs, parent Ci.Tests pass
188/188 with zero skips. McpCli Core also passes 659 with two existing platform
skips after the approval inventory was added. The earlier PR run's whole-job
timeout is retained; [current CI](https://github.com/Hexalith/Hexalith.Parties/actions/runs/39449737463)
is rerunning. A concrete request for the nine exact dependency-pointer decisions
as release owner `jpiquot` is pending; the ledger remains unchanged until an
actual response. The Contracts candidate approval remains recorded.

### Merged prerequisite and exact-main continuation

[PR #56](https://github.com/Hexalith/Hexalith.Parties/pull/56) passed its complete
CI on `df8173f04bd65cb86bc0d060dc75914e421f7640`: 4,846 unit/integration tests,
98 Aspire tests and six existing health/readiness/degradation skips. All review,
security, declaration and accessibility checks passed. The normal rebase merge
produced `fa708d1cdb71a8926c9ed82e2e18a3ce58fd52ef`, with identical source tree
and both validated full commit messages preserved. No source reference changed.
[Current evidence](evidence/story-4-10/release-readiness/parent-verification.md)
retains the positive results and exact-main push CI, which is running.

The merged-main RC command still returns exit 1 for the same nine exact pointers.
The concrete owner request remains pending; no sign-off or publication occurred.
Release and enrollment acceptance tasks remain open. The six historical runtime
skips do not extend this story's approval or live qualification claims.

### Approved dependency continuation (2026-10-21)

The requesting user replied **"I approve"** to the exact nine-pointer owner
decision and subsequently instructed **"continue"**. The immutable
[owner receipt](evidence/story-4-10/release-readiness/gitlink-signoff-approval.json)
records `jpiquot`, all nine full revisions and the proposal hashes. This decision
does not extend to later dependency revisions or a changed Contracts artifact.

The previously observed exact-main CI on
`fa708d1cdb71a8926c9ed82e2e18a3ce58fd52ef` completed successfully. Remote main
subsequently advanced to `24ae57ea2386702ca9e7368e6b1f728b8956ca62`, changing
seven pointers and adding independently implemented bounded-search and corrupt-index
safeguards. Its push CI failed with CS0246: the newer Tenants Contracts source
uses `NativeSourceProof`, absent from its selected EventStore package.

[Parties PR #57](https://github.com/Hexalith/Hexalith.Parties/pull/57), initially
at `160db8990c74d0a15c89cc09add95f7a256ec758`, preserves the current Parties fixes,
records the actual owner decision and pins the release to the nine exact approved
revisions. No module source was edited and the pinned-tool source-selection model
is unchanged. Both local RC modes and the remote release-candidate gate pass.
Both full commit messages pass the owning pinned commitlint. The ordinary Release
restore/build and seven affected test projects pass: 3,690 tests, zero skips.
[Commands and delivery evidence](evidence/story-4-10/release-readiness/approved-dependency-continuation/continuation.json)
retain the initial and later source identities and scope.

The current search declaration documents the upstream 512 UTF-16-unit query limit.
Its [refreshed candidate receipt](evidence/story-4-10/release-readiness/approved-dependency-continuation/refreshed-candidate-pending-approval.json)
binds artifact `sha512-KGjggm+dn1aA9S80MM+nXOGzFyqKBXWQVDGWhfHieB+rmbKZAGbOA+2t6TF5vRy5eK5m+RCZSdd2DHVwn+ZIUg==`,
949 current source inputs, the unchanged seven vectors, release inventory and a
fresh independent Catalog-only description review. Complete artifact verification
passes strict discovery, lint, inventory and seven-vector replay. The historical
candidate approval is preserved. The requesting user approved the refreshed
artifact, unchanged vectors and release inventory with **"Approve refreshed
candidate and continue"**; the actual
[fresh decision](evidence/story-4-10/release-readiness/approved-dependency-continuation/refreshed-candidate-approval.json)
binds that answer to the pending receipt's exact inputs. Full owning CI,
protected publication, published-byte validation,
the owning Builds pin and production enrollment remain open.

PR #57 completed successfully, including 4,931 unit/integration tests and
98 Aspire tests with six existing runtime qualification skips. Its normal merge
included later test-helper changes; every production source file and all seven
approved vectors remain byte-identical. Two subsequent external pointer updates
cancelled exact-main CI and reintroduced the incompatible dependency selection.
The requesting user then confirmed **"Other writes are paused; continue"**.
The restored release source is `8c88c27acd5ed3ee2d2f2b6f51f3432d536f2021`,
tree `100ce7c1bdc782473759715ed806fb700806d1a2`, identical to the reviewed
merged tree. [Source comparison and CI provenance](evidence/story-4-10/release-readiness/approved-dependency-continuation/merged-main-continuation.json)
and [the exact restoration checks](evidence/story-4-10/release-readiness/approved-dependency-continuation/stable-release-source.json)
retain the actual coordination instruction, validated commit message and passing
RC checks. Required push CI is running for this exact current main source.

During enrollment preparation, strengthen the offline dependency fixture helper
so a captured candidate replaces its own already-restored module root while
preserving the selected non-module stack. Otherwise enrollment silently changes
the Parties fixture test into another check of the installed package. The two
new existing-root cases fail against the old helper; retain that evidence and
verify the complete Manifest test project after the correction and final enrollment.

### Published artifact and enrollment continuation (2026-10-21)

Exact-main push CI `39573997934` passed all 4,931 unit/integration tests and
98 Aspire tests, with six existing runtime qualification skips. Protected
[release run 39576141445](https://github.com/Hexalith/Hexalith.Parties/actions/runs/39576141445)
passed its source/registry preflight, normal required-reviewer approval by
`jpiquot`, publication and exact-source publication guard. It published
[Parties 1.5.1](https://github.com/Hexalith/Hexalith.Parties/releases/tag/v1.5.1)
from `8c88c27acd5ed3ee2d2f2b6f51f3432d536f2021`; all nine declared packages
are available from NuGet. [Protected publication evidence](evidence/story-4-10/release-readiness/approved-dependency-continuation/protected-publication/dispatch.json)
retains the actual environment approval and completed run.

The public Contracts archive is
`sha512-ed4HU6YJ2b6zwl0CJ5UbGILqaoi/5GXoVtyqf5YSeCRTbt+F9ozom+jIOdJjE0MjRcUsemeNQNgs2KZkHZgZUw==`.
Its repository metadata matches that source. The seven copied vectors change
only `/package/version`; all remaining bytes and semantic assertions are
preserved. [Publication binding](evidence/story-4-10/release-readiness/approved-dependency-continuation/published-artifact-binding.json)
links the actual fresh approval, source equivalence, transformation hashes and
successful public-byte verification without dependency overrides. All seven
description documents remain byte-identical to the independently reviewed ones.

Initial public replay exposed an unsigned-only assumption in the loopback host
guard: `.deps.json` carries NuGet's restore-content hash, which differs from
the repository-signed archive-byte hash. Preserve that failed receipt. The
corrected generic guard checks restore assets/cache metadata and independently
compares exact cached archive bytes with the immutable artifact. A signed-hash
regression first fails against the old guard, then all 88 Python regressions
pass; corruption of either archive, sidecar, cache metadata, assets or deps hash
still fails. [Regression and replay evidence](evidence/story-4-10/release-readiness/approved-dependency-continuation/signed-replay-regression/checks.json)
records the correction and successful full seven-vector replay.

[Builds PR #126](https://github.com/Hexalith/Hexalith.Builds/pull/126) pins
`HexalithPartiesVersion` to 1.5.1 and refreshes only the Parties audit family.
All other families, source observations and direct consumers are preserved.
Central versions, authoritative catalog, audit provenance, consumer authority
and exception validation pass locally; both commit messages pass pinned
commitlint. Merge must preserve the audit's exact catalog-source ancestor
`4878668412fe8803c3ef232e1775b1dd09f2f857`. Full owning CI `39578987205` passed
all required checks, including source/package qualification. Normal merge
`2744d549270298cfe73679f76b477a7368429006` preserves that ancestor and the exact
tested tree. McpCli's Builds gitlink selects this merged revision.
[Integration proof](evidence/story-4-10/release-readiness/approved-dependency-continuation/builds-pin/integration.json)
records tree equality and the preserved validated merge message.

McpCli's fresh Release restore/build and all six projects pass **1,339 tests**,
with zero failures and four existing Windows-only skips. Both sample gates,
89 Python regressions, the dedicated CI enrollment class and complete production
artifact replay pass. The sample process fixture now explicitly removes inherited
production flags before selecting its synthetic package; its prior failure and
corrected positive/negative replay checks are retained.
[Enrolled verification](evidence/story-4-10/release-readiness/approved-dependency-continuation/enrollment-checks/summary.json)
and [actual production discovery](evidence/story-4-10/release-readiness/approved-dependency-continuation/production-discovery/checks.json)
prove the built CLI and stdio MCP expose exactly seven lint-clean Parties
operations, with checked CLI stdout/stderr and exit codes. All three agent entry
points remain byte-identical. [Current matrix audit](evidence/story-4-10/release-readiness/approved-dependency-continuation/matrix-test-audit-current.json)
ties every frozen scenario to executed passing tests; none of the existing skips
covers a frozen matrix row. The final merged pin receives another fresh restore
and Manifest check before independent review.

## Verification

- Parties: Release restore/build; run Contracts, domain, Server and Client test
  projects individually, including privacy, paging and package regressions.
- McpCli: `dotnet restore Hexalith.McpCli.slnx`; Release build with
  `--no-restore -warnaserror`; run each existing test project individually.
- Run artifact/vector validation, complete replay and CI sample gates;
  restore after loopback. Record exact commands/results and evidence limits.

### Local implementation evidence (2026-10-20)

The local candidate, generic coverage/CI checks and dependency-policy reconciliation
are implemented. [Verification and release prerequisites](evidence/story-4-10/verification.md)
record the exact artifact, source/vector/verifier hashes, executed commands and
limits; [matrix audit](evidence/story-4-10/matrix-test-audit.md) binds every frozen
row to executed passing cases. The story remains `in-progress`: the exact candidate approval is recorded;
protected publication, published-byte verification and enrollment remain open. Independent code review,
final Catalog-only description review and final local verification are complete.
No scratch package was enrolled. The local candidate phase preceded the
authorized upstream release continuation recorded above.

The pre-review local Contracts artifact was `0.0.0-story410`, with hash
`sha512-hZfPC0pZaJa/gTFc5EwLInXwFvCrHoqXbTSezEbHkr9ss681wpf1muvcD6ipJ1eezxCyEttwzszSlI/ks9X1og==`.
The preserved [first review snapshot](evidence/story-4-10/review-pass-1/verification.md)
records its clean seven-operation Catalog/descriptions, complete seven-vector
replay, Contracts/Server/Client 201/315/330 and focused SDK 758/758 passing tests.
These broad results are historical. The broad domain command had three
pre-existing configuration fitness failures, with exact commands and baseline
proof retained in [the failure record](evidence/story-4-10/broad-domain-log.json).
That snapshot also records McpCli Release restore/build, each existing test
project, all 80 Python regressions and both sample gates passing; existing Core
and CLI skips are reported separately.

The review-patched final candidate retains version `0.0.0-story410` with new hash
`sha512-+gUcg4QyUd/GldA6JcYdBO8jzyWXavP7hg1fBikv0j6uO62gi3C/hyC9dp+IAQ3KLC8qQXxu726EfA6/NoT5/g==`.
Its refreshed [pending receipt](evidence/story-4-10/pending-approval.json) binds
source/vector/verifier byte manifests. Focused patch checks pass Python 20, SDK
handler class 738, final malformed-payload method 18, and decorations 2; the real
packaged-sample process fixture passes nonempty enrollment/replay and rejects a
false semantic assertion with useful diagnostics. Final artifact validation has
seven clean descriptions and seven complete vectors passing; actual restored
53-package identities/versions/archive and NuGet content hashes are retained.
These focused checks were followed by independent full verification below.
The first review archive is preserved byte-for-byte and grants no new approval.

### Independent final verification (2026-10-20)

[Exact final commands and results](evidence/story-4-10/parent-final/checks.json)
and the [final assessment](evidence/story-4-10/parent-final/verification.md) record
both Release builds passing with zero warnings/errors, all six McpCli projects
passing (1,338 passed and four existing skips), and Parties Contracts/Server/Client
passing 201/315/330. The full Parties domain command returned exit 2: 2,064 passed,
the same three baseline fitness failures, zero skips. Both sample gates passed
with all 87 Python tests, nonempty enrollment and the deliberate replay failure
check. A fresh restore preceded the final 103/103 Manifest tests. The production
enrollment checker passes with zero enrolled packages, which grants no Parties
release readiness.

[Independent integrity checks](evidence/story-4-10/parent-final/integrity.json)
matched all 196 source, seven vector and 30 verifier manifest entries, the exact
artifact hash, seven final descriptions and original review receipts. The
[pending approval receipt](evidence/story-4-10/pending-approval.json) also binds
the authoritative A1 migration inventory (including N01–N04 exclusions), release
inventory candidate and final description review. Its status remains pending.

Generic lint enforcement honors exact, referenced operation/code/property
acceptances and rejects new or stale exceptions. The eight Tenants paging-member
findings accepted in Story 4.8 are transcribed; Parties has no exception. Artifact
approval receipts also require an exact relative vector filename/SHA256 map, and
CI runs mutation regressions for changed bytes and added/removed/renamed vectors.
The pending Parties release-scope candidate fails the generic approval gate as
expected. Three stale baseline pins were reconciled to the exact fresh closure
(Commons.UniqueIds 2.30.3 and EventStore.Client/Contracts 3.126.0), with `modules`
still empty. The selected Builds gitlink already supplies those pins and was not
moved by this worker.

### Review Findings (committed story range, 2026-10-21)

Code review 2026-10-21 of the committed story range `9354dc0..558ce91` (`39f75e8`, `558ce91`).

- **Code-only scope:** excludes `_bmad-output/`, the `references/` gitlink moves and the seven copied `modules/Hexalith.Parties.Contracts/*.vector.json` files (approved bytes; only `/package/version` changed). The upstream Parties code is outside this repository's range.
- **Size and mode:** 30 files, +1,805/−30, 2,186 diff lines, full mode, with `parties-migration-inventory-v1.md` as context.
- **Layers:** Blind Hunter (BH), Edge Case Hunter (EC), Verification Gap (VG) and Acceptance Auditor (AA). No layer failed.
- **Result:** 52 normalized findings. 13 survive as 1 decision, 11 patch and 1 defer entries; 26 entries are rejected.

Parent check during triage: a scratch host holding only a `ProjectReference` to a copy of `src/Hexalith.McpCli` restored `Hexalith.Parties.Contracts/1.5.1` transitively. With `-p:HexalithEventStoreVersion=3.124.0` the restore failed with NU1109 through `Hexalith.Parties.Contracts 1.5.1 -> Hexalith.EventStore.Contracts (>= 3.126.0)`.

- [x] [Review][Decision] R1 — low. The sample loopback still restores and builds the tracked ConformanceHost but no longer replays it. `39f75e8` replaced the direct `run_loopback.py --host tests/Hexalith.McpCli.ConformanceHost/...` call with `run_packaged_process_fixture.py`, whose positive path replays the same three vectors through a generated `ArtifactHost`. The tracked host's `--force` restore into the deleted task cache has no consumer left, `tools/conformance-vectors/v1/README.md:75` still says the script executes all three vectors through that host, and `:151` says CI "also runs" the fixture. Options: (1) restore the five-line direct replay so every existing statement holds; (2) delete the unused restore/build and rewrite `README.md:75` and `:151` (BH, VG, AA, EC). **Resolved 2026-10-21:** the user chose option 1 ("apply recommended"). Both options comply with the pinned Platform rules (`references/Hexalith.Platform` at `bc36d21`). The direct replay is restored before the fixture call, byte-identical to the baseline [tools/conformance-vectors/v1/run-sample-loopback.sh:31]. `bash tools/conformance-vectors/v1/run-sample-loopback.sh` exited 0 in 1 m 43 s: 100 Python tests, all three tracked-host replays without `--assets`, and all three fixture checks. A fresh `dotnet restore Hexalith.McpCli.slnx` followed.
- [ ] [Review][Patch] R2 — medium. `verify_artifact.py` copies `src/` unchanged, so every generic candidate host inherits the shipped tool's flagged `Hexalith.Parties.Contracts` reference. The candidate's restore and `resolvedPackages` evidence include Parties 1.5.1, and an `align_candidate_dependencies` override below EventStore 3.126.0 fails with NU1109 (reproduced above); the decorated Tenants candidate needs 3.125.1 (`deferred-work.md:528`). Strip `HexalithContracts` PackageReferences from the scratch tool project before restore, as `run_packaged_process_fixture.enroll_fixture` does, and add a regression (EC). [tools/conformance-vectors/v1/verify_artifact.py:151]
- [ ] [Review][Patch] R3 — medium. The candidate pin uses `PackageVersion Update=`, which does nothing when no central `PackageVersion` exists. The Builds props have none for the Works, Timesheets or Agents Contracts, so their pre-pin candidate verification fails restore with NU1010; the process fixture passes only because it adds an `Include` first. Emit `Remove` then `Include` (EC). [tools/conformance-vectors/v1/verify_artifact.py:168]
- [ ] [Review][Patch] R4 — medium. The `EnrolledInventoryCoverageGate` module-mismatch branch has no test: deleting it leaves all three `EnrolledModuleCoverageTests` green, and with a second enrolled module a copied inventory could stand in for the named one. Add a two-module fact (sample plus `string-fixture`) where one module's file is the other's valid release inventory, asserting exactly `string-fixture: inventory declares a different module.` (VG, BH, AA). [tests/Hexalith.McpCli.Core.Tests/EnrolledInventoryCoverageGate.cs:40]
- [ ] [Review][Patch] R5 — medium. The structural accepted-lint guards are untested in both gates: in C#, the non-array root, field count, duplicate row and invalid JSON; in Python, the exact key set and duplicate row. A Python mutation that drops them still passes 31/31 and then accepts a row without `approvalReference`. The existing C# assertions check only counts or prefixes. Add the cases with full messages (VG, BH, AA). [tests/Hexalith.McpCli.Core.Tests/DescriptionLintGateTests.cs:13; tools/conformance-vectors/v1/verify_artifact.py:26]
- [ ] [Review][Patch] R6 — medium. Nothing asserts that enrolled verification runs without candidate dependency overrides. Flipping `align_candidate_dependencies=False` to `True` passes every test, because the current nuspec versions equal the Builds pins; after a later Builds bump the gate could verify against older stacks. Assert the kwarg in `test_existing_approval_directory_and_package_id_ignore_case`, and assert `candidateDependencyOverrides == []` in the fixture's positive path (VG). [tools/conformance-vectors/v1/check_enrolled.py:106]
- [ ] [Review][Patch] R7 — low. Two `check_enrolled` preflight guards have no removal test. Replacing the receipt `module` check with `if False:` still passes, and `None` then raises an uncaught `TypeError` that leaves `enrolled.json` pending. The zero-match approval directory is also untested; only the ambiguous case is. Add subtests asserting exit 1, `failed`, the diagnostic and no `verify` call (VG, BH, AA). [tools/conformance-vectors/v1/check_enrolled.py:98; tools/conformance-vectors/v1/check_enrolled.py:51]
- [ ] [Review][Patch] R8 — low. The digest and malformed-root tests seed the child receipt once in `setUp`, so from the second subtest on, `assert_invalidated_child` passes trivially. Re-seed `verification.json` and `artifact.sha512` at the start of each subtest (EC). [tools/conformance-vectors/v1/test_enrolled.py:252; tools/conformance-vectors/v1/test_enrolled.py:271]
- [ ] [Review][Patch] R9 — low. The fixture builds `expected_diagnostic` from the unresolved temporary root, while `verify` resolves its output path. The pending-inventory check therefore fails spuriously wherever the temporary path is a symlink, such as macOS `/var` → `/private/var`, a platform the validation README supports. Resolve the temporary root (EC). [tools/conformance-vectors/v1/run_packaged_process_fixture.py:43]
- [ ] [Review][Patch] R10 — low. The new hash-bound files have no end-of-line rule; `.gitattributes` covers only `*.cs`. Git for Windows' default `core.autocrlf=true` checks them out as CRLF and breaks `vectorFilesSha256` and `inventorySha256` locally. Add `text eol=lf` for `tools/conformance-vectors/v1/modules/**` and `tools/inventory-coverage/v1/*.json` (BH). [.gitattributes:1]
- [ ] [Review][Patch] R11 — low. `README.md:99` says `hexalith operations parties --strict` lists `get-party`, `list-parties`, …, but the built CLI prints the full names, `parties.create-party` first, in alphabetical order (checked independently by two layers). Match the actual output (AA, BH). [README.md:99]
- [ ] [Review][Patch] R12 — low. Documentation drift: the `verify_artifact.py` synopsis omits `--accepted-lint`, a double blank line follows the lint paragraph, and the root README's hard-wrapped enrollment paragraph sits at the end of the MCP section, repeating line 99. Add the option, drop the blank line, and merge the paragraph into the enrollment section (BH). [tools/conformance-vectors/v1/README.md:83; tools/conformance-vectors/v1/README.md:131; README.md:204]
- [x] [Review][Defer] R13 — low. `AGENTS.md:83` (and its synced copies) still describes enrollment as a flagged PackageReference plus a `modules` pin. Enrollment now also needs `modules/<PackageId>/approval.json` with hash-bound vectors, a release `<module>-approved.json` and a passing `check_enrolled.py` [AGENTS.md:83] — deferred: the fix edits agent-context files. New ledger entry (`deferred-work.md:559`) for the next bmad-project-context refresh (BH).

#### Rejected (committed story range)

- `low` — `check_enrolled.py` accepts a `purpose: "fixture"` inventory and skips the module match (BH, EC, AA). The claim holds, and the process fixture's positive path depends on it. But `EnrolledModuleCoverageTests` enforces release purpose earlier in the same CI job and in the `ci` job, the inventory digest is bound to the receipt, and the fix means redesigning the fixture's synthetic authority, because the C# checker rejects `synthetic-fixture` authority under `release`.
- `low` — `approvalReference` is only required to be a nonempty string, and `publishedArtifactBinding` and `publication` are never read (BH, AA). The receipt binds the exact artifact, inventory and vector hashes. The reference is a documented free-form pointer (the fixture uses free text), and parsing evidence mechanically would add a schema.
- `false` — An unbound accepted-lint file lets new exceptions pass (BH, EC, VG). Both gates require exact set equality with the actual findings, and the artifact is hash-bound. Parties 1.5.1 has zero findings, so any added row fails as stale and `[]` changes nothing.
- `low` — Data for modules that are not enrolled (`tenants-accepted-lint.json`, orphan approval directories) is never checked (BH). The exact-equality check runs once the module is enrolled, and orphan directories are inert.
- `low` — No test backs the claim that `parties-candidate.json` fails the gate (BH, AA). Its rows are `pending`/`scope-only`, which the existing checker rejects (retained in the `approval-gate-negative` evidence). It is historical input, not a guard.
- `false` — Python and C# apply different Catalog-diagnostic rules, and the specific Python message is unreachable (BH, AA). Strict `CatalogProvider.Get` (`src/Hexalith.McpCli.Core/Catalog/CatalogProvider.cs:30`) refuses any diagnostic, so the C# test's strict `ListOperations` and `Describe` calls already fail on warnings. The unreachable Python check duplicates a fail-closed guard, and the catalog step prints the diagnostics.
- `low` — Lint acceptance is implemented twice (BH). Any divergence fails closed because CI runs both lanes, and consolidating through a host mode is a refactor.
- `low` — The `InventoryCoverage*.cs` glob and its hard-coded exclusions are repeated in three places (BH, EC). A new matching test file breaks the host builds loudly, and an explicit file list is just as fragile.
- `low` — Evidence retention gaps: the `approval.json` hash is not recorded, the first failure stops later packages, and a reused output directory keeps stale logs (BH, EC). CI uses a fresh `RUNNER_TEMP`, the commit identifies the receipt and one package is enrolled; the fixes add bookkeeping.
- `false` — The `owning-maintainer` authority contradicts "the requesting user" (BH). The requesting user is the recorded release owner `jpiquot`, per the owner receipt and the protected-environment approval.
- `false` — The Parties 1.4.0 closure test hides a downgrade (BH). `RealCandidate` models enrolling that candidate, reference and pin together, and `DependencyPolicyGate` enforces pin/restore equality separately (`tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyGate.cs:164-168`).
- `maybe-false` — Dependency reading can select a nested `.nuspec` and flattens target-framework groups (BH, EC). `package_identity` already requires exactly one root nuspec, and no NuGet-produced package with a nested nuspec listed first was shown. The overrides cover two dependencies of single-target packages. Would be `low` if true.
- `low` — `EnrolledModuleCoverageTests` reads the generated manifest by reflection, and Core.Tests references the CLI (BH). A generator change fails the test loudly, and `InternalsVisibleTo` would be a production change.
- `low` — The gates never require an example (AA). All seven describe documents contain examples bound by the artifact hash; requiring one would be a new lint policy.
- `low` — No automated smoke test of the shipped CLI/MCP process (AA). Same as FB9; that disposition stands.
- `low` — `parties-approved.json` rows reference `candidate-approval.json`, which approved the pending candidate bytes `d01c48…` (AA). The refreshed approval binds the exact `79a787…` bytes, so the chain is complete. Repointing would change approved bytes and need another approval.
- `low` — `verify`'s "Restored package bytes do not match the supplied artifact" check is untested (AA). The replay host check enforces the same binding and has mutation subtests in `test_loopback.py`.
- `low` — A `-class` filter that matches zero tests exits 0 (EC). Core.Tests runs in full in the `ci` job, so the class still executes.
- `false` — An uncaught `TypeError`, `AttributeError` or `ParseError` leaves `enrolled.json` pending (EC). Only malformed NuGet cache or assets data reaches them, the process still exits nonzero, and `pending` is not success.
- `low` — No subprocess timeouts (EC). No CI job sets `timeout-minutes`, a hang fails loudly, and timeouts add parameters.
- `low` — An unversioned or ranged nuspec dependency breaks the overrides (EC). Overrides apply only to two Hexalith dependencies with plain versions, and only when enabled.
- `low` — A nuspec version with build metadata gives a misleading mismatch (EC). Hexalith releases use plain versions, and the mismatch fails loudly.
- `false` — `expected_inventory_hash` without an inventory raises `TypeError` (EC). The only caller always supplies both.
- `false` — `WithCandidate` throws `KeyNotFoundException` for a fixture without its root (EC). Every committed fixture contains its root, and a malformed one fails the test loudly.
- `low` — A deleted inventory stays in `bin` on incremental builds (EC). This is the existing copy pattern, and CI builds clean.
- `low` — Python and C# handle a UTF-8 BOM differently (EC). The strict Python loader fails closed, and that shared loader predates the story.
