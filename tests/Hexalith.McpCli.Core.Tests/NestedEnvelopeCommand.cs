namespace Hexalith.McpCli.Core.Tests;

/// <summary>Maps a root tenant role while nested items reuse the same member name.</summary>
public sealed class NestedEnvelopeCommand
{
    /// <summary>Gets or sets the envelope tenant.</summary>
    public required string Tenant { get; init; }

    /// <summary>Gets or sets nested lines.</summary>
    public List<NestedTenantLine> Lines { get; init; } = [];

    /// <summary>Gets or sets nested lines by key.</summary>
    public Dictionary<string, NestedTenantLine> ByKey { get; init; } = [];
}
