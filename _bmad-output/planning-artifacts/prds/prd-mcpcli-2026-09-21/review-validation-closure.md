# Validation-closure consistency review

- **Reviewed:** current prd.md, addendum.md, .memlog.md, reconcile-validation-report-2026-09-22.md, the original validation folder, the architecture spine, pinned EventStore source, and the three synchronized agent-instruction entry points.
- **Validation input:** validation-2026-09-22-0901/validation-report.md
- **Verdict:** **Pass.** Every C1-C6 and R1-R4 finding is resolved in the normative PRD/addendum contract or is an explicit downstream obligation with an owner and implementation-time revisit gate. The amendments introduce no new contradiction with the decision log, pinned source contracts, or synchronized repository guidance. A post-polish regression review also passed with zero critical, high, or medium findings.
- **Findings:** 0 critical, 0 high, 0 medium, 0 low.

## Remaining critical/high findings

None.

## Original validation closure matrix

| Finding | Disposition | Exact closure evidence | Remaining work and classification |
|---|---|---|---|
| C1 — Decoration Package excluded by the allowlist | **Resolved** | PRD §4, prd.md:99, distinguishes this repository's Decoration Package from the exhaustive external Hexalith/domain allowlist and permits exposed Contracts Libraries to reference the dependency-free package. | **Explicit downstream obligation, not a PRD defect:** architecture owns AD-15 alignment before the dependency-closure test or Module pins (PRD §10.1, prd.md:525, 528). |
| C2 — architecture records cannot emit the normative public results | **Resolved** | PRD §0, prd.md:13, makes addendum §G normative; addendum.md:259-395 exhaustively defines required/optional members, types, constraints, omission, examples, and error carriage. | **Explicit downstream obligation:** architecture owns AD-5/12 and output-schema alignment before either Head or its schemas (PRD §10.1, prd.md:525, 532). |
| C3 — Tenants example casing conflicts with Module serialization | **Resolved** | Addendum §G, addendum.md:265-266, separates camel-case outer records from Module-preserved schema/example casing; the Tenants schema/example uses TenantId (addendum.md:318-320). | **Explicit downstream obligation:** architecture owns AD-6/7 casing alignment before Schema/Catalog implementation (PRD §10.1, prd.md:525, 529). |
| R1 — unmarked *Id schema contradiction | **Resolved** | PRD FR-7 preserves ordinary serializer-derived schema and makes the suffix lint-only (prd.md:237-240); memlog decision 74 explicitly supersedes the earlier plain-string clause. | **Explicit downstream obligation:** architecture owns AD-8 alignment before Schema/Catalog implementation (PRD §10.1, prd.md:525, 529). |
| R2 — missing-URL applicability undefined | **Resolved** | Addendum §E makes URL execution-only (addendum.md:203); FR-9 discovery is offline and describe submittable is precisely head-level readiness (prd.md:260-261). | **Explicit downstream obligation:** architecture owns AD-13 alignment before settings resolution (PRD §10.1, prd.md:525, 530). |
| R3 — Parties command subset tentative | **Resolved as a durable delivery gate** | FR-20 compares included canonical names publicly and contract types internally (prd.md:403); FR-21 requires a versioned include/exclude inventory, rationale, decorated type, version, and maintainer approval (prd.md:410-411). | **Owned upstream obligation:** Parties maintainer approves the inventory before decoration (prd.md:480); McpCli maintainers own the migration plan (prd.md:407). Routing choice is owned by the Parties maintainer and revisited before decoration (prd.md:537). |
| R4 — lint outcome absent from the normative result | **Resolved** | PRD FR-4 defines all four classes and pointer behavior (prd.md:189-190); addendum §E/G makes lintFindings always present and defines exact codes, required fields, property optionality, and empty-array behavior (addendum.md:193, 263-274, 326-332). | **Explicit downstream obligation:** architecture owns AD-5/12 output-record alignment before either Head/output schema (prd.md:532). |
| C4 — SM-1 could pass without Folders | **Resolved** | The schedule makes both Projects and Folders SM-1 gates (prd.md:474-475), and SM-1 names Tenants, Parties, Projects, and Folders (prd.md:503). | **Owned follow-on delivery:** Projects and Folders maintainers complete their respective Gateway-ready work after v1; the three-month metric remains unchanged. |
| C5 — two synthetic Modules violate the one-Module fixture boundary | **Resolved** | PRD §4 permits one synthetic sample Contracts Library (prd.md:99); memlog decision 80 fixes one declared sample Module with the other Identifier Kind constructed in isolation. | **Explicit downstream obligation:** architecture owns fixture alignment before the fixture story (PRD §10.1, prd.md:525, 527). |
| C6 — handoff lists completed amendments as pending | **Resolved** | PRD §10.1 marks the earlier handoff complete, links its verification, and replaces it with six story-aligned gates while allowing unaffected work to proceed (prd.md:523-532). | No stale handoff remains. The six current items are deliberately timed downstream obligations owned by architecture. |

## Reviewer-gate recheck

The four findings in the preceding validation-closure review are closed:

