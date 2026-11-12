---
title: '5.6 Reject new proprietary surfaces in CI'
type: 'feature'
created: '2026-11-10'
status: 'done'
baseline_commit: 'c9a46a11a8317dd1903e3a3ef2f27791942b316a'
route: 'dispatch'
review_loop_iteration: 1
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
- [x] `tools/proprietary-surfaces/v1/check.py`, `test_census.py`, README — owner decision 2026-11-12, "Extend the excuse to Compile items". A Compile `Include` of exactly one leading `$(P)` plus a literal suffix excuses an absent source only when every producing definition of `P` is conditional and proven unreachable. A present source is always read, and a case variant is never absent. Covered by `test_guard_excuse_carried_guard_excuses_absent_compile_sources_only`. After independent review it applies only to a direct Include with an absent cross-tree literal. Its proofs must come from facts outside the repository, and `P` must keep a reachable definition. Nine executed guard-removal controls are all caught.
- [x] `evidence/story-5-6/owner-amendment-renewal-20261112/` — owner decision 2026-11-12, "Build a 1.0.5 renewal". It renews the 20 revision-bound exclusions and 2 source-bound allowances of 1.0.3/1.0.4 at `ab4d2dc`. Review first, then exact-byte owner approval, then `assemble-renewal.py --write "<label>"`, then rerun the fixtures, release regressions and real scan. Reviewed, approved and written; see Spec Change Log.
- [x] `tools/proprietary-surfaces/v1/check.py` and `test_census.py` — owner decision 2026-11-12 ("Checker fix + new version"). A file passes when any exact-file exclusion for its path lists its hash, and a file-bound path never falls back to a directory-scope exclusion. Covered by `test_later_exact_file_exclusion_approves_another_byte_version`, with an executed guard-removal control that fails under the old first-match lookup.
- [x] ~~`evidence/story-5-6/owner-amendment-draft-20261112/` — census amendment 1.0.3 draft~~ superseded before approval by the committed 1.0.3/1.0.4 (`ba1fa6f`, `32bbd5b`) and the pin move in `ab4d2dc`; kept as review evidence. Original task: covering all 30 rejected identities and the Builds audit drift. Owner decisions 2026-11-12: "Review first, then approve"; "Add as PE03 tooling" for `Hexalith.Platform.Composition`. Independent review first, then ask for exact-byte owner approval of `authorization.draft.json`.
- [x] ~~After that approval only: write `tools/proprietary-surfaces/v1/amendments/1.0.3.json`~~ not applicable: 1.0.3 already exists in the chain. Original task: and its v2 receipt from the approved bytes unchanged, append `amendments.json`, recording the selected label verbatim. Then rerun fixtures, release regressions and the real scan, and retain the evidence.
- [x] `tools/proprietary-surfaces/v1/check.py` — re-implement the user-approved (2026-11-11) `Exists()` guard rule as an excuse only (review loop 1 supersedes the reverted pruning version). A guard may only excuse an import target that is missing from every inspected tree and would otherwise be refused (`unavailable-local-import`, `unsafe-import-path`). It never skips a present target, never removes a property alternative and never changes classification. An absent target is excused when either (a) the import's evaluated condition (its own `Condition` plus an enclosing `ImportGroup` `Condition`) has a conjunct that proves false, or (b) the import's `Project` is exactly one `$(P)` and every definition of `P` producing that value is conditional and proves false through its own or enclosing `PropertyGroup` condition. A conjunct proves false when it is `Exists(p)` with every expansion of `p` proven absent, or `!Exists(p)` with every expansion proven present. Only balanced top-level `and` conjunctions with no top-level `or` count, and a quoted argument cannot span quotes. An argument proves nothing when it contains an unresolved `$(` or a `%XX` escape, or uses a property that is only conditionally defined (it may be empty) or is also defined inside a `Target`. Relative paths in `Import`, `ImportGroup` and `PropertyGroup` conditions resolve from the declaring file; in a property element's own condition they resolve from the entry project's directory (corrected by the loop-1 `dotnet msbuild` probe, L12). Present means a committed regular blob or directory in the inspected root, or in a root-declared reference at its pin, never under a nested gitlink. Absent means no case-insensitive match in that model, and is never a tree root or the parent workspace root. `Choose`/`When` and `Target` conditions prove nothing. Record nothing new in policy.
- [x] `tools/proprietary-surfaces/v1/check.py` — nested-pin review fixes:
  1. A substituted file's import value that keeps an unresolved `$(` is refused as `unsafe-import-path` with its label as `target`; it is never name-matched against inspected-root metadata.
  2. `submodule_urls` reads only `submodule "<name>"` sections with safe paths, as `declarations()` does.
  3. A substituted blob missing from its object store fails as `nested-object-unavailable` or `workspace-object-unavailable`, with the requested label as `target`.
  4. A fixture allowance's compilation closure includes substituted members as `{path: <requested label>, sha256}`, so a changed, added or removed cross-tree member is source drift.
  5. Amendment fixture validation runs without workspace context, so any cross-tree path it meets is refused and policy loading fails closed.
  6. Every census Git call adds `-c protocol.allow=never`, drops the repository-local variables listed by `git rev-parse --local-env-vars`, and sets `GIT_NO_REPLACE_OBJECTS=1` beside `GIT_NO_LAZY_FETCH=1`.
- [x] `tools/proprietary-surfaces/v1/test_census.py`, both READMEs and a new `evidence/story-5-6/guard-excuse-review-20261111/` packet. Each regression asserts the full error document and both output streams.
  - **Excuse forms:** own-condition `Exists`/`!Exists`; a carried `$(P)` guard; generic Tenants- and Commons-shaped fallback chains with zero errors.
  - **Never skipped:** a present import and a classification property under a census-false guard (`Exists('obj/project.assets.json')`, `!Exists` on a present workspace path) are still visited and retained.
  - **Prove nothing:** `!Exists` on a nested path; top-level `or`; quote-spanning `Exists('a') == Exists('b')`; `%XX`; conditionally defined and `Target`-defined properties; the parent workspace root; a case-only difference; a relative property condition in an imported file, resolved from the project directory.
  - **Verification gaps:** a committed but file-excluded target that needs the excuse (VG1); a substituted file's guard naming a second-hop path (VG2); an allowance closure refusal carrying `target`, without patching (VG3); an invalid UTF-8 substituted blob (VG4); a symlinked sibling root and a nested tree-oid (VG5); an scp-style identity match plus a drive-letter refusal (VG6).
  - **Also cover:** `crossTreeReads` on a refusal path; amendment validation refusing a cross-tree fixture; a strict-length `assert_source_errors`.
  - Add guard-removal controls for every new rule.
  - **READMEs:** replace the pruning text with the excuse rule; state that proofs model the parent workspace; fix the `!Exists` contradiction; rewrap long lines.
  - **Verification:** repeat the nested-pin packet's verification set, with before/after accounting against `exists-guard-resolution-20261111`. Preserve prior evidence and grant no authority; do not stage, commit or push.
