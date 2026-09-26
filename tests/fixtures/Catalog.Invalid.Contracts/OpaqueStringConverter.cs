using System.Text.Json;
using System.Text.Json.Serialization;

namespace Catalog.Invalid.Contracts;

/// <summary>A custom converter whose serialized shape the Catalog cannot see.</summary>
public sealed class OpaqueStringConverter : JsonConverter<string>
{
    /// <inheritdoc/>
    public override string? Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options) => reader.GetString();

    /// <inheritdoc/>
    public override void Write(Utf8JsonWriter writer, string value, JsonSerializerOptions options)
    {
        ArgumentNullException.ThrowIfNull(writer);
        writer.WriteStringValue(value);
    }
}
