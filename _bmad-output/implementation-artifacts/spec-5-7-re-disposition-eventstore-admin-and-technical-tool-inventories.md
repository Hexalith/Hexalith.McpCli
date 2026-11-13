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

Code review pass 3 (bmad-code-review, 2026-11-13, after `06c1b93` applied the pass-2 and continuation patches). The scope was the deliverables again: 4,231 diff lines in 19 files, the pass-2 set plus `review-pass-2/verification.md`. Four layers ran (Blind B, Edge E, Acceptance A, Verification V); none failed. Of 47 findings, 12 survive in 10 patch entries, and 35 are rejected. Nothing new is deferred. Approved inventory and receipt bytes are untouched by every patch.

- [x] [Review][Patch] Running the test suite leaves bytecode in the packet, so the prescribed secret scan then fails
  - The child process in `test_real_process_accepts_only_exact_permitted_drift_reports` runs `python3 -I -c`. It loads `verify_amendments.py` or `verify_labels.py` through `spec_from_file_location` before either module sets `sys.dont_write_bytecode`, and `-I` ignores `PYTHONDONTWRITEBYTECODE`.
  - `tearDownModule` removes only the test module's own cache, and its `rmdir` fails silently on the non-empty folder.
  - Reproduced: `E/__pycache__/` holds `verify_amendments.cpython-314.pyc` and `verify_labels.cpython-314.pyc` (gitignored). `python3 scripts/scan-evidence-secrets.py E --receipt …` exits 2 with `scan-error`. The parent-review packet already notes that "review-generated bytecode was removed before scanning".
  - Fix: set `sys.dont_write_bytecode = True` first in the child code, or pass `-B`. Assert that the test leaves no `__pycache__` under `E`. Remove the stale cache before the final scan.
  - (A1) [_bmad-output/implementation-artifacts/evidence/story-5-7/test_verify_amendments.py:542]
- [x] [Review][Patch] No test pins the gate's per-module anchor counts, so the pinned-anchor re-read can silently stop
  - `verify_owner_packet` re-reads every Story 5.1 anchor at its pin (`verify_amendments.py:343`) and prints the count. Every test checks only `startswith('PASS:')` or the final summary line.
  - Replacing `:343` with `anchors = 0` passed all 40 tests.
  - Assert the exact lines `PASS: eventstore-admin: 91 rows, 277 pinned anchors, complete delta/hash chain` and `PASS: technical-tools: 68 rows, 105 pinned anchors, complete delta/hash chain` in both modes.
  - (V1) [_bmad-output/implementation-artifacts/evidence/story-5-7/test_verify_amendments.py:517]
- [x] [Review][Patch] The source `Disposition` rewrite has no damage test
  - `check_rows` forces `Disposition` to the amendment action and `Disposition / coverage` to `<action> / exclude` (`verify_amendments.py:225-228`). This covers 79 Admin and 27 technical rows.
  - Skipping either branch passed all 40 tests.
  - Add subcases that restore `defer` in an Admin `Disposition` cell and `defer / exclude` in a technical `Disposition / coverage` cell. Each expects the exact `FAIL: <module>:<key>: changed protected source field <header>` line.
  - (V2) [_bmad-output/implementation-artifacts/evidence/story-5-7/test_verify_amendments.py:175]
- [x] [Review][Patch] The label register's state and authorization guards have no tests
  - Three guards are uncovered: `invalid successor label state` (`verify_labels.py:205`), `label register must designate integrated successor state` (`:194`) and the per-field `deliveryAuthorization` check (`:196`).
  - Removing any of them passed all 40 tests. Without `:205`, a register in state `Integrated` exits 0 with "candidate only" and skips every delivery check.
  - Add these subcases:
    - a non-canonical state;
    - explicit `--approved-completion` with every integration present but a candidate state;
    - authorization missing only `source`, and missing only `approvedOn`.
  - Each subcase asserts the exit code, empty stdout and the exact stderr.
  - (V3) [_bmad-output/implementation-artifacts/evidence/story-5-7/verify_labels.py:205]
