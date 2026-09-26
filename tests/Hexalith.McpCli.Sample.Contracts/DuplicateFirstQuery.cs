using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Sample.Contracts;

/// <summary>First duplicate canonical name declaration.</summary>
[HexalithQuery("First duplicate query.", Name = "duplicate", Domain = "sample", ProjectionType = "sample-items")]
public sealed record DuplicateFirstQuery;
