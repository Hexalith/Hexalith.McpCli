---
title: '5.5 Label retained legacy surfaces and record the Parties retirement block'
type: 'feature'
created: '2026-11-10'
status: 'done'
baseline_commit: 'adde25dcc454888b3573348f30a0e2e693f55b89'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-5-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/technical-tools-migration-inventory-v1.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** No upstream README or package description labels the proprietary surfaces PS01–PS14 as compatibility binaries with a removal gate, so a caller can mistake one for a supported or retired surface. `Parties.Mcp` cannot retire because Story 5.4's owner verdict is `retirement-blocked`, with G01–G06 open.

**Approach:**
- In each of the seven owning repositories, label every surface it owns with its latest approved removal gate.
- Commit one hash-bound McpCli evidence set covering three things: the merged label commits, a Platform composition census, and the SM-3 status of the Parties retirement.

## Boundaries & Constraints

**Always:**
- **Gate text.** Copy the PS row's "Removal gate" cell verbatim from technical-tools inventory 1.0.2. Cite the latest approved module inventory beside it: Parties 1.2.0, EventStore Admin 1.0.1, and 1.0.0 for the others.
- **Required statements.** Each label states that the surface is a versioned compatibility binary, is not retired, and stays outside every Hexalith.Platform composition, then gives its removal gate.
  - The Memories labels (PS06, PS07, PS14) say that forwarded per-user identity is necessary but not sufficient.
  - The FrontComposer host (PS04) and Projects plug-in (PS09) labels say the two retire together.
  - PS05 also names the Story 5.4 verdict and the open gaps G01–G06.
- **Isolated worktrees.** Work in a fresh worktree from each repository's `origin/main`. Never touch an owner's checkout: eventstore, frontcomposer, projects and platform all have unrelated uncommitted work.
- **Commit messages.** Every upstream commit uses the `docs` type and passes that repository's commitlint.

**Never:**
- Remove, reroute or unpublish a surface, or claim a retirement. AC1–AC2 are deferred (`deferred-work.md:944`).
- Edit `references/`, move a gitlink, amend an inventory, or edit the AI.Tools migration plan (Story 5.11 owns it).
- Name McpCli as the replacement for a surface whose rows have no approved `replace`.
- Change code, build, CI, versions or package identity upstream beyond the label text.

**Decisions (2026-11-10, user):**
1. **Split: labels + slip.** The Parties retirement release and the routing-point verifier wait until G01–G06 close and a new Story 5.4 verdict is `retirement-ready`.
2. **PS05 is labeled too.** The epic lists only PS01–PS04 and PS06–PS14; PS05 is added because `Parties.Mcp` is not retiring.
3. **Delivery: direct push to main.**
   - Commit to a worktree branch from each repository's `origin/main`.
   - Re-fetch, and rebase if `origin/main` moved, then push to `main`.
   - Once pushed, confirm that the repository's `main` CI run for that commit is green. If it is red, report it and do not patch around it.
4. **Placement: README and description.**
   - Each root README gets one `## Legacy compatibility surfaces` section.
   - The six packable projects (PS01, PS03, PS04, PS06, PS07, PS10) prefix their `<Description>` with the compatibility label and a pointer to that section.
   - PS04 has no Description yet, so it gains one.
   - NuGet listings show the new text only after each package's next release.
5. **Spec size kept** at about 2,000 tokens.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected | Error handling |
|---|---|---|---|
| Platform composition | Platform's AppHost, `src/`, `deploy/`, `infrastructure/`, templates or `hexalith-platform.json` enroll, deploy, route or map a PS surface | Census records the `file:line` | HALT: never label that surface as outside Platform |
| Name-only hit | `eventstore-admin` as Admin.Server's Dapr ID; `memories-mcp` in runbooks for the existing cluster; negative test assertions | Classified as not a composition, with the reason | None |
| Pinned docs text | An upstream test or script asserts README or Description text | Run it; it passes | If it fails, report it; never edit the test |
| Docs release | The repository's release rules cut a release for `docs` | Stated before delivery | HALT for the user's decision |

</frozen-after-approval>

## Code Map

- `technical-tools-migration-inventory-v1.md:272-285` -- PS rows and their verbatim "Removal gate" cells. `:357` (G4) requires the labels and Platform exclusion. PS01/PS02 cite Admin 1.0.0 and PS05 cites Parties 1.0.0, which are stale.
- Module gates, for the cited version only:
  - `parties-migration-inventory-v1.md:94` and `:121-122`
  - `eventstore-admin-migration-inventory-v1.md:333`
  - `memories-…:172-174`
  - `projects-…:213`
  - `frontcomposer-…:168`
  - `folders-…:329-331`
  - `chatbot-…:183`
