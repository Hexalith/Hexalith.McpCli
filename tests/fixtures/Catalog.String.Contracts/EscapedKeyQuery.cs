using System.Text.Json.Serialization;
using Hexalith.McpCli.Abstractions;

namespace Catalog.String.Contracts;

/// <summary>Looks up a String identifier through an escaped serialized property name.</summary>
/// <param name="Key">The string aggregate identifier.</param>
[HexalithQuery("Look up an escaped string identifier.", Domain = "string-fixture", ProjectionType = "string-fixture", AggregateIdProperty = nameof(Key))]
public sealed record EscapedKeyQuery([property: JsonPropertyName("key/~")] string Key);
