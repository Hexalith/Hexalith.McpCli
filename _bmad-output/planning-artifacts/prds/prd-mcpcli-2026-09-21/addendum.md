---
title: "PRD Addendum: Hexalith.McpCli"
status: final
created: 2026-09-21
updated: 2026-11-20
changeProposals:
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-06.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-08.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-10.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-10-shape-coverage.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-20.md
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
- **D4 transport** — v1 uses stdio. Shared HTTP and per-user authority remain
  deferred under AD-23 K10 and PRD §8.2.
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
- A computed Query such as `projects.list` can omit both projection selectors.
  An explicit `projectionActorType` requires a resolved `projectionType` (FR-2).
- Gateway validator rules: `AggregateId` is required and nonempty on every
  Query (hence the `aggregateId` constant member); ordinary tenants, domain, and
  projection type are lowercase ASCII alphanumeric plus hyphens, at most 64
  characters. Declared platform request scopes use the separate `platform:`
  grammar and exact matching in PRD FR-15/16; public variable-scope tenant inputs
  are lowercased without trimming before selection and override comparison, and
  public `system` is reserved. Story 5.18 requires rejection of non-ASCII public input
  before lowercasing once the upstream EventStore change lands (FR-16). Aggregate and entity identifiers are alphanumeric plus dots,
  hyphens, and underscores, at most 256 characters, no colon.
- Profile storage: default `~/.eventstore/mcpcli.json`, relocated through an
  absolute `MCPCLI_HOME` under PRD FR-18 (§E), this tool only; why the
  admin CLI file is not shared: §A.
- Identifier type recognition (FR-7): the Catalog recognizes
  `ByteAether.Ulid.Ulid` by full type name, so the Decoration Package needs no reference to that type.

**Transport and host**

