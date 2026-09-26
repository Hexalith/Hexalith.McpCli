using Hexalith.McpCli.Abstractions;

namespace Catalog.Invalid.Contracts;

/// <summary>Exercises rejection of the correlation role owning the aggregate member.</summary>
/// <param name="ItemId">The member both roles claim.</param>
[HexalithCommand("Correlation and aggregate aliasing command.", Domain = "invalid", AggregateIdProperty = nameof(ItemId),
    CorrelationProperty = nameof(ItemId))]
public sealed record CorrelationAggregateCommand(string ItemId);
