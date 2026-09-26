using System.Text.Json;
using Hexalith.McpCli.Abstractions;

namespace Catalog.Invalid.Contracts;

/// <summary>Exercises rejection of a raw JSON element member.</summary>
/// <param name="ItemId">The aggregate source.</param>
/// <param name="Value">The free-form member.</param>
[HexalithCommand("Free-form element command.", Domain = "invalid", AggregateIdProperty = nameof(ItemId))]
public sealed record FreeFormElementCommand(string ItemId, JsonElement Value);
