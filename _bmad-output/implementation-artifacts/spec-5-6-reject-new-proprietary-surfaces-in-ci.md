---
title: '5.6 Reject new proprietary surfaces in CI'
type: 'feature'
created: '2026-11-10'
status: 'in-progress'
baseline_commit: 'c9a46a11a8317dd1903e3a3ef2f27791942b316a'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-5-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** CI does not enforce the approved prohibition on new proprietary MCP servers, plug-ins and CLIs in root-declared references.

**Approach:** Add a generic committed-source census, a versioned baseline derived from technical inventory 1.0.2, and a blocking CI job required by release staging.

## Boundaries & Constraints

**Always:** Read root declarations and gitlinks from the same parent revision, then inspect committed reference blobs at those pins. Cover paths beyond `src/`, inherited project metadata, registration code, packaging, containers and publication entries. Preserve PS/PE/PN classifications and FK consumer distinctions through baseline data. Exceptions identify one exact surface and require nonblank owner/reason and ISO expiry; validity includes the expiry day, using UTC today in production.

**Never:** Embed module names, paths or counts in checker logic; silently broaden exemptions; rewrite baseline allowances during a scan; initialize nested submodules; execute inspected code. Baseline changes require versioned census amendments preserving prior bytes. No production code, dependencies, gitlinks, upstream edits, publication or retirement changes.

**Decision (user, 2026-11-10, option A):** Record Builds `Samples/PublishSpike/PublishSpike.csproj` and Conversations `_bmad/scripts/epic16_native_helper/Epic16.NativeHelper.csproj` as scoped non-surface qualification exemptions through a versioned census amendment. Bind the inspected pins and source hashes in `evidence/story-5-6/planning.json`; preserve the approved technical inventory bytes. This grants no blanket exemption for future fixtures.

## I/O & Edge-Case Matrix

| State | Expected behavior |
|---|---|
| New unapproved project, tool, container or release entry | Fail with repository, gitlink, path and detection signal |
| Approved exemption or exact unexpired exception | Pass; retain classification in report |
| Missing owner/reason/expiry, malformed or expired exception | Fail, including when its target is otherwise allowed |
| Removed baseline surface | Report stale entry; preserve baseline; staleness alone does not fail |
| Missing root/object, malformed metadata or unsafe path | Fail rather than skip coverage |

</frozen-after-approval>

## Code Map

- `_bmad-output/implementation-artifacts/technical-tools-migration-inventory-v1.md:249` — census definition; PS01–PS14, PE01–PE09, PN roots and FK02–FK04 distinctions. Its Story 5.1 approval receipt binds inventory 1.0.2; retain the approved bytes and provenance.
- `_bmad-output/implementation-artifacts/evidence/story-5-1/verification.md:522` — discovery precedent; replace its hardcoded/worktree-dependent implementation. Packaging and exemption checks start at line 632.
- `_bmad-output/implementation-artifacts/evidence/story-5-6/planning.json` — exact inspected pins, fixture evidence and hashes; findings only, no approval.
- `.github/workflows/ci.yml:41` — standalone Python job pattern, pinned actions and artifact retention.
- `scripts/verify-release-source.py:32` — required CI jobs/steps. `scripts/paired_release.py:68` already consumes that map; preserve historical bootstrap recovery and the separate publication-stage map.

## Tasks & Acceptance

**Execution:**
- [x] `tools/proprietary-surfaces/v1/baseline.json` — encode approved surfaces, narrowly scoped exemptions, consumer distinctions, publication identities, root provenance and empty initial exceptions; bind source inventory and approval hashes. Preserve the original baseline and record the two authorized fixture exemptions in a versioned amendment.
- [x] `tools/proprietary-surfaces/v1/check.py` — inspect Git trees/blobs; discover candidates from project identity, executable/tool metadata, MCP references/registrations and publication metadata. Associate source signals with projects; inspect manifests/workflows/scripts even when a referenced project is absent. Emit stable JSON and diagnostics; never execute MSBuild or a discovered program.
- [x] `tools/proprietary-surfaces/v1/test_census.py` — disposable Git fixtures for the matrix, renamed/nonstandard/outside-src surfaces, inherited settings, every exemption class, orphan publication, invalid baseline/amendments, exact exception binding, date boundaries, stale entries, missing objects, nested gitlinks and worktree/HEAD independence. Assert exit status and complete output streams; prove each refusal guard is detected when removed.
- [x] `.github/workflows/ci.yml` — add required `proprietary-surface-census` job; initialize only committed root declarations without recursion; run fixtures and real scan; retain sanitized report on failure.
- [x] `scripts/verify-release-source.py` and `scripts/tests/test_paired_publication.py` — require the census job and executed steps; test missing/skipped/failed jobs and steps, including publication evidence validation.
- [x] `tools/proprietary-surfaces/v1/README.md` and `README.md` — document scope, signals, local command, reporting, expiry semantics and versioned amendment procedure.
- [x] `_bmad-output/implementation-artifacts/evidence/story-5-6/verification.md` and `sprint-status.yaml` — record checks, source pins, report hashes and outcome; scan retained evidence.

**Acceptance Criteria:**
- Given committed root references, when CI scans them, then every reference is accounted for and an unapproved surface fails with actionable evidence while approved exemptions pass.
- Given retained baseline data, when a surface disappears, then the report names it as stale and the scan changes no allowance.
- Given current paired-release source evidence, when census execution is absent or unsuccessful, then staging and publication eligibility fail; historical bootstrap gates retain their existing behavior.
- Given inspection of the change, when source and tests are examined, then no module-specific checker branch or nested initialization exists and each new refusal has a failing negative control.

## Implementation Notes

- Added a committed-object census with data-only classifications, separate exact project/package/tool/container identities, static inherited/imported metadata and registration discovery, and fail-closed metadata/policy checks.
- Preserved the original census baseline and inventory approval bytes. The option-A 1.0.1 amendment binds complete fixture-directory source closures, including additional-file detection; removals and exception replacement remain versioned operations.
- CI initializes only committed root declarations with recursion disabled. Paired staging/publication require the census job and all three executed steps; bootstrap and publication-stage job maps remain separate.
- Local checks and hashes are recorded in `evidence/story-5-6/verification.md`; sprint status is `review` for the build workflow's review phase.

## Spec Change Log

## Review Triage Log

## Verification

- `python3 -m unittest discover -v -s tools/proprietary-surfaces/v1 -p 'test_*.py'` — fixtures pass.
- `python3 tools/proprietary-surfaces/v1/check.py --output /tmp/mcpcli-story-5-6/census.json` — complete committed-pin scan passes with the authorized fixture amendment.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s scripts/tests -p 'test_*.py'` — release regressions pass.
- `git diff --check` and the shared evidence secret scan — pass. No .NET or live checks are required for this Python/data/CI-only change.
