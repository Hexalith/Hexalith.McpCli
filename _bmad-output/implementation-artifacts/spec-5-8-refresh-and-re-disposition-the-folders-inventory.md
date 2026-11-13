---
title: '5.8 Refresh and re-disposition the Folders inventory'
type: 'chore'
created: '2026-11-13'
status: 'done'
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
