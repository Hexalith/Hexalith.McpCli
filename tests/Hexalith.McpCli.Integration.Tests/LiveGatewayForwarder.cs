using System.Collections.Concurrent;
using System.Text;
using Hexalith.McpCli.Cli.Tests;

namespace Hexalith.McpCli.Integration.Tests;

/// <summary>Counts real head requests while forwarding their exact credential and body to the private Gateway.</summary>
internal sealed class LiveGatewayForwarder : IAsyncDisposable
{
    private readonly HttpClient _http;
    private readonly ScriptedGateway _gateway;
    private readonly ConcurrentQueue<(int Status, string Body)> _responses = new();

    /// <summary>Starts a test-owned loopback forwarder at the discovered Gateway endpoint.</summary>
    internal LiveGatewayForwarder(Uri endpoint)
    {
        _http = new HttpClient { BaseAddress = endpoint, Timeout = TimeSpan.FromSeconds(35) };
        _gateway = new ScriptedGateway(ForwardAsync);
    }

    /// <summary>Gets the head's loopback URL.</summary>
    internal string Url => _gateway.Url;

    /// <summary>Gets all requests, including any request a removed local guard would allow.</summary>
    internal IReadOnlyList<GatewayRequest> Requests => _gateway.Requests;

    /// <summary>Gets completed real Gateway responses.</summary>
    internal IReadOnlyList<(int Status, string Body)> Responses => [.. _responses];

    /// <inheritdoc />
    public async ValueTask DisposeAsync()
    {
        await _gateway.DisposeAsync();
        _http.Dispose();
    }

    private async Task<byte[]> ForwardAsync(GatewayRequest captured)
    {
        using var request = new HttpRequestMessage(HttpMethod.Post, captured.Path)
        { Content = new StringContent(captured.Body, Encoding.UTF8, "application/json") };
        if (captured.Headers.TryGetValue("Authorization", out string? authorization))
            request.Headers.TryAddWithoutValidation("Authorization", authorization);
        using HttpResponseMessage response = await _http.SendAsync(request, TestContext.Current.CancellationToken);
        string body = await response.Content.ReadAsStringAsync(TestContext.Current.CancellationToken);
        _responses.Enqueue(((int)response.StatusCode, body));
        return ScriptedGateway.Response((int)response.StatusCode, response.ReasonPhrase ?? "Gateway response",
            response.Content.Headers.ContentType?.ToString(), body);
    }
}
