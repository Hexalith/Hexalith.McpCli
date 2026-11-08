---
title: Open the Epic 5 gate and fix the compatibility-label ordering
created: '2026-11-08'
status: applied
review_mode: batch
source_action: epic-4-retro-item-8-gate-on-previous-verdict
baseline: aac815ed7423ea1f674a4e47cdfa79a13aaadf3d
approval: 'Product owner approved P1–P4 in conversation on 2026-11-08'
---

# Sprint Change Proposal: Epic 5 Entry Gate and Label Ordering

## 1. Issue summary

The 2026-11-08 sprint-planning run, after Story 5.1 closed, left two problems open. Neither came from a failing story.

**A. The Epic 5 entry gate has no recorded decision.** MR10 (`epics.md:212`) and the Epic 5 Entry line (`epics.md:291`) allow Stories 5.2–5.11 to become `ready-for-dev` only after a recorded product-owner decision on Epic 4 retro item 8. The Epic 4 retrospective's verdict is still `rejected`. Item 8 (`sprint-status.yaml`, `epic-4-retro-item-8-gate-on-previous-verdict`) is still `open`, and no decision exists in `epic-4-retro-2026-11-06.md:288` or after it. Every Epic 5 story after 5.1 is blocked until one is recorded.

**B. Stories 5.7–5.10 refer to labels that may not exist yet.** Each of those stories has an AC requiring that "the matching Story 5.5 compatibility label is updated upstream before the amendment counts as complete" (`epics.md` Stories 5.7–5.10). Those stories depend only on Story 5.2. The labels are created in Story 5.5 AC3, at the end of the separate Parties chain 5.3 → 5.4 → 5.5. An amendment approved before 5.5 completes has no label to update, so a literal reading blocks completion on a story the amendment does not depend on.

Evidence at `aac815e`:

- **Epic 4's own rejection causes are resolved.** The verdict cites F1, F2 and F3 (`epic-4-retro-2026-11-06.md:315-318`). It names items 1–3 as "the shortest path to `accepted-with-open-items`" (`:322-325`), and all three are `done` in `sprint-status.yaml`. The F2 and F4 follow-ups add records but keep the verdict as `rejected`.
- **Item 8's remaining substance is the Epic 3 §G gap.** The MCP output schemas accept twelve documents that §G forbids (`epic-3-retro-2026-10-16.md:29-45`), for example `paging.pageSize: 0`, a non-ULID `messageId`, an empty `violations` array, and more than three suggestions. The runtime documents conform, and the gap is in the advertised schemas only. `src/Hexalith.McpCli.Mcp` has no commit since 2026-10-16 (`git log --since=2026-10-16 -- src/Hexalith.McpCli.Mcp` is empty), so the published 2.0.1 carries the gap. `epic-3-retro-item-1-complete-output-contract` is `open`.
- **Earlier verdicts.** MR10 says "a previous retrospective verdict". The Epic 1 and Epic 2 verdicts are also `rejected`, with no human override (`epic-1-retro-2026-09-27.md:65`, `epic-2-retro-2026-10-10.md:74`). F10 (`epic-4-retro-2026-11-06.md:154-160`) raises only the Epic 3 gap as an Epic 5 blocker.

## 2. Impact analysis

| Area | Impact |
| --- | --- |
| Epic 5 | Can be completed as planned. The gate opens for 5.2–5.11. Stories 5.5 and 5.7–5.10 change one AC each, and the epic gains a release precondition. No story is added, removed, renumbered or resequenced, and no status other than item 8 changes. |
| Epics 1–4 | No scope or AC change. Their sprint status moves from `in-progress` to `done`, which matches the status definition "All stories in epic completed". The rejected retrospective verdicts and every open action item stay as they are. |
| PRD and addendum | None. §G remains authoritative, no narrower output-schema contract is approved, and the 2.0.1 acceptance is a recorded deviation, not a requirement change. |
| Architecture | None. |
| UX | No UX artifact exists. Not applicable. |
| Retrospective record | `epic-4-retro-2026-11-06.md` gains an F10 resolution follow-up, in the same form as the F2 and F4 follow-ups. |
| Sprint status | Item 8 moves `open` → `done` through `sprint_status.py update`. `epic-1` to `epic-4` move to `done` by an exact line edit; `sprint_plan.py generate` is not used because it drops comments. |
| Compiled context | `epic-5-context.md` is already stale (it still lists "Story 5.6: Reconcile Product and UX Claims"). bmad-build recompiles it automatically when any planning artifact is newer, so no manual edit is needed. |
| Code, CI, release | No code or workflow change. The new precondition blocks publishing any McpCli version after 2.0.1 until `epic-3-retro-item-1` is done. Releases are already owner-dispatched, so this is a recorded planning gate, not a new CI check. |

## 3. Recommended approach

