using Hexalith.McpCli.Abstractions;

namespace Catalog.Invalid.Contracts;

/// <summary>Exercises rejection of a blank operation description.</summary>
[HexalithQuery("   ", Domain = "invalid", ProjectionType = "invalid-items")]
public sealed record MissingDescriptionQuery;
