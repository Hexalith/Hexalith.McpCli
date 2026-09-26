using Hexalith.McpCli.Abstractions;

namespace Catalog.Invalid.Contracts;

/// <summary>Exercises rejection of a noncanonical explicit name.</summary>
[HexalithQuery("Invalid name query.", Name = "Bad_Name", Domain = "invalid")]
public sealed record BadNameQuery;
