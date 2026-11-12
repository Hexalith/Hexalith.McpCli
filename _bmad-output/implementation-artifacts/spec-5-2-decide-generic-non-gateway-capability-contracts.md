---
title: '5.2 Decide generic non-gateway capability contracts'
type: 'chore'
created: '2026-11-12'
status: 'done'
route: 'dispatch'
review_loop_iteration: 1
baseline_commit: 'f4bb819925d4fac5fa5afd262341692296a52042'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-5-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** About 525 approved inventory rows across eight inventories (EventStore Admin 1.0.1, technical-tools 1.0.2, and the Folders, Projects, FrontComposer, ChatBot, Memories and Parties inventories) carry capabilities that v1 cannot migrate as decorated Gateway Commands/Queries. No decision assigns them a generic path, a withdrawal or a named retention. Stories 5.7–5.10 and Epic 6 cannot re-disposition any row until one exists.

**Approach:** Adopt McpCli **AD-23**. It partitions every inventory row into exactly one capability class and gives each class exactly one outcome: decorated Gateway contract, named generic authenticated transport, exempt local tooling, confidential UI only, withdrawal, or continued deferral with a named gap. Use only outcomes inside v1, so that no Platform AD or PRD change is needed. Bind it with a machine-checkable class map, a stdlib verifier and exact-byte owner approval. Publish the exempt-tooling amendment upstream in Hexalith.AI.Tools.

## Boundaries & Constraints

**Always:**
- Keep the existing limits:
  - Platform AD-11/AD-14: McpCli is one public `agent` surface; UI-only and confirmation-required operations are denied, and `confirm: true` proves nothing.
  - PRD §8.2/§8.3: no MCP resources, prompts, event-stream reads, retries or plug-ins, and McpCli never calls a Module REST or Dapr API.
  - AD-20: paging stays Envelope-only.
  - MR4: task and actor context travel only as Payload properties, through `actorProperty`, or in allowed extensions.
- One class per row. An operation row takes the class of its primary capability, and a variant row takes the class of the variant it records. Any UI-only, confirmation-required or destructive row takes its restricted class, whose outcome is confidential UI, exempt (owner-held) local tooling, or withdrawal.
- Inline content up to 262144 bytes is an ordinary decorated Command Payload and needs no new class.
- Each admitted class states its versioned declaration, discovery, execution, error documents, authorization class, audit and conformance evidence, with no module-specific runtime branch.
- Each deferral names its gap and the owning role.
- Each restricted class and each Folders class names the positive and negative evidence a later parity proof collects.
- Record how each outcome maps to the `replace`/`withdraw`/`defer` dispositions that Stories 5.7–5.10 apply. `replace` still requires the decorated type to exist at the pin, and each Admin `replace` lists the G4 fixes as preconditions.
- Bind the decision, the class map and every input inventory by SHA-256. AD-23 is `ADOPTED` only after the owner approves the exact bytes. The approval names the roles it covers under the single-maintainer model.

**Never:**
- Change production `src/`, `tests/`, dependencies, CI, `references/`, the census baseline or any inventory file.
- Re-disposition a row on a draft decision.
- Admit a capability beyond v1 decorated Commands/Queries.
- Claim parity from name matching.
- Grant execution, enrollment or retirement authority.
- Push upstream without the owner's explicit approval.

## Owner Decisions (2026-11-12)

