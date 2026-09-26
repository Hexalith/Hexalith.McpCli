using Hexalith.McpCli.Abstractions;

namespace Catalog.Routing.Contracts;

/// <summary>Exercises a constant aggregate source and explicit operation naming.</summary>
[HexalithQuery("List all synthetic items.", Name = "items-list", Domain = "routing", WireType = "list-items-wire",
    ProjectionType = "routing-items", AggregateId = "routing-list")]
public sealed record ListItemsQuery;
