namespace Catalog.Invalid.Contracts;

/// <summary>Declares the base member that <see cref="HiddenRoleCommand"/> hides.</summary>
public abstract class HiddenRoleBase
{
    /// <summary>Gets or sets the hidden tenant member.</summary>
    public string Tenant { get; set; } = string.Empty;
}
