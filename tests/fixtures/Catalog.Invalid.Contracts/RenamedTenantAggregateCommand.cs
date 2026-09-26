using System.Text.Json.Serialization;
using Hexalith.McpCli.Abstractions;

namespace Catalog.Invalid.Contracts;

/// <summary>Exercises the tenant and aggregate roles owning one renamed serialized member.</summary>
/// <param name="TenantId">The renamed member both roles claim.</param>
[HexalithCommand("Tenant as aggregate command.", Domain = "invalid", AggregateIdProperty = nameof(TenantId),
    TenantProperty = nameof(TenantId))]
public sealed record RenamedTenantAggregateCommand([property: JsonPropertyName("tenant-key")] string TenantId);
