using System.Text.Json.Serialization;

namespace Hexalith.McpCli.Core.Settings;

/// <summary>The immutable settings used by Core and both heads for one process.</summary>
/// <param name="Url">The validated gateway URL, when configured.</param>
/// <param name="Token">The bearer token, when configured.</param>
/// <param name="Tenant">The session tenant.</param>
/// <param name="Actor">The trusted operator actor.</param>
/// <param name="AllowTenantOverride">Whether per-call MCP tenant selection is allowed.</param>
/// <param name="AllowedExtensions">The immutable extension allowlist.</param>
/// <param name="Format">The output format.</param>
/// <param name="Output">The optional output path.</param>
/// <param name="ReadOnly">Whether writes are disabled.</param>
/// <param name="Strict">Whether Catalog diagnostics are fatal.</param>
/// <param name="Profile">The selected profile name.</param>
/// <param name="Sources">The source of every resolved setting.</param>
public sealed record ResolvedSettings(
    Uri? Url,
    [property: JsonIgnore] string? Token,
    string? Tenant,
    string? Actor,
    bool AllowTenantOverride,
    IReadOnlySet<string> AllowedExtensions,
    string Format,
    string? Output,
    bool ReadOnly,
    bool Strict,
    string? Profile,
    IReadOnlyDictionary<string, string> Sources)
{
    /// <summary>Formats the settings without exposing the bearer token.</summary>
    /// <returns>A redacted diagnostic representation.</returns>
    public override string ToString()
        => $"{nameof(ResolvedSettings)} {{ Url = {Url}, Token = {ProfileStore.MaskToken(Token)}, "
            + $"Tenant = {Tenant}, Actor = {Actor}, AllowTenantOverride = {AllowTenantOverride}, "
            + $"Format = {Format}, Output = {Output}, ReadOnly = {ReadOnly}, Strict = {Strict}, Profile = {Profile} }}";
}
