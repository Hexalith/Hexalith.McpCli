using Microsoft.Extensions.Hosting;

namespace Hexalith.McpCli.Manifest.Tests;

/// <summary>Minimal host lifetime implementation for constructing ResourceNotificationService in unit tests.</summary>
internal sealed class TestHostApplicationLifetime : IHostApplicationLifetime, IDisposable
{
    private readonly CancellationTokenSource _started = new();
    private readonly CancellationTokenSource _stopping = new();
    private readonly CancellationTokenSource _stopped = new();

    /// <inheritdoc/>
    public CancellationToken ApplicationStarted => _started.Token;

    /// <inheritdoc/>
    public CancellationToken ApplicationStopping => _stopping.Token;

    /// <inheritdoc/>
    public CancellationToken ApplicationStopped => _stopped.Token;

    /// <inheritdoc/>
    public void StopApplication() => _stopping.Cancel();

    /// <inheritdoc/>
    public void Dispose()
    {
        _started.Dispose();
        _stopping.Dispose();
        _stopped.Dispose();
    }
}
