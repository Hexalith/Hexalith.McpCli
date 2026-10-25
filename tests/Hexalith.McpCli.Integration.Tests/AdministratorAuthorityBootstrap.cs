using System.Text.Json;

using Hexalith.EventStore.Client.Gateway;
using Hexalith.EventStore.Contracts.Queries;
using Hexalith.Tenants.Contracts.Queries;

using Microsoft.Extensions.Options;

namespace Hexalith.McpCli.Integration.Tests;

/// <summary>Waits for persisted bootstrap authority independently of resource liveness.</summary>
internal static class AdministratorAuthorityBootstrap
{
    /// <summary>The maximum duration of the privileged persisted-membership observation.</summary>
    internal static readonly TimeSpan RequestTimeout = TimeSpan.FromSeconds(60);

    /// <summary>Polls only the privileged Query until it returns the expected persisted administrator.</summary>
    internal static async Task RequireAsync(HttpClient http, string administratorId, CancellationToken cancellationToken)
    {
        IEventStoreGatewayClient gateway = new EventStoreGatewayClient(http, Options.Create(new EventStoreGatewayClientOptions()));
        var request = new SubmitQueryRequest("system", GetGlobalAdministratorsQuery.Domain, "global-administrators",
            GetGlobalAdministratorsQuery.QueryType, GetGlobalAdministratorsQuery.ProjectionType);
        using var deadline = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        deadline.CancelAfter(RequestTimeout);
        string failure = "No successful privileged administrator document.";
        try
        {
            while (true)
            {
                try
                {
                    EventStoreQueryResult result = await gateway.SubmitQueryAsync(request, cancellationToken: deadline.Token).ConfigureAwait(false);
                    if (result.Payload is { } payload && payload.TryGetProperty("items", out JsonElement items)
                        && items.EnumerateArray().Any(item => item.GetProperty("userId").GetString() == administratorId))
                        return;
                    failure = "Privileged query omitted the persisted bootstrap administrator.";
                }
                catch (EventStoreGatewayException exception)
                {
                    failure = $"Privileged query HTTP {exception.StatusCode}.";
                }
                await Task.Delay(TimeSpan.FromMilliseconds(500), deadline.Token).ConfigureAwait(false);
            }
        }
        catch (OperationCanceledException exception) when (!cancellationToken.IsCancellationRequested)
        {
            throw new TimeoutException($"Bootstrap authority did not converge in 60 seconds. {failure}", exception);
        }
    }
}
