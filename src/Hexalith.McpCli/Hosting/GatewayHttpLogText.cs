namespace Hexalith.McpCli.Hosting;

/// <summary>Formats the request text that the Gateway HTTP loggers may write to the diagnostic channel.</summary>
internal static class GatewayHttpLogText
{
    /// <summary>Returns the request URI without user information, query, or fragment.</summary>
    /// <param name="request">The outgoing Gateway request.</param>
    /// <returns>The scheme, authority, and path, or an empty string when the request has no absolute URI.</returns>
    internal static string Uri(HttpRequestMessage request)
        => request.RequestUri is { IsAbsoluteUri: true } uri
            ? uri.GetComponents(UriComponents.SchemeAndServer | UriComponents.Path, UriFormat.UriEscaped)
            : string.Empty;
}
