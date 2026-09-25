using System.ComponentModel;
using Hexalith.McpCli.Abstractions;
using Hexalith.McpCli.Sample.Contracts;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Declares optional identifiers, one of them converter-backed.</summary>
public sealed class NullableIdentifierCommand
{
    /// <summary>Gets or sets an optional string identifier.</summary>
    [HexalithIdentifier]
    [Description("The optional identifier.")]
    public string? Id { get; init; }

    /// <summary>Gets or sets an optional converter-backed identifier.</summary>
    [HexalithIdentifier]
    public SampleItemId? Sid { get; init; }
}
