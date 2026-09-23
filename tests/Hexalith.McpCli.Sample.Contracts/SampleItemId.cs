namespace Hexalith.McpCli.Sample.Contracts;

/// <summary>
/// Represents a sample aggregate identifier serialized by the module's converter.
/// </summary>
/// <param name="Value">The ULID text of the aggregate.</param>
public readonly record struct SampleItemId(string Value);
