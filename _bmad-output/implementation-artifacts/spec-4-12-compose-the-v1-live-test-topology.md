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
