using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Schema;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Core.Execution;
using Hexalith.McpCli.Core.Schema;

namespace Hexalith.McpCli.Core.Serialization;

/// <summary>Exports closed canonical documents while preserving arbitrary embedded JSON values.</summary>
public static class ResultDocumentSchema
{
    private static readonly JsonSerializerOptions ExportOptions = new(McpCliJson.Result)
    {
        NumberHandling = JsonNumberHandling.Strict,
    };

    /// <summary>Builds the success/error union advertised by a generic tool.</summary>
    /// <param name="successType">The Core success document type.</param>
    /// <returns>The closed success/error document schema.</returns>
    public static JsonElement Create(Type successType)
    {
        ArgumentNullException.ThrowIfNull(successType);
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

            if (codes[0] == "unknown_operation")
            {
                properties["operation"] = Text();
                Suggestions(properties, OperationPattern);
            }
            else if (codes[0] == "unknown_module")
            {
                properties["module"] = Text();
                Suggestions(properties, ModulePattern);
            }

            else if (codes[0] == "invalid_arguments")
            {
                // Includes semantic binding names, management/fallback names, and parser-normalized options.
                properties["argument"] = new JsonObject { ["type"] = "string", ["enum"] = Strings(
                    ["module", "kind", "operation", "payload", "tenant", "aggregateId", "correlationId", "idempotencyKey",
                        "extensions", "entityId", "pageSize", "offset", "cursor", "lint", "url", "token", "actor",
                        "allowTenantOverride", "profile", "format", "output", "readOnly", "strict", "name", "set",
                        "arguments", "clear", "transport", "extension"]) };
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

                    ConstrainRecord(context.TypeInfo.Type, schema, properties);
                }

                return node;
            },
        });

    // These grammars mirror CatalogBuilder and RoutingResolver; identity uses SchemaDeriver's shared pattern.
    // The end assertion is ECMAScript-compatible and rejects trailing newlines.
    private const string Part = "[a-z0-9]+(?:-[a-z0-9]+)*";
    private const string ModulePattern = "^" + Part + @"(?![\s\S])";
    private const string OperationPattern = "^" + Part + @"\." + Part + @"(?![\s\S])";
    private const string TenantPattern = @"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?(?![\s\S])";
    private const string PlatformPattern = "^platform:" + Part + @"(?![\s\S])";
    private const string PointerPattern = @"^(?:/(?:[^~/]|~[01])*)*(?![\s\S])";

    private static void ConstrainRecord(Type type, JsonObject schema, JsonObject properties)
    {
        if (type == typeof(ModuleSummary))
        {
            properties["name"] = Text(ModulePattern);
            properties["description"] = Text();
            properties["operationCount"]!["minimum"] = 0;
        }
        else if (type == typeof(OperationsDocument))
        {
            properties["module"] = Text(ModulePattern);
        }
        else if (type == typeof(OperationSummary) || type == typeof(OperationDescriptionDocument))
        {
            properties["name"] = Text(OperationPattern);
            properties["description"] = Text();
            properties["kind"]!["enum"] = Strings(["read", "write"]);
            if (type == typeof(OperationDescriptionDocument))
            {
                properties["schema"] = new JsonObject { ["type"] = "object" };
                properties["example"] = new JsonObject { ["type"] = "object" };
                properties["reason"] = new JsonObject { ["type"] = "string", ["enum"] = Strings(["read_only", "configuration_invalid"]) };
                schema["allOf"] = new JsonArray(
                    Conditional("submittable", true, new JsonObject { ["not"] = Required("reason") }, Required("reason")),
                    Conditional("kind", "read", DescriptionKind(read: true), DescriptionKind(read: false)));
            }
        }
        else if (type == typeof(OperationEnvelopeDocument))
        {
            properties["fixedTenant"] = Text(TenantPattern);
            properties["platformScope"] = Text(PlatformPattern);
            properties["arguments"]!["uniqueItems"] = true;
            properties["arguments"]!["items"] = new JsonObject { ["type"] = "string", ["enum"] = Strings(
                ["tenant", "aggregateId", "correlationId", "idempotencyKey", "extensions", "entityId", "pageSize", "offset", "cursor"]) };
            schema["not"] = Required("fixedTenant", "platformScope");
            schema["if"] = new JsonObject { ["anyOf"] = new JsonArray(Required("fixedTenant"), Required("platformScope")) };
            schema["then"] = Properties("arguments", new JsonObject { ["not"] = Contains("tenant") });
            schema["else"] = Properties("arguments", Contains("tenant"));
        }
        else if (type == typeof(LintFinding))
        {
            properties["severity"]!["const"] = "warning";
            properties["message"] = Text();
            properties["property"] = Text(PointerPattern);
            schema["oneOf"] = new JsonArray(
                new JsonObject
                {
                    ["properties"] = new JsonObject { ["code"] = new JsonObject { ["const"] = "hollow_description" } },
                    ["not"] = Required("property"),
                },
                new JsonObject
                {
                    ["properties"] = new JsonObject { ["code"] = new JsonObject { ["enum"] = Strings(
                        ["missing_property_description", "unmarked_identifier_like_property", "payload_paging_member"]) } },
                    ["required"] = Strings(["property"]),
                });
        }
        else if (type == typeof(CommandResult) || type == typeof(QueryResult))
        {
            properties["operation"] = Text(OperationPattern);
            properties["tenant"] = new JsonObject { ["anyOf"] = new JsonArray(Text(TenantPattern), Text(PlatformPattern)) };
            if (type == typeof(CommandResult))
            {
                foreach (string name in new[] { "messageId", "correlationId", "idempotencyKey" })
                {
                    properties[name] = Ulid();
                }

                properties["aggregateId"] = Text(@"^[A-Za-z0-9](?:[A-Za-z0-9._-]{0,254}[A-Za-z0-9])?(?![\s\S])");
                properties["status"]!["const"] = "accepted";
            }
        }
        else if (type == typeof(QueryPagingDocument))
        {
            properties["pageSize"]!["minimum"] = 1;
            properties["offset"]!["minimum"] = 0;
            properties["totalCount"]!["minimum"] = 0;
            properties["nextCursor"] = Text();
        }
        else if (type == typeof(PayloadViolation))
        {
            properties["path"] = new JsonObject { ["type"] = "string", ["pattern"] = PointerPattern };
            properties["message"] = Text();
        }
        else if (type == typeof(OperationError))
        {
            foreach (string name in new[] { "message", "detail", "reason", "clientAction", "retryAfter", "argument" })
            {
                properties[name] = Text();
            }

            properties["operation"] = Text(OperationPattern);
            properties["correlationId"] = Ulid();
            properties["violations"]!["minItems"] = 1;
        }
    }

    private static JsonObject DescriptionKind(bool read)
    {
        string[] arguments = read
            ? ["aggregateId", "entityId", "pageSize", "offset", "cursor"]
            : ["aggregateId", "correlationId", "idempotencyKey", "extensions"];
        var rules = new JsonArray(arguments.Select(name => (JsonNode?)Contains(name)).ToArray());
        var argumentSchema = new JsonObject
        {
            ["items"] = new JsonObject { ["enum"] = Strings(["tenant", .. arguments]) },
            ["allOf"] = rules,
        };
        JsonObject envelope = Properties("arguments", argumentSchema);
        if (read)
        {
            envelope["properties"]!["idempotencyKeyRequired"] = new JsonObject { ["const"] = false };
        }

        JsonObject result = Properties("envelope", envelope);
        if (read)
        {
            result["properties"]!["reason"] = new JsonObject { ["const"] = "configuration_invalid" };
        }

        return result;
    }

    private static JsonObject Conditional<T>(string name, T value, JsonObject then, JsonObject? otherwise = null)
    {
        JsonObject condition = Properties(name, new JsonObject { ["const"] = JsonValue.Create(value) });
        condition["required"] = Strings([name]);
        var result = new JsonObject { ["if"] = condition, ["then"] = then };
        if (otherwise is not null)
        {
            result["else"] = otherwise;
        }

        return result;
    }

    private static void Suggestions(JsonObject properties, string pattern)
    {
        properties["suggestions"]!["maxItems"] = 3;
        properties["suggestions"]!["items"] = Text(pattern);
    }

    private static JsonObject Properties(string name, JsonObject rule)
        => new() { ["properties"] = new JsonObject { [name] = rule } };

    private static JsonObject Required(params string[] names) => new() { ["required"] = Strings(names) };

    private static JsonObject Contains(string name) => new() { ["contains"] = new JsonObject { ["const"] = name } };

    private static JsonObject Text(string? pattern = null)
    {
        var result = new JsonObject { ["type"] = "string", ["minLength"] = 1 };
        if (pattern is not null)
        {
            result["pattern"] = pattern;
        }

        return result;
    }

    private static JsonObject Ulid() => new() { ["type"] = "string", ["minLength"] = 26, ["maxLength"] = 26, ["pattern"] = SchemaDeriver.UlidPattern };

    private static bool IsOmittedWhenNull(JsonPropertyInfo property)
        => property.AttributeProvider?.GetCustomAttributes(typeof(JsonIgnoreAttribute), inherit: true)
            .OfType<JsonIgnoreAttribute>().Any(attribute => attribute.Condition == JsonIgnoreCondition.WhenWritingNull) == true;

    private static JsonArray Strings(IEnumerable<string> values)
        => new(values.Select(value => (JsonNode?)JsonValue.Create(value)).ToArray());
}
