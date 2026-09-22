---
title: "Brief Extract: Hexalith MCP Server & CLI"
source_files:
  - brief.md
  - addendum.md
  - .memlog.md
extracted: 2026-09-21
---

# Brief Extract — source material for PRD

Sources: `brief.md`, `addendum.md`, `.memlog.md`, all in
`_bmad-output/planning-artifacts/briefs/brief-mcpcli-2026-09-21/`.

## 1. Product statement and problem

One module replaces six handwritten, per-module MCP servers with one generic
MCP server and one CLI, both driven by a single catalog of commands and
queries discovered from decorated `*.Contracts` assemblies and submitted
through the EventStore gateway client (brief.md, Executive Summary). The goal
is for a human to do any operation in Hexalith through an LLM agent (brief.md,
Executive Summary / Vision). The problem is inconsistency, not a missing
feature: each of the six per-module MCP servers has its own transport,
tool-naming scheme, description mechanism, and authentication story, so an
agent that learns one module's conventions gains nothing for the next, and
operation descriptions live only in XML doc comments that do not exist at
runtime, so each server redescribes its operations by hand and drifts from
the code (brief.md, The Problem). This is explicitly an anticipatory build —
"There is no triggering incident" — made on the bet that Agents, ChatBot, and
Conversations will soon need cross-module action and "six dialects will not
survive that contact" (brief.md, The Problem).

## 2. Users / audiences named, with success for each

- **The developer or agent operator, first** — someone with a dev/test
  EventStore and an MCP-capable agent; installs one .NET tool, points a
  profile at the gateway. Success: "a working cross-module task with no
  per-module setup" (brief.md, Who This Serves).
- **Hexalith's own agents, next** — Agents, ChatBot, and Conversations.
  Success: "one way to act on business data instead of one integration per
  module" (brief.md, Who This Serves).
- **Module authors, indirectly** — obligation shrinks to decorating records
  in their Contracts library. Success: "their module is visible to every
  agent on the day it ships, and they never write an MCP server again"
  (brief.md, Who This Serves).
- **First consumer for v1** (memlog): "a developer or an LLM agent such as
  Claude Code running the tool locally over stdio against a dev/test
  EventStore" (.memlog.md, decision line 21).

## 3. Every decision recorded

From `.memlog.md` (chronological; each tagged `(decision)` or `(override)`):

- Hard constraint: depend only on the EventStore client package plus domain
  modules' command/query definition libraries; no aggregates/projections/
  server code; "stay pragmatic, no over-engineering." Reason: user-imposed
  scope guardrail (.memlog.md, line 7). *(Note: memlog says "client
  libraries"; addendum.md "Codebase extract" clarifies definitions actually
  live in `*.Contracts`, not `*.Client` — see §9 contradiction.)*
- This module owns the decoration attributes domain modules apply to
  commands/queries; server and CLI discover operations via those attributes.
  Reason: stated as a requirement, not derived (.memlog.md, line 8).
- User chose the "Coaching" elicitation path — section-by-section, push back
  on thin assumptions. Reason: process choice, no stated rationale
  (.memlog.md, line 9).
- Problem framing decision: no triggering incident; brief must state the
  anticipated pain explicitly "rather than fabricate a current one." Reason:
  intellectual honesty about anticipatory build (.memlog.md, line 10).
- D1 accepted — hybrid discovery: attribute package carries LLM-facing
  metadata (description, kind, example); routing comes from
  `ICommandContract`/`IQueryContract` when implemented, attribute overrides
  otherwise; `[Description]` on properties. Reason: "every module can be
  exposed today; encourages convergence... without blocking on it"
  (.memlog.md, line 14; addendum.md, D1/Decisions table).
- D2 accepted — compile-time references to `*.Contracts` packages plus an
  assembly-level module marker; plugin loading parked. Reason: "trivial;
  versions pinned by central package management; no plugin loader"
  (.memlog.md, line 15; addendum.md, D2).
- D3 accepted — v1 exposes five generic discovery tools; typed per-operation
  tools behind a module filter deferred. Reason: constant tool count vs.
  "ten modules produce hundreds of tools, exceeding the limits in the
  tool-count guidance" (.memlog.md, line 16; addendum.md, D3).
