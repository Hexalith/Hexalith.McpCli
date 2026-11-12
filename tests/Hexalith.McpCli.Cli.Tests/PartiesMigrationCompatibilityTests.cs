using System.Reflection;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using Hexalith.McpCli.Core.Settings;
using Hexalith.McpCli.Sample.Contracts;
using Shouldly;

namespace Hexalith.McpCli.Cli.Tests;

/// <summary>
/// Pins the Parties migration gates C06 (downstream error privacy) and C07 (legacy Party ID reachability) through both
/// heads over the enrolled Parties Contracts catalog, using only generic McpCli behavior.
/// </summary>
public sealed class PartiesMigrationCompatibilityTests
{
    private const string Marker = "C06-MARKER";
    private const string CorrelationId = "01J9MZHXT3RKM0VWXRXGSJDATK";
    private const string SampleItemId = "01ARZ3NDEKTSV4RRFFQ69G5FAV";
    private const string Tenant = "tenant-a";

    /// <summary>
    /// Problem Details members other than status, title, detail and the copied metadata never leave the Gateway client.
    /// The markers sit in <c>type</c>, <c>instance</c>, <c>tenantId</c>, <c>errors</c>, <c>extensions</c>,
    /// <c>rejectionType</c> and other extension members.
    /// </summary>
    private static readonly string ProblemBody = $$"""
        {"type":"https://errors.invalid/{{Marker}}-type","title":"Unprocessable","status":422,
         "detail":"The request was rejected.","instance":"/api/v1/{{Marker}}-instance",
         "correlationId":"{{CorrelationId}}","tenantId":"{{Marker}}-tenant","reasonCode":"request-rejected",
         "errors":{"PartyId":["{{Marker}}-errors jane.doe@example.test"]},
         "extensions":{"{{Marker}}-extensions-key":"{{Marker}}-extensions"},
         "rejectionType":"Hexalith.Parties.Events.{{Marker}}-rejection","category":"{{Marker}}-category",
         "correctiveAction":"{{Marker}}-corrective","degradation":"{{Marker}}-degradation",
         "traceId":"{{Marker}}-trace"}
        """;

    private static readonly Func<IReadOnlyList<Assembly>> PartiesManifest = () => [PartiesAssembly()];
    private static readonly Func<IReadOnlyList<Assembly>> SampleManifest = () => [typeof(CreateItemCommand).Assembly];

