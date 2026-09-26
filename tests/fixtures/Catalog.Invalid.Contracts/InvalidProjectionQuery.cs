using Hexalith.McpCli.Abstractions;

namespace Catalog.Invalid.Contracts;

/// <summary>Exercises rejection of a noncanonical projection type.</summary>
[HexalithQuery("Invalid projection query.", Domain = "invalid", ProjectionType = "Invalid Items")]
public sealed record InvalidProjectionQuery;
