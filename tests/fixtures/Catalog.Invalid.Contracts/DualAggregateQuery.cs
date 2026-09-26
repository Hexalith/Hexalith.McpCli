using Hexalith.McpCli.Abstractions;

namespace Catalog.Invalid.Contracts;

/// <summary>Exercises rejection of two aggregate sources.</summary>
/// <param name="ItemId">The aggregate source.</param>
[HexalithQuery("Invalid dual source query.", Domain = "invalid", AggregateIdProperty = nameof(ItemId), AggregateId = "invalid-list")]
public sealed record DualAggregateQuery(string ItemId);
