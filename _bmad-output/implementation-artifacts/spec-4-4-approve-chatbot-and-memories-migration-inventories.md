---
title: '4.4 Approve ChatBot and Memories migration inventories'
type: 'chore'
created: '2026-10-17'
status: 'done'
baseline_commit: '2833aafba8ddf49222774a39eea5bf05a744f878'
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

- [x] `chatbot-migration-inventory-v1.md` — finalize source-pinned rows, context
  handoffs, security classes, prerequisites and actual approval references.
- [x] `memories-migration-inventory-v1.md` — finalize source-pinned rows,
  identity and administrative boundaries, exclusions and retirement gate.
- [x] `evidence/story-4-4/verification.md` — preserve repeatable exact source-set,
  row, variant, reference and approval checks, including negative mutations.
- [x] This spec and `sprint-status.yaml` — synchronize after applicable approval,
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

- 2026-10-17: Recorded "approve and stop" at the approval checkpoint. The
  subsequent build request resumed finalization under the same session scope;
  no second scope approval was requested.
- 2026-10-17: Finalized both inventories at 1.0.0. All 88 scope rows reference
  actual A1 session approval for `defer / exclude`; external owning-maintainer
  sign-off remains unasserted. Preserved ChatBot context/routing/concurrency
  handoffs and Memories identity, administrative and non-Gateway gaps.
- Concurrent external reference updates advanced the ChatBot checkout beyond
  the mandated pin. Verification uses read-only pinned Git objects and reports
  current HEAD/status separately; no upstream source or gitlink was changed by
  this implementation. Required workflow review and final status synchronization
  completed; the spec is done and sprint tracking is at the workflow's `review`
  handoff.
- 2026-10-17: The requesting user completed the human walkthrough with
  "apply recommended". Recorded the limited acceptance and future implementation
  preferences below; sprint tracking now advances from `review` to `done`.
  Frozen intent, source pins, scope rows and external owner gates are preserved.

## Spec Change Log

- 2026-10-17: Completed the three document execution tasks and replaced pending
  candidate checks with final approval/source-object checks and negative
  mutations. Approved intent, dispositions, source pins and authority limits
  are unchanged.
- 2026-10-17: Applied the human walkthrough recommendation: prefer explicit
  payload task provenance, clarify Command-only actor binding, retain module
  workflows and Memories identity/retirement gates, and record incremental
  future migration. Completed the human review tracking transition without
  changing runtime, approval authority or any row disposition.

## Human walkthrough decision (2026-10-17)

The requesting user instructed **"apply recommended"** after the walkthrough
and the explanation of each proposed solution. This accepts Story 4.4 as the
session-scoped inventory milestone and completes its human review. The spec
and sprint story are `done`; all 88 inventory scope rows retain `defer / exclude`.
The earlier A1 record remains the source of that limited disposition approval;
this follow-up records the reviewed planning preferences without asserting
external owning-maintainer sign-off or approving a future replacement contract.

- Reuse generic Envelope tenant selection and command correlation. The owning
  boundary must authorize the authenticated caller for the resolved tenant;
  operator actor strings supply provenance only.
- Prefer a declared Payload field with explicit identifier validation when
  task provenance is required. Use Command extensions only after their owner
  defines and approves the semantics and validation. Current Queries have no
  extension/correlation channel or ActorProperty binding; preserve that gap
  until an upstream contract or later transport decision resolves it.
- Keep business correlation and task intent distinct from submission correlation
  and provenance task IDs. Declare aggregate routing upstream and preserve
  approval/proposal version inputs as business concurrency controls.
- Retain existing module admission, payload enrichment and compound workflows.
  Planning may attempt external effects before EventStore submission; a refusal
  alone does not establish that nothing happened. McpCli gains no module-specific
  executor path or retry behavior.
- Retain Memories until the later HTTP transport supports forwarded per-user
  identity and all owner, authorization, behavior and release gates pass. Reuse
  existing identity infrastructure. Non-Gateway and destructive exclusions stay
  explicit, and legacy retirement remains a separate authorized change.
- Keep the bounded static verifier and focused human source interpretation.
  Future migration should establish one bounded operation through both generic
  heads after its prerequisites pass, with operation-specific authorization and
  behavior evidence before expansion. No operation is selected or included now.

## Review Triage Log

