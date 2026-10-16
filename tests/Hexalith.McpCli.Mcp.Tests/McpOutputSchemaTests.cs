using System.Text.Json;
using System.Text.Json.Nodes;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Core.Execution;
using Microsoft.Extensions.DependencyInjection;
using Json.Schema;
using ModelContextProtocol.Client;
using ModelContextProtocol.Protocol;
using NSubstitute;
using Shouldly;
using static Hexalith.McpCli.Mcp.Tests.McpTestSession;

namespace Hexalith.McpCli.Mcp.Tests;

/// <summary>Validates advertised schemas against real tool documents and hostile document mutations.</summary>
public sealed class McpOutputSchemaTests(ITestOutputHelper output)
{
    /// <summary>Both protocol flows advertise executable schemas with closed document objects and open payload values.</summary>
    [Theory]
    [InlineData("2025-06-18")]
    [InlineData("2026-07-28")]
    public async Task ActualResultsValidateAndDocumentMutationsFailAsync(string version)
    {
        await using McpTestSession session = await CreateAsync(version);
        IList<McpClientTool> tools = await session.Client.ListToolsAsync(cancellationToken: session.Token);
        int inputSize = tools.Sum(tool => tool.Name.Length + tool.ProtocolTool.Description!.Length
            + tool.ProtocolTool.InputSchema.GetRawText().Length);
        inputSize.ShouldBeLessThan(8000);
        int outputSize = 0;
        foreach (McpClientTool tool in tools)
        {
            JsonElement schemaDocument = tool.ProtocolTool.OutputSchema.ShouldNotBeNull();
            schemaDocument.GetProperty("type").GetString().ShouldBe("object");
            schemaDocument.GetProperty("oneOf").GetArrayLength().ShouldBe(2);
            outputSize += schemaDocument.GetRawText().Length;
            JsonSchema schema = JsonSchema.FromText(schemaDocument.GetRawText());
            object arguments = tool.Name switch
            {
                "list_modules" => new { },
                "list_operations" => new { module = "sample" },
                "describe_operation" => new { operation = "routing-fixture.envelope-item" },
                "send_command" => new SendCommandArguments("sample.create-item", CommandPayload, CorrelationId: CorrelationId),
                "run_query" => new RunQueryArguments("sample.get-item", QueryPayload),
                _ => throw new InvalidOperationException(tool.Name),
            };
            CallToolResult result = await session.CallAsync(tool.Name, arguments);
            result.IsError.ShouldBe(false);
            JsonElement actual = result.StructuredContent.ShouldNotBeNull();
            AssertValid(schema, actual, tool.Name);
            AssertClosedObjects(schema, JsonNode.Parse(actual.GetRawText())!, tool.Name);
            foreach (string member in RequiredMembers(tool.Name))
            {
                JsonObject missing = JsonNode.Parse(actual.GetRawText())!.AsObject();
                missing.Remove(member).ShouldBeTrue();
                schema.Evaluate(JsonSerializer.SerializeToElement(missing)).IsValid.ShouldBeFalse($"{tool.Name} must require {member}");
            }

            // Every tool can return a sanitized boundary error, including list_modules.
            await using McpTestSession broken = await CreateAsync(version, configure: (services, _) =>
            {
                ICatalog catalog = Substitute.For<ICatalog>();
                catalog.ListModules().Returns(_ => throw new InvalidOperationException("private"));
                catalog.ListOperations(Arg.Any<string>(), Arg.Any<string?>()).Returns(_ => throw new InvalidOperationException("private"));
                catalog.Describe(Arg.Any<string>()).Returns(_ => throw new InvalidOperationException("private"));
                services.AddSingleton(catalog);
                IOperationExecutor executor = Substitute.For<IOperationExecutor>();
                executor.ExecuteAsync(Arg.Any<OperationCall>(), Arg.Any<EnvelopeContext>(), Arg.Any<CancellationToken>(),
                    Arg.Any<Func<CancellationToken, Task<OperationError?>>?>()).Returns<Task<OperationOutcome>>(_ => throw new InvalidOperationException("private"));
                services.AddSingleton(executor);
            });
            CallToolResult failure = await broken.CallAsync(tool.Name, arguments);
            JsonElement error = AssertDocument(failure, new { error = new OperationError("internal_error", Message: "MCP tool invocation failed.") }, true);
            AssertValid(schema, error, tool.Name);
            AssertClosedObjects(schema, JsonNode.Parse(error.GetRawText())!, tool.Name);
            foreach (string member in new[] { "code", "message" })
            {
                JsonObject missing = JsonNode.Parse(error.GetRawText())!.AsObject();
                missing["error"]!.AsObject().Remove(member);
                schema.Evaluate(JsonSerializer.SerializeToElement(missing)).IsValid.ShouldBeFalse($"{tool.Name} internal_error must require {member}");
            }
        }

        output.WriteLine($"Protocol {version}: names/descriptions/input schemas {inputSize} characters; output schemas {outputSize} characters.");
    }

