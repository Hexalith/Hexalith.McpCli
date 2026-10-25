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

- Review pass 4 implementation checkpoint (2026-10-24): P37–P40 are resolved.
  Exact daemon arguments and network setup ordering are protected; both README
  claims are corrected; an empty inner command records failure. Fresh restore,
  Release warnings-as-errors solution build, all 210 Manifest cases, 18 Python
  checks in normal and optimized execution, exact one-smoke discovery and four
  mutation controls passed. Current focused receipts and source bindings are
  in `evidence/story-4-12/review-pass-4-20261024/verification.json`. Parent
  acceptance and workflow review remain pending; no fresh live smoke ran in
  this implementation checkpoint. The previous accepted live run is retained
  in the pass-3 final evidence below.

- Final status (2026-10-24): all P37–P43 patches, parent acceptance and workflow
  review are complete. Final verification passed 1,492 non-live .NET tests, 18
  Python checks normally and under optimization, and one isolated live smoke
  without skips. Earlier pending notes below are historical; current evidence is
  `evidence/story-4-12/review-pass-4-20261024/parent-final/verification.json`.

- Review pass 3 patches P25–P32 are implemented. The Release warnings-as-errors
  solution build and all three bounded root server builds passed. Six individual
  non-live suites passed 1,485 tests with zero failures and five existing skips;
  all 205 Manifest cases executed. All 15 maintained Python checks passed, and
  discovery lists exactly one live smoke. The fresh, hash-verified isolated
  runtime passed that smoke without skips in 25.627 seconds; all four private
  daemons exited 0, no private keys remained, and host Dapr identities were
  preserved. Current exact commands, source binding, patch and acceptance-matrix
  mapping are in `evidence/story-4-12/review-pass-3-20261024/`. Parent acceptance
  audit and workflow review remain pending for this resumed implementation.

- Code review pass 2 patches P15–P24 are implemented. Fresh restore and the
  final Release warnings-as-errors solution build passed; all 201 Manifest cases
  and 12 maintained runtime-tool cases passed. The prerequisite class also
  passed all 12 cases from relocated built outputs with no root `references/`
  directory. The documented `-failSkips` isolated live smoke passed one test
  without skips in 17.941 seconds; the explicit missing-CLI check exited 1 with
  `FAIL_SKIP`. All four private daemons exited 0, no private keys remained, and
  both pre-existing user AppHosts kept their identities and running state.
  Sanitized exact-command receipts and patch mapping are in
  `evidence/story-4-12/review-pass-2-20261023/`. Parent acceptance audit and review
  remain pending. The initial endpoint-fixture failure is retained separately.

- Final parent verification after the follow-up review passed: 1,479 non-live
  tests, zero failed, five existing skips; all 199 Manifest cases executed.
  All nine maintained runtime-tool tests passed. The strengthened live smoke
  passed without skips in 17.483 seconds using freshly bootstrapped binaries,
  inherited Redis-port override and optimized Python. Two real HTTP 401
  rejections preceded the successful authenticated document; all four private
  infrastructure processes exited 0 and no private keys remained. Three review
  layers produced 15 findings; seven patch groups are resolved and six low
  findings were rejected. Current receipts are in
  `evidence/story-4-12/review-patches-20261023/final-verification/`. Earlier
  checkpoints below remain historical evidence.

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

### Follow-up implementation review (2026-10-23)

Each finding was classified before grouping. BH and EC are the independent blind
and edge-case reviewers; VG is the verification-gap reviewer.

| Finding | Verdict | Route | Evidence and disposition |
| --- | --- | --- | --- |
| R-BH1 | low | patch | Python optimization removes the PID/namespace, Redis and Dapr assertions. Explicit conditional failures are direct corrections to existing checks; protect optimized execution. |
| R-BH2 | low | patch | The documented outer deadline sends SIGTERM, whose default Python action bypasses bootstrap `finally`. Install a termination handler so owned extraction-container cleanup runs; verify controlled termination. |
| R-BH3 | low | reject | Docker may create a stopped extraction container before its CLI times out. This uncommon ambiguous-create failure would require new naming and recovery state; it does not affect running user containers. |
| R-BH4 | low | reject | A process disappearing between the post-timeout poll and SIGKILL can interrupt cleanup. This narrow shutdown race is unlikely in ordinary runs; independent cleanup recovery adds branches and receipt state. Namespace destruction still terminates private processes. |
| R-BH5 | low | reject | External termination can stop infrastructure before the test child; private PID-namespace destruction then kills the child. The failed/interrupted command cannot become a passing smoke and no host workload survives in that namespace. Graceful-shutdown reordering adds lifecycle handling for an already interrupted run. |
| R-BH6 | medium | patch | The wrapper inherits `HEXALITH_EVENTSTORE_TEST_REDIS_PORT`, which the platform fixture honors, while its private Redis/components use 6379. Pin the probe to 6379 and assert the child's effective environment. Shared root cause with R-EC2. |
| R-BH7 | low | reject | A deliberately modified source checkout can contain inner source/project symlinks. Published root checkouts contain ordinary project paths; resolving every inner link adds filesystem guards for a nonstandard checkout, beyond a direct correction. |
| R-BH8 | medium | patch | Direct live AppHost execution bypasses the fixture's isolation marker and can reach host Redis. Reuse the same isolation refusal before launch, preserving non-launching preflight/inspection, and assert exact executable diagnostics. |
| R-BH9 | medium | patch | A controlled existing listener on 50001 made the missing-Sentry theory fail with AddressAlreadyInUse. When that absence condition cannot be arranged, explicitly skip only that case; retain the exact rejection assertion when free and verify an occupied-port run cannot fail. Shared root cause with R-EC1. |
| R-BH10 | medium | patch | A private daemon can exit during the child command and its recorded failure does not affect wrapper success. Check owned daemons again before accepting the child result; assert a successful child with failed infrastructure produces failure. Continuous polling is unnecessary for this correction. |
| R-EC1 | medium | patch | Independently reproduced the fixed-50001 missing-Sentry test failure with a real listener and the built assembly. Same root cause as R-BH9. |
| R-EC2 | medium | patch | The platform's Redis-port environment override survives wrapper setup and can turn a ready private runtime into an exit-zero prerequisite skip. Same root cause as R-BH6. |
| R-EC3 | low | reject | TCP permits fragmented PONG reads, but the seven-byte reply is a single local Redis write inside private loopback networking. A new accumulation loop addresses an unlikely condition in this environment. |
| R-EC4 | low | reject | TCP permits partial request-line reads, but this short pinned-client request runs on local loopback; prior 25-run evidence also passed. Accumulation and framing changes add complexity for an unlikely test transport condition. |
| R-VG1 | medium | patch | Pre-verified regression gap: replacing the wrapper's child-status return with zero leaves all four maintained tests green. Execute a real failing child and assert both the wrapper status and recorded command status. |

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

### Initial follow-up patch verification (2026-10-23)

All fourteen accepted code-review patches P1–P14 below are implemented. The final
Release warnings-as-errors solution build passed with zero warnings/errors;
all 196 Manifest tests passed with zero skips. Four maintained runtime-tool tests
passed in the discovery CI lane's command, single-smoke discovery remained exact,
and the missing-helper restore test passed under `LANG=fr_FR.UTF-8`. The maintained
bootstrap recreated and hash-verified all four native binaries from real pinned
images. The maintained isolated wrapper passed the strengthened wrong-key JWT
smoke: one executed, one passed, zero skipped in 18.378 seconds, with two HTTP 401
rejections and the successful authenticated document. All four owned private
infrastructure processes exited 0; existing user AppHosts were preserved.

Patch-to-test mapping and sanitized receipts are in
`evidence/story-4-12/review-patches-20261023/README.md`. The historical publication
packet remains unchanged. The platform lock deferral remains already tracked
(`deferred-work.md:589`); the mandatory outer deadline remains documented and used.
Parent review subsequently classified all 15 findings individually above. The
seven surviving patch groups are resolved: explicit optimized-Python guards,
SIGTERM extraction cleanup, private Redis probe pinning, direct AppHost isolation,
occupied-Sentry test handling, daemon-exit rejection and real child exit-code
propagation. Final parent restore, Release build, six non-live suites (1,479
passed, five existing skips), nine Python tests and exact smoke discovery passed.
The final isolated live run passed without skips in 17.483 seconds under
`PYTHONOPTIMIZE=1` and an inherited Redis-port override. Sanitized final receipts
are in `evidence/story-4-12/review-patches-20261023/final-verification/`.

### Review Findings (code review, 2026-10-23)

Code review 2026-10-23 of the committed story range `be89509..3196d3d` (`e5ed21a`, `3196d3d`).

- **Code-only scope:** excludes `_bmad-output/` and the `references/Hexalith.Builds` gitlink move. The Parties helper source (`parties@dc95a640`, published as 1.6.0 through its own gates) is not in scope.
- **Size and mode:** 29 files, +1,600/−7, 1,876 diff lines, full mode, with `epic-4-context.md` as context.
- **Layers:** Blind Hunter (BH), Edge Case Hunter (EC), Verification Gap (VG) and Acceptance Auditor (AA). No layer failed.
- **Result:** 53 normalized findings (BH 19, EC 20, VG 5, AA 9). 29 survive as 3 decision-needed and 11 patch entries; 24 are rejected. Nothing is deferred. The user resolved all three decisions on 2026-10-23 with the recommended option, so they became P12–P14.

Parent checks during triage:
- Platform sources at `v3.126.1`:
  - `AspireTopologyFixtureBase` probes `docker info`, Redis, placement and scheduler. On failure it skips with "Aspire topology prerequisites are missing. Start Docker Desktop…".
  - The base `Client()` calls the base `SkipIfUnavailable`.
  - `SendTranslatingAsync` turns `HttpRequestException` into `EventStoreGatewayException(503)` and rethrows caller-cancelled `TaskCanceledException` unchanged.
- `Aspire.Hosting.Testing` 13.6.3 reports "The entry point exited without building a DistributedApplication." `AppHostDirectory` comes from the compiled `apphostprojectpath` metadata.
- Gateway configuration and topic override:
  - The root EventStore `appsettings.json` holds `EventStore:Publisher:TopicOverrides:global-administrators = tenants.events`.
  - `EventPublisherOptions.TopicOverrides` defaults to empty.
  - `HexalithTenantsServerExtensions` documents that the consuming AppHost sets this override on the Gateway, and the Tenants AppHost does so (`Program.cs:60`).
- `git -C <symlinked-parent>/repo rev-parse --show-toplevel` prints the physical path, and `--show-prefix` prints an empty line.
- Under `LANG=fr_FR.UTF-8`, `dotnet restore` prints NU1101 in French ("Package … introuvable").
- `ForbiddenGatewayReportsImmediateContextAndPinnedException` passed 25 of 25 isolated runs.
- The final evidence shows the Manifest suite at 30.7 s. `Hexalith.McpCli.Integration.Tests/obj/project.assets.json` resolves `Hexalith.EventStore.Server`, `.DomainService` and `.ServiceDefaults` 3.126.1.
- The root submodule checkouts equal their gitlinks. CI runs only on `ubuntu-latest`.

- [x] [Review][Patch] P12 (resolved from DN1; user chose option 1, the wrapper sentinel) — medium. The isolated runtime is mandatory only in the README.
  - `statestore.yaml` and `pubsub.yaml` target `localhost:6379` with `keyPrefix: name`, so keys use the shared app IDs.
  - The fixture checks the CLI, the mTLS variables, Sentry and the basic probes, but nothing ties the run to `run-isolated.py`.
  - On a host with Sentry and credentials configured, a direct DLL run reads and writes a stopped user topology's state in host Redis. The conflict check sees only running app IDs.
  - Options: (1) the fixture fails unless a sentinel set by the wrapper is present, with a refusal test; (2) give the test components a private Redis DB index (`redisDB`) so a host run cannot collide with DB 0; (3) keep documentation-only, relying on the mTLS/Sentry gating. Recommended: (1) (AA, BH, EC).
