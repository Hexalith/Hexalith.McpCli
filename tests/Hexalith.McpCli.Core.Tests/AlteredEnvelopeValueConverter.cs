using System.Text.Json;
using System.Text.Json.Serialization;
using Catalog.Routing.Contracts;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Changes a trusted value when it writes a JSON string.</summary>
public sealed class AlteredEnvelopeValueConverter : JsonConverter<EnvelopeValue>
{
    /// <inheritdoc />
    public override EnvelopeValue Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
        => new(reader.GetString()!);

    /// <inheritdoc />
    public override void Write(Utf8JsonWriter writer, EnvelopeValue value, JsonSerializerOptions options)
        => writer.WriteStringValue(value.Value + "-changed");
}
