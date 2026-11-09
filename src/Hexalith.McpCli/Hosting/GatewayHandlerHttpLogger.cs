using Microsoft.Extensions.Http.Logging;
using Microsoft.Extensions.Logging;

namespace Hexalith.McpCli.Hosting;

/// <summary>
/// Logs the request sent to and the response headers received from the Gateway like the default client logger, but
/// writes no exception for a failed request: transport exceptions can quote downstream response content.
/// </summary>
/// <param name="logger">The logger for the client's <c>ClientHandler</c> category.</param>
internal sealed partial class GatewayHandlerHttpLogger(ILogger logger) : IHttpClientLogger
{
    /// <inheritdoc />
    public object? LogRequestStart(HttpRequestMessage request)
    {
        ArgumentNullException.ThrowIfNull(request);
        LogSending(logger, request.Method, GatewayHttpLogText.Uri(request));
        return null;
    }

    /// <inheritdoc />
    public void LogRequestStop(object? context, HttpRequestMessage request, HttpResponseMessage response, TimeSpan elapsed)
    {
        ArgumentNullException.ThrowIfNull(response);
        LogReceived(logger, elapsed.TotalMilliseconds, (int)response.StatusCode);
    }

    /// <inheritdoc />
    public void LogRequestFailed(object? context, HttpRequestMessage request, HttpResponseMessage? response,
        Exception exception, TimeSpan elapsed)
        => LogFailed(logger, elapsed.TotalMilliseconds);

    [LoggerMessage(EventId = 100, EventName = "RequestStart", Level = LogLevel.Information,
        Message = "Sending HTTP request {HttpMethod} {Uri}")]
    private static partial void LogSending(ILogger logger, HttpMethod httpMethod, string uri);

    [LoggerMessage(EventId = 101, EventName = "RequestEnd", Level = LogLevel.Information,
        Message = "Received HTTP response headers after {ElapsedMilliseconds}ms - {StatusCode}")]
    private static partial void LogReceived(ILogger logger, double elapsedMilliseconds, int statusCode);

    [LoggerMessage(EventId = 104, EventName = "RequestFailed", Level = LogLevel.Information,
        Message = "HTTP request failed after {ElapsedMilliseconds}ms")]
    private static partial void LogFailed(ILogger logger, double elapsedMilliseconds);
}
