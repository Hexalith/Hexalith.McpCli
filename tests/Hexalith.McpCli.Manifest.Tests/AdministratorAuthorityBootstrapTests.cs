using System.Diagnostics;
using System.Net;
using System.Text.Json;

using Hexalith.McpCli.Integration.Tests;

namespace Hexalith.McpCli.Manifest.Tests;

/// <summary>Protects the persisted administrator barrier through the actual Gateway HTTP client.</summary>
public sealed class AdministratorAuthorityBootstrapTests
{
    private const string AdministratorId = "mcpcli-live-admin";

    /// <summary>A successful document without the administrator cannot release waiting vector Commands.</summary>
    [Fact]
    public async Task DocumentWithoutAdministratorKeepsPolling()
    {
        int calls = 0;
        using var handler = new ProjectionWriterBootstrapHandler(async request =>
        {
            Assert.Equal(HttpMethod.Post, request.Method);
            Assert.Equal("/api/v1/queries", request.RequestUri!.AbsolutePath);
            using JsonDocument body = JsonDocument.Parse(await request.Content!.ReadAsStringAsync().ConfigureAwait(false));
            Assert.Equal("system", body.RootElement.GetProperty("tenant").GetString());
            Assert.Equal("global-administrators", body.RootElement.GetProperty("aggregateId").GetString());
            return Response(++calls == 1 ? "another-administrator" : AdministratorId);
        });
        using var http = new HttpClient(handler) { BaseAddress = new Uri("http://127.0.0.1:1234/") };
        await AdministratorAuthorityBootstrap.RequireAsync(http, AdministratorId, TestContext.Current.CancellationToken);
        Assert.Equal(2, calls);
    }

    /// <summary>The expected persisted membership releases the barrier after exactly one Query.</summary>
    [Fact]
    public async Task PersistedAdministratorReturnsImmediately()
    {
        int calls = 0;
        using var handler = new ProjectionWriterBootstrapHandler(_ =>
        {
            calls++;
            return Task.FromResult(Response(AdministratorId));
        });
        using var http = new HttpClient(handler) { BaseAddress = new Uri("http://127.0.0.1:1234/") };
        await AdministratorAuthorityBootstrap.RequireAsync(http, AdministratorId, TestContext.Current.CancellationToken);
        Assert.Equal(1, calls);
    }

    /// <summary>Resource liveness and successful documents cannot substitute for authority before the real deadline.</summary>
    [Fact]
    public async Task MissingPersistedAdministratorFailsAtAuthorityDeadline()
    {
        int calls = 0;
        using var handler = new ProjectionWriterBootstrapHandler(_ =>
        {
            calls++;
            return Task.FromResult(Response("another-administrator"));
        });
        using var http = new HttpClient(handler) { BaseAddress = new Uri("http://127.0.0.1:1234/") };
        var elapsed = Stopwatch.StartNew();
        TimeoutException failure = await Assert.ThrowsAsync<TimeoutException>(() =>
            AdministratorAuthorityBootstrap.RequireAsync(http, AdministratorId, TestContext.Current.CancellationToken)
                .WaitAsync(TimeSpan.FromSeconds(70), TestContext.Current.CancellationToken));
        Assert.Equal("Bootstrap authority did not converge in 60 seconds. Privileged query omitted the persisted bootstrap administrator.", failure.Message);
        Assert.Equal(TimeSpan.FromSeconds(60), AdministratorAuthorityBootstrap.RequestTimeout);
        Assert.InRange(elapsed.Elapsed, TimeSpan.FromSeconds(59), TimeSpan.FromSeconds(70));
        Assert.True(calls > 1);
    }

    private static HttpResponseMessage Response(string userId)
        => new(HttpStatusCode.OK)
        {
            Content = new StringContent(JsonSerializer.Serialize(new
            {
                correlationId = "01ARZ3NDEKTSV4RRFFQ69G5FAV",
                success = true,
                payload = new { items = new[] { new { userId } } },
            })),
        };
}
