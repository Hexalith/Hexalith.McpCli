---
title: '4.6 Publish the bootstrap Decoration Package'
type: 'feature'
created: '2026-10-17'
status: 'done'
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

## Verification

- `python3 -m unittest discover -s scripts/tests -p 'test_bootstrap_release.py'`
- `MCPCLI_RELEASE_PHASE=bootstrap bash scripts/release-prepare.sh 1.0.0`
- Build/run Abstractions.Tests and Analyzers.Tests individually in Release.
- Run the extracted local-source consumer smoke with isolated package cache.
- `actionlint .github/workflows/bootstrap-package.yml .github/workflows/ci.yml .github/workflows/release.yml`
- `git diff --check`; in Builds, run `pwsh -NoProfile -File` with
  `Tools/validate-central-package-versions.ps1`,
  `Tools/test-authoritative-package-catalog.ps1`, and
  `Tools/validate-package-version-audit.ps1`; run audit generator/validator fixture
  suites after the required complete refresh documented in `Tools/README.md`.
- Observe exact-source CI/commitlint and production release success; restore and
  compile the public-feed consumer. Report exact commands/results and blockers.
