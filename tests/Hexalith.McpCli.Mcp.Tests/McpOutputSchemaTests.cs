using System.Text.Json;
using System.Text.Json.Nodes;
using Hexalith.EventStore.Client.Gateway;
using Hexalith.EventStore.Contracts.Commands;
using Hexalith.EventStore.Contracts.Queries;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Core.Execution;
using Hexalith.McpCli.Core.Schema;
using Hexalith.McpCli.Core.Serialization;
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
        }

        output.WriteLine($"Protocol {version}: names/descriptions/input schemas {inputSize} characters; output schemas {outputSize} characters.");
    }

    /// <summary>Real Core lookup and validation errors and nested lint documents satisfy their complete contracts.</summary>
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
            ("describe_operation", new { operation = "sample.get-item" }),
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

    /// <summary>Arbitrary returned JSON remains open and paging and command optional fields follow actual Gateway responses.</summary>
    [Theory]
    [InlineData("2025-06-18")]
    [InlineData("2026-07-28")]
    public async Task ReturnedValuesAndOptionalMembersValidateAsync(string version)
    {
        await using McpTestSession session = await CreateAsync(version);
        IList<McpClientTool> tools = await session.Client.ListToolsAsync(cancellationToken: session.Token);
        JsonSchema querySchema = JsonSchema.FromText(tools.Single(tool => tool.Name == "run_query").ProtocolTool.OutputSchema!.Value.GetRawText());
        JsonSchema commandSchema = JsonSchema.FromText(tools.Single(tool => tool.Name == "send_command").ProtocolTool.OutputSchema!.Value.GetRawText());
        foreach (string json in new[] { "null", "42", "true", "\"text\"", "[1,null,{}]", "{\"unrecognized\":{\"nested\":[1,true]}}" })
        {
            JsonElement value = JsonSerializer.Deserialize<JsonElement>(json);
            foreach (QueryPagingMetadata? paging in new QueryPagingMetadata?[]
            {
                null, new(25), new(25, 0, "next", 0, false),
            })
            {
                session.Gateway.SubmitQueryAsync(Arg.Any<SubmitQueryRequest>(), Arg.Any<string?>(), Arg.Any<CancellationToken>())
                    .Returns(Task.FromResult(new EventStoreQueryResult(CorrelationId, value, false, null)
                    {
                        Metadata = paging is null ? null : new QueryResponseMetadata(Paging: paging),
                    }));
                CallToolResult result = await session.CallAsync("run_query", new RunQueryArguments("sample.get-item", QueryPayload));
                JsonElement actual = result.StructuredContent.ShouldNotBeNull();
                actual.GetProperty("document").ValueKind.ShouldBe(value.ValueKind);
                actual.TryGetProperty("paging", out _).ShouldBe(paging is not null);
                AssertValid(querySchema, actual, "run_query");
                AssertClosedObjects(querySchema, JsonNode.Parse(actual.GetRawText())!, "run_query");
            }

            session.Gateway.SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>())
                .Returns(Task.FromResult(new SubmitCommandResponse(CorrelationId, value, MessageId)));
            CallToolResult command = await session.CallAsync("send_command", new SendCommandArguments("sample.create-item", CommandPayload,
                CorrelationId: CorrelationId, IdempotencyKey: Key));
            JsonElement commandDocument = command.StructuredContent.ShouldNotBeNull();
            commandDocument.GetProperty("result").ValueKind.ShouldBe(value.ValueKind);
            commandDocument.GetProperty("idempotencyKey").GetString().ShouldBe(Key);
            AssertValid(commandSchema, commandDocument, "send_command");
            AssertClosedObjects(commandSchema, JsonNode.Parse(commandDocument.GetRawText())!, "send_command");
        }
    }

    /// <summary>Gateway failures with all metadata or no metadata and unavailable sessions validate as real error fixtures.</summary>
    [Theory]
    [InlineData("2025-06-18")]
    [InlineData("2026-07-28")]
    public async Task GatewayAndAvailabilityErrorsValidateAsync(string version)
    {
        await using McpTestSession session = await CreateAsync(version);
        IList<McpClientTool> tools = await session.Client.ListToolsAsync(cancellationToken: session.Token);
        foreach (EventStoreGatewayException exception in new[]
        {
            new EventStoreGatewayException(409, "Conflict"),
            new EventStoreGatewayException(429, "Throttled", detail: "Rate limited.", reasonCode: "busy", retryable: false,
                clientAction: "wait", retryAfter: "30", correlationId: CorrelationId),
        })
        {
            session.Gateway.SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>())
                .Returns<Task<SubmitCommandResponse>>(_ => throw exception);
            session.Gateway.SubmitQueryAsync(Arg.Any<SubmitQueryRequest>(), Arg.Any<string?>(), Arg.Any<CancellationToken>())
                .Returns<Task<EventStoreQueryResult>>(_ => throw exception);
            foreach ((string tool, OperationCall arguments) in new (string, OperationCall)[]
            {
                ("send_command", new SendCommandArguments("sample.create-item", CommandPayload)),
                ("run_query", new RunQueryArguments("sample.get-item", QueryPayload)),
            })
            {
                JsonSchema schema = JsonSchema.FromText(tools.Single(item => item.Name == tool).ProtocolTool.OutputSchema!.Value.GetRawText());
                JsonElement actual = AssertDocument(await session.CallAsync(tool, arguments), new { error = OperationError.FromGateway(exception) }, true);
                AssertValid(schema, actual, tool);
                AssertClosedObjects(schema, JsonNode.Parse(actual.GetRawText())!, tool);
            }
        }

        await using McpTestSession offline = await CreateAsync(version, Settings(hasUrl: false));
        foreach (string tool in new[] { "send_command", "run_query" })
        {
            object arguments = tool == "send_command"
                ? new SendCommandArguments("sample.create-item", CommandPayload)
                : new RunQueryArguments("sample.get-item", QueryPayload);
            JsonSchema schema = JsonSchema.FromText(tools.Single(item => item.Name == tool).ProtocolTool.OutputSchema!.Value.GetRawText());
            JsonElement actual = AssertDocument(await offline.CallAsync(tool, arguments), new
            {
                error = new OperationError("configuration_invalid", Message: "Gateway URL is not configured."),
            }, true);
            AssertValid(schema, actual, tool);
            AssertClosedObjects(schema, JsonNode.Parse(actual.GetRawText())!, tool);
        }

        JsonSchema descriptionSchema = JsonSchema.FromText(tools.Single(item => item.Name == "describe_operation").ProtocolTool.OutputSchema!.Value.GetRawText());
        JsonElement description = (await offline.CallAsync("describe_operation", new { operation = "sample.get-item" })).StructuredContent!.Value;
        AssertValid(descriptionSchema, description, "describe_operation");
        AssertClosedObjects(descriptionSchema, JsonNode.Parse(description.GetRawText())!, "describe_operation");
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

    /// <summary>Fixed result values and schema root types reject unsupported values without closing embedded schema objects.</summary>
    [Theory]
    [InlineData("2025-06-18")]
    [InlineData("2026-07-28")]
    public async Task DocumentDiscriminatorsAndPayloadSchemaRootsAreConstrainedAsync(string version)
    {
        await using McpTestSession session = await CreateAsync(version);
        IList<McpClientTool> tools = await session.Client.ListToolsAsync(cancellationToken: session.Token);
        foreach ((string tool, object arguments, string field) in new (string, object, string)[]
        {
            ("list_operations", new { module = "sample" }, "kind"),
            ("describe_operation", new { operation = "sample.get-item" }, "kind"),
            ("send_command", new SendCommandArguments("sample.create-item", CommandPayload), "status"),
        })
        {
            JsonSchema schema = JsonSchema.FromText(tools.Single(item => item.Name == tool).ProtocolTool.OutputSchema!.Value.GetRawText());
            CallToolResult result = await session.CallAsync(tool, arguments);
            JsonNode actual = JsonNode.Parse(result.StructuredContent!.Value.GetRawText())!;
            JsonNode target = tool == "list_operations" ? actual["operations"]![0]! : actual;
            target[field] = "unsupported";
            schema.Evaluate(JsonSerializer.SerializeToElement(actual)).IsValid.ShouldBeFalse($"{tool} must constrain {field}");
        }

        JsonSchema describeSchema = JsonSchema.FromText(tools.Single(item => item.Name == "describe_operation").ProtocolTool.OutputSchema!.Value.GetRawText());
        JsonNode description = JsonNode.Parse((await session.CallAsync("describe_operation", new { operation = "sample.get-item" }))
            .StructuredContent!.Value.GetRawText())!;
        foreach (string valid in new[] { "true", "false", "{\"custom\":{\"open\":[1,null,true]}}" })
        {
            description["schema"] = JsonNode.Parse(valid);
            AssertValid(describeSchema, JsonSerializer.SerializeToElement(description), "describe_operation");
        }

        foreach (string invalid in new[] { "42", "null", "[]", "\"schema\"" })
        {
            description["schema"] = JsonNode.Parse(invalid);
            describeSchema.Evaluate(JsonSerializer.SerializeToElement(description)).IsValid.ShouldBeFalse($"schema root {invalid} must fail");
        }
    }

    /// <summary>Every advertised schema enforces each error code's document shape and refuses unknown codes.</summary>
    [Theory]
    [InlineData("2025-06-18")]
    [InlineData("2026-07-28")]
    public async Task ErrorCodesDiscriminateTheirDocumentShapesAsync(string version)
    {
        await using McpTestSession session = await CreateAsync(version);
        IList<McpClientTool> tools = await session.Client.ListToolsAsync(cancellationToken: session.Token);
        foreach (McpClientTool tool in tools)
        {
            JsonSchema schema = JsonSchema.FromText(tool.ProtocolTool.OutputSchema!.Value.GetRawText());
            foreach ((OperationError error, string mismatchedCode) in new (OperationError, string)[]
            {
                (new("validation_failed", Operation: "sample.get-item", Violations: [new PayloadViolation("/", "Invalid.")]), "unknown_operation"),
                (new("gateway_error", Status: 409, Detail: "Conflict."), "invalid_arguments"),
                (new("unknown_operation", Operation: "sample.unknown", Suggestions: ["sample.get-item"]), "unknown_module"),
                (new("unknown_module", Module: "unknown", Suggestions: ["sample"]), "unknown_operation"),
                (new("invalid_arguments", Argument: "kind", Message: "Invalid kind."), "internal_error"),
                (new("internal_error", Message: "Failed."), "gateway_error"),
            })
            {
                JsonNode actual = JsonSerializer.SerializeToNode(new { error }, McpCliJson.Result)!;
                AssertValid(schema, JsonSerializer.SerializeToElement(actual), tool.Name);
                AssertClosedObjects(schema, actual, tool.Name);
                actual["error"]!["code"] = mismatchedCode;
                schema.Evaluate(JsonSerializer.SerializeToElement(actual)).IsValid.ShouldBeFalse($"{tool.Name}: {error.Code} shape cannot use {mismatchedCode}");
                actual["error"]!["code"] = "unknown_error_code";
                schema.Evaluate(JsonSerializer.SerializeToElement(actual)).IsValid.ShouldBeFalse($"{tool.Name}: unknown error codes must fail");
            }
        }
    }

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
            foreach (string member in RequiredAt(document, path, tool))
            {
                JsonNode missing = document.DeepClone();
                JsonNode target = missing;
                foreach (string segment in path)
                {
                    target = target is JsonArray array ? array[int.Parse(segment, System.Globalization.CultureInfo.InvariantCulture)]! : target[segment]!;
                }

                target.AsObject().Remove(member).ShouldBeTrue();
                schema.Evaluate(JsonSerializer.SerializeToElement(missing)).IsValid.ShouldBeFalse(
                    $"{tool}: missing /{string.Join('/', path)}/{member} must fail");
            }

            foreach ((string name, JsonNode? value) in Locate(document, path).AsObject())
            {
                if (name is "schema" or "example" or "document" or "result")
                {
                    continue;
                }

                JsonNode nullMember = document.DeepClone();
                Locate(nullMember, path)[name] = null;
                schema.Evaluate(JsonSerializer.SerializeToElement(nullMember)).IsValid.ShouldBeFalse(
                    $"{tool}: null /{string.Join('/', path)}/{name} must fail");
                if (value?.GetValueKind() == JsonValueKind.Number)
                {
                    JsonNode stringNumber = document.DeepClone();
                    Locate(stringNumber, path)[name] = value.ToJsonString();
                    schema.Evaluate(JsonSerializer.SerializeToElement(stringNumber)).IsValid.ShouldBeFalse(
                        $"{tool}: string number /{string.Join('/', path)}/{name} must fail");
                }

                if (value is JsonArray values)
                {
                    for (int index = 0; index < values.Count; index++)
                    {
                        JsonNode nullItem = document.DeepClone();
                        Locate(nullItem, path)[name]![index] = null;
                        schema.Evaluate(JsonSerializer.SerializeToElement(nullItem)).IsValid.ShouldBeFalse(
                            $"{tool}: null array item /{string.Join('/', path)}/{name}/{index} must fail");
                    }
                }
            }
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

    private static JsonNode Locate(JsonNode document, string[] path)
    {
        foreach (string segment in path)
        {
            document = document is JsonArray array ? array[int.Parse(segment, System.Globalization.CultureInfo.InvariantCulture)]! : document[segment]!;
        }

        return document;
    }

    private static string[] RequiredAt(JsonNode document, string[] path, string tool)
    {
        if (path.Length == 0)
        {
            return document["error"] is null ? RequiredMembers(tool) : ["error"];
        }

        return path[0] switch
        {
            "modules" => ["name", "description", "operationCount"],
            "operations" => ["name", "kind", "description"],
            "envelope" => ["aggregateIdRequired", "idempotencyKeyRequired", "arguments"],
            "lintFindings" => ["code", "severity", "message"],
            "paging" => ["pageSize"],
            "error" when path.Length > 1 => ["path", "message"],
            "error" => document["error"]!["code"]!.GetValue<string>() switch
            {
                "validation_failed" => ["code", "operation", "violations"],
                "gateway_error" => ["code", "status", "detail"],
                "unknown_operation" => ["code", "operation", "suggestions"],
                "unknown_module" => ["code", "module", "suggestions"],
                "invalid_arguments" => ["code", "argument", "message"],
                _ => ["code", "message"],
            },
            _ => [],
        };
    }
}
