using System.Text.Json;
using Shouldly;
using static Hexalith.McpCli.Cli.Tests.QueryCliHarness;

namespace Hexalith.McpCli.Cli.Tests;

/// <summary>Exercises declared platform scopes through the built CLI verbs.</summary>
public sealed class PlatformScopeCommandTests
{
    private const string ItemId = "01ARZ3NDEKTSV4RRFFQ69G5FAV";

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
        envelope.GetProperty("arguments").EnumerateArray().Select(item => item.GetString()).ShouldNotContain("tenant");
        harness.Calls.ShouldBe(0);
    }

    /// <summary>Query sends its declared scope despite an unrelated session tenant.</summary>
    [Fact]
    public async Task QueryUsesDeclaredPlatformScopeAsync()
    {
        await using var harness = new QueryCliHarness();
        (int exit, string output, string error) = await harness.InvokeAsync(
            ["query", "routing-fixture.items-list", "--payload", "{}", "--aggregate-id", ItemId,
                "--tenant", "session-tenant"]);

        exit.ShouldBe(0, output + error);
        harness.AssertRequest(JsonSerializer.Serialize(new
        {
            tenant = "platform:routing",
            domain = "routing",
            aggregateId = ItemId,
            queryType = "list-items-wire",
            projectionType = "routing-items",
            payload = new { },
        }));
        AssertJson(output, """{"operation":"routing-fixture.items-list","tenant":"platform:routing","document":{"items":[]}}""");
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
    }
}
