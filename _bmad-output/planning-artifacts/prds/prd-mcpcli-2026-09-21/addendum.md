---
title: "PRD Addendum: Hexalith.McpCli"
status: final
created: 2026-09-21
updated: 2026-09-22
---

# PRD Addendum: Hexalith.McpCli

Sections E and G are normative; PRD FR-9, FR-11, and FR-12 depend on them.
Sections A–D, F, and H provide context for architecture, solution design, and
implementation.

## A. Rejected alternatives and options considered

For the full D1–D6 options matrix, including pros and cons, see the brief
addendum at
`_bmad-output/planning-artifacts/briefs/brief-mcpcli-2026-09-21/addendum.md`,
sections "Options considered" and "Decisions (2026-09-21)". The following
alternatives were rejected:

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
- **D5 CLI depth** — generated per-Operation subcommands were deferred
  because typing options for nested Payloads becomes complex.
- **D6 legacy servers** — indefinite coexistence was rejected because it
  would preserve the inconsistency. The product owner rejected the strangler
  approach because it would create an unbounded transition with two ways of
  doing things, explicitly overriding the facilitator's recommendation.
  Replacement is the end state; see §D for the inventory.
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

- The executor fills two Envelope records: `SubmitCommandRequest(MessageId,
  Tenant, Domain, AggregateId, CommandType, JsonElement Payload,
  CorrelationId?, Extensions?, IdempotencyKey?)` and
  `SubmitQueryRequest(Tenant, Domain, AggregateId, QueryType,
  ProjectionType?, Payload?, EntityId?, ProjectionActorType?)`.
  `SubmitQueryRequest` also includes Paging, Search, Filters, OrderBy, and
  Freshness members. See `extract-references.md` §B, which also lists `QueryEnvelope`,
  `QueryPagingOptions`, `QueryPagingMetadata`, and the
  `EventStoreGatewayException` members that PRD FR-11 maps.
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
- Copy the logging setup from `Hexalith.EventStore.Admin.Mcp`; it sends all
  providers to stderr. Do not copy its tool registration. Build the Generic
  Tools at runtime with `McpServerTool.Create`; after settings resolution,
  register one Read-only-filtered `ToolCollection` and use the pinned SDK's
  built-in list and call dispatch (spine AD-12). Never use static
  `[McpServerToolType]` classes or a second list-tools handler.
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
- Comparable tools that share one Catalog between CLI and MCP surfaces include
  Azure `azmcp` (`--learn` progressive discovery, namespace and read-only
  filters, JSON on stdout, and logs on stderr) and Scaleway
  `scw mcp server serve` (stdio or streamable HTTP, with filters by namespace,
  resource, verb, and read-only status).
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
- Tenants is the only Module implementing `ICommandContract` or
  `IQueryContract`; wire `CommandType` differs per Module (kebab-case, full
  type name, `nameof`). This variation is why canonical `module.kebab-case`
  Operation Names map to Module-specific wire values.
- Tenants runs every Command and Query under the Envelope tenant `system`
  (`TenantIdentity.ForTenant` puts the managed tenant in the aggregate
  identifier) and no longer has a projection actor; reads go through the
  read-model store by handler routing. Hence `fixedTenant` on the marker and
  `projectionActorType` being optional.
- At the 2026-09-21 survey, none of the four candidate Contracts libraries
  carried a `[Description]` attribute. The accepted v1 scope later narrowed to
  Tenants and Parties; Projects and Folders follow after v1 (PRD FR-20).

## E. Generic Tool and CLI argument table

### Call arguments

Each Head implements every argument assigned to it in its column, with the
spelling shown. Positional CLI arguments are shown in angle brackets.

