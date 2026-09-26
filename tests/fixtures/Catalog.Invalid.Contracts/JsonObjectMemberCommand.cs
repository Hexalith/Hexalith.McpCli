using System.Text.Json.Nodes;
using Hexalith.McpCli.Abstractions;

namespace Catalog.Invalid.Contracts;

/// <summary>Exercises rejection of a JSON object node member, which the exporter describes only as an open object.</summary>
/// <param name="ItemId">The aggregate source.</param>
/// <param name="Value">The free-form member.</param>
[HexalithCommand("JSON object member command.", Domain = "invalid", AggregateIdProperty = nameof(ItemId))]
public sealed record JsonObjectMemberCommand(string ItemId, JsonObject? Value);
