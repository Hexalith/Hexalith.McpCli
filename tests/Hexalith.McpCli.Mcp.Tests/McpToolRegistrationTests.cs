using Hexalith.McpCli.Core.Settings;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Options;
using ModelContextProtocol.Server;
using Shouldly;

namespace Hexalith.McpCli.Mcp.Tests;

/// <summary>Checks that the SDK sees exactly the permitted generic tool set.</summary>
public sealed class McpToolRegistrationTests
{
    /// <summary>A writable session contains five unique tools and their structured output contracts.</summary>
    [Theory]
    [InlineData(false, 5)]
    [InlineData(true, 4)]
    public void RegistersOnlyPermittedGenericTools(bool readOnly, int expectedCount)
    {
        var services = new ServiceCollection();
        services.AddLogging();
        services.AddMcpCliMcpServer(Settings(readOnly));
        using ServiceProvider provider = services.BuildServiceProvider();
        McpServerOptions options = provider.GetRequiredService<IOptions<McpServerOptions>>().Value;

        McpServerPrimitiveCollection<McpServerTool> collection = options.ToolCollection.ShouldNotBeNull();
        collection.Count.ShouldBe(expectedCount);
        string[] names = collection.Select(tool => tool.ProtocolTool.Name).OrderBy(name => name, StringComparer.Ordinal).ToArray();
        names.ShouldBe(readOnly
            ? new[] { "describe_operation", "list_modules", "list_operations", "run_query" }
            : new[] { "describe_operation", "list_modules", "list_operations", "run_query", "send_command" });
        foreach (McpServerTool tool in collection)
        {
            tool.ProtocolTool.InputSchema.ValueKind.ShouldBe(System.Text.Json.JsonValueKind.Object);
            tool.ProtocolTool.OutputSchema.ShouldNotBeNull();
            tool.ProtocolTool.OutputSchema.Value.GetProperty("oneOf").GetArrayLength().ShouldBe(2);
            tool.ProtocolTool.Description.ShouldNotBeNullOrWhiteSpace();
            string description = tool.ProtocolTool.Description!;
            description.ShouldContain("Purpose:");
            description.ShouldContain("Use when:");
            description.ShouldContain("Next:");
            (description.IndexOf("Purpose:", StringComparison.Ordinal)
                < description.IndexOf("Use when:", StringComparison.Ordinal)).ShouldBeTrue();
            (description.IndexOf("Use when:", StringComparison.Ordinal)
                < description.IndexOf("Next:", StringComparison.Ordinal)).ShouldBeTrue();
            tool.ProtocolTool.Annotations.ShouldNotBeNull().ReadOnlyHint.ShouldBe(tool.ProtocolTool.Name != "send_command");
        }

        if (!readOnly)
        {
            var writeAnnotations = collection["send_command"].ProtocolTool.Annotations.ShouldNotBeNull();
            writeAnnotations.IdempotentHint.ShouldBe(false);
            writeAnnotations.DestructiveHint.ShouldBe(true);
        }

        static string[] Required(McpServerTool tool)
            => tool.ProtocolTool.InputSchema.TryGetProperty("required", out var required)
                ? required.EnumerateArray().Select(item => item.GetString()!).ToArray()
                : [];

        Required(collection["list_modules"]).ShouldBeEmpty();
        Required(collection["list_operations"]).ShouldBe(new[] { "module" });
        Required(collection["describe_operation"]).ShouldBe(new[] { "operation" });
        Required(collection["run_query"]).ShouldBe(new[] { "operation", "payload" });
        if (!readOnly)
        {
            Required(collection["send_command"]).ShouldBe(new[] { "operation", "payload" });
        }

        int inputLength = collection.Sum(tool => tool.ProtocolTool.Name.Length
            + (tool.ProtocolTool.Description?.Length ?? 0) + tool.ProtocolTool.InputSchema.GetRawText().Length);
        inputLength.ShouldBeLessThan(8000);

        options.Filters.Message.IncomingFilters.Count.ShouldBe(1);
        options.Filters.Request.ListToolsFilters.Count.ShouldBe(1);
    }

    private static ResolvedSettings Settings(bool readOnly)
        => new(null, null, null, null, false, new HashSet<string>(StringComparer.OrdinalIgnoreCase),
            "json", null, readOnly, false, null, new Dictionary<string, string>());
}
