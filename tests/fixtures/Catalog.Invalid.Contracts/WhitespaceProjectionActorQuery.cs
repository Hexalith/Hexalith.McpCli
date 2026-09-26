using Hexalith.McpCli.Abstractions;

namespace Catalog.Invalid.Contracts;

/// <summary>Exercises rejection of a blank projection actor type.</summary>
[HexalithQuery("Invalid blank actor query.", Domain = "invalid", ProjectionType = "invalid-items", ProjectionActorType = "   ")]
public sealed record WhitespaceProjectionActorQuery;
