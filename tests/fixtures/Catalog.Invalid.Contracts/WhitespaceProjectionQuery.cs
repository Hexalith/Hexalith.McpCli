using Hexalith.McpCli.Abstractions;

namespace Catalog.Invalid.Contracts;

/// <summary>Exercises rejection of an explicitly blank projection type rather than an absent selector.</summary>
[HexalithQuery("Invalid blank projection query.", Domain = "invalid", ProjectionType = "   ")]
public sealed record WhitespaceProjectionQuery;
