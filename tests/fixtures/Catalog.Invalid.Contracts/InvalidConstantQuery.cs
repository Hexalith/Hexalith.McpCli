using Hexalith.McpCli.Abstractions;

namespace Catalog.Invalid.Contracts;

/// <summary>Exercises rejection of an aggregate identifier constant outside the Gateway pattern.</summary>
[HexalithQuery("Invalid constant query.", Domain = "invalid", ProjectionType = "invalid-items", AggregateId = "bad id")]
public sealed record InvalidConstantQuery;
