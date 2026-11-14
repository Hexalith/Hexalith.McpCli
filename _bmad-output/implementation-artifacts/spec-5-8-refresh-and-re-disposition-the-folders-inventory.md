---
title: '5.8 Refresh and re-disposition the Folders inventory'
type: 'chore'
created: '2026-11-13'
status: 'in-progress'
baseline_commit: 'a92a2969db6903b8c6cca7e437446167e135ec9d'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-5-context.md'
story_key: '5-8-refresh-and-re-disposition-the-folders-inventory'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The approved Folders inventory 1.0.0 is pinned to `e2252f29`, which is not an ancestor of the root gitlink. Every row in it is `defer / exclude`, although Folders Story 5.12 has since decorated 41 eligible operations and recorded accepted behavior losses.

**Approach:** Produce an additive Folders 1.1.0 successor, re-pinned to gitlink `7eab70e9332c0573b50dce5b219e425b6a2d363c`, that re-dispositions all 161 entries under adopted AD-23 and the Folders 5.12 record. Gate it with a story verifier, then obtain exact-byte owner approval and integrate the PS10/PS11 Folders README label citations.

## Boundaries & Constraints

**Always:**
- Account for every 1.0.0 entry exactly once (M49, R2, L42, C13, Q35, V10, N4, G6). Give each new-pin anchors and an explicit drift status: unchanged, or the change.
- `replace` requires a decorated `[HexalithCommand]`/`[HexalithQuery]` type at the pin, its owner eligibility, its wire name and its route. `include` appears only with `replace`.
- `withdraw` names the owner rationale and the replacement experience. `defer` names a gap and its owner.
- G1–G6 name their Folders story and its status at the pin.
- Record the identifier, key and `taskId` treatment and every accepted loss, with the rows it affects.
- Approval names the Folders roles it covers and supersedes A1.

**Never:**
- Rewrite 1.0.0, AD-23, the technical 1.0.3 inventory, the receipts or `references/`.
- Enroll, publish, execute or claim parity or retirement.
- Change production, dependencies, census or gitlinks, or the AI.Tools plan (Story 5.11 indexes the successor).
- Convert legacy formats silently.
- Commit or push without explicit authorization.

**Decisions (2026-11-13):**
- **K12 conflict: "Defer + reconcile later".** C01 and C10, and rows M01, M02, M04, M13, L10, L24, L25 and L26, stay `defer` under a named "AD-23 K12 reconciliation" gap. The gap is owned by the Folders owner and the McpCli product/architecture/security owners. Record the adopted outcome beside it, and add a ledger entry following the Parties precedent (`deferred-work.md:1024`). Epic 6 cannot catalog Contracts 1.4.0 until the gap is resolved.
- **V09 remainder: "Accept them".** The owner accepts the loss of legacy REST setup, stderr errors and internal/unmapped exit 1, together with the 5.12 losses. The replacements are McpCli profiles, stdout JSON errors and exit 2. V09 becomes `withdraw` (K15).
- **Spec size: "Keep full spec".**

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Complete candidate | 1.1.0 + pin + AD-23 map + 5.12 record | Verifier passes; receipt stays pending | N/A |
| Invented or undecorated replacement | `replace` without a decorated type at the pin, or with a mismatched wire/route | Reject, naming `module:id` | nonzero exit, exact stderr |
| Damaged row, anchor, drift, class, gap or chain | missing/duplicate ID, unresolvable anchor, `include` without `replace` | Reject with an actionable diagnostic | nonzero exit |
| Completion without approval or label | pending receipt or unintegrated PS10/PS11 | Completion mode fails | nonzero exit |

</frozen-after-approval>

## Code Map

`A` = `_bmad-output/implementation-artifacts`, `F` = `references/Hexalith.Folders` (read-only, at the pin), `E` = `A/evidence/story-5-8`.

**Source inventory and authority**
- `A/folders-migration-inventory-v1.md`: the immutable 1.0.0 (sha256 `57cf556b…`, bound by the AD-23 map). Row columns and the V/N/G tables are the successor's shape.
- `_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/AD-23-{non-gateway-capability-classes.md,capability-class-map.json}`: the class per entry (103 rows and 58 records), restriction precedence at `:36-41`, and Folders proof duties at `:140-160`. V04/V05 are K09 (Folders may withdraw them). V09/V10 are K15. R01/R02 are K02. Q04/Q06/Q10/Q12/Q15/Q20 are K06.

**Folders 5.12 record and decorated types**
- `F/docs/contract/mcpcli-folders-operation-declarations.md`:
  - eligibility, CLR type and wire per candidate: `:73-122`;
  - seven diagnostics deferred (need a C13 not-applicable product decision): `:91-107`;
  - losses: `:155-163`;
  - envelope, `taskId` and identifier treatment: `:167-209`;
  - `identifier-aggregate-grammar` gap: `:256-273`;
  - `tenant-wide-query-aggregate` (Q16) gap: `:223`.
- `F/src/Hexalith.Folders.Contracts/` holds the types:
  - module: `FoldersModule.cs:3` (`folders`, String kind);
  - `Commands/<Name>.cs`: WireType `Hexalith.Folders.Commands.<Name>`, required idempotency key, aggregate `FolderId` (C05: `ProviderBindingRef`);
  - `Queries/<Name>.cs`: WireType `Hexalith.Folders.Queries.<Name>`, kebab `ProjectionType`, aggregate `FolderId` (Q13/Q35: `ProviderBindingRef`; Q16: none).
- Route as sent: `src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs:251-271`.
- `F/_bmad-output/implementation-artifacts/sprint-status.yaml:171-176`: 5.12 done; 5.10, 5.13 and 5.14 backlog.

**Drift `e2252f29`→`7eab70e9`** (no surface added, removed or renamed)
- Changed rows:
  - M01, M04, M13 and L24–L26 now require `expectedFileVersion`/`expectedLockFence`. `MutateFiles` carries both in `FileMutationRequest`.
  - M21, M41, M44, M47, R02 and L32–L35 gain `fileId`/`version`.
  - M37, M40, L19 and L22 gain `lockFence`.
- Cross-cutting: bearer tokens now go only to HTTPS or a loopback host (`src/shared/AdapterCore/BearerTransportPolicy.cs:12`).
- Changed premises:
  - G1: Contracts are now decorated.
  - G4: three internal query handlers and a new `POST /query`; none serves the 28 types.
  - G5: real implementations except the commit executor (`FoldersServerServiceCollectionExtensions.cs:122-126`).
  - V05: REST multipart `PutFileStream`.
  - N04: superseded banner.
- Registration anchor is now `Program.cs:61`.
- New native REST endpoints (`WorkspaceNativeEndpoints.cs:33-37`) are outside the MCP/CLI surface scope. Note them only.

**Reusable Story 5.7 and 4.2 evidence**
- `A/evidence/story-5-7/{build_candidate.py,verify_amendments.py,test_verify_amendments.py,verify_labels.py,approval.json,labels.json}`: hard-coded to Admin/technical. Copy and adapt. Keep `sys.dont_write_bytecode`, the live-globals guard-removal runner, exact-stream assertions and report-only owner drift.
- `A/evidence/story-4-2/verification.md:16-260`: port its count, leaf and `Name =` checks to `git show <pin>:`.
- Folders `README.md:60-61` on `origin/main` (`583d3d49`): PS10/PS11 cite "Folders inventory 1.0.0". The `F` copy predates them.

**Leave unchanged**
- Technical 1.0.3 at `:147-148` and `:187`. The next technical successor cites 1.1.0.

## Tasks & Acceptance

**Execution:**
- [x] `A/folders-migration-inventory-v1.1.0.md` and `.gitattributes` (`-text`): write the successor from the derivation rules below. Corrected premises go in G/V cells and the source section. A2 stays pending.
- [x] `E/build_candidate.py`: generate it deterministically from the 1.0.0 bytes, `git show 7eab70e9:` sources and the 5.12 record. Refuse to overwrite an approved packet.
- [x] `E/{verify_amendment.py,test_verify_amendment.py}` cover:
  - candidate and approved-completion modes;
  - 161-entry accounting against the AD-23 map;
  - anchors and drift;
  - decorated type, wire and route per `replace`;
  - include⇔replace, gap/owner and K12 handling;
  - G-story status, the hash chain and roles.
  - Test every matrix row and disposition branch with guard-removal controls, the process exit and both streams.
- [x] `E/{approval.json,labels.json,verify_labels.py,upstream/folders/}`: a pending receipt bound to the 1.0.0/1.1.0 hashes and their authorities, and a README-only PS10/PS11 citation patch whose register is chained to the 5.7 register.
- [x] `A/deferred-work.md` (grep first), `E/verification.md`, the secret-scan receipt, this spec and `A/sprint-status.yaml`: record only the supported state.

**Acceptance Criteria:**
- Given the candidate, when the verifier runs, then all 161 entries pass and the 1.0.0, AD-23 and technical 1.0.3 bytes are unchanged.
- Given exact-byte owner approval and separate delivery authorization, when completion runs, then the receipt names the covered Folders roles and the integrated Folders label cites 1.1.0. The approval grants no enrollment, execution or retirement.

### Review Findings

This is code review pass 1 (bmad-code-review, 2026-11-13), run after the two in-spec bmad-build reviews.

**Scope:** the deliverables, 3,404 diff lines in 13 files:
- the 1.1.0 inventory and `.gitattributes`;
- `build_candidate.py`, `verify_amendment.py`, `test_verify_amendment.py`, `verify_labels.py` and `delivery/lifecycle-proof.py`;
- `approval.json`, `labels.json`, `verification.md` and `upstream/folders/README.patch`;
- this story's ledger hunk;
- the Folders label commit `db40bda8`.

The baseline is `a92a296..HEAD` at `c3bd5b9`. Stream captures, secret-scan receipts, `commands.json` and `review-followup.diff` were left out.

Four layers ran: Blind B, Edge E, Verification V and Acceptance A. None failed. They raised 51 findings: 18 survive in 12 entries, and 33 were rejected.

The approved 1.1.0 bytes (SHA-256 `54a6f61d…`), `approval.json` and the delivered Folders labels can change only through a versioned successor with a fresh exact-byte approval.

