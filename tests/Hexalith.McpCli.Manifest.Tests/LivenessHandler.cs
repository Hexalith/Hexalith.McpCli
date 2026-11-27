namespace Hexalith.McpCli.Manifest.Tests;

/// <summary>Simulates a bounded transient timeout before a successful liveness response.</summary>
/// <param name="cancelFirst">Whether the first request should time out.</param>
/// <param name="wait">An optional operation that blocks a request until canceled.</param>
internal sealed class LivenessHandler(bool cancelFirst, Func<CancellationToken, Task>? wait = null) : HttpMessageHandler
{
    /// <summary>The number of actual requests observed.</summary>
    internal int Calls { get; private set; }

    /// <inheritdoc/>
    protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        Calls++;
        if (Calls == 1 && cancelFirst)
        {
            throw new TaskCanceledException("controlled request timeout");
        }
        if (wait is not null)
        {
            await wait(cancellationToken).ConfigureAwait(false);
        }
        return new HttpResponseMessage(System.Net.HttpStatusCode.OK);
    }
}