1. **Remote EventStore Admin rows** (the four Story 5.1 classes: infrastructure administration, operator diagnostics, stream/state reads, tenant reads; 46 rows): **confidential UI only**. This follows Platform AD-11's interim rule. The Admin heads retire only with UI coverage evidence.
2. **Lifecycle/status observation:** **withdraw**. Agents observe effects through the Gateway's accepted status and the module's decorated Queries. The synthetic `timed_out`/`needs_review` states are an accepted loss.
3. **Documentation resources:** **withdraw**. Documentation ships with the packages, README and AI.Tools.
4. **Streams, staged files, imports/exports and event streams** (including Folders V04/V05): **continued deferral**. The gap is a generic out-of-band staging/stream transport that needs a Platform AD and a PRD change. The owning role is the McpCli product/architecture owner. The Folders rows this class governs stay `defer` and keep EXT-MCPCLI-FOLDERS-RETIREMENT-GATE closed until the class is decided or Folders withdraws them.
5. **FrontComposer compiler CLI (FC01/FC02, PS03):** **exempt local tooling**. The AI.Tools rule and plan 1.2.0 amendment is committed upstream in this story and pushed only after explicit owner approval. Until it merges, the surface stays frozen in the census.
6. **Memories `MigrateEmbeddingVectors` (PS14):** **exempt local tooling**, owner-held, named in the same amendment. It is never placed on the agent surface. Story 5.10 still inventories its modes.
7. **Module erasure and key rotation:** **confidential UI only**.
8. **Spec size:** the owner kept the full spec (about 3,800 tokens).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Complete map | Map covers every row ID of the eight hash-bound inventories exactly once | Verifier exits 0 and prints per-inventory counts | N/A |
| Missing or duplicate row | A row ID absent from the map, or present twice | Nonzero exit naming the inventory and the ID | Damaged-input test |
| Unknown row or stale hash | A mapped ID not in the inventory, or an inventory hash mismatch | Nonzero exit naming it | Damaged-input test |
| Bad outcome | A class with zero, two, or an unlisted outcome | Nonzero exit | Damaged-input test |
| Restricted leak | A destructive, confirmation-required or UI-only row mapped to an admitted class | Nonzero exit naming the row | Damaged-input test |
| Deferral without gap | A deferred class with no gap or no owner role | Nonzero exit | Damaged-input test |

</frozen-after-approval>

## Code Map

- **Inputs (read, never edit):**
  - `_bmad-output/implementation-artifacts/eventstore-admin-migration-inventory-v1.md` (1.0.1, `7e1beb2f…`)
  - `technical-tools-migration-inventory-v1.md` (1.0.2, `8cca31f2…`)
  - `folders-` (1.0.0), `projects-`, `frontcomposer-`, `chatbot-` and `memories-` (1.0.0; the last four are session-scope approval only), and `parties-migration-inventory-v1.md` (1.2.0, owner-approved on 2026-11-09; `evidence/story-5-3/approval/amendment-1.2.0.json` binds its exact hash).
  - The row tables are the Markdown tables whose first cell is an ID such as `AC01`, `G3` or `V05`. ChatBot and Memories head their gap tables `Gate` and `Gap`, and Parties heads its C table `ID / legacy rows`. Folders C/Q candidate rows are not legacy operations.
- **`evidence/story-5-1/verification.md:1341-1352`:** the approved Admin class partition (eight classes). Reuse it verbatim as the Admin classes; the 5.1 gate checks it at `:1066-1076`. Also `:1353-1450`: the technical classes and the behavior inputs (FV01 limits, FH02 admission, AV04 disclosure).
- **`_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/ARCHITECTURE-SPINE.md`:**
  - Entry format `### AD-N — Title [ADOPTED date]` with Binds/Prevents/Rule/Provenance/Evidence (AD-22 at `:191-199`).
  - Frontmatter `updated:`/`sources` at `:11-14`.
  - Design Paradigm at `:34`.
- **Platform rules:** `references/Hexalith.Platform/_bmad-output/planning-artifacts/architecture/architecture-platform-2026-09-27/ARCHITECTURE-SPINE.md:185` (AD-11, new surfaces) and `:206-216` (AD-14). The pin is `38402bc7`.
- **AI.Tools:**
  - The local clone `/home/administrator/projects/hexalith/aitools` is clean on `main` at `8a3885d`, the same commit as the gitlink.
  - Exemption sentence: `hexalith-llm-instructions.md:78-80`.
  - Plan: `hexalith-mcpcli-migration-instructions.md:2-4` (`plan_version 1.1.0`) and `:16-18`; versioning rule at `:47-48`.
  - Upstream work follows Story 5.5's practice: a scratchpad worktree from `origin/main`, a commitlint-validated `docs` commit on a branch, and a push only on approval.
- **Folders positions** (`references/Hexalith.Folders` at `6a8cf4f9`, `_bmad-output/planning-artifacts/sprint-change-proposal-2026-11-10.md`):
  - `:177` and `:213`: staging per 5.2, otherwise `defer`.
  - `:196`: G6 authorized module-side.
  - `:294-296`: a single freshness value per Query.
