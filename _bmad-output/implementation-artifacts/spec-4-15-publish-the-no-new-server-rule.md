---
title: '4.15 Publish the no-new-server rule'
type: 'chore'
created: '2026-10-28'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 'c694bff5a29073bee6848b88c142f7da23efcf85'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-4-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The published AI.Tools rule lacks a link to a versioned migration plan listing frozen implementations. Story 4.15 also lacks upstream integration, baseline-reference and synchronization evidence.

**Approach:** Add a versioned migration index in the owning AI.Tools repository, integrate its published baseline, and record provenance and synchronization evidence for the later paired-release gate.

## Boundaries & Constraints

**Always:** Retain Hexalith.McpCli ownership, decorated Contracts for gateway-ready operations, and separately approved generic contract/transport decisions for other classes. Existing proprietary surfaces receive only safety and continuity fixes; they are migration sources, never templates. Preserve inventory approval limitations, coordinated FrontComposer/Projects retirement and Memories' HTTP per-user identity prerequisite. Completion requires upstream main integration, its containing root baseline reference, byte-identical local entry points and passing synchronization. An open PR is insufficient; Abstractions-only bootstrap remains exempt.

**Never:** Edit reference contents, initialize nested submodules, change operation dispositions, invent owner approval, authorize retirement, alter production behavior, or implement paired publication in this story. External developer CLIs remain outside this policy.

## I/O & Edge-Case Matrix

| State | Required result |
| --- | --- |
| Published rule and plan, containing baseline reference, synchronized entry points | Record instruction-prerequisite completion; other release gates remain independent |
| Local candidate, open PR, or reference missing the integrated change | Keep story completion and paired-release readiness blocked |
| Any local entry point differs | Synchronization fails; reconcile all three before accepting evidence |
| Deferred operation or missing external owner approval | Retain compatibility surface and its existing authorization, behavior and release gates |

</frozen-after-approval>

## Code Map

- Owning `/home/administrator/projects/hexalith/aitools/hexalith-llm-instructions.md`: permits only same-folder topical links. Published main/current McpCli gitlink `3f194e17174994d308ec84af9ee2b5aa68674d0d` directly integrated the core rule; do not invent a merge commit or PR.
- Owning AI.Tools `README.md`: topical catalog. No tracked build/package/commitlint/editor configuration or workflows found. Clean local main is stale at `5bf12bbcec3d8a2016396c27439de9b5107f9e5d`; base implementation safely on published main.
- `_bmad-output/implementation-artifacts/*-migration-inventory-v1.md`: six version 1.0.0 inventories. Preserve session approval versus unasserted external owner approval. Parties has legacy MCP, no inventoried CLI. Frozen CLIs: Folders, Projects, ChatBot, FrontComposer, Memories; EventStore Admin needs its successor inventory.
- `scripts/check-agent-instructions-sync.sh`: existing byte-comparison gate, already passing for the three local entry points.
- `scripts/release-request.py`, `scripts/verify-release-source.py`: preserve paired-release refusal; Story 4.16 consumes this evidence.
- Previous Story 4.14 is done: retain upstream ownership, full revisions and separate local/published evidence.

## Tasks & Acceptance

**Execution:**
- [x] Owning AI.Tools `hexalith-mcpcli-migration-instructions.md` — add version 1.0.0 index listing legacy servers, plug-ins, frozen CLIs, immutable inventories, approval limits and retirement prerequisites, including successor administration scope.
- [x] Owning AI.Tools `hexalith-llm-instructions.md`, `README.md` — link the same-folder topic and explain retained compatibility implementations without weakening the existing rule.
- [x] `references/Hexalith.AI.Tools` gitlink — integrate the qualified published revision; record integration and containment evidence.
- [x] `README.md` — link the authoritative rule, migration plan and story evidence; distinguish this instruction prerequisite from later paired-release implementation.
- [x] `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md` — verify byte identity; if a change is necessary, edit AGENTS and copy it to both others.
- [x] `_bmad-output/implementation-artifacts/evidence/story-4-15/` — retain upstream changes, full published revisions, gitlink containment, hashes and exact check results, including synchronization drift in temporary copies.
- [x] Owning AI.Tools `package.json`, `package-lock.json`, `commitlint.config.mjs`, `README.md` — supply and verify the previously missing pinned commitlint prerequisite for the required upstream commit.
- [x] This spec and `sprint-status.yaml` — record review, verification and actual completion state; do not close while upstream integration is outstanding.

