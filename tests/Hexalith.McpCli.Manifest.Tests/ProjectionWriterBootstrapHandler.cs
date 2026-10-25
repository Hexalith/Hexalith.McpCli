namespace Hexalith.McpCli.Manifest.Tests;

/// <summary>Captures maintenance and readiness requests without opening a network connection.</summary>
/// <param name="respond">The bounded response behavior for a request.</param>
internal sealed class ProjectionWriterBootstrapHandler(Func<HttpRequestMessage, Task<HttpResponseMessage>> respond) : HttpMessageHandler
{
    /// <inheritdoc/>
    protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        => respond(request);
}
