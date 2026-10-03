using System.Text.Json;
using ByteAether.Ulid;
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

    /// <summary>Each accepted call gets a fresh message ID and reuses it as correlation without inventing a key.</summary>
    [Fact]
    public async Task GeneratedIdentifiersAreDistinctAndOptionalFieldsAreOmittedAsync()
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        var captured = new List<SubmitCommandRequest>();
        gateway.SubmitCommandAsync(Arg.Do<SubmitCommandRequest>(captured.Add), Arg.Any<CancellationToken>())
            .Returns(Task.FromResult(new SubmitCommandResponse(CorrelationId)));
        IOperationExecutor executor = Create(gateway, typeof(CreateItemCommand), hasGatewayUrl: true);
        var call = new SendCommandArguments("sample.create-item", $$"""{"ItemId":"{{ItemId}}","Title":"Hello"}""");

        CommandResult first = (await executor.ExecuteAsync(call, Context(), TestContext.Current.CancellationToken))
            .Document.ShouldBeOfType<CommandResult>();
        CommandResult second = (await executor.ExecuteAsync(call, Context(), TestContext.Current.CancellationToken))
            .Document.ShouldBeOfType<CommandResult>();

        captured.Count.ShouldBe(2);
        captured[0].MessageId.ShouldNotBe(captured[1].MessageId);
        foreach ((SubmitCommandRequest request, CommandResult result) in captured.Zip([first, second]))
        {
            Ulid.TryParse(request.MessageId, provider: null, out _).ShouldBeTrue();
            request.CorrelationId.ShouldBe(request.MessageId);
            request.IdempotencyKey.ShouldBeNull();
            result.MessageId.ShouldBe(request.MessageId);
            result.CorrelationId.ShouldBe(request.CorrelationId);
            result.Tenant.ShouldBe("sample-tenant");
            result.AggregateId.ShouldBe(ItemId);
            result.Status.ShouldBe("accepted");
            using JsonDocument json = JsonDocument.Parse(JsonSerializer.Serialize(result, McpCliJson.Result));
            json.RootElement.TryGetProperty("idempotencyKey", out _).ShouldBeFalse();
            json.RootElement.TryGetProperty("result", out _).ShouldBeFalse();
            json.RootElement.TryGetProperty("duplicate", out _).ShouldBeFalse();
        }

        await gateway.Received(2).SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>());
    }

    /// <summary>Distinct caller IDs reach the gateway unchanged and the result uses the submitted correlation.</summary>
    [Fact]
    public async Task CallerIdentifiersArePreservedAsync()
    {
        const string idempotencyKey = "01J9MZHXT3RKM0VWXRXGSJDATM";
        const string returnedMessageId = "01J9MZHXT3RKM0VWXRXGSJDATN";
        const string gatewayCorrelationId = "01J9MZHXT3RKM0VWXRXGSJDATP";
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        SubmitCommandRequest? captured = null;
        gateway.SubmitCommandAsync(Arg.Do<SubmitCommandRequest>(request => captured = request), Arg.Any<CancellationToken>())
            .Returns(Task.FromResult(new SubmitCommandResponse(gatewayCorrelationId, MessageId: returnedMessageId)));
        IOperationExecutor executor = Create(gateway, typeof(CreateItemCommand), hasGatewayUrl: true);

        OperationOutcome outcome = await executor.ExecuteAsync(new SendCommandArguments(
            "sample.create-item", $$"""{"ItemId":"{{ItemId}}","Title":"Hello"}""",
            CorrelationId: CorrelationId, IdempotencyKey: idempotencyKey), Context(), TestContext.Current.CancellationToken);

        outcome.Error.ShouldBeNull();
        captured.ShouldNotBeNull();
        captured.CorrelationId.ShouldBe(CorrelationId);
        captured.IdempotencyKey.ShouldBe(idempotencyKey);
        Ulid.TryParse(captured.MessageId, provider: null, out _).ShouldBeTrue();
        captured.MessageId.ShouldNotBe(CorrelationId);
        captured.MessageId.ShouldNotBe(idempotencyKey);
        CommandResult result = outcome.Document.ShouldBeOfType<CommandResult>();
        result.MessageId.ShouldBe(returnedMessageId);
        result.CorrelationId.ShouldBe(CorrelationId);
        result.CorrelationId.ShouldNotBe(gatewayCorrelationId);
        result.IdempotencyKey.ShouldBe(idempotencyKey);
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

    /// <summary>A read passed to send fails at the operation before availability or payload validation.</summary>
    [Fact]
    public async Task SendRejectsQueryBeforeAvailabilityAsync()
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        IOperationExecutor executor = Create(gateway, typeof(GetItemQuery), readOnly: true, hasGatewayUrl: false);

        OperationOutcome outcome = await executor.ExecuteAsync(
            new SendCommandArguments("sample.get-item", "invalid-json"), Context(), TestContext.Current.CancellationToken);

        outcome.Document.ShouldBeNull();
        outcome.Error.ShouldNotBeNull().Code.ShouldBe("validation_failed");
        outcome.Error.Violations!.Single().Path.ShouldBe("/operation");
        await gateway.DidNotReceive().SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>());
    }

    /// <summary>Malformed JSON and unknown members fail before command submission.</summary>
    [Theory]
    [InlineData("{", "/")]
    [InlineData("{\"ItemId\":\"01ARZ3NDEKTSV4RRFFQ69G5FAV\",\"Title\":\"x\",\"Unexpected\":1}", "/")]
    [InlineData("{\"ItemId\":\"01ARZ3NDEKTSV4RRFFQ69G5FAV\",\"ItemId\":\"01ARZ3NDEKTSV4RRFFQ69G5FAW\",\"Title\":\"x\"}", "/")]
    [InlineData("null", "/")]
    [InlineData("[]", "/")]
    [InlineData("{\"ItemId\":\"bad\",\"Title\":\"Hello\"}", "/ItemId")]
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

    /// <summary>Caller-supplied envelope identifiers must be canonical ULIDs and are never silently regenerated.</summary>
    [Theory]
    [InlineData("bad", null, "/correlationId")]
    [InlineData(null, "bad", "/idempotencyKey")]
    [InlineData("01arz3ndektsv4rrffq69g5fav", null, "/correlationId")]
    [InlineData(null, "01arz3ndektsv4rrffq69g5fav", "/idempotencyKey")]
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

    /// <summary>Approved keys are matched without case sensitivity and reach the gateway unchanged.</summary>
    [Fact]
    public async Task MixedCaseApprovedExtensionReachesGatewayOnceAsync()
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        SubmitCommandRequest? captured = null;
        gateway.SubmitCommandAsync(Arg.Do<SubmitCommandRequest>(request => captured = request), Arg.Any<CancellationToken>())
            .Returns(Task.FromResult(new SubmitCommandResponse(CorrelationId)));
        IOperationExecutor executor = Create(gateway, typeof(CreateItemCommand), hasGatewayUrl: true);
        var extensions = new Dictionary<string, string> { ["Task-ID"] = "safe" };
        var context = new EnvelopeContext(null, null, false, new HashSet<string> { "task-id" });

        OperationOutcome outcome = await executor.ExecuteAsync(new SendCommandArguments(
            "sample.create-item", $$"""{"ItemId":"{{ItemId}}","Title":"Hello"}""", Extensions: extensions),
            context, TestContext.Current.CancellationToken);

        outcome.Error.ShouldBeNull();
        captured.ShouldNotBeNull().Extensions!["Task-ID"].ShouldBe("safe");
        await gateway.Received(1).SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>());
    }

    /// <summary>Gateway request validation forbids dangerous characters even in approved extension values.</summary>
    [Theory]
    [InlineData("<")]
    [InlineData(">")]
    [InlineData("&")]
    [InlineData("'")]
    [InlineData("\"")]
    [InlineData("\u0001")]
    [InlineData("javascript:alert(1)")]
    public async Task DangerousExtensionValuesMakeZeroCallsAsync(string value)
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        IOperationExecutor executor = Create(gateway, typeof(CreateItemCommand), hasGatewayUrl: true);
        var context = new EnvelopeContext(null, null, false, new HashSet<string> { "task-id" });
        OperationOutcome outcome = await executor.ExecuteAsync(new SendCommandArguments(
            "sample.create-item", $$"""{"ItemId":"{{ItemId}}","Title":"Hello"}""",
            Extensions: new Dictionary<string, string> { ["task-id"] = value }), context, TestContext.Current.CancellationToken);

        outcome.Error.ShouldNotBeNull().Violations!.ShouldContain(violation => violation.Path == "/extensions/task-id");
        await gateway.DidNotReceive().SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>());
    }

    /// <summary>Malformed keys retain RFC 6901 escaped member pointers.</summary>
    [Fact]
    public async Task UnsafeExtensionKeyUsesEscapedPointerAsync()
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        IOperationExecutor executor = Create(gateway, typeof(CreateItemCommand), hasGatewayUrl: true);
        var context = new EnvelopeContext(null, null, false, new HashSet<string> { "task/~" });
        OperationOutcome outcome = await executor.ExecuteAsync(new SendCommandArguments(
            "sample.create-item", $$"""{"ItemId":"{{ItemId}}","Title":"Hello"}""",
            Extensions: new Dictionary<string, string> { ["task/~"] = "safe" }), context, TestContext.Current.CancellationToken);

        outcome.Error.ShouldNotBeNull().Violations!.ShouldContain(violation => violation.Path == "/extensions/task~1~0");
        await gateway.DidNotReceive().SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>());
    }

    /// <summary>A final newline cannot satisfy the Gateway extension-key grammar.</summary>
    [Fact]
    public async Task ExtensionKeyWithFinalNewlineMakesZeroCallsAsync()
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        IOperationExecutor executor = Create(gateway, typeof(CreateItemCommand), hasGatewayUrl: true);
        const string key = "task-id\n";
        var context = new EnvelopeContext(null, null, false, new HashSet<string> { key });
        OperationOutcome outcome = await executor.ExecuteAsync(new SendCommandArguments(
            "sample.create-item", $$"""{"ItemId":"{{ItemId}}","Title":"Hello"}""",
            Extensions: new Dictionary<string, string> { [key] = "safe" }), context, TestContext.Current.CancellationToken);

        outcome.Error.ShouldNotBeNull().Violations!.ShouldContain(violation => violation.Path == "/extensions/" + key);
        await gateway.DidNotReceive().SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>());
    }

    /// <summary>Gateway's case-insensitive extension dictionary cannot silently overwrite a caller value.</summary>
    [Fact]
    public async Task CaseInsensitiveDuplicateExtensionsMakeZeroCallsAsync()
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        IOperationExecutor executor = Create(gateway, typeof(CreateItemCommand), hasGatewayUrl: true);
        var context = new EnvelopeContext(null, null, false, new HashSet<string> { "task-id" });
        OperationOutcome outcome = await executor.ExecuteAsync(new SendCommandArguments(
            "sample.create-item", $$"""{"ItemId":"{{ItemId}}","Title":"Hello"}""",
            Extensions: new Dictionary<string, string> { ["Task-ID"] = "first", ["task-id"] = "second" }),
            context, TestContext.Current.CancellationToken);

        outcome.Error.ShouldNotBeNull().Violations!.ShouldContain(violation => violation.Path == "/extensions/task-id");
        await gateway.DidNotReceive().SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>());
    }

    /// <summary>The Gateway reserves this key regardless of caller casing or allowlist contents.</summary>
    [Theory]
    [InlineData("actor:globalAdmin")]
    [InlineData("AcToR:gLoBaLaDmIn")]
    public async Task ReservedExtensionMakesZeroCallsAsync(string key)
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        IOperationExecutor executor = Create(gateway, typeof(CreateItemCommand), hasGatewayUrl: true);
        var context = new EnvelopeContext(null, null, false, new HashSet<string> { key });
        OperationOutcome outcome = await executor.ExecuteAsync(new SendCommandArguments(
            "sample.create-item", $$"""{"ItemId":"{{ItemId}}","Title":"Hello"}""",
            Extensions: new Dictionary<string, string> { [key] = "true" }), context, TestContext.Current.CancellationToken);

        outcome.Error.ShouldNotBeNull().Violations!.ShouldContain(violation => violation.Path == "/extensions/" + key);
        await gateway.DidNotReceive().SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>());
    }

    /// <summary>The pinned sanitizer's entry, member, and UTF-8 size boundaries are enforced locally.</summary>
    [Theory]
    [InlineData("count", false)]
    [InlineData("count", true)]
    [InlineData("key", false)]
    [InlineData("key", true)]
    [InlineData("value", false)]
    [InlineData("value", true)]
    [InlineData("bytes", false)]
    [InlineData("bytes", true)]
    public async Task ExtensionBoundariesMakeExpectedGatewayCallsAsync(string boundary, bool overLimit)
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        SubmitCommandRequest? captured = null;
        gateway.SubmitCommandAsync(Arg.Do<SubmitCommandRequest>(request => captured = request), Arg.Any<CancellationToken>())
            .Returns(Task.FromResult(new SubmitCommandResponse(CorrelationId)));
        IOperationExecutor executor = Create(gateway, typeof(CreateItemCommand), hasGatewayUrl: true);
        Dictionary<string, string> extensions = boundary switch
        {
            "count" => Enumerable.Range(0, overLimit ? 33 : 32).ToDictionary(index => "k" + index, _ => ""),
            "key" => new() { [new string('k', overLimit ? 101 : 100)] = "" },
            "value" => new() { ["k"] = new string('a', overLimit ? 1001 : 1000) },
            _ => new()
            {
                ["a"] = new string('é', 500),
                ["b"] = new string('é', 500),
                ["c"] = new string('é', 500),
                ["d"] = new string('é', 500),
                ["e"] = new string('x', overLimit ? 92 : 91),
            },
        };
        var context = new EnvelopeContext(null, null, false, extensions.Keys.ToHashSet(StringComparer.OrdinalIgnoreCase));
        OperationOutcome outcome = await executor.ExecuteAsync(new SendCommandArguments(
            "sample.create-item", $$"""{"ItemId":"{{ItemId}}","Title":"Hello"}""", Extensions: extensions),
            context, TestContext.Current.CancellationToken);

        if (overLimit)
        {
            outcome.Error.ShouldNotBeNull().Violations!.ShouldContain(violation => violation.Path.StartsWith("/extensions", StringComparison.Ordinal));
            await gateway.DidNotReceive().SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>());
        }
        else
        {
            outcome.Error.ShouldBeNull();
            IDictionary<string, string> submitted = captured.ShouldNotBeNull().Extensions.ShouldNotBeNull();
            submitted.Count.ShouldBe(extensions.Count);
            foreach ((string key, string value) in extensions)
            {
                submitted.TryGetValue(key, out string? actual).ShouldBeTrue();
                actual.ShouldBe(value);
            }

            await gateway.Received(1).SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>());
        }
    }

    /// <summary>A mutable caller dictionary is enumerated once, then its validated snapshot is submitted.</summary>
    [Fact]
    public async Task MutableExtensionsCannotChangeAfterValidationAsync()
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        SubmitCommandRequest? captured = null;
        gateway.SubmitCommandAsync(Arg.Do<SubmitCommandRequest>(request => captured = request), Arg.Any<CancellationToken>())
            .Returns(Task.FromResult(new SubmitCommandResponse(CorrelationId)));
        IOperationExecutor executor = Create(gateway, typeof(CreateItemCommand), hasGatewayUrl: true);
        var extensions = new ChangingExtensions();
        var context = new EnvelopeContext(null, null, false, new HashSet<string> { "task-id" });

        OperationOutcome outcome = await executor.ExecuteAsync(new SendCommandArguments(
            "sample.create-item", $$"""{"ItemId":"{{ItemId}}","Title":"Hello"}""", Extensions: extensions),
            context, TestContext.Current.CancellationToken);

        outcome.Error.ShouldBeNull();
        extensions.EnumerationCount.ShouldBe(1);
        captured.ShouldNotBeNull().Extensions.ShouldNotBeNull()["task-id"].ShouldBe("safe");
        await gateway.Received(1).SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>());
    }

    /// <summary>A supplied key replaces raw mapped data, and the computed accessor sees the rebuilt envelope.</summary>
    [Theory]
    [InlineData(false, false, false)]
    [InlineData(true, true, true)]
    public async Task ComputedAccessorSeesTrustedEnvelopeAndNestedNullAsync(
        bool includeRawIdentity, bool rawNull, bool nullDetails)
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        SubmitCommandRequest? captured = null;
        gateway.SubmitCommandAsync(Arg.Do<SubmitCommandRequest>(request => captured = request), Arg.Any<CancellationToken>())
            .Returns(Task.FromResult(new SubmitCommandResponse(CorrelationId)));
        IOperationExecutor executor = Create(gateway, typeof(Routing.Module), hasGatewayUrl: true);
        const string key = "01J9MZHXT3RKM0VWXRXGSJDATM";

        var payload = new Dictionary<string, object?>
        {
            ["ItemId"] = ItemId,
            ["Correlation"] = rawNull ? null : new { invalid = true },
            ["Idempotency"] = rawNull ? null : 42,
            ["Details"] = nullDetails ? null : new { Note = (string?)null },
        };
        if (includeRawIdentity)
        {
            payload["Tenant"] = "acme";
            payload["Actor"] = "operator-1";
        }

        OperationOutcome outcome = await executor.ExecuteAsync(new SendCommandArguments(
            "routing-fixture.computed-envelope", JsonSerializer.Serialize(payload),
            IdempotencyKey: key),
            new EnvelopeContext("acme", "operator-1", false, new HashSet<string>()), TestContext.Current.CancellationToken);

        outcome.Error.ShouldBeNull();
        captured.ShouldNotBeNull();
        captured.AggregateId.ShouldBe(ItemId);
        captured.Payload.GetProperty("Tenant").GetString().ShouldBe("acme");
        captured.Payload.GetProperty("Actor").GetString().ShouldBe("operator-1");
        captured.Payload.GetProperty("Correlation").GetString().ShouldBe(captured.MessageId);
        captured.Payload.GetProperty("Idempotency").GetString().ShouldBe(key);
        if (nullDetails)
        {
            captured.Payload.GetProperty("Details").ValueKind.ShouldBe(JsonValueKind.Null);
        }
        else
        {
            captured.Payload.GetProperty("Details").GetProperty("Note").ValueKind.ShouldBe(JsonValueKind.Null);
        }
        captured.IdempotencyKey.ShouldBe(key);
        await gateway.Received(1).SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>());
    }

    /// <summary>Present tenant and actor members must be strings exactly matching trusted values.</summary>
    [Theory]
    [InlineData("Tenant", "null", "/Tenant")]
    [InlineData("Tenant", "42", "/Tenant")]
    [InlineData("Tenant", "\"ACME\"", "/Tenant")]
    [InlineData("Actor", "null", "/Actor")]
    [InlineData("Actor", "false", "/Actor")]
    [InlineData("Actor", "\"Operator-1\"", "/Actor")]
    public async Task RawIdentityConflictMakesZeroCallsAsync(string member, string rawValue, string path)
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        IOperationExecutor executor = Create(gateway, typeof(Routing.Module), hasGatewayUrl: true);
        string payload = $$"""{"ItemId":"{{ItemId}}","{{member}}":{{rawValue}}}""";
        OperationOutcome outcome = await executor.ExecuteAsync(new SendCommandArguments("routing-fixture.computed-envelope", payload),
            new EnvelopeContext("acme", "operator-1", false, new HashSet<string>()), TestContext.Current.CancellationToken);

        outcome.Error.ShouldNotBeNull().Violations!.Single().Path.ShouldBe(path);
        await gateway.DidNotReceive().SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>());
    }

    /// <summary>A payload actor cannot supply the missing trusted session actor.</summary>
    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task MissingTrustedActorMakesZeroCallsAsync(bool rawActor)
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        IOperationExecutor executor = Create(gateway, typeof(Routing.Module), hasGatewayUrl: true);
        string payload = rawActor
            ? $$"""{"ItemId":"{{ItemId}}","Actor":"caller"}"""
            : $$"""{"ItemId":"{{ItemId}}"}""";

        OperationOutcome outcome = await executor.ExecuteAsync(new SendCommandArguments("routing-fixture.computed-envelope", payload),
            new EnvelopeContext("acme", null, false, new HashSet<string>()), TestContext.Current.CancellationToken);

        outcome.Error.ShouldNotBeNull().Violations!.Single().Path.ShouldBe("/actor");
        await gateway.DidNotReceive().SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>());
    }

    /// <summary>Optional raw null is removed when the caller omits a key.</summary>
    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task OptionalIdempotencyIsAbsentWithoutCallerKeyAsync(bool rawNull)
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        SubmitCommandRequest? captured = null;
        gateway.SubmitCommandAsync(Arg.Do<SubmitCommandRequest>(request => captured = request), Arg.Any<CancellationToken>())
            .Returns(Task.FromResult(new SubmitCommandResponse(CorrelationId)));
        IOperationExecutor executor = Create(gateway, typeof(Routing.Module), hasGatewayUrl: true);
        string payload = rawNull
            ? $$"""{"ItemId":"{{ItemId}}","Idempotency":null}"""
            : $$"""{"ItemId":"{{ItemId}}"}""";

        OperationOutcome outcome = await executor.ExecuteAsync(new SendCommandArguments("routing-fixture.nullable-idempotency", payload),
            new EnvelopeContext("acme", null, false, new HashSet<string>()), TestContext.Current.CancellationToken);

        outcome.Error.ShouldBeNull();
        captured.ShouldNotBeNull().IdempotencyKey.ShouldBeNull();
        captured.Payload.TryGetProperty("Idempotency", out _).ShouldBeFalse();
        await gateway.Received(1).SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>());
    }

    /// <summary>A required nullable member still needs a caller key even if raw JSON contains null.</summary>
    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task RequiredNullableIdempotencyNeedsCallerKeyAsync(bool rawNull)
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        IOperationExecutor executor = Create(gateway, typeof(Routing.Module), hasGatewayUrl: true);
        string payload = rawNull
            ? $$"""{"ItemId":"{{ItemId}}","Idempotency":null}"""
            : $$"""{"ItemId":"{{ItemId}}"}""";

        OperationOutcome outcome = await executor.ExecuteAsync(new SendCommandArguments(
            "routing-fixture.required-nullable-idempotency", payload),
            new EnvelopeContext("acme", null, false, new HashSet<string>()), TestContext.Current.CancellationToken);

        outcome.Error.ShouldNotBeNull().Violations!.Single().Path.ShouldBe("/idempotencyKey");
        await gateway.DidNotReceive().SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>());
    }

    /// <summary>The supplied key satisfies a serializer-required nullable member.</summary>
    [Fact]
    public async Task SuppliedKeyFillsRequiredNullableMemberAsync()
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        SubmitCommandRequest? captured = null;
        gateway.SubmitCommandAsync(Arg.Do<SubmitCommandRequest>(request => captured = request), Arg.Any<CancellationToken>())
            .Returns(Task.FromResult(new SubmitCommandResponse(CorrelationId)));
        IOperationExecutor executor = Create(gateway, typeof(Routing.Module), hasGatewayUrl: true);

        OperationOutcome outcome = await executor.ExecuteAsync(new SendCommandArguments(
            "routing-fixture.required-nullable-idempotency", $$"""{"ItemId":"{{ItemId}}","Idempotency":"bad"}""",
            IdempotencyKey: CorrelationId),
            new EnvelopeContext("acme", null, false, new HashSet<string>()), TestContext.Current.CancellationToken);

        outcome.Error.ShouldBeNull();
        captured.ShouldNotBeNull().Payload.GetProperty("Idempotency").GetString().ShouldBe(CorrelationId);
        await gateway.Received(1).SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>());
    }

    /// <summary>Lowercase aggregate ULIDs fail at the proper source before submission.</summary>
    [Theory]
    [InlineData("routing-fixture.computed-envelope", "/aggregateId")]
    [InlineData("routing-fixture.nullable-idempotency", "/ItemId")]
    public async Task LowercaseAggregateUlidMakesZeroCallsAsync(string operation, string path)
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        IOperationExecutor executor = Create(gateway, typeof(Routing.Module), hasGatewayUrl: true);
        OperationOutcome outcome = await executor.ExecuteAsync(new SendCommandArguments(operation,
            $$"""{"ItemId":"{{ItemId.ToLowerInvariant()}}"}"""),
            new EnvelopeContext("acme", "operator-1", false, new HashSet<string>()), TestContext.Current.CancellationToken);

        outcome.Error.ShouldNotBeNull().Violations!.ShouldContain(violation => violation.Path == path);
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

    /// <summary>A timed-out submission has one call and only a stable failure document.</summary>
    [Fact]
    public async Task GatewayTimeoutDoesNotRetryOrClaimSafeResubmissionAsync()
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        gateway.SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>())
            .Returns<Task<SubmitCommandResponse>>(_ => throw new EventStoreGatewayException(
                503, "EventStore gateway unavailable",
                detail: "The EventStore gateway did not respond before the request timed out.",
                reason: "gateway-timeout", innerException: new TaskCanceledException()));
        IOperationExecutor executor = Create(gateway, typeof(CreateItemCommand), hasGatewayUrl: true);

        OperationOutcome outcome = await executor.ExecuteAsync(
            new SendCommandArguments("sample.create-item", $$"""{"ItemId":"{{ItemId}}","Title":"Hello"}"""),
            Context(), TestContext.Current.CancellationToken);

        outcome.Document.ShouldBeNull();
        outcome.Error.ShouldNotBeNull().Code.ShouldBe("gateway_error");
        outcome.Error.Status.ShouldBe(503);
        outcome.Error.Reason.ShouldBe("gateway-timeout");
        outcome.Error.Detail.ShouldBe("The EventStore gateway did not respond before the request timed out.");
        using JsonDocument json = JsonDocument.Parse(JsonSerializer.Serialize(new { error = outcome.Error }, McpCliJson.Result));
        JsonElement error = json.RootElement.GetProperty("error");
        error.GetProperty("code").GetString().ShouldBe("gateway_error");
        error.GetProperty("status").GetInt32().ShouldBe(503);
        error.GetProperty("reason").GetString().ShouldBe("gateway-timeout");
        error.TryGetProperty("retryable", out _).ShouldBeFalse();
        error.TryGetProperty("clientAction", out _).ShouldBeFalse();
        error.GetRawText().ShouldNotContain("safe", Case.Insensitive);
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
