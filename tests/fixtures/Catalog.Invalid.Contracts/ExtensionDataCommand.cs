using System.Text.Json;
using System.Text.Json.Serialization;
using Hexalith.McpCli.Abstractions;

namespace Catalog.Invalid.Contracts;

/// <summary>Exercises rejection of a payload that cannot have a closed Schema.</summary>
[HexalithCommand("Extension data command.", Domain = "invalid", AggregateIdProperty = nameof(ItemId))]
public sealed class ExtensionDataCommand
{
    /// <summary>Gets the aggregate identifier.</summary>
    [HexalithIdentifier]
    public string ItemId { get; init; } = string.Empty;

    /// <summary>Gets unmapped members, which a closed Schema cannot describe.</summary>
    [JsonExtensionData]
    public Dictionary<string, JsonElement>? Extras { get; init; }
}
