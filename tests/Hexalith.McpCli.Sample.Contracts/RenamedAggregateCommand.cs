using System.Text.Json.Serialization;
using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Sample.Contracts;

/// <summary>Exercises an aggregate accessor bound to a renamed serialized property.</summary>
/// <param name="ItemId">The aggregate identifier.</param>
[HexalithCommand("Read a renamed aggregate property.", Domain = "sample", AggregateIdProperty = nameof(ItemId))]
public sealed record RenamedAggregateCommand([property: JsonPropertyName("aggregate/~id")] string ItemId);
