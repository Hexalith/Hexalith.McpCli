namespace Hexalith.McpCli.Core.Settings;

/// <summary>Version-one connection and operator settings stored for one named profile.</summary>
/// <param name="Url">The optional gateway URL.</param>
/// <param name="Token">The optional bearer token.</param>
/// <param name="Format">The optional CLI output format.</param>
/// <param name="Tenant">The optional session tenant.</param>
/// <param name="Actor">The optional trusted operator actor.</param>
/// <param name="AllowTenantOverride">Whether per-call MCP tenant selection is allowed.</param>
/// <param name="AllowedExtensions">The allowed command extension keys.</param>
public sealed record ConnectionProfile(
    string? Url = null,
    string? Token = null,
    string? Format = null,
    string? Tenant = null,
    string? Actor = null,
    bool? AllowTenantOverride = null,
    IReadOnlyList<string>? AllowedExtensions = null)
{
    /// <summary>Formats the profile without exposing the bearer token.</summary>
    /// <returns>A redacted diagnostic representation.</returns>
    public override string ToString()
        => $"{nameof(ConnectionProfile)} {{ Url = {Url}, Token = {ProfileStore.MaskToken(Token)}, Format = {Format}, "
            + $"Tenant = {Tenant}, Actor = {Actor}, AllowTenantOverride = {AllowTenantOverride} }}";
}