- **Do not touch:**
  - `tools/proprietary-surfaces/v1/baseline.json`, which binds technical 1.0.2.
  - `tests/Hexalith.McpCli.Cli.Tests/PartiesRetirementSafetyTests.cs:156`, which parses the Admin AC/AM names.
  - Story 5.1's `approval.json` and verification text.

## Tasks & Acceptance

**Execution:**
- [x] `_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/AD-23-non-gateway-capability-classes.md` -- write the decision. It covers:
  - the class table and its outcomes;
  - the one-class precedence rule;
  - each admitted class's declaration, discovery, execution, errors, authorization, audit and conformance;
  - a Folders section giving, for V04/V05, R01/R02, G6 and V01/V02, the governed rows plus their positive and negative evidence;
  - the treatment and negative evidence for restricted operations;
  - each deferral's gap and owner role;
  - the outcome-to-disposition rule, including the G4 preconditions;
  - an explicit "no Platform AD or PRD change required" statement.

  Its status stays `proposed` until approved -- this is the single decision Stories 5.7–5.10 consume.
- [x] `.../AD-23-capability-class-map.json` -- for each class: `id`, `outcome` and `gap`/`ownerRole`; for each inventory: path, version, SHA-256 and `rows` mapped to class IDs; plus explicit `records` for non-operation rows (AU, AX, FK, PE, PN, candidates C/Q, G rows, and PS rows governed by companion inventories) -- this keeps the map complete and mechanically checkable.
- [x] `_bmad-output/implementation-artifacts/evidence/story-5-2/verify_class_map.py` and `test_verify_class_map.py` -- a stdlib verifier that has no module names or counts in code, plus one damaged-input test for each matrix row -- the verifier proves the "exactly one class" and restricted-row rules, and each test proves its guard.
- [x] `.../ARCHITECTURE-SPINE.md` -- add the AD-23 entry with Binds FR-21/FR-22, MR1–MR3 and MR9, and update `updated`/`sources` -- this adopts the decision as a McpCli AD.
- [x] Upstream AI.Tools worktree -- amend the exemption sentence and the plan to 1.2.0 for each exempted surface, then validate with commitlint -- AC6 requires the amendment; it is pushed only after the owner approves.
- [x] `evidence/story-5-2/verification.md` and `approval.json` -- record the verifier output, the hashes, the owner's words, the roles covered and the limits -- adoption evidence.
- [x] `sprint-status.yaml` and this spec -- update the workflow state.

**Acceptance Criteria:**
- Given the approved AD-23, when it is read, then every class has exactly one listed outcome, and every row of the eight bound inventories maps to exactly one class or to an explicit non-operation record.
- Given the restricted rows (AC13, AC20, AC21, AC25, AC28, AM01, AM03, AM06, AM12–AM15, FC02 and the PS14 live/rollback/abort modes), when their treatment is checked, then each is assigned to confidential UI, exempt local tooling or withdrawal, and its negative evidence is named.
- Given the whole change, when it is diffed against the baseline, then `src/`, `tests/`, `tools/`, `references/`, CI and all inventory bytes are unchanged.
- Given an exempt-tooling outcome, when 5.2 completes, then the AI.Tools amendment is committed upstream, or recorded as pending with the surface still frozen in the census.

## Design Notes

**Classes.** A tag in the form D# cites the Owner Decision that set the outcome. Implementation may split or rename classes when a row's primary capability requires it, but it may not change an outcome.

**Decorated Gateway contract (admitted; v1 already defines all seven facets):**
- K01: ordinary module operations awaiting module-side decoration or handlers, including the FH02/H02 manifest families per consumer.
- K02: module-state resource reads (Folders R01/R02, Projects R-data, FH03) become module Queries; the URI and subscription are not preserved.
- K03: freshness, paging and filter inputs (Folders V01/V02). Freshness is fixed per Query or declared as a Payload property, filters are Payload properties, and paging is Envelope-only.
- K04: context, idempotency-key and identifier format. Values are canonical uppercase ULIDs, and the module accepts them (Folders G3).
- K05: provider egress and pre-submit effects, authorized module-side (Folders G6, ChatBot V07/V08).
- K06: module diagnostics. These are exposed only if the owner decorates them.

