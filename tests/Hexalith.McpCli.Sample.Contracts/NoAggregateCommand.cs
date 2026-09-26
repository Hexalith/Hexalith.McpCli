using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Sample.Contracts;

/// <summary>Exercises safe exclusion of a source-free command.</summary>
[HexalithCommand("Invalid source-free command.", Domain = "sample")]
public sealed record NoAggregateCommand;
