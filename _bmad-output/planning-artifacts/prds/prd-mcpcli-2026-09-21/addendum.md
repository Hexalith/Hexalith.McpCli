---
title: "PRD Addendum: Hexalith.McpCli"
status: final
created: 2026-09-21
updated: 2026-09-22
---

# PRD Addendum: Hexalith.McpCli

Normative: §E argument table and §G result documents (PRD FR-9, FR-11, and
FR-12 are specified against them). Context for architecture, solution design, and
implementation: §A–D, §F, §H.

## A. Rejected alternatives and options considered

Full options matrix (D1–D6, pros and cons): the brief addendum at
`_bmad-output/planning-artifacts/briefs/brief-mcpcli-2026-09-21/addendum.md`,
sections "Options considered" and "Decisions (2026-09-21)". Rejected, and
why:

- **D1 discovery** — attribute-only and marker-interface-only were both
  rejected in favor of the hybrid: attribute-only duplicates routing data that
  `ICommandContract` implementers already declare; marker-interface-only has no
  place for a description, and most modules do not implement the marker
  interfaces today.
- **D2 assembly loading** — plug-in folder via `AssemblyLoadContext` parked:
  dependency resolution and version skew are over-engineering for v1.
- **D3 tool shape** — one MCP tool per operation parked: ten modules produce
  hundreds of tools, past the tool-count guidance (see §C). "Both, behind a module
  filter" is parked (PRD §8.2).
- **D4 transport** — any authentication server rejected. Hosted HTTP is the
  next release, not v1, because the hard part is operations, not code.
- **D5 CLI depth** — generated per-operation subcommands parked: option
  typing for nested payloads gets fiddly.
