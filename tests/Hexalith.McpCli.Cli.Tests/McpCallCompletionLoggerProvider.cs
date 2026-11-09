using Microsoft.Extensions.Logging;

namespace Hexalith.McpCli.Cli.Tests;

/// <summary>Waits for a piped MCP call's response writer before the harness tears down its transport.</summary>
internal sealed class McpCallCompletionLoggerProvider : ILoggerProvider, ILogger
{
    private readonly TaskCompletionSource _completed = new(TaskCreationOptions.RunContinuationsAsynchronously);

    /// <summary>Gets completion after the server has finished writing the tool response.</summary>
    internal Task Completed => _completed.Task;

    /// <inheritdoc />
    public ILogger CreateLogger(string categoryName) => this;

    /// <inheritdoc />
    public void Dispose() { }

    /// <inheritdoc />
    public IDisposable? BeginScope<TState>(TState state) where TState : notnull => null;

    /// <inheritdoc />
    public bool IsEnabled(LogLevel logLevel) => true;

    /// <inheritdoc />
    public void Log<TState>(LogLevel logLevel, EventId eventId, TState state, Exception? exception,
        Func<TState, Exception?, string> formatter)
    {
        if (formatter(state, exception).Contains("method 'tools/call' request handler completed", StringComparison.Ordinal))
            _completed.TrySetResult();
    }
}
