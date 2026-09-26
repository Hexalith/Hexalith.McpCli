using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Sample.Contracts;

/// <summary>Exercises rejection of a failing example.</summary>
/// <param name="ItemId">The aggregate source.</param>
[HexalithQuery("Invalid example query.", Domain = "sample", ProjectionType = "sample-items", AggregateIdProperty = nameof(ItemId),
    Example = "{\"ItemId\":15}")]
public sealed record InvalidExampleQuery([property: HexalithIdentifier] SampleItemId ItemId);
