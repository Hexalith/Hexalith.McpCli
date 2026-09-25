using ByteAether.Ulid;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Offers members of different CLR types for envelope-role type checks.</summary>
public sealed class EnvelopeTypedCommand
{
    /// <summary>Gets or sets an ordinary title.</summary>
    public required string Title { get; init; }

    /// <summary>Gets or sets a numeric value that no envelope role accepts.</summary>
    public int Count { get; init; }

    /// <summary>Gets or sets a CLR ULID accepted only by correlation and idempotency roles.</summary>
    public Ulid Key { get; init; }

    /// <summary>Gets or sets a nullable CLR ULID accepted only by correlation and idempotency roles.</summary>
    public Ulid? OptionalKey { get; init; }
}
