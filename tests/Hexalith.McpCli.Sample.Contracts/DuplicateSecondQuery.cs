using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Sample.Contracts;

/// <summary>Second duplicate canonical name declaration.</summary>
[HexalithQuery("Second duplicate query.", Name = "duplicate", Domain = "sample", ProjectionType = "sample-items")]
public sealed record DuplicateSecondQuery;
