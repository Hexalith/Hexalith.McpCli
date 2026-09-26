using Hexalith.McpCli.Abstractions;

namespace Catalog.Invalid.Contracts;

/// <summary>Exercises rejection of a missing declared role.</summary>
/// <param name="ItemId">The aggregate source.</param>
[HexalithCommand("Invalid role command.", Domain = "invalid", AggregateIdProperty = nameof(ItemId), TenantProperty = "Missing")]
public sealed record InvalidRoleCommand(string ItemId);
