namespace Hexalith.McpCli.Core.Tests;

/// <summary>An identifier value object whose converter writes JSON numbers.</summary>
/// <param name="Value">The numeric value.</param>
public readonly record struct NumericIdentifier(int Value);
