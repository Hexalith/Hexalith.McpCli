using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;
using Hexalith.McpCli.Sample.Contracts;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Supplies converter-first options with conflicting settings.</summary>
public static class FixtureSerializerOptions
{
    private static int _readCount;

    /// <summary>Gets how often the module provider was read.</summary>
    public static int ReadCount => Volatile.Read(ref _readCount);

    /// <summary>Gets the provider resolver that Core must not copy.</summary>
    public static IJsonTypeInfoResolver Resolver { get; } = new DefaultJsonTypeInfoResolver();

    /// <summary>Gets options whose converters are preserved before canonical converters.</summary>
    public static JsonSerializerOptions Options
    {
        get
        {
            Interlocked.Increment(ref _readCount);
            var options = new JsonSerializerOptions(JsonSerializerDefaults.Web)
            {
                PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
                PropertyNameCaseInsensitive = true,
                DefaultIgnoreCondition = JsonIgnoreCondition.Never,
                UnmappedMemberHandling = JsonUnmappedMemberHandling.Skip,
                TypeInfoResolver = Resolver,
            };
            options.Converters.Add(new SampleItemIdConverter());
            options.Converters.Add(new NumericIdentifierConverter());
            options.Converters.Add(new JsonNumberEnumConverter<StatusValue>());
            return options;
        }
    }
}
