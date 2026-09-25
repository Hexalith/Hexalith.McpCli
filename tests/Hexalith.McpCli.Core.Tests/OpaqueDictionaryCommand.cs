using Hexalith.McpCli.Sample.Contracts;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Holds converter-backed dictionary values whose schema is unknown.</summary>
public sealed class OpaqueDictionaryCommand
{
    /// <summary>Gets or sets opaque values by name.</summary>
    public Dictionary<string, SampleItemId> Items { get; init; } = [];
}
