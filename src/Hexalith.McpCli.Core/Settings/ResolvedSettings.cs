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
    string? Token,
    string? Tenant,
    string? Actor,
    bool AllowTenantOverride,
    IReadOnlySet<string> AllowedExtensions,
    string Format,
    string? Output,
    bool ReadOnly,
    bool Strict,
    string? Profile,
    IReadOnlyDictionary<string, string> Sources);
