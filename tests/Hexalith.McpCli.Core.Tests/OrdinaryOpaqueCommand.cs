using System.ComponentModel;
using Hexalith.McpCli.Sample.Contracts;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Has an ordinary converter-backed member with unknown schema shape.</summary>
public sealed class OrdinaryOpaqueCommand
{
    /// <summary>Gets or sets a value without an identifier declaration.</summary>
    [Description("The opaque value.")]
    public SampleItemId Value { get; init; }
}