| Argument | MCP tools | CLI | Notes |
|---|---|---|---|
| module | `list_operations` | `operations <module>` | Module Name |
| kind | `list_operations` (optional) | `--kind read\|write` | filter |
| operation | `describe_operation`, `send_command`, `run_query` | `describe <op>`, `send <op>`, `query <op>` | Operation Name |
| payload | `send_command`, `run_query` | `--payload <json>` / `@file` / stdin | validated against the Schema |
| tenant | `send_command`, `run_query` (optional) | none per call; `--tenant` is a session setting (global) | the only per-call identity value, MCP only; honored per PRD FR-16 (fixed tenant, then operator gate) |
| aggregateId | `send_command`, `run_query` (optional) | `--aggregate-id` | explicit value wins over the constant; disagreement with the accessor value is a validation failure; required when a Query has no property and no constant |
| correlationId | `send_command` (optional) | `--correlation-id` | caller-supplied ULID is passed through; when omitted, the generated message identifier is used as command correlation; no second identifier is generated (§B) |
| idempotencyKey | `send_command` (optional) | `--idempotency-key` | caller-supplied ULID; never generated; passed through and echoed when present; retry safety requires a trusted Gateway adapter for the Command type |
| entityId | `run_query` (optional) | `--entity-id` | Gateway `EntityId` |
| pageSize, offset, cursor | `run_query` (optional) | `--page-size`, `--offset`, `--cursor` | Gateway paging; the only paging channel (PRD FR-16) |
| extensions | `send_command` (optional) | `--extension key=value` (repeatable) | Gateway `Extensions` map; keys must be in the Profile's `allowedExtensions`; Commands only (§B) |
| lint | none | `describe --lint` | `lintFindings` is always present in the describe result; this flag makes findings produce exit 1 |

The `module` argument is required and non-empty in both Heads. An absent or
empty argument fails input binding before Catalog dispatch: the MCP SDK returns
a JSON-RPC invalid-parameters error before tool invocation, while the CLI
returns the §G `invalid_arguments` document at exit 2 with `argument: module`.
`unknown_module` applies to a non-empty name that is absent from the Catalog.

### Session settings and profiles

For session settings, `--profile` resolves first: flag, `EVENTSTORE_PROFILE`,
then the file's `activeProfile`. Every other setting resolves in this order:
flag, environment variable, selected Profile, then default. Skip sources that
the table marks as `none`. Only the MCP `tenant` argument is a per-call source,
gated by PRD FR-16.

| Setting | Flag | Environment variable | Profile field | Default |
|---|---|---|---|---|
| url | `--url` | `EVENTSTORE_URL` | `url` | none; required only when an execution call reaches the Gateway |
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

### Success documents

Both Heads serialize the same record types by using the tool's canonical
serializer options. The MCP Server declares each record type as the output
schema for the tool that returns it (PRD FR-11). This section is exhaustive:
fields listed as required are always
present, arrays use `[]` when empty, and optional members are omitted rather than serialized as
`null`. Outer result fields use the canonical camel-case spelling below. Embedded `schema` and
`example` documents preserve the Module's serializer contract, including property casing.

| Document | Required members | Optional members |
|---|---|---|
| `list_modules` | `modules`; each item has `name`, `description`, `operationCount` | none |
| `list_operations` | `module`, `operations`; each item has `name`, `kind`, `description` | none |
| `describe_operation` | `name`, `kind`, `description`, `schema`, `envelope`, `lintFindings`, `submittable`; `envelope` has `aggregateIdRequired`, `idempotencyKeyRequired`, `arguments`; each lint finding has `code`, `severity`, `message` | `example`, `envelope.fixedTenant`, lint finding `property` (required for property-level findings), `reason` (required when `submittable` is `false`) |
| `send_command` | `operation`, `messageId`, `correlationId`, `tenant`, `aggregateId`, `status` | `idempotencyKey` (echoed only when caller-supplied), `result` (present only when the Gateway returns a result payload) |
| `run_query` | `operation`, `tenant`, `document` | `paging`; when present it requires `pageSize` and may independently include `offset`, `nextCursor`, `totalCount`, `hasMore` |

Public member types and constraints:

