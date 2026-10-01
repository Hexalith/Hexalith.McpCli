using System.Text.Json;
using System.Text.Json.Nodes;
using Shouldly;
using static Hexalith.McpCli.Cli.Tests.QueryCliHarness;

namespace Hexalith.McpCli.Cli.Tests;

/// <summary>Checks CLI query refusal documents, exit codes, and absence of gateway requests.</summary>
public sealed class QueryValidationCommandTests
{
    /// <summary>Malformed or duplicate JSON returns exactly one root violation.</summary>
    [Theory]
    [InlineData("{")]
    [InlineData("{\"ItemId\":\"a\",\"ItemId\":\"b\"}")]
    [InlineData("{\"Nested\":{\"nested/~\":1,\"nested/~\":2}}")]
    public async Task InvalidJsonExitsTwoWithoutRequestsAsync(string payload)
    {
        await using var harness = new QueryCliHarness();
        (int exit, string output, string error) = await harness.InvokeAsync(
            ["query", "lint-fixture.inspect-item", "--payload", payload, "--tenant", "session-tenant"]);
        AssertValidation(exit, output, error, "lint-fixture.inspect-item", "/");
        using JsonDocument document = JsonDocument.Parse(output);
        document.RootElement.GetProperty("error").GetProperty("violations").GetArrayLength().ShouldBe(1);
        harness.Calls.ShouldBe(0);
    }

    /// <summary>Nested failures are reported together with escaped RFC 6901 paths.</summary>
    [Fact]
    public async Task NestedFailuresKeepEverySerializedPointerAsync()
    {
        const string payload = """
            {"ItemId":"01ARZ3NDEKTSV4RRFFQ69G5FAV","ExternalId":42,
             "Nested":{"Label":false,"nested/~":7,"page/~size":"bad"},
             "Entries":[{"Count":"bad","MarkedId":"01ARZ3NDEKTSV4RRFFQ69G5FAV"}],
             "EntriesByKey":{"key/~":{"Quantity":false}}}
            """;
        await using var harness = new QueryCliHarness();
        (int exit, string output, string error) = await harness.InvokeAsync(
            ["query", "lint-fixture.inspect-item", "--payload", payload, "--tenant", "session-tenant"]);
        AssertValidation(exit, output, error, "lint-fixture.inspect-item", "/", "/ExternalId", "/Nested", "/Nested/Label", "/Nested/nested~1~0",
            "/Nested/page~1~0size", "/Entries", "/Entries/0", "/Entries/0/Count", "/EntriesByKey",
            "/EntriesByKey/key~1~0", "/EntriesByKey/key~1~0/Quantity");
        using JsonDocument document = JsonDocument.Parse(output);
        document.RootElement.GetProperty("error").GetProperty("violations").GetArrayLength().ShouldBe(12);
        harness.Calls.ShouldBe(0);
    }

    /// <summary>Supplies invalid envelope identifiers and query paging options through real CLI bindings.</summary>
    public static IEnumerable<object?[]> InvalidOptions()
    {
        foreach (string value in new[] { "", " ", "not-a-ulid", "550e8400-e29b-41d4-a716-446655440000" })
        {
            yield return ["routing-fixture.get-http2-status", "--aggregate-id", value, "/aggregateId"];
        }

        foreach (string value in new[] { "-a", "a-", "a.b", "a_b", "A", "a/b", "a:b", "é", "a\n", new string('a', 65) })
        {
            yield return ["routing-fixture.get-http2-status", "--tenant", value, "/tenant"];
        }

        foreach (string option in new[] { "--aggregate-id", "--entity-id" })
        {
            foreach (string value in new[] { "", " ", "-a", "a-", ".a", "a.", "_a", "a_", "a/b", "a:b", "é", "a\n", new string('a', 257) })
            {
                yield return ["string-fixture.list-items", option, value, option == "--aggregate-id" ? "/aggregateId" : "/entityId"];
            }
        }

        yield return ["string-fixture.list-items", "--page-size", "0", "/pageSize"];
        yield return ["string-fixture.list-items", "--page-size", "201", "/pageSize"];
        yield return ["string-fixture.list-items", "--offset", "-1", "/offset"];
        yield return ["string-fixture.list-items", "--cursor", new string('x', 4097), "/cursor"];
        yield return ["string-fixture.list-items", "--cursor", string.Concat(Enumerable.Repeat("😀", 2048)) + "x", "/cursor"];
    }

