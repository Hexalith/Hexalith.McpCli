using Hexalith.McpCli.Core.Execution;

namespace Hexalith.McpCli.Core.Settings;

/// <summary>The resolved process settings or a public configuration error.</summary>
/// <param name="Settings">The settings on success.</param>
/// <param name="Error">The configuration error on failure.</param>
public sealed record SettingsResolution(ResolvedSettings? Settings, OperationError? Error);