**Withdrawal:**
- K07: documentation delivery (D3).
- K08: lifecycle/status (D2).
- K15: legacy session context, stubs, local profile/config, completion, wizards and CLI conventions. This includes Admin AM16–AM18, AC22–AC24 and AC25–AC31, Memories S01–S04, L02 and L06, and Projects L12/L13.

**Continued deferral:**
- K09: streams, staging and files (D4).
- K10: forwarded per-user identity and HTTP caller authority (MR9; owner: McpCli product owner).

**Confidential UI only:**
- A1–A4: the four remote Admin classes from Story 5.1 (D1).
- K12: module confirmation-required or destructive operations, including erasure and key rotation (D7).

**Exempt local tooling:**
- K13: the compiler CLI (D5).
- K14: PS14 (D6).

**Outcome-to-disposition rule.** Decorated contract → `replace` only when the decorated type exists at the pin, otherwise `defer` naming the module gap. Confidential UI → `withdraw`; the head retires only with UI coverage evidence. Exempt → `withdraw` from migration scope; the surface is retained and not counted as retired. Withdrawal → `withdraw` with the accepted loss. Deferral → `defer` with the gap.

### Review-derived verifier and approval design (iteration 1)

- The decision must independently bind its expected input inventory set, the sole outcome for every class, required restricted identities, eligible non-operation record identities, and required approval roles. Put a small machine-readable policy block in the decision itself, or derive these facts from its normative tables. The map hashes this decision; map-owned flags alone cannot establish these requirements. No module names or counts belong in verifier code.
- Derive all actual row identities from source. Every non-record identity must retain exactly one class; every record must be explicitly eligible under the independently bound policy. Required restrictions must survive deletion of map-owned restriction evidence. Include PS14 and Parties C03/C04/C05's mixed create/update/deactivation variants. Required classes/outcomes and expected inventories must match the decision exactly. Normalize repository paths before duplicate detection.
- Validate approver and instruction as nonblank strings and rolesCovered as an array of nonblank strings covering every required role. The required role list is in the bound decision, not a mutable receipt field. Retain exact artifact-hash verification; a documentary verifier does not authenticate a human signature.
- Keep approved decision/map bytes immutable through adoption. Their effective status must come from the separate approval receipt, with clear conditional proposed/adopted wording and no post-approval changes to the bound artifacts. The unbound spine entry and workflow state may record adoption only after approval. The final approval request must identify these exact candidate bytes; no automatic status/hash refresh may replace them.
- Add executed damaged-input regressions for a whole missing inventory, outcome/decision disagreement, removed PS14 restriction plus admission, operation-to-record laundering, role omissions/invalid types/whitespace, path aliases, and the final receipt-driven adoption path. Test the actual script process: failure exits 1, stdout is empty, stderr starts FAIL; success exits 0. Existing matrix scenarios still apply.
- Parties 1.2.0 is approved under the existing exact-byte Story 5.3 receipt. Preserve that approval and its limited scope accurately; do not claim it is pending. The independent destructive-label/enrollment conflict remains disclosed without runtime or inventory edits.

**KEEP during re-derivation:** Reuse the reviewed decision's Admin eight-class names, all seven admission facets, detailed Folders boundaries/evidence, named deferrals, G4 preconditions, source inventory hashes, and the retained AI.Tools local commit. Preserve every unchanged source/inventory/reference/CI byte, the frozen spec block, and the no-push boundary. The first candidate is archived under `/tmp/mcpcli-story-5-2-iteration-1/` for positive preservation; it is not an approved decision. Re-derive the map/verifier/tests/evidence from this corrected design rather than rerunning unrelated discovery. Reuse the locally committed upstream amendment `10b709b86f9c9148e5a18177e8d11fad79ae2c0b` and its successful commitlint evidence; do not recommit or push it.

## Verification

