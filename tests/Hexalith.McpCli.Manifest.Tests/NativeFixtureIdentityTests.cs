using System.Text.Json;

using Hexalith.McpCli.Integration.Tests;

namespace Hexalith.McpCli.Manifest.Tests;

/// <summary>Protects native signed scope grants without starting an application.</summary>
public sealed class NativeFixtureIdentityTests
{
    /// <summary>Every immutable vector/plan normal scope has one exact grant; reserved and wildcard scopes are absent.</summary>
    [Fact]
    public void LiveIdentityGrantsExactlyTheRequiredNormalTenants()
    {
        string root = FindRepositoryRoot();
        var expected = new HashSet<string>(StringComparer.Ordinal);
        foreach (string directory in new[] { "tools/conformance-vectors/v1/modules", "tools/live-topology/plans" })
        {
            foreach (string file in Directory.EnumerateFiles(Path.Combine(root, directory), "*.json", SearchOption.AllDirectories))
            {
                using JsonDocument document = JsonDocument.Parse(File.ReadAllBytes(file));
                Visit(document.RootElement);
            }
        }
        IReadOnlyDictionary<string, object> claims = NativeFixtureIdentity.CreateClaims(1000, live: true);
        Assert.Equal(expected.Order(StringComparer.Ordinal), ((string[])claims["eventstore:tenant"]).Order(StringComparer.Ordinal));
        Assert.Equal("agent", claims["eventstore:surface"]);
        Assert.Equal("GlobalAdministrator", claims["role"]);
        Assert.False(claims.ContainsKey("global_admin"));
        Assert.False(claims.ContainsKey("tenants"));
        Assert.DoesNotContain(((string[])claims["eventstore:permission"]), permission => permission.Contains('*'));

        void Visit(JsonElement value)
        {
            if (value.ValueKind == JsonValueKind.Object)
            {
                foreach (JsonProperty property in value.EnumerateObject())
                {
                    if (property.Name == "envelope" && property.Value.TryGetProperty("tenant", out JsonElement tenant)
                        && tenant.ValueKind == JsonValueKind.String && tenant.GetString() is { } scope && !scope.StartsWith("platform:", StringComparison.Ordinal))
                        expected.Add(scope);
                    Visit(property.Value);
                }
            }
            else if (value.ValueKind == JsonValueKind.Array)
                foreach (JsonElement item in value.EnumerateArray()) Visit(item);
        }
    }

    /// <summary>The excluded administrator read uses its actual UI eligibility and exact read permission.</summary>
    [Fact]
    public void AuthorityObservationUsesUiEligibilityWithoutGrantingAdministratorClaims()
    {
        IReadOnlyDictionary<string, object> claims = NativeFixtureIdentity.CreateClaims(1000, live: false, authorityRead: true);
        Assert.Equal("ui", claims["eventstore:surface"]);
        Assert.Equal(new[] { "query:read", "global-administrators:read" }, (string[])claims["eventstore:permission"]);
        Assert.Equal(new[] { "global-administrators" }, (string[])claims["eventstore:domain"]);
        Assert.Empty((string[])claims["eventstore:tenant"]);
        Assert.False(claims.ContainsKey("global_admin"));
        Assert.False(claims.ContainsKey("role"));
    }

    private static string FindRepositoryRoot()
    {
        DirectoryInfo? current = new(AppContext.BaseDirectory);
        while (current is not null && !File.Exists(Path.Combine(current.FullName, "Hexalith.McpCli.slnx"))) current = current.Parent;
        return current?.FullName ?? throw new InvalidOperationException("Repository root is unavailable.");
    }

    /// <summary>The independent smoke is an exact read caller without any business tenant or write grant.</summary>
    [Fact]
    public void SmokeIdentityCarriesOnlyItsNativeReadPermissions()
    {
        IReadOnlyDictionary<string, object> claims = NativeFixtureIdentity.CreateClaims(1000, live: false);
        Assert.Empty((string[])claims["eventstore:tenant"]);
        Assert.Equal(new[] { "query:read", "tenants:read" }, (string[])claims["eventstore:permission"]);
        Assert.Equal(new[] { "tenants" }, (string[])claims["eventstore:domain"]);
        Assert.Equal("agent", claims["eventstore:surface"]);
        Assert.False(claims.ContainsKey("global_admin"));
    }
}
