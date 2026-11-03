namespace Hexalith.McpCli.Manifest.Tests;

/// <summary>Runs only an offline disposal callback for infrastructure ownership controls.</summary>
internal sealed class NativeCatalogTestDisposable(Func<ValueTask> callback) : IAsyncDisposable
{
    /// <inheritdoc />
    public ValueTask DisposeAsync() => callback();
}
