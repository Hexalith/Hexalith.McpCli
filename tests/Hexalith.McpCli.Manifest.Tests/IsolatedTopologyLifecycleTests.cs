using Hexalith.McpCli.Integration.Tests;

namespace Hexalith.McpCli.Manifest.Tests;

/// <summary>Protects independent fixture disposal and failure preservation without starting infrastructure.</summary>
public sealed class IsolatedTopologyLifecycleTests
{
    /// <summary>One failed owner cannot prevent later client, builder or lock cleanup.</summary>
    [Fact]
    public async Task CleanupAttemptsEveryOwnerAndRetainsFirstFailure()
    {
        var expected = new IOException("first owned failure");
        var calls = new List<int>();
        IOException actual = await Assert.ThrowsAsync<IOException>(async () =>
            await IsolatedTopologyLifecycle<object>.DisposeOwnedAsync(null,
                () => { calls.Add(1); return ValueTask.FromException(expected); },
                () => { calls.Add(2); return ValueTask.FromException(new InvalidOperationException("later owned failure")); },
                () => { calls.Add(3); return ValueTask.CompletedTask; }));
        Assert.Same(expected, actual);
        Assert.Equal(new[] { 1, 2, 3 }, calls);
    }

    /// <summary>Preparation keeps its original exception even when all independent disposals fail.</summary>
    [Fact]
    public async Task FailedPreparationKeepsOriginalFailureAndAttemptsEveryOwner()
    {
        var calls = new List<int>();
        await IsolatedTopologyLifecycle<object>.DisposeOwnedAsync(new InvalidDataException("original preparation failure"),
            () => { calls.Add(1); return ValueTask.FromException(new IOException("first cleanup")); },
            () => { calls.Add(2); return ValueTask.FromException(new IOException("second cleanup")); });
        Assert.Equal(new[] { 1, 2 }, calls);
    }
    /// <summary>A request timeout can recover before the enclosing readiness deadline.</summary>
    [Fact]
    public async Task IndividualRequestTimeoutRetainsBoundedLivenessRetry()
    {
        using var handler = new LivenessHandler(cancelFirst: true);
        using var client = new HttpClient(handler) { BaseAddress = new Uri("http://127.0.0.1:1") };
        await IsolatedTopologyLifecycle<object>.WaitForAlivenessAsync(client, TimeSpan.FromSeconds(5), TestContext.Current.CancellationToken);
        Assert.Equal(2, handler.Calls);
    }

    /// <summary>Outer cancellation stops liveness without issuing another request.</summary>
    [Fact]
    public async Task CanceledReadinessNeverRetriesOrSubmitsARequest()
    {
        using var handler = new LivenessHandler(cancelFirst: false);
        using var client = new HttpClient(handler) { BaseAddress = new Uri("http://127.0.0.1:1") };
        using var canceled = new CancellationTokenSource();
        canceled.Cancel();
        await Assert.ThrowsAnyAsync<OperationCanceledException>(() =>
            IsolatedTopologyLifecycle<object>.WaitForAlivenessAsync(client, TimeSpan.FromSeconds(5), canceled.Token));
        Assert.Equal(0, handler.Calls);
    }
}
