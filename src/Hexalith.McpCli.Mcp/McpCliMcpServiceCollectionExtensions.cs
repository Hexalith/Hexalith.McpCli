using System.Reflection;
using System.Text.Json;
using System.Text.Json.Nodes;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Core.Execution;
using Hexalith.McpCli.Core.Serialization;
using Hexalith.McpCli.Core.Settings;
using Microsoft.Extensions.DependencyInjection;
using ModelContextProtocol.Server;
using ModelContextProtocol.Protocol;
using ModelContextProtocol;
using Json.Schema;

namespace Hexalith.McpCli.Mcp;

/// <summary>Registers a fixed set of generic MCP tools for one resolved session.</summary>
public static class McpCliMcpServiceCollectionExtensions
{
    /// <summary>Adds the stdio server and the permitted tool collection.</summary>
    public static IServiceCollection AddMcpCliMcpServer(this IServiceCollection services, ResolvedSettings settings)
    {
        ArgumentNullException.ThrowIfNull(services);
        ArgumentNullException.ThrowIfNull(settings);

        var collection = new McpServerPrimitiveCollection<McpServerTool>();
        collection.Add(Create((Func<IServiceProvider, ModelContextProtocol.Protocol.CallToolResult>)McpToolHandlers.ListModules,
            "list_modules", "Purpose: List modules, descriptions, and operation counts. Use when: Starting catalog discovery. Next: Call list_operations with a module name.",
            typeof(ModulesDocument), readOnly: true));
        collection.Add(Create((Func<string, IServiceProvider, string?, ModelContextProtocol.Protocol.CallToolResult>)McpToolHandlers.ListOperations,
            "list_operations", "Purpose: List a module's operations, optionally filtered by read or write kind. Use when: Choosing an operation in a known module. Next: Call describe_operation with an operation name.",
            typeof(OperationsDocument), readOnly: true));
        collection.Add(Create((Func<string, IServiceProvider, ModelContextProtocol.Protocol.CallToolResult>)McpToolHandlers.DescribeOperation,
            "describe_operation", "Purpose: Show payload schema, optional example, envelope arguments, lint findings, and availability. Use when: Preparing a selected operation. Next: If submittable, call run_query for a read or send_command for a write.",
            typeof(OperationDescriptionDocument), readOnly: true));
        if (!settings.ReadOnly)
        {
            collection.Add(Create((Func<string, string, IServiceProvider, CancellationToken, string?, string?, string?, string?,
                IReadOnlyDictionary<string, string>?, Task<ModelContextProtocol.Protocol.CallToolResult>>)McpToolHandlers.SendCommand,
                "send_command", "Purpose: Submit a write through EventStore. Use when: describe_operation shows a submittable write and the payload and envelope are ready. Next: Inspect the accepted result or error before any further action; a gateway-timeout or gateway-unreachable error does not prove rejection, so do not resubmit automatically.",
                typeof(CommandResult), readOnly: false));
        }

        collection.Add(Create((Func<string, string, IServiceProvider, CancellationToken, string?, string?, string?, int?, int?,
            string?, Task<ModelContextProtocol.Protocol.CallToolResult>>)McpToolHandlers.RunQuery,
            "run_query", "Purpose: Read through EventStore and return a document with optional paging. Use when: describe_operation shows a submittable read and the payload and envelope are ready. Next: Inspect the document and use the returned cursor for another page when present.",
            typeof(QueryResult), readOnly: true));

        var inputSchemas = collection.ToDictionary(tool => tool.ProtocolTool.Name,
            tool => JsonSchema.FromText(tool.ProtocolTool.InputSchema.GetRawText()), StringComparer.Ordinal);

        string version = typeof(McpCliMcpServiceCollectionExtensions).Assembly
            .GetCustomAttribute<AssemblyInformationalVersionAttribute>()?.InformationalVersion ?? "0.0.0";
        _ = services.AddMcpServer(options =>
        {
            options.ServerInfo = new() { Name = "hexalith", Version = version };
            options.ToolCollection = collection;
            options.Filters.Message.IncomingFilters.Add(next => async (context, cancellationToken) =>
            {
                if (context.JsonRpcMessage is JsonRpcRequest { Method: "tools/call", Params: JsonObject parameters })
                {
                    if (parameters["name"] is not JsonValue toolValue
                        || !toolValue.TryGetValue<string>(out string? toolName))
                    {
                        throw new McpProtocolException("Tool name must be a string.", McpErrorCode.InvalidParams);
                    }

                    string? required = toolName switch
                    {
                        "list_operations" => "module",
                        "describe_operation" or "send_command" or "run_query" => "operation",
                        _ => null,
                    };
                    if (required is not null && (parameters["arguments"] is not JsonObject arguments
                        || arguments[required] is not JsonValue value
                        || !value.TryGetValue<string>(out string? text)
                        || string.IsNullOrWhiteSpace(text)))
                    {
                        throw new McpProtocolException($"{required} is required and must be non-empty.", McpErrorCode.InvalidParams);
                    }

                    if (inputSchemas.TryGetValue(toolName, out JsonSchema? schema)
                        && !schema.Evaluate(JsonSerializer.SerializeToElement(parameters["arguments"] ?? new JsonObject())).IsValid)
                    {
                        throw new McpProtocolException("Tool arguments do not match the input schema.", McpErrorCode.InvalidParams);
                    }

                    if (toolName == "run_query" && parameters["arguments"] is JsonObject queryArguments)
                    {
                        foreach (string name in new[] { "pageSize", "offset" })
                        {
                            if (queryArguments[name] is not JsonNode number)
                            {
                                continue;
                            }

                            JsonElement integer = JsonSerializer.SerializeToElement(number);
                            if (integer.ValueKind != JsonValueKind.Number || !integer.TryGetInt32(out _))
                            {
                                throw new McpProtocolException($"{name} must be representable as an Int32 integer.", McpErrorCode.InvalidParams);
                            }
                        }
                    }
                }

                await next(context, cancellationToken).ConfigureAwait(false);
            });
            options.Filters.Request.ListToolsFilters.Add(next => async (request, cancellationToken) =>
            {
                ModelContextProtocol.Protocol.ListToolsResult result = await next(request, cancellationToken).ConfigureAwait(false);
                string[] permitted = settings.ReadOnly
                    ? ["list_modules", "list_operations", "describe_operation", "run_query"]
                    : ["list_modules", "list_operations", "describe_operation", "send_command", "run_query"];
                var toolsByName = result.Tools.ToDictionary(tool => tool.Name, StringComparer.Ordinal);
                if (toolsByName.Count != permitted.Length || permitted.Any(name => !toolsByName.ContainsKey(name)))
                {
                    throw new InvalidOperationException("MCP tool advertisement differs from the permitted collection.");
                }

                result.Tools = permitted.Select(name => toolsByName[name]).ToArray();
                return result;
            });
        }).WithStdioServerTransport();
        return services;
    }

    private static McpServerTool Create(Delegate method, string name, string description, Type successType, bool readOnly)
    {
        return McpServerTool.Create(method, new McpServerToolCreateOptions
        {
            Name = name,
            Description = description,
            ReadOnly = readOnly,
            Destructive = !readOnly,
            Idempotent = readOnly,
            UseStructuredContent = true,
            OutputSchema = McpOutputSchema.Create(successType),
            SerializerOptions = McpCliJson.Result,
        });
    }

}
