using Microsoft.Extensions.Logging;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>One recorded log call.</summary>
/// <param name="Level">The log level.</param>
/// <param name="EventId">The event identifier.</param>
/// <param name="Fields">The structured fields, without the original format.</param>
/// <param name="Text">The formatted message.</param>
public sealed record LogEntry(LogLevel Level, EventId EventId, IReadOnlyDictionary<string, object?> Fields, string Text);
