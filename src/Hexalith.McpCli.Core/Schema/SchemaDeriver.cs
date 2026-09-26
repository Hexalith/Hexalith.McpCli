using System.ComponentModel;
using System.Reflection;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Schema;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;
using ByteAether.Ulid;
using Hexalith.McpCli.Abstractions;
using Hexalith.McpCli.Core.Catalog;

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
    /// <exception cref="ContractDeclarationException">The payload contract or a property role cannot be exposed as declared.</exception>
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

        JsonTypeInfo typeInfo;
        try
        {
            typeInfo = options.GetTypeInfo(payloadType);
        }
        catch (Exception exception) when (exception is InvalidOperationException or NotSupportedException)
        {
            throw InvalidContract(payloadType, exception);
        }

        if (isCommand && typeInfo.Kind != JsonTypeInfoKind.Object)
        {
            throw new ContractDeclarationException("invalid_schema",
                $"Command payload type {payloadType} must have an object serialization contract, not {typeInfo.Kind}.");
        }

        IReadOnlyDictionary<PropertyRole, PropertyBinding> bindings = ResolveBindings(payloadType, typeInfo, roleNames);
        var exporterOptions = new JsonSchemaExporterOptions
        {
            TransformSchemaNode = (context, schema) => Transform(context, schema, options, identifierKind, bindings),
        };
        JsonNode schemaNode;
        try
        {
            schemaNode = JsonSchemaExporter.GetJsonSchemaAsNode(options, payloadType, exporterOptions);
        }
        catch (Exception exception) when (exception is InvalidOperationException or NotSupportedException)
        {
            throw InvalidContract(payloadType, exception);
        }

        if (isCommand)
        {
            if (schemaNode is not JsonObject root)
            {
                throw new ContractDeclarationException("invalid_schema",
                    $"Command payload type {payloadType} must serialize as a JSON object, not as {schemaNode.ToJsonString()}.");
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
        if (roleNames is null || roleNames.Values.All(name => name is null))
        {
            return bindings;
        }

        if (typeInfo.Kind != JsonTypeInfoKind.Object)
        {
            throw InvalidReference($"Payload type {payloadType} declares property roles but has a {typeInfo.Kind} serialization contract, not an object.");
        }

        foreach ((PropertyRole role, string? clrName) in roleNames)
        {
            if (clrName is null)
            {
                continue;
            }

            if (string.IsNullOrWhiteSpace(clrName))
            {
                throw InvalidReference($"Property role {role} names a blank CLR property '{clrName}'.");
            }

            PropertyInfo[] clrMatches = payloadType.GetProperties(BindingFlags.Public | BindingFlags.Instance)
                .Where(property => string.Equals(property.Name, clrName, StringComparison.Ordinal))
                .ToArray();
            if (clrMatches.Length == 0)
            {
                throw InvalidReference($"Property role {role} names {clrName}, which is not a public instance property of {payloadType}.");
            }

            if (clrMatches.Length > 1)
            {
                throw InvalidReference($"Property role {role} names {clrName}, which matches {clrMatches.Length} CLR properties "
                    + $"of {payloadType} because one hides another.");
            }

            PropertyInfo clrProperty = clrMatches[0];
            JsonPropertyInfo[] metadataMatches = typeInfo.Properties
                .Where(property => property.AttributeProvider is PropertyInfo candidate
                    && candidate.Name == clrProperty.Name
                    && candidate.DeclaringType == clrProperty.DeclaringType)
                .ToArray();
            if (metadataMatches.Length != 1)
            {
                throw InvalidReference(metadataMatches.Length == 0
                    ? $"Property role {role} names {clrName}, which is not a serialized input member under the Module payload options."
                    : $"Property role {role} names {clrName}, which maps to {metadataMatches.Length} serialized members.");
            }

            JsonPropertyInfo metadata = metadataMatches[0];
            if (metadata.Get is null && metadata.Set is null && metadata.AssociatedParameter is null)
            {
                throw InvalidReference($"Property role {role} names {clrName}, which is ignored and never serialized under the Module payload options.");
            }

            // Ownership is resolved on the serialized member, after [JsonPropertyName] and naming policy mapping.
            PropertyBinding? owner = bindings.Values.FirstOrDefault(existing
                => string.Equals(existing.SerializedName, metadata.Name, StringComparison.Ordinal));
            if (owner is not null)
            {
                throw (owner.Role, role) is (PropertyRole.Tenant, PropertyRole.AggregateId) or (PropertyRole.AggregateId, PropertyRole.Tenant)
                    ? new ContractDeclarationException("tenant_is_aggregate_id",
                        $"Tenant and AggregateId roles both own serialized member {metadata.Name} (CLR property {clrName}).")
                    : new ContractDeclarationException("conflicting_property_roles",
                        $"Property roles {owner.Role} and {role} both own serialized member {metadata.Name} (CLR property {clrName}).");
            }

            if ((role == PropertyRole.AggregateId && metadata.Get is null)
                || (metadata.Set is null && metadata.AssociatedParameter is null)
                || metadata.IsExtensionData)
            {
                throw InvalidReference($"Property role {role} must name a deserializable payload property: {clrName}.");
            }

            if (!IsSupportedRoleType(role, metadata.PropertyType))
            {
                throw InvalidReference($"Property role {role} cannot bind member {clrName} of type {metadata.PropertyType}.");
            }

            if (role != PropertyRole.AggregateId && HasExternalPropertyConverter(clrProperty))
            {
                throw InvalidReference($"Property role {role} names {clrName}, whose custom JsonConverter makes the serialized member converter-opaque.");
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

    private static bool IsSupportedRoleType(PropertyRole role, Type propertyType) => role switch
    {
        PropertyRole.Tenant or PropertyRole.Actor => propertyType == typeof(string),
        PropertyRole.Correlation or PropertyRole.IdempotencyKey => propertyType == typeof(string)
            || (Nullable.GetUnderlyingType(propertyType) ?? propertyType) == typeof(Ulid),
        _ => true,
    };

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
            string member = context.TypeInfo.Properties.First(property => property.IsExtensionData).Name;
            throw new ContractDeclarationException("invalid_schema",
                $"JSON extension data member {member} of payload type {context.TypeInfo.Type} cannot be represented by a closed schema.");
        }

        if (context.TypeInfo.PolymorphismOptions is not null)
        {
            throw new ContractDeclarationException("invalid_schema",
                $"Polymorphic payload type {context.TypeInfo.Type} at {Location(context)} cannot be represented by a closed schema.");
        }

        JsonPropertyInfo? metadata = context.PropertyInfo;
        Type nodeType = Nullable.GetUnderlyingType(context.TypeInfo.Type) ?? context.TypeInfo.Type;
        if (IsFreeForm(nodeType))
        {
            throw new ContractDeclarationException("invalid_schema", metadata is not null
                ? $"Free-form member {metadata.Name} of type {nodeType} cannot be represented by a closed schema."
                : $"Free-form value of type {nodeType} at {Location(context)} cannot be represented by a closed schema.");
        }

        PropertyInfo? clrProperty = metadata?.AttributeProvider as PropertyInfo;
        bool rootProperty = IsRootProperty(context);
        bool declaredIdentifier = clrProperty is not null
            && (Attribute.IsDefined(clrProperty, typeof(HexalithIdentifierAttribute), true)
                || rootProperty
                    && bindings.TryGetValue(PropertyRole.AggregateId, out PropertyBinding? aggregate)
                    && ReferenceEquals(aggregate.Metadata, metadata));
        bool clrUlid = metadata is not null
            && (Nullable.GetUnderlyingType(metadata.PropertyType) == typeof(Ulid)
                || metadata.PropertyType == typeof(Ulid));
        bool opaqueConverter = schema is JsonValue boolean
            && boolean.TryGetValue<bool>(out bool unconstrained)
            && unconstrained
            || HasExternalPropertyConverter(clrProperty);
        if (opaqueConverter && metadata is null)
        {
            throw new ContractDeclarationException("invalid_schema",
                $"Opaque payload root {context.TypeInfo.Type} at {Location(context)} cannot be represented by a closed schema.");
        }

        if (opaqueConverter && metadata is not null && !(declaredIdentifier || clrUlid))
        {
            throw new ContractDeclarationException("invalid_schema",
                $"Opaque serialized member {metadata.Name} of type {metadata.PropertyType} has a custom converter and cannot be represented by a closed schema.");
        }

        if (schema is JsonObject container)
        {
            ConstrainOpaqueElements(context.TypeInfo, container, metadata?.Name ?? Location(context));
            if ((Nullable.GetUnderlyingType(context.TypeInfo.Type) ?? context.TypeInfo.Type) == typeof(TimeOnly))
            {
                // The exporter's "time" format requires an offset that TimeOnly deserialization rejects.
                container.Remove("format");
            }
        }

        if (schema is not JsonObject && !(opaqueConverter && (declaredIdentifier || clrUlid)))
        {
            return schema;
        }

        JsonObject node = opaqueConverter ? new JsonObject() : (JsonObject)schema;
        if (clrProperty is not null)
        {
            string? description = clrProperty.GetCustomAttribute<DescriptionAttribute>()?.Description
                ?? metadata!.AssociatedParameter?.AttributeProvider?.GetCustomAttributes(typeof(DescriptionAttribute), true)
                    .OfType<DescriptionAttribute>().FirstOrDefault()?.Description;
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
                    throw new ContractDeclarationException("invalid_identifier_type",
                        $"Declared identifier {metadata!.Name} of type {metadata.PropertyType} does not serialize as a JSON string.");
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

            if (rootProperty && bindings.Values.Any(binding => binding.Role != PropertyRole.AggregateId
                && ReferenceEquals(binding.Metadata, metadata)))
            {
                node["readOnly"] = true;
            }
        }

        if (ContainsType(node, "object") && context.TypeInfo.Kind == JsonTypeInfoKind.Object)
        {
            node["additionalProperties"] = false;
            if (context.Path.IsEmpty && node["required"] is JsonArray required)
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

    private static bool HasExternalPropertyConverter(PropertyInfo? clrProperty)
    {
        // A property-level converter is opaque even when STJ wraps it for Nullable<T> and exports the underlying shape.
        if (clrProperty is null
            || Attribute.GetCustomAttribute(clrProperty, typeof(JsonConverterAttribute), true) is not JsonConverterAttribute attribute)
        {
            return false;
        }

        return (attribute.ConverterType ?? attribute.GetType()).Assembly != typeof(JsonSerializer).Assembly;
    }

    private static bool IsRootProperty(JsonSchemaExporterContext context)
        => context.PropertyInfo is not null
            && context.Path.Length == 2
            && string.Equals(context.Path[0], "properties", StringComparison.Ordinal);

    private static void ConstrainOpaqueElements(JsonTypeInfo typeInfo, JsonObject node, string location)
    {
        string? elementKeyword = typeInfo.Kind switch
        {
            JsonTypeInfoKind.Enumerable => "items",
            JsonTypeInfoKind.Dictionary => "additionalProperties",
            _ => null,
        };

        // The exporter omits the element keyword only when the element schema is unconstrained (true).
        if (elementKeyword is null || typeInfo.ElementType is null || node.ContainsKey(elementKeyword))
        {
            return;
        }

        Type elementType = typeInfo.ElementType;
        Type effectiveElement = Nullable.GetUnderlyingType(elementType) ?? elementType;
        if (IsFreeForm(effectiveElement))
        {
            throw new ContractDeclarationException("invalid_schema",
                $"Free-form element type {elementType} of member {location} cannot be represented by a closed schema.");
        }

        if (effectiveElement != typeof(Ulid))
        {
            throw new ContractDeclarationException("invalid_schema",
                $"Opaque element type {elementType} of member {location} ({typeInfo.Type}) cannot be represented by a closed schema.");
        }

        node[elementKeyword] = new JsonObject
        {
            ["type"] = Nullable.GetUnderlyingType(elementType) is null ? JsonValue.Create("string") : new JsonArray("string", "null"),
            ["pattern"] = UlidPattern,
            ["minLength"] = 26,
            ["maxLength"] = 26,
        };
    }

    private static bool OpaqueIdentifierWritesString(JsonPropertyInfo metadata, JsonSerializerOptions options, IdentifierKind identifierKind)
    {
        Type propertyType = metadata.PropertyType;
        Type effectiveType = Nullable.GetUnderlyingType(propertyType) ?? propertyType;
        bool hasConverter = metadata.CustomConverter is not null
            || options.Converters.Any(converter => converter.CanConvert(propertyType) || converter.CanConvert(effectiveType))
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
                Type probeType = customConverter.CanConvert(metadata.PropertyType)
                    ? metadata.PropertyType
                    : Nullable.GetUnderlyingType(metadata.PropertyType) ?? metadata.PropertyType;
                MethodInfo method = typeof(SchemaDeriver).GetMethod(nameof(ProbeCustomConverter), BindingFlags.NonPublic | BindingFlags.Static)!
                    .MakeGenericMethod(probeType);
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

    private static bool IsFreeForm(Type type) => type == typeof(object)
        || type == typeof(JsonElement)
        || type == typeof(JsonDocument)
        || typeof(JsonNode).IsAssignableFrom(type);

    private static string Location(JsonSchemaExporterContext context)
        => context.Path.IsEmpty ? "#" : "#/" + string.Join('/', context.Path.ToArray());

    private static ContractDeclarationException InvalidReference(string message) => new("invalid_property_reference", message);

    private static ContractDeclarationException InvalidContract(Type payloadType, Exception exception)
        => new("invalid_schema", $"Payload type {payloadType} has an invalid serialization contract: {exception.Message}", exception);

    private static string Escape(string segment) => segment.Replace("~", "~0", StringComparison.Ordinal).Replace("/", "~1", StringComparison.Ordinal);
}
