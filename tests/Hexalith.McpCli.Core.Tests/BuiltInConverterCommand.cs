using System.Text.Json.Serialization;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Annotates an enum member with a System.Text.Json converter.</summary>
public sealed class BuiltInConverterCommand
{
    /// <summary>Gets or sets the status written by the built-in converter.</summary>
    [JsonConverter(typeof(JsonStringEnumConverter<StatusValue>))]
    public required StatusValue Mode { get; init; }
}
