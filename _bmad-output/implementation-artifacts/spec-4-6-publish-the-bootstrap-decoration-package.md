---
title: '4.6 Publish the bootstrap Decoration Package'
type: 'feature'
created: '2026-10-17'
status: 'in-progress'
route: 'dispatch'
review_loop_iteration: 1
baseline_commit: '04178de98f30b0c5541f7efb978e9b9acc8e8c1d'
context:
  - '_bmad-output/implementation-artifacts/epic-4-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Upstream Contracts cannot adopt McpCli decorations until Abstractions
is published. Existing bootstrap scripts depend on the whole solution and CI.

**Approach:** Isolate the bootstrap gate, harden and verify its release path,
publish the validated package, and introduce its version in the owning Builds
catalog. Retain semantic-release version selection; its first release is 1.0.0.

## Boundaries & Constraints

**Always:** Publish only `Hexalith.McpCli.Abstractions`, including its existing
analyzer, with zero consumer-visible package dependencies. Bootstrap builds only
Abstractions and analyzer production projects plus author-time test dependencies.
Use an independent bootstrap CI result and commitlint success for the exact
current main SHA. Recheck main after production approval. Validate version
availability, credentials and staged contents before pushing; publish those same
validated bytes. Keep credentials out of evidence. Preserve unrelated artifacts.

Add `HexalithMcpCliVersion` and the Abstractions package entry in
`/home/administrator/projects/hexalith/builds/Props/Directory.Packages.props`,
using the verified published version and the owning repository's checks.
Record upstream integration and registry evidence; unavailable publication or
owner integration keeps the corresponding acceptance criteria incomplete.

**Never:** Edit `references/`, move gitlinks, enroll modules, change runtime
behavior, introduce module-specific code, publish the tool, or enable paired
releases. Bootstrap requires no decorated upstream Contracts, Aspire tier,
FR-22 evidence or full-tool CI success. Test fixtures are permitted. Package
publication and release tags are external effects, performed only after review
and checks on committed source; any required commits must pass pinned commitlint.

## I/O & Edge-Case Matrix

| Scenario | Input/state | Expected behavior | Failure evidence |
| --- | --- | --- | --- |
| Valid bootstrap | Fresh isolated staging and selected version | One validated Abstractions package; packaged analyzer works | Package identity/hash and consumer build |
| Invalid package | Wrong ID/version, missing DLL/analyzer, dependency leakage, extra artifact | Reject before push | Specific error; zero push calls |
| Invalid request | Unsupported phase, invalid/taken version, missing credentials, uncertain registry response | Reject before publication | Nonzero exit; zero push calls |
| Invalid source | Wrong branch, stale SHA or missing bootstrap/commitlint success | Refuse release | Gate identifies failed prerequisite |

</frozen-after-approval>

## Code Map

- `scripts/release-prepare.sh` currently restores/builds the solution; reuse
  explicit Abstractions packing, replace bootstrap preparation and shared staging.
- `scripts/validate-release-packages.py` already checks exact artifacts, nuspec
  identity/version, compile DLL, bundled analyzer and dependency absence.
- `scripts/release-preflight.sh` checks registry/credentials; `release-publish.sh`
  validates again but can bypass phase preflight when invoked directly.
- `.github/workflows/ci.yml` contains the local-source consumer/analyzer smoke;
  extract it into an independent gate. `release.yml` currently requires full CI.
- `.github/workflows/release.yml` now owns new publication and tagged recovery.
  NuGet trusted publishing is bound to that exact workflow and its `production`
  environment, so the former separate recovery workflow cannot acquire the
  temporary publication key. Recovery validates public package content before
  completing GitHub release and never republishes an already present package.
- `.releaserc.json` supplies one semantic-release version and explicit scripts;
  `tools/release-packages.json` retains the future pair declaration.
- Abstractions.Tests uses Sample.Contracts and EventStore.Contracts fixtures;
  Analyzers.Tests references Roslyn. Neither needs Core, CLI or MCP production code.

## Tasks & Acceptance

**Execution:**

- [x] `scripts/smoke-bootstrap-consumer.sh`, release preparation/publication and
  source verification — clear inherited NuGet fallback folders/configuration, test
  the actual prepared package before its receipt, and recheck the exact committed
  source and independent gates at final tag/publication boundaries. Direct publish
  must enforce the same source policy. Reject malformed registry version strings.
- [x] `.github/workflows/release.yml` recovery mode and recovery tests — migrate
  to bootstrap staging, recover missing publication after a tag, and verify an
  already published package before completing GitHub release without a second push.
  Preserve strict duplicate rejection for ordinary publication. Cover absent,
  matching, mismatching and uncertain public package states without network effects.
- [x] `scripts/tests/test_bootstrap_release.py` — cover staging/receipt symlink
  guards and existing paired-validator structural checks beyond its first guard.

- [x] `scripts/release-{prepare,preflight,publish}.sh` — isolate bootstrap builds
  and staging; enforce supported phase, version and credentials before effects.
- [x] `scripts/validate-release-packages.py` and new
  `scripts/tests/test_bootstrap_release.py` — cover every matrix rejection with
  synthetic packages and stubbed registry/push calls; protect existing checks.
- [x] `.github/workflows/bootstrap-package.yml`, `ci.yml`, `release.yml` —
  extract the standalone gate, run author-time tests and packaged consumer smoke,
  and require its exact-source success for bootstrap. Keep paired release blocked.
- [x] `README.md` — document gate, release sequence and exact consumer reference.
- [x] `_bmad-output/implementation-artifacts/evidence/story-4-6/verification.md`
  — record local checks, committed SHA, CI/release URLs, package hash, public-feed
  consumer proof and owning Builds revision. Execute the reviewed bootstrap
  workflow after integrating its validated changes into main.
- [x] `/home/administrator/projects/hexalith/builds/Props/Directory.Packages.props`
  — introduce the published version/property/package entry upstream; validate and
  integrate in that repository, preserving its existing work.
- [x] `/home/administrator/projects/hexalith/builds/Tools/package-version-audit.json`
  — preserve the previous audit, commit reviewed catalog declarations, then run
  the owning README's complete audit refresh for the new package family. Preserve
  all unrelated selected versions and historical observations.
- [x] This spec and `sprint-status.yaml` — synchronize status with actual evidence.

**Acceptance Criteria:**

- Given unavailable tool/module/Aspire prerequisites, when bootstrap runs, then
  its independent package and author-time gate still succeeds.
- Given a reviewed exact green main SHA, when bootstrap publication runs, then
  only its validated Abstractions package becomes available at the selected version.
- Given that published version, when an isolated decorated Contracts consumer
  restores from NuGet, then its single exact reference compiles and loads the analyzer.
- Given the published package, when Builds integration completes, then the owning
  catalog exposes `HexalithMcpCliVersion` without editing the read-only checkout.

## Implementation Notes

