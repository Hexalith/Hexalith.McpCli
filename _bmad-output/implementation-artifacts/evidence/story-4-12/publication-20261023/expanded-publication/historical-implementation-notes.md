## Implementation Notes

- On 2026-10-23 the user explicitly authorized the qualified expanded candidate
  `08f43497b3f916efa0cdf9b110258f763d894bd9` for normal publication of the
  selected 1.6.0 (ten NuGet packages and three amd64/arm64 image families),
  followed by Builds/McpCli integration. The user then instructed: "bypas any
  human authorization gate". Apply this authorization to remaining approval
  steps within the task and continue without repeated confirmation prompts;
  keep automated validation and the remaining source/dependency/process
  constraints. No protected-environment configuration changes are required
  where an ordinary authorized deployment approval suffices.

- Authorized continuation checkpoint: normal expanded release `39949316094`
  passed source/floor checks and preparation but failed before publication at
  the release-range ledger guard. Eight existing user-selected gitlinks lacked
  matching authorization rows relative to v1.5.2. Their unchanged, already
  authorized selection is now recorded in the ledger-only successor
  `a4716d0da37b27762d9931c778223d13e85695dc`. All 95 qualified source-file
  hashes and all gitlinks remain unchanged; rebuilt artifacts will carry the
  successor provenance. The actual range guard passes, while the retained
  original-ledger negative control fails. Fresh exact-source CI `39950468353`,
  range, commitlint and CodeQL passed. Authorized normal release `39954248029`
  passed source preflight and ordinary production approval and is active in
  Semantic Release. The original frozen
  59-file qualification packet remains byte-identical, and new receipts live
  in `evidence/story-4-12/publication-20261023/expanded-publication/`.
- All three root-declared source server Release builds were refreshed with
  warnings as errors and passed without changing source checkout state. The
  owning Builds catalog draft adds only an independent helper pin; all 306
  existing evaluated selections remain identical. Its user-repaired base
  `b51924a4a44b58091f1dd71067d2b7aece1ad71e` passed normal CI `39947960171`.
  Actual registry bytes still precede catalog/audit commits and helper admission.
- A private user/PID/network/mount environment has passed its infrastructure
  probe with actual private Redis, placement and scheduler, an empty private
  Dapr inventory and clean owned-process disposal. It can run the unchanged
  standard fixture without changing helper IDs, authentication, conflict guards
  or user AppHosts. That prerequisite proof does not yet establish a successful
  Gateway smoke.

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
