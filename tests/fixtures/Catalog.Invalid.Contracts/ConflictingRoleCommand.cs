using Hexalith.McpCli.Abstractions;

namespace Catalog.Invalid.Contracts;

/// <summary>Exercises rejection of conflicting ownership of one member.</summary>
/// <param name="ItemId">The conflicting source.</param>
[HexalithCommand("Invalid role ownership command.", Domain = "invalid", AggregateIdProperty = nameof(ItemId), TenantProperty = nameof(ItemId))]
public sealed record ConflictingRoleCommand(string ItemId);
