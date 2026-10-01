using System.Text.Json;
using Hexalith.EventStore.Client.Gateway;
using Hexalith.EventStore.Contracts.Queries;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Core.Execution;
using Hexalith.McpCli.Core.Serialization;
using NSubstitute;
using Shouldly;
using QueryResult = Hexalith.McpCli.Core.Execution.QueryResult;
using Routing = global::Catalog.Routing.Contracts;
using StringContracts = global::Catalog.String.Contracts;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Verifies valid query routing, trusted tenant selection, and canonical results.</summary>
public sealed class QueryExecutionTests
{
    private const string ItemId = "01ARZ3NDEKTSV4RRFFQ69G5FAV";
    private const string OtherId = "01ARZ3NDEKTSV4RRFFQ69G5FAW";

    /// <summary>Accessor, explicit, and constant sources select exactly one declared route.</summary>
    [Theory]
    [InlineData("routing-fixture.interface-item", "{\"ItemId\":\"01ARZ3NDEKTSV4RRFFQ69G5FAV\"}", null, ItemId)]
    [InlineData("routing-fixture.interface-item", "{\"ItemId\":\"01ARZ3NDEKTSV4RRFFQ69G5FAV\"}", ItemId, ItemId)]
    [InlineData("routing-fixture.get-http2-status", "{}", ItemId, ItemId)]
    [InlineData("string-fixture.list-items", "{}", null, "items-index")]
    [InlineData("string-fixture.list-items", "{}", "other-index", "other-index")]
    public async Task AggregateSourcesUseDescriptorRoutingOnceAsync(
        string operation, string payload, string? explicitId, string expectedId)
    {
        IEventStoreGatewayClient gateway = CreateGateway();
        OperationOutcome outcome = await Create(gateway).ExecuteAsync(
            new RunQueryArguments(operation, payload, AggregateId: explicitId), Context("session-tenant"),
            TestContext.Current.CancellationToken);

        outcome.Error.ShouldBeNull();
        bool isString = operation.StartsWith("string-fixture.", StringComparison.Ordinal);
        string tenant = isString ? "fixed-tenant" : "session-tenant";
        string wire = isString ? "list-items-wire"
            : operation == "routing-fixture.interface-item" ? "interface-item-wire" : "get-http2-status";
        using JsonDocument expectedPayload = JsonDocument.Parse(payload);
        var expected = new SubmitQueryRequest(tenant, isString ? "string-fixture" : "routing", expectedId,
            wire, isString ? "string-items" : "routing-items", expectedPayload.RootElement, ProjectionActorType:
                operation == "routing-fixture.interface-item" ? "RoutingProjectionActor" : null);
        AssertRequest(gateway, expected);
        AssertResult(outcome, operation, tenant, "{\"items\":[]}");
    }

    /// <summary>Conflicting explicit/accessor values and missing aggregate sources fail before submission.</summary>
    [Theory]
    [InlineData("routing-fixture.interface-item", "{\"ItemId\":\"01ARZ3NDEKTSV4RRFFQ69G5FAV\"}", OtherId)]
    [InlineData("routing-fixture.get-http2-status", "{}", null)]
    public async Task AggregateRefusalsMakeZeroGatewayCallsAsync(string operation, string payload, string? explicitId)
    {
        IEventStoreGatewayClient gateway = CreateGateway();
        OperationOutcome outcome = await Create(gateway).ExecuteAsync(
            new RunQueryArguments(operation, payload, AggregateId: explicitId), Context("session-tenant"),
            TestContext.Current.CancellationToken);

        AssertRefusal(outcome, gateway, "/aggregateId");
    }

    /// <summary>A fixed tenant wins over session state and permits only a matching per-call tenant.</summary>
    [Theory]
    [InlineData(null, null, false)]
    [InlineData("session-tenant", null, false)]
    [InlineData("session-tenant", null, true)]
    [InlineData("session-tenant", "fixed-tenant", false)]
    [InlineData("session-tenant", "fixed-tenant", true)]
    [InlineData(null, "fixed-tenant", false)]
    public async Task FixedTenantWinsAsync(string? sessionTenant, string? callTenant, bool allowOverride)
    {
        IEventStoreGatewayClient gateway = CreateGateway();
        OperationOutcome outcome = await Create(gateway).ExecuteAsync(
            new RunQueryArguments("string-fixture.list-items", "{}", Tenant: callTenant),
            Context(sessionTenant, allowOverride), TestContext.Current.CancellationToken);

        outcome.Error.ShouldBeNull();
        AssertRequest(gateway, new SubmitQueryRequest("fixed-tenant", "string-fixture", "items-index",
            "list-items-wire", "string-items", JsonSerializer.SerializeToElement(new { })));
        AssertResult(outcome, "string-fixture.list-items", "fixed-tenant", "{\"items\":[]}");
    }

