using Hexalith.McpCli.Abstractions;

namespace Catalog.Invalid.Contracts;

/// <summary>Exercises rejection of a collection whose elements are free-form.</summary>
/// <param name="ItemId">The aggregate source.</param>
/// <param name="Value">The collection of free-form elements.</param>
[HexalithCommand("Free-form element list command.", Domain = "invalid", AggregateIdProperty = nameof(ItemId))]
public sealed record ObjectListCommand(string ItemId, List<object> Value);
