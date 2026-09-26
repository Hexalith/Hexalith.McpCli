using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>A valid query declaration whose serialization contract raises a non-coded exception during operation resolution.</summary>
[HexalithQuery("Faulting query.", Domain = "faulting", WireType = "faulting", ProjectionType = "faulting-items")]
public sealed class FaultingQuery
{
    /// <summary>Gets or sets a member whose converter creation faults.</summary>
    [FaultingConverter]
    public string? Value { get; set; }
}
