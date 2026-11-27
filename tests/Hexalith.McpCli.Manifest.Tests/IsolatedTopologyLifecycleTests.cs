using System.Collections.Immutable;
using System.Diagnostics;

using Aspire.Hosting;
using Aspire.Hosting.ApplicationModel;
using Aspire.Hosting.Testing;

using Hexalith.McpCli.Integration.Tests;

using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging.Abstractions;

using NSubstitute;

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

    /// <summary>A published terminal state takes precedence even when the watcher has not delivered it.</summary>
    [Fact]
    public async Task ReadinessErrorChecksLatestSnapshotBeforeRethrowing()
    {
        using var lifetime = new TestHostApplicationLifetime();
        using var notifications = CreateNotifications(lifetime);
        var resource = new TestResource("eventstore");
        await PublishStateAsync(notifications, resource, KnownResourceStates.Running);

        InvalidOperationException failure = await Assert.ThrowsAsync<InvalidOperationException>(() =>
            IsolatedTopologyLifecycle<object>.RunWithTerminalFailureWatchAsync(
                notifications,
                [resource.Name],
                async _ =>
                {
                    await PublishStateAsync(notifications, resource, KnownResourceStates.Exited, 42);
                    throw new TimeoutException("readiness timed out");
                },
                DelayedEventsAsync,
                TestContext.Current.CancellationToken));

        Assert.Equal("Declared Aspire resource 'eventstore' entered terminal failure state 'Exited' (exit code: 42) during topology startup.",
            failure.Message);
    }

    /// <summary>Initialization cancels each readiness wait and releases every initialized owner.</summary>
    /// <param name="stage">The readiness wait in progress when another declared resource crashes.</param>
    [Theory]
    [InlineData("Running")]
    [InlineData("Endpoint")]
    [InlineData("Aliveness")]
    [InlineData("Readiness")]
    public async Task FailedInitializationCancelsReadinessAndDisposesAllOwners(string stage)
    {
        var resource = new TestResource("eventstore");
        var crashed = new TestResource("tenants");
        var timeout = TimeSpan.FromSeconds(15);
        AspireResource[] resources =
        [
            new(resource.Name, "http", timeout, timeout, stage == "Aliveness", timeout),
            new(crashed.Name, "http", timeout, timeout, false, timeout),
        ];
        var readyEntered = new TaskCompletionSource(TaskCreationOptions.RunContinuationsAsynchronously);
        using var limit = CancellationTokenSource.CreateLinkedTokenSource(TestContext.Current.CancellationToken);
        limit.CancelAfter(TimeSpan.FromSeconds(5));
        CancellationToken readinessToken = default;
        async Task WaitAsync(CancellationToken token)
        {
            readinessToken = token;
            readyEntered.SetResult();
            await Task.Delay(Timeout.InfiniteTimeSpan, token);
        }
        await using var fixture = new LifecycleTestFixture(resources, WaitAsync);

        int appDisposals = 0;
        IDistributedApplicationBuilder appBuilder = DistributedApplication.CreateBuilder(
            new DistributedApplicationOptions { DisableDashboard = true });
        appBuilder.AddResource(resource);
        appBuilder.AddResource(crashed);
        appBuilder.Services.AddSingleton(_ => new NativeCatalogTestDisposable(() =>
        {
            appDisposals++;
            return ValueTask.CompletedTask;
        }));
        DistributedApplication application = appBuilder.Build();
        _ = application.Services.GetRequiredService<NativeCatalogTestDisposable>();
        UrlSnapshot[] urls = [new UrlSnapshot("http", "http://127.0.0.1:1", false)];
        await PublishStateAsync(application.ResourceNotifications, resource,
            stage == "Running" ? KnownResourceStates.Starting : KnownResourceStates.Running,
            urls: stage is "Running" or "Endpoint" ? null : urls);
        await PublishStateAsync(application.ResourceNotifications, crashed, KnownResourceStates.Running, urls: urls);
        var builder = Substitute.For<IDistributedApplicationTestingBuilder>();
        builder.BuildAsync(Arg.Any<CancellationToken>()).Returns(application);
        using var handler = new LivenessHandler(cancelFirst: false, WaitAsync);
        using var client = new HttpClient(handler);
        using var secondClient = new HttpClient();
        var createdClients = new List<HttpClient>();
        DirectoryInfo directory = Directory.CreateTempSubdirectory();
        string lockPath = Path.Combine(directory.FullName, "fixture.lock");
        try
        {
            Task startup = fixture.InitializeAsync(
                (_, _) => Task.FromResult(builder),
                (_, _) => Task.CompletedTask,
                (_, registered) =>
                {
                    HttpClient selected = registered.Name == resource.Name ? client : secondClient;
                    createdClients.Add(selected);
                    return selected;
                },
                lockPath,
                limit.Token).AsTask();

            try
            {
                if (stage is "Aliveness" or "Readiness")
                {
                    await readyEntered.Task.WaitAsync(limit.Token);
                    Assert.Equal(2, createdClients.Count);
                }
                else
                {
                    Assert.Empty(createdClients);
                    Assert.False(startup.IsCompleted);
                }
                await PublishStateAsync(application.ResourceNotifications, crashed, KnownResourceStates.Exited, 42);

                InvalidOperationException failure = await Assert.ThrowsAsync<InvalidOperationException>(() => startup);
                Assert.Equal("Declared Aspire resource 'tenants' entered terminal failure state 'Exited' (exit code: 42) during topology startup.",
                    failure.Message);
                if (stage is "Aliveness" or "Readiness")
                {
                    Assert.True(readinessToken.IsCancellationRequested);
                }
                Assert.False(limit.IsCancellationRequested);
                Assert.Equal(1, appDisposals);
                await builder.Received(1).DisposeAsync();
                foreach (HttpClient owned in createdClients)
                {
                    Assert.Throws<ObjectDisposedException>(() => { _ = owned.GetAsync("/alive", limit.Token); });
                }
                using FileStream reopened = File.Open(lockPath, FileMode.Open, FileAccess.ReadWrite, FileShare.None);
            }
            finally
            {
                await limit.CancelAsync();
                await Task.WhenAny(startup);
            }
        }
        finally
        {
            directory.Delete(recursive: true);
        }
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

    /// <summary>Non-terminal operation exceptions propagate unchanged when no watched resource failed.</summary>
    [Fact]
    public async Task NonTerminalOperationExceptionPropagatesWhenNoResourceFailed()
    {
        using var lifetime = new TestHostApplicationLifetime();
        using var notifications = CreateNotifications(lifetime);
        var resource = new TestResource("eventstore");
        await PublishStateAsync(notifications, resource, KnownResourceStates.Running);

        var expected = new InvalidDataException("non-terminal failure");
        InvalidDataException actual = await Assert.ThrowsAsync<InvalidDataException>(() =>
            IsolatedTopologyLifecycle<object>.RunWithTerminalFailureWatchAsync(
                notifications,
                [resource.Name],
                _ => Task.FromException(expected),
                TestContext.Current.CancellationToken));
        Assert.Same(expected, actual);
    }

    /// <summary>Outer cancellation or timeout propagates as OperationCanceledException when no resource failed.</summary>
    [Fact]
    public async Task TimeoutCancellationPropagatesWhenNoResourceFailed()
    {
        using var lifetime = new TestHostApplicationLifetime();
        using var notifications = CreateNotifications(lifetime);
        var resource = new TestResource("eventstore");
        await PublishStateAsync(notifications, resource, KnownResourceStates.Starting);

        using var budget = new CancellationTokenSource(TimeSpan.FromMilliseconds(75));
        await Assert.ThrowsAnyAsync<OperationCanceledException>(() =>
            IsolatedTopologyLifecycle<object>.RunWithTerminalFailureWatchAsync(
                notifications,
                [resource.Name],
                token => Task.Delay(TimeSpan.FromMinutes(2), token),
                budget.Token));
    }

    /// <summary>Missing state and exit code format explicitly as Unknown and none.</summary>
    [Fact]
    public void CreateTerminalFailureExceptionHandlesNullStateAndExitCode()
    {
        var snapshot = new CustomResourceSnapshot
        {
            ResourceType = "Project",
            State = null,
            ExitCode = null,
            Urls = ImmutableArray<UrlSnapshot>.Empty,
            Properties = ImmutableArray<ResourcePropertySnapshot>.Empty,
        };
        InvalidOperationException failure = IsolatedTopologyLifecycle<object>.CreateTerminalFailureException("eventstore", snapshot);
        Assert.Contains("eventstore", failure.Message, StringComparison.Ordinal);
        Assert.Contains("Unknown", failure.Message, StringComparison.Ordinal);
        Assert.Contains("exit code: none", failure.Message, StringComparison.Ordinal);
    }

    /// <summary>IsTerminalFailureState rejects null, whitespace, and non-terminal states while matching case-insensitively.</summary>
    /// <param name="state">The candidate Aspire state text.</param>
    /// <param name="expected">Whether the state should trigger terminal-failure abort.</param>
    [Theory]
    [InlineData(null, false)]
    [InlineData("", false)]
    [InlineData("   ", false)]
    [InlineData("Running", false)]
    [InlineData("Starting", false)]
    [InlineData("NotStarted", false)]
    [InlineData("failedtostart", true)]
    [InlineData("EXITED", true)]
    [InlineData("Finished", true)]
    [InlineData("runtimeunhealthy", true)]
    public void IsTerminalFailureStateMatchesOnlyDeclaredTerminalStates(string? state, bool expected)
        => Assert.Equal(expected, IsolatedTopologyLifecycle<object>.IsTerminalFailureState(state));

    /// <summary>An empty watched resource list runs the operation directly without watching.</summary>
    [Fact]
    public async Task EmptyWatchedResourcesRunsOperationDirectly()
    {
        using var lifetime = new TestHostApplicationLifetime();
        using var notifications = CreateNotifications(lifetime);
        bool ran = false;
        await IsolatedTopologyLifecycle<object>.RunWithTerminalFailureWatchAsync(
            notifications,
            [],
            _ =>
            {
                ran = true;
                return Task.CompletedTask;
            },
            TestContext.Current.CancellationToken);
        Assert.True(ran);
    }

    /// <summary>An unexpected watcher fault cancels the in-flight operation and propagates the watcher error.</summary>
    [Fact]
    public async Task UnexpectedWatcherFaultCancelsOperationAndPropagates()
    {
        using var lifetime = new TestHostApplicationLifetime();
        using var notifications = CreateNotifications(lifetime);
        var expected = new InvalidProgramException("watcher stream faulted");
        var elapsed = Stopwatch.StartNew();

        InvalidProgramException actual = await Assert.ThrowsAsync<InvalidProgramException>(() =>
            IsolatedTopologyLifecycle<object>.RunWithTerminalFailureWatchAsync(
                notifications,
                ["eventstore"],
                token => Task.Delay(TimeSpan.FromMinutes(2), token),
                _ => FaultingStreamAsync(expected),
                TestContext.Current.CancellationToken));
        elapsed.Stop();
        Assert.Same(expected, actual);
        Assert.True(elapsed.Elapsed < TimeSpan.FromSeconds(10), $"Expected immediate abort on watcher fault, took {elapsed.Elapsed}.");
    }

    /// <summary>A watcher fault does not mask a non-cancellation exception already thrown by the operation.</summary>
    [Fact]
    public async Task WatcherFaultDoesNotMaskOperationException()
    {
        using var lifetime = new TestHostApplicationLifetime();
        using var notifications = CreateNotifications(lifetime);
        var operationError = new InvalidDataException("operation error");
        var watcherError = new InvalidProgramException("watcher error");

        InvalidDataException actual = await Assert.ThrowsAsync<InvalidDataException>(() =>
            IsolatedTopologyLifecycle<object>.RunWithTerminalFailureWatchAsync(
                notifications,
                ["eventstore"],
                _ => Task.FromException(operationError),
                _ => FaultingStreamAsync(watcherError),
                TestContext.Current.CancellationToken));
        Assert.Same(operationError, actual);
    }

    private static async IAsyncEnumerable<ResourceEvent> FaultingStreamAsync(Exception failure)
    {
        await Task.Yield();
        throw failure;
#pragma warning disable CS0162
        yield break;
#pragma warning restore CS0162
    }

    private static async IAsyncEnumerable<ResourceEvent> DelayedEventsAsync(
        [System.Runtime.CompilerServices.EnumeratorCancellation] CancellationToken cancellationToken)
    {
        await Task.Delay(Timeout.InfiniteTimeSpan, cancellationToken);
        yield break;
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
