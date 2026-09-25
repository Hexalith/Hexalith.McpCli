namespace Hexalith.McpCli.Core.Tests;

/// <summary>Contains a nested extension-data contract.</summary>
public sealed class ExtensionContainerCommand
{
    /// <summary>Gets or sets the nested value.</summary>
    public required NestedExtensionValue Inner { get; init; }
}
