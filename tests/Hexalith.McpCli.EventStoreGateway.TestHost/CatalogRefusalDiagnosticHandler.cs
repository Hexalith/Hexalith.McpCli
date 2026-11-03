using Hexalith.EventStore.ServiceDefaults.Routing;

using Microsoft.AspNetCore.Diagnostics;

namespace Hexalith.McpCli.EventStoreGateway.TestHost;

/// <summary>Retains the SDK's refusal category and reason for isolated live-test diagnostics.</summary>
internal sealed class CatalogRefusalDiagnosticHandler(ILogger<CatalogRefusalDiagnosticHandler> logger) : IExceptionHandler
{
    /// <inheritdoc/>
    public ValueTask<bool> TryHandleAsync(HttpContext httpContext, Exception exception, CancellationToken cancellationToken)
    {
        if (exception is RouteCatalogUnavailableException refusal)
            logger.LogWarning("Isolated catalog refusal: Category={Category}, Reason={Reason}", refusal.Category, refusal.Message);
        return ValueTask.FromResult(false);
    }
}
