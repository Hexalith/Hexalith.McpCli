using System.Text.Json.Serialization;
using Catalog.Routing.Contracts;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Uses a converter that does not preserve trusted envelope strings.</summary>
public sealed class AlteredEnvelopeCommand
{
    /// <summary>Gets or sets the converter-backed member.</summary>
    [JsonConverter(typeof(AlteredEnvelopeValueConverter))]
    public required EnvelopeValue Value { get; init; }
}
