using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Schema;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Core.Execution;
using Hexalith.McpCli.Core.Serialization;

namespace Hexalith.McpCli.Mcp;

/// <summary>Exports closed canonical documents while preserving arbitrary embedded JSON values.</summary>
internal static class McpOutputSchema
{
    private static readonly JsonSerializerOptions ExportOptions = new(McpCliJson.Result)
    {
        NumberHandling = JsonNumberHandling.Strict,
    };

    /// <summary>Builds the success/error union advertised by a generic tool.</summary>
    internal static JsonElement Create(Type successType)
    {
        JsonNode success = Export(successType);
        JsonObject errorProperties = Export(typeof(OperationError))["properties"]!.AsObject();
        var errors = new JsonArray();
        AddError(["validation_failed"], ["code", "operation", "violations"]);
        AddError(["gateway_error"], ["code", "status", "detail"],
            ["reason", "retryable", "clientAction", "retryAfter", "correlationId"]);
        AddError(["unknown_operation"], ["code", "operation", "suggestions"]);
        AddError(["unknown_module"], ["code", "module", "suggestions"]);
        AddError(["invalid_arguments"], ["code", "argument", "message"]);
        AddError(["read_only", "catalog_empty", "catalog_invalid", "unsupported_transport", "configuration_invalid", "internal_error"],
            ["code", "message"]);
        var schema = new JsonObject
        {
            ["type"] = "object",
            ["oneOf"] = new JsonArray(success, new JsonObject
            {
                ["type"] = "object",
                ["properties"] = new JsonObject
                {
                    ["error"] = new JsonObject { ["type"] = "object", ["oneOf"] = errors },
                },
                ["required"] = new JsonArray("error"),
                ["additionalProperties"] = false,
            }),
        };
        return JsonSerializer.SerializeToElement(schema, McpCliJson.Result);

        void AddError(string[] codes, string[] required, string[]? optional = null)
        {
            var properties = new JsonObject();
            foreach (string name in required.Concat(optional ?? []))
            {
                properties[name] = errorProperties[name]!.DeepClone();
            }

            properties["code"] = new JsonObject { ["type"] = "string", ["enum"] = Strings(codes) };
            errors.Add(new JsonObject
            {
                ["type"] = "object", ["properties"] = properties,
                ["required"] = Strings(required), ["additionalProperties"] = false,
            });
        }
    }

    private static JsonNode Export(Type type)
        => JsonSchemaExporter.GetJsonSchemaAsNode(ExportOptions, type, new JsonSchemaExporterOptions
        {
            TreatNullObliviousAsNonNullable = true,
            TransformSchemaNode = (context, node) =>
            {
                if (context.PropertyInfo is JsonPropertyInfo property && IsOmittedWhenNull(property)
                    && node is JsonObject scalar && scalar["type"] is JsonArray types)
                {
                    for (int index = types.Count - 1; index >= 0; index--)
                    {
                        if (types[index]!.GetValue<string>() == "null")
                        {
                            types.RemoveAt(index);
                        }
                    }

                    if (types.Count == 1)
                    {
                        scalar["type"] = types[0]!.DeepClone();
                    }
                }

                if (context.TypeInfo.Kind == JsonTypeInfoKind.Object && node is JsonObject schema
                    && schema["properties"] is JsonObject properties)
                {
                    schema["type"] = "object";
                    schema["additionalProperties"] = false;
                    schema["required"] = Strings(context.TypeInfo.Properties.Where(property =>
                        properties.ContainsKey(property.Name) && !IsOmittedWhenNull(property)).Select(property => property.Name));

                    if (context.TypeInfo.Type == typeof(CommandResult))
                    {
                        properties["status"]!["const"] = "accepted";
                    }

                    if (context.TypeInfo.Type == typeof(OperationSummary) || context.TypeInfo.Type == typeof(OperationDescriptionDocument))
                    {
                        properties["kind"]!["enum"] = new JsonArray("read", "write");
                    }

                    if (context.TypeInfo.Type == typeof(OperationDescriptionDocument))
                    {
                        properties["schema"] = new JsonObject { ["type"] = new JsonArray("object", "boolean") };
                    }
                }

                return node;
            },
        });

    private static bool IsOmittedWhenNull(JsonPropertyInfo property)
        => property.AttributeProvider?.GetCustomAttributes(typeof(JsonIgnoreAttribute), inherit: true)
            .OfType<JsonIgnoreAttribute>().Any(attribute => attribute.Condition == JsonIgnoreCondition.WhenWritingNull) == true;

    private static JsonArray Strings(IEnumerable<string> values)
        => new(values.Select(value => (JsonNode?)JsonValue.Create(value)).ToArray());
}
