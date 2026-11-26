---
title: '5.11 Reconcile product claims and the migration plan'
type: 'chore'
created: '2026-11-16'
status: 'in-progress'
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

## Code review pass 2 on 25 November 2026

### Review Findings

**Changes requested.** Four reviewers examined the evidence tooling, the owner
documentation follow-up, the approval and integration records,
`verification.md` and `docs/release/migration-status.md` at `88fd6347` against
`008d95cc` (a 4,311-line deliverables diff). The default verifier passed.
`--approved-completion` exited 1 with
`FAIL: AC3 generated release notes remain deferred by the owner`. The 46
reconciliation tests and 8 offline-probe tests passed. CI run 45711922776 on
`88fd6347` failed at the CiCd guard because the story commit moved the Builds
gitlink. All four layers returned 58 findings: 2 decisions, 16 patches, 1
deferral and 23 rejections. On 2026-11-26 the owner resolved both decisions, which leaves 18 open patches.

- [x] [Review][Decision] **Medium · Bind the owner-documentation follow-up before it removes the candidate headings.** Removing "(Story 5.11 candidate)" turns stale facts into current statements: Tenants and FrontComposer still cite "merged AI.Tools plan 1.2.0" (`build_packet.py:162`, `:167`; `owner-doc-follow-up/tenants.patch`), while 1.3.0 is approved and pinned. Projects, Parties and the shared README setup still install `--version 2.0.1` (`build_packet.py:177`), although v3.0.0 has been published. The follow-up has no patch, before or after SHA-256 and no replay test (`owner-doc-follow-up/README.md:13-27`). Completion checks only the ChatBot and Works follow-ups and tolerates the candidate headings elsewhere. Any owner correction of 1.2.0→1.3.0 or 2.0.1 fails `verify_current_migration_text` (`verify_reconciliation.py:724`) with "current main migration text drift", so the default verifier also depends on mutable owner main. Options: (1, recommended) refresh the facts, bind the follow-up by hash with a replay test, require it at completion and let the current-main check accept the delivered bytes or the owner-approved follow-up bytes; (2) status-neutral banners without plan or tool versions, with the tolerance widened to exactly those rewrites; (3) keep the candidate headings, limit the follow-up to ChatBot and Works and close the open heading item as won't-fix. Resolved 2026-11-26: the owner chose a new option 4, status-neutral wording with current-main drift reported rather than refused, after a deeper option analysis. Patch below.
- [x] [Review][Decision] **Medium · Choose how completion accepts a re-owned audited deferral.** Audited entry `ea9d3ee950934c10` (Story 5.4 F7 acceptance) was approved as "open; retain the source-spec acceptance gate". It now reads "historical acceptance record. The canonicalizer change is tracked by Epic 4 retro item 9 and Story 5.18" (`deferred-work.md:1014`). A separate resolution only closes statuses beginning `resolved`, `done`, `obsolete` or `superseded` (`verify_reconciliation.py:451`), so completion has no path through this entry. Story 5.18 is in backlog. Options: (1, recommended) an owner-approved `transferred` resolution that names the successor key and owner and is verified against sprint status; (2) restore the open acceptance gate in the ledger and name Story 5.18 there; (3) leave completion refusing until Story 5.18 closes the entry as resolved. Resolved 2026-11-26: the owner chose option 2 after a deeper analysis. The gate is still open because Story 5.18 is in backlog, and the six-item batch lists F7 among its skipped findings (`deferred-work.md:1704`). Patch below.
- [x] [Review][Patch] **High · Restore CiCd's Builds gitlink.** `88fd6347` moves `references/Hexalith.Builds` from the CiCd v6.8.3 pin `62876129` to the local checkout `bf8a28b4`. This repeats `7f51c059`, which `59b8a121` (github-actions) had reverted. The guard fails CI with "gitlink (actual … bf8a28b4…, expected … 62876129… from v6.8.3)". The spec's Never rule leaves Builds untouched. `7e3f3a77` (github-actions) restored the pin on main during this review, but the local checkout is still at `bf8a28b4`, so the next story commit would sweep it in again. Align the local checkout with the committed pin and stage only story paths. [`references/Hexalith.Builds`]
- [x] [Review][Patch] **Medium · Make the owner follow-up status-neutral and report current-main drift (Decision 1, option 4).** In `owner-doc-follow-up/` and `build_packet.py:162`, `:167`, `:166` and `:168`, cite "the approved AI.Tools migration plan" instead of "merged AI.Tools plan 1.2.0". Replace "The published McpCli 2.0.1 tool predates Projects enrollment." with "An installed tool discovers them only from a published McpCli release that enrolls Projects.Contracts 2.0.0." Keep the verified 2.0.1 install line. Add patch SHA-256s to `owner-doc-follow-up/README.md`. In `verify_current_migration_text`, print `reported: <owner>: current main migration text drift: <path>` on stderr instead of refusing. Strict checks of delivered bytes at the recorded commits and the ChatBot/Works completion gate stay unchanged. The three drift tests assert the exact reported line. [`evidence/story-5-11/verify_reconciliation.py:724`, `test_verify_reconciliation.py:670`]
- [x] [Review][Patch] **Medium · Restore the audited status of `ea9d3ee950934c10` (Decision 2, option 2).** Replace the status at `deferred-work.md:1014` with `status: open; retain the source-spec acceptance gate`. Move "The canonicalizer change is tracked by Epic 4 retro item 9 and Story 5.18." onto that entry's `evidence:` line. Keep the line count unchanged and re-run the verifier. [`_bmad-output/implementation-artifacts/deferred-work.md:1014`]
- [x] [Review][Patch] **Medium · Record the 23 changed audited deferrals as a completion blocker.** Replaying `check_retained_deferrals` against the current ledger refuses at `1c8ef2a87fc429cc`. 23 of the 65 audited entries have changed `sourceStatus`, and `integration.json` has no `deferralResolutions`. The blockers (`integration.json:94`) and the follow-up summary (`verification.md:269-276`) name only AC3 and the ChatBot/Works guidance. The completion fixtures replay the publication ledger (`test_verify_reconciliation.py:347`), so nothing shows this. [`evidence/story-5-11/integration.json:94`]
- [x] [Review][Patch] **Medium · Point the release status at an approved authority index.** The status calls `inputs.json@c6a40c10` the "approved inventory index" that "records inventory authority". That file records Admin 1.0.3 and technical-tools 1.0.4 as `candidate-pending`, so a release reader following the link sees pending authority. The approved plan 1.3.0 and the approval receipt hold the effective authority. [`docs/release/migration-status.md:11`]
- [x] [Review][Patch] **Medium · Back or restate the 3.0.0 offline probe claim.** The 25 November section says the `3.0.0+ad7f963…` Release executable passed Projects discovery, Tenants description and ChatBot unknown-operation refusal. `check_offline_cli.py` installs and probes only published 2.0.1 with the Parties/Tenants cohort and `folders.unavailable` (`:26-29`, `:142-145`), and no capture was retained. [`evidence/story-5-11/verification.md:278`]
- [x] [Review][Patch] **Medium · Finish the ChatBot follow-up's CLI and MCP corrections.** The patched `cli-automation-client` row now covers McpCli CLI operations but keeps "user-delegated via OAuth device flow", which McpCli's README and source do not implement. The experience row "explicitly exposed on UI, CLI, and/or MCP" remains beside the both-heads rule. PRD line 997 still promises "UI/API, CLI, and MCP association/status/audit parity" although association decisions are UI-only. None of these phrases is in `check_owner_conflicts`. [`evidence/story-5-11/owner-doc-follow-up/chatbot.patch`]
- [x] [Review][Patch] **Medium · Test that the `integrated` state triggers completion.** Removing the `integration`/`labels` `integrated` trigger leaves all 46 tests green. A default run on `state='integrated'` then prints PASS without delivery, AC3 or SM-3 checks. [`evidence/story-5-11/verify_reconciliation.py:932`, `test_verify_reconciliation.py:297`]
- [x] [Review][Patch] **Medium · Test each half of the ChatBot/Works guidance check.** Removing either the required-sentence half or the obsolete-claim half leaves all tests green, because the test reads real owner main, where both halves fail. [`evidence/story-5-11/verify_reconciliation.py:497`, `test_verify_reconciliation.py:520`]
- [x] [Review][Patch] **Medium · Exercise the separate deferral-resolution path.** No test contains `deferralResolutions`. Neutralizing the resolution binding (`:447`) or the missing/duplicate check (`:440`) leaves all tests green, so a denial or a wrong-owner resolution would close an audited gate. [`evidence/story-5-11/verify_reconciliation.py:445`, `test_verify_reconciliation.py:528`]
- [x] [Review][Patch] **Medium · Test the SM-3 retirement and outcome guards.** Removing any of these leaves all tests green: the Parties verdict approval and `retirement-ready` check, resolved G01–G06 with recorded owners, the clean-scan manifest binding, gate-proof surface/gate/result/removal, pending or slip with retirements listed, and the pre-deadline `pending-not-met` rule. [`evidence/story-5-11/verify_reconciliation.py:508`, `test_verify_reconciliation.py:734`]
- [x] [Review][Patch] **Medium · Test the completion-date and owner-decision bindings.** Removing the decision-to-approval instruction and receipt binding, the future `completedOn` check or the `decidedOn`-after-completion check leaves all tests green. [`evidence/story-5-11/verify_reconciliation.py:626`, `test_verify_reconciliation.py:544`]
- [x] [Review][Patch] **Medium · Test AC3 release identity and date order.** Removing the published, non-draft, tag and `id` check, or the release→publication→evidence→decision ordering, leaves all tests green. The full-revision (`:417`) and decision-date (`:422`) messages also have no test. [`evidence/story-5-11/verify_reconciliation.py:383`, `test_verify_reconciliation.py:510`]
- [x] [Review][Patch] **Medium · Test the delivery bindings.** Removing any of these leaves all 46 tests green: the published receipt's approval and digest (`:689-690`), the AI.Tools link count (`:803`), the `aiToolsCommit` match (`:873`), the Story 5.10 binding (`:951-954`), "rebased document base differs" (`:708`), "Git delivery authorization predates exact-byte approval" (`:825-827`) and "invalid owner rebase footprint" (`:850-851`). Parent mutants confirmed the last three. [`evidence/story-5-11/verify_reconciliation.py:708`, `test_verify_reconciliation.py:544`]
- [x] [Review][Patch] **Medium · Test the offline probe's `main` exit contract.** No test calls `main`. A `main` that returns 0 or prints PASS after a failure would ship undetected. [`evidence/story-5-11/check_offline_cli.py:171`]
- [x] [Review][Patch] **Low · Mark the undated pre-delivery sections as historical.** "Prepared changes", "Checks and evidence" and "Completion gates retained" sit at the same level as the dated sections. They still say a semantic-release hook preserves the generator (`:86`), list the removed Node tests (`:102`), require fresh exact-byte approval (`:155`) and call Story 5.10 delivery incomplete (`:158-159`). [`evidence/story-5-11/verification.md:60`]
- [x] [Review][Patch] **Low · Compare commit and publication dates in UTC.** `commit_date` takes the committer-offset date from `%cI`, while `published_at` is UTC. A commit made just after local midnight on a nightly release fails or passes the ordering check by one day. [`evidence/story-5-11/verify_reconciliation.py:361`]
- [x] [Review][Patch] **Low · Keep failure evidence when the probe gets a non-object response.** A `result` or tool entry that is not an object raises `AttributeError`. `run_probe` and `main` catch only `OSError`, `ValueError` and `SubprocessError`, so the staging directory is deleted instead of being renamed `failed-*`. A stub server returning `"result": []` reproduced this. [`evidence/story-5-11/check_offline_cli.py:164`]
- [x] [Review][Defer] Nine ledger statuses carry the future date 2026-12-21 [`deferred-work.md:259`] — deferred: pre-existing. They were written with the six-item deferred-work batch (`deferred-work.md:1689`), not by this story. They include audited entries `bcf011d9603aebe0` and `a03161fe049a33d2`.