- `evidence/story-5-4-owner-approval/owner-approval.json` -- the verdict, G01–G06 and their owners.
- Upstream checkouts are at `/home/administrator/projects/hexalith/<repo>`, with origin `github.com/Hexalith/Hexalith.<Repo>`:
  - **eventstore:** PS01 `src/Hexalith.EventStore.Admin.Cli` (NuGet tool `eventstore-admin`, Description `:11`) and PS02 `…Admin.Mcp`.
  - **frontcomposer:** PS03 `…FrontComposer.Cli` (package README `src/Hexalith.FrontComposer.Cli/README.md`) and PS04 `…FrontComposer.Mcp` (on NuGet, no Description).
  - **parties:** PS05 `src/Hexalith.Parties.Mcp` (container `parties-mcp`); the root `README.md:28` and `:138` mention it.
  - **memories:** PS06 `…Memories.Cli` and PS07 `…Memories.Mcp` (package READMEs), and PS14 `tools/MigrateEmbeddingVectors`. The local checkout is 7 commits behind origin.
  - **projects:** PS08 `…Projects.Cli` and PS09 `…Projects.Mcp`.
  - **folders:** PS10 `…Folders.Cli` (packable, not released) and PS11 `…Folders.Mcp`. The local checkout is 1 commit behind origin.
  - **chatbot:** PS12 and PS13 (`README.md:78-80`). It has `commitlint.config.cjs` and no root `package.json`, so check the repository's CI for its validator.
- Platform: `/home/administrator/projects/hexalith/platform`. Use AD-11 at `references/Hexalith.Platform/_bmad-output/planning-artifacts/architecture/architecture-platform-2026-09-27/ARCHITECTURE-SPINE.md:184`. `tests/Hexalith.Platform.Composition.Tests/PartiesAdoptionTests.cs:74` asserts that `parties-mcp` is absent.
- `scripts/scan-evidence-secrets.py <dir> --receipt <new.json>` -- the committed secret scan.
- SM-3 is defined at `planning-artifacts/prds/prd-mcpcli-2026-09-21/prd.md:532`, and `:526` checks it three months after v1. v1 (2.0.1) was published on 2026-11-05, which gives a deadline of 2027-02-05.

## Tasks & Acceptance

**Execution:**
- [x] For each of the seven repositories, in a worktree from `origin/main`:
  - Add the README section, plus the `<Description>` prefix where Decision 4 applies.
  - Grep the repository's tests and scripts for pinned README or Description text, and run any matches.
  - Check the release rules for `docs` commits.
  - Commit with a validated `docs` message on branch `docs/mcpcli-5-5-compatibility-labels`. Put the worktree under `/tmp/claude-1000/-home-administrator-projects-hexalith-mcpcli/d081051d-4cf2-49eb-90bc-99f8b39c053d/scratchpad/wt-5-5/<repo>`, and use the already-fetched `origin/main`.
  - **Sequencing:** keep every commit local during implementation, with no push, fetch or other remote operation. The push to `main` and the CI check (Decision 3) run only after the Build review passes. Until then, `labels.json` records the local commit as `pendingPush`.
- [x] Platform census -- `git grep` at Platform `origin/main` for every PS project, tool command and container name, excluding `references/` and evidence paths. Classify each hit as in the matrix.
- [x] `_bmad-output/implementation-artifacts/evidence/story-5-5/`:
  - `labels.json`: for each PS row, the repository, merged commit, `file:line`, label SHA-256, gate source and inventory versions.
  - `platform-census.json`.
  - `sm3-status.json`: Parties retirement blocked by G01–G06, the SM-3 deadline 2027-02-05 not yet passed, a pointer to the deferred entry, and that Story 5.11 records the final outcome.
  - `verification.md` and a scan receipt.
  - `labels.json` is also the register that later amendments (Stories 5.7–5.10) must update before their label change counts.
- [x] `sprint-status.yaml` -- record the 5.5 status and the retained block.

**Acceptance Criteria:**
- Given each repository's merged `main`, when its labels are read, then each of PS01–PS14 has exactly one label with every required statement, and its gate text matches the inventory cell byte for byte.
- Given Platform `origin/main`, when the census runs, then no Platform composition enrolls, deploys, routes or maps a PS surface, and every remaining hit is classified with its reason.
- Given the evidence set, when it is scanned, then the scan passes and the set binds each label commit, the Platform revision and the inventory hashes.
- Given the whole change, when it is inspected, then McpCli `src/`, `tests/`, `references/`, the inventories and every upstream non-label line are unchanged.

### Review Findings