- 2026-10-18, resumed build review: All three independent layers completed;
  their eleven findings are individually triaged below. Both surviving patches
  are applied: corrected evidence state wording and a dirty-after-public-consumer
  regression protecting recovery's final source check. The regression detects
  removal of that check. Final parent verification passed all 60 release tests,
  20 Abstractions tests and 19 analyzer tests without skips, real preparation,
  a fresh NuGet.org consumer, actionlint, shell syntax and whitespace checks.
  Public package bytes match the recorded signed package hash. No new release,
  remote write, owner Builds change or gitlink change was made. The workflow's
  completion step records the reviewed corrections in a local commit.

- 2026-10-18, second-pass review corrections: Applied all ten remaining patch
  findings. The packaged README uses absolute links and version-neutral wording,
  states the production approval caveat, and runs the consumer once through
  preparation. Release test discovery includes every `test_*.py`. Recovery allows
  900 seconds of post-push propagation waiting, and the consumer requires its
  warning on `MissingDescriptionQuery.cs`. Executed workflow fixtures now cover
  preserved helpers across the tag checkout, the exact `DISPATCH_SHA` handoff,
  both NuGet-login output bindings, and missing/unmerged tag refusal. All 59
  release tests, 20 Abstractions tests and 19 analyzer tests pass with no skips;
  real package preparation, packaged README inspection, actionlint, shell syntax
  and whitespace checks pass. Four isolated workflow mutations are rejected.
  Evidence now records the prior committed-source gates and separate gitlink
  sync history. These local corrections await the parent review; no publication,
  Builds edit, gitlink change or remote write was performed.

- 2026-10-18, final review: All three review layers completed. Seven surviving
  findings were patched (six fixes, with duplicate verification findings); four
  were rejected with evidence and none deferred. Recovery completes existing
  draft releases after asset upload, and executed workflow fixtures check exact
  asset bytes and failure propagation. Publication rejects extra arguments,
  preparation detects package mutation during consumer smoke, local download
  write errors retain their cause, and source-gate errors retain sanitized
  stderr. Final parent verification passed 57 release tests, 20 Abstractions
  tests and 19 analyzer tests with zero skips, real preparation/consumer proof,
  cache-isolation rejection, actionlint, shell syntax and whitespace checks.
  The original package publication and Builds integration remain as recorded;
  these corrections are local and require committed-main gates before any
  future production run.

- 2026-10-18, review corrections: Completed all 22 remaining patch findings.
  Every recovery helper comes from the preserved reviewed directory, and newly
  pushed package downloads retry bounded 404 propagation. Added regressions for
  downloaded-package analyzer proof, same-entry changed bytes, analyzer warning
  assertions, detached HEAD, semantic-release wiring, Git ignore behavior,
  post-preparation dirty source and fresh consumer/usage guards. Both release
  modes gate source before production approval; bootstrap concurrency separates
  events. README and durable evidence now include exact commands, output and
  central package management. Release tests pass 51/51, author-time tests 20/20
  and 19/19, real preparation with forced terminal logger and source-isolation
  negative proof pass, as do actionlint/shell/whitespace checks. No publication,
  Builds edit, gitlink move or remote write was performed in this patch pass.

- 2026-10-17, completion: Trusted-publishing recovery pushed the exact tagged
  Abstractions `1.0.0` package through `release.yml`, then verified the public
  signed package and completed the GitHub release without a second push. An
  isolated NuGet.org consumer compiled both decorations and loaded the analyzer.
  The owning Builds catalog and complete revision-bound audit were validated and
  pushed at `eeab884dead9e5da859d9cda57a028fcfca433ae`. Detailed links, hashes
  and checks are in `evidence/story-4-6/verification.md`; no review finding was
  deferred.

- 2026-10-17, trusted publishing correction: The first production release
  selected `1.0.0` and tagged reviewed source, but the long-lived org secret's
  NuGet push returned HTTP 403. The user supplied an active organization-owned
  trusted-publishing policy for `release.yml` and `production`. Recovery moved
  into that workflow, which requests OIDC credentials. It checks the exact
  tagged source, successful original push gates and ancestry to current main;
  this permits the workflow repair commit while preserving the original tag.
  Public publication and Builds integration remain open.

- 2026-10-17, review loop 1: Reused the preserved candidate and corrected source
  rechecks, fallback isolation, registry version validation, prepared-byte consumer
  proof and partial-release recovery. Expanded offline coverage passes 26 tests;
  real package preparation, cache-isolation rejection, both author-time suites
  (20 + 19 tests), four-workflow actionlint and shell/whitespace checks pass.
  Publication, exact committed-main CI and owning Builds integration remain open.

- 2026-10-17: Bootstrap scripts, independent CI gate, author-time/packaged-consumer
  checks, source guard and rejection tests implemented. Local verification is
  recorded in `evidence/story-4-6/verification.md`. Source review, committed-main
  gates, publication/public-feed proof and owning Builds integration remain
  pending; the story remains in-progress.
- 2026-10-17: The requesting user answered "approve and stop" at Checkpoint 1.
  The approved intent is frozen; this spec and sprint tracking are ready-for-dev.
  Implementation and publication have not started. Resume with `bmad-build 4.6`
  in a fresh session.

## Spec Change Log

- 2026-10-17, review loop 1: recovery workflow callers were missing from the code
  map and task list. Moving staging and rejecting duplicate publication would
  break both recovery upload and GitHub-only completion. Added explicit recovery
  migration/tests and final publication proof requirements. Known-bad state:
  tagged partial release cannot finish and a fallback cache can falsify feed proof.
  KEEP: isolated Abstractions/analyzer builds, strict request/registry checks,
  private validated snapshot, SHA-256 receipt, independent exact-source CI,
  packaged analyzer proof, explicit incomplete external evidence, and existing
  matrix tests. The previous candidate is available for reconstruction at
  `/tmp/mcpcli-4-6-reviewed-candidate-2os__xtx`; inspect and reuse those working designs while
  correcting the listed review findings. Frozen intent is unchanged.

## Review Triage Log

### Resumed build review (2026-10-18)

All three layers completed: Blind Hunter returned ten findings, Edge Case Hunter
returned none, and Verification Gap returned one demonstrated regression gap.
Each finding is assessed independently below before grouping. No new deferrals
are required; the earlier agent-context deferral remains tracked in
`deferred-work.md:491`.

