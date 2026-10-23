using System.Net.Http.Headers;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

using Hexalith.EventStore.Testing.Integration;
using Hexalith.McpCli.AppHost;

namespace Hexalith.McpCli.Integration.Tests;

/// <summary>Uses the platform lifecycle and prerequisite handling for the three-service test topology.</summary>
public sealed class AspireTopologyFixture : AspireTopologyFixtureBase<Projects.Hexalith_McpCli_AppHost>, IAsyncLifetime
{
    private string? _additionalPrerequisiteFailure;
    private readonly string _signingKey = Convert.ToBase64String(RandomNumberGenerator.GetBytes(32));

    /// <inheritdoc/>
    protected override IReadOnlyList<AspireResource> Resources =>
    [
        new("eventstore", "http", TimeSpan.FromSeconds(30), TimeSpan.FromMinutes(2), true, TimeSpan.FromMinutes(2)),
        new("tenants", "http", TimeSpan.FromSeconds(30), TimeSpan.FromMinutes(2), true, TimeSpan.FromMinutes(2)),
        new("parties", "http", TimeSpan.FromSeconds(30), TimeSpan.FromMinutes(2), true, TimeSpan.FromMinutes(2)),
    ];

    /// <inheritdoc/>
    protected override IReadOnlyList<string> ExtraAppArgs =>
    [
        $"--Authentication:JwtBearer:SigningKey={_signingKey}",
    ];

    /// <summary>Rejects an existing requested topology before the platform starts or waits on resources.</summary>
    public new async ValueTask InitializeAsync()
    {
        _additionalPrerequisiteFailure = await TopologyPrerequisites.GetFailureAsync().ConfigureAwait(false);
        if (_additionalPrerequisiteFailure is not null) return;

        if (!DaprTestPrerequisites.IsAvailable)
        {
            _additionalPrerequisiteFailure = "Basic platform Redis, placement or scheduler prerequisites are unavailable.";
            return;
        }
        TopologyConfiguration.EnsureNoConflictingTopology(3501);

        await base.InitializeAsync().ConfigureAwait(false);
    }

    /// <summary>Reports missing topology-specific prerequisites using the standard skip diagnostic.</summary>
    public new void SkipIfUnavailable()
    {
        if (_additionalPrerequisiteFailure is not null)
            Assert.Skip(DaprTestPrerequisites.SkipReason + " " + _additionalPrerequisiteFailure);
        base.SkipIfUnavailable();
    }

    /// <summary>Creates a caller-owned client at the platform-discovered endpoint with a short-lived test identity.</summary>
    internal HttpClient CreateAuthenticatedGatewayClient()
    {
        // The pinned Gateway client sets buffering before its first request, so it
        // needs a fresh client after the platform's liveness client has been used.
        var client = new HttpClient { BaseAddress = Client("eventstore").BaseAddress, Timeout = TimeSpan.FromSeconds(35) };
        long now = DateTimeOffset.UtcNow.ToUnixTimeSeconds();
        string header = Encode(JsonSerializer.SerializeToUtf8Bytes(new { alg = "HS256", typ = "JWT" }));
        string payload = Encode(JsonSerializer.SerializeToUtf8Bytes(new Dictionary<string, object>
        {
            ["iss"] = "mcpcli-live-tests", ["aud"] = "hexalith-eventstore", ["sub"] = "mcpcli-live-smoke",
            ["tenants"] = "[\"system\"]", ["domains"] = "[\"tenants\"]", ["permissions"] = "[\"query:read\"]",
            ["iat"] = now, ["nbf"] = now - 30, ["exp"] = now + 300,
        }));
        string unsigned = header + "." + payload;
        string signature = Encode(HMACSHA256.HashData(Encoding.UTF8.GetBytes(_signingKey), Encoding.ASCII.GetBytes(unsigned)));
        client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", unsigned + "." + signature);
        return client;
    }

    private static string Encode(byte[] bytes) => Convert.ToBase64String(bytes).TrimEnd('=').Replace('+', '-').Replace('/', '_');
}
