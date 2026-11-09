using System.Text.Json;
using Hexalith.McpCli.Integration.Tests;
using Shouldly;

namespace Hexalith.McpCli.Cli.Tests;

/// <summary>Verifies the live process harness's CLI/MCP documents and complete channels without starting topology.</summary>
public sealed class BoundaryProcessHarnessTests
{
    /// <summary>Successful and failed process calls retain all public channels and exactly one request per head.</summary>
    /// <param name="command">Whether to submit a Command.</param>
    /// <param name="refused">Whether the Gateway refuses authentication.</param>
    [Theory]
    [InlineData(false, false)]
    [InlineData(true, false)]
    [InlineData(false, true)]
    [InlineData(true, true)]
    public async Task ProcessHeadsPreserveCompleteDocumentsAndChannelsAsync(bool command, bool refused)
    {
        string directory = Path.Combine(Path.GetTempPath(), "mcpcli-process-boundary-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(directory);
        try
        {
            await using var gateway = new ScriptedGateway(request => refused
                ? ScriptedGateway.Response(401, "Unauthorized", null, string.Empty)
                : command ? ScriptedGateway.AcceptCommand(request)
                : ScriptedGateway.Response(200, "OK", "application/json", """{"correlationId":"01J9MZHXT3RKM0VWXRXGSJDATK","payload":{"id":"process-party"}}"""));
            var environment = new Dictionary<string, string?> { ["EVENTSTORE_URL"] = gateway.Url };
            string profile = Path.Combine(directory, "mcpcli.json");
            string operation = command ? "parties.deactivate-party" : "parties.get-party";
            const string payload = """{"PartyId":"process-party"}""";
            HeadResult cli = await BoundaryHeads.InvokeCliAsync(profile, environment,
                [command ? "send" : "query", operation, "--payload", payload, "--tenant", "tenant-a"]);
            HeadResult mcp = await BoundaryHeads.InvokeMcpAsync(profile, environment, ["--tenant", "tenant-a"],
                command ? "send_command" : "run_query", new Dictionary<string, object?> { ["operation"] = operation, ["payload"] = payload });
            string expected = refused ? """{"error":{"code":"gateway_error","status":401,"detail":"Unauthorized"}}"""
                : command ? JsonSerializer.Serialize(new { operation, messageId = "generated", correlationId = "generated",
                    tenant = "tenant-a", aggregateId = "process-party", status = "accepted" })
                : JsonSerializer.Serialize(new { operation, tenant = "tenant-a", document = new { id = "process-party" } });
            foreach (HeadResult result in new[] { cli, mcp })
            {
                BoundaryHeads.AssertDocument(result, expected, refused,
                    !refused && command ? ["messageId", "correlationId"] : []);
                HeadDiagnostics.AssertGatewayOnly(result, gateway.Url, command ? "/api/v1/commands" : "/api/v1/queries",
                    refused ? 401 : command ? 202 : 200, process: true);
            }
            gateway.Requests.Count.ShouldBe(2);
        }
        finally { Directory.Delete(directory, recursive: true); }
    }
}
