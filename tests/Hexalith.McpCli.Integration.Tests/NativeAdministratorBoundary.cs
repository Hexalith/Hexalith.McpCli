using System.Text.Json;

using Hexalith.Commons.UniqueIds;
using Hexalith.EventStore.Client.Gateway;
using Hexalith.EventStore.Contracts.Commands;
using Hexalith.EventStore.Contracts.Queries;
using Hexalith.Tenants.Contracts.Commands;
using Hexalith.Tenants.Contracts.Identity;
using Hexalith.Tenants.Contracts.Queries;

namespace Hexalith.McpCli.Integration.Tests;

/// <summary>Requires actual owner rejection of a signed nonmember hint and independent unchanged persisted tenant state.</summary>
internal static class NativeAdministratorBoundary
{
    /// <summary>Uses an existing exact tenant grant; this fresh smoke has never created the target.</summary>
    internal const string TargetTenant = "vector-create";

    /// <summary>Submits one bounded command and observes absence before and after with the real persisted administrator.</summary>
    internal static async Task RequireNonmemberRejectionAsync(IEventStoreGatewayClient nonmember, IEventStoreGatewayClient administrator,
        CancellationToken cancellationToken)
    {
        using var deadline = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        deadline.CancelAfter(TimeSpan.FromSeconds(90));
        var query = new SubmitQueryRequest(TargetTenant, GetTenantQuery.Domain, TargetTenant, GetTenantQuery.QueryType,
            GetTenantQuery.ProjectionType, JsonSerializer.SerializeToElement(new GetTenantQuery { TenantId = TargetTenant }));
        await RequireAbsentAsync().ConfigureAwait(false);
        string message = UniqueIdHelper.GenerateSortableUniqueStringId();
        var command = new SubmitCommandRequest(message, TenantPlatformScopes.Tenants, CreateTenant.Domain, TargetTenant,
            CreateTenant.CommandType, JsonSerializer.SerializeToElement(new CreateTenant(TargetTenant, "Rejected nonmember smoke", null)),
            message, IdempotencyKey: message);
        try
        {
            await nonmember.SubmitCommandAsync(command, deadline.Token).ConfigureAwait(false);
            throw new InvalidOperationException("A signed nonmember administrator hint created a tenant.");
        }
        catch (EventStoreGatewayException rejected) when (rejected.StatusCode == 422
            && (rejected.ReasonCode ?? rejected.Reason) == "insufficient-permissions-rejection") { }
        await RequireAbsentAsync().ConfigureAwait(false);

        async Task RequireAbsentAsync()
        {
            try
            {
                await administrator.SubmitQueryAsync(query, cancellationToken: deadline.Token).ConfigureAwait(false);
                throw new InvalidOperationException("The nonmember smoke target has persisted business state.");
            }
            // Bound SDK 4.1.0 QueryNotFoundExceptionHandler emits this stable projection-absence code.
            catch (EventStoreGatewayException missing) when (missing.StatusCode == 404
                && missing.ReasonCode == QueryProblemReasonCodes.ProjectionMissing) { }
        }
    }
}
