using System.IO.Pipelines;
using System.Reflection;
using System.Text.Json;
using Hexalith.McpCli.Core;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Core.Execution;
using Hexalith.McpCli.Core.Settings;
using Hexalith.McpCli.Sample.Contracts;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using ModelContextProtocol.Client;
using ModelContextProtocol.Protocol;
using ModelContextProtocol.Server;
using ModelContextProtocol;
using Shouldly;

namespace Hexalith.McpCli.Mcp.Tests;

/// <summary>Exercises the SDK's built-in list and call dispatch over JSON-RPC streams.</summary>
public sealed class McpProtocolTests
{
    /// <summary>Fresh SDK sessions keep the fixed surface as the catalog grows and carry Core discovery documents.</summary>
    [Theory]
    [InlineData(false, false, false, "2025-06-18")]
    [InlineData(true, false, false, "2025-06-18")]
    [InlineData(false, true, false, "2025-06-18")]
    [InlineData(true, true, false, "2025-06-18")]
    [InlineData(false, false, true, "2025-06-18")]
    [InlineData(true, false, true, "2025-06-18")]
    [InlineData(false, false, false, "2026-07-28")]
    [InlineData(true, false, false, "2026-07-28")]
    [InlineData(false, true, false, "2026-07-28")]
    [InlineData(true, true, false, "2026-07-28")]
    [InlineData(false, false, true, "2026-07-28")]
    [InlineData(true, false, true, "2026-07-28")]
    public async Task DiscoversAndCallsWithTheCoreDocumentAsync(bool readOnly, bool hasGatewayUrl,
        bool expandedCatalog, string protocolVersion)
    {
        using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(10));
        ResolvedSettings settings = new(hasGatewayUrl ? new Uri("https://gateway.example/") : null, null, "session-tenant", null,
            false, new HashSet<string>(), "json", null, readOnly, false, null, new Dictionary<string, string>());
        Assembly[] manifest = expandedCatalog
            ? [typeof(CreateItemCommand).Assembly, typeof(Catalog.Routing.Contracts.Module).Assembly,
                typeof(Catalog.Lint.Contracts.Module).Assembly,
                typeof(Manifest.MarkedEmpty.Contracts.Module).Assembly]
            : [typeof(CreateItemCommand).Assembly];
        var services = new ServiceCollection();
        services.AddLogging();
        services.AddMcpCliCore(settings, () => manifest, _ => { });
        services.AddMcpCliMcpServer(settings);
        using ServiceProvider provider = services.BuildServiceProvider();
        McpServerOptions options = provider.GetRequiredService<IOptions<McpServerOptions>>().Value;
        var clientToServer = new Pipe();
        var serverToClient = new Pipe();
        await using var serverTransport = new StreamServerTransport(
            clientToServer.Reader.AsStream(), serverToClient.Writer.AsStream(), "test-server");
        var clientTransport = new StreamClientTransport(
            clientToServer.Writer.AsStream(), serverToClient.Reader.AsStream());
        await using McpServer server = McpServer.Create(serverTransport, options,
            provider.GetRequiredService<ILoggerFactory>(), provider);
        Task serverTask = server.RunAsync(timeout.Token);
        await using McpClient client = await McpClient.CreateAsync(clientTransport,
            new McpClientOptions { ProtocolVersion = protocolVersion }, cancellationToken: timeout.Token);
        client.NegotiatedProtocolVersion.ShouldBe(protocolVersion);

        IList<McpClientTool> tools = await client.ListToolsAsync(cancellationToken: timeout.Token);
        tools.Select(tool => tool.Name).ShouldBe(readOnly
            ? new[] { "list_modules", "list_operations", "describe_operation", "run_query" }
            : new[] { "list_modules", "list_operations", "describe_operation", "send_command", "run_query" });
        foreach (McpClientTool tool in tools)
        {
            string description = tool.ProtocolTool.Description.ShouldNotBeNull();
            description.ShouldContain("Purpose:");
            description.ShouldContain("Use when:");
            description.ShouldContain("Next:");
            tool.ProtocolTool.Annotations.ShouldNotBeNull().ReadOnlyHint.ShouldBe(tool.Name != "send_command");
        }

        tools.Single(tool => tool.Name == "list_modules").ProtocolTool.Description.ShouldNotBeNull()
            .ShouldContain("Next: Call list_operations");
        tools.Single(tool => tool.Name == "list_operations").ProtocolTool.Description.ShouldNotBeNull()
            .ShouldContain("Next: Call describe_operation");
        string describeGuidance = tools.Single(tool => tool.Name == "describe_operation")
            .ProtocolTool.Description.ShouldNotBeNull();
        describeGuidance.ShouldContain("Next: If submittable, call run_query for a read");
        describeGuidance.ShouldContain("send_command for a write");

