using Hexalith.McpCli.Abstractions;

[assembly: HexalithModule("marked-empty", "Module with no operations.", IdentifierKind.String)]

namespace Manifest.MarkedEmpty.Contracts;

/// <summary>
/// Provides a type for locating the marked, operation-free assembly in tests.
/// </summary>
public sealed class Module
{
}
