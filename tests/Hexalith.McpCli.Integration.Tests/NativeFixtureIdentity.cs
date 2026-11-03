using Hexalith.McpCli.AppHost;

namespace Hexalith.McpCli.Integration.Tests;

/// <summary>Declares the native signed fixture grants independently of resource startup.</summary>
internal static class NativeFixtureIdentity
{
    /// <summary>The signed negative-control subject, never enrolled by bootstrap.</summary>
    internal const string NonmemberId = "mcpcli-live-nonmember";

    /// <summary>Creates exact native grants; persisted authority remains the owner's responsibility.</summary>
    internal static IReadOnlyDictionary<string, object> CreateClaims(long now, bool live, bool maintenance = false, bool authorityRead = false, bool nonmember = false)
    {
        var claims = new Dictionary<string, object>
        {
            ["iss"] = "mcpcli-live-tests", ["aud"] = "hexalith-eventstore", ["sub"] = nonmember ? NonmemberId : TopologyConfiguration.BootstrapAdministratorId,
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
        // This signed role is a hint for the real bootstrapped actor. The owner must independently
        // verify its current native-source membership before restoring administrator command context.
        if (live || maintenance) claims["role"] = "GlobalAdministrator";
        // The real writer maintenance endpoint also requires its existing UI surface.
        if (maintenance)
        {
            claims["eventstore:surface"] = "ui";
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