Code review pass 2 (bmad-code-review, 2026-11-10). The scope was the deliverables, 2,899 diff lines in 21 files:
- the seven upstream label commits on `main`: EventStore `3de922e1`, FrontComposer `01fc48e3`, Parties `4c9fb0a0`, Memories `1143ba17`, Projects `77067782`, Folders `f4f5ce0c` (merged as `f1f63909`) and ChatBot `82f20d5e`;
- `.gitattributes`, the three evidence scripts, `verification.md`, `sm3-status.json`, `delivery-outcomes.json`, `secret-scan.json` and `labels.json`;
- the story's `deferred-work.md` hunks.

The generated `platform-census.json` was left out; `platform-census.py` reproduces it.

Four layers ran and none failed: Blind Hunter (B1–B20), Edge Case Hunter (E1–E30), Verification Gap (V1–V2 gaps, V3–V6 other) and Acceptance Auditor (A1–A11).

Of 67 findings, 32 group into 13 patches. There is no decision and no deferral, and 35 are rejected.

Independent re-checks during triage:
- `verify-labels.py` passes 14 of 14 against the pushed commits, including Folders `f1f63909`.
- Every register anchor, label, Description, README and message SHA-256 matches the committed blobs.
- Each current `origin/main` keeps the label files unchanged.
- The amended FrontComposer message passes its owner commitlint (0 problems).

**Applied (2026-11-10, user "Apply every patch"):** all 13 patches.
- Regenerated `labels.json`. Only the procedure text, the ChatBot note and Parties' moved `originMainWhenRecorded` changed.
- Re-ran the read-back: 14 of 14 at the label commits, and again with Folders at `f1f63909`.
- Re-ran the census at `a9c3555c`: byte-identical.
- Rescanned the evidence: clean, 8 files bound.
- The four new guards were probed. Each refuses a bad input that the committed version accepted ("Guard probes" in `evidence/story-5-5/verification.md`).
- No upstream repository changed.

- [x] [Review][Patch] `check_outcome` never proves that a label commit reached `main`
  - `pushed`, and `ci-red` with `mergedCommit == commit`, accept a hand-entered outcome without `ancestor(commit, 'origin/main')`.
  - `merged-unreviewed` passes with empty runs, because `all([])` is true.
  - An unfinished run (conclusion `None`) counts as red.
  - So a never-pushed SHA could be registered as delivered, and Stories 5.7–5.10 inherit that.
  - Fix: for every status except `push-rejected`, require the ancestry, non-empty runs and final conclusions. Then regenerate, re-verify and rescan. All seven current commits are on `origin/main`.
  - Not changed: the `baseIsOriginMain` rename.
  - (V1, B3, E1, E2, E3) [_bmad-output/implementation-artifacts/evidence/story-5-5/build-labels.py:171]
- [x] [Review][Patch] The AC1 read-back for Folders reads the pre-merge commit `f4f5ce0c`, not the merged `main` commit `f1f63909`
  - Ancestry alone does not prove the label survived the `/pushall` merge.
  - Run and record `verify-labels.py --rev folders=f1f639090a4e6b8cbeacb246e7052968dbc75836`. It passes, and its first-parent diff is the label alone.
  - Keep `build-labels.py` on `f4f5ce0c`.
  - (V2, E18) [_bmad-output/implementation-artifacts/evidence/story-5-5/verification.md:178]
- [x] [Review][Patch] Instructions written for delivery were not refreshed after delivery
  - `DELIVERY_PROCEDURE`, copied into `labels.json` `deliveryProcedure`, and steps 0 and 1 of `verification.md` still say:
    - "Parties already needs this: its origin/main is 64085d9f, not the recorded base 87a7b600";
    - "status merged-unreviewed; currently Folders".
  - The register now records Parties base `64085d9f` and Folders `ci-red`.
  - Step 4 says the tool "refuses an outcome whose `mergedCommit` differs from the pushed commit", but `ci-red` and `merged-unreviewed` accept an out-of-band ancestor merge.
  - The resolved push entry in the ledger still tells the reader to "follow the delivery procedure" after pushing.
  - Fix: make the procedure generic, correct step 4, put that evidence line in the past tense, then regenerate and rescan.
  - Not changed: the ledger heading (B18 part, false), because CLAUDE.md files entries under their source spec's heading.
  - (B1, B18, E11, E29, V4, A4) [_bmad-output/implementation-artifacts/evidence/story-5-5/build-labels.py:110]
