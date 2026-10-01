using Hexalith.McpCli.Abstractions;

namespace Catalog.String.Contracts;

/// <summary>Lists synthetic items through a String-kind aggregate constant.</summary>
[HexalithQuery("List synthetic string items.", Domain = "string-fixture", WireType = "list-items-wire",
    ProjectionType = "string-items", AggregateId = "items-index")]
public sealed record ListItemsQuery;