- [x] [Review][Patch] Several register fields are checked but never damaged in isolation
  - The fields are: label `sha256`/`file` (`verify_labels.py:147`), `row['gate']` (`:151`), the canonical 40-hex `integration.commit` (`:180`), and the before-section snapshot compared with the base section (`:124`, second conjunct).
  - Removing any of these checks passed all 40 tests.
  - Add one subcase per field with an exact `FAIL:` line. The before-section case should be re-hashed so that it passes the file-hash check.
  - (V4) [_bmad-output/implementation-artifacts/evidence/story-5-7/test_verify_amendments.py:698]
- [x] [Review][Patch] The workflow-status parser's fail-closed branches are untested
  - `yaml_status` rejects a duplicate key (`verify_amendments.py:304`) and an unsupported scalar (`:308`). These branches guard the spec/sprint `done` completion trigger.
  - Taking the last duplicate, or returning `None` for an unsupported scalar, passed all 40 tests.
  - Add a duplicated `status:` line and `status: [done]`, each expecting the exact `FAIL:` diagnostic.
  - (V5) [_bmad-output/implementation-artifacts/evidence/story-5-7/test_verify_amendments.py:407]
- [x] [Review][Patch] Some completion tests still assert only part of their output
  - These tests use `assertIn` or a `FAIL:` prefix instead of the full error, against the repository pitfall rule:
    - `test_published_approval_receipt_must_exist_and_match_validated_approved_bytes` uses `assertIn('approval', stderr)`, which the file path alone satisfies;
    - `test_standalone_completion_requires_full_owner_role_and_binding_validation`;
    - `test_forged_integrated_state_and_missing_delivery_authority`;
    - the reverted-inventory subtests;
    - the invalid `--root` refusal in `test_real_cli_candidate_and_completion_process_streams`.
  - Assert exit, stdout and the exact stderr in each case.
  - (B7) [_bmad-output/implementation-artifacts/evidence/story-5-7/test_verify_amendments.py:854]
- [x] [Review][Patch] Label-gate failures do not name the failing repository or file role
  - `verify_labels.git` drops Git's stderr and the repository path (`:45-48`). A failure among the seven checkouts therefore reads only `git show origin/main:README.md failed for label evidence`. `verify_amendments.git` already includes stderr.
  - The receipt check reports `…/approval.json: published inventory differs from approved candidate` (`:202-203`), calling the receipt an inventory.
  - Fix: include the repository path and stderr in the message, and say "artifact" instead of "inventory". The test at `:889` mocks its own message, and the published-artifact expectations change with the wording.
  - (B6) [_bmad-output/implementation-artifacts/evidence/story-5-7/verify_labels.py:47]
- [x] [Review][Patch] The packet's entry documents never point to the final 40-test state
  - `verification.md` opens with "all 27 tests" (`:8`) and "all 34 focused tests" (`:18`). `delivery/verification.md:23` and `review-pass-2/verification.md:29` repeat those counts.
  - None of them links [parent verification](evidence/story-5-7/review-pass-2/parent-review/verification.md), which records the 40-test final state and fresh scans.
  - Add a dated "Final state" pointer at the top of `verification.md` that names the 40-test parent packet. The historical counts stay as they are.
  - (B11, E19) [_bmad-output/implementation-artifacts/evidence/story-5-7/verification.md:3]
- [x] [Review][Patch] The tracked "approved bytes still say pending" deferral omits locations that the verifier enforces
  - The entry at `deferred-work.md:1037` is already tracked (E7). It lists the frontmatter, the intro and the A2 section.
  - It omits:
    - the G1 records: Admin 1.0.2 `:187` says "A2 successor still requires exact-byte owner approval", and technical 1.0.3 `:185` says "A2 needs fresh exact-byte approval";
    - every row's `[A2](#a2-amendment-approval-pending)` Approval cell;
    - the verifier constants that require them: `APPROVAL` (`verify_amendments.py:27`) and `PREREQUISITE_TOKENS` (`:37`, `:45`).
  - Extend that entry's evidence. Add this pass's rejected cosmetic successor items to its "may carry" list: B3, A3, A6 and B15 below.
  - (A2, E7) [_bmad-output/implementation-artifacts/deferred-work.md:1037]

