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
- [ ] Owning `/home/administrator/projects/hexalith/parties`:
  `src/Hexalith.Parties.Aspire/{Hexalith.Parties.Aspire.csproj,HexalithPartiesServerExtensions.cs,PartiesServerProjectMetadata.cs}`,
  `tests/Hexalith.Parties.Aspire.Tests/`, solution and release declarations —
  prepare and qualify the server-package-free helper using platform composition;
  release through the owning repository's normal gates.
- [ ] Owning Hexalith.Builds `Props/Directory.Packages.props` and required catalog
  audit files — enroll the actual published helper version without changing
  approved Contracts identities; integrate only the necessary root gitlinks.
- [ ] `tools/dependency-policy.json` and
  `tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyTests.cs` — admit the
  reviewed helper only for tests; preserve production and implementation-package
  rejection with meaningful negative cases.
- [ ] `tests/Hexalith.McpCli.AppHost/{Hexalith.McpCli.AppHost.csproj,Program.cs,appsettings.json,DaprComponents/}`
  — compose the three services, explicit Gateway routing, shared Dapr components
  and test authentication through helpers; validate root checkout membership.
- [ ] `tests/Hexalith.McpCli.Integration.Tests/{Hexalith.McpCli.Integration.Tests.csproj,AspireTopologyFixture.cs,AspireTopologyCollection.cs,GatewaySmokeTests.cs}`
  — share the standard fixture, prerequisite checks and Integration trait; issue
  one bounded authenticated query through the pinned Gateway client and assert
  a real successful document. Keep liveness separate from usability.
- [ ] `tests/Hexalith.McpCli.Manifest.Tests/TopologyConfigurationTests.cs` — protect
  root-only source selection and dependency/configuration guards with negative
  cases that fail when the guard is removed.
- [ ] `Hexalith.McpCli.slnx`, `.github/workflows/ci.yml`, `README.md` and
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

- Qualification checkpoint, 2026-10-23 11:34 UTC: the bounded shared-publisher
  backport `d9070aa0d43feb9e3359286bc797d2be65960727` is based on canonical
  `397c94a4e246c90b21cf408790fa0d55bf32d795`, changes only the 404 reader/tests,
  and passed normal Builds CI `39941850208` plus 138 local publisher contracts.
  The newer catalog/main/G-4 work remains unchanged; the main-based timed-out
  CI is preserved as historical evidence. Fresh normal submodule cloning
  resolves the backport without moving the catalog gitlink.
- The current expanded Parties candidate
  `08f43497b3f916efa0cdf9b110258f763d894bd9` preserves user main `4b87e814`
  and changes only the six execution/verification declarations. It passed
  exact-source CI `39943732687`, range `39943732055`, commitlint `39943732609`
  and CodeQL `39943732654`. Native blocking results are 5,798 passed, zero
  failed, three prerequisite skips; native Aspire results are 123 passed, zero
  failed, six existing health-suite skips. The concurrent-session isolation
  case passed in 3m45.109s. Skips do not establish live acceptance.
- The reviewable expanded-source packet is
  `evidence/story-4-12/publication-20261023/expanded-source-candidate/README.md`.
  It records the selected, still unpublished normal 1.6.0, exact source and
  dependency/output changes, current local `.4` helper qualification, complete
  gate evidence, corrected lockfile-pinned commitlint validation and the pending
  26-file McpCli diff. All independent non-live checks remain concrete:
  47 isolated-draft tests, 11 SDK-aligned executable checks and 139 actual-root
  Manifest tests passed without skips. Actual production pins and helper
  enrollment policy remain unchanged; McpCli remains uncommitted.
- Expanded-source publication has not been dispatched or approved: it requires
  the new authorization determined by the parent after the material user-source
  expansion. Actual publication/artifact review, Builds/catalog integration and
  a non-skipped McpCli live smoke remain pending. The latest read-only snapshot
  still contains conflicting user `eventstore` and `tenants` registrations;
  no user process was stopped, reused, restarted or reconfigured.

