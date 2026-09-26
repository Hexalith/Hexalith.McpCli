using Hexalith.McpCli.Abstractions;

namespace Catalog.Invalid.Contracts;

/// <summary>Exercises rejection of an untyped object member.</summary>
/// <param name="ItemId">The aggregate source.</param>
/// <param name="Value">The free-form member.</param>
[HexalithCommand("Free-form object command.", Domain = "invalid", AggregateIdProperty = nameof(ItemId))]
public sealed record FreeFormObjectCommand(string ItemId, object? Value);
