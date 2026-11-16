---
title: '5.11 Reconcile product claims and the migration plan'
type: 'chore'
created: '2026-11-16'
status: 'in-review'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: '008d95ccc77d932a372cb6c749d9d1fb1bc1ea57'
story_key: '5-11-reconcile-product-claims-and-the-migration-plan'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The authoritative plan indexes obsolete inventories; active product documents still promise proprietary adapters or capabilities AD-23 does not admit. Approved Admin/technical inventories also describe their approvals as pending.

**Approach:** Reconcile the inventory chain, active module claims and release notes with adopted decisions and recorded delivery. Publish plan 1.3.0 with a new immutable inventory revision after prerequisites and approvals pass.

## Boundaries & Constraints

**Always:** Preserve every approved predecessor, AD-23 byte, exemption and independent gate. Prepare upstream patches outside `references/`; preserve owner changes. Inventory approval and Git delivery require separate, explicit authorization of the prepared bytes. Story 5.10 delivery is a completion prerequisite; preparation may proceed meanwhile.

Align MR1/MR6 and FR-21 with adopted AD-23: confidential UI, explicit withdrawal and named local exemptions need no invented McpCli transport. Keep Parties retirement blocked by G01–G06 and its separate restriction conflict; index the Folders K12 and Projects paging conflicts. Record the existing owner “Labels + slip” decision and SM-3 deadline 2027-02-05; reassess the date at completion.

**Never:** Change runtime exposure, production dependencies, census authority, frozen evidence or historical release notes; execute operations, retire binaries, publish packages, waive open gates or claim ecosystem completion. Change only the AI.Tools gitlink, after upstream integration is verified; leave Builds/CI-owned files untouched.

## I/O & Edge-Case Matrix

| State | Required result |
| --- | --- |
| Approved inventory, incomplete delivery | Report both states; completion refuses |
| Missing version, role, hash, gate or upstream integration | Name the missing binding; no success claim |
| Pending new amendment | Receipt determines effective status; no premature approval wording |
| Unresolved exposure conflict | Named owner and blocking successor; no compliance claim |
| Exempt compiler/vector tooling | Retained locally; never counted retired |

</frozen-after-approval>

## Code Map

`A` = `_bmad-output/implementation-artifacts`; `E` = `A/evidence/story-5-11`.

- `E/investigation.md` maps pinned module paths, inventory histories and ledger anchors. Use current owner guidance and recheck main before deriving patches.
- `A/evidence/story-5-{7,8,9,10}/` supplies amendment verifiers, receipts and successive label registers; reuse their lifecycle checks.
- `_bmad-output/planning-artifacts/{epics.md,prds/prd-mcpcli-2026-09-21/prd.md,architecture/architecture-mcpcli-2026-09-22/ARCHITECTURE-SPINE.md}` contains local contradictions.
- `.releaserc.json` currently invokes the pinned release-notes generator; append the committed migration status through a module-owned hook, preserving publication checks.

## Tasks & Acceptance

**Execution:**
- [x] `E/{inputs.json,investigation.md}`: capture full revisions, hashes, all eight inventory histories, approvals, fourteen labels and prerequisite states. Recheck 5.10 delivery before completion.
- [x] `A/eventstore-admin-migration-inventory-v1.0.3.md`, `A/technical-tools-migration-inventory-v1.0.4.md`, `.gitattributes`: add successors correcting pending self-description via receipt-based status; re-cite current companion inventories, including Folders 1.1.0. Preserve dispositions, pins, safety fields and owners. Record earlier approval separately from fresh approval.
- [x] `E/{approval.json,labels.json,verify_reconciliation.py,test_verify_reconciliation.py,upstream/}`: prepare hash-bound amendments and seven owner README patches. Check complete accounting, preserved bytes, class/gate semantics, approval roles, published inventory bytes and label integration; test the matrix and guard removals with exact streams.
- [x] `E/upstream/`: prepare the AI.Tools plan/rule amendment and the active module PRD, architecture, flow and README corrections mapped in `investigation.md`. Name actually available operations, `hexalith` setup and stdio discovery, safe refusal and confidential UI handoff. Preserve historical names as migration sources. No speculative operation availability.
- [x] Local planning files above, `README.md`, `A/epic-5-context.md`: align current claims, MR1/MR6, disposition semantics and inventory/plan citations without rewriting historical snapshots.
- [x] `docs/release/migration-status.md`, `scripts/migration-release-notes.mjs`, `scripts/tests/migration-release-notes.test.mjs`, `.releaserc.json`: append gateway-only scope, evidenced retirements and all remaining binaries/removal gates to generated notes. Exercise the pinned generator without publishing; fail on absent status input. No workflow edits.
- [x] `E/deferral-dispositions.md`, `A/deferred-work.md`: audit the original migration-drift entry and every Epic 5 deferral, recording resolved evidence or an existing owner/gate as already tracked. Acceptance needs an explicit owner decision. Grep before adding; preserve unresolved gates.
- [x] `E/{verification.md,integration.json}`, AI.Tools gitlink, this spec and `A/sprint-status.yaml`: after authorized integration, bind published inventory revision, upstream main containment, exact plan bytes and passing instruction sync. Otherwise retain in-review with the exact blockers.