| ID | Verdict | Route | Evidence and decision |
| --- | --- | --- | --- |
| BH01 | false | reject | The six reference movements and dependency-policy edits were concurrent external work observed during implementation. This story changed only its five document/tracking files; the workflow requires the review snapshot to include all changes since baseline. Preserve the unrelated edits and do not claim or commit them as Story 4.4. |
| BH02 | false | reject | The no-.NET-validation statement is explicitly about this document-only story. The concurrent dependency edits are not implementation output or evidence for this story; their validation belongs to their owning work. |
| BH03 | medium | patch | Reproduced: appending an overriding duplicate approval key passes the first-match metadata parser while a YAML consumer can read a different value. Reject duplicate frontmatter keys and add a negative mutation. |
| BH04 | medium | patch | Reproduced: swapping both ChatBot M01/M02 and L01/L02 names passes the inventory-derived association check with wrong rationales and anchors. Derive expected associations from pinned source instead of the inventory. |
| BH05 | low | reject | Reproduced: nonblank line-1 anchors pass. The evidence explicitly promises file existence, bounds and nonblank lines and disclaims semantic proof for prose; source interpretation is separately reviewed. Automatically proving every cited behavior would add substantial source-text coupling for a contrived bulk replacement, beyond a direct correction. |
| BH06 | medium | patch | Reproduced: deleting all G rows passes despite removing owning handoffs required by this scope. Check the expected gate IDs and nonempty owner/prerequisite fields and reject missing gates. |
| BH07 | medium | patch | Reproduced: replacing Memories' post-HTTP authorization/behavior/release conditions with identity-only sufficiency passes. Protect the full necessary retirement conditions and add a negative mutation. |
| BH08 | medium | patch | Reproduced: removing the complete A1 Limits paragraph passes while dropping explicit publication/withdrawal/retention/retirement restrictions. Check those authority limits and reject their removal. |
| BH09 | medium | patch | Reproduced: erasure prerequisites in V14 can be replaced with filler while IDs/cell checks pass. Protect required erasure, retention and key-rotation exclusions and add a negative mutation. |
| BH10 | medium | patch | Reproduced: an unrelated source_repository URL passes beside the required module/revision. Validate the exact pinned repository URL and reject a wrong URL. |

The edge-case layer returned no findings; the verification-gap layer reported
no verification gaps. BH03/04/06/07/08/09/10 share the incomplete static-integrity
checks root cause and route to one bounded evidence-check patch. No intent or
scope change is required; no review deferral is created.

All seven patch findings are resolved in the embedded verifier: duplicate keys,
pinned-source associations, prerequisite-owner gates, complete retirement
conditions, A1 authority limits, destructive exclusions and repository provenance
now have rejecting mutations. The parent reran the complete evidence block and
all 50 negative mutations passed. There are no remaining accepted findings and
no new deferred work.

## Verification

- Execute the evidence document's candidate/final source and row checks; expect
  exact source revisions, sets, valid anchors and honest approval state.
- Reject in-memory missing/duplicate rows, incorrect surface associations,
  false approval, unsupported inclusion and a weakened Memories identity gate.
- Run `git diff --check`; inspect local Markdown/YAML and upstream HEAD/status.
  No .NET build applies to these document-only artifacts. Static checks supply
  no live Gateway, authorization, persisted-effect or release proof.

- 2026-10-17 implementation validation: executed the complete Bash block in
  `evidence/story-4-4/verification.md` via Python
  `subprocess.run(['bash', '-e'], input=block, text=True)`; exit 0. Verified exact
  pinned source sets, all 88 A1 scope rows, local link fragments/source anchors,
  13 ChatBot and 15 Memories negative mutations, absent Contracts decorations
  and MCP resources/prompts, and the unchanged frozen approval block SHA-256
  `6fcb8a85a4ea996683371a2b173b63678dc17635138657bcfabfff8a00a85a74`.
  `git diff --check` passed. No .NET build applies to these document-only changes;
  external owner, live security/behavior and retirement gates remain open.

- 2026-10-17 final validation after review fixes: the parent reran the complete
  Bash evidence block; exit 0 with 24 ChatBot and 26 Memories rejecting mutations,
  exact pinned source/surface sets, all 88 limited A1 references, source/link
  checks, absent decorations/resources/prompts and unchanged frozen-intent hash.
  Markdown frontmatter and sprint YAML parsed successfully; `git diff --check`
  passed. All four execution tasks and all five acceptance criteria are complete.
- Local completion message validated after `npm ci` with the pinned commitlint
  21.2.2 CLI: `npx --no -- commitlint --verbose` read the temporary message file
  and exited 0 with `found 0 problems, 0 warnings`. The exact validated message
  is `docs(review): complete story 4.4 verification and tracking`; successful
  output is preserved in `/tmp/story-4-4-commitlint.BurJ8f`.
- 2026-10-17 walkthrough completion validation: the complete evidence Bash block
  exited 0 with all 88 scope rows and all 50 negative mutations passing. Separate
  hashes confirmed unchanged frozen intent, inventory frontmatters and all
  scope/prerequisite rows. Frontmatter and sprint YAML parsed successfully;
  `git diff --check` passed. No runtime, dependency or upstream change was made.
