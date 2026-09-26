using System.Collections.Concurrent;
using Microsoft.Extensions.Logging;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Records every enabled log call with its structured fields.</summary>
/// <typeparam name="T">The logger category.</typeparam>
public sealed class RecordingLogger<T> : ILogger<T>
{
    private readonly ConcurrentQueue<LogEntry> _entries = new();

    /// <summary>Gets the recorded entries in call order.</summary>
    public IReadOnlyList<LogEntry> Entries => [.. _entries];

    /// <inheritdoc/>
    public IDisposable? BeginScope<TState>(TState state)
        where TState : notnull => null;

    /// <inheritdoc/>
    public bool IsEnabled(LogLevel logLevel) => true;

    /// <inheritdoc/>
    public void Log<TState>(LogLevel logLevel, EventId eventId, TState state, Exception? exception, Func<TState, Exception?, string> formatter)
    {
        ArgumentNullException.ThrowIfNull(formatter);
        Dictionary<string, object?> fields = state is IEnumerable<KeyValuePair<string, object?>> pairs
            ? pairs.Where(pair => pair.Key != "{OriginalFormat}").ToDictionary(pair => pair.Key, pair => pair.Value, StringComparer.Ordinal)
            : [];
        _entries.Enqueue(new LogEntry(logLevel, eventId, fields, formatter(state, exception)));
    }
}
