# Hexalith.McpCli

Hexalith.McpCli provides a shared MCP server and CLI for decorated Hexalith Contracts libraries.

Contracts authors reference `Hexalith.McpCli.Abstractions` and declare one module on the assembly. Place each operation type in its own file:

```csharp
// Module.cs
using Hexalith.McpCli.Abstractions;
[assembly: HexalithModule("inventory", "Manage inventory items.", IdentifierKind.Ulid,
    WireTypeConvention = WireTypeConvention.KebabCase)]
```

```csharp
// CreateItemCommand.cs
using System.ComponentModel;
using Hexalith.McpCli.Abstractions;

[HexalithCommand("Create an inventory item.", Domain = "inventory",
    AggregateIdProperty = nameof(ItemId))]
public sealed record CreateItemCommand(
    [property: HexalithIdentifier, Description("The item's ULID.")] string ItemId);
```

```csharp
// GetItemQuery.cs
using System.ComponentModel;
using Hexalith.McpCli.Abstractions;

[HexalithQuery("Read an inventory item.", Domain = "inventory",
    AggregateIdProperty = nameof(ItemId), ProjectionType = "inventory-items")]
public sealed record GetItemQuery(
    [property: HexalithIdentifier, Description("The item's ULID.")] string ItemId);
```

The module's identifier kind applies to `[HexalithIdentifier]` properties and aggregate identifier properties. Descriptions are required constructor arguments; routing values can instead come from the EventStore contract interfaces.

The `Hexalith.McpCli.Abstractions` package includes a build analyzer. Diagnostic `MCPCLI001` warns on a command or query type whose `[HexalithCommand]` or `[HexalithQuery]` description is empty, whitespace, or null. Supply a nonblank description to resolve it. The analyzer requires .NET SDK 10.0.4xx or later; an older SDK may report `CS9057` because its compiler cannot load the analyzer's Roslyn version. Contracts projects need only the Abstractions package reference.

## Gateway boundary

The CLI and MCP server share one catalog and executor. McpCli discovers operations only from flagged, referenced `*.Contracts` packages. It submits commands and queries to the EventStore gateway; the gateway routes them to the owning module server. McpCli never connects to a module server or references its implementation packages.

The requested Works, Timesheets, Agents, Conversations, Projects, and Folders packages are not enrolled yet. Their current Contracts assemblies lack declarations or live gateway paths required by the [integration spec](_bmad-output/implementation-artifacts/spec-add-six-domain-modules.md). Until decorated, verified packages are published and pinned, `hexalith modules` returns `catalog_empty`. This is a release readiness state, not a connection failure.

## CLI and MCP

Run the executable from source with `dotnet run --project src/Hexalith.McpCli --`, or use `hexalith` after installing the tool package. A gateway URL is required for execution, but discovery works offline.

```sh
hexalith modules
hexalith operations your-module --kind read
hexalith describe your-module.your-operation --lint
hexalith config profile add dev --url https://gateway.example
hexalith config set dev tenant acme
hexalith config set dev allowedExtensions task-id,trace-id
hexalith config use dev
hexalith config current
hexalith send your-module.your-command --payload @command.json --idempotency-key 01ARZ3NDEKTSV4RRFFQ69G5FAV
hexalith send your-module.your-command --payload @command.json --extension task-id=abc --extension trace-id=xyz
hexalith query your-module.your-query --payload @query.json --page-size 25
hexalith mcp --transport stdio
```

`--url`, `--token`, `--tenant`, `--actor`, `--allow-tenant-override`, `--profile`, `--format json|table`, `--output`, `--read-only`, and `--strict` are global options. Command and query payloads can be inline JSON, `@file`, or `-` for stdin. `--read-only` removes command submission from the MCP tool list and makes CLI `send` fail. The local profile file is `~/.eventstore/mcpcli.json`; token values are masked in `config` output. `config profile`, `config use`, and `config set` ignore `--profile` and `EVENTSTORE_PROFILE` and render their output using `--format`, then `EVENTSTORE_FORMAT`, then `json`, never the active profile's format.

