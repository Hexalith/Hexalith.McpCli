using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Sample.Contracts;

/// <summary>Exercises rejection of two aggregate sources.</summary>
/// <param name="ItemId">The aggregate source.</param>
[HexalithQuery("Invalid dual source query.", Domain = "sample", AggregateIdProperty = nameof(ItemId), AggregateId = "sample-list")]
public sealed record DualAggregateQuery(string ItemId);
