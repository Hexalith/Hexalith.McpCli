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

#### Code review pass 2 — 2026-11-16

Scope: deliverables `979e1e1..5008de3`, 17 files and 3,599 lines. The scope is the same as pass 1, now including the pass-1 patches and the R-V1 fix. Story 5.11's interleaved `3511afd` hunks and the check, scan and test-stream receipts are excluded. All four layers returned and none failed.

Baseline at HEAD `5008de3` (= origin/main):
- Both default verifiers exit 0, and both completion modes exit 1 on unintegrated labels.
- AD-23 is still adopted, and 30 tests pass in 275.9 s.
- Main CI 43943458640 for `5008de3` fails in the same five jobs as 43916598661. These are pre-existing failures tracked at `deferred-work.md:1043`.

The 44 raw findings resolve to 1 decision-needed, 10 patches, 3 deferrals and 25 rejections. IDs are prefixed `2`; a re-raised finding cites its pass-1 verdict ID.

Decision resolved 2026-11-16: D3 ("Section-level check") becomes a patch. Totals are now 0 decision-needed, 11 patches, 3 deferrals and 25 rejections.

- [x] [Review][Patch] D3 ChatBot main README moved after the pin, so a README-only delivery onto current main cannot pass completion [`evidence/story-5-10/verify_labels.py:47`] — `verify_labels.py:47` requires the integrated commit's whole README to equal `after`, which is the pin README with the section swapped.
  - Resolved: the user chose "Section-level check". `check_delivery` will require each integrated commit to be README-only, with its diff exactly the authorized section swap applied to its own parent: the parent section equals `before`, the commit section equals `after`, and all other bytes are unchanged.
  - The patch file and the approved bytes stay unchanged, and no new approval is needed. The register's whole-README `afterSha256` becomes historical evidence.
  - Add exact-stream tests for both modules: moved-main acceptance, and a commit with an extra change outside the section.
  - ChatBot remote main `e2727327` is two commits past pin `6a4ca07b` (`bf0f44ff`, `e2727327`, both 2026-11-16). They rewrite README lines 37-57 (build/test guidance), outside the compatibility section.
  - The authorized `upstream/chatbot/README.patch` still applies cleanly to that README (hunk `@@ -178,5 +178,5 @@`). The result hashes `2cace945…`, not the register's `afterSha256` `e6d142d1…`.
  - `delivery-authorization.json` plans delivery from isolated owner origin/main checkouts. The verifier would reject that delivery with `chatbot: integrated README bytes mismatch`.
  - Memories remote main `d2a39a84` has no README change since its pin.
  - Pass-1 E9 was rejected because both READMEs were unchanged; that premise no longer holds for ChatBot.
  - Options: (a) verify at section level; (b) deliver byte-exact on the pin, then merge; (c) regenerate the ChatBot label with new approval and authorization.
  - Medium. [2E6]
- [x] [Review][Patch] Three mutable enrollment/dependency files are bound to the baseline working tree, so the next routine bump breaks both verifiers [`evidence/story-5-10/verify_amendment.py:166`]
  - `B.AUTHORITIES` (`build_candidate.py:45-46`) includes `Directory.Build.props`, `tools/dependency-policy.json` and `src/Hexalith.McpCli/Hexalith.McpCli.csproj`. They changed 18, 25 and 3 times since 2026-10-15.
  - `verify_owner_packet` requires their working-tree bytes to equal `979e1e1`. `packet()` (`build_candidate.py:663`) re-hashes them into the receipt `artifacts` that `check_approval` compares (`verify_amendment.py:142-143`).
  - Apply the pass-1 D2 rule ("HEAD checks only on regen"): verification reads these three from `BASELINE` Git objects, and regeneration keeps the working-tree equality.
  - Add a test that changes the fixture's `Directory.Build.props`: the default verifier still passes and regeneration refuses.
  - Medium. [2V-o1, 2E4, 2A2]
- [x] [Review][Patch] Completion delivery guards have no negative tests [`evidence/story-5-10/test_verify_amendment.py:566`]
  - Pre-verified: each of these removals leaves all 30 tests green: the exact `authorize` word check (`verify_labels.py:40`), either 40-hex SHA check (`:44`, `:54`), or the `commitSha256` comparison (`:50`).
  - Add exact-stream subtests for: wrong words (as in Story 5.9 `test_verify_amendment.py:261-271`); a symbolic or short commit or inventory revision; a mismatched commit hash.
  - [2V1]
- [x] [Review][Patch] Owner-checkout origin and pending-claim guards have no tests [`evidence/story-5-10/verify_labels.py:98`]
  - Pre-verified: removing `:97-98` or `:106-107` leaves the suite green.
  - Add, each with exact streams: a pending register that claims authorization, a revision or an integration; a completion fixture whose checkout origin is another repository.
  - [2V2]
