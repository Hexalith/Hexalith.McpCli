using System.Text.Json.Serialization;

namespace Hexalith.McpCli.Core.Execution;

/// <summary>Returned gateway paging metadata.</summary>
/// <param name="PageSize">The effective positive page size.</param>
/// <param name="Offset">The returned offset, when present.</param>
/// <param name="NextCursor">The returned next cursor, when present.</param>
/// <param name="TotalCount">The returned total count, when present.</param>
/// <param name="HasMore">Whether a next page exists, when known.</param>
public sealed record QueryPagingDocument(
    int PageSize,
    [property: JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)] int? Offset = null,
    [property: JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)] string? NextCursor = null,
    [property: JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)] long? TotalCount = null,
    [property: JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)] bool? HasMore = null);