    /// <summary>Invalid envelope options return the complete canonical failure document and zero requests.</summary>
    [Theory]
    [MemberData(nameof(InvalidOptions))]
    public async Task InvalidOptionsExitTwoWithoutRequestsAsync(string operation, string option, string value, string path)
    {
        await using var harness = new QueryCliHarness();
        List<string> arguments = ["query", operation, "--payload", "{}"];
        if (operation == "routing-fixture.get-http2-status")
        {
            if (option != "--aggregate-id")
            {
                arguments.AddRange(["--aggregate-id", ItemId]);
            }

            if (option != "--tenant")
            {
                arguments.AddRange(["--tenant", "session-tenant"]);
            }
        }

        arguments.AddRange([option, value]);
        (int exit, string output, string error) = await harness.InvokeAsync([.. arguments]);
        AssertValidation(exit, output, error, operation, path);
        string message = path switch
        {
            "/tenant" => "The tenant does not match the Gateway tenant pattern.",
            "/aggregateId" => "The aggregate identifier does not match the module and Gateway rules.",
            "/entityId" => "Entity identifier does not match the Gateway pattern.",
            "/pageSize" => "Page size must be between 1 and 200.",
            "/offset" => "Offset cannot be negative.",
            _ => "Cursor must be at most 4096 characters and cannot be combined with offset.",
        };
        AssertJson(output, JsonSerializer.Serialize(new
        {
            error = new { code = "validation_failed", operation, violations = new[] { new { path, message } } },
        }));
        harness.Calls.ShouldBe(0);
    }

    /// <summary>A nonblank cursor conflicts with an explicitly supplied zero offset.</summary>
    [Fact]
    public async Task CursorWithOffsetZeroMakesNoRequestsAsync()
    {
        await using var harness = new QueryCliHarness();
        (int exit, string output, string error) = await harness.InvokeAsync(
            ["query", "string-fixture.list-items", "--payload", "{}", "--offset", "0", "--cursor", "opaque-cursor"]);
        AssertValidation(exit, output, error, "string-fixture.list-items", "/cursor");
        AssertJson(output, """
            {"error":{"code":"validation_failed","operation":"string-fixture.list-items",
            "violations":[{"path":"/cursor","message":"Cursor must be at most 4096 characters and cannot be combined with offset."}]}}
            """);
        harness.Calls.ShouldBe(0);
    }

    /// <summary>Omitting the session tenant on a query without a fixed tenant fails at the envelope path.</summary>
    [Fact]
    public async Task MissingTenantMakesNoRequestsAsync()
    {
        await using var harness = new QueryCliHarness();
        (int exit, string output, string error) = await harness.InvokeAsync(
            ["query", "routing-fixture.get-http2-status", "--payload", "{}", "--aggregate-id", ItemId]);
        AssertValidation(exit, output, error, "routing-fixture.get-http2-status", "/tenant");
        AssertJson(output, """
            {"error":{"code":"validation_failed","operation":"routing-fixture.get-http2-status",
            "violations":[{"path":"/tenant","message":"The tenant does not match the Gateway tenant pattern."}]}}
            """);
        harness.Calls.ShouldBe(0);
    }

    /// <summary>Payload accessor identifiers fail at the payload member rather than the envelope aggregate.</summary>
    [Theory]
    [InlineData("not-a-ulid")]
    [InlineData("550e8400-e29b-41d4-a716-446655440000")]
    public async Task InvalidPayloadAggregateUsesPayloadPointerAsync(string identifier)
    {
        JsonNode payload = JsonNode.Parse(InspectPayload)!;
        payload["ItemId"] = identifier;
        await using var harness = new QueryCliHarness();
        (int exit, string output, string error) = await harness.InvokeAsync(
            ["query", "lint-fixture.inspect-item", "--payload", payload.ToJsonString(), "--tenant", "session-tenant"]);
        AssertValidation(exit, output, error, "lint-fixture.inspect-item", "/", "/ItemId");
        harness.Calls.ShouldBe(0);
    }