    /// <summary>
    /// C06: a Gateway failure for a Parties operation yields exactly the generic document a Sample operation gets for the
    /// same failure, and no downstream marker reaches stdout, stderr, MCP text content or MCP structured content.
    /// </summary>
    /// <param name="scenario">The failure shape.</param>
    /// <param name="command">Whether the failing call is a Command rather than a Query.</param>
    [Theory]
    [InlineData("problem", true)]
    [InlineData("problem", false)]
    [InlineData("text", true)]
    [InlineData("text", false)]
    [InlineData("inner-transport", true)]
    [InlineData("inner-transport", false)]
    [InlineData("inner-json", true)]
    [InlineData("inner-json", false)]
    public async Task GatewayFailureMarkersStayOutOfBothHeadsAsync(string scenario, bool command)
    {
        string directory = TemporaryDirectory();
        try
        {
            await using var gateway = new ScriptedGateway(_ => FailureResponse(scenario, command));
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            string expected = scenario switch
            {
                "problem" => $$$"""{"error":{"code":"gateway_error","status":422,"detail":"The request was rejected.","reason":"request-rejected","correlationId":"{{{CorrelationId}}}"}}""",
                "text" => """{"error":{"code":"gateway_error","status":500,"detail":"Internal Server Error"}}""",
                "inner-transport" => """{"error":{"code":"gateway_error","status":503,"detail":"The EventStore gateway could not be reached.","reason":"gateway-unreachable"}}""",
                _ => command
                    ? """{"error":{"code":"gateway_error","status":202,"detail":"Command response body could not be parsed."}}"""
                    : """{"error":{"code":"gateway_error","status":200,"detail":"Query response body could not be parsed."}}""",
            };

            var results = new List<(string Head, HeadResult Result)>();
            foreach ((string module, Func<IReadOnlyList<Assembly>> manifest, string operation, string payload) in Calls(command))
            {
                results.Add((module + " CLI", await BothHeads.InvokeCliAsync(store, manifest, NoEnvironment,
                    [command ? "send" : "query", operation, "--payload", payload, "--url", gateway.Url, "--tenant", Tenant])));
                results.Add((module + " MCP", await BothHeads.InvokeMcpAsync(store, manifest, NoEnvironment,
                    ["--url", gateway.Url, "--tenant", Tenant], command ? "send_command" : "run_query",
                    new Dictionary<string, object?> { ["operation"] = operation, ["payload"] = payload })));
            }

            foreach ((string head, HeadResult result) in results)
            {
                BothHeads.AssertDocument(result, expected, isError: true);
                result.AllChannels.ShouldNotContain(Marker, Case.Insensitive, head);
                result.AllChannels.ShouldNotContain("jane.doe", Case.Insensitive, head);
                HeadDiagnostics.AssertGatewayOnly(result, gateway.Url, command ? "/api/v1/commands" : "/api/v1/queries",
                    ReceivedStatus(scenario, command));
            }

            gateway.Requests.Select(request => request.Path).ShouldBe(
                Enumerable.Repeat(command ? "/api/v1/commands" : "/api/v1/queries", 4));
            gateway.Requests.Select(request => JsonDocument.Parse(request.Body).RootElement.GetProperty("domain").GetString())
                .ShouldBe(["party", "party", "sample", "sample"]);
            if (scenario == "inner-transport")
            {
                // The invalid header line really is carried by the client's inner exception chain.
                using var client = new HttpClient();
                HttpRequestException failure = await Should.ThrowAsync<HttpRequestException>(
                    () => client.GetAsync(gateway.Url, TestContext.Current.CancellationToken));
                failure.ToString().ShouldContain(Marker);
            }
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>
    /// C07: legacy braced, parenthesized and X-format GUID root Party IDs fail at the aggregate pointer with equal
    /// documents from both heads and no Gateway request.
    /// </summary>
    /// <param name="partyId">The legacy root Party ID.</param>
    /// <param name="command">Whether the call is the deactivate Command rather than the detail Query.</param>
    [Theory]
    [InlineData("{1b4e28ba-2fa1-11d2-883f-0016d3cca427}", true)]
    [InlineData("{1b4e28ba-2fa1-11d2-883f-0016d3cca427}", false)]
    [InlineData("(1b4e28ba-2fa1-11d2-883f-0016d3cca427)", true)]
    [InlineData("(1b4e28ba-2fa1-11d2-883f-0016d3cca427)", false)]
    [InlineData("{0x1b4e28ba,0x2fa1,0x11d2,{0x88,0x3f,0x00,0x16,0xd3,0xcc,0xa4,0x27}}", true)]
    [InlineData("{0x1b4e28ba,0x2fa1,0x11d2,{0x88,0x3f,0x00,0x16,0xd3,0xcc,0xa4,0x27}}", false)]
    public async Task LegacyRootPartyIdsFailBeforeTheGatewayInBothHeadsAsync(string partyId, bool command)
    {
        string directory = TemporaryDirectory();
        try
        {
            await using var gateway = new ScriptedGateway(ScriptedGateway.AcceptCommand);
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            string operation = command ? "parties.deactivate-party" : "parties.get-party";
            string payload = JsonSerializer.Serialize(new { PartyId = partyId });
            string expected = JsonSerializer.Serialize(new
            {
                error = new
                {
                    code = "validation_failed",
                    operation,
                    violations = new[]
                    {
                        new { path = "/PartyId", message = "The aggregate identifier does not match the module and Gateway rules." },
                    },
                },
            });

            HeadResult cli = await BothHeads.InvokeCliAsync(store, PartiesManifest, NoEnvironment,
                [command ? "send" : "query", operation, "--payload", payload, "--url", gateway.Url, "--tenant", Tenant]);
            HeadResult mcp = await BothHeads.InvokeMcpAsync(store, PartiesManifest, NoEnvironment,
                ["--url", gateway.Url, "--tenant", Tenant], command ? "send_command" : "run_query",
                new Dictionary<string, object?> { ["operation"] = operation, ["payload"] = payload });

            BothHeads.AssertDocument(cli, expected, isError: true);
            HeadDiagnostics.AssertNoGateway(cli);
            BothHeads.AssertDocument(mcp, expected, isError: true);
            HeadDiagnostics.AssertNoGateway(mcp);
            gateway.Requests.ShouldBeEmpty();
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>
    /// C07: a support-safe legacy root Party ID and braced, parenthesized and X-format GUID child IDs reach the Gateway
    /// byte-for-byte through both heads; McpCli neither converts nor rejects String-kind child identifiers.
    /// </summary>
    [Fact]
    public async Task LegacyChildIdsAndSupportSafeRootReachTheGatewayUnchangedAsync()
    {
        const string root = "Legacy.party_01-A";
        const string channelId = "{1b4e28ba-2fa1-11d2-883f-0016d3cca427}";
        const string parenthesizedChannelId = "(2c5f39cb-3fb2-12e3-994f-1127e4ddb538)";
        const string identifierId = "{0x1b4e28ba,0x2fa1,0x11d2,{0x88,0x3f,0x00,0x16,0xd3,0xcc,0xa4,0x27}}";
        string directory = TemporaryDirectory();
        try
        {
            await using var gateway = new ScriptedGateway(ScriptedGateway.AcceptCommand);
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            string payload = JsonSerializer.Serialize(new
            {
                PartyId = root,
                Type = "Person",
                PersonDetails = new { FirstName = "Ada", LastName = "Lovelace" },
                ContactChannels = new[]
                {
                    new { PartyId = root, ContactChannelId = channelId, Type = "Email", Value = "ada@example.test", IsPreferred = true },
                    new { PartyId = root, ContactChannelId = parenthesizedChannelId, Type = "Email", Value = "lovelace@example.test", IsPreferred = false },
                },
                Identifiers = new[] { new { PartyId = root, IdentifierId = identifierId, Type = "Other", Value = "customer-49" } },
            });
            string expected = JsonSerializer.Serialize(new
            {
                operation = "parties.create-party",
                messageId = "<generated>",
                correlationId = CorrelationId,
                tenant = Tenant,
                aggregateId = root,
                status = "accepted",
            });

            HeadResult cli = await BothHeads.InvokeCliAsync(store, PartiesManifest, NoEnvironment,
                ["send", "parties.create-party", "--payload", payload, "--correlation-id", CorrelationId,
                    "--url", gateway.Url, "--tenant", Tenant]);
            HeadResult mcp = await BothHeads.InvokeMcpAsync(store, PartiesManifest, NoEnvironment,
                ["--url", gateway.Url, "--tenant", Tenant], "send_command", new Dictionary<string, object?>
                {
                    ["operation"] = "parties.create-party", ["payload"] = payload, ["correlationId"] = CorrelationId,
                });

            BothHeads.AssertDocument(cli, expected, isError: false, "messageId");
            BothHeads.AssertDocument(mcp, expected, isError: false, "messageId");
            gateway.Requests.Count.ShouldBe(2);
            string expectedBody = JsonSerializer.Serialize(new
            {
                messageId = "<generated>",
                tenant = Tenant,
                domain = "party",
                aggregateId = root,
                commandType = "Hexalith.Parties.Contracts.Commands.CreatePartyComposite",
                payload = JsonNode.Parse(payload),
                correlationId = CorrelationId,
            });
            foreach (GatewayRequest request in gateway.Requests)
            {
                request.Path.ShouldBe("/api/v1/commands");
                BothHeads.AssertJson(request.Body, expectedBody, "messageId");
                JsonElement submitted = JsonDocument.Parse(request.Body).RootElement;
                string.Equals(submitted.GetProperty("aggregateId").GetString(), root, StringComparison.Ordinal).ShouldBeTrue();
                JsonElement submittedPayload = submitted.GetProperty("payload");
                string.Equals(submittedPayload.GetProperty("PartyId").GetString(), root, StringComparison.Ordinal).ShouldBeTrue();
                string.Equals(submittedPayload.GetProperty("ContactChannels")[0].GetProperty("ContactChannelId").GetString(),
                    channelId, StringComparison.Ordinal).ShouldBeTrue();
                string.Equals(submittedPayload.GetProperty("ContactChannels")[1].GetProperty("ContactChannelId").GetString(),
                    parenthesizedChannelId, StringComparison.Ordinal).ShouldBeTrue();
                string.Equals(submittedPayload.GetProperty("Identifiers")[0].GetProperty("IdentifierId").GetString(),
                    identifierId, StringComparison.Ordinal).ShouldBeTrue();
                request.Body.ShouldContain("\"ContactChannelId\":\"" + channelId + "\"");
                request.Body.ShouldContain("\"ContactChannelId\":\"" + parenthesizedChannelId + "\"");
                request.Body.ShouldContain("\"IdentifierId\":\"" + identifierId + "\"");
            }

            HeadDiagnostics.AssertGatewayOnly(cli, gateway.Url, "/api/v1/commands", 202);
            HeadDiagnostics.AssertGatewayOnly(mcp, gateway.Url, "/api/v1/commands", 202);
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Gets an empty environment so no inherited variable reaches either head.</summary>
    private static IReadOnlyDictionary<string, string?> NoEnvironment { get; } = new Dictionary<string, string?>();

    /// <summary>Checks that the enrolled Parties Contracts package restored for this run is exactly 3.1.1.</summary>
    [Fact]
    public void CatalogUsesTheEnrolledPartiesContractsPackage()
    {
        string deps = Path.Combine(AppContext.BaseDirectory, "Hexalith.McpCli.Cli.Tests.deps.json");
        using JsonDocument document = JsonDocument.Parse(File.ReadAllText(deps));
        document.RootElement.GetProperty("libraries").EnumerateObject().Select(library => library.Name)
            .Where(name => name.StartsWith("Hexalith.Parties.", StringComparison.Ordinal))
            .ShouldBe(["Hexalith.Parties.Contracts/3.1.1"]);
        PartiesAssembly().GetTypes().Select(type => type.FullName).ShouldContain("Hexalith.Parties.Contracts.Commands.DeactivateParty");
    }

    private static Assembly PartiesAssembly() => Assembly.Load(new AssemblyName("Hexalith.Parties.Contracts"));

    private static IEnumerable<(string Module, Func<IReadOnlyList<Assembly>> Manifest, string Operation, string Payload)> Calls(
        bool command)
    {
        yield return command
            ? ("parties", PartiesManifest, "parties.deactivate-party", """{"PartyId":"party-c06"}""")
            : ("parties", PartiesManifest, "parties.get-party", """{"PartyId":"party-c06"}""");
        yield return command
            ? ("sample", SampleManifest, "sample.create-item", $$"""{"ItemId":"{{SampleItemId}}","Title":"Hello"}""")
            : ("sample", SampleManifest, "sample.get-item", $$"""{"ItemId":"{{SampleItemId}}"}""");
    }

    private static byte[] FailureResponse(string scenario, bool command) => scenario switch
    {
        "problem" => ScriptedGateway.Response(422, "Unprocessable Entity", "application/problem+json", ProblemBody),
        "text" => ScriptedGateway.Response(500, "Internal Server Error", "text/plain; charset=utf-8",
            $"{Marker}-text: System.InvalidOperationException at Hexalith.Parties.Secret for jane.doe@example.test"),
        "inner-transport" => Encoding.ASCII.GetBytes(
            $"HTTP/1.1 200 OK\r\n{Marker}-transport invalid header line for jane.doe\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"),
        _ => ScriptedGateway.Response(command ? 202 : 200, command ? "Accepted" : "OK", "application/json",
            $$"""{"correlationId":"{{Marker}}-json jane.doe@example.test","payload":"""),
    };

    private static int? ReceivedStatus(string scenario, bool command) => scenario switch
    {
        "problem" => 422,
        "text" => 500,
        "inner-transport" => null,
        _ => command ? 202 : 200,
    };

    private static string TemporaryDirectory()
    {
        string path = Path.Combine(Path.GetTempPath(), "mcpcli-parties-migration-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(path);
        return path;
    }
}
