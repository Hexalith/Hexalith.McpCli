using Hexalith.McpCli.Abstractions;

namespace Catalog.Invalid.Contracts;

/// <summary>Exercises rejection of the tenant and actor roles owning one member.</summary>
/// <param name="ItemId">The aggregate source.</param>
/// <param name="Operator">The member both envelope roles claim.</param>
[HexalithCommand("Tenant and actor aliasing command.", Domain = "invalid", AggregateIdProperty = nameof(ItemId),
    TenantProperty = nameof(Operator), ActorProperty = nameof(Operator))]
public sealed record ActorTenantCommand(string ItemId, string Operator);
