using System.Net.Http.Headers;
using System.Text.Json;

using Hexalith.Commons.UniqueIds;
using Hexalith.EventStore.Client.Gateway;
using Hexalith.EventStore.Contracts.Commands;
using Hexalith.EventStore.Contracts.Queries;
using Hexalith.Tenants.Contracts.Commands;
using Hexalith.Tenants.Contracts.Identity;
using Hexalith.Tenants.Contracts.Queries;

using Microsoft.Extensions.Options;

namespace Hexalith.McpCli.Integration.Tests;

/// <summary>Seeds the Projects list vector through real Tenant commands and waits for owner authorization.</summary>
internal static class NativeProjectsListSetup
{
    /// <summary>The tenant selected by the approved Projects list vector.</summary>
    internal const string TenantId = "tenant-a";

    /// <summary>The only subject that receives the Projects list credential.</summary>
    internal const string ReaderId = "mcpcli-project-list-reader";

    /// <summary>Returns a scoped credential after the Projects worker applies the persisted Tenant membership.</summary>
    internal static async Task<string> PrepareAsync(AspireTopologyFixture fixture, CancellationToken cancellationToken)
    {
        using var deadline = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        deadline.CancelAfter(TimeSpan.FromSeconds(90));
        using var administrator = CreateClient(fixture.GatewayEndpoint, fixture.CreateLiveIdentity());
        IEventStoreGatewayClient tenants = new EventStoreGatewayClient(administrator, Options.Create(new EventStoreGatewayClientOptions()));

        await SubmitAsync(CreateTenant.CommandType, new CreateTenant(TenantId, "Projects list fixture", null)).ConfigureAwait(false);
        var tenant = new SubmitQueryRequest(TenantId, GetTenantQuery.Domain, TenantId, GetTenantQuery.QueryType,
            GetTenantQuery.ProjectionType, JsonSerializer.SerializeToElement(new GetTenantQuery { TenantId = TenantId }));
        await RequireQueryAsync(tenants, tenant, 404, deadline.Token).ConfigureAwait(false);
        await SubmitAsync(AddUserToTenant.CommandType, new { TenantId, UserId = ReaderId, Role = "TenantReader" }).ConfigureAwait(false);

        string identity = fixture.CreateProjectsListIdentity();
        using var reader = CreateClient(fixture.GatewayEndpoint, identity);
        IEventStoreGatewayClient projects = new EventStoreGatewayClient(reader, Options.Create(new EventStoreGatewayClientOptions()));
        var list = new SubmitQueryRequest(TenantId, "projects", "projects", "Hexalith.Projects.Queries.ListProjects.v1",
            Payload: JsonSerializer.SerializeToElement(new { pageSize = 50 }));
        await RequireQueryAsync(projects, list, 403, deadline.Token).ConfigureAwait(false);
        return identity;

        async Task SubmitAsync(string commandType, object payload)
        {
            string message = UniqueIdHelper.GenerateSortableUniqueStringId();
            await tenants.SubmitCommandAsync(new SubmitCommandRequest(message, TenantPlatformScopes.Tenants, CreateTenant.Domain,
                TenantId, commandType, JsonSerializer.SerializeToElement(payload), message), deadline.Token).ConfigureAwait(false);
        }
    }

    private static HttpClient CreateClient(Uri endpoint, string identity) => new()
    {
        BaseAddress = endpoint,
        Timeout = TimeSpan.FromSeconds(15),
        DefaultRequestHeaders = { Authorization = new AuthenticationHeaderValue("Bearer", identity) },
    };

    private static async Task RequireQueryAsync(IEventStoreGatewayClient gateway, SubmitQueryRequest query,
        int pendingStatus, CancellationToken cancellationToken)
    {
        while (true)
        {
            try
            {
                EventStoreQueryResult response = await gateway.SubmitQueryAsync(query, cancellationToken: cancellationToken).ConfigureAwait(false);
                if (response.Payload.HasValue) return;
                throw new InvalidOperationException($"The fixture query {query.QueryType} did not return a successful document.");
            }
            catch (EventStoreGatewayException pending) when (pending.StatusCode == pendingStatus)
            {
                await Task.Delay(TimeSpan.FromMilliseconds(500), cancellationToken).ConfigureAwait(false);
            }
        }
    }
}
