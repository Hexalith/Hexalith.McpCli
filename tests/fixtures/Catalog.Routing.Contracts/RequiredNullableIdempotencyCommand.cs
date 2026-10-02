using System.Text.Json.Serialization;
using Hexalith.McpCli.Abstractions;

namespace Catalog.Routing.Contracts;

/// <summary>Exercises a serializer-required nullable idempotency member.</summary>
/// <param name="ItemId">The aggregate identifier.</param>
/// <param name="Idempotency">The required but nullable idempotency member.</param>
[HexalithCommand("Command with a required nullable idempotency member.", Domain = "routing",
    AggregateIdProperty = nameof(ItemId), IdempotencyKeyProperty = nameof(Idempotency))]
public sealed record RequiredNullableIdempotencyCommand(
    [property: HexalithIdentifier] string ItemId,
    [property: JsonRequired] string? Idempotency);
