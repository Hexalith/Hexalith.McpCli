using System.Text.Json.Serialization;
using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Uses a property-level converter that emits a JSON number.</summary>
public sealed class PropertyConvertedNumericIdentifierCommand
{
    /// <summary>Gets or sets the invalid converted identifier.</summary>
    [HexalithIdentifier]
    [JsonConverter(typeof(NumericIdentifierConverter))]
    public required NumericIdentifier ItemId { get; init; }
}
