using System.Text.Json;
using System.Text.Json.Serialization;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Accepts arbitrary extension data through a get-only dictionary.</summary>
public sealed class GetOnlyExtensionDataCommand
{
    /// <summary>Gets arbitrary extension fields.</summary>
    [JsonExtensionData]
    public Dictionary<string, JsonElement> Extras { get; } = [];
}
