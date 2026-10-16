using System.Text.Json;
using Hexalith.EventStore.Client.Gateway;
using Hexalith.EventStore.Contracts.Commands;
using Hexalith.EventStore.Contracts.Queries;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Core.Execution;
using Hexalith.McpCli.Core.Serialization;
using Microsoft.Extensions.DependencyInjection;
using ModelContextProtocol;
using ModelContextProtocol.Protocol;
using NSubstitute;
using Shouldly;
using static Hexalith.McpCli.Mcp.Tests.McpTestSession;

namespace Hexalith.McpCli.Mcp.Tests;

/// <summary>Proves execution arguments and complete documents survive the MCP boundary.</summary>
public sealed class McpExecutionTests
{
    /// <summary>All command envelope fields reach one Gateway call and both heads serialize the same result.</summary>
    [Theory]
    [InlineData("2025-06-18", false)]
    [InlineData("2025-06-18", true)]
    [InlineData("2026-07-28", false)]
    [InlineData("2026-07-28", true)]
    public async Task CommandArgumentsAndOptionalResultMatchCoreAsync(string version, bool withResult)
    {
        JsonElement? response = withResult ? JsonSerializer.SerializeToElement(new { accepted = true, extra = new[] { 1 } }) : null;
        await using McpTestSession session = await CreateAsync(version, configure: (_, gateway) =>
            gateway.SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>())
                .Returns(Task.FromResult(new SubmitCommandResponse(CorrelationId, response, MessageId))));
        var arguments = new SendCommandArguments("routing-fixture.envelope-item", QueryPayload,
            Tenant: "session-tenant", AggregateId: ItemId, CorrelationId: CorrelationId, IdempotencyKey: Key,
            Extensions: new Dictionary<string, string> { ["task-id"] = "work-42" });
        JsonElement actual = await session.AssertParityAsync(arguments);
        actual.TryGetProperty("result", out _).ShouldBe(withResult);
        var call = session.Gateway.ReceivedCalls().ShouldHaveSingleItem();
        call.GetMethodInfo().Name.ShouldBe(nameof(IEventStoreGatewayClient.SubmitCommandAsync));
        object?[] values = call.GetArguments();
        SubmitCommandRequest request = values[0].ShouldBeOfType<SubmitCommandRequest>();
        request.MessageId.Length.ShouldBe(26);
        request.MessageId.ShouldNotBe(CorrelationId);
        var expected = new SubmitCommandRequest(request.MessageId, "session-tenant", "routing", ItemId,
            "envelope-item", JsonSerializer.SerializeToElement(new Dictionary<string, string>
            {
                ["ItemId"] = ItemId, ["tenant/~"] = "session-tenant", ["Actor"] = "operator-1",
                ["Correlation"] = CorrelationId, ["Idempotency"] = Key,
            }), CorrelationId, new Dictionary<string, string> { ["task-id"] = "work-42" }, Key);
        JsonElement.DeepEquals(JsonSerializer.SerializeToElement(request, McpCliJson.Result),
            JsonSerializer.SerializeToElement(expected, McpCliJson.Result)).ShouldBeTrue();
        ((CancellationToken)values[1]!).CanBeCanceled.ShouldBeTrue();
    }

    /// <summary>Default correlation uses the generated attempt ID and optional command fields stay absent.</summary>
    [Theory]
    [InlineData("2025-06-18")]
    [InlineData("2026-07-28")]
    public async Task CommandDefaultsDoNotInventOptionalMembersAsync(string version)
    {
        await using McpTestSession session = await CreateAsync(version);
        CallToolResult result = await session.CallAsync("send_command", new SendCommandArguments("sample.create-item", CommandPayload));
        SubmitCommandRequest request = session.Gateway.ReceivedCalls().ShouldHaveSingleItem()
            .GetArguments()[0].ShouldBeOfType<SubmitCommandRequest>();
        request.CorrelationId.ShouldBe(request.MessageId);
        request.IdempotencyKey.ShouldBeNull();
        request.Extensions.ShouldBeNull();
        AssertDocument(result, new CommandResult("sample.create-item", MessageId, request.MessageId,
            "sample-tenant", ItemId, "accepted"));
    }

    /// <summary>Object, scalar, array, and null query documents and optional paging retain their JSON types.</summary>
    [Theory]
    [InlineData("2025-06-18", "{\"extra\":{\"values\":[1,true]}}", true)]
    [InlineData("2025-06-18", "42", false)]
    [InlineData("2025-06-18", "[1,\"two\",null]", true)]
    [InlineData("2025-06-18", "null", false)]
    [InlineData("2026-07-28", "{\"extra\":{\"values\":[1,true]}}", true)]
    [InlineData("2026-07-28", "42", false)]
    [InlineData("2026-07-28", "[1,\"two\",null]", true)]
    [InlineData("2026-07-28", "null", false)]
    public async Task QueryArgumentsAndValueTypesMatchCoreAsync(string version, string payload, bool withPaging)
    {
        JsonElement response = JsonSerializer.Deserialize<JsonElement>(payload);
        await using McpTestSession session = await CreateAsync(version, configure: (_, gateway) =>
            gateway.SubmitQueryAsync(Arg.Any<SubmitQueryRequest>(), Arg.Any<string?>(), Arg.Any<CancellationToken>())
                .Returns(Task.FromResult(new EventStoreQueryResult(CorrelationId,
                    response.ValueKind == JsonValueKind.Null ? null : response, false, null)
                {
                    Metadata = withPaging ? new QueryResponseMetadata(Paging: new QueryPagingMetadata(25, 0, "next", 50, true)) : null,
                })));
        var arguments = new RunQueryArguments("sample.get-item", QueryPayload, Tenant: "sample-tenant",
            AggregateId: ItemId, EntityId: "entity-42", PageSize: 25, Cursor: "opaque-cursor");
        JsonElement actual = await session.AssertParityAsync(arguments);
        actual.GetProperty("document").ValueKind.ShouldBe(response.ValueKind);
        actual.TryGetProperty("paging", out _).ShouldBe(withPaging);
        var call = session.Gateway.ReceivedCalls().ShouldHaveSingleItem();
        call.GetMethodInfo().Name.ShouldBe(nameof(IEventStoreGatewayClient.SubmitQueryAsync));
        object?[] values = call.GetArguments();
        var expected = new SubmitQueryRequest("sample-tenant", "sample", ItemId, "get-item", "sample-items",
            JsonSerializer.Deserialize<JsonElement>(QueryPayload), "entity-42")
        {
            Paging = new QueryPagingOptions(25, null, "opaque-cursor"),
        };
        JsonElement.DeepEquals(JsonSerializer.SerializeToElement(values[0], McpCliJson.Result),
            JsonSerializer.SerializeToElement(expected, McpCliJson.Result)).ShouldBeTrue();
        values[1].ShouldBeNull();
        ((CancellationToken)values[2]!).CanBeCanceled.ShouldBeTrue();
    }

    /// <summary>Fixed and session tenant policy remains in Core and refusals never reach the Gateway.</summary>
    [Theory]
    [InlineData("2025-06-18")]
    [InlineData("2026-07-28")]
    public async Task TenantResolutionAndRefusalsMatchCoreAsync(string version)
    {
        foreach ((string operation, string? tenant, bool gate, string supplied, bool refused) in new[]
        {
            ("sample.get-item", "session-tenant", false, "sample-tenant", false),
            ("sample.get-item", "session-tenant", true, "other", true),
            ("routing-fixture.get-http2-status", "session-tenant", false, "other", true),
            ("routing-fixture.get-http2-status", "session-tenant", true, "other", false),
            ("routing-fixture.get-http2-status", (string?)null, false, "other", false),
        })
        {
            await using McpTestSession session = await CreateAsync(version, Settings(tenant, gate));
            JsonElement result = await session.AssertParityAsync(new RunQueryArguments(operation,
                operation.StartsWith("sample.", StringComparison.Ordinal) ? QueryPayload : "{}", Tenant: supplied, AggregateId: ItemId));
            if (refused)
            {
                result.GetProperty("error").GetProperty("code").GetString().ShouldBe("validation_failed");
                session.Gateway.ReceivedCalls().ShouldBeEmpty();
            }
            else
            {
                result.GetProperty("tenant").GetString().ShouldBe(supplied);
                session.Gateway.ReceivedCalls().ShouldHaveSingleItem();
            }
        }
    }

    /// <summary>Wrong kinds, payloads, envelope arguments, offline calls and Gateway failures match Core documents.</summary>
    [Theory]
    [InlineData("2025-06-18")]
    [InlineData("2026-07-28")]
    public async Task ExecutionRefusalsAndGatewayFailuresMatchCoreAsync(string version)
    {
        await using McpTestSession session = await CreateAsync(version);
        OperationCall[] invalid = [
            new SendCommandArguments("sample.get-item", QueryPayload),
            new RunQueryArguments("sample.create-item", CommandPayload),
            new SendCommandArguments("sample.create-item", "null"),
            new SendCommandArguments("sample.create-item", "{"),
            new SendCommandArguments("sample.create-item", CommandPayload, CorrelationId: CorrelationId.ToLowerInvariant()),
            new SendCommandArguments("sample.create-item", CommandPayload, IdempotencyKey: "invalid"),
            new SendCommandArguments("sample.create-item", CommandPayload, AggregateId: MessageId),
            new SendCommandArguments("sample.create-item", CommandPayload, Extensions: new Dictionary<string, string> { ["unknown"] = "value" }),
            new RunQueryArguments("sample.get-item", QueryPayload, PageSize: 0),
            new RunQueryArguments("sample.get-item", QueryPayload, Offset: 0, Cursor: "cursor"),
            new RunQueryArguments("sample.missing", QueryPayload),
        ];
        foreach (OperationCall arguments in invalid)
        {
            await session.AssertParityAsync(arguments);
            session.Gateway.ReceivedCalls().ShouldBeEmpty();
        }

        await using McpTestSession offline = await CreateAsync(version, Settings(hasUrl: false));
        await offline.AssertParityAsync(new SendCommandArguments("sample.create-item", CommandPayload));
        await offline.AssertParityAsync(new RunQueryArguments("sample.get-item", QueryPayload));
        offline.Gateway.ReceivedCalls().ShouldBeEmpty();
        (await offline.CallAsync("list_modules")).IsError.ShouldBe(false);

        var gatewayError = new EventStoreGatewayException(409, "Conflict", detail: "Rejected by Gateway.",
            reasonCode: "conflict", retryable: false, clientAction: "inspect", correlationId: CorrelationId, retryAfter: "30");
        session.Gateway.SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>())
            .Returns<Task<SubmitCommandResponse>>(_ => throw gatewayError);
        await session.AssertParityAsync(new SendCommandArguments("sample.create-item", CommandPayload, CorrelationId: CorrelationId));
        session.Gateway.ReceivedCalls().ShouldHaveSingleItem();
        session.Gateway.SubmitQueryAsync(Arg.Any<SubmitQueryRequest>(), Arg.Any<string?>(), Arg.Any<CancellationToken>())
            .Returns<Task<EventStoreQueryResult>>(_ => throw new EventStoreGatewayException(200, "Malformed response"));
        await session.AssertParityAsync(new RunQueryArguments("sample.get-item", QueryPayload));
        session.Gateway.ReceivedCalls().ShouldHaveSingleItem();
        (await session.CallAsync("list_operations", new { module = "sample" })).IsError.ShouldBe(false);
    }

    /// <summary>Read-only registration omits writes and the shared executor independently refuses direct writes.</summary>
    [Theory]
    [InlineData("2025-06-18")]
    [InlineData("2026-07-28")]
    public async Task ReadOnlyDirectExecutionIsStillGuardedAsync(string version)
    {
        await using McpTestSession session = await CreateAsync(version, Settings(readOnly: true));
        (await session.Client.ListToolsAsync(cancellationToken: session.Token)).Select(tool => tool.Name)
            .ShouldBe(["list_modules", "list_operations", "describe_operation", "run_query"]);
        OperationOutcome result = await session.Provider.GetRequiredService<IOperationExecutor>().ExecuteAsync(
            new SendCommandArguments("sample.create-item", "{"), session.Provider.GetRequiredService<EnvelopeContext>(), session.Token);
        JsonSerializer.SerializeToElement(result.Error, McpCliJson.Result).GetRawText().ShouldBe(
            JsonSerializer.SerializeToElement(new OperationError("read_only", Message: "Command submission is disabled in read-only mode."), McpCliJson.Result).GetRawText());
        session.Gateway.ReceivedCalls().ShouldBeEmpty();
    }

    /// <summary>Unexpected catalog and executor exceptions produce the exact sanitized tool document.</summary>
    [Theory]
    [InlineData("2025-06-18")]
    [InlineData("2026-07-28")]
    public async Task BoundaryExceptionsAreSanitizedAsync(string version)
    {
        await using McpTestSession session = await CreateAsync(version, configure: (services, _) =>
        {
            ICatalog catalog = Substitute.For<ICatalog>();
            catalog.ListModules().Returns(_ => throw new InvalidOperationException("secret-token catalog"));
            catalog.ListOperations(Arg.Any<string>(), Arg.Any<string?>()).Returns(_ => throw new InvalidOperationException("secret-token catalog"));
            catalog.Describe(Arg.Any<string>()).Returns(_ => throw new InvalidOperationException("secret-token catalog"));
            services.AddSingleton(catalog);
            IOperationExecutor executor = Substitute.For<IOperationExecutor>();
            executor.ExecuteAsync(Arg.Any<OperationCall>(), Arg.Any<EnvelopeContext>(), Arg.Any<CancellationToken>(),
                Arg.Any<Func<CancellationToken, Task<OperationError?>>?>())
                .Returns<Task<OperationOutcome>>(_ => throw new InvalidOperationException("secret-token executor"));
            services.AddSingleton(executor);
        });
        foreach ((string tool, object arguments) in new (string, object)[]
        {
            ("list_modules", new { }), ("list_operations", new { module = "sample" }),
            ("describe_operation", new { operation = "sample.get-item" }),
            ("send_command", new SendCommandArguments("sample.create-item", CommandPayload)),
            ("run_query", new RunQueryArguments("sample.get-item", QueryPayload)),
        })
        {
            AssertDocument(await session.CallAsync(tool, arguments), new
            {
                error = new OperationError("internal_error", Message: "MCP tool invocation failed."),
            }, isError: true);
        }
        session.Gateway.ReceivedCalls().ShouldBeEmpty();
    }

    /// <summary>Required arguments and malformed bound values fail at protocol binding before execution.</summary>
    [Theory]
    [InlineData("2025-06-18")]
    [InlineData("2026-07-28")]
    public async Task BindingFailuresUseInvalidParametersAsync(string version)
    {
        await using McpTestSession session = await CreateAsync(version);
        foreach ((string tool, object arguments) in new (string, object)[]
        {
            ("list_operations", new { module = 1 }), ("describe_operation", new { operation = "" }),
            ("send_command", new { operation = "sample.create-item" }),
            ("run_query", new { operation = "sample.get-item", payload = new { ItemId } }),
            ("run_query", new { operation = "sample.get-item", payload = QueryPayload, pageSize = "25" }),
            ("send_command", new { operation = "sample.create-item", payload = CommandPayload, extensions = new { task = 42 } }),
        })
        {
            McpProtocolException exception = await Should.ThrowAsync<McpProtocolException>(() => session.CallAsync(tool, arguments),
                $"{tool}: {JsonSerializer.Serialize(arguments)}");
            exception.ErrorCode.ShouldBe(McpErrorCode.InvalidParams);
            session.Gateway.ReceivedCalls().ShouldBeEmpty();
        }
    }
}