- [x] [Review][Patch] Source-premise guards in `check_source_drift` have no failing controls [`evidence/story-5-10/verify_amendment.py:117`]
  - Pre-verified: `:117` and `:123-137` can be weakened with all 30 tests green. They cover:
    - the Contracts csproj and the old `src` tree / `.mcp.json` premise;
    - the fixed tools/leaves, the 12 tools and the host resources/prompts;
    - the Memories fixed sources, the 4 registrations and `ValidAlgorithms`;
    - the PS14 premises.
  - Only the gitlink and decoration guards have controls (`test_verify_amendment.py:380-392`).
  - Add one fake-git case per guard, asserting its exact message.
  - [2V3]
- [x] [Review][Patch] `verify_labels.py` reads the approval decision outside its error handler [`evidence/story-5-10/verify_labels.py:121`]
  - The pass-1 PASS-message patch added this read. A missing or malformed `approval.json` now produces a traceback instead of `FAIL:`.
  - Move the read into the `try`.
  - Low. [2B5, 2E3]
- [x] [Review][Patch] Recorded state is stale again after `5008de3` [`evidence/story-5-10/verification.md:7`]
  - The verification.md summary names only `e2e3db7`/`008d95c` and origin/main `119a4b5`.
  - `verification.md:346-348` and `sprint-status.yaml:103` say no commit or push happened, yet the resumed patches are origin/main as `5008de3`.
  - `deferred-work.md:686` lists the same two commits and the `119a4b5` run.
  - `deferred-work.md:1192` says the labels "are delivered unchanged", though integration is pending.
  - Fix: record `5008de3` and CI run 43943458640 (same pre-existing failures as `deferred-work.md:1043`), and change the wording to "will be delivered unchanged".
  - Low. [2A4, 2B12, 2B14]
- [x] [Review][Patch] Ledger D1g misstates the doubled-period scope and cause [`_bmad-output/implementation-artifacts/deferred-work.md:1211`]
  - `drift()` (`build_candidate.py:452`) appends `.` after notes that already end in one. As a result, 22 rows end in `..`:
    - ChatBot: M08, L02–L05, L08–L11, V01, V03, G2–G5;
    - Memories: M01, M03, L03, V04, V05, V07, G3.
  - The ledger attributes the doubled periods only to G2–G5 via `WRITES` (`:58`).
  - Low. [2B7]
- [x] [Review][Patch] Ledger D1a omits the dropped withdrawal/inclusion precondition [`_bmad-output/implementation-artifacts/deferred-work.md:1196`]
  - ChatBot 1.0.0 "Approval limits and retirement gate" (`chatbot-migration-inventory-v1.md:157-161`) requires the following before any included operation or legacy withdrawal: equivalent safe output and error behavior, build/release compatibility, and differential behavior evidence.
  - Neither successor carries this precondition, although they add 5 + 20 withdrawals.
  - Also record two replacements: `build_candidate.py:571` replaces every legacy "Source evidence" cell, and `:573` replaces V10's "Current behavior" cell.
  - Low. [2B8]
- [x] [Review][Patch] Ledger R-B9 anchor points at the output-format branch [`_bmad-output/implementation-artifacts/deferred-work.md:1221`] — At Memories pin `9d87500e`, `tools/MigrateEmbeddingVectors/Program.cs:79` is the json-format check. The `await service.RunAsync` without an outer mapper is at `:77`. Low. [2E14]
- [x] [Review][Patch] Ledger self-anchors drifted past this story's insertion [`_bmad-output/implementation-artifacts/deferred-work.md:846`]
  - `008d95c` inserted `:686`, and Story 5.11's `3511afd` inserted `:145`. Anchors that were correct at baseline now miss.
  - Remap (citing line in parentheses):
    - `:697` → `:699` (`:754`);
    - `:787`, `:791`, `:795` → `:789`, `:793`, `:797` (`:846`);
    - `:556` → `:557` (`:853`, `:859`);
    - `:1045` → `:1047` (`:1104`);
    - `:682` → `:683` (`:1129`);
    - `:1047` → `:1049` (`:1151`).
  - Low. [2E13]
- [x] [Review][Defer] Verification still needs the unpublished ChatBot `acc93459` object [`evidence/story-5-10/verify_amendment.py:123`] — deferred: approved receipt bytes; fold into the next ChatBot successor under the pass-1 D1 rule.
  - GitHub returns HTTP 422 for `acc93459`, so a fresh clone cannot run `verify_amendment.py`.
  - `approval.json` binds 38 `@acc93459` pinnedArtifacts, and `build_candidate.py:289` reads predecessor anchors at `oldpin`.
  - The published `839aee31` has the same `src` tree.
  - Medium. [2B1]
- [x] [Review][Defer] ChatBot L11/L12 drift cites query-handler anchors they do not have [`evidence/story-5-10/build_candidate.py:421`] — deferred: approved bytes; fold into the next ChatBot successor. Low. [2B6]
- [x] [Review][Defer] PS14 T02–T04 cite the dry-run command as their documentation evidence [`evidence/story-5-10/build_candidate.py:411`] — deferred: approved bytes; fold into the next Memories successor. The fixed `--dry-run` needle anchors every T row at `docs/operations/embedding-providers.md:214`. Low. [2E10]

