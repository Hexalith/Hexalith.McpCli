---
title: '5.9 Refresh and re-disposition Projects and FrontComposer inventories'
type: 'chore'
created: '2026-11-16'
status: 'ready-for-dev'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-5-context.md'
story_key: '5-9-refresh-and-re-disposition-projects-and-frontcomposer-invent'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The Projects (latest 2.0.0, session-approved by Projects Story 6.6) and FrontComposer 1.0.0 inventories are pinned to revisions that are stale or not ancestors of the root gitlinks. Their 46 legacy Projects rows and 26 FrontComposer rows are all still `defer / exclude` under session approvals, with `external_maintainer_approval: unasserted`. Meanwhile, Projects has decorated four reads (T01–T04) and AD-23 has been adopted.

**Approach:** Produce additive successors: Projects 2.1.0 (from 2.0.0) and FrontComposer 1.1.0 (from 1.0.0). Re-pin each to the root gitlink in HEAD when this spec is approved (currently Projects `bf9f98969efa036fd60700c627e712b4375e654a` and FrontComposer `33e71036c04f2b99955376e9c90cbb1fc3a81e64`; recheck before writing). Re-disposition every entry under the adopted AD-23 class map and record the coupled host/plug-in retirement gate. Gate the successors with a story verifier, then obtain exact-byte owner approval and integrate the PS03/PS04/PS08/PS09 label citations.

## Boundaries & Constraints

**Always:**
- Account for every predecessor entry exactly once: Projects T01–T04, R11, M5, L18, V12 and G6; FrontComposer H3, D13, C2, V8 and G4. Give each entry anchors at the new pin and a drift status: unchanged, or the change.
- Each row's disposition follows its AD-23 class (restriction precedence applies):
  - `replace` requires a type decorated at the pin, with its wire name, exact Gateway route and eligibility. A Projects `replace` also requires the enrolled decorated Contracts candidate whose closure fits `tools/dependency-policy.json`.
  - `include` appears only with `replace`.
  - `withdraw` names the owner rationale, the replacement experience and the accepted loss.
  - `defer` names a gap and its owner.
- Task and actor context travels only as Payload properties, through `actorProperty`, or in allowed Envelope extensions. A read that needs context with no such channel stays `defer` with that gap.
- The coupled gate names every host consumer that must move before the FrontComposer host and the Projects plug-in retire together (FK01–FK04), and it records the separate treatment of the compiler CLI (K13).
- Any FrontComposer `replace` row carries the FV04 and FV08 machine-result and exit-code parity clarifications.
- The approval replaces `unasserted` with the roles it covers under the single-maintainer model, and it supersedes A1 and the 2.0.0 session decision.
- Keep the evidence packet proportionate: one generator, one candidate verifier, one label verifier and their tests.

**Never:**
- Rewrite Projects 1.0.0 or 2.0.0, FrontComposer 1.0.0, AD-23, technical 1.0.3, earlier receipts, or anything in `references/`.
- Change Projects' enrollment files, production code, dependencies, census, gitlinks, or the AI.Tools plan (Story 5.11 indexes the successors).
- Enroll, publish, execute, or claim parity or retirement.
- Convert legacy formats silently.
- Commit or push without explicit authorization.

**Decisions (2026-11-16):**
- **Pin: "Proceed, pin at approval".** Pin each module to the HEAD gitlink at approval, and read sources only from git objects.
- **Legacy reads: "Replace now".**
  - L01–L07, R01, R02, R04, V01 and V02 become `replace / include`, mapped to T01–T04 per Projects UX-DR19.
  - The owner accepts these differences:
    - no resource URIs or subscriptions;
    - explicit `--aggregate-id` instead of the first-visible default;
    - envelope paging up to 200 instead of the 25/50/100 caps;
    - Safe Metadata by default;
    - file IDs no longer score in trace;
    - McpCli JSON errors and exit 2.
  - Projects 6.7 cutover and DW-82 publication remain retirement prerequisites.
- **Losses: "Accept all".** The owner accepts the losses for every withdrawal-class row:
  - Projects:
    - R05, R11 (K07);
    - L12, L13, V04, V11, V12 (K15);
    - V07 (K08);
    - M01–M04, L14–L17, V05, V06, V10 (K12; they move to the confidential Web/Chatbot UI, with UI evidence before retirement).
  - FrontComposer:
    - H01, V01 (K08);
    - D01–D13 (K07);
    - C01, C02, V06–V08 (K13; exempt and retained, never counted retired).
