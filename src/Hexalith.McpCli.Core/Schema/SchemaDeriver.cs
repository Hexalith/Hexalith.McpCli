using System.ComponentModel;
using System.Reflection;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Schema;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;
using ByteAether.Ulid;
using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Core.Schema;

/// <summary>Exports an operation payload contract and resolves declared property roles.</summary>
public static class SchemaDeriver
{
    /// <summary>The JSON Schema pattern for a 26-character ULID string.</summary>
    public const string UlidPattern = "^[0-7][0-9A-HJKMNP-TV-Za-hjkmnp-tv-z]{25}$";

    /// <summary>Derives one reusable schema from canonical module payload options.</summary>
    /// <param name="payloadType">The decorated payload type.</param>
    /// <param name="options">The cached module payload options.</param>
    /// <param name="identifierKind">The module's declared identifier kind.</param>
    /// <param name="isCommand">Whether to enforce a non-null object root.</param>
    /// <param name="roleNames">Declared roles mapped to exact top-level CLR property names.</param>
    /// <returns>The schema and its effective property bindings.</returns>
    public static DerivedSchema Derive(
        Type payloadType,
        JsonSerializerOptions options,
        IdentifierKind identifierKind,
        bool isCommand,
        IReadOnlyDictionary<PropertyRole, string?>? roleNames = null)
    {
        ArgumentNullException.ThrowIfNull(payloadType);
        ArgumentNullException.ThrowIfNull(options);
        if (!options.IsReadOnly)
        {
            throw new ArgumentException("Module payload options must be read-only.", nameof(options));
        }

        if (identifierKind is not (IdentifierKind.Ulid or IdentifierKind.String))
        {
            throw new ArgumentOutOfRangeException(nameof(identifierKind), identifierKind, "The Module identifier kind is unknown.");
        }

        JsonTypeInfo typeInfo = options.GetTypeInfo(payloadType);
        if (isCommand && typeInfo.Kind != JsonTypeInfoKind.Object)
        {
            throw new ArgumentException("A Command payload must have an object serialization contract.", nameof(payloadType));
        }
        IReadOnlyDictionary<PropertyRole, PropertyBinding> bindings = ResolveBindings(payloadType, typeInfo, roleNames);
        var exporterOptions = new JsonSchemaExporterOptions
        {
            TransformSchemaNode = (context, schema) => Transform(context, schema, options, identifierKind, bindings),
        };
        JsonNode schemaNode = JsonSchemaExporter.GetJsonSchemaAsNode(options, payloadType, exporterOptions);
        if (isCommand)
        {
            if (schemaNode is not JsonObject root)
            {
                throw new ArgumentException("A Command payload must serialize as a JSON object.", nameof(payloadType));
            }

            root["type"] = "object";
        }

        return new DerivedSchema(schemaNode, bindings);
    }

    private static IReadOnlyDictionary<PropertyRole, PropertyBinding> ResolveBindings(
        Type payloadType,
        JsonTypeInfo typeInfo,
        IReadOnlyDictionary<PropertyRole, string?>? roleNames)
    {
        var bindings = new Dictionary<PropertyRole, PropertyBinding>();
        if (roleNames is null)
        {
            return bindings;
        }

        if (typeInfo.Kind != JsonTypeInfoKind.Object)
        {
            throw new ArgumentException("An operation with property roles must have an object serialization contract.", nameof(payloadType));
        }

        foreach ((PropertyRole role, string? clrName) in roleNames)
        {
            if (clrName is null)
            {
                continue;
            }

            if (string.IsNullOrWhiteSpace(clrName))
            {
                throw new ArgumentException($"Property role {role} has an empty CLR property name.", nameof(roleNames));
            }

            PropertyInfo[] clrMatches = payloadType.GetProperties(BindingFlags.Public | BindingFlags.Instance)
                .Where(property => string.Equals(property.Name, clrName, StringComparison.Ordinal))
                .ToArray();
            if (clrMatches.Length != 1)
            {
                throw new ArgumentException($"Property role {role} must name one exact top-level CLR property: {clrName}.", nameof(roleNames));
            }

            PropertyInfo clrProperty = clrMatches[0];
            JsonPropertyInfo[] metadataMatches = typeInfo.Properties
                .Where(property => property.AttributeProvider is PropertyInfo candidate
                    && candidate.Name == clrProperty.Name
                    && candidate.DeclaringType == clrProperty.DeclaringType)
                .ToArray();
            if (metadataMatches.Length != 1)
            {
                throw new ArgumentException($"Property role {role} names an ignored or ambiguous serialized property: {clrName}.", nameof(roleNames));
            }

            JsonPropertyInfo metadata = metadataMatches[0];
            if ((role == PropertyRole.AggregateId && metadata.Get is null)
                || (metadata.Set is null && metadata.AssociatedParameter is null)
                || metadata.IsExtensionData)
            {
                throw new ArgumentException($"Property role {role} must name a deserializable payload property: {clrName}.", nameof(roleNames));
            }

            if (bindings.Values.Any(existing => string.Equals(existing.SerializedName, metadata.Name, StringComparison.Ordinal)))
            {
                throw new ArgumentException($"Two property roles cannot own the same serialized member: {metadata.Name}.", nameof(roleNames));
            }

            bindings.Add(role, new PropertyBinding(
                role,
                clrProperty,
                metadata.Name,
                "/" + Escape(metadata.Name),
                metadata));
        }

        return bindings;
    }

