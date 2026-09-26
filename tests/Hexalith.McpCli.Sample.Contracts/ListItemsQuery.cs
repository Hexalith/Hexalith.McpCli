using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Sample.Contracts;

/// <summary>Exercises a constant aggregate source and explicit operation naming.</summary>
[HexalithQuery("List all synthetic items.", Name = "items-list", Domain = "sample", WireType = "list-items-wire",
    ProjectionType = "sample-items", AggregateId = "sample-list")]
public sealed record ListItemsQuery;