- [x] `tools/proprietary-surfaces/v1/check.py` — implement the user-approved (2026-11-11) cross-tree resolution for MSBuild imports and Compile item sources only. **Workspace rule:** a path escaping the inspected root reference is normalized against the parent revision tree; inside a root-declared gitlink it is read at that root's pin; if absent and the import is `Exists()`-conditioned on that exact path, it is absent; anything else, including a path above the parent root, keeps `unsafe-import-path` / `unsafe-or-nested-compile-source`. **Nested rule:** a path inside a nested gitlink resolves at that exact nested commit, read from the single root-declared reference whose `.gitmodules` URL equals the nested entry's URL at the same pin (trim one trailing `/` and one trailing `.git`; host case-insensitive; relative URLs never match). No unique match → `nested-pin-unresolvable:<path>`; commit missing from that checkout's object store → `nested-object-unavailable:<path>`. Never initialize, fetch, check out or execute anything. Allow one cross-tree hop per resolution chain; a further escape or gitlink inside the substituted tree keeps the existing refusal. Record each cross-tree read's repository, commit, path and blob hash in report provenance. Publication targets inside nested gitlinks keep `nested-publication-target`. No module names, paths or counts in logic.
- [x] `tools/proprietary-surfaces/v1/test_census.py` — disposable Git fixtures: escaping import resolved into a sibling root at its pin; absent `Exists()`-conditioned escape; escape above the parent root; nested import resolved through a same-URL root at a nested pin that differs from the root pin; URL normalization match plus relative, ambiguous and missing-entry refusals; missing nested commit; second-hop refusal; nested Compile source; report provenance; `OutputType=Exe` arriving through each rule. Executed guard-removal controls for every new refusal; assert full stdout/stderr and error documents.
- [x] `tools/proprietary-surfaces/v1/README.md`, `README.md` and `evidence/story-5-6/nested-pin-resolution-20261111/` — document both rules and the CI precondition (root references are full clones, so nested pins must be reachable in them). Run fixtures, release regressions, all five matrix rows, determinism across two hash seeds and a fresh committed-pin scan. Record before/after blocker accounting against `manifest-selector-resolution-20261111`, including how many prior source-file rejections now associate with an approved project. Retain the final report once and record repeat runs as hashes. Preserve all prior evidence, policy and inventory bytes; add no allowance, exception, exemption or approval. Keep story/sprint `in-progress` unless the scan passes; do not stage, commit or push.
- [x] Continue from `evidence/story-5-6/coverage-resolution-20261111/decision-packet.md` with bounded generic committed-JSON publication-target resolution in `tools/proprietary-surfaces/v1/check.py`. Start by inspecting the exact committed ChatBot `.github/scripts/pack-release-packages.sh`, `release-metadata.json` and `.inventory.packages[].project` at its root gitlink; record what those bytes prove. Support only the finite selector and ordered shell iteration semantics needed to enumerate those targets without executing jq or inspected code, and inspect each resolved project's metadata before qualification. Keep logic and fixtures generic: no module-specific names, paths, counts or branches. Preserve refusals for runtime/generated inputs, unsupported selectors, unknown mutations, unsafe paths and nested repositories. No nested initialization, reference/gitlink/dependency change or added allowance, exception, exemption or owner approval is authorized (user, 2026-11-11).
- [x] Add exact observation, error-document, stdout and stderr regression assertions in `tools/proprietary-surfaces/v1/test_census.py`; execute guard-removal controls for every new guard. Update both READMEs for the supported subset. Run relevant fixtures, release regressions, all five matrix rows and a fresh committed-pin scan; retain failed attempts and rerun final verification after any implementation change.
- [x] Preserve all prior evidence and create a separate `evidence/story-5-6/manifest-selector-resolution-20261111/` packet with exact commands/results, full canonical revisions, source blob/SHA-256 bindings, policy/prior-evidence/reference integrity checks and complete before/after blocker accounting. Include a concise decision packet distinguishing remaining scanner limitations, proven upstream defects (assert none without committed evidence of an active defect) and exact observations needing owner disposition, with the next concrete action for each. Run the evidence secret scanner. Keep story/sprint `in-progress` until acceptance succeeds; do not stage, commit or push.
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
- 2026-11-11 — User chose "nested-pin resolution" after the [manifest-selector packet](evidence/story-5-6/manifest-selector-resolution-20261111/decision-packet.md) showed the remaining blockers cascade from refused layout-fallback imports. For example, `references/Hexalith.EventStore` `src/Hexalith.EventStore.Admin.Cli` fails `unsafe-import-path:Directory.Build.props`, and 62 of its source files then become separate rejections. Parent investigation: the error comes from parent-relative fallbacks (`../references/…`, `../../references/…`), which in this workspace land in root-declared references. The nested alternative is skipped. The workspace rule reads those paths at root pins, which the frozen boundary already allows. The nested rule reads a nested pin from the same-URL root checkout. Example: EventStore `b882c1005050aaebfa70618b5a72c1c8be452281` nests Builds `11f8534fc89a2c4a18a984307e927abb6d6c7ff3`, reachable from root Builds `891886ddc60a9924d053bb74bf6bcc73e101b2ce` history (`origin/main`). CI clones root references fully. Scope: MSBuild imports and Compile sources only. No nested initialization, execution, allowance, exception, exemption or owner approval is granted.
- 2026-11-11 — User approved the `Exists()` guard extension and an independent review afterwards, following the [nested-pin decision packet](evidence/story-5-6/nested-pin-resolution-20261111/decision-packet.md). Targets: Tenants `Directory.Build.targets` at `019aa0a82d021e08475a68fc50eff3b6a0e6c111`, whose fallback guards sit on property definitions (20 errors), and Commons `src/libraries/Directory.Build.props` at `11555ace9efcae2928a00122dcba91243e5a8a1a`, whose import uses negated guards (4 errors). Parent soundness limit: CI initializes root references without recursion, so nested-gitlink paths are absent there. A `!Exists()` on a nested path therefore never proves a guarded element unreachable. Both cases still resolve through their workspace-present or outside-root-absent guards. No allowance, exception, exemption or approval is granted.
- 2026-11-11 — Review loop 1 (bad_spec R1, R2), triggered by BH3, EC3, BH5, BH8 and EC11 in the cross-tree resolution review below.
  - **Root cause:** the parent-written guard task let `Exists()` proofs drop present imports and classification-relevant property alternatives. That went beyond the user's approved phrasing, "carry `Exists()` guards from property definitions to the import that uses them". Proofs rest on committed-source facts that differ at real build time: generated `obj/`/`bin/` and ignored files, and standalone layouts without workspace siblings.
  - **Known-bad state avoided:** `<OutputType Condition="Exists('obj/project.assets.json')">Exe</OutputType>` disappeared from the census while every restored build is an executable.
  - **Amended:** the guard task now only excuses an absent, otherwise-refused import target. It adds proof-correctness rules (R4–R10) and nested-pin fixes (R2, R3, R11–R14). The test task covers R15–R21.
  - **Reverted:** the guard-pass code in `check.py`, `test_census.py` and both READMEs was reverted to the nested-pin state plus the upstream `94f5ee6`/`2723ce1` merge. 195 census fixtures pass after the revert. Nested-pin code is amended in place, not reverted, because its design had no bad_spec finding. The `exists-guard-resolution-20261111` packet stays as superseded evidence.
  - **KEEP:**
    - balanced top-level `and` splitting that returns nothing for `or` or unbalanced text
    - presence only from committed root content at root pins, never nested
    - guard scope limited to the element's own condition plus the enclosing `PropertyGroup`/`ImportGroup`
    - `Choose`/`When` and `Target` conditions prove nothing
    - generic Tenants- and Commons-shaped fixtures that end with zero errors
    - the 24-error accounting target (Tenants 20, Commons 4) as the expected outcome

