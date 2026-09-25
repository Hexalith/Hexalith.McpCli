using System.Globalization;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Reads string or numeric input but always writes a JSON number.</summary>
public sealed class NumericIdentifierConverter : JsonConverter<NumericIdentifier>
{
    /// <inheritdoc />
    public override NumericIdentifier Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        int value = reader.TokenType switch
        {
            JsonTokenType.String => int.TryParse(reader.GetString(), NumberStyles.None, CultureInfo.InvariantCulture, out int parsed) ? parsed : 1,
            JsonTokenType.Number => reader.GetInt32(),
            _ => throw new JsonException("A numeric identifier is required."),
        };
        return new NumericIdentifier(value);
    }

    /// <inheritdoc />
    public override void Write(Utf8JsonWriter writer, NumericIdentifier value, JsonSerializerOptions options)
        => writer.WriteNumberValue(value.Value);
}
