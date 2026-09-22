---
title: "PRD Addendum: Hexalith.McpCli"
status: final
created: 2026-09-21
updated: 2026-09-22
---

# PRD Addendum: Hexalith.McpCli

Material that informs the PRD but belongs to architecture, solution design, or
implementation rather than to the requirements themselves. The PRD references
this file; downstream documents draw from it.

## A. Rejected alternatives and options considered

The full options matrix (D1–D6, chosen / next release / not chosen, with pros
and cons per option) is preserved in the product brief addendum at
`_bmad-output/planning-artifacts/briefs/brief-mcpcli-2026-09-21/addendum.md`
under "Options considered" and "Decisions (2026-09-21)". It is not duplicated
here. Summary of what was rejected and why:

- **D1 discovery** — attribute-only (duplicates routing data that
  `ICommandContract` implementers already declare) and marker-interface-only
  (most modules do not implement them today; no place for a description)
  were both rejected in favor of the hybrid.
- **D2 assembly loading** — plug-in folder via `AssemblyLoadContext` parked:
  dependency resolution and version skew are over-engineering for v1.
- **D3 tool shape** — one MCP tool per operation parked: ten modules produce
  hundreds of tools, past the tool-count guidance (see §C). "Both, behind a module
  filter" is the first follow-up candidate.
- **D4 transport** — any authentication server rejected. Hosted HTTP is the
  next release, not v1, because the hard part is operations, not code.
- **D5 CLI depth** — generated per-operation subcommands parked: option
  typing for nested payloads gets fiddly.
- **D6 legacy servers** — coexist-indefinitely rejected (keeps the
  inconsistency forever); strangler rejected by the product owner, an
  explicit override of the facilitator's recommendation, because it means an
  unbounded transition with two ways of doing things. Replace is the end
  state; see §D for the replacement inventory.

## B. Mechanism and transport decisions

- Envelope records the executor fills: `SubmitCommandRequest(MessageId,
  Tenant, Domain, AggregateId, CommandType, JsonElement Payload,
  CorrelationId?, Extensions?, IdempotencyKey?)` and
  `SubmitQueryRequest(Tenant, Domain, AggregateId, QueryType,
  ProjectionType?, Payload?, EntityId?, ProjectionActorType?)` plus
  Paging / Search / Filters / OrderBy / Freshness. Confirmed against
  `extract-references.md` §B, which also lists `QueryEnvelope`,
  `QueryPagingOptions`, `QueryPagingMetadata`, and the
  `EventStoreGatewayException` members that the PRD's FR-11 maps to.
- Transport switch is `hexalith mcp --transport stdio|http`; v1 ships stdio
  only. HTTP reuses the Parties `McpContextForwardingHandler` pattern
  (bearer token, `X-Tenant-Id`, `X-User-Id`).
- Stdio host pattern to copy: `Hexalith.EventStore.Admin.Mcp` (static
  `[McpServerToolType]` classes, logging forced to stderr).
- Profiles and exit codes copied from `Hexalith.EventStore.Admin.Cli`
  (`~/.eventstore/profiles.json`, exit codes 0/1/2).
- Pinned packages: ModelContextProtocol 2.2.0,
  ModelContextProtocol.AspNetCore 2.2.0, System.CommandLine 2.0.12. No
  Spectre.Console. Central package management via Hexalith.Builds.
- Flat layout `src/Hexalith.McpCli.*` and `tests/Hexalith.McpCli.*.Tests`,
  matching sibling modules rather than the nested layout documented in
  `hexalith-llm-instructions.md` (PRD Open Question 2).
- Runtime targets: .NET 10, C# 14, `.slnx` only, xUnit v3 with Shouldly and
  NSubstitute, `TreatWarningsAsErrors`.
