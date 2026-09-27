using System.Text.Json;
using Hexalith.EventStore.Client.Gateway;
using Hexalith.EventStore.Contracts.Commands;
using Hexalith.EventStore.Contracts.Queries;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Core.Execution;
using Hexalith.McpCli.Core.Serialization;
using Hexalith.McpCli.Sample.Contracts;
using NSubstitute;
using Shouldly;
using CoreQueryResult = Hexalith.McpCli.Core.Execution.QueryResult;
using StringContracts = global::Catalog.String.Contracts;
using Routing = global::Catalog.Routing.Contracts;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Checks Core preflight, envelope construction, and one-call gateway behavior.</summary>
public sealed class OperationExecutorTests
{
    private const string ItemId = "01ARZ3NDEKTSV4RRFFQ69G5FAV";
    private const string CorrelationId = "01J9MZHXT3RKM0VWXRXGSJDATK";

    /// <summary>An interface-routed command reaches the gateway once with its declared wire type.</summary>
    [Fact]
    public async Task CommandUsesDeclaredRoutingAndCanonicalResponseAsync()
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        SubmitCommandRequest? captured = null;
        gateway.SubmitCommandAsync(Arg.Do<SubmitCommandRequest>(request => captured = request), Arg.Any<CancellationToken>())
            .Returns(call => Task.FromResult(new SubmitCommandResponse(((SubmitCommandRequest)call[0]).CorrelationId!,
                JsonSerializer.SerializeToElement(new { accepted = true }), CorrelationId)));
        IOperationExecutor executor = Create(gateway, typeof(CreateItemCommand), hasGatewayUrl: true);

        OperationOutcome outcome = await executor.ExecuteAsync(
            new SendCommandArguments("sample.create-item", $$"""{"ItemId":"{{ItemId}}","Title":"Hello"}"""),
            Context(), TestContext.Current.CancellationToken);