- D4 accepted — single binary with stdio and HTTP transports; v1 ships
  stdio with profile/env token + default tenant; HTTP with header forwarding
  in the next release, no new auth server. Reason: "the SDK makes the
  transport switch a few lines; the catalog and executor are identical
  across both transports" (.memlog.md, line 17; addendum.md, D4).
- D5 accepted — thin CLI (`modules`, `operations`, `describe`, `send`,
  `query`, `mcp` serve) with global url/token/tenant/format/profile flags,
  JSON on stdout, logs on stderr; generated per-operation subcommands
  deferred. Reason: "small; proves the catalog without MCP; scriptable"
  (.memlog.md, line 18; addendum.md, D5).
- D6 override — product owner overruled the facilitator's strangler
  recommendation and chose to REPLACE the six existing per-module MCP
  servers. Reason: "user wants the inconsistency removed for good."
  Implication logged: generic server must reach feature parity with the
  ChatBot catalog (read/write flag, correlation/task/tenant args); migration
  phasing still to be decided (.memlog.md, line 19; addendum.md, D6).
- D6 cadence decision: replacement is the declared end state with cutover
  after v1; v1 proves the generic server on Tenants, Parties, Projects,
  Folders; the rule "no new per-module MCP server" applies from day one;
  each existing server is deleted once covered. Reason: sequencing the
  override into an executable plan (.memlog.md, line 20).
- First-consumer decision (see §2) (.memlog.md, line 21).
- Primary cost driving the build: inconsistency an LLM sees across the six
  servers (naming, args, descriptions, auth); maintenance and next-module
  friction are secondary. Reason: prioritization for the brief's problem
  statement (.memlog.md, line 22).
- Vision decision, in the user's own words: "the MCP/CLI enables a human to
  do any operation in Hexalith through an LLM agent." Implication noted:
  identity forwarding (HTTP mode) becomes essential, not optional, and
  undecorated commands are invisible to agents (.memlog.md, line 24;
  brief.md, Vision).
- User confirmed: the anticipatory-build belief (Agents/ChatBot/
  Conversations will need cross-module action); "no new per-module MCP
  server" is a rule the user is making, not proposed; the five success
  criteria, the in/next/out scope, and the vision policy sentence were all
  accepted as drafted (.memlog.md, line 26).

Decisions table from `addendum.md` (Decisions section) — restates D1–D6 with
"Chosen for v1 / Next release / Not chosen" columns; D1 Not chosen = attribute-
only (A) and marker-interfaces-only (B); D2 Not chosen = plugin folder (B);
D3 Not chosen = typed tools behind module filter (C) and one-tool-per-op (A);
D4 Not chosen = any auth server; D5 Not chosen = generated per-operation
subcommands (B); D6 Not chosen = coexist indefinitely (B) and strangler (C)
(addendum.md, "Decisions (2026-09-21)").

## 4. Scope

**Explicit v1 IN** (brief.md, Scope):
- The attribute package.
- The catalog builder.
- The five generic MCP tools and matching CLI verbs, over stdio, JSON on
  stdout, logs on stderr, connection profiles borrowed from the existing
  admin CLI.
- Coverage of Tenants, Parties, Projects, and Folders.
- A written rule, placed in the Hexalith agent instructions, that no new
  per-module MCP server is created.

