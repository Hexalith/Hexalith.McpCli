using System.ComponentModel;
using System.Text.Json.Serialization;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Separates constructor-bound getters from computed getters.</summary>
public sealed class CtorBoundCommand
{
    /// <summary>Initializes the constructor-bound payload value.</summary>
    /// <param name="value">The supplied value.</param>
    [JsonConstructor]
    public CtorBoundCommand(string value)
    {
        Value = value;
    }

    /// <summary>Gets the constructor-bound input.</summary>
    [Description("The constructor-bound input.")]
    public string Value { get; }

    /// <summary>Gets a computed getter with no input binding.</summary>
    public int Length => Value.Length;
}
