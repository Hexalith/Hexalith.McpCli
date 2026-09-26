using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Sample.Contracts;

/// <summary>Exercises exclusion of two operation decorations.</summary>
[HexalithCommand("Invalid doubly decorated command.", Domain = "sample")]
[HexalithQuery("Invalid doubly decorated query.", Domain = "sample")]
public sealed record DoublyDecoratedOperation;
