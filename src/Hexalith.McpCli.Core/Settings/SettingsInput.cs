namespace Hexalith.McpCli.Core.Settings;

/// <summary>Explicit global CLI options before precedence resolution.</summary>
/// <param name="Url">The explicit gateway URL.</param>
/// <param name="Token">The explicit bearer token.</param>
/// <param name="Tenant">The explicit session tenant.</param>
/// <param name="Actor">The explicit session actor.</param>
/// <param name="AllowTenantOverride">The explicit tenant override gate.</param>
/// <param name="Profile">The explicit profile name.</param>
/// <param name="Format">The explicit output format.</param>
/// <param name="Output">The explicit output file.</param>
/// <param name="ReadOnly">The explicit read-only flag.</param>
/// <param name="Strict">The explicit strict Catalog flag.</param>
public sealed record SettingsInput(
    string? Url = null,
    string? Token = null,
    string? Tenant = null,
    string? Actor = null,
    bool? AllowTenantOverride = null,
    string? Profile = null,
    string? Format = null,
    string? Output = null,
    bool? ReadOnly = null,
    bool? Strict = null);