- **Main sync: "Integrate now".** Before implementation, run `git pull --rebase` on `main` so that HEAD contains `ab92da41988c4d423c05ea3f5ab401ed0db1fc32`.
- **Spec size: "Keep full spec".**

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Complete candidates | Both successors + pins + AD-23 map + predecessors | Verifier passes; receipt stays pending | N/A |
| Invented replacement | `replace` without a decorated type at the pin, wire/route mismatch, or `include` without `replace` | Reject, naming `module:id` | nonzero exit, exact stderr |
| Class drift | Disposition contradicts the AD-23 class (e.g. K12 not `withdraw`), `withdraw` without a loss, `defer` without a gap/owner | Reject, naming `module:id` and class | nonzero exit |
| Damaged accounting | Missing/duplicate ID, unresolvable anchor, missing drift, gate without FK01–FK04 or K13 treatment, FrontComposer `replace` without FV04/FV08 | Reject with an actionable diagnostic | nonzero exit |
| Completion without approval or labels | Pending receipt or unintegrated label | Completion mode fails | nonzero exit |

</frozen-after-approval>

## Code Map

`A` = `_bmad-output/implementation-artifacts`, `E` = `A/evidence`, `P`/`F` = `references/Hexalith.{Projects,FrontComposer}` read through `git show <pin>:` (the working checkouts move).

**Predecessors and authority**
- `A/projects-migration-inventory-v2.md` (on `origin/main`):
  - the 2.0.0 T01–T04 table and decision;
  - legacy rows with 1.0.0 anchors at `3d256e63`;
  - baseline `ce71717a`, an ancestor of the pin.
- `A/projects-migration-inventory-v1.md` (sha `252af571…`) and `A/frontcomposer-migration-inventory-v1.md` (sha `cde0f43a…`): the row shapes that the AD-23 map binds.
- `_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/AD-23-*.{md,json}`:
  - disposition rule `:246-252`; precedence `:38-45`; classes `:70-83`, `:125-128`;
  - K12 `:178-188` (Projects maintenance `:181`); K13 `:206-213`, `:223-226`;
  - Projects policy `:573-599`; FrontComposer policy `:601-616`; roles `:320-321`.
- Classes by row:

  | Module | K01 | K02 | K03 | K04 | K07 | K08 | K10 | K12 | K13 | K15 |
  |---|---|---|---|---|---|---|---|---|---|---|
  | Projects | M05, L01–L11, L18, V02 | R01–R04, R06–R10 | V01, V03 | V08, V09 | R05, R11 | V07 | — | M01–M04, L14–L17, V05, V06, V10 | — | L12, L13, V04, V11, V12 |
  | FrontComposer | H02, V04 | H03, V05 | — | — | D01–D13 | H01, V01 | V02, V03 | — | C01, C02, V06–V08 | — |

**Projects at the pin** (identical to `4eed8caf` outside `_bmad-output`)
- Decorated (module `projects`, String kind, no projection selectors):
  - module: `P/src/Hexalith.Projects.Contracts/ProjectsMcpCliModule.cs:3`;
  - `Queries/ListProjectsQuery.cs:15-16` (wire `:52`);
  - `GetProjectQuery.cs:12-13` (`:30`);
  - `ResolveProjectFromConversationQuery.cs:10-11` (`:20`);
  - `ResolveProjectFromAttachmentsQuery.cs:10-11` (`:20`).
- No Commands are decorated.
- Owner mapping and UI-only rule: `P/_bmad-output/planning-artifacts/epics.md:229`, `:59`, `:1507`.
- Owner story status: 6-7 cutover, 7-6…7-14 Commands, 8-1 audit, 8-2 export, 8-4/8-5 and 8-7 packages are backlog; 8-11 is blocked.
- Drift:
  - `Mcp/`, `Cli/`, the submitter, the Client scan window and `Commands/` are unchanged (same lines).
  - Server reads gain a shared REST preamble (`Server/Queries/ProjectQueryRequestPreamble.cs:19,45`) that affects R01–R03, R05, L01–L03 and M05/L18.
  - L04/L05/V02: file IDs no longer score, and candidates are re-authorized (`ResolveProjectFromAttachmentsEndpoint.cs:85,100`, `ResolveProjectFromConversationEndpoint.cs:139`, deadlines `:47`/`:73`).
  - V09 is +4 lines (`ProjectsDomainProcessor.cs:112`, `:809`); supported Queries pass `taskId: null` (`Server/Authorization/ProjectAuthorizationGate.cs:32-47`).
  - G1: Contracts slimmed and UI split off (`src/Hexalith.Projects.UI.Contracts`).
  - G2: `ProjectReadQueryAdmission.cs:12-33`; gate `:417`/`:593`.
  - G4: handlers `ProjectsServerServiceCollectionExtensions.cs:163-166`.
  - Labels are at `README.md:7-8`.

