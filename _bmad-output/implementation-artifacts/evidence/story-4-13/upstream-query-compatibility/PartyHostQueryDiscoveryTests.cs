using System.Net;
using System.Net.Http.Json;
using System.Text.Json;

using Hexalith.EventStore.Client.Projections;
using Hexalith.EventStore.Contracts.Queries;
using Hexalith.EventStore.DomainService;
using Hexalith.EventStore.Queries;
using Hexalith.EventStore.Server.Pipeline.Queries;
using Hexalith.EventStore.Server.Queries;
using Hexalith.EventStore.ServiceDefaults.Authentication;
using Hexalith.Parties.Contracts.Models;
using Hexalith.Parties.Contracts.ValueObjects;
using Hexalith.Parties.Projections.Configuration;
using Hexalith.Parties.Projections.Models;

using Microsoft.AspNetCore.TestHost;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;
using Microsoft.Extensions.Logging.Abstractions;

using NSubstitute;

using Shouldly;

namespace Hexalith.Parties.Tests.Gateway;

/// <summary>Proves the actual host advertises and executes the approved actor-bearing query contracts.</summary>
public sealed class PartyHostQueryDiscoveryTests
{
    private static readonly JsonSerializerOptions s_wireOptions = new(JsonSerializerDefaults.Web);

    /// <summary>Query capabilities come from the production host assembly scan, without test handler registration.</summary>
    [Fact]
    public async Task ActualHostDiscoversAndAdvertisesApprovedQueryHandlersAsync()
    {
        using var factory = new PartiesProcessTestFactory();
        using HttpClient client = factory.CreateAuthenticatedClient(EventStoreWorkloadOperations.DomainServiceMetadata);
        using HttpResponseMessage response = await client.PostAsJsonAsync("/admin/operational-index-metadata",
            new AdminOperationalIndexMetadata.Request(["party"]), TestContext.Current.CancellationToken);

        response.StatusCode.ShouldBe(HttpStatusCode.OK);
        AdminOperationalIndexMetadata.Response metadata = (await response.Content.ReadFromJsonAsync<AdminOperationalIndexMetadata.Response>(
            TestContext.Current.CancellationToken)).ShouldNotBeNull();
        string[] advertised = metadata.Domains.Single(domain => domain.Domain == "party").QueryTypes.ToArray();
        using IServiceScope scope = factory.Services.CreateScope();
        IDomainQueryHandler[] handlers = scope.ServiceProvider.GetServices<IDomainQueryHandler>().ToArray();
        foreach (string queryType in new[] { "PartyDetail", "PartyIndex", "PartySearch" })
        {
            advertised.Count(candidate => candidate == queryType).ShouldBe(1);
            handlers.Count(handler => handler.Domain == "party" && handler.QueryType == queryType).ShouldBe(1);
        }
    }