The recommended approach is to **adjust the existing artifacts directly**. The effort is low: four documentation edits and two status transitions. The scope is **minor**, because the product owner has already made the decisions and no backlog needs reorganizing.

The product owner chose to accept the §G gap for 2.0.1 and fix it before the next release, over two alternatives:

- **Remediating before Epic 5.** This would delay the two Epic 5 tracks, which are mostly inventory and decision work, behind a change to the MCP output schemas that none of their acceptance criteria depend on.
- **Accepting with no release condition.** This would let a later release ship the same loose schemas again.

The precondition is placed where the gap would actually reach users again: a new published package. The earliest Epic 5 work that is likely to release is Story 5.3, which enrolls a new Parties Contracts version.

Rollback does not apply, because nothing completed is being undone. Reducing the MVP scope does not apply either, because the defect is in the planning record, not in the scope.

**Risks:**

- Treating this decision as acceptance of the Epic 3 or Epic 4 verdict. The P1 wording rules that out.
- Treating it as an exception to items 5, 6 or 9. P1 restates that they still bind Epic 5.
- A release published before `epic-3-retro-item-1` is done. P2 puts the precondition in the Epic 5 Entry, which every Epic 5 story spec is compiled from.

**Handoff note for Story 5.3:** `epic-2-retro-item-1-protect-profile-output` (a result path can overwrite the private profile store) and `epic-2-retro-item-2-anchor-profile-names` are still `open`. Story 5.3 moves operators onto McpCli profiles. Its spec should either account for these two items or record why they do not affect the move.

## 4. Detailed change proposals

### P1: Record the item 8 decision

**File:** `_bmad-output/implementation-artifacts/epic-4-retro-2026-11-06.md`, appended after "F4 resolution follow-up — 2026-11-06".

**Before:** the file ends with the F4 follow-up. Item 8 has no decision.

**After:**

```markdown
## F10 resolution follow-up — 2026-11-08

The product owner decided item 8 through the [2026-11-08 sprint change proposal](../planning-artifacts/sprint-change-proposal-2026-11-08.md).

1. **Epic 3 §G gap: accepted for 2.0.1 only.** The output schemas that the published 2.0.1 package advertises omit the twelve §G semantic constraints recorded in Epic 3 F1 (`epic-3-retro-2026-10-16.md:29-45`). This is accepted as a fixed historical deviation of that package, because its runtime documents conform and only the advertised schemas are looser. §G remains authoritative, and no narrower contract is approved. `epic-3-retro-item-1-complete-output-contract` stays **open** and is now a precondition for every later release: no McpCli version after 2.0.1 is published until that item is **done**.
2. **Epic 5 gate: opened.** Stories 5.2–5.11 may become `ready-for-dev` while this retrospective's verdict remains **rejected**. The basis is that the verdict's three causes, F1–F3, are resolved by items 1–3. Those are the items "Acceptance verdict" names as the path to `accepted-with-open-items`. For MR10, this decision also covers the rejected Epic 1, 2 and 3 verdicts; their open action items carry forward unchanged. Open items 5, 6 and 9 still bind Epic 5 evidence, release and tenant-isolation claims (MR10, MR11, Story 5.4).

This decision does not change the **rejected** verdict of this retrospective or of Epics 1–3. It grants no exception to any other gate and no execution, enrollment or retirement authority. Item 8 is **done**.
```

**Status:** `epic-4-retro-item-8-gate-on-previous-verdict`: `open` → `done`, by running
`uv run .claude/skills/bmad-retrospective/scripts/sprint_status.py update --file _bmad-output/implementation-artifacts/sprint-status.yaml --epic 4 --set-action-status '[{"id":"epic-4-retro-item-8-gate-on-previous-verdict","status":"done"}]'`.

**Rationale:** the decision follows the record pattern of F2 and F4. It names the only package the acceptance covers, and it gives the open Epic 3 item a binding condition instead of leaving it without a deadline. The coverage of the Epic 1–3 verdicts closes the literal ambiguity in "a previous retrospective verdict" without reopening any of them.

### P2: Note the gate decision in Epic 5's Entry and MR10

**File:** `_bmad-output/planning-artifacts/epics.md`.

**Frontmatter `changeProposals`.**
Before:

```yaml
changeProposals:
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-06.md
```

After:

```yaml
changeProposals:
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-06.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-08.md
```

**MR10 (line 212).** Append one sentence after "…(Epic 4 retro F10; `sprint-status.yaml` action items).":

> Item 8 was decided on 2026-11-08 (see the Epic 5 Entry); items 5, 6 and 9 remain open.

**Epic 5 Entry (line 291).**
Before:

> **Entry:** Epic 4's v1 release (2.0.1) and Story 5.1's approved inventories; while the Epic 4 retrospective verdict remains `rejected`, Story 5.2 and later stories become `ready-for-dev` only after a recorded product-owner decision on Epic 4 retro item 8 (MR10). **Exit:** …

