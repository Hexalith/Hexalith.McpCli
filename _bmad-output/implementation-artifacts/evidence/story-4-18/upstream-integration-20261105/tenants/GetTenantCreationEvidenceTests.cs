using System.Text.Json;

using Hexalith.EventStore.Client.Queries;
using Hexalith.EventStore.Contracts.Projections;
using Hexalith.EventStore.Contracts.Queries;
using Hexalith.EventStore.DomainService;
using Hexalith.EventStore.Testing.Fakes;
using Hexalith.Tenants.Authorization;
using Hexalith.Tenants.Contracts.Events;
using Hexalith.Tenants.Contracts.Events.Rejections;
using Hexalith.Tenants.Contracts.Queries;
using Hexalith.Tenants.Projections;
using Hexalith.Tenants.Queries.Handlers;
using Hexalith.Tenants.Server.Projections;
using Hexalith.Tenants.Telemetry;

using Microsoft.Extensions.Logging.Abstractions;

using NSubstitute;

using Shouldly;

using Xunit;

namespace Hexalith.Tenants.Server.Tests.Queries;

/// <summary>Separates a retained rejection checkpoint from evidence that a tenant was created.</summary>
public sealed class GetTenantCreationEvidenceTests
{
    private const string Tenant = "vector-create";

    /// <summary>Retains rejection checkpoints while requiring actual creation before a tenant read succeeds.</summary>
    [Fact]
    public async Task RejectedCreationRemainsAbsentUntilActualCreationAndLaterRejectionPreservesIt()
    {
        var store = new InMemoryReadModelStore();
        var projection = new TenantProjectionHandler(store);
        QueryResult before = await QueryAsync(store, administrator: true);
        before.Success.ShouldBeFalse();
        before.ErrorMessage.ShouldBe("Tenant not found");

        ProjectionEventDto rejection = Event(new InsufficientPermissionsRejection(Tenant, "nonmember", null, "CreateTenant"), 1);
        await projection.ProjectAsync(new("system", "tenants", Tenant, [rejection]), TestContext.Current.CancellationToken);
        TenantReadModel checkpoint = (await store.GetAsync<TenantReadModel>("statestore", "projection:tenants:" + Tenant, TestContext.Current.CancellationToken)).Value.ShouldNotBeNull();
        checkpoint.TenantId.ShouldBeEmpty();
        checkpoint.ProjectionVersion.ShouldBe("tenant-sequence:1");
        (await store.GetAsync<TenantIndexReadModel>("statestore", "projection:tenant-index:singleton", TestContext.Current.CancellationToken))
            .Value.ShouldNotBeNull().AggregateSequences[Tenant].ShouldBe(1);
        QueryResult rejected = await QueryAsync(store, administrator: true);
        rejected.Success.ShouldBeFalse();
        rejected.ErrorMessage.ShouldBe("Tenant not found");
        rejected.PayloadBytes.ShouldBeNull();

        ProjectionEventDto creation = Event(new TenantCreated(Tenant, "Created later", null, DateTimeOffset.UnixEpoch), 2);
        await projection.ProjectAsync(new("system", "tenants", Tenant, [rejection, creation]), TestContext.Current.CancellationToken);
        QueryResult created = await QueryAsync(store, administrator: true);
        created.Success.ShouldBeTrue();
        JsonElement detail = JsonSerializer.Deserialize<JsonElement>(created.PayloadBytes!);
        detail.GetProperty("tenantId").GetString().ShouldBe(Tenant);
        detail.GetProperty("name").GetString().ShouldBe("Created later");

        await projection.ProjectAsync(new("system", "tenants", Tenant, [rejection, creation,
            Event(new InsufficientPermissionsRejection(Tenant, "nonmember", null, "UpdateTenant"), 3)]), TestContext.Current.CancellationToken);
        QueryResult afterLaterRejection = await QueryAsync(store, administrator: true);
        afterLaterRejection.Success.ShouldBeTrue();
        JsonSerializer.Deserialize<JsonElement>(afterLaterRejection.PayloadBytes!).GetProperty("name").GetString().ShouldBe("Created later");
    }

    /// <summary>Preserves the existing forbidden response for a caller without administrator authority.</summary>
    [Fact]
    public async Task RejectionCheckpointDoesNotRevealExistenceToNonAdministrator()
    {
        var store = new InMemoryReadModelStore();
        QueryResult before = await QueryAsync(store, administrator: false);
        before.Success.ShouldBeFalse();
        before.ErrorMessage.ShouldBe("Forbidden");
        await new TenantProjectionHandler(store).ProjectAsync(new("system", "tenants", Tenant,
            [Event(new InsufficientPermissionsRejection(Tenant, "nonmember", null, "CreateTenant"), 1)]), TestContext.Current.CancellationToken);

        QueryResult after = await QueryAsync(store, administrator: false);
        after.Success.ShouldBeFalse();
        after.ErrorMessage.ShouldBe("Forbidden");
        after.PayloadBytes.ShouldBeNull();
    }

    private static async Task<QueryResult> QueryAsync(InMemoryReadModelStore store, bool administrator)
    {
        ITenantsGlobalAdministratorAuthority authority = Substitute.For<ITenantsGlobalAdministratorAuthority>();
        authority.IsCurrentGlobalAdministratorAsync(Arg.Any<string>(), Arg.Any<CancellationToken>()).Returns(administrator);
        var handler = new GetTenantQueryHandler(store, authority, Substitute.For<IQueryCursorCodec>(),
            new TenantTelemetry(new EventStoreDomainDiagnostics("tenants")), NullLogger<GetTenantQueryHandler>.Instance);
        return await handler.ExecuteAsync(new QueryEnvelope(Tenant, GetTenantQuery.Domain, Tenant,
            GetTenantQuery.QueryType, [], "query-correlation", "principal", Tenant, isGlobalAdmin: true), TestContext.Current.CancellationToken);
    }

    private static ProjectionEventDto Event(object payload, long sequence)
        => new(payload.GetType().FullName!, JsonSerializer.SerializeToUtf8Bytes(payload, payload.GetType()),
            "json", sequence, DateTimeOffset.UnixEpoch, "projection-correlation", "message-" + sequence, "actor");
}