**Rejected (35):**
- B1 low: the `.gitmodules` drift report prints twice on the amendments path. It is cosmetic, root `.gitmodules` currently equals the baseline, and the fix adds a parameter to `labels.verify`.
- B2 false: retained exemptions recorded as `withdraw`. AD-23 (`AD-23-non-gateway-capability-classes.md:250`) maps exempt local tooling to "`withdraw` from migration scope only after the named AI.Tools amendment; retain the tool, never count it as retired".
- B3 low: the fallback Amendment owner. PE01/PE02's source cells say "Owner: Builds maintainer role", but the hard-coded fallback assigns "FrontComposer and relevant census owning maintainers". These are retained records with unchanged governance. Correcting approved bytes needs an amendment, so it rides along with the tracked successor.
- B4 low: delivery authorization and read-back fields are unbound. Every delivered README must equal the reconstructed after-bytes (`verify_labels.py:181`), and the recorded `readmeSha256` values match all seven integrated READMEs. The extra guards would bind observation-only fields.
- B5 low: the McpCli root origin is unchecked. A fork clone would hold the evidence itself, and the fix adds a guard for a relocation that has not been shown.
- B8 false: the real-process expectation reuses code under test. The in-process tests at `test_verify_amendments.py:486` and `:875` assert fixed drift-report strings for controlled drift.
- B9 low: guard-removal evidence is not reproducible for the six newest methods. The parent packet claims none for them, and this pass's mutation run found the remaining gaps (V1–V5).
- B10 low: owner CI follow-ups are untracked. `delivery/verification.md` discloses every failed, cancelled and still-running owner run as inherited and non-passing, and those repairs belong to the owner repositories.
- B12 low: `yaml_status` scans the whole spec. A body line starting with `status:` fails loudly, and none exists.
- B13 low: the section ends at any `#` line. All fourteen integrated and current sections end at a `## ` heading or at EOF with no code fence. The same extractor binds the registered snapshots.
- B14 low: the replacement-claim denylist. Settled in pass 2 (B9/E9/V8). The delivered labels are byte-bound to their integrated commits.
- B15 low: the successors lack a verification footer. This is a cosmetic change to approved bytes and rides along with the tracked successor.
- B16 low: the `.gitattributes` whitespace exemption covers scripts. This is the repository convention for scanned packets (stories 4.18, 5.4 and 5.5) because the scan receipts bind every file. Narrowing it is more than a direct correction.
- E1 low: the builder drops a parent heading. Settled in pass 2 (A6); the builder refuses the approved packet.
- E2 low: the builder overwrites an integrated register when the receipt is missing or pending. This cannot happen while the published approved receipt exists.
- E3 low: the builder is not transactional. Settled in pass 1 (B8).
- E4 low: the builder `assert` is stripped under `-O`. Settled in pass 2 (E2).
- E5 low: the builder fails with `StopIteration` on a missing heading. The builder is retired.
- E6 low: a pending receipt can keep `approvalRequest`. The pending path cannot recur for the immutable approved receipt, and the fix adds a guard.
- E8 low: a local `origin/main` branch could shadow the remote ref. That needs a deliberately ambiguous ref, and the fix changes every Git mock in the tests.
- E9 low: `baseRevision` is not checked as the parent. Settled in pass 2 (E4).
- E10 low: absolute `ownerCheckout` paths. Settled in pass 1 (B6).
- E11 low: same as B14.
- E12 low: non-object JSON tracebacks. Settled in pass 1 (B9).
- E13 false: `read_text` without an encoding. The absolute Linux owner paths pin the gates to this workspace, where Python decodes UTF-8.
- E14 false: a regenerated sprint key stops forced completion. The integrated register forces completion regardless (`verify_labels.py:98`), and so does the spec status.
- E15 false: an anchor at a root `SKILL.md`. No row anchor targets one, and rows must equal the baseline predecessor bytes.
- E16 low: unverified read-back fields. Same as B4. The claimed FrontComposer mismatch is `ownerState.readmeSha256`, a pre-delivery observation of the owner's working tree.
- E17 false: the real-process test fails in the pending phase. That phase cannot recur because the receipt is approved, published and immutable.
- E18 low: temporary fixtures under the repository root. They are removed on exit and exist for milliseconds, and the fix needs a fixture redesign.
- E20 low: `git status` may refresh an owner index. Settled in pass 2 (E1).
- A3 low: AV13 reads `retain / exclude`. AV13 is a governance record, not an operation, so the `exclude` rule for operations does not apply. The wording rides along with the tracked successor.
- A4 rejected: the task text overstates current-section checks. The fix edits the spec under review.
- A5 rejected: the spec's ledger line references (`:1030`/`:1038`; the entries start at `:1032` and `:1037`). The fix edits the spec under review.
- A6 low: the successors dropped predecessor prose references. Their "Source notation" section keeps the immutable predecessor's observations binding, and restoring the prose needs an amendment that can ride along.