#### Implementation follow-up on 26 November 2026

The pass-2 changes are prepared and replay the published packet without
changing its approved hashes. The Builds checkout matches the CiCd pin.
The default verifier reports EventStore PRD drift and verifies the
original delivery. The nine status-neutral owner patches include the
ChatBot and Works guidance corrections and await fresh owner approval
and integration. The restored F7 acceptance gate leaves 22 of the 65
audited statuses changed. These require separate owner resolutions.
CiCd/Builds still owns AC3, and completion remains blocked.
[Verification evidence](evidence/story-5-11/verification.md)

#### Rejected

- **Low · Pin the NuGet source for the offline probe.** The user-level NuGet configuration lists only nuget.org, and McpCli has no repository NuGet.Config. Pinning would add configuration with no observed exposure.
- **False · The verifier is tuned to conversation wording.** Delivery authorization must equal the immutable publication record (`verify_reconciliation.py:823`), and the approval receipt is hash-bound. The phrase set admits only recorded words.
- **False · GitHub rule bypasses and Builds checks lack authorization (blind and acceptance).** The recorded "push all changes of all repositories to main" instruction authorized direct pushes, which GitHub reports as bypasses. Builds does not apply to owners that have not adopted CiCd, and the McpCli Builds exception was user-authorized.
- **Low · The final-plan approval is weaker than the packet approval.** It is an immutable owner receipt in which the same owner, covering all 13 roles, replied "approve" to the exact plan SHA-256. Strengthening it would need a new receipt.
- **False · Published secret-scan findings need follow-up.** The flagged spans are the quoted test canary `opaque-private-canary` in ledger summaries, not a credential.
- **False · The migration status goes stale once appended.** It is dated, makes no enrollment claim, and per-release refresh belongs to the deferred AC3 work owned by CiCd/Builds.
- **Low · Session-scope inventories cite themselves as receipts.** These are approved, published bytes, and the `session-scope-only` authority distinguishes them.
- **False · `.replace('\n+', '\n')` could strip legitimate lines.** It applies only to the appended literal (`build_packet.py:118-126`), where no other line starts with `+`, and the output is byte-verified.
- **Low · Hard-coded `.github/workflows/release.yml` and tag pattern.** The check binds the CiCd-delivered workflow that exists today. A rename fails closed in the still-deferred AC3 path.
- **Low · Summary-hash IDs give no resolution path.** The check fails closed, and the replay found no changed audited summary.
- **False · Sanitizer drift yields spurious mismatches.** The replay shows the 42 unchanged entries compare equal. Only `sourceStatus` differs in the other 23.
- **Low · Dead `correct()` replacement targets.** Twelve targets match nothing, but the targeted claims are absent from owner main, and the delivered bytes were verified. No surviving stale claim was demonstrated.
- **Low · Banner insertion ignores front matter and fences.** This is latent in the frozen generator, and the delivered banners were verified.
- **False · Tracebacks from `build_packet.py`.** A loud failure on malformed input is correct behavior.
- **False · Verifier tracebacks on null bindings.** They still refuse. The 25 November review rejected object-shape checks as low.
- **Low · Probe timeouts lose that probe's streams.** Help and discovery commands are unlikely to time out, and a fix adds a branch.
- **Low · An empty `packages` list passes.** The 19 November review rejected this as low, and the current manifest records `hexalith.mcpcli.2.0.1.nupkg`.
- **Low · An uninitialized submodule falls back into McpCli.** Wrong-repository reads fail against expected hashes, and the sibling layout is documented (22 November rejection).
- **Low · `--root` for another checkout.** The only effect is a mismatch refusal.
- **False · `sourceRepository` substring match.** `inputs.json` is hash-bound by `approval.json` artifacts, so the check runs only on frozen bytes.
- **Low · Locale-dependent `read_text`.** Python coerces the C locale to UTF-8, so the failure is unlikely, and the fix touches many call sites.
- **Low · PS01/PS02 cite Admin 1.0.3 while labels keep 1.0.2.** Both name the same G1–G6 set. These are approved, published bytes.

