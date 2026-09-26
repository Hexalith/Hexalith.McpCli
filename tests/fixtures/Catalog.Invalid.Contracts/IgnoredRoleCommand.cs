using System.Text.Json.Serialization;
using Hexalith.McpCli.Abstractions;

namespace Catalog.Invalid.Contracts;

/// <summary>Exercises rejection of a role that names a member excluded from serialization.</summary>
[HexalithCommand("Ignored role member command.", Domain = "invalid", AggregateIdProperty = nameof(ItemId), TenantProperty = nameof(Tenant))]
public sealed class IgnoredRoleCommand
{
    /// <summary>Gets or sets the aggregate identifier.</summary>
    public string ItemId { get; set; } = string.Empty;

    /// <summary>Gets or sets a tenant member that is never serialized.</summary>
    [JsonIgnore]
    public string Tenant { get; set; } = string.Empty;
}