**Explicit OUT / refused if proposed for v1** (brief.md, Scope — "parked, not
rejected forever"):
- Plugin loading of Contracts assemblies from a folder.
- Typed one-tool-per-operation exposure.
- Generated per-operation CLI subcommands.
- Any OAuth or identity server.
- Event stream reading.
- MCP resources or prompts.
- Any reference to an aggregate, projection, handler, or server-side project
  from another module.

**Next release, already decided** (brief.md, Scope):
- HTTP transport in the same binary, forwarding the caller's bearer token,
  tenant header, and user header, as Parties does today.
- No new authentication server.
- Deletion of legacy MCP servers as each is covered.

## 5. Concrete solution shape

- **Attribute package**: two attributes mark a record as a command or a
  query; they carry "a description, whether the operation reads or writes,
  and an optional example"; routing data comes from existing contract
  interfaces, with attribute fallbacks for modules that don't implement them
  (brief.md, The Solution). Property-level descriptions use
  `[Description]` (addendum.md, D1 Option C). Package has no dependencies
  and stays that way (brief.md, The Solution).
- **Assembly discovery**: compile-time references to `*.Contracts`
  packages; catalog scans loaded assemblies carrying an assembly-level
  `[HexalithModule]` marker (addendum.md, D2 Option A).
- **Catalog**: built at startup from referenced Contracts assemblies; knows
  every module, every operation, the JSON schema of each payload, and
  whether the operation is a read or a write; same catalog drives both heads
  (brief.md, The Solution).
- **Five MCP tools** (addendum.md, D3 Option B): `list_modules`,
  `list_operations(module)`, `describe_operation(name)` (returns JSON schema
  and example), `send_command(name, tenant?, aggregateId?, payload)`,
  `run_query(name, ..., payload)`.
- **CLI verbs** (addendum.md, D5 Option A): `modules`, `operations
  <module>`, `describe <op>`, `send <op> --payload <json>`, `query <op>
  --payload <json>`, `mcp` (serve); global flags `--url --token --tenant
  --format json|table --profile`; profiles and exit codes borrowed from
  `Hexalith.EventStore.Admin.Cli`.
- **Envelope fields**: `SubmitCommandRequest(MessageId, Tenant, Domain,
  AggregateId, CommandType, JsonElement Payload, CorrelationId?,
  Extensions?, IdempotencyKey?)`; `SubmitQueryRequest(Tenant, Domain,
  AggregateId, QueryType, ProjectionType?, Payload?, EntityId?,
  ProjectionActorType?)` plus Paging/Search/Filters/OrderBy/Freshness
  (addendum.md, "EventStore client package"). Message ID and idempotency
  key are generated by the tool per call; correlation ID is optional
  pass-through (addendum.md, Constraints on every option).
- **Transport**: `hexalith mcp --transport stdio|http`; v1 ships stdio only;
  HTTP lands next release using the existing forwarding-handler pattern, no
  new auth server (addendum.md, D4 Option C).
- **Config/profile mechanism**: connection profile or environment variables
  for EventStore URL, bearer token, default tenant — the
  `Hexalith.EventStore.Admin.Mcp` pattern (brief.md, The Solution;
  addendum.md, D4 Option A). CLI adds `--profile` and profiles borrowed from
  `Hexalith.EventStore.Admin.Cli` (addendum.md, D5 Option A;
  addendum.md, "Conventions").
- **Validation**: both heads "validate the payload against the schema" and
  "fill the message envelope with a fresh message ID and idempotency key"
  before submitting through the EventStore gateway client (brief.md, The
  Solution).
- **Error/exit-code behavior**: exit codes 0/1/2, JSON/CSV/table output,
  shell completions — carried over from `Hexalith.EventStore.Admin.Cli`
  shape (addendum.md, "Conventions"). No explicit MCP-side error-message
  requirements stated beyond schema validation before submission.

## 6. Prior art: six existing per-module MCP servers

From `addendum.md`, "Codebase extract... Prior art":
- The six: `Hexalith.{Parties,Projects,Folders,Memories,ChatBot,
  FrontComposer}.Mcp`. These are the replacement target.
  `Hexalith.EventStore.Admin.Mcp` / `.Admin.Cli` are admin-plane tools, out
  of scope for replacement.
- "All six MCP servers are handwritten, per-module, and bound to typed
  clients (one tool method per command)." Example:
  `Hexalith.Parties/src/Hexalith.Parties.Mcp/Tools/PartiesMcpTools.cs` calls
  `IPartiesCommandClient.CreatePartyAsync`.
- `Hexalith.ChatBot/src/Hexalith.ChatBot.Mcp/ChatBotMcpToolCatalog.cs` is
  "the closest precedent to a catalog": a declarative registry mapping tool
  names to client methods, required/optional args, description, read/write
  kind — hand-maintained, single-module. This is the feature set the generic
  server must reach parity with before ChatBot's server is deleted
  (addendum.md, D6 Option A).
- `Hexalith.EventStore.Admin.Mcp` (admin-plane, not a replacement target) is
  a stdio server using `[McpServerToolType]` static classes with logging
  forced to stderr — cited as the stdio/logging pattern to copy.
  (addendum.md, "Prior art" and "Stdio MCP host pattern" reference.)
- Auth pattern differs per server: `Hexalith.Parties.Mcp/
  McpContextForwardingHandler.cs` forwards the inbound bearer token and
  `X-Tenant-Id`/`X-User-Id` headers; admin tools instead use a static bearer
  token from environment variables (addendum.md, "EventStore client
  package").
- Command descriptions live in XML doc comments today; "No module has a
  description attribute on a command" (addendum.md, Prior art).
- General differentiator (brief.md, The Problem): "Each per-module server
  has its own transport, tool-naming scheme, description mechanism, and
  authentication story" — addendum does not itemize per-server transport/
  naming differences beyond the Parties/ChatBot/Admin examples above; the
  six `.Cli` companion projects "were counted but not enumerated by the
  survey" (addendum.md, Open items).

## 7. Constraints and policies

From `addendum.md`, "Constraints on every option" (restated in brief.md,
Scope — Guardrails):
- Tenant is always envelope-supplied (profile, flag, or forwarded header),
  never taken from the payload.
- IDs are ULIDs; the catalog must not validate them as GUIDs.
- Message ID and idempotency key are generated by the tool per call;
  correlation ID optionally passed through.
- Queries and commands are distinguishable in the catalog so a read-only
  mode is one filter away.
- Only Hexalith dependencies allowed: the EventStore client package and the
  `*.Contracts` libraries being exposed.

Additional policy statements:
- "Zero module-specific code in this repo; adding a module is a package
  reference and a rebuild" — implied by brief.md Success Criteria ("Adding a
  fifth module is a package reference and a rebuild") and D2's rationale.
- EventStore client carries no auth itself; callers attach a
  `DelegatingHandler` (addendum.md, "EventStore client package").
- Design rule cited from `hexalith-llm-instructions.md`: "reuse technical
  modules rather than duplicating plumbing" (addendum.md, Conventions).
- .NET 10, `.slnx` only, central package management via
  `Hexalith.Builds/Props/Directory.Packages.props`; pinned
  `ModelContextProtocol 2.2.0`, `ModelContextProtocol.AspNetCore 2.2.0`,
  `System.CommandLine 2.0.12`; no Spectre.Console anywhere (addendum.md,
  Conventions).
- Flat module layout: `src/Hexalith.{Module}{,.Contracts,.Client,.Server,
  .UI,.Cli,.Mcp,...}` + `tests/` — noted as diverging from
  `hexalith-llm-instructions.md`'s documented nested layout, which "no
  module follows" (addendum.md, Conventions; Open items).

## 8. Success metrics / "done" criteria

Checked three months after v1 ships (brief.md, Success Criteria):
- Tenants, Parties, Projects, and Folders "fully exposed with zero
  module-specific code in this repository. Adding a fifth module is a
  package reference and a rebuild."
- "An agent completes a task that spans at least two modules using only the
  five generic tools, with no per-module prompting or handwritten tool."
- "At least one legacy per-module MCP server has been deleted, and no new
  one has been created since this brief was accepted." (This second clause
  doubles as a counter-metric / guardrail: creating a new per-module server
  after acceptance is a failure condition.)
- "Every operation in the four modules carries a description that a person
  who has never seen the code can understand. A schema that validates is
  not enough." (Qualitative bar stated as a success criterion, not just a
  schema check.)
