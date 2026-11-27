namespace Hexalith.McpCli.Manifest.Tests;

/// <summary>Minimal empty service provider for constructing ResourceNotificationService in unit tests.</summary>
internal sealed class TestServiceProvider : IServiceProvider
{
    /// <inheritdoc/>
    public object? GetService(Type serviceType) => null;
}