        if (!readOnly)
        {
            Tool write = tools.Single(tool => tool.Name == "send_command").ProtocolTool;
            var annotations = write.Annotations.ShouldNotBeNull();
            annotations.IdempotentHint.ShouldBe(false);
            annotations.DestructiveHint.ShouldBe(true);
            write.Description.ShouldNotBeNull().ShouldContain("does not prove rejection, so do not resubmit automatically");
        }

        ICatalog catalog = provider.GetRequiredService<ICatalog>();
        CallToolResult modules = await client.CallToolAsync("list_modules", new Dictionary<string, object?>(),
            cancellationToken: timeout.Token);
        JsonElement moduleDocument = AssertCoreDocument(modules, catalog.ListModules().Document.ShouldNotBeNull());
        moduleDocument.GetProperty("modules").GetArrayLength().ShouldBe(expandedCatalog ? 4 : 1);
        JsonElement sampleModule = moduleDocument.GetProperty("modules").EnumerateArray()
            .Single(item => item.GetProperty("name").GetString() == "sample");
        sampleModule.GetProperty("operationCount").GetInt32().ShouldBe(3);
        if (expandedCatalog)
        {
            JsonElement emptyModule = moduleDocument.GetProperty("modules").EnumerateArray()
                .Single(item => item.GetProperty("name").GetString() == "marked-empty");
            emptyModule.GetProperty("operationCount").GetInt32().ShouldBe(0);
        }

        foreach (string? kind in new string?[] { null, "read", "write" })
        {
            var arguments = new Dictionary<string, object?> { ["module"] = "sample" };
            if (kind is not null)
            {
                arguments["kind"] = kind;
            }

            CallToolResult operations = await client.CallToolAsync("list_operations", arguments,
                cancellationToken: timeout.Token);
            JsonElement operationDocument = AssertCoreDocument(operations,
                catalog.ListOperations("sample", kind).Document.ShouldNotBeNull());
            operationDocument.GetProperty("module").GetString().ShouldBe("sample");
            JsonElement.ArrayEnumerator rows = operationDocument.GetProperty("operations").EnumerateArray();
            rows.Count().ShouldBe(kind is null ? 3 : kind == "read" ? 1 : 2);
            if (kind is not null)
            {
                rows.ShouldAllBe(row => row.GetProperty("kind").GetString() == kind);
            }
        }

        CallToolResult invalidKind = await client.CallToolAsync("list_operations",
            new Dictionary<string, object?> { ["module"] = "sample", ["kind"] = "Read" }, cancellationToken: timeout.Token);
        AssertCoreDocument(invalidKind, new
        {
            error = new OperationError("invalid_arguments", Message: "kind must be read or write", Argument: "kind"),
        }, isError: true);

        foreach (string operation in new[] { "sample.get-item", "sample.create-item" })
        {
            bool isRead = operation == "sample.get-item";
            CallToolResult description = await client.CallToolAsync("describe_operation",
                new Dictionary<string, object?> { ["operation"] = operation }, cancellationToken: timeout.Token);
            JsonElement document = AssertCoreDocument(description, catalog.Describe(operation).Document.ShouldNotBeNull());
            document.GetProperty("schema").GetProperty("properties").GetProperty("ItemId");
            document.TryGetProperty("example", out _).ShouldBeFalse();
            JsonElement envelope = document.GetProperty("envelope");
            envelope.GetProperty("fixedTenant").GetString().ShouldBe("sample-tenant");
            envelope.GetProperty("aggregateIdRequired").GetBoolean().ShouldBeFalse();
            envelope.GetProperty("idempotencyKeyRequired").GetBoolean().ShouldBeFalse();
            envelope.GetProperty("arguments").EnumerateArray().Select(item => item.GetString()).ShouldBe(isRead
                ? new[] { "aggregateId", "entityId", "pageSize", "offset", "cursor" }
                : new[] { "aggregateId", "correlationId", "idempotencyKey", "extensions" });
            document.GetProperty("lintFindings").ValueKind.ShouldBe(JsonValueKind.Array);
            document.GetProperty("submittable").GetBoolean().ShouldBe(hasGatewayUrl && (!readOnly || operation == "sample.get-item"));
            if (!hasGatewayUrl || (readOnly && operation == "sample.create-item"))
            {
                document.GetProperty("reason").GetString().ShouldBe(readOnly && operation == "sample.create-item"
                    ? "read_only" : "configuration_invalid");
            }
            else
            {
                document.TryGetProperty("reason", out _).ShouldBeFalse();
            }
        }

