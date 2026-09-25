using Hexalith.McpCli.Sample.Contracts;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Holds converter-backed values whose element schema is unknown.</summary>
public sealed class OpaqueCollectionCommand
{
    /// <summary>Gets or sets a list of opaque values.</summary>
    public List<SampleItemId> Items { get; init; } = [];
}
