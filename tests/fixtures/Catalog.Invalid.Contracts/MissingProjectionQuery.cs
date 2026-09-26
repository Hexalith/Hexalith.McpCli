using Hexalith.McpCli.Abstractions;

namespace Catalog.Invalid.Contracts;

/// <summary>Exercises exclusion of an attribute-routed Query without a projection type.</summary>
[HexalithQuery("Query missing its projection type.", Domain = "invalid")]
public sealed record MissingProjectionQuery;
