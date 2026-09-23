using System.Text.Json;

namespace Hexalith.McpCli.Sample.Contracts;

/// <summary>
/// Supplies the sample identifier converter to payload serialization.
/// </summary>
public static class SampleSerializerOptions
{
    /// <summary>Gets the module's converter-bearing serializer options.</summary>
    public static JsonSerializerOptions Options { get; } = CreateOptions();

    private static JsonSerializerOptions CreateOptions()
    {
        var options = new JsonSerializerOptions();
        options.Converters.Add(new SampleItemIdConverter());
        return options;
    }
}