**Acceptance Criteria:**
- Given approved successors and completed prerequisites, when plan integration is verified, then a new plan version/revision indexes every historical amendment and current inventory with accurate authority and retirement state.
- Given all active module topics, when the patch manifest is audited, then each targets McpCli or explicitly identifies retained compatibility/exempt tooling, with accurate setup and refusal flows.
- Given an Epic 5 release, when notes are generated, then the committed migration status is included and neither blocked retirements nor ecosystem completion is claimed.
- Given every scoped deferral, when completion is checked, then each has a sourced disposition; unresolved work retains its owner and blocking gate.

## Verification

- Run the story verifier, its focused tests and the Node notes tests under `run-with-temp`; save useful logs in `E`.
- Recheck adopted AD-23, all upstream patch applications and changed owner documentation tests; validate new command examples against the built CLI without Gateway calls.
- Run the shared evidence secret scan, `scripts/check-agent-instructions-sync.sh` and `git diff --check`.
- Before authorized Git delivery, require each owner's pinned commitlint and mandatory Builds check. No bypass of the recorded missing-CI-configuration blocker.

## Implementation Notes

- 2026-11-16: The user approved the on-disk draft with “approve and continue”. The frozen intent and constraints are locked. Implementation starts from the preserved baseline; prior planning files are the only untracked work. Approval permits implementation and review, while exact-byte inventory approval and Git delivery remain separate decisions.

- 2026-11-16 implementation: prepared 23 inventory versions across eight families,
  receipt-based Admin 1.0.3 / technical 1.0.4, fourteen labels, thirty patches
  across nine owners, the local claim corrections and the release-note hook.
  The 56-row deferral audit is prepared; exact owner acceptance remains pending.
  No immutable predecessor, AD-23 byte, runtime exposure, dependency, census,
  Builds/CI-owned file, historical release or reference checkout was changed.
- Completion remains blocked by fresh exact-byte approval; Story 5.10 delivery;
  missing CiCd configuration; separate Git delivery authorization; immutable
  inventory publication; final plan approval/AI.Tools integration; containing
  gitlink; and completion-date SM-3/deferral owner decisions. See
  [verification](evidence/story-5-11/verification.md) and
  [integration bindings](evidence/story-5-11/integration.json). The authoritative
  plan remains 1.2.0; the 1.3.0 candidate has an explicit null publication binding.

## Spec Change Log

## Review Triage Log

2026-11-16 build review: all three independent reviewers returned before triage. Each finding is recorded individually below. These are corrections to the already-required documentation, binding or verification behavior, with no new public surface or intent change; survivors route to patch. B3/E1/V3, B5/E2 and B9/V1 share their respective root causes.