Code review pass 4 (bmad-code-review, 2026-11-13, after `491f114` applied the pass-3 patches). The scope was the deliverables again: 4,569 diff lines in 21 files, the pass-3 set plus `review-pass-3/run_guard_controls.py` and `review-pass-3/verification.md`. Four layers ran (Blind B, Edge E, Acceptance A, Verification V); none failed. Of 22 findings, 14 survive in 6 patch entries, and 8 are rejected. Nothing new is deferred. Every patch leaves the approved inventory and receipt bytes untouched; neither `approval.json` nor `labels.json` binds the scripts.

- [x] [Review][Patch] The pass-3 guard-control runner reports 7 of its 18 controls as detected even when nothing is removed
  - `replacement()` compiles each mutant into a copy of the module globals (`namespace = dict(original.__globals__)`). The tests inject their fixtures with `patch.object(L, 'read_json' | 'git' | 'checked_file', …)`, and the copied namespace never sees those patches.
  - Effect: the seven `L.verify` mutants read the real integrated `labels.json` and real Git, print `PASS: … integrated delivery verified`, and fail the target test at an unrelated assertion. Affected: the three `deliveryAuthorization` fields, label `file`/`sha256`/`gate`, and the before-section binding. For example, the authorization controls fail at the `Integrated`-state subcase (`test_verify_amendments.py:888`), not at the authorization assertion.
  - The detection rule (`:111`, `bool(result.failures) and not result.errors`) accepts any failure, which is why the vacuous result was counted.
  - Reproduced by the parent: identity "mutations" through the shipped `replacement()` still give 3, 1 and 6 failures on the three `L.verify` target tests. The same identity mutation on `V.check_rows`, `V.yaml_status` and `L.git` gives 0.
  - Rebound to the live module globals, each of the seven mutants fails exactly its intended subtest (A1, V1). The tests are sound; the runner and its "18/18 detected" claim (`review-pass-3/verification.md:28`, `review-pass-3/parent-review/verification.md:14`) are not.
  - Fix:
    - Build each mutant as `types.FunctionType(<function code>, original.__globals__, …)` so it sees the tests' patches.
    - Count a control as detected only with no errors and a failure whose text contains the removed guard's diagnostic.
    - Add an identity-mutation control that must report `detected: false`.
    - Re-run all 18 controls and record the result in the next pass's evidence, together with a correction note that the pass-3 receipt supported only 11 of them. The pass-3 runner and receipts stay unchanged.
  - The pass-2 `source_pins` control was recorded with `errors: 1` and `detected: true` (B2). No pass-2 runner was retained, and `test_historical_source_pins_require_every_baseline_root_declaration` now covers that guard independently, so nothing more is needed there.
  - (V1, B1, B2, E1, E2, E5, A1) [_bmad-output/implementation-artifacts/evidence/story-5-7/review-pass-3/run_guard_controls.py:32]
- [x] [Review][Patch] `test_resolvable_abbreviated_inventory_revision_is_rejected` fails on owner label drift that the gate only reports
  - The test runs the real integrated register against the owners' real `origin/main` refs and expects stderr to be exactly `FAIL: completion requires integrated inventory revision\n`.
  - `verify_labels.verify` prints `reported: <repo>: current origin/main compatibility labels differ from delivered candidate` (`verify_labels.py:189-190`) before it reaches the revision check (`:198-199`).
  - Pass-2 Decision 1 made that drift report-only, and Stories 5.9 and 5.10 will rewrite PS08/PS09/PS14. The verification layer injected a later section into one owner's `origin/main` README, and the test then failed with the `reported: chatbot: …` line ahead of the expected `FAIL:`.
  - It is the only test that runs the real register against live owner refs and expects an exact stderr. `test_real_cli_candidate_and_completion_process_streams` already derives its reports with `expected_process_reports`.
  - Fix: patch `L.git` so that `origin/main:README.md` returns each owner's delivered after-README, as `completion_fixture` does, and keep the real `rev-parse` resolution.
  - (V4) [_bmad-output/implementation-artifacts/evidence/story-5-7/test_verify_amendments.py:950]
