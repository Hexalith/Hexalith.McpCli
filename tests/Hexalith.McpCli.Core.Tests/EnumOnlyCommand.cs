namespace Hexalith.McpCli.Core.Tests;

/// <summary>Contains an enum using the canonical converter.</summary>
public sealed class EnumOnlyCommand
{
    /// <summary>Gets or sets the enum input.</summary>
    public required StatusValue Mode { get; init; }
}