| ID | Verdict | Evidence and route |
| --- | --- | --- |
| B1 | medium | FR-22 still requires a generic extension for other classes at local PRD:444, contradicting the corrected FR-21 and adopted AD-23. Patch the remaining direct claim. |
| B2 | medium | The replacement AI.Tools plan omits its predecessor's ongoing inventory-amendment and plan/index versioning obligations; future owners would lose the change-control rule. Patch the candidate and preservation checks. |
| B3 | medium | The completion checker proves ancestry against the mutable submodule HEAD while accepting an unrelated committed gitlink string. A fresh checkout could lack the approved plan. Patch committed-gitlink containment and a distinguishing fixture. |
| B4 | medium | The synthetic final-plan fixture contains none of the candidate's independent safety/removal gates yet passes completion. Patch shared semantic validation of the actual final approved bytes. |
| B5 | medium | A single unrelated example.invalid URL plus plain historical paths/hashes satisfies final immutable-link verification. Patch exact repository/revision/path links for every indexed inventory and receipt. |
| B6 | medium | SM-3 checks only today's date, allowing an overdue unreasoned outcome and invalidating completed evidence the next day. Patch a recorded completion-date assessment with outcome and overdue owner-reason evidence; preserve historical verification. |
| B7 | medium | Any nonblank deferralOwnerDecision, including an undecided sentence, passes completion. Patch an explicit structured owner decision bound to the exact audit, source and date without waiving unresolved gates. |
| B8 | medium | Source-story heuristics misroute the independent net11 runtime-maintenance entry and 5.11's technical re-citation to the K12 successor. Patch entry-specific recorded gates and tests. |
| B9 | medium | Existing release-automation discovery invokes Python tests and the selector Node file only; the new notes tests have no normal runner. Patch a Python discovery adapter without touching owned workflow files. |
| B10 | medium | Offline probes assert only exit codes and tool count, so an unrelated error or five wrong tool names could satisfy the claimed evidence. Patch complete error/stream, discovery and exact tool-name assertions. |
| E1 | medium | Independently confirms B3: no ancestry check targets the root's actual committed AI.Tools gitlink. Same patch group as B3. |
| E2 | medium | Independently confirms B5: per-inventory immutable URLs are not required. Same patch group as B5. |
| E3 | medium | select() followed by blocking readline() can hang indefinitely on a partial stdio line and prevent child cleanup. Patch chunk buffering under one absolute deadline, with a partial-line process fixture. |
| V1 | medium | Pre-verified verification gap: normal CI's release-automation commands never execute the new release-note output/refusal tests. Same patch group as B9; use the existing Python discovery lane. |
| V2 | medium | The real 5.10 delivery verifier requires its historical labels on current main, so delivering 5.11's superseding labels makes the prerequisite fail. Patch historical-delivery verification plus independent current supersession checks; do not edit frozen 5.10 evidence. |
| V3 | medium | Independently confirms B3; the synthetic git fixture currently treats every ancestry check as successful and hides the mismatch. Same patch group as B3. |
| O1 | medium | Parent audit: Parties 1.0.0 explicitly records session-only scope and no separate sign-off (:42, :61), but the new history classifies it as owner-approved via the later 1.1.0 receipt. Patch the historical authority without changing either receipt or predecessor. |
| O2 | low | Parent audit: sprint-status definitions use review, while this change writes in-review (the spec's separate vocabulary). Patch the sprint value and its completion-trigger fixture; the correction adds no behavior or complexity. |

All 18 findings survive as 14 patch groups. No new deferral or frozen-intent change is required. The existing approval, prerequisite and delivery blockers remain independent.

Resolution: all fourteen patch groups were corrected. Final parent verification passes 27 story tests, two Python release-note adapter tests (which execute the two pinned Node tests), candidate validation, expected completion refusal, published 2.0.1 offline/stdio probes, adopted AD-23, instruction sync and diff checks. No new work was deferred. The exact audit is prepared but not owner-accepted; upstream integration remains incomplete, so the spec stays in-review and sprint stays review. No commit or push is authorized or created. Fresh packet approval follows prerequisite delivery/rebinding: Story 5.10's mutable delivery register will change when delivered, so refresh its pending 5.11 bindings before requesting final exact-byte approval. Evidence: evidence/story-5-11/final-checks/checks.json.

- 2026-11-16 delivery continuation: the user requested “push all changes”, then “fix” for the missing-configuration refusal. Git delivery is now authorized; candidate inventory approval remains pending. The merged AI.Tools correction cfd1ebea92587cdea41b9aa2cff47358bf2f32f6 limits the shared checker to adopted modules. The containing baseline is updated; McpCli keeps its existing CI and no CI migration/configuration is invented. The earlier missing-file result remains historical evidence, not a current adoption requirement.
