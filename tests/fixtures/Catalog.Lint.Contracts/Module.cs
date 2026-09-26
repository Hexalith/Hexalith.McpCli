using Hexalith.McpCli.Abstractions;

[assembly: HexalithModule("lint-fixture", "Description quality fixtures.", IdentifierKind.Ulid,
    WireTypeConvention = WireTypeConvention.KebabCase)]

namespace Catalog.Lint.Contracts;

/// <summary>Locates the lint fixture Contracts assembly.</summary>
public sealed class Module;