**Acceptance Criteria:**
- Given a new module, when its author follows the baseline, then no new proprietary per-module MCP server, plug-in or CLI is created; decorated Contracts or an approved generic decision provide the path.
- Given a frozen implementation, when its author follows the versioned plan, then its inventory or successor gap and safety/continuity limit are identifiable without retirement approval.
- Given completion assessment, when evidence is checked, then upstream main contains the finished rule/plan, the root baseline contains that revision, and local entry points pass synchronization.

## Implementation Notes

Approved by the user on 2026-10-28: "approve and continue". The implementation stage requires sequential execution, no pushes and no remote operations. Prepare and verify the upstream candidate locally against the published baseline already available in the root reference; retain outstanding publication and reference-integration requirements explicitly until they can be completed. Do not claim a local patch is merged or mark the story done.

Parent verification found the owning repository had no pinned validator or effective rules. Added minimal development-only commitlint configuration and lockfile, using the same exact CLI/policy version 21.2.2 as McpCli. Offline lock generation and `npm ci` succeeded; the pinned CLI accepts the exact stored candidate message and rejects malformed and unknown-type controls. This necessary publication prerequisite expands the footprint by three tooling files and README guidance; it changes no runtime packages. The original three-document evidence packet remains historical; the current candidate and parent checks are recorded in `evidence/story-4-15/parent-final/`.

After reading the full candidate diff and completing local checks, the parent resolved publication authority against the approved frozen scope: the user approved upstream integration and its containing root baseline, which necessarily require committing and publishing the instruction change. That existing authorization takes precedence over the skill's generic no-remote implementation rule. Proceed with the specific approved publication and reference integration, preserving the remaining review and acceptance checks; no additional approval is required.

## Spec Change Log

## Review Triage Log

### Build review (2026-10-28)

All three layers completed. Verification Gap found no gaps. Each Blind Hunter
finding and the Edge Case finding is classified separately below before repair.

| ID | Verdict | Route | Evidence |
| --- | --- | --- | --- |
| BH1 | low | patch | The historical manifest excludes current parent receipts and archives. Add a current packet manifest for direct artifact verification. |
| BH2 | medium | patch | Temporary-index command receipts omit their environment. Replaying the recorded argv alone uses the real index. Preserve honest historical limitations and capture fresh index setup/environment explicitly. |
| BH3 | low | patch | Post-publication equality was checked against files in a clean committed checkout, but per-file committed hashes were not retained in the final receipt. Capture committed bytes and hashes directly for audit. |
| BH4 | low | patch | The missing-plan Git control does not implement an unpublished/open-PR readiness gate. Label that part as documentary policy assessment, keeping executable missing-object and release-refusal checks separate. |
| BH5 | low | patch | The successful offline npm commands were visible in tool output but absent from the retained packet. Capture the install needed for the runtime-metadata correction with exact results. |
| BH6 | medium | patch | The new validator requires Node >=22.12.0, absent from root package metadata and README prerequisites. Contributors can encounter unsupported runtimes; add the direct metadata and prerequisite. |
| BH7 | low | patch | Immutable inventory contents were verified locally, while the current packet lacks a fresh remote observation of their containing McpCli revision. Capture published containment. |
| BH8 | false | reject | The administration row identifies both exact package names and expressly states its successor inventory is outstanding, with no approved mapping or completeness claim. It does not claim source-pinned administration inventory evidence; no advertised source reference is missing. |
| BH9 | low | patch | A final README sentence refers to the whole current packet as pre-publication despite its new publication receipts. Limit that sentence to the historical local verification file. |
| BH10 | low | patch | Current observations lack capture timestamps. Add actual UTC capture times to fresh receipts; do not invent original command times for historical files. |
| EC1 | low | patch | The archived browseable plan's ownership link targets a missing sibling file. Add navigation to the immutable published rule while preserving the hash-bound plan bytes. |

All surviving findings have direct documentation, scalar configuration or
receipt corrections, with no new runtime surface or changed operation scope.
No intent/spec loopback or deferred ledger entry is required.

All patch findings are resolved. BH1–BH7, BH9–BH10 and EC1 have retained
corrections and targeted evidence; BH8 remains rejected for the stated reason.
The parent inspected the exact three-file owning follow-up, confirmed unchanged
dependency entries, and published the Node prerequisite correction as
`5be77fcbd96546e722b30a117516b1e03e6e4975`, containing the original rule/plan
revision `68e60375eb298854611b2fefd1dfef95bad7a8c9`. The clean root baseline
now contains the final revision. No finding is deferred. Temporary-index
environment records retain task-specific overrides while omitting ambient PATH.

