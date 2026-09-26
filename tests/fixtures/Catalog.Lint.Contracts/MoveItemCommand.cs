using System.ComponentModel;
using Hexalith.McpCli.Abstractions;

namespace Catalog.Lint.Contracts;

/// <summary>Exercises command-specific description and paging lint rules.</summary>
/// <param name="ItemId">The aggregate identifier source.</param>
/// <param name="TenantId">The tenant supplied by the envelope.</param>
/// <param name="PageSize">An ordinary command payload member.</param>
/// <param name="Offset">Another ordinary command payload member.</param>
[HexalithCommand(" move item ", Domain = "lint-fixture", AggregateIdProperty = nameof(ItemId),
    TenantProperty = nameof(TenantId))]
public sealed record MoveItemCommand(
    [property: Description("The item aggregate identifier.")] string ItemId,
    [property: Description("The tenant supplied by the envelope.")] string TenantId,
    [property: Description("The size of the requested move.")] int PageSize,
    [property: Description("The starting position of the move.")] int Offset);
