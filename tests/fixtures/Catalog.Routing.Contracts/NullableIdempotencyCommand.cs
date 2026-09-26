using Hexalith.McpCli.Abstractions;

namespace Catalog.Routing.Contracts;

/// <summary>Exercises an optional idempotency key member.</summary>
/// <param name="ItemId">The aggregate identifier.</param>
/// <param name="Idempotency">The optional idempotency identifier.</param>
[HexalithCommand("Command with an optional idempotency key.", Domain = "routing", AggregateIdProperty = nameof(ItemId),
    IdempotencyKeyProperty = nameof(Idempotency))]
public sealed record NullableIdempotencyCommand([property: HexalithIdentifier] string ItemId, string? Idempotency = null);