Commands use `hexalith send MODULE.OPERATION --payload '{"ItemId":"..."}'`, `--payload @command.json`, or `cat command.json | hexalith send MODULE.OPERATION --payload -`. The payload follows the declared schema and supplies the aggregate identifier; an optional `--aggregate-id` must equal it. A successful send exits 0, makes one Gateway request, and returns `operation`, the Gateway `messageId` when provided (otherwise the submitted message ID), the submitted `correlationId`, resolved `tenant` and `aggregateId`, and `status: "accepted"`. Each call generates a new ULID message ID and uses it as correlation unless `--correlation-id` supplies one. `--correlation-id` and `--idempotency-key` must be canonical uppercase ULIDs; any other value, including lowercase ULID text, fails with `validation_failed` instead of being replaced. The tool never generates an idempotency key. When a command declares a non-nullable or serializer-required idempotency member, the caller must supply `--idempotency-key`, including when a required member is nullable. `describe` reports this requirement as `envelope.idempotencyKeyRequired: true`. A supplied key replaces any raw mapped payload value; without it, a raw non-null key is rejected and a raw null key is removed. The result includes `idempotencyKey` only when supplied and `result` only when returned by the Gateway. It never includes a `duplicate` field. Validation failures exit 2 and submit nothing. Gateway failures exit 2 with a `gateway_error` document. A timeout or other uncertain Gateway outcome may have reached the Gateway; `gateway_error` reasons `gateway-timeout` and `gateway-unreachable` are uncertain even when the detail says the Gateway could not be reached. Do not assume that submitting the command again is safe.

Queries use `hexalith query MODULE.OPERATION --payload '{"Key":"item-42"}'`, `--payload @query.json`, or `cat query.json | hexalith query MODULE.OPERATION --payload -`. The payload follows the operation's described schema and preserves its property casing. Aggregate selection uses `--aggregate-id`, then the declared payload accessor, then a query's declared constant. An explicit value must agree with a payload accessor, may override a constant, and is required when neither source exists. Validation completes before exactly one Gateway submission using the catalog's routing values.

The global CLI `--tenant` sets the session tenant; it is never a per-call override. A module's fixed tenant wins over that session value. A query requires a resolved tenant. MCP per-call tenants may replace a session tenant only when tenant override is enabled; matching values need no override, and a per-call value cannot conflict with a fixed tenant. When no session tenant is configured, an MCP per-call tenant is used as supplied, without the override gate. Commands take a declared payload tenant from the resolved tenant and a declared actor from the session only. If the caller includes either mapped member, it must be a JSON string exactly matching the trusted value. The executor fills omitted or matching members before submission and validates the rebuilt payload. A mapped correlation member is always replaced with the supplied `--correlation-id` or the generated message ID.

Commands and queries follow the module's declared ULID or String kind for aggregate identifiers. In ULID-kind modules, aggregate identifiers and marked payload identifiers must use canonical uppercase ULID text. Payload properties of CLR type `Ulid` must also use canonical uppercase text in any module, as must `Ulid` elements in nested collections and dictionaries. In String-kind modules, marked string-typed payload properties have no added ULID pattern or nonempty requirement; other schema rules may still constrain them. Aggregate identifiers also require 1–256 ASCII letters, digits, dots, underscores, or hyphens, starting and ending with a letter or digit. Tenant values require 1–64 lowercase ASCII letters, digits, or hyphens with the same start/end rule. A declared payload tenant member is filled from the resolved tenant; a conflicting or non-string caller value fails validation.

Queries accept `--entity-id` for an optional entity within the aggregate. Entity identifiers require 1–256 ASCII letters, digits, dots, underscores, or hyphens, starting and ending with a letter or digit. They follow this Gateway syntax even for ULID-kind modules.

