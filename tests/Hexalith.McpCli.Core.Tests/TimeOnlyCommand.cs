namespace Hexalith.McpCli.Core.Tests;

/// <summary>Carries time-of-day values without offsets.</summary>
public sealed class TimeOnlyCommand
{
    /// <summary>Gets or sets a required time of day.</summary>
    public TimeOnly At { get; init; }

    /// <summary>Gets or sets an optional time of day.</summary>
    public TimeOnly? Maybe { get; init; }
}
