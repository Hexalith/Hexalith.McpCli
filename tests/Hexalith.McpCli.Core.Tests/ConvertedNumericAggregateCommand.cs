namespace Hexalith.McpCli.Core.Tests;

/// <summary>Has an aggregate-mapped identifier whose provider converter emits a number.</summary>
public sealed class ConvertedNumericAggregateCommand
{
    /// <summary>Gets or sets the invalid aggregate source.</summary>
    public required NumericIdentifier Source { get; init; }
}
