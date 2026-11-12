namespace Hexalith.McpCli.Manifest.Tests;

/// <summary>Simulates a bounded transient timeout before a successful liveness response.</summary>
/// <param name="cancelFirst">Whether the first request should time out.</param>
internal sealed class LivenessHandler(bool cancelFirst) : HttpMessageHandler
{
    /// <summary>The number of actual requests observed.</summary>
    internal int Calls { get; private set; }

    /// <inheritdoc/>
    protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        Calls++;
        return Calls == 1 && cancelFirst
            ? Task.FromException<HttpResponseMessage>(new TaskCanceledException("controlled request timeout"))
            : Task.FromResult(new HttpResponseMessage(System.Net.HttpStatusCode.OK));
    }
}