## Code review pass 3 on 26 November 2026

### Review Findings

**Changes requested.** Four reviewers examined the evidence tooling, the owner
documentation follow-up, the approval and integration records,
`verification.md`, `docs/release/migration-status.md`, the 3.0.0 offline
capture and the F7 ledger hunk at `3a112628` against `008d95cc` (a 4,973-line
deliverables diff). The default verifier exited 0 and reported EventStore PRD
drift. `--approved-completion` exited 1 with
`FAIL: AC3 generated release notes remain deferred by the owner`. All 65
reconciliation and offline-probe tests passed in one run (40.8 s). CI run
45729222188 on `3a112628` failed in `Manifest.Tests` (NU1109 and eight
dependency-policy and native-catalog failures). These failures are outside this
story's evidence-only commits, and `main` was already red at `7e3f3a77`. During
the review, `40159c8c` replaced the stale AC3 anchor and added a rerun note.
The four layers returned 50 findings: 1 decision, 8 patches (one already applied
by `40159c8c`), no deferrals and 34 rejections. On 2026-11-26 the owner resolved the decision, which leaves 8 open patches.

- [x] [Review][Decision] **High · Keep the approved PS03 and PS14 labels intact in the owner follow-up.** `owner-doc-follow-up/frontcomposer.patch` (README `@@ -29,8`) and `memories.patch` (README `@@ -133,3`) rewrite the approved label lines, changing "under merged AI.Tools plan 1.2.0" to "under the approved AI.Tools migration plan". `labels.json` is hash-bound by `approval.json` and still holds the 1.2.0 text. The current-main label check requires each approved label exactly once (`verify_reconciliation.py:879-883`). Replaying the FrontComposer or Memories follow-up as owner main makes the default verifier exit 1 with `FAIL: PS03: current main label is missing or duplicated` (or `PS14`). ChatBot and Works pass. No test sends the replayed follow-up through `check_delivery`: `replay_follow_up` (`test_verify_reconciliation.py:52-82`) feeds only `check_owner_conflicts`. The follow-up README says only that these edits "remove provisional headings". Pass-2 decision 1 kept the strict label check. Even once labels are resolved, integrating the follow-up raises current-main drift reports on about ten owner files. The EventStore report is line-level: the owner appended a DW-549 sentence to a delivered row and kept the McpCli text. Options: (1, recommended) keep both label lines byte-identical to `labels.json` and change only the surrounding banners and headings. Fold the 1.2.0 label wording into the next labels successor, refresh the patch SHA-256s, and add a `CompletionBindingTests` case that serves each replayed follow-up as owner main. It asserts the exact default and completion streams, including the expected drift reports. (2) Prepare a hash-bound labels successor that carries the status-neutral PS03/PS14 text, have owners approve it with the follow-up, and let the current-main check accept the approved successor labels while delivered commits stay strict. (3) Let the current-main label check accept either the approved label or the exact follow-up line bound by its patch digest. Resolved 2026-11-26: the owner chose option 1 after a deeper option analysis. Plan 1.3.0 says K13 and K14 "remain the named local exemptions adopted by plan 1.2.0" (`hexalith-mcpcli-migration-instructions.md:28-30`), so the approved label text is accurate and needs no labels successor. Patch below.
- [x] [Review][Patch] **High · Keep the PS03 and PS14 labels byte-identical in the follow-up (Decision 1, option 1).** Remove the label-line change from `frontcomposer.patch` (README `@@ -29,8`) and from the first README hunk of `memories.patch` (`@@ -133,3`), keeping the heading and banner changes. Refresh both patch SHA-256s in `owner-doc-follow-up/README.md`. Add a `CompletionBindingTests` case that serves each of the nine replayed follow-ups as owner main through `run_binding` and asserts the exact default and completion streams, including the expected `reported:` drift lines. [`evidence/story-5-11/owner-doc-follow-up/frontcomposer.patch`, `memories.patch`, `test_verify_reconciliation.py`]
- [x] [Review][Patch] **Medium · Finish the ChatBot MCP client row.** The patched `mcp-human-delegated-client` row now limits scope to enrolled McpCli operations. It still says "current authenticated human; record source user, presence, actor type, scope and delegation expiry" and "1 hour maximum; terminates on logout, revocation, or lost presence". The McpCli stdio head uses a configured Gateway credential and `--actor`. It has no delegation, presence or session expiry, and forwarded headers wait for the HTTP transport (AD-22). This is the same defect as the CLI row's "OAuth device flow" that pass 2 fixed. `check_owner_conflicts` does not check this row. Describe the head's actual credential, actor and lifetime, and add the stale phrases to `check_owner_conflicts`. [`evidence/story-5-11/owner-doc-follow-up/chatbot.patch`]
- [x] [Review][Patch] **Medium · Test the reverted-correction branch of the drift report.** The `obsolete` term is the only signal that owner main re-added a passage the delivery removed. With it forced to `False`, or with `if not retained:` alone, all 55 reconciliation tests pass. Add a subtest that re-adds a removed passage and keeps every added passage. It asserts the exact `reported:` line. [`evidence/story-5-11/verify_reconciliation.py:775`, `test_verify_reconciliation.py:914`]
- [x] [Review][Patch] **Medium · Test that an unreadable but present path still fails.** When `git show origin/main:<path>` fails while `ls-tree` still lists the path, the check re-raises. Removing the re-raise leaves all tests green, so an unreadable owner main, such as a partial clone, would pass as reported drift. Add the case next to the deleted-path test. [`evidence/story-5-11/verify_reconciliation.py:740-741`, `test_verify_reconciliation.py:947`]
- [x] [Review][Patch] **Low · Keep failure evidence when a discovery probe returns non-object values.** `validate_probe` calls `.get` on nested values. `{"modules":[1,2]}` or `"envelope":[]` raises `AttributeError`, which `run_probe` does not catch, so the staging directory is deleted and a traceback replaces `FAIL:`. Pass 2 fixed the same defect for stdio only. Check the nested shapes, or catch `AttributeError` and `TypeError` in `run_probe`, and extend the non-object test. [`evidence/story-5-11/check_offline_cli.py:46`, `:174`]
- [x] [Review][Patch] **Low · Name the seven status-neutral patches in the completion blockers.** The `integration.json` blockers name only the ChatBot and Works follow-up. `sprint-status.yaml` says completion awaits "the documentation follow-up". The 22 November item "Remove provisional headings from delivered guidance" is still open, and no blocker covers it. Record the other seven owners' patches as that item's blocker and align the sprint comment. [`evidence/story-5-11/integration.json:94`]
- [x] [Review][Patch] **Low · Replace the stale AC3 ledger anchor.** The AC3 blocker cited `deferred-work.md:1265`, which is now a Folders K12 entry. The AC3 entry is `77748cf5a6cb9421` at `:1448`. Applied by `40159c8c` during this review. [`evidence/story-5-11/integration.json:95`]
- [x] [Review][Patch] **Low · Mark the two remaining undated sections historical.** "Parent verification after review fixes" still says acceptance is pending and that no commit or push was created. "Shared-guidance correction and authorized delivery continuation" says McpCli keeps its existing CI until CiCd adoption. Pass 2 dated three such sections and missed these two. Date both 16 November. [`evidence/story-5-11/verification.md:223`, `:241`]
- [x] [Review][Patch] **Low · Retain receipts for the 26 November checks.** `follow-up-tests-20261126.stderr.txt` ends with `Ran 64 tests … FAILED (failures=1)`. After the `build_packet.py` correction only seven tests were rerun, yet `verification.md:345` reports all 65 distinct tests passing across the two runs. The `40159c8c` rerun note retains no log. The newest secret-scan receipt dates from 22 November. No streams back the AD-23, instruction-sync or `git diff --check` claims (`:349`, `:356`). Retain one full-suite log on the final bytes, a fresh scan receipt and the check streams. [`evidence/story-5-11/verification.md:345`]