**FrontComposer at the pin** (no Mcp/Cli/corpus/Counter.Web change since `11c8377a`; `81a440a8` is not an ancestor, so diff through merge-base `b06f86d5`)
- Changed:
  - H01/V01: lifecycle entries are bound to tenant and user (`Mcp/Invocation/FrontComposerMcpLifecycleTracker.cs:61`, `:134`; `FrontComposerMcpLifecycleStore.cs:140`, `:210-221`, `:373`).
  - V02: `/mcp` always requires an authenticated user (`Mcp/Extensions/FrontComposerMcpEndpointRouteBuilderExtensions.cs:52`, `:60-61`, `:81-106`).
  - V03: API-key scheme, and conflicting identities are refused (`Mcp/HttpFrontComposerMcpAgentContextAccessor.cs:100-101`, `:177`; `Mcp/FrontComposerMcpApiKeyAuthenticationHandler.cs:39-61`).
  - D11 body; D13 rendering.
  - C02/V07: link refusals (`Cli/WriteSafetyPolicy.cs:8-9`; `Cli/PathUtilities.cs:32`, `:61`).
  - V08: anchors shifted (`Cli/CliApplication.cs:13`, `:42`, `:55-57`).
- Otherwise unchanged; re-anchor from `git show`.
- Recount: 1 tool, 13 documents, 2 leaves; the catalog still covers only 9.1.0→9.2.0.
- Labels are at `README.md:32-33`.

**Coupled gate and parity inputs**
- FK01–FK04 come from `A/technical-tools-migration-inventory-v1.0.3.md:129-132` (G3 `:187`). Re-verify each at the gitlinks:
  - FK01: `P/src/Hexalith.Projects.Mcp/ProjectsMcpModule.cs:35`, `:51`, `:62`.
  - FK02: Counter.Web `/mcp` (`Program.cs:194`, `:236`).
  - FK03: Parties UI csproj `:66-67`.
  - FK04: FrontComposer test csprojs.
- No other consumer exists in the 17 gitlinks.
- FV04 and FV08: `E/story-5-1/verification.md:1473-1508`.

**Reuse**
- `E/story-5-8/{build_candidate.py,verify_amendment.py,test_verify_amendment.py}`: copy and adapt (`check_approval` `:226-243`, `completion_requested` `:262-270`, exact-stream tests, `sys.dont_write_bytecode`).
- `E/story-5-7/verify_labels.py` handles multiple repositories. Chain the new register to `E/story-5-8/labels.json`, taking the old PS03/PS04/PS08/PS09 rows from `E/story-5-7/labels.json`.
- Approval receipt: use the shape of `E/story-5-8/approval.json`, with "approve" for the candidates and a separate "authorize" for delivery.

**Leave unchanged:** `tools/inventory-coverage/v1/projects-*.json`, the Projects vectors and plans, AI.Tools plan 1.2.0 (`:57-58`), and technical 1.0.3. Ledger `deferred-work.md:682`: note that the re-pin resolves the Projects/FrontComposer part of the unpublished-pin entry.

## Tasks & Acceptance

**Execution:**
- [ ] Precondition: run `git pull --rebase` on `main`, confirm that HEAD contains `ab92da41` and that the Projects 2.0.0 bytes are present, and record the HEAD gitlinks as the pins. If the rebase conflicts, HALT.
- [ ] Write `A/projects-migration-inventory-v2.1.0.md`, `A/frontcomposer-migration-inventory-v1.1.0.md` and their `.gitattributes` (`-text`) entries, following the derivation rules below. Corrected premises go in the G/V cells and source sections. The approval stays pending.
- [ ] `E/story-5-9/build_candidate.py`: generate both successors deterministically from the predecessor bytes, the `git show <pin>:` sources and the AD-23 map. Refuse to overwrite an approved packet.
- [ ] `E/story-5-9/{verify_amendment.py,test_verify_amendment.py}`:
  - candidate and approved-completion modes;
  - per-module accounting against the AD-23 map;
  - every matrix row and disposition branch;
  - guard-removal controls, exit code and both streams.
