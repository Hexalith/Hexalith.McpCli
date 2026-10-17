---
title: '4.4 Approve ChatBot and Memories migration inventories'
type: 'chore'
created: '2026-10-17'
status: 'ready-for-dev'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '_bmad-output/implementation-artifacts/epic-4-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** ChatBot and Memories have no source-pinned migration inventories.
Their legacy tools and CLIs carry context, authorization and behavior that a
generic Gateway call cannot implicitly replace.

**Approach:** Finalize linked, versioned inventories outside `src/`, with one
row per concrete surface, explicit variants and exclusions, security classes,
replacement gaps and actual approval references. Proposed current scope is
`defer / exclude`, retaining legacy capabilities while prerequisites remain.

## Boundaries & Constraints

**Always:** Pin ChatBot source
`acc934599cf1efff36b0643eddc6a3cc4c2978d5` and Memories source
`f6b60d5a2e9b81d84fddad789c7d9bed40d3a533`. Account for ChatBot's 12 MCP
tools and 12 CLI leaves; Memories' four MCP tools, 14 implemented CLI leaves
and four executable stubs. Distinguish stubs, adjacent REST capabilities and
unsupported resources from implemented agent operations.

Preserve ChatBot task/actor/tenant/correlation provenance, separate business
correlation and task-intent IDs, approval/retry/concurrency controls, routing
and enriched or compound submissions. State how each context would travel
through Payload, allowed Envelope metadata or operator settings. Such mappings
remain future proposals and confer no authenticated authority.

Record Memories ingress JWT, tenant membership and subject provenance, upstream
bearer propagation, search/traversal/ingestion behavior and CLI administrative
boundaries. Its Legacy Server remains nondeletable until the HTTP release
supports forwarded per-user identity and authorization, behavior and release
gates pass. Explicitly exclude non-Gateway variants, erasure, key rotation and
resource/stream behavior; no absent row establishes parity.

Use canonical operation names and exact decorated CLR types only for established
Gateway-ready replacements. Neither inspected Contracts package declares
McpCli operations; existing DTOs and plain commands alone supply no readiness.
Record approval authority honestly: session approval cannot assert external
owning-maintainer sign-off. Missing owner evidence remains an open owner gate.

**Never:** Change runtime, upstream source, dependencies, enrollment, publication,
retention or submodule pointers. Introduce module-specific executor paths,
resources/prompts, typed tools, dynamic plug-ins, executor retries, event stream
reading or v1 HTTP identity. Trust payload identity, relax canonical ULIDs,
execute migrations or infer withdrawal/deletion permission from an inventory.

**Approved decision (2026-10-17):** The requesting user answered "approve and
stop" to the recommended session scope: all rows in both source-pinned
candidates remain `defer / exclude`, retaining legacy capabilities. This
approves the spec for later finalization; external owning-maintainer sign-off
remains unasserted. Stop at `ready-for-dev` before implementation and review.

</frozen-after-approval>

## Code Map

- ChatBot `src/Hexalith.ChatBot.Mcp/ChatBotMcpToolCatalog.cs` and
  `ChatBotMcpTools.cs` declare the 12 tools;
  `src/Hexalith.ChatBot.Cli/ChatBotCliCommands.cs` declares corresponding CLI
  leaves. The inventory supplies exact source paths/lines; reuse its map.
- ChatBot services and Server Gateway stages own caller context and admission;
  Contracts command records are plain source types. Preserve the distinction
  between a business retry command and forbidden generic executor retries.
- Memories `src/Hexalith.Memories.Mcp/McpCompositionRoot.cs:81` registers four
  tools. `Authentication/` owns JWT/tenant checks; `McpCompositionRoot.cs:67`
  configures scoped bearer forwarding. CLI `Commands/RootCommandFactory.cs:106`
  declares wired leaves and `:84` the four stubs. Contracts `V1/` contains REST
  DTOs, not decorated queries.
- McpCli `src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs:127` fills
  trusted actor/tenant properties; `:149` handles Command correlation and
  extensions; `:259` builds Queries without correlation or extensions.
- Follow Story 4.3's distinction between session approval and external owner
  sign-off. Keep README and runtime unchanged: this story changes documents.

## Tasks & Acceptance

**Execution:**

Paths below are under `_bmad-output/implementation-artifacts/`.

- [ ] `chatbot-migration-inventory-v1.md` — finalize source-pinned rows, context
  handoffs, security classes, prerequisites and actual approval references.
- [ ] `memories-migration-inventory-v1.md` — finalize source-pinned rows,
  identity and administrative boundaries, exclusions and retirement gate.
- [ ] `evidence/story-4-4/verification.md` — preserve repeatable exact source-set,
  row, variant, reference and approval checks, including negative mutations.
- [ ] This spec and `sprint-status.yaml` — synchronize after applicable approval,
  implementation, review and verification gates pass; preserve unrelated work.

**Acceptance Criteria:**

- Given pinned sources, when completeness is checked, then all 42 implemented
  surfaces and four CLI stubs have distinct rows, with variants explicitly
  accounted for and no unimplemented capability asserted as working.
- Given any row, when assessed, then disposition, coverage, rationale, security,
  replacement or unresolved gap and actual approval are explicit; pending
  approval cannot be mistaken for an approved inventory.
- Given ChatBot context, when future replacement is assessed, then task,
  actor, tenant and both correlation roles retain explicit generic handoffs
  without a module-specific executor or payload-derived authority.
- Given Memories per-user operations, when retirement is assessed, then missing
  forwarded identity, exact Gateway contracts or authorization/behavior/release
  evidence keeps its Legacy Server nondeletable.
- Given non-Gateway resources or unsupported variants, when scope is assessed,
  then explicit exclusions retain gaps instead of implying parity or retirement.

## Implementation Notes

- 2026-10-17: Recorded "approve and stop". Candidate finalization and required
  review remain pending. Resume implementation under this approval without
  seeking the same scope approval again.

## Spec Change Log

## Review Triage Log

## Verification

- Execute the evidence document's candidate/final source and row checks; expect
  exact source revisions, sets, valid anchors and honest approval state.
- Reject in-memory missing/duplicate rows, incorrect surface associations,
  false approval, unsupported inclusion and a weakened Memories identity gate.
- Run `git diff --check`; inspect local Markdown/YAML and upstream HEAD/status.
  No .NET build applies to these document-only artifacts. Static checks supply
  no live Gateway, authorization, persisted-effect or release proof.
