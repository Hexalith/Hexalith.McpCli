using System.Text.Json;
using Catalog.Routing.Contracts;
using Hexalith.EventStore.Client.Gateway;
using Hexalith.EventStore.Contracts.Commands;
using Hexalith.EventStore.Contracts.Queries;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Core.Execution;
using Hexalith.McpCli.Core.Serialization;
using NSubstitute;
using Shouldly;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Verifies trusted envelope filling for converter-backed value objects.</summary>
public sealed class EnvelopeValueObjectTests
{
    private const string ItemId = "01ARZ3NDEKTSV4RRFFQ69G5FAV";
    private const string Correlation = "01J9MZHXT3RKM0VWXRXGSJDATK";

    /// <summary>The computed aggregate accessor materializes typed members only after trusted values are filled.</summary>
    [Fact]
    public async Task CommandMaterializesEnvelopeValueObjectsAfterFillingAsync()
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        SubmitCommandRequest? captured = null;
        gateway.SubmitCommandAsync(Arg.Do<SubmitCommandRequest>(request => captured = request), Arg.Any<CancellationToken>())
            .Returns(Task.FromResult(new SubmitCommandResponse(Correlation)));
        var provider = new CatalogProvider(() => [typeof(ComputedEnvelopeCommand).Assembly], new RecordingLogger<CatalogProvider>());
        var executor = new OperationExecutor(provider, new ExecutionAvailability(false, true), gateway, strict: false);

        OperationOutcome outcome = await executor.ExecuteAsync(new SendCommandArguments(
            "routing-fixture.computed-envelope", $$$"""{"ItemId":"{{{ItemId}}}","Correlation":42,"Idempotency":{}}""",
            CorrelationId: Correlation, IdempotencyKey: Correlation), Context(), TestContext.Current.CancellationToken);

        outcome.Error.ShouldBeNull();
        captured.ShouldNotBeNull();
        ModuleDescriptor module = provider.Get(false).Catalog!.Modules.Single();
        ComputedEnvelopeCommand command = captured.Payload.Deserialize<ComputedEnvelopeCommand>(module.ModulePayloadOptions).ShouldNotBeNull();
        command.Tenant.ShouldNotBeNull().Value.ShouldBe("acme");
        command.Actor.ShouldNotBeNull().Value.ShouldBe("operator-1");
        command.Correlation.ShouldNotBeNull().Value.ShouldBe(Correlation);
        command.Idempotency.ShouldNotBeNull().Value.ShouldBe(Correlation);
        command.AggregateId.ShouldBe(ItemId);
        captured.Tenant.ShouldBe("acme");
        captured.AggregateId.ShouldBe(ItemId);
        await gateway.Received(1).SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>());
    }

    /// <summary>Queries fill typed tenant members and submit their declared routing without a payload tenant.</summary>
    [Fact]
    public async Task QueryFillsEnvelopeValueObjectTenantAsync()
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        SubmitQueryRequest? captured = null;
        gateway.SubmitQueryAsync(Arg.Do<SubmitQueryRequest>(request => captured = request), Arg.Any<string?>(), Arg.Any<CancellationToken>())
            .Returns(Task.FromResult(new EventStoreQueryResult(Correlation,
                JsonSerializer.SerializeToElement(new { items = Array.Empty<string>() }), false, null)));
        IOperationExecutor executor = CreateQueryExecutor(gateway);

        OperationOutcome outcome = await executor.ExecuteAsync(new RunQueryArguments("envelope-values.value-object-envelope", "{}"),
            Context(), TestContext.Current.CancellationToken);

        outcome.Error.ShouldBeNull();
        captured.ShouldNotBeNull();
        captured.Tenant.ShouldBe("acme");
        captured.Payload!.Value.GetProperty("Tenant").GetString().ShouldBe("acme");
        captured.AggregateId.ShouldBe("items");
        await gateway.Received(1).SubmitQueryAsync(Arg.Any<SubmitQueryRequest>(), Arg.Any<string?>(), Arg.Any<CancellationToken>());
    }

    /// <summary>Typed tenants retain the same ownership guard and exact error document as string members.</summary>
    /// <param name="rawTenant">An untrusted JSON value supplied for the envelope-owned member.</param>
    [Theory]
    [InlineData("\"other\"")]
    [InlineData("null")]
    [InlineData("42")]
    [InlineData("{}")]
    public async Task QueryRejectsUntrustedTenantBeforeGatewayAsync(string rawTenant)
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        OperationOutcome outcome = await CreateQueryExecutor(gateway).ExecuteAsync(
            new RunQueryArguments("envelope-values.value-object-envelope", "{\"Tenant\":" + rawTenant + "}"),
            Context(), TestContext.Current.CancellationToken);

        outcome.Document.ShouldBeNull();
        JsonElement actual = JsonSerializer.SerializeToElement(new { error = outcome.Error }, McpCliJson.Result);
        using JsonDocument expected = JsonDocument.Parse("""
            {"error":{"code":"validation_failed","operation":"envelope-values.value-object-envelope","violations":[{"path":"/Tenant","message":"The payload tenant disagrees with the resolved tenant."}]}}
            """);
        JsonElement.DeepEquals(actual, expected.RootElement).ShouldBeTrue(actual.GetRawText());
        await gateway.DidNotReceive().SubmitQueryAsync(Arg.Any<SubmitQueryRequest>(), Arg.Any<string?>(), Arg.Any<CancellationToken>());
    }

    private static IOperationExecutor CreateQueryExecutor(IEventStoreGatewayClient gateway)
    {
        var provider = new CatalogProvider(() => [new InventoryCoverageContractsAssembly("envelope-values", typeof(ValueObjectEnvelopeQuery))],
            new RecordingLogger<CatalogProvider>());
        return new OperationExecutor(provider, new ExecutionAvailability(false, true), gateway, strict: false);
    }

    private static EnvelopeContext Context() => new("acme", "operator-1", false, new HashSet<string>());
}