- "The CLI produces the same catalog and the same results as the MCP
  server, so a shell script and an agent cannot disagree about what
  Hexalith can do."

No separate counter-metrics section exists; the "no new per-module server
created" clause inside criterion 3 is the only explicit failure-mode check.

## 9. Risks, open questions, assumptions, TODOs

From `addendum.md`, "Open items":
- `hexalith-llm-instructions.md` documents a nested `src/libraries/...`
  module layout that no inspected module follows; "Confirm the layout for
  this module with a maintainer before scaffolding."
- Kiota as an MCP generator is unverified (community wrappers only); no
  official System.CommandLine-to-MCP bridge found; "Neither blocks the
  design."
- The six `.Cli` companion projects "were counted but not enumerated by the
  survey; list them before the deletion plan is written."
- "HTTP mode authentication needs a design pass (issuer, token validation,
  header forwarding) before it is enabled in production."

Design risk called out explicitly:
- "Two coexisting styles" of command/query definition (EventStore-native
  `ICommandContract`/`IQueryContract` implementers vs. plain records with no
  ecosystem marker) is named "the main design risk for a generic catalog"
  (addendum.md, "How domain modules define commands and queries").

Assumptions/process notes from `.memlog.md`:
- Success Criteria were drafted "marked ASSUMPTION" and only had the tag
  removed after explicit user confirmation (.memlog.md, lines 25, 27) —
  i.e., they were provisional until confirmed, worth flagging as
  lower-confidence source material even though now accepted.
