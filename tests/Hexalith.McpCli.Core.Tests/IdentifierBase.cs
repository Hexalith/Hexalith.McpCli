using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Declares an identifier on an overridable property.</summary>
public abstract class IdentifierBase
{
    /// <summary>Gets or sets the declared identifier.</summary>
    [HexalithIdentifier]
    public abstract string Key { get; init; }
}