- [x] [Review][Patch] P13 (resolved from DN2; user chose option 1, pin and document) — medium. The Integration.Tests closure adds unguarded EventStore server packages.
  - The spec-mandated platform fixture root `Hexalith.EventStore.Testing.Integration` (already in `testPackages`) brings `Hexalith.EventStore.Server`, `.DomainService` and `.ServiceDefaults` 3.126.1 into a McpCli project for the first time.
  - Only the AppHost closure is tested, so a later platform bump can add implementation packages with no test failing.
  - The "Never import server … packages" constraint and the "reuse the platform fixture" approach conflict here.
  - Options: (1) add a Manifest test pinning the exact `Hexalith.*` package set of the Integration.Tests restore, and name this test-only platform closure in the README; (2) accept it as recorded evidence only; (3) treat it as a violation and stop using the platform fixture. Recommended: (1) (AA).
- [x] [Review][Patch] P14 (resolved from DN3; user chose option 1, move to `tools/` now) — medium. The supported live command runs tools from the dated evidence folder.
  - `README.md:246` and the bootstrap link execute `_bmad-output/…/expanded-publication/private-runtime/run-isolated.py` and `bootstrap-runtime.py`.
  - Stories 4.13 and 4.14 must reuse and evolve them, but editing them changes retained, hash-referenced evidence, and no gate checks them.
  - Options: (1) move the wrapper, bootstrap and `binaries.json` to a maintained location such as `tools/live-topology/`, keep the evidence copies, and point the README there; (2) leave them until 4.14 wires the lane and record a ledger deferral. Recommended: (1) (AA, BH).
- [x] [Review][Patch] P1 — medium. The Gateway lacks the `global-administrators` → `tenants.events` topic override.
  - Moving the Gateway content root to the AppHost directory (`:48`) skips the root EventStore `appsettings.json`, which carries that override. The code default is empty.
  - The Tenants helper requires the consuming AppHost to set it.
  - `global-administrators` events would therefore go to the default topic, which Tenants does not subscribe to. The `ListTenants` smoke cannot see this; 4.13 command vectors will.
  - Fix (configuration only, no module branch): add a `Gateway:TopicOverrides` section to `appsettings.json`, map it generically to `EventStore__Publisher__TopicOverrides__<domain>`, and assert it through P2's inspection (BH). [tests/Hexalith.McpCli.AppHost/Program.cs:48]
- [x] [Review][Patch] P2 — medium. Composition inspection omits most of the composed settings.
  - `Topology:InspectComposition` records only token length, hash and match, the sidecar config and the Gateway content root. It omits:
    - the `EventStore__DomainServices__Registrations__*` values;
    - the JWT issuer, audience, algorithm, `RequireHttpsMetadata` and signing-key match (as a hash);
    - the Gateway sidecar HTTP port;
    - each resource's resolved project path.
  - Deleting the route loop or changing the issuer leaves every CI test green; only a manual live run fails. Nothing pins the root source the helpers launch.
  - Fix: extend the snapshot with these non-secret values and assert them in `ComposedResourcesKeepTokensAclAndGatewayContentRoot` against the fixture's values and `_root/references/<module>/src/<module>/<module>.csproj` (VG, BH, AA). [tests/Hexalith.McpCli.AppHost/Program.cs:100]
- [x] [Review][Patch] P3 — medium. The fixture's basic-prerequisite branch is never exercised.
  - The `basic` row has a null `expected`. With nothing on Sentry's fixed port 50001 (CI and `dapr init`), `GetFailureAsync` returns the Sentry failure first, so `AspireTopologyFixture.cs:37-41` never runs.
  - Removing that branch, or changing the Sentry port, leaves every case green.
  - Fix:
    - Split the row. A `sentry` row asserts the exact `Dapr Sentry is not reachable on localhost:50001.`.
    - A basic row keeps 50001 reachable (bind a listener, or reuse an existing one) and uses the reserved placement and scheduler port. It asserts the "Basic platform…" detail and `DoesNotContain("Dapr Sentry")`.
  - VG reproduced the Sentry skip; the parent confirmed the order (VG, AA, BH, EC). [tests/Hexalith.McpCli.Manifest.Tests/DaprPrerequisiteTests.cs:14]
- [x] [Review][Patch] P4 — medium. A missing root checkout fails the live fixture without the required path.
  - In-process, the AppHost writes the path to stderr and returns 2.
  - `DistributedApplicationTestingBuilder` then fails with only "The entry point exited without building a DistributedApplication.", contrary to the "fail before launch with the required path" matrix row.
  - Fix: the fixture calls `TopologyConfiguration.ValidateWorkspace(RepositoryProjectPaths.GetRepositoryRoot())` before `base.InitializeAsync`, with an executable test asserting the message (AA, EC). [tests/Hexalith.McpCli.Integration.Tests/AspireTopologyFixture.cs:42]
- [x] [Review][Patch] P5 — medium. The exit-2 filter's `JsonException` and `Win32Exception` clauses are unprotected.
  - Every launch test reaching Dapr feeds valid JSON through the stub on `PATH`.
  - Removing either clause stays green, while a missing `dapr`/`git` or non-JSON `dapr list` output would crash with a stack trace.
  - Fix: add `TopologyLaunchTests` cases for non-JSON stub output and a `PATH` without `dapr`, asserting the exit code, empty stdout and the exact stderr (VG). [tests/Hexalith.McpCli.AppHost/Program.cs:30]
- [x] [Review][Patch] P6 — medium. Several `CheckAspireHelperClosure` branches have no test.
  - Untested: an unresolved transitive dependency (`:272-275`), a transitive project node, an unapproved transitive `Hexalith.*.Aspire` package (the `!policy.TestPackages.Contains(id)` clause), and `LoadFailures` pass-through.
  - Removing any of them keeps the gate green, although it backs AC1's server-free closure claim.
  - Fix: add `AspireHelperDependencyTests` cases with exact messages (BH). [tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyGate.cs:272]
- [x] [Review][Patch] P7 — medium. The invalid-credential probe does not exercise JWT signature validation.
  - `Bearer invalid-token` is not a JWT, so it gets a 401 even with signature, issuer and audience validation disabled. The README's "JWT validation … stay enabled" is not demonstrated.
  - Fix: replace it with a well-formed token signed by a different key, keeping exactly two 401s before the one authenticated query. Verification needs the isolated live run (BH). [tests/Hexalith.McpCli.Integration.Tests/GatewaySmokeTests.cs:30]
- [x] [Review][Patch] P8 — low. Configuration read after the exit-2 boundary crashes instead of reporting.
  - A missing `Gateway:Routes:*:<field>` throws an unhandled `InvalidOperationException` (stack trace, no exit 2).
  - An empty value passes `??`. `Topology:PreflightOnly` returns before routes are read. A non-boolean `Topology:*` flag crashes the same way.
  - This is the pass-1 B1 defect left in neighbouring reads.
  - Fix: read and validate routes (`IsNullOrWhiteSpace`) and both flags inside the existing `try` before the preflight return, with launch tests asserting exit 2, empty stdout and exact stderr (VG, BH, EC). [tests/Hexalith.McpCli.AppHost/Program.cs:54]
- [x] [Review][Patch] P9 — low. The README omits the platform's Docker prerequisite and its different skip text.
  - The base fixture requires a healthy `docker info`. Without it the smoke skips with "Aspire topology prerequisites are missing. Start Docker Desktop…", not the documented `DAPR integration prerequisites are unavailable…`.
  - Docker is not listed as a prerequisite.
  - Fix: list Docker and both skip texts (AA, BH, EC). [README.md:251]
- [x] [Review][Patch] P10 — low. The README overstates the helper approval scope.
  - `Hexalith.Parties.Aspire` "is approved only for this test topology", but `testPackages` is a flat list that `CheckTestProjects` applies to every test project.
  - Fix: say it is an approved test package, and that the AppHost closure test pins its version and server-free closure (BH, EC). [README.md:97]
- [x] [Review][Patch] P11 — low. The NU1101 assertion only passes in English.
  - On a French-locale machine (`LANG=fr_FR.UTF-8`, reproduced) the restore prints the localized message and `MissingHelperRestoreCannotFallBackToWorkspaceOrGlobalPackages` fails.
  - Fix: set `DOTNET_CLI_UI_LANGUAGE=en` on the restore process (EC). [tests/Hexalith.McpCli.Manifest.Tests/AspireHelperDependencyTests.cs:70]

#### Rejected (code review, 2026-10-23)

- `false` — `HttpRequestException` after liveness loses the probe context (BH). `SendTranslatingAsync` turns it into `EventStoreGatewayException(503)`, which the probe catches.
- `false` — The probe reports a fake 503/200 and drops Title/Detail (EC). The status is the pinned client's documented one, and the wrapped inner exception carries the detail.
- `false` — The timeout message hard-codes "30 seconds" (BH). `GatewaySmokeBoundaryTests` pins both the message and `RequestTimeout`, so they cannot drift silently.
- `false` — The AppHost reads its configuration from the source directory, so the copies are unused and launch tests are not isolated (BH). This is Aspire's `apphostprojectpath` design, and the tests assert against the reported directory; no run reads a wrong file.
- `false` — The Manifest suite gets much slower (BH). The final run took 30.7 s, within the documented ~35 s.
- `false` — The Sentry endpoint has three disagreeing spellings (BH). All three name the same loopback port 50001, the wrapper binds it, and the probe connects; no divergent behavior is shown.
- `false` — The fixture's conflict check runs before the base lock, so a sibling fixture fails instead of waiting (BH). The spec requires reporting a conflicting topology, not waiting on it, and the private namespaces hide host fixtures.
- `false` — A symlinked `references/` parent passes `ValidateWorkspace` (BH). The physical `--show-toplevel` path differs from the lexical one, so it is rejected.
- `low` — A symlinked or 8.3 short-name ancestor rejects a legitimate checkout (VG, EC). Confirmed, but CI and the team's setups are Linux/WSL. A correct fix must also keep rejecting a linked `references/` ancestor, which is more than swapping the comparison.
- `low` — `ValidateWorkspace` accepts any self-rooted Git directory and never compares the gitlink (BH). Checkouts currently equal their gitlinks, and the source-ahead-of-helper skew is normal source-build behavior. The fix adds a gitlink probe.
- `low` — A stalled Gateway during the two 401 probes surfaces as a `TaskCanceledException` type mismatch (AA). JWT bearer rejects unauthenticated requests before routing, so this stall is unlikely, and the test still fails within 30 s. The fix adds a catch branch.
- `low` — The fixture hard-codes port 3501 and ignores `Dapr__GatewayHttpPort` (AA, BH, EC). The wrapper and README fix 3501, and the in-process AppHost rechecks the actual port. The fix adds parsing.
- `low` — The fixture's own conflict call has no test (BH). The AppHost's identical call is covered by `TopologyLaunchTests`. Reaching the fixture's call needs host Redis to answer PONG on 6379, which `DaprTestPrerequisites` hard-codes.
- `low` — `new`-hidden `SkipIfUnavailable` and `InitializeAsync` let the base `Client()` throw instead of skipping (BH, EC). The only caller skips first. The fix adds a guard.
- `low` — Helper versions and `Aspire.AppHost.Sdk/13.6.3` are pinned outside the policy file (BH). A version change fails the test loudly, which is the intended re-review signal. Sibling AppHosts pin the SDK the same way, and a drift check adds a guard.
- `low` — The Dapr version is checked only by the substring "CLI version:" (BH). A wrong version still runs and fails visibly. Comparing pins adds a guard.
- `low` — The shared ACL also grants peer `/api/v1/queries` and Gateway `/process` on non-target callees (BH). The extra grants reach routes those services do not expose, in a disposable topology. Per-callee configs add files and tests.
- `low` — Path and host resolution is duplicated, with bare `dotnet` in `TopologyLaunchTests` and `AspireHelperDependencyTests` (BH, EC). `dotnet` must be on `PATH` for the SDK restore anyway. The fix extracts a helper.
- `low` — `ValidateGatewayPort` probes only 127.0.0.1, so an `[::1]`-only listener slips through; it also runs twice (BH, EC). On Linux a dual-stack `[::]` listener is detected. The second call is harmless. The fix adds a probe.
- `low` — Non-`EADDRINUSE` bind failures are reported as "already in use" (EC). These are Windows reserved ranges or loopback misconfiguration, outside CI and the supported environment. The fix adds a branch.
- `low` — A port can be taken between the probe and daprd's bind (EC). This race is inherent to probing, and the platform's readiness bound still fails the run.
- `low` — `.gitmodules` or checkout I/O and permission errors crash instead of exiting 2 (EC). These are unlikely local states, and the fix widens the filter and needs tests.
- `low` — Inherited `GIT_DIR`, `GIT_WORK_TREE` or `GIT_INDEX_FILE` misdirect `git` (EC). No repository hook runs these tests, and the fix scrubs three call sites.
- `low` — Sentry reachable only on `::1` while the configuration names 127.0.0.1 (EC). The wrapper binds 127.0.0.1, and the fix adds address-specific probing.
- `maybe-false` (low if true) — The 403 boundary server's single read could leave body bytes unread and reset the connection (EC). It passed 25 of 25 isolated runs. Stress-running under parallel CI load would settle it.

