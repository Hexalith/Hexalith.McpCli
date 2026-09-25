using System.Collections.Concurrent;
using System.Reflection;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;
using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Core.Serialization;

/// <summary>Owns the JSON contracts used by payloads and result documents.</summary>
public static class McpCliJson
{
    private static readonly ConcurrentDictionary<Assembly, Lazy<JsonSerializerOptions>> ModuleOptions = new();

    /// <summary>Gets canonical payload options for modules without a provider.</summary>
    public static JsonSerializerOptions Payload { get; } = CreatePayload(null);

    /// <summary>Gets the separate result document options.</summary>
    public static JsonSerializerOptions Result { get; } = CreateResult();

    /// <summary>Gets one cached payload options instance for a Contracts module.</summary>
    /// <param name="contractsAssembly">The marked Contracts assembly.</param>
    /// <param name="module">The Module declaration from that assembly.</param>
    /// <returns>Read-only canonical payload options.</returns>
    public static JsonSerializerOptions ForModule(Assembly contractsAssembly, HexalithModuleAttribute module)
    {
        ArgumentNullException.ThrowIfNull(contractsAssembly);
        ArgumentNullException.ThrowIfNull(module);
        return ModuleOptions.GetOrAdd(
            contractsAssembly,
            _ => new Lazy<JsonSerializerOptions>(
                () => CreatePayload(ReadProvider(contractsAssembly, module)),
                LazyThreadSafetyMode.ExecutionAndPublication)).Value;
    }

    private static JsonSerializerOptions? ReadProvider(Assembly assembly, HexalithModuleAttribute module)
    {
        Type? provider = module.SerializerOptionsProvider;
        if (provider is null)
        {
            return null;
        }

        if (provider.Assembly != assembly)
        {
            throw new ArgumentException("The serializer options provider must be in the Contracts assembly.", nameof(module));
        }

        PropertyInfo? property = provider.GetProperty("Options", BindingFlags.Public | BindingFlags.Static | BindingFlags.DeclaredOnly);
        if (property is null || property.PropertyType != typeof(JsonSerializerOptions) || property.GetMethod is null || property.GetIndexParameters().Length != 0)
        {
            throw new ArgumentException("The serializer options provider must expose public static JsonSerializerOptions Options { get; }.", nameof(module));
        }

        return (JsonSerializerOptions?)property.GetValue(null)
            ?? throw new ArgumentException("The serializer options provider returned null.", nameof(module));
    }

    private static JsonSerializerOptions CreatePayload(JsonSerializerOptions? provider)
    {
        var options = new JsonSerializerOptions
        {
            PropertyNamingPolicy = null,
            PropertyNameCaseInsensitive = false,
            DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
            UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow,
            TypeInfoResolver = CreateResolver(),
        };

        if (provider is not null)
        {
            foreach (JsonConverter converter in provider.Converters)
            {
                options.Converters.Add(converter);
            }
        }

        options.Converters.Add(new JsonStringEnumConverter(namingPolicy: null, allowIntegerValues: false));
        options.MakeReadOnly();
        return options;
    }

    private static JsonSerializerOptions CreateResult()
    {
        var options = new JsonSerializerOptions(JsonSerializerDefaults.Web)
        {
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
            WriteIndented = true,
            TypeInfoResolver = new DefaultJsonTypeInfoResolver(),
        };
        options.Converters.Add(new JsonStringEnumConverter(JsonNamingPolicy.CamelCase));
        options.MakeReadOnly();
        return options;
    }

    private static DefaultJsonTypeInfoResolver CreateResolver()
    {
        var resolver = new DefaultJsonTypeInfoResolver();
        resolver.Modifiers.Add(typeInfo =>
        {
            if (typeInfo.Kind != JsonTypeInfoKind.Object)
            {
                return;
            }

            for (int index = typeInfo.Properties.Count - 1; index >= 0; index--)
            {
                JsonPropertyInfo property = typeInfo.Properties[index];

                // A getter-only member is still input when deserialization populates it in place.
                bool populated = (property.ObjectCreationHandling ?? typeInfo.PreferredPropertyObjectCreationHandling) == JsonObjectCreationHandling.Populate;
                if (property.Get is not null && property.Set is null && property.AssociatedParameter is null && !property.IsExtensionData && !populated)
                {
                    typeInfo.Properties.RemoveAt(index);
                }
            }
        });
        return resolver;
    }
}
