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
- [x] Continue the 111 coverage errors in `evidence/story-5-6/implementation-resume-20261111/acceptance-blockers.json`: group every error by root cause, identify what exact committed source proves, and implement bounded generic fixes in `tools/proprietary-surfaces/v1/check.py` where that proof suffices. This user authorization (2026-11-11) extends generic source-resolution work; preserve runtime/generated-input and nested-repository refusals. Execute no inspected code, initialize no nested submodules, change no references/gitlinks or policy allowances, exceptions, exemptions, approvals, or dependencies. Do not commit, stage, or push.
- [x] Add regressions in `tools/proprietary-surfaces/v1/test_census.py` and executed guard-removal controls for new guards. Run relevant fixtures, release regressions, all five matrix rows, and a fresh committed-pin scan. Preserve earlier evidence; write a distinct `evidence/story-5-6/coverage-resolution-20261111/` packet with commands, exact pins/source bindings, before/after grouping, policy/prior-evidence integrity, and verification results. Update both READMEs for any supported-subset changes.
- [x] Prepare a concise remaining-blocker decision packet in that new evidence directory separating scanner limitations, upstream source defects, and observations requiring exact owner disposition; recommend the next concrete action for each group, grant no authority, and keep story/sprint `in-progress` until acceptance succeeds.
- [x] `tools/proprietary-surfaces/v1/check.py` — address inspection cases E01–E05 in the retained handoff disposition packet through generic, bounded static resolution of project targets and Compile item provenance. Resolve finite literal shell variables, loops, function arguments and working directories when provable from committed source. Inspect no nested repository and execute no inspected code; unresolved runtime/generated source must retain actionable coverage errors. Keep other inspectable projects/files visible when an individual source fails rather than discarding that root's observations. Do not add allowances, exclusions, exceptions or owner authority.
- [x] `tools/proprietary-surfaces/v1/test_census.py` — cover supported target/item resolution, unresolved and unbounded variants, directory containment, nested gitlinks, dynamic generated sources and retained partial-root observations. Every new refusal needs an executed guard-removal negative control; assert full output streams and exact discovered identities.
- [x] `tools/proprietary-surfaces/v1/README.md`, `README.md` and `evidence/story-5-6/` — document the supported static subset and remaining limitations; retain fresh fixture, release, matrix, mutation and real-scan evidence with exact pins and policy integrity. Keep story/sprint in-progress while current-reference acceptance is unsuccessful.
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

### Review Findings

Independent code review — 2026-11-10. Scope: committed Story 5.6 changes from
`c9a46a11a8317dd1903e3a3ef2f27791942b316a` through
`dedc826`; concurrent Story 5.12 changes and uncommitted work are excluded.
All four layers completed: Blind Hunter (BH), Edge Case Hunter (EC),
Verification Gap (VG), and Acceptance Auditor (AA). Each of the 24 submitted
findings received its own verdict before grouping into the 20 actions below.
Outcome: 0 decision-needed, 20 patch, 0 defer, 0 rejected. P1 is high; P2–P20
are medium. These findings remain open; no implementation patches were applied.

User decision — 2026-11-10: option 2, leave all 20 patch findings as action
items. All checkboxes remain open. Story and sprint status are `in-progress`;
issues fixed: 0; deferred: 0; rejected: 0.

