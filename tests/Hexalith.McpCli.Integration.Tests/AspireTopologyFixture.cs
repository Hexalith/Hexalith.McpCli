using System.Net.Http.Headers;
using System.Diagnostics;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

using Hexalith.EventStore.Aspire;
using Hexalith.EventStore.Testing.Integration;
using Hexalith.McpCli.AppHost;
using Hexalith.EventStore.Client.Gateway;
using Hexalith.EventStore.Contracts.Queries;
using Hexalith.Tenants.Contracts.Queries;

using Microsoft.Extensions.Options;

namespace Hexalith.McpCli.Integration.Tests;

/// <summary>Uses the platform lifecycle and prerequisite handling for the three-service test topology.</summary>
public sealed class AspireTopologyFixture : AspireTopologyFixtureBase<Projects.Hexalith_McpCli_AppHost>, IAsyncLifetime
{
    /// <summary>The test-owned identity bootstrapped by the server inside private state.</summary>
    internal const string AdministratorId = TopologyConfiguration.BootstrapAdministratorId;
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
        if (Environment.GetEnvironmentVariable("MCPCLI_ISOLATED_TOPOLOGY") != "1")
            throw new InvalidOperationException("Live topology tests require tools/live-topology/run-isolated.py; refusing to use host Dapr or Redis.");
        TopologyConfiguration.ValidateWorkspace(RepositoryProjectPaths.GetRepositoryRoot());
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
    internal HttpClient CreateAuthenticatedGatewayClient(bool invalidSignature = false)
    {
        // The pinned Gateway client sets buffering before its first request, so it
        // needs a fresh client after the platform's liveness client has been used.
        var client = new HttpClient { BaseAddress = Client("eventstore").BaseAddress, Timeout = TimeSpan.FromSeconds(35) };
        client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", CreateIdentity(invalidSignature, live: false));
        return client;
    }

    /// <summary>The platform-discovered Gateway endpoint; never a configured host topology.</summary>
    internal Uri GatewayEndpoint => Client("eventstore").BaseAddress!;

    /// <summary>Creates the short-lived delegated identity shared privately with one runner.</summary>
    internal string CreateLiveIdentity() => CreateIdentity(invalidSignature: false, live: true);

    /// <summary>Activates the standard platform prerequisite before allowing vector writes into fresh state.</summary>
    internal async Task RequireProjectionWriterAsync(CancellationToken cancellationToken)
    {
        string receipt = Environment.GetEnvironmentVariable("MCPCLI_ISOLATED_REDIS_BACKUP_RECEIPT")
            ?? throw new InvalidOperationException("The isolated wrapper omitted its pre-application Redis backup receipt.");
        var start = new ProcessStartInfo("git") { RedirectStandardOutput = true, RedirectStandardError = true };
        foreach (string argument in new[] { "-C", Path.Combine(RepositoryProjectPaths.GetRepositoryRoot(), "references", "Hexalith.EventStore"), "rev-parse", "HEAD" })
            start.ArgumentList.Add(argument);
        using Process git = Process.Start(start)!;
        using var deadline = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        deadline.CancelAfter(TimeSpan.FromSeconds(10));
        Task<string> output = git.StandardOutput.ReadToEndAsync(deadline.Token);
        Task<string> error = git.StandardError.ReadToEndAsync(deadline.Token);
        try { await git.WaitForExitAsync(deadline.Token).ConfigureAwait(false); }
        finally { if (!git.HasExited) git.Kill(entireProcessTree: true); }
        if (git.ExitCode != 0) throw new InvalidOperationException("Cannot identify the deployed EventStore source commit for private writer activation.");
        _ = await error.ConfigureAwait(false);
        using var http = new HttpClient { BaseAddress = GatewayEndpoint, Timeout = TimeSpan.FromSeconds(30) };
        http.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", CreateLiveIdentity());
        await ProjectionWriterBootstrap.ActivateAsync(http, receipt, (await output.ConfigureAwait(false)).Trim(), cancellationToken).ConfigureAwait(false);
    }

    /// <summary>Waits for a privileged persisted-membership query, independently of resource liveness.</summary>
    internal async Task RequireAdministratorAuthorityAsync(CancellationToken cancellationToken)
    {
        using var http = new HttpClient { BaseAddress = GatewayEndpoint, Timeout = TimeSpan.FromSeconds(15) };
        http.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", CreateLiveIdentity());
        IEventStoreGatewayClient gateway = new EventStoreGatewayClient(http, Options.Create(new EventStoreGatewayClientOptions()));
        var request = new SubmitQueryRequest("system", GetGlobalAdministratorsQuery.Domain, "global-administrators",
            GetGlobalAdministratorsQuery.QueryType, GetGlobalAdministratorsQuery.ProjectionType);
        using var deadline = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        deadline.CancelAfter(TimeSpan.FromSeconds(60));
        string failure = "No successful privileged administrator document.";
        try
        {
            while (true)
            {
                try
                {
                    EventStoreQueryResult result = await gateway.SubmitQueryAsync(request, cancellationToken: deadline.Token).ConfigureAwait(false);
                    if (result.Payload is { } payload && payload.TryGetProperty("items", out JsonElement items)
                        && items.EnumerateArray().Any(item => item.GetProperty("userId").GetString() == AdministratorId))
                        return;
                    failure = "Privileged query omitted the persisted bootstrap administrator.";
                }
                catch (EventStoreGatewayException exception)
                {
                    failure = $"Privileged query HTTP {exception.StatusCode}.";
                }
                await Task.Delay(TimeSpan.FromMilliseconds(500), deadline.Token).ConfigureAwait(false);
            }
        }
        catch (OperationCanceledException exception) when (!cancellationToken.IsCancellationRequested)
        {
            throw new TimeoutException($"Bootstrap authority did not converge in 60 seconds. {failure}", exception);
        }
    }

    private string CreateIdentity(bool invalidSignature, bool live)
    {
        long now = DateTimeOffset.UtcNow.ToUnixTimeSeconds();
        string header = Encode(JsonSerializer.SerializeToUtf8Bytes(new { alg = "HS256", typ = "JWT" }));
        string payload = Encode(JsonSerializer.SerializeToUtf8Bytes(new Dictionary<string, object>
        {
            ["iss"] = "mcpcli-live-tests", ["aud"] = "hexalith-eventstore", ["sub"] = live ? AdministratorId : "mcpcli-live-smoke",
            ["tenants"] = live ? "[\"system\",\"tenant-a\"]" : "[\"system\"]",
            ["domains"] = live ? "[\"tenants\",\"party\",\"global-administrators\"]" : "[\"tenants\"]",
            ["permissions"] = live ? "[\"command:write\",\"query:read\"]" : "[\"query:read\"]",
            ["global_admin"] = live ? "true" : "false",
            ["iat"] = now, ["nbf"] = now - 30, ["exp"] = now + (live ? 600 : 300),
        }));
        string unsigned = header + "." + payload;
        string signature = Encode(HMACSHA256.HashData(Encoding.UTF8.GetBytes(invalidSignature ? Convert.ToBase64String(RandomNumberGenerator.GetBytes(32)) : _signingKey), Encoding.ASCII.GetBytes(unsigned)));
        return unsigned + "." + signature;
    }

    private static string Encode(byte[] bytes) => Convert.ToBase64String(bytes).TrimEnd('=').Replace('+', '-').Replace('/', '_');
}
