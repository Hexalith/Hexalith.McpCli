using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Sample.Contracts;

/// <summary>Exercises rejection of a blank projection actor type.</summary>
[HexalithQuery("Invalid blank actor query.", Domain = "sample", ProjectionType = "sample-items", ProjectionActorType = "   ")]
public sealed record WhitespaceProjectionActorQuery;