    private static JsonNode Transform(
        JsonSchemaExporterContext context,
        JsonNode schema,
        JsonSerializerOptions options,
        IdentifierKind identifierKind,
        IReadOnlyDictionary<PropertyRole, PropertyBinding> bindings)
    {
        if (context.TypeInfo.Kind == JsonTypeInfoKind.Object
            && context.TypeInfo.Properties.Any(property => property.IsExtensionData))
        {
            throw new NotSupportedException($"JSON extension data is unsupported in payload type {context.TypeInfo.Type}.");
        }

        if (context.TypeInfo.PolymorphismOptions is not null)
        {
            throw new NotSupportedException($"Polymorphic payload type {context.TypeInfo.Type} cannot be represented by a closed schema.");
        }

        JsonPropertyInfo? metadata = context.PropertyInfo;
        PropertyInfo? clrProperty = metadata?.AttributeProvider as PropertyInfo;
        bool declaredIdentifier = clrProperty is not null
            && (clrProperty.IsDefined(typeof(HexalithIdentifierAttribute), true)
                || bindings.TryGetValue(PropertyRole.AggregateId, out PropertyBinding? aggregate)
                    && ReferenceEquals(aggregate.Metadata, metadata));
        bool clrUlid = metadata is not null
            && (Nullable.GetUnderlyingType(metadata.PropertyType) == typeof(Ulid)
                || metadata.PropertyType == typeof(Ulid));
        bool opaqueConverter = schema is JsonValue boolean
            && boolean.TryGetValue<bool>(out bool unconstrained)
            && unconstrained;
        if (opaqueConverter && metadata is null)
        {
            throw new NotSupportedException($"Opaque payload root {context.TypeInfo.Type} cannot be represented by a closed schema.");
        }

        if (opaqueConverter && metadata is not null && !(declaredIdentifier || clrUlid))
        {
            throw new NotSupportedException($"Opaque serialized member {metadata.Name} cannot be represented by a closed schema.");
        }

        if (schema is not JsonObject && !(opaqueConverter && (declaredIdentifier || clrUlid)))
        {
            return schema;
        }

        JsonObject node = schema as JsonObject ?? new JsonObject();
        if (clrProperty is not null)
        {
            string? description = clrProperty.GetCustomAttribute<DescriptionAttribute>()?.Description;
            if (description is not null)
            {
                node["description"] = description;
            }

            if (declaredIdentifier || clrUlid)
            {
                if (opaqueConverter
                    ? !OpaqueIdentifierWritesString(metadata!, options, identifierKind)
                    : !SerializesAsString(node))
                {
                    throw new ArgumentException($"Declared identifier {clrProperty.Name} does not serialize as a JSON string.");
                }

                bool nullable = metadata!.IsGetNullable || AllowsNull(node);
                node["type"] = nullable ? new JsonArray("string", "null") : JsonValue.Create("string");
                if (identifierKind == IdentifierKind.Ulid && declaredIdentifier || clrUlid)
                {
                    node["pattern"] = UlidPattern;
                    node["minLength"] = 26;
                    node["maxLength"] = 26;
                }
                else
                {
                    node.Remove("pattern");
                }
            }

            if (bindings.Values.Any(binding => binding.Role != PropertyRole.AggregateId
                && ReferenceEquals(binding.Metadata, metadata)))
            {
                node["readOnly"] = true;
            }
        }

        if (ContainsType(node, "object") && context.TypeInfo.Kind == JsonTypeInfoKind.Object)
        {
            node["additionalProperties"] = false;
            if (context.PropertyInfo is null && node["required"] is JsonArray required)
            {
                foreach (PropertyBinding binding in bindings.Values.Where(binding => binding.Role != PropertyRole.AggregateId))
                {
                    for (int index = required.Count - 1; index >= 0; index--)
                    {
                        if (string.Equals(required[index]?.GetValue<string>(), binding.SerializedName, StringComparison.Ordinal))
                        {
                            required.RemoveAt(index);
                        }
                    }
                }
            }
        }

        return node;
    }

