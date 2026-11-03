using Hexalith.McpCli.AppHost;

namespace Hexalith.McpCli.Integration.Tests;

/// <summary>Declares the native signed fixture grants independently of resource startup.</summary>
internal static class NativeFixtureIdentity
{
    /// <summary>Creates exact native grants; persisted authority remains the owner's responsibility.</summary>
    internal static IReadOnlyDictionary<string, object> CreateClaims(long now, bool live, bool maintenance = false, bool authorityRead = false)
    {
        var claims = new Dictionary<string, object>
        {
            ["iss"] = "mcpcli-live-tests", ["aud"] = "hexalith-eventstore", ["sub"] = TopologyConfiguration.BootstrapAdministratorId,
            ["eventstore:surface"] = "agent",
            ["eventstore:tenant"] = live ? new[] { "tenant-a", "vector-audit", "vector-users", "vector-removal", "vector-enable",
                "vector-members", "vector-disable", "vector-config-removal", "vector-config", "vector-read", "vector-roles",
                "vector-create", "vector-update", "vector-list-a", "vector-list-b", "vector-list-c",
                "vector-membership-a", "vector-membership-b", "vector-membership-c" } : Array.Empty<string>(),
            ["eventstore:domain"] = live ? new[] { "tenants", "party", "global-administrators" } : new[] { "tenants" },
            ["eventstore:permission"] = live ? new[] { "command:submit", "query:read", "tenants:read", "global-administrators:read",
                "tenants:create", "tenants:update", "tenants:disable", "tenants:enable", "tenants:add-user", "tenants:remove-user",
                "tenants:change-user-role", "tenants:set-configuration", "tenants:remove-configuration" }
                : new[] { "query:read", "tenants:read" },
            ["iat"] = now, ["nbf"] = now - 30, ["exp"] = now + (live ? 600 : 300),
        };
        // The real writer maintenance endpoint requires its existing operator role.
        // Business calls use the separate native grants and persisted administrator barrier.
        if (maintenance)
        {
            claims["eventstore:surface"] = "ui";
            claims["role"] = "GlobalAdministrator";
        }
        // The persisted administrator read is an existing UI-only infrastructure query.
        // It remains excluded from agent discovery and needs its own exact read credential.
        if (authorityRead)
        {
            claims["eventstore:surface"] = "ui";
            claims["eventstore:tenant"] = Array.Empty<string>();
            claims["eventstore:domain"] = new[] { "global-administrators" };
            claims["eventstore:permission"] = new[] { "query:read", "global-administrators:read" };
        }
        return claims;
    }
}
