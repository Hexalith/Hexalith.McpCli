---
title: '5.7 Re-disposition EventStore Admin and technical-tool inventories'
type: 'chore'
created: '2026-11-13'
status: 'in-progress'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: '48076b1bd041b45250597937da82594e202985f3'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-5-context.md'
story_key: '5-7-re-disposition-eventstore-admin-and-technical-tool-inventori'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The approved Admin 1.0.1 and technical-tools 1.0.2 inventories still defer capabilities decided by adopted AD-23, and their compatibility labels cite those older gates.

**Approach:** Produce additive Admin 1.0.2 and technical-tools 1.0.3 amendments, validate complete row dispositions and approval chains, and prepare the corresponding upstream label updates. Completion requires exact-byte owner approval and integrated labels.

## Boundaries & Constraints

**Always:** Cover all 91 Admin and 68 technical rows using adopted classes; preserve pins, destructive/confirmation classifications and anchors. Operations/variants need outcomes and rationale; accounting records retain explicit governance. Remote Admin withdrawal requires confidential UI coverage before retirement. Withdraw local Admin behavior, documentation resources and synthetic lifecycle with accepted losses. Retain compiler/PS14 exemptions under merged AI.Tools authority. Defer undeclared Gateway replacements and forwarded authority with gaps/owners. `replace` requires an exact decorated type at its pin and eligibility; no Admin replacement is admitted. Retain G4's AV10/AV11, token-display and URL-disclosure prerequisites for future Admin parity.

**Never:** Rewrite approved inventories, receipts, AD-23 or historical evidence; change production, dependencies, census or gitlinks; execute legacy operations; infer parity or retirement. Preserve owner worktrees and read-only references. Prepare upstream patches before delivery approval; commits/pushes/merges need explicit authorization.

## I/O & Edge-Case Matrix

| State | Required result |
| --- | --- |
| Complete amendments | Exactly-once row accounting; adopted classes; named withdrawal rationale or deferral gap/owner |
| Restricted or invented replacement | Reject; require declared eligibility and pinned type evidence |
| Damaged row, anchor, class, safety field or chain | Reject with actionable diagnostics and nonzero exit |
| Missing owner roles, approval or integrated labels | Candidate remains pending; completion fails |

</frozen-after-approval>

## Code Map

Paths below use `A = _bmad-output/implementation-artifacts` and `E = A/evidence/story-5-7`.

- `A/{eventstore-admin,technical-tools}-migration-inventory-v1.md` — immutable AD-23/census predecessors.
- `_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/AD-23-{non-gateway-capability-classes.md,capability-class-map.json}` — disposition authority; `A/evidence/story-5-2/{approval.json,main-integration.json}` proves adoption/exemption delivery.
- `A/evidence/story-5-1/verification.md` — embedded gate: rows 229, Admin 381, technical 550, anchors 932, chain 1155. Reuse semantics against committed original pins; current-HEAD assertions are historical.
- `A/evidence/story-5-5/{labels.json,build-labels.py,verify-labels.py}` — historical versions; register requires refreshing all 14 citations across seven owning READMEs.

## Tasks & Acceptance

**Execution:**
- [x] `A/eventstore-admin-migration-inventory-v1.0.2.md` and `A/technical-tools-migration-inventory-v1.0.3.md` — add successors; correct PS01/PS02 to Admin 1.0.2 and current summary to 68. Keep historical 65-row approval distinct; record losses and retained gates.
- [x] `E/{verify_amendments.py,test_verify_amendments.py}` — retain row, registration, destructive, confirmation and anchor checks; add class/outcome, delta/hash-chain, role and completion checks. Test every matrix failure and disposition branch with guard-removal controls, process exit and both streams.
- [ ] `E/{approval.json,verification.md}` — SHA-256-bind predecessors, decision/map, candidates and changed rows. Record exact owner words/roles only after approval; retain commands, preservation checks and blockers. Candidate chain and verification packet are prepared; exact-byte owner approval remains pending.
- [x] Owning `README.md` files in EventStore, FrontComposer, Memories, Parties, Projects, Folders and ChatBot — prepare isolated README-only patches: UI gates PS01/PS02, retained exemptions PS03/PS14, all technical citations. Keep PS14 four-mode accounting, independent gates and Parties' blocked verdict.
- [ ] `E/{labels.json,verify_labels.py}` — designate successor register chained to Story 5.5; bind patch/commit bytes, inventory hashes, label anchors/hashes. Verify citation contents and gate text; require integrated upstream evidence for completion. Candidate register, seven patches and verifier are prepared; integrated commit evidence remains pending separate delivery authorization.
- [x] `E/`, this spec and `A/sprint-status.yaml` — retain validation/secret-scan evidence and record only the supported approval/delivery state.

**Acceptance Criteria:**
- Given adopted AD-23, when successors are checked, then every row is accounted for and prior approved bytes remain identical.
- Given existing labels, when amendments complete, then integrated labels/register match approved gates and citations.
- Given owner approval, when recorded, then named roles/exact hashes grant disposition authority only, never execution, enrollment or retirement.

## Verification

- `python3 -I E/verify_amendments.py` — candidate checks pass; approved-completion mode additionally requires owner and integrated-label evidence.
- `python3 -I -m unittest discover -v -s E -p 'test_*.py'` — all damaged inputs and controls pass.
- `python3 -I A/evidence/story-5-2/verify_class_map.py` — still adopted with original hashes.
- `python3 scripts/scan-evidence-secrets.py E --receipt /tmp/mcpcli-story-5-7-secret-scan.json` — clean; retain receipt after final evidence changes.
- `git diff --check` and baseline hash comparison — clean; historical approvals, inventories, AD-23, census and references unchanged.

