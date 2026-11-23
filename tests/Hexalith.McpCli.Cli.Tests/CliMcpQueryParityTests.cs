using System.Reflection;
using System.Text.Json;
using System.Text.Json.Nodes;
using Hexalith.McpCli.Core.Settings;
using Hexalith.McpCli.Sample.Contracts;
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
            Func<IReadOnlyList<Assembly>> manifest = lint
                ? () => [typeof(global::Catalog.Lint.Contracts.Module).Assembly]
                : () => [Assembly.Load(new AssemblyName("Hexalith.Parties.Contracts"))];
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

    /// <summary>Both heads send the same query and expose only the paging metadata returned by the Gateway.</summary>
    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task QueryDocumentsAndGatewayRequestsMatchAsync(bool returnsPaging)
    {
        string directory = Path.Combine(Path.GetTempPath(), "mcpcli-query-parity-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(directory);
        try
        {
            const string paging = """{"pageSize":10,"nextCursor":"next+/=42","hasMore":true}""";
            string metadata = returnsPaging ? $$""","metadata":{"paging":{{paging}}}""" : "";
            await using var gateway = new ScriptedGateway(_ => ScriptedGateway.Response(200, "OK", "application/json",
                $$"""{"correlationId":"01J9MZHXT3RKM0VWXRXGSJDATK","payload":{"title":"Hello"},"success":true{{metadata}}}"""));
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            Func<IReadOnlyList<Assembly>> manifest = () => [typeof(GetItemQuery).Assembly];
            IReadOnlyDictionary<string, string?> environment = new Dictionary<string, string?>();
            string[] globals = ["--url", gateway.Url];
            string payload = $$"""{"ItemId":"{{ItemId}}"}""";
            HeadResult cli = await BothHeads.InvokeCliAsync(store, manifest, environment,
                ["query", "sample.get-item", "--payload", payload, "--page-size", "25", .. globals]);
            HeadResult mcp = await BothHeads.InvokeMcpAsync(store, manifest, environment, globals, "run_query",
                new Dictionary<string, object?> { ["operation"] = "sample.get-item", ["payload"] = payload, ["pageSize"] = 25 });

            string resultPaging = returnsPaging ? $$""","paging":{{paging}}""" : "";
            string expected = $$"""{"operation":"sample.get-item","tenant":"sample-tenant","document":{"title":"Hello"}{{resultPaging}}}""";
            BothHeads.AssertDocument(cli, expected, isError: false);
            BothHeads.AssertDocument(mcp, expected, isError: false);
            IReadOnlyList<GatewayRequest> requests = gateway.Requests;
            requests.Count.ShouldBe(2);
            requests.ShouldAllBe(request => request.Method == "POST" && request.Path == "/api/v1/queries");
            BothHeads.AssertJson(requests[0].Body, requests[1].Body);
            using JsonDocument sent = JsonDocument.Parse(requests[0].Body);
            sent.RootElement.GetProperty("tenant").GetString().ShouldBe("sample-tenant");
            sent.RootElement.GetProperty("domain").GetString().ShouldBe("sample");
            sent.RootElement.GetProperty("paging").GetProperty("pageSize").GetInt32().ShouldBe(25);
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }
}
