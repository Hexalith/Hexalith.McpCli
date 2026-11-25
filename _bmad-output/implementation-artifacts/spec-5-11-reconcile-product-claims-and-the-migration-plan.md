---
title: '5.11 Reconcile product claims and the migration plan'
type: 'chore'
created: '2026-11-16'
status: 'in-review'
route: 'dispatch'
review_loop_iteration: 1
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
- `docs/release/migration-status.md` records the Gateway scope and per-surface retirement gates. The shared release-notes generator is owned by CiCd/Builds.

## Tasks & Acceptance

**Execution:**
- [x] `E/{inputs.json,investigation.md}`: capture full revisions, hashes, all eight inventory histories, approvals, fourteen labels and prerequisite states. Recheck 5.10 delivery before completion.
- [x] `A/eventstore-admin-migration-inventory-v1.0.3.md`, `A/technical-tools-migration-inventory-v1.0.4.md`, `.gitattributes`: add successors correcting pending self-description via receipt-based status; re-cite current companion inventories, including Folders 1.1.0. Preserve dispositions, pins, safety fields and owners. Record earlier approval separately from fresh approval.
- [x] `E/{approval.json,labels.json,verify_reconciliation.py,test_verify_reconciliation.py,upstream/}`: prepare hash-bound amendments and seven owner README patches. Check complete accounting, preserved bytes, class/gate semantics, approval roles, published inventory bytes and label integration; test the matrix and guard removals with exact streams.
- [x] `E/upstream/`: prepare the AI.Tools plan/rule amendment and the active module PRD, architecture, flow and README corrections mapped in `investigation.md`. Name actually available operations, `hexalith` setup and stdio discovery, safe refusal and confidential UI handoff. Preserve historical names as migration sources. No speculative operation availability.
- [x] Local planning files above, `README.md`, `A/epic-5-context.md`: align current claims, MR1/MR6, disposition semantics and inventory/plan citations without rewriting historical snapshots.
- [x] `docs/release/migration-status.md` records gateway-only scope, evidenced retirements, remaining binaries and gates. Appending this file to generated notes is deferred to CiCd/Builds by the 19 November decision below. AC3 remains open.
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

### Review Findings

2026-11-19 code review (scope 1a+1b+1c vs `008d95c`). Four layers returned. Decision resolved to defer (option 3). Twelve patch groups remain.

- [x] [Review][Defer] GitHub release notes do not append committed migration status [README.md:85] — deferred: CiCd perimeter forbids `.releaserc*`; Builds `invoke_plugins.mjs` emits conventional notes only. Keep `docs/release/migration-status.md`. Do not restore a module hook. Stop claiming generated notes append the status. already tracked (`deferred-work.md:1265`).

- [x] [Review][Patch] Stop claiming generated notes append the committed migration status [`README.md:85`]
- [x] [Review][Patch] Regenerate the Epic 5 deferral audit against the live ledger [`_bmad-output/implementation-artifacts/evidence/story-5-11/deferral-dispositions.json`]
- [x] [Review][Patch] Stop attaching predecessor source pins and “omits T01–T04” prose to current companion versions [`_bmad-output/implementation-artifacts/evidence/story-5-11/build_packet.py:101`]
- [x] [Review][Patch] Finish AD-23 alignment in PRD vision/admin-boundary and epics FR21 [`_bmad-output/planning-artifacts/prds/prd-mcpcli-2026-09-21/prd.md:21`]
- [x] [Review][Patch] Rebase AI.Tools patches onto the revision README cites, or stop claiming that revision already follows AD-23 [`README.md:46`]
- [x] [Review][Patch] Report one current state for the missing `.github/hexalith-ci.json` blocker [`_bmad-output/implementation-artifacts/evidence/story-5-11/inputs.json:435`]
- [x] [Review][Patch] Isolate `git apply` from a parent work tree [`_bmad-output/implementation-artifacts/evidence/story-5-11/verify_reconciliation.py:180`]
- [x] [Review][Patch] Save install streams on timeout and refuse non-object stdio JSON [`_bmad-output/implementation-artifacts/evidence/story-5-11/check_offline_cli.py:97`]
- [x] [Review][Patch] Require Admin 1.0.3 citations in successor labels [`_bmad-output/implementation-artifacts/evidence/story-5-11/verify_reconciliation.py:123`]
- [x] [Review][Patch] Inspect no-change owners at `origin/main`, not HEAD [`_bmad-output/implementation-artifacts/evidence/story-5-11/build_packet.py:555`]
- [x] [Review][Patch] Re-derive owner-topic `correct()` bytes in `check_patches` [`_bmad-output/implementation-artifacts/evidence/story-5-11/verify_reconciliation.py:184`]
- [x] [Review][Patch] Record the actual focused-test count [`_bmad-output/implementation-artifacts/evidence/story-5-11/checks.json:69`]

