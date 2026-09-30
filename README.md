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
hexalith config use dev
hexalith config current
hexalith send your-module.your-command --payload @command.json --idempotency-key 01ARZ3NDEKTSV4RRFFQ69G5FAV
hexalith query your-module.your-query --payload @query.json --page-size 25
hexalith mcp --transport stdio
```

`--url`, `--token`, `--tenant`, `--actor`, `--allow-tenant-override`, `--profile`, `--format json|table`, `--output`, `--read-only`, and `--strict` are global options. Command payloads can be inline JSON, `@file`, or `-` for stdin. `--read-only` removes command submission from the MCP tool list and rejects CLI writes. The local profile file is `~/.eventstore/mcpcli.json`; token values are masked in `config` output. `config profile`, `config use`, and `config set` ignore `--profile` and `EVENTSTORE_PROFILE` and render their output using `--format`, then `EVENTSTORE_FORMAT`, then `json`, never the active profile's format.

`config profile add` replaces the whole record when the profile already exists and refuses an explicit `--tenant`, `--actor`, or `--allow-tenant-override` without writing anything. After adding the profile, `config set` changes one of `tenant`, `actor`, `allowTenantOverride`, or `allowedExtensions` while keeping every other field.

The stdio MCP server exposes up to five generic tools: `list_modules`, `list_operations`, `describe_operation`, `send_command`, and `run_query`. Its protocol output uses stdout and diagnostics use stderr. The HTTP MCP transport is reserved for a later release.
