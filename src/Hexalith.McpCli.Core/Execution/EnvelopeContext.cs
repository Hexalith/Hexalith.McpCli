namespace Hexalith.McpCli.Core.Execution;

/// <summary>Trusted session values used when forming a gateway envelope.</summary>
/// <param name="Tenant">The session tenant.</param>
/// <param name="Actor">The trusted session actor.</param>
/// <param name="AllowTenantOverride">Whether an MCP call may select another tenant.</param>
/// <param name="AllowedExtensions">The allowlisted command extension keys.</param>
public sealed record EnvelopeContext(
    string? Tenant,
    string? Actor,
    bool AllowTenantOverride,
    IReadOnlySet<string> AllowedExtensions);