    private static bool OpaqueIdentifierWritesString(JsonPropertyInfo metadata, JsonSerializerOptions options, IdentifierKind identifierKind)
    {
        Type propertyType = metadata.PropertyType;
        Type effectiveType = Nullable.GetUnderlyingType(propertyType) ?? propertyType;
        bool hasConverter = metadata.CustomConverter is not null
            || options.Converters.Any(converter => converter.CanConvert(propertyType))
            || effectiveType.IsDefined(typeof(JsonConverterAttribute), true);
        if (!hasConverter && effectiveType != typeof(Ulid))
        {
            return false;
        }

        string[] samples = identifierKind == IdentifierKind.Ulid
            ? ["01ARZ3NDEKTSV4RRFFQ69G5FAV"]
            : ["01ARZ3NDEKTSV4RRFFQ69G5FAV", "sample", "1"];
        bool sawString = false;
        foreach (string sample in samples)
        {
            bool? writesString = ProbeStringSample(metadata, options, sample);
            if (writesString == false)
            {
                return false;
            }

            sawString |= writesString == true;
        }

        return sawString;
    }

    private static bool? ProbeStringSample(JsonPropertyInfo metadata, JsonSerializerOptions options, string sample)
    {
        try
        {
            if (metadata.CustomConverter is JsonConverter customConverter)
            {
                MethodInfo method = typeof(SchemaDeriver).GetMethod(nameof(ProbeCustomConverter), BindingFlags.NonPublic | BindingFlags.Static)!
                    .MakeGenericMethod(metadata.PropertyType);
                return (bool?)method.Invoke(null, [customConverter, options, sample]);
            }

            object? value = JsonSerializer.Deserialize(JsonSerializer.Serialize(sample), metadata.PropertyType, options);
            if (value is null)
            {
                return null;
            }

            using JsonDocument output = JsonDocument.Parse(JsonSerializer.Serialize(value, metadata.PropertyType, options));
            return output.RootElement.ValueKind == JsonValueKind.String;
        }
        catch (Exception exception) when (exception is JsonException or FormatException or ArgumentException or InvalidOperationException or NotSupportedException or TargetInvocationException)
        {
            return null;
        }
    }

    private static bool? ProbeCustomConverter<T>(JsonConverter converter, JsonSerializerOptions options, string sample)
    {
        if (converter is JsonConverterFactory factory)
        {
            JsonConverter? created = factory.CreateConverter(typeof(T), options);
            if (created is null)
            {
                return null;
            }

            converter = created;
        }

        if (converter is not JsonConverter<T> typed)
        {
            return null;
        }

        var reader = new Utf8JsonReader(System.Text.Encoding.UTF8.GetBytes(JsonSerializer.Serialize(sample)));
        reader.Read();
        T? value = typed.Read(ref reader, typeof(T), options);
        if (value is null)
        {
            return null;
        }

        using var stream = new MemoryStream();
        using (var writer = new Utf8JsonWriter(stream))
        {
            typed.Write(writer, value, options);
        }

        using JsonDocument output = JsonDocument.Parse(stream.ToArray());
        return output.RootElement.ValueKind == JsonValueKind.String;
    }

    private static bool SerializesAsString(JsonObject node)
    {
        JsonNode? type = node["type"];
        if (type is JsonValue scalar)
        {
            return scalar.TryGetValue<string>(out string? name) && name == "string";
        }

        return type is JsonArray array && array.Count > 0 && array.All(item => item is JsonValue value
            && value.TryGetValue<string>(out string? name) && (name == "string" || name == "null"))
            && ContainsType(node, "string");
    }

    private static bool AllowsNull(JsonObject node) => ContainsType(node, "null");

    private static bool ContainsType(JsonObject node, string type)
    {
        JsonNode? value = node["type"];
        return value is JsonValue scalar && scalar.TryGetValue<string>(out string? name)
                && string.Equals(name, type, StringComparison.Ordinal)
            || value is JsonArray array && array.Any(item => item is JsonValue itemValue
                && itemValue.TryGetValue<string>(out string? itemName)
                && string.Equals(itemName, type, StringComparison.Ordinal));
    }

    private static string Escape(string segment) => segment.Replace("~", "~0", StringComparison.Ordinal).Replace("/", "~1", StringComparison.Ordinal);
}
