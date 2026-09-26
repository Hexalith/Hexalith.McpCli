using System.Text.Json.Nodes;
using Hexalith.McpCli.Abstractions;

namespace Catalog.Invalid.Contracts;

/// <summary>Exercises rejection of a JSON array node member, which the exporter describes only as an open array.</summary>
/// <param name="ItemId">The aggregate source.</param>
/// <param name="Value">The free-form member.</param>
[HexalithCommand("JSON array member command.", Domain = "invalid", AggregateIdProperty = nameof(ItemId))]
public sealed record JsonArrayMemberCommand(string ItemId, JsonArray? Value);
