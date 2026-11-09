using System.Diagnostics;
using System.Text.Json;
using System.Text.Json.Nodes;
using Hexalith.McpCli.Cli.Tests;
using ModelContextProtocol.Protocol;
using Shouldly;

namespace Hexalith.McpCli.Integration.Tests;

/// <summary>Runs the existing production-catalog adapter in separate processes without changing the fixture package closure.</summary>
internal static class BoundaryHeads
{
    /// <summary>Runs one CLI invocation with a private configuration environment and every channel captured.</summary>
    internal static async Task<HeadResult> InvokeCliAsync(string profile, IReadOnlyDictionary<string, string?> environment,
        IReadOnlyList<string> arguments)
    {
        using var deadline = CancellationTokenSource.CreateLinkedTokenSource(TestContext.Current.CancellationToken);
        deadline.CancelAfter(TimeSpan.FromSeconds(45));
        using Process process = Start(profile, environment, arguments);
        Task<string> stdout = process.StandardOutput.ReadToEndAsync(deadline.Token);
        Task<string> stderr = process.StandardError.ReadToEndAsync(deadline.Token);
        try { await process.WaitForExitAsync(deadline.Token); }
        finally { if (!process.HasExited) process.Kill(entireProcessTree: true); }
        return new(process.ExitCode, await stdout, await stderr, null);
    }

    /// <summary>Initializes stdio MCP and calls exactly one tool, preserving text and structured content.</summary>
    internal static async Task<HeadResult> InvokeMcpAsync(string profile, IReadOnlyDictionary<string, string?> environment,
        IReadOnlyList<string> globals, string tool, IReadOnlyDictionary<string, object?> arguments)
    {
        using var deadline = CancellationTokenSource.CreateLinkedTokenSource(TestContext.Current.CancellationToken);
        deadline.CancelAfter(TimeSpan.FromSeconds(45));
        using Process process = Start(profile, environment, ["mcp", "--transport", "stdio", .. globals]);
        Task<string> stderr = process.StandardError.ReadToEndAsync(deadline.Token);
        try
        {
            await WriteAsync(new { jsonrpc = "2.0", id = 1, method = "initialize", @params = new
            { protocolVersion = "2025-06-18", capabilities = new { }, clientInfo = new { name = "retirement-boundary", version = "1" } } });
            _ = await ReadReplyAsync(1);
            await WriteAsync(new { jsonrpc = "2.0", method = "notifications/initialized", @params = new { } });
            await WriteAsync(new { jsonrpc = "2.0", id = 2, method = "tools/call", @params = new { name = tool, arguments } });
            JsonElement reply = await ReadReplyAsync(2);
            CallToolResult result = reply.GetProperty("result").Deserialize<CallToolResult>(new JsonSerializerOptions(JsonSerializerDefaults.Web))!;
            process.StandardInput.Close();
            Task<string> trailingOutput = process.StandardOutput.ReadToEndAsync(deadline.Token);
            await process.WaitForExitAsync(deadline.Token);
            return new(process.ExitCode, await trailingOutput, await stderr, result);
        }
        finally { if (!process.HasExited) process.Kill(entireProcessTree: true); }

        async Task WriteAsync(object message)
        {
            await process.StandardInput.WriteLineAsync(JsonSerializer.Serialize(message).AsMemory(), deadline.Token);
            await process.StandardInput.FlushAsync(deadline.Token);
        }
        async Task<JsonElement> ReadReplyAsync(int id)
        {
            while (true)
            {
                string? line = await process.StandardOutput.ReadLineAsync(deadline.Token);
                Assert.NotNull(line);
                using JsonDocument message = JsonDocument.Parse(line);
                JsonElement frame = message.RootElement;
                frame.GetProperty("jsonrpc").GetString().ShouldBe("2.0");
                if (frame.TryGetProperty("id", out JsonElement received) && received.GetInt32() == id)
                {
                    frame.TryGetProperty("error", out _).ShouldBeFalse();
                    return frame.Clone();
                }
                // Only protocol notifications may precede the matching response; all stdout must be JSON-RPC.
                frame.TryGetProperty("method", out _).ShouldBeTrue();
            }
        }
    }

    /// <summary>Checks the complete error/result document on every supported channel.</summary>
    internal static void AssertDocument(HeadResult result, string expected, bool isError, params string[] mask)
    {
        if (result.Tool is null)
        {
            result.Exit.ShouldBe(isError ? 2 : 0, result.Output + result.Error);
            AssertJson(result.Output, expected, mask);
            return;
        }
        result.Exit.ShouldBe(0, result.Error);
        result.Output.ShouldBeEmpty();
        result.Tool.IsError.ShouldBe(isError);
        AssertJson(result.Tool.StructuredContent.ShouldNotBeNull().GetRawText(), expected, mask);
        AssertJson(result.Tool.Content.ShouldHaveSingleItem().ShouldBeOfType<TextContentBlock>().Text, expected, mask);
    }