Rejected (25):
- 2B2, 2E9, 2A3, 2V-o2 low: no script reads `delivery-authorization.json`. This repeats pass-1 E10 and matches completed Story 5.9, whose verifier also never reads its authorization file. The fix adds a cross-file guard against a divergence nobody has shown.
- 2B3 low: case/whitespace-tolerant exact words is pass-1 B12.
- 2B4 low: the approved receipt holds exactly the ten roles, and extra roles or keys would grant nothing. The fix adds guards for a case that does not occur.
- 2B9 low: `blob/main` links are pass-1 E20.
- 2B10 low: silent rewrite no-ops are pass-1 E16. The approved packet refuses regeneration, and the verifier compares hash-bound bytes.
- 2B11 false: the narrow decoration regex is pass-1 E12/B11. No `Hexalith(Module|Command|Query)` token exists in either Contracts tree at the pins.
- 2B13 low: the `.gitattributes` rule is identical to the 5.8 and 5.9 rules (`.gitattributes:48`, `:53`). The "pending receipt" comment is cosmetic.
- 2B15, 2E8 low: absolute `ownerCheckout` paths are pass-1 E8. Shared CI policy keeps story-evidence checks out of module CI.
- 2E1 false: the packet is approved, so `build_candidate.py:695` refuses before any write. The first generation run completed.
- 2E2 false: the uncaught `StopIteration` is pass-1 E14; exact sets are required before every `next()`.
- 2E5 low: a later owner relabel failing current-origin completion is by design ("current upstream citations", matching 5.9). A successor relabel supersedes these labels.
- 2E7 false: a local remote-tracking ref holds only fetched or pushed commits, and a stale ref fails loudly.
- 2E11 low: non-UTF-8 locales are pass-1 E15.
- 2E12 low: `--root` names the packet being verified and is the test seam. Loading that root's sibling verifier is intended.
- 2E15, 2A8 low: since `v3.0.0`, main already has a `feat` and 15 other `fix` commits, so these three do not change the next release. The published history is immutable.
- 2A1 false: unmet AC2 is pass-1 A1, the recorded pending gate. Its new delivery-path blocker is D3.
- 2A5 low: the Design Note keeps G2 on every other Memories defer row, and the bytes state "G2 remains open:" with G2's gate text. That is stricter, and the bytes are approved.
- 2A6 low: the single-maintainer placeholder approver is identical to the completed Story 5.9 receipt, and the bytes are approved.
- 2A7 low: the "unchanged" claims being broader than the verifier is pass-1 A8. The story commits touch only `_bmad-output/` and `.gitattributes`.
- 2A9 low: the packet has exactly the four required scripts; the extra receipts are preserved history.
- 2B12 command-table part, false: `verification.md:106` heads that table "Preparation", and `:126` marks the result superseded. The stale summary part is a patch above.
- 2B14 parts 1–2, low: other modules' source-pin portions belong to their own stories. The red CI note already records its run ID.

#### Code review pass 3 — 2026-11-16

Scope: deliverables `979e1e1..ccbdd3e`, 18 files and 4,286 lines. This is the pass-2 set plus `ccbdd3e`'s Story 5.11 fixture hunk (P2-B2). Story 5.11's interleaved `3511afd` `.gitattributes` and ledger hunks are removed through a synthetic `--no-index` diff. All four layers returned and none failed.

Baseline at HEAD `ccbdd3e` (= origin/main):
- Both default verifiers exit 0. Both completion modes exit 1 with "completion requires integrated PS06/PS07/PS12/PS13/PS14 labels".
- AD-23 is still adopted, all 36 tests pass in 298.9 s, and `git diff --check 979e1e1 ccbdd3e` is clean.
- Main CI 43957388915 for `ccbdd3e` fails in the same five jobs as 43943458640 (`deferred-work.md:1043`).
- Story 5.11's `verify_reconciliation.py` exits 1 with `deferral accounting/source/owner/gate mismatch` (3W1).
- ChatBot owner main is still `e2727327`. Memories owner main moved to `d2a39a84`, with no README change since pin `9d87500e`.

The 57 raw findings resolve to 1 decision-needed, 7 patches, 2 deferrals and 38 rejections. IDs are prefixed `3`; a re-raised finding cites its earlier verdict ID.

Decision resolved 2026-11-16: 3D1 ("Check at inventoryRevision") becomes a patch. Totals are now 0 decision-needed, 8 patches, 2 deferrals and 38 rejections. The user left all eight patches as action items.

