---
title: '5.10 Refresh and re-disposition ChatBot and Memories inventories'
type: 'chore'
created: '2026-11-16'
status: 'ready-for-dev'
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
- [ ] Precondition: `git fetch`; confirm `main` contains `origin/main` and the HEAD gitlinks equal the approval pins. If the gitlinks moved or a rebase conflicts, HALT.
- [ ] `A/chatbot-migration-inventory-v1.1.0.md`, `A/memories-migration-inventory-v1.1.0.md`, `.gitattributes` (`-text`): write successors following Design Notes; approval pending.
- [ ] `E/story-5-10/build_candidate.py`: generate both deterministically from predecessor bytes, `git show <pin>:` sources and the AD-23 map; refuse to overwrite an approved packet.
- [ ] `E/story-5-10/{verify_amendment.py,test_verify_amendment.py}`: candidate and approved-completion modes, every matrix row, guard-removal controls, exit code and both streams.
- [ ] `E/story-5-10/{approval.json,labels.json,verify_labels.py,upstream/{chatbot,memories}/}`: pending receipt bound to predecessor/successor hashes and authorities; README-only label patches citing the successors, changing gate text only where an amendment changes the gate (PS14's four-mode inventory obligation).
- [ ] `A/deferred-work.md` (grep first: `:682` ChatBot partial resolution; `:1048`/`:1147` re-routed to Story 5.11), `E/story-5-10/verification.md`, secret-scan receipt, this spec, `A/sprint-status.yaml`: record only the supported state.

**Acceptance Criteria:**
- Given the candidates, when the verifier runs, then every entry passes and all protected predecessor and authority bytes are unchanged.
- Given exact-byte owner approval and separate delivery authorization, when completion runs, then the receipts name the covered roles, both owner READMEs on `origin/main` cite the successors, and nothing is enrolled, executed or retired.

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

## Spec Change Log

## Review Triage Log
