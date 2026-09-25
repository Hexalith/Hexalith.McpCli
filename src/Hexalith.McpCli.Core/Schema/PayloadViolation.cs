namespace Hexalith.McpCli.Core.Schema;

/// <summary>Describes one JSON Schema violation.</summary>
/// <param name="Path">The JSON Pointer instance location.</param>
/// <param name="Message">The validator's explanation.</param>
public sealed record PayloadViolation(string Path, string Message);
