using System.IO.Pipelines;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
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

/// <summary>Checks matching query execution through both heads and the HTTP gateway client.</summary>
public sealed class CliMcpQueryParityTests
{
    private const string ItemId = "01ARZ3NDEKTSV4RRFFQ69G5FAV";

    /// <summary>
    /// A payload tenant that disagrees with the envelope, or a tenant or actor member the query does not declare, fails
    /// with the same complete document through both heads before any Gateway call.
    /// </summary>
    /// <param name="module">The fixture module: the lint fixture declares a tenant member, Parties declares none.</param>
    /// <param name="member">The disagreeing or undeclared payload member.</param>
    [Theory]
    [InlineData("lint", "Tenant")]
    [InlineData("parties", "Tenant")]
    [InlineData("parties", "ActorId")]
    public async Task IdentityMismatchFailsInBothHeadsBeforeTheGatewayAsync(string module, string member)
    {
        string directory = Path.Combine(Path.GetTempPath(), "mcpcli-query-identity-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(directory);
        try
        {
            await using var gateway = new ScriptedGateway(_ => ScriptedGateway.Response(200, "OK", "application/json",
                """{"correlationId":"01J9MZHXT3RKM0VWXRXGSJDATK","payload":{},"success":true}"""));
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            bool lint = module == "lint";
            string operation = lint ? "lint-fixture.inspect-item" : "parties.get-party";
            Func<IReadOnlyList<System.Reflection.Assembly>> manifest = lint
                ? () => [typeof(global::Catalog.Lint.Contracts.Module).Assembly]
                : () => [System.Reflection.Assembly.Load(new System.Reflection.AssemblyName("Hexalith.Parties.Contracts"))];
            JsonObject payload = lint
                ? JsonNode.Parse(QueryCliHarness.InspectPayload)!.AsObject()
                : new JsonObject { ["PartyId"] = "party-identity" };
            payload[member] = "tenant-b";
            object[] violations = lint
                ? [new { path = "/Tenant", message = "The payload tenant disagrees with the resolved tenant." }]
                :
                [
                    new { path = "/", message = $"Some additional properties did not match the required schema: [\"{member}\"]" },
                    new { path = "/" + member, message = "All values fail against the false schema" },
                ];
            string expected = JsonSerializer.Serialize(new { error = new { code = "validation_failed", operation, violations } });
            string[] globals = ["--url", gateway.Url, "--tenant", "session-tenant", "--actor", "operator-1"];
            IReadOnlyDictionary<string, string?> environment = new Dictionary<string, string?>();

            HeadResult cli = await BothHeads.InvokeCliAsync(store, manifest, environment,
                ["query", operation, "--payload", payload.ToJsonString(), .. globals]);
            HeadResult mcp = await BothHeads.InvokeMcpAsync(store, manifest, environment, globals, "run_query",
                new Dictionary<string, object?> { ["operation"] = operation, ["payload"] = payload.ToJsonString() });

            BothHeads.AssertDocument(cli, expected, isError: true);
            BothHeads.AssertDocument(mcp, expected, isError: true);
            HeadDiagnostics.AssertNoGateway(cli);
            HeadDiagnostics.AssertNoGateway(mcp);
            gateway.Requests.ShouldBeEmpty();
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>CLI and MCP send the same query envelope and return the same document.</summary>
    [Fact]
    public async Task QueryDocumentsAndGatewayRequestsMatchAsync()
    {
        using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(10));
        string directory = Path.Combine(Path.GetTempPath(), "mcpcli-query-parity-" + Guid.NewGuid().ToString("N"));
        using var portProbe = new TcpListener(IPAddress.Loopback, 0);
        portProbe.Start();
        int port = ((IPEndPoint)portProbe.LocalEndpoint).Port;
        portProbe.Stop();
        string url = $"http://127.0.0.1:{port}/";
        using var gateway = new HttpListener();
        gateway.Prefixes.Add(url);
        gateway.Start();
        var captured = new List<JsonElement>();
        Task responses = Task.Run(async () =>
        {
            for (int index = 0; index < 2; index++)
            {
                HttpListenerContext request = await gateway.GetContextAsync();
                request.Request.HttpMethod.ShouldBe("POST");
                request.Request.Url!.AbsolutePath.ShouldBe("/api/v1/queries");
                using var reader = new StreamReader(request.Request.InputStream);
                string body = await reader.ReadToEndAsync();
                captured.Add(JsonDocument.Parse(body).RootElement.Clone());
                byte[] response = Encoding.UTF8.GetBytes("""
                    {"correlationId":"01J9MZHXT3RKM0VWXRXGSJDATK","payload":{"title":"Hello"},"success":true}
                    """);
                request.Response.ContentType = "application/json";
                request.Response.ContentLength64 = response.Length;
                await request.Response.OutputStream.WriteAsync(response);
                request.Response.Close();
            }
        }, timeout.Token);

        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            Func<IReadOnlyList<System.Reflection.Assembly>> manifest = () => [typeof(GetItemQuery).Assembly];
            var settings = new ResolvedSettings(new Uri(url), null, "sample-tenant", null, false,
                new HashSet<string>(), "json", null, false, false, null, new Dictionary<string, string>());
            var services = new ServiceCollection();
            services.AddLogging();
            services.AddMcpCliCore(settings, manifest, _ => { });
            services.AddMcpCliMcpServer(settings);
            using ServiceProvider provider = services.BuildServiceProvider();
            McpServerOptions options = provider.GetRequiredService<IOptions<McpServerOptions>>().Value;
            var clientToServer = new Pipe();
            var serverToClient = new Pipe();
            await using var serverTransport = new StreamServerTransport(
                clientToServer.Reader.AsStream(), serverToClient.Writer.AsStream(), "query-parity-server");
            var clientTransport = new StreamClientTransport(
                clientToServer.Writer.AsStream(), serverToClient.Reader.AsStream());
            await using McpServer server = McpServer.Create(serverTransport, options,
                provider.GetRequiredService<ILoggerFactory>(), provider);
            Task serverTask = server.RunAsync(timeout.Token);
            await using McpClient client = await McpClient.CreateAsync(clientTransport,
                new McpClientOptions { ProtocolVersion = "2025-06-18" }, cancellationToken: timeout.Token);

            string payload = $$"""{"ItemId":"{{ItemId}}"}""";
            TextWriter originalOut = Console.Out;
            using var output = new StringWriter();
            try
            {
                Console.SetOut(output);
                int exit = await new CliRunner(store, manifest).InvokeAsync(
                    ["query", "sample.get-item", "--payload", payload, "--page-size", "25", "--url", url],
                    TestContext.Current.CancellationToken);
                exit.ShouldBe(0);
            }
            finally
            {
                Console.SetOut(originalOut);
            }

            CallToolResult mcp = await client.CallToolAsync("run_query", new Dictionary<string, object?>
            {
                ["operation"] = "sample.get-item", ["payload"] = payload, ["pageSize"] = 25,
            }, cancellationToken: timeout.Token);
            mcp.IsError.ShouldBe(false);
            JsonElement cliDocument = JsonDocument.Parse(output.ToString()).RootElement;
            JsonElement.DeepEquals(cliDocument, mcp.StructuredContent.ShouldNotBeNull()).ShouldBeTrue();
            await responses.WaitAsync(timeout.Token);
            captured.Count.ShouldBe(2);
            JsonElement.DeepEquals(captured[0], captured[1]).ShouldBeTrue();
            captured[0].GetProperty("tenant").GetString().ShouldBe("sample-tenant");
            captured[0].GetProperty("domain").GetString().ShouldBe("sample");

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
            gateway.Stop();
            if (Directory.Exists(directory))
            {
                Directory.Delete(directory, recursive: true);
            }
        }
    }
}