- [x] [Review][Patch] The summary claims in `verification.md` are false for Folders
  - The Checks row "Pinned README and Description tests … all pass" omits the Folders PD10 tests: `Pd10V2ContractTests.cs:309` and `Pd10ConformanceSetTests.cs:72` bind `Hexalith.Folders.Cli.csproj` at 1206 bytes and fail at 1324. They were reported and not edited, as the matrix requires.
  - ":34 each failure was compared with its parent commit" does not hold for the `a87d0a0d` `dotnet format` failure, and CI/CodeQL on `f1f63909` were cancelled.
  - Fix: record the PD10 row, and state the format failure's basis: only `.cs` files fail, which the label does not touch, and `a87d0a0d` is the first completed CI run that contains the label.
  - Not changed: the out-of-band merge (A3 part), which was a concurrent session's action, already recorded.
  - (A2, A3, B14) [_bmad-output/implementation-artifacts/evidence/story-5-5/verification.md:161]
- [x] [Review][Patch] The commitlint evidence leaves out the amended FrontComposer message
  - `c9af83ed` was amended to `01fc48e3` with a new body, but the Checks row names only "the amended Parties commit".
  - `commitlint.result` is a constant string.
  - Record the `01fc48e3` validation: the owner CLI, read-only, reports 0 problems and 0 warnings, and the `main` Commitlint run succeeded.
  - Refuted: the A5 `requiredStatements` part. `locate()` at `:247-248` and `:257` raises unless the exact line is committed, and `verify-labels.py` checks section placement.
  - (B4, E6, A5) [_bmad-output/implementation-artifacts/evidence/story-5-5/verification.md:159]
- [x] [Review][Patch] The read-back does not check the target file of a citation link
  - `technicalToolsCited` and `moduleInventoryCited` check only the title and the `blob/<PIN>/` prefix.
  - So a wrong `MODULE_INVENTORIES` path, for example after a Story 5.7–5.10 version bump, would pass. That contradicts the docstring "a generator mistake cannot verify itself".
  - Fix: compare the full link, with each expected file, for both citations. The current targets are correct.
  - (B7, V6, E14) [_bmad-output/implementation-artifacts/evidence/story-5-5/verify-labels.py:96]
- [x] [Review][Patch] The census can classify a PS01 tool invocation as Admin.Server's Dapr identity
  - `named` drops `<tool-command-form>` before `named == {'eventstore-admin'}`. So a `dotnet tool run eventstore-admin …` line outside the composition areas (`eng/`, `scripts/`, `tests/`, `docs/`) passes with the reason "not the PS01 … tool".
  - Fix: add `and '<tool-command-form>' not in terms`, regenerate (expected byte-identical, since no current hit has both terms) and rescan.
  - All 39 current non-area `eventstore-admin` lines were read and are Admin.Server identities.
  - (V5, E19, B12, A9) [_bmad-output/implementation-artifacts/evidence/story-5-5/platform-census.py:139]
- [x] [Review][Patch] The ledger entry for the PS03/PS04 Descriptions leaves out what the follow-up needs
  - PS04 needs a new `<Description>` element, not a prefix.
  - Both scripts support only the prefix case: `build-labels.py` searches for the prefix and hard-codes `added: False`. In `verify-labels.py`, the `replace(PREFIX)` equality makes the `('1','0')` numstat allowance unreachable.
  - FrontComposer packs per-package READMEs, so a PS03/PS04 release made before the reseal ships with no NuGet label.
  - Add these to the entry.
  - (B8) [_bmad-output/implementation-artifacts/deferred-work.md:969]
- [x] [Review][Patch] The `memories-mcp` container label is not recorded as a side effect
  - `Hexalith.Memories.Mcp` sets `EnableContainer` with no `ContainerDescription` or label override.
  - The .NET SDK falls back to `Description` for `org.opencontainers.image.description`, so the next `memories-mcp` image carries the prefix.
  - The evidence mentions only NuGet.
  - (B9) [_bmad-output/implementation-artifacts/evidence/story-5-5/verification.md:130]
- [x] [Review][Patch] The SM-3 v1 anchor is stale
  - `epics.md:292` holds "Epic 4's v1 release (2.0.1)" only before `76f2e74`. At HEAD it is `:293`.
  - An uncommitted edit by a concurrent session moves it to `:294`, so use the line at HEAD when applying.
  - (V3) [_bmad-output/implementation-artifacts/evidence/story-5-5/sm3-status.json:24]
- [x] [Review][Patch] The AC4 check cannot show that the story commits left `src/`, `tests/` and `references/` untouched
  - `git diff --stat HEAD` inspects only uncommitted changes.
  - Record `git show --stat --format= 17c3681 f20a377 f2fc7c5 d6f7ffb 7f61892 -- src tests references` (empty).
  - Note that the 13 gitlink moves in `adde25d..HEAD` come from the concurrent `efcda9e` `/pushall`.
  - (A8) [_bmad-output/implementation-artifacts/evidence/story-5-5/verification.md:163]