    /// <summary>Caller tenant conflicts and non-string values are refused before envelope filling.</summary>
    [Theory]
    [InlineData("\"other-tenant\"")]
    [InlineData("null")]
    [InlineData("42")]
    [InlineData("false")]
    [InlineData("{}")]
    [InlineData("[]")]
    public async Task RawTenantOwnershipFailuresMakeNoRequestsAsync(string tenant)
    {
        JsonNode payload = JsonNode.Parse(InspectPayload)!;
        payload["Tenant"] = JsonNode.Parse(tenant);
        await using var harness = new QueryCliHarness();
        (int exit, string output, string error) = await harness.InvokeAsync(
            ["query", "lint-fixture.inspect-item", "--payload", payload.ToJsonString(), "--tenant", "session-tenant"]);
        AssertValidation(exit, output, error, "lint-fixture.inspect-item", "/Tenant");
        AssertJson(output, """
            {"error":{"code":"validation_failed","operation":"lint-fixture.inspect-item",
            "violations":[{"path":"/Tenant","message":"The payload tenant disagrees with the resolved tenant."}]}}
            """);
        harness.Calls.ShouldBe(0);
    }

    /// <summary>A missing Gateway URL returns configuration_invalid while all three discovery verbs remain available.</summary>
    [Fact]
    public async Task MissingUrlLeavesOfflineDiscoveryAvailableAsync()
    {
        await using var harness = new QueryCliHarness();
        (int exit, string output, string error) = await harness.InvokeAsync(
            ["query", "routing-fixture.get-http2-status", "--payload", "{}", "--aggregate-id", ItemId, "--tenant", "session-tenant"], withUrl: false);
        exit.ShouldBe(2);
        AssertDiagnostics(error);
        AssertJson(output, """{"error":{"code":"configuration_invalid","message":"Gateway URL is not configured."}}""");

        foreach (string[] arguments in new[] { new[] { "modules" }, new[] { "operations", "routing-fixture" }, new[] { "describe", "routing-fixture.get-http2-status" } })
        {
            (int discoveryExit, string discoveryOutput, string discoveryError) = await harness.InvokeAsync(arguments, withUrl: false);
            discoveryExit.ShouldBe(0, discoveryOutput + discoveryError);
            AssertDiagnostics(discoveryError);
            using JsonDocument document = JsonDocument.Parse(discoveryOutput);
            document.RootElement.TryGetProperty("error", out _).ShouldBeFalse();
            if (arguments[0] == "describe")
            {
                document.RootElement.GetProperty("submittable").GetBoolean().ShouldBeFalse();
                document.RootElement.GetProperty("reason").GetString().ShouldBe("configuration_invalid");
            }
        }

        harness.Calls.ShouldBe(0);
    }

    private static void AssertValidation(int exit, string output, string stderr, string operation, params string[] paths)
    {
        exit.ShouldBe(2, output + stderr);
        AssertDiagnostics(stderr);
        using JsonDocument document = JsonDocument.Parse(output);
        document.RootElement.EnumerateObject().Select(member => member.Name).ShouldBe(["error"]);
        JsonElement error = document.RootElement.GetProperty("error");
        error.EnumerateObject().Select(member => member.Name).Order(StringComparer.Ordinal).ShouldBe(["code", "operation", "violations"]);
        error.GetProperty("code").GetString().ShouldBe("validation_failed");
        error.GetProperty("operation").GetString().ShouldBe(operation);
        JsonElement[] violations = [.. error.GetProperty("violations").EnumerateArray()];
        violations.ShouldNotBeEmpty();
        violations.Select(item => item.GetProperty("path").GetString()).Distinct().Order(StringComparer.Ordinal).ShouldBe(paths.Order(StringComparer.Ordinal));
        foreach (JsonElement violation in violations)
        {
            violation.EnumerateObject().Select(member => member.Name).Order(StringComparer.Ordinal).ShouldBe(["message", "path"]);
            violation.GetProperty("message").GetString().ShouldNotBeNullOrWhiteSpace();
        }
    }
}