        CommandResult result = outcome.Document.ShouldBeOfType<CommandResult>();
        outcome.Error.ShouldBeNull();
        captured.ShouldNotBeNull();
        captured.Domain.ShouldBe("sample");
        captured.CommandType.ShouldBe("create-item");
        captured.Tenant.ShouldBe("sample-tenant");
        captured.AggregateId.ShouldBe(ItemId);
        captured.Payload.GetProperty("Title").GetString().ShouldBe("Hello");
        captured.CorrelationId.ShouldBe(captured.MessageId);
        captured.IdempotencyKey.ShouldBeNull();
        result.MessageId.ShouldBe(CorrelationId);
        result.CorrelationId.ShouldBe(captured.MessageId);
        result.Status.ShouldBe("accepted");
        result.Result.ShouldNotBeNull();
        JsonElement json = JsonSerializer.SerializeToElement(result, McpCliJson.Result);
        json.TryGetProperty("idempotencyKey", out _).ShouldBeFalse();
        await gateway.Received(1).SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>());
    }

    /// <summary>Mapped tenant, actor, correlation, and key fields come from the trusted envelope.</summary>
    [Fact]
    public async Task CommandFillsMappedEnvelopeAndEscapedPropertyAsync()
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        SubmitCommandRequest? captured = null;
        gateway.SubmitCommandAsync(Arg.Do<SubmitCommandRequest>(request => captured = request), Arg.Any<CancellationToken>())
            .Returns(call => Task.FromResult(new SubmitCommandResponse(((SubmitCommandRequest)call[0]).CorrelationId!)));
        IOperationExecutor executor = Create(gateway, typeof(Routing.Module), hasGatewayUrl: true);
        var extensions = new Dictionary<string, string> { ["task-id"] = "abc" };
        var context = new EnvelopeContext("acme", "operator-1", false, new HashSet<string>(StringComparer.OrdinalIgnoreCase) { "task-id" });

        OperationOutcome outcome = await executor.ExecuteAsync(new SendCommandArguments(
            "routing-fixture.envelope-item", $$"""{"ItemId":"{{ItemId}}","tenant/~":"acme"}""",
            CorrelationId: CorrelationId, IdempotencyKey: CorrelationId, Extensions: extensions), context,
            TestContext.Current.CancellationToken);

        outcome.Error.ShouldBeNull();
        captured.ShouldNotBeNull();
        captured.Payload.GetProperty("tenant/~").GetString().ShouldBe("acme");
        captured.Payload.GetProperty("Actor").GetString().ShouldBe("operator-1");
        captured.Payload.GetProperty("Correlation").GetString().ShouldBe(CorrelationId);
        captured.Payload.GetProperty("Idempotency").GetString().ShouldBe(CorrelationId);
        captured.Extensions!["task-id"].ShouldBe("abc");
        outcome.Document.ShouldBeOfType<CommandResult>().IdempotencyKey.ShouldBe(CorrelationId);
    }

    /// <summary>Read-only mode is enforced before URL availability or gateway access.</summary>
    [Fact]
    public async Task ReadOnlyCommandFailsBeforeGatewayAsync()
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        IOperationExecutor executor = Create(gateway, typeof(CreateItemCommand), readOnly: true, hasGatewayUrl: false);

        OperationOutcome outcome = await executor.ExecuteAsync(
            new SendCommandArguments("sample.create-item", $$"""{"ItemId":"{{ItemId}}","Title":"Hello"}"""),
            Context(), TestContext.Current.CancellationToken);

        outcome.Error.ShouldNotBeNull().Code.ShouldBe("read_only");
        await gateway.DidNotReceive().SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>());
    }

    /// <summary>Kind mismatch wins over the read-only and missing-URL gates.</summary>
    [Fact]
    public async Task KindMismatchFailsBeforeAvailabilityAsync()
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        IOperationExecutor executor = Create(gateway, typeof(CreateItemCommand), readOnly: true, hasGatewayUrl: false);

        OperationOutcome outcome = await executor.ExecuteAsync(new RunQueryArguments("sample.create-item", "{}"),
            Context(), TestContext.Current.CancellationToken);

        outcome.Error.ShouldNotBeNull().Code.ShouldBe("validation_failed");
        outcome.Error.Violations!.Single().Path.ShouldBe("/operation");
        await gateway.DidNotReceive().SubmitQueryAsync(Arg.Any<SubmitQueryRequest>(), Arg.Any<string?>(), Arg.Any<CancellationToken>());
    }

    /// <summary>Malformed JSON and unknown members fail before command submission.</summary>
    [Theory]
    [InlineData("{", "/")]
    [InlineData("{\"ItemId\":\"01ARZ3NDEKTSV4RRFFQ69G5FAV\",\"Title\":\"x\",\"Unexpected\":1}", "/")]
    [InlineData("{\"ItemId\":\"01ARZ3NDEKTSV4RRFFQ69G5FAV\",\"ItemId\":\"01ARZ3NDEKTSV4RRFFQ69G5FAW\",\"Title\":\"x\"}", "/")]
    [InlineData("null", "/")]
    public async Task InvalidPayloadFailsBeforeGatewayAsync(string payload, string expectedPathPrefix)
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        IOperationExecutor executor = Create(gateway, typeof(CreateItemCommand), hasGatewayUrl: true);

        OperationOutcome outcome = await executor.ExecuteAsync(new SendCommandArguments("sample.create-item", payload),
            Context(), TestContext.Current.CancellationToken);

        outcome.Error.ShouldNotBeNull().Code.ShouldBe("validation_failed");
        outcome.Error.Violations.ShouldNotBeNull().ShouldContain(item => item.Path.StartsWith(expectedPathPrefix, StringComparison.Ordinal));
        await gateway.DidNotReceive().SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>());
    }

    /// <summary>Tenant and actor disagreements, absent keys, and disallowed extensions never reach the gateway.</summary>
    [Theory]
    [InlineData("{\"ItemId\":\"01ARZ3NDEKTSV4RRFFQ69G5FAV\",\"tenant/~\":\"other\"}", true, "/tenant~1~0")]
    [InlineData("{\"ItemId\":\"01ARZ3NDEKTSV4RRFFQ69G5FAV\",\"Actor\":\"other\"}", true, "/Actor")]
    [InlineData("{\"ItemId\":\"01ARZ3NDEKTSV4RRFFQ69G5FAV\"}", false, "/idempotencyKey")]
    public async Task EnvelopeViolationsFailBeforeGatewayAsync(string payload, bool supplyKey, string path)
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        IOperationExecutor executor = Create(gateway, typeof(Routing.Module), hasGatewayUrl: true);

        OperationOutcome outcome = await executor.ExecuteAsync(new SendCommandArguments(
            "routing-fixture.envelope-item", payload, IdempotencyKey: supplyKey ? CorrelationId : null),
            new EnvelopeContext("acme", "operator-1", false, new HashSet<string>()), TestContext.Current.CancellationToken);

        outcome.Error.ShouldNotBeNull().Code.ShouldBe("validation_failed");
        outcome.Error.Violations!.Single().Path.ShouldBe(path);
        await gateway.DidNotReceive().SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>());
    }

    /// <summary>Query paging uses the envelope and returned metadata stays in the result document.</summary>
    [Fact]
    public async Task QueryUsesGatewayRoutingAndPagingAsync()
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        SubmitQueryRequest? captured = null;
        gateway.SubmitQueryAsync(Arg.Do<SubmitQueryRequest>(request => captured = request), Arg.Any<string?>(), Arg.Any<CancellationToken>())
            .Returns(Task.FromResult(new EventStoreQueryResult(CorrelationId, JsonSerializer.SerializeToElement(new { title = "A" }), false, null)
            {
                Metadata = new QueryResponseMetadata(Paging: new QueryPagingMetadata(25, 0, "next", 2, true)),
            }));
        IOperationExecutor executor = Create(gateway, typeof(GetItemQuery), hasGatewayUrl: true);

        OperationOutcome outcome = await executor.ExecuteAsync(new RunQueryArguments(
            "sample.get-item", $$"""{"ItemId":"{{ItemId}}"}""", PageSize: 25, Offset: 0),
            Context(), TestContext.Current.CancellationToken);

        CoreQueryResult result = outcome.Document.ShouldBeOfType<CoreQueryResult>();
        outcome.Error.ShouldBeNull();
        captured.ShouldNotBeNull();
        captured.Domain.ShouldBe("sample");
        captured.QueryType.ShouldBe("get-item");
        captured.ProjectionType.ShouldBe("sample-items");
        captured.AggregateId.ShouldBe(ItemId);
        captured.Paging.ShouldNotBeNull().PageSize.ShouldBe(25);
        result.Paging.ShouldNotBeNull().NextCursor.ShouldBe("next");
        result.Document.ShouldNotBeNull().GetProperty("title").GetString().ShouldBe("A");
        await gateway.Received(1).SubmitQueryAsync(Arg.Any<SubmitQueryRequest>(), Arg.Any<string?>(), Arg.Any<CancellationToken>());
    }

    /// <summary>Cursor and offset conflict is rejected before any Gateway call.</summary>
    [Fact]
    public async Task QueryPagingConflictFailsBeforeGatewayAsync()
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        IOperationExecutor executor = Create(gateway, typeof(GetItemQuery), hasGatewayUrl: true);

        OperationOutcome outcome = await executor.ExecuteAsync(new RunQueryArguments(
            "sample.get-item", $$"""{"ItemId":"{{ItemId}}"}""", Offset: 0, Cursor: "next"),
            Context(), TestContext.Current.CancellationToken);

        outcome.Error.ShouldNotBeNull().Violations!.Single().Path.ShouldBe("/cursor");
        await gateway.DidNotReceive().SubmitQueryAsync(Arg.Any<SubmitQueryRequest>(), Arg.Any<string?>(), Arg.Any<CancellationToken>());
    }

    /// <summary>An explicit aggregate mismatch cannot redirect a valid payload to another stream.</summary>
    [Fact]
    public async Task ExplicitAggregateMismatchFailsBeforeGatewayAsync()
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        IOperationExecutor executor = Create(gateway, typeof(CreateItemCommand), hasGatewayUrl: true);

        OperationOutcome outcome = await executor.ExecuteAsync(new SendCommandArguments(
            "sample.create-item", $$"""{"ItemId":"{{ItemId}}","Title":"Hello"}""",
            AggregateId: "01ARZ3NDEKTSV4RRFFQ69G5FAW"), Context(), TestContext.Current.CancellationToken);

        outcome.Error.ShouldNotBeNull().Violations!.Single().Path.ShouldBe("/aggregateId");
        await gateway.DidNotReceive().SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>());
    }

    /// <summary>Caller-supplied envelope identifiers must be ULIDs and are never silently regenerated.</summary>
    [Theory]
    [InlineData("bad", null, "/correlationId")]
    [InlineData(null, "bad", "/idempotencyKey")]
    public async Task InvalidEnvelopeUlidFailsBeforeGatewayAsync(string? correlationId, string? idempotencyKey, string path)
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        IOperationExecutor executor = Create(gateway, typeof(CreateItemCommand), hasGatewayUrl: true);

        OperationOutcome outcome = await executor.ExecuteAsync(new SendCommandArguments(
            "sample.create-item", $$"""{"ItemId":"{{ItemId}}","Title":"Hello"}""",
            CorrelationId: correlationId, IdempotencyKey: idempotencyKey), Context(), TestContext.Current.CancellationToken);

        outcome.Error.ShouldNotBeNull().Violations!.Single().Path.ShouldBe(path);
        await gateway.DidNotReceive().SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>());
    }

    /// <summary>Non-allowlisted extensions cannot cross the gateway boundary.</summary>
    [Fact]
    public async Task DisallowedExtensionFailsBeforeGatewayAsync()
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        IOperationExecutor executor = Create(gateway, typeof(CreateItemCommand), hasGatewayUrl: true);

        OperationOutcome outcome = await executor.ExecuteAsync(new SendCommandArguments(
            "sample.create-item", $$"""{"ItemId":"{{ItemId}}","Title":"Hello"}""",
            Extensions: new Dictionary<string, string> { ["task-id"] = "abc" }), Context(), TestContext.Current.CancellationToken);

        outcome.Error.ShouldNotBeNull().Violations!.Single().Path.ShouldBe("/extensions/task-id");
        await gateway.DidNotReceive().SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>());
    }

    /// <summary>Allowlisting a key does not bypass the gateway's extension sanitizer rules.</summary>
    [Theory]
    [InlineData("task-id", "../secret")]
    [InlineData("bad:key:", "safe")]
    public async Task UnsafeExtensionFailsBeforeGatewayAsync(string key, string value)
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        IOperationExecutor executor = Create(gateway, typeof(CreateItemCommand), hasGatewayUrl: true);
        var context = new EnvelopeContext(null, null, false, new HashSet<string>(StringComparer.OrdinalIgnoreCase) { key });

        OperationOutcome outcome = await executor.ExecuteAsync(new SendCommandArguments(
            "sample.create-item", $$"""{"ItemId":"{{ItemId}}","Title":"Hello"}""",
            Extensions: new Dictionary<string, string> { [key] = value }), context, TestContext.Current.CancellationToken);

        outcome.Error.ShouldNotBeNull().Violations!.Single().Path.ShouldBe("/extensions/" + key.Replace("/", "~1", StringComparison.Ordinal));
        await gateway.DidNotReceive().SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>());
    }

    /// <summary>A per-call tenant cannot override the trusted session tenant without the operator gate.</summary>
    [Fact]
    public async Task TenantOverrideGateFailsBeforeGatewayAsync()
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        IOperationExecutor executor = Create(gateway, typeof(Routing.Module), hasGatewayUrl: true);
        var context = new EnvelopeContext("acme", "operator-1", false, new HashSet<string>());

        OperationOutcome outcome = await executor.ExecuteAsync(new SendCommandArguments(
            "routing-fixture.envelope-item", $$"""{"ItemId":"{{ItemId}}"}""",
            Tenant: "other", IdempotencyKey: CorrelationId), context, TestContext.Current.CancellationToken);

        outcome.Error.ShouldNotBeNull().Violations!.Single().Path.ShouldBe("/tenant");
        await gateway.DidNotReceive().SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>());
    }

    /// <summary>An optional payload key cannot create an idempotency key without a caller envelope value.</summary>
    [Fact]
    public async Task PayloadOnlyIdempotencyKeyFailsBeforeGatewayAsync()
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        IOperationExecutor executor = Create(gateway, typeof(Routing.Module), hasGatewayUrl: true);

        OperationOutcome outcome = await executor.ExecuteAsync(new SendCommandArguments(
            "routing-fixture.nullable-idempotency", $$"""{"ItemId":"{{ItemId}}","Idempotency":"{{CorrelationId}}"}"""),
            new EnvelopeContext("acme", null, false, new HashSet<string>()), TestContext.Current.CancellationToken);

        outcome.Error.ShouldNotBeNull().Violations!.Single().Path.ShouldBe("/idempotencyKey");
        await gateway.DidNotReceive().SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>());
    }

    /// <summary>A string-kind module accepts its declared string identifier and preserves a JSON-null query result.</summary>
    [Fact]
    public async Task StringIdentifierQueryReturnsRequiredNullDocumentAsync()
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        gateway.SubmitQueryAsync(Arg.Any<SubmitQueryRequest>(), Arg.Any<string?>(), Arg.Any<CancellationToken>())
            .Returns(Task.FromResult(new EventStoreQueryResult(null, null, false, null)));
        IOperationExecutor executor = Create(gateway, typeof(StringContracts.Module), hasGatewayUrl: true);

        OperationOutcome outcome = await executor.ExecuteAsync(new RunQueryArguments(
            "string-fixture.lookup", "{\"Key\":\"item-42\"}"), Context(), TestContext.Current.CancellationToken);

        CoreQueryResult result = outcome.Document.ShouldBeOfType<CoreQueryResult>();
        result.Tenant.ShouldBe("fixed-tenant");
        JsonElement document = JsonSerializer.SerializeToElement(result, McpCliJson.Result);
        document.GetProperty("document").ValueKind.ShouldBe(JsonValueKind.Null);
        document.TryGetProperty("paging", out _).ShouldBeFalse();
        await gateway.Received(1).SubmitQueryAsync(Arg.Is<SubmitQueryRequest>(request => request.AggregateId == "item-42"),
            Arg.Any<string?>(), Arg.Any<CancellationToken>());
    }

    /// <summary>A gateway rejection maps its status and does not cause a retry.</summary>
    [Fact]
    public async Task GatewayFailureIsMappedWithoutRetryAsync()
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        gateway.SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>())
            .Returns<Task<SubmitCommandResponse>>(_ => throw new EventStoreGatewayException(409, "Conflict", reasonCode: "conflict"));
        IOperationExecutor executor = Create(gateway, typeof(CreateItemCommand), hasGatewayUrl: true);

        OperationOutcome outcome = await executor.ExecuteAsync(
            new SendCommandArguments("sample.create-item", $$"""{"ItemId":"{{ItemId}}","Title":"Hello"}"""),
            Context(), TestContext.Current.CancellationToken);

        outcome.Error.ShouldNotBeNull().Code.ShouldBe("gateway_error");
        outcome.Error.Status.ShouldBe(409);
        outcome.Error.Reason.ShouldBe("conflict");
        await gateway.Received(1).SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>());
    }

    private static IOperationExecutor Create(IEventStoreGatewayClient gateway, Type contractType,
        bool readOnly = false, bool hasGatewayUrl = false)
    {
        var provider = new CatalogProvider(() => [contractType.Assembly], new RecordingLogger<CatalogProvider>());
        return new OperationExecutor(provider, new ExecutionAvailability(readOnly, hasGatewayUrl), gateway, strict: false);
    }

    private static EnvelopeContext Context()
        => new("unused-session-tenant", null, false, new HashSet<string>(StringComparer.OrdinalIgnoreCase));
}