- 2026-11-12 — The user answered "yes" to the offered next steps. As with the earlier "yes", that means the first offer: draft the owner amendment. The [owner draft](evidence/story-5-6/owner-amendment-draft-20261112/README.md) was built from the final-2 report, every hash read from committed blobs.
  - **Decisions:** "Review first, then approve"; "Add as PE03 tooling" for `Hexalith.Platform.Composition`; "Checker fix + new version" for the Builds audit snapshot, which the first-match exclusion lookup could not accept as a second approved version.
  - **Dry run:** the active policy plus the draft, run against the real pins, gives 0 rejected observations and 46 coverage errors (from 47). CI stays red on coverage errors, which no allowance can settle.
  - **No authority yet:** no receipt exists and the active policy is unchanged.
- 2026-11-12 — While the reviewed draft waited for the pins to settle (user: "Wait, rebuild at new pins"), another session made a series of changes:
  - it committed amendments 1.0.3 and 1.0.4 (`ba1fa6f`, `32bbd5b`), owner "Requesting user via the current release instruction", whose receipts record that human validation was explicitly bypassed;
  - it resolved the stash conflict in `check.py` and its README, keeping this story's safe guard code and its own `sourceRevision`-aware `omitted()`;
  - it committed everything with new pins for all 16 roots in `ab4d2dc`, and pushed.

  The draft is superseded. At `ab4d2dc` the scan reports 2 rejected observations and 22 errors: 20 `excluded-source-revision-drift` (1.0.3/1.0.4 exclusions bound to the earlier pins), 2 source-drifted allowances (Memories `tools/release-containers.json`, Platform `Composition`), and the 2 Tenants AppHost Compile fallbacks. 222 census fixtures pass.
- 2026-11-12 — User decisions at `ab4d2dc`: "Build a 1.0.5 renewal" and "Extend the excuse to Compile items".
  - **Compile rule:** the Tenants AppHost `$(HexalithPlatformRoot)\DaprSelfHostedMtls*.cs` fallbacks are excused, because their outside-root alternatives (Tenants `Directory.Build.props` lines 64–65) carry `Exists()` guards that prove false. No other observation changed.
  - **[Renewal draft](evidence/story-5-6/owner-amendment-renewal-20261112/README.md):**
    - 20 exclusions renewed at the new pins; 18 are byte-identical, and the FrontComposer and Projects workflows changed and were reviewed;
    - 2 allowance source renewals: the Memories `buildsSha`, and the Composition closure, which gains `WorksPreviewManagedRuntime.cs` from `eff9e909`.
  - **Dry run:** the active chain plus the draft, with the Compile rule, exits 0 at `ab4d2dc`: 0 errors, 0 rejected, all 17 roots passing.
  - **No authority yet:** no 1.0.5 receipt exists.
- 2026-11-12 — The owner selected "Approve hash-only 1.0.5 as owner (Recommended)", the hash-only renewal lists with canonical SHA-256 `46167f41a77406075acc9e396308c75b138ac32c5382a756b27bfc7a65452345`.
  - **Written:** `assemble-renewal.py --write` recorded the label verbatim, wrote `amendments/1.0.5.json`, its v2 receipt and the index entry, and loaded the chain at 1.0.5.
  - **Verification:** 223 census fixtures and 195 release regressions pass. The real committed-pin scan exits 0, identically for hash seeds 1 and 2, at `ab4d2dc`: 0 errors, 0 rejected observations, 17 of 17 roots passing ([post-approval verification](evidence/story-5-6/owner-amendment-renewal-20261112/post-approval-verification.json)).
  - **Outcome:** current-reference acceptance succeeds, and the story moves to done/review.
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

### Cross-tree resolution review — 2026-11-11

