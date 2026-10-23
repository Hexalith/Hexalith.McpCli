---
title: '4.12 Compose the v1 live test topology'
type: 'feature'
created: '2026-10-23'
status: 'in-progress'
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

- [ ] [Review][Patch] P12 (resolved from DN1; user chose option 1, the wrapper sentinel) — medium. The isolated runtime is mandatory only in the README.
  - `statestore.yaml` and `pubsub.yaml` target `localhost:6379` with `keyPrefix: name`, so keys use the shared app IDs.
  - The fixture checks the CLI, the mTLS variables, Sentry and the basic probes, but nothing ties the run to `run-isolated.py`.
  - On a host with Sentry and credentials configured, a direct DLL run reads and writes a stopped user topology's state in host Redis. The conflict check sees only running app IDs.
  - Options: (1) the fixture fails unless a sentinel set by the wrapper is present, with a refusal test; (2) give the test components a private Redis DB index (`redisDB`) so a host run cannot collide with DB 0; (3) keep documentation-only, relying on the mTLS/Sentry gating. Recommended: (1) (AA, BH, EC).
- [ ] [Review][Patch] P13 (resolved from DN2; user chose option 1, pin and document) — medium. The Integration.Tests closure adds unguarded EventStore server packages.
  - The spec-mandated platform fixture root `Hexalith.EventStore.Testing.Integration` (already in `testPackages`) brings `Hexalith.EventStore.Server`, `.DomainService` and `.ServiceDefaults` 3.126.1 into a McpCli project for the first time.
  - Only the AppHost closure is tested, so a later platform bump can add implementation packages with no test failing.
  - The "Never import server … packages" constraint and the "reuse the platform fixture" approach conflict here.
  - Options: (1) add a Manifest test pinning the exact `Hexalith.*` package set of the Integration.Tests restore, and name this test-only platform closure in the README; (2) accept it as recorded evidence only; (3) treat it as a violation and stop using the platform fixture. Recommended: (1) (AA).
- [ ] [Review][Patch] P14 (resolved from DN3; user chose option 1, move to `tools/` now) — medium. The supported live command runs tools from the dated evidence folder.
  - `README.md:246` and the bootstrap link execute `_bmad-output/…/expanded-publication/private-runtime/run-isolated.py` and `bootstrap-runtime.py`.
  - Stories 4.13 and 4.14 must reuse and evolve them, but editing them changes retained, hash-referenced evidence, and no gate checks them.
  - Options: (1) move the wrapper, bootstrap and `binaries.json` to a maintained location such as `tools/live-topology/`, keep the evidence copies, and point the README there; (2) leave them until 4.14 wires the lane and record a ledger deferral. Recommended: (1) (AA, BH).
- [ ] [Review][Patch] P1 — medium. The Gateway lacks the `global-administrators` → `tenants.events` topic override.
  - Moving the Gateway content root to the AppHost directory (`:48`) skips the root EventStore `appsettings.json`, which carries that override. The code default is empty.
  - The Tenants helper requires the consuming AppHost to set it.
  - `global-administrators` events would therefore go to the default topic, which Tenants does not subscribe to. The `ListTenants` smoke cannot see this; 4.13 command vectors will.
  - Fix (configuration only, no module branch): add a `Gateway:TopicOverrides` section to `appsettings.json`, map it generically to `EventStore__Publisher__TopicOverrides__<domain>`, and assert it through P2's inspection (BH). [tests/Hexalith.McpCli.AppHost/Program.cs:48]
- [ ] [Review][Patch] P2 — medium. Composition inspection omits most of the composed settings.
  - `Topology:InspectComposition` records only token length, hash and match, the sidecar config and the Gateway content root. It omits:
    - the `EventStore__DomainServices__Registrations__*` values;
    - the JWT issuer, audience, algorithm, `RequireHttpsMetadata` and signing-key match (as a hash);
    - the Gateway sidecar HTTP port;
    - each resource's resolved project path.
  - Deleting the route loop or changing the issuer leaves every CI test green; only a manual live run fails. Nothing pins the root source the helpers launch.
  - Fix: extend the snapshot with these non-secret values and assert them in `ComposedResourcesKeepTokensAclAndGatewayContentRoot` against the fixture's values and `_root/references/<module>/src/<module>/<module>.csproj` (VG, BH, AA). [tests/Hexalith.McpCli.AppHost/Program.cs:100]
