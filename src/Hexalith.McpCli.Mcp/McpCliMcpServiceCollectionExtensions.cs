using System.Reflection;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Schema;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Core.Execution;
using Hexalith.McpCli.Core.Serialization;
using Hexalith.McpCli.Core.Settings;
using Microsoft.Extensions.DependencyInjection;
using ModelContextProtocol.Server;
using ModelContextProtocol.Protocol;
using ModelContextProtocol;

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
            "list_modules", "When: discover supported modules. Effect: read catalog. Returns: module names and descriptions.",
            typeof(ModulesDocument), readOnly: true));
        collection.Add(Create((Func<string, IServiceProvider, string?, ModelContextProtocol.Protocol.CallToolResult>)McpToolHandlers.ListOperations,
            "list_operations", "When: inspect a module. Effect: read catalog. Returns: declared read and write operations.",
            typeof(OperationsDocument), readOnly: true));
        collection.Add(Create((Func<string, IServiceProvider, ModelContextProtocol.Protocol.CallToolResult>)McpToolHandlers.DescribeOperation,
            "describe_operation", "When: prepare an operation. Effect: read catalog. Returns: payload schema, routing and availability.",
            typeof(OperationDescriptionDocument), readOnly: true));
        if (!settings.ReadOnly)
        {
            collection.Add(Create((Func<string, string, IServiceProvider, CancellationToken, string?, string?, string?, string?,
                IReadOnlyDictionary<string, string>?, Task<ModelContextProtocol.Protocol.CallToolResult>>)McpToolHandlers.SendCommand,
                "send_command", "When: submit a declared command. Effect: write through EventStore. Returns: accepted command or error.",
                typeof(CommandResult), readOnly: false));
        }

        collection.Add(Create((Func<string, string, IServiceProvider, CancellationToken, string?, string?, string?, int?, int?,
            string?, Task<ModelContextProtocol.Protocol.CallToolResult>>)McpToolHandlers.RunQuery,
            "run_query", "When: execute a declared query. Effect: read through EventStore. Returns: document and paging.",
            typeof(QueryResult), readOnly: true));

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
        JsonNode success = JsonSchemaExporter.GetJsonSchemaAsNode(McpCliJson.Result, successType);
        JsonNode error = JsonSchemaExporter.GetJsonSchemaAsNode(McpCliJson.Result, typeof(OperationError));
        var schema = new JsonObject
        {
            ["type"] = "object",
            ["oneOf"] = new JsonArray(
                Close(success),
                new JsonObject
                {
                    ["type"] = "object",
                    ["properties"] = new JsonObject { ["error"] = Close(error) },
                    ["required"] = new JsonArray("error"),
                    ["additionalProperties"] = false,
                }),
        };
        return McpServerTool.Create(method, new McpServerToolCreateOptions
        {
            Name = name,
            Description = description,
            ReadOnly = readOnly,
            Destructive = !readOnly,
            Idempotent = readOnly,
            UseStructuredContent = true,
            OutputSchema = JsonSerializer.SerializeToElement(schema, McpCliJson.Result),
            SerializerOptions = McpCliJson.Result,
        });
    }

    private static JsonNode Close(JsonNode schema)
    {
        if (schema is JsonObject objectSchema)
        {
            objectSchema["additionalProperties"] = false;
        }

        return schema;
    }
}
