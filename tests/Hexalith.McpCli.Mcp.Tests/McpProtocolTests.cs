using System.IO.Pipelines;
using System.Text.Json;
using Hexalith.McpCli.Core;
using Hexalith.McpCli.Core.Catalog;
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
    /// <summary>Both session modes advertise only permitted tools and return the Core document.</summary>
    [Theory]
    [InlineData(false, 5, "2025-06-18")]
    [InlineData(true, 4, "2025-06-18")]
    [InlineData(false, 5, "2026-07-28")]
    [InlineData(true, 4, "2026-07-28")]
    public async Task DiscoversAndCallsWithTheCoreDocumentAsync(bool readOnly, int expectedTools, string protocolVersion)
    {
        using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(10));
        ResolvedSettings settings = new(new Uri("https://gateway.example/"), null, "sample-tenant", null,
            false, new HashSet<string>(), "json", null, readOnly, false, null, new Dictionary<string, string>());
        var services = new ServiceCollection();
        services.AddLogging();
        services.AddMcpCliCore(settings, () => [typeof(CreateItemCommand).Assembly], _ => { });
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

        IList<McpClientTool> tools = await client.ListToolsAsync(cancellationToken: timeout.Token);
        tools.Count.ShouldBe(expectedTools);
        tools.Select(tool => tool.Name).ShouldBe(readOnly
            ? new[] { "list_modules", "list_operations", "describe_operation", "run_query" }
            : new[] { "list_modules", "list_operations", "describe_operation", "send_command", "run_query" });
        CallToolResult result = await client.CallToolAsync("list_modules", new Dictionary<string, object?>(),
            cancellationToken: timeout.Token);
        result.IsError.ShouldBe(false);
        JsonElement structured = result.StructuredContent.ShouldNotBeNull();
        structured.GetProperty("modules").GetArrayLength().ShouldBe(1);
        JsonElement expected = JsonSerializer.SerializeToElement(provider.GetRequiredService<ICatalog>().ListModules().Document,
            Core.Serialization.McpCliJson.Result);
        JsonElement.DeepEquals(structured, expected).ShouldBeTrue();

        CallToolResult failure = await client.CallToolAsync("describe_operation",
            new Dictionary<string, object?> { ["operation"] = "sample.does-not-exist" },
            cancellationToken: timeout.Token);
        failure.IsError.ShouldBe(true);
        JsonElement error = failure.StructuredContent.ShouldNotBeNull();
        error.GetProperty("error").GetProperty("code").GetString().ShouldBe("unknown_operation");
        string text = failure.Content.Single().ShouldBeOfType<TextContentBlock>().Text;
        JsonElement.DeepEquals(JsonDocument.Parse(text).RootElement, error).ShouldBeTrue();

        McpProtocolException invalidModule = await Should.ThrowAsync<McpProtocolException>(() =>
            client.CallToolAsync("list_operations", new Dictionary<string, object?> { ["module"] = "" },
                cancellationToken: timeout.Token).AsTask());
        invalidModule.ErrorCode.ShouldBe(McpErrorCode.InvalidParams);
        McpProtocolException invalidOperation = await Should.ThrowAsync<McpProtocolException>(() =>
            client.CallToolAsync("describe_operation", new Dictionary<string, object?> { ["operation"] = " " },
                cancellationToken: timeout.Token).AsTask());
        invalidOperation.ErrorCode.ShouldBe(McpErrorCode.InvalidParams);

        timeout.Cancel();
        try
        {
            await serverTask;
        }
        catch (OperationCanceledException)
        {
        }
    }
}