- `hexalith mcp --transport stdio` runs the shipped host. Selecting `http`
  returns `unsupported_transport`. The legacy Parties
  `McpContextForwardingHandler` forwarded the incoming bearer token and
  identity headers. AD-23 K10 keeps shared HTTP deferred pending product-owner
  approval of an AD-14 token exchange. The service must validate issuer and
  audience, map the client, and attest the authenticated actor and effective
  origin. Forwarding the raw incoming bearer token is prohibited. The Gateway
  receives the exchanged credential. Approval requires
  denial evidence from the selected environment for invalid credentials or
  spoofed identity. [AD-23 K10](../../architecture/architecture-mcpcli-2026-09-22/AD-23-non-gateway-capability-classes.md#deferrals-and-disposition-rules)
- Copy the logging setup from `Hexalith.EventStore.Admin.Mcp`; it sends all
  providers to stderr. Do not copy its tool registration. Build the Generic
  Tools at runtime with `McpServerTool.Create`; after settings resolution,
  register one Read-only-filtered `ToolCollection` and use the pinned SDK's
  built-in list and call dispatch. An SDK `ListToolsFilters` filter orders the
  assembled list by the fixed permitted-name sequence (spine AD-12); collection
  insertion order is not a discovery guarantee. Never use static
  `[McpServerToolType]` classes or a second list-tools handler.
- Exit codes 0/1/2 copied from `Hexalith.EventStore.Admin.Cli`, with the
  meaning of exit 1 narrowed to `describe --lint` (PRD FR-14).
- MCP C# SDK notes relevant to FR-9 and FR-19: the SDK has no first-class
  per-session tool filtering (open proposal #1881), so Read-only Mode is a
  startup decision, not a per-request one (see §C on why read-only removes
  the write tool rather than labeling it).

**Toolchain and layout**

- Current packages: ModelContextProtocol 2.4.0 and System.CommandLine 3.0.0.
  ModelContextProtocol.AspNetCore remains reserved for the future HTTP release.
  No Spectre.Console. Effective versions come from the root-declared
  Hexalith.Builds catalog, root build overrides and dependency policy; this
  reconciliation authorizes no package update.
- Flat layout `src/Hexalith.McpCli.*` and `tests/Hexalith.McpCli.*.Tests`,
  matching sibling modules rather than the nested layout documented in
  `hexalith-llm-instructions.md` (PRD Open Question 2, resolved by the
  architecture spine on 2026-09-22).
- Runtime targets: .NET 11, C# 15, `.slnx` only, xUnit v3 with Shouldly and
  NSubstitute, `TreatWarningsAsErrors`. The EventStore client package pulls
  the Dapr SDK into the global tool (PRD NFR-6).

**Catalog build**

- Assembly enumeration for FR-5: an MSBuild target collects `PackageReference`
  items carrying `HexalithContracts="true"` metadata into the scan list at
  build time; the tool is published untrimmed.
- A Module may set `SerializerOptionsProvider` to a type in its marked
  Contracts assembly. That type must directly declare a public static,
  non-indexed `JsonSerializerOptions Options { get; }` returning a non-null
  value. The tool copies its converters in order into the Module's cached
  Payload options and retains the canonical resolver and other settings.
  Omitting the provider uses canonical defaults. A foreign type, invalid
  getter, thrown exception or null return excludes the Module with the
  assembly diagnostic `invalid_serializer_options_provider` (PRD §5.1, FR-6).

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
- **Successor migration targets:** `Hexalith.EventStore.Admin.Mcp` and
  `.Admin.Cli` are obsolete proprietary surfaces. Their infrastructure
  operations have owner-approved dispositions under AD-23. The confidential UI,
  withdrawal and authorization/effect gates in the Admin inventory govern removal.
- **Parity bar:** `ChatBotMcpToolCatalog.cs` (read/write kind, correlation,
  task and tenant arguments).
- **Local-tooling exemptions.** AD-23 K13 retains FrontComposer’s local
  `inspect` and `migrate` commands. K14 retains the owner-held Memories
  `MigrateEmbeddingVectors` tool. Both are excluded from the retirement count.
  Other inventoried CLI and MCP surfaces keep their FR-21 owner and evidence gates.

Survey findings from 2026-09-21 (full detail in `extract-references.md`):

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
- At the original 2026-09-21 survey, Tenants ran every Command and Query under
  the Envelope tenant `system` (`TenantIdentity.ForTenant` put the managed
  tenant in the aggregate identifier). That historical design motivated
  `fixedTenant`; it is not current Tenants enrollment policy. Current Commands
  and cross-tenant reads declare `platform:tenants`; single-tenant reads use the
  selected public tenant and matching aggregate identifier (PRD §8.1). Projection
  actor routing remains optional and follows the owning contract.
- At the 2026-09-21 survey, none of the four candidate Contracts libraries
  carried a `[Description]` attribute. The accepted v1 scope later narrowed to
  Tenants and Parties. PRD §8.1 records the current cohort.

## E. Generic Tool and CLI argument table

### Call arguments

Each Head implements every argument assigned to it in its column, with the
spelling shown. Positional CLI arguments are shown in angle brackets.

| Argument | MCP tools | CLI | Notes |
|---|---|---|---|
| module | `list_operations` | `operations <module>` | Module Name |
| kind | `list_operations` (optional) | `--kind read\|write` | filter |
| operation | `describe_operation`, `send_command`, `run_query` (required string) | `describe <op>`, `send <op>`, `query <op>` | Non-empty Operation Name |
| payload | `send_command`, `run_query` (required string containing JSON text) | `--payload <json>`, `--payload @file`, or `--payload -` for stdin | The Operation Schema describes the decoded JSON value. |
| tenant | `send_command`, `run_query` (optional) | none per call; `--tenant` is a session setting (global) | the only per-call identity value, MCP only; honored per PRD FR-16 (declared platform scope, else fixed tenant, else canonical public tenant under the operator gate) |
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

For a session configured for tenant `vector-users` and an actor authorized
to read that tenant, the shipped `tenants.get-tenant-users` Query accepts
this MCP request. Its `TenantId` supplies the aggregate. Paging belongs in
the tool arguments.

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "run_query",
    "arguments": {
      "operation": "tenants.get-tenant-users",
      "payload": "{\"TenantId\":\"vector-users\"}",
      "tenant": "vector-users",
      "pageSize": 2
    }
  }
}
```

In either MCP revision, a missing required argument or an object passed
directly as `payload` fails input binding with JSON-RPC `InvalidParams`
(`-32602`) before tool invocation. Once an available Operation of the
matching kind is resolved, malformed JSON inside a bound string produces
the §G `validation_failed` tool result at `/`. Both failures send zero
Gateway requests.

After Core resolves an Operation Name, `send_command`/`send` requires kind
`write` and `run_query`/`query` requires kind `read`. A mismatch returns
`validation_failed` with one violation at `/operation` before Read-only or
missing-URL availability checks and before Payload parsing, regardless of the
session. A matching write Operation in Read-only Mode still returns `read_only`.

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

With `--output`, ordinary CLI results go to the selected file and stdout stays
empty, including when `describe --lint` exits 1. Errors at exit 2 go to stdout
as §G JSON regardless of `--output` or `--format`. If the destination check
fails before a Gateway call or Profile change, the error message is
`The result destination cannot be written; no request was sent.` A later write
failure can follow either action. Inspect the target state before retrying.
FR-14 gives the full exit-code contract, including interruption.

For `mcp --transport stdio`, valid inherited
`format` is ignored for protocol output; explicit `--format json` is accepted.
Explicit `--format table` and any `--output` fail before Catalog or transport
startup with one §G `invalid_arguments` object on stderr (`argument: format` or
`output`, format first if both), zero stdout bytes, exit 2, and no output file
opened. Malformed inherited settings still fail ordinary validation. These
options never reformat or redirect the protocol stream.

When a URL and token both resolve, both must come from flags, from the environment
or from the selected Profile. A mixed pair is `configuration_invalid`.
A URL may be used without a token.

**Private credential entry (Story 5.16, backlog).** Profile creation and
rotation must support a non-echoing terminal prompt and explicitly selected
stdin for automation. Reject conflicting inputs. Keep the token out of process
arguments, stdout, stderr and diagnostics on these paths. Ordinary commands
and MCP stdio retain their input streams. Use the locked private-file
transaction so cancellation or invalid input preserves the original settings
and permissions. Both Heads must require HTTPS for a bearer token sent to a non-loopback
Gateway. Profile mutations must also reject unsafe stored combinations.
Operators may use HTTPS or the documented private loopback port-forward.

Boolean environment variables accept `true`, `false`, `1`, `0`.

Profile file: default `~/.eventstore/mcpcli.json`, this tool only. An explicit
constructor file path takes precedence; otherwise an absolute `MCPCLI_HOME`
selects `<MCPCLI_HOME>/.eventstore/mcpcli.json` on every OS, and an unset override
uses the user-profile home. Empty, whitespace-only, relative,
control-character-containing or existing-file overrides fail safely as
`configuration_invalid` without exposing the path or falling back to the real
home. This is a store-location selector outside the session-setting table, not
an identity or per-call override. Existing atomicity and file protections apply.
Under Story 5.19, measure the completed UTF-8 serialization before replacement.
Exactly 1,048,576 bytes is valid. One byte over must leave the prior file,
permissions and active Profile intact and remove the temporary file (FR-18).

Profile document:

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
      "actor": "01J9MZHXT3RKM0VWXRXGSJDATK",
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

- The generic Heads defer the Gateway's `Search`, `Filters`, `OrderBy`
  and `Freshness` arguments and HTTP conditional requests and responses
  (`ifNoneMatch`, `ETag`, `IsNotModified`). The parity exclusion applies
  only to those generic features. For each approved replacement, FR-21 and
  AD-23 K03 still require evidence for its Payload and handler semantics.
  Where applicable, prove the fixed or explicit freshness value, defaults,
  supported inputs, filtering before Envelope paging, totals and continuation
  contents. Verify rejection of conflicting, unsupported and out-of-bounds
  inputs. [AD-23 K03](../../architecture/architecture-mcpcli-2026-09-22/AD-23-non-gateway-capability-classes.md)
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
`null`. CLI profile-management documents explicitly report `"activeProfile": null` when their result includes the active selection and no profile is active. Outer result fields use the canonical camel-case spelling below. Embedded `schema` and
`example` documents preserve the Module's serializer contract, including property casing.
Decoration property-reference strings use exact top-level CLR names; the Catalog
resolves `[JsonPropertyName]` and caches serialized names and escaped pointers for
Schema, envelope ownership, and aggregate access (PRD §5.1). Pre-fill validation
removes only mapped envelope-owned members from a copy, retains the raw values
for ownership checks, and validates the complete rebuilt Payload after filling
(PRD FR-16).

| Document | Required members | Optional members |
|---|---|---|
| `list_modules` | `modules`; each item has `name`, `description`, `operationCount` | none |
| `list_operations` | `module`, `operations`; each item has `name`, `kind`, `description` | none |
| `describe_operation` | `name`, `kind`, `description`, `schema`, `envelope`, `lintFindings`, `submittable`; `envelope` has `aggregateIdRequired`, `idempotencyKeyRequired`, `arguments`; each lint finding has `code`, `severity`, `message` | `example`, `envelope.fixedTenant`, `envelope.platformScope`, lint finding `property` (required for property-level findings), `reason` (required when `submittable` is `false`) |
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
| `schema` | JSON object produced by FR-7; contents remain open, including nested boolean schemas (owner clarification, 2026-11-08) |
| `example` | JSON object that validates against `schema` |
| `envelope` | JSON object; `fixedTenant` is an exact Gateway-valid ordinary Tenant string; `platformScope` is an exact declared `platform:` scope under PRD §5.1; the two optional members are mutually exclusive; `aggregateIdRequired` and `idempotencyKeyRequired` are booleans; `idempotencyKeyRequired` is true exactly when the Operation names a non-nullable or serializer-required `idempotencyKeyProperty` (effective `JsonPropertyInfo.IsRequired` under its Payload options); `arguments` is a duplicate-free array of applicable §E argument-name strings |
| `lintFindings` | array of objects defined below; empty when no finding exists |
| `submittable` | boolean describing head-level surface availability from Read-only Mode and resolved Gateway URL only; Tenant, actor, Payload, and per-call Envelope requirements are evaluated on execution; `reason` is `read_only` or `configuration_invalid` when false |
| `messageId`, `correlationId`, `idempotencyKey` | canonical uppercase ULID string (FR-17 governs acknowledgment and fallback) |
| `tenant` | non-empty resolved ordinary/fixed Tenant satisfying FR-15, or the exact declared platform scope under FR-16; a public variable-scope `system` value is refused |
| `aggregateId` | non-empty string satisfying the FR-15 Gateway aggregate-identifier pattern and the Module's Identifier Kind |
| `status` | string constant `accepted` in a successful Command result. The HTTP response code appears as an integer only on `gateway_error`. |
| `result` | any JSON value returned as `SubmitCommandResponse.ResultPayload`; omitted when the Gateway returns no payload |
| `document` | any JSON value returned as `EventStoreQueryResult.Payload`, including a required `document: null` when the Payload is null |
| `paging.nextCursor` | non-empty string when present |
| `paging.hasMore` | boolean |

The following JSON documents illustrate the result shapes with synthetic data.

`list_modules`:

```json
{ "modules": [ { "name": "tenants", "description": "Tenant lifecycle and membership.", "operationCount": 15 } ] }
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
  "envelope": { "aggregateIdRequired": false, "idempotencyKeyRequired": false, "arguments": ["tenant", "aggregateId", "entityId", "pageSize", "offset", "cursor"] },
  "lintFindings": [],
  "submittable": true
}
```

For `tenants.list-tenants`, the corresponding platform-scoped Envelope is:

```json
{ "platformScope": "platform:tenants", "aggregateIdRequired": false, "idempotencyKeyRequired": false, "arguments": ["aggregateId", "entityId", "pageSize", "offset", "cursor"] }
```

`arguments` lists the Envelope arguments the caller may supply; `tenant` is
omitted when the Operation declares a platform scope or the Module declares a
fixed tenant. Either declaration ignores the session tenant and requires an
exact ordinal match from any supplied per-call tenant; the operator override
gate cannot replace a declaration. Variable-scope values follow FR-16's
canonicalization and operator gate. Lint finding `code` is one of
`missing_property_description`, `unmarked_identifier_like_property`,
`payload_paging_member`, or `hollow_description`; `severity` is the string
constant `warning`. For the first three codes, `property` is an RFC 6901 JSON
Pointer to the recursively inspected property, using Module-serialized casing.
The operation-level `hollow_description` finding omits `property`.

`send_command` for an authorized `parties.reactivate-party` call with a
caller-supplied idempotency key (Parties inventory T06, AD-23 K01):

```json
{ "operation": "parties.reactivate-party", "messageId": "01J9MZHXT3RKM0VWXRXGSJDATM", "idempotencyKey": "01J9MZHXT3RKM0VWXRXGSJDATN", "correlationId": "01J9MZHXT3RKM0VWXRXGSJDATK", "tenant": "acme", "aggregateId": "party-42", "status": "accepted" }
```

An accepted result always uses the correlation ID submitted with the Command,
whether caller-supplied or generated, including when the Gateway echoes a
different valid correlation ID. If the acknowledgment omits `messageId` or
sets it to null, use the submitted message ID. If the Gateway supplies a canonical
message ID, return it even when it differs from the submitted one.

The tool does not infer replay when the returned `messageId` differs from the
identifier generated for the attempt. The Gateway uses the canonical execution
identifier for both replay and pending admission, but its response provides no
generic replay classification.
Callers must not retry an unknown command outcome unless the target deployment has
confirmed a trusted idempotency adapter for that Command type.

`run_query`:

```json
{ "operation": "tenants.list-tenants", "tenant": "platform:tenants", "document": [ ], "paging": { "pageSize": 50, "offset": 0, "nextCursor": "…", "totalCount": 120, "hasMore": true } }
```

### Error documents

At exit 2 an ordinary CLI action writes one error document to stdout. An
`mcp` startup failure writes the structured error to stderr and leaves stdout
empty. Once serving, a bound tool's failure sets `isError: true`, places the
error in `structuredContent.error`, and includes the same document as JSON in
the first text content block. JSON-RPC input-binding failures precede tool
invocation (§E). These rules apply to both supported protocol revisions.
Normal MCP shutdown exits 0. A faulted hosting service writes
`MCP server stopped unexpectedly.` to stderr and exits 2.

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
- `operation` follows the Operation Name contract above except that
  `unknown_operation.operation` preserves the exact non-empty requested name,
  including noncanonical spelling (owner decision, 2026-11-08). For
  `unknown_operation`, `suggestions` is an array of at most three canonical
  Operation Name strings. For `unknown_module`, `module` is the exact non-empty
  requested Module Name and `suggestions` is an array of at most three declared
  canonical Module Name strings. Both suggestion lists are ordered by
  case-insensitive edit distance, with ordinal name order breaking ties.
- `invalid_arguments` can arise during CLI input binding or during semantic
  checks on a bound tool call. For example, `list_operations` with
  `{"module":"tenants","kind":"Read"}` passes MCP string binding and returns
  a structured tool error with `argument` equal to `kind`. The two accepted
  values are `read` and `write`. A wrong JSON type fails earlier with
  JSON-RPC `InvalidParams`. `message` explains the missing or invalid value.
- The published `invalid_arguments.argument` values are `module`, `kind`,
  `operation`, `payload`, `tenant`, `aggregateId`, `correlationId`,
  `idempotencyKey`, `extensions`, `entityId`, `pageSize`, `offset`, `cursor`,
  `lint`, `url`, `token`, `actor`, `allowTenantOverride`, `profile`, `format`,
  `output`, `readOnly`, `strict`, `name`, `set`, `arguments`, `clear`,
  `transport`, and `extension`. CLI syntax errors can name a recognized option
  such as `extension`, or use `arguments` for general command syntax.
- `violations` is a non-empty array; each `path` is an RFC 6901 JSON Pointer and
  each `message` is a non-empty string.
- A call-kind mismatch uses `validation_failed` at `/operation`; a JSON null
  or non-object Command Payload uses `validation_failed` at `/`.
- For a Gateway client exception, copy its integer `StatusCode` to `status`.
  A malformed or semantically invalid HTTP-success response can therefore
  produce a 2xx error status. Use the first nonblank exception `Detail` or
  `Title` for `detail`, falling back to `Gateway request failed.` when both
  are blank. Use the first nonblank `ReasonCode`, `Code` or `Reason` for
  `reason`. Copy `retryable` when supplied, and the nonblank Gateway strings
  `clientAction` and `retryAfter` when supplied. Include an exception's
  `correlationId` only when it is a canonical ULID. Omit other absent optional
  values. Fixtures cover Gateway Problem Details, malformed HTTP 202 Command
  and HTTP 200 Query responses, semantic Query failure and missing metadata.

**Malformed message ID (Story 5.17, backlog).** The pinned EventStore client
5.4.0 returns a successful acknowledgment DTO without an HTTP status. For
a present empty, whitespace-only or noncanonical message ID in an otherwise
valid success acknowledgment, retain the actual status for this call at the
HTTP response boundary. Core must return `gateway_error` with that integer
`status`, the submitted `correlationId`, and stable `detail` explaining that
the Command may have succeeded. The CLI exits 2 and MCP sets `isError: true`
after exactly one submission. Test both HTTP 200 and 202, including a valid
echoed correlation ID different from the submitted one. The exception
mapping also covers unparseable JSON and a missing or blank acknowledgment
correlation ID.

`validation_failed`:

```json
{ "error": { "code": "validation_failed", "operation": "parties.reactivate-party", "violations": [ { "path": "/PartyId", "message": "must match the aggregate identifier pattern" } ] } }
```

`gateway_error`:

```json
{ "error": { "code": "gateway_error", "status": 409, "reason": "conflict", "detail": "The aggregate version has changed.", "retryable": false, "clientAction": "inspect", "correlationId": "01J9MZHXT3RKM0VWXRXGSJDATK" } }
```

`unknown_operation`:

```json
{ "error": { "code": "unknown_operation", "operation": "parties.reactvate-party", "suggestions": ["parties.reactivate-party"] } }
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

- **Projects.** Public `Hexalith.Projects.Contracts` 2.0.0 passes the dependency
  allowlist. Its four reads are `projects.list`, `projects.describe`,
  `projects.trace-conversation` and `projects.trace-attachments`. The enrolled
  list contract carries `pageSize` and `cursor` in the Payload. Generic paging
  arguments populate the Envelope (AD-20). Projects and EventStore must agree
  how these contracts apply before the native paging test. For Story 5.21,
  the Projects and environment owners supply a native host, identity roles and
  synthetic records. FR-20 defines the populated-page, detail and denial checks.
  Record the live verdict under DW-82. The CLI and plug-in retain separate
  migration gates. [Enrolled Contracts and reads](../../../../README.md#gateway-boundary)
- **Folders.** Epic 6 gates enrollment on published eligible Contracts and a
  server-free composition helper. The Folders inventory governs the agent-facing
  subset and the dry-run, redaction and freshness obligations. A separate K12
  decision covers restricted and mixed operations. The Folders owner must
  approve each replacement or withdrawal and its supporting evidence before
  legacy retirement. [Epic 6](../../epics.md#epic-6-replace-and-retire-the-folders-cli-and-mcp-server)
