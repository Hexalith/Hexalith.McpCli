using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Sample.Contracts;

/// <summary>Exercises rejection of invalid gateway routing values.</summary>
[HexalithQuery("Invalid routing query.", Domain = "Bad Domain", ProjectionType = "sample-items")]
public sealed record InvalidRoutingQuery;