### Review Findings (code review pass 2, 2026-10-23)

Code review 2026-10-23 of the full committed story range `be89509..d9dc31a` (`e5ed21a`, `3196d3d`, `c432b45`, `d9dc31a`).

- **Code-only scope:** excludes `_bmad-output/` and `references/`. 35 files, +2,575/−7, 2,880 diff lines, full mode, with `epic-4-context.md` as context.
- **Layers:** Blind Hunter (BH), Edge Case Hunter (EC), Verification Gap (VG) and Acceptance Auditor (AA). No layer failed.
- **Result:** 52 normalized findings (BH 19, EC 21, VG 5, AA 7). 17 survive as 10 patch entries and 1 defer; 35 are rejected. No decision is needed.

Parent checks during triage:
- With `MCPCLI_ISOLATED_TOPOLOGY=1` and no `dapr` on `PATH`, the built smoke exits 0 with `Skipped: 1`. With `-failSkips` it exits 1, reporting `[FAIL]` and `FAIL_SKIP : DAPR integration prerequisites are unavailable…`.
- The reusable `ci / build-and-test` job initializes every root submodule (`git -c submodule.recurse=false submodule update --init`). The repository's own jobs initialize only Builds. Manifest.Tests took 47.2 s in CI run `40000531511`.
- `ExistingSentryListenerDoesNotFailPrerequisiteRun` took 9.6 s, and 9.3 s pinned to one core, against its 30 s budget.
- The pinned `daprio/dapr` and `redis` values are registry digests: `docker pull` resolves them (`Digest: sha256:0ac4…`).
- The extracted `redis-server` links host `libssl.so.3`, `libcrypto.so.3`, `libz.so.1` and `libzstd.so.1`.
- `tools/live-topology/runs/` is not git-ignored. An empty `MCPCLI_ISOLATED_RUNTIME_DIR` resolves to the working directory.

- [x] [Review][Patch] P15 — medium. A skipped smoke inside the wrapper exits 0, like a pass. [README.md:248]
  - xUnit v3 exits 0 for a skip. With Docker stopped, the base fixture skips inside the wrapper, which then records `commandExitCode: 0` and prints `Command completed: exit 0`.
  - AC4 requires the recorded result to distinguish skipped, failed and passed proof; only a manual read of stdout does so today.
  - Fix: add `-failSkips` to both documented live commands (`README.md:248`, `tools/live-topology/README.md:31`). A skip then exits 1 and stays identifiable as `FAIL_SKIP` with the standard diagnostic (AA).
- [x] [Review][Patch] P16 — medium. `DaprPrerequisiteTests` depends on the real root source checkouts. [tests/Hexalith.McpCli.Manifest.Tests/DaprPrerequisiteTests.cs:79]
  - It runs the repository's Integration.Tests output with the isolation sentinel set. The fixture now calls `ValidateWorkspace` before any prerequisite probe (`AspireTopologyFixture.cs:37`).
  - On a checkout with only `references/Hexalith.Builds` initialized, which is the documented minimum for restore, all ten cases and `ExistingSentryListenerDoesNotFailPrerequisiteRun` fail with "Required root source project … is missing" instead of skipping. CI passes only because the reusable job initializes every root submodule.
  - Fix: run the child against a temporary root with declared, git-initialized stand-in checkouts, prepared once per test process. This follows the `TopologyFixtureLaunchTests` and `TopologyLaunchTests.PrepareSources` pattern (EC).
- [x] [Review][Patch] P17 — medium. Composition inspection omits settings that the live run depends on. [tests/Hexalith.McpCli.AppHost/Program.cs:134]
  - Omitted settings:
    - each sidecar's placement and scheduler addresses (the wrapper's private 6050/6060);
    - `ASPNETCORE_ENVIRONMENT` and `DOTNET_ENVIRONMENT`;
    - the empty `Authentication__JwtBearer__Authority`;
    - the statestore and pubsub component paths;
    - the cleared endpoint ports.
  - Dropping any of them keeps `ComposedResourcesKeepTokensAclAndGatewayContentRoot` green; only a manual live run fails. Without the placement and scheduler arguments, sidecars fall back to default addresses where nothing listens inside the namespace.
  - Fix: add these non-secret values to the snapshot. Pass `--Dapr:PlacementHostAddress` and `--Dapr:SchedulerHostAddress` in that test, and assert every value for all three resources (VG, BH).
- [x] [Review][Patch] P18 — medium. The wrapper's child deadline path is untested. [tools/live-topology/run-isolated.py:166]
  - The 900 s literal cannot be injected. No test covers the path from timeout through `stop_owned(child)` to `commandExitCode` 124.
  - This deadline is the guard for the tracked indefinite platform lock wait (`deferred-work.md:589`). Changing 124 to 0 would let a hung run pass, and all nine runtime tests would stay green.
  - Fix: move the deadline into a module constant, patch it in `wrapper_fixture`, and add a hung-child mode. It asserts exit 124, the recorded receipt, and that the real child was stopped (BH).
- [x] [Review][Patch] P19 — medium. The 10 s bounds on `dapr list` and `git rev-parse` are untested. [tests/Hexalith.McpCli.AppHost/TopologyConfiguration.cs:134]
  - Replacing `WaitForExit(10000)` with `WaitForExit()` (`:67`, `:134`), or removing `TimeoutException` from the `Program.cs:54` filter, keeps every test green. The Dapr stub delays only `--version`.
  - Fix: make the stub honor a delay for `list` and add a slow `git` shim. For both, assert exit 2, empty stdout and the exact "exceeded 10 seconds" stderr (VG, AA).
- [x] [Review][Patch] P20 — medium. Private-key cleanup and result withholding are untested. [tools/live-topology/run-isolated.py:190]
  - VG showed that deleting the `*.key` unlink loop, or copying `DAPR_CERT_KEY` into `result.json`, leaves all nine runtime tests green. `result.json` is the receipt copied into story evidence.
  - Fix: in the `success` fixture run, assert that `issuer.key` is gone and that `private-test-credential` appears in no run file except the child's own output (VG).
- [x] [Review][Patch] P21 — low. The runtime directory can resolve inside the checkout. [tools/live-topology/run-isolated.py:17]
  - When `MCPCLI_ISOLATED_RUNTIME_DIR` is unset, it falls back to the script directory. When it is empty, it resolves to the working directory; the root README command produces this when `$private_runtime` is unset in a new shell.
  - Runs then land in `tools/live-topology/runs/` or `runs/`, neither of which is git-ignored. They contain `outside.json`, `result.json`, certificates, logs, and Redis and scheduler data.
  - Fix: in `__main__`, refuse an unset or empty value with a clear message before creating anything, and add a test (BH, EC).
- [x] [Review][Patch] P22 — low. The private Dapr probe parses stdout before checking the exit code. [tools/live-topology/run-isolated.py:153]
  - A failing `dapr list` with empty stdout records `JSONDecodeError` instead of `Private Dapr registration probe exited N.`, and its stderr is never recorded. The `dapr-exit` fixture returns valid `[]`, which hides this.
  - Fix: check the exit code first, record a bounded stderr excerpt, and make the fixture return empty stdout (VG, BH, EC).
- [x] [Review][Patch] P23 — low. The README's live-smoke text contradicts the wrapper. [README.md:253]
  - It says the wrapper supplies the `DAPR_*` variables "with your local CA and issuer credentials". The wrapper actually reads fresh credentials from its private Sentry.
  - "On other platforms use an equivalent process deadline" (`:251`) implies portability. The wrapper is Linux-only (`unshare`, `/proc/self/ns`), and the fixture refuses to run without it.
  - It names Sentry at `localhost:50001`, but the configuration and wrapper pin `127.0.0.1:50001`.
  - Fix: correct these three statements (AA, BH).
- [x] [Review][Patch] P24 — low. The runtime requirements omit the host libraries that `redis-server` needs. [tools/live-topology/README.md:10]
  - The hash-pinned `redis-server` links host `libssl.so.3`, `libcrypto.so.3`, `libz.so.1` and `libzstd.so.1`, but the requirements say only "OpenSSL". A host without them fails with "redis exited before prerequisites were ready".
  - Fix: name the OpenSSL 3, zlib and zstd shared libraries in the requirements (BH).
- [x] [Review][Defer] D1 — low. The agent instructions do not describe the live-topology project and tools. [AGENTS.md:100] — deferred: agent-context edit, tracked under the Story 4.12 ledger heading.
  - `AGENTS.md:100` says a test project missing from the CI list is silently skipped. Integration.Tests is deliberately absent, and the `dotnet test` command that `AGENTS.md:99` prescribes fails for it outside the wrapper.
  - The CI `tools/live-topology` unittest check is not named, and the "about 35 s" figure for Manifest.Tests is now 47.2 s in CI (BH).

#### Rejected (code review pass 2, 2026-10-23)

