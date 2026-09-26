using Hexalith.McpCli.Abstractions;

namespace Catalog.Invalid.Contracts;

/// <summary>Exercises safe exclusion of a source-free command.</summary>
[HexalithCommand("Invalid source-free command.", Domain = "invalid")]
public sealed record NoAggregateCommand;
