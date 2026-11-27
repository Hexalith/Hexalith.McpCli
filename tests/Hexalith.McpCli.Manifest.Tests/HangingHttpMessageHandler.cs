namespace Hexalith.McpCli.Manifest.Tests;

/// <summary>Holds HTTP liveness requests open until canceled so terminal-failure aborts can be verified.</summary>
internal sealed class HangingHttpMessageHandler : HttpMessageHandler
{
    private readonly TaskCompletionSource _requestStarted = new(TaskCreationOptions.RunContinuationsAsynchronously);

    /// <summary>Completes once the first outgoing HTTP request has been received.</summary>
    internal Task RequestStarted => _requestStarted.Task;

    /// <inheritdoc/>
    protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        _requestStarted.TrySetResult();
        await Task.Delay(Timeout.InfiniteTimeSpan, cancellationToken).ConfigureAwait(false);
        return new HttpResponseMessage(System.Net.HttpStatusCode.OK);
    }
}
