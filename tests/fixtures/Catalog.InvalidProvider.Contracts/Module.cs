using Hexalith.McpCli.Abstractions;

[assembly: HexalithModule("invalid-provider", "Invalid provider fixture.", IdentifierKind.String,
    SerializerOptionsProvider = typeof(Catalog.InvalidProvider.Contracts.Module))]

namespace Catalog.InvalidProvider.Contracts;

/// <summary>Intentionally does not expose serializer options.</summary>
public sealed class Module;
