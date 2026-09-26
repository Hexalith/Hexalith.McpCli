using Hexalith.McpCli.Abstractions;

namespace Catalog.Invalid.Contracts;

/// <summary>Exercises rejection of invalid gateway routing values.</summary>
[HexalithQuery("Invalid routing query.", Domain = "Bad Domain", ProjectionType = "invalid-items")]
public sealed record InvalidRoutingQuery;