#### Implementation follow-up on 26 November 2026

All eight open pass-3 fixes are prepared locally. The owner patch replay
preserves PS03 and PS14 and exercises both reconciliation commands. The
ChatBot follow-up describes the configured Gateway credential, session actor
and stdio process lifetime. All 69 focused tests pass in one run. Story
5.11 remains in review while the owner follow-up, 22 audited deferral
resolutions and AC3 are open.
[Verification evidence](evidence/story-5-11/verification.md#pass-3-verification-on-26-november-2026)

#### Rejected

- **Low · The 3.0.0 offline record has no generator, date or per-record hashes (blind, acceptance).** Its `binarySha256` matches `src/Hexalith.McpCli/bin/Release/net11.0/Hexalith.McpCli.dll` (`f13d5838…`, built 25 November). Each claimed probe is in the record, and `modules` lists all three modules. A generator would be new tooling.
- **False · Audited evidence edits are never refused.** Evidence edits are free by design. Pass-2 decision 2 moved the Story 5.18 sentence onto the evidence line.
- **False · The restored F7 status is a builder default that reopens a historical receipt (blind, edge).** The approved entry at `c6a40c10` had no status line, so its audited `sourceStatus` was that fallback. Pass-2 decision 2 (option 2) restores the open gate, because Story 5.18 is in backlog.
- **False · Drift only reports, even when a safety rule is reversed.** That is pass-2 decision 1 (option 4). Delivered bytes stay strict at the recorded commits.
- **False · The delivery authorization's exact-words check is loose.** Rejected in pass 2: the words must equal the immutable publication record.
- **False · GitHub rule bypasses lack authority.** Rejected in pass 2: the recorded "push all changes of all repositories to main" instruction authorized them.
- **Low · The final-plan approval is weaker than the packet receipt.** Rejected in pass 2: it is an immutable owner receipt.
- **False · The release status links stale records.** The plan bytes are identical at `2e591bdd` and the current gitlink `01e64857`. The delivery record link binds historical delivery, not current blockers.
- **False · The verifier never checks the current AI.Tools gitlink.** Rejected on 22 November: a later pointer change is a separate event.
- **False · The release status names no release or cohort.** Rejected in pass 2: it is dated and makes no enrollment claim. Per-release refresh belongs to AC3.
- **Low · The published tool's NuGet origin is unproven (blind, edge).** Rejected in pass 2: the user configuration lists only nuget.org.
- **Low · Help probes check almost nothing.** The CLI test projects own the help contract. Deeper evidence checks would add assertions for no observed regression.
- **False · New blockers are missing from the ledger.** The blockers and their owners are in `integration.json` and the audit. Pass 2 rejected the redaction findings. The Parties fitness failures exist at the owner base and are recorded in `verification.md`.
- **False · The owner follow-up cannot be approved byte for byte.** A patch SHA-256 plus its recorded base revision fixes the result bytes, and the replay applies all nine.
- **Low · A missing PR head silently skips the footprint check.** This is deliberate (`verify_reconciliation.py:813-814`). The immutable record comparison at `:811` still binds the checks.
- **Low · A hung discovery probe loses its partial streams.** The `failed-*` directory is retained, and a hang in the published tool's help is unlikely.
- **Low · The two-second stdio shutdown timeout.** The real binary exits cleanly within it.
- **Low · A server request reusing id 1 or 2.** With empty client capabilities the server sends no requests, and the 19 November review rejected id coercion.
- **Low · Short credential-named environment values over-redact.** This is unlikely on the runner. Raw and retained hashes are recorded separately.
- **Low · The ledger is sanitized with the ambient environment.** The failure mode is a closed refusal, and it needs a credential value in the ledger text.
- **Low · `--root` for another checkout.** Rejected in pass 2.
- **Low · Null record objects print a traceback.** Rejected on 25 November: verification still refuses.
- **Low · `sourceRepository` partial match.** `inputs.json` is hash-bound, so the check runs only on frozen bytes.
- **Low · Patch mode headers.** The approved patches have none, and nothing introduces them.
- **Low · Dead `correct()` targets.** Rejected in pass 2.
- **Low · Deleted already-resolved audited entries.** AC4 concerns unresolved gates, which remain checked.
- **False · Deleting only the census `.csproj` passes SM-3.** That leaves the legacy server unbuildable. The 25 November patch checks the retired project on owner main.
- **Low · Stale local `origin/main` refs.** The verifier documents local refs (19 November rejection).
- **Low · `completedOn` against UTC commit dates.** Completion is not recorded yet. A one-day edge near midnight is unlikely.
- **False · `1c8ef2a87fc429cc` looks closed.** `integration.json` names it as the first refusal.
- **Low · The status-neutral banner in successor packets is untested.** `build_packet.py:380-381` refuses to regenerate an approved packet, so the path is unreachable today.

## Code review pass 4 on 26 November 2026

### Review Findings

**Changes requested.** Four reviewers examined the full deliverables diff
`008d95cc..f7908f80` (5,529 lines, 41 files): the five evidence scripts, the
owner documentation follow-up, the approval, integration and final-plan
records, `verification.md`, `docs/release/migration-status.md`, the 3.0.0
offline capture, the `review-pass-3-20261126/` receipts and the F7 ledger hunk.
At `f7908f80` all 69 reconciliation and offline-probe tests passed (44.5 s).
The default verifier exited 0 and reported EventStore PRD drift.
`--approved-completion` exited 1 with
`FAIL: AC3 generated release notes remain deferred by the owner`. CI for
`b9901766`, `7e9379a9` and `f7908f80` was still running, and every earlier
`main` run had failed. During the review, the non-story commit `39dc7d07`
(CI product gate) landed; it changes no Story 5.11 file. The four layers
returned 51 findings: 1 decision, 10 patches, no deferrals and 31 rejections. On 2026-11-26 the owner resolved the decision, which leaves 11 open patches.

- [x] [Review][Decision] **Medium · Keep ChatBot's service-client registry consistent with its code and active requirements.** The pass-3 fix renamed `mcp-human-delegated-client` to `mcpcli-stdio-client` and redefined `cli-automation-client` as a "Gateway credential configured in McpCli" (`owner-doc-follow-up/chatbot.patch`, PRD `@@ -662,4`). That table lists ChatBot's own credential classes. `cli-automation-client` is a ChatBot Keycloak client (`chatbot/src/Hexalith.ChatBot.AppHost/KeycloakRealms/hexalith-realm.json:616`) and a `ServiceClientClass.CliAutomation` grant with OAuth proof (`tests/Hexalith.ChatBot.Contracts.Tests/ServiceClientGrantContractTests.cs:29-48`). No realm entry or class defines `mcpcli-stdio-client`. On ChatBot `origin/main` `794753de`, outside the five patched files, `epics.md:142` (FR83) still lets a human-delegated MCP client make human decisions. `:3286-3287` binds `mcp-human-delegated-client` to a one-hour presence session, `:4479` closes the M1 list on `cli-automation-client` and `mcp-human-delegated-client`, and PRD NFR67 (`prd.md:1315`) still requires human-delegated MCP tests. The course-correction banner (`epics.md:30`) marks Story 5.7 (backlog) as non-target but covers neither FR83 nor the rename. `check_owner_conflicts` reads neither file. Options: (1, recommended) keep ChatBot's identifiers and add no McpCli class. Record `mcp-human-delegated-client` as withdrawn for M1: the generic stdio head replaces it and refuses human decisions. Keep the stdio head's configured Gateway credential, session actor and process lifetime in the actor-class table (`@@ -629,4`). Add FR83 (`epics.md:142`) and NFR67 hunks so the active requirements agree, and guard their stale phrases. Story acceptance criteria stay under the `epics.md:30` banner. (2) Keep the new identifier and extend the follow-up to every ChatBot `epics.md` reference (FR83, `:3131`, `:3155`, `:3286-3287`, Story 5.7 and `:4479`) and NFR67, with a guard for each. (3) Keep the patch and list the identifier change and the `epics.md`/NFR67 inconsistencies in `owner-doc-follow-up/README.md` for the ChatBot owner to settle at approval. Resolved 2026-11-26: after a deeper option analysis the owner chose a revised option 1. It describes both McpCli heads under the existing `cli-automation-client` class and withdraws `mcp-human-delegated-client`. A McpCli profile holds one Gateway credential shared by both heads (`README.md:351`), and the delivered ChatBot FR83 (`prd.md:1156`) calls McpCli one public agent-capable calling surface. Platform AD-14 (pinned `99a17baa`, `ARCHITECTURE-SPINE.md:130`, `:224`) maps each calling surface to one Keycloak client and keeps that map under Platform ownership. Patch below.
- [ ] [Review][Patch] **Medium · Describe both McpCli heads under `cli-automation-client` and withdraw `mcp-human-delegated-client` (Decision 1, option 1).** In the `chatbot.patch` PRD hunk `@@ -662,4`, make the `cli-automation-client` row cover both McpCli heads. They share the profile's Gateway credential and the session actor (`--actor`). The Gateway authorizes actor, tenant and operation. Approval and approved execution require the confidential UI. Credential expiry follows the issuer, and a stdio session ends when its process exits. Replace the `mcpcli-stdio-client` row with `mcp-human-delegated-client`, marked withdrawn and not issued. Change PRD NFR67 (`prd.md:1315`) and these `epics.md` requirement lines so they test refusal on both McpCli heads: FR83 (`:142`, copying the delivered PRD FR83 wording), NFR67 (`:236`) and the coverage line (`:562`). Leave the Epic 5 acceptance criteria to the `epics.md:30` banner. List `:1609` and `:5686` in `owner-doc-follow-up/README.md`. Add ChatBot `epics.md` to `check_owner_conflicts` with the stale FR83 and NFR67 phrases. Update the `mcpcli-stdio-client` assertion (`test_verify_reconciliation.py:684-687`), refresh the patch SHA-256 and rerun the replay. [`evidence/story-5-11/owner-doc-follow-up/chatbot.patch`]
- [ ] [Review][Patch] **Medium · Test every owner-conflict phrase against the owner text it replaces.** `'delegation expiry for audit'` never occurs in the ChatBot base PRD, whose stale row reads "scope, and delegation expiry |". The refusal test appends each guard's own literal (`test_verify_reconciliation.py:714`), so it cannot detect a phrase that never matched. The Works `DESIGN.md` and mockup guards (`verify_reconciliation.py:495-500`) have no refusal case. Only 5 of 8 PRD phrases and 1 of 4 EXPERIENCE phrases are tested. Correct the dead phrase. Assert that each obsolete phrase occurs in the reverse-applied base document. Add a refusal subtest for every phrase and file. [`evidence/story-5-11/verify_reconciliation.py:479`]
- [ ] [Review][Patch] **Medium · Test the Projects AD-29 acceptance path.** Disabling the branch at `verify_reconciliation.py:765-777` leaves all five drift tests green. The real verifier then adds a false Projects `ARCHITECTURE-SPINE.md` drift line. Every other fixture serves the delivered bytes, and the only AD-29 case is negative. Serve the unchanged Projects `origin/main` spine and expect `(0,VERIFIED,'')`. [`evidence/story-5-11/test_verify_reconciliation.py:976`]
- [ ] [Review][Patch] **Medium · Test the seven untested offline-probe guards.** Removing any of these checks leaves all 11 tests green: exit code (`:37`), discovery stderr (`:41`), error document (`:43`), help output (`:71`), the 1 MiB buffer (`:104`), initialize identity (`:144-145`) and clean shutdown (`:155`). Add a failing case for each that asserts the exact message. [`evidence/story-5-11/check_offline_cli.py:37`]
- [ ] [Review][Patch] **Medium · Require each separate deferral resolution to be committed by the completion date.** `check_retained_deferrals` checks the resolution revision's ancestry but not its date (`verify_reconciliation.py:461-466`). Completion orders every delivery and approval event before `completedOn` (`:661`). A completion recorded before the 22 resolutions would keep a pre-deadline SM-3 assessment. Pass `completed` from `:664` and require `commit_date(root,revision) <= completed`, with a test. [`evidence/story-5-11/verify_reconciliation.py:461`]
- [ ] [Review][Patch] **Low · Finish the Works mockup correction.** The patch changes only the lede, kicker and section label. Beside the new "shared McpCli heads" kicker, `key-mcp-cli.html` still says "adapter command syntax intentionally unspecified" (line 59) and "input: retained in adapter context" (line 68). McpCli's CLI syntax is published. Correct both labels in `works.patch`, refresh its SHA-256 and rerun the replay. [`evidence/story-5-11/owner-doc-follow-up/works.patch`]
- [ ] [Review][Patch] **Low · Describe every follow-up edit in the owner README.** `owner-doc-follow-up/README.md:13-16` says the other edits "remove provisional headings". The FrontComposer and Tenants patches also replace "merged AI.Tools plan 1.2.0" with "the approved AI.Tools migration plan". The Projects patch also replaces the 2.0.1 tool statement (pass-2 decision 1). Owners approve these bytes from that description. Name both changes. [`evidence/story-5-11/owner-doc-follow-up/README.md:13`]
- [ ] [Review][Patch] **Low · Correct the drift-line count.** `verification.md:374` says the fixtures reported ten drift lines. `test_default_and_completion_check_replayed_owner_main_documents` asserts eleven (`test_verify_reconciliation.py:661-673`). [`evidence/story-5-11/verification.md:374`]
- [ ] [Review][Patch] **Low · Retain the remaining 26 November receipts.** `verification.md:390-391` says the published 2.0.1 probe passed, but no `offline-runs/` capture exists. The claim of 22 changed entries with first refusal `1c8ef2a87fc429cc` (`verification.md:320-322`, `integration.json` blockers) has no replay stream. `--approved-completion` stops at AC3 (`verify_reconciliation.py:650`) before `check_retained_deferrals` runs. The pass-3 streams have no command and exit-code manifest, and `memories-docs.stdout.txt` names no test or command. Retain the probe run, a deferral replay and a manifest, and link the 3.0.0 record for the help claim. [`evidence/story-5-11/verification.md:390`]
- [ ] [Review][Patch] **Low · Update the stale audit line of `1c8ef2a87fc429cc`.** `deferred-work.md:189` still says "exact-byte owner acceptance and upstream integration remain pending. This row is not closed." That sits beside `status: done 2026-11-24`, set by `0545c3fc`. Record the 22 November approval and integration, and state that closure awaits a separate owner resolution. Keep the line count. [`_bmad-output/implementation-artifacts/deferred-work.md:189`]
- [ ] [Review][Patch] **Low · Use the exact audited owners in the resolution table.** `check_retained_deferrals` requires `resolution.owner` to equal the audited owner (`verify_reconciliation.py:457`). The table under "Audited owner" regroups owners. For example, it files `a03161fe049a33d2` ("McpCli CI and live-topology maintenance owners.") under "McpCli product/architecture and maintenance roles". Resolutions written from the table would be refused. [`evidence/story-5-11/verification.md:427`]

#### Rejected

- **False · The follow-up has no approval path, and permanent drift lines hide regressions (blind).** Pass-2 decision 1 (option 4) chose reported drift. Pass 3 rejected the approval point: a patch SHA-256 plus its base revision fixes the bytes.
- **False · The owner documentation tests that read the patched ChatBot and FrontComposer files were not rerun (blind).** Those patches change only banner lines in those files. The ChatBot ADR tests assert ADR text, and none of them references the banner.
- **Low · The 3.0.0 offline record predates the EventStore 5.5.2 move (blind).** It is dated and bound to its binary. The cohort move changes no CLI option or enrolled module.
- **False · `verification.md` and `integration.json` are not current at the top (blind).** The 22 November assessment is dated, as passes 2 and 3 required. `assessedOn` dates the delivered-state assessment, and that state is unchanged.
- **Low · Nothing checks the release status content (blind).** The file is dated and static and is reviewed each pass. A content suite would be new tooling, and the AC3 path still reads the file.
- **False · Completion never enforces the seven status-neutral patches listed as a blocker (acceptance).** Pass-2 decision 1 (option 4) limits the machine gate to ChatBot and Works. The blocker tracks the open 22 November item, which keeps the story open.
- **Low · Verifier tracebacks on null or non-object values (edge).** Rejected on 25 November and in passes 2 and 3: verification still refuses.
- **Low · `sourceRepository` substring match (edge).** Rejected in passes 2 and 3: `inputs.json` is hash-bound.
- **Low · `--root` for another checkout (edge).** Rejected in passes 2 and 3.
- **Low · The AI.Tools gitlink may name an unmerged commit (edge).** `verify_reconciliation.py:909` byte-compares the plan and instructions at the gitlink with the delivered revision. A later pointer change is a separate event (22 November rejection).
- **False · Extra plan index rows pass the index check (edge).** The plan bytes are owner-approved and hash-bound through `planSha256` and the final-plan approval.
- **Low · Deleted or reopened resolved audited entries (edge).** Rejected in pass 3: AC4 concerns unresolved gates.
- **Low · `<!--` inside code hides later text (edge).** None of the five checked owner documents has a comment inside code, and the fix needs a Markdown parser.
- **Low · SM-3 lacks owner-specific gates for PS07, PS11 and PS13 (edge).** No retirement is claimed. Each receipt binds the label's inventory gate and an owning-maintainer "approve". The spec only indexes K12 and paging.
- **False · A status-neutral rebased delivery is refused (edge).** The rebase check replays the recorded Projects delivery, which used historical wording.
- **False · A delivered path absent from the parent raises (edge).** No delivered patch creates a file.
- **Low · `verifiedOn` may precede its commit (edge).** The recorded dates follow their commits, and the fix adds a guard.
- **False · A CRLF final plan is refused (edge).** The approved plan bytes are LF and hash-bound.
- **Low · Git configuration changes the applied bytes (edge).** This is unlikely, and pass 2 isolated `git apply`.
- **Low · The Parties verdict may name an unrelated candidate head (edge).** The verdict is hash-bound through `checked`, and the fix adds a guard.
- **Low · Dead `correct()` targets (edge).** Rejected in passes 2 and 3.
- **Low · Malformed patches for unusual line endings (edge).** The generator is frozen, and the delivered bytes are verified.
- **Low · Banner insertion ignores front matter and fences (edge).** Rejected in pass 2.
- **Low · `build_packet.py` tracebacks (edge).** Rejected in pass 2.
- **Low · The ledger block parser can absorb a following heading (edge).** A spurious refusal fails closed, and the replay found the 42 unchanged entries equal.
- **Low · A timed-out probe loses its partial streams (edge).** Rejected in passes 2 and 3.
- **Low · An empty `packages` list passes (edge).** Rejected on 19 November and in pass 2.
- **Low · Late stdout after `tools/list` goes unrecorded (edge).** Draining adds a branch. Pass 3 rejected the shutdown-timeout variant.
- **Low · A NuGet.Config feed could supply 2.0.1 (edge).** Rejected in passes 2 and 3.
- **False · Removing "historical acceptance record" from F7 invites sweeps to reopen it (edge).** Pass-2 decision 2 (option 2) restored the open gate deliberately.
- **Low · The 3.0.0 stdio record's stream hashes have no retained files (verification-gap).** Pass 3 rejected the record's missing generator and per-record hashes as low.
