using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Has a marked identifier whose provider converter emits a number.</summary>
public sealed class ConvertedNumericIdentifierCommand
{
    /// <summary>Gets or sets the invalid converted identifier.</summary>
    [HexalithIdentifier]
    public required NumericIdentifier ItemId { get; init; }
}
