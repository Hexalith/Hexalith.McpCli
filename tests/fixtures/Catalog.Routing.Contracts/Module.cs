using Hexalith.McpCli.Abstractions;

[assembly: HexalithModule("routing-fixture", "Valid routing, aggregate source, and envelope variants.", IdentifierKind.Ulid,
    WireTypeConvention = WireTypeConvention.KebabCase)]

namespace Catalog.Routing.Contracts;

/// <summary>Locates the routing-variant Contracts assembly.</summary>
public sealed class Module;
