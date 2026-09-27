using System.IO.Pipelines;
using System.Text.Json;
using Hexalith.McpCli.Cli;
using Hexalith.McpCli.Core;
using Hexalith.McpCli.Core.Settings;
using Hexalith.McpCli.Mcp;
using Hexalith.McpCli.Sample.Contracts;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using ModelContextProtocol.Client;
using ModelContextProtocol.Protocol;
using ModelContextProtocol.Server;
using Shouldly;

namespace Hexalith.McpCli.Cli.Tests;

/// <summary>Compares both generic heads against one synthetic Contracts catalog.</summary>
public sealed class CliMcpDiscoveryParityTests
{
    /// <summary>The CLI and MCP protocol return equal discovery documents and lookup errors.</summary>
    [Fact]
    public async Task DiscoveryDocumentsMatchAcrossHeadsAsync()
    {
        using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(10));
        string directory = Path.Combine(Path.GetTempPath(), "mcpcli-parity-" + Guid.NewGuid().ToString("N"));
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            Func<IReadOnlyList<System.Reflection.Assembly>> manifest = () => [typeof(CreateItemCommand).Assembly];
            ResolvedSettings settings = new(new Uri("https://gateway.example/"), null, "sample-tenant", null,
                false, new HashSet<string>(), "json", null, false, false, null, new Dictionary<string, string>());
            var services = new ServiceCollection();
            services.AddLogging();
            services.AddMcpCliCore(settings, manifest, _ => { });
            services.AddMcpCliMcpServer(settings);
            using ServiceProvider provider = services.BuildServiceProvider();
            McpServerOptions options = provider.GetRequiredService<IOptions<McpServerOptions>>().Value;
            var clientToServer = new Pipe();
            var serverToClient = new Pipe();
            await using var serverTransport = new StreamServerTransport(
                clientToServer.Reader.AsStream(), serverToClient.Writer.AsStream(), "parity-server");
            var clientTransport = new StreamClientTransport(
                clientToServer.Writer.AsStream(), serverToClient.Reader.AsStream());
            await using McpServer server = McpServer.Create(serverTransport, options,
                provider.GetRequiredService<ILoggerFactory>(), provider);
            Task serverTask = server.RunAsync(timeout.Token);
            await using McpClient client = await McpClient.CreateAsync(clientTransport,
                new McpClientOptions { ProtocolVersion = "2025-06-18" }, cancellationToken: timeout.Token);

            await CompareAsync(store, manifest, client, ["modules"], "list_modules", new Dictionary<string, object?>());
            await CompareAsync(store, manifest, client, ["operations", "sample"], "list_operations",
                new Dictionary<string, object?> { ["module"] = "sample" });
            await CompareAsync(store, manifest, client, ["describe", "sample.create-item"], "describe_operation",
                new Dictionary<string, object?> { ["operation"] = "sample.create-item" });
            await CompareAsync(store, manifest, client, ["operations", "missing"], "list_operations",
                new Dictionary<string, object?> { ["module"] = "missing" }, expectedError: true);

            timeout.Cancel();
            try
            {
                await serverTask;
            }
            catch (OperationCanceledException)
            {
            }
        }
        finally
        {
            if (Directory.Exists(directory))
            {
                Directory.Delete(directory, recursive: true);
            }
        }
    }

    private static async Task CompareAsync(ProfileStore store, Func<IReadOnlyList<System.Reflection.Assembly>> manifest,
        McpClient client, string[] cliArgs, string tool, Dictionary<string, object?> arguments, bool expectedError = false)
    {
        TextWriter originalOut = Console.Out;
        using var output = new StringWriter();
        try
        {
            Console.SetOut(output);
            int exit = await new CliRunner(store, manifest).CreateRoot()
                .Parse([.. cliArgs, "--url", "https://gateway.example/", "--tenant", "sample-tenant"]).InvokeAsync();
            exit.ShouldBe(expectedError ? 2 : 0);
        }
        finally
        {
            Console.SetOut(originalOut);
        }

        CallToolResult mcp = await client.CallToolAsync(tool, arguments);
        mcp.IsError.ShouldBe(expectedError);
        JsonElement cli = JsonDocument.Parse(output.ToString()).RootElement;
        JsonElement structured = mcp.StructuredContent.ShouldNotBeNull();
        JsonElement.DeepEquals(cli, structured).ShouldBeTrue();
    }
}
