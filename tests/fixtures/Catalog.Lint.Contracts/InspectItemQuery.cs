using System.ComponentModel;
using System.Text.Json.Serialization;
using Hexalith.McpCli.Abstractions;

namespace Catalog.Lint.Contracts;

/// <summary>Exercises description linting across nested and renamed input members.</summary>
/// <param name="ItemId">The declared aggregate identifier source.</param>
/// <param name="ExternalId">An identifier-like member without a marker.</param>
/// <param name="Nested">A nested input object.</param>
/// <param name="Entries">A collection of input objects.</param>
[HexalithQuery("Inspect one item and its nested values.", Domain = "lint-fixture", ProjectionType = "lint-items",
    AggregateIdProperty = nameof(ItemId), TenantProperty = nameof(Tenant))]
public sealed record InspectItemQuery(
    [property: Description("The item aggregate identifier.")] string ItemId,
    [property: Description("An external reference identifier.")] string ExternalId,
    [property: Description("The nested input value.")] NestedItem Nested,
    [property: Description("The collection of input entries.")] List<CollectionEntry> Entries)
{
    /// <summary>Gets a query paging size that belongs in the envelope.</summary>
    [Description("The requested page size.")]
    public int PageSize { get; init; }

    /// <summary>Gets a query paging offset that belongs in the envelope.</summary>
    [Description("The requested offset.")]
    public int Offset { get; init; }

    /// <summary>Gets a query paging cursor that belongs in the envelope.</summary>
    [Description("The requested cursor.")]
    public string? Cursor { get; init; }

    /// <summary>Gets entries by an arbitrary map key.</summary>
    [Description("The keyed input entries.")]
    public Dictionary<string, DictionaryValue> EntriesByKey { get; init; } = [];

    /// <summary>Gets the tenant filled from the envelope.</summary>
    public string? Tenant { get; init; }

    /// <summary>Gets an input with a renamed lower-case spelling.</summary>
    [JsonPropertyName("lowerCamel")]
    public string? Renamed { get; init; }

    /// <summary>Gets an ignored identifier-like member.</summary>
    [JsonIgnore]
    public string? IgnoredId { get; init; }

    /// <summary>Gets a computed identifier-like member.</summary>
    public string ComputedId => ItemId;
}
