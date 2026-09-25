using System.Text.Json.Serialization;
using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Declares an identifier whose property-level converter is a factory.</summary>
public sealed class FactoryIdentifierCommand
{
    /// <summary>Gets or sets the factory-converted identifier.</summary>
    [HexalithIdentifier]
    [JsonConverter(typeof(FactoryIdentifierConverterFactory))]
    public required FactoryIdentifier Id { get; init; }
}
