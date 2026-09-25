using System.Text.Json;
using System.Text.Json.Serialization;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Accepts arbitrary nested extension data.</summary>
public sealed class NestedExtensionValue
{
    /// <summary>Gets or sets arbitrary extension fields.</summary>
    [JsonExtensionData]
    public Dictionary<string, JsonElement>? Extras { get; init; }
}
