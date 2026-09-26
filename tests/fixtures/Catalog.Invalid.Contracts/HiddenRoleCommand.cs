using Hexalith.McpCli.Abstractions;

namespace Catalog.Invalid.Contracts;

/// <summary>Exercises rejection of a role whose name matches a hiding member and the member it hides.</summary>
[HexalithCommand("Hidden role member command.", Domain = "invalid", AggregateIdProperty = nameof(ItemId), TenantProperty = nameof(Tenant))]
public sealed class HiddenRoleCommand : HiddenRoleBase
{
    /// <summary>Gets or sets the aggregate identifier.</summary>
    public string ItemId { get; set; } = string.Empty;

    /// <summary>Gets or sets a member that hides the base tenant with another type.</summary>
    public new int Tenant { get; set; }
}
