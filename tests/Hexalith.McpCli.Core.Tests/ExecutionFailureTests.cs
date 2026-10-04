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
using StringContracts = global::Catalog.String.Contracts;
using Routing = global::Catalog.Routing.Contracts;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Checks stable execution failures and submission counts for both operation kinds.</summary>
public sealed class ExecutionFailureTests
{
    private const string ItemId = "01ARZ3NDEKTSV4RRFFQ69G5FAV";

    /// <summary>Both call kinds retain the exact client status and make one submission.</summary>
    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task GatewayFailuresKeepClientStatusAfterOneCallAsync(bool command)
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        var failure = new EventStoreGatewayException(202, "Malformed success", detail: "Invalid response", retryable: false);
        gateway.SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>())
            .Returns(Task.FromException<SubmitCommandResponse>(failure));
        gateway.SubmitQueryAsync(Arg.Any<SubmitQueryRequest>(), Arg.Any<string?>(), Arg.Any<CancellationToken>())
            .Returns(Task.FromException<EventStoreQueryResult>(failure));
        OperationCall call = command
            ? new SendCommandArguments("sample.create-item", $$"""{"ItemId":"{{ItemId}}","Title":"Hello"}""")
            : new RunQueryArguments("string-fixture.list-items", "{}");

        OperationOutcome outcome = await Executor(gateway).ExecuteAsync(call, Context(), TestContext.Current.CancellationToken);

        outcome.Document.ShouldBeNull();
        AssertJson(outcome.Error.ShouldNotBeNull(), """{"code":"gateway_error","status":202,"detail":"Invalid response","retryable":false}""");
        gateway.ReceivedCalls().Count().ShouldBe(1);
    }

    /// <summary>Unexpected exception content is never copied into a public failure.</summary>
    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task UnexpectedFailuresHideTokenAndStackAfterOneCallAsync(bool command)
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        var failure = new IOException("token-secret /private/profile.json at Example.Stack()");
        gateway.SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>())
            .Returns(Task.FromException<SubmitCommandResponse>(failure));
        gateway.SubmitQueryAsync(Arg.Any<SubmitQueryRequest>(), Arg.Any<string?>(), Arg.Any<CancellationToken>())
            .Returns(Task.FromException<EventStoreQueryResult>(failure));
        OperationCall call = command
            ? new SendCommandArguments("sample.create-item", $$"""{"ItemId":"{{ItemId}}","Title":"Hello"}""")
            : new RunQueryArguments("string-fixture.list-items", "{}");

        OperationOutcome outcome = await Executor(gateway).ExecuteAsync(call, Context(), TestContext.Current.CancellationToken);

        outcome.Document.ShouldBeNull();
        AssertJson(outcome.Error.ShouldNotBeNull(), """{"code":"internal_error","message":"Operation execution failed."}""");
        gateway.ReceivedCalls().Count().ShouldBe(1);
    }

    /// <summary>Execution and describe share canonical case-sensitive lookup and ordered suggestions.</summary>
    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task UnknownOperationMatchesDescribeWithNoSubmissionAsync(bool command)
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        CatalogProvider provider = Provider();
        var availability = new ExecutionAvailability(false, true);
        const string requested = "STRING-fixture.looku";
        OperationCall call = command
            ? new SendCommandArguments(requested, "{}")
            : new RunQueryArguments(requested, "{}");
        OperationOutcome outcome = await new OperationExecutor(provider, availability, gateway, strict: false)
            .ExecuteAsync(call, Context(), TestContext.Current.CancellationToken);
        OperationError described = new CatalogService(provider, availability, strict: false).Describe(requested).Error.ShouldNotBeNull();

        outcome.Document.ShouldBeNull();
        OperationError error = outcome.Error.ShouldNotBeNull();
        error.Code.ShouldBe("unknown_operation");
        error.Operation.ShouldBe(requested);
        error.Suggestions.ShouldBe(described.Suggestions);
        error.Suggestions.ShouldNotBeNull().Count.ShouldBeLessThanOrEqualTo(3);
        gateway.ReceivedCalls().ShouldBeEmpty();
    }

    /// <summary>An invalid String accessor reports the escaped mapped payload pointer.</summary>
    [Fact]
    public async Task EscapedAccessorIdentifierUsesPayloadPointerAsync()
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        OperationOutcome outcome = await Executor(gateway).ExecuteAsync(
            new RunQueryArguments("string-fixture.escaped-key", """{"key/~":"bad/id"}"""),
            Context(), TestContext.Current.CancellationToken);

        outcome.Document.ShouldBeNull();
        AssertJson(outcome.Error.ShouldNotBeNull(),
            """{"code":"validation_failed","operation":"string-fixture.escaped-key","violations":[{"path":"/key~1~0","message":"The aggregate identifier does not match the module and Gateway rules."}]}""");
        gateway.ReceivedCalls().ShouldBeEmpty();
    }

    /// <summary>Missing tenant, invalid syntax, cursor length, and offset conflict have distinct messages.</summary>
    [Theory]
    [InlineData(null, null, null, "/tenant", "A tenant is required for this operation.")]
    [InlineData("bad/tenant", null, null, "/tenant", "The tenant does not match the Gateway tenant pattern.")]
    [InlineData("acme", "long", null, "/cursor", "Cursor must be at most 4096 characters.")]
    [InlineData("acme", "cursor", 0, "/cursor", "Cursor cannot be combined with offset.")]
    public async Task ValidationMessagesIdentifyTheFailedRuleAsync(string? tenant, string? cursorKind, int? offset,
        string path, string message)
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        string? cursor = cursorKind == "long" ? new string('x', 4097) : cursorKind;
        OperationOutcome outcome = await Executor(gateway).ExecuteAsync(
            new RunQueryArguments("routing-fixture.get-http2-status", "{}", AggregateId: ItemId,
                Cursor: cursor, Offset: offset), new EnvelopeContext(tenant, null, false, new HashSet<string>()),
            TestContext.Current.CancellationToken);

        outcome.Document.ShouldBeNull();
        outcome.Error.ShouldNotBeNull().Violations.ShouldNotBeNull().ShouldHaveSingleItem().ShouldBe(new(path, message));
        gateway.ReceivedCalls().ShouldBeEmpty();
    }

    private static CatalogProvider Provider() => new(
        () => [typeof(CreateItemCommand).Assembly, typeof(StringContracts.Module).Assembly, typeof(Routing.Module).Assembly],
        new RecordingLogger<CatalogProvider>());

    private static IOperationExecutor Executor(IEventStoreGatewayClient gateway)
        => new OperationExecutor(Provider(), new ExecutionAvailability(false, true), gateway, strict: false);

    private static EnvelopeContext Context()
        => new("sample-tenant", null, false, new HashSet<string>());

    private static void AssertJson(object actual, string expected)
    {
        using JsonDocument expectedDocument = JsonDocument.Parse(expected);
        JsonElement json = JsonSerializer.SerializeToElement(actual, McpCliJson.Result);
        JsonElement.DeepEquals(json, expectedDocument.RootElement).ShouldBeTrue(json.GetRawText());
    }
}
