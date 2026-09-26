using System.Text.Json.Serialization;
using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Sample.Contracts;

/// <summary>Exercises mapped envelope roles and serialized pointer escaping.</summary>
/// <param name="ItemId">The aggregate source.</param>
/// <param name="Tenant">The envelope tenant.</param>
/// <param name="Correlation">The correlation identifier.</param>
/// <param name="Idempotency">The required idempotency identifier.</param>
/// <param name="Actor">The operator actor.</param>
[HexalithCommand("Change an item using mapped envelope values.", Domain = "sample", AggregateIdProperty = nameof(ItemId),
    TenantProperty = nameof(Tenant), CorrelationProperty = nameof(Correlation),
    IdempotencyKeyProperty = nameof(Idempotency), ActorProperty = nameof(Actor),
    Example = "{\"ItemId\":\"01ARZ3NDEKTSV4RRFFQ69G5FAV\"}")]
public sealed record EnvelopeItemCommand(
    SampleItemId ItemId,
    [property: JsonPropertyName("tenant/~")] string Tenant,
    string Correlation,
    string Idempotency,
    string Actor);