- [x] [Review][Patch] Six `verify_amendments.py` guards can be removed without failing any of the 46 tests
  - The `check_rows` call to `check_replacement` (`:217`) is the only guard on the `Exact replacement` amendment column. `test_class_outcome_and_disposition_restrictions` calls `V.check_replacement` directly only (`:262-267`), and no test damages that cell through `check_rows`. Replacing the call with `pass` passed all 46 tests (V2). This is the frozen matrix row "Restricted or invented replacement".
  - `verify_owner_packet`'s `check_metadata` call (`:340`) and the preceding `successor version mismatch` check (`:339`) are tested only by calling `V.check_metadata` directly (`:418-428`). Removing either passed all 46 tests (V3, A2).
  - In `anchor_evidence`, three guards are untested: the continuation-without-path refusal (`:158`), the unresolved-anchor `raise` (`:178`, replaced with `continue`) and the `/SKILL.md` refusal (`:179`, which enforces the rule against using agent skills from `references/`). Removing any of them passed all 46 tests (A2).
  - On the approved packet, the receipt hash still rejects any byte change, but only with the generic `approval artifact/hash-chain binding mismatch`. A candidate with a re-bound receipt would pass, which breaks the repository rule that every guard needs a test that fails when it is removed.
  - Fix:
    - Damage a real row's `Exact replacement` cell (Admin AC01 and technical FH02) through `self.damaged(...)`/`check_rows`.
    - Damage the successor's `inventory_version` and, separately, its `source_revision` through `verify_owner_packet`.
    - Feed `anchor_evidence` synthetic rows with a leading `:12` continuation, an unmapped path, and a `references/<repo>/…/SKILL.md` anchor.
    - Each case expects the exact `FAIL:` line on an empty stdout.
  - `:239` (blank rationale or owner) is reachable only with synthetic whitespace cells, because the parser strips cells and `:208` refuses empty ones first. It is left as it is.
  - (V2, V3, A2) [_bmad-output/implementation-artifacts/evidence/story-5-7/verify_amendments.py:217]
- [x] [Review][Patch] Several tests still assert only part of their output
  - The guard-present half of `test_guard_removal_controls_for_safety_class_outcome_loss_gap_and_record` asserts only exit 1 (`:308`).
  - Both in-suite guard-removal tests (`:315`, `:390`) and `test_new_root_submodule_reports_drift_and_keeps_original_pins` (`:543`) assert `stdout.startswith('PASS: fixture checked\n')`.
  - `test_real_process_accepts_only_exact_permitted_drift_reports` asserts `run.stdout.startswith('PASS:')` (`:644`). It is the only test of the drift path, so a regression that turned injected drift into "completion requires owner approval and integrated labels" with exit 0 would pass.
  - Fix: assert the exact `FAIL:` line with an empty stdout in the first half, and the full fixed stdout everywhere else. The drift test should expect the same three amendment lines and one label line as `test_real_cli_candidate_and_completion_process_streams`.
  - (B10) [_bmad-output/implementation-artifacts/evidence/story-5-7/test_verify_amendments.py:644]
- [x] [Review][Patch] Replacement and anchor diagnostics do not name the failing module and row
  - `check_replacement` (`verify_amendments.py:189-194`) builds its messages from the capability class: a damaged AC03 reports `FAIL: A3: invented replacement; …`, and AM05 reports `FAIL: A1: restricted or non-Gateway replacement is forbidden`. Each class covers many rows.
  - Several messages give only the key: `anchor_evidence` (`:175`, `:179`) and the outcome checks in `check_rows` (`:245-273`). G1–G6 exist in both modules.
  - The frozen matrix requires actionable diagnostics for a damaged row.
  - Fix: pass a `f'{module}:{key} ({cid})'` label in place of the bare class, prefix the key-only messages with `{module}:`, and update the exact expectations, including the new `check_rows` case from the previous entry.
  - (B3) [_bmad-output/implementation-artifacts/evidence/story-5-7/verify_amendments.py:189]
