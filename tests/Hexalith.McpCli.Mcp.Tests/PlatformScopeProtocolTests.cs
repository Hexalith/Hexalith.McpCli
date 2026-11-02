using System.Text.Json;
using System.Text.Json.Nodes;
using Hexalith.EventStore.Contracts.Commands;
using Hexalith.EventStore.Contracts.Queries;
using Hexalith.McpCli.Core.Execution;
using Json.Schema;
using ModelContextProtocol.Client;
using ModelContextProtocol.Protocol;
using NSubstitute;
using Shouldly;
using static Hexalith.McpCli.Mcp.Tests.McpTestSession;

namespace Hexalith.McpCli.Mcp.Tests;

/// <summary>Checks canonical scope behavior and advertised result schemas through both MCP protocols.</summary>
public sealed class PlatformScopeProtocolTests
{
    /// <summary>Describe and execution retain the declared scope over unrelated session tenants.</summary>
    [Theory]
    [InlineData("2025-06-18")]
    [InlineData("2026-07-28")]
    public async Task DescribeSendAndQueryPreserveDeclaredScopeAsync(string version)
    {
        await using McpTestSession session = await CreateAsync(version);
        IList<McpClientTool> tools = await session.Client.ListToolsAsync(cancellationToken: session.Token);
        foreach (bool command in new[] { false, true })
        {
            string operation = command ? "routing-fixture.colon-wire" : "routing-fixture.items-list";
            CallToolResult described = await session.CallAsync("describe_operation", new { operation });
            JsonElement description = AssertSchema(described, tools.Single(tool => tool.Name == "describe_operation"));
            JsonElement envelope = description.GetProperty("envelope");
            envelope.GetProperty("platformScope").GetString().ShouldBe("platform:routing");
            envelope.TryGetProperty("fixedTenant", out _).ShouldBeFalse();
            envelope.GetProperty("arguments").EnumerateArray().Select(item => item.GetString()).ShouldNotContain("tenant");
            JsonNode malformed = JsonNode.Parse(description.GetRawText())!;
            malformed["envelope"]!["platformScope"] = 42;
            JsonSchema.FromText(tools.Single(tool => tool.Name == "describe_operation").ProtocolTool.OutputSchema!.Value.GetRawText())
                .Evaluate(JsonSerializer.SerializeToElement(malformed)).IsValid.ShouldBeFalse();

            foreach (string? supplied in new string?[] { null, "platform:routing" })
            {
                session.Gateway.ClearReceivedCalls();
                string toolName = command ? "send_command" : "run_query";
                OperationCall call = command
                    ? new SendCommandArguments(operation, QueryPayload, Tenant: supplied)
                    : new RunQueryArguments(operation, "{}", Tenant: supplied, AggregateId: ItemId);
                CallToolResult result = await session.CallAsync(toolName, call);
                AssertSchema(result, tools.Single(tool => tool.Name == toolName)).GetProperty("tenant").GetString()
                    .ShouldBe("platform:routing");
                object request = session.Gateway.ReceivedCalls().ShouldHaveSingleItem().GetArguments()[0]!;
                if (command)
                {
                    SubmitCommandRequest sent = request.ShouldBeOfType<SubmitCommandRequest>();
                    sent.Tenant.ShouldBe("platform:routing");
                    sent.Domain.ShouldBe("routing");
                    sent.AggregateId.ShouldBe(ItemId);
                    sent.CommandType.ShouldBe("items:colon");
                }
                else
                {
                    SubmitQueryRequest sent = request.ShouldBeOfType<SubmitQueryRequest>();
                    sent.Tenant.ShouldBe("platform:routing");
                    sent.Domain.ShouldBe("routing");
                    sent.AggregateId.ShouldBe(ItemId);
                    sent.QueryType.ShouldBe("list-items-wire");
                    sent.ProjectionType.ShouldBe("routing-items");
                }
            }
        }
    }