    /// <summary>Checks an accepted Command against its captured request and the complete Gateway result payload.</summary>
    internal static void AssertCommandAccepted(HeadResult result, string operation, string tenant, string aggregateId,
        GatewayRequest request, string responseBody)
    {
        using JsonDocument sent = JsonDocument.Parse(request.Body);
        using JsonDocument received = JsonDocument.Parse(responseBody);
        var expected = new JsonObject
        {
            ["operation"] = operation,
            ["messageId"] = received.RootElement.TryGetProperty("messageId", out JsonElement messageId)
                && messageId.ValueKind != JsonValueKind.Null ? messageId.GetString() : sent.RootElement.GetProperty("messageId").GetString(),
            ["correlationId"] = sent.RootElement.GetProperty("correlationId").GetString(),
            ["tenant"] = tenant,
            ["aggregateId"] = aggregateId,
            ["status"] = "accepted",
        };
        if (received.RootElement.TryGetProperty("resultPayload", out JsonElement payload) && payload.ValueKind != JsonValueKind.Null)
            expected["result"] = JsonNode.Parse(payload.GetRawText());
        AssertDocument(result, expected.ToJsonString(), isError: false);
    }

    /// <summary>Pins the qualified Gateway's complete missing/invalid-token challenge document.</summary>
    internal static void AssertAuthenticationRefusal(HeadResult result, bool credentialPresent)
    {
        string detail = credentialPresent ? "The provided authentication token is invalid."
            : "Authentication is required to access this resource.";
        AssertDocument(result, JsonSerializer.Serialize(new { error = new
        { code = "gateway_error", status = 401, detail, reason = "authentication_required" } }), isError: true);
    }

    /// <summary>Pins the qualified Gateway's complete signed-grant refusal, including its request correlation.</summary>
    internal static void AssertTenantAuthorizationRefusal(HeadResult result, string tenant, string reason, string correlationId)
    {
        string detail = $"Not authorized for tenant '{tenant}'."
            + (reason == "principal_not_member" ? " No tenant authorization claims found. Access denied." : string.Empty);
        AssertDocument(result, JsonSerializer.Serialize(new { error = new
        { code = "gateway_error", status = 403, detail, reason, correlationId } }), isError: true);
    }

    private static void AssertJson(string actual, string expected, string[] mask)
    {
        JsonNode actualNode = JsonNode.Parse(actual)!;
        JsonNode expectedNode = JsonNode.Parse(expected)!;
        foreach (string member in mask)
        {
            if (actualNode is JsonObject actualObject && actualObject.ContainsKey(member)) actualObject[member] = "<generated>";
            if (expectedNode is JsonObject expectedObject && expectedObject.ContainsKey(member)) expectedObject[member] = "<generated>";
        }
        JsonElement.DeepEquals(JsonSerializer.SerializeToElement(actualNode), JsonSerializer.SerializeToElement(expectedNode))
            .ShouldBeTrue(actual);
    }

    private static string RepositoryRoot()
    {
        for (DirectoryInfo? directory = new(AppContext.BaseDirectory); directory is not null; directory = directory.Parent)
            if (File.Exists(Path.Combine(directory.FullName, "Hexalith.McpCli.slnx"))) return directory.FullName;
        throw new InvalidOperationException("Repository root is missing.");
    }

    private static Process Start(string profile, IReadOnlyDictionary<string, string?> environment, IReadOnlyList<string> arguments)
    {
        var start = new ProcessStartInfo("dotnet")
        { RedirectStandardInput = true, RedirectStandardOutput = true, RedirectStandardError = true, WorkingDirectory = RepositoryRoot() };
        start.ArgumentList.Add(Path.Combine(RepositoryRoot(),
            "tests/Hexalith.McpCli.ConformanceHost/bin/Release/net10.0/Hexalith.McpCli.ConformanceHost.dll"));
        foreach (string argument in arguments) start.ArgumentList.Add(argument);
        foreach (string key in start.Environment.Keys.Where(key => key.StartsWith("EVENTSTORE_", StringComparison.Ordinal)
            || key.StartsWith("MCPCLI_", StringComparison.Ordinal)).ToArray()) start.Environment.Remove(key);
        start.Environment["DOTNET_ENVIRONMENT"] = "Production";
        start.Environment["ASPNETCORE_ENVIRONMENT"] = "Production";
        start.Environment["MCPCLI_CONFORMANCE_PROFILE_PATH"] = profile;
        foreach ((string key, string? value) in environment) start.Environment[key] = value;
        return Process.Start(start)!;
    }
}