- [x] [Review][Patch] The ChatBot release text reports an outcome from a semantic-release step that never ran
  - Release run 42805809900 failed at compile, before semantic-release ran, so "semantic-release finds no release-worthy commit" was never observed.
  - Say that, and that the default rules cut no release for `docs`.
  - (B16) [_bmad-output/implementation-artifacts/evidence/story-5-5/verification.md:211]
- [x] [Review][Patch] The `.gitattributes` comment lists only four evidence files
  - The glob protects, and the receipt binds, every Story 5.5 file, including the three scripts and `delivery-outcomes.json`.
  - Say "every scanned Story 5.5 evidence file".
  - (B19) [.gitattributes:37]

**Rejected (35):**
- B2 low: a Folders `deliveryPath` field. `mergedCommit` differs from `localCommit` and the note records the merge, so adding a schema field brings no reachable benefit.
- B5 false: `requiredStatements`. `locate()` raises unless the built line, which holds the gate cell and statements, is committed exactly once.
- B6 low: the register is never read back. Every row anchor and hash was cross-checked against the blobs and matches; adding a cross-checker would be extra code.
- B10 low: the intro on non-legacy package pages. Pass 1 recorded the effect (P5), the heading scopes "These", and a change would need a re-push to seven repositories.
- B11 false: census scope. ChatBot's AppHost is its own local-development umbrella ("ADR exception boundary"). It never adds `Hexalith.ChatBot.Mcp`, and its realm is the local sandbox. AD-11 governs Platform compositions, which the spec scopes to the Platform repository.
- B13 low: revision freshness. The auditor's rerun at the newer Platform `origin/main` `d7c74e8a` is still clean.
- B15 false: tests not tied to pushed commits. The Parties `87a7b600..64085d9f` and EventStore `aa16227b..39ebd8b4` rebases touch neither the root README, the Admin.Cli files nor any pinned test, so the procedure's rerun condition never fired.
- B17 false: local paths and credential details. `GH_CONFIG_DIR` is a path, not a credential, and 2,520 committed `_bmad-output` files already carry `/home/administrator`.
- B20 false: `platform-census.json` was omitted by the user's scope choice and is reproducible.
- E4 low: misspelled repository keys. A typo is unlikely, and guarding against it would add code.
- E5 low: a merge commit as the `build-labels.py` rev. The procedure passes the label commit; `verify-labels.py` handles the merge (first parent).
- E7 low: `docsCommitCutsRelease` is a literal. All seven subjects are `docs:`.
- E8 low: `onOriginMain` is a literal. Pin `c70ca978` is on `origin/main`.
- E9 false: the working-tree owner approval is byte-identical to the pin.
- E10 low: `baseIsOriginMain` after delivery is accurate (`base` ≠ `origin/main`). A rename would change the schema.
- E12 low: duplicate PS rows. Unlikely; it would need a guard.
- E13 low: `verify-labels.py` reads the working-tree inventory. `build-labels.py` enforces equality with the pin in the same procedure, and any drift fails loudly.
- E15 low: section prose outside the bullets. None exists, and a check would need a guard.
- E16 low: an exact duplicate label line elsewhere. Unlikely; it would need a guard.
- E17 low: a parent that already holds the section. Unlikely; it would need a guard.
- E20 low: `RESOLUTIONS` without line hashes. This affects reruns only; anchors are content-checked.
- E21 low: the bare `memories` classification. This affects reruns only, and invocation forms are caught by `COMMAND_FORM`.
- E22 low: the canned `_bmad-output` reason. Exactly one hit at the recorded revision, and the reason is accurate there.
- E23 low: `PartiesAdoptionTests` classified by path. One hit, reruns only.
- E24 low: the fixed AD-11 index. Correct at the recorded revision, reruns only.
- E25 low: `revisionSource`. A dynamic value would break the documented byte-identical rerun.
- E26 false: non-UTF-8 input fails loudly.
- E27 false: a missing evidence file fails loudly, so the census stays closed.
- E28 low: the `d6f7ffb` claim. `verify-labels.py` enforces README-only for FrontComposer and the procedure runs both scripts; commit history is immutable.
- E30 low: "no build change" in the upstream messages. The messages are pushed history, and the spec allows the Description label text.
- A1 low: the Decision 4 narrowing. It is a user decision tracked in the ledger, and the only fix would edit the spec.
- A6 low: the ChatBot commitlint substitute. It is disclosed, was settled in pass 1 (BH14), and the commit is pushed.
- A7 false: commitlint in owner checkouts. A read-only CLI run modifies no owner file.
- A10 low: spec `done` against sprint `review`. That is the normal state during review, and this review sets the status.
- A11 false: red `main` runs. Decision 3's report-and-halt path was followed, and the user decided.

