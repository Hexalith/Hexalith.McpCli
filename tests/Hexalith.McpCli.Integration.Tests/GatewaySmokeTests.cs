using System.Text.Json;
using System.Net;
using System.Net.Http.Headers;

using Hexalith.EventStore.Client.Gateway;
using Hexalith.EventStore.Contracts.Queries;
using Hexalith.EventStore.Testing.Integration;
using Hexalith.Tenants.Contracts.Queries;

using Microsoft.Extensions.Options;

namespace Hexalith.McpCli.Integration.Tests;

/// <summary>Separates resource liveness from a bounded authenticated Gateway usability proof.</summary>
[Collection("AspireTopology")]
[Trait("Category", "Integration")]
public sealed class GatewaySmokeTests(AspireTopologyFixture fixture)
{
    /// <summary>Requires an actual successful query document through the pinned Gateway client.</summary>
    [Fact]
    public async Task AuthenticatedQueryReturnsSuccessfulDocument()
    {
        fixture.SkipIfUnavailable();
        using HttpClient http = fixture.CreateAuthenticatedGatewayClient();
        IEventStoreGatewayClient gateway = new EventStoreGatewayClient(http, Options.Create(new EventStoreGatewayClientOptions()));
        var request = new SubmitQueryRequest("system", ListTenantsQuery.Domain, "index",
            ListTenantsQuery.QueryType, ListTenantsQuery.ProjectionType);
        AuthenticationHeaderValue validIdentity = http.DefaultRequestHeaders.Authorization!;
        await RequireUnauthorizedAsync(null);
        using HttpClient wrongKey = fixture.CreateAuthenticatedGatewayClient(invalidSignature: true);
        await RequireUnauthorizedAsync(wrongKey.DefaultRequestHeaders.Authorization);
        http.DefaultRequestHeaders.Authorization = validIdentity;
        await fixture.RequireAdministratorAuthorityAsync(TestContext.Current.CancellationToken).ConfigureAwait(true);
        EventStoreQueryResult result = await GatewaySmokeProbe.ExecuteAsync(gateway, request, TestContext.Current.CancellationToken).ConfigureAwait(true);

        Assert.False(result.IsNotModified);
        Assert.False(string.IsNullOrWhiteSpace(result.CorrelationId));
        Assert.True(result.Payload.HasValue, "The Gateway returned no successful query document.");
        JsonElement document = result.Payload.Value;
        Assert.Equal(JsonValueKind.Object, document.ValueKind);
        Assert.Equal(JsonValueKind.Array, document.GetProperty("items").ValueKind);
        Assert.Contains(document.GetProperty("hasMore").ValueKind, new[] { JsonValueKind.True, JsonValueKind.False });
        Assert.Contains(document.GetProperty("cursor").ValueKind, new[] { JsonValueKind.Null, JsonValueKind.String });

        async Task RequireUnauthorizedAsync(AuthenticationHeaderValue? identity)
        {
            http.DefaultRequestHeaders.Authorization = identity;
            using var deadline = CancellationTokenSource.CreateLinkedTokenSource(TestContext.Current.CancellationToken);
            deadline.CancelAfter(GatewaySmokeProbe.RequestTimeout);
            EventStoreGatewayException rejected = await Assert.ThrowsAsync<EventStoreGatewayException>(() =>
                gateway.SubmitQueryAsync(request, cancellationToken: deadline.Token));
            Assert.Equal((int)HttpStatusCode.Unauthorized, rejected.StatusCode);
        }

    }
}
