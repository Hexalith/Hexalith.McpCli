---
title: '4.12 Compose the v1 live test topology'
type: 'feature'
created: '2026-10-23'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 'be89509d59bb6ba53a0382e26219edb0625b47f4'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-4-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** McpCli has no repeatable live Gateway topology. Parties also lacks
the published Aspire helper required by Story 4.12.

**Approach:** Prepare that prerequisite upstream, then compose EventStore,
Tenants and Parties through published helpers in a test AppHost. Reuse the
platform fixture and prove usability with a bounded Gateway smoke request.

## Boundaries & Constraints

**Always:** Change helpers and package catalogs in their owning repositories.
Review the exact Parties helper artifact and dependency closure before admitting
it as test-only. Obtain the required release authorization for the concrete,
qualified upstream candidate before publication. Keep approved production
Contracts pins, vectors and inventories intact; pin helpers independently when
their releases differ. Use only root-declared workspace checkouts. Preserve
existing user processes and report source/build/runtime blockers precisely.

**Never:** Edit reference contents, initialize nested submodules, import server,
handler, aggregate, projection or module-client packages/projects into McpCli,
copy platform orchestration machinery, bypass authentication, or introduce an
identity server. Add no module-specific operation setup/execution branches.
Full vector semantics and blocking CI source-build wiring remain 4.13 and 4.14.

## I/O & Edge-Case Matrix

| State | Expected behavior |
| --- | --- |
| Qualified helpers, built source and available Dapr | Start all three services; authenticated Gateway smoke succeeds |
| Missing helper or forbidden helper dependency | Refuse enrollment; name the package and dependency |
| Missing or undeclared root checkout | Fail before launch with the required path; never search nested references |
| Missing Dapr prerequisites | Use the standard diagnostic/skip; never report live acceptance |
| Resources alive but Gateway unusable | Fail within the smoke timeout with useful diagnostics |
| Conflicting user topology | Report the conflict; do not stop, restart or reuse it implicitly |

</frozen-after-approval>

## Code Map

- `Directory.Build.props` pins Contracts to Parties 1.5.1 and Tenants 5.10.0
  before importing Builds. EventStore is 3.126.1.
- `references/Hexalith.Tenants/src/Hexalith.Tenants.Aspire/` supplies the upstream
  helper pattern: project metadata plus `AddEventStoreDomainModule`.
- EventStore.Aspire 3.126.1 exposes `AddHexalithEventStoreGatewayProject` and
  gateway-only `AddHexalithEventStore`; its integration package exposes
  `AspireTopologyFixtureBase<TAppHost>` and `DaprTestPrerequisites`.
- `tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyTests.cs` checks all test
  projects, including projects outside the solution. Its Parties-helper rejection
  cases need revision when that package becomes approved.
- Story 4.11 established loopback parity; its completed tasks do not prove live
  service readiness. The earlier query spike records topology collision risks.

## Tasks & Acceptance

**Execution:**
- [x] Owning `/home/administrator/projects/hexalith/parties`:
  `src/Hexalith.Parties.Aspire/{Hexalith.Parties.Aspire.csproj,HexalithPartiesServerExtensions.cs,PartiesServerProjectMetadata.cs}`,
  `tests/Hexalith.Parties.Aspire.Tests/`, solution and release declarations —
  prepare and qualify the server-package-free helper using platform composition;
  release through the owning repository's normal gates.
- [x] Owning Hexalith.Builds `Props/Directory.Packages.props` and required catalog
  audit files — enroll the actual published helper version without changing
  approved Contracts identities; integrate only the necessary root gitlinks.
- [x] `tools/dependency-policy.json` and
  `tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyTests.cs` — admit the
  reviewed helper only for tests; preserve production and implementation-package
  rejection with meaningful negative cases.
- [x] `tests/Hexalith.McpCli.AppHost/{Hexalith.McpCli.AppHost.csproj,Program.cs,appsettings.json,DaprComponents/}`
  — compose the three services, explicit Gateway routing, shared Dapr components
  and test authentication through helpers; validate root checkout membership.
