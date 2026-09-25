using System.ComponentModel;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>A nested payload value.</summary>
/// <param name="Count">The numeric count.</param>
public sealed record NestedValue([property: Description("The count inside a nested value.")] int Count);
