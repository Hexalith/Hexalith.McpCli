---
title: '5.8 Refresh and re-disposition the Folders inventory'
type: 'chore'
created: '2026-11-13'
status: 'ready-for-dev'
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
- [ ] `A/folders-migration-inventory-v1.1.0.md` and `.gitattributes` (`-text`): write the successor from the derivation rules below. Corrected premises go in G/V cells and the source section. A2 stays pending.
- [ ] `E/build_candidate.py`: generate it deterministically from the 1.0.0 bytes, `git show 7eab70e9:` sources and the 5.12 record. Refuse to overwrite an approved packet.
- [ ] `E/{verify_amendment.py,test_verify_amendment.py}` cover:
  - candidate and approved-completion modes;
  - 161-entry accounting against the AD-23 map;
  - anchors and drift;
  - decorated type, wire and route per `replace`;
  - include⇔replace, gap/owner and K12 handling;
  - G-story status, the hash chain and roles.
  - Test every matrix row and disposition branch with guard-removal controls, the process exit and both streams.
- [ ] `E/{approval.json,labels.json,verify_labels.py,upstream/folders/}`: a pending receipt bound to the 1.0.0/1.1.0 hashes and their authorities, and a README-only PS10/PS11 citation patch whose register is chained to the 5.7 register.
- [ ] `A/deferred-work.md` (grep first), `E/verification.md`, the secret-scan receipt, this spec and `A/sprint-status.yaml`: record only the supported state.

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

## Spec Change Log

## Review Triage Log
