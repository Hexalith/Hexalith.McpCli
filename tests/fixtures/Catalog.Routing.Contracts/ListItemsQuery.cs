using Hexalith.McpCli.Abstractions;

namespace Catalog.Routing.Contracts;

/// <summary>Exercises a constant aggregate source and explicit operation naming.</summary>
[HexalithQuery("List all synthetic items.", Name = "items-list", Domain = "routing", WireType = "list-items-wire",
    ProjectionType = "routing-items", AggregateId = "01ARZ3NDEKTSV4RRFFQ69G5FAV", PlatformScope = "platform:routing")]
public sealed record ListItemsQuery;
