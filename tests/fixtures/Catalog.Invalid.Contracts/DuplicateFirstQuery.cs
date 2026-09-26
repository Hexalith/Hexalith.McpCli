using Hexalith.McpCli.Abstractions;

namespace Catalog.Invalid.Contracts;

/// <summary>First duplicate canonical name declaration.</summary>
[HexalithQuery("First duplicate query.", Name = "duplicate", Domain = "invalid", ProjectionType = "invalid-items")]
public sealed record DuplicateFirstQuery;
