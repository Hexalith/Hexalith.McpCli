using Hexalith.McpCli.Abstractions;

namespace Catalog.Invalid.Contracts;

/// <summary>Exercises exclusion of two operation decorations.</summary>
[HexalithCommand("Invalid doubly decorated command.", Domain = "invalid")]
[HexalithQuery("Invalid doubly decorated query.", Domain = "invalid")]
public sealed record DoublyDecoratedOperation;
