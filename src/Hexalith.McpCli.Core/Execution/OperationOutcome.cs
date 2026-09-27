namespace Hexalith.McpCli.Core.Execution;

/// <summary>One execution result: a public success document or an error.</summary>
/// <param name="Document">A <see cref="CommandResult"/> or <see cref="QueryResult"/> on success.</param>
/// <param name="Error">The public error on failure.</param>
public sealed record OperationOutcome(object? Document, OperationError? Error);
