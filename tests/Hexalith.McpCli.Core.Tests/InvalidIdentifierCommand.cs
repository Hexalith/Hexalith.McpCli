using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>A declaration whose marked identifier is not a JSON string.</summary>
public sealed class InvalidIdentifierCommand
{
    /// <summary>Gets or sets the invalid numeric identifier.</summary>
    [HexalithIdentifier]
    public int ItemId { get; init; }
}
