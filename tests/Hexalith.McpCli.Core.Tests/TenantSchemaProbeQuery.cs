using System.Text.Json.Serialization;
using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Separates aggregate routing from a tenant member with a deliberately stricter schema.</summary>
[HexalithQuery("Probe tenant filling and final schema validation.", Domain = "query-validation",
    WireType = "tenant-schema-probe", ProjectionType = "probe-items",
    AggregateIdProperty = nameof(ItemId), TenantProperty = nameof(Tenant))]
public sealed record TenantSchemaProbeQuery
{
    /// <summary>Gets the independent aggregate identifier.</summary>
    public required string ItemId { get; init; }

    /// <summary>Gets the envelope-owned tenant whose identifier marker requires a ULID.</summary>
    [HexalithIdentifier]
    [JsonPropertyName("tenant/~")]
    public string? Tenant { get; init; }
}
