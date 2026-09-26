using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Sample.Contracts;

/// <summary>Exercises exclusion of an attribute-routed Query without a projection type.</summary>
[HexalithQuery("Query missing its projection type.", Domain = "sample")]
public sealed record MissingProjectionQuery;
