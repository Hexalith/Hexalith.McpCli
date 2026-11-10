---
title: '5.6 Reject new proprietary surfaces in CI'
type: 'feature'
created: '2026-11-10'
status: 'done'
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
- Build review pass 1 applied all 13 patch groups, closed the parent P1 follow-up, and recorded six current-pin non-surface test/qualification observations without a directory exemption. Final verification: 53 census tests, 195 release tests, all 17 root references and all three mutation probes pass. No findings were deferred. See [reviewed evidence](evidence/story-5-6/review-pass-1/verification.md); the initial evidence remains preserved.

## Spec Change Log

## Review Triage Log

### Build review pass 1 — 2026-11-10

All three review layers completed. Each finding was assessed before grouping. Patches extend existing generic discovery, policy validation and verification paths; they add no runtime public surface. Concurrent Story 5.12 work is outside this review's fixes.

| ID | Verdict | Evidence | Route |
|---|---|---|---|
| BH1 | medium | A wildcard import is reduced to literal filenames, while unconsumed metadata ignores OutputType; a neutral executable is omitted. | P1 |
| BH2 | medium | PackageReference/ProjectReference Include values are appended without property expansion, so a local MCP dependency alias disappears. | P2 |
| BH3 | medium | Metadata matching and the property dictionary are case-sensitive although MSBuild property names are not; lowercase OutputType is missed. | P2 |
| BH4 | medium | The JSON prefilter recognizes image/project structure but not packages alone; release.json package entries are skipped. | P3 |
| BH5 | medium | The same JSON prefilter skips mcpServers/servers under nonstandard JSON filenames. | P3 |
| BH6 | medium | Absent publication projects are emitted only when IDENTITY matches; dotnet publish missing/Neutral.csproj is ignored. | P4 |
| BH7 | medium | Script/workflow discovery has no literal docker build/push target extraction, so neutral orphan image publications disappear. | P5 |
| BH8 | high | Amendment approval only requires nonblank text and an evidence hash; explicit rejection and unrelated/non-JSON receipts can authorize allowances. | P6 |
| BH9 | false | Root removal is reported as stale without rewriting policy, consistent with the approved stale-report behavior. The guide requires a new lineage when changing policy root/scope data; it does not require failing an observed removal. | reject |
| BH10 | medium | Fixture sourcePrefix hashes only directory members; inherited metadata and linked sources outside it can change compiled behavior without source drift. | P7 |
| BH11 | medium | The test/perf path check skips all non-project publication/configuration files rather than applying exact approved allowances. | P8 |
| BH12 | medium | The scan step has the default success condition, so failed initialization/fixtures leave no report for the always-run artifact step. | P9 |
| EC1 | medium | The traced local glob case reaches the same incomplete import/fallback branch as BH1. | P1 |
| EC2 | medium | The traced PackageReference alias reaches the same unexpanded reference handling as BH2. | P2 |
| EC3 | medium | Executable-project detection suppresses a neutral executable solely because its path contains tests/perf or Tests. | P8 |
| EC4 | medium | Publication metadata with unresolved MSBuildProjectName is explicitly omitted, allowing a renamed approved package to become stale and pass. | P2 |
| EC5 | medium | The image regex allows newline whitespace and captures repository: as the identity of a YAML mapping; changing the real repository preserves that identity. | P10 |
| EC6 | medium | Neutral dotnet tool install and docker publication targets have neither explicit command extraction nor a matching suffix token. | P5 |
| EC7 | medium | The orphan-publication claim is disproved by the same reachable neutral-name skip described in BH6. | P4 |
| VG1 | medium | Pre-verified regression gap: scanning only the first root leaves all 34 fixtures passing; no multi-root fixture protects complete accounting. | P11 |
| VG2 | medium | Pre-verified regression gap: disabling TOML discovery leaves all fixtures passing; JSON-only configuration tests do not protect TOML consumers. | P12 |
| VG3 | medium | Pre-verified regression gap: removing report redaction leaves all fixtures passing; no census-boundary credential canary protects retained output. | P13 |
| VG-O1 | medium | The verified wildcard-import reproduction confirms BH1/EC1; unconsumed OutputType metadata cannot substitute for resolved imports. | P1 |

P1 imports; P2 property resolution; P3 JSON prefilter; P4 orphan projects; P5 publication commands; P6 approval decisions/scope; P7 fixture compilation closure; P8 path-based exemptions; P9 failure diagnostics; P10 YAML image mappings; P11 multiple roots; P12 TOML coverage; P13 census redaction coverage.

Parent follow-up for P1: a disposable fixture with `$(ExternalDir)/*.props` and an unconsumed `OutputType=Exe` file still returned `passed` after the first patch batch. The medium verdict and P1 route are retained; executable/dependency fallback signals and regressions are required before final verification. The tool guide must also describe the corrected closure and v2 receipt format.

Applied P1–P13: final checks and independent policy/source audit pass; BH9 is rejected on the recorded evidence. No open patch or deferral remains.

## Verification

- `python3 -m unittest discover -v -s tools/proprietary-surfaces/v1 -p 'test_*.py'` — fixtures pass.
- `python3 tools/proprietary-surfaces/v1/check.py --output /tmp/mcpcli-story-5-6/census.json` — complete committed-pin scan passes with the authorized fixture amendment.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s scripts/tests -p 'test_*.py'` — release regressions pass.
- `git diff --check` and the shared evidence secret scan — pass. No .NET or live checks are required for this Python/data/CI-only change.
