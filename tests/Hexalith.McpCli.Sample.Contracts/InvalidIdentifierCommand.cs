using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Sample.Contracts;

/// <summary>Exercises rejection of a non-string aggregate identifier.</summary>
/// <param name="ItemId">The invalid source.</param>
[HexalithCommand("Invalid identifier command.", Domain = "sample", AggregateIdProperty = nameof(ItemId))]
public sealed record InvalidIdentifierCommand(int ItemId);