        if (expandedCatalog)
        {
            CallToolResult emptyOperations = await client.CallToolAsync("list_operations",
                new Dictionary<string, object?> { ["module"] = "marked-empty" }, cancellationToken: timeout.Token);
            JsonElement emptyDocument = AssertCoreDocument(emptyOperations,
                catalog.ListOperations("marked-empty").Document.ShouldNotBeNull());
            emptyDocument.GetProperty("module").GetString().ShouldBe("marked-empty");
            emptyDocument.GetProperty("operations").GetArrayLength().ShouldBe(0);

            CallToolResult addedOperations = await client.CallToolAsync("list_operations",
                new Dictionary<string, object?> { ["module"] = "routing-fixture" }, cancellationToken: timeout.Token);
            JsonElement addedDocument = AssertCoreDocument(addedOperations,
                catalog.ListOperations("routing-fixture").Document.ShouldNotBeNull());
            addedDocument.GetProperty("operations").GetArrayLength().ShouldBeGreaterThan(0);
            CallToolResult example = await client.CallToolAsync("describe_operation",
                new Dictionary<string, object?> { ["operation"] = "routing-fixture.envelope-item" },
                cancellationToken: timeout.Token);
            JsonElement exampleDocument = AssertCoreDocument(example,
                catalog.Describe("routing-fixture.envelope-item").Document.ShouldNotBeNull());
            exampleDocument.GetProperty("example").GetProperty("ItemId").GetString()
                .ShouldBe("01ARZ3NDEKTSV4RRFFQ69G5FAV");
            CallToolResult lint = await client.CallToolAsync("describe_operation",
                new Dictionary<string, object?> { ["operation"] = "lint-fixture.inspect-item" },
                cancellationToken: timeout.Token);
            JsonElement lintDocument = AssertCoreDocument(lint,
                catalog.Describe("lint-fixture.inspect-item").Document.ShouldNotBeNull());
            lintDocument.GetProperty("lintFindings").GetArrayLength().ShouldBeGreaterThan(0);
        }

        IList<McpClientTool> toolsAfterCatalog = await client.ListToolsAsync(cancellationToken: timeout.Token);
        toolsAfterCatalog.Select(tool => tool.Name).ShouldBe(tools.Select(tool => tool.Name));

        CallToolResult unknownModule = await client.CallToolAsync("list_operations",
            new Dictionary<string, object?> { ["module"] = "smple" }, cancellationToken: timeout.Token);
        JsonElement unknownDocument = AssertCoreDocument(unknownModule,
            new { error = catalog.ListOperations("smple").Error.ShouldNotBeNull() }, isError: true);
        unknownDocument.GetProperty("error").GetProperty("code").GetString().ShouldBe("unknown_module");
        JsonElement suggestions = unknownDocument.GetProperty("error").GetProperty("suggestions");
        suggestions.GetArrayLength().ShouldBe(expandedCatalog ? 3 : 1);
        suggestions.EnumerateArray().Select(item => item.GetString()).ShouldContain("sample");

        CallToolResult failure = await client.CallToolAsync("describe_operation",
            new Dictionary<string, object?> { ["operation"] = "sample.does-not-exist" },
            cancellationToken: timeout.Token);
        JsonElement error = AssertCoreDocument(failure,
            new { error = catalog.Describe("sample.does-not-exist").Error.ShouldNotBeNull() }, isError: true);
        error.GetProperty("error").GetProperty("code").GetString().ShouldBe("unknown_operation");

        foreach (Dictionary<string, object?> arguments in new[]
        {
            new Dictionary<string, object?>(),
            new Dictionary<string, object?> { ["module"] = "" },
        })
        {
            McpProtocolException invalidModule = await Should.ThrowAsync<McpProtocolException>(() =>
                client.CallToolAsync("list_operations", arguments, cancellationToken: timeout.Token).AsTask());
            invalidModule.ErrorCode.ShouldBe(McpErrorCode.InvalidParams);
            invalidModule.Message.ShouldBe("Request failed (remote): module is required and must be non-empty.");
        }
        McpProtocolException invalidOperation = await Should.ThrowAsync<McpProtocolException>(() =>
            client.CallToolAsync("describe_operation", new Dictionary<string, object?> { ["operation"] = " " },
                cancellationToken: timeout.Token).AsTask());
        invalidOperation.ErrorCode.ShouldBe(McpErrorCode.InvalidParams);
        invalidOperation.Message.ShouldBe("Request failed (remote): operation is required and must be non-empty.");

        timeout.Cancel();
        try
        {
            await serverTask;
        }
        catch (OperationCanceledException)
        {
        }
    }

    private static JsonElement AssertCoreDocument<T>(CallToolResult result, T expected, bool isError = false)
    {
        result.IsError.ShouldBe(isError);
        JsonElement actual = result.StructuredContent.ShouldNotBeNull();
        JsonElement canonical = JsonSerializer.SerializeToElement(expected, Core.Serialization.McpCliJson.Result);
        JsonElement.DeepEquals(actual, canonical).ShouldBeTrue();
        string text = result.Content.Single().ShouldBeOfType<TextContentBlock>().Text;
        using JsonDocument parsed = JsonDocument.Parse(text);
        JsonElement.DeepEquals(parsed.RootElement, actual).ShouldBeTrue();
        return actual;
    }
}
