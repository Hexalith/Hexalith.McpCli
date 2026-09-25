using System.Text.Json.Serialization;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Declares polymorphic payload serialization.</summary>
[JsonPolymorphic]
[JsonDerivedType(typeof(PolymorphicDerived), "derived")]
public abstract class PolymorphicBase
{
    /// <summary>Gets or sets the base member.</summary>
    public string? BaseValue { get; init; }
}