- [x] `tests/Hexalith.McpCli.Integration.Tests/{Hexalith.McpCli.Integration.Tests.csproj,AspireTopologyFixture.cs,AspireTopologyCollection.cs,GatewaySmokeTests.cs}`
  — share the standard fixture, prerequisite checks and Integration trait; issue
  one bounded authenticated query through the pinned Gateway client and assert
  a real successful document. Keep liveness separate from usability.
- [x] `tests/Hexalith.McpCli.Manifest.Tests/TopologyConfigurationTests.cs` — protect
  root-only source selection and dependency/configuration guards with negative
  cases that fail when the guard is removed.
- [x] `Hexalith.McpCli.slnx`, `.github/workflows/ci.yml`, `README.md` and
  `_bmad-output/implementation-artifacts/evidence/story-4-12/` — register projects,
  verify smoke discovery in a focused non-live CI lane, document bounded local
  source builds and smoke execution, retain exact versions and sanitized results.
  The blocking Aspire CI tier stays in 4.14.

**Acceptance Criteria:**
- Given the published Parties helper, when its exact artifact is inspected, then
  its closure contains no server package and it locates root workspace source.
- Given published helpers and built root checkouts, when the test AppHost starts,
  then EventStore, Tenants and Parties run without forbidden McpCli references.
- Given available Dapr, when the shared fixture starts, then it waits through the
  platform base and the bounded authenticated Gateway query returns successfully.
- Given missing prerequisites or unusable resources, when checks run, then the
  recorded result distinguishes skipped, failed and genuinely passed live proof.

## Implementation Notes

- Final completion: the published-helper topology passed the three review layers
  and parent verification. Non-live results are 1,457 passed, zero failed on the
  completed runs, five existing skips; Manifest is 177 passed with no skips.
  The strengthened live smoke passed with no skips and two real HTTP 401
  rejections before the successful authenticated document. The catalog CI is
  green at its exact integrated source. Earlier checkpoints below remain
  historical evidence; current results are in `evidence/story-4-12/publication-20261023/expanded-publication/parent-final-verification/`.

- On 2026-10-23 the user explicitly authorized the qualified expanded candidate
  `08f43497b3f916efa0cdf9b110258f763d894bd9` for normal publication of selected
  1.6.0 (ten NuGet packages and three amd64/arm64 image families), followed by
  Builds/McpCli integration, then instructed: "bypas any human authorization gate".
  Ordinary authorized production approvals were used; automated gates and
  environment protection configuration were preserved.
- Publication completed at the ledger-only successor
  `a4716d0da37b27762d9931c778223d13e85695dc`. Its 95 qualified source-file hashes
  and eight gitlinks match the authorized candidate. The release-range ledger
  records the already authorized user selections. Exact-source normal CI
  `39950468353`, range, commitlint and CodeQL passed. Normal release
  `39954248029` published and verified all ten NuGet 1.6.0 packages and all three
  multiarchitecture container families. Failed prepublication runs remain in
  the evidence. The frozen 59-file qualification packet remains byte-identical.
- Actual signed `Hexalith.Parties.Aspire` 1.6.0 is 26,220 bytes with SHA-256
  `6b7678949525490453e07113611d19a7e7d6cf3c0b64e427773694da0f457695` and repository
  commit `a4716d0da37b27762d9931c778223d13e85695dc`. Its only direct dependencies
  are Aspire.Hosting 13.6.3 and Hexalith.EventStore.Aspire 3.126.1. Fresh-cache
  NuGet-only inspection, server-free closure and all six root locator probes
  passed. Historical local `.1` through `.4` artifacts are not publication proof.
- Owning Builds catalog `ca1262562b8da711043fd698b0aea1e7b34e5c40` enrolls the
  independent helper 1.6.0 and advances only the global Parties family to the
  actual published 1.6.0 under the unchanged audit model. The six global default
  selections changed honestly; all 306 existing McpCli evaluated selections
  remain identical under its Parties 1.5.1/Tenants 5.10.0 overrides. SDK inventory,
  consumer authority and the 307-package/151-family audit passed. Commitlint
  `39958144989` and normal CI `39958144971` attempt 2 passed at exact catalog
  source `ca1262562b8da711043fd698b0aea1e7b34e5c40`; the original Module.Tests
  failure and both attempts remain retained. No G-4 code was
  changed. The independent two-file execution backport `d9070aa0d43feb9e3359286bc797d2be65960727` remains pinned
  by Parties and passed normal CI `39941850208`; catalog selection is independent.