## Design Notes

No intent gaps remain. Shared upstream publication follows implementation and review. Footprint: documentation, one reference and evidence; no runtime API or package changes. Reuse inventories without duplicating operation tables. Investigation began on clean McpCli main `6103e9c8f91258c28b926a8e1b5c14f27ad19725`.

## Verification

- Run `bash scripts/check-agent-instructions-sync.sh` and `cmp`; temporary-copy drift must fail.
- Check topical/inventory links, policy clauses, approval limits and retirement dependencies against sources.
- Record published-main integration ancestry, root gitlink containment and hashes of policy, plan and entry points.
- Run `git diff --check` in each owner. No .NET/live rerun for documentation. Validate eventual commit messages with owning pinned commitlint before presenting or using them; never bypass tooling blockers.

### Local implementation and verification (2026-10-28)

Prepared the three-document candidate in owning AI.Tools against published main
`3f194e17174994d308ec84af9ee2b5aa68674d0d`, after a clean offline fast-forward
from `5bf12bbcec3d8a2016396c27439de9b5107f9e5d`. The new 1.0.0 plan links
six immutable inventories at McpCli `c694bff5a29073bee6848b88c142f7da23efcf85`,
lists actual legacy package names and frozen CLIs, and preserves scope-approval
limits, non-gateway decisions, successor administration inventory gaps and all
retirement conditions. The original published ownership rule is unchanged; its
new link is a same-folder topical link. Root README links the authoritative rule,
plan candidate and evidence while retaining the independent release gates.

Checked tasks above denote locally prepared candidate/evidence work only.
Upstream main integration and the containing root reference remain outstanding;
review is pending. No reference contents, gitlink, operation dispositions,
production behavior, release scripts or local entry points changed. No remote
operations, push, publication or new commit occurred. Story and sprint remain
`in-progress`; no instruction-prerequisite or paired-release completion is claimed.

Verification covers exact patch/archive reproduction from the published baseline,
immutable inventory targets and hashes, policy preservation, existing root
containment, unchanged paired-release refusals, passing synchronization and both
`cmp` checks, plus three temporary-entry-point drift failures and restored success.
Root whitespace validation passes. Plain owning `git diff --check` reports only
the new CRLF lines; the explicit `cr-at-eol` check passes while preserving existing
file bytes. The owner has no pinned commitlint setup; cached empty-rule tooling
does not establish valid commit-message evidence. No candidate message was used.
No .NET/live run is needed or claimed for documentation. Exact commands, qualified
results, hashes and remaining requirements are retained in the
[local implementation packet](evidence/story-4-15/README.md).

### Authoritative publication and integration (2026-10-28)

The parent read the complete diff, independently verified the candidate and
resolved the missing pinned validator before publication. The six-file owning
AI.Tools change was committed with its successfully validated exact message and
pushed to authoritative main as `68e60375eb298854611b2fefd1dfef95bad7a8c9`.
A fresh remote-main observation matches that full revision; its parent is
`3f194e17174994d308ec84af9ee2b5aa68674d0d`. This is direct main integration,
not an invented PR merge. The clean root-declared baseline reference was then
fetched and fast-forwarded to that exact revision. Root README now links the
published rule and plan. The current
[publication packet](evidence/story-4-15/parent-final/README.md) supersedes the
historical local-only observations; final workflow review remains pending.

Post-integration qualification passes all four matrix rows: published main and
the candidate gitlink match the exact six-file revision; the historical baseline
fails the missing-plan control; all three synchronization drift controls fail
and restored/current copies pass; and exact inventory bytes and published
approval limits preserve deferred capabilities. Both paired-publication guards
still refuse independently. The frozen intent is unchanged. All implementation
tasks and acceptance criteria are satisfied in the candidate; root commit and
final workflow review remain next. Exact checks are in
[qualification.json](evidence/story-4-15/parent-final/qualification.json).

### Final review completion (2026-10-28)

The three review layers are complete and all accepted patches are resolved.
Final publication, committed-file hashes and reference integration are retained
in [the final receipt](evidence/story-4-15/parent-final/upstream-review-publication.json).
The post-review acceptance receipt separates documentary unpublished/open-PR
policy assessment from executed controls, retains current source fingerprints
and UTC observations, and checks the current packet manifest. No runtime or
inventory behavior changed. The spec is done; sprint status is review for
maintainer acceptance. The root integration is recorded in a local commit;
root publication is not automatic under the Build presentation step.