Rejected:

- blob/main successor label URLs (`blind-hunter`) — `false`: unpublished candidates cannot use a commit SHA yet; each label already binds inventory SHA-256, same pattern as 5.7–5.9; Parties SHA links are for already-published files.
- Receipts omitted from this review diff (`blind-hunter`) — `false`: chunk 1d was excluded on purpose; `secret-scan-*.json` and `offline-*.txt` exist in the tree.
- AD-21 vs FR-21 “same gate” (`blind-hunter`) — `false`: AD-21 still fails a `withdraw`/`defer` row that names a cataloged contract; FR-21 reports cataloged operations no row mentions. Those are different cases.
- Machine-local `ownerCheckout` paths (`blind-hunter`) — `low`: verifier requires sibling checkouts; `mainVerification` already says local refs only.
- Offline tests never invoke 2.0.1 (`blind-hunter`) — `false`: `check_offline_cli.py` installs and runs 2.0.1; `test_offline_cli.py` replays committed captures by design.
- Child ignores SIGKILL (`edge-case-hunter`) — `false`: SIGKILL cannot be ignored on this Linux runner.
- JSON-RPC id type coercion (`edge-case-hunter`) — `false`: published 2.0.1 and `validate_tools` use integer ids; no mismatch demonstrated.
- Stdio capture hash vs `stdoutSha256` (`edge-case-hunter`) — `false`: CLI records keep raw and retained hashes; stdio records the raw hash while writing a redacted file on purpose.
- Empty `packages` if nupkg prefix is not lowercase (`edge-case-hunter`) — `low`: NuGet cache names on this runner are already `hexalith.mcpcli.*`.
- Label text with fewer than two backticks (`edge-case-hunter`) — `low`: predecessor labels always carry that form; not an everyday path.
- Inventory frontmatter `IndexError` (`edge-case-hunter`) — `low`: every bound inventory has YAML frontmatter; not reached in this packet.
- Duplicate Story 5.10 README section (`edge-case-hunter`) — `low`: `replace` of a unique composed section; no duplicate demonstrated.
- `done`-prefix auto-completion (`edge-case-hunter`) — `low`: completion already refuses this candidate; a `done-…` status is not in use.

### Review correction and prerequisite recheck, 2026-11-22

All twelve patch items are prepared against current main. The refreshed packet
binds 65 ledger entries and all 30 owner patches. Story 5.10 delivery is verified
separately from its owner approval. McpCli has adopted CiCd and now has its
required configuration. All 45 focused tests passed; approved completion refuses
pending fresh exact-byte approval. The separate central release-notes deferral
keeps AC3 open. The audit decision, owner integrations, inventory publication,
final plan and containing gitlink remain outstanding. See
[evidence](evidence/story-5-11/verification.md) and [bindings](evidence/story-5-11/integration.json).

### BMAD review on 2026-11-22

The reviewers checked the refreshed packet against the original story baseline. The release-note implementation stays with CiCd/Builds under the existing deferral. These findings concern the accuracy of the packet and the evidence needed to report completion.