- **Scope:** code-only `ef80e45..884f65e` in `tools/proprietary-surfaces/v1/` and `README.md` (1,488 lines): nested-pin resolution plus the first guard pass. The upstream `fix(ci)` commits merged by another session are out of scope.
- **Process:** all three layers completed before triage, and each finding got its verdict before grouping. Parent checks: MSBuild Import docs; both fixture exemptions have zero cross-tree reads; peak RSS is 619 MB; Git is 2.53.0; the scan has no nested-pin errors.
- **Outcome:** 2 bad_spec entries trigger loop 1. The 19 patch entries are folded into the amended tasks, because the guard code is re-derived. 1 entry is deferred and 7 findings are rejected.

| ID | Verdict | Evidence | Route |
|---|---|---|---|
| BH1 | medium | MSBuild docs: relative paths in imported files resolve from the importing project, except the Import path. `unreachable()` used the declaring file for every guard. | R4 |
| BH2 | medium | `Exists('../..')` normalizes to `.`, which `matches()` reports absent; the guarded element is dropped. | R5 |
| BH3 | high | Uncommitted `obj/`/ignored paths are proven absent, so a conditional `OutputType=Exe` is dropped and never rescanned. | R1 |
| BH4 | low | Absence uses exact-case lookups; Windows/macOS `Exists()` matches case-insensitively. | R6 |
| BH5 | medium | A `!Exists` workspace-presence proof drops a property that a standalone build of the root keeps. | R1 |
| BH6 | low | No trace of skipped elements. The excuse-only rule hides no committed content, and a new report field adds surface. | reject |
| BH7 | low | `crossTreeReads` lack a consuming project; tracing needs a new report surface and causes no named failure. | reject |
| BH8 | medium | `compilation_closure` now filters to local entries. Cross-tree closure members, previously refused, pass unbound across pin bumps. | R2 |
| BH9 | low | Fixture validation resolves cross-tree at current pins. Current fixtures have zero cross-tree reads; the fix deletes the context argument. | R3 |
| BH10 | low | Peak RSS of the full scan is 619 MB, well within CI runners; the fix adds cache management. | reject |
| BH11 | medium | `GIT_NO_LAZY_FETCH` needs Git 2.44+, and inherited repository variables can redirect reads; the README states an unconditional guarantee. | R14 |
| BH12 | low | The v1 README says a negated `!Exists` proves nothing, contradicting the guard section; several lines are unwrapped. | R15 |
| BH13 | low | Missing and refused cross-tree paths share rule names, but `target` disambiguates; renaming changes the report contract. | reject |
| BH14 | medium | A local glob spanning a nested gitlink expands silently. That behavior predates this diff. | D1 |
| BH15 | medium | `submodule_urls` accepts any section with path/url, unlike `declarations()`. The reason-suffix suggestion is not adopted. | R12 |
| BH16 | medium | scp identity, nested non-commit pin, refusal-path provenance, context passing, an ImportGroup absent-`Exists` case and strict `zip` have no tests. | R21 |
| EC1 | medium | Probe confirmed: the parent workspace root is proven absent. | R5 |
| EC2 | medium | Probe confirmed: a conditionally defined property loses its empty alternative, so `!Exists('$(P)')` is proven present. | R7 |
| EC3 | high | Probe confirmed: a build-time-only path is proven absent and the guarded property is hidden. | R1 |
| EC4 | medium | `(.*?)\2` lets `Exists('a') == Exists('b')` match one bogus argument, which is then proven absent. | R8 |
| EC5 | medium | Probe confirmed the same wrong base directory as BH1. | R4 |
| EC6 | low | `%2E` escapes are compared literally; an existing file is proven absent. | R9 |
| EC7 | low | Global `-p:` overrides are a general static-census limit. Under the excuse-only rule they can excuse only absent targets. | reject |
| EC8 | low | `Resolver.text` digests before its try block, so a missing substituted blob raises an untargeted `git-object-unavailable`. | R13 |
| EC9 | medium | Probe confirmed the same pre-existing local-glob gap as BH14. | D1 |
| EC10 | medium | Probe confirmed: a `[remote "x"]` section with path/url resolves a nested pin that Git would ignore. | R12 |
| EC11 | medium | Probe confirmed: a sibling pin moves substituted bytes while a closure allowance stays approved. | R2 |
| EC12 | low | Same time-mixed receipt validation as BH9. | R3 |
| EC13 | medium | Same lazy-fetch version gap as BH11; `protocol.allow=never` closes it on every version. | R14 |
| EC14 | medium | Inherited `GIT_DIR`/object-directory variables redirect `git -C` reads; this change rebuilt that environment line. | R14 |
| EC15 | low | Probe confirmed: `Target` definitions replace values that later evaluation-time guards expand. | R10 |
| EC16 | medium | Probe confirmed: an unresolved `$(` import in a substituted file name-matches inspected-root metadata, an unreported second hop. | R11 |
| EC17 | low | Validation reads cross-tree bytes that never reach `crossTreeReads`; removed by R3. | R3 |
| EC18 | low | `workspace-object-unavailable` is an extra, documented, more specific rule name with no consumer impact. | reject |
| VG1 | medium | Pre-verified: `import_optional` is shadowed by `unreachable()`, so mutants survive. | R16 |
| VG2 | medium | Pre-verified: a substituted-file guard using `absent(label, None)` survives. | R17 |
| VG3 | low | Pre-verified: the allowance-error `target` is unprotected. | R18 |
| VG4 | low | Pre-verified: the `malformed-text` label rewrap is unprotected. | R19 |
| VG5 | medium | Pre-verified: the moved symlink and commit-type guards now protect cross-tree reads untested. | R20 |
| VG6 | low | Pre-verified: the scp identity branch is untested. The filed disposition was defer; a direct test is cheap. | R21 |
| VG-O1 | low | Works' nested URL case (`Chatbot`) differs from root `ChatBot`, but no current scan error reaches it, and the failure is fail-closed. | reject |

- **Routes, bad_spec:** R1 guards prune present content; R2 unbound cross-tree closure members.
- **Routes, patch (folded into amended tasks):** R3 context-free fixture validation; R4 condition base directory; R5 tree/workspace roots; R6 case-insensitive absence; R7 undefined property branch; R8 quote-bounded arguments; R9 escapes; R10 `Target` properties; R11 substituted unresolved imports; R12 submodule sections; R13 targeted missing blobs; R14 Git isolation; R15 README; R16–R21 tests.
- **Deferred:** D1, recorded in `deferred-work.md`.

