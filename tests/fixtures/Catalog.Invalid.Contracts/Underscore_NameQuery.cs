using Hexalith.McpCli.Abstractions;

namespace Catalog.Invalid.Contracts;

/// <summary>Exercises rejection of a type-derived name that is not ASCII-alphanumeric.</summary>
[HexalithQuery("Noncanonical type name query.", Domain = "invalid", ProjectionType = "invalid-items")]
public sealed record Underscore_NameQuery;