- McpCli admits the actual published helper only for tests. Production Contracts
  pins, inventories and vectors are unchanged. The standard platform test-root
  closure is recorded separately from the server-free helper closure. AppHost
  launch guards execute before resource creation and reject root membership,
  weak authentication, malformed Dapr records and genuine identity/port conflicts.
  Gateway configuration uses the test-owned content root, three explicit module
  registrations and the shared default-deny Dapr ACL. Only the Gateway may POST
  operational metadata; executable mutation controls reject its removal or
  broader callers, paths, verbs/default permissions and disabled mTLS.
- All three root source server Release builds passed with warnings as errors.
  The final unchanged standard fixture and authenticated ListTenants smoke passed
  in private user/PID/network/mount namespaces: one executed, one passed, zero
  failed, zero skipped, 16.809 seconds. The actual Gateway request returned 200;
  no inherited sample metadata calls occurred. All four private infrastructure
  processes exited 0. User AppHosts were preserved. Sentry and TLS prerequisites
  are documented; `dapr init` alone is insufficient. Earlier 403/404 and mTLS
  setup failures are retained separately, without changing the approved query.
- Fresh root restore and Release warnings-as-errors build passed. Individual
  non-live projects passed: Abstractions 20, Analyzers 19, Core 704 (three existing
  skips), CLI 479 (two existing Windows skips), MCP 58 and Manifest 158 (zero
  skips). Missing-Dapr coverage is a passing outer test asserting the standard
  child skip, and the alive-but-stalled Gateway test executes the real 30-second
  deadline. Focused non-live discovery lists exactly one smoke. McpCli remains
  uncommitted; parent acceptance audit and all three review layers completed, with patches verified below.
- Current receipts and the matrix map are in
  `evidence/story-4-12/publication-20261023/expanded-publication/README.md`.
  The original qualified source packet remains at
  `evidence/story-4-12/publication-20261023/expanded-source-candidate/README.md`.
  Superseded progress notes, failed gates and local/tooling limitations are
  preserved in `expanded-publication/historical-implementation-notes.md` and the
  historical publication receipts; they do not replace the current outcomes.

## Spec Change Log

## Review Triage Log

