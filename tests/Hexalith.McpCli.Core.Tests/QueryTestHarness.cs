using System.Reflection;
using System.Text.Json;
using Hexalith.EventStore.Client.Gateway;
using Hexalith.EventStore.Contracts.Queries;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Core.Execution;
using Hexalith.McpCli.Core.Serialization;
using NSubstitute;
using Shouldly;
using Lint = global::Catalog.Lint.Contracts;
using Routing = global::Catalog.Routing.Contracts;
using StringContracts = global::Catalog.String.Contracts;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Provides shared synthetic query inputs and exact gateway assertions.</summary>
internal static class QueryTestHarness
{
    /// <summary>The valid aggregate ULID shared by synthetic query cases.</summary>
    internal const string ItemId = "01ARZ3NDEKTSV4RRFFQ69G5FAV";
    /// <summary>The valid lint query input before trusted tenant filling.</summary>
    internal const string InspectPayload = """
        {"ItemId":"01ARZ3NDEKTSV4RRFFQ69G5FAV","ExternalId":"ordinary/reference",
         "Nested":{"Label":"item","nested/~":"value"},"Entries":[]}
        """;

    /// <summary>Builds a lazy catalog of unchanged fixture assemblies or an isolated probe.</summary>
    internal static CatalogProvider Provider(Assembly? probe = null) => new(
        () => probe is null ? [typeof(Lint.Module).Assembly, typeof(Routing.Module).Assembly, typeof(StringContracts.Module).Assembly]
            : [probe], new RecordingLogger<CatalogProvider>());

    /// <summary>Creates the shared executor with a controlled Gateway availability state.</summary>
    internal static IOperationExecutor Executor(IEventStoreGatewayClient gateway, bool hasUrl = true, Assembly? probe = null)
        => new OperationExecutor(Provider(probe), new ExecutionAvailability(false, hasUrl), gateway, strict: false);

    /// <summary>Creates trusted session state without tenant override or command extensions.</summary>
    internal static EnvelopeContext Context(string? tenant = "session-tenant") => new(tenant, null, false, new HashSet<string>());

    /// <summary>Creates a Gateway substitute with an object or null document and optional response metadata.</summary>
    internal static IEventStoreGatewayClient Gateway(QueryResponseMetadata? metadata = null, bool nullDocument = false)
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        gateway.SubmitQueryAsync(Arg.Any<SubmitQueryRequest>(), Arg.Any<string?>(), Arg.Any<CancellationToken>())
            .Returns(Task.FromResult(new EventStoreQueryResult("01J9MZHXT3RKM0VWXRXGSJDATK",
                nullDocument ? null : JsonSerializer.SerializeToElement(new { items = Array.Empty<string>() }), false, null) { Metadata = metadata }));
        return gateway;
    }

    /// <summary>Checks all expected violation locations and the absence of every Gateway call.</summary>
    internal static void AssertRefusal(OperationOutcome outcome, IEventStoreGatewayClient gateway, params string[] paths)
    {
        outcome.Document.ShouldBeNull();
        OperationError error = outcome.Error.ShouldNotBeNull();
        error.Code.ShouldBe("validation_failed");
        error.Violations.ShouldNotBeNull().ShouldNotBeEmpty();
        error.Violations.Select(item => item.Path).Distinct().Order(StringComparer.Ordinal)
            .ShouldBe(paths.Order(StringComparer.Ordinal));
        error.Violations.ShouldAllBe(item => !string.IsNullOrWhiteSpace(item.Message));
        gateway.ReceivedCalls().ShouldBeEmpty();
    }

    /// <summary>Checks a complete, single query request and its unchanged cancellation token.</summary>
    internal static void AssertRequest(IEventStoreGatewayClient gateway, SubmitQueryRequest expected)
    {
        NSubstitute.Core.ICall call = gateway.ReceivedCalls().ShouldHaveSingleItem();
        call.GetMethodInfo().Name.ShouldBe(nameof(IEventStoreGatewayClient.SubmitQueryAsync));
        object?[] arguments = call.GetArguments();
        JsonElement actual = JsonSerializer.SerializeToElement(arguments[0].ShouldBeOfType<SubmitQueryRequest>(), McpCliJson.Result);
        JsonElement.DeepEquals(actual, JsonSerializer.SerializeToElement(expected, McpCliJson.Result)).ShouldBeTrue(actual.GetRawText());
        arguments[1].ShouldBeNull();
        arguments[2].ShouldBe(TestContext.Current.CancellationToken);
    }

    /// <summary>Compares the complete canonical result with type-preserving JSON equality.</summary>
    internal static void AssertResult(OperationOutcome outcome, string expected)
    {
        outcome.Error.ShouldBeNull();
        using JsonDocument document = JsonDocument.Parse(expected);
        JsonElement actual = JsonSerializer.SerializeToElement(outcome.Document, McpCliJson.Result);
        JsonElement.DeepEquals(actual, document.RootElement).ShouldBeTrue(actual.GetRawText());
    }
}
