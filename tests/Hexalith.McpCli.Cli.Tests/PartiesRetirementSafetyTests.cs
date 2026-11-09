using System.Reflection;
using System.Text.Json;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Core.Execution;
using Hexalith.McpCli.Core.Serialization;
using Hexalith.McpCli.Core.Settings;
using Hexalith.McpCli.Hosting;
using Microsoft.Extensions.Logging.Abstractions;
using Shouldly;

namespace Hexalith.McpCli.Cli.Tests;

/// <summary>Pins the public retirement safety boundary over the shipped Contracts manifest through both heads.</summary>
public sealed class PartiesRetirementSafetyTests
{
    private const string Correlation = "01J9MZHXT3RKM0VWXRXGSJDATK";
    private static readonly IReadOnlyDictionary<string, string?> EmptyEnvironment = new Dictionary<string, string?>();
    private static readonly Func<IReadOnlyList<Assembly>> Manifest = ManifestLoader.Load;

    /// <summary>Both call kinds preserve authentication and authorization failures without leaking the credential.</summary>
    /// <param name="command">Whether to submit a Command.</param>
    /// <param name="status">The refused Gateway status.</param>
    /// <param name="credential">The private credential, or null for a missing token.</param>
    [Theory]
    [InlineData(false, 401, null)]
    [InlineData(true, 401, null)]
    [InlineData(false, 401, "forged-secret-token")]
    [InlineData(true, 401, "forged-secret-token")]
    [InlineData(false, 403, "tenant-a-private-token")]
    [InlineData(true, 403, "tenant-a-private-token")]
    public async Task CredentialRefusalsPreserveTheCompleteGatewayErrorAsync(bool command, int status, string? credential)
    {
        string directory = TemporaryDirectory();
        try
        {
            string detail = status == 401 ? "Authentication is required." : "The principal cannot access this tenant.";
            string body = JsonSerializer.Serialize(new { status, detail, reasonCode = "access-denied", correlationId = Correlation });
            await using var gateway = new ScriptedGateway(_ => ScriptedGateway.Response(status,
                status == 401 ? "Unauthorized" : "Forbidden", "application/problem+json", body));
            string expected = JsonSerializer.Serialize(new { error = new { code = "gateway_error", status, detail,
                reason = "access-denied", correlationId = Correlation } });
            var environment = new Dictionary<string, string?> { ["EVENTSTORE_URL"] = gateway.Url, ["EVENTSTORE_TOKEN"] = credential };
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            string operation = Operation(command);
            HeadResult cli = await BothHeads.InvokeCliAsync(store, Manifest, environment,
                [command ? "send" : "query", operation, "--payload", Payload, "--tenant", "tenant-b"]);
            HeadResult mcp = await BothHeads.InvokeMcpAsync(store, Manifest, environment, ["--tenant", "tenant-b"],
                command ? "send_command" : "run_query", new Dictionary<string, object?> { ["operation"] = operation, ["payload"] = Payload });
            foreach (HeadResult result in new[] { cli, mcp })
            {
                BothHeads.AssertDocument(result, expected, isError: true);
                HeadDiagnostics.AssertGatewayOnly(result, gateway.Url, command ? "/api/v1/commands" : "/api/v1/queries", status);
                if (credential is not null)
                    (result.Output + result.Error + result.Tool?.StructuredContent + JsonSerializer.Serialize(result.Tool?.Content)).ShouldNotContain(credential);
            }
            gateway.Requests.Count.ShouldBe(2);
            foreach (GatewayRequest request in gateway.Requests)
            {
                request.Headers.TryGetValue("Authorization", out string? authorization).ShouldBe(credential is not null);
                authorization.ShouldBe(credential is null ? null : "Bearer " + credential);
                JsonDocument.Parse(request.Body).RootElement.GetProperty("tenant").GetString().ShouldBe("tenant-b");
            }
        }
        finally { Directory.Delete(directory, recursive: true); }
    }

