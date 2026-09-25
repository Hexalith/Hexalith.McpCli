using System.Text.Json.Serialization;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Fills a getter-only collection in place through property-level populate handling.</summary>
public sealed class PopulatedCollectionCommand
{
    /// <summary>Gets the tags populated during deserialization.</summary>
    [JsonObjectCreationHandling(JsonObjectCreationHandling.Populate)]
    public List<string> Tags { get; } = [];
}
