using System.Collections.Immutable;
using System.Diagnostics;

using Aspire.Hosting.ApplicationModel;

using Hexalith.McpCli.Integration.Tests;

using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging.Abstractions;

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

    /// <summary>Any declared terminal failure state aborts the Running wait immediately with resource diagnostics.</summary>
    /// <param name="terminalState">The Aspire terminal failure state to publish.</param>
    /// <param name="exitCode">The process exit code attached to the snapshot.</param>
    [Theory]
    [InlineData("FailedToStart", 1)]
    [InlineData("Exited", 137)]
    [InlineData("Finished", 0)]
    [InlineData("RuntimeUnhealthy", 2)]
    public async Task WaitForResourceRunningAbortsImmediatelyOnDeclaredTerminalFailure(string terminalState, int exitCode)
    {
        using var lifetime = new TestHostApplicationLifetime();
        using var notifications = CreateNotifications(lifetime);
        var resource = new TestResource("eventstore");
        await PublishStateAsync(notifications, resource, KnownResourceStates.Starting);

        using var budget = new CancellationTokenSource(TimeSpan.FromMinutes(2));
        var elapsed = Stopwatch.StartNew();
        Task waitTask = IsolatedTopologyLifecycle<object>.WaitForResourceRunningAsync(
            notifications,
            resource.Name,
            [resource.Name, "tenants"],
            budget.Token);

        await Task.Delay(50, TestContext.Current.CancellationToken);
        await PublishStateAsync(notifications, resource, terminalState, exitCode);

        InvalidOperationException failure = await Assert.ThrowsAsync<InvalidOperationException>(() => waitTask);
        elapsed.Stop();
        Assert.True(elapsed.Elapsed < TimeSpan.FromSeconds(10), $"Expected immediate abort, took {elapsed.Elapsed}.");
        Assert.Contains("eventstore", failure.Message, StringComparison.Ordinal);
        Assert.Contains(terminalState, failure.Message, StringComparison.Ordinal);
        Assert.Contains(exitCode.ToString(System.Globalization.CultureInfo.InvariantCulture), failure.Message, StringComparison.Ordinal);
    }

    /// <summary>A declared terminal failure aborts endpoint URL discovery immediately instead of waiting out the timeout.</summary>
    [Fact]
    public async Task WaitForEndpointAbortsImmediatelyOnDeclaredTerminalFailure()
    {
        using var lifetime = new TestHostApplicationLifetime();
        using var notifications = CreateNotifications(lifetime);
        var resource = new TestResource("parties");
        await PublishStateAsync(notifications, resource, KnownResourceStates.Running);

        using var budget = new CancellationTokenSource(TimeSpan.FromMinutes(2));
        var elapsed = Stopwatch.StartNew();
        Task<string> waitTask = IsolatedTopologyLifecycle<object>.WaitForEndpointAsync(
            notifications,
            resource.Name,
            "http",
            [resource.Name],
            budget.Token);

        await Task.Delay(50, TestContext.Current.CancellationToken);
        await PublishStateAsync(notifications, resource, KnownResourceStates.Exited, 139);

        InvalidOperationException failure = await Assert.ThrowsAsync<InvalidOperationException>(() => waitTask);
        elapsed.Stop();
        Assert.True(elapsed.Elapsed < TimeSpan.FromSeconds(10), $"Expected immediate abort, took {elapsed.Elapsed}.");
        Assert.Contains("parties", failure.Message, StringComparison.Ordinal);
        Assert.Contains(KnownResourceStates.Exited, failure.Message, StringComparison.Ordinal);
        Assert.Contains("139", failure.Message, StringComparison.Ordinal);
    }

    /// <summary>A sibling declared resource crash aborts an in-flight /alive probe without waiting for AlivenessTimeout.</summary>
    [Fact]
    public async Task WaitForAlivenessAbortsImmediatelyWhenWatchedResourceCrashes()
    {
        using var lifetime = new TestHostApplicationLifetime();
        using var notifications = CreateNotifications(lifetime);
        var gateway = new TestResource("eventstore");
        var tenants = new TestResource("tenants");
        await PublishStateAsync(notifications, gateway, KnownResourceStates.Running);
        await PublishStateAsync(notifications, tenants, KnownResourceStates.Running);

        using var handler = new HangingHttpMessageHandler();
        using var client = new HttpClient(handler) { BaseAddress = new Uri("http://127.0.0.1:1") };
        var elapsed = Stopwatch.StartNew();

        Task watchTask = IsolatedTopologyLifecycle<object>.RunWithTerminalFailureWatchAsync(
            notifications,
            [gateway.Name, tenants.Name],
            token => IsolatedTopologyLifecycle<object>.WaitForAlivenessAsync(client, TimeSpan.FromMinutes(2), token),
            TestContext.Current.CancellationToken);

        await handler.RequestStarted.WaitAsync(TimeSpan.FromSeconds(5), TestContext.Current.CancellationToken);
        await PublishStateAsync(notifications, tenants, KnownResourceStates.FailedToStart, 42);

        InvalidOperationException failure = await Assert.ThrowsAsync<InvalidOperationException>(() => watchTask);
        elapsed.Stop();
        Assert.True(elapsed.Elapsed < TimeSpan.FromSeconds(10), $"Expected immediate abort, took {elapsed.Elapsed}.");
        Assert.Contains("tenants", failure.Message, StringComparison.Ordinal);
        Assert.Contains(KnownResourceStates.FailedToStart, failure.Message, StringComparison.Ordinal);
        Assert.Contains("42", failure.Message, StringComparison.Ordinal);
    }

    /// <summary>A declared resource crash aborts WaitForReadinessAsync sidecar waits immediately.</summary>
    [Fact]
    public async Task WaitForReadinessAbortsImmediatelyWhenWatchedResourceCrashes()
    {
        using var lifetime = new TestHostApplicationLifetime();
        using var notifications = CreateNotifications(lifetime);
        var projects = new TestResource("projects");
        await PublishStateAsync(notifications, projects, KnownResourceStates.Running);

        var readinessEntered = new TaskCompletionSource(TaskCreationOptions.RunContinuationsAsynchronously);
        var elapsed = Stopwatch.StartNew();

        Task watchTask = IsolatedTopologyLifecycle<object>.RunWithTerminalFailureWatchAsync(
            notifications,
            [projects.Name],
            async token =>
            {
                readinessEntered.TrySetResult();
                await Task.Delay(TimeSpan.FromMinutes(6), token);
            },
            TestContext.Current.CancellationToken);

        await readinessEntered.Task.WaitAsync(TimeSpan.FromSeconds(5), TestContext.Current.CancellationToken);
        await PublishStateAsync(notifications, projects, KnownResourceStates.RuntimeUnhealthy, 7);

        InvalidOperationException failure = await Assert.ThrowsAsync<InvalidOperationException>(() => watchTask);
        elapsed.Stop();
        Assert.True(elapsed.Elapsed < TimeSpan.FromSeconds(10), $"Expected immediate abort, took {elapsed.Elapsed}.");
        Assert.Contains("projects", failure.Message, StringComparison.Ordinal);
        Assert.Contains(KnownResourceStates.RuntimeUnhealthy, failure.Message, StringComparison.Ordinal);
        Assert.Contains("7", failure.Message, StringComparison.Ordinal);
    }

    /// <summary>Undeclared explicit-start catalog-source clones in NotStarted or terminal states never false-trigger startup.</summary>
    [Fact]
    public async Task UndeclaredCatalogSourceNotStartedAndTerminalStatesAreIgnored()
    {
        using var lifetime = new TestHostApplicationLifetime();
        using var notifications = CreateNotifications(lifetime);
        var tenants = new TestResource("tenants");
        var catalogClone = new TestResource("tenants-catalog-source");
        await PublishStateAsync(notifications, catalogClone, KnownResourceStates.NotStarted);
        await PublishStateAsync(notifications, tenants, KnownResourceStates.Starting);

        Task runningTask = IsolatedTopologyLifecycle<object>.WaitForResourceRunningAsync(
            notifications,
            tenants.Name,
            [tenants.Name],
            TestContext.Current.CancellationToken);

        await Task.Delay(50, TestContext.Current.CancellationToken);
        await PublishStateAsync(notifications, catalogClone, KnownResourceStates.Exited, 1);
        await PublishStateAsync(notifications, tenants, KnownResourceStates.Running, urls: [new UrlSnapshot("http", "http://127.0.0.1:5000", false)]);

        await runningTask;
        string endpoint = await IsolatedTopologyLifecycle<object>.WaitForEndpointAsync(
            notifications,
            tenants.Name,
            "http",
            [tenants.Name],
            TestContext.Current.CancellationToken);
        Assert.Equal("http://127.0.0.1:5000", endpoint);
    }

    /// <summary>A declared resource already in a terminal failure state rejects immediately before running the operation.</summary>
    [Fact]
    public async Task AlreadyFailedDeclaredResourceThrowsBeforeInvokingOperation()
    {
        using var lifetime = new TestHostApplicationLifetime();
        using var notifications = CreateNotifications(lifetime);
        var worker = new TestResource("projects-workers");
        await PublishStateAsync(notifications, worker, KnownResourceStates.Finished, 0);

        bool invoked = false;
        InvalidOperationException failure = await Assert.ThrowsAsync<InvalidOperationException>(() =>
            IsolatedTopologyLifecycle<object>.RunWithTerminalFailureWatchAsync(
                notifications,
                [worker.Name],
                _ =>
                {
                    invoked = true;
                    return Task.CompletedTask;
                },
                TestContext.Current.CancellationToken));

        Assert.False(invoked);
        Assert.Contains("projects-workers", failure.Message, StringComparison.Ordinal);
        Assert.Contains(KnownResourceStates.Finished, failure.Message, StringComparison.Ordinal);
        Assert.Contains("0", failure.Message, StringComparison.Ordinal);
    }

    private static ResourceNotificationService CreateNotifications(IHostApplicationLifetime lifetime)
        => new(
            NullLogger<ResourceNotificationService>.Instance,
            lifetime,
            new TestServiceProvider(),
            new ResourceLoggerService());

    private static Task PublishStateAsync(
        ResourceNotificationService notifications,
        IResource resource,
        string state,
        int? exitCode = null,
        UrlSnapshot[]? urls = null)
        => notifications.PublishUpdateAsync(resource, snapshot => snapshot with
        {
            ResourceType = "Project",
            State = new ResourceStateSnapshot(state, null),
            ExitCode = exitCode,
            Urls = urls is null ? ImmutableArray<UrlSnapshot>.Empty : [.. urls],
            Properties = ImmutableArray<ResourcePropertySnapshot>.Empty,
        });
}
