using System.Text.Json;
using Shouldly;
using static Hexalith.McpCli.Cli.Tests.QueryCliHarness;

namespace Hexalith.McpCli.Cli.Tests;

/// <summary>Exercises declared platform scopes through the built CLI verbs.</summary>
public sealed class PlatformScopeCommandTests
{
    private const string ItemId = "01ARZ3NDEKTSV4RRFFQ69G5FAV";

    /// <summary>Reserved public tenant input returns the full CLI refusal without submitting either operation.</summary>
    [Theory]
    [InlineData(false, "system")]
    [InlineData(false, "SyStEm")]
    [InlineData(true, "system")]
    [InlineData(true, "SyStEm")]
    public async Task ReservedSystemTenantExitsTwoWithoutRequestsAsync(bool command, string tenant)
    {
        await using var harness = new QueryCliHarness(commandResponse: command);
        string operation = command ? "routing-fixture.envelope-item" : "routing-fixture.get-http2-status";
        string[] arguments = command
            ? ["send", operation, "--payload", JsonSerializer.Serialize(new { ItemId }), "--tenant", tenant,
                "--actor", "operator-1", "--correlation-id", "01J9MZHXT3RKM0VWXRXGSJDATK",
                "--idempotency-key", "01J9MZHXT3RKM0VWXRXGSJDATN"]
            : ["query", operation, "--payload", "{}", "--aggregate-id", ItemId, "--tenant", tenant];
        (int exit, string output, string error) = await harness.InvokeAsync(arguments);

        exit.ShouldBe(2, output + error);
        AssertJson(output, JsonSerializer.Serialize(new
        {
            error = new
            {
                code = "validation_failed",
                operation,
                violations = new[] { new { path = "/tenant", message = "The public tenant 'system' is reserved." } },
            },
        }));
        AssertDiagnostics(error);
        error.ShouldNotContain("System.Net.Http");
        harness.Calls.ShouldBe(0);
    }

    /// <summary>Describe shows the fixed scope and omits the tenant argument.</summary>
    [Fact]
    public async Task DescribeReportsPlatformScopeAsync()
    {
        await using var harness = new QueryCliHarness();
        (int exit, string output, string error) = await harness.InvokeAsync(
            ["describe", "routing-fixture.items-list"], withUrl: false);

        exit.ShouldBe(0, output + error);
        using JsonDocument document = JsonDocument.Parse(output);
        JsonElement envelope = document.RootElement.GetProperty("envelope");
        envelope.GetProperty("platformScope").GetString().ShouldBe("platform:routing");
        envelope.GetProperty("aggregateIdRequired").GetBoolean().ShouldBeFalse();
        envelope.GetProperty("arguments").EnumerateArray().Select(item => item.GetString()).ShouldNotContain("tenant");
        harness.Calls.ShouldBe(0);
    }

    /// <summary>Query uses its declared scope and default aggregate, and accepts a valid explicit aggregate.</summary>
    [Theory]
    [InlineData(null, ItemId)]
    [InlineData("01ARZ3NDEKTSV4RRFFQ69G5FAW", "01ARZ3NDEKTSV4RRFFQ69G5FAW")]
    public async Task QueryUsesDeclaredPlatformScopeAsync(string? explicitId, string expectedId)
    {
        await using var harness = new QueryCliHarness();
        string[] arguments = ["query", "routing-fixture.items-list", "--payload", "{}", "--tenant", "session-tenant"];
        if (explicitId is not null)
        {
            arguments = [.. arguments, "--aggregate-id", explicitId];
        }

        (int exit, string output, string error) = await harness.InvokeAsync(arguments);

        exit.ShouldBe(0, output + error);
        harness.AssertRequest(JsonSerializer.Serialize(new
        {
            tenant = "platform:routing",
            domain = "routing",
            aggregateId = expectedId,
            queryType = "list-items-wire",
            projectionType = "routing-items",
            payload = new { },
        }));
        AssertJson(output, """{"operation":"routing-fixture.items-list","tenant":"platform:routing","document":{"items":[]}}""");
    }

    /// <summary>A malformed explicit ID fails before the Gateway even when a valid default exists.</summary>
    [Fact]
    public async Task InvalidExplicitIdDoesNotFallBackToDefaultAsync()
    {
        await using var harness = new QueryCliHarness();
        const string operation = "routing-fixture.items-list";
        (int exit, string output, string error) = await harness.InvokeAsync(
            ["query", operation, "--payload", "{}", "--aggregate-id", "01arz3ndektsv4rrffq69g5fav"]);

        exit.ShouldBe(2, output + error);
        AssertJson(output, JsonSerializer.Serialize(new
        {
            error = new
            {
                code = "validation_failed",
                operation,
                violations = new[] { new { path = "/aggregateId", message = "The aggregate identifier does not match the module and Gateway rules." } },
            },
        }));
        AssertDiagnostics(error);
        error.ShouldNotContain("System.Net.Http");
        harness.Calls.ShouldBe(0);
    }

    /// <summary>Send uses its declared scope despite an unrelated session tenant.</summary>
    [Fact]
    public async Task SendUsesDeclaredPlatformScopeAsync()
    {
        await using var harness = new QueryCliHarness(commandResponse: true);
        (int exit, string output, string error) = await harness.InvokeAsync(
            ["send", "routing-fixture.colon-wire", "--payload", JsonSerializer.Serialize(new { ItemId }),
                "--tenant", "session-tenant"]);

        exit.ShouldBe(0, output + error);
        using JsonDocument document = JsonDocument.Parse(output);
        document.RootElement.GetProperty("tenant").GetString().ShouldBe("platform:routing");
        document.RootElement.GetProperty("status").GetString().ShouldBe("accepted");
        harness.Calls.ShouldBe(1);
        JsonElement request = harness.AssertCommandRequest();
        request.GetProperty("tenant").GetString().ShouldBe("platform:routing");
        request.GetProperty("domain").GetString().ShouldBe("routing");
        request.GetProperty("aggregateId").GetString().ShouldBe(ItemId);
        request.GetProperty("commandType").GetString().ShouldBe("items:colon");
        AssertJson(request.GetProperty("payload").GetRawText(), JsonSerializer.Serialize(new { ItemId }));
    }
}