**Commands:**
- `python3 -I _bmad-output/implementation-artifacts/evidence/story-5-2/verify_class_map.py` -- expected: exit 0, with per-inventory counts.
- `python3 -I -m unittest discover -v -s _bmad-output/implementation-artifacts/evidence/story-5-2 -p 'test_*.py'` -- expected: every damaged input is rejected.
- `git diff --stat f4bb819925d4fac5fa5afd262341692296a52042 -- src tests tools references .github _bmad-output/implementation-artifacts/*-migration-inventory-v1.md` -- expected: empty.
- `git diff --check` -- expected: clean.

## Implementation Notes

- 2026-11-12: The user approved the specification with "approve and stop". The intent and Owner Decisions D1–D8 are frozen. Implementation has not started. This approves the spec only: AD-23 still needs exact-byte owner approval before adoption, and the AI.Tools push needs its own explicit approval.
- 2026-11-12 first implementation (archived after review iteration 1): Prepared the proposed [AD-23 decision](../planning-artifacts/architecture/architecture-mcpcli-2026-09-22/AD-23-non-gateway-capability-classes.md), complete 625-row class map (472 classified rows and 153 explicit records), stdlib verifier and 17 passing tests. The [verification packet](evidence/story-5-2/verification.md) and [pending approval receipt](evidence/story-5-2/approval.json) bind the candidate and all eight input inventory hashes. The spine entry is proposed; adoption and its task remain pending exact-byte owner approval with covered roles. The AI.Tools amendment is committed locally at `10b709b86f9c9148e5a18177e8d11fad79ae2c0b`, with successful pinned commitlint evidence; push/merge approval remains pending and exempt surfaces remain frozen. No forbidden path or inventory bytes changed. The evidence records the downstream Parties destructive-label/enrollment conflict and Folders C10's mixed destructive variant; neither is silently resolved by this story. Story status remains in progress for workflow review and owner approval.
- 2026-11-12 implementation iteration 2: Re-derived the complete map and verifier from the corrected review design. The decision independently binds inventories, sole class outcomes, inherited restrictions, eligible records/governing policy and required approval roles. Parties C03/C04/C05 now inherit the restricted mixed-variant treatment; Parties 1.2.0's existing approval and limited scope are preserved accurately. All 37 subprocess-based tests pass, including each reproduced bypass and adoption by receipt alone with unchanged decision/map bytes. The [verification packet](evidence/story-5-2/verification.md) identifies the exact candidate hashes. The spine entry is prepared as proposed; final adoption and its evidence tasks remain pending exact-byte owner approval, with no post-approval artifact rewrite. The retained AI.Tools commit and commitlint evidence were reused without a recommit or push. No forbidden path, inventory byte or frozen intent changed.

## Spec Change Log

- 2026-11-12, review iteration 1: Source authority and verification/adoption design corrected after independent review reproduced omitted-inventory, removable-restriction, record-laundering, conflicting-outcome and invalid-role inputs passing. Parties 1.2.0 approval is confirmed by its existing hash-bound receipt. Added independently decision-bound verifier requirements and immutable, receipt-controlled adoption so final approved bytes do not change. KEEP instructions above preserve the useful decision content, complete mapping work, focused checks and upstream commit; forbidden paths and frozen intent remain unchanged.

## Review Triage Log

