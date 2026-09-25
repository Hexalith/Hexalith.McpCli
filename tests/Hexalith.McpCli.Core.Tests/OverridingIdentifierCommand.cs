namespace Hexalith.McpCli.Core.Tests;

/// <summary>Overrides a declared identifier without repeating its attribute.</summary>
public sealed class OverridingIdentifierCommand : IdentifierBase
{
    /// <inheritdoc />
    public override string Key { get; init; } = string.Empty;
}