| Member | JSON contract |
|---|---|
| Success Module `name` / `module` | non-empty string equal to a declared canonical Module Name; the `unknown_module` error's `module` member follows the error rule below |
| `operation` / Operation `name` | non-empty string in the FR-8 canonical form |
| `description`, `message`, `detail` | non-empty string |
| `operationCount`, `paging.offset`, `paging.totalCount` | integer greater than or equal to zero |
| `paging.pageSize` | integer greater than zero |
| `kind` | string enum: `read`, `write` |
| `schema` | JSON object produced by FR-7 |
| `example` | JSON object that validates against `schema` |
| `envelope` | JSON object; `fixedTenant` is a Gateway-valid Tenant string; `aggregateIdRequired` and `idempotencyKeyRequired` are booleans; `idempotencyKeyRequired` is true exactly when the Operation names a non-nullable `idempotencyKeyProperty`; `arguments` is a duplicate-free array of applicable §E argument-name strings |
| `lintFindings` | array of objects defined below; empty when no finding exists |
| `submittable` | boolean describing head-level surface availability from Read-only Mode and resolved Gateway URL only; Tenant, actor, Payload, and per-call Envelope requirements are evaluated on execution; `reason` is `read_only` or `configuration_invalid` when false |
| `messageId`, `correlationId`, `idempotencyKey` | ULID string; `messageId` is the Gateway's canonical execution identifier |
| `tenant` | non-empty string satisfying the FR-15 Gateway Tenant pattern |
| `aggregateId` | non-empty string satisfying the FR-15 Gateway aggregate-identifier pattern and the Module's Identifier Kind |
| `status` | string constant `accepted`, representing the successful Gateway `202 Accepted` response; later values require a public-contract change |
| `result` | any JSON value returned as `SubmitCommandResponse.ResultPayload`; omitted when the Gateway returns no payload |
| `document` | any JSON value returned as `EventStoreQueryResult.Payload` |
| `paging.nextCursor` | non-empty string when present |
| `paging.hasMore` | boolean |

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
  "schema": { "type": "object", "additionalProperties": false, "properties": { "TenantId": { "type": "string", "description": "…" } }, "required": ["TenantId"] },
  "example": { "TenantId": "acme" },
  "envelope": { "fixedTenant": "system", "aggregateIdRequired": false, "idempotencyKeyRequired": false, "arguments": ["aggregateId", "entityId", "pageSize", "offset", "cursor"] },
  "lintFindings": [],
  "submittable": true
}
```

`arguments` lists the Envelope arguments the caller may supply; `tenant` is
omitted when the Module declares a `fixedTenant`. Lint finding `code` is one of
`missing_property_description`, `unmarked_identifier_like_property`,
`payload_paging_member`, or `hollow_description`; `severity` is the string
constant `warning`. For the first three codes, `property` is an RFC 6901 JSON
Pointer to the recursively inspected property, using Module-serialized casing.
The operation-level `hollow_description` finding omits `property`.

`send_command` (example with a caller-supplied idempotency key):

```json
{ "operation": "parties.create-party", "messageId": "01J9…", "idempotencyKey": "01J9…", "correlationId": "01J9…", "tenant": "acme", "aggregateId": "party-42", "status": "accepted", "result": { } }
```

The tool does not infer replay when the returned `messageId` differs from the
identifier generated for the attempt. The Gateway uses the canonical execution
identifier for both replay and pending admission, but its response provides no
generic replay classification.
Callers must not retry an unknown command outcome unless the target deployment has
confirmed a trusted idempotency adapter for that Command type.

`run_query`:

```json
{ "operation": "tenants.list-tenants", "tenant": "system", "document": [ ], "paging": { "pageSize": 50, "offset": 0, "nextCursor": "…", "totalCount": 120, "hasMore": true } }
```

### Error documents

The CLI writes an error document to stdout with exit 2; the MCP Server
returns it as `structuredContent.error` with `isError: true`. For any `mcp`
failure before JSON-RPC initialization, the CLI instead writes the structured
error to stderr and leaves stdout empty. After initialization, failures travel
only as JSON-RPC/MCP errors.

| Error code | Required members under `error` | Optional members under `error` |
|---|---|---|
| `validation_failed` | `code`, `operation`, `violations`; each violation has `path`, `message` | none |
| `gateway_error` | `code`, `status`, `detail` | `reason`, `retryable`, `clientAction`, `retryAfter`, `correlationId` |
| `unknown_operation` | `code`, `operation`, `suggestions` | none |
| `unknown_module` | `code`, `module`, `suggestions` | none |
| `invalid_arguments` | `code`, `argument`, `message` | none |
| `read_only`, `catalog_empty`, `catalog_invalid`, `unsupported_transport`, `configuration_invalid`, `internal_error` | `code`, `message` | none |

Error member types and constraints:

- `error` is an object; `code` is exactly the row's string discriminator.
- `operation` follows the Operation Name contract above. For
  `unknown_operation`, `suggestions` is an array of at most three canonical
  Operation Name strings. For `unknown_module`, `module` is the exact non-empty
  requested Module Name and `suggestions` is an array of at most three declared
  canonical Module Name strings. Both suggestion lists are ordered by
  case-insensitive edit distance, with ordinal name order breaking ties.
- `invalid_arguments` is emitted by CLI Head input binding before a Core call;
  `argument` is the non-empty canonical §E argument name and `message` explains
  the missing or invalid value. MCP input-schema binding failures use JSON-RPC
  invalid parameters before tool invocation, outside these tool documents.
- `violations` is a non-empty array; each `path` is an RFC 6901 JSON Pointer and
  each `message` is a non-empty string.
- Gateway `status` is the integer `EventStoreGatewayException.StatusCode`
  copied without reclassification. It may therefore be `2xx` when the pinned
  client reports an HTTP-success response that is malformed or fails semantic
  validation. `detail` is the first non-empty value of
  `EventStoreGatewayException.Detail` and `.Title`, so it is always present.
  `reason` is the first non-empty value of `.ReasonCode`,
  `.Code`, and `.Reason`; it is omitted when all are absent. `clientAction` is
  a non-empty forward-compatible Gateway string when supplied; `retryable` is
  boolean when supplied; `retryAfter` is the non-empty Gateway header or
  extension string; and `correlationId` is a ULID string. No optional value is
  synthesized. Fixtures cover complete Gateway Problem Details, malformed
  `202` command and `200` query responses, a semantic query failure, and a
  locally created client exception with optional metadata absent.

`validation_failed`:

```json
{ "error": { "code": "validation_failed", "operation": "parties.create-party", "violations": [ { "path": "/PartyId", "message": "must match the aggregate identifier pattern" } ] } }
```

`gateway_error`:

```json
{ "error": { "code": "gateway_error", "status": 409, "reason": "conflict", "detail": "…", "retryable": false, "clientAction": "inspect", "correlationId": "01J9…" } }
```

`unknown_operation`:

```json
{ "error": { "code": "unknown_operation", "operation": "parties.crate-party", "suggestions": ["parties.create-party"] } }
```

`unknown_module`:

```json
{ "error": { "code": "unknown_module", "module": "partes", "suggestions": ["parties"] } }
```

CLI input binding (`invalid_arguments`):

```json
{ "error": { "code": "invalid_arguments", "argument": "module", "message": "module is required and must be non-empty" } }
```

### Offline discovery

Catalog-only discovery does not require a resolved Gateway URL. A missing URL
produces `configuration_invalid` for execution calls only: `send`, `query`,
`send_command`, and `run_query`. It does not prevent `modules`, `operations`, `describe`, `config`,
`--version`, MCP startup, or MCP discovery calls. In such a session,
`describe_operation` returns `submittable: false, reason: configuration_invalid`
unless a write Operation is already blocked by Read-only Mode, which takes
precedence as `reason: read_only`.

## H. Module prerequisite detail

Expanded from PRD §8.1 for the Module maintainers.

- **Projects.** **Today:** `Hexalith.Projects.Contracts` carries ASP.NET
  Core, Fluxor, FluentUI, and FrontComposer.Shell, so it fails the PRD §4
-  allowlist and the tool cannot reference it (FR-20). **Becomes:** Slim the
  Contracts Library. Add Query types for the 11 resources the Legacy Server
  exposes. Configure attribute routing with `wireType` from the instance
  `CommandType` property and `aggregateIdProperty = ProjectId`. Name the
  existing members through `tenantProperty`, `correlationProperty`,
  `idempotencyKeyProperty`, and `actorProperty = ActorPrincipalId`, so the
  records remain unchanged. Decide whether the server-side tenant guard in the
  Projects command submitter moves into the aggregate because direct Gateway
  submission bypasses it. **Owner:** the Projects maintainer. **Acceptance:**
  `list_operations projects` shows the agreed subset and each Operation is
  accepted by the Gateway.
- **Folders.** **Today:** `Hexalith.Folders.Contracts` holds read models and
  OpenAPI only, and the Legacy Server exposes 49 tools over REST with
  dry-run, redaction, and freshness semantics. **Becomes:** Add decorated
  Command and Query types for the agent-facing subset, handled by a Folders
  domain service. Move dry-run, redaction, and freshness into handlers or drop
  them and list them in the migration plan. **Owner:** the Folders
  maintainer. **Acceptance:** `list_operations folders` shows the agreed
  subset and each Operation is accepted by the Gateway.