- `low` — The fixture hard-codes port 3501 (VG, BH). Already rejected in pass 1: the wrapper and README fix 3501, and the AppHost rechecks the configured port. The fix adds parsing.
- `low` — The isolation refusal precedes the prerequisite probes, so a direct run on a host without Dapr fails instead of skipping (AA). This is the user's P12 choice: fail unless the wrapper sentinel is present. "Never report live acceptance" still holds; aligning the frozen matrix row would mean renegotiating the spec.
- `low` — A plain `dapr init` host cannot pass the smoke, because the topology uses a default-deny ACL with mTLS (AA). Under P12 and P14 the wrapper is the only supported environment, and it supplies Sentry and mTLS. Elsewhere the smoke refuses or skips and never claims success. Changing this would mean renegotiating the spec.
- `low` — Integration.Tests restores EventStore server packages, and the "Never" constraint text is unchanged (AA). This was accepted in P13 with a pinning test; the only remaining fix is a spec edit.
- `low` — The `[submodule]` section check in `.gitmodules` parsing has no test (AA). Git writes `path` keys only inside submodule sections, so the guarded case does not occur in practice.
- `low` — The outer wrapper exits on SIGTERM before the inner cleanup finishes (BH). This affects only a run that has already timed out. `timeout` still exits non-zero, and the inner supervisor finishes cleanup (the R-BH5 precedent).
- `low` — SIGTERM's `SystemExit` bypasses `except Exception`, leaving no exit code in `result.json` (EC). This affects only an interrupted run, which still exits non-zero; PID-namespace teardown kills the child. The fix adds signal handling.
- `low` — Up to about 90 s of startup plus the 900 s child deadline can exceed the 960 s outer deadline (EC). This needs both a hung child and slow startup; the full live run took 17.5 s. Either deadline ends in a non-zero exit.
- `low` — The mount namespace still shares `/tmp` and `~/.dapr`, including the platform lock (BH). The lock wait is the tracked `deferred-work.md:589` entry, which already requires an outer deadline. Redis, scheduler and certificate state are private. A private `/tmp` adds mount handling.
- `low` — The isolation check is only an environment variable (BH). This is the P12 sentinel the user chose; bypassing it needs a deliberate export. `DaprPrerequisiteTests` reserves the placement and scheduler ports, so its child cannot launch.
- `low` — The `daprd` version and presence are not verified (BH, EC). Already rejected in pass 1: a wrong or missing runtime fails visibly at readiness, and pinning adds a guard.
- `low` — One shared ACL file applies every allowed operation to all three targets (BH). Already rejected in pass 1: per-callee configs add files and tests for a disposable topology.
- `false` — The smoke never queries Parties (BH). The frozen task requires exactly one bounded query. Composition inspection asserts the Parties routes, and live Parties semantics belong to 4.13.
- `low` — The JWT negative cases omit expired, wrong-issuer, wrong-audience and `alg:none` tokens (BH). The topology sets only the issuer, audience and key values, which inspection pins. The validation rules are the platform's, and the wrong-key 401 proves they run.
- `false` — The closure tests pin only `Hexalith.*` packages, so a helper patch could add dependencies silently (BH). The Builds catalog pins helper versions exactly, and the identity assertion fails on any helper version change, which forces a re-review.
- `low` — Helper and fixture versions are C# literals outside the policy file (BH). Already rejected in pass 1: a Builds bump fails Manifest.Tests loudly, and the documented bump procedure runs that suite.
- `low` — The launch tests copy whole build outputs, and configuration still comes from the source directory (BH). Already rejected in pass 1: the copy moves the workspace root that `GetRepositoryRoot` derives. The suite ran in 47.2 s in CI.
- `low` — `GatewaySmokeProbe`'s caller-cancellation exclusion is untested, and the timeout test waits 30 s (BH). Removing the exclusion only changes the exception text of a run the caller already cancelled. The 30 s wait is the pinned shipped deadline.
- `low` — A symlinked ancestor makes a valid checkout fail (EC). Already rejected in pass 1.
- `low` — `.gitmodules` entries written as `Path =`, or with comments or trailing slashes, are misread (EC). Git writes the lowercase `path = ` form. The fix adds parsing.
- `low` — A listener bound only on `[::1]` to the Gateway port goes undetected (EC). Already rejected in pass 1.
- `low` — A guard that returns 2 under the testing builder surfaces only as "entry point exited without building" (EC). The fixture runs the runtime-dependent guards itself first. The remaining guards check checked-in configuration covered by `TopologyLaunchTests`, and the AppHost still writes its diagnostic to stderr.
- `low` — Setting both `PreflightOnly` and `InspectComposition` silently skips inspection (EC). These internal test flags are set only by tests, and the fix adds a branch.
- `false` — Missing or duplicate annotations make inspection crash (EC). Inspection is test-only, and a helper change that produces such a model should fail loudly; the composition test does.
- `false` — The 30 s budget for ten nested runs can be flaky (EC). Measured at 9.6 s, and 9.3 s pinned to one core; CI passed.
- `maybe-false` (low if true) — The 403 server's single read could reset the connection (EC). Same as pass 1: it passed 25 of 25 isolated runs.
- `low` — The wrapper runs `bin/` without re-verifying hashes (EC). Tampering needs write access to the user's own private directory, and a partial binary fails loudly at start.
- `low` — Sentry certificates could be read while still being written (EC). This narrow race fails loudly in mTLS, and every recorded live run passed.
- `low` — A network setup or `mkdir` failure before the `try` leaves no `result.json` (EC). It fails loudly with a traceback and a non-zero exit; moving it adds receipt handling.
- `false` — The bootstrap pulls by image ID, which fails with the classic image store (EC). The pinned values are registry digests: `docker pull` resolved them (`Digest: sha256:0ac4…`), so classic-store hosts can pull them too.
- `false` — A registry port in an image reference breaks the tag split (EC). `binaries.json` contains only `daprio/dapr` and `redis`, so no such reference is reachable.
- `low` — A timed-out `docker create` can orphan a container (EC). Already rejected in the follow-up review (R-BH3).
- `low` — A failed `docker cp` can leave a partial file (EC). The bootstrap exits non-zero and refuses to reuse the directory, and a partial executable fails loudly at start.

### Parent acceptance audit for review pass 2 (2026-10-23)

The parent inspected the combined story source diff from the preserved baseline
and checked the current evidence against all six frozen matrix rows. All tasks
and P15–P24 are complete. Current six-project verification passed 1,481 non-live
tests with zero failures and five existing unrelated skips; all 201 Manifest
cases ran. Twelve Python runtime tests and the fresh live smoke passed; the
live smoke had zero skips. Exact parent commands and counts are in
`evidence/story-4-12/review-pass-2-20261023/parent-verification/`.

| Matrix row | Executed covering checks |
| --- | --- |
| Qualified helpers and live services | `GatewaySmokeTests.AuthenticatedQueryReturnsSuccessfulDocument`: one pass in 17.941 seconds; two real 401 rejections and a successful authenticated document; all four private daemons exited 0. |
| Missing or forbidden helper | `AspireHelperDependencyTests` and actual helper/fixture closure checks passed in the 201-case Manifest run; package identities and dependency paths are asserted. |
| Missing or undeclared root checkout | Configuration and executable AppHost/fixture refusal tests passed; exact required paths are retained. |
| Missing Dapr prerequisites | The outer prerequisite tests passed with stand-in root checkouts; relocated output-only verification also passed. The separate `-failSkips` child exited 1 with the standard diagnostic and `FAIL_SKIP`. |
| Alive but unusable Gateway | Both real HTTP 403 and alive-but-stalled Gateway tests passed, including the shipped 30-second query deadline and exact diagnostic. |
| Conflicting user topology | Real occupied-port and Dapr-identity AppHost refusal checks passed; existing user AppHost identities stayed unchanged across the isolated live run. |

The frozen intent is byte-identical to the resumed HEAD. Historical publication
and upstream qualification packets remain intact. Workflow review follows this
audit; no new publication or dependency update was required.

### Workflow review of pass 2 implementation (2026-10-23)

All three context-free review layers returned before triage. Each of the thirteen
findings is classified separately below. The blind layer's arithmetic line is
not a finding. The packet conversion was independently reproduced with
`git -c core.autocrlf=true cat-file --filters`: its README hash changed from the
qualified bytes, although all 59 current worktree packet hashes still matched.

| Finding | Verdict | Route | Evidence and disposition |
| --- | --- | --- | --- |
| F-BH1 | low | reject | A deliberately substituted Git/Dapr shim can exit while a background descendant retains its pipes; the parent accepts the reproduced overrun. The installed `git rev-parse` and Dapr probe have no demonstrated such descendant, and the supported live process retains its outer deadline. Combining stream/process cancellation and descendant cleanup adds guards for an uncommon replacement-tool state. |
| F-BH2 | low | reject | Python's negative child return code becomes a different nonzero shell status, while the receipt preserves the actual negative return code. No failure becomes a success or skip. Signal normalization adds a branch for a child externally signaled inside the private namespace; the supported outer timeout already reports its own nonzero result. |
| F-BH3 | low | patch | Private-key deletion occurs after four potentially ten-second daemon shutdowns and can be preempted by the documented twenty-second outer kill allowance. Move deletion ahead of the slow shutdown loop and assert its ordering; services already loaded their credentials. |
| F-BH4 | low | patch | Current uncommitted validation has a canonical base revision but no source fingerprint. Add a current SHA-256 file map and reference it from the current verification record, leaving earlier checkpoints intact. |
| F-BH5 | low | patch | The root evidence README still presents the unpublished checkpoint as current. Prefix a current status/index and label the existing text historical without deleting it. |
| F-BH6 | medium | patch | Independent checkout filtering under `core.autocrlf=true` changes the frozen qualification README's byte hash. Mark the complete qualified packet byte-preserved, then verify all 59 hashes through checkout filters. No qualified file contents may change. |
| F-BH7 | low | reject | A legitimate listener on port 1024 makes the positive lower-bound test fail. This is uncommon on the supported Linux test environment; occupied-port rejection is already explicitly covered. Adding a skip/availability branch complicates the boundary test for that rare environment. |
| F-BH8 | low | reject | The two older synthetic-workspace Git initializers wait without a bound, unlike the new prerequisite fixture. An installed local `git init --quiet` stalling on task-owned temporary directories was not demonstrated; adding deadline and cleanup branches protects an unlikely test-environment condition. |
| F-BH9 | low | reject | Failed `unshare` startup leaves `outside.json` and its actual nonzero exit/console error without an inner result receipt. It creates no child topology and cannot establish live acceptance. New outer receipt handling adds lifecycle branches for a failure already diagnosed before launch. |
| F-BH10 | low | patch | Bootstrap deliberately refuses the incomplete directory left after a pull/extraction failure. Add an explicit instruction to select a fresh task-owned directory before retrying; preserve refusal to overwrite existing directories. |
| F-EC1 | low | reject | The same reproduced inherited-pipe issue affects the three-second CLI prerequisite check. The actual installed CLI was not shown to abandon pipe-owning children; the isolated run still has an outer deadline. New stream/descendant lifecycle handling addresses an uncommon substituted-tool state. |
| F-EC2 | low | reject | carried: R-BH3 already records Docker creating a stopped extraction container before its ID is returned. Termination during that same ambiguous-create interval has the same orphan outcome. Preserve the recorded rejection: new naming/recovery state is disproportionate for this rare extraction failure and no running user container is affected. |
| F-VG1 | low | patch | Trusted pre-verified removal control: deleting SIGKILL leaves all twelve runtime tests green because the current hung child handles SIGTERM. Add a real SIGTERM-ignoring child regression that requires forced termination and receipt/status 124. The existing fallback can use an internal grace-period constant to keep this regression short. |

Survivors have six separate root causes and all route to direct patches. No
intent gap, spec loopback, new deferral, dependency update or publication is
needed. Existing deferred items remain unchanged.

### Final review patch verification (2026-10-23)

All six surviving workflow-review patch groups are resolved. The two new runtime
regressions reject their corresponding SIGKILL-removal and cleanup-order
mutations. All fourteen Python checks pass. The parent's final maintained-wrapper
smoke passed one test without skips in 20.529 seconds; all four private daemons
exited 0, stderr was empty, and no private keys remained. All 43 current source
hashes match the verification map. Git checkout filtering under
`core.autocrlf=true` preserves all 59 qualified packet files and the packet index.

