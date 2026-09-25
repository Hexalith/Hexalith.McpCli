namespace Hexalith.McpCli.Core.Tests;

/// <summary>Has an unmarked aggregate source declared by the operation.</summary>
public sealed class AggregateOnlyCommand
{
    /// <summary>Gets or sets the declared aggregate source.</summary>
    public required string Source { get; init; }

    /// <summary>Gets or sets an unmarked identifier-like number.</summary>
    public int OtherId { get; init; }
}
