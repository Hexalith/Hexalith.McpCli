---
title: '5.10 Refresh and re-disposition ChatBot and Memories inventories'
type: 'chore'
created: '2026-11-16'
status: 'in-review'
baseline_commit: '979e1e126c6d7010997f4f20b2bb3defae81333e'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-5-context.md'
story_key: '5-10-refresh-and-re-disposition-chatbot-and-memories-inventories'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** ChatBot 1.0.0 (pin `acc93459`, unpublished, not an ancestor of the gitlink) and Memories 1.0.0 (pin `f6b60d5a`) are stale session-scope inventories with every row `defer / exclude` and `external_maintainer_approval: unasserted`. Memories omits the PS14 `MigrateEmbeddingVectors` operator CLI, and AD-23 has since been adopted.

**Approach:** Produce additive successors ChatBot 1.1.0 and Memories 1.1.0, re-pinned to the HEAD gitlinks at approval (currently ChatBot `6a4ca07b18e9b58500dc79dfede1f308da36c828`, Memories `9d87500eaf4c39ce0cec0cb3a03e5dd62c167106`; both published). Re-disposition every entry under the adopted AD-23 class map, inventory the four PS14 modes as added rows, gate both with a story verifier, then obtain exact-byte owner approval and integrate the PS06/PS07/PS12/PS13/PS14 label citations.

## Boundaries & Constraints

**Always:**
- Account for every predecessor entry exactly once (ChatBot M01–M12, L01–L12, V01–V15, X01–X04, G1–G5; Memories M01–M04, L01–L14, S01–S04, V01–V17, X01–X06, G1–G6), with anchors at the new pin and a drift status: "unchanged", or the change.
- Dispositions follow the row's AD-23 class (restriction precedence applies). Neither module decorates any type at its pin, so no row is `replace`/`include`:
  - K01/K03/K04/K05/K06 → `defer`, naming the module Contracts/handler/admission gap and the module owner;
  - K09/K10 → `defer` with the AD-23 class gap and owner;
  - K07/K12/K15 → `withdraw` with owner rationale, replacement experience and accepted loss; K12 adds confidential-UI coverage evidence as a retirement prerequisite;
  - PS14 modes (K14) → `withdraw` from migration scope, retained owner-held tooling, never counted retired.
- PS14 rows record each mode's effect, security class, `--tenant` rule, `--yes`/interactive confirmation and non-interactive refusal, direct Redis/Dapr access, exit codes and absent user/tenant authority.
- Memories rows that depend on forwarded per-user identity stay `defer` and record the HTTP release as necessary but insufficient, alongside tenant and user authorization, administrative scope, semantic behavior and release/rollback evidence.
- ChatBot governed workflows: plain Commands, REST DTOs and OpenAPI never count as decorated Gateway readiness; task and correlation context travel only as Payload properties, `actorProperty` or allowed Envelope extensions.
- The approval replaces `unasserted` with the roles it covers under the single-maintainer model and supersedes A1.
- Keep the evidence packet proportionate: one generator, one candidate verifier, one label verifier and their tests.

**Never:**
- Rewrite ChatBot/Memories 1.0.0, AD-23, technical 1.0.3, earlier receipts or label registers, or anything in `references/`.
- Change enrollment, production code, dependencies, census, gitlinks or the AI.Tools plan (Story 5.11 indexes the successors).
- Enroll, publish, execute, or claim parity or retirement; convert legacy formats silently.
- Commit or push without explicit authorization.

**Decisions (2026-11-16):**
- **Losses: "Accept all".** The owner accepts the loss for every withdrawal-class row, each becoming `withdraw / exclude`:
  - ChatBot: V12 (K15); X03 (K07; no resources/prompts exist); V14, X01, X02 (K12; unsupported erasure/key-rotation variants stay absent).
  - Memories: L02, L06, S01–S04, V10, V16, V17, X06 (K15); L10, V09, V14, V15, X02, X03 (K12; they move to the confidential UI, with UI coverage evidence before retirement).
- **Technical successor: "Re-route to 5.11".** No technical-tools successor in this story. Update `deferred-work.md:1048` and `:1147` to name Story 5.11 (with the Admin successor) as the delivery vehicle.
- **Spec size: "Keep full spec".**

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Complete candidates | Both successors + pins + AD-23 map + predecessors | Verifier passes; receipt stays pending | N/A |
| Invented readiness | Any `replace`/`include`, or a row citing a plain Command/REST DTO as readiness | Reject, naming `module:id` | nonzero exit, exact stderr |
| Class drift | Disposition contradicts the AD-23 class; `withdraw` without loss; `defer` without gap/owner | Reject, naming `module:id` and class | nonzero exit |
| Damaged accounting | Missing/duplicate ID, unresolvable anchor, missing drift, PS14 row missing a required field, identity-dependent row without the HTTP-release prerequisite | Reject with an actionable diagnostic | nonzero exit |
| Completion without approval or labels | Pending receipt or unintegrated label | Completion mode fails | nonzero exit |

</frozen-after-approval>

## Code Map

`A` = `_bmad-output/implementation-artifacts`, `E` = `A/evidence`, `C`/`M` = `references/Hexalith.{ChatBot,Memories}` read through `git show <pin>:` only.

