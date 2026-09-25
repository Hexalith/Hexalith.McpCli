namespace Hexalith.McpCli.Core.Tests;

/// <summary>A nested item whose ordinary member shares the root envelope member's name.</summary>
public sealed class NestedTenantLine
{
    /// <summary>Gets or sets a required nested member named like the root tenant.</summary>
    public required string Tenant { get; init; }
}