### Review Findings (code review, 2026-10-28)

Code review of the committed story range `c694bff..e6ddf3f` plus the owning AI.Tools commits `3f194e1..5be77fc` (`68e6037`, `5be77fc`; paths prefixed `Hexalith.AI.Tools/` in the diff).

- **Code-only scope:** excludes `_bmad-output/` and the gitlink line, and leaves out the generated `package-lock.json`. 6 file diffs, 211 diff lines, full mode, with `epic-4-context.md` as context.
- **Layers:** Blind Hunter (BH), Edge Case Hunter (EC), Verification Gap (VG) and Acceptance Auditor (AA). No layer failed. The Acceptance Auditor found no blocking AC violation. It confirmed the gitlink, the `68e6037` containment, the passing synchronization script, the inventory counts and both paired-release refusals.
- **Result:** 27 findings (BH 13, EC 7, VG 1, AA 6). After triage: 1 decision-needed, 4 patch, 3 defer and 15 rejected.

Parent checks during triage:
- **The lockfile is consistent.** `package-lock.json` (lockfile v3, 71 packages) pins the same two devDependencies as `package.json`. Every entry resolves from `registry.npmjs.org` with sha512 integrity, and all are dev-only. The root `engines` matches the commitlint CLI's own `>=22.12.0`, and `node_modules/` is ignored.
- **Four inventory source revisions are absent upstream.** GitHub returns HTTP 422 "No commit found" for Folders `e2252f29`, ChatBot `acc93459`, FrontComposer `81a440a8` and Projects `3d256e63`. They are also absent from the sibling clones. They exist only in this checkout's `references/` submodule clones and were McpCli gitlinks at `cad469e`, which is on `origin/main`. Parties `49373094` and Memories `f6b60d5a` are on upstream `main`.
- **Platform uses `hexalith-module`.** Pinned Platform `8de9095` uses `dotnet tool run hexalith-module` as its workspace run/debug tool (`references/Hexalith.Platform/README.md:36`, `:88`).

- [x] [Review][Decision] D1 — medium. Resolved on 2026-10-29 with option 1 (exempt Hexalith build and workspace tooling), now patch P5. Hexalith-owned Builds CLIs are neither frozen nor exempted (BH3, EC5, AA2). `references/Hexalith.Builds` packs `Hexalith.Builds.Module.Cli` (`hexalith-module`) and `Hexalith.Builds.Evidence.Cli` (`hexalith-evidence`) as dotnet tools.
  - The exemption covers only external developer CLIs (Aspire, Dapr, `dotnet`), at `Hexalith.AI.Tools/hexalith-mcpcli-migration-instructions.md:16` and `hexalith-llm-instructions.md:78`.
  - The plan's frozen table lists neither tool.
  - The successor scope asks only for "remaining proprietary technical/domain CLI or MCP packages" to be identified.
  - A Builds author or agent cannot tell whether these tools are frozen, exempt, or barred from gaining siblings (AC2). The PRD's "Frozen CLI" definition covers module CLIs that McpCli replaces.
- [x] [Review][Patch] P1 — low. Both README summaries drop "only" from the safety-and-continuity limit [README.md:44] (AA1, BH13 drift part).
  - `README.md:44` says the surfaces "receive safety and continuity fixes".
  - `Hexalith.AI.Tools/README.md:50` says "Retained implementations receive safety and continuity fixes".
  - The rule says "Limit them to safety and continuity fixes", and the spec's Always rule says "only". The root README also omits "never templates for new modules".
  - Fix: say "receive only safety and continuity fixes" in both places. Add "never templates for new modules" to the root README.
- [x] [Review][Patch] P2 — low. A literal reading of "A later source change … requires a versioned inventory update" covers the safety and continuity fixes the freeze permits [Hexalith.AI.Tools/hexalith-mcpcli-migration-instructions.md:41] (BH2).
  - Read that way, every permitted fix also forces a cross-repository inventory revision.
  - Fix: limit it to a source change that adds, removes or alters an inventoried tool, resource, CLI operation or behavior variant.