- Latest continuation checkpoint: the authorized source `a413dc7df41a98f9d02cd8fb823e544086520956`
  passed normal CI/range proof, but release `39931847401` failed before packing,
  tagging or publication because the pinned shared preflight rejected the new
  helper's NuGet index HTTP 404. The narrowly tested shared repair is upstream
  in Builds `e6d0cc245c43a109672b1b71e1768ef8e2cabbe0` (145 publisher contract
  tests passed; its normal CI is pending).
- A separate user `/pushall` advanced Parties to
  `8bc955b77d3e48dff809b258bd457407114c73f6`, adding Memories recovery/health,
  a Projections API extension and eight updated root gitlinks. The new source
  selects Aspire.Hosting 13.6.3 and other newer dependencies. The task preserves
  that work. Its release-tooling pin and qualification cleanup now produce
  candidate `0f336bd005dbed9e2e278bc1861dfc0fb2322a15`; fresh exact-source gates
  are pending. No expanded-source release was dispatched or approved. The
  materially changed candidate requires its own concrete release authorization;
  the earlier authorization remains evidence for the original prepared source.
- The expanded helper's unpublished local `.2` qualification and source-scope
  assessment are retained under `evidence/story-4-12/publication-20261023/`.
  The pending downstream draft has passed 47 non-live tests, with affected
  executable checks/discovery also verified on SDK 13.6.3 without CLI-bundle
  opt-out or warning suppression. Published-artifact review, catalog enrollment,
  McpCli integration and live acceptance are still pending. Two user AppHosts
  remain preserved, including a conflicting `eventstore` sidecar at the latest
  inspection.

- Current continuation checkpoint: exact-source Parties CI `39928383173`
  passed at `a413dc7df41a98f9d02cd8fb823e544086520956` (Tier 3: 123 passed,
  zero failed, six existing skips). Authorized normal release `39931847401`
  passed source and protected-environment gates but failed before publication:
  the shared NuGet version-floor reader rejected the new helper's index 404.
  The narrow Builds repair is `e6d0cc245c43a109672b1b71e1768ef8e2cabbe0`,
  with 145 publisher contract tests passing and an original-reader regression
  control failing. Builds CI `39934362740` is pending completion.
- User main then advanced to `8bc955b77d3e48dff809b258bd457407114c73f6`,
  adding the previously excluded Memories recovery runtime and eight root
  gitlinks. The six-file immutable-publisher pin repair was replayed without
  changing that work at `287aa8e0bc5a68d7845cd0eb0927519f7889b6b4`; its new
  exact-source CI is `39935258902` and its range gate already passed. The new
  Builds catalog changes the helper's Aspire.Hosting input from 13.6.1 to
  13.6.3. The expanded source requires qualification and the parent's release
  authorization-scope assessment before another release dispatch. No helper
  has been admitted to McpCli and nothing has been published by this story.
- The current read-only Dapr snapshot again contains a user `eventstore`
  registration (PID 3188860, HTTP 21238); both generated user AppHosts are
  preserved. Published APIs do not expose complete namespace/state/metadata
  isolation for this fixed-ID composition. Actual conflicting launches remain
  rejected; live McpCli acceptance remains unproved.

- Authorized continuation: the exact helper candidate was integrated upstream at
  `4449020abcc01080a2375c7141b39aa18913d4aa`, followed by focused CI repairs at
  `f2c1b1968c10b04ce5a5ef41685248b01c1da40b` and
  `ad44f1d433799b2e1ca37a0bdb722a2ecfe09c87`. The repairs select the exact UI
  label and install the pinned Dapr CLI needed by manifest qualification; safe
  exception diagnostics retain withheld private output. Build/test, UI,
  owner-publisher, declaration, BMAD and independent range gates passed. The
  first Aspire attempt failed one existing concurrent-session readiness test;
  both failed and superseded retry evidence are retained. A locally reproduced
  cold-start race was repaired by starting the two fixtures sequentially while
  retaining both live sessions, all original assertions and timeouts, at
  `a413dc7df41a98f9d02cd8fb823e544086520956`. Its exact-source CI run
  `39928383173` has passed build/unit, Tier 2, UI, publisher, declaration and
  BMAD; Tier 3 remains active. Its independent range and commitlint gates passed.
  Publication has not run.
