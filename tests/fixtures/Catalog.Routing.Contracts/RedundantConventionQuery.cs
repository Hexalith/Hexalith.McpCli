using Hexalith.McpCli.Abstractions;

namespace Catalog.Routing.Contracts;

/// <summary>Exercises an attribute wire type that repeats the Module's kebab-case convention value.</summary>
[HexalithQuery("Query whose attribute repeats its convention wire type.", Domain = "routing", WireType = "redundant-convention",
    ProjectionType = "routing-items", AggregateId = "routing-list")]
public sealed record RedundantConventionQuery;
