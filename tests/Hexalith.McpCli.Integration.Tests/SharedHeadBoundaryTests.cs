using System.Diagnostics;
using System.Net.Http.Headers;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using Hexalith.EventStore.Aspire;
using Hexalith.EventStore.Testing.Integration;
using Hexalith.EventStore.Client.Gateway;
using Hexalith.EventStore.Contracts.Queries;
using Hexalith.McpCli.Cli.Tests;
using Microsoft.Extensions.Options;
using Shouldly;

namespace Hexalith.McpCli.Integration.Tests;

/// <summary>Proves credential refusal, tenant isolation and repeated soft deactivation against fresh persisted state.</summary>
[Collection("AspireTopology")]
[Trait("Category", "Integration")]
public sealed class SharedHeadBoundaryTests(AspireTopologyFixture fixture)
{
    private const string Party = "retirement-boundary-party";
    private const string Missing = "retirement-missing-party";
    /// <summary>Runs each boundary with independent end-state reads; the two concurrent Commands are CLI-only.</summary>
    [Fact]
    public async Task SharedHeadsPreserveAuthorizationAndDeactivationSafety()
    {
        fixture.SkipIfUnavailable();
        CancellationToken cancellation = TestContext.Current.CancellationToken;
        await fixture.RequireAdministratorAuthorityAsync(cancellation);
        await fixture.RequireProjectionWriterAsync(cancellation);
        string directory = Path.Combine(Path.GetTempPath(), "mcpcli-live-safety-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(directory);
        var receipts = new List<object>();
        string authorizedToken = fixture.CreateBoundaryAuthorizedIdentity();
        using var authorizedHttp = new HttpClient { BaseAddress = fixture.GatewayEndpoint, Timeout = TimeSpan.FromSeconds(35) };
        authorizedHttp.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", authorizedToken);
        IEventStoreGatewayClient authorized = new EventStoreGatewayClient(authorizedHttp, Options.Create(new EventStoreGatewayClientOptions()));
        try
        {
            await using var forwarder = new LiveGatewayForwarder(fixture.GatewayEndpoint);
            string profile = Path.Combine(directory, "mcpcli.json");
            string create = JsonSerializer.Serialize(new { PartyId = Party, Type = "Person",
                PersonDetails = new { FirstName = "BoundaryPrivateMarker", LastName = "MustNotBeDisclosed" } });
            HeadResult created = await InvokeAsync(false, true, "parties.create-party", create, "tenant-b", authorizedToken);
            AssertAccepted(created, "parties.create-party", "tenant-b", Party);
            JsonElement active = await ReadAsync(Party, active: true);
            foreach (bool mcp in new[] { false, true })
            foreach (bool command in new[] { false, true })
            {
                foreach (var scenario in new[]
                {
                    (Name: "missing-token", Token: (string?)null, Status: 401, Reason: (string?)null),
                    (Name: "forged-token", Token: (string?)fixture.CreateBoundaryIdentity(invalidSignature: true), Status: 401, Reason: (string?)null),
                    (Name: "tenant-a-grant", Token: (string?)fixture.CreateBoundaryIdentity(), Status: 403, Reason: (string?)"tenant_mismatch"),
                    (Name: "nonmember", Token: (string?)fixture.CreateBoundaryIdentity(nonmember: true), Status: 403, Reason: (string?)"principal_not_member"),
                })
                {
                    JsonElement before = await ReadAsync(Party, active: true);
                    int requests = forwarder.Requests.Count;
                    string operation = command ? "parties.deactivate-party" : "parties.get-party";
                    HeadResult refused = await InvokeAsync(mcp, command, operation, Payload(Party), "tenant-b", scenario.Token);
                    AssertGatewayRefusal(refused, forwarder, requests, scenario.Status, scenario.Reason, operation);
                    if (scenario.Token is null) forwarder.Requests[^1].Headers.ContainsKey("Authorization").ShouldBeFalse();
                    JsonElement after = await ReadAsync(Party, active: true);
                    JsonElement.DeepEquals(before, after).ShouldBeTrue("A rejected call changed the authorized persisted read.");
                    receipts.Add(new { scenario = scenario.Name, head = mcp ? "mcp" : "cli", kind = command ? "command" : "query",
                        status = scenario.Status, gatewayRequests = 1, persistedBeforeSha256 = Hash(before), persistedAfterSha256 = Hash(after) });
                }
                if (mcp)
                {
                    int requests = forwarder.Requests.Count;
                    string operation = command ? "parties.deactivate-party" : "parties.get-party";
                    HeadResult denied = await InvokeAsync(true, command, operation, Payload(Party), "tenant-a", authorizedToken,
                        perCallTenant: "tenant-b");
                    AssertLocal(denied, operation, "Per-call tenant override is disabled.");
                    forwarder.Requests.Count.ShouldBe(requests);
                    JsonElement.DeepEquals(active, await ReadAsync(Party, active: true)).ShouldBeTrue();
                    requests = forwarder.Requests.Count;
                    HeadResult crossTenant = await InvokeAsync(true, command, operation, Payload(Party), "tenant-a",
                        fixture.CreateBoundaryIdentity(), perCallTenant: "tenant-b", allowOverride: true);
                    AssertGatewayRefusal(crossTenant, forwarder, requests, 403, "tenant_mismatch", operation);
                    JsonElement.DeepEquals(active, await ReadAsync(Party, active: true)).ShouldBeTrue();
                    receipts.Add(new { scenario = "mcp-override-disabled-and-authorized-selection-denied", kind = command ? "command" : "query",
                        gatewayRequests = 1, persistedAfterSha256 = Hash(active) });
                }
                foreach (string tenant in new[] { "platform:tenants", "system", "SYSTEM", "tenant-\u0430", "\u0130", "\uff54\uff45\uff4e\uff41\uff4e\uff54" })
                {
                    int requests = forwarder.Requests.Count;
                    string operation = command ? "parties.deactivate-party" : "parties.get-party";
                    HeadResult refused = await InvokeAsync(mcp, command, operation, Payload(Party), tenant, authorizedToken);
                    AssertLocal(refused, operation, tenant.Equals("system", StringComparison.OrdinalIgnoreCase)
                        ? "The public tenant 'system' is reserved." : "The tenant does not match the Gateway tenant pattern.");
                    forwarder.Requests.Count.ShouldBe(requests);
                    JsonElement.DeepEquals(active, await ReadAsync(Party, active: true)).ShouldBeTrue();
                    receipts.Add(new { scenario = "invalid-public-tenant", tenant, head = mcp ? "mcp" : "cli",
                        kind = command ? "command" : "query", gatewayRequests = 0, persistedAfterSha256 = Hash(active) });
                }
            }
            // Missing aggregate: the command is submitted once, and independent authorized reads prove absence.
            foreach (bool mcp in new[] { false, true })
            {
                string target = Missing + (mcp ? "-mcp" : "-cli");
                await RequireAbsentAsync(target);
                int beforeMissing = forwarder.Requests.Count;
                HeadResult missing = await InvokeAsync(mcp, true, "parties.deactivate-party", Payload(target), "tenant-b", authorizedToken);
                AssertGatewayRefusal(missing, forwarder, beforeMissing, 404, "party-not-found", "parties.deactivate-party");
                await RequireAbsentAsync(target);
                receipts.Add(new { scenario = "C05-missing", head = mcp ? "mcp" : "cli", status = 404,
                    reason = "party-not-found", persistedPartyAbsentBeforeAndAfter = true });
            }

            // Separate processes are required for truly concurrent CLI calls: Console capture is process-global.
            int beforeConcurrent = forwarder.Requests.Count;
            HeadResult[] concurrent = await Task.WhenAll(ConcurrentDeactivateAsync(), ConcurrentDeactivateAsync());
            foreach (HeadResult result in concurrent) AssertAccepted(result, "parties.deactivate-party", "tenant-b", Party);
            forwarder.Requests.Count.ShouldBe(beforeConcurrent + 2);
            string[] messageIds = forwarder.Requests.Skip(beforeConcurrent).Select(request =>
                JsonDocument.Parse(request.Body).RootElement.GetProperty("messageId").GetString()!).ToArray();
            messageIds.Distinct(StringComparer.Ordinal).Count().ShouldBe(2);
            JsonElement inactive = await ReadAsync(Party, active: false);
            long sequence = await PersistedPartyEvents.RequireOneDeactivationAsync("tenant-b", Party, cancellation);
            receipts.Add(new { scenario = "C05-concurrent-repeat", accepted = 2, distinctMessageIds = messageIds,
                persistedDeactivationEvents = 1, sequence, persistedAfterSha256 = Hash(inactive) });
            string output = Environment.GetEnvironmentVariable("MCPCLI_LIVE_OUTPUT")
                ?? throw new InvalidOperationException("The isolated boundary case needs its evidence output directory.");
            await File.WriteAllTextAsync(Path.Combine(output, "boundary-result.json"), JsonSerializer.Serialize(new
            { result = "passed", identityAuthority = "Gateway checks exact signed tenant grants; administrator bootstrap independently reads persisted membership.", cases = receipts },
                new JsonSerializerOptions { WriteIndented = true }), cancellation);

            async Task<HeadResult> InvokeAsync(bool mcp, bool command, string operation, string payload, string tenant, string? token,
                string? perCallTenant = null, bool allowOverride = false)
            {
                var environment = new Dictionary<string, string?> { ["EVENTSTORE_URL"] = forwarder.Url, ["EVENTSTORE_TOKEN"] = token };
                var globals = new List<string> { "--tenant", tenant };
                if (allowOverride) globals.Add("--allow-tenant-override");
                HeadResult result;
                if (mcp)
                {
                    var arguments = new Dictionary<string, object?> { ["operation"] = operation, ["payload"] = payload };
                    if (perCallTenant is not null) arguments["tenant"] = perCallTenant;
                    result = await BoundaryHeads.InvokeMcpAsync(profile, environment, globals,
                        command ? "send_command" : "run_query", arguments);
                }
                else result = await BoundaryHeads.InvokeCliAsync(profile, environment,
                    [command ? "send" : "query", operation, "--payload", payload, .. globals]);
                if (token is not null) Channels(result).ShouldNotContain(token);
                if (operation != "parties.create-party") Channels(result).ShouldNotContain("BoundaryPrivateMarker");
                return result;
            }

            async Task<HeadResult> ConcurrentDeactivateAsync()
            {
                var start = new ProcessStartInfo("dotnet") { RedirectStandardOutput = true, RedirectStandardError = true };
                string root = RepositoryProjectPaths.GetRepositoryRoot();
                foreach (string argument in new[] { Path.Combine(root, "tests/Hexalith.McpCli.ConformanceHost/bin/Release/net10.0/Hexalith.McpCli.ConformanceHost.dll"),
                    "send", "parties.deactivate-party", "--payload", Payload(Party), "--tenant", "tenant-b" }) start.ArgumentList.Add(argument);
                foreach (string key in start.Environment.Keys.Where(key => key.StartsWith("EVENTSTORE_", StringComparison.Ordinal)
                    || key.StartsWith("MCPCLI_", StringComparison.Ordinal)).ToArray()) start.Environment.Remove(key);
                start.Environment["EVENTSTORE_URL"] = forwarder.Url;
                start.Environment["EVENTSTORE_TOKEN"] = authorizedToken;
                start.Environment["MCPCLI_CONFORMANCE_PROFILE_PATH"] = Path.Combine(directory, Guid.NewGuid().ToString("N") + ".json");
                using Process process = Process.Start(start)!;
                Task<string> stdout = process.StandardOutput.ReadToEndAsync(cancellation);
                Task<string> stderr = process.StandardError.ReadToEndAsync(cancellation);
                using var deadline = CancellationTokenSource.CreateLinkedTokenSource(cancellation);
                deadline.CancelAfter(TimeSpan.FromSeconds(45));
                try { await process.WaitForExitAsync(deadline.Token); }
                finally { if (!process.HasExited) process.Kill(entireProcessTree: true); }
                var result = new HeadResult(process.ExitCode, await stdout, await stderr, null);
                Channels(result).ShouldNotContain(authorizedToken);
                HeadDiagnostics.AssertGatewayOnly(result, forwarder.Url, "/api/v1/commands", 202);
                return result;
            }
        }
        finally { Directory.Delete(directory, recursive: true); }

        async Task<JsonElement> ReadAsync(string id, bool active)
        {
            using var deadline = CancellationTokenSource.CreateLinkedTokenSource(cancellation);
            deadline.CancelAfter(TimeSpan.FromSeconds(45));
            while (true)
            {
                try
                {
                    EventStoreQueryResult result = await authorized.SubmitQueryAsync(Query(id), cancellationToken: deadline.Token);
                    if (result.Payload is { } payload && payload.GetProperty("isActive").GetBoolean() == active)
                    {
                        // Freshness reports this observation's clock; compare all persisted business members.
                        JsonObject business = JsonNode.Parse(payload.GetRawText())!.AsObject();
                        business.Remove("freshness");
                        return JsonSerializer.SerializeToElement(business);
                    }
                }
                catch (EventStoreGatewayException missing) when (missing.StatusCode == 404
                    || missing.StatusCode == 500 && missing.ReasonCode == QueryProblemReasonCodes.InternalError
                        && missing.Detail == QueryAdapterFailureReason.ReadModelUnavailable) { }
                await Task.Delay(250, deadline.Token);
            }
        }
        async Task RequireAbsentAsync(string id)
        {
            EventStoreGatewayException missing = await Assert.ThrowsAsync<EventStoreGatewayException>(() =>
                authorized.SubmitQueryAsync(Query(id), cancellationToken: cancellation));
            // The qualified SDK's missing-detail sentinel maps to 500 in EventStore 4.1.0 (inventory C05).
            Assert.Equal(500, missing.StatusCode);
            Assert.Equal(QueryProblemReasonCodes.InternalError, missing.ReasonCode);
            Assert.Equal(QueryAdapterFailureReason.ReadModelUnavailable, missing.Detail);
            await PersistedPartyEvents.RequireNoPartyCreatedAsync("tenant-b", id, cancellation);
        }
    }

    private static SubmitQueryRequest Query(string id) => new("tenant-b", "party", id, "PartyDetail", "party-detail",
        JsonSerializer.SerializeToElement(new { PartyId = id }));
    private static string Payload(string id) => JsonSerializer.Serialize(new { PartyId = id });
    private static string Hash(JsonElement value) => Convert.ToHexStringLower(SHA256.HashData(Encoding.UTF8.GetBytes(value.GetRawText())));
    private static string Channels(HeadResult result) => result.Output + result.Error + result.Tool?.StructuredContent + JsonSerializer.Serialize(result.Tool?.Content);
    private static void AssertAccepted(HeadResult result, string operation, string tenant, string party)
    {
        string expected = JsonSerializer.Serialize(new { operation, messageId = "generated", correlationId = "generated", tenant,
            aggregateId = party, status = "accepted" });
        BoundaryHeads.AssertDocument(result, expected, isError: false, "messageId", "correlationId");
    }
    private static void AssertLocal(HeadResult result, string operation, string message)
    {
        BoundaryHeads.AssertDocument(result, JsonSerializer.Serialize(new { error = new { code = "validation_failed", operation,
            violations = new[] { new { path = "/tenant", message } } } }), isError: true);
        HeadDiagnostics.AssertNoGateway(result, process: true);
    }
    private static void AssertGatewayRefusal(HeadResult result, LiveGatewayForwarder forwarder, int before,
        int status, string? reason, string operation)
    {
        forwarder.Requests.Count.ShouldBe(before + 1);
        (int receivedStatus, string body) = forwarder.Responses[^1];
        receivedStatus.ShouldBe(status);
        var error = new Dictionary<string, object?> { ["code"] = "gateway_error", ["status"] = status };
        if (status == 401) error["detail"] = "Unauthorized";
        else
        {
            using JsonDocument problem = JsonDocument.Parse(body);
            JsonElement value = problem.RootElement;
            value.GetProperty("reasonCode").GetString().ShouldBe(reason);
            string? detail = value.GetProperty("detail").GetString();
            if (reason == "tenant_mismatch") detail.ShouldBe("Not authorized for tenant 'tenant-b'.");
            if (reason == "principal_not_member") detail.ShouldBe("Not authorized for tenant 'tenant-b'. No tenant authorization claims found. Access denied.");
            error["detail"] = detail;
            error["reason"] = reason;
            if (value.TryGetProperty("correlationId", out JsonElement correlation))
            {
                error["correlationId"] = correlation.GetString();
            }
            foreach (string member in new[] { "retryable", "clientAction", "retryAfter" })
                if (value.TryGetProperty(member, out JsonElement metadata)) error[member] = metadata.Clone();
        }
        BoundaryHeads.AssertDocument(result, JsonSerializer.Serialize(new { error }), isError: true);
        HeadDiagnostics.AssertGatewayOnly(result, forwarder.Url, operation == "parties.get-party" ? "/api/v1/queries" : "/api/v1/commands", status, process: true);
    }
}