- All three root source server Release builds passed with warnings as errors.
  The isolated AppHost/integration draft compiles, discovers exactly one smoke,
  and passed configuration and executable preflight checks. Root configuration
  guards are present in McpCli, with 27 guard cases passing. Helper admission,
  solution enrollment and live acceptance remain pending publication. Receipts
  live under `evidence/story-4-12/publication-20261023/`. Executed negative tests
  passed for helper refusal, actual Program root/auth/conflict preflight guards,
  a real alive-but-stalled Gateway with the 30-second request deadline, and the
  standard missing-Dapr skip result (the covering outer test passes without a
  skip). The earlier local Dapr app-ID conflict cleared independently without
  stopping user processes.

- On 2026-10-23 the user explicitly authorized the prepared upstream Parties
  normal release (ten NuGet packages and three multiarchitecture container
  families) through normal gates, followed by Builds/McpCli integration. This
  authorization overrides the build workflow's default no-push/no-remote rule
  for this scoped continuation; required CI, range, protected-environment and
  published-artifact checks still apply.

- Prepared the upstream Parties helper and its normal release declarations in
  `/home/administrator/projects/hexalith/parties`; no reference contents were
  edited. The task-only candidate is bound to upstream baseline
  `6c83309d08a10f36a0da866521b9d0da6f8fc998` by the file hashes and patch in
  `evidence/story-4-12/`.
- The local, **unpublished** artifact `Hexalith.Parties.Aspire` version
  `1.6.0-story412.1` passed isolated artifact/closure inspection and six source
  locator probes. It has only Aspire.Hosting 13.6.1 and
  Hexalith.EventStore.Aspire 3.126.1 as direct dependencies. This prerelease label
  identifies a local qualification artifact; it is not the normal release's
  version or proof of publication.
- Broader upstream qualification uses an isolated baseline-plus-task snapshot to
  exclude concurrent unrelated Parties runtime edits. Exact committed-source CI,
  the independent main-push range gate and protected release authorization remain
  required by the owning repository's normal release workflow.
- McpCli helper enrollment, Builds catalog changes and gitlinks, the test AppHost,
  fixture, smoke, guards and CI discovery remain pending the required upstream
  publication. Production Contracts pins, vectors and inventories are unchanged.
  No live Gateway smoke has run and live acceptance is not established.

## Spec Change Log

## Review Triage Log

## Verification

Local prerequisite qualification is recorded in
`evidence/story-4-12/README.md`, including the exact final source/patch/archive
hashes, all ten staged package identities, owning test receipts and the normal
publication/integration scope. The final fresh-cache helper qualification passed;
its restored archive hash equals
`95218af9fe9345fbf496602a5474e2d0c30c035ddc9b7778992996928601a73a`.
The owning tests required focused reruns after support-build and isolated-Git
setup corrections; their earlier failures remain in the evidence. Thirteen
upstream runtime tests were explicitly skipped. Publication and the new live
McpCli smoke have not run, so the story's acceptance criteria are not complete.


- Run owning-repository helper tests, package inspection and required release gates.
- `dotnet restore Hexalith.McpCli.slnx`
- `dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror`
- Run Manifest.Tests and each other existing test project individually in Release.
- `dotnet test tests/Hexalith.McpCli.Integration.Tests --no-build --configuration Release`
  — require a non-skipped successful smoke for acceptance. Retain timeout and
  prerequisite diagnostics separately from actual live success.
