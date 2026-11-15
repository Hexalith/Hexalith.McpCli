using Hexalith.McpCli.Abstractions;

namespace Catalog.Routing.Contracts;

/// <summary>Exercises computed domain queries without either projection selector.</summary>
[HexalithQuery("Read computed status.", Domain = "routing")]
public sealed record ComputedStatusQuery;
