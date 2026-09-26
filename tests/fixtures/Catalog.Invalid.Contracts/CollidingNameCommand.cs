using System.Text.Json.Serialization;
using Hexalith.McpCli.Abstractions;

namespace Catalog.Invalid.Contracts;

/// <summary>Exercises a System.Text.Json contract error: two members serialize under one name.</summary>
[HexalithCommand("Colliding serialized names command.", Domain = "invalid", AggregateIdProperty = nameof(ItemId))]
public sealed class CollidingNameCommand
{
    /// <summary>Gets or sets the aggregate identifier.</summary>
    public string ItemId { get; set; } = string.Empty;

    /// <summary>Gets or sets a member renamed onto its sibling's name.</summary>
    [JsonPropertyName("Title")]
    public string Caption { get; set; } = string.Empty;

    /// <summary>Gets or sets the sibling member.</summary>
    public string Title { get; set; } = string.Empty;
}