### Cross-tree resolution review, loop 1 — 2026-11-11

- **Scope:** code-only `ef80e45` → working tree in `tools/proprietary-surfaces/v1/` and `README.md` (2,314 lines). It covers nested-pin resolution, the excuse-only guard, the R-fixes, and the upstream `2723ce1`/`94f5ee6` checker commits merged by another session.
- **Process:** all three layers completed before triage, and each finding was checked against the rows above first.
- **Parent checks:**
  - A `dotnet msbuild` probe shows a property element's own `Exists()` resolving from the entry project's directory. A `PropertyGroup` or `Import` condition resolves from the declaring file.
  - Fresh scans at `6ec91eb` and at `f223aaa` (three concurrent build-only commits, no pin moves) both report 47 errors and 30 rejections. The latter equals `guard-excuse-review-20261111/runs/final-1/census.json`.
- **Outcome:** no bad_spec or intent_gap entries, so no further loop. 19 patch entries, 2 deferrals and 7 rejections.

| ID | Verdict | Evidence | Route |
|---|---|---|---|
| BH1 | medium | Probe: `%73hared` in an import and its exact `Exists()` is excused as absent, and the importing project loses `executable-project`. MSBuild unescapes both. | L1 |
| BH2 | low | `Resolver.matches` absence uses exact-case lookups, so a case-variant workspace target is excused. The guard model already folds case. | L2 |
| BH3 | medium | A `dotnet build # note \` comment still joins the next physical command; bash does not continue inside comments. Pre-existing joining behavior. | D2 |
| BH4 | medium | Unresolved `GetPathOfFileAbove('Directory.Build.props', …)` imports skip `Directory.Build.*` candidates, so upward chains are neither read nor refused. Pre-existing. | D3 |
| BH5 | medium | An inherited `GIT_ALLOW_PROTOCOL` or `protocol.<name>.allow` overrides `-c protocol.allow=never`. Reproduced on Git 2.53. | L5 |
| BH6 | medium | `exists_arguments()` still uses `(.*?)\1`; `Exists('a/') == Exists('/../b')` yields a spanning argument that can match a target. | L3 |
| BH7 | medium | The two Tenants AppHost Compile refusals are real false positives, but excusing Compile items is outside the approved import-only intent. The "evidence out of date" claim is false: the `final-1` report equals the fresh 47-error scan. Surfaced as a user decision. | reject |
| BH8 | low | carried: same claim as BH6 of the first review (no trace of excused elements); code unchanged in that respect. | reject |
| BH9 | medium | `sdk_identities` grants an SDK identity from a lone `Sdk.targets` import. An `Aspire.AppHost.Sdk` targets import therefore suppresses `executable-project` on any Exe. | L4 |
| BH10 | low | Local rules (`unavailable-local-import`, …) carry no `target`; adding one changes established report rows and causes no named failure. | reject |
| BH11 | low | carried: same claim as BH10 of the first review (retained trees); peak RSS is now 770 MB, still well within CI runners. | reject |
| BH12 | low | The README says CI initialization "provides" nested pins; only commits reachable from remote refs are cloned. | L6 |
| BH13 | low | The README says every Git call adds the protections; `repository_variables()` does not, and its failure reads as `git-object-unavailable`. | L7 |
| EC1 | low | Probe: an import target normalizing to the parent workspace root `.` with an exact `Exists()` is excused as absent. | L8 |
| EC2 | medium | Probe: a label traversing a committed symlink directory is proven absent while MSBuild follows the link; a package identity was hidden. | L9 |
| EC3 | medium | Probe: a `;`-list or whitespace-padded import or `Exists()` argument is treated as one absent path, while MSBuild splits and trims it. | L10 |
| EC4 | low | `!Exists('file/')` with a trailing separator is false in MSBuild for a file; the census proves it present. | L11 |
| EC5 | medium | Same protocol override as BH5. | L5 |
| EC6 | low | `#` lines skipped in a `shell: cmd` workflow step still run under cmd. Rare, and the fix needs per-step shell context. | reject |
| EC7 | medium | Probe: a `#` line after a continued line, or a second `logical_commands` pass, merges the next publish into the comment. Whether `94f5ee6` introduced it is unverified. | D2 |
| EC8 | medium | Probe: a Dockerfile `RUN` continuation interrupted by a full-line comment hides its `dotnet publish`; Docker drops such comments before joining. | D2 |
| EC9 | medium | MSBuild probe confirms an enclosing `PropertyGroup` condition resolves from the declaring file. `refuted(guards, path)` resolves it from the project directory and misproves carried excuses. | L12 |
| EC10 | low | `target_defined` sees only Targets visited so far, but Targets run after evaluation; the reviewer's own probe shows no unsound excuse. | reject |
| EC11 | low | Same `repository_variables()` claim as BH13; that call reads no objects. | L7 |
| VG1 | medium | Pre-verified: deleting the committed-directory check in `Tree.absent` leaves 214 tests green. | L13 |
| VG2 | medium | Pre-verified: an unresolvable nested pin in a guard returning absent leaves 214 tests green. | L14 |
| VG3 | medium | Pre-verified: unreadable-root and no-workspace guard fallbacks flipped to true leave 214 tests green. | L15 |
| VG4 | medium | Pre-verified: the HopPresent case passes by root-name length coincidence; the boundary check is unprotected. | L16 |
| VG5 | low | Pre-verified: the shell comment-line skip in `execute()` is unprotected. | L17 |
| VG6 | low | Pre-verified: the `safe_label` tail validation is unprotected. | L18 |
| VG7 | low | Pre-verified: the `crossTreeReads: []` default on early-failing roots is unprotected. | L19 |
| VG-O1 | false | Its 50-error count came from its probe copies; fresh real scans at `6ec91eb` and `f223aaa` both report 47 errors. | reject |

