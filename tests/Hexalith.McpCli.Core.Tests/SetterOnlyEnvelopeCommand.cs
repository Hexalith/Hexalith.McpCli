using System.ComponentModel;
using System.Text.Json.Serialization;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Accepts an envelope value through a setter-only member.</summary>
public sealed class SetterOnlyEnvelopeCommand
{
    /// <summary>Gets or sets an ordinary payload member.</summary>
    public required string Title { get; init; }

    /// <summary>Sets the envelope tenant.</summary>
    [Description("The tenant supplied by the envelope.")]
    [JsonPropertyName("tenant/~")]
    public string Tenant { set { } }
}