| Finding | Verdict | Route | Verified evidence |
| --- | --- | --- | --- |
| Blind B1: Parties 1.2.0 approval | medium | bad_spec | Existing Story 5.3 amendment receipt is approved on 2026-11-09 and binds exactly the map's inventory SHA-256; stale non-frozen Code Map propagated the false pending claim. |
| Blind B2: Parties C03/C04/C05 | medium | patch (superseded by loopback) | Source variants explicitly govern T04/T05/T07 creation, removals and deactivation; current decision's mixed-variant precedence requires restricted classification. Preserve correction in re-derivation. |
| Blind B3: whole missing inventory | medium | bad_spec | Removing the technical inventory from the actual proposed map passes; expected inputs must be independently bound by the decision. |
| Blind B4: removable PS14 restriction | medium | bad_spec | Removing PS14 evidence and selecting K01 passes against unchanged source; required restrictions cannot be map-owned policy alone. |
| Blind B5: operation record laundering | medium | bad_spec | Moving actual Parties T01 into an arbitrary unclassified record passes; record eligibility needs independent authority. |
| Blind B6: outcome disagreement | medium | bad_spec | K09 changed to withdrawal passes against the unchanged deferred decision; sole outcomes need decision binding. |
| Blind B7: approval roles and whitespace | medium | bad_spec | An adopted map with whitespace-only owner/instruction and unrelated roles passes with matching hashes; coverage and types need decision-bound roles. |
| Blind B8: governing cycles | low | rejected | A self-reference passes, but no current record is cyclic; adding a general graph traversal for hypothetical bookkeeping cycles exceeds a direct correction for a negligible case. Record eligibility and independent governing policy are being enforced separately. |
| Blind B9: aliased inventory paths | medium | patch (superseded by loopback) | Adding the same technical file through ./ passes and double-counts its identities; normalize resolved paths before duplicate detection. |
| Blind B10: adoption mutates approved bytes | medium | bad_spec | Presented decision/map include proposed status, while the procedure asks for later adopted edits that change both hashes; move effective status to the separate approval receipt. |
| Edge E1: removable inherited restrictions | medium | bad_spec | Same reproduced PS14 evidence-removal/admission failure as B4; independently required restrictions will govern the map. |
| Edge E2: capability row as bookkeeping | medium | bad_spec | Same reproduced T01 classification loss as B5; explicit non-operation eligibility will govern records. |
| Edge E3: incomplete covered roles | medium | bad_spec | Same reproduced unrelated-role adoption as B7; bound roles, nonblank strings and array types will be checked. |
| Edge E4: null JSON traceback | low | rejected | Null document produces AttributeError and process exit 1, so damaged input is still rejected; no current input is null. Additional schema guards for this cosmetic diagnostic are unnecessary beyond the required semantic checks. |
| Verification V1: process exit untested | medium | patch (superseded by loopback) | Pre-verified: replacing sys.exit(main()) with main() leaves all 17 tests green while the standalone command exits 0 after failure. Add a real subprocess test for exit and both channels. |


### Review pass 2 triage

| Finding | Verdict | Route | Verified evidence |
| --- | --- | --- | --- |
| Blind 2-B1: named row assignments can drift | medium | patch | Parent reproduced AC13→K14 and Folders V04→K01 passing after fixture receipt rebinding. Extend the existing decision-owned policy comparison to operation row class assignments; no new runtime/public surface is needed. |
| Blind 2-B2: ChatBot V10 | medium | patch | V10 records operation/task handle discrepancy and authoritative tenant/status/audit obligations, rather than only the withdrawn synthetic engine. Its primary handle/context handoff belongs to K04; preserve the module Query evidence explicitly. |
| Blind 2-B3: Parties C08 | false | rejected | Source C08 explicitly rejects raw forwarding weaknesses and adopts v1 configured stdio operator-session/Gateway credentials. K04 expresses that approved replacement, not an admission of the legacy forwarded identity. Future HTTP forwarding remains K10. |
| Blind 2-B4: authorized query content | medium | patch | The shared audit cell's blanket content prohibition conflicts with authorized Memories corpus evidence and ChatBot conversation results. Narrow it to unauthorized content in result documents and content-free diagnostics/evidence. |
| Blind 2-B5: Parties reconciliation tracking | medium | defer | Existing destructive labels and enrolled Commands require a separate Parties/McpCli owner resolution; no equivalent ledger entry was found. Track an explicit inventory/exposure reconciliation gate before restricted compliance or retirement claims. |
| Blind 2-B6: pending role policy | medium | patch | Parent reproduced a pending decision lacking requiredApprovalRoles returning 0. Validate the existing required-role policy for pending candidates as well as adoption. |
| Blind 2-B7: malformed object traceback | low | rejected | carried: same null/non-object diagnostic claim as iteration-1 E4; the unchanged get/exception path still exits nonzero. This cosmetic unsupported-input case does not justify extra schema machinery. |
| Blind 2-B8: Effect/Confirmation test branches | medium | patch | Reviewer demonstrated the branch-removal gap; parent confirmed every synthetic restriction is in a Security class column. Add process cases with restrictions exclusively in each source column. |
| Blind 2-B9: missing approval date | low | rejected | Hashes, owner instruction and complete roles are the specified adoption validity requirements; an approval date is retained provenance, not an additional authority grant. The real pending receipt stays null until owner approval is recorded. Additional date-format policy is unnecessary for this manual metadata case. |
| Blind 2-B10: approvalLimit can drift | medium | patch | Map approvalLimit is unbound display metadata and can falsely claim owning-maintainer authority. Compare it with the existing decision-owned inventory policy and cover a damaged session-scope claim. |
| Blind 2-B11: retained-section hashes | low | patch | Preservation receipt lists unchanged sections but no section hashes. Add before/after hashes and the extraction/comparison command; do not imply prior owner approval of the archived first candidate. |
| Edge 2-E1: malformed null JSON | low | rejected | carried: iteration-1 E4 and pass-2 B7; input already fails nonzero. No additional shape guard is required. |
| Edge 2-E2: concurrent inventory edits | low | rejected | Inputs are read-only, hash-bound snapshots in this workflow; no concurrent inventory writer runs. Supporting adversarial mutation between hashing and parsing would add snapshot machinery for an unlikely documentary-only case, with no runtime authority granted. |
| Verification 2-V1: record binding regressions | medium | patch | Pre-verified mutations removing record_policy classId or governedBy leave 37 tests green. Add actual-packet C01→K13 and PS09 M01→existing L01 regressions, requiring the governing-policy mismatch and both channels. |


