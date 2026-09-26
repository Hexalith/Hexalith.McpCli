using Hexalith.McpCli.Abstractions;

namespace Catalog.Invalid.Contracts;

/// <summary>Second duplicate canonical name declaration.</summary>
[HexalithQuery("Second duplicate query.", Name = "duplicate", Domain = "invalid", ProjectionType = "invalid-items")]
public sealed record DuplicateSecondQuery;
