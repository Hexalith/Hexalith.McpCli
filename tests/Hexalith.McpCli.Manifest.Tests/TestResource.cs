using Aspire.Hosting.ApplicationModel;

namespace Hexalith.McpCli.Manifest.Tests;

/// <summary>Minimal resource identity for unit testing Aspire resource state notifications.</summary>
/// <param name="name">The declared resource name.</param>
internal sealed class TestResource(string name) : IResource
{
    /// <inheritdoc/>
    public string Name { get; } = name;

    /// <inheritdoc/>
    public ResourceAnnotationCollection Annotations { get; } = [];
}
