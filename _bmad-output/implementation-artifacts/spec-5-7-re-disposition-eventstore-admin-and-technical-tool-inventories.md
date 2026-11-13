---
title: '5.7 Re-disposition EventStore Admin and technical-tool inventories'
type: 'chore'
created: '2026-11-13'
status: 'done'
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
- [x] `E/{approval.json,verification.md}` — SHA-256-bind predecessors, decision/map, candidates and changed rows. The user approved the exact candidates with "approve" on 2026-11-13 under all previously confirmed owner roles; the receipt records the exact instruction, roles and separate Git delivery authorization.
- [x] Owning `README.md` files in EventStore, FrontComposer, Memories, Parties, Projects, Folders and ChatBot — prepare isolated README-only patches: UI gates PS01/PS02, retained exemptions PS03/PS14, all technical citations. Keep PS14 four-mode accounting, independent gates and Parties' blocked verdict.
- [x] `E/{labels.json,verify_labels.py}` — successor register chains Story 5.5 to the approved inventories, fourteen labels and seven integrated README-only commits. Both approved-completion gates pass against published receipt/inventory bytes and current owner main sections.
- [x] `E/`, this spec and `A/sprint-status.yaml` — retain validation/secret-scan evidence and record only the supported approval/delivery state.

**Acceptance Criteria:**
- Given adopted AD-23, when successors are checked, then every row is accounted for and prior approved bytes remain identical.
- Given existing labels, when amendments complete, then integrated labels/register match approved gates and citations.
- Given owner approval, when recorded, then named roles/exact hashes grant disposition authority only, never execution, enrollment or retirement.

### Review Findings

Code review pass 2 (bmad-code-review, 2026-11-13, after the in-spec pass 1). The scope was the deliverables, 3,813 diff lines in 18 files:
- the seven upstream label commits on `main`: EventStore `639c9d5c`, FrontComposer `19418a0c`, Parties `6bc68c8f`, Memories `a3f0b3a4`, Projects `065f0477`, Folders `583d3d49` and ChatBot `6a4ca07b`;
- both successor inventories, `.gitattributes`, the four evidence scripts, `approval.json`, `labels.json`, `verification.md` and `delivery/verification.md`.

Generated stdout/stderr, scan receipts, delivery transcripts and pre-refresh snapshots were left out. Four layers ran (Blind B, Edge E, Acceptance A, Verification V); none failed.

