using System.Text.Json;
using System.Text.Json.Serialization;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Creates a converter that reads and writes <see cref="FactoryIdentifier"/> as a JSON string.</summary>
public sealed class FactoryIdentifierConverterFactory : JsonConverterFactory
{
    /// <inheritdoc />
    public override bool CanConvert(Type typeToConvert) => typeToConvert == typeof(FactoryIdentifier);

    /// <inheritdoc />
    public override JsonConverter CreateConverter(Type typeToConvert, JsonSerializerOptions options) => new Converter();

    private sealed class Converter : JsonConverter<FactoryIdentifier>
    {
        public override FactoryIdentifier Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
            => new(reader.GetString() ?? throw new JsonException("A string identifier is required."));

        public override void Write(Utf8JsonWriter writer, FactoryIdentifier value, JsonSerializerOptions options)
            => writer.WriteStringValue(value.Value);
    }
}