- [x] [Review][Patch] The upstream table in `verification.md` still lists three pre-refresh base revisions without saying so
  - `verification.md:160-168` lists EventStore base `f2062f7f…` (patch `d2626f04…`), Projects `77067782…` and ChatBot `82f20d5e…`. The delivered `labels.json` and `delivery/label-publications.json` record `c08fcae8…`, `1ea04f79…` and `62e82201…`.
  - The "Final state" preamble marks only earlier test counts and pending-state statements as historical. No evidence document links the rebase transcripts or `delivery/pre-refresh/`.
  - Fix: add one sentence to the "Final state" preamble. It should say that delivery rebased the EventStore, Projects and ChatBot patches onto newer owner mains without changing label text, link `delivery/label-publications.json` and `delivery/pre-refresh/`, and name `labels.json` as authoritative for delivered bases and patch hashes.
  - (B4) [_bmad-output/implementation-artifacts/evidence/story-5-7/verification.md:160]

**Rejected (8):**
- B5 false: 36 rows "invent" owner names. The 34 rows beyond PE01/PE02 (AV01–AV13, AX01–AX07, FV01, FV04–FV09, PE03–PE09) have no owner column or owner text in their source cells, so the fallback is the approved amendment's own owner assignment and contradicts nothing. The diagnostic correctly says the owner differs from that preserved assignment. Only PE01/PE02's "Owner: Builds maintainer role" conflicts, and that is already tracked (`deferred-work.md:1040`).
- B6 low: the PS03/PS14 labels name "merged AI.Tools plan 1.2.0" without a link. Each label links the technical 1.0.3 inventory, which cites AI.Tools main `10b709b8…`, so the authority is one hop away. Changing the delivered labels needs a new relabel in two owner repositories.
- B7 low: no check that the old 1.0.2/1.0.1 citations were removed. None of the seven delivered after-sections contains one, and every label is byte-bound to its integrated commit. The fix adds a guard for a state that has not been shown.
- B8 low: CI does not bind the approved inventories or receipt. That needs a new CI test outside this documentary story. The local hash-chain gates and the next successor's predecessor binding catch any byte change.
- B9 low: `.gitattributes` leaves the predecessor, AD-23, Story 5.1 and Story 5.2 inputs at `text: unspecified`. `core.autocrlf` is unset here, and the gates are pinned to this Linux workspace by absolute owner paths (pass-3 E13), so they fail closed elsewhere. Changing other stories' line-ending attributes is more than a direct correction.
- B11 low: the original matrix table maps only the first 20 tests, and the pending branch of the real-process test is dead. Each later pass maps its own cases in its verification packet, and the pending phase cannot recur (pass-3 E17).
- E3 low: governance records outside `PREREQUISITE_TOKENS` need only a nonblank rationale. The approved bytes are hash-bound by the receipt, and changing a record's rationale needs a new owner approval. The fix adds a guard for a state that has not been shown.
- E4 false: a README without a trailing newline would give a malformed patch. All 21 base, delivered and current `origin/main` README blobs end with a newline, and the builder refuses the approved packet.

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

- 2026-11-13 review pass 3 implementation: Closed all ten accepted patch groups without changing approved inventory/receipt bytes. Added isolated negative cases and exact process documents for source dispositions, workflow scalars, register state/authorization, label fields, before sections and canonical integrated commits; both amendment modes now pin 277/105 anchor re-reads. Child imports disable bytecode before loading verifiers and assert the packet stays cache-free. Git errors name the checkout and retain stderr; receipt/inventory publication failures say artifact. The existing successor deferral now covers G1 language, every A2 Approval link, enforcing constants and the accepted cosmetic carry items. Final tests, guard-removal controls and scans are retained in [review pass 3 evidence](evidence/story-5-7/review-pass-3/verification.md).
- 2026-11-13 review pass 4 implementation: Closed all six accepted patch groups without changing approved inventory, receipt or label-register bytes. The corrected guard-control runner rebuilds each mutant over the live module globals and requires an unchanged baseline that passes, a failure with no errors, and the guard's diagnostic in a failing assertion. All 26 controls (the 18 from pass 3 plus 8 new ones) are detected, and an identity control is not. This corrects pass 3's "18/18 detected", which supported only 11. Three new tests cover the `check_replacement` call, the successor version and metadata calls, and the anchor continuation, unresolved-path, CODEOWNERS, declared-repository and `/SKILL.md` guards; the CODEOWNERS guard was also found untested while this group was applied. The abbreviated-revision test now serves the delivered README at owner `origin/main`. Partial assertions now compare full output. Replacement and anchor diagnostics name `module:key`. The entry document explains the pre-refresh upstream bases. All 49 tests, both verifiers, both completion gates, AD-23 adoption and a clean packet scan are retained in [review pass 4 evidence](evidence/story-5-7/review-pass-4/verification.md).

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