- MCP C# SDK notes relevant to FR-9 and FR-19: tools can be declared
  statically with `[McpServerToolType]` or built at runtime with
  `McpServerTool.Create` and a custom list-tools handler, which is the path
  for a catalog-driven surface; the SDK has no first-class per-session tool
  filtering (open proposal #1881), so Read-only Mode is a startup decision,
  not a per-request one (see §C on why read-only removes the write tool
  rather than labeling it).
- Profile storage: the admin CLI's `ConnectionProfile(Url, Token, Format)`
  has no extension-data member and `ProfileManager.Save` rewrites the whole
  file, so this tool keeps its default Tenant per Profile in
  `~/.eventstore/mcpcli.json` (PRD FR-18).
- Assembly enumeration for FR-5: the scan list is generated at build time
  from package references (source generator or MSBuild item), and the tool
  is published untrimmed or with Contracts assemblies rooted.

## C. Research and comparables

- MCP tool-count guidance: selection accuracy degrades beyond roughly 30–50
  tools; Claude Code caps MCP tool output at 25k tokens; VS Code cites a
  128-tool cap. Source: brief addendum, "Research extract".
- `Hexalith.FrontComposer.Mcp` is a prior generic, descriptor-driven MCP
  host inside Hexalith itself (runtime `McpCommandDescriptor` records,
  hosting the Projects plug-in). It is a comparable for the catalog idea and
  a deletion target once Projects is Gateway-ready.
- CLI + MCP sharing one catalog: Azure `azmcp` (`--learn` progressive
  discovery, namespace and read-only filters, JSON stdout / logs stderr);
  Scaleway `scw mcp server serve` (stdio or streamable HTTP, filters by
  namespace, resource, verb, read-only).
- Landscape research for this PRD (`research-landscape.md` in this folder):
  - Catalog-driven MCP servers converge on four to six meta tools named
    list / describe / invoke.
  - MCP tool annotations (`readOnlyHint`, `destructiveHint`,
    `idempotentHint`) are per tool and clients treat them as untrusted
    server claims, which is why read-only mode removes the write tool
    rather than labeling it.
  - A fixed generic tool surface never needs `listChanged`.
  - Deterministic `tools/list` ordering keeps client prompt caches warm.
  - Speakeasy and Stainless generate one tool per operation, so this
    product's meta-tool shape is a deliberate divergence from the SDK
    generator camp.
- `Hexalith.FrontComposer.Mcp` is a prior generic, descriptor-driven MCP
  host inside Hexalith itself (runtime `McpCommandDescriptor` records,
  hosting the Projects plug-in). It is a comparable for the catalog idea and
  a deletion target once Projects is Gateway-ready.
- CLI + MCP sharing one catalog: Azure `azmcp` (`--learn` progressive
  discovery, namespace and read-only filters, JSON stdout / logs stderr);
  Scaleway `scw mcp server serve` (stdio or streamable HTTP, filters by
  namespace, resource, verb, read-only).
- Landscape research for this PRD (`research-landscape.md` in this folder):
  catalog-driven MCP servers converge on four to six meta tools named
  list / describe / invoke; MCP tool annotations (`readOnlyHint`,
  `destructiveHint`, `idempotentHint`) are per tool and clients treat them as
  untrusted server claims, which is why read-only mode removes the write tool
  rather than labeling it; a fixed generic tool surface never needs
  `listChanged`; deterministic `tools/list` ordering keeps client prompt
  caches warm; Speakeasy and Stainless generate one tool per operation, so
  this product's meta-tool shape is a deliberate divergence from the SDK
  generator camp.

## D. Prior art inventory

The six per-module servers to replace: `Hexalith.Parties.Mcp`,
`Hexalith.Projects.Mcp`, `Hexalith.Folders.Mcp`, `Hexalith.Memories.Mcp`,
`Hexalith.ChatBot.Mcp`, `Hexalith.FrontComposer.Mcp`.
`Hexalith.EventStore.Admin.Mcp` and `.Admin.Cli` are admin-plane tools and
are not replacement targets. `ChatBotMcpToolCatalog.cs` is the feature-parity
bar (read/write kind, correlation, task and tenant args). Per-module CLIs found
in the survey: Folders, Projects, ChatBot, FrontComposer, Memories, with
divergent global options (`--base-address`, `--correlation-id`) and exit-code
enums; whether they are deletion targets is PRD Open Question 4.

Survey facts that shaped the PRD (full detail in `extract-references.md`):

- Only `Hexalith.Parties.Mcp` reaches the EventStore gateway, and it
  hand-rolls the HTTP call instead of using `IEventStoreGatewayClient`.
- Folders, Projects, ChatBot, and Memories servers front module REST or Dapr
  APIs with semantics (task scoping, freshness modes, dry-run gates,
  redaction) that a gateway call does not reproduce. Hence the
  "Gateway-ready" prerequisite in PRD §4.8 and §9.1.
- `Hexalith.Folders.Contracts` holds OpenAPI YAML only, no command or query
  records.
- Tenants is the only module implementing `ICommandContract` /
  `IQueryContract`; wire `CommandType` differs per module (kebab-case, full
  type name, `nameof`). Hence canonical `module.kebab-case` Operation Names
  mapped to per-module wire values.
- Zero `[Description]` attributes exist in any of the four v1 Contracts
  libraries.

## E. Generic Tool and CLI argument table

Both Heads implement every row under the spelling given. Positional CLI
arguments are shown in angle brackets.

| Argument | MCP tools | CLI | Notes |
|---|---|---|---|
| module | `list_operations` | `operations <module>` | Module Name |
| kind | `list_operations` (optional) | `--kind read\|write` | filter |
| operation | `describe_operation`, `send_command`, `run_query` | `describe <op>`, `send <op>`, `query <op>` | Operation Name |
| payload | `send_command`, `run_query` | `--payload <json>` / `@file` / stdin | validated against the Schema |
| tenant | `send_command`, `run_query` (optional) | `--tenant` (global) | per-call argument wins over flag |
| aggregateId | `send_command`, `run_query` (optional) | `--aggregate-id` | explicit value wins; disagreement with the Payload is a validation failure |
| correlationId | `send_command`, `run_query` (optional) | `--correlation-id` | ULID, pass-through |
| idempotencyKey | `send_command` (optional) | `--idempotency-key` | ULID; generated when absent; returned in the result |
| entityId | `run_query` (optional) | `--entity-id` | Gateway `EntityId` |
| pageSize, offset, cursor | `run_query` (optional) | `--page-size`, `--offset`, `--cursor` | Gateway paging |
| extensions | `send_command`, `run_query` (optional) | `--extension key=value` (repeatable) | Gateway `Extensions` map |
| lint | none | `describe --lint` | lists undescribed properties, exit 1 if any |

Global CLI options: `--url`, `--token`, `--tenant`, `--profile`, `--format
json|table`, `--output <file>`, `--read-only`, `--strict`.

Environment variables: `EVENTSTORE_URL`, `EVENTSTORE_TOKEN`,
`EVENTSTORE_TENANT`, `EVENTSTORE_FORMAT`, `EVENTSTORE_READ_ONLY`,
`EVENTSTORE_PROFILE`.

Resolution order for every option: per-call argument, flag, environment
variable, Profile, default. Defaults: format `json`; the URL default is the Gateway address that the
architecture document designates; no default Tenant.

Profile files: `~/.eventstore/profiles.json` (`version: 1`, `activeProfile`,
`profiles: { name: { url, token, format } }`, shared with the admin CLI) and
`~/.eventstore/mcpcli.json` (`{ profiles: { name: { tenant } } }`, this tool
only).

## F. Deferred capabilities

- Query search, filters, order-by, freshness: `SubmitQueryRequest` carries
  `Search`, `Filters`, `OrderBy`, `Freshness`; `EventStoreQueryResult`
  carries `ETag` and `IsNotModified`; `SubmitQueryAsync` accepts
  `ifNoneMatch`. Not exposed in v1 (PRD FR-9); excluded from parity
  (FR-21).
- Command status: the client's `GetCommandStatusAsync`. Not exposed in v1;
  the message identifier is returned so status can be looked up with admin
  tools meanwhile (PRD §9.2).
- Executor retries: `EventStoreGatewayException.Retryable` and `RetryAfter`
  are surfaced to the caller (FR-11); the executor never retries (§6).
