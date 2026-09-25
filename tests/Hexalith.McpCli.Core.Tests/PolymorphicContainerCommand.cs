namespace Hexalith.McpCli.Core.Tests;

/// <summary>Contains a nested polymorphic member.</summary>
public sealed class PolymorphicContainerCommand
{
    /// <summary>Gets or sets the polymorphic value.</summary>
    public required PolymorphicBase Inner { get; init; }
}
