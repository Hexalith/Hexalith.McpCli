using System.Text.Json.Serialization;
using Hexalith.McpCli.Abstractions;

namespace Catalog.Invalid.Contracts;

/// <summary>Exercises rejection of an envelope role bound to a converter-opaque member.</summary>
[HexalithCommand("Opaque role member command.", Domain = "invalid", AggregateIdProperty = nameof(ItemId), TenantProperty = nameof(Tenant))]
public sealed class OpaqueRoleCommand
{
    /// <summary>Gets or sets the aggregate identifier.</summary>
    public string ItemId { get; set; } = string.Empty;

    /// <summary>Gets or sets a tenant member serialized by a custom converter.</summary>
    [JsonConverter(typeof(OpaqueStringConverter))]
    public string Tenant { get; set; } = string.Empty;
}
