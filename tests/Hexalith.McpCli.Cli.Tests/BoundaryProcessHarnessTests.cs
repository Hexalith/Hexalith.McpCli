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

    /// <summary>The live acceptance assertion preserves optional Gateway business results on both process heads.</summary>
    /// <param name="withResult">Whether the Gateway returns a business result.</param>
    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task AcceptedCommandsPreserveCompleteGatewayResultsAsync(bool withResult)
    {
        string directory = Path.Combine(Path.GetTempPath(), "mcpcli-command-result-boundary-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(directory);
        string? responseBody = null;
        try
        {
            await using var gateway = new ScriptedGateway(request =>
            {
                using JsonDocument sent = JsonDocument.Parse(request.Body);
                responseBody = JsonSerializer.Serialize(new
                {
                    messageId = sent.RootElement.GetProperty("messageId").GetString(),
                    correlationId = sent.RootElement.GetProperty("correlationId").GetString(),
                    resultPayload = withResult ? new { id = "process-party", isActive = false, identifiers = new[] { "kept-result" } } : null,
                });
                return ScriptedGateway.Response(202, "Accepted", "application/json", responseBody);
            });
            var environment = new Dictionary<string, string?> { ["EVENTSTORE_URL"] = gateway.Url };
            string profile = Path.Combine(directory, "mcpcli.json");
            const string operation = "parties.deactivate-party";
            const string payload = """{"PartyId":"process-party"}""";
            foreach (bool mcp in new[] { false, true })
            {
                int before = gateway.Requests.Count;
                HeadResult result = mcp
                    ? await BoundaryHeads.InvokeMcpAsync(profile, environment, ["--tenant", "tenant-a"], "send_command",
                        new Dictionary<string, object?> { ["operation"] = operation, ["payload"] = payload })
                    : await BoundaryHeads.InvokeCliAsync(profile, environment,
                        ["send", operation, "--payload", payload, "--tenant", "tenant-a"]);
                gateway.Requests.Count.ShouldBe(before + 1);
                BoundaryHeads.AssertCommandAccepted(result, operation, "tenant-a", "process-party", gateway.Requests[^1], responseBody!);
                HeadDiagnostics.AssertGatewayOnly(result, gateway.Url, "/api/v1/commands", 202, process: true);
            }
        }
        finally { Directory.Delete(directory, recursive: true); }
    }

    /// <summary>Real CLI and MCP processes preserve every qualified 401/403 challenge and signed-grant error member.</summary>
    /// <param name="scenario">The Gateway authentication or authorization failure.</param>
    /// <param name="command">Whether to submit a Command.</param>
    /// <param name="emptyBody">Whether the 401 challenge has no response body.</param>
    [Theory]
    [InlineData("missing-token", false, false)]
    [InlineData("missing-token", true, false)]
    [InlineData("forged-token", false, false)]
    [InlineData("forged-token", true, false)]
    [InlineData("tenant_mismatch", false, false)]
    [InlineData("tenant_mismatch", true, false)]
    [InlineData("principal_not_member", false, false)]
    [InlineData("principal_not_member", true, false)]
    [InlineData("missing-token", false, true)]
    [InlineData("missing-token", true, true)]
    [InlineData("forged-token", false, true)]
    [InlineData("forged-token", true, true)]
    public async Task QualifiedCredentialRefusalsPreserveCompleteDocumentsAsync(string scenario, bool command, bool emptyBody)
    {
        const string correlation = "01J9MZHXT3RKM0VWXRXGSJDATK";
        string directory = Path.Combine(Path.GetTempPath(), "mcpcli-credential-boundary-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(directory);
        bool authentication = scenario is "missing-token" or "forged-token";
        int status = authentication ? 401 : 403;
        string reason = authentication ? "authentication_required" : scenario;
        string detail = scenario switch
        {
            "missing-token" => "Authentication is required to access this resource.",
            "forged-token" => "The provided authentication token is invalid.",
            "tenant_mismatch" => "Not authorized for tenant 'tenant-b'.",
            _ => "Not authorized for tenant 'tenant-b'. No tenant authorization claims found. Access denied.",
        };
        var problem = new Dictionary<string, object?> { ["status"] = status, ["detail"] = detail, ["reasonCode"] = reason };
        if (!authentication) problem["correlationId"] = correlation;
        string? token = scenario == "missing-token" ? null : "process-private-credential";
        try
        {
            await using var gateway = new ScriptedGateway(_ => ScriptedGateway.Response(status,
                authentication ? "Unauthorized" : "Forbidden", emptyBody ? null : "application/problem+json",
                emptyBody ? string.Empty : JsonSerializer.Serialize(problem)));
            var environment = new Dictionary<string, string?> { ["EVENTSTORE_URL"] = gateway.Url, ["EVENTSTORE_TOKEN"] = token };
            string profile = Path.Combine(directory, "mcpcli.json");
            string operation = command ? "parties.deactivate-party" : "parties.get-party";
            const string payload = """{"PartyId":"process-party"}""";
            foreach (bool mcp in new[] { false, true })
            {
                int before = gateway.Requests.Count;
                HeadResult result = mcp
                    ? await BoundaryHeads.InvokeMcpAsync(profile, environment, ["--tenant", "tenant-b"],
                        command ? "send_command" : "run_query", new Dictionary<string, object?> { ["operation"] = operation, ["payload"] = payload })
                    : await BoundaryHeads.InvokeCliAsync(profile, environment,
                        [command ? "send" : "query", operation, "--payload", payload, "--tenant", "tenant-b"]);
                gateway.Requests.Count.ShouldBe(before + 1);
                gateway.Requests[^1].Headers.ContainsKey("Authorization").ShouldBe(token is not null);
                if (authentication) BoundaryHeads.AssertAuthenticationRefusal(result, token is not null, emptyBody);
                else BoundaryHeads.AssertTenantAuthorizationRefusal(result, "tenant-b", reason, correlation);
                if (token is not null) result.AllChannels.ShouldNotContain(token);
                HeadDiagnostics.AssertGatewayOnly(result, gateway.Url, command ? "/api/v1/commands" : "/api/v1/queries", status, process: true);
            }
        }
        finally { Directory.Delete(directory, recursive: true); }
    }
}
