using System.ComponentModel;
using System.Text.Json.Serialization;

namespace Catalog.Lint.Contracts;

/// <summary>Provides constructor-bound nested members.</summary>
/// <param name="Label">An undescribed nested label.</param>
/// <param name="Escaped">An undescribed renamed member.</param>
public sealed record NestedItem(
    string Label,
    [property: JsonPropertyName("nested/~")] string Escaped)
{
    /// <summary>A serialized identifier-like field with a declared description.</summary>
    [JsonInclude]
    [Description("The external identifier of the nested item.")]
    public string? ExternalId;

    /// <summary>A serialized paging field without a declared description.</summary>
    [JsonInclude]
    public int PageSize;
}
