using System.Net;
using System.Text;
using Hexalith.McpCli.Integration.Tests;
using Shouldly;

namespace Hexalith.McpCli.Cli.Tests;

/// <summary>Proves that concurrent boundary requests overlap at the real forwarding boundary.</summary>
public sealed class LiveGatewayForwarderTests
{
    /// <summary>Neither request is forwarded until both complete network requests have been captured.</summary>
    [Fact]
    public async Task ConcurrentPairIsCapturedBeforeEitherRequestIsForwardedAsync()
    {
        LiveGatewayForwarder? observed = null;
        await using var upstream = new ScriptedGateway(_ =>
        {
            observed!.Requests.Count.ShouldBe(2);
            return ScriptedGateway.Response(202, "Accepted", "application/json", "{}");
        });
        await using var forwarder = new LiveGatewayForwarder(new Uri(upstream.Url));
        observed = forwarder;
        Task pair = forwarder.CaptureConcurrentPairAsync(TimeSpan.FromSeconds(5));
        using var http = new HttpClient { BaseAddress = new Uri(forwarder.Url), Timeout = TimeSpan.FromSeconds(5) };
        Task<HttpResponseMessage> first = http.PostAsync("api/v1/commands", new StringContent("first", Encoding.UTF8, "application/json"), TestContext.Current.CancellationToken);
        using var deadline = CancellationTokenSource.CreateLinkedTokenSource(TestContext.Current.CancellationToken);
        deadline.CancelAfter(TimeSpan.FromSeconds(3));
        while (forwarder.Requests.Count == 0) await Task.Delay(10, deadline.Token);
        await Task.Delay(100, deadline.Token);
        upstream.Requests.ShouldBeEmpty();
        first.IsCompleted.ShouldBeFalse();
        pair.IsCompleted.ShouldBeFalse();
        Task<HttpResponseMessage> second = http.PostAsync("api/v1/commands", new StringContent("second", Encoding.UTF8, "application/json"), TestContext.Current.CancellationToken);
        await pair.WaitAsync(deadline.Token);
        HttpResponseMessage[] responses = await Task.WhenAll(first, second).WaitAsync(deadline.Token);
        foreach (HttpResponseMessage response in responses)
        {
            response.StatusCode.ShouldBe(HttpStatusCode.Accepted);
            response.Dispose();
        }
        upstream.Requests.Count.ShouldBe(2);
    }

    /// <summary>A missing second request times out without forwarding the first one.</summary>
    [Fact]
    public async Task IncompleteConcurrentPairIsBoundedAndNeverForwardedAsync()
    {
        await using var upstream = new ScriptedGateway(_ => ScriptedGateway.Response(202, "Accepted", "application/json", "{}"));
        await using var forwarder = new LiveGatewayForwarder(new Uri(upstream.Url));
        Task pair = forwarder.CaptureConcurrentPairAsync(TimeSpan.FromMilliseconds(100));
        using var http = new HttpClient { BaseAddress = new Uri(forwarder.Url), Timeout = TimeSpan.FromSeconds(3) };
        Task<HttpResponseMessage> first = http.PostAsync("api/v1/commands", new StringContent("first"), TestContext.Current.CancellationToken);
        await Assert.ThrowsAsync<TimeoutException>(() => pair);
        await Assert.ThrowsAsync<HttpRequestException>(() => first);
        upstream.Requests.ShouldBeEmpty();
    }
}