- [ ] `E/story-5-9/{approval.json,labels.json,verify_labels.py,upstream/{projects,frontcomposer}/}`:
  - a pending receipt bound to the predecessor and successor hashes and their authorities;
  - README-only patches for PS08/PS09 (Projects) and PS03/PS04 (FrontComposer) that cite the successors;
  - the patches change a gate's text only where an amendment changes that gate.
- [ ] `A/deferred-work.md` (grep first), `E/story-5-9/verification.md`, the secret-scan receipt, this spec and `A/sprint-status.yaml`: record only the supported state.

**Acceptance Criteria:**
- Given the candidates, when the verifier runs, then every entry passes and all protected predecessor and authority bytes are unchanged.
- Given exact-byte owner approval and separate delivery authorization, when completion runs, then:
  - the receipts name the covered roles;
  - both owner READMEs on `origin/main` cite the successors;
  - nothing is enrolled, executed or retired.

## Design Notes

Derivation rules (the decisions above apply first):
- **Legacy reads:** L01 and R01 map to T01. L02, L03, L06, L07, R02 and R04 map to T02. L04, L05 and V02 map to T03/T04. V01 maps to T01/T02. Each row records the accepted differences, and its open gaps are DW-82 publication, live acceptance and 6.7 cutover.
- **Withdrawals:** each withdrawal row names its class, rationale, replacement experience and accepted loss.
  - K12 rows name the confidential Web/Chatbot UI (Projects 7.6–7.14 for UI coverage evidence) as a retirement prerequisite.
  - K07 documentation ships in packages, README and AI.Tools.
  - K13 rows cite AI.Tools amendment 1.2.0 and stay retained.
- **T01–T04:** `replace / include` stays unchanged. Re-anchor them at the pin. Open gaps: DW-82 publication, live acceptance and 6.7 cutover.
- **Rows with no decorated type:** `defer`, with owner Projects and the backlog story (8.1/8.2/8.4/8.5) or the K10 owner. This covers:
  - Projects: R03, R06–R10, L08–L11, M05/L18 and V03;
  - FrontComposer: H02, H03, V04, V05, V02 and V03.
- **V08:** takes the read correlation path on canonical ULIDs. Its command parts follow the K12 withdrawals.
- **V09:** stays `defer` for Commands and M05, with the gap "no Query extension channel". T01–T04 need no task context.
- **G rows:** each records its status at the pin.
  - Projects G6 and FrontComposer G4 become the coupled gate: FK01–FK04 move first; then the host and the Projects plug-in retire together, after K12 UI evidence and 6.7 cutover.
  - The compiler CLI is retained as K13-exempt and is excluded from the gate.

## Verification

**Commands:**
- `python3 -I A/evidence/story-5-9/verify_amendment.py`: passes on the pending candidates. With `--approved-completion`, it fails until approval and label integration.
- `python3 -I -m unittest discover -v -s A/evidence/story-5-9 -p 'test_*.py'`: passes, with every control detected.
- `python3 -I A/evidence/story-5-2/verify_class_map.py`: reports that AD-23 is still adopted.
- `python3 scripts/scan-evidence-secrets.py A/evidence/story-5-9 --receipt <task-owned path>` and `git diff --check`: both clean.

## Implementation Notes

- 2026-11-16: The user approved this spec with "approve and stop". The frozen intent and decisions are now locked; implementation resumes in a fresh `bmad-build` session.
  - Approval-time HEAD was `4c2bbd5f444922357acbd7fe05d08e2a31b985ed`, with gitlinks Projects `bf9f98969efa036fd60700c627e712b4375e654a` and FrontComposer `33e71036c04f2b99955376e9c90cbb1fc3a81e64`. These are the pins; recheck them after the required `git pull --rebase`.
  - At approval, local `main` was 3 ahead and 2 behind `origin/main`.
  - The `references/Hexalith.Platform` checkout was modified by another session and is not part of this story.

## Spec Change Log

## Review Triage Log