- [x] [Review][Patch] P1 — Validate amendment authority against the approved lineage [tools/proprietary-surfaces/v1/check.py:200]. A hash-bound, untracked JSON file containing only `{"decision":"approved","source_revisions":{}}`, or an incomplete v2 receipt with just schema and decision, can authorize a new executable allowance. Validate authority structure, provenance and authorized scope rather than accepting the presence of a revision dictionary or schema name. Sources: BH7; high.
- [x] [Review][Patch] P2 — Read SDK identities from XML declarations [tools/proprietary-surfaces/v1/check.py:547]. Adding `<!-- Microsoft.NET.Sdk.Web -->` to a neutral executable under `src/` makes it disappear from the census; an AppHost SDK name in a comment also suppresses executable detection. Inspect actual SDK declarations and protect both comment cases. Sources: BH1; medium.
- [x] [Review][Patch] P3 — Resolve local imports independently of metadata filename extensions [tools/proprietary-surfaces/v1/check.py:458]. Committed imports such as `eng/runtime.xml` and `eng/Hidden.PROPS` can declare `OutputType=Exe` while the scan reports no surface. The `.props`/`.targets` filename filter also omits these imports from fixture compilation closures. Resolve literal local imports against committed blobs and validate their XML. Sources: BH2, EC4, AA1; medium.
- [x] [Review][Patch] P4 — Evaluate targets after project properties [tools/proprietary-surfaces/v1/check.py:420]. `Directory.Build.targets` is visited before the project, so its `$(HostDir)/*.props` import cannot use the project's `HostDir` and is never revisited. A local imported `OutputType=$(HostKind)` with project `HostKind=Exe` then passes without a candidate. Preserve props/project/targets ordering or refuse unresolved classification imports. Sources: BH3; medium.
- [x] [Review][Patch] P5 — Track effective default package identities [tools/proprietary-surfaces/v1/check.py:624]. Replacing an approved explicit `PackageId=old` with `AssemblyName=new` leaves the executable approved and reports only the old package as stale; the new effective package identity is never emitted. Include SDK default package/assembly identities in discovery and rename checks. Sources: BH4; medium.
- [x] [Review][Patch] P6 — Recognize F# and VB MCP attributes without arguments [tools/proprietary-surfaces/v1/check.py:27]. `[<McpServerTool>]` and `<McpServerTool>` terminate the name with `>`, which the pattern excludes. Adding these attributes to an approved dependency consumer therefore adds no registration signal. Cover the supported languages' attribute syntax. Sources: BH5; medium.
- [x] [Review][Patch] P7 — Detect direct MCP server construction [tools/proprietary-surfaces/v1/check.py:595]. An approved executable dependency consumer can add `McpServer.Create(new StdioServerTransport(options), options)` and `RunAsync()` without gaining a registration signal. The exact source compiled against ModelContextProtocol.Core 2.4.0 and completed a stdio MCP initialize exchange, while its committed census fixture remained approved. Detect the public direct server/transport construction APIs as server signals. Sources: BH6; medium.
- [x] [Review][Patch] P8 — Match MSBuild recursive globs in fixture closures [tools/proprietary-surfaces/v1/check.py:494]. Python `fnmatch` omits `shared/Root.cs` for `shared/**/*.cs`, whereas MSBuild's `**` permits zero intermediate directories. Changing that compiled source passes a source-bound fixture allowance because its hash is absent. Use MSBuild-compatible glob semantics for imports and Compile items. Sources: BH8; medium.
- [x] [Review][Patch] P9 — Inspect container publication action inputs [tools/proprietary-surfaces/v1/check.py:699]. A workflow using `docker/build-push-action`, `push: true`, and literal `tags: registry.invalid/neutral:latest` passes without a publication candidate. Inspect the action's publication inputs and bind each image identity. Sources: BH9; medium.
- [x] [Review][Patch] P10 — Inspect supported YAML image structures [tools/proprietary-surfaces/v1/check.py:721]. Flow mappings such as `containers: [{name: neutral, image: registry.invalid/neutral:latest}]`, inline Compose mappings, and Kustomize `images`/`newName` entries pass without candidates. Extend structural image discovery beyond the current line-oriented `image:` and `repository:` forms. Sources: BH10, AA4; medium.
- [x] [Review][Patch] P11 — Preserve conditional property alias alternatives [tools/proprietary-surfaces/v1/check.py:436]. `Kind=Exe` for Release followed by `Kind=Library` for another configuration collapses to the last value before `OutputType=$(Kind)` is resolved. The census passes with no surfaces although `dotnet msbuild -getProperty:OutputType -p:Configuration=Release` returns `Exe`. Retain all classification-relevant conditional possibilities or fail closed. Sources: EC1; medium.
- [x] [Review][Patch] P12 — Resolve imported Compile paths against the consuming project [tools/proprietary-surfaces/v1/check.py:485]. An imported `eng/linked.props` with `Compile Include="../../shared/Secondary.cs"` in `tests/Neutral/Neutral.csproj` compiles the repository's shared file, but the census resolves the path relative to `eng/` and omits it. Subsequent compiled behavior changes pass the fixture's source hashes. Apply project-relative item semantics while preserving explicitly expanded `MSBuildThisFileDirectory` paths. Sources: EC2; medium.
- [x] [Review][Patch] P13 — Resolve aliases in unconsumed classification metadata [tools/proprietary-surfaces/v1/check.py:570]. An unresolved `$(ExternalDir)/*.props` import with local metadata defining `Kind=Exe` and `OutputType=$(Kind)` passes without a surface or prerequisite diagnostic. The fallback sees only the literal expression. Expand local aliases conservatively or refuse unresolved classification values. Sources: EC3; medium.
- [x] [Review][Patch] P14 — Inspect both supported JSON server sections [tools/proprietary-surfaces/v1/check.py:660]. A document with `mcpServers: {}` and a populated `servers` object passes without inspecting the latter. Validate and inspect both present sections instead of choosing the first. Sources: EC5; medium.
- [x] [Review][Patch] P15 — Recognize equals-form Docker tags [tools/proprietary-surfaces/v1/check.py:767]. Both `docker build --tag=registry.invalid/neutral:1 .` and `docker buildx build --tag=registry.invalid/neutral:1 --push .` pass without candidates because the parser only handles separate tag/value tokens. Support literal equals-form options and bind their exact image identities. Sources: EC6, AA3; medium.
- [x] [Review][Patch] P16 — Inspect executable scripts without filename extensions [tools/proprietary-surfaces/v1/check.py:518]. A committed executable `scripts/ship` with a shell shebang and literal `docker push registry.invalid/neutral:latest` passes without inspection. Include executable shell scripts identified by their interpreter, with regression coverage for tool and container commands. Sources: EC7; medium.
- [x] [Review][Patch] P17 — Protect independent container-identity detection [tools/proprietary-surfaces/v1/test_census.py:147]. Removing the `ContainerRepository`-only signal leaves all 53 fixtures and the real scan passing, but changes a neutral project's sole `<ContainerRepository>neutral-mcp</ContainerRepository>` case from rejected to passed. Add an independent refusal fixture asserting both the project signal and publication identity. Sources: VG1; medium.
- [x] [Review][Patch] P18 — Protect F# and VB project recognition [tools/proprietary-surfaces/v1/test_census.py:135]. Restricting `PROJECT` to `.csproj` leaves all fixtures and the real scan passing; an executable `.fsproj` then disappears. Parameterize executable and orphan-project coverage over the supported `.csproj`, `.fsproj` and `.vbproj` formats. Sources: VG2; medium.
- [x] [Review][Patch] P19 — Refuse unsafe publication paths instead of skipping them [tools/proprietary-surfaces/v1/check.py:710]. Literal `dotnet publish /tmp/Neutral.csproj` and `dotnet publish ../Neutral.csproj` both pass without candidates or diagnostics because the loop explicitly continues on these paths. Enforce the spec's unsafe-path refusal and retain an actionable diagnostic. Sources: AA2; medium.
- [x] [Review][Patch] P20 — Associate workflow matrix projects with publication commands [tools/proprietary-surfaces/v1/check.py:704]. A workflow `ship.yml` with matrix project `missing/Neutral.csproj` and `dotnet publish ${{ matrix.project }}` passes without an orphan candidate: expression removal disconnects the command from the literal project. Track supported local workflow substitutions or refuse unresolved publication targets. Sources: AA5; medium.