    /// <summary>Invalid public tenant inputs fail before either call kind reaches the Gateway.</summary>
    /// <param name="tenant">The invalid tenant spelling.</param>
    /// <param name="command">Whether to submit a Command.</param>
    [Theory]
    [InlineData("platform:tenants", false)]
    [InlineData("platform:tenants", true)]
    [InlineData("system", false)]
    [InlineData("system", true)]
    [InlineData("SYSTEM", false)]
    [InlineData("SYSTEM", true)]
    [InlineData("tenant-\u0430", false)]
    [InlineData("tenant-\u0430", true)]
    [InlineData("\u0130", false)]
    [InlineData("\u0130", true)]
    [InlineData("\uff54\uff45\uff4e\uff41\uff4e\uff54", false)]
    [InlineData("\uff54\uff45\uff4e\uff41\uff4e\uff54", true)]
    public async Task PublicTenantNegativesHaveNoGatewayCallsAsync(string tenant, bool command)
    {
        await WithStoreAsync(async (store, gateway) =>
        {
            string operation = Operation(command);
            string message = tenant.Equals("system", StringComparison.OrdinalIgnoreCase)
                ? "The public tenant 'system' is reserved." : "The tenant does not match the Gateway tenant pattern.";
            string expected = TenantError(operation, message);
            HeadResult cli = await BothHeads.InvokeCliAsync(store, Manifest, EmptyEnvironment,
                [command ? "send" : "query", operation, "--payload", Payload, "--url", gateway.Url, "--tenant", tenant]);
            AssertRefused(cli, expected);
            foreach (bool perCall in new[] { false, true })
            {
                var arguments = new Dictionary<string, object?> { ["operation"] = operation, ["payload"] = Payload };
                if (perCall) arguments["tenant"] = tenant;
                HeadResult mcp = await BothHeads.InvokeMcpAsync(store, Manifest, EmptyEnvironment,
                    perCall ? ["--url", gateway.Url] : ["--url", gateway.Url, "--tenant", tenant],
                    command ? "send_command" : "run_query", arguments);
                AssertRefused(mcp, expected);
            }
            gateway.Requests.ShouldBeEmpty();
        });
    }

    /// <summary>Local override permission never follows from an MCP per-call tenant argument.</summary>
    /// <param name="command">Whether to submit a Command.</param>
    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task DisabledMcpOverrideMakesNoGatewayCallsAsync(bool command)
    {
        await WithStoreAsync(async (store, gateway) =>
        {
            string operation = Operation(command);
            HeadResult result = await BothHeads.InvokeMcpAsync(store, Manifest, EmptyEnvironment,
                ["--url", gateway.Url, "--tenant", "tenant-a"], command ? "send_command" : "run_query",
                new Dictionary<string, object?> { ["operation"] = operation, ["payload"] = Payload, ["tenant"] = "tenant-b" });
            AssertRefused(result, TenantError(operation, "Per-call tenant override is disabled."));
            gateway.Requests.ShouldBeEmpty();
        });
    }

    /// <summary>Accepted F7 limitation: epic-4-retro-item-9-ascii-tenant-input must flip this Kelvin alias pin when fixed.</summary>
    [Fact]
    public async Task AcceptedF7Item9KelvinAliasReachesTheGatewayAsAsciiAsync()
    {
        await WithStoreAsync(async (store, gateway) =>
        {
            const string expected = """{"operation":"parties.deactivate-party","messageId":"generated","correlationId":"01J9MZHXT3RKM0VWXRXGSJDATK","tenant":"kelvin","aggregateId":"safety-party","status":"accepted"}""";
            HeadResult cli = await BothHeads.InvokeCliAsync(store, Manifest, EmptyEnvironment,
                ["send", "parties.deactivate-party", "--payload", Payload, "--url", gateway.Url, "--tenant", "\u212Aelvin", "--correlation-id", Correlation]);
            HeadResult mcp = await BothHeads.InvokeMcpAsync(store, Manifest, EmptyEnvironment,
                ["--url", gateway.Url, "--tenant", "\u212Aelvin"], "send_command", new Dictionary<string, object?>
                { ["operation"] = "parties.deactivate-party", ["payload"] = Payload, ["correlationId"] = Correlation });
            foreach (HeadResult result in new[] { cli, mcp })
            {
                BothHeads.AssertDocument(result, expected, isError: false, "messageId");
                HeadDiagnostics.AssertGatewayOnly(result, gateway.Url, "/api/v1/commands", 202);
            }
            gateway.Requests.Count.ShouldBe(2);
            foreach (GatewayRequest request in gateway.Requests)
                JsonDocument.Parse(request.Body).RootElement.GetProperty("tenant").GetString().ShouldBe("kelvin");
        });
    }