**Predecessors and authority**
- `A/chatbot-migration-inventory-v1.md` (sha `3dccbe0f…`), `A/memories-migration-inventory-v1.md` (sha `489af91e…`); `.gitattributes:117-118` (`-text`).
- AD-23 `…/AD-23-non-gateway-capability-classes.md`: precedence `:38-45`, classes `:70-83`, ChatBot V10 `:95-108`, K12 `:178-188`, K14 `:215-226`, deferral owners `:232-233`, outcome rules `:246-252`; policy rowClasses for both inventories in the verifier-policy block. Adoption receipt `E/story-5-2/approval.json` (`verify_class_map.py` exits 0).
- Technical 1.0.3 PS06/PS07/PS12/PS13/PS14 `:143-144`, `:149-151`, G3 `:187`. AI.Tools plan 1.2.0: K14 `:34`, ChatBot/Memories `:59-60`, retirement `:115-125`.
- Spec 4.4 human walkthrough `A/spec-4-4-…md:152-185` (Envelope tenant/correlation, Payload task provenance, no Query extensions, keep module admission).

**ChatBot at `6a4ca07b`** (equals owner `origin/main`)
- Unchanged counts: 12 tools (`Mcp/ChatBotMcpTools.cs`, `Mcp/Program.cs:42-43`), 12 leaves (`Cli/ChatBotCliCommands.cs:58-63`); no resources/prompts; no `[Hexalith*]` decoration; Contracts csproj byte-identical.
- Old pin: `acc93459` differs from published merge-base `839aee31` only by deleting `.mcp.json` (same `src` tree); reuse 5.8's `OLD_SOURCE_PIN`/`OLD_SOURCE_TREE` check.
- Drift (162 of 199 anchors identical):
  - V10: formatters now show `OperationId`, then TaskId, then CommandId (`Mcp/ChatBotMcpResultFormatter.cs:28-30`, `Cli/ChatBotCliOutputFormatter.cs:24-26`); server `OperationId = CommandId` (`Server/Gateway/CommandGateway.cs:120`); owner spec `spec-1-5-…:24`, `:87` (in review).
  - OpenAPI: status/audit IDs CommandId-only (M11/M12/L11/L12); writes gain 422/409/503 fail-closed (writes, V11); transitions drop `actorId` (M11/L11/V12).
  - V08 concurrency converter is stricter; V11 has three new message codes; `CommandGateway` adds admission-evidence validation.
  - Shifts: `AcceptedCommandDispatcher.cs` −7/−36; compatibility endpoint `:230→:223`; query handlers +4; MCP formatter +3; CLI formatter +3; `README.md:67→:78`, `:81→:92`.
- Planning: McpCli target `epics.md:30`; Epic 5 stories backlog (`sprint-status.yaml:102-112`); no decorated-Contracts story.
- Labels PS12/PS13 at `README.md:181-182` ("ChatBot inventory gates"; cite technical 1.0.3 and ChatBot 1.0.0 at McpCli `c70ca978`).

**Memories at `9d87500e`** (ancestor of owner `origin/main` `e4b2b08e`, whose 3 extra commits touch no surface)
- Unchanged counts: 4 tools (`Mcp/McpCompositionRoot.cs:91`, `:94-97`), 14 leaves + 4 stubs (`Cli/Commands/RootCommandFactory.cs:94`); `Mcp/Tools/` and `Cli/Commands/` byte-identical; no decoration; Contracts csproj unchanged.
- Drift:
  - JWT `ValidAlgorithms` (`Mcp/McpCompositionRoot.cs:46-55`, later lines +10; `ValidateMcpAuthenticationOptions.cs:63`; V01/V02/V15).
  - Ingest admission fence 409 (`Server/Endpoints/IngestionEndpoints.cs:114`; M02/L06/V06); `SOURCE_PUBLICATION_CHANGED` (`SearchEndpoints.cs:978`, `GraphEndpoints.cs:166`; M01/M03/L03).
  - Gateway composed as "workload authority without forwarding user credentials" (`Server/Hosting/MemoriesServerServiceCollectionExtensions.cs:643-660`; G2/G3/V08). EventStore csproj now references EventStore.Contracts (`:33`/`:40`).
  - CLI error catalog adds 8 codes (V17); quickstart requires SDK 11.0.100 (L06/V10).
  - New client methods with no CLI/MCP caller (`Client/MemoriesClient.cs:226`, `:273`, `:492`; X06/V16), plus line shifts.
- PS14 (unchanged since `f6b60d5a`):
  - Modes `tools/MigrateEmbeddingVectors/Program.cs:333-336` (exactly one; else exit 2); options `:256-327`; confirmation `:45`, `:47-61`; Redis `:143`, `:223`; Dapr `:142-150`, `:224` (no API token in code).
  - Service `src/Hexalith.Memories.Server/Migration/EmbeddingVectorMigrationService.cs`: `--tenant` required `:98-102`, refusal `:104-107`, dry-run `:149-195`, live `:197-312`, rollback `:314-360`, abort `:362-420`.
  - Exits `EmbeddingMigrationExitCodes.cs:12-21`; runbook `docs/operations/embedding-providers.md:205-209`.