- D6 migration phasing "still to be decided" at the time of the override
  (.memlog.md, line 19) — later partially resolved by the cadence decision
  (line 20), but exact per-server cutover order/timing is not specified in
  any of the three files.

## 10. Rejected alternatives and options-considered material

Full options-considered matrix from `addendum.md`, "Options considered"
(six decisions, D1–D6, in dependency order):

**D1 — catalog discovery.**
- Option A, New attributes only (not chosen): `[HexalithCommand]`/
  `[HexalithQuery]` carrying description, domain, type name, aggregate-ID
  property; `System.ComponentModel.Description` on properties; server scans
  referenced assemblies. Pros: works for all modules; description lives
  next to code; tiny dependency-free package. Cons: duplicates routing data
  already declared by `ICommandContract` implementers; two sources of truth
  for Tenants-style modules.
- Option B, Marker interfaces only (not chosen): rely solely on
  `ICommandContract`/`IQueryContract`; no new attribute package. Pros: zero
  new contracts; routing data authoritative. Cons: Timesheets, Projects,
  Parties don't implement them today so most modules stay invisible until
  migrated; no place for an LLM-facing description; contradicts the product
  owner's requirement that this module provide decoration attributes.
- Option C, Hybrid (chosen) — see §5.

**D2 — assembly loading.**
- Option A, Compile-time references (chosen) — see §5.
- Option B, Plugin folder (parked): Contracts DLLs dropped in a folder,
  loaded via `AssemblyLoadContext` at startup. Pros: no rebuild needed.
  Cons: dependency resolution, version skew, load-context bugs;
  "over-engineering for v1."

**D3 — tool shape over MCP.**
- Option A, One MCP tool per operation (parked): typed tool per
  command/query via `McpServerTool.Create(AIFunction)`. Pros: best per-call
  UX; protocol-level schema validation; single call to act. Cons: "ten
  modules produce hundreds of tools," exceeding tool-count guidance; needs a
  module filter to be usable.
- Option B, Generic discovery tools (chosen) — see §5. Cons noted: "two or
  three round trips before the first action; schema is in a response body,
  not a tool definition."
- Option C, Both, behind a filter (parked, "first follow-up candidate"):
  generic tools always on; `--expose parties,tenants` additionally publishes
  typed tools for those modules. Pros: best of both for focused sessions.
  Cons: more surface to test.

**D4 — transport and identity.**
- Option A, Local stdio process (chosen as v1 transport under Option C):
  dotnet tool; URL/token/tenant from profile or env vars; identity is
  "whoever owns the configured token." Pros: works with Claude Code, Claude
  Desktop, VS Code today; no hosting; no auth server. Cons: "a shared static
  token is a service principal; audit trail says 'the tool,' not the
  human."
- Option B, Hosted HTTP server (next-release transport under Option C):
  ASP.NET Core Streamable HTTP, `AddMcpAuthentication` + JWT bearer,
  forwarding caller's bearer and `X-Tenant-Id`/`X-User-Id` (Parties
  pattern). Pros: caller identity preserved end to end; one shared server
  for the whole install. Cons: "deployment, TLS, token issuer wiring; the
  hard part is operations, not code."
- Option C, One binary, both transports (chosen) — see §5. Cons: "HTTP
  authentication still needs a design pass before it is turned on in
  production."

**D5 — CLI depth.**
- Option A, Thin companion (chosen) — see §5. Cons: "payload as a JSON
  string is clumsy for humans."
- Option B, Generated per-operation subcommands (parked): e.g. `hexalith
  parties create-party --name "..."` built dynamically from the catalog;
  `--help` doubles as discovery (azmcp pattern). Pros: excellent human UX;
  shell completion over the whole domain. Cons: "option typing for nested
  payloads gets fiddly."

