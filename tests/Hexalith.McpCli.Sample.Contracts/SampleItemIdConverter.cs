using System.Text.Json;
using System.Text.Json.Serialization;

namespace Hexalith.McpCli.Sample.Contracts;

/// <summary>
/// Serializes the sample identifier value object as one JSON string.
/// </summary>
public sealed class SampleItemIdConverter : JsonConverter<SampleItemId>
{
    /// <inheritdoc />
    public override SampleItemId Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
        => new(reader.GetString() ?? throw new JsonException("An item identifier cannot be null."));

    /// <inheritdoc />
    public override void Write(Utf8JsonWriter writer, SampleItemId value, JsonSerializerOptions options)
    {
        if (value.Value is null)
        {
            throw new JsonException("An item identifier cannot be null.");
        }

        writer.WriteStringValue(value.Value);
    }
}