The Release build and all six non-live .NET suites passed against the same
unchanged .NET sources: 1,481 passed, zero failed, five existing unrelated skips.
No frozen intent, qualified packet contents, production dependency, gitlink,
inventory or vector changed in this resumed run. Final source-bound commands,
counts and sanitized runtime receipts are in
`evidence/story-4-12/review-pass-2-20261023/verification.json` and
`evidence/story-4-12/review-pass-2-20261023/parent-verification/`.

### Review Findings (code review pass 3, 2026-10-24)

Code review 2026-10-24 of the full committed story range `be89509..c1a3e46` (`e5ed21a`, `3196d3d`, `c432b45`, `d9dc31a`, `6646412`, `c1a3e46`).

- **Code-only scope:** excludes `_bmad-output/` and `references/`. 36 files, +2,819/−7, 3,130 diff lines, full mode, with `epic-4-context.md` as context.
- **Layers:** Blind Hunter (BH), Edge Case Hunter (EC), Verification Gap (VG) and Acceptance Auditor (AA). No layer failed.
- **Result:** 44 normalized findings (BH 13, EC 17, VG 6, AA 8). 11 survive as 8 patch entries; 33 are rejected. No decision is needed and nothing is deferred.

Parent checks during triage:
- At `v3.126.1`, `DaprTestPrerequisites` hard-codes Redis `6379` (`const int RedisPort`). Only `AspireTopologyFixtureBase` and `DaprDiagnostics.ResolveRedisPort` honor `HEXALITH_EVENTSTORE_TEST_REDIS_PORT`.
- `Aspire.AppHost.Sdk` 13.6.3 (`Sdk/Sdk.targets:76`) skips `AddReferenceToDashboardAndDCP` when `AspireUseCliBundle` is `true`. The AppHost `project.assets.json` has no Orchestration or Dashboard package. `~/.aspire/bundle` holds `dcp` and `dashboard`, and `aspire --version` reports `13.6.1`. The Builds catalog pins neither package. Story evidence records that the bundle was enabled to remove the ASPIRE010 suppression.
- Two EventStore `v3.126.1` base `appsettings.json` values have code defaults that match: `RateLimiting` (`PermitLimit 1000`, `WindowSeconds 60`) and `Publisher:PubSubName` (`pubsub`). The Gateway reads no `Gateway` section. Of the AppHost `Dapr` section it reads only `Dapr:DeclarativeSubscriptions`, which is absent there.
- `ExistingSentryListenerDoesNotFailPrerequisiteRun` took 9.1 s, and 8.9 s pinned to one core, including the P16 workspace copy (budget 30 s). CI run `40021086071` at `c1a3e46` passed.
- `private-runtime/README.md` in the evidence explains the veth pair: "The private veth pair supplies multicast-capable networking". The maintained `run-isolated.py` does not carry that explanation.

- [x] [Review][Patch] P25 — medium. The wrapper's environment handoff to the child is mostly unpinned. [tools/live-topology/run-isolated.py:58]
  - `inside()` sets three groups of variables:
    - the placement and scheduler port overrides and `Dapr__*` (`:58`);
    - `NAMESPACE`, `DAPR_CONTROLPLANE_TRUST_DOMAIN` and `DAPR_CONTROLPLANE_NAMESPACE` (`:77`);
    - `DAPR_TRUST_ANCHORS`, `DAPR_CERT_CHAIN` and `DAPR_CERT_KEY` (`:127`).
  - `TopologyPrerequisites.GetMtlsFailureAsync` and the platform's `DaprLocalEndpoints` consume these variables.
  - The `success` child prints only the Redis port, the isolation flag and `DAPR_CERT_KEY`. VG deleted `DAPR_CONTROLPLANE_TRUST_DOMAIN` and `DAPR_TRUST_ANCHORS` and changed the placement port to 50005; all 14 Python tests passed.
  - Fix: make the `success` child dump all six mTLS and control-plane variables and the placement, scheduler and Gateway port variables. Assert their exact values, or that they are non-empty for the certificates. Also assert that the placement and scheduler ports equal the `--port` arguments of the services recorded in `result.json` (VG).
- [x] [Review][Patch] P26 — medium. The wrapper's readiness failure guards are untested. [tools/live-topology/run-isolated.py:123]
  - Untested guards:
    - "Sentry exited before generating certificates" (`:123`);
    - "Private Sentry certificates were not ready" (`:125`);
    - "{name} exited before prerequisites were ready" (`:141`);
    - "Private prerequisite port {port} did not become reachable" (`:151`).
  - `wrapper_fixture` writes the certificates synchronously, `Daemon.poll` returns `None` until the child succeeds, and `Connection` always connects. VG removed both early-exit checks and all 14 Python tests passed.
  - Without the guards, a crashed daemon surfaces only after 40 s with a generic timeout, or the supervisor hangs until the outer 960 s deadline.
  - Fix:
    - Move the 40 s readiness bound into a module constant, following P18's `COMMAND_TIMEOUT_SECONDS`.
    - Add fixture modes for: Sentry exits early, certificates never appear, a daemon exits during readiness, and a port never connects.
    - For each mode, assert exit 1, the exact `result.json` error and that no `command.stdout.txt` exists (VG, AA).
- [x] [Review][Patch] P27 — medium. The fixture's broken-CLI prerequisite branch is untested. [tests/Hexalith.McpCli.Integration.Tests/TopologyPrerequisites.cs:27]
  - "Dapr CLI '--version' did not report an installed CLI." is never reached: the stub always prints `CLI version: test-fixture` and exits 0 for `--version` (`tests/fixtures/Topology.DaprStub/Program.cs:10`).
  - Removing the check makes a broken or foreign `dapr` fail later at `dapr list` instead of producing the standard skip.
  - Fix: let the stub fail `--version` under a test variable. Add a `DaprPrerequisiteTests` row asserting the standard skip prefix plus this exact detail, and update the nested `Total: 10` count (`DaprPrerequisiteTests.cs:131`) (VG, AA).
- [x] [Review][Patch] P28 — medium. `ValidateWorkspace`'s physical top-level comparison is untested. [tests/Hexalith.McpCli.AppHost/TopologyConfiguration.cs:76]
  - Every negative case fails earlier:
    - the forged `.git` file at git's nonzero exit, which uses the same message;
    - the sibling link at `LinkTarget`;
    - the alternate layouts at the missing project.
  - Removing the comparison stays green. Yet pass 1 rejected the "symlinked `references/` parent" finding precisely because this comparison rejects it.
  - Fix: add a `TopologyConfigurationTests` case in which `references` is a symlink to another directory, and assert the exact "is not its own Git working tree" message (AA).
