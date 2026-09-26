using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Sample.Contracts;

/// <summary>Exercises rejection of a noncanonical explicit name.</summary>
[HexalithQuery("Invalid name query.", Name = "Bad_Name", Domain = "sample")]
public sealed record BadNameQuery;
