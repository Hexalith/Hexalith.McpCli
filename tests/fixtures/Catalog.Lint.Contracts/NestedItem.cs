using System.ComponentModel;
using System.Text.Json.Serialization;

namespace Catalog.Lint.Contracts;

/// <summary>Provides constructor-bound nested members.</summary>
/// <param name="Label">A nested label described on its constructor parameter.</param>
/// <param name="Escaped">An undescribed renamed member.</param>
public sealed record NestedItem(
    [param: Description("The label supplied for the nested item.")] string Label,
    [property: JsonPropertyName("nested/~")] string Escaped)
{
    /// <summary>A serialized identifier-like field with a declared description.</summary>
    [JsonInclude]
    [JsonPropertyName("external/~id")]
    [Description("The external identifier of the nested item.")]
    public string? ExternalId;

    /// <summary>A serialized paging field without a declared description.</summary>
    [JsonInclude]
    [JsonPropertyName("page/~size")]
    public int PageSize;
}
