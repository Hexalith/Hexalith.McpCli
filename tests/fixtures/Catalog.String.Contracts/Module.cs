using Hexalith.McpCli.Abstractions;

[assembly: HexalithModule("string-fixture", "String identifier fixture.", IdentifierKind.String,
    FixedTenant = "fixed-tenant", WireTypeConvention = WireTypeConvention.FullTypeName)]

namespace Catalog.String.Contracts;

/// <summary>Locates the String-identifier Contracts assembly.</summary>
public sealed class Module;