- **Routes, patch:**
  - L1 `%XX` import values and exact arguments refused
  - L2 case-folded target absence
  - L3 one shared `Exists()` parser
  - L4 paired `Sdk.props`/`Sdk.targets`
  - L5 `GIT_ALLOW_PROTOCOL=''`
  - L6 nested-pin reachability wording
  - L7 `repository_variables()` wording and rule
  - L8 parent-root target
  - L9 symlink prefixes unknown
  - L10 `;`/whitespace values
  - L11 trailing-separator presence
  - L12 `PropertyGroup` condition base
  - L13–L19 tests
- **Deferred:** D2 comment-aware continuation joining; D3 upward `GetPathOfFileAbove` chains.
- **Spec correction:** L12 corrects the guard task's "other conditions resolve from the entry project's directory" to the element's own `Condition` only, on the probe evidence.

### Owner-amendment draft review — 2026-11-12

- **Scope:** the exact-file exclusion union in `check.py`, its test, and the draft files `authorization.draft.json`, `README.md`, `build-draft.py` and `dry-run-gate.py` (695 lines).
- **Process:** all three layers completed before triage.
- **Outcome:** every patch is applied in place. One finding is deferred and four are rejected. The draft canonical SHA-256 moved from `f8c44dea…` to `df0eda1a…`.

| ID | Verdict | Evidence | Route |
|---|---|---|---|
| BH1 | high | Verified at the pins: the four new PE06 identities hash the `servers`-section stdio `fluentui-mcp` entries, not the HTTP entry, which is already approved. The draft's reason strings said HTTP. | O1 |
| BH2 | medium | The draft holds only the five lists, but `load_policy` requires the amendment header keys, so "unchanged bytes become 1.0.3.json" cannot hold. | O2 |
| BH3 | medium | The scratch-baseline dry run never exercised chain loading (header, receipt binding, authorization equality, authority, exact removal). | O3 |
| BH4 | low | The README lacked the scan command, the scratch baseline hash, `not-included.json`/`secret-scan.json`, and the passing-root baseline (3, not 6). | O2 |
| BH5 | medium | `<Project/>` yields no observation either way, so `return False` after the hash check survived the new test. | O4 |
| BH6 | medium | Tool README step 5 did not describe combined same-path versions or the removed directory fallback. | O5 |
| BH7 | low | Superseded byte versions stay approved, and same-path entries are not checked for agreement. A removal operation or consistency guard adds surface; the README now documents accumulation and requires the same row and classification. | O5 |
| BH8 | medium | The Conversations exclusion hid four identities from the owner; the reason and README now name them. | O1 |
| BH9 | medium | PE03 and PE05 enumerations in hash-bound inventory 1.0.2 do not list `Composition` or the Builds release fixture. | D4 |
| BH10 | medium | Prefix picks accepted any identity, and "already approved" claims were unchecked. Memories has G4, not PS, rows on those files. | O6 |
| BH11 | low | Both scripts hard-coded the local account path. | O6 |
| BH12 | low | Ten stale allowances were left without comment; the README now lists them exactly, after checking the report. | O2 |
| BH13 | low | "Ships nothing" overstated the release fixture; it builds draft releases that are deleted afterwards. | O1 |
| BH14 | low | One decision label was paraphrased; all three are now quoted verbatim. | O2 |
| EC1 | low | Same accumulation as BH7. | O5 |
| EC2 | medium | Same unchecked prefix picks as BH10. | O6 |
| EC3 | low | The Builds fixture prefix mapped every non-project kind to an observation class. | O6 |
| EC4 | medium | The builder did not check that the report parent and gitlinks still match `HEAD`. | O6 |
| EC5 | low | The gate ignored `removeExceptions`. | O3 |
| EC6 | low | The gate removal used `assert` and an any-match test, not exactly one. | O3 |
| EC7 | low | The gate did not verify amendment index hashes. | O3 |
| EC8 | low | The gate could overwrite a live policy directory, or fail without an argument. | O3 |
| EC9 | medium | Same header mismatch as BH2. | O2 |
| EC10 | low | Same Memories G4-versus-PS wording as BH10. | O1 |
| VG1 | medium | Pre-verified: the non-scoped exact-file prefix match is unprotected, yet two active baseline exclusions use it. | O4 |
| VG2 | medium | Pre-verified: `additionalSha256` in the union is unprotected. | O4 |
| VG-O1 | medium | Same tool README gap as BH6. | O5 |
| VG-O2 | low | Same gate merge divergence as EC5 and EC6. | O3 |

**Routes:**
- **O1:** corrected reason strings (PE06 stdio `fluentui-mcp`, the four named Conversations identities, Memories G4 wording, the release fixture).
- **O2:** README mapping and reproducibility.
- **O3:** `assemble-amendment.py --rehearse`, a `load_policy` rehearsal outside the repository, plus a hardened gate.
- **O4:** the exclusion test made observable, with `additionalSha256` and non-scoped prefix cases; four executed guard-removal controls are all detected.
- **O5:** tool README step 5.
- **O6:** the builder checks exact expectations, active-policy claims and pins, and derives its root from its own location.
- **Deferred:** D4, inventory reconciliation, in `deferred-work.md`. BH7's removal operation and consistency guard are not adopted.

**Fresh results:**
- 220 census fixtures pass.
- The chain rehearsal loads version 1.0.3 with 522 allowances and 64 exclusions.
- The coverage dry run leaves 0 rejected observations and 46 coverage errors, with passing roots 3 → 6.
- The draft secret scan is clean.

### Compile excuse and 1.0.5 renewal review — 2026-11-12

- **Scope:** the Compile rule in `check.py`, its test and README, and the renewal draft folder (1,172 lines).
- **Process:** all three layers completed before triage.
- **Outcome:** every finding is valid and was patched in place. No bad_spec: the rule's approved intent stands, and the patches make the implementation match it.
- **Fresh results:**
  - 223 census fixtures and 195 release regressions pass.
  - Nine guard-removal controls on the corrected rule are all caught. Two redundant conditions were removed, because their removal was undetectable.
  - Both renewal variants dry-run with exit 0: 0 errors, 0 rejected, 17/17 roots passing.

