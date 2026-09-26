using Hexalith.McpCli.Abstractions;

namespace Catalog.Invalid.Contracts;

/// <summary>Exercises rejection of a colon, which the Gateway reserves in a query wire type.</summary>
[HexalithQuery("Query with a colon in its wire type.", Domain = "invalid", WireType = "items:colon",
    ProjectionType = "invalid-items")]
public sealed record ColonWireQuery;