### Pass-3 continuation workflow review (2026-11-13)

All three workflow layers completed. Verification-gap review found no material gap and independently passed all 44 tests. Blind review supplied ten findings; edge-case review supplied two. The following rows preserve every individual verdict before grouping. No new deferral is created.

| Finding | Verdict | Route | Verified evidence |
| --- | --- | --- | --- |
| Blind B1: handoff spec scan became stale | low | patch | The handoff input binding predates this workflow's in-review status transition by two bytes. Retain that historical receipt and capture new final source bindings and scans after the final spec/status edits. |
| Blind B2: individual approval identity/instruction checks untested | medium | patch | The existing approval fixture omits both fields together, so either independent nonblank check may disappear without a failure. Add isolated missing/blank cases for approver and exactApprovalInstruction. |
| Blind B3: individual approval source/date checks untested | medium | patch | The fixture likewise omits approvalSource and approvedOn together. Both establish approval provenance; independently exercise absent/blank values through exact entry-point refusals. |
| Blind B4: approval schema check untested | medium | patch | The approval schema/baseline test changes only baselineCommit. Damage schemaVersion alone to prevent silently accepting unsupported receipt formats after a future guard change. |
| Blind B5: canonical inventory revision check untested | medium | patch | Missing inventoryRevision is covered but abbreviated resolvable revisions are not. Add an isolated abbreviated-revision refusal while preserving all other completion evidence. |
| Blind B6: nonblank pinned-anchor check untested | low | patch | The current anchor test changes range only. A whitespace-only pinned source line reaches the separate content predicate; add a direct damaged-content case. |
| Blind B7: unique compatibility heading check untested | low | patch | Current malformed-section cases exercise missing headings and reporting, but do not isolate duplicate-section refusal. Add a direct duplicate-heading case with the exact diagnostic. |
| Blind B8: multiline label refusal untested | low | patch | No fixture supplies CR/LF within a registered label. Add both values before reconstruction so removing the one-line guard changes the expected refusal. |
| Blind B9: origin query/fragment refusals untested | low | patch | Existing origin cases cover host and repository identity only. Add otherwise valid GitHub origins with query and fragment suffixes independently. |
| Blind B10: Parties approval citation guard untested | medium | patch | Existing rehashed label damage removes the blocked verdict; it does not isolate owner-approval.json. Retain the verdict while removing that citation and assert the specific refusal. |
| Edge E1: escaped double-quoted YAML status | low | rejected | yaml_status preserves the literal escape instead of interpreting it. The workflow writes plain scalar statuses, and the immutable integrated label register independently forces approved completion. Supporting/rejecting a new escape grammar adds a guard for an undemonstrated workflow state. |
| Edge E2: non-object JSON register traceback | low | rejected | Carried: the same non-object JSON diagnostic issue was rejected as Blind B9 in pass 1 and Edge E12 in pass 3. Arrays/null fail with a nonzero process result and cannot admit a damaged packet; an extra container guard improves only unsupported-input diagnostics. |

Blind B2-B10 receive independent focused regression cases. B1 is completed by the parent's final source and packet scans, after all review and status updates. The original approved inventory and receipt bytes remain immutable.

All nine regression findings are patched through isolated cases, including missing/empty/whitespace approval fields, a resolvable abbreviated inventory revision, whitespace-only pinned content, duplicate headings, CR/LF labels, origin suffixes and the Parties approval citation. Parent discovery and direct execution each pass all **46 tests**; both default and approved-completion verifiers, unchanged AD-23 adoption, all **18 guard-removal controls** and whitespace checks pass. No review item remains open and no new deferral was added. The spec is done and sprint status is review. Fresh final source bindings and a complete packet scan, captured after these status/triage edits, supersede the handoff receipts as current evidence: [final parent verification](evidence/story-5-7/review-pass-3/parent-review/verification.md).
