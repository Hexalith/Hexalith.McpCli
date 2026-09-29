using System.Text.Json;
using System.Text.Json.Serialization;
using Hexalith.McpCli.Core.Settings;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>
/// Runs a probe before each profile is serialized into the transaction's temporary file, then writes the profile
/// with the store's field rules. A probe can inspect the temporary file mid-write or throw to interrupt it.
/// </summary>
/// <param name="probe">Receives the zero-based profile write index before that profile is written.</param>
internal sealed class ConnectionProfileProbeConverter(Action<int> probe) : JsonConverter<ConnectionProfile>
{
    private static readonly JsonSerializerOptions ProfileOptions = new(JsonSerializerDefaults.Web)
    {
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    };

    private int _writes;

    /// <summary>Creates serializer options equivalent to the store's options with this probe attached.</summary>
    /// <param name="probe">Receives the zero-based profile write index before that profile is written.</param>
    /// <returns>The transaction serializer options.</returns>
    internal static JsonSerializerOptions Options(Action<int> probe)
        => new(ProfileOptions) { Converters = { new ConnectionProfileProbeConverter(probe) } };

    /// <inheritdoc />
    public override ConnectionProfile Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
        => throw new NotSupportedException("The probe only observes writes.");

    /// <inheritdoc />
    public override void Write(Utf8JsonWriter writer, ConnectionProfile value, JsonSerializerOptions options)
    {
        probe(_writes++);
        JsonSerializer.Serialize(writer, value, ProfileOptions);
    }
}
