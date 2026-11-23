using Hexalith.McpCli.Abstractions;

namespace Catalog.Lint.Contracts;

/// <summary>Exercises an operation description that only restates its name.</summary>
[HexalithQuery(" inspect hollow ", Domain = "lint-fixture", ProjectionType = "lint-items", AggregateId = "01ARZ3NDEKTSV4RRFFQ69G5FAV")]
public sealed record InspectHollowQuery;
