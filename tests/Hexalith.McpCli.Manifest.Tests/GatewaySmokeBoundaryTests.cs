using System.Diagnostics;
using System.Net;
using System.Net.Sockets;
using System.Text;

using Hexalith.EventStore.Client.Gateway;
using Hexalith.EventStore.Contracts.Queries;
using Hexalith.McpCli.Integration.Tests;

using Microsoft.Extensions.Options;

namespace Hexalith.McpCli.Manifest.Tests;

/// <summary>Proves a live listener can still be unusable and the real smoke query remains bounded.</summary>
public sealed class GatewaySmokeBoundaryTests
{
    /// <summary>A real HTTP failure retains the pinned client exception and contextual status diagnostic.</summary>
    [Fact]
    public async Task ForbiddenGatewayReportsImmediateContextAndPinnedException()
    {
        using var listener = new TcpListener(IPAddress.Loopback, 0);
        listener.Start();
        int port = ((IPEndPoint)listener.LocalEndpoint).Port;
        using var deadline = CancellationTokenSource.CreateLinkedTokenSource(TestContext.Current.CancellationToken);
        deadline.CancelAfter(TimeSpan.FromSeconds(10));
        Task server = RespondAsync();
        using var http = new HttpClient { BaseAddress = new Uri($"http://127.0.0.1:{port}") };
        var gateway = new EventStoreGatewayClient(http, Options.Create(new EventStoreGatewayClientOptions()));
        InvalidOperationException failure = await Assert.ThrowsAsync<InvalidOperationException>(() =>
            GatewaySmokeProbe.ExecuteAsync(gateway, new SubmitQueryRequest("test", "example", "index", "list-example"), deadline.Token));
        Assert.Equal("Authenticated Gateway query failed with HTTP 403 after resource liveness passed. Check Gateway routing, authentication and domain-service logs.", failure.Message);
        EventStoreGatewayException cause = Assert.IsType<EventStoreGatewayException>(failure.InnerException);
        Assert.Equal(403, cause.StatusCode);
        await server;

        async Task RespondAsync()
        {
            using TcpClient connection = await listener.AcceptTcpClientAsync(deadline.Token);
            using NetworkStream stream = connection.GetStream();
            byte[] buffer = new byte[4096];
            int received = await stream.ReadAsync(buffer, deadline.Token);
            Assert.StartsWith("POST /api/v1/queries ", Encoding.ASCII.GetString(buffer, 0, received));
            await stream.WriteAsync(Encoding.ASCII.GetBytes("HTTP/1.1 403 Forbidden\r\nContent-Type: application/problem+json\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}"), deadline.Token);
        }
    }

    /// <summary>An alive HTTP endpoint that never answers the query fails at the shipped smoke deadline.</summary>
    [Fact]
    public async Task AliveGatewayThatNeverAnswersQueryFailsWithinSmokeDeadline()
    {
        using var listener = new TcpListener(IPAddress.Loopback, 0);
        listener.Start();
        int port = ((IPEndPoint)listener.LocalEndpoint).Port;
        using var serverLifetime = CancellationTokenSource.CreateLinkedTokenSource(TestContext.Current.CancellationToken);
        serverLifetime.CancelAfter(TimeSpan.FromSeconds(40));
        int requests = 0;
        Task server = ServeAsync();
        var endpoint = new Uri($"http://127.0.0.1:{port}");
        using var livenessClient = new HttpClient { BaseAddress = endpoint };
        using HttpResponseMessage alive = await livenessClient.GetAsync("alive", serverLifetime.Token).ConfigureAwait(true);
        Assert.Equal(HttpStatusCode.OK, alive.StatusCode);
        using var http = new HttpClient { BaseAddress = endpoint, Timeout = TimeSpan.FromSeconds(40) };
        var gateway = new EventStoreGatewayClient(http, Options.Create(new EventStoreGatewayClientOptions()));
        var request = new SubmitQueryRequest("test", "example", "index", "list-example");
        var elapsed = Stopwatch.StartNew();
        try
        {
            TimeoutException failure = await Assert.ThrowsAsync<TimeoutException>(() => GatewaySmokeProbe.ExecuteAsync(gateway, request, TestContext.Current.CancellationToken)
                .WaitAsync(TimeSpan.FromSeconds(35), TestContext.Current.CancellationToken));
            Assert.Equal("Authenticated Gateway query exceeded 30 seconds after resource liveness passed. Check Gateway routing, sidecars and domain-service logs.", failure.Message);
            Assert.Equal(TimeSpan.FromSeconds(30), GatewaySmokeProbe.RequestTimeout);
            Assert.InRange(elapsed.Elapsed, TimeSpan.FromSeconds(29), TimeSpan.FromSeconds(35));
            Assert.Equal(2, Volatile.Read(ref requests));
        }
        finally
        {
            serverLifetime.Cancel();
            listener.Stop();
            try { await server.ConfigureAwait(true); }
            catch (OperationCanceledException) { }
        }

        async Task ServeAsync()
        {
            for (int index = 0; index < 2; index++)
            {
                using TcpClient connection = await listener.AcceptTcpClientAsync(serverLifetime.Token).ConfigureAwait(true);
                using NetworkStream stream = connection.GetStream();
                byte[] buffer = new byte[4096];
                var headersBuffer = new StringBuilder();
                while (!headersBuffer.ToString().Contains("\r\n\r\n", StringComparison.Ordinal))
                {
                    int read = await stream.ReadAsync(buffer, serverLifetime.Token).ConfigureAwait(true);
                    Assert.True(read > 0, "The test request ended before its headers were complete.");
                    headersBuffer.Append(Encoding.ASCII.GetString(buffer, 0, read));
                }
                string headers = headersBuffer.ToString();
                if (index == 0)
                {
                    Assert.StartsWith("GET /alive ", headers);
                    await stream.WriteAsync(Encoding.ASCII.GetBytes("HTTP/1.1 200 OK\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"), serverLifetime.Token).ConfigureAwait(true);
                    Interlocked.Increment(ref requests);
                }
                else
                {
                    Assert.StartsWith("POST /api/v1/queries ", headers);
                    Interlocked.Increment(ref requests);
                    await Task.Delay(Timeout.InfiniteTimeSpan, serverLifetime.Token).ConfigureAwait(true);
                }
            }
        }
    }
}
