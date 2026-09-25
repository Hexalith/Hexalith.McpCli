using System.Text.Json;
using System.Text.Json.Serialization;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Accepts arbitrary top-level extension data.</summary>
public sealed class ExtensionDataCommand
{
    /// <summary>Gets or sets arbitrary extension fields.</summary>
    [JsonExtensionData]
    public Dictionary<string, JsonElement>? Extras { get; init; }
}
