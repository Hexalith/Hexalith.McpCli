using Hexalith.EventStore.Client.Gateway;
using Hexalith.EventStore.Contracts.Queries;

namespace Hexalith.McpCli.Integration.Tests;

/// <summary>Bounds the single usability request independently of the platform's startup/liveness budget.</summary>
internal static class GatewaySmokeProbe
{
    /// <summary>The fixed maximum duration of the authenticated Gateway request.</summary>
    internal static readonly TimeSpan RequestTimeout = TimeSpan.FromSeconds(30);

    /// <summary>Executes exactly one Gateway query after the fixture has established resource liveness.</summary>
    internal static async Task<EventStoreQueryResult> ExecuteAsync(IEventStoreGatewayClient gateway, SubmitQueryRequest request, CancellationToken cancellationToken = default)
    {
        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        timeout.CancelAfter(RequestTimeout);
        try
        {
            return await gateway.SubmitQueryAsync(request, cancellationToken: timeout.Token).ConfigureAwait(false);
        }
        catch (OperationCanceledException exception) when (timeout.IsCancellationRequested && !cancellationToken.IsCancellationRequested)
        {
            throw new TimeoutException("Authenticated Gateway query exceeded 30 seconds after resource liveness passed. Check Gateway routing, sidecars and domain-service logs.", exception);
        }
        catch (EventStoreGatewayException exception)
        {
            throw new InvalidOperationException($"Authenticated Gateway query failed with HTTP {exception.StatusCode} after resource liveness passed. Check Gateway routing, authentication and domain-service logs.", exception);
        }
    }
}
