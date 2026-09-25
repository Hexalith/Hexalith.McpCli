using System.Text.Json.Serialization;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Fills a getter-only collection in place through type-level populate handling.</summary>
[JsonObjectCreationHandling(JsonObjectCreationHandling.Populate)]
public sealed class PopulatedTypeCommand
{
    /// <summary>Gets the lines populated during deserialization.</summary>
    public List<string> Lines { get; } = [];
}
