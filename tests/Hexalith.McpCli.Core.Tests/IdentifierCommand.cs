using ByteAether.Ulid;
using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Separates declared identifiers from merely similar property names.</summary>
public sealed class IdentifierCommand
{
    /// <summary>Gets or sets the declared aggregate identifier.</summary>
    [HexalithIdentifier]
    public required string ItemKey { get; init; }

    /// <summary>Gets or sets a separate CLR ULID.</summary>
    public Ulid Tracking { get; init; }

    /// <summary>Gets or sets an unmarked identifier-like integer.</summary>
    public int ExternalId { get; init; }
}
