using System.Text.Json;
using System.Text.Json.Serialization;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Serializes an opaque Query payload as one JSON string.</summary>
public sealed class OpaqueQueryPayloadConverter : JsonConverter<OpaqueQueryPayload>
{
    /// <inheritdoc />
    public override OpaqueQueryPayload Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
        => new(reader.GetString() ?? throw new JsonException("A value is required."));

    /// <inheritdoc />
    public override void Write(Utf8JsonWriter writer, OpaqueQueryPayload value, JsonSerializerOptions options)
        => writer.WriteStringValue(value.Value);
}
