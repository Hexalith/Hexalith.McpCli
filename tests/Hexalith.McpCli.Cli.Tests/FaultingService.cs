using Microsoft.Extensions.Hosting;

namespace Hexalith.McpCli.Cli.Tests;

/// <summary>Simulates a hosted service that fails after startup.</summary>
internal sealed class FaultingService : BackgroundService
{
    /// <inheritdoc />
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        await Task.Yield();
        throw new InvalidOperationException("serving fault");
    }
}