    /// <summary>All inventoried Admin names and excluded Tenants names remain absent and uncallable even with confirmation.</summary>
    [Fact]
    public async Task RestrictedNamesCannotBeDiscoveredOrAuthorizedByConfirmAsync()
    {
        string root = FindRoot();
        string[] admin = File.ReadLines(Path.Combine(root, "_bmad-output/implementation-artifacts/eventstore-admin-migration-inventory-v1.md"))
            .Where(line => (line.StartsWith("| AC", StringComparison.Ordinal) || line.StartsWith("| AM", StringComparison.Ordinal))
                && line.Split('|')[2].Trim().StartsWith('`'))
            .Select(line => line.Split('|')[2].Trim().Trim('`')).Distinct(StringComparer.Ordinal).ToArray();
        using JsonDocument inventory = JsonDocument.Parse(File.ReadAllText(Path.Combine(root, "tools/inventory-coverage/v1/tenants-approved.json")));
        string[] excluded = inventory.RootElement.GetProperty("legacyRows").EnumerateArray()
            .Where(row => row.GetProperty("coverage").GetString() == "exclude")
            .SelectMany(row => row.GetProperty("targetIds").EnumerateArray().Select(id => id.GetString()))
            .Select(id => inventory.RootElement.GetProperty("targets").EnumerateArray().Single(target => target.GetProperty("id").GetString() == id)
                .GetProperty("name").GetString()!).ToArray();
        admin.ShouldNotBeEmpty();
        excluded.Length.ShouldBe(6);
        string[] restricted = [.. admin, .. excluded];
        var provider = new CatalogProvider(Manifest, NullLogger<CatalogProvider>.Instance);
        var catalog = new CatalogService(provider, new ExecutionAvailability(false, true), strict: true);
        string[] modules = catalog.ListModules().Document!.Modules.Select(module => module.Name).ToArray();
        await WithStoreAsync(async (store, gateway) =>
        {
            foreach (string module in modules)
            {
                HeadResult cli = await BothHeads.InvokeCliAsync(store, Manifest, EmptyEnvironment, ["operations", module]);
                HeadResult mcp = await BothHeads.InvokeMcpAsync(store, Manifest, EmptyEnvironment, [], "list_operations",
                    new Dictionary<string, object?> { ["module"] = module, ["confirm"] = true });
                string expected = JsonSerializer.Serialize(catalog.ListOperations(module).Document, McpCliJson.Result);
                BothHeads.AssertDocument(cli, expected, isError: false);
                BothHeads.AssertDocument(mcp, expected, isError: false);
                HeadDiagnostics.AssertNoGateway(cli);
                HeadDiagnostics.AssertNoGateway(mcp);
                foreach (string name in restricted)
                    JsonDocument.Parse(cli.Output).RootElement.GetProperty("operations").EnumerateArray()
                        .Select(operation => operation.GetProperty("name").GetString()).ShouldNotContain(name);
            }
            foreach (string name in restricted)
            {
                // Suggestions belong to discovery; the exact whole lookup error must be preserved by execution.
                OperationError lookup = catalog.Describe(name).Error.ShouldNotBeNull();
                lookup.Code.ShouldBe("unknown_operation");
                string expected = JsonSerializer.Serialize(new { error = lookup }, McpCliJson.Result);
                foreach (bool confirm in new[] { false, true })
                {
                    string payload = confirm ? """{"confirm":true}""" : "{}";
                    foreach (bool command in new[] { false, true })
                    {
                        HeadResult cli = await BothHeads.InvokeCliAsync(store, Manifest, EmptyEnvironment,
                            [command ? "send" : "query", name, "--payload", payload, "--url", gateway.Url, "--tenant", "tenant-a"]);
                        AssertRefused(cli, expected);
                        var arguments = new Dictionary<string, object?> { ["operation"] = name, ["payload"] = payload };
                        if (confirm) arguments["confirm"] = true;
                        HeadResult mcp = await BothHeads.InvokeMcpAsync(store, Manifest, EmptyEnvironment,
                            ["--url", gateway.Url, "--tenant", "tenant-a"], command ? "send_command" : "run_query", arguments);
                        AssertRefused(mcp, expected);
                    }
                }
            }
            // CLI confirmation is not a supported argument and cannot grant authority.
            HeadResult invalid = await BothHeads.InvokeCliAsync(store, Manifest, EmptyEnvironment,
                ["send", "projection-reset", "--payload", "{}", "--confirm", "true"]);
            AssertRefused(invalid, """{"error":{"code":"invalid_arguments","message":"The command contains an unknown or malformed option. Run with --help for usage.","argument":"arguments"}}""");
            gateway.Requests.ShouldBeEmpty();
        });
    }

    private const string Payload = """{"PartyId":"safety-party"}""";
    private static string Operation(bool command) => command ? "parties.deactivate-party" : "parties.get-party";
    private static string TenantError(string operation, string message) => JsonSerializer.Serialize(new
    { error = new { code = "validation_failed", operation, violations = new[] { new { path = "/tenant", message } } } });
    private static void AssertRefused(HeadResult result, string expected)
    {
        BothHeads.AssertDocument(result, expected, isError: true);
        HeadDiagnostics.AssertNoGateway(result);
    }
    private static async Task WithStoreAsync(Func<ProfileStore, ScriptedGateway, Task> action)
    {
        string directory = TemporaryDirectory();
        try
        {
            await using var gateway = new ScriptedGateway(ScriptedGateway.AcceptCommand);
            await action(new ProfileStore(Path.Combine(directory, "mcpcli.json")), gateway);
        }
        finally { Directory.Delete(directory, recursive: true); }
    }
    private static string TemporaryDirectory()
    {
        string directory = Path.Combine(Path.GetTempPath(), "mcpcli-retirement-safety-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(directory);
        return directory;
    }
    private static string FindRoot()
    {
        for (DirectoryInfo? directory = new(AppContext.BaseDirectory); directory is not null; directory = directory.Parent)
            if (File.Exists(Path.Combine(directory.FullName, "Hexalith.McpCli.slnx"))) return directory.FullName;
        throw new InvalidOperationException("Repository root is missing.");
    }
}