    /// <summary>Legacy actor routing fields cannot divert an advertised query away from authenticated SDK handlers.</summary>
    /// <param name="wire">The unchanged gateway request shape used by approved Contracts 1.5.1.</param>
    /// <param name="expectedIdPath">The path to the returned canonical identifier.</param>
    [Theory]
    [InlineData("""{"tenant":"tenant-a","domain":"party","aggregateId":"party-story49","queryType":"PartyDetail","projectionType":"party-detail","projectionActorType":"PartyDetailProjectionQueryActor","payload":{"PartyId":"party-story49"},"entityId":"party-story49"}""", "id")]
    [InlineData("""{"tenant":"tenant-a","domain":"party","aggregateId":"parties","queryType":"PartyIndex","projectionType":"party-index","projectionActorType":"PartyIndexProjectionQueryActor","entityId":"parties","payload":{"Type":"Person","Active":true,"CreatedAfter":"2026-01-01T00:00:00Z"},"paging":{"pageSize":2,"offset":0}}""", "items")]
    [InlineData("""{"tenant":"tenant-a","domain":"party","aggregateId":"parties","queryType":"PartySearch","projectionType":"party-index","projectionActorType":"PartyIndexProjectionQueryActor","entityId":"parties","payload":{"Query":" Ada ","Type":"Person","Active":true},"paging":{"pageSize":2,"offset":0}}""", "search")]
    public async Task ApprovedOldWireUsesDiscoveredHandlersAndCanonicalReadModelsAsync(string wire, string expectedIdPath)
    {
        CancellationToken cancellationToken = TestContext.Current.CancellationToken;
        IReadModelStore store = CanonicalReadModels();
        using var original = new PartiesProcessTestFactory();
        using var factory = original.WithWebHostBuilder(builder => builder.ConfigureTestServices(services =>
        {
            // Replace only persistence. Handler discovery, metadata, authentication and query DI stay real.
            services.RemoveAll<IReadModelStore>();
            services.AddSingleton(store);
        }));
        using HttpClient metadataClient = factory.CreateClient();
        string metadataAssertion = (await factory.Services.GetRequiredService<IWorkloadAssertionIssuer>()
            .IssueAsync(new WorkloadAssertionRequest("parties", EventStoreWorkloadOperations.DomainServiceMetadata), cancellationToken))!;
        metadataClient.DefaultRequestHeaders.Add(DaprAppChannelToken.HeaderName, PartiesProcessTestFactory.ChannelToken);
        metadataClient.DefaultRequestHeaders.Add(EventStoreWorkloadAuthenticationDefaults.AssertionHeaderName, metadataAssertion);
        using HttpResponseMessage metadataResponse = await metadataClient.PostAsJsonAsync("/admin/operational-index-metadata",
            new AdminOperationalIndexMetadata.Request(["party"]), cancellationToken);
        metadataResponse.StatusCode.ShouldBe(HttpStatusCode.OK);
        AdminOperationalIndexMetadata.Response metadata = (await metadataResponse.Content
            .ReadFromJsonAsync<AdminOperationalIndexMetadata.Response>(cancellationToken)).ShouldNotBeNull();
        string[] queryTypes = metadata.Domains.Single(domain => domain.Domain == "party").QueryTypes.ToArray();
        SubmitQueryRequest request = JsonSerializer.Deserialize<SubmitQueryRequest>(wire, s_wireOptions).ShouldNotBeNull();
        queryTypes.ShouldContain(request.QueryType);
        request.ProjectionActorType.ShouldNotBeNullOrWhiteSpace();

        using HttpClient queryClient = factory.CreateClient();
        string queryAssertion = (await factory.Services.GetRequiredService<IWorkloadAssertionIssuer>()
            .IssueAsync(new WorkloadAssertionRequest("parties", EventStoreWorkloadOperations.DomainServiceQuery), cancellationToken))!;
        queryClient.DefaultRequestHeaders.Add(DaprAppChannelToken.HeaderName, PartiesProcessTestFactory.ChannelToken);
        queryClient.DefaultRequestHeaders.Add(EventStoreWorkloadAuthenticationDefaults.AssertionHeaderName, queryAssertion);
        IDomainQueryHandlerRegistry registry = Substitute.For<IDomainQueryHandlerRegistry>();
        registry.SupportsQueryAsync("party", request.QueryType, Arg.Any<CancellationToken>())
            .Returns(queryTypes.Contains(request.QueryType, StringComparer.Ordinal));
        IDomainQueryInvoker invoker = Substitute.For<IDomainQueryInvoker>();
        invoker.InvokeAsync(Arg.Any<QueryEnvelope>(), Arg.Any<CancellationToken>()).Returns(async call =>
        {
            using HttpResponseMessage response = await queryClient.PostAsJsonAsync("/query", call.Arg<QueryEnvelope>(), call.Arg<CancellationToken>()).ConfigureAwait(false);
            response.StatusCode.ShouldBe(HttpStatusCode.OK);
            return (await response.Content.ReadFromJsonAsync<QueryResult>(call.Arg<CancellationToken>()).ConfigureAwait(false)).ShouldNotBeNull();
        });
        IQueryRouter actorRouter = Substitute.For<IQueryRouter>();
        var router = new HandlerAwareQueryRouter(actorRouter, registry, invoker, NullLogger<HandlerAwareQueryRouter>.Instance);
        var query = new SubmitQuery(request.Tenant, request.Domain, request.AggregateId, request.QueryType,
            JsonSerializer.SerializeToUtf8Bytes(request.Payload!.Value), "01J9MZHXT3RKM0VWXRXGSJDATK", "vector-admin",
            request.EntityId, request.ProjectionType, request.ProjectionActorType, Paging: request.Paging);

        QueryRouterResult result = await router.RouteQueryAsync(query, cancellationToken);

        result.Success.ShouldBeTrue();
        result.ProjectionType.ShouldBe(request.ProjectionType);
        JsonElement payload = result.Payload!.Value;
        string identifier = expectedIdPath == "id" ? payload.GetProperty("id").GetString()!
            : expectedIdPath == "search" ? payload.GetProperty("items")[0].GetProperty("party").GetProperty("id").GetString()!
            : payload.GetProperty("items")[0].GetProperty("id").GetString()!;
        identifier.ShouldBe("party-story49");
        if (request.Paging is not null)
        {
            payload.GetProperty("pageSize").GetInt32().ShouldBe(2);
            payload.GetProperty("totalCount").GetInt32().ShouldBe(1);
            result.Metadata!.Paging!.PageSize.ShouldBe(2);
        }
        await invoker.Received(1).InvokeAsync(Arg.Any<QueryEnvelope>(), Arg.Any<CancellationToken>());
        await actorRouter.DidNotReceive().RouteQueryAsync(Arg.Any<SubmitQuery>(), Arg.Any<CancellationToken>());
    }

    private static IReadModelStore CanonicalReadModels()
    {
        DateTimeOffset now = DateTimeOffset.UtcNow;
        IReadModelStore store = Substitute.For<IReadModelStore>();
        store.GetAsync<PartyDetailSdkReadModel>("statestore", PartySdkReadModelAddresses.Detail("tenant-a", "party-story49"), Arg.Any<CancellationToken>())
            .Returns(new ReadModelEntry<PartyDetailSdkReadModel>(new PartyDetailSdkReadModel
            {
                Detail = new PartyDetail
                {
                    Id = "party-story49", Type = PartyType.Person, IsActive = true,
                    DisplayName = "Ada Lovelace", SortName = "Lovelace, Ada", CreatedAt = now, LastModifiedAt = now,
                },
                ProjectedAt = now, ProjectionVersion = "1",
            }, "detail-etag"));
        store.GetAsync<PartyIndexSdkReadModel>("statestore", PartySdkReadModelAddresses.Index("tenant-a"), Arg.Any<CancellationToken>())
            .Returns(new ReadModelEntry<PartyIndexSdkReadModel>(new PartyIndexSdkReadModel
            {
                Entries = new Dictionary<string, PartyIndexEntry>
                {
                    ["party-story49"] = new PartyIndexEntry
                    {
                        Id = "party-story49", Type = PartyType.Person, IsActive = true,
                        DisplayName = "Ada Lovelace", SortName = "Lovelace, Ada", CreatedAt = now, LastModifiedAt = now,
                    },
                },
                ProjectedAt = now, ProjectionVersion = "1",
            }, "index-etag"));
        return store;
    }
}
