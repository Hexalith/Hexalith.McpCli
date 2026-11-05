using System.Text.Json;
using Hexalith.EventStore.Client.Queries;
using Hexalith.EventStore.Contracts.Projections;
using Hexalith.EventStore.Contracts.Queries;
using Hexalith.EventStore.DomainService;
using Hexalith.EventStore.Testing.Fakes;
using Hexalith.Tenants.Contracts.Events;
using Hexalith.Tenants.Contracts.Events.Rejections;
using Hexalith.Tenants.Contracts.Queries;
using Hexalith.Tenants.Projections;
using Hexalith.Tenants.Queries.Handlers;
using Hexalith.Tenants.Server.Projections;
using Hexalith.Tenants.Telemetry;
using Microsoft.Extensions.Logging.Abstractions;
using NSubstitute;

JsonElement Payload(QueryResult result) => result.PayloadBytes is { Length: > 0 } bytes ? JsonSerializer.Deserialize<JsonElement>(bytes) : default;
var store = new InMemoryReadModelStore();
var projection = new TenantProjectionHandler(store);
const string tenant = "vector-create";
ProjectionEventDto Event(object payload, long sequence) => new(payload.GetType().FullName!,
    JsonSerializer.SerializeToUtf8Bytes(payload, payload.GetType()), "json", sequence,
    DateTimeOffset.UnixEpoch, "probe-correlation", "probe-" + sequence, "probe-actor");
async Task<QueryResult> Query(bool administrator = true)
{
    var query = new GetTenantQueryHandler(store, new AdministratorAuthority(administrator),
        Substitute.For<IQueryCursorCodec>(), new TenantTelemetry(new EventStoreDomainDiagnostics("tenants")),
        NullLogger<GetTenantQueryHandler>.Instance);
    return await query.ExecuteAsync(new QueryEnvelope(tenant, GetTenantQuery.Domain, tenant,
        GetTenantQuery.QueryType, [], "probe-query", "administrator", tenant, isGlobalAdmin: true), default);
}
var before = await Query();
if (before.Success || before.ErrorMessage != "Tenant not found") throw new Exception("Expected initial tenant absence.");
var denied = Event(new InsufficientPermissionsRejection(tenant, "nonmember", null, "CreateTenant"), 1);
await projection.ProjectAsync(new("system", "tenants", tenant, [denied]));
var detail = (await store.GetAsync<TenantReadModel>("statestore", "projection:tenants:" + tenant)).Value!;
var rejected = await Query();
Console.WriteLine(JsonSerializer.Serialize(new { caseName = "rejection-only", detail, querySuccess = rejected.Success,
    error = rejected.ErrorMessage, payload = Payload(rejected).ValueKind == JsonValueKind.Undefined ? (JsonElement?)null : Payload(rejected) }));
if (rejected.Success || rejected.ErrorMessage != "Tenant not found") throw new Exception("Rejection-only projection is exposed as a tenant.");
var unauthorized = await Query(false);
if (unauthorized.Success || unauthorized.ErrorMessage != "Forbidden") throw new Exception("Nonmember existence concealment changed.");
await projection.ProjectAsync(new("system", "tenants", tenant,
    [denied, Event(new TenantCreated(tenant, "Created later", null, DateTimeOffset.UnixEpoch), 2)]));
var created = await Query();
if (!created.Success || Payload(created).GetProperty("tenantId").GetString() != tenant
    || Payload(created).GetProperty("name").GetString() != "Created later") throw new Exception("Creation after rejection failed.");
Console.WriteLine(JsonSerializer.Serialize(new { caseName = "creation-after-rejection", querySuccess = created.Success, payload = Payload(created) }));
await projection.ProjectAsync(new("system", "tenants", tenant, [denied,
    Event(new TenantCreated(tenant, "Created later", null, DateTimeOffset.UnixEpoch), 2),
    Event(new InsufficientPermissionsRejection(tenant, "nonmember", null, "UpdateTenant"), 3)]));
var stillExists = await Query();
if (!stillExists.Success || Payload(stillExists).GetProperty("name").GetString() != "Created later")
    throw new Exception("Rejection after creation hid an existing tenant.");
Console.WriteLine(JsonSerializer.Serialize(new { caseName = "rejection-after-creation", querySuccess = stillExists.Success, payload = Payload(stillExists) }));