- [x] [Review][Patch] P3 — low. The plan has `plan_version` and `inventory_revision` but no rule for revising either [Hexalith.AI.Tools/hexalith-mcpcli-migration-instructions.md:2] (AA5, BH8).
  - Story 5.1's EventStore Admin successor inventory, or any re-pinned inventory, leaves the updater without guidance, and the frontmatter pin goes stale.
  - Fix: one sentence. Revise `plan_version` and move `inventory_revision` whenever an indexed inventory is re-pinned or added, or a row of the frozen table changes.
- [x] [Review][Patch] P4 — low. The future-inventory requirements omit PRD FR-21's coverage coupling [Hexalith.AI.Tools/hexalith-mcpcli-migration-instructions.md:55] (AA3).
  - Lines 55-60 require dispositions and "exact replacement contract or unresolved gap".
  - They omit three things FR-21 requires:
    - Gateway-ready rows name the canonical operation and decorated contract type.
    - `include` requires `replace`.
    - `exclude` requires an approved `withdraw` or `defer`.
  - Fix: add that sentence.
- [x] [Review][Patch] P5 — medium. Exempt Hexalith build and workspace tooling in both the rule and the plan [Hexalith.AI.Tools/hexalith-llm-instructions.md:78] (from D1).
  - In the owning AI.Tools checkout, extend `hexalith-llm-instructions.md:78-79` and `hexalith-mcpcli-migration-instructions.md:16-17` with one matching sentence. Hexalith.Builds build and workspace tooling that never invokes module operations is outside the rule. Currently that is `hexalith-module` and `hexalith-evidence`. The drafted "never reads or changes module data" test was dropped: `hexalith-module down` deletes each run's data stores (`references/Hexalith.Platform/README.md:205-210`, `:245`).
  - Batch P5 with P1–P4 into one owning AI.Tools commit, validated with the AI.Tools pinned commitlint. Then publish it to AI.Tools `main` and move the `references/Hexalith.AI.Tools` gitlink.
  - Update the two `README.md:44`/`:46` permalinks to the new revision, and record the new revision's evidence (integration, containment, synchronization).
  - Platform `8de9095` keeps `hexalith-module` as its run/debug tool, accepted from 4.35.2 up to (not including) 5.0.0. No Platform, Builds or manifest change is needed.
- [x] [Review][Defer] W1 — medium. Four of the six indexed inventories pin source revisions that do not exist upstream [_bmad-output/implementation-artifacts/folders-migration-inventory-v1.md:6] (BH1). Deferred: pre-existing from Stories 4.2–4.4. The inventories are immutable, and re-pinning or preserving the objects upstream belongs to the inventory owners. Logged in `deferred-work.md`.
- [x] [Review][Defer] W2 — medium. AI.Tools has no CI or hook commitlint gate for its new pinned policy [Hexalith.AI.Tools/package.json:6] (VG1, pre-verified; EC4; BH5 enforcement part). Deferred: pre-existing gap in the owning repository. The fix is an upstream AI.Tools caller of the Builds reusable `commitlint.yml`. Logged in `deferred-work.md`.
- [x] [Review][Defer] W3 — low. Relative links in the packed README break on nuget.org [README.md:46] (EC7, BH10 packaging part). Deferred: pre-existing README pattern (`README.md:130`, `:259`, `:261`, `:269`, `:276`, `:287`). Both packages pack `README.md` as `PackageReadmeFile`. Logged in `deferred-work.md`.

#### Rejected (code review, 2026-10-28)

- BH4 `false`:
  - **Location claim:** McpCli-specific release content in the shared plan. AI.Tools keeps repository-specific text out of its universal entry points only, not its topical files. The spec places this gate in the plan, so moving it would edit the spec.
  - **"Local entry points" ambiguity:** the paragraph's subject is paired McpCli publication, and evidence is recorded "in the consuming repository". `scripts/check-agent-instructions-sync.sh` exists only in McpCli, so the referent is fixed.
