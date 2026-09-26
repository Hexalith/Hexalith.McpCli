using Hexalith.McpCli.Abstractions;

namespace Catalog.Routing.Contracts;

/// <summary>Exercises acronym and digit naming and explicit aggregate input.</summary>
[HexalithQuery("Read HTTP2 status.", Domain = "routing", ProjectionType = "routing-items")]
public sealed record GetHTTP2StatusQuery;
