using System.Text.Json.Serialization;
using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>A decorated Query whose converter hides its root JSON shape.</summary>
/// <param name="Value">The converted value.</param>
[HexalithQuery("Read an opaque value.")]
[JsonConverter(typeof(OpaqueQueryPayloadConverter))]
public sealed record OpaqueQueryPayload(string Value);