## Implementation Notes

- **Labels (local, `pendingPush`).** All seven label commits are on `docs/mcpcli-5-5-compatibility-labels` in isolated worktrees under the session scratchpad (`wt-5-5/<repo>`), each a direct child of the already-fetched `origin/main`. Nothing was fetched or pushed. Parties' `origin/main` moved to `87a7b600` through an owner push during the story. That commit touches neither `README.md` nor any test that reads it, so the label commit was rebased locally and its README tests were rerun. Commits, anchors and hashes are in `evidence/story-5-5/labels.json`.
- **Release rules.** No repository's release rules cut a release for `docs`. Only ChatBot's `release.yml` runs on push. Its gates will run, but semantic-release finds nothing to release. The Memories `qualify-builds-publication.yml` also runs on this push, because `src/**/*.csproj` changed. It is an offline qualification that publishes nothing.
- **Pinned text.** The README tests in Parties, Folders and EventStore were built in Release and run, and all pass. The other four repositories pin no root README or Description text. Details are in `evidence/story-5-5/verification.md`.
- **Validators.** The ChatBot repository has no pinned commitlint CLI, root `package.json` or CI commitlint step. Its message was validated with `@commitlint/cli` 21.2.4 against its own `commitlint.config.cjs`.
- **Projects README.** The file had no final newline, so the diff rewrites its only line with identical text.
- **Census.** `docs/implementation/**` in Platform is treated as an evidence path: it holds dated captured snapshots, as technical-tools PE07 records. Its hit counts are kept in `platform-census.json`.
- **PRD anchor.** The spec cites `prd.md:526` for the three-month check. In the current PRD the sentence is at `prd.md:527`, under the heading at line 525.
- **McpCli changes.** Beyond the evidence set and `sprint-status.yaml`, the only McpCli change is a root `.gitattributes` entry. It keeps `evidence/story-5-5/**` byte-exact, as the Story 5.4 packet entry does.
- **After the Build review (Decision 3).** Follow the delivery procedure in `evidence/story-5-5/verification.md`, also recorded as `deliveryProcedure` in `labels.json`. For each repository, it rebases, revalidates and pushes the label commit, records every `main` run, and halts for the user on a rejected push or a red run. It then regenerates the register from the pushed commits with `build-labels.py`, reruns `verify-labels.py` against them, and rescans.
- **Folders merged out of band.** A concurrent Cursor `/pushall` in the Folders owner checkout merged the local label branch into Folders `main` as `f1f63909`, pushed it before the review, and removed the worktree and branch. The merged `main` carries the labels unchanged, and the register records the merge as `merged-unreviewed`. The other six label branches are equally exposed to `/pushall`.

- **Delivery (2026-11-10, user "push all changes").**
  - **Parties:** rebased onto `64085d9f`, revalidated and pushed as `4c9fb0a0`. Its `main` CI is red, but only on a pre-existing "Lifecycle controller tests" failure that also fails on the parent.
  - **Folders:** `main` is red from this story. `contract-spine-gates` PD10 conformance tests bind `Hexalith.Folders.Cli.csproj` at 1206 bytes, and the Description prefix makes it 1324. Both the planning sweep and review pass 1 missed that binding. Its CI failure is an unrelated format error.
  - **EventStore (rebased to `7422ce56`), FrontComposer, Memories, Projects and ChatBot:** the pushes were refused with HTTP 403. The session's `gh-cicd-agent` token has no write access to them. No other credential was used.
  - Nothing was patched around. `labels.json` was regenerated from these commits, and the read-back passes 14 of 14. The evidence was rescanned clean.
  - The outcomes and remaining steps are in `evidence/story-5-5/verification.md`.

- **Correction (2026-11-10): the Folders attribution.** The delivery note above says Folders is "red from this story", which is wrong. `contract-spine-gates` was already red at `e88c9400` (run 42109497136), from Folders' own PD10 drift. The Description prefix adds one more drift, which masks the earlier one. A revert of only the prefix still fails 5 of the 24 PD10 tests. The user kept the label and made no Folders commit. The approval-bound PD10 v2 requalification, owned by the Folders maintainer, must rebind `Hexalith.Folders.Cli.csproj` at 1324 bytes, and Decision 4 is unchanged.

