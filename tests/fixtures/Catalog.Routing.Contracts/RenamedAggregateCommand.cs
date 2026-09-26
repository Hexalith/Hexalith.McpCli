using System.Text.Json.Serialization;
using Hexalith.McpCli.Abstractions;

namespace Catalog.Routing.Contracts;

/// <summary>Exercises an aggregate accessor bound to a renamed serialized property.</summary>
/// <param name="ItemId">The aggregate identifier.</param>
[HexalithCommand("Read a renamed aggregate property.", Domain = "routing", AggregateIdProperty = nameof(ItemId))]
public sealed record RenamedAggregateCommand([property: JsonPropertyName("aggregate/~id")] string ItemId);
