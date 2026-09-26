using Hexalith.McpCli.Abstractions;

namespace Catalog.String.Contracts;

/// <summary>Looks up a non-ULID aggregate identifier.</summary>
/// <param name="Key">The string aggregate identifier.</param>
[HexalithQuery("Look up a string identifier.", Domain = "string-fixture", ProjectionType = "string-fixture", AggregateIdProperty = nameof(Key))]
public sealed record LookupQuery(string Key);