- **Former H1, repository instructions:** AGENTS.md:107, CLAUDE.md:107, and .github/copilot-instructions.md:107 now all say that message ID is generated per call while idempotency is optional and caller-supplied only. Their SHA-256 hashes match, scripts/check-agent-instructions-sync.sh passes, and the append-only memlog records the synchronized change.
- **Former H2, pre-initialize MCP channels:** FR-6 and FR-14 require every pre-initialize MCP failure to write one structured error to stderr, emit zero stdout bytes, and exit 2; initialized failures use MCP/JSON-RPC only (prd.md:229, 321). Addendum §G carries the same exception, and the append-only memlog records the general rule. Architecture channel alignment is explicitly gated at prd.md:532.
- **Former M1, idempotency parity:** SM-4 masks only generated message and correlation identifiers, requires exact caller-supplied idempotency equality/presence, and requires omission from both Heads when absent (prd.md:506).
- **Former M2, Parties type verification:** FR-20/FR-21 compare canonical Operation Names with list_operations, then separately verify decorated contract types using an internal Catalog descriptor, generated manifest, or reflection test; public output is not expanded with CLR names (prd.md:403, 410-411).

## Requested contract checks

- **Idempotency:** coherent across PRD §4/FR-16/FR-17/SM-4, addendum §§E/G, memlog decisions 83 and 96, and the agent instructions. Pinned SubmitCommandRequest defines IdempotencyKey as optional caller input, and SubmitCommandResponse has no replay/duplicate classification. The stricter product choice to require ULID form is deliberate and logged.
- **§10.1 timing:** all six architecture mismatches have an architecture owner and a before-story/before-implementation revisit gate. They remain real differences in the present architecture spine, but they are explicit downstream obligations rather than defects hidden in the PRD.
- **Lint:** the normative contract includes hollow_description, missing_property_description, unmarked_identifier_like_property, and payload_paging_member; property-level findings use RFC 6901 pointers, operation-level findings omit property, and [] is the no-finding value.
- **Strict/startup channels:** generalized beyond strict mode to every pre-initialize MCP failure, with stderr-only structured error and empty stdout.
- **Gateway errors:** addendum §G requires code, status, and non-empty detail, using exception Detail with Title fallback; reason, retryable, clientAction, retryAfter, and correlationId are optional and omitted when absent. This matches the nullable pinned EventStoreGatewayException members.
- **Query paging:** paging requires positive pageSize when present; offset, nextCursor, totalCount, and hasMore are independently optional. This matches pinned QueryPagingMetadata.
- **Head arguments and submittable:** addendum §E assigns arguments by Head (addendum.md:177-193); describe submittable reports only Read-only/URL surface availability while tenant, actor, Payload, and per-call Envelope checks remain execution-time validation (prd.md:260-261).
- **Parties inventory:** the versioned, owner-approved inventory is the scope authority; canonical public-name coverage and internal decorated-type verification are separate mandatory gates.
- **Latest implementability refinements:** the zero-module-specific-code guardrail now expressly permits pinned Contracts references and dependency-graph-generated scan metadata (prd.md:100); correlationProperty is command-only, omitted correlation resolves to the generated message ID, and supplied/omitted fixtures are required (prd.md:140, 340, 343-344); describe exposes idempotencyKeyRequired for non-nullable decorated properties (prd.md:260, 354; addendum.md:272, 288); and gateway_error preserves the actual exception status, including malformed/semantic 2xx failures (prd.md:282; addendum.md:372-384).

## Downstream obligations, not findings

The current architecture spine still contains the superseded record shapes, suffix typing, generated idempotency, unconditional missing-URL rejection, two-Module sample fixture, and incomplete startup-channel wording at ARCHITECTURE-SPINE.md:83, 101, 107, 131, 187-193, and 238. PRD §10.1 identifies the architecture as owner and gates each affected implementation area before work may rely on those decisions. This review therefore does not relabel those known, explicitly scheduled alignments as PRD defects.

Other open items also have durable ownership and revisit conditions: HTTP authentication (architecture, before the HTTP story), Parties routing (Parties maintainer, before decoration), deletion order (product owner, when the migration plan is drafted), and upstream dates (product owner plus Tenants/Parties maintainers, before publishing the Decoration Package), at prd.md:536-539.

## Verification evidence

- Agent instruction synchronization: passed scripts/check-agent-instructions-sync.sh; all three files hash to 58ea5f302f11b60a01597aca0c49d5975a4e6f8157ce6d94970d65ade09e3a4f.
- Final reviewed fingerprints after editorial polish and finalization: prd.md 0208226f781f28920d49bf1bbe42868de99e1c372b2382b1407354e9f2a47e45; addendum.md fa8a994d7c4ca7da8b541f848d7c287c3d76c3aa6293d84705c92a15ef308451; .memlog.md 9ca8bdfc817d650f2b2978d12afd1910429582f7ab4a5b33c227f069a2104777.
- This is requirements/consistency validation, not implementation certification or proof that upstream Module inventories and decorations already exist.