    /// <summary>Conflicting command and query scope input is rejected before gateway submission.</summary>
    [Theory]
    [InlineData("2025-06-18", false)]
    [InlineData("2025-06-18", true)]
    [InlineData("2026-07-28", false)]
    [InlineData("2026-07-28", true)]
    public async Task ConflictingPerCallScopeIsRefusedAsync(string version, bool command)
    {
        await using McpTestSession session = await CreateAsync(version);
        string toolName = command ? "send_command" : "run_query";
        OperationCall call = command
            ? new SendCommandArguments("routing-fixture.colon-wire", QueryPayload, Tenant: "platform:other")
            : new RunQueryArguments("routing-fixture.items-list", "{}", Tenant: "platform:other");
        IList<McpClientTool> tools = await session.Client.ListToolsAsync(cancellationToken: session.Token);
        JsonElement result = AssertSchema(await session.CallAsync(toolName, call),
            tools.Single(tool => tool.Name == toolName), isError: true);
        result.GetProperty("error").GetProperty("code").GetString().ShouldBe("validation_failed");
        result.GetProperty("error").GetProperty("violations").EnumerateArray().ShouldHaveSingleItem()
            .GetProperty("path").GetString().ShouldBe("/tenant");
        session.Gateway.ReceivedCalls().ShouldBeEmpty();
    }

    /// <summary>Mixed-case public tenant input works with a matching lowercase session or no session.</summary>
    [Theory]
    [InlineData("2025-06-18", "acme", false)]
    [InlineData("2025-06-18", "acme", true)]
    [InlineData("2025-06-18", null, false)]
    [InlineData("2025-06-18", null, true)]
    [InlineData("2026-07-28", "acme", false)]
    [InlineData("2026-07-28", "acme", true)]
    [InlineData("2026-07-28", null, false)]
    [InlineData("2026-07-28", null, true)]
    public async Task MixedCasePublicTenantIsForwardedCanonicallyAsync(string version, string? sessionTenant, bool command)
    {
        await using McpTestSession session = await CreateAsync(version, Settings(sessionTenant));
        OperationCall call = command
            ? new SendCommandArguments("routing-fixture.envelope-item", QueryPayload, Tenant: "AcMe",
                CorrelationId: CorrelationId, IdempotencyKey: Key)
            : new RunQueryArguments("routing-fixture.get-http2-status", "{}", Tenant: "AcMe", AggregateId: ItemId);
        string toolName = command ? "send_command" : "run_query";
        IList<McpClientTool> tools = await session.Client.ListToolsAsync(cancellationToken: session.Token);
        AssertSchema(await session.CallAsync(toolName, call), tools.Single(tool => tool.Name == toolName))
            .GetProperty("tenant").GetString().ShouldBe("acme");
        object request = session.Gateway.ReceivedCalls().ShouldHaveSingleItem().GetArguments()[0]!;
        if (command)
        {
            SubmitCommandRequest sent = request.ShouldBeOfType<SubmitCommandRequest>();
            sent.Tenant.ShouldBe("acme");
            sent.Payload.GetProperty("tenant/~").GetString().ShouldBe("acme");
        }
        else
        {
            request.ShouldBeOfType<SubmitQueryRequest>().Tenant.ShouldBe("acme");
        }
    }

    private static JsonElement AssertSchema(CallToolResult result, McpClientTool tool, bool isError = false)
    {
        result.IsError.ShouldBe(isError);
        JsonElement actual = result.StructuredContent.ShouldNotBeNull();
        JsonSchema schema = JsonSchema.FromText(tool.ProtocolTool.OutputSchema.ShouldNotBeNull().GetRawText());
        schema.Evaluate(actual).IsValid.ShouldBeTrue(actual.GetRawText());
        JsonNode extra = JsonNode.Parse(actual.GetRawText())!;
        extra["unexpectedDocumentMember"] = true;
        schema.Evaluate(JsonSerializer.SerializeToElement(extra)).IsValid.ShouldBeFalse();
        using JsonDocument text = JsonDocument.Parse(result.Content.ShouldHaveSingleItem().ShouldBeOfType<TextContentBlock>().Text);
        JsonElement.DeepEquals(text.RootElement, actual).ShouldBeTrue();
        return actual;
    }
}