**D6 — relationship to the six existing per-module MCP servers.**
- Option A, Replace (chosen, product owner override) — see §3/§4. Cons:
  "feature parity is a hard requirement; cross-repo coordination for six
  deletions after v1."
- Option B, Coexist indefinitely (rejected). Pros: no friction. Cons: "the
  inconsistency this module exists to remove persists forever."
- Option C, Strangler (recommended by the facilitator, rejected by the
  product owner): no new per-module server; an existing one migrates when
  next touched. Pros: v1 ships independently; gradual convergence. Cons: "a
  potentially unbounded transition period with two ways of doing things."

Research/comparables informing the options (addendum.md, "Research extract"
and "Comparables" — not decisions, but material the options draw on):
- MCP C# SDK 2.2.0 capabilities (static vs. dynamic tool declaration,
  transports, HTTP auth via `AddMcpAuthentication`/RFC 9728/PKCE); per-user
  tool filtering has no first-class API (open proposal #1881).
- Tool-count guidance: Anthropic — selection accuracy degrades beyond
  ~30–50 tools, recommends Tool Search Tool with deferred loading above 10
  tools/10k tokens; Claude Code enables MCP tool search by default, caps
  MCP tool output at 25k tokens; Azure MCP Server cites a VS Code 128-tool
  cap.
- Comparables: Azure API Management (REST-operations-to-MCP-tools, "an
  accepted product pattern"); OpenAPI-to-MCP generators ("none understands
  CQRS envelopes, so none is reusable here"); MCP gateways/aggregators
  (lazy discovery, one catalog over MCP and REST).
- CLI+MCP-sharing-one-catalog precedents: Azure `azmcp` (`--learn` JSON
  progressive discovery, namespace/read-only filters, JSON stdout/logs
  stderr); Scaleway `scw mcp server serve` (stdio or streamable HTTP,
  filters by namespace/resource/verb/read-only); a .NET blog precedent for
  adding an MCP mode to an existing CLI.

## 11. Qualitative intent

- **Descriptions must be human-legible, not just schema-valid**: "Every
  operation in the four modules carries a description that a person who has
  never seen the code can understand. A schema that validates is not
  enough" (brief.md, Success Criteria). This is an explicit rejection of
  treating the attribute as a formality.
- **The attribute is load-bearing, not decoration**: "a command without a
  description is a command an agent cannot use, so the attribute stops
  being decoration and becomes part of what it means for a Hexalith
  operation to exist. Every module that ships after this brief ships
  agent-ready or is not finished" (brief.md, Vision). Sets a tone of
  strictness/completeness that a bare FR checklist would flatten into "has
  a description field."
- **Consistency is the product, not a side effect**: the brief frames the
  entire module around eliminating "six dialects" so "an agent that learns
  one module's conventions gains nothing for the next" — implies the CLI
  and MCP tool surface should feel identical in naming, error shape, and
  behavior across every exposed module, not merely functionally equivalent
  (brief.md, The Problem).
- **CLI and MCP must never disagree**: "so a shell script and an agent
  cannot disagree about what Hexalith can do" (brief.md, Success Criteria)
  — a trust/predictability requirement, not just a shared-code
  implementation detail.
- **stdout/stderr discipline as a UX contract for agents**: "JSON on
  stdout, logs on stderr" appears repeatedly (brief.md, Scope; addendum.md,
  D5, Conventions) — signals that clean machine-parseable output is a
  first-class experience concern for the agent as the primary "user," not
  an implementation nicety.
- **Small, dependency-free package as a design ethic**: "The package has no
  dependencies and stays that way" (brief.md, The Solution) — a stated
  value (minimalism, low friction for module authors) beyond what a
  functional requirement would capture.
- **Honesty about the anticipatory nature of the build**: the memlog
  explicitly records a correction to "state the anticipated pain explicitly
  rather than fabricate a current one" (.memlog.md, line 10) — the brief's
  tone deliberately avoids manufactured urgency.
- **Product-owner decisiveness over process orthodoxy**: D6 is explicitly
  logged as an "override" of the facilitator's own strangler recommendation
  (.memlog.md, line 19; addendum.md, D6 Option C) — worth preserving in the
  PRD as a signal that this is a deliberate, informed rejection of the
  "safer" incremental path, not an oversight.
