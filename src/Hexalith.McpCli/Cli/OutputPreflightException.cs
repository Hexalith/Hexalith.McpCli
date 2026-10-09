namespace Hexalith.McpCli.Cli;

/// <summary>Signals that a predictable result destination check failed.</summary>
internal sealed class OutputPreflightException(string message, Exception innerException)
    : IOException(message, innerException);
