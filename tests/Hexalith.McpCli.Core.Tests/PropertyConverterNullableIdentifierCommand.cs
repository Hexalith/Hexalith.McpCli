using System.Text.Json.Serialization;
using Hexalith.McpCli.Abstractions;
using Hexalith.McpCli.Sample.Contracts;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Declares an optional identifier whose converter is applied at the property level.</summary>
public sealed class PropertyConverterNullableIdentifierCommand
{
    /// <summary>Gets or sets the optional converter-backed identifier.</summary>
    [HexalithIdentifier]
    [JsonConverter(typeof(SampleItemIdConverter))]
    public SampleItemId? Id { get; init; }
}