Set a Profile's extension allowlist with `config set PROFILE allowedExtensions task-id,trace-id`, using comma-separated keys without spaces; `config set PROFILE allowedExtensions ''` clears the list. Supply values with repeatable `send --extension key=value` options or the MCP `send_command` tool's `extensions` object. Both heads use the same validation. Allowlist matching ignores case, but a call cannot contain two keys that differ only by case. Keys may contain ASCII letters, digits, dots, underscores, hyphens, and colons; each colon-separated segment must start and end with a letter or digit. Keys and values must pass the Gateway's injection checks, and values cannot contain `<`, `>`, `&`, `'`, or `"`. The reserved `actor:globalAdmin` key is rejected. A colon-delimited key also requires exactly one Gateway trusted-extension policy to claim and accept it for that authenticated caller and command. At most 32 entries are allowed, with keys up to 100 characters, values up to 1,000 characters, and 4,096 UTF-8 bytes combined. Both heads send approved keys and values unchanged; queries do not carry extensions.

`--page-size` accepts 1–200, `--offset` accepts 0–2,147,483,647, and `--cursor` accepts at most 4,096 UTF-16 code units. A nonblank cursor cannot be combined with an offset, including offset 0; empty or whitespace cursors are preserved. To request the next page when the projection uses cursor paging, pass the returned `paging.nextCursor` as `--cursor` without `--offset`. These options populate the query envelope's `Paging` with only the values supplied. Omitting all three omits envelope paging. Payload members named `PageSize`, `Offset`, or `Cursor` remain ordinary payload data, retain their lint warnings, and never supply or override envelope paging.

Query success exits 0 and always returns `operation`, `tenant`, and `document`, including `"document": null` when the Gateway returns no payload. `paging` appears only when returned by the Gateway; it includes `pageSize` and independently returned `offset`, `nextCursor`, `totalCount`, or `hasMore`. Unavailable metadata is omitted; returned zero counts/offsets and `hasMore: false` are preserved. Request paging never supplies result metadata. Queries carry no correlation identifier or extensions. Validation failures exit 2 without submitting to the Gateway.

`modules`, `operations <module>`, and `describe <operation>` browse the local Contracts catalog without making Gateway requests, even when a URL is configured. Modules and operations are listed in ordinal name order. `operations` includes both reads and writes by default; `--kind read` or `--kind write` filters the list. Read-only mode keeps writes visible. `describe` includes the payload schema, an example when declared, envelope requirements and arguments, and `lintFindings`. Without a URL it reports `submittable: false` and `reason: configuration_invalid`; a write in read-only mode reports `reason: read_only` first. `submittable` reflects only read-only mode and whether a URL is configured; it does not check the token, tenant, actor, or Gateway reachability. Module property casing is preserved in schemas and examples.

With `--format table`, modules use tab-separated `NAME`, `OPERATIONS`, `DESCRIPTION` columns, operations use `NAME`, `KIND`, `DESCRIPTION`, and configuration displays use `FIELD`, `VALUE`. `describe` stays JSON and emits one format note on stderr. It exits 0 even with lint findings unless `--lint` is supplied; with that flag, findings produce exit 1 without changing the document. Errors exit 2.

Catalog diagnostics go to stderr while ordinary discovery retains valid entries. `--strict` rejects any catalog diagnostic, including warnings, with `catalog_invalid` at exit 2 before checking for an empty catalog. Lint findings alone do not invalidate a strict catalog. A catalog with no valid operations returns `catalog_empty` at exit 2 when strict diagnostics have not already rejected it. `config` and `--version` bypass catalog construction.

`config profile add` stores only `--url`, `--token`, and `--format`, never environment values; it replaces the whole record when the profile already exists and refuses an explicit `--tenant`, `--actor`, or `--allow-tenant-override` without writing anything. After adding the profile, `config set` changes one of `tenant`, `actor`, `allowTenantOverride`, or `allowedExtensions` while keeping every other field.

The stdio MCP server exposes up to five generic tools: `list_modules`, `list_operations`, `describe_operation`, `send_command`, and `run_query`. Its protocol output uses stdout and diagnostics use stderr. The HTTP MCP transport is reserved for a later release.