- Planning: Epic 32 registration hold pending Gateway operations "and the per-user identity path" (`epics.md:914`); R1 unresolved (`implementation-readiness.md:43`).
- Labels PS06/PS07/PS14 at `README.md:134-136`.

**Reuse**
- `E/story-5-9/{build_candidate.py,verify_amendment.py,test_verify_amendment.py,verify_labels.py}`: copy and adapt. Widen `parse()`'s ID regex (`build_candidate.py:162`) and section map for S/X rows; model added rows on `class_entries` (`:175`); drop the FK, Projects-package and paging logic.
- `check_approval`, `check_delivery`, exact-word `approve`/`authorize` guards, and approval-race rechecks are generic.
- Labels: chain to `E/story-5-9/labels.json`, with prior rows from `E/story-5-7/labels.json:328,340,400,412,424`.

## Tasks & Acceptance

**Execution:**
- [x] Precondition: `git fetch`; confirm `main` contains `origin/main` and the HEAD gitlinks equal the approval pins. If the gitlinks moved or a rebase conflicts, HALT.
- [x] `A/chatbot-migration-inventory-v1.1.0.md`, `A/memories-migration-inventory-v1.1.0.md`, `.gitattributes` (`-text`): write successors following Design Notes; approval pending.
- [x] `E/story-5-10/build_candidate.py`: generate both deterministically from predecessor bytes, `git show <pin>:` sources and the AD-23 map; refuse to overwrite an approved packet.
- [x] `E/story-5-10/{verify_amendment.py,test_verify_amendment.py}`: candidate and approved-completion modes, every matrix row, guard-removal controls, exit code and both streams.
- [x] `E/story-5-10/{approval.json,labels.json,verify_labels.py,upstream/{chatbot,memories}/}`: pending receipt bound to predecessor/successor hashes and authorities; README-only label patches citing the successors, changing gate text only where an amendment changes the gate (PS14's four-mode inventory obligation).
- [x] `A/deferred-work.md` (grep first: `:682` ChatBot partial resolution; `:1048`/`:1147` re-routed to Story 5.11), `E/story-5-10/verification.md`, secret-scan receipt, this spec, `A/sprint-status.yaml`: record only the supported state.

**Acceptance Criteria:**
- Given the candidates, when the verifier runs, then every entry passes and all protected predecessor and authority bytes are unchanged.
- Given exact-byte owner approval and separate delivery authorization, when completion runs, then the receipts name the covered roles, both owner READMEs on `origin/main` cite the successors, and nothing is enrolled, executed or retired.

### Review Findings

Code review pass 1, 2026-11-16. Scope: deliverables `979e1e1..008d95c`, 17 files and 3,339 lines. The scope covers both successors, the four scripts, approval.json, labels.json, the six upstream patch files, verification.md, and the `.gitattributes` and ledger hunks. All four layers returned and none failed.

The 50 raw findings resolve to 12 decision-needed entries, 4 patches, 0 deferrals and 21 rejections. Baseline at HEAD `119a4b5`: both default verifiers exit 0, both completion modes exit 1 on unintegrated labels, and all 26 tests pass in 200.6 s.

D1 covers the eleven entries in approved inventory bytes, or in authorization-bound patch bytes or their generator and verifier. D2 covers verifier durability.

Decisions resolved 2026-11-16. D1 ("Fold into next successor") turns D1a–D1k into one deferral at `deferred-work.md:1191`. D2 ("HEAD checks only on regen") becomes a patch. Totals now: 0 decision-needed, 5 patches, 11 deferrals, 21 rejections.

- [x] [Review][Defer] D1a Successor drops predecessor obligations while claiming legacy columns are preserved — The notation (`chatbot-migration-inventory-v1.1.0.md:37`, `memories-migration-inventory-v1.1.0.md:37`) says legacy columns preserve scope, but the generator breaks that: — deferred: user chose "Fold into next successor" (approved and authorized bytes are immutable; corrections need a successor with exact-byte approval and a relabel) — `deferred-work.md:1191`
  - It overwrites the legacy G-row prerequisite cells and ChatBot V10's handoff cell.
  - It omits ChatBot 1.0.0's "Proposed generic context handoff" section (`chatbot-migration-inventory-v1.md:129-155`).
  - Lost from the successor:
    - ChatBot G2's status-handle decisions.
    - V10's rule not to use caller taskId as ownership proof or add polling/event streaming.
    - Memories G1's payload/envelope separation and annotations.
    - Memories G3's "do not add module-specific adapters to McpCli".
    - Memories G4's diagnostics/streams/import-export/consent/erasure/wizard decision list.
    - The six-row context mapping: tenant selector not forwarded, business vs submission correlation, taskIntentId not a ULID, StateOwnerAggregateId.
  - Medium. [E2, B4, B5; B5's Envelope-correlation sub-point is rejected because CONTEXT_GATE wording is the spec's Always rule.]
- [x] [Review][Defer] D1b Amendment owner is a generic module owner on every G row — `build_candidate.py:185` `owner()` writes "<Module> owning and Contracts/handler/admission/security maintainers" on every G row, while the legacy Owner column still names the original owners. Reassigned: — deferred: user chose "Fold into next successor" (approved and authorized bytes are immutable; corrections need a successor with exact-byte approval and a relabel) — `deferred-work.md:1191`
  - ChatBot G2 (EventStore) and G4 (McpCli closure/Catalog).
  - Memories G2 (Platform/Gateway), G4 (architecture/product, operations/security), G5 (release + McpCli) and G6.
  - Withdrawal rows also name Contracts/handler maintainers although they have no Contracts gap.
  - Medium. [A5, B2]
- [x] [Review][Defer] D1c Hand-authored drift misses observed pin changes: — deferred: user chose "Fold into next successor" (approved and authorized bytes are immutable; corrections need a successor with exact-byte approval and a relabel) — `deferred-work.md:1191`
  - T01–T04 say "source unchanged since the old pin". But `RedisNaturalLanguageNamespaceMigrator.cs` changed between `f6b60d5a` and `9d87500e` (+55/−24, fenced atomic per-unit migration). The cited `RedisEmbeddingMigrationStore.cs:172` calls it.
  - M11/L11 omit the removal of `actorId` from `CommandOperationTransition`, which is the schema of `lastTransition` in status responses.
  - L06 cites `IngestionEndpoints.cs:114`, but its drift names only the SDK prerequisite.
  - Both headers say "the Contracts project is unchanged", but 7 ChatBot and 8 Memories Contracts source files changed; only the csproj files are identical.
  - Medium. [E4, A3, A4, E13]
- [x] [Review][Defer] D1d Predecessor anchors drop silently; Memories V08 lost `IndexGraphActivity.cs:119` — `build_candidate.py:286-298` keeps only difflib-equal lines. The statement still exists at `:146`, and no check notices the drop. Medium. [E3, V2, V-o2] — deferred: user chose "Fold into next successor" (approved and authorized bytes are immutable; corrections need a successor with exact-byte approval and a relabel) — `deferred-work.md:1191`
- [x] [Review][Defer] D1e Approved 1.1.0 bytes still describe themselves as pending — The bytes carry `status: pending` (`:3`), "It is pending." (`:22`), and ChatBot G1 (`:114`) / Memories G6 (`:115`) say "pending now" and "currently pending". `verify_amendment.py:50` requires the pending status. This is the defect at `deferred-work.md:1048`, but that entry covers only Admin 1.0.2 and technical 1.0.3. Medium. [E5, B1, V-o1] — deferred: user chose "Fold into next successor" (approved and authorized bytes are immutable; corrections need a successor with exact-byte approval and a relabel) — `deferred-work.md:1191`
- [x] [Review][Defer] D1f Verifier certifies content against the generator's own output — `verify_amendment.py:85-92` compares PS14 fields, replacement, rationale, owner and drift to `B.*()` output, and `:104` does the same for evidence. D1b–D1d therefore pass by construction, and any correct independent check would fail on the approved bytes. Medium. [B9] — deferred: user chose "Fold into next successor" (approved and authorized bytes are immutable; corrections need a successor with exact-byte approval and a relabel) — `deferred-work.md:1191`
- [x] [Review][Defer] D1g Write-execution boilerplate is applied to unrelated G rows — `WRITES` (`build_candidate.py:58`) includes G2–G5: — deferred: user chose "Fold into next successor" (approved and authorized bytes are immutable; corrections need a successor with exact-byte approval and a relabel) — `deferred-work.md:1191`
  - ChatBot G4/G5 drift reads "changed: Retained write/provider/dispatcher code is not currently executable…", and their drift cells end with "..".
  - CONTEXT_GATE appears in G1, and the HTTP gate in Memories G1/G4/G5.
  - Low. [A6, B3]
- [x] [Review][Defer] D1h PS14 direct-access cells are imprecise — At the pin, `Program.cs:142` builds `DaprClient` without the `--dapr-http` value; only the actor proxy (`:146`) uses it. The silent `localhost:6379` and `http://localhost:3500` fallbacks (`:223-224`) and the SDK-default token and secret paths are not recorded. Low. [B8] — deferred: user chose "Fold into next successor" (approved and authorized bytes are immutable; corrections need a successor with exact-byte approval and a relabel) — `deferred-work.md:1191`
- [x] [Review][Defer] D1i K12/K14 prerequisites are narrower than AD-23 — K12 rows omit resumability/concurrency and the negative-proof list (AD-23 `:183-187`). T01–T04 omit K14's negative proofs (`:219-222`). AD-23 still governs. Low. [B7] — deferred: user chose "Fold into next successor" (approved and authorized bytes are immutable; corrections need a successor with exact-byte approval and a relabel) — `deferred-work.md:1191`
- [x] [Review][Defer] D1j CLI and stub rows sit under "## MCP tools" — `build_candidate.py:587-590` emits a section heading only when the headers change. ChatBot L01–L12 and Memories L01–L14/S01–S04 therefore lose their own sections. Low. [E1] — deferred: user chose "Fold into next successor" (approved and authorized bytes are immutable; corrections need a successor with exact-byte approval and a relabel) — `deferred-work.md:1191`
- [x] [Review][Defer] D1k PS14 README label repeats itself — The PS14 line in `upstream/memories/README.patch` links Memories 1.1.0 twice and states the T01–T04 modes twice. `delivery-authorization.json` binds those patch bytes. Low. [A10, B14] — deferred: user chose "Fold into next successor" (approved and authorized bytes are immutable; corrections need a successor with exact-byte approval and a relabel) — `deferred-work.md:1191`
- [x] [Review][Patch] D2 Verifier and tests halt permanently once the ChatBot/Memories gitlinks move or local main lags origin/main — `verify_amendment.py:115-118` and `build_candidate.py:649-656` (reached through `packet()` at `verify_amendment.py:185`) require HEAD gitlinks to equal the pins and origin/main to be an ancestor of HEAD. `/pushall` routinely moves gitlinks, and label completion is still pending. Medium. [E11] Resolved: user chose "HEAD checks only on regen". The verifier keeps the BASELINE gitlink == pin and pin-ancestry checks; HEAD-gitlink equality and origin/main ⊆ HEAD run only in `build_candidate.py` regeneration. [`evidence/story-5-10/verify_amendment.py:115`]
- [x] [Review][Patch] Delivery guards for the integrated README bytes and inventory-revision ancestry have no negative test [`evidence/story-5-10/test_verify_amendment.py:474`] — Removing `verify_labels.py:47` or `:55` leaves the suite green (pre-verified by the verification-gap layer). [V1]
- [x] [Review][Patch] General guard-removal control is tautological [`evidence/story-5-10/test_verify_amendment.py:552`] — The test stubs a function and then calls the stub. Replace it with source-removal controls run through the entrypoints (as `:459` does), and correct the claim at `verification.md:148-150`. [A7]
- [x] [Review][Patch] PASS messages misstate the recorded state [`evidence/story-5-10/verify_amendment.py:211`, `evidence/story-5-10/verify_labels.py:121`] — With the approved receipt, the output still says "owner approval … remain completion gates" and "approval and delivery pending". [A9]
- [x] [Review][Patch] Recorded state is stale [`deferred-work.md:686`, `evidence/story-5-10/verification.md:176`, `:245`, `sprint-status.yaml:103`]:
  - The ledger says delivery authorization and McpCli publication remain pending.
  - verification.md and sprint status say there was no commit or push, but `e2e3db7` and `008d95c` are on McpCli origin/main.
  - AI.Tools `cfd1ebe` supersedes the check.py blocker premise. The checker applies only after CiCd adoption, and McpCli has no `.github/hexalith-ci.json`, so its existing required CI gates apply; main CI is currently red.
  - B13 part 3 is rejected: Story 5.11's technical 1.0.4 candidate already re-cites both 1.1.0 successors and T01–T04.
  - [A2, B13]

Rejected (21):
- A1 false: completion correctly refuses; AC2 is the recorded pending gate, not a defect.
- A8 low: the story commit changed no census, AI.Tools or production file, and adding an authority would change the approved receipt's expected artifacts.
- A11 false: the inventory header (`memories-migration-inventory-v1.1.0.md:52-54`) records connect-before-validation, and no row claims a zero-connection refusal.
- E6 false: neither inventory has K08, A1–A8 or K13 rows in the adopted map.
- E7 false: prior label rows are hash-bound immutable inputs, and the generated rows cite 1.1.0.
- E8 low: the absolute `ownerCheckout` matches completed Story 5.9; completion is a local owner-checkout gate.
- E9 low: both owner READMEs are unchanged since the pins (ChatBot origin/main equals the pin; Memories `9d87500e..5c1c2258` has no README diff), and a mismatch would fail loudly.
- E10 low: completion requires the authorization inside the register; the bypass is contrived.
- E12 false: no `Hexalith(Module|Command|Query)` token exists in either Contracts tree at the pins.
- E14 false: exact row and repository sets are required before the `next()` loops, and the class map is adopted and hash-bound.
- E15 low: Linux C/POSIX locales coerce to UTF-8, and the evidence runs on Linux.
- E16 false: the sources are immutable pinned blobs, and every delimiter is present.
- E17 low: baseline AI.Tools `7ef8166` has `plan_version: '1.2.0'` (`:2`) and the MigrateEmbeddingVectors row (`:34`).
- E18 low: statuses are tool-written lowercase keys with two-space indentation; the failure is hypothetical.
- E19 low: the characters are hypothetical, and builder and verifier agree on the actual pins.
- E20 low: this matches delivered Story 5.9 practice, and the SHA-256 beside each link binds the content.
- B6 false: the spec Design Notes assign the HTTP gate, not G2, to M01–M04/V01–V03; a fix would edit the spec.
- B10 low: duplicate of E17.
- B11 false: duplicate of E12.
- B12 low: the recorded instructions are exactly `approve` and `authorize`; the guard is the same generic one used in Stories 5.7–5.9.
- B15 low/false: README drift is false (the READMEs are unchanged); the brittleness and absolute-path points are E9 and E8.

## Design Notes

- **Identity-dependent Memories rows:** M01–M04 (per-user JWT security class) and K10 V01–V03; every other Memories `defer` row keeps G2.
- **Administrative scope:** L01/L13 stay unscoped deployment metadata, with no admin-role claim.
- **ChatBot V10:** stays `defer` (K04). The upstream handle fix is drift, but no decorated status Query exists. Acceptance still never proves completion.
- **ChatBot M10/L10/V07/V08 (K05):** the gap is module-side provider and pre-submit authority. Approval/proposal versions stay Payload concurrency inputs.
- **PS14 rows T01–T04 (`--dry-run`, `--live`, `--rollback`, `--abort`):** each cites AI.Tools plan 1.2.0 and states that `--yes` grants no agent authority.
- **G rows:** record status at the pin. ChatBot G1 and Memories G6 are satisfied only by the recorded receipt. Retirement gates stay open.

## Verification

**Commands:**
- `python3 -I A/evidence/story-5-10/verify_amendment.py` -- passes on pending candidates; `--approved-completion` fails until approval and label integration.
- `python3 -I -m unittest discover -v -s A/evidence/story-5-10 -p 'test_*.py'` -- passes with every control detected.
- `python3 -I A/evidence/story-5-2/verify_class_map.py` -- AD-23 still adopted.
- `python3 scripts/scan-evidence-secrets.py A/evidence/story-5-10 --receipt <task-owned path>` and `git diff --check` -- clean.

## Implementation Notes

- 2026-11-16: The user approved this spec with "approve and stop". The frozen intent and decisions are now locked; implementation resumes in a fresh `bmad-build` session.
  - Approval-time HEAD and `origin/main` were both `979e1e126c6d7010997f4f20b2bb3defae81333e`, with gitlinks ChatBot `6a4ca07b18e9b58500dc79dfede1f308da36c828` and Memories `9d87500eaf4c39ce0cec0cb3a03e5dd62c167106`. These are the pins; recheck them in the precondition task.
  - At approval, the working tree was clean apart from this untracked spec. Nothing was committed or pushed.

- 2026-11-16 implementation: Prepared pending ChatBot 1.1.0 (48 predecessor entries) and Memories 1.1.0 (51 predecessor entries plus four PS14 modes), one deterministic generator, one candidate verifier, one label verifier and 26 tests. Final candidate and label checks, all 26 tests, unchanged adopted AD-23 and diff whitespace pass; both completion entrypoints refuse pending approval. Exact-byte inventory approval and separate label-delivery authorization remain pending. Nothing is enrolled, executed or retired, and no upstream files were changed.
- Precondition evidence: `git fetch` succeeded; HEAD `e2e3db7ba2d45d61feacc39c41b3051310fbc57f` contains fetched `origin/main` `979e1e126c6d7010997f4f20b2bb3defae81333e`; both HEAD gitlinks equal the approved pins. Existing user edits to spec status and sprint status were preserved.
- 2026-11-16 owner approval: The user replied exactly `approve` to acceptance of both reviewed inventory files and all ten roles in approval.json. Recorded the decision and explicit role coverage without changing either inventory, any label/README patch or any earlier receipt. Separate delivery authorization and upstream integration remain pending; the story stays in-review and no commit or push is authorized.
- Approval-state verification: all 26 tests pass in 105.872 seconds; both default verifiers, adopted AD-23 and whitespace checks pass. Both completion modes refuse only for unintegrated PS06/PS07/PS12/PS13/PS14 labels, and real regeneration refuses the approved receipt. Read-only isolated-copy checks confirm both prepared patches match the locally observed owner origin/main README bytes; unrelated owner work remains untouched. Evidence: evidence/story-5-10/approval-checks.json and the approval-state secret scan.
- 2026-11-16 delivery authorization: The user replied exactly `authorize` to committing/pushing the approved packet and both README-only updates. Recorded the hash-bound authorization in evidence/story-5-10/delivery-authorization.json and freshly fetched all three owner main branches. The mandatory pre-push command `python3 references/Hexalith.Builds/check.py` failed in a clean temporary McpCli checkout at exact HEAD with exit 1 because `.github/hexalith-ci.json` is absent; evidence/story-5-10/delivery-gate.json retains the exact result. Active shared guidance requires this gate to pass before every push and assigns CI configuration to Hexalith.CiCd. No commit or push was attempted, no gate was bypassed, and authorization remains valid for resumption after that repository configuration blocker is resolved. The story stays in-review; approved bytes, root gitlinks and owner local work remain unchanged.

## Spec Change Log

- 2026-11-16 code review pass 1 patches: all five action items implemented. Current HEAD gitlinks and origin/main containment are checked only when regenerating; verification retains BASELINE pin equality and published-pin ancestry. Delivery tests now reject each integrated README mismatch and off-main inventory revision through both entrypoints, and removing the actual guards breaks the exact-stream assertions. The five general controls remove source statements and run the verifier entrypoint instead of invoking stubs. Pending, approved and integrated output states are checked explicitly. Ledger, sprint and verification records now reflect publication through `e2e3db7`/`008d95c`, recorded approval and authorization, unintegrated labels, adoption-only check.py guidance at AI.Tools `cfd1ebe`, and failed main CI run 43916598661. Story 5.11 already indexes both successors and T01–T04.
  - Local validation: 29 tests pass in 148.425 seconds; both default verifiers and unchanged adopted AD-23 pass; both completion modes refuse only the missing integrated labels; the real generator refuses the approved receipt; whitespace checks pass. Protected inventory, receipt, label, authorization and patch hashes are unchanged. Evidence: `evidence/story-5-10/review-patch-checks.json`, `review-patch-state.json`, and the review-patch secret scan. No commit, push, enrollment, live execution or upstream checkout change occurred in this patch session. Workflow completion and authorized upstream delivery remain separate gates.

- 2026-11-16 factual evidence correction (no frozen-intent change): `git diff --name-status 839aee31e2a9be11feab3fb726006bb4c2f890b5 acc934599cf1efff36b0643eddc6a3cc4c2978d5` reports `M .mcp.json`, not a deleted file. Both `src` trees are exactly `59158fccb3a2819816a2e13a39095b238bdf1c9b`; generation and verification use that source-tree equality and the observed single configuration-file change.

## Review Triage Log

2026-11-16 build review: all three independent layers returned before triage. Every finding is recorded below before grouping. These are direct source-description corrections or narrow tests/guards for demonstrated states; no intent or authority change is required.

| ID | Layer | Verdict | Evidence and route |
| --- | --- | --- | --- |
| B1 | Blind hunter | medium | The pinned admission validator always returns CanonicalExecutionUnavailable at its atomic-participation check; the pipeline rejects it before reservation/dispatch and the problem factory returns nonretryable 503. The candidate's write/provider descriptions omit this effective refusal. Patch the current-behavior/drift descriptions and anchors. |
| B2 | Blind hunter | medium | Pinned ChatBotApplicationBoundaryPolicy uses CreateHumanPolicy; JWT setup installs a denying bearer scheme when configuration is absent. V01/V03 currently report unchanged. Patch the authentication drift and pinned evidence. |
| B3 | Blind hunter | medium | OperationStatusHttpResults validates canonical metadata and requires CanonicalRevision to be null before public retry eligibility. V10/M11/L11 omit those changed semantics. Patch the status descriptions and anchors. |
| B4 | Blind hunter | medium | IngestionWorkflowConfigurationCapture.NewUnitId calls UnitOwnershipAuthority.Qualify, which prefixes configured-generation IDs with owned-. Memories V06 still describes only GUID identity. Patch both configured and historical forms without conversion. |
| B5 | Blind hunter | medium | Pinned search services call SourcePublicationVisibility.FilterQueryAsync; graph traversal uses the publication read gate and publication filtering. Recording only SOURCE_PUBLICATION_CHANGED misses successful read visibility changes. Patch affected read/variant descriptions and anchors. |
| B6 | Blind hunter | medium | SyntacticSearchService orders raw windows before hydration, validates complete windows/keys, and leaves invalid documents consuming raw positions. V04/V05 say unchanged. Patch ranking/paging/count/error drift and evidence. |
| B7 | Blind hunter | medium | Hosting has conditional fixed-domain versus multi-domain workload transport; EventStoreMemoriesCommandStore's multi-domain branch refuses absent exact bound-command proof. The candidate omits those conditions. Patch V08/G3 and current source observations. |
| B8 | Blind hunter | medium | RedisEmbeddingMigrationStore commits alias cutover before SetEmbeddingConfigAsync; the service subsequently heartbeats/completes the marker. Failure can therefore follow active-alias changes. Patch T02's blanket failure guarantee and bind the concrete source evidence. |
| B9 | Blind hunter | medium | The OpenAPI evidence needle is the first operationId (SubmitCommand at line 31), which does not establish the status/audit CommandId restriction or transition actor removal. Patch these anchors to their specific statements. |
| B10 | Blind hunter | medium | Receipt comparisons finish before the output loop; an approval injected during the first successor write is later overwritten by pending receipt bytes. Patch mutation-time rechecks, avoid unchanged writes, and test that demonstrated schedule. Do not claim atomic publication across arbitrary external writers. |
| E1 | Edge case | medium | Independently reproduces B10's receipt overwrite after the final preflight comparison. Same root cause and patch group as B10. |
| E2 | Edge case | medium | Independently verifies B8's post-cutover failure state in the Redis store and marker completion path. Same root cause and patch group as B8. |
| E3 | Edge case | medium | Real command and deterministic-packet tests hard-code pending receipt data; fixture copies also inherit real approval state. Valid approval/integration would fail the documented suite. Patch isolated pending fixtures and state-aware real expectations; exercise the approved lifecycle. |
| V1 | Verification gap | medium | Pre-verified: removing the publication-byte comparison loop still passes all 20 tests. The success fixture returns matching local bytes and negative cases fail earlier. Patch exact-stream rejection cases for each successor and approval receipt at both inventoryRevision and current origin/main, with a guard-removal control. |

All 14 findings route to 12 patch groups (B8/E2 and B10/E1 share root causes). No new deferral or specification loopback is required.

Resolution: all 12 groups are patched. Final checks.json records all 26 tests passing in 105.974 seconds, both default verifiers passing, both completion modes refusing pending approval, unchanged adopted AD-23 and a clean whitespace check. Source-fact and exact OpenAPI tests cover B1–B9/E2; injected write and unchanged-file tests cover B10/E1; state-aware isolated lifecycle tests cover E3; all six published-byte mismatch cases and removal of the actual comparison loop cover V1. Verification and final scan evidence are in evidence/story-5-10. The story stays in-review for owner approval and separate delivery authorization; no done claim or commit is made.

### Build review of resumed patches — 2026-11-16

All three independent layers returned before triage: blind hunter (10), edge cases (1), verification gaps (1). The preserved baseline diff also contains previously committed Story 5.11 work. Its findings below are recorded individually and rejected from this run because the approved intent explicitly assigns technical successors and plan reconciliation to Story 5.11; no Story 5.11 file is changed in this run.

| ID | Layer | Verdict | Evidence and route |
| --- | --- | --- | --- |
| R-B1 | Blind hunter | medium | Story 5.11 `build_packet.py:523` still emits an absent-CiCd-config blocker after adoption-only guidance. Rejected from this run: the technical successor/plan belongs to Story 5.11 under the explicit intent decision. |
| R-B2 | Blind hunter | medium | Story 5.11 `verify_reconciliation.py:354` rejects one candidate marker while its completion fixture removes only that marker and retains other candidate wording. Effective prior delivery is separately checked, but final prose can remain stale. Rejected from this run: final plan reconciliation is explicitly assigned to Story 5.11. |
| R-B3 | Blind hunter | medium | Story 5.11 `verify_reconciliation.py:353` checks ancestry of the approved AI.Tools revision, then reads the earlier revision rather than the actual gitlink's documentation bytes. Rejected from this run: the AI.Tools plan/gitlink is explicitly excluded from Story 5.10. |
| R-B4 | Blind hunter | medium | Story 5.11 `verify_reconciliation.py:163` checks owner paths and ancestry but no owner-origin identity. Rejected from this run: the nine-owner reconciliation packet belongs to Story 5.11. Story 5.10 already validates its two owning origins. |
| R-B5 | Blind hunter | medium | Story 5.11 `verify_reconciliation.py:340` accepts literal passed check statuses without command/revision/result receipts. Rejected from this run: the technical/plan delivery packet is explicitly Story 5.11 work. |
| R-B6 | Blind hunter | medium | Story 5.11 `build_packet.py:297` refuses only an initially approved receipt; unknown states and approval arriving during later writes are unprotected. Rejected from this run: technical-successor generation is assigned to Story 5.11. Story 5.10 retains its existing unknown-state and write-time checks. |
| R-B7 | Blind hunter | medium | Story 5.11 `verify_reconciliation.py:29` uses ordinary JSON parsing, so conflicting duplicate members select the last value. Rejected from this run: Story 5.11 owns that packet; Story 5.10 already rejects duplicate members. |
| R-B8 | Blind hunter | medium | Story 5.11 `verify_reconciliation.py:160` checks only the names/count of no-change owners, not their declared inspected revisions and hashes. Rejected from this run: the all-owner census/reconciliation work is explicitly outside this intent. |
| R-B9 | Blind hunter | medium | Memories T01 promises a mapped domain-failure exit and limits unmapped failures to bootstrap; pinned service `RunAsync` catches only cancellation around dry-run reads, and Program has no encompassing exception mapper. Defer: an existing approved-byte defect, to be corrected in the next approved Memories successor; approved bytes remain unchanged. |
| R-B10 | Blind hunter | medium | Memories T03/T04 omit partial rollback/abort effects: pinned Redis store commits aliases/marker before configuration persistence, then abort performs further cleanup/marker writes. Defer: an existing approved-byte defect, to be corrected in the next approved Memories successor with recovery obligations. |
| R-E1 | Edge cases | medium | Pre-verified in a disposable fixture: Story 5.11 `verify_reconciliation.py:180-185` applies an additional production-file hunk while verifying only the declared documentation target. Rejected from this run: technical-successor/plan patches are explicitly Story 5.11 work; none are changed here. |
| R-V1 | Verification gaps | medium | Pre-verified: changing Story 5.10's output symlink scan to leaf-only passes all four existing generator tests, yet a symlinked upstream/chatbot directory redirects README.patch writes outside the repository. Patch: add exact-stream, no-write parent-symlink coverage and an actual source-removal control. |

Routes after individual verdicts: one test patch (R-V1), two distinct pre-existing approved-byte deferrals (R-B9/R-B10), nine findings rejected from the explicitly separate Story 5.11 work. The eleven earlier user-deferred groups remain tracked at `deferred-work.md:1191`; no approved inventory, receipt, register, authorization or patch is modified.

Resolution: R-V1 is patched. The parent-symlink test checks exact streams and unchanged local/external output bytes, then removes the actual ancestor expansion and demonstrates the redirected write in disposable scratch. Final verification passes all 30 tests in 228.029 seconds, both default verifiers, adopted AD-23, approved regeneration refusal and whitespace; both completion modes still refuse the missing owner-label integration. Evidence: [final checks](evidence/story-5-10/review-final-checks.json), [verification](evidence/story-5-10/verification.md) and [secret scan](evidence/story-5-10/secret-scan-review-complete.json). One earlier harness run timed out at 360 seconds without a test result; the logged final run completed successfully. R-B9/R-B10 are tracked separately under this spec's deferred-work heading. The spec stays in-review and sprint stays review because the completion gate is unsatisfied; approved bytes and authorization remain unchanged. No commit, push or upstream integration was performed.