- **D6 legacy servers** — coexist-indefinitely rejected (keeps the
  inconsistency forever); strangler rejected by the product owner because it
  means an unbounded transition with two ways of doing things (an explicit
  override of the facilitator's recommendation). Replace is the end
  state; see §D for the replacement inventory.
- **Profile store (2026-09-22)** — sharing `~/.eventstore/profiles.json` with
  the admin CLI rejected after validation: one profile name cannot target both
  the admin API and the Gateway, `csv` is unsupported here, and the admin CLI's
  `ConnectionProfile(Url, Token, Format)` has no extension-data member while
  `ProfileManager.Save` rewrites the whole file. Decision: own file, same
  shape (§E).
- **Per-call tenant wins (2026-09-22)** — rejected after validation: an LLM
  must not pick the tenant; the per-call argument is gated by the operator
  (PRD FR-16).

## B. Mechanism and transport decisions

**Envelope and Gateway rules**

- The Envelope records that the executor fills: `SubmitCommandRequest(MessageId,
  Tenant, Domain, AggregateId, CommandType, JsonElement Payload,
  CorrelationId?, Extensions?, IdempotencyKey?)` and
  `SubmitQueryRequest(Tenant, Domain, AggregateId, QueryType,
  ProjectionType?, Payload?, EntityId?, ProjectionActorType?)` plus its Paging, Search, Filters, OrderBy, and Freshness members (source:
  `extract-references.md` §B, which also lists `QueryEnvelope`,
  `QueryPagingOptions`, `QueryPagingMetadata`, and the
  `EventStoreGatewayException` members that PRD FR-11 maps to).
- `SubmitQueryRequest` has no correlation identifier or extensions member and
  its validator rejects additional properties, which is why PRD FR-16 sends
  neither on Queries.
- Gateway validator rules: `AggregateId` is required and nonempty on every
  Query (hence the `aggregateId` constant member); tenant, domain, and
  projection type are lowercase alphanumeric plus hyphens, at most 64
  characters; aggregate and entity identifiers are alphanumeric plus dots,
  hyphens, and underscores, at most 256 characters, no colon.
- Profile storage: `~/.eventstore/mcpcli.json`, this tool only (§E); why the
  admin CLI file is not shared: §A.
- Identifier type recognition (FR-7): the Catalog recognizes
  `ByteAether.Ulid.Ulid` by full type name, so the Decoration Package needs no reference to that type.

**Transport and host**

- Transport switch is `hexalith mcp --transport stdio|http`; v1 ships stdio
  only. HTTP reuses the Parties `McpContextForwardingHandler` pattern
  (bearer token, `X-Tenant-Id`, `X-User-Id`).
- Stdio host pattern to copy from `Hexalith.EventStore.Admin.Mcp`: the
  logging setup (all providers to stderr). Tool registration is not copied:
  the Generic Tools are built at runtime with `McpServerTool.Create` and a
  custom list-tools handler (spine AD-12), never static
  `[McpServerToolType]` classes.
- Exit codes 0/1/2 copied from `Hexalith.EventStore.Admin.Cli`, with the
  meaning of exit 1 narrowed to `describe --lint` (PRD FR-14).
- MCP C# SDK notes relevant to FR-9 and FR-19: the SDK has no first-class
  per-session tool filtering (open proposal #1881), so Read-only Mode is a
  startup decision, not a per-request one (see §C on why read-only removes
  the write tool rather than labeling it).

**Toolchain and layout**

- Pinned packages: ModelContextProtocol 2.2.0,
  ModelContextProtocol.AspNetCore 2.2.0, System.CommandLine 2.0.12. No
  Spectre.Console. Central package management via Hexalith.Builds.
- Flat layout `src/Hexalith.McpCli.*` and `tests/Hexalith.McpCli.*.Tests`,
  matching sibling modules rather than the nested layout documented in
  `hexalith-llm-instructions.md` (PRD Open Question 2, resolved by the
  architecture spine on 2026-09-22).
- Runtime targets: .NET 10, C# 14, `.slnx` only, xUnit v3 with Shouldly and
  NSubstitute, `TreatWarningsAsErrors`. The EventStore client package pulls
  the Dapr SDK into the global tool (PRD NFR-6).

**Catalog build**

- Assembly enumeration for FR-5: an MSBuild target collects `PackageReference`
  items carrying `HexalithContracts="true"` metadata into the scan list at
  build time; the tool is published untrimmed.

## C. Research and comparables

- MCP tool-count guidance: selection accuracy degrades beyond roughly 30–50
  tools; Claude Code caps MCP tool output at 25,000 tokens; VS Code cites a
  128-tool cap. Source: brief addendum, "Research extract".
- `Hexalith.FrontComposer.Mcp` is a prior generic, descriptor-driven MCP
  host inside Hexalith itself (runtime `McpCommandDescriptor` records,
  hosting the Projects plug-in): a comparable for the catalog idea. Its
  deletion status is in §D.
- CLI + MCP sharing one catalog: Azure `azmcp` (`--learn` progressive
  discovery, namespace and read-only filters, JSON stdout / logs stderr);
  Scaleway `scw mcp server serve` (stdio or streamable HTTP, filters by
  namespace, resource, verb, read-only).
- Landscape research for this PRD (`research-landscape.md` in this folder):
  - Catalog-driven MCP servers converge on four to six meta tools named
    list / describe / invoke.
  - MCP tool annotations (`readOnlyHint`, `destructiveHint`,
    `idempotentHint`) are per tool and clients treat them as untrusted
    server claims, which is why Read-only Mode removes the write tool
    rather than labeling it.
  - A fixed generic tool surface never needs `listChanged`.
  - Deterministic `tools/list` ordering keeps client prompt caches warm.
  - Speakeasy and Stainless generate one tool per operation, so this
    product's meta-tool shape is a deliberate divergence from the SDK
    generator camp.

## D. Prior art inventory

- **Legacy Servers to replace** (PRD §3): `Hexalith.Parties.Mcp`,
  `Hexalith.Folders.Mcp`, `Hexalith.ChatBot.Mcp`, `Hexalith.Memories.Mcp`
  (standalone), `Hexalith.FrontComposer.Mcp` (descriptor-driven host), and
  `Hexalith.Projects.Mcp` (the plug-in it hosts). The host and the plug-in
  are deleted together (FR-21).
- **Not targets:** `Hexalith.EventStore.Admin.Mcp` and `.Admin.Cli`, the
  admin-plane tools.
- **Parity bar:** `ChatBotMcpToolCatalog.cs` (read/write kind, correlation,
  task and tenant arguments).
- **Frozen CLIs** (PRD FR-22, deletion candidates on the FR-21 parity bar):
  Folders, Projects, ChatBot, FrontComposer, Memories, with divergent global
  options (`--base-address`, `--correlation-id`) and exit-code enums.

Survey facts that shaped the PRD (full detail in `extract-references.md`):

- Only `Hexalith.Parties.Mcp` reaches the EventStore Gateway, and it
  hand-rolls the HTTP call instead of using `IEventStoreGatewayClient`.
- The Folders, Projects, ChatBot, and Memories servers sit in front of module
  REST or Dapr APIs whose semantics (task scoping, freshness modes, dry-run
  gates, redaction) a Gateway call does not reproduce. Hence the
  "Gateway-ready" prerequisite in PRD §4 and §8.1.
- `Hexalith.Folders.Contracts` holds read models and OpenAPI YAML only, no
  command or query records.
- Tenants is the only module implementing `ICommandContract` /
  `IQueryContract`; wire `CommandType` differs per module (kebab-case, full
  type name, `nameof`). Hence canonical `module.kebab-case` Operation Names
  mapped to per-module wire values.
- Tenants runs every Command and Query under the Envelope tenant `system`
  (`TenantIdentity.ForTenant` puts the managed tenant in the aggregate
  identifier) and no longer has a projection actor; reads go through the
  read-model store by handler routing. Hence `fixedTenant` on the marker and
  `projectionActorType` being optional.
- None of the four v1 Contracts libraries carries a `[Description]`
  attribute.

## E. Generic Tool and CLI argument table

Both Heads implement every row with the spelling shown. Positional CLI
arguments are shown in angle brackets.

| Argument | MCP tools | CLI | Notes |
|---|---|---|---|
| module | `list_operations` | `operations <module>` | Module Name |
| kind | `list_operations` (optional) | `--kind read\|write` | filter |
| operation | `describe_operation`, `send_command`, `run_query` | `describe <op>`, `send <op>`, `query <op>` | Operation Name |
| payload | `send_command`, `run_query` | `--payload <json>` / `@file` / stdin | validated against the Schema |
| tenant | `send_command`, `run_query` (optional) | none per call; `--tenant` is a session setting (global) | the only per-call identity value, MCP only; honored per PRD FR-16 (fixed tenant, then operator gate) |
| aggregateId | `send_command`, `run_query` (optional) | `--aggregate-id` | explicit value wins over the constant; disagreement with the accessor value is a validation failure; required when a Query has no property and no constant |
| correlationId | `send_command` (optional) | `--correlation-id` | ULID, pass-through; Commands only (§B) |
| idempotencyKey | `send_command` (optional) | `--idempotency-key` | ULID; generated when absent; returned in the result |
| entityId | `run_query` (optional) | `--entity-id` | Gateway `EntityId` |
| pageSize, offset, cursor | `run_query` (optional) | `--page-size`, `--offset`, `--cursor` | Gateway paging; the only paging channel (PRD FR-16) |
| extensions | `send_command` (optional) | `--extension key=value` (repeatable) | Gateway `Extensions` map; keys must be in the Profile's `allowedExtensions`; Commands only (§B) |
| lint | none | `describe --lint` | lists undescribed properties, unmarked identifier-like properties, and Payload paging members; exit 1 if any |

Session settings. `--profile` resolves first (flag, `EVENTSTORE_PROFILE`, then
the file's `activeProfile`); every other setting resolves from the flag, then the environment variable,
then the selected Profile, then the default, skipping any source the table
marks none. Only the MCP `tenant` argument is a per-call source, gated by
PRD FR-16.

| Setting | Flag | Environment variable | Profile field | Default |
|---|---|---|---|---|
| url | `--url` | `EVENTSTORE_URL` | `url` | none (missing is `configuration_invalid`) |
| token | `--token` | `EVENTSTORE_TOKEN` | `token` | none |
| tenant | `--tenant` | `EVENTSTORE_TENANT` | `tenant` | none |
| actor | `--actor` | `EVENTSTORE_ACTOR` | `actor` | none |
| allowTenantOverride | `--allow-tenant-override` | `EVENTSTORE_ALLOW_TENANT_OVERRIDE` | `allowTenantOverride` | `false` |
| allowedExtensions | none | none | `allowedExtensions` | empty |
| format | `--format json\|table` | `EVENTSTORE_FORMAT` | `format` | `json` |
| output | `--output <file>` | none | none | stdout |
| read-only | `--read-only` | `EVENTSTORE_READ_ONLY` | none | `false` |
| strict | `--strict` | `EVENTSTORE_STRICT` | none | `false` |
| profile | `--profile` | `EVENTSTORE_PROFILE` | `activeProfile` | none |

Boolean environment variables accept `true`, `false`, `1`, `0`.

Profile file: `~/.eventstore/mcpcli.json`, this tool only:

```json
{
  "version": 1,
  "activeProfile": "dev",
  "profiles": {
    "dev": {
      "url": "https://gateway.example.test",
      "token": "…",
      "format": "json",
      "tenant": "acme",
      "actor": "01J9…",
      "allowTenantOverride": false,
      "allowedExtensions": ["task-id"]
    }
  }
}
```

`config use`, `config current`, and `config profile list|add|remove` mirror
the admin CLI; `config set <profile> <field> <value>` manages `tenant`,
`actor`, `allowTenantOverride`, and `allowedExtensions` (a comma-separated
list).

## F. Deferred capabilities

- Query search, filters, order-by, freshness: `SubmitQueryRequest` carries
  `Search`, `Filters`, `OrderBy`, `Freshness`; `EventStoreQueryResult`
  carries `ETag` and `IsNotModified`; `SubmitQueryAsync` accepts
  `ifNoneMatch`. Not exposed in v1 (PRD FR-9); excluded from parity
  (FR-21).
- Query correlation identifier and extensions: not carried by the pinned
  client's query request (§B). Deferred until the client carries them (PRD
  §8.2).
- Command status: the client's `GetCommandStatusAsync`. Not exposed in v1;
  the message identifier is returned so that status can be looked up with
  admin tools in the meantime (PRD §8.2).
- Executor retries: `EventStoreGatewayException.Retryable` and `RetryAfter`
  are surfaced to the caller (FR-11); the executor never retries (PRD §4
  Idempotency).

## G. Result and error documents

Both Heads serialize the same record types with the tool's canonical
serializer options; the MCP Server declares each record type as the output schema of the tool
that returns it (PRD FR-11). One example per document; optional members are omitted when
absent.

`list_modules`:

```json
{ "modules": [ { "name": "tenants", "description": "Tenant lifecycle and membership.", "operationCount": 6 } ] }
```

`list_operations`:

```json
{ "module": "tenants", "operations": [ { "name": "tenants.get-tenant-users", "kind": "read", "description": "Lists the users of one tenant." } ] }
```

`describe_operation`:

```json
{
  "name": "tenants.get-tenant-users", "kind": "read",
  "description": "Lists the users of one tenant.",
  "schema": { "type": "object", "additionalProperties": false, "properties": { "tenantId": { "type": "string", "description": "…" } }, "required": ["tenantId"] },
  "example": { "tenantId": "acme" },
  "envelope": { "fixedTenant": "system", "aggregateIdRequired": false, "arguments": ["aggregateId", "entityId", "pageSize", "offset", "cursor"] },
  "submittable": true
}
```

`arguments` lists the Envelope arguments the caller may supply; `tenant` is
omitted when the Module declares a `fixedTenant`.

`send_command` (`duplicate` is present once OQ-9 confirms the Gateway reports it):

```json
{ "operation": "parties.create-party", "messageId": "01J9…", "idempotencyKey": "01J9…", "correlationId": "01J9…", "tenant": "acme", "aggregateId": "01J9…", "status": "accepted", "duplicate": false, "result": { } }
```

`run_query`:

```json
{ "operation": "tenants.list-tenants", "tenant": "system", "document": [ ], "paging": { "pageSize": 50, "offset": 0, "nextCursor": "…", "totalCount": 120, "hasMore": true } }
```

Error documents (the CLI writes one to stdout with exit 2; the MCP Server
returns it as `structuredContent.error` with `isError: true`).

`validation_failed`:

```json
{ "error": { "code": "validation_failed", "operation": "parties.create-party", "violations": [ { "path": "/partyId", "message": "must match the ULID pattern" } ] } }
```

`gateway_error`:

```json
{ "error": { "code": "gateway_error", "status": 409, "reason": "conflict", "detail": "…", "retryable": false, "retryAfter": null, "clientAction": "inspect", "correlationId": "01J9…" } }
```

`unknown_operation`:

```json
{ "error": { "code": "unknown_operation", "operation": "parties.crate-party", "suggestions": ["parties.create-party"] } }
```

Other codes with only `code` and `message`: `read_only`, `catalog_empty`,
`catalog_invalid`, `unsupported_transport`, `configuration_invalid`,
`internal_error`.

## H. Module prerequisite detail

Expanded from PRD §8.1 for the Module maintainers.

- **Projects.** **Today:** `Hexalith.Projects.Contracts` carries ASP.NET
  Core, Fluxor, FluentUI, and FrontComposer.Shell, so it fails the PRD §4
  allowlist and the tool cannot reference it (FR-20). **Becomes:** a slimmed
  Contracts Library; Query types for the 11 resources the Legacy Server
  exposes; attribute routing (`wireType` from the instance `CommandType` property,
  `aggregateIdProperty = ProjectId`); `tenantProperty`,
  `correlationProperty`, `idempotencyKeyProperty`, and
  `actorProperty = ActorPrincipalId` naming the existing members, so records
  are unchanged; a decision on whether the server-side tenant guard in the
  Projects command submitter moves into the aggregate, since direct Gateway
  submission bypasses it. **Owner:** the Projects maintainer. **Acceptance:**
  `list_operations projects` shows the agreed subset and each Operation is
  accepted by the Gateway.
- **Folders.** **Today:** `Hexalith.Folders.Contracts` holds read models and
  OpenAPI only, and the Legacy Server exposes 49 tools over REST with
  dry-run, redaction, and freshness semantics. **Becomes:** decorated Command
  and Query types for the agent-facing subset, handled by a Folders domain
  service; dry-run, redaction, and freshness either move into handlers or are
  dropped and listed in the migration plan. **Owner:** the Folders
  maintainer. **Acceptance:** `list_operations folders` shows the agreed
  subset and each Operation is accepted by the Gateway.