| Finding | Verdict | Evidence and disposition |
| --- | --- | --- |
| Blind 1 | Medium | The synthetic completion fixture passes with the live AC3 ledger entry open. Enforce the recorded deferral in completion. |
| Blind 2 | Medium | The success fixture carries candidate publication instructions and pending successor authority into its final plan. Check published authority and final wording. |
| Blind 3 | High | An ancestor check permits a later gitlink to revert the approved plan or rule. Check both blobs at the gitlink. |
| Blind 4 | Medium | The published artifact loop omits historical inventory and receipt blobs referenced by immutable links. Verify their contents at publication. |
| Blind 5 | Medium | The verifier accepts eight owner names with no inspection details. Recompute each recorded inspection at its revision. |
| Blind 6 | Medium | A second file can be added during patch application without affecting the declared target's hash. Check the patch's complete footprint. |
| Blind 7 | Medium | Comparing URL strings rejects an SSH checkout of the same GitHub repository. Reuse the repository identity comparison. |
| Blind 8 | Medium | The final-delivery verifier accepts one literal instruction even though the story recognizes an explicit push request. Preserve the instruction, its source and its scope. |
| Blind 9 | Medium | The builder starts replacing evidence before checking prerequisites and writes a provisional receipt twice. Validate the prepared outputs before replacing the pending packet. |
| Blind 10 | Low | The new offline probe passed in scratch. The committed run summary lacks a binding to that run's machine-readable result. Record it separately from the historical capture. |
| Edge 1 | Medium | The checked-in deferral explicitly leaves AC3 unmet. Same completion correction as Blind 1. |
| Edge 2 | Medium | The audit omits the ledger's resolution field, including the implemented scanner and its regression tests. Carry resolved evidence into the audit. |
| Edge 3 | Medium | The original migration-drift row has no recorded owner. The audit presents its fallback as a recorded assignment. Identify its source or mark the assignment as proposed. |
| Edge 4 | High | A reverted descendant remains an ancestor-check success. Same pinned-blob correction as Blind 3. |
| Edge 5 | Medium | The synchronization check reads the working directory. A local edit can hide a mismatch at the published root revision. Check its committed entries too. |
| Edge 6 | Medium | The final fixture can still describe both approved successors as pending. Same final-plan correction as Blind 2. |
| Edge 7 | Medium | Removing inspected paths and source revisions leaves all eight expected names. Same inspection correction as Blind 5. |
| Edge 8 | Medium | A stdio parsing failure bypasses redaction after the child has written its diagnostics. Keep raw capture in private scratch and sanitize on failure. |
| Verification 1 | Medium | Replacing the enumeration revision with HEAD leaves the original test green. Exercise divergent file listings at the two revisions. |
| Verification 2 | Medium | The published-completion fixture succeeds with no change to the recorded open AC3. Same completion correction as Blind 1. |
| Verification 3 | Medium | A retired-state receipt for exempt PS03 passes the SM-3 test. Count only eligible legacy servers. |

The review corrections passed all 45 focused tests. The completion verifier still requires exact-byte owner approval. The current evidence scan is recorded in the [verification report](evidence/story-5-11/verification.md).

### Owner decision on 22 November 2026

