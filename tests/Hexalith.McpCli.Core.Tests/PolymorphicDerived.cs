namespace Hexalith.McpCli.Core.Tests;

/// <summary>Adds a derived member that a closed base schema cannot accept.</summary>
public sealed class PolymorphicDerived : PolymorphicBase
{
    /// <summary>Gets or sets the derived member.</summary>
    public string? DerivedValue { get; init; }
}