| IDs | Verdict | Evidence | Route |
|---|---|---|---|
| VG1, BH1 | medium | `any(proofs)` and a dropped `bool(proofs)` survived the suite; a mixed-producer or late-bound value would be excused. | Q1 |
| VG-O1, BH3 | medium | The excuse reached item aliases and `Copy` outputs, which were previously refused as `dynamic-generated-compile-source`. | Q2 |
| VG-O2, EC1, EC2, BH2 | medium | A wildcard in the property value was excused: locally via `Tree.absent`, and cross-tree because the `absent` flag was discarded. | Q3 |
| EC3 | medium | With every definition of `P` refuted, the build sees an empty or environment value that the census did not model. | Q4 |
| EC4 | medium | A guard proven false only from the repository's own tree, for example `obj/`, can be true after a build. | Q5 |
| BH5, BH6 | low | The real Tenants shape (backslash suffix, `'$(P)' == ''` conjunction, chained fallbacks) and a cross-tree case variant were untested, and one branch asserted only rule names. | Q1 |
| EC5, EC6, EC7, EC8, EC14, EC15, VG-O4, BH7, BH16 | low–medium | The builder used plain Git, raised on missing roots, compared against older hashes, accepted stale reviewed entries, under-checked the closure, chain and root coverage, and bound no checker hash. | Q6 |
| EC9, EC10, EC13, BH8 | medium | `--write` did not enforce the approved bytes, recheck pins, write atomically or load the written chain. | Q7 |
| EC11, EC12, VG-O3, BH14 | low | The gate and assembler failed on a file `DIR`, and a docstring named the wrong script. | Q8 |
| BH4, BH9, BH10, BH12, BH13, BH15 | low–medium | README and receipt problems: intro and placement, a missing first-human-validation note and scope disclaimers, per-entry owners, incomplete change summaries, the 16-of-17 pin wording, and reproduction steps. | Q9 |
| BH11 | medium | Revision-bound renewal recurs at every pin move; the hash-only alternative was not offered. | Q10 |

**Routes:**
- **Q1:** pinned the proofs, the real-shape case and the full error documents.
- **Q2:** the excuse applies to a direct `Compile` `Include` only.
- **Q3:** an absent literal is required.
- **Q4:** at least one reachable definition is required.
- **Q5:** proofs must come from facts outside the inspected repository, and local sources are never excused.
- **Q6:** builder hardening.
- **Q7:** `--write` requires `--approved-sha256` and verifies the pins, `check.py` and the report, writes atomically and loads the chain.
- **Q8:** gate and assembler fixes.
- **Q9:** README and receipt accuracy.
- **Q10:** a hash-only variant, dry-run clean, offered to the owner.

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


### Committed-manifest selector resolution — 2026-11-11

Implemented the bounded generic committed-JSON row selector and ordered shell
read semantics required by the exact pinned packaging source. The selector
resolves all three declared projects; each selected project's metadata is
inspected without errors and emits no proprietary-surface observation. Other
repository sources retain their existing coverage and policy failures.

Fresh serial verification passes 178 census fixtures, 169 executed guard-removal
controls, 195 release regressions and all five I/O matrix rows. Full report bytes
match across hash seeds 1 and 2. Failed/superseded attempts are preserved in the
[new verification packet](evidence/story-5-6/manifest-selector-resolution-20261111/verification.md).

The original and updated checkers scan the same full parent revision and root
pins. Coverage errors fall from 109 to 107, resolving both packaging-script
diagnostics, with no new blocker. All 17 roots are accounted for, 2 complete,
with 548 observations, 120 rejected observations and 2 stale allowances.
All 421 retained evidence/policy files and the reference/gitlink state remain
unchanged. No allowance, exemption, exception, owner authority, dependency,
staging, commit, push or publication changed. The
[decision packet](evidence/story-5-6/manifest-selector-resolution-20261111/decision-packet.md)
binds remaining scanner limits, source boundaries, embedded-data context and
exact owner dispositions. No active upstream defect is inferred. Story and
sprint remain `in-progress` while current-reference acceptance fails.


### Nested-pin resolution — 2026-11-11

Implemented the approved cross-tree resolution for MSBuild imports and Compile
item sources only. Workspace paths are read from the root-declared reference
they land in, at its committed pin. Nested-gitlink paths are read at the exact
nested commit from the single root whose declared URL matches after the one
`/` and one `.git` trim, with a case-insensitive host; relative URLs never match.
One hop is allowed per chain. Other paths keep `unsafe-import-path` /
`unsafe-or-nested-compile-source`, now with the refused label as `target`.
`nested-pin-unresolvable`, `nested-object-unavailable` and
`workspace-object-unavailable` name the specific failures. An absent path is
optional only under an `Exists()` on that exact path, alone or as a top-level
`and` conjunct. Every substituted read is listed in the repository summary's
`crossTreeReads`. Git reads set `GIT_NO_LAZY_FETCH=1`; nothing is initialized,
fetched, checked out or executed. Nested publication targets still fail.

The [verification packet](evidence/story-5-6/nested-pin-resolution-20261111/verification.md)
records 192 passing census fixtures (14 new), 212 detected guard-removal controls
(43 new, 8 prior anchors adapted), 195 release regressions, all five matrix rows,
and byte-identical reports across hash seeds 1 and 2. The unchanged HEAD
checker reproduces the manifest-selector report at the same root pins. The
fresh committed-pin scan exits 1: 17 roots accounted for, 5 complete, 479
observations, 39 rejected observations, 68 coverage errors (from 107), 10 stale
allowances and 58 verified cross-tree reads. All 62 prior standalone source-file
rejections now associate with approved EventStore Admin.Cli/Admin.Mcp projects.
All 14 new blocker keys were masked by a resolved refusal on the same source.
Prior evidence, policy, inventory and reference bytes are unchanged, and the
evidence secret scan is clean.

The [decision packet](evidence/story-5-6/nested-pin-resolution-20261111/decision-packet.md)
leaves 24 cross-tree fallbacks refused: Tenants targets guarded by
property-definition `Exists()`, and a Commons import guarded by negated
`Exists()`. Approving either generic extension is a separate decision. No
allowance, exception, exemption, approval, dependency, reference or gitlink
changed. Story and sprint remain `in-progress`; nothing was staged, committed
or pushed.


### Exists() guard resolution — 2026-11-11