- BH5 (engine part), EC1 `low` — `engines` is advisory without `engine-strict`. npm still prints EBADENGINE, the README states Node 22.12.0, and McpCli uses the same unguarded pattern. The fix adds a new `.npmrc` guard.
- EC2 `low` — `NODE_ENV=production` or `omit=dev` installs nothing. That is contrived for a dev-only tooling package, and McpCli has the same pattern.
- EC3 `low` — `npx --no` in a nested checkout before `npm ci` resolves an ancestor's commitlint. The README orders `npm ci` first, and nobody commits in the read-only nested `references/` checkouts. The fix adds a guard.
- BH6 `false` — The AI.Tools commitlint policy diverges from the Builds and McpCli overrides. No repository policy requires AI.Tools to adopt either set of overrides; the spec named plain `config-conventional` 21.2.2. AI.Tools runs no semantic-release, so no caller diverges.
- BH7 `false` — The README conflicts with `hexalith-git-instructions.md:55`. That file says to write the message to a temporary file and validate it with commitlint, and validating the exact full message on stdin satisfies that. The pinned tooling is repository-specific and belongs in the README.
- BH9 `false` — Nothing mechanically enforces the instruction prerequisite. Story 4.16's AC gates on "recorded FR-22 merge/baseline/synchronization evidence", and the spec says Story 4.16 consumes this evidence.
- BH10 (permalink part), EC6 `low` — The README permalinks are pinned to `5be77fc`. Pinning to the exact published revision is the spec's provenance intent, and the links go stale only after a later rule revision. The proposed fix is a new sync-script guard.
- BH10 (wording part) `false` — The "authoritative `main`" referent is unclear. Its object, "the finished rule and plan", and the preceding paragraph both identify AI.Tools.
- BH11 `false` — The EventStore Admin inventory has no named owner or tracking item. The plan names owning roles, as the inventories do, and McpCli story numbers are repository-specific planning. Release inventories gate enrollment coverage, not frozen-surface migration.
- BH12 `false` — No automated check detects a new `*.Mcp`/`*.Cli` project. AC1 is met by the instruction ("when its author follows the baseline"), and automated detection is new scope.
- BH13 (wording part) `false` — "a necessary, insufficient prerequisite" is grammatical and unambiguous.
- AA4 `false` — The README credits Story 4.16. Story 4.16's AC implements the paired release workflow ("When the paired release workflow runs …"), and Story 4.18 publishes, so the README's "owns paired-release implementation" is accurate.
- AA6 `false` — Scope note only. The parent verified the excluded lockfile, as recorded above.

### Code review patch resolution (2026-10-29)

All five patches are applied, and D1 is resolved with option 1.

- **Upstream:** the owning AI.Tools commit `70dbf73e80787299c832d30d911b16b105ab194d` (parent `5be77fc`) changes `README.md`, `hexalith-llm-instructions.md` and `hexalith-mcpcli-migration-instructions.md`.
  - It is published on authoritative `main`; `git ls-remote` and the GitHub commit API both resolve it.
  - Its exact message passed the pinned AI.Tools commitlint 21.2.2, and a malformed control was rejected.
  - `hexalith-llm-instructions.md` keeps its CRLF line endings, and `git diff --check` with `cr-at-eol` passes.
- **P1:** both READMEs say retained implementations receive only safety and continuity fixes. The root README adds "never templates for new modules".
- **P2:** only a source change that adds, removes or alters an inventoried tool, resource, CLI operation or behavior variant, or a newly discovered surface, forces an inventory update. A safety or continuity fix that leaves them unchanged does not.
- **P3:** every change to the plan is published under a new `plan_version`, and `inventory_revision` moves whenever an indexed inventory is re-pinned or added. This change publishes plan 1.1.0. `inventory_revision` stays `c694bff`, because no inventory changed.
- **P4:** gateway-ready rows name the canonical operation and decorated contract type; `include` requires `replace`, and `exclude` requires an approved `withdraw` or `defer`.
- **P5 (D1):** the rule and the plan exempt Hexalith.Builds build and workspace tooling that never invokes module operations (currently `hexalith-module` and `hexalith-evidence`). The FrontComposer compiler CLI stays frozen as listed. Platform `8de9095` needs no change.
- **Root:**
  - `references/Hexalith.AI.Tools` is fast-forwarded to `70dbf73`, which contains `68e6037` and `5be77fc`. No nested submodule exists.
  - `README.md:44` and `:46` link the `70dbf73` rule and plan 1.1.0, and the new evidence packet.
  - The synchronization script passes, the three entry points are byte-identical, and a temporary-copy drift control fails.
- **Evidence:** [code-review-20261029](evidence/story-4-15/code-review-20261029/README.md); `evidence/story-4-15/LATEST.md` points to it.

Not changed: dispositions, inventories, production code, release scripts and the paired-release refusal. No .NET, live or hosted run applies. The McpCli gitlink move, README, evidence, ledger and status edits are uncommitted in the working tree. The containing root baseline reference therefore exists once they are committed.