- [x] [Review][Patch] The verifier reads old Folders pin `e2252f29`, which survives only in local reflog entries that expire soon (medium; Decision 1 resolved: **Read via 2236855e**) — `check_source_drift` reads `B.surfaces(root, OLD_PIN)` and the generated client at `OLD_PIN` on every verifier and test run (`verify_amendment.py:196`, `:199`).
  - `e2252f29` is in no ref of `references/Hexalith.Folders`, is absent from the owner checkout, and GitHub returns 422 "No commit found".
  - Only four HEAD/main reflog entries from 2026-10-16 retain it. Unreachable entries expire after 30 days by default (about 2026-11-15), and a later gc can prune the object.
  - Once it is pruned, both completion verifiers and all 36 tests fail permanently. They already cannot run in any fresh clone.
  - `e2252f29` is a single commit on top of the published `2236855e`, which is on GitHub and an ancestor of the `7eab70e9` gitlink. It only deletes `.mcp.json` and `.vscode/mcp.json`, so every `src/` byte the verifier reads is identical at `2236855e`.
  - Fix: record the `e2252f29:src` tree id in the builder constants while the object still exists. Read the old-pin sources at the published `2236855e`, and require its `src` tree id to equal the recorded id (and `e2252f29`'s, when present). Add a guard-removal test. Approved bytes stay unchanged.
  - (E1) [_bmad-output/implementation-artifacts/evidence/story-5-8/verify_amendment.py:196]
- [x] [Review][Defer] The K12 rationale on M01/M04/L24/L25 contradicts the adopted outcome next to it (low; approved bytes; Decision 2 resolved: **Fold into K12 successor**) — The four rows show `K01` / `decorated-gateway-contract`, but their rationale says "adopted confidential UI only conflicts with 5.12 owner decoration". Inventory `:42` repeats the claim for all ten entries.
  - These rows are deferred only because their target C10 is K12-restricted (AD-23 `:157`). `disposition()` gives every K12 key one shared string (`build_candidate.py:240`).
  - Epic 6 reads these rows when it resolves the K12 gap.
  - (B1, A4) [_bmad-output/implementation-artifacts/folders-migration-inventory-v1.1.0.md:99] — deferred: correcting approved bytes needs a new version, a new exact-byte approval and a PS10/PS11 relabel. Epic 6 cannot catalog Folders until the K12 successor exists, so that successor carries the fix and may also carry the rejected cosmetic items. Tracked in the ledger under "code review of spec-5-8".
- [x] [Review][Defer] The deferred K12 rows carry a full replace-style "Exact replacement" (low; approved bytes; Decision 3 resolved: **Fold into K12 successor**) — M01/M02/M04/M13/L10/L24–L26/C01/C10 are `defer / exclude`, yet each shows "C10: `…MutateFiles`; owner eligible; wire …; SubmitCommandRequest(…)".
  - Other deferred rows say "no decorated replacement" or "None; named prerequisite remains open". `replacement()` checks eligibility but not K12 membership.
  - The Exact replacement column can therefore read as an approved replacement for exactly the operations that Epic 6 is told not to catalog.
  - (A3) [_bmad-output/implementation-artifacts/folders-migration-inventory-v1.1.0.md:162] — deferred: same reason as Decision 2. Tracked in the same ledger section.
- [x] [Review][Defer] The file-mutation drift leaves out that the fence fields are now required and credits `ownerFileId` to the add/change rows (low; approved bytes; Decision 4 resolved: **Fold into K12 successor**) — The drift cells on M01/M04/M13/L24–L26/C10 say only "gains ownerFileId/expectedFileVersion/expectedLockFence".
  - At `7eab70e9` both fences are `Required = Newtonsoft.Json.Required.Always` (`HexalithFoldersClient.g.cs:11711`, `:11717`), and the legacy `add-file`/`change-file` tools take them as non-optional `long` parameters. The Code Map says "now require".
  - `ownerFileId` is reachable from the legacy tools only through the `remove-file` `RemoveFileRequest` JSON body. `add-file`/`change-file` never expose it.
  - (A1) [_bmad-output/implementation-artifacts/folders-migration-inventory-v1.1.0.md:99] — deferred: same reason as Decision 2. Tracked in the same ledger section.
- [x] [Review][Patch] The completion gate's published-artifact binding has no refusal test — Replacing the guard at `verify_labels.py:89` with `True` still passes all 36 tests. Both test fixtures fake every root `git show`.
  - On an isolated copy of the real packet with `inventoryRevision=85a5437`, the real code fails, while the code with the guard removed prints the PASS for integrated delivery.
  - Add `LabelTests` cases against real graph revisions: a revision older than the inventory, and `cab549c`, which holds the pending receipt. Assert the exact `(1, '', 'FAIL: …\n')` streams.
  - (V1) [_bmad-output/implementation-artifacts/evidence/story-5-8/test_verify_amendment.py:641]
- [x] [Review][Patch] The Folders delivery bindings have no refusal tests — Disabling the integrated README byte check (`verify_labels.py:80`), the owning-origin check (`:57`) or the commit byte-hash check (`:83`) still passes all 36 tests.
  - Real `583d3d49`, which is README-only, on `origin/main` and still cites 1.0.0, passes once `:80` is disabled.
  - Add real-graph cases for `583d3d49` as the integration, a fork `origin`, and a tampered `commitSha256`, each with exact streams.
  - (V2) [_bmad-output/implementation-artifacts/evidence/story-5-8/test_verify_amendment.py:695]
- [x] [Review][Patch] The completion trigger from integrated labels and the builder's delivered-label refusal are untested — Removing `verify_amendment.py:299` (`labels.state == 'integrated'` forces completion) or `build_candidate.py:542` (refuse to rebuild after integrated labels) still passes all 36 tests.
  - `:299` is the only approval gate on this path, because `owner_checked=True` makes `verify_labels.verify` skip its own check.
  - Add a `V` entrypoint case with a pending receipt, integrated labels and spec/sprint not done, expecting the exact approval FAIL. Add a builder case expecting the refusal with no writes.
  - (V3) [_bmad-output/implementation-artifacts/evidence/story-5-8/verify_amendment.py:299]
- [x] [Review][Patch] The McpCli route evidence is read from the mutable working tree — `verify_amendment.py:186` uses `(root / 'src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs').read_text()`, while every other authority comes from committed objects.
  - `verification.md:82` claims "Every source read uses committed Git objects".
  - A later Epic 6 refactor of request construction would fail Story 5.8's completion gate for reasons unrelated to it. An uncommitted edit changes the verifier's result.
  - Read the file with `git show BASELINE:` (`a92a296` line 251 is the cited `SubmitCommandRequest`) and keep the claim true.
  - (B4, E13, E21) [_bmad-output/implementation-artifacts/evidence/story-5-8/verify_amendment.py:186]
- [x] [Review][Patch] The evidence claims to prove that `expectedFileVersion`/`expectedLockFence` are required, but only checks that they exist — `verification.md:136-137` says the both-pin checks prove "required expectedFileVersion/expectedLockFence".
  - `check_source_drift` checks only that `JsonProperty("<prop>"` is absent at the old pin and present at the new one. Only `ownerFileId` gets a required-mode assertion.
  - Assert `Required = Newtonsoft.Json.Required.Always` for both fences in the new-pin class block, and add a guard-removal and corruption test.
  - (E20, A2) [_bmad-output/implementation-artifacts/evidence/story-5-8/verify_amendment.py:204]
- [x] [Review][Patch] The new K12 ledger entry has wrong anchors and stale status — AD-23 `:36` should be `:38` (restriction precedence), and `:155` should be `:157` (the C10 add/change-plus-removal variant). The inventory's `:39` should be `:40` (the IDs) and `:42`–`:43` (the catalog hold).
  - The status still says "neither decoration nor this pending candidate overrides AD-23", but 1.1.0 is approved and published at `f3c8f5f`.
  - (B2, E16, A5) [_bmad-output/implementation-artifacts/deferred-work.md:1049]
- [x] [Review][Patch] Some current-state wording still describes the pre-delivery state — `verification.md:19-24` says "All 31 tests passed …" as current fact, which conflicts with the final 36-test record.
  - `verification.md:150` labels the 1.1.0 hash "pending candidate", and `:158-159` says "The pending receipt names the Folders roles it must cover".
  - The new `.gitattributes` comment says "pending receipts".
  - Mark these as historical or update them to the approved/integrated state.
  - (B15) [_bmad-output/implementation-artifacts/evidence/story-5-8/verification.md:21]
- [x] [Review][Patch] `verification.md` says the 1.1.0 hash is enforced against the baseline commit — The table header at `:141-142` says the hashes are "also enforced against the baseline commit", and the table includes Folders 1.1.0.
  - 1.1.0 is not in `B.AUTHORITIES` and does not exist at `a92a296`. Deterministic regeneration and the receipt check it, not the baseline.
  - Split the row out, or state what actually checks it.
  - (E22) [_bmad-output/implementation-artifacts/evidence/story-5-8/verification.md:141]

**Rejected (33):**
- B3 low: the hard-coded prose anchors and the ancestry sentence resolve at immutable pins, and the approved hash freezes the builder output. They cannot drift, and checking them would add guards.
- B5/E19 low: the `blob/main` link uses an immutable, versioned filename and carries the exact SHA-256, and it follows the technical 1.0.3 citation convention approved in 5.7. Fixing it needs another owner-repo delivery.
- B6/E11 low: the 5.7 register input is immutable and hash-chained. The delivered PS10/PS11 text cites 1.1.0, and `README.md` bytes are verified exactly, so the stale-citation case cannot occur.
- B7 false: the approval guards are tested through fixtures (`owner approval lacks identity` and `lacks required covered` are asserted). Because the spec is done, damage to the real `approval.json` fails the default verifier entrypoint.
- B8/E2/E3 low: build review 1 already rejected the absolute owner checkout (B1) for this documentary packet. Ancestry against `origin/main` is backed by retained `ls-remote` readbacks (D3). Live remote checks would add network state.
- B9/E15/A6 low: the real receipt's `rolesCovered` equals `requiredApprovalRoles` exactly. Amendment owners name who must close each gap, not approvers, and no gate depends on mapping them. Changing the policy wording means changing receipt bytes.
- B10 false: the receipt's `artifacts` and `amendment.toSha256` bind the 1.1.0 hash, and `check_approval` requires them to equal the recomputed hashes.
- B11/A9 low: the seven diagnostic rows repeat one anchor (cosmetic, approved bytes). The CLR-type part is false, because the column heading admits "undecorated roadmap candidate" names.
- B12 low: the A2 sentence at `:28` is broken (cosmetic, approved bytes). The K12 successor can carry the fix.
- B13 false: the 5.12 record (`declarations.md:155`) declares the loss under the joint "V04/V05" decision. V05 is still deferred for staging, which is consistent with that.
- B14 low: V04's withdrawal is permitted by AD-23 `:152-153`, and only the citation is missing (approved bytes). The K12 successor can carry it.
- B16 low: the duplicated replacement listing in the V rows is a readability issue only (approved bytes). The K12 successor can carry the fix.
- E4 false: completion already requires `origin/main` for ancestry, so the drift read cannot change the outcome. Failing loudly when the remote branch is missing is correct.
- E5 false: every `next()` lookup runs over hash-chained or immutable inputs (the 5.7 register, the AD-23 map, PS10/PS11 coverage checked first), so a miss cannot be reached.
- E6 low: the builder refuses the approved packet, so it cannot run now. A transactional write would add complexity.
- E7 low: the recorded run used `-B -I`, not `-O`. Changing the helper would desynchronize its retained captures.
- E8 low: rerunning the helper intentionally regenerates its captures, and Git shows the change.
- E9/E10 false: the pinned declaration table has 48 unique IDs (counted), and the MCP resources are unique at the immutable pin.
- E12 false: neither pin has a class whose name begins with `FileMutationRequest`, `FileMetadataItem` or `LockLeaseMetadata` (checked with `grep`).
- E14 low: the tests deliberately load helpers from isolated `--root` views. Ordinary runs use the real root.
- E17 low: "Above inclusive 1048576 is invalid" is ambiguous wording (cosmetic, approved bytes). The K12 successor can carry the fix.
- E18 low: `README.patch` is a byte-bound record, verified by equality and never applied. The delivery is complete.
- E23 low: commit subjects already published on `main` cannot be changed without rewriting history, and they are outside the reviewed diff.
- A7 low: V09 points to "their affected rows in the 5.12 source table" (`:67`), so the rows are referenced (approved bytes). The K12 successor can carry the full list.
- A8 low: G4/G5/V05 have new-pin anchors, and the verifier checks the premises (`verify_amendment.py:211-218`). Only the source-line citations are missing (approved bytes). The K12 successor can carry them.

Code review pass 2 (bmad-code-review, 2026-11-14). It ran after `edd15cf` applied the pass-1 patches and the resumed build review's five patch groups.

**Scope:** the deliverables again, 3,720 diff lines in 13 files. The range is `a92a296..HEAD` at `edd15cf`, over the pass-1 file set plus the Folders label commit `db40bda8`.

Four layers ran: Blind B, Edge E, Verification V and Acceptance A. None failed. They raised 33 findings: 22 survive in 13 entries (10 patch, 3 defer), and 11 were rejected.

The approved 1.1.0 bytes, `approval.json` and the delivered labels are unchanged. The three defers follow pass-1 Decision 2: fold approved-byte defects into the K12 successor.

- [x] [Review][Patch] The published-graph fixture reads mutable state, so the retained lifecycle proof now fails and a later Folders relabel will break four tests (medium)
  - `published_graph_fixture` reads the register from the working-tree `labels.json` and copies the working-tree `approval.json` (`test_verify_amendment.py:795-796`).
  - It also points the fixture's `origin/main` at the owner checkout's moving `origin/main` (`:806`).
  - I reran `delivery/lifecycle-proof.py` with its delivery directory redirected to a scratch folder. It now reports `Ran 50 tests … FAILED (failures=5)`: all five `test_real_publication_*` and `test_real_delivery_*` cases fail.
    - In the synthetic lifecycle register, the integration commit is `LABEL_PIN` and the approval is synthetic, so the guard-removal runs never reach PASS.
    - The retained `delivery/lifecycle-integrated.*` captures still show the 36-test pass from before the patches. `review-final-20261114/commands.json` never reran the helper.
  - `published_guard_control` asserts empty stderr. But `verify_labels.py:97-98` prints a `reported:` line whenever the current `origin/main` compatibility section differs from the delivered one.
    - Folders `origin/main` has already moved to `b915d3ec`; its README is unchanged so far.
    - The planned K12-successor relabel of PS10/PS11 will make the four guard-control tests fail.
  - Fix:
    - Read the register and approval from their published commits with `git show`, and set the fixture's `refs/remotes/origin/main` to the delivery commit `db40bda8`.
    - Rerun the lifecycle proof into a new task-owned packet and record its exact streams.
  - (E1, B8) [_bmad-output/implementation-artifacts/evidence/story-5-8/test_verify_amendment.py:795]
- [x] [Review][Patch] The duplicate workflow-status guard has no test (medium) — `completion_requested` rejects a second status line (`verify_amendment.py:266`). Without that check, a second `done` line silently disables the done trigger at `:267`.
  - The two "duplicate workflow statuses" tests assert the test-only helper's `fixture requires one workflow status` error (`test_verify_amendment.py:67-71`), not the verifier's.
  - The V layer deleted `:266` in an isolated copy. Both `verify_amendment.py` and `verify_labels.py` then exit 0 with the pending PASS on a duplicated spec or sprint status, and all 50 tests still pass.
  - Fix:
    - For both the spec key and the sprint key, add a `workspace_view()` case that appends a second status line. Assert `(1, '', 'FAIL: duplicate workflow status …\n')` from both entrypoints through `fixture_process`.
    - Add a deletion control like `test_real_verifier_calls_source_drift_guard_and_deletion_control`.
  - (V1) [_bmad-output/implementation-artifacts/evidence/story-5-8/verify_amendment.py:266]
- [x] [Review][Patch] Label-register and inventory-verifier guards have no failing-input tests or removal controls (medium) — The test file contains none of these guards' messages, so disabling any one of them leaves all 50 tests passing.
  - Label guards, demonstrated by the V layer on the real integrated register: with only the named `require` disabled, each tampered input returns `(0, 'PASS: … integrated delivery verified\n', '')`.
    - `verify_labels.py:78`, canonical integrated label commit: a 12-character `db40bda8a107` resolves.
    - `:39`, register schema: `schemaVersion = '9.9.9'`.
    - `:54`, repository/base: `baseRevision = '0'*40` or a fork URL.
    - `:61`, README hashes: `readme.beforeSha256 = '0'*64`.
    - `:62`, README-only patch: an appended `src/Other.cs` hunk with a matching `sha256`.
    - `:72`, retention semantics: no test either.
  - Inventory-verifier guards (A layer):
    - Some have mutable inputs, and removing them only changes the diagnostic, because the receipt hash chain and `:293` still reject: `:116` legacy identity, `:119` target-disposition inheritance, `:276` preserved authority (AC1) and `:293` candidate prose.
    - The others have pinned inputs: `:145-147` set checks, `:164-166` registration and module, `:172` no decorated target, `:203` surface drift, `:218-223` premises and `:280` AD-23 adoption.
  - Fix:
    - Add exact-stream refusal cases with guard-removal controls for each guard.
    - For the label cases, use `invoke_register`/`reject` and write the changed patch file into `self.root`.
    - For the pinned premises, patch `B.source`, as `test_required_fence_attributes_and_guard_removal` does.
    - CLAUDE.md requires a removal-sensitive test for every new guard.
  - (V2, V3, A1) [_bmad-output/implementation-artifacts/evidence/story-5-8/verify_labels.py:78]
- [x] [Review][Patch] The lifecycle proof's "real inputs unchanged" claim is a literal, not the checked comparison (low) — `delivery/lifecycle-proof.py:68` writes `'realInputsUnchanged': True`, and the only check is the `assert` at `:64`.
  - Deleting `:64` leaves `test_lifecycle_proof_binds_local_captures_and_replay` green, because it asserts the constant (`test_verify_amendment.py:203`). Under `python -O` the `assert` is stripped, so the field stays `True` even if the real bytes changed.
  - Fix:
    - Compute the field from `before == after` and raise an exception instead of using `assert`.
    - Add a negative control that changes a protected path's second snapshot, and assert the failure with no summary written.
  - (V4, E2) [_bmad-output/implementation-artifacts/evidence/story-5-8/delivery/lifecycle-proof.py:64]
- [x] [Review][Patch] Three 5.8 ledger anchors point at the wrong builder lines (low) — `deferred-work.md:1057`, `:1062` and `:1067` cite `build_candidate.py:241`, `:266` and `:304`.
  - `edd15cf` added four lines, so these now land on a blank line, the R01/R02 gaps line and `row_name`.
  - The targets are now `:245` (the shared K12 string), `:270` (`replacement()`) and `:308` (`drift()`). The newer SDK entry already cites `:308`.
  - (B1, E8, A3) [_bmad-output/implementation-artifacts/deferred-work.md:1057]
- [x] [Review][Patch] The two resumed-build-review deferrals sit under the pass-1 code-review heading (low) — The SDK end-anchor and redirect entries (`deferred-work.md:1068-1077`) say "identified during resumed build review on 2026-11-14". They are filed under `## Deferred from: code review of spec-5-8… (2026-11-13)`.
  - Their delivery vehicle, "next versioned Folders successor", also reads differently from the neighbouring entries' "K12 reconciliation successor".
  - Fix: give them their own source/date heading, and name the K12 reconciliation successor as the vehicle. Epic 6 cannot catalog Folders before it exists, so that successor is the next Folders version.
  - (B2, A4) [_bmad-output/implementation-artifacts/deferred-work.md:1068]
- [x] [Review][Patch] The SDK end-anchor ledger entry cites 2 of the 23 changed files (low) — The entry frames the change as client-SDK tightening and cites only `Oq2RequestValidation.cs:13` and `Oq2WireObjectConverter.cs:16`.
  - Between `2236855e` and `7eab70e9`, `\z` anchors were added in 23 `src` files (none at `2236855e`). They include server and domain validators the legacy heads reach: `FolderCommandValidator`, `WorkspacePathPolicyValidator`, `StreamNameSegment`, `OrganizationAclCommandValidator`, `OrganizationProviderBindingCommandValidator`, and the provider-readiness and diagnostics query handlers.
  - The successor's "determine affected rows" work would start from an incomplete premise. Fix: extend the summary and evidence to the server and domain validators.
  - (B3) [_bmad-output/implementation-artifacts/deferred-work.md:1069]
- [x] [Review][Patch] `verification.md` still says no commit or push happened (low) — `verification.md:63-65` says "No commit or push was performed", but that text was committed in `edd15cf`, which equals `origin/main`. The title still says "(2026-11-13)" above the 2026-11-14 current-state section.
  - The commit carries the user's authorship and no agent attribution, so the frozen "Never commit" rule (which binds the agent) is not shown to be violated. Only the current-state wording is stale.
  - Fix: say that the build session performed no commit and that the user later committed the work as `edd15cf`, and date the title.
  - (B9, A5) [_bmad-output/implementation-artifacts/evidence/story-5-8/verification.md:64]
- [x] [Review][Patch] The preserved-authority hash table lists 4 of the 8 bound authorities (low) — The table under "Preserved authority hashes, enforced against the baseline commit and bound by approval.json" omits four authorities that `B.AUTHORITIES` (`build_candidate.py:48-51`) pins and `approval.json` binds.
  - The missing four are story-5-2 `approval.json` and `main-integration.json`, and story-5-7 `approval.json` and `labels.json`.
  - Fix: add the four rows.
  - (B10) [_bmad-output/implementation-artifacts/evidence/story-5-8/verification.md:208]
- [x] [Review][Patch] Test fixtures compare unresolved temp paths with the verifiers' resolved roots (low) — Three fixtures use `root = Path(temp)` (`test_verify_amendment.py:111`, `:649`, `:799`), while `verify_amendment.verify` and `verify_labels.verify` call `Path(root).resolve()`.
  - Patched reads such as `path == self.root/B.E/'labels.json'` (`:735`) therefore miss under a symlinked `TMPDIR`, for example macOS `/private/var`.
  - Fix: resolve each temp root (`Path(temp).resolve()`).
  - (E6) [_bmad-output/implementation-artifacts/evidence/story-5-8/test_verify_amendment.py:111]
- [x] [Review][Defer] Most M/L rows claim "unchanged … existing semantics retained", backed only by name-set checks (medium; approved bytes) — 96 rows say `unchanged: … existing semantics retained`.
  - `check_source_drift` compares only tool, resource and leaf name sets plus six generated-model properties. `check_drift` compares cells with the builder's own `drift()` text.
  - Between `2236855e` and `7eab70e9`, 28 legacy-head and AdapterCore files changed, for example:
    - `CommandPipeline`, `CommandOptions`, `FileCommand` and `CredentialResolver` (CLI);
    - `ToolPipeline`, `RequestBody`, `FileTools` and `McpCredentialResolver` (MCP);
    - `RequestBodyParser`, `MutationSourcing`, `QuerySourcing`, `SafeBearerTokenHandler` and `LoopbackBypassProxy` (shared AdapterCore).
  - The SDK end-anchor and redirect omissions (`deferred-work.md:1068`, `:1073`) are two instances. No ledger entry covers the remaining unaudited legacy-head drift.
  - A retirement or parity decision that takes "existing semantics retained" at face value would miss unrecorded behavior differences, which the epic says block retirement.
  - The A-layer point that the spec claims all acceptance conditions are satisfied would require editing this spec, so that part is rejected.
  - (B7, A2) [_bmad-output/implementation-artifacts/folders-migration-inventory-v1.1.0.md:113] — deferred: approved bytes. Correcting them needs a new version, exact-byte approval and a PS10/PS11 relabel. Per pass-1 Decision 2 the K12 successor carries a per-surface semantic drift audit, and its verifier should compare tool parameters and CLI options between the pins. Ledger: "code review pass 2 of spec-5-8".
- [x] [Review][Defer] The approved 1.1.0 bytes still describe themselves as pending (low; approved bytes) — The metadata says `status: pending` and `approval_ref: '#a2-amendment-approval-pending'`, and the A2 section says "Until then this is a pending proposal". Every Approval cell links `#a2-amendment-approval-pending`.
  - The delivered Folders README sends readers straight to this file.
  - The 5.7 code review tracked the same defect for Admin 1.0.2 and technical 1.0.3 (`deferred-work.md:1037`). No Folders entry exists.
  - (B4) [_bmad-output/implementation-artifacts/folders-migration-inventory-v1.1.0.md:3] — deferred: approved bytes. The K12 successor should state approved status and cite `evidence/story-5-8/approval.json`. Ledger: "code review pass 2 of spec-5-8".
- [x] [Review][Defer] Query-target replace rows attribute G1/G2 to Folders Story 5.14 (low; approved bytes) — `disposition()` emits `G1/G2/G4/G5 / Story 5.14` for every Query-target `replace` row (`build_candidate.py:259`). That is 114 occurrences in the inventory, for example M15 and Q16.
  - In this document "gap / Story" names the owning story (as in `G6 / Story 5.10`). The G table says G1 is Folders 5.12 (done) and G2 is Folders 5.13.
  - The Command variant, `G1/G2/G3/G5; command-payload-translation / Story 5.13`, is ambiguous in the same way.
  - Epic 6 planning could read G2 as closing with 5.14.
  - (A6) [_bmad-output/implementation-artifacts/folders-migration-inventory-v1.1.0.md:113] — deferred: approved bytes. The K12 successor should give each gap its own story. Ledger: "code review pass 2 of spec-5-8".

**Rejected (11):**
- B5 low: bare story numbers in the approved bytes (Folders 5.10/5.12/5.13/5.14 next to McpCli 5.11). The G table names "Folders Story" for each gap, so readers can resolve them. This is cosmetic, in approved bytes, and the K12 successor can qualify them.
- B6 low: the verifier "checks determinism, not correctness". By design it pairs builder derivation with independent checks at the pin: accounting, decorated type/wire/domain/aggregate/projection, resolvable anchors, G-story status and both-pin model fields. The semantic defects it missed are tracked for the successor. Independent rules for them would fail the approved bytes now.
- B11 low: `git diff --check` without a revision, plus the packet-wide whitespace exemption. `git diff --check a92a296 HEAD` is clean, and no packet script, JSON, `verification.md` or `README.patch` has trailing whitespace or lacks a final newline. The exemption is the repository convention for scanned packets (5.7 pass-3 B16).
- B12 low: free-form `approvedOn` dates and no ordering check. The receipts are immutable, both record `2026-11-13`, and a fix would add guards.
- B13 low: the N01 anchor is the doc-comment line `:16` instead of `MapFolderPermissionMaintenance(` at `:17`. The anchor resolves to the adjacent non-blank line of the right member. This is cosmetic, in approved bytes, and the K12 successor can use exact declaration needles.
- B14 low: the Epic 6 catalog hold exists only in prose. Enrollment needs an approved coverage inventory under `tools/inventory-coverage/v1/`, and Story 5.12's gate fails cataloged excluded operations. The hold is tracked at `deferred-work.md:1045`. A Folders-specific refusal in production gates is forbidden by the zero-module-specific rule and this story's Never list.
- E3 low: the lifecycle proof's default delivery folder overwrites retained captures on rerun. Settled in pass 1 (E8): a rerun regenerates captures intentionally and Git shows the change. A transactional write adds complexity.
- E4 false: a hard FAIL when the owner checkout lacks `origin/main` or a README. Completion requires `origin/main` for ancestry (`verify_labels.py:81`), so failing loudly is correct (pass-1 E4). No Folders revision without `README.md` has been shown.
- E5 low: the executed 5.2 and 5.7 helpers are not pinned to the baseline. Both are immutable evidence of earlier stories, their hashes are bound in `review-final-20261114/commands.json`, and a pin would add a guard.
- E7 low: the exact git `fatal:` text is locale-dependent. The recorded workspace runs `C.UTF-8` without git translations. Forcing `LC_ALL=C` would add an environment parameter to the shared builder's `git()` helper, and the exact-stream assertion is the repository rule.
- V5 low: completion does not compare `labels.json` or the README patch with a published copy. Every structural field is checked against the builder output and the owner graph (`verify_labels.py:54-83`), so only the free-text delivery authorization is unpinned. The integrated register was not yet on `inventoryRevision`, so a fix needs a new revision binding and guard.

Code review pass 3 (bmad-code-review, 2026-11-14). It ran after `733fc71` applied the pass-2 patches and the resumed pass-2 build review's four patch groups.

**Scope:** the deliverables again, 4,063 diff lines in 13 files. The range is `a92a296..HEAD` at `733fc71`, over the pass-2 file set plus the Folders label commit `db40bda8`.

Four layers ran: Blind B, Edge E, Verification V and Acceptance A. None failed. They raised 36 findings: 13 survive in 11 entries (8 patch, 3 defer), and 23 were rejected.
- The root volume was 100% full during the run. The V layer therefore reports its gaps from code reading and test-message searches, not mutation runs.
- The A layer reran all 65 tests, both completion gates and AD-23, and all passed.

The approved 1.1.0 bytes, `approval.json` and the delivered labels are unchanged. The three defers follow pass-1 Decision 2.

- [x] [Review][Patch] The approval-decision and label-state guards have no tests, and the label verifier's integrated-state trigger is untested standalone (medium) — The guards are `verify_amendment.py:234` (`unknown approval decision`), `verify_labels.py:40` (`invalid label register state`) and the `register.get('state') == 'integrated'` trigger at `verify_labels.py:41`.
  - The test file contains neither message. Every integrated-register label test passes `--approved-completion` or patches `verify_owner_packet` out. `test_integrated_labels_force_owner_approval_without_done_status` covers only the inventory verifier's trigger (`verify_amendment.py:309`).
  - The A layer demonstrated on an isolated pending copy, with the guard removed:
    - `decision: "rejected"` returns `(0, 'PASS: … owner decision: rejected; candidate only …')`;
    - `state: "withdrawn"` returns the pending label PASS.
  - Without `:41`, an integrated register with pending approval and a non-done workflow takes the pending branch's success line.
  - Fix: add exact-stream refusal cases with guard-removal controls for:
    - an unknown decision;
    - an unknown register state;
    - a standalone `verify_labels.py` run with only `state='integrated'`, expecting `FAIL: completion requires exact-byte owner approval and covered Folders roles`, plus a trigger-removal control.
  - (A1, V2) [_bmad-output/implementation-artifacts/evidence/story-5-8/verify_labels.py:40]
- [x] [Review][Patch] The completion check that the approved bytes are still on `origin/main` has no test (medium) — `verify_labels.py:89` requires the bytes at both `inventoryRevision` and `origin/main` to equal the local inventory and receipt.
  - Every test that reaches `:89` either returns the local bytes for both reads (`test_completion_chain_and_exact_delivery_bytes`, `existing_graph_fixture`) or fails on the first condition (`85a5437`, `cab549c`).
  - Both conditions share one message, so `published_guard_control` cannot tell them apart.
  - Deleting `and B.sha(B.git(root,'show',f'origin/main:{path}')) == digest` leaves every test passing. Completion would then accept a `main` that later rewrote or removed the approved inventory or receipt.
  - Fix:
    - Add an `existing_graph_fixture` variant whose `committed` returns changed bytes only for `('show','origin/main:'+path)`.
    - Cover both paths and assert the exact `FAIL: <path>: published artifact differs from owner-approved bytes` stream.
    - Add a removal control for that half of the condition.
  - (V1) [_bmad-output/implementation-artifacts/evidence/story-5-8/verify_labels.py:89]
- [x] [Review][Patch] Thirteen backstopped row, anchor, metadata and label-artifact guards have no removal control (low) — No test contains the message of any of these guards:
  - `verify_amendment.py`: `:91` (amendment columns), `:111`–`:113` (legacy/amendment disposition, coverage and combined), `:131` (anchor path escapes), `:135` (source anchor), `:246` (frontmatter) and `:252` (damaged or duplicate metadata);
  - `verify_labels.py`: `:28`, `:30` and `:70`.
  - Removing any one leaves all 65 tests passing. A full run still refuses the damage later, so nothing wrong is accepted; only the named diagnostic is lost. The later checks are the candidate-bytes check at `verify_amendment.py:295`, the receipt hash chain, or the label byte comparisons at `verify_labels.py:61`, `:62` and `:68`.
  - The A layer demonstrated three cases passing `check_rows` once the matching guard is removed: M03 `Coverage=exclude`, M03 `Disposition=defer` and V07 `defer / include`.
  - The frozen matrix asks for actionable diagnostics, and CLAUDE.md requires a removal-sensitive test for every guard.
  - Fix: add one row per guard to the existing `guard()` tables and the `LabelTests.guard` helper, as pass 2 did for `:116`, `:119`, `:276` and `:293`.
  - (A3, V3) [_bmad-output/implementation-artifacts/evidence/story-5-8/verify_amendment.py:111]
- [x] [Review][Patch] The lifecycle proof's post-child workflow check accepts a child that reverts one of the two statuses, and has no test (low) — `delivery/lifecycle-proof.py:67` calls `completion_requested(fixture, False)`. That returns true when either the spec or the sprint entry is `done` (`verify_amendment.py:269`).
  - The summary still claims `sourceFixture: 'approved / integrated / spec done / sprint done'` (`:75`).
  - No test contains `synthetic lifecycle workflow changed during child run`.
  - Fix:
    - Snapshot the fixture spec and sprint bytes after `workflow_status`, and require them unchanged after the child, as `:65` already does for the receipt and labels.
    - Add a child that rewrites only the sprint status, and assert the refusal and that no summary is written.
  - (V other) [_bmad-output/implementation-artifacts/evidence/story-5-8/delivery/lifecycle-proof.py:67]
- [x] [Review][Patch] The lifecycle proof writes its stream sidecars before its integrity checks (low) — `delivery/lifecycle-proof.py:62` writes `lifecycle-integrated.{stdout,stderr}.txt` before the checks at `:65`–`:72`.
  - A refusal therefore overwrites the sidecars but leaves the old `lifecycle-integrated.json`, whose `sha256` values no longer match them. With the default delivery folder, those are the retained historical captures.
  - The two negative tests assert only that the JSON summary is absent: `test_lifecycle_proof_rejects_changed_real_inputs_without_summary` and `test_lifecycle_proof_rejects_child_label_mutation_under_optimization`.
  - Fix: compute the capture hashes after the child, but write the sidecars only after every check passes. Make both negative tests assert an empty delivery folder.
  - (E3) [_bmad-output/implementation-artifacts/evidence/story-5-8/delivery/lifecycle-proof.py:62]
- [x] [Review][Patch] Five text reads use the locale encoding (low) — `verify_amendment.py:265`, `:285` (twice) and `:286`, and `build_candidate.py:357` and `:512`, call `read_text()` without an encoding.
  - `-I` ignores `PYTHONUTF8`. Under a non-UTF-8 locale such as `LANG=en_US.ISO-8859-1`, the en dashes in both inventories mis-decode and the verifier fails the approved bytes.
  - `source()` already decodes Git output as UTF-8, and the Story 5.2 verifier passes `encoding="utf-8"`.
  - Fix: pass `encoding='utf-8'` at each of these calls.
  - (E1) [_bmad-output/implementation-artifacts/evidence/story-5-8/verify_amendment.py:285]
- [x] [Review][Patch] Two tests resolve 7-character commit abbreviations (low) — `test_verify_amendment.py:1041` and `:1048` run `rev-parse` on `85a5437^{commit}` and `cab549c^{commit}`. A later commit with the same prefix would make them ambiguous.
  - `verification.md:31-32` already records the full SHAs.
  - Fix: use the full SHAs.
  - (B10) [_bmad-output/implementation-artifacts/evidence/story-5-8/test_verify_amendment.py:1041]
- [x] [Review][Patch] The reproduction prerequisites omit the parent commits the graph tests read (low) — `existing_graph_fixture` resolves McpCli `HEAD^` and the owner's `LABEL_PIN^` and `LABEL_PIN^^` (`test_verify_amendment.py:1110`–`:1113`).
  - `verification.md:29-33` lists only `85a5437`, `cab549c` and `c3bd5b9` as additional test objects, so a shallow clone fails with a git error.
  - Fix: list those parent commits in the prerequisites, and state that the McpCli tests read the current `HEAD`. Do not add skip branches.
  - (E9) [_bmad-output/implementation-artifacts/evidence/story-5-8/verification.md:30]
- [x] [Review][Defer] The 1.1.0 G2 gap drops three 1.0.0 gate requirements (medium; approved bytes) — 1.0.0 G2 (`folders-migration-inventory-v1.md:88`) requires:
  - content/search egress policy;
  - "Envelope tenant/actor are comparison inputs, never self-authenticating authority";
  - "Prove denied cross-tenant reads/writes disclose no protected data and cause no mutation".
  - 1.1.0 G2 (`:89`, from `build_candidate.py:54`) keeps only "… deny-before-access and zero unauthorized effects remain unproved".
  - The pinned 5.12 record's G2/G3 still names "envelope comparison" (`docs/contract/mcpcli-folders-operation-declarations.md:167-168`).
  - Seven M rows still cite G2 for "path/egress policy" (`:119`, `:120`, `:139`, `:142`, `:144`–`:146`).
  - G2's Drift cell says "unchanged … existing semantics retained", and no decision records the narrowing.
  - Folders 5.13 or Epic 6 could therefore close G2 against the narrower text without proving egress, envelope comparison or non-disclosure on denial.
  - (A2) [_bmad-output/implementation-artifacts/folders-migration-inventory-v1.1.0.md:89] — deferred: approved bytes. Per pass-1 Decision 2, the K12 successor restores the three requirements. Ledger: "code review pass 3 of spec-5-8".
- [x] [Review][Defer] The approved 1.1.0 prose cites only the unpublished predecessor `e2252f29` (low; approved bytes) — `:18` says "Source was refreshed from `e2252f29…`", a commit GitHub cannot resolve.
  - The verifier actually compares the published ancestor `2236855e`, bound to `src` tree `d0f81f0f…`. It appears nowhere in the approved bytes, so a reader of the public repository cannot reproduce the drift baseline.
  - The spec-4-15 ledger entry (`deferred-work.md:682`) tracks the unpublished 1.0.0 pin. 1.1.0 re-pins the source but not the drift-baseline citation.
  - (B12) [_bmad-output/implementation-artifacts/folders-migration-inventory-v1.1.0.md:18] — deferred: approved bytes. The K12 successor cites `2236855e` and the recorded tree. Ledger: "code review pass 3 of spec-5-8".
- [x] [Review][Defer] The builder's source-grammar and duplicate guards are never exercised (low) — No test reaches:
  - in `surfaces()`: `build_candidate.py:152` (duplicate MCP tool), `:182` (upload helper link), `:185` (one client call per CLI leaf) and the file-remove grammar;
  - the helper and call guards in `client_operations()`, and `upload_operations()`;
  - the one-section and one-label checks in `compatibility_section()` and `label_candidate()`.
  - `surfaces()` stores resources, and `client_operations()` stores calls, without duplicate checks.
  - Both pins are fixed, so none of these can fire today. They matter when the K12 successor moves the pin, since it is expected to reuse this builder.
  - (V4) [_bmad-output/implementation-artifacts/evidence/story-5-8/build_candidate.py:152] — deferred: not reachable at the fixed pins. The K12 successor adds changed-source controls and duplicate checks when it re-pins. Ledger: "code review pass 3 of spec-5-8".

**Rejected (23):**
- B1/E10 low: the delivered PS10/PS11 links use `blob/main`, where 1.0.0 used a commit permalink. This was settled in pass 1 (B5/E19). The versioned filename is immutable, the label carries the exact SHA-256 and the link follows the technical 1.0.3 convention. Changing it needs another owner-repo delivery. The K12 successor's relabel can pin the publication commit at no extra cost.
- B2 false: `label_candidate` reads the hash-chained 5.7 register (`verify_labels.py:45`), whose PS10/PS11 texts contain the 1.0.0 link. The delivered README bytes, which cite 1.1.0, are compared exactly (`:61`, `:80`), so a label that keeps 1.0.0 cannot pass (pass-1 B6/E11).
- B3 low: the receipt check accepts extra roles, unknown keys and free-form dates. The real `rolesCovered` equals `requiredApprovalRoles` exactly. Completion compares the receipt bytes with `inventoryRevision` and `origin/main` (`verify_labels.py:89`), so such changes cannot be edited in. The fix would add guards (pass-1 B9, pass-2 B12).
- B4 low: the receipt omits 5.7's `approvalRequest` and `requiredRolesSource`. The spec requires only the covered roles and the A1 supersession, and the receipt records both. Its `approvalSource` states the question and both replies. Changing it needs a new exact-byte approval; the K12 successor's receipt can follow the 5.7 shape.
- B5/E6 false: every bare `next()` runs over inputs that are checked first. The AD-23 map is a preserved authority compared with the baseline (`verify_amendment.py:278`), and `labels.json` binds the 5.7 register's hash (`verify_labels.py:45`). A miss is unreachable (pass-1 E5).
- B6/V other false: at the immutable pins the declaration table has 48 unique IDs, and the resources and tools are unique (pass-1 E9/E10), so nothing is overwritten. Duplicate checks for a new pin are part of the V4 defer.
- B7 false: the suite is deliberately independent of lifecycle state. The documented gates are the default entrypoints, which run completion because the spec is done and the labels are integrated. Damage to the working-tree receipt fails them, so it does not go unnoticed (pass-1 B7).
- B8 false: the lifecycle proof claims only that the suite is independent of synthetic metadata, and says real completion is verified separately (`lifecycle-proof.py:74`; delivery follow-up D1).
- B9 low: the absolute owner checkout and the lack of CI coverage. Settled in build review 1 (B1) and pass 1 (B8); the path comes from the immutable 5.7 register.
- B11 low: Story 6.1's prerequisites do not mention the K12 hold. Story 5.12's gate fails cataloged excluded operations, so the K12 rows cannot be cataloged, and the ledger tracks the hold (`deferred-work.md:1045`). Editing Epic 6 planning is outside this story (pass-2 B14).
- B13/E7 false: archiving the spec or reindenting the sprint key cannot downgrade the real packet, because `labels.state == 'integrated'` forces completion independently (`verify_amendment.py:309`, `verify_labels.py:41`).
- B14 false: every remaining use of "final" sits under a heading marked Historical, and the pre-approval section says its references are superseded (`verification.md:199-203`).
- A4 low: the 161-entry accounting message does not name the missing ID. A missing entry cannot occur in the immutable approved bytes, and duplicates are already named (`verify_amendment.py:71`). The K12 successor's verifier can report the set differences.
- A5 false: the V04 row itself says "C10 and its rows remain K12 deferred" (`folders-migration-inventory-v1.1.0.md:268`), so it does not present the replacement as reachable.
- A6 false: `verification.md` scopes its claim to "This build session performed no commit or push", which is true, and `audit.json` records head `7fa3df6` as of its capture. The spec part would edit the spec under review.
- E2 false: the label verifier fails hard when the owner checkout lacks `origin/main` or its README. Completion requires `origin/main` for ancestry (`verify_labels.py:81`) (pass-1 E4, pass-2 E4).
- E4 low: rerunning the lifecycle proof with the default delivery folder overwrites the retained captures. Settled in pass 1 (E8) and pass 2 (E3): Git shows the change.
- E5 low: the builder writes non-transactionally. It refuses the approved packet, so it cannot run now (pass-1 E6).
- E8 false: Windows path separators. The register's absolute POSIX owner checkout (`labels.json:20`) already prevents a Windows run.

Erratum to pass 3: the backstopped-guard patch row above says "Thirteen" but names eleven sites (eight in `verify_amendment.py`, three in `verify_labels.py`). `verification.md` and the guard-removal helper correctly say eleven.

Code review pass 4 (bmad-code-review, 2026-11-14). It ran after the resumed pass-3 build applied the eight pass-3 patches and eight build-review patch groups. Those changes are uncommitted on top of `733fc71`.

**Scope:** the deliverables, 4,571 diff lines in 14 files, `a92a296..` working tree. The set is the pass-3 file set plus the new `review-pass3-20261114/guard-removal.py` and the Folders label commit `db40bda8`.

Four layers ran: Blind B, Edge E, Verification V and Acceptance A. None failed. They raised 36 findings: 11 survive in 6 entries (5 patch, 1 defer), and 25 were rejected.
- The V and A layers demonstrated their gaps with guard deletions in isolated `workspace_view(pending=False)` copies. All 77 tests still passed after each deletion, and the real sources stayed unchanged.
- The A layer reran all 77 tests, both completion gates and AD-23, and all passed.

The approved 1.1.0 bytes, `approval.json` and the delivered labels are unchanged.

- [ ] [Review][Patch] Parts of combined verifier guards have no test (medium) — Each part below can be deleted with all 77 tests still passing:
  - **V1:** the `all(V.nonblank(auth.get(k)) …)` part of the delivery-authorization check (`verify_labels.py:76`). The only refusal case sets `deliveryAuthorization = None`, so a `{}` or blank-`exactWords` authorization would pass the real completion gate.
  - **V2:** the `deliveryAuthorization` and `integration` parts of the pending no-false-delivery guard (`verify_labels.py:91`). Only `inventoryRevision` is tested.
  - **V3:** the `surface` and `repository` parts of the row binding (`verify_labels.py:67`). In completion this is the only check on a row's surface, so a label attached to the wrong legacy surface would pass both verifiers.
  - **A1:**
    - the `after_section` and `before_section` parts at `verify_labels.py:61`. Pending mode accepts a rewritten after-section, and only `:80` catches it in completion;
    - the `baselineCommit` and `sourceRevision` parts at `verify_amendment.py:228`;
    - the `rolesPolicy` part at `verify_amendment.py:232`.
  - The published-bytes check at `verify_labels.py:89` still protects the real receipt, but not the register, the rows or the authorization.
  - Fix: add exact-stream refusal cases for each part, with removal controls that disable only that part. Use the half-removal pattern of `test_completion_rejects_rewritten_published_artifacts_and_half_removal`, and extend `test_completion_chain_and_exact_delivery_bytes`, `test_register_chain_coverage_hash_citation_and_no_false_delivery` and the approval-receipt guard tables.
  - (V1, V2, V3, A1) [_bmad-output/implementation-artifacts/evidence/story-5-8/verify_labels.py:76]
- [ ] [Review][Patch] The builder's overwrite refusals are tested only for `approved` and `integrated` (low) — `build_candidate.py:542-543` refuses any decision other than `pending`, and `:547-548` any label state other than the pending one.
  - `test_builder_refuses_approved_packet_before_any_write` uses only `decision='approved'`, and `test_builder_refuses_integrated_labels_before_any_write` only `state='integrated'`.
  - Narrowing either condition to the tested value leaves all 77 tests passing. A recorded rejection or an unknown label state would then be overwritten by a fresh pending packet.
  - Fix: add a `'rejected'` decision subcase and a `'withdrawn'` state subcase, each asserting the exact refusal and no writes.
  - (V4, V5) [_bmad-output/implementation-artifacts/evidence/story-5-8/build_candidate.py:542]
- [ ] [Review][Patch] Five lifecycle-proof checks have no removal-sensitive test (low) — Removing the approval half of the post-child check (`delivery/lifecycle-proof.py:63`, `after_fixture[0] == approval and`) leaves all six lifecycle tests passing. A child that resets the synthetic approval would then still get a success summary.
  - The four setup checks at `:48-55` (approval, labels, workflow, candidate) appear in no test.
  - Fix: add a child that rewrites only the fixture approval, and a setup failure for each check by patching the helper's `workflow_status` or `write_text`. Assert each exact refusal and an empty delivery folder.
  - (A2) [_bmad-output/implementation-artifacts/evidence/story-5-8/delivery/lifecycle-proof.py:63]
- [ ] [Review][Patch] The final closure audit checks fewer protected files than earlier audits, and cannot be regenerated (low) — `review-pass3-final-20261114/audit.json` lists 8 protected artifacts. The pass-2-final and pass-3 audits each list 14.
  - It drops Story 5.2 `approval.json`/`main-integration.json`, Story 5.7 `approval.json`/`labels.json`, and the two `upstream/folders/README.*.section.md` files that `labels.json` binds by hash. `verification.md` nonetheless says the audit "verifies … the protected bytes against `HEAD`".
  - The generating runner was kept only in a session scratchpad.
  - The audit checks exit codes and hash consistency but not stream content, so a `reported:` drift line or a wrong PASS line would pass.
  - The `whitespace` capture's stderr holds two commit-graph warnings that pass 1 avoided with `-c core.commitGraph=false`.
  - Fix:
    - Retain the runner in the packet and restore the 14-entry protected list.
    - Assert the exact expected stdout and stderr of every gate, and run git with `-c core.commitGraph=false`.
    - Regenerate the final packet and correct the `verification.md` claim.
  - (B1, B2) [_bmad-output/implementation-artifacts/evidence/story-5-8/review-pass3-final-20261114/audit.json:1]
- [ ] [Review][Patch] The pass-3 builder-guard ledger entry omits untested builder guards (low) — `deferred-work.md:1121` lists the untested builder guards to exercise before a re-pin. It omits:
  - `anchor()`'s `pinned source missing` (`build_candidate.py:121`), which a re-pin hits first;
  - `damaged or duplicate pinned CLI root registrations` (`:166`);
  - `unsupported pinned file CLI registration` and `upload kind` (`:177`, `:179`);
  - `duplicate pinned CLI leaf` (`:188`).
  - Fix: add them to that uncommitted pass-3 entry's summary and evidence.
  - (B5) [_bmad-output/implementation-artifacts/deferred-work.md:1121]
- [x] [Review][Defer] Nothing outside this spec requires the next technical successor to cite Folders 1.1.0 (low) — The Code Map says "The next technical successor cites 1.1.0", and the Never list keeps technical 1.0.3 unchanged.
  - PS10 and PS11 in technical 1.0.3 (`technical-tools-migration-inventory-v1.0.3.md:147-148`) still cite Folders 1.0.0, PS10 at the unpublished `e2252f29`.
  - The only technical-successor ledger entry (`deferred-work.md:1039`) covers its pending self-description, not this re-citation, so Stories 5.9/5.10/5.11 could miss it.
  - (A4) [_bmad-output/implementation-artifacts/technical-tools-migration-inventory-v1.0.3.md:147] — deferred: approved technical bytes stay unchanged under this story's Never list. Ledger: "code review pass 4 of spec-5-8".

**Rejected (25):**
- E1 false: builder delimiter splits at a new pin. The delimiters exist at both immutable pins, and re-pin hardening is the pass-3 builder deferral (resumed pass-3 build E7).
- E2 false: at both `2236855e` and `7eab70e9`, all 49 `[McpServerTool(` attributes match the tool regex (checked with `git grep`), and the leaf set equals 1.0.0's 42 leaves.
- E3 false: bare `next()` StopIteration. Every lookup runs over authorities checked first (pass-1 E5, pass-3 B5/E6).
- E4 false: a missing spec or reindented sprint key cannot downgrade the real packet, because integrated labels force completion (pass-3 B13/E7).
- E5 false: `FileMutationRequest`, `FileMetadataItem` and `LockLeaseMetadata` each exist at both pins (checked), so no block is empty.
- E6 false: a hard FAIL without owner `origin/main` (pass-1/2 E4).
- E7 false: `main(root=…)` with a non-ancestor root. No caller passes a root (resumed pass-3 build E11).
- E8 low: non-transactional builder writes (pass-1 E6).
- E9 false: a missing 1.0.0 link in the prior label. The 5.7 register is hash-chained and the delivered README is compared exactly (pass-3 B2).
- E10 false: pending standalone run after editing the 5.7 register. The real register is integrated, so every run takes completion, which checks the 5.7 authorities against the baseline.
- E11 low: `approvedOn` date validation adds guards on immutable receipts (pass-2 B12, pass-3 B3).
- E12 low: ambiguous anchor needles. Every anchor resolves at the immutable pins. Exact needles are cosmetic in approved bytes, and the K12 successor can adopt them (pass-2 B13).
- E13 low: a localized git message in one test (pass-2 E7).
- E14 false: sidecar writes before `relative_to` (resumed pass-3 build E11).
- B3 low: raw `merge-base` refusal text. The refusal is loud and exact-stream tested, and a named message per exit code adds branches on published revisions.
- B4 low: completion trusts the register's `ownerCheckout`.
  - This corrects pass-2 V5: that field is not compared with the builder output.
  - It still needs a deliberately edited `labels.json`, which Git shows. The checkout's `origin` must still name the owning repository, and every owner byte and ancestry check runs.
  - Pinning it adds a guard and reworks two fixtures. The K12 successor's verifier can bind it.
- B6 false: the K12 hold names only Contracts 1.4.0. Cataloged excluded operations fail the Story 5.12 gate for any Contracts version, and only version differences are report-only.
- B7 low: the spec-4-15 ledger entry still lists Folders. It remains true for the immutable 1.0.0 pin, and Story 5.11 reconciles the re-pin.
- B8 false: the guard-removal run's `commands.json` entry binds all 11 inputs, including `test_verify_amendment.py`. The final audit compared those with the current files.
- B9 low: mixed `--root` helper loading. Only tests pass `--root`, and their copies are byte-identical. A single-tree loader changes the copied-entrypoint deletion controls.
- B10 low: the approved-but-undelivered PASS wording describes a state the published packet has left. It is cosmetic.
- B11 low: N03's class-declaration anchor is cosmetic in approved bytes (pass-2 B13).
- B12 false: the scope was the user's choice. The excluded files are captures and receipts, as in passes 1–3.
- V other false: same as B8.
- A3 low: the pass-3 "Thirteen" miscount. Fixing it would edit the earlier review row, so it gets the erratum note above instead.

## Design Notes

Derivation rules (the decisions above apply first):
- An eligible decorated candidate becomes `replace / include` with:
  - its CLR type, wire, `folders` domain, aggregate source, projection type and eligibility;
  - its open gaps. G1 is done but still owes AD-15 closure and Catalog acceptance (6.1). G2/G3 are 5.13, G4/G5 are 5.14, G6 is 5.10.
- An M/L/R row inherits its target's outcome. R01/R02 take Q28/Q30 and record the loss of URI and subscription.
- The seven diagnostics and their rows (M18, M20, M24, M26, M29, M31, M34) are `defer` (owner decoration and a C13 product decision).
- N01/N02 are `withdraw` (confidential UI). N03/N04 are `defer` (no type).
- V04 is `withdraw` (accepted local-file loss). V05 is `defer` (K09 staging; McpCli product/architecture owner).
- V07 is `replace` (canonical uppercase ULID key), with the auto-key and `sha256:` losses accepted. V01–V03, V06 and V08 are `replace`, each with its governing gap.

## Verification

**Commands:**
- `python3 -I A/evidence/story-5-8/verify_amendment.py`: expected to pass on the pending candidate. `--approved-completion` fails until approval and label integration.
- `python3 -I -m unittest discover -v -s A/evidence/story-5-8 -p 'test_*.py'`: expected to pass with every control detected.
- `python3 -I A/evidence/story-5-2/verify_class_map.py`: expected to report AD-23 still adopted.
- `python3 scripts/scan-evidence-secrets.py A/evidence/story-5-8 --receipt <task-owned path>` and `git diff --check`: expected clean.

## Implementation Notes

- 2026-11-13: The user approved this spec with "approve and stop". The frozen intent and decisions are locked, and implementation resumes in a fresh `bmad-build` session. Exact-byte inventory approval and Folders label delivery remain pending their own requests. Planning scratch (per-row drift anchors) lived in a session scratchpad only; regenerate anchors from `git show 7eab70e9:` sources.
- 2026-11-13: Implemented the pending 1.1.0 successor and deterministic generator, with 161 entries (123 replace, 33 defer, 5 withdraw). Candidate and PS10/PS11 patch verifiers pass; 21 tests cover matrix scenarios, exact process streams and live-global guard removal. Both-pin source checks preserve the 49-tool/2-resource/42-leaf sets and prove added model fields. Verification is recorded in [the Story 5.8 packet](evidence/story-5-8/verification.md). The candidate receipt supersedes A1 only upon exact-byte approval; no approval, delivery, enrollment, parity or retirement is asserted. Story status stays in-progress because exact-byte owner approval and separately authorized upstream label integration remain unsatisfied completion conditions.
- 2026-11-13: Build review 1 applied all 11 patch groups; the final 31-test suite, candidate verifier, label verifier and adopted AD-23 gate pass. Completion still fails with the exact pending-approval diagnostic. The final candidate SHA-256 is `54a6f61d4f0d83876d8113c7c9d8775dc73190ecdbd8a3beb34cda10946d6407`. No review deferrals were added; the approved K12 reconciliation remains open. The approved story's completion conditions take precedence over the build workflow's generic done/commit steps: status remains in-progress and no commit or delivery is authorized.

- 2026-11-13: The user replied "approve" to the exact candidate and required-role approval question, then separately "authorize" for publication and README-only label delivery. The approval receipt now records those words and the inherited repository-owner identity, without changing the approved candidate bytes. Pending-state test cases now use isolated copies, retaining their exact refusal streams and guard-removal controls after real approval and delivery. Both 31-test runs pass: current source and an isolated approved/integrated/done source view. Publication and integrated-label verification are the remaining delivery steps.

- 2026-11-13: Published the approved inventory/receipt at `f3c8f5f7c37f2a03287fc41ecf2e7ca8c5f49091` and delivered the exact README-only PS10/PS11 patch at Folders `db40bda8a107fcb03405e074810be16c0d47c85f`. Remote main revisions and exact artifact bytes were read back. Both real approved-completion verifiers pass. The approved candidate and authorities remain unchanged; the existing K12 reconciliation remains open. A focused follow-up review covers the lifecycle-test maintenance and delivery records since the previously reviewed implementation at `cab549c7b06fa4eef08e46cfcde038f62ea81fbf`; the original story baseline remains unchanged.

- 2026-11-13: Delivery follow-up review applied eight direct patch groups, rejected one finding and added no review deferrals. The final 36-test suite and retained synthetic-lifecycle proof both pass, as do both real default approved-completion entrypoints and the AD-23 adoption gate. The approved candidate remains SHA-256 `54a6f61d4f0d83876d8113c7c9d8775dc73190ecdbd8a3beb34cda10946d6407`. All story acceptance conditions are satisfied; spec status is done and sprint status is review per the build workflow. The separately recorded K12 catalog hold remains open for Epic 6.

- 2026-11-14: Applied all nine code-review patch entries without changing approved inventory, approval or label bytes. Historical Folders source now reads published ancestor `2236855ee181bdeed2a103537c66316a1612c792`, bound to recorded `src` tree `d0f81f0f00570c2d8ba1f34af2fcdf7bccb9d7e0`; the original object is checked when present. Route evidence reads the original McpCli baseline, and both mutation fences require `Required.Always`. Added real-graph publication/delivery refusal cases, integrated-label lifecycle refusals, absent-object and corruption controls. The 47-test suite, both real default completion gates and AD-23 adoption verification pass. Corrected the existing K12 ledger anchors/status and historical evidence wording; the three approved-byte deferrals remain in the existing ledger. Final retained checks are in `evidence/story-5-8/review-patches-20261114/commands.json`. No commit, push, enrollment, execution, parity or retirement was performed.

- 2026-11-14: Resumed build completed the nine requested review patches and five follow-up patch groups. Final verification passed all 50 tests, both real completion verifiers and the AD-23 gate, with exact-stream captures and complete executable-input hashes in [the final command manifest](evidence/story-5-8/review-final-20261114/commands.json). Matrix coverage and protected artifact bytes were audited. Two pre-existing approved-byte drift omissions were added to the versioned-successor ledger; three prior K12-successor defects remain there without duplicate entries. Spec is done and sprint tracking is review. Approved inventory, approval, labels, production code, dependencies and gitlinks remain unchanged. The frozen scope requires separate explicit commit authorization; no commit or push was performed.

- 2026-11-14: Implemented all ten code-review-pass-2 patch entries. Published-graph fixtures now read the committed register/approval and pin their temporary owner ref to the delivered label commit. Added exact-stream refusal/removal controls for the listed workflow, label and inventory guards, plus a fail-closed lifecycle snapshot comparison and negative control. The retained ordinary suite passed all 63 tests in 63.186 seconds; the fresh synthetic lifecycle proof passed all 63 in 63.013 seconds and computed that real protected inputs were unchanged. Both real completion verifiers, AD-23 and whitespace checks passed. Ledger anchors, review grouping, 23-file client/server/domain validation evidence, verification history and the complete eight-authority hash table are corrected. Exact commands, complete streams and executable-input hashes are in [the pass-2 command manifest](evidence/story-5-8/review-pass2-20261114/commands.json). Approved inventory, approval, label register, delivered labels, production, dependencies, census and gitlinks remain unchanged. The three pass-2 approved-byte deferrals remain in the existing K12-successor ledger. Spec/sprint transition follows the build workflow review; no commit or push was performed.

- 2026-11-14: Completed all ten pass-2 patch entries and four follow-up build-review patch groups. Final ordinary and synthetic-lifecycle suites each passed all 65 tests, including optimized child-mutation refusal, blank/malformed duplicate status detection and the real declaration-caller deletion control. Three focused checks also passed under a symlinked temporary directory. Both real completion gates, AD-23 and whitespace checks pass; evidence is retained in [the final pass-2 command manifest](evidence/story-5-8/review-pass2-final-20261114/commands.json). One new approved-byte omission (Q08 optional task context) is assigned to the K12 successor, and six existing deferrals were carried without duplicates. Spec is done and sprint tracking is review. Approved artifacts and frozen intent remain unchanged. No commit or push was performed.

- 2026-11-14: Implemented all eight code-review-pass-3 patch entries. New exact-stream refusal cases with removal controls cover the unknown approval decision, the unknown label-register state, the standalone integrated-state label trigger (copied-entrypoint deletion), each half of the published-bytes check at `inventoryRevision` and `origin/main`, and the eleven listed backstopped guard sites. The lifecycle proof now compares the fixture spec/sprint bytes after the child and writes its sidecars only after every check; all three negative lifecycle tests require an empty delivery folder. The six verifier/builder text reads decode UTF-8, and a new ASCII-locale (`-X utf8=0`, `LC_ALL=C`) entrypoint test protects them. Two tests use full SHAs, and the reproduction prerequisites list every parent commit the graph tests read. The ordinary and synthetic-lifecycle suites each passed all 75 tests. A review follow-up then added a corrupt-predecessor-object refusal, a completion-mode owner-drift report case and a post-child candidate check in the lifecycle proof, and rewrote the guard-removal helper to mutate only isolated copies: 27 of 27 mutations are detected at assertions, and real sources stay unchanged. Only the 8 tests covering those edits were rerun; the full 77-test suite is left to coordinator verification. Both real completion gates (also under the ASCII locale), AD-23, three symlinked-temp tests and whitespace pass. Exact commands, streams and executable-input hashes are in [the pass-3 command manifest](evidence/story-5-8/review-pass3-20261114/commands.json). No deferral was added; the three pass-3 defers remain in the ledger. Approved inventory, approval, label register, delivered labels, production, dependencies, census and gitlinks remain unchanged. Spec is done and sprint tracking is review. No commit or push was performed.

- 2026-11-14: The resumed pass-3 build review completed with all eight patch groups applied.
  - Parent final verification passed all 77 tests in both the ordinary and synthetic-lifecycle runs, with no skips.
  - Both real completion gates passed under the UTF-8 and ASCII locales, as did AD-23, five symlinked-temp tests, and the tracked and untracked whitespace checks.
  - The isolated-copy guard-removal report still detects 27 of 27 mutations against the current sources.
  - The evidence is in [the final pass-3 command manifest](evidence/story-5-8/review-pass3-final-20261114/commands.json), its closure audit and a clean secret-scan receipt.
  - One pre-existing approved-byte omission (the G3/G4 gate narrowing) was assigned to the K12 successor. The three pass-3 defers remain in the ledger.
  - Approved artifacts and the frozen intent are unchanged.
  - Spec is done and sprint tracking is review. The frozen scope requires separate explicit commit authorization, so no commit or push was performed.

## Spec Change Log

## Review Triage Log

### Build review 1 (2026-11-13)

All three independent layers completed before triage. Each finding below has its own verdict; shared fixes are grouped only after those verdicts. The review snapshot is `/tmp/mcpcli-story-5-8-5grc5k44.diff`.

| Finding | Verdict | Route | Evidence and decision |
| --- | --- | --- | --- |
| B1: absolute owner checkout prevents fresh-clone reproduction | low | reject | The new verifier uses the exact owner checkout already recorded and required by Story 5.7's immutable label register (`verify_labels.py:119`). This documentary packet is reproducible in its recorded workspace; adding checkout configuration for other machines is more than a direct correction and is unlikely to affect this bounded approval run. |
| B2: cumulative label diff rejects intervening source commits | medium | patch | `verify_labels.py:81` compares the delivery revision to the historical label base. A later source-only commit plus a README-only delivery therefore fails the stated delivery check; compare the delivery commit with its parent while retaining the exact README-byte check. |
| B3: omitted ownerFileId drift | medium | patch | The pinned generated-client diff adds optional `FileMutationRequest.ownerFileId` with owner-incarnation semantics alongside both fence fields. Its absence leaves the affected mutation rows' drift evidence incomplete; add the field, semantics, anchors and both-pin check. |
| B4: diagnostic Query heading asserts nonexistent types | low | patch | The heading says CLR type at the pin even for the seven undecorated diagnostic roadmap entries. Correct the heading directly without changing their defer/exclude outcomes. |
| B5: N03 repeats N04 renewal rationale | low | patch | The shared N03/N04 branch describes RenewWorkspaceLock for organization ACL baseline/grant/revoke. Give N03 its own rationale; its lack of a decorated replacement remains unchanged. |
| B6: JsonRequired checked anywhere in Command source | medium | patch | The guard only checks a file-wide substring; other required properties keep it true when the idempotency property's annotation is removed. Check that property's attributes and protect the check with the demonstrated corruption. |
| B7: inferred names do not prove actual client/target links | medium | patch | MCP targets derive from tool names and File CLI targets from leaf names. The report claims call-link verification, but neither detects a changed client call or upload-kind branch; check those existing call sites and add controls. |
| B8: hard-coded group discovery ignores root registrations | medium | patch | The pinned CliApplication registers the seven groups at lines 45–51, but discovery never reads those registrations. An additional registration is invisible to the claimed complete leaf-set check; validate the registered group set and reject unsupported registrations. |
| B9: duplicate JSON members bypass overwrite protection | medium | patch | Ordinary json.loads accepts an approved decision followed by pending, whereas the verifier rejects duplicate members. Apply duplicate rejection before generator writes and cover both protected state files. |
| B10: non-object JSON produces traceback | medium | patch (with E2) | Top-level lists in approval/labels and null/list repository values reach unchecked .get calls. Validate those demonstrated shapes and assert controlled failures through entrypoints. |
| E1: approval can race a running generator | low | reject | A concurrent external approval between the initial pending check and writes can race regeneration. No approval writer or concurrent workflow is part of this run; an update lock/transaction adds state and coordination for an unlikely documentary maintenance race, so the low finding is rejected under the workflow's complexity rule. |
| E2: null/list repository produces traceback | medium | patch (with B10) | The unchecked repository .get call raises AttributeError for both demonstrated values. This is the same malformed-document root cause as B10 and shares its fix. |
| V1: automatic done triggers lack protecting tests | medium | patch | The verification-gap reviewer removed both completion_requested helpers in memory and all 21 tests still passed. Cover spec and sprint done independently through both default verifier entrypoints, with guard-removal controls. |
| V2: Git ancestry calls lack protecting tests | medium | patch | The verification-gap reviewer removed both merge-base calls in memory and all six label tests still passed. Real temporary Git graphs must reject unmerged owner-label and inventory revisions with exact output assertions. |

The surviving findings form 11 small patch groups (B10/E2 share one). They were sent to the original implementation agent together and all were applied. The final full 31-test run and both verifiers pass, and approved-completion still rejects the pending receipt. No intent or specification change was required, and the frozen decisions remain untouched.

### Delivery follow-up review (2026-11-13)

All three independent layers completed before triage. The edge-case and verification-gap layers returned no findings; the verification-gap reviewer reran all 31 tests and both real approved-completion entrypoints successfully. The blind reviewer returned the nine findings below. The [retained review snapshot](evidence/story-5-8/delivery/review-followup.diff) covers delivery/lifecycle maintenance since the already-reviewed implementation at `cab549c7b06fa4eef08e46cfcde038f62ea81fbf`; the original story baseline remains unchanged.

| Finding | Verdict | Route | Evidence and decision |
| --- | --- | --- | --- |
| D1: synthetic lifecycle source is not a valid completed delivery fixture | false | reject | The proof tests that pending-state test fixtures remain independent of synthetic approved/integrated/done metadata; it does not claim the synthetic delivery passes the acceptance gate. `verification.md` explicitly states that this fixture is test evidence only and that real delivery comes from the separate published revision/blob/README checks. Both real approved-completion captures already pass, so the described false acceptance does not occur. |
| D2: extra integration observation fields are not validated | low | patch | `verify_labels.py` validates the delivery commit and commit byte hash, then independently checks its README bytes and ancestry. The two additional observational fields add no authority and can become misleading; remove them from `labels.json` and retain their observations in the bound delivery evidence. |
| D3: remote readbacks are claimed without retained query output | medium | patch | The readbacks were executed in the delivery orchestration, but their raw stdout was not retained. Capture post-publication `ls-remote` for both repositories and bind the observed revisions and exact published artifact comparisons in `delivery/integration.json`. |
| D4: lifecycle proof hardcodes its original checkout | low | patch | The retained helper would run against the original absolute checkout after copying the packet elsewhere. Derive its root directly from the saved helper's repository location; the recorded owner checkout remains governed by the existing immutable label chain. |
| D5: lifecycle proof writes global temporary filenames and retains temporary references | low | patch | The proof's `/tmp` sidecars are not relative to the retained packet and can be overwritten by another checkout. Write them beside the helper in its task-owned delivery directory and use relative sidecar references. No concurrent approval or locking workflow is added. |
| D6: lifecycle captures lack command/cwd/hash bindings | medium | patch | The pending stdout/stderr are retained, but have no companion command record; the synthetic lifecycle summary does not hash its logs. Bind both captures to their exact command, working directory, exit status and full stream SHA-256s, and retain the helper command for reproduction. |
| D7: test-only README observation rewrite applies to unrelated repositories | low | patch | Both observation wrappers match a command suffix without checking its repository. Restrict substitution to the registered Folders owner checkout and test owner substitution and unrelated-repository pass-through; source/approval/ancestry guards remain unchanged. |
| D8: count=1 prevents the fixture helper from detecting duplicate statuses | low | patch | Both fixture copies claim exactly-one status but cap `re.subn` at one match. Count all matching lines and refuse duplicate workflow status before accepting the modified fixture. |
| D9: sprint comment still presents delivered gates as pending | low | patch | The tracker comment was not yet updated during staged publication. Replace the stale pending statement with the real published completion state and move tracking to review when the build workflow finishes. |

Eight direct patch groups were accepted; one finding was rejected on the explicit fixture/acceptance distinction. No new review deferrals were added. The approved inventory and its authorities remain unchanged, and the existing K12 reconciliation remains open.

### Resumed build review (2026-11-14)

All three independent layers completed before triage. The edge-case layer returned no findings and independently passed the suite. The verification layer passed all 47 tests and both completion commands, then demonstrated an undetected caller-deletion mutation. The blind layer returned ten findings. The full review snapshot is `/tmp/mcpcli-story-5-8-7lmi9bve.diff`, against the preserved baseline `a92a2969db6903b8c6cca7e437446167e135ec9d`; this resumed implementation began at `ab05973f63388447984d9d21742f97700254acdb`.

| Finding | Verdict | Route | Evidence and decision |
| --- | --- | --- | --- |
| B1: missing receipts permit rebuilding an existing approved successor | medium | patch | The builder skips both state checks when their files are absent and derives a pending packet. Refuse missing receipts when the successor exists, with exact-stream/no-write tests; pristine initialization remains supported. |
| B2: SDK end-anchor tightening is absent from approved source drift | low | defer | The pinned client validators changed `$` to `\z`, while the approved inventory omits that tightening. This predates the resumed patches and changes approved documentary bytes; track the correction for the versioned successor, with affected-row analysis before any parity claim. |
| B3: redirect disabling is absent from approved source drift | low | defer | The pinned bearer handler explicitly sets `AllowAutoRedirect = false`, and MCP registration selects it. The approved transport paragraph omits that setting. Track this pre-existing approved-byte omission for the successor; no existing receipt or label is rewritten. |
| B4: mutation drift requiredness and ownerFileId reachability | low | defer | carried: the same approved-byte defect and user decision remain unchanged; already tracked (`deferred-work.md:1064`). No duplicate ledger entry. |
| B5: K01 rationale incorrectly describes its adopted outcome | low | defer | carried: the approved rows and the prior K12-successor decision remain unchanged; already tracked (`deferred-work.md:1054`). No duplicate ledger entry. |
| B6: deferred K12 rows present replace-style routes | low | defer | carried: the same approved replacement-column wording remains reserved for the K12 successor; already tracked (`deferred-work.md:1059`). No duplicate ledger entry. |
| B7: Code Map omits Q17 from its K06 list | low | reject | The implementation and approved diagnostic scope correctly include all seven entries. This finding proposes only editing this build's spec, which the review workflow explicitly rejects; it demonstrates no verifier defect. |
| B8: historical delivery section presents its old workflow state as current | low | patch | Its heading is at the same level as the historical heading, so the old done/review sentence is ambiguous during resumed review. Date and label that section explicitly as historical. |
| B9: absolute owner-checkout reproduction prerequisites are implicit | low | patch | The earlier decision rejecting a configurable-checkout feature remains in force. A direct documentation correction can state the existing owner path and required local objects/refs without changing the immutable register or verifier surface. |
| B10: new command manifest omits executable helper dependencies | low | patch | The captured input list has only four Python files, while the suite imports the lifecycle helper and Story 5.2/5.7 code. Bind those unchanged executable inputs, and include the full set in final verification. |
| V1: source-drift checks can be disconnected from the real owner entrypoint | medium | patch | Pre-verified: deleting `check_source_drift(root,surface)` leaves all 47 tests passing and accepts a copied builder with an invalid recorded tree. Add a real copied-entrypoint corruption test and a caller-deletion control with exact output assertions. |

The five direct patch groups were applied by the original implementation agent and verified by the parent: all 50 tests passed in 46.608 seconds, both real completion entrypoints passed, and AD-23 and whitespace checks passed. Two newly identified omissions in already-approved bytes are recorded under this source spec in the ledger; the three existing K12-successor corrections are carried without duplication. The approved inventory, receipts and delivered labels remain immutable.

### Resumed pass-2 build review (2026-11-14)

All three independent layers completed before triage. The edge-case layer returned no findings. The blind layer returned ten findings; the verification layer demonstrated that deleting the declaration-check invocation leaves all 63 tests passing and permits a corrupted module declaration. The review snapshot is `/tmp/mcpcli-story-5-8-dshza010.diff`, against the preserved baseline `a92a2969db6903b8c6cca7e437446167e135ec9d`; this resumed implementation began at `7fa3df6a6b827f85fba6e12ec22c5efa08034ac8`.

| Finding | Verdict | Route | Evidence and decision |
| --- | --- | --- | --- |
| B1: optimized lifecycle helper can lose its synthetic-state checks | medium | patch | The remaining setup and post-child assertions disappear under Python optimization, so a child that changes the copied label state can leave a successful integrated-fixture claim. Replace the demonstrated checks with explicit failures and test child corruption without a success summary. |
| B2: duplicate status keys with blank values escape counting | medium | patch | `completion_requested` counts only values matching its word pattern; a second empty status key is therefore invisible. Count every exact key occurrence independently of value parsing and extend both copied-entrypoint deletion controls. A new policy validating every sole workflow-state value is unnecessary to correct this duplicate-key defect. |
| B3: V03 omits Q08 optional task context | low | defer | The pinned `GetFolderIndexingStatus` declares optional `TaskId`, while V03's target list omits Q08 and the legacy MCP/CLI adapters send null. This pre-existing approved-byte omission must be accounted for in the K12 successor, including affected M22/L38/Q08/V03 rows and the independent authority treatment. Ledger grep found no matching entry before append. |
| B4: Python reproduction prerequisite omits the minimum version | low | patch | The helpers use `Path.is_relative_to`, so the documented prerequisite must state Python 3.9 or newer. This is a direct documentation correction. |
| B5: K01 rows inherit a contradictory K12 rationale | low | defer | carried: the same approved-byte defect and owner decision remain unchanged; already tracked (`deferred-work.md:1054`). No duplicate entry or approved-byte edit. |
| B6: deferred K12 rows still present affirmative replacement routes | low | defer | carried: the same blocked-candidate wording remains reserved for the K12 successor; already tracked (`deferred-work.md:1059`). No duplicate entry. |
| B7: mutation drift omits fence requiredness and misattributes ownerFileId | low | defer | carried: the same approved-byte defect and successor decision remain unchanged; already tracked (`deferred-work.md:1064`). No duplicate entry. |
| B8: semantic-retention claims exceed name-level drift evidence | medium | defer | carried: the per-surface semantic drift audit remains assigned to the K12 successor; already tracked (`deferred-work.md:1085`). No duplicate entry. |
| B9: approved inventory retains its pending self-description | low | defer | carried: approved metadata and anchors remain immutable and the effective receipt is linked; the successor correction is already tracked (`deferred-work.md:1090`). No duplicate entry. |
| B10: collective story suffix misattributes G1/G2 | low | defer | carried: each gap's owning story will be corrected in the approved successor; already tracked (`deferred-work.md:1095`). No duplicate entry. |
| V1: declaration checks can be disconnected from the owner entrypoint | medium | patch | Pre-verified: deleting `check_declarations(root,old,new,decl,surface)` leaves all 63 tests passing and accepts a pinned module changed from String to Ulid. Add a copied-entrypoint corruption test and caller-deletion control with exact streams. |

The original implementation agent applied all four patch groups and passed seven focused tests. Parent verification then passed all 65 tests in both ordinary and synthetic-lifecycle runs, plus three focused tests under a symlinked temporary directory, both real completion entrypoints, AD-23 and whitespace checks. The final [command manifest](evidence/story-5-8/review-pass2-final-20261114/commands.json) binds the executed sources and exact streams. One new approved-byte omission was assigned to the K12 successor; six existing deferrals were carried without duplicate ledger entries.

### Resumed pass-3 build review (2026-11-14)

All three independent layers completed before triage. The review snapshot is the full diff against the preserved baseline `a92a2969db6903b8c6cca7e437446167e135ec9d`, including the untracked pass-3 packet (16,722 lines). This resumed implementation began at `733fc7114a572758c67a0fdb2e55e128c1c3044b`. The parent reran all 75 tests, both real completion entrypoints, AD-23 and `git diff --check`, and all passed. A `--no-index --check` of every untracked file was also clean.

| Finding | Verdict | Route | Evidence and decision |
| --- | --- | --- | --- |
| V1: an unreadable historical predecessor object is treated as absent | medium | patch | Pre-verified. Deleting `require(historical.returncode in {0,1}, …)` (`verify_amendment.py:199`) leaves every test passing. A corrupt `e2252f29` object makes `rev-parse` exit 128, which then skips the tree binding and passes. Add an exit-128 `subprocess.run` fake with the exact `cannot inspect historical predecessor object` refusal and a removal control. |
| V2: completion-mode owner drift reporting is untested | medium | patch | Pre-verified. `test_current_owner_drift_is_report_only` covers only the pending arm. Every completion fixture pins `origin/main` to the delivered README. The real packet always runs in completion mode, so changing or hardening `verify_labels.py:97-98` goes unnoticed. Add an `existing_graph_fixture` variant whose owner `origin/main:README.md` differs. Assert `(0, integrated PASS, 'reported: … differs from delivered candidate\n')`. |
| E2: guard-removal helper edits real sources in place and survives signals unrestored | medium | patch | Confirmed at `review-pass3-20261114/guard-removal.py:59-81`. `finally` does not run on SIGTERM/SIGHUP/SIGKILL, although the docstring promises restoration "also on interruption". A leftover mutation is a deleted guard, which every default gate still passes. Concurrent sessions in this workspace have committed working-tree edits mid-task. Run the mutations and child suites inside a `workspace_view(pending=False)` copy, as `delivery/lifecycle-proof.py` does, so real sources are never written. |
| B3: helper mutates tracked verifier sources and records no overlap window | medium | patch (with E2) | Same in-place-mutation defect as E2, with the same fix. |
| E1: helper counts any nonzero exit as a detected mutation | low | patch | `guard-removal.py:75` sets `detected` to `returncode != 0`. On Python 3.12+ a `-k` filter that matches nothing exits 5, and an import or `setUpClass` error exits 1. The retained report is sound, because all 21 runs show `FAILED (failures=…)` with assertion lines. A rerun after a test rename would still misreport. Require at least one test run, a `failures=` count, no `errors=`, and a recorded assertion line. |
| B2: helper detection criterion and interpreter-dependent exit | low | patch (with E1) | Same detection-criterion defect as E1. |
| B2 (second claim): "each encoding fix reverted" overstates the helper | low | patch | `verification.md:91` says each encoding fix was reverted. The helper reverts `:265` and `build_candidate.py:512` alone, but `verify_amendment.py:285`, `:286` and `build_candidate.py:357` only together (`guard-removal.py:33-40`). Add the individual mutations so the claim holds. The V layer showed each read is individually protected. |
| E3: lifecycle proof does not re-check the fixture candidate after the child | low | patch | `delivery/lifecycle-proof.py:53-54` compares `B.NEW` only before the child. The post-child checks (`:62-66`) cover receipt, labels and workflow but not the candidate. The summary still reports `candidateSha256`. Add `B.NEW` to the post-child comparison, with a child-mutation test asserting refusal and an empty delivery folder. |
| B5: candidate not re-checked after the child | low | patch (with E3) | Same defect as E3. |
| V other: the suite and lifecycle proof need a UTF-8 locale | low | patch | Verified by the V and B layers. Under `LC_ALL=C -X utf8=0`, `setUpClass` (`test_verify_amendment.py:333-334`) and `workflow_status` (`:69-73`) raise `UnicodeDecodeError`. The pass-3 fix and its child-process test cover only the entrypoint gates. `verification.md:21` does not state the requirement. Smallest fix: state in the prerequisites that the unittest suite and lifecycle proof require a UTF-8 locale, while both verifier entrypoints also run under an ASCII locale. |
| B1: suite and lifecycle proof fail under a non-UTF-8 locale | low | patch (with V other) | Same root cause and fix as V other. |
| E6: `workflow_status` uses the locale codec | low | patch (with V other) | Same root cause and fix as V other. |
| B10: closure audit does not cover the final manifest | low | patch | `review-pass3-20261114/audit.json` records `capturedCommandStreamsVerified: 10`, while `commands.json` holds 13 commands. The three after-closure reruns are unaudited. Recompute the audit after the last command, over every captured stream. |
| B4: G3 and G4 also lost 1.0.0 or 5.12 gate requirements | medium | defer | Confirmed in approved bytes. 1.1.0 G4 (`folders-migration-inventory-v1.1.0.md:91`) drops 1.0.0's "McpCli v1 queries carry no extensions/freshness arguments; a Contracts payload works only if an approved handler translates its semantics" (`folders-migration-inventory-v1.md:90`). 1.1.0 G3 (`:90`) omits the 5.12 admission rules (`declarations.md:179-182`). This predates these patches; route it to the K12 successor in a new ledger entry. |
| E4: lifecycle summary records the default helper command, not the actual invocation | low | reject | Each packet's `commands.json` records the exact `main(delivery=…)` invocation that produced its summary. The summary's `helper` field documents the default entrypoint. A replay that overwrites `delivery/` is the settled pass-1 E8/pass-2 E3 point. |
| B6: retained summaries name a command that did not produce them | low | reject | Same as E4. |
| E5: the child suite has no timeout | low | reject | An unlikely stall in an interactively run helper. A timeout adds a parameter and a failure branch, and the recorded runs bound their outer process. |
| E7: builder delimiter splits scan the whole file when a delimiter is absent at a new pin | false | reject | Both pins are immutable, and the delimiters exist at them (the pinned client-link checks pass and their changed-source tests detect altered links). Hardening for a new pin is the pass-3 builder-guard deferral already in the ledger. |
| E10: drift-evidence anchors take the first file match at a new pin | false | reject | At the immutable pins every cited anchor resolves to the named property, and the approved bytes bind the builder output. Re-pin hardening is the same existing deferral. |
| E8: register rows with extra fields or relocated identical artifacts pass completion | low | reject | The integrated register is published at `c3bd5b9` and immutable. Every consumed field is compared with the builder output and the owner graph, and relocated paths must stay inside the repository with identical bytes. Extra fields carry no authority (pass-2 V5). |
| E9: missing register keys produce bare `KeyError` refusals | low | reject | They fail loudly with exit 1 on damaged immutable inputs. Shape guards for each key add complexity. The missing-path backstop `FAIL: 'path'` is already pinned by test. |
| B7: list/object decision or state values produce `TypeError` text | low | reject | Same reason as E9. `read_json` rejects non-object documents, and these values occur only in a damaged receipt or register. |
| E11: an exception after sidecar writes leaves new sidecars beside a stale summary | false | reject | The cited raise paths are unreachable from the shown callers. `root` defaults to `SCRIPT.parents[5]`, so `SCRIPT.relative_to(root)` cannot raise, and no caller passes another root. A failed summary write is the same disk failure that would interrupt the sidecar writes. |
| E12: pass-3 review row says "Thirteen" backstopped guards but lists 11 | low | reject | The row miscounts: it names 11 sites, and `verification.md` correctly says eleven. Fixing it means editing this build's spec, which this review rejects. Code review pass 4 can correct its own record. |
| B8: the spec's Verification section describes the pending lifecycle | low | reject | Its fix edits this build's spec. |
| B9: whitespace gate skipped the untracked pass-3 packet | false | reject | `git diff --no-index --check` over every untracked file reports nothing, so no whitespace defect escaped. Final verification will include the new files. |
| B11: the root K12 ledger entry does not index the folded-in entries | low | reject | Every folded entry names the "K12 reconciliation successor" under a spec-5-8 heading, and Story 5.11 reconciles every intra-epic deferral. Editing the existing entry would add a duplicated index. |

The original implementation agent applied all eight patch groups and passed the eight tests covering the edited files. It also reran the isolated-copy guard-removal helper, which detected 27 of 27 mutations with the real sources unchanged. Parent verification then passed:
- all 77 tests in both the ordinary and synthetic-lifecycle runs, with no skips;
- both real completion entrypoints under the UTF-8 and ASCII locales, and AD-23;
- five focused tests under a symlinked temporary directory;
- `git diff --check` and an untracked-file whitespace check.

The final [command manifest](evidence/story-5-8/review-pass3-final-20261114/commands.json) and [closure audit](evidence/story-5-8/review-pass3-final-20261114/audit.json) bind the executed sources, the exact streams, matrix coverage, the protected bytes and the frozen intent. One pre-existing approved-byte omission (G3/G4) was assigned to the K12 successor under a new ledger heading.
