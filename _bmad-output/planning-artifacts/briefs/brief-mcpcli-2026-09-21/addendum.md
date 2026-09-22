---
title: "Addendum: Hexalith MCP Server & CLI"
status: ready-for-review
created: 2026-09-21
updated: 2026-09-21
---

# Addendum

Supporting detail for the brief that belongs in downstream documents (architecture, PRD, solution design).

## Research extract: MCP C# SDK and comparables (2026-09-21)

### Official ModelContextProtocol C# SDK

- Latest stable 2.2.0 (2026-08-13). Packages: `ModelContextProtocol.Core`, `ModelContextProtocol` (hosting/DI), `ModelContextProtocol.AspNetCore` (HTTP). Sources: https://www.nuget.org/packages/ModelContextProtocol, https://github.com/modelcontextprotocol/csharp-sdk/releases
- Static declaration: `[McpServerToolType]`, `[McpServerTool]`, `[Description]`; JSON Schema 2020-12 generated from signatures.
- Dynamic tools are supported: `McpServerTool.Create(...)` from a delegate, `MethodInfo`, or `AIFunction`; custom `ListToolsHandler` / `CallToolHandler`; `ToolCollection.ListChanged`. This is the path for building tools from CQRS metadata rather than hand-written methods. https://modelcontextprotocol.github.io/csharp-sdk/api/ModelContextProtocol.Server.McpServerTool.html
- Per-user tool filtering has no first-class API (open proposal, issue #1881); use a custom `ListToolsHandler`.
- Transports: stdio, Streamable HTTP (stateless by default since 2.0), legacy SSE.
- HTTP auth: `AddMcpAuthentication()` + JWT bearer + `RequireAuthorization()` on `MapMcp`; RFC 9728 protected-resource metadata; PKCE mandatory. https://github.com/modelcontextprotocol/csharp-sdk/releases/tag/v2.0.0

### Tool-count guidance (matters for the catalog design)

- Anthropic: selection accuracy degrades beyond roughly 30 to 50 tools; recommends the Tool Search Tool with deferred loading when a server exposes more than 10 tools or more than 10k tokens of definitions. https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool
- Claude Code enables MCP tool search by default and caps MCP tool output at 25k tokens. https://code.claude.com/docs/en/mcp
- Azure MCP Server cites a VS Code 128-tool cap and offers namespace / single / consolidated tool modes.

### Comparables

- Azure API Management exports REST operations as MCP tools: shows that generating tools from an existing operation catalog is an accepted product pattern. https://learn.microsoft.com/en-us/azure/api-management/export-rest-mcp-server
- OpenAPI-to-MCP generators (Speakeasy, FastMCP, openapi-mcp-generator): same pattern for OpenAPI; none understands CQRS envelopes, so none is reusable here.
- MCP gateways and aggregators (MetaMCP, Docker MCP Gateway, MarimerLLC/mcp-aggregator): show lazy discovery and exposure of one catalog over both MCP and REST.

### CLI + MCP sharing one catalog (precedents)

- Azure MCP Server `azmcp`: one catalog exposed both as CLI verbs and as MCP tools; `--learn` returns JSON command info for progressive discovery; namespace and read-only filters; JSON on stdout, logs on stderr. https://github.com/microsoft/mcp/blob/main/servers/Azure.Mcp.Server/docs/azmcp-commands.md
- Scaleway CLI `scw mcp server serve`: stdio or streamable HTTP; filters by namespace, resource, verb, read-only. https://cli.scaleway.com/mcp/
- .NET precedent for adding an MCP mode to an existing CLI: https://erikej.github.io/mcp/dotnet/copilot/2025/05/06/mcp-dotnet-copilot.html


## Codebase extract: what exists today in Hexalith (2026-09-21)

Paths are relative to `references/`.

### Prior art: per-module MCP and CLI projects already ship

- Six domain modules ship their own MCP server: `Hexalith.{Parties,Projects,Folders,Memories,ChatBot,FrontComposer}.Mcp`. These six are the replacement target. `Hexalith.EventStore.Admin.Mcp` and `Hexalith.EventStore.Admin.Cli` are admin-plane tools and are not in scope for replacement. Six `.Cli` projects exist alongside; the survey did not enumerate them individually.
- All six MCP servers are handwritten, per-module, and bound to typed clients (one tool method per command). Example: `Hexalith.Parties/src/Hexalith.Parties.Mcp/Tools/PartiesMcpTools.cs` calls `IPartiesCommandClient.CreatePartyAsync` and so on.
- `Hexalith.ChatBot/src/Hexalith.ChatBot.Mcp/ChatBotMcpToolCatalog.cs` is the closest precedent to a catalog: a declarative registry mapping tool names to client methods, required/optional args, description, read/write kind. Hand-maintained, single-module.
- `Hexalith.EventStore.Admin.Mcp` is a stdio server using `[McpServerToolType]` static classes, with logging forced to stderr. Admin plane only.
- Command descriptions live in XML doc comments today. No module has a description attribute on a command.

### EventStore client package (the one allowed technical dependency)

- Project: `Hexalith.EventStore/src/Hexalith.EventStore.Client/` (depends on `Hexalith.EventStore.Contracts`, `Dapr.Client`, `Microsoft.Extensions.Http`).
- Interface `IEventStoreGatewayClient` (`Gateway/IEventStoreGatewayClient.cs`): `SubmitCommandAsync(SubmitCommandRequest)`, `GetCommandStatusAsync(messageId)`, `SubmitQueryAsync(SubmitQueryRequest, ifNoneMatch)`, `ReadStreamAsync(StreamReadRequest)`.
- Envelopes (`Hexalith.EventStore.Contracts/Commands|Queries/`): `SubmitCommandRequest(MessageId, Tenant, Domain, AggregateId, CommandType, JsonElement Payload, CorrelationId?, Extensions?, IdempotencyKey?)`; `SubmitQueryRequest(Tenant, Domain, AggregateId, QueryType, ProjectionType?, Payload?, EntityId?, ProjectionActorType?)` plus Paging/Search/Filters/OrderBy/Freshness; `EventStoreQueryResult` carries ETag / IsNotModified.
- IDs are ULIDs, not GUIDs.
- DI: `AddEventStoreGatewayClient(options)` registers a typed HttpClient; options hold BaseAddress and the four endpoint paths (one per operation above). Optional `AddEventStoreDaprServiceInvocation(appId, apiToken)`.
- Auth: the client carries none. Callers attach a DelegatingHandler. Existing pattern: `Hexalith.Parties.Mcp/McpContextForwardingHandler.cs` forwards the inbound bearer token and the `X-Tenant-Id` / `X-User-Id` headers. Admin tools use a static bearer token from environment variables. Tenant is envelope-supplied, never payload-controlled.

### How domain modules define commands and queries

- The definition-only library is `*.Contracts` (Commands/, Queries/, Events/, Models/, ValueObjects/). `*.Client` projects hold handwritten or generated HTTP senders, not definitions.
- Two coexisting styles (the main design risk for a generic catalog):
  1. EventStore-native (Tenants, and any module the REST generator targets): records implement `ICommandContract` / `IQueryContract` (`Hexalith.EventStore.Contracts/Commands/ICommandContract.cs`, `Queries/IQueryContract.cs`) with static abstract `CommandType` / `QueryType`, `Domain`, `ProjectionType`, and instance `AggregateId`; decorated with `[RestRoute(...)]`. Example: `Hexalith.Tenants/src/Hexalith.Tenants.Contracts/Commands/CreateTenant.cs`, `Queries/ListTenantsQuery.cs`.
  2. Plain records without an ecosystem marker (Timesheets, Projects, Parties). Projects uses a module-local `IProjectCommand` marker carrying TenantId / ProjectId / ActorPrincipalId / CorrelationId / IdempotencyKey. Example: `Hexalith.Timesheets/src/Hexalith.Timesheets.Contracts/Commands/TimeEntries/ApproveTimeEntry.cs`.
- `[PolymorphicSerialization]` is used only by Hexalith.Works. Not a viable ecosystem-wide discovery hook.
- Discovery today is compile-time only: the Roslyn generator `Hexalith.EventStore.RestApi.Generators` emits an `internal` manifest (`RestApiManifestEmitter.cs:36`), not consumable from other assemblies. Runtime `AssemblyScanner` scans aggregates and projections, not contracts. No public runtime catalog found.

### Conventions

- .NET 10, `.slnx` only, central package management through `Hexalith.Builds/Props/Directory.Packages.props`. Pinned: `ModelContextProtocol 2.2.0`, `ModelContextProtocol.AspNetCore 2.2.0`, `System.CommandLine 2.0.12`. No Spectre.Console anywhere.
- CLI shape reference: `Hexalith.EventStore.Admin.Cli` (PackAsTool, RootCommand + subcommands, global `--url/--token/--format/--output/--profile`, connection profiles, exit codes, JSON/CSV/table output, shell completions).
- Module layout is flat: `src/Hexalith.{Module}{,.Contracts,.Client,.Server,.UI,.Cli,.Mcp,...}` + `tests/`. `hexalith-llm-instructions.md` documents a different nested layout that no module follows (see Open items).
- Design rule from `hexalith-llm-instructions.md`: reuse technical modules rather than duplicating plumbing.

## Decisions (2026-09-21)

All six decisions below were made with the product owner on 2026-09-21. The option bodies that follow are rationale, kept for the architect and PRD author.

| Decision | Chosen for v1 | Next release | Not chosen |
| --- | --- | --- | --- |
| D1 Discovery | C. Hybrid: attribute for LLM metadata, contract interfaces for routing, attribute fallback | | A, B |
| D2 Assembly loading | A. Compile-time references + module marker | | B. Plugin folder |
| D3 Tool shape | B. Five generic discovery tools | | C. Typed tools behind a module filter; A |
| D4 Transport and identity | C. One binary; stdio shipped | HTTP with header forwarding | Any auth server |
| D5 CLI depth | A. Thin companion | | B. Generated per-operation subcommands |
| D6 Existing per-module servers | A. Replace (product owner override of the strangler recommendation) | Delete each legacy server once the generic one covers it | B, C |

## Constraints on every option

- Tenant is always envelope-supplied (profile, flag, or forwarded header), never taken from the payload.
- IDs are ULIDs; the catalog must not validate them as GUIDs.
- Message ID and idempotency key are generated by the tool per call; correlation ID optionally passed through.
- Queries and commands are distinguishable in the catalog so a read-only mode is one filter away.
- Only Hexalith dependencies: the EventStore client package and the `*.Contracts` libraries being exposed.

## Options considered

Six decisions (D1 to D6), in dependency order. Each option: disposition, one-line mechanism, pros, cons.

### D1. How the catalog discovers operations

**Option A. New attributes only (not chosen).** This module ships `[HexalithCommand]` / `[HexalithQuery]` carrying description, domain, type name, and aggregate-ID property; `System.ComponentModel.Description` on properties; server scans referenced Contracts assemblies at startup.
- Pros: works for all modules regardless of style; description lives next to the code; the attribute package is tiny and dependency-free.
- Cons: duplicates routing data (Domain, CommandType) that `ICommandContract` implementers already declare; two sources of truth for Tenants-style modules.

**Option B. Marker interfaces only (not chosen).** Rely on `ICommandContract` / `IQueryContract` from `Hexalith.EventStore.Contracts`; no new attribute package.
- Pros: zero new contracts; routing data is authoritative.
- Cons: Timesheets, Projects, Parties do not implement them today, so most modules are invisible until migrated; no place for an LLM-facing description (XML docs are not available at runtime); contradicts the product owner's requirement that this module provide the decoration attributes other modules apply.

**Option C. Hybrid (chosen).** Attribute carries description, read/write kind, and optional example. Routing (Domain, CommandType, AggregateId) comes from `ICommandContract` when the record implements it, from optional attribute properties when it does not. Property descriptions use `[Description]`.
- Pros: every module can be exposed today; encourages convergence on `ICommandContract` without blocking on it; single small attribute package.
- Cons: two code paths in the catalog builder (small, contained).

### D2. Assembly loading

**Option A. Compile-time references (chosen).** The server and CLI reference the chosen `*.Contracts` packages; the catalog scans loaded assemblies carrying an assembly-level `[HexalithModule]` marker.
- Pros: trivial; versions pinned by central package management; no plugin loader.
- Cons: adding a module means a rebuild. Acceptable for an internal tool.

**Option B. Plugin folder (parked).** Contracts DLLs dropped in a folder and loaded through an `AssemblyLoadContext` at startup.
- Pros: no rebuild.
- Cons: dependency resolution, version skew, load-context bugs. Over-engineering for v1.

### D3. Tool shape exposed over MCP

**Option A. One MCP tool per operation (parked).** A typed tool per command and query generated with `McpServerTool.Create(AIFunction)`.
- Pros: best per-call UX; protocol-level schema validation; single call to act.
- Cons: ten modules produce hundreds of tools, exceeding the limits in the tool-count guidance above. Needs a module filter to be usable.

**Option B. Generic discovery tools (chosen).** Five tools: `list_modules`, `list_operations(module)`, `describe_operation(name)` returning JSON schema and example, `send_command(name, tenant?, aggregateId?, payload)`, `run_query(name, ..., payload)`.
- Pros: constant tool count; matches the stated requirement (discover, then invoke); same catalog serves the CLI unchanged; payload validated against the generated schema before submission.
- Cons: two or three round trips before the first action; schema is in a response body, not a tool definition.

**Option C. Both, behind a filter (parked, first follow-up candidate).** Generic tools always on; `--expose parties,tenants` additionally publishes typed tools for those modules.
- Pros: best of both for focused sessions.
- Cons: more surface to test.

### D4. Transport and identity

**Option A. Local stdio process (v1 transport under Option C).** Shipped as a dotnet tool; EventStore URL, bearer token, and default tenant from a connection profile or environment variables (the `Hexalith.EventStore.Admin.Mcp` pattern). Identity is whoever owns the configured token.
- Pros: works with Claude Code, Claude Desktop, VS Code today; no hosting; no authentication server.
- Cons: a shared static token is a service principal; audit trail says "the tool", not the human.

**Option B. Hosted HTTP server (next-release transport under Option C).** ASP.NET Core Streamable HTTP, `AddMcpAuthentication` plus JWT bearer, forwarding the caller's bearer and `X-Tenant-Id` / `X-User-Id` to the EventStore through a delegating handler (the `Hexalith.Parties.Mcp` pattern).
- Pros: caller identity preserved end to end; one shared server for the whole install.
- Cons: deployment, TLS, token issuer wiring; the hard part is operations, not code.

**Option C. One binary, both transports (chosen).** `hexalith mcp --transport stdio|http`; v1 ships stdio; HTTP lands in the next release with the existing forwarding-handler pattern and no new authentication server.
- Pros: the SDK makes the transport switch a few lines; the catalog and executor are identical across both transports.
- Cons: HTTP authentication still needs a design pass before it is turned on in production.

### D5. CLI depth

**Option A. Thin companion (chosen).** Verbs `modules`, `operations <module>`, `describe <op>`, `send <op> --payload <json>`, `query <op> --payload <json>`, `mcp` (serve); global `--url --token --tenant --format json|table --profile`; profiles and exit codes borrowed from `Hexalith.EventStore.Admin.Cli`.
- Pros: small; proves the catalog without MCP; scriptable by shell-based agents; JSON on stdout, logs on stderr.
- Cons: payload as a JSON string is clumsy for humans.

**Option B. Generated per-operation subcommands (parked).** `hexalith parties create-party --name "..."` built dynamically from the catalog; `--help` doubles as discovery (the azmcp pattern).
- Pros: excellent human UX; shell completion over the whole domain.
- Cons: option typing for nested payloads gets fiddly.

### D6. Relationship to the six existing per-module MCP servers

**Option A. Replace (chosen, product owner override).** The six domain `Hexalith.*.Mcp` projects listed under Prior art are declared end of life; v1 proves the generic server on Tenants, Parties, Projects, and Folders; each legacy server is deleted as soon as the generic one covers it; no new per-module server is created after 2026-09-21. The generic server must cover the ChatBot catalog's feature set (read/write kind, optional correlation, task, and tenant args) before that server is deleted.
- Pros: removes the inconsistency for good; the ecosystem converges on one approach.
- Cons: feature parity is a hard requirement; cross-repo coordination for six deletions after v1.

**Option B. Coexist indefinitely (rejected).**
- Pros: no friction.
- Cons: the inconsistency this module exists to remove persists forever.

**Option C. Strangler (recommended by the facilitator, rejected by the product owner).** Coexist under two rules: no new per-module server; an existing one migrates when next touched.
- Pros: v1 ships independently; gradual convergence.
- Cons: a potentially unbounded transition period with two ways of doing things.

## Open items

- `hexalith-llm-instructions.md` documents a nested `src/libraries/...` module layout that no inspected module follows. Confirm the layout for this module with a maintainer before scaffolding.
- Kiota as an MCP generator is unverified (only community wrappers found). No official System.CommandLine-to-MCP bridge found. Neither blocks the design.
- The six `.Cli` projects were counted but not enumerated by the survey; list them before the deletion plan is written.
- HTTP mode authentication needs a design pass (issuer, token validation, header forwarding) before it is enabled in production.
