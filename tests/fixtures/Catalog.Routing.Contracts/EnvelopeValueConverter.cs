using System.Text.Json;
using System.Text.Json.Serialization;

namespace Catalog.Routing.Contracts;

/// <summary>Preserves envelope value objects as their exact JSON strings.</summary>
public sealed class EnvelopeValueConverter : JsonConverter<EnvelopeValue>
{
    /// <inheritdoc />
    public override EnvelopeValue Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
        => new(reader.GetString() ?? throw new JsonException("An envelope value cannot be null."));

    /// <inheritdoc />
    public override void Write(Utf8JsonWriter writer, EnvelopeValue value, JsonSerializerOptions options)
        => writer.WriteStringValue(value.Value);
}