### Review completion (2026-11-12)

All surviving patches from both independent three-layer review passes are applied. The parent independently reran the standalone verifier and all **45 process tests** against the final candidate: all passed. The forbidden-path/inventory diff and whitespace checks pass. The approval packet contains the final immutable decision/map hashes; effective AD-23 adoption and the two adoption task boxes remain pending exact-byte owner approval covering every decision-bound role. No upstream push occurred. The Parties reconciliation is tracked at `deferred-work.md:1024` with owners, acceptance evidence and the retirement/compliance gate. Prior iteration test counts above are historical.


### Owner adoption (2026-11-12)

The user replied **"approve"** directly to the final exact-candidate approval request and confirmation of all listed owner roles. The [approval receipt](evidence/story-5-2/approval.json) records the verbatim response and all twelve decision-bound roles, retaining the existing approver identity with its source reference. It binds the unchanged decision (`f47b64c7772ed9d9763e4438a176cb7bea01e8e0793f7217c6bd1f3274545560`), class map (`21cb3643ef3e652031bf13f02e237b2cfadb2be24bcbf2d02e879a584ac8a4c3`) and eight inventory hashes. The standalone verifier reports effective status `adopted`. Both adoption tasks are complete; the approved decision/map bytes and frozen intent remain unchanged. Earlier pending-adoption notes above are historical.

AI.Tools push and merge remain pending separate approval; the locally committed amendment satisfies the specification's allowed pending-amendment completion path, with exempt surfaces still frozen. The separately tracked Parties reconciliation, Folders staging gate and later inventory/exposure/retirement evidence remain open. The build workflow marks this spec done and the sprint story review.


### Upstream push delivery (2026-11-12)

After the adoption summary identified the AI.Tools push as the remaining separate approval, the user replied **"approve"**. The exact approved amendment commit `10b709b86f9c9148e5a18177e8d11fad79ae2c0b` was pushed to `docs/mcpcli-local-tooling-exemptions`; a fresh remote branch read-back matches it. The [delivery record](evidence/story-5-2/upstream-delivery.json) retains the raw response, exact push command/result and remote revision. Earlier pending-push notes are historical. Merge remains pending and exempt surfaces stay frozen. No reference gitlink or approved decision/map/inventory bytes changed, and this approval does not push McpCli's local completion commits.


### Main integration (2026-11-12)

The user requested **"merge all changes to main"**. AI.Tools main was clean and fast-forwarded to the exact approved amendment `10b709b86f9c9148e5a18177e8d11fad79ae2c0b`; its remote main read-back confirms that revision. The [integration record](evidence/story-5-2/main-integration.json) retains the request and successful commands. The amendment merge gate is satisfied; earlier pending-merge notes above are historical. All McpCli story and delivery commits are published together to main under the same request. No approved decision/map/input, census baseline, inventory or reference gitlink bytes changed; remaining Parties, Folders and later release/retirement gates stay open.
