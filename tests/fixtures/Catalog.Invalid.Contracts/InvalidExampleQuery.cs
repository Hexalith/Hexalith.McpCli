using Hexalith.McpCli.Abstractions;

namespace Catalog.Invalid.Contracts;

/// <summary>Exercises rejection of a failing example.</summary>
/// <param name="ItemId">The aggregate source.</param>
[HexalithQuery("Invalid example query.", Domain = "invalid", ProjectionType = "invalid-items", AggregateIdProperty = nameof(ItemId),
    Example = "{\"ItemId\":15}")]
public sealed record InvalidExampleQuery([property: HexalithIdentifier] string ItemId);