- [x] [Review][Patch] P29 — medium. The contents of `statestore.yaml` and `pubsub.yaml` are unpinned. [tests/Hexalith.McpCli.AppHost/DaprComponents/statestore.yaml:9]
  - Composition inspection checks only each component's `LocalPath`. Nothing checks:
    - `redisHost: localhost:6379`, which must match the wrapper's private Redis;
    - `actorStateStore: 'true'`, `keyPrefix`, or the component names `statestore` and `pubsub` (the Gateway's `PubSubName` default is `pubsub`);
    - the `scopes`.
  - Dropping `parties` from `scopes` or flipping `actorStateStore` keeps CI green. Even the live `ListTenants` smoke cannot see the Parties scope.
  - The live-lane remainder of VG's finding belongs to Story 4.14 by the frozen spec.
  - Fix: rewrite both files as JSON, as `accesscontrol.yaml` already is, and add a content test modeled on `TopologyAccessControlTests` that also cross-checks the Redis port with `run-isolated.py` (BH, VG).
- [x] [Review][Patch] P30 — medium. The Aspire CLI bundle is an undocumented live prerequisite. [tests/Hexalith.McpCli.AppHost/Hexalith.McpCli.AppHost.csproj:4]
  - `AspireUseCliBundle=true` means DCP and the dashboard come from the developer's `~/.aspire/bundle`, not from Builds-pinned packages. That bundle is 13.6.1 here, while the SDK and hosting packages are 13.6.3.
  - Neither README lists the Aspire CLI among the live requirements. On a host without it, the documented live command fails at orchestration startup, and the discovery CI job cannot notice because building does not need DCP.
  - Fix: name the Aspire CLI bundle and its version in `README.md:251` and the `tools/live-topology/README.md:10` requirements. Moving DCP to Builds-pinned packages would be an upstream catalog change outside this patch (BH).
- [x] [Review][Patch] P31 — low. The maintained wrapper does not say why it creates the veth pair. [tools/live-topology/run-isolated.py:50]
  - `mcpcli0`/`mcpcli1` with `172.31.251.1/24` look unused. The qualification evidence says the pair supplies multicast-capable networking, so a maintainer reusing the tool in 4.13 or 4.14 could remove it and break the private topology.
  - Fix: add a one-line comment stating that purpose (BH).
- [x] [Review][Patch] P32 — low. The bootstrap leaves its pulled images in the host Docker store without saying so. [tools/live-topology/README.md:21]
  - The bootstrap pulls `daprio/dapr` and `redis` by digest and removes only its extraction containers. The README describes that cleanup but not that both images remain.
  - Fix: add one sentence noting that the images remain and naming the `docker image rm` cleanup for the two pinned references (BH).

#### Rejected (code review pass 3, 2026-10-24)

- `low` — The Gateway's AppHost content root drops the Gateway's own base `appsettings.json` (BH). At `v3.126.1` the RateLimiting and PubSubName code defaults equal the base values. The one setting that mattered, the topic override, was restored in P1 and is pinned by inspection. What remains is the MediatR licence log-level suppression. A separate content root would not restore base settings either.
- `low` — Readiness probes TCP ports while the `--healthz-port` flags go unused (BH). The flags give the three control-plane daemons distinct health ports in one namespace, so removing them is wrong. Every recorded live run passed TCP readiness, and health polling adds code.
- `low` — The host environment passes unfiltered into the private run (BH). A stray, fully specified `Gateway__Routes__*` in the caller's shell is uncommon, and partial routes already exit 2. An allowlist must still carry PATH, HOME and the .NET variables, which adds lifecycle code.
- `low` — `result.json` cannot tell a skip from a failure (BH, AA). Carried from P15: with `-failSkips` the recorded run directory keeps `command.stdout.txt` with `FAIL_SKIP` and the xUnit counts. Structured report parsing adds code.
- `low` — `MCPCLI_ISOLATED_RUNTIME_DIR=.` or another in-checkout path is accepted, and `runs/` is not ignored (BH). An unprepared path fails at the missing `bin/sentry`, before Sentry creates any key. A prepared runtime inside the checkout shows up as untracked. Refusing repository paths or requiring the receipt adds guards.
- `false` — The README's "server-free closure" claim is untrue because only `Hexalith.*` identities are pinned (BH). The claim and AC1 concern Hexalith implementation packages, which `CheckAspireHelperClosure` rejects. `Grpc.AspNetCore.Server` and the Keycloak hosting library are third-party, Builds-governed transitives, and the AppHost composes no Keycloak resource (the pass-2 rejection).
- `low` — The inspection snapshot omits the sidecar Dapr app ID (BH). The pinned helpers set the IDs, and any helper version change fails the identity pin. A changed ID fails the live run loudly at the ACL and routing.
- `low` — Nothing proves at run time that the default-deny ACL is enforced (BH). Inspection pins each sidecar's configuration attachment and mTLS. Earlier failed runs recorded real ACL 403s, and a negative live call extends the single-query smoke.
- `low` — `ExistingSentryListenerDoesNotFailPrerequisiteRun` hard-codes `Total: 10` (BH). A changed row count fails visibly, with the actual summary printed. Reflection-based counting adds code. P27 updates the number.
- `low` — A copied clone or a `git init`'d copy passes as the declared checkout (EC). Already rejected in pass 1 (gitlink comparison).
- `low` — A symlink inside the checkout passes (EC). Already rejected as R-BH7.
- `low` — A symlinked ancestor rejects a valid checkout (EC). Already rejected in passes 1 and 2.
- `low` — An inherited `GIT_DIR` or `GIT_WORK_TREE` misdirects `git` (EC). Already rejected in pass 1.
- `low` — A `<root>/<module>.slnx` would redirect the helper locator (EC). That file does not exist in the McpCli root, inspection pins every resolved project path, and the fix adds a guard.
- `low` — An `[::1]`-only listener on the Gateway port goes undetected (EC). Already rejected in passes 1 and 2.
- `low` — Failures outside the guarded block crash with a stack trace (EC). Workspace validation precedes helper composition. The checked-in `appsettings.json` is always present, and inspection-lookup crashes were rejected in pass 2. Widening the filter adds branches.
- `false` — An empty `Gateway:Routes` passes preflight and fails only live (EC). `ComposedResourcesKeepTokensAclAndGatewayContentRoot` asserts the exact registration set, so an empty or renamed section fails CI.
- `low` — The fixture hard-codes port 3501 (EC, VG). Already rejected in passes 1 and 2.
- `false` — The probe diagnostic hides the cause behind 200 or 503 (EC). Already rejected in pass 1: the inner exception carries the detail.
- `low` — A nonexistent or typo'd runtime directory creates a stray tree and fails late (EC). The resulting error names the missing `bin/sentry` path. A receipt check adds a guard.
- `low` — A failure in network setup or the certificate directory before the `try` leaves no receipt (EC). Already rejected in pass 2.
- `low` — `issuer.key` can be read while still being written (EC). Already rejected in pass 2.
- `low` — Startup plus the 900 s child deadline can exceed the outer 960 s (EC). Already rejected in pass 2.
- `low` — A `docker create` timeout or TERM before the container ID is captured orphans the container (EC). Already rejected as R-BH3 and F-EC2.
- `false` — The 30 s budget for the nested prerequisite run is flaky (EC). Re-measured after P16: 9.1 s, and 8.9 s on one core.
- `maybe-false` (low if true) — The 403 server's single read could reset the connection (EC). Already rejected in passes 1 and 2 (25 of 25 isolated runs).
- `low` — No test reaches the fixture's early conflict refusal (VG). Carried from pass 1. Reaching it needs a PONG on the hard-coded Redis `6379` (verified above) plus placement and scheduler listeners. The AppHost's identical check still refuses the conflict before any resource starts.
- `low` — Nothing checks that the root servers are built before launch (AA). An unbuilt checkout fails loudly within the platform's bounded readiness. The README build block is mandatory, and `WithCompiledProjectExecutable` would change the composition.
- `low` — Helper admission pins identity, not the content hash (AA). Only nuget.org is configured, and published versions are immutable there. A hash literal adds another value to maintain on every bump.
- `false` — The shared fixture's Tenants-only identity is a module-specific branch (AA). The fixture has no branch on module, and the claims serve the single required query. Parameterizing identities is Story 4.13 work.
- `low` — JWT validation is wired through configuration keys rather than the helpers (AA). The helpers require Keycloak resources, which the Never clause forbids. The remaining fix is spec wording.

### Parent acceptance audit for review pass 3 (2026-10-24)

The parent inspected the topology implementation and resumed code delta, checked
every execution task and all six frozen matrix rows, and independently verified
all 44 implementation hashes and 134 receipt-file hashes against the current
working tree. All 20 recorded validation commands exited successfully. The six
non-live suites passed 1,485 tests with five existing unrelated skips; every one
of the 205 Manifest cases ran. The isolated live smoke passed without skips,
rejected missing and wrong-key credentials, and returned the authenticated
document. All four private daemons exited 0, and no private keys remained.
Frozen intent and historical qualification packets remain unchanged. Exact
audit totals are recorded in `evidence/story-4-12/review-pass-3-20261024/parent-acceptance.json`.
Workflow review follows this audit.

### Workflow review of pass 3 implementation (2026-10-24)

All three context-free review layers completed before triage. Each of their
fifteen findings was classified separately before grouping. Four independent
root causes survive as direct patches; no intent gap, spec loopback, publication,
dependency update or new deferral is needed.

| Finding | Verdict | Route | Evidence and disposition |
| --- | --- | --- | --- |
| G-BH1 | low | patch | The new broken-CLI row covers nonzero exit only; the stub always prints the accepted version marker on zero exit. Add an exit-zero malformed-version row protecting the existing output-format predicate. |
| G-BH2 | low | reject | carried: pass-2 rejected the untested caller-cancellation exclusion. Removing it changes only the diagnostic for an already cancelled call; the caller still receives cancellation and the run fails. |
| G-BH3 | low | patch | Signing-key tests cover ASCII short and 32-byte inputs but not 31 bytes or a shorter multibyte string meeting the byte threshold. Direct boundary cases protect the specified UTF-8 byte rule. |
| G-BH4 | low | reject | A failing version probe loses its captured stderr, but retains the exact '--version' prerequisite diagnostic and standard skip. Additional result formatting/length handling addresses uncommon broken-tool failures and adds branches. |
| G-BH5 | low | reject | carried: pass-1 rejected Dapr version pin enforcement; the documented version is a prerequisite, and a wrong runtime fails visibly. A supported-version check adds a guard. |
| G-BH6 | low | reject | A missing Aspire bundle fails at the platform's orchestration startup. P30 explicitly documents the required bundle; reproducing platform bundle resolution in the fixture adds prerequisite logic for an unmet documented requirement. |
| G-BH7 | medium | patch | The actual outer entry point accepts an empty command, creates infrastructure and reports exit zero without a test. Refuse empty commands before any directory or namespace setup; cover both empty syntaxes. |
| G-BH8 | low | reject | An ip setup failure retains its command and exit status but hides captured stderr. This occurs before launch in an unsupported/failed namespace setup; adding a new exception/receipt boundary is disproportionate to this uncommon diagnostic loss. |
| G-BH9 | low | reject | A failing discovery process can leave stdout only in the redirected file, although stderr and the nonzero step remain visible. No actual failure of this fixed discovery invocation after a passing build was demonstrated; extra CI failure-handling branches address an uncommon diagnostic state. |
| G-BH10 | low | reject | The current source map explicitly binds exact uncommitted working-tree bytes, unlike the immutable upstream qualification packet. A different checkout's line-ending conversion can invalidate that historical snapshot; a repo-wide line-ending policy or normalized replacement would change the evidence model rather than directly correct this run. |
| G-EC1 | low | reject | carried: F-BH1 already records the reproduced inherited-output-descendant timeout overrun. Installed git/Dapr were not shown to abandon pipe-owning children; extra stream/descendant cancellation remains rejected and the supported run retains its outer deadline. |
| G-EC2 | low | reject | carried: R-BH3 and F-EC2 already record the ambiguous docker-create timeout/termination orphan. Exact recovery naming/state adds complexity for a never-started extraction container; no running user container is affected. |
| G-EC3 | low | reject | carried: R-BH4 already records the narrow exit-between-timeout-and-SIGKILL race. Namespace destruction still terminates private processes; independent shutdown recovery remains rejected. |
| G-EC4 | low | reject | carried: R-EC3 already records theoretical fragmented Redis PONG reads on private local loopback. An accumulation loop remains disproportionate for the short single-write reply in the supported environment. |
| G-VG1 | medium | patch | Trusted pre-verified gap: deleting outer '*command' forwarding leaves all fifteen Python tests green and permits success without a smoke. Exercise the configured public CLI through a controlled namespace launcher and real child, asserting its marker/output, receipt and nonzero status. |

- [x] [Review][Patch] P33 — Add the malformed exit-zero Dapr version-output row and update the nested theory count.
- [x] [Review][Patch] P34 — Pin 31-byte rejection and multibyte 32-byte signing-key admission.
- [x] [Review][Patch] P35 — Refuse empty outer wrapper commands before creating files or entering namespaces.
- [x] [Review][Patch] P36 — Exercise actual outer CLI command forwarding and exit propagation with a real child under the inert fixture.

### Final workflow-review closure (2026-10-24)

P33–P36 are resolved. The parent reviewed the final patches and reran fresh
restore, Release warnings-as-errors solution build, three bounded source-server
builds, six individual non-live suites, seventeen Python tests, exact one-smoke
discovery and the isolated live smoke. All checks passed: 1,490 non-live .NET
tests, zero failed and five existing unrelated skips; all 210 Manifest cases ran.
The live smoke passed one test without skips in 17.544 seconds, with two real
401 rejections before the authenticated document. All four private daemons
exited 0, no private keys remained, and all seven host Dapr applications were
preserved. Every frozen matrix row passed its executed checks.

The three independent review layers produced fifteen findings. Four direct
patches are complete and eleven findings were rejected, including six carried
earlier dispositions. No new work was deferred. Existing ledger entries remain
unchanged. Final commands, source bindings and sanitized results are recorded
in `evidence/story-4-12/review-pass-3-20261024/parent-final/verification.json`.
The earlier pass-3 implementation checkpoint remains unchanged and is superseded
by this final parent acceptance. Frozen intent and historical packets are intact.

### Review Findings (code review pass 4, 2026-10-24)

Code review 2026-10-24 of the full committed story range `be89509..3b17388` (`e5ed21a`, `3196d3d`, `c432b45`, `d9dc31a`, `6646412`, `c1a3e46`, `2a857e3`, `3b17388`).

- **Code-only scope:** excludes `_bmad-output/` and `references/`. 37 files, +3,047/−7, 3,364 diff lines, full mode, with `epic-4-context.md` as context.
- **Layers:** Blind Hunter (BH), Edge Case Hunter (EC), Verification Gap (VG) and Acceptance Auditor (AA). No layer failed.
- **Result:** 50 normalized findings (BH 24, EC 18, VG 4, AA 4). 7 survive as 4 patch entries and 2 defer entries; 43 are rejected. No decision is needed.

Parent checks during triage:
- At `v3.126.1`, `AspireTopologyFixtureBase.cs:127-128` appends `--Dapr:PlacementHostAddress=localhost:{PlacementPort}` and `--Dapr:SchedulerHostAddress=localhost:{SchedulerPort}` after `ExtraAppArgs`. The ports come from `HEXALITH_EVENTSTORE_TEST_PLACEMENT_PORT` and `HEXALITH_EVENTSTORE_TEST_SCHEDULER_PORT` (`DaprLocalEndpoints.cs:28`, `:31`).
- The repository root has no `NuGet.config`.
- Story 4.14 (`_bmad-output/planning-artifacts/epics.md:1477`) makes the integration project the blocking `aspire-test-project`.
- `subprocess.Popen([])` raises `IndexError`, which `inside()`'s existing `except Exception` records as exit 1.
- At `3b17388` the 17 maintained Python checks pass in 4.5 s, and the working tree is clean.

- [x] [Review][Patch] P37 — medium. The wrapper's daemon launch arguments and private network setup are unasserted. [tools/live-topology/run-isolated.py:83]
  - Tests read only the placement and scheduler `--port` values from `result.json`, and the fixture's fake `subprocess.run` ignores its arguments.
  - VG: removing `--tls-enabled` from placement, changing Sentry's `--trust-domain`, or deleting `ip link set lo up` leaves every Python and Manifest test green. A mismatch with `accesscontrol.yaml` (trust domain `public`, Sentry `127.0.0.1:50001`) appears only at the next manual live run, which Stories 4.13 and 4.14 depend on.
  - Fix: in `test_wrapper_pins_the_effective_child_environment_to_private_services`, assert the full `receipt['services'][name]['arguments']` of all four daemons, with `RUNTIME_DIR`, `run_dir` and the certificate directory substituted. Record the fake `run` calls and assert that the exact five `ip` commands precede the first daemon launch (VG).
- [x] [Review][Patch] P38 — low. The README says copied source directories are refused, but a copied clone passes. [README.md:232]
  - `ValidateWorkspace` rejects a checkout without its own `.git` and one whose physical top level differs. A clone copied or re-cloned into `references/<module>` has its own `.git` and top level, so it passes. Comparing the gitlink stays rejected (passes 1 and 3).
  - Fix (wording only): say the AppHost refuses missing, undeclared or linked checkouts and source directories that are not their own Git working tree, and that it does not compare the checkout with the recorded gitlink (AA, BH).
- [x] [Review][Patch] P39 — low. The README describes fixture skips that the mandatory wrapper does not produce. [README.md:251]
  - The wrapper checks Redis, Sentry, placement, scheduler and an empty `dapr list` before starting the child. A missing native binary or Dapr CLI therefore ends the run with `Private environment failed: FileNotFoundError: …` and exit 1 (`tools/live-topology/run-isolated.py:190`), before any smoke. The README documents only the fixture's skip texts.
  - Fix: add one sentence stating that a wrapper-level prerequisite failure ends the run with `Private environment failed: …` and exit 1 before the smoke, and that the skip diagnostics describe the fixture's own checks (AA).
- [x] [Review][Patch] P40 — low. The inner supervisor still records a passing receipt when it runs no command. [tools/live-topology/run-isolated.py:185]
  - After readiness, the `if command:` block falls through to `result['commandExitCode'] = 0` and `return 0`. P35 refuses an empty command only in the outer `__main__`; the `--inside` path forwards `sys.argv[4:]` unchecked. No public entry point reaches this branch, and no test covers it.
  - Fix: delete the `if command:` condition and the fallback at `:185-186`. An empty command then fails inside the existing `except` with exit 1 (AA).
- [x] [Review][Defer] D2 — medium. The live smoke runs in no CI job, so the composed topology and the fixture's token can regress while CI stays green. [.github/workflows/ci.yml:108] — deferred: already tracked by Story 4.14 (`_bmad-output/planning-artifacts/epics.md:1477`), which makes the integration project the blocking `aspire-test-project`; the frozen spec keeps the blocking tier there. No ledger entry was added because the planned story owns it (VG).
- [x] [Review][Defer] D3 — low. The "zero module-specific code" policy text does not exempt the live-topology test composition. [AGENTS.md:83] — deferred: agent-context edit, filed under the Story 4.12 ledger heading next to D1.
  - `tests/Hexalith.McpCli.AppHost/Program.cs:82` and `:85` call the Tenants and Parties server helpers. `TopologyConfiguration.cs:13` and `:16` list the three modules, and the smoke uses `ListTenantsQuery` with a Tenants-only identity.
  - The frozen spec requires this composition, and it has no per-module branch. However, an agent that follows `AGENTS.md:83` could report it as a violation or refuse later topology work (AA).

#### Rejected (code review pass 4, 2026-10-24)

- `low` — The fixture's conflict check (app IDs and port 3501) runs in no test (VG). Carried from passes 1 and 3. VG's new route moves the call ahead of `DaprTestPrerequisites.IsAvailable`. The host-run `basic` prerequisite row would then probe the real port 3501 and fail wherever a user sidecar holds it, so the fix also needs skip handling. Inside the wrapper, `dapr list` is verified empty and the network namespace is private, so the check cannot fire on the supported path; the AppHost repeats it anyway.
- `low` — The fixture hard-codes port 3501 (VG, BH, EC). Already rejected in passes 1–3.
- `false` — The helper closure gate ignores non-`Hexalith.*` packages, contradicting the server-free claim (BH). Already rejected in passes 2 and 3.
- `low` — Version literals live in C# tests instead of the policy file (BH). Already rejected in passes 1 and 2: a Builds bump fails Manifest.Tests loudly.
- `false` — Route validation checks only non-empty values, and a deleted `Gateway:Routes` fails only live (BH). Already rejected in pass 3: `ComposedResourcesKeepTokensAclAndGatewayContentRoot` asserts the exact registration set, including `AppId` and `MethodName`.
- `low` — One shared ACL file is not target-scoped (BH). Already rejected in passes 1 and 2.
- `false` — Parties is checked only for liveness, and neither head runs against the topology (BH). Already rejected in pass 2: the frozen task is one bounded query, and live module and head semantics belong to Story 4.13.
- `low` — The JWT negatives omit wrong issuer or audience, expiry and `alg:none` (BH). Already rejected in pass 2.
- `low` — A failure in network setup or in creating the certificate directory, before the `try`, leaves no `result.json` (BH, EC). Already rejected in passes 2 and 3.
- `low` — SIGTERM's `SystemExit` during the child wait leaves no `commandExitCode`, and the child is not stopped gracefully (BH, EC). Already rejected in pass 2.
- `low` — The wrapper does not verify the runtime directory, the binary hashes or the Dapr versions (BH, EC). Already rejected in passes 1–3.
- `low` — The mount namespace shares `/tmp`, so the platform lock can block the isolated run (BH). Already rejected in pass 2; the lock wait is tracked at `deferred-work.md:589`.
- `false` — The fixture's command line overrides the wrapper's `Dapr__PlacementHostAddress` and `Dapr__SchedulerHostAddress`, so the environment test pins unused values (BH). The fixture builds `localhost:{port}` from the port variables (verified above). The test pins both port variables and cross-checks them against the daemons' `--port`, so the effective addresses are pinned.
- `low` — `TopologyDaprComponentTests` matches a line of `run-isolated.py` with a regex (BH). A reformat fails the test loudly with its own message, which forces a recheck. A shared data file would add an artifact for three readers.
- `low` — Manifest.Tests adds real 30 s and 10 s waits and repeated output copies (BH). Already rejected in passes 1 and 2.
- `low` — The subprocess test helpers drop captured output on timeout and are duplicated with drift (BH). A timed-out test still fails. Duplication and the unbounded `git init` were rejected in pass 1 and as F-BH8, and a shared helper adds code.
- `false` — The nested prerequisite run's 30 s budget is tight (BH, EC). Already rejected in passes 2 and 3 (9.1 s measured). BH observed about 14 s while four review layers ran at the same time.
- `maybe-false` (low if true) — The 403 server's single read could reset the connection (BH, EC). Already rejected in passes 1–3 (25 of 25 isolated runs).
- `false` — The Gateway's AppHost content root loads the AppHost's settings, and the copied outputs are unused (BH). Already rejected in passes 1 and 3: the Gateway reads no `Gateway` section and, of `Dapr`, only the absent `DeclarativeSubscriptions`. No `appsettings.Development.json` exists.
- `low` — The exit-2 filter misses `IOException` and `UnauthorizedAccessException`, and `appsettings.json` loads outside it (BH, EC). Already rejected in passes 1 and 3.
- `false` — `MissingHelperRestoreCannotFallBackToWorkspaceOrGlobalPackages` proves only stock NuGet behavior (BH). The repository root has no `NuGet.config` with a workspace source. The actual AppHost restore is gated by `CheckAspireHelperClosure`, which rejects a project-type helper (`SourceHelperIsRejected`).
- `false` — The bootstrap never checks the `image` tags (BH). Images are pulled by digest, and each extracted binary's SHA-256 is verified; the tag selects nothing.
- `false` — `docker rm` with `check=True` in the `finally` hides the original error (BH). Python chains the original exception as `__context__`, and the traceback prints both.
- `low` — A `docker create` timeout or TERM before the container ID is captured orphans the container (BH, EC). Already rejected as R-BH3, F-EC2 and G-EC2.
- `low` — A symlinked ancestor rejects a valid checkout (EC). Already rejected in passes 1–3.
- `low` — `ValidateWorkspace` discards `git rev-parse` stderr, so a dubious-ownership refusal reads as "not its own Git working tree" (EC). The running user owns the checkouts, both locally and in CI. The fix adds a separate nonzero-exit diagnostic; the version-probe equivalent was rejected as G-BH4.
- `low` — Bind failures other than `EADDRINUSE` read as "already in use" (EC). Already rejected in pass 1.
- `low` — An `[::1]`-only listener on the Gateway port goes undetected (EC). Already rejected in passes 1–3.
- `low` — `.gitmodules` keys with other casing, trailing slashes or `./` are misread (EC). Already rejected in pass 2.
- `false` — The probe misreports synthesized statuses as HTTP statuses (EC). Already rejected in passes 1 and 3.
- `low` — A missing `git` or a denied symlink leaks the `cli` case's temporary directory (EC). Without `git`, the class fixture's `git init` fails before any case runs. Symlink denial occurs only on Windows, and CI runs on Linux.
- `low` — Sentry certificates could be read while still being written (EC). Already rejected in passes 2 and 3.
- `low` — A partial or `-LOADING` Redis reply aborts the run (EC). `-LOADING` cannot occur, because Redis starts with `--save ''`, `--appendonly no` and a fresh directory. Partial reads were rejected as R-EC3 and G-EC4.
- `low` — `stop_owned` raising inside the `finally` skips later stops and the `result.json` write (EC). It needs a process that survives SIGKILL for 5 s; R-BH4 and G-EC3 rejected the same cleanup-recovery state.

### Parent acceptance audit for review pass 4 (2026-10-24)

The parent inspected the full story implementation diff and the resumed P37–P40
patches, verified every execution task and all six frozen matrix rows, and
checked the exact six-file implementation checkpoint map. Fresh source-server
builds and all six non-live suites passed: 1,490 .NET tests, zero failures and
five existing unrelated skips; all 210 Manifest cases ran. All eighteen Python
checks passed normally and under optimization, and all four removal/change
controls failed at their target assertions. The isolated live smoke passed
without skips in 22.094 seconds, rejected missing and wrong-key credentials,
and returned the authenticated document. All four private daemons exited 0;
no private keys remained; all seven host Dapr applications kept their identities
and ports. The reused native binaries matched their pinned SHA-256 values.

Current source binding, exact commands and the executed matrix mapping are in
`evidence/story-4-12/review-pass-4-20261024/parent-acceptance/verification.json`.
Frozen intent, dependency pins, gitlinks, inventories, vectors and ledger entries
remain unchanged. Workflow review follows this audit.

### Workflow review of pass 4 implementation (2026-10-24)

All three context-free review layers completed before triage. The verification
reviewer found no new gaps. The blind layer returned ten findings (its arithmetic
line is not a finding); the edge-case layer returned three. Each finding was
classified separately before grouping. Three independent direct patches survive;
eight carried dispositions retain their earlier rejection. No intent gap,
spec loopback, dependency update, publication or new deferral is needed.

| Finding | Verdict | Route | Evidence and disposition |
| --- | --- | --- | --- |
| H-BH1 | medium | patch | The actual fixture-closure assertion filters `Hexalith.` with `Ordinal`, although NuGet graph identities are case-insensitive. A lowercase unreviewed transitive package is omitted. Use case-insensitive selection and a regression that injects an unreviewed mixed-case package into the real restored graph. |
| H-BH2 | medium | patch | The daemon stand-in records arguments but ignores `Popen` options. Removing `start_new_session=True` leaves tests green although cleanup calls `killpg(process.pid)`. Assert actual daemon launch options, including process-group ownership and effective environment. |
| H-BH3 | medium | patch | The successful wrapper test does not inspect all four shutdown results or stop calls. Stopping only scheduler can retain a passing test. Record daemon stop calls and require each owned daemon to stop with its final status recorded. |
| H-BH4 | low | reject | A daemon can exit during the bounded child wait, delaying failure until that wait returns. It still cannot produce accepted live proof: the post-command check rejects it and the outer deadline bounds the run. Continuous monitoring adds supervision branches for an uncommon crash after successful readiness. |
| H-BH5 | low | reject | carried: R-BH3, F-EC2 and G-EC2 already cover interruption or timeout after Docker creates a never-started extraction container but before its ID is captured. Recovery naming/state remains disproportionate; no running user container is affected. |
| H-BH6 | low | reject | carried: pass 2 rejected the same SIGTERM/SystemExit receipt gap. An interrupted run exits nonzero, the PID namespace ends its child, and private-key cleanup still runs. New interruption receipt handling remains unnecessary for acceptance. |
| H-BH7 | low | reject | An installed local `ip` command stalling before daemon launch was not demonstrated. The mandatory outer deadline already fails that run; adding per-command timeout guards addresses an uncommon substituted-tool or failed-kernel state. |
| H-BH8 | low | reject | carried: passes 2 and 3 rejected missing structured receipts for namespace/network/certificate-directory failures before the `try`. Such startup failures exit nonzero before any child topology can establish live acceptance; widening the lifecycle boundary adds branches. |
| H-BH9 | low | reject | carried: pass-4 code review rejected discarded Git stderr at the same physical-root check. The checkout diagnostic remains precise for supported owned checkouts; a separate bounded nonzero-exit diagnostic adds handling for uncommon ownership or corruption failures. |
| H-BH10 | low | reject | carried: F-EC1 already covers a substituted CLI exiting while a descendant holds its output pipes. Installed Dapr has not shown that behavior; stream/descendant cancellation adds lifecycle handling and the supported run retains its outer deadline. |
| H-EC1 | low | reject | carried: F-BH1 and G-EC1 already record the independently reproduced inherited-output-descendant overrun in Git/Dapr probes. The actual installed tools were not shown to abandon such children; extra stream/process cancellation remains rejected. |
| H-EC2 | low | reject | carried: R-BH3, F-EC2 and G-EC2 already record the same ambiguous Docker-create interruption orphan. New unique naming and recovery state remains disproportionate for a never-started extraction container. |
| H-EC3 | low | reject | carried: R-BH4 and G-EC3 already record the process-exit race between timeout and SIGKILL. Namespace destruction still terminates private processes; independent shutdown recovery remains rejected. |

- [x] [Review][Patch] P41 — Select Hexalith package identities case-insensitively and protect the real integration closure assertion with injected lowercase/mixed-case unreviewed packages.
- [x] [Review][Patch] P42 — Assert daemon process-group ownership and effective `Popen` launch wiring in the inert supervisor fixture.
- [x] [Review][Patch] P43 — Assert exact stop calls and final stopped status for all four owned daemons.

### Final workflow-review closure for pass 4 (2026-10-24)

P37–P43 are resolved. The parent inspected the three final review patches and
reran fresh restore, the Release warnings-as-errors solution build, all six
non-live suites, eighteen Python checks normally and under optimization, three
bounded root source-server builds, exact one-smoke discovery and the isolated
live smoke. All checks passed: 1,492 non-live .NET tests, zero failures and five
existing unrelated skips; all 212 Manifest cases ran. The single live smoke
passed without skips in 19.090 seconds, with two real 401 rejections before
the authenticated document. All four private daemons exited 0, no private keys
remained, and all seven host Dapr applications kept their identities and ports.

Three independent review layers produced thirteen findings: three direct patches
are complete and ten findings were rejected, including eight carried earlier
dispositions. No new work was deferred. Removal controls reject loss of daemon
process-group ownership and partial cleanup. Lowercase and mixed-case injected
transitives are rejected by the actual pinned integration closure assertion.

Current source binding, exact commands and sanitized results are recorded in
`evidence/story-4-12/review-pass-4-20261024/parent-final/verification.json`;
earlier checkpoints remain unchanged. Frozen intent, dependency pins, gitlinks,
production code, inventories, vectors and existing ledger entries are intact.

### Review Findings (code review pass 5, 2026-10-25)

Code review 2026-10-25 of the product chunk on `main` at `253b21b`, from baseline `be89509`. 38 files, +3,160/−8, 3,499 diff lines. Full mode, with `epic-4-context.md` loaded. Tracking files and `evidence/story-4-12/` were left for later runs.

Layers: Blind Hunter, Edge Case Hunter, Verification Gap, and Acceptance Auditor. None failed. Acceptance Auditor reported no acceptance miss.

- [x] [Review][Patch] The smoke probe's caller-cancellation guard is untested [tests/Hexalith.McpCli.Integration.Tests/GatewaySmokeProbe.cs:21]
  - `ExecuteAsync` wraps `OperationCanceledException` as the 30-second `TimeoutException` only when its own timer fired and the caller token is still active.
  - `GatewaySmokeBoundaryTests` never cancels the caller token. Dropping `&& !cancellationToken.IsCancellationRequested` still leaves those tests green, and an aborted smoke is then diagnosed as a hung authenticated query.
- [x] [Review][Defer] The authenticated smoke success path is not executed by normal CI [.github/workflows/ci.yml:126] — deferred: already tracked (`spec` pass 4 D2; Story 4.14 owns the blocking Aspire lane at `_bmad-output/planning-artifacts/epics.md`). No new ledger entry.
- [x] [Review][Defer] The isolated smoke can wait on the platform fixture lock in the shared temp directory [references/Hexalith.EventStore/src/Hexalith.EventStore.Testing.Integration/AspireTopologyFixtureBase.cs:203] — deferred: already tracked (`deferred-work.md:589`). No new ledger entry.

#### Rejected (code review pass 5, 2026-10-25)

- `false` — Default-deny omits `/project` and `/replay-state`, so an empty `items` page can pass the smoke. The frozen smoke is one `ListTenants` document, and pass 4's live run returned that document through this ACL. An empty page is a successful query on an empty store.
- `false` — `redisHost: localhost:6379` misses Redis bound to `127.0.0.1`. Pass 4's isolated smoke reached Redis with that pairing, and `TopologyDaprComponentTests` locks it.
- `false` — The fixture's `localhost:{port}` placement and scheduler arguments miss the IPv4 listeners. The same live smoke started the sidecars with those arguments and passed. `ComposedResourcesKeepTokensAclAndGatewayContentRoot` pins the effective addresses.
- `false` — The `mcpcli1` veth has no address, so host Docker cannot reach the private daemons. The child command runs in the same network namespace, and the daemons listen on `127.0.0.1` or `0.0.0.0` there. Docker is only the platform `docker info` probe.
- `low` — `DAPR_CERT_KEY` is copied into the Redis, placement, and scheduler environments. The key is a disposable per-run issuer key, and splitting those environments adds a second environment map.
- `low` — The wrapper does not rehash binaries or require Dapr CLI 1.18.2 and runtime 1.18.7. Carried from passes 1–3. Bootstrap already checks the four SHA-256 values, and a wrong CLI still fails inside the outer deadline.
- `false` — A timed-out `dapr list` in the wrapper has no bounded diagnostic. `TimeoutExpired` is caught, printed as `Private environment failed: …`, and written to `result.json`.
- `false` — A daemon that exits during a failing command is dropped. The wrapper keeps the command's exit code, and `ownedInfrastructureStopped` still records each daemon. The success-only raise is what stops a crash from hiding behind exit 0.
- `false` — `--inside` with an empty command raises `IndexError`. That path returns exit 1 and is pinned by `test_inner_wrapper_refuses_an_empty_command`. The public entry rejects an empty command before `unshare`.
- `false` — `ReadToEndAsync` then `WaitForExit` deadlocks on xUnit's synchronization context. The reads start before the wait, and this test host does not install a context that would resume them on the blocked thread. The missing `IOException` catch was already rejected in passes 1 and 3.
- `false` — The 30-second parent budget cannot cover the twelve prerequisite cases. Passes 2 and 3 measured that test at 9.1 s and 9.6 s. `git init` runs once in the fixture, and only the slow-CLI case waits, on a 3-second probe.
- `maybe-false` (low if true) — `return 0` after `RunAsync` hides a non-zero `Environment.ExitCode`. Nothing in this diff shows `RunAsync` setting that code and then returning. A thrown startup failure never reaches the return.
- `low` — The live fixture puts the signing key on the AppHost command line. The key is random and lasts one smoke. Moving it off `ExtraAppArgs` changes the platform fixture's only argument channel.
- `false` — `CheckAspireHelperClosure` allows non-`Hexalith` packages. The method comment and the tests limit the ban to non-package nodes and unapproved `Hexalith.*` packages. Carried from passes 2 and 3.
- `false` — `ValidateWorkspace` does not compare a checkout with its gitlink. `README.md` states that boundary, and the guard checks declaration, the project file, and that the directory is its own working tree.
- `false` — The root README expands `$private_runtime` without assigning it. The command comment points at the bootstrap that assigns it, and an empty `MCPCLI_ISOLATED_RUNTIME_DIR` exits before the smoke with an explicit message.
- `low` — `stop_owned` can throw on `SIGKILL` and skip `result.json`. Carried as R-BH4 and G-EC3. It requires the process to disappear between the grace timeout and `SIGKILL`.
- `low` — `ip` setup sits before the supervisor `try`, so a failure skips `result.json`. Carried as H-BH8. The process still exits non-zero before any live claim, and the outer deadline bounds a hung `ip`.
- `low` — Sentry certificate files can be read before the write finishes. Carried from passes 2 and 3. A stability loop is extra machinery for a write that the accepted live run completed.
- `false` — The bootstrap success line always says four binaries. `binaries.json` has four records, and a hash or copy failure raises before that line.
- `low` — A missing `appsettings.json` is loaded before the exit-2 catch. Carried from passes 1 and 3. The file ships with the AppHost, and a missing file already fails the process.
- `false` — An empty `Gateway:Routes` section passes preflight. The shipped file has the three routes, and `ComposedResourcesKeepTokensAclAndGatewayContentRoot` asserts that set.
- `low` — Setting preflight and inspect together skips inspection and returns 0. The launch tests pass one flag. Rejecting both adds a branch for a combination the supported commands do not use.
- `low` — A blank placement or scheduler address is passed through. The wrapper and the fixture set those addresses on the supported path.
- `low` — `FileNotFoundException` during composition is not exit 2. `ValidateWorkspace` already fails a missing checkout with exit 2 before resources are added.
- `low` — A bind-mounted checkout can pass the working-tree check. Reaching that state takes an extra mount, and a device-id comparison adds a new rule.
- `low` — A hung unauthorized query fails as `OperationCanceledException` rather than the probe's timeout text. The assertion still fails within 30 seconds and names the exception. A second wrapper adds a branch beside the authenticated probe.
- `false` — A missing graph root throws `KeyNotFoundException` instead of an admission failure. `RestoredDependencyGraph` always inserts `RootId`, and `MissingHelperHasAnExactDiagnostic` keeps that root.
- `low` — `git init` in the topology test setup has no timeout. Carried from pass 1. A local `git init` hang was not shown, and a timeout wrapper adds process-kill handling.
- `false` — `InvokeAsync` reads `ExitCode` before a killed host has exited. On timeout, `WaitForExitAsync` throws and the return that reads `ExitCode` does not run.