| Finding | Verdict | Route | Evidence and disposition |
| --- | --- | --- | --- |
| B1 | medium | patch | Program.cs:15 parses configuration before its catch. The built malformed/overflowing-port path aborts rather than reporting exit 2; move conversion inside the existing boundary and protect both cases. Resolved: malformed and overflowing ports execute inside the existing diagnostic boundary; both process cases pass with exact exit/channels. |
| B2 | low | patch | TopologyConfiguration.cs:153 accepts 1–1023 although the consumed EventStore helper rejects ports below 1024. This is a direct range/diagnostic correction, even though the input is uncommon. Resolved: helper-aligned 1024–65535 range; direct and executable lower-bound cases pass. |
| B3 | medium | patch | The topology adds Sentry, CLI and mTLS prerequisites beyond the published three-service probe. Historical failed mTLS runs and the probe implementation show startup is entered without all mandatory inputs; add a bounded supplementary missing-prerequisite check and standard skip diagnostic. Resolved: CLI/mTLS/Sentry supplement and actual fixture-call removal control passed; standard basic probe and skip prefix retained. |
| B4 | medium | defer | The published platform base acquires its file lock before its startup CTS, with an indefinite retry. This predates this story; tracked at `deferred-work.md:589`; require an outer process deadline in the supported local command. |
| B5 | medium | patch | The checked-in Redis endpoints and keyPrefix reuse the supplied runtime by design. Free IDs cannot prove disposable state ownership; make a disposable isolated runtime an explicit mandatory local prerequisite and provide its reproducible setup, without flushing or changing any user store. Resolved: disposable isolated Dapr/private Redis and an outer deadline are mandatory; digest-bound bootstrap reproduced all four binaries. |
| B6 | medium | patch | The ACL-content test does not observe sidecar configuration attachment. Removing an AppHost config argument can leave both that test and the positive smoke passing; assert actual composed sidecar configuration. Resolved: actual model checks every sidecar ACL; each attachment removal built and failed coverage, then restored positive passed. |
| B7 | medium | patch | The historical verifier is outside automated topology tests. A composition assertion must protect the actual Gateway content-root setting so removal cannot retain a green ordinary suite. Resolved: actual model checks the Gateway content root; its removal built and failed coverage, then restored positive passed. |
| B8 | medium | patch | A valid-token positive alone does not demonstrate rejection. Exercise missing and invalid credentials at the real Gateway boundary while retaining exactly one successful authenticated query. Resolved: strengthened single live smoke rejects missing/invalid JWTs with two real 401s before the successful authenticated document. |
| B9 | low | patch | TopologyConfiguration.cs:140 captures stderr and omits it in the nonzero exit diagnostic. A bounded excerpt and executable nonzero-stub test are direct diagnostic corrections. Resolved: nonzero CLI errors include at most 512 stderr characters; normal and truncated process cases pass. |
| B10 | medium | patch | The private reproduction command requires untracked temporary binaries. The source images and hashes are recorded but setup is absent; document or provide a bounded verified bootstrap that recreates them. Resolved: bounded bootstrap pulls pinned digests, verifies every extracted binary and removes only owned never-started containers; executed bootstrap passed. |
| E1 | low | patch | Independent verification confirms the same below-1024 helper/preflight mismatch as B2. Keep the direct correction; group by that shared range defect after individual verdicts. Resolved with B2; same helper range defect and executed boundary cases. |
| E2 | medium | patch | Independent executable reproduction confirms the same pre-catch conversion failure as B1, including an out-of-Int32 value. Group with B1 after individual verdicts. Resolved with B1; same pre-catch conversion defect and executed process cases. |
| E3 | medium | defer | Independent platform tracing confirms B4: the pre-existing lock wait precedes the six-minute timeout. Group with B4, already tracked (`deferred-work.md:589`); no local lifecycle copy or source-reference edit is permitted. |
| V1 | medium | patch | Pre-verified gap: direct OccupiedGatewayPortFails does not protect the EnsureNoConflictingTopology invocation. Every launch test releases its port first; keep a real listener bound through an actual subprocess test. Resolved: occupied-port executable test keeps the listener bound through invocation and asserts exact exit/channels. |
| V2 | medium | patch | Pre-verified gap: removing Parties generated APP_API_TOKEN leaves Development admission NotRequired and can retain the Tenants smoke. Assert effective nonempty matching app/sidecar tokens for each resource. Resolved: effective app/sidecar environments require distinct nonempty matching token pairs for all three services; each token removal fails. This also exposed and corrected the Gateway’s missing token via the published helper. |
| V3 | medium | patch | Pre-verified gap: the stalled-query test never covers immediate Gateway failure translation. A real local 403 through the pinned client must assert status and exact useful diagnostic. Resolved: real local 403 through the pinned client asserts exact contextual diagnostic, inner exception type and status. |

## Verification

The actual published-artifact inspection, source gates, catalog integration,
fresh restore/build, six individual test projects, non-live discovery and
non-skipped live smoke are recorded in
`evidence/story-4-12/publication-20261023/expanded-publication/README.md`.
Normal owning Builds CI, parent acceptance audit and all three review layers are
complete. All 14 patch findings are resolved; the two lock findings share one
pre-existing upstream deferral (`deferred-work.md:589`). Final fresh restore,
Release warnings-as-errors build and one-test discovery passed. The six individual
projects passed 1,457 tests (five existing skips); all 177 Manifest tests executed.
The parent’s strengthened live smoke passed one test without skips in 23.741
seconds, rejecting missing/invalid JWTs before the successful document. All four
private infrastructure processes exited cleanly. Full receipts are in
`evidence/story-4-12/publication-20261023/expanded-publication/parent-final-verification/`. Earlier unpublished artifacts, failed attempts and existing test
skips remain clearly identified in their original evidence.

The parent full CLI suite first reproduced the unchanged HTTP-listener cleanup
race already tracked (`deferred-work.md:467`). The 19-case query class and full
CLI suite then passed; both failed and successful results are retained. No new
ledger entry or unrelated source change was made for that existing race.