After:

> **Entry:** Epic 4's v1 release (2.0.1) and Story 5.1's approved inventories; while the Epic 4 retrospective verdict remains `rejected`, Story 5.2 and later stories become `ready-for-dev` only after a recorded product-owner decision on Epic 4 retro item 8 (MR10). **Gate decision (2026-11-08):** recorded in the [sprint change proposal](sprint-change-proposal-2026-11-08.md) and the Epic 4 retrospective's F10 follow-up; Stories 5.2–5.11 may become `ready-for-dev`, the Epic 3 §G output-schema gap is accepted for 2.0.1 only, and no McpCli version after 2.0.1 is published until `epic-3-retro-item-1-complete-output-contract` is done. **Exit:** …

**Rationale:** Epic 5 story specs are compiled from this text, so whoever plans a release reads the precondition in the epic itself. MR10 stays a requirement and gains only a status pointer.

### P3: Make the label clause independent of Story 5.5's timing

**File:** `_bmad-output/planning-artifacts/epics.md`, Stories 5.5, 5.7, 5.8, 5.9 and 5.10.

**Stories 5.7, 5.9 and 5.10 (identical text), and Story 5.8 (which reads "the amendment" instead of "an amendment" in its Given line).**
Before:

```markdown
**Given** a removal gate that an amendment changes,
**When** the amendment is approved,
**Then** the matching Story 5.5 compatibility label is updated upstream before the amendment counts as complete.
```

After (Story 5.8 keeps "the amendment" in its Given line):

```markdown
**Given** a removal gate that an amendment changes,
**When** the amendment is approved,
**Then** if Story 5.5 has already labeled the affected surface, that compatibility label is updated upstream before the amendment counts as complete,
**And** otherwise the amendment completes without a label change, and Story 5.5 labels the surface from the latest approved inventory version.
```

**Story 5.5 AC3.**
Before:

```markdown
**Then** each is labeled in its upstream README or package description as a versioned compatibility binary with the inventory gate that removes it, stays outside every Platform composition, and is not counted as retired,
```

After:

```markdown
**Then** each is labeled in its upstream README or package description as a versioned compatibility binary with the removal gate from its latest approved inventory version when this story completes, stays outside every Platform composition, and is not counted as retired,
```

**Rationale:** whichever track finishes first, every label ends up carrying the current gate. Story 5.5 labels from the newest approved inventory, and any amendment approved after that updates the label. The two tracks stay independent as the Epic 5 implementation notes intend. The alternative, making 5.7–5.10 depend on 5.5, would serialize the non-gateway track behind Parties retirement.

### P4: Close Epics 1–4 in sprint status

**File:** `_bmad-output/implementation-artifacts/sprint-status.yaml`, `development_status`.

**Before:** `epic-1: in-progress`, `epic-2: in-progress`, `epic-3: in-progress`, `epic-4: in-progress`.

**After:** `epic-1: done`, `epic-2: done`, `epic-3: done`, `epic-4: done`. `epic-5` stays `in-progress`.

**Rationale:** every story and retrospective in these epics is `done`, which meets the file's definition "done: All stories in epic completed". Sprint planning never moves an epic forward on its own. The verdicts stay in each retrospective's frontmatter, and open work stays visible in `action_items`. The edit replaces those four exact lines only, and a diff checks that every comment survives.

## 5. Implementation handoff

**Scope:** minor. The Developer agent applies P1–P4 directly. The product owner (the requesting user, under the single-maintainer model) made the decision, so no PM or architect escalation is needed.

| Role | Responsibility |
| --- | --- |
| Developer agent | Apply P1–P4 exactly, keeping every other byte the same. Run `sprint_status.py update` for item 8, edit the four epic lines, then run `uv run .claude/skills/bmad-sprint-planning/scripts/sprint_plan.py validate` and diff `sprint-status.yaml` to confirm every comment survived. |
| Product owner | Approve this proposal. Before dispatching any McpCli release after 2.0.1, confirm that `epic-3-retro-item-1-complete-output-contract` is `done`. |
| Story 5.3 author | Account for the open `epic-2-retro-item-1` and `-item-2` profile items in the spec, or record why they do not apply. |

**Success criteria:**

1. `epic-4-retro-2026-11-06.md` ends with the P1 follow-up, its frontmatter still reads `verdict: rejected`, and no other byte has changed.
2. `epics.md` contains the P2 and P3 text exactly, and nothing else changes.
3. `sprint-status.yaml` shows item 8 as `done` and `epic-1`–`epic-4` as `done`. Apart from `last_updated` and those five values, `git diff` shows no change, all comments are intact, and `sprint_plan.py validate` passes.
4. Stories 5.2–5.11 can then become `ready-for-dev` in the normal way, through story creation. This proposal does not move any story.
