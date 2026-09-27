using System.Net.Http.Headers;

namespace Hexalith.McpCli.Hosting;

/// <summary>Adds the process's configured bearer credential only to gateway requests.</summary>
internal sealed class StaticBearerTokenHandler(string token) : DelegatingHandler
{
    /// <inheritdoc />
    protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
        return base.SendAsync(request, cancellationToken);
    }
}