- **User decisions after delivery (2026-11-10).**
  - **Folders:** keep the label and make no Folders commit.
  - **FrontComposer README-only:** this narrows frozen Decision 4 from six Description prefixes to four (PS01, PS06, PS07, PS10). A pre-push sweep showed that FrontComposer seals every tracked `.csproj` digest (`consumer_configuration_sha256`). The Description hunks would have failed `dependency-governance`, and a reseal cannot authorize itself. The unpushed commit `c9af83ed` became `01fc48e3`.
  - **PS03/PS04 Descriptions:** deferred to FrontComposer's reseal procedure (ledger).
  - **Rest of the sweep:** Memories passed in full (5,416 unit tests, publication qualification and package validation). EventStore had a targeted search and showed no seal. `build-labels.py` and `verify-labels.py` now enforce README-only for FrontComposer.

- **Delivery complete (2026-11-10, user "push all changes").**
  - **Pushes:** EventStore (rebased again, to `3de922e1`), FrontComposer `01fc48e3`, Memories `1143ba17`, Projects `77067782`, ChatBot `82f20d5e` and McpCli went out with the user's credential. All 14 labels are on `main`, and no release was cut.
  - **CI:** Memories is green. The red EventStore, FrontComposer, Projects and ChatBot runs match their parents test for test, so they are pre-existing.
  - **Open items:** Folders keeps its pre-existing PD10 red, plus the label's csproj drift (owner requalification), and the PS03/PS04 Descriptions wait for FrontComposer's reseal.
  - **Evidence:** the register is regenerated and verified against all seven `main` commits, and rescanned.

## Spec Change Log

## Review Triage Log

### Review pass 1 (2026-11-10)

Layers: Blind Hunter (BH), Edge Case Hunter (EC), Verification Gap (VG; no gap findings, three other findings). No intent_gap or bad_spec; eight patch groups, one defer, seven rejections.

