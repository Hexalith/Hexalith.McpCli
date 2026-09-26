using System.Text.Json.Nodes;
using Hexalith.McpCli.Abstractions;

namespace Catalog.Invalid.Contracts;

/// <summary>Exercises rejection of a JSON node member.</summary>
/// <param name="ItemId">The aggregate source.</param>
/// <param name="Value">The free-form member.</param>
[HexalithCommand("Free-form node command.", Domain = "invalid", AggregateIdProperty = nameof(ItemId))]
public sealed record FreeFormNodeCommand(string ItemId, JsonNode? Value);
