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
- [ ] Owning Parties release workflow; owning Builds
  `/home/administrator/projects/hexalith/builds/Props/Directory.Packages.props`
  — deliver verified publication and its central pin through normal owner gates.
- [ ] `src/Hexalith.McpCli/Hexalith.McpCli.csproj`, `tools/dependency-policy.json`,
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