| ID | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|
| BH1 | After the push, the register update covers only `mergedCommit`/`mainCiRuns` | medium | `labels.json:6` and Implementation Notes plan only those two fields. A rebase changes `localCommit`, `base`, row commits and possibly README anchors and hashes. | patch P1 |
| EC1 | The recorded Parties base is stale | medium | Parties `origin/main` is now `64085d9f`, not the recorded `87a7b600` (`labels.json:155-156`). | patch P1 |
| EC2 | Rebased SHAs leave stale bindings and an invalidated scan | medium | Same root as BH1. Any `labels.json` edit changes the hash the scan binds. | patch P1 |
| EC3 | No disposition for a rejected push or a red `main` CI | low | Decision 3 covers red CI ("report it"), but the evidence procedure records neither outcome. A direct procedure correction. | patch P1 |
| EC11 | AC1 on merged `main` is unverified; `mergedCommit` is null | medium | Expected under the post-review sequencing; covered by the P1 re-verification after the push. | patch P1 |
| VG-O1 | Register checked only against local commits; read-back tool is scratch-only | medium | Post-push step does not re-run the read-back; the tool is `scratchpad/s55/verify_labels.py`. | patch P1, P2 |
| BH2 | Read-back, census and commitlint commands cannot be re-run | medium | Census `method.command` uses placeholders; no committed scripts. Precedent: `evidence/story-5-4/verify-live.py`. | patch P2 |
| VG-O2 | The `use McpCli` check can never match | low | `'use McpCli' in label.lower()` compares mixed case with lowercased text. The claim holds today: McpCli appears only in URLs and PS05's verdict sentence. | patch P2 |
| BH14 | Commitlint provenance is weak | low | Owner installs are 21.2.4 for EventStore, FrontComposer and Projects, equal to each `origin/main` lockfile, so that part is false. ChatBot's validator source and exact command are unrecorded. | patch P2 |
| BH4 | The `references/**` exclusion claims every gitlink manifest is checked | low | `moduleManifestsAtPlatformGitlinks` covers the seven PS-owning modules only. A direct text correction. | patch P3 |
| BH5 | Composition-area hits record only a shared reason | low | `eventstore-admin` is also PS01's tool command. `WorksPreviewModel.cs:166` needs its resolving identity (`:48` Admin.Server.Host) to be checkable. | patch P3 |
| EC7 | Recorded `startsWith` omits leading whitespace | low | `ARCHITECTURE-SPINE.md:184` starts with two spaces; `lineSha256` matches. | patch P3 |
| EC9 | Exclusion `lineHits` cannot be reproduced | low | A rerun gives about 11,190, not 11,252. The count is not defined as deduplicated `(path,line)`. | patch P3 |
| BH6 | PS05 label has no link and no update trigger | medium | Readers cannot resolve the Story 5.4 verdict. The register rule covers only removal-gate changes. `owner-approval.json` exists at `c70ca97` (SHA-256 `8bf60a27…`). | patch P4 |
| EC4 | Labels go stale when G01–G06 or the cited inventory versions change | medium | Same root as BH6: the register rule is too narrow. | patch P4 |
| VG-O3 | Projects and ChatBot pack the root README into every package | low | `Directory.Build.props:84-88` and `:43-47`. The effect is not recorded. | patch P5 |
| BH8 | Packed READMEs: per-project README lacks the label; the root README ships everywhere | low | Per-project part rejected: frozen Decision 4 fixes the placement, and the Description prefix labels the NuGet page. Root-README part confirmed for EventStore `:93,108` and Folders `:72-76`. | patch P5 / reject |
| EC5 | Packed project READMEs lack the section | low | Rejected: same as BH8 per-project part (Decision 4). | reject |
| EC12 | Projects README title line is rewritten | low | Only an EOF newline is added; the read-back ignores terminators. Record the exception. | patch P5 |
| BH10 | The SM-3 record does not explain why 2.0.1 is v1 | low | `epics.md:292` names "Epic 4's v1 release (2.0.1)"; earlier tags were Abstractions-only (`README.md:87,121`). | patch P6 |
| EC8 | `entrySha256` hashes only `deferred-work.md:944` | low | Edits to the summary, owner or status go undetected. | patch P6 |
| BH11 | The deferred retirement has no sprint or epic tracking, and the ledger entry is imprecise | low | Tracking is false: the user chose ledger tracking ("Labels + slip"), the sprint comment records the block, and Story 5.11 reconciles `epics.md`. The entry lacks the 2027-02-05 deadline and a `path:line` anchor (CLAUDE.md). | patch P7 |
| BH13 | Small `labels.json` schema gaps | low | Missing technical-tools `title`, PS14 out of ID order, `messageSha256` normalization undefined. The multi-line Description part is false: the commit SHA binds the whole file and the prefix is on the hashed line. | patch P8 |
| BH9 | Wrong wording for libraries and unpublished projects | low | "Versioned compatibility binary" is false: AC3 and technical inventory G4 mandate it. The PS10 `nugetVisibility` wording implies an existing listing for a never-published package. | patch P8 |
| BH7 | Older README text still presents surfaces as current features | medium | Parties `README.md:28,138`, Memories `:47-48,118-119`, ChatBot `:3,78` predate this story. Reconciling product claims is Story 5.11. | defer |
| BH3 | The `docs/implementation/**` exclusion leaves 3,489 hits unclassified | false | Approved technical-tools row PE07 (`:301`) puts "`docs/implementation` snapshots inside the roots" out of census scope, so it is an evidence path. | reject |
| EC10 | The same `docs/implementation` exclusion breaks AC2 | false | Same refutation as BH3 (PE07). | reject |
| EC6 | Census misses `Projects.Hexalith_X_Mcp` and `<module>-mcp` names | false | Aspire generates `Projects.*` only from a ProjectReference, whose path contains the fixed-string term. Only `parties-mcp` and `memories-mcp` are published images, and both are searched. | reject |
| BH12 | The spec Code Map still cites `prd.md:526` | low | Rejected: the fix edits this build's spec. Evidence already records `:527`. | reject |

## Design Notes

A label adds one root README section per repository, with one bullet per surface:

```markdown
## Legacy compatibility surfaces

These are versioned compatibility binaries. They are not retired and stay outside every Hexalith.Platform composition.

- `Hexalith.Parties.Mcp` (container `parties-mcp`): removal gate "Parties inventory gates; replacement evidence and approved withdrawal for every row" ([technical-tools inventory 1.0.2](<pinned McpCli URL>) PS05; Parties inventory 1.2.0). Retirement is blocked: the Story 5.4 verdict is `retirement-blocked`, with G01–G06 open.
```

A Description prefix keeps the existing text after it:

`<Description>Compatibility binary, not retired; see "Legacy compatibility surfaces" in the repository README for its removal gate. Hexalith EventStore administration CLI — …</Description>`

Pin the inventory links to McpCli commit `c70ca9784da393cb1929741c6a6c9564717eace5`, which is on `origin/main` and holds every cited version.

## Verification

**Commands:**
- `git -C <worktree> diff origin/main --stat` -- expected: only `README.md`, plus the Decision 4 `.csproj` `<Description>` lines.
- `gh run list -R Hexalith/Hexalith.<Repo> --commit <sha>` -- expected: every `main` run for the pushed commit concludes `success`.
- `<repo commitlint> --verbose` on each exact message -- expected: 0 problems.
- `python3 scripts/scan-evidence-secrets.py _bmad-output/implementation-artifacts/evidence/story-5-5 --receipt <scratch>/scan.json` -- expected: exit 0.
- `git diff --stat HEAD -- src tests references` -- expected: empty.
