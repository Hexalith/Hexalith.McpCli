using System.Text.Json.Serialization;

namespace Hexalith.McpCli.Core.Catalog;

/// <summary>Describes envelope arguments available to an operation.</summary>
/// <param name="FixedTenant">The module tenant, when fixed.</param>
/// <param name="AggregateIdRequired">Whether the caller must supply an aggregate identifier.</param>
/// <param name="IdempotencyKeyRequired">Whether the caller must supply an idempotency key.</param>
/// <param name="Arguments">The applicable envelope argument names.</param>
public sealed record OperationEnvelopeDocument(
    [property: JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)] string? FixedTenant,
    bool AggregateIdRequired,
    bool IdempotencyKeyRequired,
    IReadOnlyList<string> Arguments);
