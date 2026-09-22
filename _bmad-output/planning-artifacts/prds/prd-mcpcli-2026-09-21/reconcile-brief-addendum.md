---
title: "Reconciliation: Brief Addendum + Memlog vs PRD + PRD Addendum"
created: 2026-09-21
---

# Reconciliation

Inputs read in full:
- INPUT A: `briefs/brief-mcpcli-2026-09-21/addendum.md`
- INPUT B: `briefs/brief-mcpcli-2026-09-21/.memlog.md`
- Target: `prds/prd-mcpcli-2026-09-21/prd.md` and `prds/prd-mcpcli-2026-09-21/addendum.md`

Note: `brief.md` itself was not one of the two required inputs, so its prose (Problem/Success Criteria/Scope text) is reconciled only to the extent the memlog describes it.

## Coverage table

| Input item | Source | Where in PRD/addendum | Status |
|---|---|---|---|
| ModelContextProtocol SDK packages (Core/hosting/AspNetCore), static `[McpServerToolType]` declaration | A, SDK research | PRD §7 lists pinned package versions; PRD addendum B repeats pinning | Captured (partial: package names only, no static-vs-dynamic mechanism) |
| Dynamic tool registration (`McpServerTool.Create`, custom `ListToolsHandler`/`CallToolHandler`, `ToolCollection.ListChanged`) — "the path for building tools from CQRS metadata" | A, SDK research | Not present in PRD or PRD addendum | **Missing** |
| Per-user tool filtering has no first-class SDK API (issue #1881); use a custom `ListToolsHandler` | A, SDK research | Not present anywhere; PRD FR-19/FR-9 need exactly this mechanism to drop `send_command` in Read-only Mode | **Missing** |
| Transports: stdio, Streamable HTTP (stateless default), legacy SSE | A, SDK research | PRD/addendum only mention stdio v1 and HTTP next release; SSE and "stateless by default" not mentioned | Partial (immaterial for v1, relevant to HTTP design pass) |
| HTTP auth mechanics: `AddMcpAuthentication()`, JWT bearer, `RequireAuthorization()`, RFC 9728 protected-resource metadata, PKCE mandatory | A, SDK research | Open Question 1 flags "HTTP authentication design" but none of these specifics are recorded anywhere | **Missing** |
| Tool-count guidance (30–50 tool degradation, Claude Code 25k-token cap, VS Code 128-tool cap) | A, SDK research | PRD addendum C, "MCP tool-count guidance" | Captured |
| Anthropic Tool Search Tool / deferred loading recommendation (>10 tools or >10k tokens) | A, SDK research | Not carried; moot at 5 tools but the reasoning behind NFR-2's 2,000-token budget is otherwise unsourced | Partial |
| Comparable: Azure API Management REST→MCP export | A, Comparables | Not carried into PRD addendum C | Missing (low importance — precedent role covered by azmcp/scw) |
| Comparable: OpenAPI-to-MCP generators (Speakeasy, FastMCP, openapi-mcp-generator) | A, Comparables | PRD addendum C only states the generator-camp divergence via `research-landscape.md`, not this specific list | Partial |
| Comparable: MCP gateways/aggregators (MetaMCP, Docker MCP Gateway, mcp-aggregator) | A, Comparables | Not carried | Missing (low importance) |
| CLI+MCP precedent: azmcp (`--learn`, namespace/read-only filters, stdout/stderr split) | A, Comparables | PRD addendum C | Captured |
| CLI+MCP precedent: `scw mcp server serve` | A, Comparables | PRD addendum C | Captured |
| .NET MCP-mode-on-existing-CLI blog precedent | A, Comparables | Not carried | Missing (low importance) |
| Prior art: 6 per-module `.Mcp` servers are the replacement target; Admin.Mcp/Admin.Cli out of scope | A, Codebase extract | PRD §2.2, §8, PRD addendum D | Captured |
| `Hexalith.ChatBot.Mcp` catalog is the closest precedent / feature-parity bar | A, Codebase extract | PRD FR-21, PRD addendum D | Captured |
| Only `Hexalith.Parties.Mcp` reaches the Gateway (hand-rolled HTTP, not `IEventStoreGatewayClient`) | A, Codebase extract | PRD addendum D survey facts | Captured |
| No command has a `[Description]` today | A, Codebase extract | PRD addendum D ("Zero `[Description]` attributes...") and PRD §4.1 note | Captured |
| `IEventStoreGatewayClient` methods: `SubmitCommandAsync`, `GetCommandStatusAsync`, `SubmitQueryAsync(request, ifNoneMatch)`, `ReadStreamAsync` | A, EventStore client | Only `SubmitCommandAsync`/`SubmitQueryAsync` are implied via FR-17; `GetCommandStatusAsync` and the `ifNoneMatch` conditional-read parameter are never mentioned; `ReadStreamAsync` is explicitly excluded (§8, deliberate — event reading is a non-goal) | Partial/**Missing** for `GetCommandStatusAsync` and `ifNoneMatch` |
| `SubmitCommandRequest`/`SubmitQueryRequest` field lists, Paging/Search/Filters/OrderBy/Freshness | A, EventStore client | PRD addendum B reproduces both envelope signatures verbatim, including "plus Paging / Search / Filters / OrderBy / Freshness" | Captured (but see Gap: Search/Filters/OrderBy/Freshness never surfaced as tool/CLI arguments) |
| `EventStoreQueryResult` carries ETag / IsNotModified | A, EventStore client | Not carried into PRD or PRD addendum; FR-17's query response mapping never mentions ETag or not-modified handling | **Missing** |
| DI registration (`AddEventStoreGatewayClient`, `AddEventStoreDaprServiceInvocation`) | A, EventStore client | Not carried | Missing (low importance — pure wiring, architecture-level) |
| Auth: client carries none; `DelegatingHandler` pattern; `McpContextForwardingHandler` forwards bearer + `X-Tenant-Id`/`X-User-Id`; admin tools use static env-var bearer token | A, EventStore client | PRD addendum B ("HTTP reuses the Parties `McpContextForwardingHandler` pattern"), PRD §6 Identity | Captured |
| Two contract styles: `ICommandContract`/`IQueryContract` w/ static abstracts + `[RestRoute]` vs. plain records w/ module-local markers (e.g. `IProjectCommand`) | A, Codebase extract | PRD FR-2, PRD addendum D | Captured |
| `[PolymorphicSerialization]` used only by Works, not a viable ecosystem-wide hook | A, Codebase extract | Not carried | Missing (low importance — already superseded by the D1 hybrid decision) |
| Discovery is compile-time only today (Roslyn `RestApiManifestEmitter` emits internal manifest; `AssemblyScanner` scans aggregates/projections, not contracts; no public runtime catalog) | A, Codebase extract | Implied by FR-5 but the specific prior-art mechanics (emitter, scanner) are not named | Partial |
| Conventions: .NET 10, `.slnx` only, central package management, pinned SDK versions, no Spectre.Console | A, Conventions | PRD §7, PRD addendum B | Captured |
| CLI shape reference `Hexalith.EventStore.Admin.Cli` (profiles, exit codes, global flags, JSON/CSV/table, completions) | A, Conventions | PRD §4.4, §4.6, PRD addendum B; CSV explicitly dropped as `[ASSUMPTION]` (FR-13), completions deferred (§9.2) | Captured, divergences explained |
| Flat module layout vs. nested layout in `hexalith-llm-instructions.md`; brief flagged this as an **open item requiring maintainer confirmation** | A, Conventions + Open items | PRD addendum B states flat layout as settled fact; PRD Open Questions (§11) does **not** list "confirm layout with a maintainer" | Partial/misplaced — an unresolved open item was silently converted into a stated decision |
| Design rule: reuse technical modules rather than duplicating plumbing | A, Conventions | Not restated; implicit in the two-dependency policy | Partial (low importance) |
| D1 Discovery: Hybrid chosen; attribute-only and interface-only rejected | A, Decisions/Options | PRD FR-1–FR-4, PRD addendum A | Captured |
| D2 Assembly loading: compile-time refs chosen; plugin folder parked | A, Decisions/Options | PRD FR-5, §6, §8, PRD addendum A | Captured |
| D3 Tool shape: 5 generic tools chosen; typed-per-op parked; "both behind a filter" = first follow-up | A, Decisions/Options | PRD FR-9, §9.2, PRD addendum A | Captured |
| D4 Transport/identity: stdio v1, HTTP next release (no new auth server) chosen; any auth server rejected | A, Decisions/Options | PRD §2.2, §6, §9.2, Open Question 1, PRD addendum A/B | Captured |
| D5 CLI depth: thin companion chosen; generated subcommands parked | A, Decisions/Options | PRD §4.4, §9.2, PRD addendum A | Captured |
| D6 Existing servers: Replace (product-owner override of strangler) chosen; coexist and strangler rejected | A, Decisions/Options | PRD §4.8, FR-20–22, Vision, PRD addendum A | Captured — see **Contradiction 1** on effective date |
| Constraint: tenant always envelope-supplied, never payload | A, Constraints | PRD §6, Glossary "Tenant", FR-16 | Captured |
| Constraint: IDs are ULIDs, validate with `Ulid.TryParse` not `Guid.TryParse` | A, Constraints | PRD §6, FR-7, FR-15 | Captured |
| Constraint: message ID + idempotency key generated per call, correlation ID optional pass-through | A, Constraints | PRD §6, FR-16 | Captured |
| Constraint: commands/queries distinguishable so read-only is one filter | A, Constraints | PRD §4.7, FR-19, Glossary | Captured |
| Constraint: only two dependency kinds (EventStore client + Contracts libraries) | A, Constraints | PRD §6, §7, §8 | Captured |
| Open item: Kiota/System.CommandLine-to-MCP bridge unverified, does not block design | A, Open items | Not carried | Missing (correctly low priority — brief itself says it doesn't block) |
| Open item: six `.Cli` projects not enumerated, list before deletion plan | A, Open items | PRD addendum D lists only **five**: Folders, Projects, ChatBot, FrontComposer, Memories; PRD Open Question 4 says "Four or five per-module CLIs exist" | **Contradicted** — see Contradiction 2 |
| Open item: HTTP auth needs a design pass before production | A, Open items | PRD Open Question 1, §9.2 | Captured |
| Memlog: hard constraint is `*.Contracts` libraries, not `*.Client` (wording slip corrected) | B | PRD §12 Assumptions Index, explicitly notes the correction | Captured, divergence explicitly labeled |
| Memlog: this module owns the decoration attributes other modules apply | B | PRD FR-1–FR-4, Glossary "Decoration Attribute/Package" | Captured |
| Memlog: first consumer v1 = developer or LLM agent running locally over stdio against dev/test EventStore | B | PRD §2.1, §2.2, UJ-1 | Captured |
| Memlog: primary cost is cross-module inconsistency an LLM sees, not maintenance | B | PRD §1 Vision (implicit — "An agent that learns one module gains nothing for the next") | Captured |
| Memlog: vision — a human should be able to do any operation through an LLM agent; identity forwarding becomes essential once vision is taken seriously | B | PRD §1 opens with this exact sentence; §6 Identity and §9.2 flag HTTP/identity as load-bearing | Captured |
| Memlog: "no new per-module MCP server" is a rule the user is making, effective as of 2026-09-21, not a proposal | B | PRD Vision/FR-22 make it effective "from the day this PRD is accepted" | **Contradicted** — see Contradiction 1 |
| Memlog: D6 cadence — v1 proves the generic server on Tenants/Parties/Projects/Folders; rule applies "from day one" | B | PRD §4.8, FR-20 | Captured (module list matches); "from day one" vs. "from PRD acceptance" is the same date-shift as Contradiction 1 |
| Memlog: five success criteria and scope in/next/out accepted (content lives in `brief.md`, not in the two required inputs) | B | Cannot verify against PRD line-by-line since `brief.md` was not a required input; PRD §10 Success Metrics and §9 MVP Scope exist and look structurally consonant | Not fully checkable — out of reconciliation scope per task instructions |

## Gaps (ordered by importance, with suggested fix)

1. **Query freshness/ETag semantics never surfaced.** The brief addendum records that `SubmitQueryAsync` takes an `ifNoneMatch` parameter and `EventStoreQueryResult` carries `ETag`/`IsNotModified`, and the envelope has a `Freshness` field — all reproduced verbatim in PRD addendum B. But PRD FR-9 (`run_query` arguments) and FR-17 (response mapping) never mention conditional reads, ETag, or "not modified" results. Without this, `run_query` either always does a full fetch (defeating the Gateway's caching contract) or the behavior is undefined.
   **Fix:** Add a consequence to FR-17: "Query results carry the Gateway's ETag; a caller-supplied `ifNoneMatch`/freshness argument on `run_query` (FR-9) short-circuits to `code: not_modified` with no Payload re-fetch." Cross-reference `EventStoreQueryResult.ETag`/`IsNotModified` in PRD addendum B.

2. **`GetCommandStatusAsync` has no home.** The brief lists it as one of four `IEventStoreGatewayClient` methods, but no Generic Tool, CLI verb, or FR ever calls it — UJ-1 says Nadia "sees both Commands accepted with message identifiers she can trace," implying she traces them somewhere, but the tool gives her no way to poll status through either Head.
   **Fix:** Either add an explicit non-goal ("checking command status after submission is out of scope for v1; use the EventStore directly") to §8, or add a small FR under §4.5 exposing it (e.g., `describe`-adjacent `status <messageId>` verb / tool). Silence here reads as an oversight, not a decision.

3. **Open item "confirm module layout with a maintainer" was silently resolved instead of carried forward.** The brief addendum explicitly flags the flat-vs-nested layout mismatch with `hexalith-llm-instructions.md` as something to confirm with a maintainer before scaffolding. PRD addendum B instead states the flat layout as a settled fact, and PRD §11 Open Questions does not list it.
   **Fix:** Either add an 8th Open Question ("Module layout: flat (as used by sibling modules) vs. the nested layout `hexalith-llm-instructions.md` documents — confirm with a maintainer before scaffolding. Owner: maintainers.") or, if the choice is now considered final, say so explicitly in PRD addendum B rather than presenting it as inherited convention.

4. **Per-module `.Cli` count and enumeration are inconsistent, and the "six" from the brief was never reconciled.** See Contradiction 2 below — this also blocks Open Question 4 from being answerable as written.
   **Fix:** Re-run the survey to get an exact count and list (the six legacy-server modules are Parties, Projects, Folders, Memories, ChatBot, FrontComposer — confirm whether Parties has a `.Cli` or not), update PRD addendum D and Open Question 4 to agree, and state whether the discrepancy from the brief's "six" is a correction or an omission.

5. **SDK mechanism notes useful to architecture are missing from the PRD addendum.** Two research findings directly bear on how FR-9/FR-19 get implemented: (a) dynamic tool registration via `McpServerTool.Create`/custom `ListToolsHandler` is "the path for building tools from CQRS metadata," and (b) per-user/mode tool filtering has no first-class SDK API and needs a custom `ListToolsHandler`. Neither appears in PRD addendum B, which otherwise carries the stdio host pattern and package pins.
   **Fix:** Add two bullets to PRD addendum B: "Generic Tools are registered dynamically via `McpServerTool.Create`, not `[McpServerTool]` static methods, since they wrap catalog-driven metadata, not fixed methods." and "Read-only Mode's four-vs-five tool list (FR-19) is implemented via a custom `ListToolsHandler`; the SDK has no first-class per-mode/per-user tool filtering API (tracked upstream as issue #1881)."

## Contradictions

1. **Effective date of the "no new per-module MCP server" rule.** The brief's Decisions table and memlog both fix this as a rule already in force as of the decision date, 2026-09-21 ("no new per-module server is created after 2026-09-21"; memlog: "a rule the user is making, not proposed"). The PRD (Vision, §1, and FR-22) instead ties the effective date to a future, unspecified event — "from the day this PRD is accepted" / "applies from acceptance of this PRD, before v1 ships." If PRD acceptance lags the decision date, the PRD's wording permits exactly what the product owner already forbade. **Suggested resolution:** restate FR-22 and the Vision sentence to anchor on 2026-09-21 (the decision date), not PRD acceptance, or explicitly justify the change if it is deliberate.

2. **Count and enumeration of legacy `.Cli` companions.** The brief addendum states "Six `.Cli` projects exist alongside [the six `.Mcp` servers]" as an unresolved open item to enumerate. PRD addendum D enumerates five: Folders, Projects, ChatBot, FrontComposer, Memories (no Parties). PRD Open Question 4 then describes "Four or five per-module CLIs exist" — a hedge that disagrees with both the brief's six and the addendum's own list of five. These three numbers (six / five / "four or five") cannot all be right. **Suggested resolution:** settle on one count via a fresh survey and make PRD addendum D and Open Question 4 agree; note explicitly if the brief's "six" was simply wrong.

## Deliberate divergences (explained by the PRD, not gaps)

- **Dependency terminology correction** (`*.Contracts`, not `*.Client`): PRD §12 explicitly labels this as resolving a wording slip in the brief's earliest memlog entry. Correctly flagged, not a gap.
- **Parity definition (FR-21)**: PRD ties Legacy Server deletion to Gateway-readiness *and* ChatBot-catalog feature parity — matches D6's chosen option and memlog's stated implication exactly.
- **Folders kept in v1 despite being the largest prerequisite** (§9.1 note): PRD explicitly states this was a product-owner choice to keep Folders in v1 rather than swap it for a lighter module, sourced from the addendum's survey fact that `Hexalith.Folders.Contracts` holds only OpenAPI YAML today.
- **Canonical `module.kebab-case` Operation Naming (FR-8)**: PRD addendum D explains this was necessitated by the survey finding that wire `CommandType` values differ per module (kebab-case, full type name, `nameof`) — a deliberate abstraction layer, not carried directly from any brief decision but justified by brief-sourced evidence.
