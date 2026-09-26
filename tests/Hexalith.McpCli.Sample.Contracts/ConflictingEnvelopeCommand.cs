using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Sample.Contracts;

/// <summary>Exercises rejection of two envelope roles owning one member.</summary>
/// <param name="ItemId">The aggregate source.</param>
/// <param name="EnvelopeValue">The conflicting envelope member.</param>
[HexalithCommand("Invalid envelope ownership command.", Domain = "sample", AggregateIdProperty = nameof(ItemId),
    CorrelationProperty = nameof(EnvelopeValue), IdempotencyKeyProperty = nameof(EnvelopeValue))]
public sealed record ConflictingEnvelopeCommand(string ItemId, string EnvelopeValue);
