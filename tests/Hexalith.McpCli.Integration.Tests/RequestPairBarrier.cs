namespace Hexalith.McpCli.Integration.Tests;

/// <summary>Releases a captured request pair within one bounded test-owned deadline.</summary>
internal sealed class RequestPairBarrier
{
    /// <summary>Counts complete requests arriving at the forwarder; incremented atomically.</summary>
    internal int Arrivals;

    /// <summary>Completes when both requests are captured, before either is forwarded.</summary>
    internal TaskCompletionSource Captured { get; } = new(TaskCreationOptions.RunContinuationsAsynchronously);

    /// <summary>Completes at capture or fails when the pair's absolute waiting budget expires.</summary>
    internal Task Ready { get; }

    /// <summary>Starts the capture deadline using the current test's cancellation token.</summary>
    /// <param name="timeout">Maximum time allowed for both requests to arrive.</param>
    internal RequestPairBarrier(TimeSpan timeout)
        => Ready = Captured.Task.WaitAsync(timeout, TestContext.Current.CancellationToken);
}