## Implementation Notes

- 2026-11-13: The user approved this specification with "approve and continue". Frozen intent is locked; exact-byte inventory approval and upstream delivery remain pending their concrete packets.

- 2026-11-13: Candidate Admin 1.0.2 and technical 1.0.3 account for all 91/68 rows; all source facts and predecessor bytes remain preserved. Added explicit current applicability for historical decision prerequisites and retained independent UI/safety/retirement gates. Both candidate verifiers and all 20 focused tests pass, including 12 guard-removal controls. Seven isolated README-only patches pass read-only apply checks; exact section snapshots/full-blob hashes keep unrelated redactable README content out of the packet. Narrow byte-preservation attributes and final validation/secret-scan evidence are recorded in [the verification packet](evidence/story-5-7/verification.md).
- 2026-11-13: Status remains in-progress. Exact-byte owner approval, separate delivery authorization, inventory publication and seven upstream label integrations are still pending; both approved-completion modes correctly fail. No legacy operation, production change, census/gitlink update, upstream edit, stage, commit, push or merge was performed.
- 2026-11-13: Three independent review layers completed; all nine surviving patch groups are fixed, with three negligible findings rejected and none deferred. Final parent verification passes all 27 tests, both candidate verifiers and unchanged AD-23 adoption; both completion modes refuse the pending packet. Final evidence is retained in [review pass 1](evidence/story-5-7/review-pass-1/verification.md). The expanded scan required a typography-only correction to copied Admin header-scheme prose; the verifier requires that exact normalization, approved predecessors and technical inventory stay byte-identical, and pending Admin/EventStore hash bindings are refreshed. The story remains in-progress because its frozen completion gate requires exact-byte owner approval and integrated labels; the generic workflow's terminal done/commit actions cannot run yet.

## Spec Change Log

## Review Triage Log

### Review pass 1 (2026-11-13)

| Finding | Verdict | Route | Verified evidence |
| --- | --- | --- | --- |
| Blind B1: status-dependent test fixture | medium | patch | Parent discovery reproduced the spec subcase failure after the required in-review transition: literal in-progress replacement is a no-op. Construct the done fixture independently of current status. |
| Blind B2: label completion omits owner approval | medium | patch | Parent ran the positive label-completion fixture successfully while the actual receipt remained pending; the standalone label verifier reads no approval receipt. Reuse the complete owner/role/hash validation without recursive verifier calls. |
| Blind B3: published receipt unbound | medium | patch | Completion reads only the two inventory blobs at inventoryRevision; no read of its approval receipt occurs. Require the integrated receipt to match the locally validated approved receipt so public candidate links carry the same authority. |
| Blind B4: reverted integrated state accepted | medium | patch | Both completion checks prove ancestry but read only historical revision blobs. A revert preserves ancestry and can remove labels/inventories from current origin/main. Verify the current compatibility sections and immutable inventory/approval blobs too. |
| Blind B5: owning checkout identity unchecked | medium | patch | Repository URL is compared with historical JSON, while Git reads trust an independent ownerCheckout path. Check each checkout's origin identity before using its local origin/main as owner integration evidence; this remains local-ref verification, not a fresh network attestation. |
| Blind B6: absolute checkout paths | low | rejected | The retained packet intentionally records this workspace's owner object stores and local refs. Other locations fail closed; adding a checkout-mapping interface for a hypothetical relocation exceeds a direct correction to this documentary packet. |
| Blind B7: visible surface identity can drift | medium | patch | Parent independently changed displayed PS04 to Nonexistent.Package with rehashed section/patch bytes; all 14 labels still passed. Bind the displayed surface prefix to the unchanged historical identity. |
| Blind B8: interrupted candidate generation | low | rejected | Partial pending regeneration is reversible and its mismatched hashes fail verification; approved packets cannot be overwritten. Multi-file transactional generation adds complexity for an interrupted preparation command, with no false completion or approved-byte loss demonstrated. |
| Blind B9: non-object JSON traceback | low | rejected | Parent reproduced AttributeError for an array; the CLI refuses it with nonzero exit. It cannot admit a damaged packet. Extra container guards would improve only diagnostics for unsupported, non-packet input. |
| Blind B10: approval inputs outside scan scope | medium | patch | Parent inspected the scan manifest: neither additive inventory nor the spec is present. Added source-bound temporary-copy scans. The first expanded scan flagged abstract header-scheme prose; formatting the literal scheme as code, with an exact source-fact normalization regression, resolves it without changing facts, predecessors or scanner policy. Pending Admin/EventStore hashes are rebound and both scans refreshed. |
| Edge E1: quoted YAML done bypass | medium | patch | Both status regexes compare quoted captures directly with done. Valid double-quoted done avoids the completion gate; normalize supported YAML scalar quoting and cover both status sources. |
| Edge E2: no-op status fixture | medium | patch | Same reproduced failure as B1; the supplied diff already has in-review while the test replaces only in-progress. |
| Verification V1: ancestry guard-removal gap | medium | patch | Reviewer removed both merge-base checks and all four LabelTests still passed. Add negative merged/unmerged Git graph cases for owner and inventory commits, asserting exit and both streams. |
| Verification V2: suite fails after workflow transition | medium | patch | Parent independently reproduced the filed failure. Same status-fixture defect as B1/E2; refresh evidence after fixing it. |