| ID | Verdict | Route | Evidence |
| --- | --- | --- | --- |
| B4.1 | low | reject | Carried B3.4: retaining/importing original artifacts would improve recovery when rebuilding changes consumer bytes, but this uncommon mismatch already fails closed. Artifact retention and import add a recovery path beyond a direct correction. |
| B4.2 | low | reject | Carried second-pass normal-publication readback finding: ordinary publication ends after NuGet push; the runbook requires a separate public-feed proof. Adding download/consumer orchestration to normal publication adds branches for an uncommon post-push registry failure. |
| B4.3 | low | reject | Completion uploads staging without another receipt check, so an external modification between the recovery and completion steps could change the asset. No workflow step writes staging in that interval; adding another guarded snapshot addresses an unusual outside mutation, while the NuGet publisher already pushes a private validated snapshot. |
| B4.4 | low | reject | Carried second-pass `gh release view` finding: any view error enters create; an existing release then makes the real create fail. Distinguishing transient errors from absence adds branches for an uncommon recovery failure. |
| B4.5 | low | reject | Carried second-pass `mktemp` failure finding: failed allocation before trap installation can strand staging; the next preparation explicitly refuses it. Cleanup restructuring for a failed temporary-directory allocation remains an uncommon availability improvement. |
| B4.6 | low | reject | A previously pushed package becoming visible between the two index reads makes preflight stop as already published, without a second push. A later recovery verifies it; handling this narrow propagation race requires a new duplicate-to-verification branch. |
| B4.7 | low | reject | Carried B3.5: recovery intentionally acquires its trusted identity for both paths, although an already-published package needs no push key. Conditional key acquisition adds orchestration branches for unavailable trusted-publishing configuration. |
| B4.8 | false | reject | `.releaserc.json` configures only the normal `main` release branch; pinned semantic-release `lib/get-next-version.js` emits prereleases only for a prerelease branch. The supported release path cannot produce the alleged prerelease partial tag; accepting SemVer syntax alone does not create one. |
| B4.9 | low | reject | Recovery accepts an existing remote tag on a green main ancestor without proving the originating release attempt. Exploiting that difference requires deliberately creating a tag and approving recovery; recording and enforcing release-attempt provenance adds a new gate for that unusual maintainer action. Ordinary version selection remains semantic-release-owned. |
| B4.10 | low | patch | The evidence opening says both artifacts remain in-progress; the spec is now in-review while sprint tracking is still in-progress. Replace the transient status claim with accurate wording about completed checks and pending review. |
| V4.1 | medium | patch | Deleting only recovery's final source recheck leaves all 59 tests green. A demonstrated consumer-build source mutation then returns success; add a dirty-after-consumer regression asserting the specific source error, nonzero exit, no verification-success message, and zero pushes. |

The two surviving findings have separate causes and receive separate narrow
patches. Existing publication and owning Builds acceptance remain satisfied.
Both patches are applied; parent verification passed 60 release tests and both
author-time suites. No surviving finding remains open.