Implemented the approved guard extension for MSBuild imports and property
definitions. Only an element's own `Condition` and an enclosing
`PropertyGroup`/`ImportGroup` `Condition` are evaluated. Each must be a balanced
top-level `and` conjunction with no top-level `or`, using the property
alternatives in effect at that position; an unresolved `$(` proves nothing.
`Exists(p)` proves an element unreachable when every expansion is proven absent
under the local, workspace and nested rules. `!Exists(p)` does so when every
expansion is a committed regular blob or directory in the inspected root, or in a
root-declared reference at its pin. A nested path is never proven present.
Unreachable conditional definitions contribute no alternative; unreachable
imports are not visited. `Choose`/`When` and `Target` conditions are never
evaluated. Nothing new is recorded in policy.

During this work another session committed `884f65e` (*build: sync local
changes via /pushall*). It included this story's uncommitted work and moved
eight root gitlinks. It then merged upstream `94f5ee6` into `check.py`, the tests
and the census guide as `6ec91eb`. Verification therefore runs at `6ec91eb`. The
before baseline is the exact nested-pin checker plus the upstream `check.py`
hunks. It differs from the current checker only by this extension, and both
bindings are retained.

The [verification packet](evidence/story-5-6/exists-guard-resolution-20261111/verification.md)
records 197 passing census fixtures, 236 detected guard-removal controls (24
new; `Review-S07-optional` adapted because the guard proof now runs first), 195
release regressions, all five matrix rows and byte-identical reports across hash
seeds 1 and 2. Against that same-pin baseline, all 24 cross-tree fallback
errors (Tenants 20, Commons 4) and 11 dependent publication rejections resolve,
with no new blocker. Commons is now fully inspected. The fresh scan exits 1: 17
roots, 6 complete, 473 observations, 30 rejected observations, 45 coverage
errors and 10 stale allowances. The
[decision packet](evidence/story-5-6/exists-guard-resolution-20261111/decision-packet.md)
leaves owner dispositions, including one exclusion whose bytes changed at the
new Builds pin, plus protected boundaries, scanner limits and embedded data. No
allowance, exception, exemption, approval, dependency, reference or gitlink
changed through this work. Story and sprint remain `in-progress`; this work
performed no staging, commit or push.

Superseded by review loop 1 (2026-11-11): the cross-tree resolution review
found that this pruning form lets census-false guards hide present
classification, so its code was reverted. The excuse-only rewrite replaces it;
this packet stays as superseded evidence.


### Guard excuse review loop 1 — 2026-11-11

Re-implemented the approved `Exists()` guard rule as an excuse only. A guard
now excuses an absent import target that would otherwise be refused as
`unavailable-local-import` or an absent `unsafe-import-path`, through (a) the
import's own or enclosing `ImportGroup` condition, or (b) every definition of
the single `$(P)` it imports. Present imports are always visited, every
conditional property alternative is kept and classification is unchanged.
Proofs model the parent workspace from committed tree entries; presence is
exact-case and never nested, absence is case-insensitive and never a tree root,
the parent workspace root, a glob, a path above the parent or a path below an
unopened gitlink. The nested-pin review fixes R2, R3 and R11–R14 are applied:
substituted `$(` imports are refused with their label, nested `.gitmodules`
need valid `submodule` sections with safe paths, missing substituted blobs fail
with the requested label, closures bind cross-tree members by label, amendment
fixture validation has no workspace context, and every Git call disables
protocols, lazy fetches and replace objects and drops repository-local
variables. Nothing new is recorded in policy.

The [verification packet](evidence/story-5-6/guard-excuse-review-20261111/verification.md)
records 214 passing census fixtures (19 new), 283 detected guard-removal
controls (71 new, 4 adapted here), 195 release regressions, all five matrix
rows and byte-identical reports across hash seeds 1 and 2. The fresh scan exits
1: 17 roots, 6 complete, 473 observations, 30 rejected observations, 47
coverage errors and 10 stale allowances. Against the no-guard baseline at the
same pins, all 24 cross-tree fallback errors (Tenants 20, Commons 4) resolve
and no import refusal remains. Against the superseded pruning checker, all 58
blocker keys remain and two Tenants AppHost Compile refusals become visible: a
guarded `$(HexalithPlatformRoot)` fallback at `Directory.Build.props:65` keeps
its `$(MSBuildThisFileDirectory)../..` alternative, which the pruning version
dropped, and the excuse never covers a Compile item. The no-guard baseline
masked them with that project's import refusal. The
[decision packet](evidence/story-5-6/guard-excuse-review-20261111/decision-packet.md)
groups the remaining blockers. No allowance, exception, exemption, approval,
dependency, reference or gitlink changed. Story and sprint remain
`in-progress`; nothing was staged, committed or pushed.

### Loop-1 review patches — 2026-11-12

Applied L1–L19 from the loop-1 review in place:
- escaped and `;`-list import values are refused, and values are trimmed
- absence of a cross-tree target is case-folded and refuses the parent root and symlink prefixes
- one shared `Exists()` parser serves both rules
- an explicit SDK identity needs both `Sdk.props` and `Sdk.targets`
- `GIT_ALLOW_PROTOCOL` is empty, and the local-variable call reports `git-unavailable`
- `!Exists('dir/')` is proven only for directories
- `PropertyGroup` conditions resolve from the declaring file, following the probe
- seven test gaps are closed

D2 and D3 are in `deferred-work.md`.

The rerun [final-2](evidence/story-5-6/guard-excuse-review-20261111/runs/final-2/commands.json),
at parent `f223aaa5acd70c04a413f3251f83d96472a6b0d9` (build-only commits since
`6ec91eb`, no pin moves), passes:
- 219 census fixtures, with all 297 guard-removal controls detected
- 195 release regressions
- all five matrix rows, and `git diff --check`
- byte-identical reports across hash seeds 1 and 2
- a clean evidence secret scan

The real scan is unchanged by the patches. It exits 1 with 47 errors, 30
rejected observations, 473 observations, 6 complete roots and 10 stale
allowances. Current-reference acceptance therefore still fails on owner
dispositions, protected boundaries, scanner limits, embedded data and the
guarded Tenants Compile fallback. Story and sprint remain `in-progress`; I
staged, committed and pushed nothing.