- [x] [Review][Patch] 3D1 Verification no longer detects ChatBot/Memories enrollment, so completion cannot show "nothing is enrolled" [`evidence/story-5-10/verify_labels.py:58`] — the pass-2 mutable-authority patch removed the only enrollment check.
  - Resolved: the user chose (a). In completion, read `src/Hexalith.McpCli/Hexalith.McpCli.csproj` and `tools/dependency-policy.json` at the recorded canonical `inventoryRevision`. Refuse with exact streams if either enrolls `Hexalith.ChatBot.Contracts` or `Hexalith.Memories.Contracts`: a `HexalithContracts="true"` `PackageReference`, or a policy `modules` key. Default mode keeps the BASELINE-object reads. Add exact-stream tests for each file and module, plus a guard-removal control.
  - `authority_bytes()` (`evidence/story-5-10/build_candidate.py:646-652`) returns BASELINE objects for `Directory.Build.props`, `tools/dependency-policy.json` and `src/Hexalith.McpCli/Hexalith.McpCli.csproj` unless regenerating. `verify_amendment.py:166-167` then compares that value with itself.
  - Completion never regenerates, and no other script reads the csproj or the policy `modules`. A working-tree `HexalithContracts="true"` ChatBot or Memories reference therefore passes both modes, including `--approved-completion`.
  - AC2 requires completion to show nothing is enrolled, and the Never list forbids changing enrollment.
  - Options:
    - (a) Completion checks the recorded `inventoryRevision` csproj and policy `modules` for no `Hexalith.ChatBot.Contracts` or `Hexalith.Memories.Contracts` enrollment. This survives later bumps and later legitimate enrollment. Recommended.
    - (b) Both modes check the working tree. This catches drift now, but 5.10's verifier goes red when a later story enrolls either module.
    - (c) Accept the gap and rely on the enrollment gates (inventory coverage, vectors, `DependencyPolicyTests`), recording that the verifier does not check enrollment.
  - Medium. [3A1]
- [x] [Review][Patch] Regeneration-path tests read the real HEAD gitlinks, origin/main and live mutable files [`evidence/story-5-10/test_verify_amendment.py:90`]
  - `workspace()` symlinks `.git`, `src` and `tools` and copies the live `Directory.Build.props` (`:90-92`).
  - Generator and regeneration tests therefore check the real HEAD gitlinks, `origin/main` ancestry and live mutable bytes. These are `:387`, `:732`, `:754`, `:782` and `:798`.
  - The auditor's probe moved the ChatBot gitlink. `:387` then failed with `chatbot: HEAD root gitlink pin mismatch; halt`, and `:798` exited 1 instead of 0. `/pushall` routinely moves every gitlink, and a routine `dependency-policy.json` bump has the same effect. This contradicts the pass-1 D2 rule.
  - Fake HEAD `ls-tree` and `merge-base origin/main HEAD` as `:456-479` does, and write the BASELINE bytes of the three mutable files into the workspace.
  - Medium. [3A2, 3E22]
- [x] [Review][Patch] Only `Directory.Build.props` exercises the mutable-authority rule [`evidence/story-5-10/test_verify_amendment.py:387`]
  - Pre-verified: with `tools/dependency-policy.json` removed from `B.MUTABLE_AUTHORITIES`, the test stays green, but an edited policy makes the verifier fail.
  - Run the test once per `MUTABLE_AUTHORITIES` entry, with that file as a real copy in the workspace. Expect PASS from both verifiers and the exact generator refusal.
  - Medium. [3V1]
- [x] [Review][Patch] Four guards can be removed without a failing test [`evidence/story-5-10/verify_amendment.py:144`]
  - Pre-verified removals and what then gets through:
    - `unknown approval decision` (`verify_amendment.py:144`): a `revoked` decision passes.
    - `duplicate workflow status` (`:160`): a duplicate spec status passes.
    - `unsupported label register schema` (`verify_labels.py:70`): schema `9.9.9` passes.
    - The missing-receipt refusal (`build_candidate.py:699-700`): deleted receipts beside existing successors are regenerated as pending.
  - Add exact-stream refusal cases with `removed_source` controls to `test_duplicate_json_unknown_state_and_missing_metadata` (`:806`) and `test_generator_refuses_approved_authorized_symlink_and_approval_race` (`:732`).
  - Medium. [3V2]
- [x] [Review][Patch] The label verifier's own completion triggers are untested [`evidence/story-5-10/verify_labels.py:72`]
  - Pre-verified: removing `register['state'] == 'integrated' or V.completion_requested(root,False)` keeps the suite green. Spec `done` and `state: integrated` then pass as candidates.
  - Add standalone label-verifier runs without the flag for spec `done`, sprint `done` and `state: integrated`. Each needs the exact refusal and a removal control.
  - Medium. [3V3]
- [x] [Review][Patch] 5.10's recorded checks omit Story 5.11's verifier and suite, although both read the ledger 5.10 edits [`evidence/story-5-10/verification.md:422`]
  - `review-pass2-after-review-checks.json` ran only `RecordedAuthorityAndLifecycleTests` (3 tests). `verify_reconciliation.py` and the full 5.11 suite would have shown the break from `5008de3` onwards (59 vs 56 entries).
  - Add both to 5.10's recorded checks whenever 5.10 changes the shared ledger. Record the current exit 1 and its routed cause (3W1) rather than claiming green.
  - Medium. [3V4]
