using System.Text.Json.Serialization;

namespace Catalog.Routing.Contracts;

/// <summary>A string-backed value object used by trusted envelope members.</summary>
/// <param name="Value">The exact envelope value.</param>
[JsonConverter(typeof(EnvelopeValueConverter))]
public sealed record EnvelopeValue(string Value);
