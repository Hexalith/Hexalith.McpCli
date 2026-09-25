using System.Text.Json.Serialization;
using Hexalith.McpCli.Sample.Contracts;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Has an ordinary optional member whose converter is applied at the property level.</summary>
public sealed class PropertyConverterNullableCommand
{
    /// <summary>Gets or sets the optional converter-backed value.</summary>
    [JsonConverter(typeof(SampleItemIdConverter))]
    public SampleItemId? Value { get; init; }
}