- [x] [Review][Patch] Ledger anchors remapped in pass 2 still miss their entries [`_bmad-output/implementation-artifacts/deferred-work.md:754`]
  - They were already wrong at `979e1e1`, and the pass-2 +2 remap (2E13) kept them wrong:
    - `:754` cites `:699`, inside the AI.Tools commitlint entry. The relative-link entry starts at `:705`.
    - `:846` cites `:793` and `:797`. The truncated-PEM and malformed-XML entries start at `:795` and `:801`; `:789` is correct.
    - `:853` cites `:833`, the Platform reference-check owner line. The mixed profile-identity entry starts at `:836`.
    - `:1104` cites `:1047`. The Admin/technical entry starts at `:1048`.
  - Low. [3B1, 3A3, 3E27, 3E28, 3E29]
- [x] [Review][Patch] Recorded state is stale a third time, and verification.md has no current-state summary [`evidence/story-5-10/verification.md:7`]
  - `verification.md:7-12`, `deferred-work.md:686` and `sprint-status.yaml:103` say publication runs "through `5008de3`", citing CI 43943458640. origin/main is now `ccbdd3e`, and its CI 43957388915 fails in the same five jobs.
  - `deferred-work.md:686` says the ChatBot pin was "observed equal to its owning `origin/main`". Since pass 2, ChatBot main has been `e2727327`, two commits past the pin.
  - The append-only log says both "in progress" (`:353`) and "in-review" (`:403`, `:432`), with no current summary.
  - Fix: replace the opening paragraph with a dated current-state summary that names no moving tip SHA, and date the ChatBot equality observation. The summary covers approval, authorization, pending labels, the test count, CI by reference to the tracked failures, and spec and sprint state. The preparation table is covered by pass-2 2B12.
  - Low. [3A4, 3B17]
- [x] [Review][Defer] 3W1 Story 5.10's later edits invalidated Story 5.11's bound evidence, and 5.10's delivery will invalidate more [`_bmad-output/implementation-artifacts/evidence/story-5-11/verify_reconciliation.py:196`] — deferred: Story 5.11 owns its packet and its pending owner decision. The pass-2 build review routed the mismatch there (P2-B1), but no ledger entry tracked it. Now tracked at `deferred-work.md:1246`.
  - `scoped_deferrals` (`evidence/story-5-11/build_packet.py:242-267`) binds each spec-5-* entry's ledger line, hash and text. `deferral-dispositions.json` holds 56 entries, the HEAD ledger has 62, and `verify_reconciliation.py` exits 1 at HEAD.
  - 5.10's six new entries (`deferred-work.md:1191`, `:1218`, `:1223`, `:1228`, `:1234`, `:1240`) are missing, and re-anchored spec-5-4/5-8 entries changed bytes.
  - `ccbdd3e` changed `evidence/story-5-11/test_verify_reconciliation.py` (`a90f02d1…` → `7bac50fa…`). 5.11's `secret-scan-final.json`, `secret-scan-final-reviewed.json` and `secret-scan-guidance-update.json` still bind the old hash.
  - 5.11's `inputs.json` and `labels.json` bind 5.10's candidate `labels.json` hash, which changes when 5.10 records its delivery.
  - Medium. [3B8, 3V5, 3A5, 3E25]
- [x] [Review][Defer] ChatBot V14 keeps legacy text saying unsupported variants "remain defer/exclude" beside `withdraw / exclude` [`_bmad-output/implementation-artifacts/chatbot-migration-inventory-v1.1.0.md:98`] — deferred: approved bytes; fold into the next ChatBot successor under the pass-1 D1 rule (`deferred-work.md:1257`). The generator rewrites the legacy Disposition cell, as `verify_amendment.py:95-96` requires, but keeps the predecessor rationale. V14 is the only withdrawal row whose legacy text says defer. Low. [3B11]

