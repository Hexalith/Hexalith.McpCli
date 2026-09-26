using Hexalith.McpCli.Abstractions;

[assembly: HexalithModule("invalid-fixture", "Invalid declarations beside one surviving duplicate.", IdentifierKind.Ulid,
    WireTypeConvention = WireTypeConvention.KebabCase)]

namespace Catalog.Invalid.Contracts;

/// <summary>Locates the invalid-declaration Contracts assembly.</summary>
public sealed class Module;
