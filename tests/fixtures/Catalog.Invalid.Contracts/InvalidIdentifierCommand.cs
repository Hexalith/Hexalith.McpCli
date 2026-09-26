using Hexalith.McpCli.Abstractions;

namespace Catalog.Invalid.Contracts;

/// <summary>Exercises rejection of a non-string aggregate identifier.</summary>
/// <param name="ItemId">The invalid source.</param>
[HexalithCommand("Invalid identifier command.", Domain = "invalid", AggregateIdProperty = nameof(ItemId))]
public sealed record InvalidIdentifierCommand(int ItemId);