- [ ] [Review][Patch] P3 — medium. The fixture's basic-prerequisite branch is never exercised.
  - The `basic` row has a null `expected`. With nothing on Sentry's fixed port 50001 (CI and `dapr init`), `GetFailureAsync` returns the Sentry failure first, so `AspireTopologyFixture.cs:37-41` never runs.
  - Removing that branch, or changing the Sentry port, leaves every case green.
  - Fix:
    - Split the row. A `sentry` row asserts the exact `Dapr Sentry is not reachable on localhost:50001.`.
    - A basic row keeps 50001 reachable (bind a listener, or reuse an existing one) and uses the reserved placement and scheduler port. It asserts the "Basic platform…" detail and `DoesNotContain("Dapr Sentry")`.
  - VG reproduced the Sentry skip; the parent confirmed the order (VG, AA, BH, EC). [tests/Hexalith.McpCli.Manifest.Tests/DaprPrerequisiteTests.cs:14]
- [ ] [Review][Patch] P4 — medium. A missing root checkout fails the live fixture without the required path.
  - In-process, the AppHost writes the path to stderr and returns 2.
  - `DistributedApplicationTestingBuilder` then fails with only "The entry point exited without building a DistributedApplication.", contrary to the "fail before launch with the required path" matrix row.
  - Fix: the fixture calls `TopologyConfiguration.ValidateWorkspace(RepositoryProjectPaths.GetRepositoryRoot())` before `base.InitializeAsync`, with an executable test asserting the message (AA, EC). [tests/Hexalith.McpCli.Integration.Tests/AspireTopologyFixture.cs:42]
- [ ] [Review][Patch] P5 — medium. The exit-2 filter's `JsonException` and `Win32Exception` clauses are unprotected.
  - Every launch test reaching Dapr feeds valid JSON through the stub on `PATH`.
  - Removing either clause stays green, while a missing `dapr`/`git` or non-JSON `dapr list` output would crash with a stack trace.
  - Fix: add `TopologyLaunchTests` cases for non-JSON stub output and a `PATH` without `dapr`, asserting the exit code, empty stdout and the exact stderr (VG). [tests/Hexalith.McpCli.AppHost/Program.cs:30]
- [ ] [Review][Patch] P6 — medium. Several `CheckAspireHelperClosure` branches have no test.
  - Untested: an unresolved transitive dependency (`:272-275`), a transitive project node, an unapproved transitive `Hexalith.*.Aspire` package (the `!policy.TestPackages.Contains(id)` clause), and `LoadFailures` pass-through.
  - Removing any of them keeps the gate green, although it backs AC1's server-free closure claim.
  - Fix: add `AspireHelperDependencyTests` cases with exact messages (BH). [tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyGate.cs:272]
- [ ] [Review][Patch] P7 — medium. The invalid-credential probe does not exercise JWT signature validation.
  - `Bearer invalid-token` is not a JWT, so it gets a 401 even with signature, issuer and audience validation disabled. The README's "JWT validation … stay enabled" is not demonstrated.
  - Fix: replace it with a well-formed token signed by a different key, keeping exactly two 401s before the one authenticated query. Verification needs the isolated live run (BH). [tests/Hexalith.McpCli.Integration.Tests/GatewaySmokeTests.cs:30]
- [ ] [Review][Patch] P8 — low. Configuration read after the exit-2 boundary crashes instead of reporting.
  - A missing `Gateway:Routes:*:<field>` throws an unhandled `InvalidOperationException` (stack trace, no exit 2).
  - An empty value passes `??`. `Topology:PreflightOnly` returns before routes are read. A non-boolean `Topology:*` flag crashes the same way.
  - This is the pass-1 B1 defect left in neighbouring reads.
  - Fix: read and validate routes (`IsNullOrWhiteSpace`) and both flags inside the existing `try` before the preflight return, with launch tests asserting exit 2, empty stdout and exact stderr (VG, BH, EC). [tests/Hexalith.McpCli.AppHost/Program.cs:54]
- [ ] [Review][Patch] P9 — low. The README omits the platform's Docker prerequisite and its different skip text.
  - The base fixture requires a healthy `docker info`. Without it the smoke skips with "Aspire topology prerequisites are missing. Start Docker Desktop…", not the documented `DAPR integration prerequisites are unavailable…`.
  - Docker is not listed as a prerequisite.
  - Fix: list Docker and both skip texts (AA, BH, EC). [README.md:251]
- [ ] [Review][Patch] P10 — low. The README overstates the helper approval scope.
  - `Hexalith.Parties.Aspire` "is approved only for this test topology", but `testPackages` is a flat list that `CheckTestProjects` applies to every test project.
  - Fix: say it is an approved test package, and that the AppHost closure test pins its version and server-free closure (BH, EC). [README.md:97]
- [ ] [Review][Patch] P11 — low. The NU1101 assertion only passes in English.
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