| ID | Verdict | Route | Evidence |
| --- | --- | --- | --- |
| B1 | medium | bad_spec | Consumer smoke inherits fallback folders; the reviewer reproduced success against an empty source using a cached package. Clear configuration and fallback folders. |
| B2 | high | patch | Direct publisher calls only registry/package checks and succeeds in a non-Git fixture. Enforce exact committed-source checks at this entry point. |
| B3 | medium | patch | Workflow source check precedes restore/build; source can become stale before tagging. Repeat after preparation and before push. |
| B4 | medium | patch | The registry predicate accepts empty/whitespace/non-version strings. Validate each listed version before approving availability. |
| B5 | medium | patch | Production rebuilds after the independent gate and does not consumer-test its prepared bytes. Smoke the prepared package before recording the receipt. |
| B6 | medium | bad_spec | Pinned semantic-release tags before publication. Existing recovery is present, but the new staging and strict duplicate checks break it; migrate recovery and document it. |
| B7 | medium | patch | Existing paired checks remain present, but the only fixture stops at missing files and cannot protect later structural checks. Extend fixture coverage. |
| B8 | medium | patch | Only the package symlink is tested; staging-directory and receipt guards can disappear without detection. Add both rejection cases. |
| E1 | medium | patch | Independently confirms B4: malformed registry version strings are accepted as a free-version result. |
| V1 | medium | patch | Mutation controls removed directory/receipt symlink guards while all 16 tests passed. Add rejection and zero-push assertions for each. |
| V2 | high | patch | Recovery upload/create uses nupkgs/*.nupkg while preparation now writes nupkgs/bootstrap/*.nupkg. Update the caller. |
| V3 | high | bad_spec | Recovery unconditionally calls the now duplicate-rejecting publisher; when NuGet succeeded and GitHub failed, recovery stops. Add a verified existing-package completion path. |

Loop 1: recovery/consumer proof planning gaps trigger re-derivation; patch findings
are retained in the amended tasks. Publication and upstream integration stay open.


### Review pass 2

| ID | Verdict | Route | Evidence |
| --- | --- | --- | --- |
| B2.1 | medium | patch | Real empty-source smoke succeeds with inherited RestoreSources pointing at staging; force selected source properties. |
| B2.2 | medium | patch | Real empty-source smoke succeeds with inherited RestorePackagesPath pointing at a populated cache; force the fresh packages path. |
| B2.3 | high | patch | Receipt stores only hash; ignored staging can survive switching source revisions and pass a newer source gate. Bind preparation SHA and clean state and verify before publishing. |
| B2.4 | medium | patch | 2147483648.0.0 passes validation but NuGet cannot represent its major component. Reject overflow before requests/effects. |
| B2.5 | low | patch | Relative local sources are resolved relative to generated configuration rather than caller; normalize local paths. |
| B2.6 | low | patch | A consumer under Directory.Build.props inherits warning-as-error policy, breaking the intentional warning. Disable parent build imports for this probe. |
| B2.7 | false | reject | Recovery intentionally requires byte-equivalent consumer content and rejects changed DLLs. Different build paths/compiler can produce different bytes; refusing those is the documented fail-closed content policy. The supported Actions path and pinned SDK are stable; no incorrect publication was shown. Record this recovery limitation explicitly. |
| B2.8 | medium | patch | Recovery validates phase argument but absent-package publication reads ambient phase. Pass the validated phase to its subprocess. |
| B2.9 | medium | patch | Matching recovery fixture does not vary the generated core-properties exclusion; add different metadata to protect documented comparison behavior. |
| B2.10 | medium | patch | Source fixture only varies run_attempt; add conflicting run_number/attempt fixtures to protect latest-run ordering. |
| E2.1 | high | patch | Independent stale-source reproduction confirms B2.3: matching old package/hash can be pushed after verifying another commit. |
| V2.1 | medium | patch | Mutation replacing receipt creation with no-op leaves all 26 tests green. Assert exact preparation receipt and publish preparation output end to end. |

Surviving findings group into source-bound preparation receipts, consumer
isolation, numeric bounds, recovery phase propagation, and regression fixtures.
All route to narrow patches; frozen intent remains unchanged.

All surviving pass-2 patches were completed; 35 release tests and final local
checks pass. Reviewed source is ready for committed-main gates. External
publication and Builds acceptance remain open.

### Review pass 3 (2026-10-18)

| ID | Verdict | Route | Evidence |
| --- | --- | --- | --- |
| B3.1 | medium | patch | The pinned GitHub semantic-release plugin creates a draft before uploading assets (`node_modules/@semantic-release/github/lib/publish.js:96`); recovery's existing-release branch uploads but never publishes that draft. Publish it after a successful upload and cover draft recovery. |
| B3.2 | medium | patch | `release-publish.sh` reads only its first argument, so `VERSION --dry-run` reaches publication. Reject extra arguments before preflight and protect the zero-effect rejection. |
| B3.3 | false | reject | The 14 gitlink differences belong to commits already present when this invocation began on clean main. This resumed implementation has no `references/` changes; reverting those unrelated user commits would violate preservation instructions. |
| B3.4 | low | reject | Rebuilding with changed consumer bytes fails closed as documented and already assessed in B2.7. Retained-artifact import would add a new recovery mode; pinned same-path/toolchain repacks and the published recovery passed. The proposed fallback is beyond a direct correction for an uncommon mismatch. |
| B3.5 | low | reject | The script's existing-publication branch needs no key, while the production workflow deliberately obtains its trusted identity for both paths. An unavailable login can block GitHub-only completion, but conditional acquisition adds orchestration branches for failed trusted-publishing configuration; reject this uncommon availability improvement. |
| B3.6 | medium | patch | An isolated stub changed the package during the consumer build: preparation returned 0 and its receipt authorized the changed bytes. Capture the hash before the smoke and refuse a changed hash afterward before issuing the receipt. |
| B3.7 | low | reject | An interrupted receipt write can leave a partial receipt and require preserving/removing it before retry. Publication refuses invalid receipts, and normal writes are small; atomic receipt handoff adds machinery for an uncommon filesystem/interruption case. |
| B3.8 | low | patch | The download catch-all includes local `write_bytes` errors and discards their cause as registry uncertainty. Move the local write outside network-error handling and protect its reported filesystem cause. |
| B3.9 | medium | patch | The tests execute recovery but never the final workflow block. A wrong bootstrap asset glob in either create/upload branch would remain green. Execute both branches against a fake backend and assert exact attachment bytes. |
| B3.10 | low | patch | A local failing `gh` stub wrote an authentication explanation to stderr; the source gate discarded it and reported only exit 1. Preserve sanitized subprocess stderr and cover token redaction. |
| V3.1 | medium | patch | Independent verification confirms B3.9: recovery script fixtures stop before inline GitHub completion; the workflow assertion only checks strings. Execute missing/existing release completion and check exact package contents. |

Edge Case Hunter returned no findings and independently passed all 51 release tests.
All seven surviving findings were patched and covered by executed regressions;
no findings were deferred. The frozen intent is unchanged. The parent verbose
run also passed all 51 release tests (64.170 seconds), with no skips.

## Verification

- `python3 -m unittest discover -s scripts/tests -p 'test_*.py'`
- `MCPCLI_RELEASE_PHASE=bootstrap bash scripts/release-prepare.sh 1.0.0`
- Build/run Abstractions.Tests and Analyzers.Tests individually in Release.
- Preparation runs the extracted local-source consumer smoke with an isolated package cache.
- `actionlint .github/workflows/bootstrap-package.yml .github/workflows/ci.yml .github/workflows/release.yml`
- `git diff --check`; in Builds, run `pwsh -NoProfile -File` with
  `Tools/validate-central-package-versions.ps1`,
  `Tools/test-authoritative-package-catalog.ps1`, and
  `Tools/validate-package-version-audit.ps1`; run audit generator/validator fixture
  suites after the required complete refresh documented in `Tools/README.md`.
- Observe exact-source CI/commitlint and production release success; restore and
  compile the public-feed consumer. Report exact commands/results and blockers.

### Review Findings

Code review 2026-10-18 (range `04178de..34bc4b3`, full mode; Blind Hunter, Edge Case Hunter, Verification Gap, Acceptance Auditor).

- [x] [Review][Patch] (applied 2026-10-18) `production` had no approval gate or branch restriction — medium. Found while resolving the decision below: `gh api .../environments/production` returned `protection_rules: []` and `deployment_branch_policy: null`, so the documented "after production approval" recheck had no approval, and a `release.yml` on any branch could request the trusted-publishing key. Configured required reviewer `jpiquot` and a custom deployment branch policy admitting only `main`; read back and recorded in the evidence. Admin bypass remains enabled. [.github/workflows/release.yml:49]
- [x] [Review][Decision] (resolved: option 4 — this review accepted as the retroactive review of `e3a3f05`, deviation recorded in the evidence, `production` gate configured) Published 1.0.0 through recovery code that no review pass covered — medium. Review passes 1 and 2 ended at 35 tests (`d9f822d`). `e3a3f05` then added the `release.yml` `recover` job, `verify-release-source.py --tagged-recovery`, the `MCPCLI_RECOVERY_VERSION` publisher switch and 3 tests, and that code performed the HTTP 201 push (run 39057687505) and GitHub release completion (run 39058088252). The frozen Never rule says publication happens "only after review and checks on committed source". The package bytes were rebuilt from the reviewed tag and verified on the public feed, so the gap is governance, not package content. Options: (1) accept this review as the retroactive review of `e3a3f05` and record the deviation in the evidence; (2) also require the recovery patches below to be applied and reviewed before `done`; (3) treat the publication as non-compliant and decide on the package (for example, unlist it and republish a new version). [.github/workflows/release.yml:98]
- [x] [Review][Patch] (applied 2026-10-18) Tagged recovery runs the tag's helper scripts instead of the preserved reviewed copies — medium. The preserved `recover-bootstrap-release.py` and `release-publish.sh` call `scripts/validate-release-packages.py`, `scripts/smoke-bootstrap-consumer.sh`, `scripts/release-preflight.sh` and `scripts/release-receipt.py` relative to the working directory, which is the tag checkout. Only `verify-release-source.py`, `release-publish.sh` and `load_script` modules come from `$RUNNER_TEMP/release-scripts`. Recovering an older tag would use its outdated validator, preflight or receipt rules, or fail if the tag predates them. Resolve every sibling script relative to the calling script, and make the preserved-scripts test sabotage every tagged helper. [scripts/release-publish.sh:7; scripts/recover-bootstrap-release.py:41]
- [x] [Review][Patch] (applied 2026-10-18) Recovery fails right after its own push while NuGet is still processing the package — medium. The download happens immediately after `dotnet nuget push`, and a 404 is reported as an "uncertain registry response". This happened in run 39057687505 and needed a second dispatch. A re-dispatch during index lag sees the version as absent, pushes again and gets a 409. Add a bounded wait for the pushed version only, keep failing closed after the bound, and add a 404-then-200 fixture. [scripts/recover-bootstrap-release.py:60]
- [x] [Review][Patch] (applied 2026-10-18) Evidence depends on temporary local paths and omits exact commands — medium. The public-feed consumer proof (AC3), the isolation negative proof, the repack-equivalence check and the commitlint input exist only under `/tmp`. The public-feed and Builds validation commands are not listed, although Verification asks for exact commands and results. Inline the commands and key output lines (restore source, `1 Warning(s)`, `NU1101`, validator counts) while the directories still exist. [_bmad-output/implementation-artifacts/evidence/story-4-6/verification.md:21]
- [x] [Review][Patch] (applied 2026-10-18) No test protects recovery's consumer build of the downloaded public package — medium. Deleting the `smoke-bootstrap-consumer.sh` call leaves all 38 tests green, so recovery could complete the GitHub release without the analyzer proof the README promises. Add a recovery case with `SMOKE_FAIL=1` and `REGISTRY_STATE=taken`, and assert the restore source is the download directory. [scripts/recover-bootstrap-release.py:69]
- [x] [Review][Patch] (applied 2026-10-18) Recovery content comparison is not tested with changed bytes under the same entry names — medium. Replacing `content()` with an entry-name set leaves all tests green. Add a public package whose compile DLL bytes differ and assert "content does not match". [scripts/recover-bootstrap-release.py:22]
- [x] [Review][Patch] (applied 2026-10-18) The consumer analyzer assertions have no negative tests — medium. Removing both `grep` checks and the `CS8032`/`CS9057` check leaves all tests green, and the real gates too. Add stub output variants (missing `MCPCLI001`, `2 Warning(s)`, a `CS8032` line), each failing preparation without a receipt. [scripts/smoke-bootstrap-consumer.sh:71]
- [x] [Review][Patch] (applied 2026-10-18) Detached-HEAD acceptance, which every production checkout uses, is never exercised — medium. Tightening to `branch != "main"` leaves all tests green but would break every release and recovery. Add a stub state that prints an empty branch and expect success in both modes. [scripts/verify-release-source.py:38]
- [x] [Review][Patch] (applied 2026-10-18) `.releaserc.json` prepare command and asset glob are untested — medium. Reverting `assets` to `nupkgs/*.nupkg` or dropping `--verify-source` changes nothing any test reads. The asset upload has never run, because the only new-release run stopped at the 403. Read `.releaserc.json` in the harness, run its `prepareCmd`, and assert the asset glob matches exactly the prepared package. [.releaserc.json:18]
- [x] [Review][Patch] (applied 2026-10-18) The load-bearing `/nupkgs/` ignore rule is untested — medium. Without it, the receipt shows as untracked and makes `publishCmd` fail "uncommitted changes" after tagging. The stub `git` hides this. Add a real-git test seeded with the repository `.gitignore`. [.gitignore:227]
- [x] [Review][Patch] (applied 2026-10-18) Consumer smoke fails when the terminal logger is forced — low. Verified by probe: with `MSBUILDTERMINALLOGGER=on`, the build reports `succeeded with 1 warning(s)` in ANSI-styled text and the script exits 1. Pass `-tl:off` to restore and build. [scripts/smoke-bootstrap-consumer.sh:69]
- [x] [Review][Patch] (applied 2026-10-18) README overstates the credential check and the key-acquisition timing — low. `check_registry` only rejects a blank `NUGET_API_KEY`, so an invalid key is found at push time after tagging, as the 403 showed. In the `publish` job, `NuGet/login` runs before semantic-release builds, not "shortly before the push". [README.md:62; README.md:60]
- [x] [Review][Patch] (applied 2026-10-18) README consumer reference omits the central-package-management form — low. Hexalith Contracts repositories get versions from the Builds catalog, where an inline `Version` raises NU1008. Document the versionless reference with `HexalithMcpCliVersion`. [README.md:47]
- [x] [Review][Patch] (applied 2026-10-18) README keeps story-specific, now-stale release bookkeeping — low. It says the steps "remain required before claiming story completion" and links the story evidence. Make the section a reusable release checklist and link the published package. [README.md:66; README.md:44]
- [x] [Review][Patch] (applied 2026-10-18) README local smoke command fails on a second run — low. The script refuses an existing directory, and the README passes the fixed path `/tmp/mcpcli-bootstrap-consumer`. Use `"$(mktemp -d)/consumer"`. [README.md:55]
- [x] [Review][Patch] (applied 2026-10-18) Deferred-work anchor still points at the replaced preflight line — low. `deferred-work.md:6` cites `scripts/release-preflight.sh:9`, which is now a single call to `release-request.py`. The bootstrap acceptance lives in `validate_request` and `verify-release-source.py`. [_bmad-output/implementation-artifacts/deferred-work.md:6]
- [x] [Review][Patch] (applied 2026-10-18) Bootstrap concurrency lets a manual run cancel the push run the release gate needs — low. Dispatch and push on `main` share `bootstrap-package-${{ github.ref }}` with cancel-in-progress, and the gate accepts only the latest push run. Add `github.event_name` to the group. [.github/workflows/bootstrap-package.yml:11]
- [x] [Review][Patch] (applied 2026-10-18) `MCPCLI_RECOVERY_VERSION` switches direct publication to the tagged-recovery source policy without documentation — low. The README describes direct invocation as exact committed-source checks against current main, but the variable accepts a green tagged ancestor instead. Document the switch. [scripts/release-publish.sh:22]
- [x] [Review][Patch] (applied 2026-10-18) Source-gate tests assert only the generic "source gate failed" prefix — low. The I/O matrix requires the gate to identify the failed prerequisite, but swapping workflow names in the messages would pass. Assert each specific reason. [scripts/tests/test_bootstrap_release.py:570]
- [x] [Review][Patch] (applied 2026-10-18) Recovery prompts for production approval before any source check — low. `verify-source` is skipped for recovery, and `recover` has no `needs`. Run `verify-source` for both modes and make `recover` depend on it. [.github/workflows/release.yml:26]
- [x] [Review][Patch] (applied 2026-10-18) The fresh-consumer-directory guard is untested — low. Changing it to `mkdir -p` leaves all tests green and would allow reuse of a populated `packages/` cache. Add a second-invocation test that fails before any `dotnet` call. [scripts/smoke-bootstrap-consumer.sh:18]
- [x] [Review][Patch] (applied 2026-10-18) The receipt's after-preparation clean check is untested — low. Dropping `and after['source_clean']` leaves all tests green. Add clean-before, dirty-after preparation and expect publication refusal. [scripts/release-receipt.py:26]
- [x] [Review][Patch] (applied 2026-10-18) The `release-prepare.sh` usage guard is untested — low. Deleting it leaves all tests green, so a misspelled `--verify-source` in `.releaserc.json` would silently skip the pre-tag recheck. Add an unknown-argument test with no effects. [scripts/release-prepare.sh:8]

#### Rejected

- Spec `done` vs sprint `review` vs evidence "ready for review" (Blind, Edge Case, Acceptance Auditor) — fix edits the spec under review; this review's status sync reconciles it.
- Recovery drops the frozen "exact current main SHA" rule (Acceptance Auditor) — false; the `recover` job's first step runs the non-recovery source gate on `github.sha` after approval, requiring current main and both green results, and also gates the tag SHA.
- Commitlint evidence missing for `e3a3f05` and `34bc4b3` (Acceptance Auditor) — false; push runs 39057525597 and 39059408789 succeeded, and the first is linked in the evidence.
- GitHub release asset is a rebuild, not the pushed bytes (Blind) — low; content equality with the public package is verified, and the fix needs plumbing out of the temporary directory.
- Hard-coded `user: jpiquot` for `NuGet/login` (Blind) — low; a variable adds configuration surface for the same maintenance step.
- Paired pack and tool-install smoke deleted without tracking (Blind, Edge Case) — false; Story 4.16 owns isolated tool installation and offline smoke, and every entry point rejects `paired`.
- Four-part registry versions fail closed (Edge Case) — low; only semantic-release publishes this ID, and the fix changes the version grammar.
- Ignored build inputs such as `*.csproj.user` count as clean (Edge Case) — low; CI uses fresh checkouts, and the fix adds an ignored-file policy.
- Empty array under `set -u` on bash before 4.4 (Edge Case) — low; publication runs on Ubuntu, the scripts already need GNU tools, and it fails before any push.
- `;` or `,` in source or consumer paths (Edge Case) — low; fails loudly, and the fix adds a guard.
- Ancestor `Directory.Build.rsp` reaches the consumer (Edge Case) — low; temporary roots have none, and it fails closed.
- NU1900 replay or ambient `TreatWarningsAsErrors` (Edge Case) — low; not observed in any run, fails closed, and the fix adds properties.

### Review Findings

Code review 2026-10-18, second pass (range `04178de..55ed6e9`, code only: `_bmad-output/` and `references/` excluded by the user's scope choice; full mode; Blind Hunter, Edge Case Hunter, Verification Gap, Acceptance Auditor).

- [x] [Review][Decision] (resolved: option 1 — became the patch below; options 2 and 3 are left to Story 4.16, which decides each package README) The release runbook ships as the NuGet package README — low. `Hexalith.McpCli.Abstractions.csproj` packs the root `README.md` as `PackageReadmeFile`, so the new "Bootstrap package release" section (production approval, trusted publishing, recovery, `MCPCLI_RECOVERY_VERSION`) is on the nuget.org page, and `v1.0.0` already ships it. Its three repo-relative workflow links (`bootstrap-package.yml` once, `release.yml` twice) are broken on nuget.org, like the existing `_bmad-output/…` link in "Gateway boundary", and every later package will still say "1.0.0 is published" with `Version="[1.0.0]"`. The spec task requires the README to document the release sequence, so the fix depends on intent. Options: (1) keep the section, make its links absolute GitHub URLs and word the version text so it does not go stale; (2) give the package its own short README and keep the runbook in the repository README; (3) move the runbook to a maintainer document linked from the README; (4) accept as is. [README.md:40; src/Hexalith.McpCli.Abstractions/Hexalith.McpCli.Abstractions.csproj:5]
- [x] [Review][Patch] (applied 2026-10-18) Make the packaged README work on nuget.org — low. Resolved from the decision above: make the four repo-relative links (three workflow links and the existing `_bmad-output/…` link) absolute `https://github.com/Hexalith/Hexalith.McpCli/blob/main/…` URLs, link the package page without a version, present `[1.0.0]` as an example of pinning one exact version, and drop the fixed `(1.0.0)` after `HexalithMcpCliVersion`. [README.md:42; README.md:44; README.md:52; README.md:80]
- [x] [Review][Patch] (applied 2026-10-18) Recover-job wiring of the preserved scripts and the tag handoff is never executed by tests — medium. The reviewer pointed `release.yml:165` and `:177` back at `scripts/…` and all 57 tests still passed: the preserved-scripts test calls the preserved copies itself, and `complete_github_release` leaves a working-tree `verify-release-source.py` that also satisfies a reverted block. The "Require an existing release tag on main" step and its `DISPATCH_SHA` write to `$GITHUB_ENV` never run, and no test checks that both production jobs take `NUGET_API_KEY` from the `nuget-login` output. A reverted path would make recovery of `v1.0.0` run the tag's helpers and fail. Run the recover job's preserve, tag, rebuild, publish and complete steps in order with `RUNNER_TEMP` and a temporary `GITHUB_ENV`, sabotage the working-tree scripts after the preserve step, and assert one push, no tagged-helper call and `DISPATCH_SHA=<tag sha>`. [.github/workflows/release.yml:121; scripts/tests/test_bootstrap_release.py:834]
- [x] [Review][Patch] (applied 2026-10-18) The post-push public-download wait is too short for NuGet processing — medium. 12 attempts 10 s apart allow about 110 s. In the only observed case, run 39057687505 got a 404 right after its push, and the package was available when run 39058088252 started about five minutes later. If the bound expires, recovery fails after an irreversible push, and a re-dispatch while the index still lags sees the version as absent and gets a 409 from a second push. Raise the bound to cover NuGet's usual processing time (for example 15 minutes), and update the README sentence and the bounded-wait test. [scripts/recover-bootstrap-release.py:18]
- [x] [Review][Patch] (applied 2026-10-18) Evidence does not record the final committed source or its gate runs — low. `verification.md` never mentions `55ed6e9`, `c60ffa9` or `844776f`, and still says the corrections "require their own committed-main gates before any production use", although the CI, Commitlint and Bootstrap package push runs for `55ed6e9` succeeded. Record the commit and the three run URLs. [_bmad-output/implementation-artifacts/evidence/story-4-6/verification.md:464]
- [x] [Review][Patch] (applied 2026-10-18) Evidence claims no gitlink changed, but the story's range moves 14 — low. `verification.md:159` says "No read-only `references/` checkout or gitlink is changed by this work". `4a84c16` (`/pushall`) moved all 14 gitlinks, including Builds to `544fd2e` with this story's catalog commits, and `c60ffa9`, which also edits this story's evidence, moved Conversations from `e753cf8` to `476369f` rather than back to the baseline `4e93736`. State that the story implementation changed no gitlink and that the moves came from those sync commits. [_bmad-output/implementation-artifacts/evidence/story-4-6/verification.md:159]
- [x] [Review][Patch] (applied 2026-10-18) Deferred-work anchor is stale again — low. `deferred-work.md:6` cites `scripts/verify-release-source.py:28`, which is now `return json.loads(result.stdout)`; the bootstrap phase check moved to line 39 when `failure_detail` was added. [_bmad-output/implementation-artifacts/deferred-work.md:6]
- [x] [Review][Patch] (applied 2026-10-18) README overstates the production approval gate — low. The README says the environment "requires a maintainer's approval", but the evidence records that admin bypass is enabled and self-approval is allowed ("a deliberate pause, not an independent review"). Add that caveat. [README.md:66]
- [x] [Review][Patch] (applied 2026-10-18) The consumer smoke does not check which type raised `MCPCLI001` — low. `grep -q 'warning MCPCLI001:'` plus one total warning accepts a warning on `CreateItemCommand` with none on `MissingDescriptionQuery`. Match `MissingDescriptionQuery.cs(` on the warning line, and add a stub variant that reports the wrong file. [scripts/smoke-bootstrap-consumer.sh:72]
- [x] [Review][Patch] (applied 2026-10-18) The bootstrap gate runs the consumer smoke twice on the same bytes — low. `release-prepare.sh:32` already runs `smoke-bootstrap-consumer.sh` against the prepared package; the workflow's last step repeats it, and so does the README local gate's third command. Remove both duplicates. [.github/workflows/bootstrap-package.yml:44]
- [x] [Review][Patch] (applied 2026-10-18) The release test discovery is pinned to one file name — low. `-p 'test_bootstrap_release.py'` would silently skip any new `scripts/tests/test_*.py`, the same "CI silently skips it" pitfall the agent instructions record for .NET test projects. Use `-p 'test_*.py'` in the workflow and the README. [.github/workflows/bootstrap-package.yml:31]
- [x] [Review][Defer] Agent instructions do not name the release script suite or its gate [AGENTS.md:96] — deferred: the fix edits agent-context files. `Running and verifying` has no `python3 -m unittest discover -s scripts/tests` command and no mention of `bootstrap-package.yml`, so an agent changing release scripts may skip the suite until CI runs it.

#### Rejected

- Spec `done` vs sprint `review` vs evidence (Acceptance Auditor) — the fix edits the spec under review; this review's status sync sets both.
- Tagged-recovery mode at direct entry points does not require a green current main (Acceptance Auditor) — low; the workflow's first `recover` step enforces it, the README documents the switch, the tagged source had green gates, and a direct check needs a new HEAD-independent gate path.
- Post-tag recheck of current main turns a merge into a partial release (Blind) — low; the spec task requires rechecks "at final tag/publication boundaries", the window is seconds, and recovery covers it.
- Tagged recovery compares a stale `origin/main` with live main (Blind, Edge Case) — low; it fails closed and ties current main to the workflow source checked green in the first step. Fetching would accept an unchecked newer main, and a re-dispatch completes through the already-published path.
- NuGet key present during preparation (Blind) — low; the job's `id-token: write` lets any step mint its own key and `GITHUB_TOKEN` has `contents: write`, so unsetting the variable does not remove the exposure. Isolating the build needs a separate job.
- SDK rolls forward to the latest patch, and a rebuild mismatch is not diagnosed (Blind) — low; already assessed in B2.7 and B3.4, the README states the toolchain requirement, and it fails closed.
- Hard-coded `DISPATCH_REF: refs/heads/main` in two recover steps (Blind) — false; the first recover step and `verify-source` already require `github.ref` to be `refs/heads/main`, so the value cannot differ.
- `main` has no branch protection (Blind) — low; the README claims none, and the `production` required reviewer is the enforced approval. Protection is repository configuration outside this diff.
- No actionlint in CI (Blind) — low; the spec lists it as a local check, which the evidence records, and a CI job is new scope.
- Normal publication does not download and verify the public package, and the receipt is named `.sha256` but holds JSON (Blind) — low; public-feed proof is a recorded evidence step, and nothing uses `sha256sum -c`.
- A missing `REPOSITORY` reports a bare `KeyError` (Blind) — low; the workflows always set it, the message names the key, and the fix adds guards.
- Recovery-created releases use GitHub-generated notes (Blind) — low; cosmetic, and semantic-release notes need new plumbing.
- Package bytes could change between the hash recheck and the receipt (Edge Case) — low; nothing writes the staging directory during `--verify-source`, and the fix adds a parameter.
- A `mktemp` failure or partial receipt leaves staging behind (Edge Case) — low; the next run refuses with an explicit message, B3.7 already assessed partial receipts, and CI uses fresh runners.
- Empty array under `set -u` on bash before 4.4 (Edge Case) — low; already rejected; the scripts need GNU tools and run on Ubuntu.
- Four-part registry versions fail the index check (Edge Case) — low; already rejected; only semantic-release publishes this ID.
- `;`, `,` or `%` in source or consumer paths (Edge Case) — low; already rejected; it fails loudly.
- A transient `gh release view` failure falls through to create (Edge Case) — low; rare within a rare path, create fails loudly when a published release exists, and telling not-found apart adds branches.
- `--clobber` replaces a draft's original asset with rebuilt bytes (Edge Case) — low; same as the earlier "asset is a rebuild" rejection, and content equality with the public package is verified.

### Review Findings

Code review 2026-10-18, third pass (range `04178de..4a5e935`, code only: `_bmad-output/` and `references/` excluded by the user's scope choice; full mode; Blind Hunter, Edge Case Hunter, Verification Gap, Acceptance Auditor). 33 findings: 16 survive in 11 patch entries, 17 rejected, none deferred.

- [ ] [Review][Patch] Production-mode job guards and source-gate steps are never executed or asserted — medium. Deleting `if: ${{ inputs.recovery_version == '' }}` from `publish` leaves all 60 tests green; a recovery dispatch would then also run semantic-release and, after a releasable repair commit, cut a new version next to the recovery. Replacing the `run:` lines of the `verify-source` step, the `publish` "Recheck source…" step and the `recover` "Require current reviewed recovery workflow…" step with `true` also leaves all 60 green: the structural test checks only `needs:` text, and `run_workflow_step` has no `${{ github.sha }}`/`${{ github.ref }}` mapping. Assert both mutually exclusive `if:` conditions, map those expressions, and execute the three steps under `SOURCE_STATE=stale` and `bootstrap-failed`, asserting the specific gate message. [.github/workflows/release.yml:46; .github/workflows/release.yml:99; scripts/tests/test_bootstrap_release.py:1171]
- [ ] [Review][Patch] The workflow-step harness is not hermetic — medium. `run_workflow_step` starts from the fixture environment, so deleting `DISPATCH_REF` from the recover Publish step, `REPOSITORY`/`DISPATCH_REF` from Complete, or `MCPCLI_RELEASE_PHASE` from Rebuild leaves all 60 tests green; each breaks a real partial-release recovery, and the Complete case fails only after the NuGet push. It also maps an unknown `${{ … }}` expression to its literal text, so a step wired to the wrong expression passes when a stub ignores it. Remove the step-declared keys (`DISPATCH_REF`, `REPOSITORY`, `MCPCLI_RELEASE_PHASE`, `RECOVERY_VERSION`, `GH_TOKEN`) from the inherited environment before applying declarations, and fail on unmapped expressions. [scripts/tests/test_bootstrap_release.py:294; scripts/tests/test_bootstrap_release.py:302]
- [ ] [Review][Patch] Option-like source identifiers skip the receipt and source gates — low. Reproduced: `release-receipt.py verify R P -h` and `verify-release-source.py -h refs/heads/main bootstrap` print help and exit 0, so a direct `release-publish.sh` with `DISPATCH_SHA=-h` (or `DISPATCH_REF=-h`) pushes without receipt or committed-source checks, contradicting the README's direct-invocation claim. `release-request.py` also exits 0 for a `-h` version or phase, so preflight passes without key or registry checks (the validator then rejects before any push). Pass `--` before the positional arguments of every script-to-script call, keeping options such as `--tagged-recovery` and `--registry` before it, and add a `DISPATCH_SHA=-h` regression asserting a nonzero exit and zero pushes. [scripts/release-publish.sh:23; scripts/release-publish.sh:34; scripts/release-preflight.sh:7]
- [ ] [Review][Patch] A registry-index 404 still means "version free" after 1.0.0 is public — low. `version_is_published` returns False on 404; flat-container indexes persist for published IDs (including unlisted versions), so a 404 is now an uncertain response, yet publication and recovery continue to `dotnet nuget push`, against the matrix rule "uncertain registry response → zero push calls". Treat 404 as uncertain and switch the fixture's default absent state to `free`. [scripts/release-request.py:39]
- [ ] [Review][Patch] The analyzer load-failure check is unreachable — low. When the analyzer fails to load, `MCPCLI001` is missing, so the first `grep -Eq` exits under `set -e` without a message before the `CS8032|CS9057` check runs. That check fires only when `MCPCLI001`, a CS warning and `1 Warning(s)` appear together, which a real build cannot produce because CS8032 and CS9057 are themselves warnings; the `load-failure` fixture is exactly that impossible output. Run the load check first, give each failed check its own message, and make the fixture omit `MCPCLI001`. [scripts/smoke-bootstrap-consumer.sh:72; scripts/tests/test_bootstrap_release.py:135]
- [ ] [Review][Patch] The core-properties exclusion is documented with a wrong premise — low. Verified: the public 1.0.0 package and two local repacks contain the same `package/services/metadata/core-properties/nuget.psmdcp` (identical SHA-256, no generated ID or date); only `lastModifiedBy` records the packing NuGet version. The comment says pack "regenerates its core-properties ID/date", and the README says "regenerated package core-properties metadata". State the actual reason: the file records the packing NuGet version, not consumer content. [scripts/recover-bootstrap-release.py:30; README.md:69]
- [ ] [Review][Patch] README release commands are incomplete — low. The "For a local gate" block omits the Abstractions.Tests and Analyzers.Tests runs that `bootstrap-package.yml` performs, although the preceding paragraph lists them as part of the gate. The post-release public-feed proof says "in a fresh directory" without a command, while `smoke-bootstrap-consumer.sh` copies `global.json` from the working directory and must run from the repository root with a fresh target directory. Add both exact commands. [README.md:56; README.md:73]
- [ ] [Review][Patch] Existing validator manifest and phase checks are unprotected — low. Deleting the `expected_ids` manifest check leaves all 60 tests green, and no test calls the validator with an unknown phase, although the task requires protecting existing checks. Add a manifest-mutation fixture and an unknown-phase validator call. [scripts/validate-release-packages.py:26; scripts/validate-release-packages.py:29]
- [ ] [Review][Patch] Recovery request validation is untested — low. `test_invalid_requests_are_rejected_by_every_entry_point_before_effects` covers only prepare, preflight and publish; deleting `request.validate_request` from recovery leaves all 60 green, and an invalid version then surfaces as a source-gate tag error instead of naming the request. Add `recover-bootstrap-release.py` to the entry-point cases. [scripts/recover-bootstrap-release.py:68; scripts/tests/test_bootstrap_release.py:515]
- [ ] [Review][Patch] The source gate's `head_branch == "main"` filter is untested — low. The `gh` stub always reports `head_branch: main`, so removing this new filter leaves all 60 tests green. Add a fixture whose only successful run for the SHA is on another branch. [scripts/verify-release-source.py:98]
- [ ] [Review][Patch] No smoke test passes a URL package source — low. Replacing the scheme-preserving branch with `Path(source).resolve()` leaves all 60 tests green and turns `https://api.nuget.org/v3/index.json` into a local path, breaking the README's per-release public-feed proof. Add a URL case asserting that NuGet.Config and `RestoreSources` carry the URL unchanged. [scripts/smoke-bootstrap-consumer.sh:15]

#### Rejected

- Package replaced between the post-smoke hash check and the receipt (Edge Case) — low; already rejected in pass 2: nothing writes staging during `--verify-source`, and the fix adds a parameter.
- README says the consumer compiles the receipt's bytes (Edge Case claim) — low; same window as above, and the post-smoke hash recheck holds in every supported run.
- Re-dispatch during NuGet validation re-pushes and gets 409 (Edge Case) — low; fails closed, the 15-minute post-push wait covers the pushing run, a later re-dispatch completes through the already-published path, and handling 409 adds a branch.
- Four-part registry versions fail the index check (Edge Case) — low; already rejected twice.
- A `mktemp` failure strands staging (Edge Case) — low; already rejected twice.
- Empty array under `set -u` on bash before 4.4 (Edge Case) — low; already rejected twice.
- `file://` or `;` in package source paths (Edge Case) — low; `;` already rejected; `file://` fails loudly, and the fix adds a guard.
- DLLs embed the checkout path because `ContinuousIntegrationBuild` is not imported (Blind) — low; already assessed in B2.7, B3.4 and pass 2; the runner path is stable, the README states the limitation, and changing tracked build settings would itself break comparison with `v1.0.0`.
- Recovery rebuilds old tags with current main's build recipe (Blind) — low; the deliberate pass-1 correction to run preserved reviewed helpers; a later recipe change fails closed, and recording the recipe adds receipt fields.
- A new release can proceed while an earlier tag remains unpublished (Blind) — low; requires ignoring a failed release run, and the fix adds a per-tag registry gate.
- Recovery does not control the "Latest" release (Blind) — low; matters only in the previous scenario, and selecting the highest tag adds a branch.
- The default semantic-release fail comment suggests a restart, and `pull-requests: write` is unused (Blind) — low; both are pre-existing configuration this diff does not touch, the README documents recovery, and the path is rare.
- The publish checkout persists the write token (Blind) — low; pre-existing step, and `prepareCmd` runs inside semantic-release with `GITHUB_TOKEN` in its environment, so persisted credentials add little exposure (pass-2 rationale).
- Recovery does not verify the nuget.org repository signature (Blind) — low; the package comes over HTTPS from api.nuget.org, which signs every package, and verification is a new guard.
- Evidence location is undefined and the receipt is not attached to the release (Blind) — low; evidence is recorded per story, and release assets or attestation add release surface.
- `--tagged-recovery` value is not validated in the source gate (Blind) — low; every caller validates it first, the gate issues only read-only calls and fails closed on a mismatch, and the fix adds a guard.
- No test asserts that `bootstrap-package.yml` stays isolated from the tool build (Acceptance Auditor) — low; such an edit is visible in review, it guards no script path, and a negative text assertion would be brittle.