    /// <summary>Without a fixed tenant, per-call selection respects the operator override gate.</summary>
    [Theory]
    [InlineData("session-tenant", null, false, "session-tenant")]
    [InlineData("session-tenant", null, true, "session-tenant")]
    [InlineData("session-tenant", "session-tenant", false, "session-tenant")]
    [InlineData("session-tenant", "session-tenant", true, "session-tenant")]
    [InlineData(null, "call-tenant", false, "call-tenant")]
    [InlineData(null, "call-tenant", true, "call-tenant")]
    [InlineData("session-tenant", "call-tenant", true, "call-tenant")]
    public async Task SessionAndPerCallTenantsRespectOverrideAsync(
        string? sessionTenant, string? callTenant, bool allowOverride, string expectedTenant)
    {
        IEventStoreGatewayClient gateway = CreateGateway();
        OperationOutcome outcome = await Create(gateway).ExecuteAsync(
            new RunQueryArguments("routing-fixture.get-http2-status", "{}", Tenant: callTenant, AggregateId: ItemId),
            Context(sessionTenant, allowOverride), TestContext.Current.CancellationToken);

        outcome.Error.ShouldBeNull();
        AssertRequest(gateway, new SubmitQueryRequest(expectedTenant, "routing", ItemId, "get-http2-status",
            "routing-items", JsonSerializer.SerializeToElement(new { })));
        AssertResult(outcome, "routing-fixture.get-http2-status", expectedTenant, "{\"items\":[]}");
    }

    /// <summary>Missing and disallowed tenants fail closed even when the aggregate is valid.</summary>
    [Theory]
    [InlineData("string-fixture.list-items", null, "other-tenant", false)]
    [InlineData("string-fixture.list-items", "session-tenant", "other-tenant", true)]
    [InlineData("routing-fixture.get-http2-status", "session-tenant", "other-tenant", false)]
    [InlineData("routing-fixture.get-http2-status", null, null, false)]
    [InlineData("routing-fixture.get-http2-status", null, null, true)]
    public async Task TenantRefusalsMakeZeroGatewayCallsAsync(
        string operation, string? sessionTenant, string? callTenant, bool allowOverride)
    {
        IEventStoreGatewayClient gateway = CreateGateway();
        OperationOutcome outcome = await Create(gateway).ExecuteAsync(
            new RunQueryArguments(operation, "{}", Tenant: callTenant, AggregateId: ItemId),
            Context(sessionTenant, allowOverride), TestContext.Current.CancellationToken);

        AssertRefusal(outcome, gateway, "/tenant");
    }

    /// <summary>Object and absent gateway payloads retain all required fields without synthesizing metadata.</summary>
    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task ResultsHaveExactlyRequiredFieldsAsync(bool nullPayload)
    {
        IEventStoreGatewayClient gateway = CreateGateway(nullPayload);
        OperationOutcome outcome = await Create(gateway).ExecuteAsync(
            new RunQueryArguments("string-fixture.list-items", "{}"), Context(null),
            TestContext.Current.CancellationToken);

        outcome.Error.ShouldBeNull();
        AssertResult(outcome, "string-fixture.list-items", "fixed-tenant", nullPayload ? "null" : "{\"items\":[]}");
        AssertRequest(gateway, new SubmitQueryRequest("fixed-tenant", "string-fixture", "items-index",
            "list-items-wire", "string-items", JsonSerializer.SerializeToElement(new { })));
    }

    private static IEventStoreGatewayClient CreateGateway(bool nullPayload = false)
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        gateway.SubmitQueryAsync(Arg.Any<SubmitQueryRequest>(), Arg.Any<string?>(), Arg.Any<CancellationToken>())
            .Returns(Task.FromResult(new EventStoreQueryResult("01J9MZHXT3RKM0VWXRXGSJDATK",
                nullPayload ? null : JsonSerializer.SerializeToElement(new { items = Array.Empty<string>() }),
                false, null)));
        return gateway;
    }

    private static IOperationExecutor Create(IEventStoreGatewayClient gateway)
        => new OperationExecutor(new CatalogProvider(
            () => [typeof(Routing.Module).Assembly, typeof(StringContracts.Module).Assembly],
            new RecordingLogger<CatalogProvider>()), new ExecutionAvailability(false, true), gateway, strict: false);

    private static EnvelopeContext Context(string? tenant, bool allowOverride = false)
        => new(tenant, null, allowOverride, new HashSet<string>());

    private static void AssertRequest(IEventStoreGatewayClient gateway, SubmitQueryRequest expected)
    {
        NSubstitute.Core.ICall call = gateway.ReceivedCalls().ShouldHaveSingleItem();
        call.GetMethodInfo().Name.ShouldBe(nameof(IEventStoreGatewayClient.SubmitQueryAsync));
        object?[] arguments = call.GetArguments();
        SubmitQueryRequest actual = arguments[0].ShouldBeOfType<SubmitQueryRequest>();
        JsonElement.DeepEquals(JsonSerializer.SerializeToElement(actual, McpCliJson.Result),
            JsonSerializer.SerializeToElement(expected, McpCliJson.Result)).ShouldBeTrue();
        arguments[1].ShouldBeNull();
        arguments[2].ShouldBe(TestContext.Current.CancellationToken);
    }

    private static void AssertResult(OperationOutcome outcome, string operation, string tenant, string document)
    {
        QueryResult result = outcome.Document.ShouldBeOfType<QueryResult>();
        JsonElement actual = JsonSerializer.SerializeToElement(result, McpCliJson.Result);
        using JsonDocument expected = JsonDocument.Parse(
            $$"""{"operation":"{{operation}}","tenant":"{{tenant}}","document":{{document}}}""");
        JsonElement.DeepEquals(actual, expected.RootElement).ShouldBeTrue();
    }

    private static void AssertRefusal(OperationOutcome outcome, IEventStoreGatewayClient gateway, string path)
    {
        outcome.Document.ShouldBeNull();
        outcome.Error.ShouldNotBeNull().Code.ShouldBe("validation_failed");
        outcome.Error.Violations.ShouldNotBeNull().ShouldHaveSingleItem().Path.ShouldBe(path);
        gateway.ReceivedCalls().ShouldBeEmpty();
    }
}
