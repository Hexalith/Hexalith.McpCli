using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Sample.Contracts;

/// <summary>Exercises acronym and digit naming and explicit aggregate input.</summary>
[HexalithQuery("Read HTTP2 status.", Domain = "sample", ProjectionType = "sample-items")]
public sealed record GetHTTP2StatusQuery;