The requesting user replied “approve” to the exact reconciliation packet and its 65-entry audit. The reviewed receipt SHA-256 is `00bc7dc3cc8c2c4194b90a7cb11fb97b2b24baa31deeb8301cc55ed5083455a8`. The [audit decision](evidence/story-5-11/integration.json) binds both audit files and retains all 63 unresolved entries with their existing gates.
The user confirmed “Yes, I cover all 13 listed roles”. The [owner receipt](evidence/story-5-11/approval.json) records exact-byte approval of Admin 1.0.3, technical 1.0.4 and all 39 artifacts. The user separately authorized delivery to main across all repositories. McpCli published the inventories at `c6a40c10fd6db19cfce4cb0592f3b82bbb853729`. All eight owner repositories integrated their documentation. The user approved the final plan bytes. AI.Tools merged plan 1.3.0 in [PR 3](https://github.com/Hexalith/Hexalith.AI.Tools/pull/3), and McpCli pins the merge at `eed86f29`. The [final plan receipt](evidence/story-5-11/final-plan-approval.json) records the decision. AC3 remains open under the existing release-note deferral.

## Code review on 22 November 2026 after delivery

### Review Findings

**Changes requested.** The four BMAD reviewers examined the story against `008d95cc..efc7f815`. McpCli and all 18 direct references were synced to their respective main branches. All 47 focused tests and the instruction-sync check passed. With the required sibling checkout layout, both verifier modes failed on current FrontComposer main (`6d90c615`). Replaying just FrontComposer at its recorded delivery commit (`8199bcf7`) made delivery verification pass and made `--approved-completion` reach its expected AC3 refusal.

- [x] [Review][Patch] **High · Correct the published plan status.** The README still directs readers to plan 1.2.0 and says publication and integration are outstanding. The pinned plan is 1.3.0 at `2e591bdd`, with inventories published at `c6a40c10`. Refresh the README, release status, PRD, architecture spine, epics and Epic 5 context. Date the pre-delivery assessment that still appears current in `verification.md`. See `README.md:46`, `README.md:85`, `docs/release/migration-status.md:13`, `verification.md:42` and `verification.md:255`.
- [ ] [Review][Patch] **High · Correct ChatBot's approval and execution flows.** The delivered PRD still grants the CLI client approval and execution at line 630. The experience spine still promises human-delegated MCP approval after presence and actor checks at lines 337 and 488. Correct the active requirements and journeys to direct these actions to confidential UI, then check the resulting owner documents. See ChatBot commit `555183e9` and `evidence/story-5-11/upstream/chatbot/EXPERIENCE-4.patch:8`.
- [x] [Review][Patch] **High · Verify owner delivery across subsequent edits.** FrontComposer `09c4c90` edited digest rules and a date in the governance spine after the approved migration text landed. The full-file comparison with `origin/main` now rejects delivery. Verify exact bytes at the integrated commit and check the migration text and labels that must still hold on current main. See `verify_reconciliation.py:449` and `:450`.
- [x] [Review][Patch] **High · Require evidence of an AC3 decision change.** A Boolean on an existing decision that preserves open gates permits completion with deferred release notes. A changed decision needs explicit owner words, scope, date and source. The current waiver has no such binding. See `verify_reconciliation.py:342` and `test_verify_reconciliation.py:454`.
- [x] [Review][Patch] **High · Allow the release owner to resolve AC3 after packet approval.** Updating its ledger disposition changes the bytes and line references used to reproduce the approved audit. Refreshing that audit would invalidate the approved and published hashes. Check the historical audit against its recorded revision and accept a separately bound resolution of the same entry. Exercise this transition through the default verification path. See `verify_reconciliation.py:226` and `test_verify_reconciliation.py:459`.
- [x] [Review][Patch] **Medium · Correct the Epic 3 release gate.** The release status lists output-contract remediation as an outstanding restriction. The retrospective and PRD record closure on 8 November 2026. Keep the remaining candidate qualification requirements explicit. See `docs/release/migration-status.md:40` and `prd.md:479`.
- [x] [Review][Patch] **Medium · Validate the McpCli publication check and its recorded exception.** The delivery check validates nine upstream owners. It accepts a record that omits the root `inventoryPublication` section, including its failed Builds result and the scoped exception recorded for this delivery. Check the root publication evidence against the receipt. See `verify_reconciliation.py:433`, `:451` and `integration.json:255`.
- [x] [Review][Patch] **Medium · Bind Git delivery authorization to the approved packet.** The verifier accepts the word `authorize` with no footprint and ignores `deliveryAuthorization.approvalSha256`. Require the receipt and scope for the bytes authorized for delivery. See `verify_reconciliation.py:425` and the passing fixture at `test_verify_reconciliation.py:346`.
- [x] [Review][Patch] **Medium · Identify each upstream repository.** Commit ancestry on a local `origin/main` can come from a fork. Verify each configured remote's repository identity before accepting main containment, as the prior-delivery check already does for ChatBot and Memories. See `verify_reconciliation.py:311` and `:443`.
- [x] [Review][Patch] **Medium · Check immutable links within each inventory row.** Admin 1.0.3 and technical-tools 1.0.4 share a receipt. With one receipt link pointing to `main`, the correct link on the other row satisfies the global URL check. Verify the exact inventory and receipt targets within their respective cells. See `verify_reconciliation.py:252`, `:400` and `test_verify_reconciliation.py:449`.
- [x] [Review][Patch] **Medium · Include active flows in the no-change audit.** The inspected filename list omits UX and epic documents. Works' `EXPERIENCE.md:20` discusses shared heads and line 38 still describes exact MCP tools/resources. Review active channel and flow claims when establishing that an owner needs no edits. See `build_packet.py:345` and the [follow-up audit](evidence/story-5-11/owner-doc-follow-up/README.md).
- [ ] [Review][Patch] **Low · Remove provisional headings from delivered guidance.** Seven owner READMEs and the active planning patches carry candidate language into the published documents. Use status-neutral guidance for subsequent owner corrections and retain the dated candidate state in the historical packet. See `build_packet.py:173` and `:266`.
- [x] [Review][Patch] **Medium · Keep offline probe records consistent on failure.** The probe replaces capture files before all checks succeed. A failed rerun leaves the previous success manifest next to files from the new run. Capture in a fresh directory and publish the manifest and its streams together. See `check_offline_cli.py:139`, `:144` and `:150`.
- [x] [Review][Patch] **Medium · Exercise delivery through the default verifier entry point.** The normal test helper forces `blocked`, and the delivery fixtures call `check_completion` directly. A missing delivery check on the default path would still leave those tests green. Add a delivered packet with an invalid owner binding and assert the default command's refusal. See `verify_reconciliation.py:552`, `test_verify_reconciliation.py:67` and `:362`.

- [x] [Review][Defer] Generated release notes still omit the migration status. CiCd/Builds owns the existing AC3 deferral. Already tracked (`deferred-work.md:1265`).

#### Rejected

- **Low · Require an alternative layout for all owner checkouts.** The verifier documents sibling checkouts, which are also checked in the approved manifest. Replay succeeded in that layout. Supporting additional directory mappings is optional tooling work; the November 19 review already assessed this request.
- **False as a historical delivery failure · Require every later McpCli main revision to retain the original gitlink.** The story requires a recorded containing revision. The verifier checks its main ancestry, committed gitlink and approved plan/rule blobs at `verify_reconciliation.py:462`. A later pointer change is a separate event that can be assessed against that later revision.

## Code review on 25 November 2026

### Review Findings

**Changes requested.** Four reviewers examined the delivery verifier, its tests,
and the approval and integration records at `ec657cbc` against `008d95cc`.
The default command and `--approved-completion` both exited 1 with
`FAIL: deferral accounting/source/owner/gate mismatch`. The verifier suite ran
41 tests and reported 12 failures, including subtests, from the same mismatch.
The instruction-sync check passed.

Eight existing patch items still apply. The frozen audit replayed exactly with
both the ledger and the redactor from `c6a40c10`. The historical ledger alone
left two entries different. Invoking the delivery check separately reproduced
the whole-file drift failure on EventStore's PRD at `e2cb52894`. The unrelated
PRD updates left the migration passages intact. The previous findings also
cover the unsupported AC3 Boolean, root publication checks, Git authorization
binding, canonical repository identity, immutable URLs in each inventory row,
and the default command's delivered-state test gap.

- [x] [Review][Patch] **High · Require evidence that a legacy server cleared its removal gates before crediting SM-3.** The completion test credits Parties MCP on a five-field assertion without evidence for G01–G06, the separate restriction conflict, or the owning repository's removal. [`evidence/story-5-11/verify_reconciliation.py:355`]
- [x] [Review][Patch] **Medium · Verify the complete delivery footprint.** The nine recorded owner commits match their expected paths, and the recorded pin commit changes only the AI.Tools gitlink. The verifier reads individual blobs and accepts delivery commits that also change files outside that scope. [`evidence/story-5-11/verify_reconciliation.py:443`]
- [x] [Review][Patch] **Medium · Bind AI.Tools approval and hosted checks to the delivered revision.** The verifier accepts a pass string without comparing the tested head, the receipt's reviewed head, and the recorded merge. The fixture accepts unrelated heads and an open review. [`evidence/story-5-11/verify_reconciliation.py:485`]
- [x] [Review][Patch] **Medium · Check the final plan's authority and compatibility claims.** The fixture accepts draft status, claims that all compatibility surfaces are retired, and a replacement of confidential UI and refusal guidance with proprietary adapter and MCP execution. Check approved status and the applicable AD-23 and retirement claims. [`evidence/story-5-11/verify_reconciliation.py:478`]
- [x] [Review][Patch] **Medium · Bind the packet approval to the reviewed receipt and explicit role confirmation.** Removing `reviewedReceiptSha256` and `exactRoleConfirmation` passes the approval check. The published receipt has both fields, and its reviewed digest can be replayed from the pending form. [`evidence/story-5-11/verify_reconciliation.py:43`]
- [x] [Review][Patch] **Medium · Test the Projects rebase through the delivery caller.** The helper is tested directly. Removing its invocation from delivery verification leaves all 15 completion-binding tests green and would reject the recorded rebase. [`evidence/story-5-11/test_verify_reconciliation.py:422`]
- [x] [Review][Patch] **Medium · Test the final approval receipt digest with real receipt bytes.** The completion fixture replaces the digest check with a stub. A receipt with changed bytes and the same parsed fields needs to fail at the digest check. [`evidence/story-5-11/test_verify_reconciliation.py:371`]
- [x] [Review][Patch] **Medium · Require the completion date to follow delivery and approval.** The fixture accepts completion before publication, delivery authorization and final approval. A backdated completion would preserve a pre-deadline SM-3 assessment despite later delivery. [`evidence/story-5-11/verify_reconciliation.py:346`]
- [x] [Review][Patch] **Medium · Bind earlier historical approval receipts to their frozen revisions.** A changed Story 5.1 approver with a replacement digest passes both the historical and publication checks. The existing baseline receipt check covers Stories 5.7–5.10. [`evidence/story-5-11/verify_reconciliation.py:78`]

#### Rejected

- **Low · Add object-shape checks to every evidence reader.** A manually corrupted JSON document with a scalar or list at its root produces a traceback and still refuses verification. The recorded packet and normal generation produce objects.

The [owner documentation follow-up](evidence/story-5-11/owner-doc-follow-up/README.md)
contains the ChatBot and Works corrections and the status-neutral headings.
All nine patches applied in scratch. The new bytes await owner approval and
integration. CiCd/Builds still owns the generated-notes change for AC3.

### Build review triage on 25 November 2026

| Finding | Verdict | Evidence and route |
| --- | --- | --- |
| Blind 1 | Medium | An unrelated owner’s express denial passed the AC3 decision check. Bind affirmative approval to the release owner and audited entry. |
| Blind 2 | Medium | A copied Markdown file at an arbitrary source revision passed AC3. Verify the release-generation record, tagged source and generated body. |
| Blind 3 | Medium | Authorization limited to the root README passed delivery. Bind scope to the immutable authorization record. |
| Blind 4 | Medium | A modified open deferral owner passed completion. Check current ownership and gates for the unresolved entries captured by the audit. |
| Blind 5 | Medium | Approved text inside an HTML comment passed the current-main check. Verify visible passages and labels. |
| Blind 6 | False | The root gitlink check proves the story’s recorded containing revision. A later separately governed pointer change does not invalidate historical delivery. |
| Blind 7 | Medium | A modified Story 5.4 receipt with empty evidence passed the retirement guard. Require a separately approved successor with checked evidence. |
| Blind 8 | Medium | The inventoried path can disappear while the project survives elsewhere. Check for the retired project on owner main. |
| Blind 9 | Medium | The ChatBot PRD still promised CLI/MCP approval in MVP and integration requirements. Correct the remaining scope language in the owner patch. |
| Blind 10 | Medium | The Works experience entry still described exact tool and resource names. Use generic discovery of enrolled operations in the owner patch. |
| Blind 11 | Medium | A malformed response left no stdout capture to diagnose the failure. Preserve sanitized stdout and stderr in the cleanup path. |
| Edge 1 | High | The completion check could admit AC3 evidence while the ChatBot and Works conflicts remained active. Require the owner corrections in current main for completion. |
| Edge 2 | Medium | A copied release status followed by contradictory text passed AC3. Require the committed status as the final section of verified release output. |
| Edge 3 | Medium | Admin MCP could use a single composite record for G1–G6. Require its independent gates. |
| Edge 4 | Medium | A retirement receipt with an express denial met the previous text check. Require affirmative, bound owner approval. |
| Edge 5 | Medium | The current-main checker accepted guidance hidden in comments. Same patch as Blind 5. |
| Edge 6 | Medium | An authorization for one owner could pass full delivery. Same patch as Blind 3. |
| Edge 7 | Medium | A different valid-looking AI.Tools run URL passed. Bind the recorded hosted-check metadata as well as the tested and merged bytes. |
| Edge 8 | Medium | A failed stdio probe omitted its captured response. Same patch as Blind 11. |
| Verification 1 | Medium | Removing the paired-retirement rule left the focused suite green. Test rejection of each one-sided retirement. |
| Verification 2 | Medium | Hashing raw bytes for both stdio digest fields left the suite green. Exercise successful redaction with separate digest assertions. |
| Verification 3 | Medium | The positive Parties fixture contradicted the retained scope of its source owner receipt. Same patch as Blind 7. |
| Verification 4 | Medium | A local-only authorization passed the default delivery check. Same patch as Blind 3. |
| Verification 5 | Medium | An express AC3 denial passed completion. Same patch as Blind 1. |