#### Individual triage verdicts

IDs below are sequential across the four independent layers. Each verdict was
rendered before grouping; repeated findings retain their own evidence and route.

| ID | Source | Verdict | Verified outcome | Route |
|---|---|---|---|---|
| 1 | blind-hunter / BH1 | medium | A Web/AppHost SDK name in a comment suppresses a neutral executable; a disposable committed fixture returned passed with no surfaces. | P2 |
| 2 | blind-hunter / BH2 | medium | A literal local XML import setting OutputType=Exe is absent from the metadata candidate set and the scan passes. | P3 |
| 3 | blind-hunter / BH3 | medium | Targets run before project-defined import properties; the reproduced local executable declaration is omitted. | P4 |
| 4 | blind-hunter / BH4 | medium | Removing explicit PackageId in favor of AssemblyName admits the new implicit package and makes only the old identity stale. | P5 |
| 5 | blind-hunter / BH5 | medium | The registration regex excludes the argument-free F#/VB attribute terminator; the reproduced F# consumer remains approved. | P6 |
| 6 | blind-hunter / BH6 | medium | Follow-up compilation and an actual MCP initialize response establish a usable direct server; its identical source adds no census signal. The initial factory-only evidence was strengthened before this verdict. | P7 |
| 7 | blind-hunter / BH7 | high | Hash-bound empty-revision and incomplete-v2 authority files both admit a new allowance without approved lineage; parent reproduction independently confirmed the empty-revision case. | P1 |
| 8 | blind-hunter / BH8 | medium | A recursive Compile glob omits its zero-directory source; modifying that file leaves the source-bound allowance approved. | P8 |
| 9 | blind-hunter / BH9 | medium | A literal build-push action tag with push enabled yields no publication candidate. | P9 |
| 10 | blind-hunter / BH10 | medium | A valid flow-mapping container image yields no publication candidate. | P10 |
| 11 | edge-case-hunter / EC1 | medium | Release MSBuild selects Exe while the conditional-alias census fixture passes with no surfaces. | P11 |
| 12 | edge-case-hunter / EC2 | medium | Project-relative imported Compile source is absent from the closure and its subsequent mutation passes. | P12 |
| 13 | edge-case-hunter / EC3 | medium | Unconsumed metadata declaring OutputType through a local alias evades the unresolved-import fallback. | P13 |
| 14 | edge-case-hunter / EC4 | medium | The uppercase .PROPS import is a real MSBuild executable declaration but is excluded by the same metadata filename filter as finding 2. | P3 |
| 15 | edge-case-hunter / EC5 | medium | Empty mcpServers shadows a populated supported servers section; the reproduced scan has no candidates. | P14 |
| 16 | edge-case-hunter / EC6 | medium | Docker --tag=value yields no publication candidate in the reproduced committed script. | P15 |
| 17 | edge-case-hunter / EC7 | medium | An executable shell script without an extension is outside interesting paths despite its literal publication command. | P16 |
| 18 | verification-gap / VG1 | medium | Pre-verified mutation: removing independent container identity detection leaves all 53 tests and the real scan passing while the sole-signal fixture stops rejecting. | P17 |
| 19 | verification-gap / VG2 | medium | Pre-verified mutation: removing F#/VB project recognition leaves all tests and the real scan passing while an executable F# project stops rejecting. | P18 |
| 20 | acceptance-auditor / AA1 | medium | The auditor independently reproduced the XML-import executable omission; this violates inherited-metadata coverage and AC1. | P3 |
| 21 | acceptance-auditor / AA2 | medium | Absolute and parent-relative publication paths are explicitly skipped and return passed, contrary to the unsafe-path matrix. | P19 |
| 22 | acceptance-auditor / AA3 | medium | Ordinary Docker and buildx equals-form tags both evade literal-container publication discovery under AC1. | P15 |
| 23 | acceptance-auditor / AA4 | medium | Inline Compose images and Kustomize newName entries both evade the line-oriented image scanner under AC1. | P10 |
| 24 | acceptance-auditor / AA5 | medium | A missing matrix project used by dotnet publish yields no orphan candidate, violating absent-project workflow coverage. | P20 |

