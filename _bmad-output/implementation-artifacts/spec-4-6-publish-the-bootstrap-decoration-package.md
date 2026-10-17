---
title: '4.6 Publish the bootstrap Decoration Package'
type: 'feature'
created: '2026-10-17'
status: 'ready-for-dev'
route: 'dispatch'
review_loop_iteration: 0
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
- `.releaserc.json` supplies one semantic-release version and explicit scripts;
  `tools/release-packages.json` retains the future pair declaration.
- Abstractions.Tests uses Sample.Contracts and EventStore.Contracts fixtures;
  Analyzers.Tests references Roslyn. Neither needs Core, CLI or MCP production code.

## Tasks & Acceptance

**Execution:**

- [ ] `scripts/release-{prepare,preflight,publish}.sh` — isolate bootstrap builds
  and staging; enforce supported phase, version and credentials before effects.
- [ ] `scripts/validate-release-packages.py` and new
  `scripts/tests/test_bootstrap_release.py` — cover every matrix rejection with
  synthetic packages and stubbed registry/push calls; protect existing checks.
- [ ] `.github/workflows/bootstrap-package.yml`, `ci.yml`, `release.yml` —
  extract the standalone gate, run author-time tests and packaged consumer smoke,
  and require its exact-source success for bootstrap. Keep paired release blocked.
- [ ] `README.md` — document gate, release sequence and exact consumer reference.
- [ ] `_bmad-output/implementation-artifacts/evidence/story-4-6/verification.md`
  — record local checks, committed SHA, CI/release URLs, package hash, public-feed
  consumer proof and owning Builds revision. Execute the reviewed bootstrap
  workflow after integrating its validated changes into main.
- [ ] `/home/administrator/projects/hexalith/builds/Props/Directory.Packages.props`
  — introduce the published version/property/package entry upstream; validate and
  integrate in that repository, preserving its existing work.
- [ ] `/home/administrator/projects/hexalith/builds/Tools/package-version-audit.json`
  — preserve the previous audit, commit reviewed catalog declarations, then run
  the owning README's complete audit refresh for the new package family. Preserve
  all unrelated selected versions and historical observations.
- [ ] This spec and `sprint-status.yaml` — synchronize status with actual evidence.

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

- 2026-10-17: The requesting user answered "approve and stop" at Checkpoint 1.
  The approved intent is frozen; this spec and sprint tracking are ready-for-dev.
  Implementation and publication have not started. Resume with `bmad-build 4.6`
  in a fresh session.

## Spec Change Log

## Review Triage Log

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
