using Microsoft.Extensions.Http.Logging;
using Microsoft.Extensions.Logging;

namespace Hexalith.McpCli.Hosting;

/// <summary>
/// Logs the start and end of the whole Gateway request pipeline like the default client logger, but writes no
/// exception for a failed request: transport exceptions can quote downstream response content.
/// </summary>
/// <param name="logger">The logger for the client's <c>LogicalHandler</c> category.</param>
internal sealed partial class GatewayPipelineHttpLogger(ILogger logger) : IHttpClientLogger
{
    /// <inheritdoc />
    public object? LogRequestStart(HttpRequestMessage request)
    {
        ArgumentNullException.ThrowIfNull(request);
        LogStart(logger, request.Method, GatewayHttpLogText.Uri(request));
        return null;
    }

    /// <inheritdoc />
    public void LogRequestStop(object? context, HttpRequestMessage request, HttpResponseMessage response, TimeSpan elapsed)
    {
        ArgumentNullException.ThrowIfNull(response);
        LogEnd(logger, elapsed.TotalMilliseconds, (int)response.StatusCode);
    }

    /// <inheritdoc />
    public void LogRequestFailed(object? context, HttpRequestMessage request, HttpResponseMessage? response,
        Exception exception, TimeSpan elapsed)
        => LogFailed(logger, elapsed.TotalMilliseconds);

    [LoggerMessage(EventId = 100, EventName = "RequestPipelineStart", Level = LogLevel.Information,
        Message = "Start processing HTTP request {HttpMethod} {Uri}")]
    private static partial void LogStart(ILogger logger, HttpMethod httpMethod, string uri);

    [LoggerMessage(EventId = 101, EventName = "RequestPipelineEnd", Level = LogLevel.Information,
        Message = "End processing HTTP request after {ElapsedMilliseconds}ms - {StatusCode}")]
    private static partial void LogEnd(ILogger logger, double elapsedMilliseconds, int statusCode);

    [LoggerMessage(EventId = 104, EventName = "RequestPipelineFailed", Level = LogLevel.Information,
        Message = "HTTP request failed after {ElapsedMilliseconds}ms")]
    private static partial void LogFailed(ILogger logger, double elapsedMilliseconds);
}