#### Review verification

- `python3 -m unittest discover -v -s tools/proprietary-surfaces/v1 -p 'test_*.py'` — 53 passed.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s scripts/tests -p 'test_*.py'` — 195 passed.
- `python3 tools/proprietary-surfaces/v1/check.py --output /tmp/mcpcli-story-5-6-review-census.json` — passed; 17 root references, 460 surfaces, 39 stale allowances, no errors. Passing the current pins does not settle the reproduced negative cases above.
- Parent disposable Git fixtures independently confirmed the XML/uppercase imports, SDK comment, targets ordering, conditional alias, implicit package rename, both source-closure gaps, F# attribute, dual server sections, container action/YAML/tag formats, extensionless script, unsafe paths, matrix publication and malformed authority outcomes.
- The direct-server follow-up built against ModelContextProtocol.Core 2.4.0 with zero warnings/errors and received a successful stdio initialize response with empty stderr. Inspected reference code was never executed; this probe used newly constructed disposable source.

#### Rejected

None.

## Implementation Notes

- Added a committed-object census with data-only classifications, separate exact project/package/tool/container identities, static inherited/imported metadata and registration discovery, and fail-closed metadata/policy checks.
- Preserved the original census baseline and inventory approval bytes. The option-A 1.0.1 amendment binds complete fixture-directory source closures, including additional-file detection; removals and exception replacement remain versioned operations.
- CI initializes only committed root declarations with recursion disabled. Paired staging/publication require the census job and all three executed steps; bootstrap and publication-stage job maps remain separate.
- Local checks and hashes are recorded in `evidence/story-5-6/verification.md`; sprint status is `review` for the build workflow's review phase.
- Build review pass 1 applied all 13 patch groups, closed the parent P1 follow-up, and recorded six current-pin non-surface test/qualification observations without a directory exemption. Final verification: 53 census tests, 195 release tests, all 17 root references and all three mutation probes pass. No findings were deferred. See [reviewed evidence](evidence/story-5-6/review-pass-1/verification.md); the initial evidence remains preserved.

## Spec Change Log

- 2026-11-11 — User answered "yes" to the offered next steps; proceed with the first scope: generic resolution of the five inspection cases before owner disposition of rejected identities. This authorizes implementation and verification within the existing committed-source boundary, not a new allowance or qualification. E01–E05 and their exact source pins/paths remain defined by [the retained packet](evidence/story-5-6/handoff-verification-20261110/disposition-packet.json). Resolve what committed source proves; retain coverage errors for unresolvable runtime or generated targets, with complete observations from independently inspectable files. Prior baseline, inventory, approval and amendment bytes remain preserved.

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

## Resumed implementation — 2026-11-10

P1–P20 are implemented with focused regressions and guard-removal controls.
The census suite passes 76 tests; the saved release regression run passes 195
tests; all 20 mutation probes fail their covering tests when the guard is
removed. README and the census guide describe the corrected behavior.

The real committed-pin census exits 1. All 17 roots are accounted for, with
12 rejected observations (six effective package identities, three previously
shadowed developer server definitions, two Kustomize image identities and one
registration-signal drift). Projects additionally fails on an unsafe project
publication path in its committed CI workflow. The exact identities, pins,
paths and signals are in [acceptance blockers](evidence/story-5-6/patch-pass-2-20261110/acceptance-blockers.json).
No allowance, approval, prior amendment, gitlink or reference content was changed.

This supersedes earlier passing-current-pin completion claims for the updated
scanner. Story/sprint completion remains blocked on disposition of these
observations and the unsafe upstream publication path; no new owner authority
is inferred. Independent review is in progress.

### Resumed build review — 2026-11-10

All three layers completed. Each finding was assessed before grouping. The 17
findings below are verified and route to 14 small patches within existing
scanner behavior and test coverage; no public runtime surface is added. The
implementation subagent was lost in the server restart, so patches are applied
in the parent session. No finding is deferred or rejected.

| ID | Verdict | Verified evidence | Route |
|---|---|---|---|
| BH1 | high | A v1 receipt is accepted based on current-parent commitment plus its own fixture data; it need not match the retained legacy binding. | R1 |
| BH2 | medium | sdk_identities scans Sdk attributes on Import elements, including a demonstrated false conditional import. | R2 |
| BH3 | medium | The nonempty-text check ignores an empty PackageId assignment and retains the previous approved identity. | R3 |
| BH4 | medium | PackAsTool has no effective ToolCommandName default; changing AssemblyName under a fixed PackageId changes the actual tool identity unnoticed. | R4 |
| BH5 | medium | Expanded PackageReference/ProjectReference strings are classified without splitting their MSBuild item-list semicolons. | R5 |
| BH6 | medium | Compile item expressions are accepted as literal paths and yield an empty linked-source set instead of resolution or refusal. | R6 |
| BH7 | medium | Unresolved directory globs find no literal metadata filename, and unconsumed fallback only reads props/targets. | R7 |
| BH8 | medium | Shell extraction uses physical lines, separating the demonstrated Docker command from its literal tag. | R8 |
| BH9 | medium | Docker push reads following[1] as the image, so the demonstrated --all-tags option masks the real image. | R9 |
| BH10 | medium | Registration matching is case-sensitive for VB source despite its case-insensitive attribute identifiers. | R10 |
| EC1 | medium | Import conditions do not propagate into the imported property definitions; later Library imports erase an Exe branch. | R11 |
| EC2 | medium | Independent committed fixture and MSBuild evaluation confirm the unresolved XML-directory glob omission described by BH7. | R7 |
| EC3 | medium | Independent committed fixture confirms a continued Docker command has no image candidate. | R8 |
| EC4 | medium | The literal-project regex extracts a trailing basename from quoted paths with spaces; distinct complete targets share an approval key. | R12 |
| EC5 | medium | The demonstrated conditional-import omission violates the all-unapproved-surfaces refusal claim at the same branch. | R11 |
| VG1 | medium | Pre-verified isolated factory mutation leaves all 76 tests green because the current factory case also matches transport construction. | R13 |
| VG2 | medium | Pre-verified recursive-glob mutation restricted to zero directories leaves all 76 tests green; nested added source lacks a covering assertion. | R14 |

### Final resumed outcome — 2026-11-10

Applied R1–R14 from the resumed review. Verification now passes 85 census
tests, 195 release regression tests and 34 guard-removal controls. Every I/O
matrix row has passing executed coverage. The exact historical v1 receipt is
additionally frozen in a baseline-hash-bound registry; no original allowance,
approval or amendment bytes changed.

The updated real scan exits 1: 17 roots are accounted for, with nine rejected
observations and five inspection errors. Error roots have incomplete candidate
results; earlier observed failures remain retained. All source pins, exact
commands and current findings are in the [final verification](evidence/story-5-6/patch-pass-2-20261110/verification.md).
The story and sprint remain `in-progress`: current-reference release acceptance
requires owner disposition or further approved source/qualification work. The
build workflow halts at the failed verification gate.

### Implementation handoff verification — 2026-11-10

Re-ran verification at `09ba8ce1ada39de9cd3f5073137cc399979e62d1`: 85 census
tests, 195 release regressions and all 34 guard-removal controls pass. All five
I/O matrix rows have fresh passing executed coverage. The committed-pin scan
exits 1 with 17 roots accounted for, nine current rejected observations and
five inspection errors; error roots retain incomplete candidate results.

The new [handoff verification](evidence/story-5-6/handoff-verification-20261110/verification.md)
preserves all prior evidence. Its [disposition packet](evidence/story-5-6/handoff-verification-20261110/disposition-packet.json)
binds all twelve prior/current rejected identities and all five inspection
errors to exact root pins, committed blob hashes, applicable historical
inventory rows and approval limits, same-path active allowances, and specific
missing decisions. No checker, active allowance, approval, prior amendment,
dependency, reference content or gitlink changed. This evidence grants no new
authority; the story and sprint remain `in-progress` pending owner disposition
or approved generic source-resolution work.
The [fresh evidence secret scan](evidence/story-5-6/handoff-verification-20261110/secret-scan.json)
is clean: 20 files checked, zero findings and zero inspection errors.


### Bounded source-resolution implementation — 2026-11-11

Implemented the approved generic E01–E05 source-resolution work. Committed
Compile aliases and byte-preserving Copy inputs retain source provenance;
finite literal shell variables, ordered loops, function arguments and scoped
working directories resolve without executing inspected code. Generated or
runtime source and exact nested targets remain actionable coverage errors.
Individual source and allowance-closure failures preserve other observations
and mark the root partial, with no stale claims from incomplete coverage.

The [new verification packet](evidence/story-5-6/source-resolution-20261111/verification.md)
records 117 passing census tests, 195 passing release regressions,
70 executed guard-removal controls and all five matrix rows. The real
committed-pin scan exits 1: 17 roots are accounted for, 5 are complete,
with 14 rejected observations and 50 coverage errors. E04 resolves;
E01 yields two exact orphan observations; E02 retains generated-source refusal;
E03/E05 identify exact nested targets and refuse nested inspection. Policy,
approval, original inventory, amendment and gitlink bytes remain unchanged.
The story and sprint remain `in-progress` while current-reference acceptance
is unsuccessful; no owner disposition or additional authority is inferred.

### Bounded source-resolution review — 2026-11-11

All three independent layers completed before triage. Every submitted finding
received an individual verdict before grouping; parent reproductions confirm
the concrete outcomes. All 19 findings route to 18 patches in existing census
behavior, with no new runtime surface or allowance. No finding is deferred.

| ID | Verdict | Evidence | Route |
|---|---|---|---|
| BH1 | medium | Inline loop bodies are consumed without inspecting their original line; the committed fixture passes with no observation or error. | S01 |
| BH2 | medium | A quoted dotnet executable has no regex invocation match; its committed orphan publication passes silently. | S02 |
| BH3 | medium | Docker global options and image push place the verb outside following[0]; both committed neutral-image fixtures pass silently. | S03 |
| BH4 | medium | Two quoted matrix alternatives become one space-concatenated orphan identity instead of the two present ordinary projects. | S04 |
| BH5 | medium | Unquoted heredoc command substitutions are skipped; a committed literal dotnet publication inside one passes silently. | S05 |
| BH6 | medium | An unrelated neutral library suppresses attacker/neutral:latest by basename; its exact container publication vanishes. | S06 |
| BH7 | medium | A missing literal local import has zero matches and no prerequisite diagnostic; the committed fixture passes. | S07 |
| BH8 | medium | A 1,100-property chain raises uncaught RecursionError instead of retaining the sanitized coverage report. | S08 |
| BH9 | high | An npm bin definition in another repository borrows the named Builds tool identity and is approved without an exact allowance. | S09 |
| BH10 | medium | Every ancestor props file is inspected even when a nearer file stops MSBuild discovery; the shadowed root Exe marks the library executable. | S10 |
| EC1 | medium | Recursive finite-loop execution resets conditional state and overwrites the possible pre-branch publication target. | S11 |
| EC2 | medium | Unknown loop execution discards its resulting directory, so a later publication trusts the pre-loop directory only. | S12 |
| EC3 | medium | read/unset/declare state changes leave a previous literal target trusted; the runtime-read parent fixture approves that old identity. | S13 |
| EC4 | medium | Single-quoted function arguments lose quote provenance and expand a variable that the shell passes literally. | S14 |
| EC5 | medium | The shebang comprehension reads executable blobs outside per-source recovery; a missing executable blob discards the rest of its root. | S15 |
| VG1 | medium | Pre-verified mutation changes report-write failure to exit zero while all 117 tests pass; CI relies on that exit status. | S16 |
| Parent1 | medium | FLAG=value dotnet publish missing/New.csproj is swallowed as one assignment; the full committed fixture returns passed with no observations. | S17 |
| Parent2 | medium | A previously allowed missing/Old.csproj remains approved after read -r target; no unknown-target error is emitted. | S13 |
| Parent3 | medium | Actual scans with PYTHONHASHSEED=1 and 2 produce different error rules for the same committed Parties metadata; source-alternative iteration is unordered. | S18 |

S01 inline loops; S02 executable quoting; S03 Docker verbs/options; S04 matrix alternatives; S05 executable heredocs; S06 exact container provenance; S07 missing local imports; S08 property depth; S09 tool consumption versus definition; S10 nearest build metadata; S11 conditional loop state; S12 unknown-loop directories; S13 shell state writers; S14 quoted function arguments; S15 executable-blob recovery; S16 report-I/O boundary verification; S17 prefixed environment assignments; S18 deterministic diagnostics.

All patches are pending. Existing owner decisions and current-reference acceptance remain unresolved.

Patch validation found two further concrete regressions; each is verified before grouping.

| ID | Verdict | Evidence | Route |
|---|---|---|---|
| Parent4 | medium | A literal forged @matrix-projects encoded token is decoded as an approved target even outside a workflow; the committed fixture passes under the unrelated approval. | S19 |
| Parent5 | medium | Excluding all unconsumed Directory.Build.props/targets by filename skips even malformed XML; the committed malformed default-metadata fixture passes. | S20 |

S19 removes forgeable matrix authority; S20 preserves unconsumed metadata validation and classification while retaining nearest-file project discovery. Both are pending patches.

Final state-writer validation confirmed two remaining concrete cases after the first complete parent verification; its passing evidence is retained under `source-resolution-review-20261111/attempts/parent-final-1/`.

| ID | Verdict | Evidence | Route |
|---|---|---|---|
| Parent6 | medium | printf -v target changes the shell variable, but a later publication still approves its previous literal value; full committed fixture passes with no errors. | S21 |
| Parent7 | medium | Multiple assignments on one line update only the first variable in the resolver, allowing a later target assignment to retain an unrelated old approval. | S22 |

S21 refuses unsupported printf shell-state writes; S22 resolves or invalidates every assignment on a multi-assignment line. Both are pending patches in the existing state model.

| ID | Verdict | Evidence | Route |
|---|---|---|---|
| Parent8 | medium | An ordinary present web project declaring ContainerRegistry=trusted.invalid and ContainerRepository=neutral still has trusted.invalid/neutral:latest rejected; the complete declared source association is lost. | S23 |

S23 recognizes exact declared registry/repository image provenance for ordinary projects, preserving refusal of other registries and every project carrying MCP/CLI signals. This changes no allowance.

### Reviewed source-resolution outcome — 2026-11-11

Applied S01–S23, closing all 24 individually triaged findings without deferral.
Fresh parent verification passes 142 census tests, 195 release regressions, all
110 guard-removal controls and all five matrix rows. Complete report bytes
match across Python hash seeds 1 and 2. Original evidence and policy bindings
remain unchanged.

The real scan exits 1: 17 roots are accounted for, 3 are fully inspected,
with 540 observations, 112 rejections and 110 coverage errors. The
[final verification](evidence/story-5-6/source-resolution-review-20261111/verification.md)
and [current blocker packet](evidence/story-5-6/source-resolution-review-20261111/acceptance-blockers.json)
bind the exact findings and commands. E04 target enumeration resolves, while
its imported metadata still prevents qualification; E02 currently stops on an
unsafe import before generated provenance. Unresolved metadata and nested or
runtime source remain refused, without a new allowance or owner authority.
Story and sprint remain `in-progress`; the workflow halts at unsuccessful
current-reference acceptance. No local commit or publication was performed.

### Implementation resume verification — 2026-11-11

The requested implementation and all recorded patches are already present at
`ec458664b0218d07357091b5a5ea12897154db2a`. Fresh serial verification passes
142 census fixtures, 195 release regressions, all 110 guard-removal controls
and all five matrix rows. Complete report bytes match across Python hash seeds
1 and 2. Checker, census tests and both READMEs match the preceding reviewed
packet; all nine policy bindings and its 111 receipt-covered files are unchanged.

Seven root pins have changed since that packet. The current committed-pin
scan exits 1: all 17 roots are accounted for, 3 are fully inspected, with
542 observations, 114 rejections, 111 coverage errors and 4 stale allowances.
The [fresh verification](evidence/story-5-6/implementation-resume-20261111/verification.md)
and [source-bound blockers](evidence/story-5-6/implementation-resume-20261111/acceptance-blockers.json)
retain the exact commands, root revisions, findings and integrity evidence.
No implementation, allowance, approval, amendment, dependency, reference or
gitlink changed. No new authority is inferred; story and sprint remain
`in-progress` while current-reference acceptance is unsuccessful.


### Continued coverage resolution — 2026-11-11

Implemented bounded generic command-token recognition, literal heredoc
boundaries, redirected loop terminators, balanced `elif` state, committed-script
path locators and bounded JSON object-array/wrapper traversal. Runtime/generated
inputs, unsupported PowerShell evaluation, external imports/Compile inputs and
nested repositories retain their refusals. No policy, reference, gitlink,
dependency or owner authority changed.

The [new verification](evidence/story-5-6/coverage-resolution-20261111/verification.md)
passes 158 census fixtures, 132 executed guard-removal controls, 195 release
regressions and all five matrix rows. Complete report bytes match across hash
seeds 1 and 2. Policy and prior evidence remain unchanged; parent audit verified
all 125 receipt-bound packet files and all four final implementation/README
hashes. Earlier attempts are retained.

The [coverage assessment](evidence/story-5-6/coverage-resolution-20261111/coverage-assessment.json)
accounts for all 111 original errors once across 12 root causes: 101 diagnostics
remain, 8 sources have no remaining error, and 2 original diagnostics resolve
while their sources remain partial. Eight newly reported errors remain refused.
The fresh committed-pin scan exits **1**, with 17 roots accounted for, 2 complete,
548 observations, 120 rejected observations, 109 coverage errors and 2 stale
allowances. These observations do not establish a count of new tools.

The [decision packet](evidence/story-5-6/coverage-resolution-20261111/decision-packet.md)
separates scanner limitations, protected source boundaries, embedded-data
ambiguity, exact owner dispositions and the absence of a proven active upstream
defect. Its next concrete scanner step is a bounded committed-manifest selector
for the source-bound ChatBot release packaging case. This grants no approval
or additional scope. Story and sprint remain `in-progress` at unsuccessful
current-reference acceptance. No staging, commit or push was performed.