    /// <summary>Returned null, scalar and array query documents and optional paging are accepted without closing arbitrary data.</summary>
    [Theory]
    [InlineData("2025-06-18")]
    [InlineData("2026-07-28")]
    public async Task QueryVariantsAndCoreErrorsValidateAsync(string version)
    {
        await using McpTestSession session = await CreateAsync(version);
        IList<McpClientTool> tools = await session.Client.ListToolsAsync(cancellationToken: session.Token);
        foreach ((string tool, object arguments) in new (string, object)[]
        {
            ("list_operations", new { module = "unknown" }),
            ("list_operations", new { module = "sample", kind = "invalid" }),
            ("describe_operation", new { operation = "sample.unknown" }),
            ("describe_operation", new { operation = "lint-fixture.inspect-item" }),
            ("send_command", new SendCommandArguments("sample.create-item", "null")),
            ("send_command", new SendCommandArguments("sample.create-item", CommandPayload, CorrelationId: CorrelationId)),
            ("run_query", new RunQueryArguments("sample.create-item", CommandPayload)),
        })
        {
            JsonSchema schema = JsonSchema.FromText(tools.Single(item => item.Name == tool).ProtocolTool.OutputSchema!.Value.GetRawText());
            CallToolResult result = await session.CallAsync(tool, arguments);
            AssertValid(schema, result.StructuredContent!.Value, tool);
            AssertClosedObjects(schema, JsonNode.Parse(result.StructuredContent.Value.GetRawText())!, tool);
        }
    }

    private static string[] RequiredMembers(string tool) => tool switch
    {
        "list_modules" => ["modules"],
        "list_operations" => ["module", "operations"],
        "describe_operation" => ["name", "kind", "description", "schema", "envelope", "lintFindings", "submittable"],
        "send_command" => ["operation", "messageId", "correlationId", "tenant", "aggregateId", "status"],
        "run_query" => ["operation", "tenant", "document"],
        _ => throw new InvalidOperationException(tool),
    };

    private static void AssertValid(JsonSchema schema, JsonElement actual, string tool)
    {
        EvaluationResults result = schema.Evaluate(actual, new EvaluationOptions { OutputFormat = OutputFormat.List });
        result.IsValid.ShouldBeTrue($"{tool}: {actual.GetRawText()}\n{JsonSerializer.Serialize(result)}");
    }

    private static void AssertClosedObjects(JsonSchema schema, JsonNode document, string tool)
    {
        var paths = new List<string[]>();
        Collect(document, []);
        foreach (string[] path in paths)
        {
            JsonNode mutated = document.DeepClone();
            JsonNode current = mutated;
            foreach (string segment in path)
            {
                current = current is JsonArray array ? array[int.Parse(segment, System.Globalization.CultureInfo.InvariantCulture)]! : current[segment]!;
            }

            current.AsObject()["unexpectedDocumentMember"] = true;
            schema.Evaluate(JsonSerializer.SerializeToElement(mutated)).IsValid.ShouldBeFalse($"{tool}: extra member at /{string.Join('/', path)} must fail");
        }

        void Collect(JsonNode? node, string[] path)
        {
            if (node is JsonObject obj)
            {
                paths.Add(path);
                foreach ((string name, JsonNode? child) in obj)
                {
                    if (name is not ("schema" or "example" or "document" or "result"))
                    {
                        Collect(child, [.. path, name]);
                    }
                }
            }
            else if (node is JsonArray array)
            {
                for (int index = 0; index < array.Count; index++)
                {
                    Collect(array[index], [.. path, index.ToString(System.Globalization.CultureInfo.InvariantCulture)]);
                }
            }
        }
    }
}