- [x] [Review][Patch] The completion gates fail once later approved work changes owner compatibility sections or root `.gitmodules` (Decision 1 resolved: **A. Report, don't fail**)
  - `verify_labels.py:183` requires each owner's current `origin/main` compatibility section to equal the 5.7 after-section. `labels.json` is `integrated`, so completion is forced on every run.
  - `verify_amendments.py:326` requires root `.gitmodules` to equal the baseline, and `source_pins` (`:138`) requires the Story 5.1 pin set to equal the working `.gitmodules`.
  - Stories 5.9 and 5.10 will rewrite the PS08/PS09/PS14 labels, and any new root reference changes `.gitmodules`. Either turns both gates red, and `test_real_cli_candidate_and_completion_process_streams` with them.
  - Fix:
    - Current-section drift and a changed working `.gitmodules` become `reported: …` stderr lines with exit 0, the repo's "reported, never failed" convention.
    - `source_pins` reads the baseline `.gitmodules` blob.
    - These still fail: recorded-commit bytes, ancestry, README-only delivery, commit hash and the immutable McpCli inventory/receipt blobs.
    - The current-section test expects the exact report, and a new-submodule test is added.
  - The user chose this after a deeper comparison with a supersession pointer and leave-as-is. Story 5.5's gate likewise checks recorded revisions only.
  - (B7, E5, E7) [_bmad-output/implementation-artifacts/evidence/story-5-7/verify_labels.py:183]
- [x] [Review][Defer] The approved inventory bytes still describe themselves as pending and undelivered [_bmad-output/implementation-artifacts/eventstore-admin-migration-inventory-v1.0.2.md:3] — deferred: correcting approved bytes needs a new version and exact-byte approval. The next technical (Stories 5.9/5.10) and Admin (Story 5.11) successors carry it (Decision 2 resolved: **Fold into next amendment**).
  - Both successors carry `status: pending`, `approval_status: pending`, the heading "A2 Amendment approval pending", "Candidate amendment … pending exact-byte owner approval" and "Candidate label patches remain undelivered". `check_metadata` (`verify_amendments.py:87`) requires those values.
  - All 14 integrated README labels link readers straight to these pages. Unlike AD-23, the bytes never say that the separate receipt sets the effective status.
  - The successors should state the approved status, cite the 5.7 receipt and move the labels with them. They can also carry the rejected cosmetic fixes B10 and A6.
  - (B1, E18, A1)
- [x] [Review][Patch] The completion triggers have no test that isolates them
  - Spec/sprint `done` trigger: with the real register integrated, `test_claimed_done_in_spec_or_sprint_cannot_bypass_approval` passes even when `verify_amendments.py:358-359` is removed. Feed it a candidate register.
  - Integrated-register trigger on the `V.verify` path (`verify_labels.py:98-99`): removed, `V.main([])` returns 0 on a forged integrated register. No test covers it.
  - `--approved-completion` delivery requirement (`verify_amendments.py:362`): removed, an approved receipt with undelivered labels returns 0. No test covers it.
  - Assert exit, empty stdout and the exact stderr in each case.
  - (V1, V2, V3, E14) [_bmad-output/implementation-artifacts/evidence/story-5-7/test_verify_amendments.py:335]
- [x] [Review][Patch] The label semantic guards are hidden behind a `FAIL:` prefix assertion
  - `test_citation_gate_and_required_semantics_damaged_with_rehashed_label` and `test_register_predecessor_coverage_inventory_patch_and_anchor_damage` assert only the prefix, so the gate and surface guards fire first.
  - Removing `verify_labels.py:154`, `:157`, `:160`, `:163`, `:165`, `:174` or `:175`, or `:106` (row coverage), still passes all 27 tests.
  - Assert `FAIL: <key>: <message>` exactly per subtest. Add cases for the technical SHA, the Admin citation/hash, the Admin "No Admin Gateway replacement" text, a module citation version, PS03 "never counted as retired", a replacement claim and the intro sentence.
  - (V4, E16, A2) [_bmad-output/implementation-artifacts/evidence/story-5-7/test_verify_amendments.py:454]
- [x] [Review][Patch] The delivery read-back guards are untested
  - `completion_fixture` always returns the candidate README and `README.md\n` for `diff`.
  - Removing `verify_labels.py:181` (integrated README bytes) or `:185` (README-only delivery) still passes every test.
  - The inventory/receipt blobs at `inventoryRevision` (`:197`) are never damaged.
  - Add subcases to `test_complete_delivery_fixture_and_each_completion_binding`.
  - (V5, A2) [_bmad-output/implementation-artifacts/evidence/story-5-7/test_verify_amendments.py:498]
- [x] [Review][Patch] The preserved-authority guards have no tests
  - No test triggers `approved predecessor bytes changed`, `preserved authority changed`, `root .gitmodules changed`, `exemption amendment is not integrated`, `AD-23 exact-byte owner adoption is required` or `approval required roles/source mismatch`. Add damage cases with exact stderr.
  - The `.gitmodules` case follows the outcome of the first decision.
  - (A2) [_bmad-output/implementation-artifacts/evidence/story-5-7/verify_amendments.py:325]
- [x] [Review][Patch] The origin-URL test never tries a non-GitHub host
  - Removing the host condition makes `https://gitlab.example/Hexalith/Hexalith.EventStore.git` pass.
  - (V6) [_bmad-output/implementation-artifacts/evidence/story-5-7/test_verify_amendments.py:583]
- [x] [Review][Patch] The PS01/PS02 `Operation inventory` rewrite has no damage test
  - Replacing `verify_amendments.py:230` with `continue` still passes all tests.
  - Add a subcase that restores the Admin 1.0.0 citation and expects `technical-tools:PS01: changed protected source field Operation inventory`.
  - (V7) [_bmad-output/implementation-artifacts/evidence/story-5-7/test_verify_amendments.py:111]
- [x] [Review][Patch] The default verifier says completion is still required after verifying it
  - Reproduced: plain `verify_amendments.py` prints "owner decision: approved; completion requires owner approval and integrated labels", because `main` reads only the CLI flag while `verify()` forced completion from the spec status.
  - Return the effective completion from `verify()` and print from it.
  - (B8, E10, A8) [_bmad-output/implementation-artifacts/evidence/story-5-7/verify_amendments.py:378]
- [x] [Review][Patch] Running the test file directly reports an error
  - Reproduced: `python3 -I …/test_verify_amendments.py` ends with `FAILED (errors=1)`. In `__main__`, `__cached__` is `None`, so `Path(__cached__)` raises `TypeError` in `tearDownModule`.
  - Return early when it is `None`.
  - (E15) [_bmad-output/implementation-artifacts/evidence/story-5-7/test_verify_amendments.py:57]
- [x] [Review][Patch] Delivery evidence never records the final results of the owner CI runs whose required checks were bypassed
  - Observed 2026-11-13: EventStore `CI` on `639c9d5c` failed at "Fail on blocking test failures". EventStore `main` CI already failed on `d457ecd5` and `f2062f7f`.
  - ChatBot `ci` and `release` failed on `6a4ca07b` and on its parent `62e82201`. Parties `CI` was cancelled (its parent failed).
  - FrontComposer, Memories, Projects and Folders are green.
  - Record these final states and their inherited causes next to the bypass note.
  - (B13, A4) [_bmad-output/implementation-artifacts/evidence/story-5-7/delivery/verification.md:40]
- [x] [Review][Patch] Seven delivery worktrees and branches were left behind
  - Each owner repository still has a `/home/administrator/projects/hexalith/.scratchpad/story-5-7-delivery/<repo>` worktree and the local branch `docs/mcpcli-5-7-inventory-labels`. All seven branches are ancestors of `origin/main`.
  - Remove the worktrees and delete the merged branches.
  - (A9) [_bmad-output/implementation-artifacts/evidence/story-5-7/delivery/worktrees.json:1]
- [x] [Review][Defer] McpCli `main` CI stays red for reasons outside 5.7, and no ledger entry tracks it [.github/workflows/ci.yml:1] — deferred: pre-existing.
  - Restore fails NU1202: Hexalith.Commons.UniqueIds 3.0.0 supports only net11.0 while the targets remain net10.0.
  - The census check fails on Builds-pin source drift (`Tools/package-version-audit.json` and three PowerShell qualification scripts).
  - Recorded only in the sprint-status comment and `delivery/verification.md:33-36`; still failing on `36a2d51`.
  - (B12)

**Rejected (26):**
- B2 false: overwritten Disposition/Removal gate cells. The intro lists the preserved fields and omits both. The predecessor stays immutable. `exclude` is mandatory without `replace`, so the hard-coded coverage is policy, not loss.
- B3 low: PS01/PS02/AV13 governance points at the v1 files. The cells reproduce the adopted, immutable AD-23 map, and changing them would need an AD-23 amendment.
- B4 false: PS03 governance. The AD-23 map governs PS03 by `classId` K13, and its row carries K13 and `exempt-local-tooling`.
- B5 false: row owners missing from `rolesCovered`. AD-23's normative policy fixes the required coverage. The owner column preserves source governance and claims no approval.
- B6 low: loose receipt bindings (no hashes in the request text, `candidatePacket` by path, free-form date, unvalidated `approvalRequest`, also A8). The inventory hashes are bound in `artifacts` and `delivery/authorization.json`, and adding guards to an approved receipt brings no reachable benefit.
- B6/A4 false: one "approve" covering approval and push. The request explicitly asked for both. The limit says delivery is not implied, and it was not.
- B9/E9/V8 low: removal-gate cells are checked by tokens and column positions. The approved bytes are hash-bound to the receipt, and the builder refuses to run on an approved packet.
- B10 low: shared intro text and the "deferred backup backend" wording. Changing approved bytes needs an amendment; it can ride along if the second decision chooses one.
- B11/A3 low: `blob/main` citations. The successor paths are immutable and every label carries the content SHA-256; re-pinning needs seven more upstream pushes.
- B11 false: the PS01 label omits local Admin losses. The spec requires UI gates in labels; the inventory records the losses.
- B12 false: no tracking for UI coverage and G4 fixes. They are owner-assigned open gates in the approved inventories, and Story 5.11 reconciles remaining gates.
- B14 false: stale sections and status mismatch. `verification.md` opens by marking the later pending statements as history. Spec `done` against sprint `review` is the normal state during review.
- B15 low: the final `git diff --check` saw only the working tree. `git diff --check 48076b1 HEAD` over every deliverable is clean.
- E1 low: the builder's `git status` can refresh an owner index. The builder refuses the approved packet, so this cannot recur.
- E2 low: the builder `assert` under `-O`. Unreachable for the same reason.
- E3 low: the `re.sub` template. The fixed gate constants contain no backslashes, and the builder is retired.
- E4 low: `baseRevision` not checked as the parent. The publication transcripts show every base is the rebased parent, and a check would add a guard.
- E6 low: absolute `ownerCheckout` paths. Settled in pass 1 (B6); other locations fail closed.
- E8 false: an unknown outcome defaults to `withdraw`. The class map must equal its baseline bytes (`verify_amendments.py:325`), so no unknown outcome can reach the code.
- E11 low: tracebacks on malformed JSON or map. Settled in pass 1 (B9); the map is immutable.
- E12 false: the standalone label verifier while the spec says `done`. It prints "candidate only" and claims no completion.
- E13 false: `splitlines` separators. None of the seven delivered READMEs contains a non-`\n` separator, so label lines match Git's.
- E17 false: PS14 loses the Memories refresh. The gate keeps "four-mode inventory", and the label names Story 5.10 accounting.
- A5 low: the candidate reached `main` in a concurrent `/pushall` before approval. The delivery evidence records it, the bytes were unchanged, and nothing is left to fix.
- A6 low: dropped census and authority headings. The tables are intact and no consumer parses those headings; this can ride along in an amendment.
- A7 false: weaker anchor checks. Row cells must equal the approved predecessor bytes at immutable pins, which Story 5.1's gate verified content by content.

## Verification

- `python3 -I E/verify_amendments.py` — candidate checks pass; approved-completion mode additionally requires owner and integrated-label evidence.
- `python3 -I -m unittest discover -v -s E -p 'test_*.py'` — all damaged inputs and controls pass.
- `python3 -I A/evidence/story-5-2/verify_class_map.py` — still adopted with original hashes.
- `python3 scripts/scan-evidence-secrets.py E --receipt /tmp/mcpcli-story-5-7-secret-scan.json` — clean; retain receipt after final evidence changes.
- `git diff --check` and baseline hash comparison — clean; historical approvals, inventories, AD-23, census and references unchanged.

## Implementation Notes

- 2026-11-13 delivery: The user replied "approve" directly to the exact-candidate and commit/push request. Recorded approval of the unchanged inventory hashes under all twelve previously confirmed roles, plus Git delivery authorization. Refreshed three upstream bases without changing label text and prepared seven isolated README-only commits, preserving original owner worktrees. Approval exposed state-dependent negative fixtures; tests now construct pending receipts independently of actual adoption and retain real process refusal coverage. All 27 focused tests pass after adoption. Earlier pending-approval notes below describe the pre-approval history.

- 2026-11-13: The user approved this specification with "approve and continue". Frozen intent is locked; exact-byte inventory approval and upstream delivery remain pending their concrete packets.

- 2026-11-13: Candidate Admin 1.0.2 and technical 1.0.3 account for all 91/68 rows; all source facts and predecessor bytes remain preserved. Added explicit current applicability for historical decision prerequisites and retained independent UI/safety/retirement gates. Both candidate verifiers and all 20 focused tests pass, including 12 guard-removal controls. Seven isolated README-only patches pass read-only apply checks; exact section snapshots/full-blob hashes keep unrelated redactable README content out of the packet. Narrow byte-preservation attributes and final validation/secret-scan evidence are recorded in [the verification packet](evidence/story-5-7/verification.md).
- 2026-11-13: Status remains in-progress. Exact-byte owner approval, separate delivery authorization, inventory publication and seven upstream label integrations are still pending; both approved-completion modes correctly fail. No legacy operation, production change, census/gitlink update, upstream edit, stage, commit, push or merge was performed.
- 2026-11-13: Three independent review layers completed; all nine surviving patch groups are fixed, with three negligible findings rejected and none deferred. Final parent verification passes all 27 tests, both candidate verifiers and unchanged AD-23 adoption; both completion modes refuse the pending packet. Final evidence is retained in [review pass 1](evidence/story-5-7/review-pass-1/verification.md). The expanded scan required a typography-only correction to copied Admin header-scheme prose; the verifier requires that exact normalization, approved predecessors and technical inventory stay byte-identical, and pending Admin/EventStore hash bindings are refreshed. The story remains in-progress because its frozen completion gate requires exact-byte owner approval and integrated labels; the generic workflow's terminal done/commit actions cannot run yet.

- 2026-11-13 completion: Published the approved inventory/receipt packet at 42d3c2fd48405e0f2c27f9b61f6d7025e4246934 and integrated all fourteen labels in seven owner main branches. Both approved-completion commands and all 27 tests pass after integration. [Delivery evidence](evidence/story-5-7/delivery/verification.md) records canonical commits, exact read-backs, authorization and CI observations. Concurrent /pushall work adopted prepared files and moved reference pins before publication; the publication commit's build/census inputs match its actual parent. Broad CI is blocked by inherited net10/net11 dependency incompatibility and Builds census drift, recorded separately without changing those inputs. Original checkouts were not edited by this task; concurrent changes and the unrelated Platform gitlink modification are preserved.

- 2026-11-13 review pass 2 implementation: Closed all eleven patch groups. Current owner compatibility-section drift (including absent or malformed sections) and working `.gitmodules` drift now emit exact `reported:` diagnostics with exit 0; original source coverage reads the baseline `.gitmodules` blob. Recorded delivery bytes, ancestry, README-only scope, commit hashes and immutable published inventory/receipt blobs remain blocking. Added isolated completion-trigger tests, exact semantic/authority/read-back/URL/citation diagnostics and real-process drift coverage; direct-file teardown handles an absent bytecode cache, and the default PASS message reports effective completion. Final owner CI outcomes and inherited failures are retained beside the bypass disclosure, and all seven clean merged delivery worktrees/branches were removed while preserving original checkouts. The 34-test focused suite and both completion gates pass. See [review pass 2 evidence](evidence/story-5-7/review-pass-2/verification.md). Workflow review and the parent final scan follow this implementation handoff; the two accepted deferrals remain unchanged.

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


### Continuation workflow review (2026-11-13)

All three required layers completed. Edge-case tracing returned no findings. Blind review and verification-gap review found the following additional regression gaps; each existing guard is reachable, but its specific rejection was not isolated in the test suite. All route to focused test patches and require no change to approved intent or runtime behavior.

| Finding | Verdict | Route | Verified evidence |
| --- | --- | --- | --- |
| Blind B1: label path confinement | medium | patch | `verify_labels.py:53` rejects escaping paths; no label-file absolute/symlink escape case exists in the tests. Add exact refusal and both-stream coverage using temporary files. |
| Blind B2: label schema | medium | patch | `verify_labels.py:97` checks schemaVersion, but no label schema damage fixture reaches it. Add an otherwise valid candidate with a changed schema. |
| Blind B3: historical owner identity | medium | patch | `verify_labels.py:117` binds registered owner identity; current tests damage checkout origin only. Mutate the registered repository independently. |
| Blind B4: canonical base revision | medium | patch | `verify_labels.py:121` requires a full canonical revision; no abbreviated-but-resolvable base fixture exists. Add its exact format refusal. |
| Blind B5: committed before snapshot | medium | patch | `verify_labels.py:124` binds the full before README hash; existing hash damage targets patch artifacts instead. Damage beforeSha256 alone. |
| Blind B6: per-owner row assignment | medium | patch | `verify_labels.py:128` checks ownership after global coverage; no fixture preserves global IDs while reassigning one owner. Add that case. |
| Blind B7: after reconstruction | medium | patch | `verify_labels.py:136` binds reconstructed full/section bytes; no isolated afterSha256 or independently rehashed section damage case exists. Add both. |
| Blind B8: exact README patch | medium | patch | `verify_labels.py:140` compares reconstructed patch bytes; the old test damages only the outer hash. Rehash a patch with an unrelated file/edit and require the exact patch-content error. |
| Blind B9: registered surface identity | medium | patch | `verify_labels.py:144` checks row.surface; the current test changes displayed label text. Change only the registered surface. |
| Blind B10: baseline root declaration coverage | medium | patch | `verify_amendments.py:138` checks historical source-pin coverage; the new drift fixture changes working declarations only. Damage the baseline Git blob independently. |
| Verification V1: approved builder overwrite refusal | medium | patch | `build_candidate.py:138` refuses approved regeneration before any writes, but tests import only source_fact. Add an isolated approved-packet entry-point refusal test with exact streams and unchanged artifact bytes. |


All eleven continuation-review findings above are patched by six additional isolated test methods. Parent verification passes all **40 tests** through discovery and direct execution, both completion gates, unchanged AD-23 adoption and whitespace checks. No review finding remains open; the two previously accepted deferrals remain already tracked in `deferred-work.md:1030` and `deferred-work.md:1038`. Final parent evidence and fresh exact-input/packet secret scans are retained in [parent verification](evidence/story-5-7/review-pass-2/parent-review/verification.md). The spec is done and sprint status is review, as required by the build workflow.