Rejected (38):
- 3B2 false: `blob/main` label links are pass-1 E20 / 2B9. They target versioned successor files that are never edited, and every label carries the inventory SHA-256, as in the 5.7–5.9 labels. Story 5.11's immutable-link rule (`test_verify_reconciliation.py:290`) covers its plan links, not README labels.
- 3B3 low: an unread `delivery-authorization.json` is pass-1 E10 / 2B2. Completed Story 5.9's verifier never reads its authorization file either.
- 3B4 low: the register goes straight from candidate to `integrated`. Approval and authorization live in `approval.json` and `delivery-authorization.json`, and the PASS line reports both. A new state would rewrite authorization-bound bytes.
- 3B5 low: commitlint and the repository checks are delivery-session procedure recorded as evidence (as in Story 5.9's `delivery-commitlint.json`), and owner CI enforces commitlint. The fix adds a cross-file guard.
- 3B6 low: absolute `ownerCheckout` paths are pass-1 E8 / 2B15. They are copied from the Story 5.7 register, as in 5.8 and 5.9, and completion is a local delivery gate.
- 3B7 low: this is 2E5. Story 5.11's `check_prior_delivery` already verifies 5.10's historical delivery against superseding current labels, and 5.11 completion waits for 5.10 delivery.
- 3B9 false: this is pass-1 B12 / 2B3. No other word passes; only case and whitespace variants of the same word do.
- 3B10 low: D1b (`deferred-work.md:1191`) already tracks the generic `owner()` strings. The receipt covers all ten roles explicitly, so no row lacks a covering role, and the fix needs a successor.
- 3B12 false: this is 2A5. "G2 remains open" in G2 is accurate, and the HTTP gate on every Memories `defer` row is a frozen Always rule.
- 3B13, 3E16 false: the narrow regex is pass-1 E12 / 2B11. `git grep -E 'Hexalith(Module|Command|Query)(Attribute)?\b'` finds nothing in any `.cs` file at either pin, so no attribute form can slip past the regex.
- 3B14 low: this is 2B13. No packet `.py` or `.md` file has trailing whitespace, and the comment wording is cosmetic.
- 3B15 low: the approval covers the exact inventory bytes. Script changes go through review, and each run's checks JSON binds the script hashes.
- 3B16 false: codes 0, 1, 2 and 130 match `EmbeddingMigrationExitCodes.cs:12-21` at the pin. The file is anchored, and `verify_amendment.py:131` refuses any change to it since the old pin. Missing-tenant exit behavior belongs to R-B9.
- 3E1, 3E2 false: this is pass-1 E14 / 2E2. The adopted AD-23 map and the approved 5.7 register are immutable and contain both entries, and the generator refuses the approved packet first.
- 3E3, 3E11 low: tracebacks need hand-damaged registers or README shapes that do not occur, and they still fail loudly.
- 3E4 low: the approved receipt makes `build_candidate.py` refuse before any write. An argument parser would add surface with no reachable harm.
- 3E5 low: the approved receipt closes generation, and atomic writes would add complexity.
- 3E6 false: rows in both modules map only to K01, K03–K07, K09, K10, K12, K14, K15 and governance. No K08, K13 or A-class row exists.
- 3E7 false: all nine non-unique needles resolve first to the intended statement: `epics.md` "McpCli", both formatters' `response.OperationId`, `.RecordAdmissionAsync(context`, `--dry-run`, `11.0.100`, `ValidAlgorithms`, and `SOURCE_PUBLICATION_CHANGED` twice. The T02–T04 `--dry-run` documentation issue is already deferred in pass 2.
- 3E8 false: each block terminator exists exactly once at the pin, and each OpenAPI block holds one operation.
- 3E9 false: none of the 230 pinned sources contains a form feed, vertical tab, U+0085, U+2028/2029 or lone CR.
- 3E10 false: all five label rows carry the 1.1.0 citation and their gate text, and none keeps a 1.0.0 citation.
- 3E12 false: both pinned READMEs end with a newline.
- 3E13 false: no predecessor row cites the same `path:line` twice.
- 3E14 false: neither predecessor contains a range anchor token.
- 3E15 false: neither pin has a non-ASCII path.
- 3E17 low: both status files carry exactly one status, a removed line would be a hand edit, and the fix adds a guard.
- 3E18 low: this is 2E12. Loading the root's own verifier is the test seam that `--root` provides.
- 3E19 low: the standalone label verifier only echoes the decision. `verify_amendment.py`, the documented command, validates it, so the fix adds a guard.
- 3E20 low: the approving session records the dates, and the fix adds guards.
- 3E21 false: the ChatBot labels are at lines 181-182 on both the pin and owner main `e2727327`, and the Memories README is unchanged since its pin.
- 3E23, 3E24 low: this local evidence suite needs the root-declared and owner checkouts, as in Stories 5.7–5.9, and CI does not run it.
- 3E26 low: Story 5.11's tests read 5.11's own live lifecycle; that is 5.11 test design, outside this change.
- 3E30 false: `deferred-work.md:686` is `partial_chatbot_resolution_2026_11_16`.

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

- 2026-11-16 code review pass 2 patches: all eleven action items are implemented. Delivery validates the authorized compatibility-section swap against each integrated commit's own parent, retains README-only/current-main/ancestry/hash checks, and accepts unrelated parent README changes. Verification reads the three mutable enrollment/dependency authorities from BASELINE Git objects; regeneration still refuses changed working bytes. Exact-stream tests cover delivery authorization words, canonical revisions and commit hashes, pending claims and owner origins, thirteen source-premise faults with actual guard removal, and handled missing/malformed approval documents. Ledger/status corrections record publication through `5008de3`, CI run 43943458640, all 22 doubled-period rows, dropped predecessor obligations and current source/self-anchors.
  - Final validation: all 36 tests pass in 323.163 seconds; all eight checks pass, including both default verifiers, adopted AD-23 and whitespace. Both completion entrypoints return the exact missing-integrated-label refusal, and regeneration refuses the approved packet. Before/after hashes bind the same four final source/test scripts and unchanged protected approved/authorized bytes. Evidence: `evidence/story-5-10/review-pass2-checks.json`, `review-pass2-state.json` and `secret-scan-review-pass2-final.json`. The deliberately interrupted earlier run is separately retained and superseded. The spec stays in-review and sprint stays review pending label integration; no commit, push, enrollment, execution, retirement or upstream checkout change occurred in this pass.

- 2026-11-22 code review pass 3 patches: All eight action items are implemented. Completion checks both enrollment declarations at the recorded inventory revision. The tests isolate regeneration inputs and exercise all three mutable authorities, four uncovered guards, standalone completion triggers and missing generator receipts. The ledger references and current-state summary are corrected. All 39 Story 5.10 tests and both default verifiers pass. Both completion commands refuse the five unintegrated labels. The Story 5.11 verifier and its full suite reproduce the stale deferral audit tracked under 3W1 (65 ledger entries, 56 bound). Its 27 tests reported 12 failures across seven methods. The spec and sprint return to review. [Check results](evidence/story-5-10/review-pass3-checks.json)

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

### Build review of pass-2 patches — 2026-11-16

All three independent layers returned before triage: blind hunter (10), edge cases (2), verification gaps (1). The cumulative baseline diff includes previously committed Story 5.11 and release-tooling work. Each finding receives its own verdict below before grouping; the approved intent explicitly assigns technical successors and final product/plan reconciliation to Story 5.11. A consumer fixture broken by this run's parent-README read is part of this run's responsibility.

| ID | Layer | Verdict | Evidence and route |
| --- | --- | --- | --- |
| P2-B1 | Blind hunter | medium | The Story 5.11 audit records 56 entries against 62 scoped ledger entries. Read-only derivation from both HEAD and the current ledger returns 62, proving the mismatch predates this run. Rejected from this run: refreshing that technical-successor/plan audit and its approval bindings belongs to the explicitly separate Story 5.11. |
| P2-B2 | Blind hunter | medium | `evidence/story-5-11/test_verify_reconciliation.py:test_real_prior_lifecycle_checks_historical_delivery_with_superseding_current_labels` supplies integrated README blobs but no parent blobs. The new real Story 5.10 check consequently falls through to Git for synthetic revisions. Patch: retain both historical before blobs and serve each commit's parent README, keeping the actual delivery checks enabled. |
| P2-B3 | Blind hunter | medium | PRD Vision/admin-boundary text and epics FR21 still require generic administration/resource decisions despite adopted AD-23. Rejected from this run: the intent explicitly assigns final product claims and plan reconciliation to Story 5.11, and excludes changing that plan here. |
| P2-B4 | Blind hunter | medium | Carried R-B1/R-B5: Story 5.11 generation retains the obsolete absent-CiCd-config blocker and its completion check requires a Builds-check status. Same unchanged delivery-policy problem; retain the prior rejection from this run because technical-successor/plan delivery belongs to Story 5.11. |
| P2-B5 | Blind hunter | medium | Story 5.11 `check_assessments` requires only a nonblank retirement surface, so an exempt PS14 receipt can satisfy its SM-3 loop. Rejected from this run: validating the final plan's Legacy Server retirement assessment belongs to the explicitly separate Story 5.11; this story makes no retirement claim. |
| P2-B6 | Blind hunter | medium | Carried R-B8: Story 5.11 `check_patches` checks no-change owner names/count but not their inspected revisions/hashes. Retain the prior rejection from this run: all-owner reconciliation is explicitly assigned to Story 5.11. |
| P2-B7 | Blind hunter | medium | Carried R-B6: Story 5.11 generation checks approval only at entry and later writes its receipt without a snapshot recheck. Retain the prior rejection from this run: technical-successor generation is explicitly assigned to Story 5.11. Story 5.10 retains its mutation-time receipt checks. |
| P2-B8 | Blind hunter | medium | Carried R-B7 for duplicate JSON members. Additionally, Story 5.11's ordinary JSON reader admits null/array roots whose `.get()` raises an uncaught AttributeError. Rejected from this run: this is the separately assigned technical/plan packet reader; no such reader is changed here. |
| P2-B9 | Blind hunter | medium | Story 5.11's offline proof retains every complete input chunk in `Responses.output` while bounding only `pending`, allowing unrelated complete frames to grow the transcript until the deadline. Rejected from this run: the published offline proof supports Story 5.11's product-claim reconciliation, explicitly separate from these inventory amendments. |
| P2-B10 | Blind hunter | medium | Carried R-B3: Story 5.11 checks the approved AI.Tools revision's ancestry but reads that revision's document bytes rather than the actual descendant gitlink's bytes. Retain the prior rejection from this run: the intent excludes the AI.Tools plan/gitlink and assigns reconciliation to Story 5.11. |
| P2-E1 | Edge cases | medium | Carried R-B6, same root cause as P2-B7: approval arriving during Story 5.11 generation can be overwritten. Retain the prior Story 5.11 rejection without duplicating its disposition. |
| P2-E2 | Edge cases | medium | Story 5.11's incremental writes follow linked output files/parents and have no destination-symlink check; the reviewer reproduced an external overwrite. Rejected from this run: technical-successor generation is explicitly assigned to Story 5.11. Story 5.10's existing parent-symlink refusal remains tested. |
| P2-V1 | Verification gaps | medium | Pre-verified: removing Story 5.11's populated SM-3 receipt state/authority/date checks leaves all seven CompletionBindingTests passing; its only met case has no receipt. Rejected from this run: tests for the final plan's retirement assessment belong to the explicitly separate Story 5.11, and this story asserts no retirement. |

After individual verdicts: one patch (P2-B2), twelve findings rejected from the explicitly separate Story 5.11 work, including carried prior dispositions. No new deferral or intent/specification loopback is needed. Approved inventories, receipts, register, authorization and patches remain unchanged.

Resolution: P2-B2 is patched by supplying both historical parent README blobs in the existing consumer fixture, without stubbing the real delivery checks. Parent verification passes all 36 Story 5.10 tests and all three affected Story 5.11 lifecycle tests; all nine recorded checks pass, including both default verifiers, unchanged adopted AD-23, exact completion/regeneration refusals and whitespace. The final five source/test hashes and all twelve protected hashes are unchanged across verification. Every frozen matrix case has a covering test recorded as passed. Evidence: [parent verification](evidence/story-5-10/review-pass2-after-review-checks.json), [verification notes](evidence/story-5-10/verification.md) and [final scan](evidence/story-5-10/secret-scan-build-pass2-reviewed.json). The story remains in-review and sprint remains review because upstream labels are unintegrated; existing CI failures and earlier approved-byte deferrals remain open. No commit, push, upstream checkout change, enrollment or retirement occurred in this run.

### Build review of pass-3 fixes, 2026-11-22

The three reviewers examined the eight reopened items against the freshly pulled McpCli main. The original inventory approval baseline remains the basis for the historical source checks.

| Finding | Verdict | Evidence and disposition |
| --- | --- | --- |
| Blind 1 | Medium | MSBuild splits a literal semicolon-delimited Include into separate items. The first verifier compared the whole attribute to a package ID. Cover individual marked items. |
| Blind 2 | Medium | A later marked Update can enroll an existing Include. Account for updates to declared package IDs. |
| Blind 3 | Low | A parseable XML document with a different root supplied an empty package set. Require an MSBuild Project root. |
| Blind 4 | Medium | An unknown XML encoding raises LookupError before the project-specific parse diagnostic. Handle the encoding error through both completion commands. |
| Blind 5 | Low | Two enrollment fixtures put items directly under Project. Move the items into ItemGroup so the fixtures describe valid declarations. |
| Blind 6 | Low | The independent test fixture specified the three current mutable files. Check its membership against the production list so future additions also require coverage. |
| Blind 7 | Low | Both owners verify the same immutable enrollment blobs during independent delivery checks. The extra Git reads affect local completion only. Keep each delivery check self-contained for the Story 5.11 historical caller. |
| Blind 8 | Medium | The first receipt identified failed subtests and hashed stderr. Include the observed assertion for each failure in the final receipt so the attribution can be checked offline. |
| Blind 9 | Medium | Counts alone cannot establish the history of changed ledger text. Run the verifier and full consumer suite from the exact starting commit and compare their diagnostics with the final checks. |
| Edge 1 | Medium | The manifest treats metadata names case-insensitively. Read both attribute and child metadata with that rule when verifying declared enrollment. |
| Edge 2 | Medium | The multiple-Include case also occurs for a target following another package in the same attribute. Cover it with Blind 1. |
| Edge 3 | Medium | Marked Update metadata was missed when the corresponding Include had no marker. Cover it with Blind 2. |
| Edge 4 | Low | A different root element cannot establish absence of enrollment in a project. Cover it with Blind 3. |
| Edge 5 | Medium | The unsupported-encoding traceback bypassed the documented one-line refusal. Cover it with Blind 4. |
| Edge 6 | Low | An independent fixture list catches removal from the production set but also needs to detect additions. Cover it with Blind 6. |
| Edge 7 | Low | The historical verification paragraph referred to publication commits formerly listed in the introduction. Link to the dated publication evidence. |
| Verification 1 | Medium | Uppercase TRUE was recognized in code but every refusal fixture used lowercase. Pin case-insensitive marker values through both commands. |
| Verification 2 | Medium | Story 5.11 supplied current enrollment files for its simulated historical commit. Bind both files to historical inputs and exercise the later-enrollment case. |
| Verification 3 | Medium | The reviewer reproduced the unknown-encoding traceback through the integrated fixture. Cover it with Blind 4. |

All eight pass-3 action items are checked. The final full Story 5.10 suite passed all 39 tests, including the five frozen matrix scenarios. Both candidate verifiers passed. Both completion commands returned the outstanding label-integration diagnostic. All 14 protected file hashes matched. Story 5.11 ran 27 tests on the untouched starting commit and the final build. The same 12 assertions failed across the same seven methods on both checkouts. The Story 5.10 historical-delivery consumer passed with its fixed historical inputs. Story 5.10 remains in review pending the five owner README labels. [Final check record](evidence/story-5-10/review-pass3-after-review-checks.json) · [Evidence scan](evidence/story-5-10/secret-scan-build-pass3-reviewed.json)
