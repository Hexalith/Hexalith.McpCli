using System.Globalization;
using System.Net;
using System.Runtime.ExceptionServices;

using Aspire.Hosting;
using Aspire.Hosting.ApplicationModel;
using Aspire.Hosting.Testing;

using Hexalith.EventStore.Testing.Integration;

namespace Hexalith.McpCli.Integration.Tests;

/// <summary>Owns only the AppHost inside the already authenticated isolated wrapper.</summary>
/// <remarks>The current SDK fixture consumes a Platform descriptor and never owns infrastructure.
/// This suite instead retains its existing isolated AppHost lifecycle through Aspire's public API.</remarks>
public abstract class IsolatedTopologyLifecycle<TAppHost> : IAsyncLifetime where TAppHost : class
{
    private static readonly HashSet<string> TerminalFailureStates = new(StringComparer.OrdinalIgnoreCase)
    {
        KnownResourceStates.FailedToStart,
        KnownResourceStates.Exited,
        KnownResourceStates.Finished,
        KnownResourceStates.RuntimeUnhealthy,
    };

    private DistributedApplication? _application;
    private IDistributedApplicationTestingBuilder? _builder;
    private FileStream? _fixtureLock;
    private readonly Dictionary<string, HttpClient> _clients = new(StringComparer.Ordinal);

    /// <summary>The explicitly declared resources.</summary>
    protected abstract IReadOnlyList<AspireResource> Resources { get; }

    /// <summary>Arguments selected by the owning fixture before AppHost evaluation.</summary>
    protected abstract IReadOnlyList<string> ExtraAppArgs { get; }

    /// <summary>Checks fixture-specific readiness within the same startup and cleanup boundary.</summary>
    protected virtual Task WaitForReadinessAsync(CancellationToken cancellationToken) => Task.CompletedTask;

    /// <summary>Gets only an initialized, declared Aspire discovery client.</summary>
    protected HttpClient Client(string resourceName) => _clients.TryGetValue(resourceName, out HttpClient? client)
        ? client : throw new InvalidOperationException("The declared isolated topology client is unavailable.");

    /// <inheritdoc/>
    public async ValueTask InitializeAsync()
    {
        using var startup = new CancellationTokenSource(TimeSpan.FromMinutes(6));
        try
        {
            // Serialize the owned AppHost lifecycle, with the same outer startup deadline.
            string lockPath = Path.Combine(Path.GetTempPath(), "hexalith-dapr-test-fixture.lock");
            while (_fixtureLock is null)
            {
                startup.Token.ThrowIfCancellationRequested();
                try { _fixtureLock = new FileStream(lockPath, FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None); }
                catch (IOException) { await Task.Delay(250, startup.Token).ConfigureAwait(false); }
            }
            string[] arguments = [.. ExtraAppArgs,
                $"--Dapr:PlacementHostAddress=localhost:{DaprLocalEndpoints.PlacementPort}",
                $"--Dapr:SchedulerHostAddress=localhost:{DaprLocalEndpoints.SchedulerPort}"];
            _builder = await DistributedApplicationTestingBuilder.CreateAsync<TAppHost>(arguments, startup.Token).ConfigureAwait(false);
            _application = await _builder.BuildAsync(startup.Token).ConfigureAwait(false);
            await _application.StartAsync(startup.Token).ConfigureAwait(false);
            IReadOnlyList<AspireResource> resources = Resources;
            string[] watchedResources = [.. resources.Select(resource => resource.Name)];
            await RunWithTerminalFailureWatchAsync(
                _application.ResourceNotifications,
                watchedResources,
                async watchedToken =>
                {
                    foreach (AspireResource resource in resources)
                    {
                        using var ready = CancellationTokenSource.CreateLinkedTokenSource(watchedToken);
                        ready.CancelAfter(resource.ReadinessTimeout);
                        await _application.ResourceNotifications.WaitForResourceAsync(resource.Name, KnownResourceStates.Running, ready.Token).ConfigureAwait(false);
                        string endpoint = await WaitForEndpointCoreAsync(_application.ResourceNotifications, resource.Name, resource.EndpointName, ready.Token).ConfigureAwait(false);
                        HttpClient client = _application.CreateHttpClient(resource.Name, resource.EndpointName);
                        client.BaseAddress ??= new Uri(endpoint);
                        client.Timeout = resource.ClientTimeout;
                        _clients.Add(resource.Name, client);
                    }
                    foreach (AspireResource resource in resources.Where(resource => resource.WaitForAliveness))
                    {
                        await WaitForAlivenessAsync(Client(resource.Name), resource.AlivenessTimeout, watchedToken).ConfigureAwait(false);
                    }

                    await WaitForReadinessAsync(watchedToken).ConfigureAwait(false);
                },
                startup.Token).ConfigureAwait(false);
        }
        catch (Exception failure)
        {
            await CleanupAsync(failure).ConfigureAwait(false);
            throw;
        }
    }

    /// <summary>Determines whether an Aspire resource state indicates a terminal startup failure.</summary>
    internal static bool IsTerminalFailureState(string? state)
        => !string.IsNullOrWhiteSpace(state) && TerminalFailureStates.Contains(state);

    /// <summary>Formats a diagnostic exception identifying the crashed resource, terminal state, and exit code.</summary>
    internal static InvalidOperationException CreateTerminalFailureException(string resourceName, CustomResourceSnapshot snapshot)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(resourceName);
        ArgumentNullException.ThrowIfNull(snapshot);
        string state = snapshot.State?.Text ?? "Unknown";
        string exitCode = snapshot.ExitCode is int code ? code.ToString(CultureInfo.InvariantCulture) : "none";
        return new InvalidOperationException(
            $"Declared Aspire resource '{resourceName}' entered terminal failure state '{state}' (exit code: {exitCode}) during topology startup.");
    }

    /// <summary>Runs a startup operation while watching only declared resources for terminal failure states.</summary>
    internal static Task RunWithTerminalFailureWatchAsync(
        ResourceNotificationService notifications,
        IEnumerable<string> watchedResources,
        Func<CancellationToken, Task> operation,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(notifications);
        return RunWithTerminalFailureWatchAsync(
            notifications,
            watchedResources,
            operation,
            notifications.WatchAsync,
            cancellationToken);
    }

    /// <summary>Runs a startup operation while watching declared resources via the supplied event stream.</summary>
    internal static async Task RunWithTerminalFailureWatchAsync(
        ResourceNotificationService notifications,
        IEnumerable<string> watchedResources,
        Func<CancellationToken, Task> operation,
        Func<CancellationToken, IAsyncEnumerable<ResourceEvent>> watchEvents,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(notifications);
        ArgumentNullException.ThrowIfNull(watchedResources);
        ArgumentNullException.ThrowIfNull(operation);
        ArgumentNullException.ThrowIfNull(watchEvents);

        var watched = new HashSet<string>(watchedResources, StringComparer.OrdinalIgnoreCase);
        if (watched.Count == 0)
        {
            await operation(cancellationToken).ConfigureAwait(false);
            return;
        }

        foreach (string name in watched)
        {
            if (notifications.TryGetCurrentState(name, out ResourceEvent? current)
                && IsTerminalFailureState(current.Snapshot.State?.Text))
            {
                throw CreateTerminalFailureException(current.Resource.Name, current.Snapshot);
            }
        }

        using var linked = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        using var watchStop = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        InvalidOperationException? terminalFailure = null;
        Exception? watcherFailure = null;

        Task watchTask = Task.Run(async () =>
        {
            try
            {
                await foreach (ResourceEvent resourceEvent in watchEvents(watchStop.Token).ConfigureAwait(false))
                {
                    if (!watched.Contains(resourceEvent.Resource.Name) && !watched.Contains(resourceEvent.ResourceId))
                    {
                        continue;
                    }

                    if (IsTerminalFailureState(resourceEvent.Snapshot.State?.Text))
                    {
                        InvalidOperationException failure = CreateTerminalFailureException(
                            resourceEvent.Resource.Name,
                            resourceEvent.Snapshot);
                        Interlocked.CompareExchange(ref terminalFailure, failure, null);
                        try { await linked.CancelAsync().ConfigureAwait(false); }
                        catch (ObjectDisposedException) { }
                        return;
                    }
                }
            }
            catch (OperationCanceledException) when (watchStop.IsCancellationRequested)
            {
            }
            catch (Exception failure)
            {
                Interlocked.CompareExchange(ref watcherFailure, failure, null);
                try { await linked.CancelAsync().ConfigureAwait(false); }
                catch (ObjectDisposedException) { }
            }
        }, CancellationToken.None);

        Exception? operationFailure = null;
        try
        {
            await operation(linked.Token).ConfigureAwait(false);
        }
        catch (Exception failure)
        {
            operationFailure = failure;
        }
        finally
        {
            await watchStop.CancelAsync().ConfigureAwait(false);
            await watchTask.ConfigureAwait(false);
        }

        if (Volatile.Read(ref terminalFailure) is InvalidOperationException terminal)
        {
            throw terminal;
        }

        if (operationFailure is not null)
        {
            if (operationFailure is OperationCanceledException && !cancellationToken.IsCancellationRequested
                && Volatile.Read(ref watcherFailure) is Exception canceledByWatcher)
            {
                ExceptionDispatchInfo.Capture(canceledByWatcher).Throw();
            }

            ExceptionDispatchInfo.Capture(operationFailure).Throw();
        }

        if (Volatile.Read(ref watcherFailure) is Exception unexpectedWatcherFailure)
        {
            ExceptionDispatchInfo.Capture(unexpectedWatcherFailure).Throw();
        }

        foreach (string name in watched)
        {
            if (notifications.TryGetCurrentState(name, out ResourceEvent? current)
                && IsTerminalFailureState(current.Snapshot.State?.Text))
            {
                throw CreateTerminalFailureException(current.Resource.Name, current.Snapshot);
            }
        }
    }

    /// <summary>Waits for a declared resource to enter Running while aborting on any watched terminal failure.</summary>
    internal static Task WaitForResourceRunningAsync(
        ResourceNotificationService notifications,
        string resourceName,
        IEnumerable<string> watchedResources,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(notifications);
        ArgumentException.ThrowIfNullOrWhiteSpace(resourceName);
        return RunWithTerminalFailureWatchAsync(
            notifications,
            watchedResources,
            token => notifications.WaitForResourceAsync(resourceName, KnownResourceStates.Running, token),
            cancellationToken);
    }

    /// <summary>Waits for a declared resource endpoint URL while aborting on any watched terminal failure.</summary>
    internal static async Task<string> WaitForEndpointAsync(
        ResourceNotificationService notifications,
        string resourceName,
        string endpointName,
        IEnumerable<string> watchedResources,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(notifications);
        ArgumentException.ThrowIfNullOrWhiteSpace(resourceName);
        ArgumentException.ThrowIfNullOrWhiteSpace(endpointName);
        string? endpoint = null;
        await RunWithTerminalFailureWatchAsync(
            notifications,
            watchedResources,
            async token => endpoint = await WaitForEndpointCoreAsync(notifications, resourceName, endpointName, token).ConfigureAwait(false),
            cancellationToken).ConfigureAwait(false);
        return endpoint!;
    }

    private static async Task<string> WaitForEndpointCoreAsync(
        ResourceNotificationService notifications,
        string resourceName,
        string endpointName,
        CancellationToken cancellationToken)
    {
        while (true)
        {
            cancellationToken.ThrowIfCancellationRequested();
            if (notifications.TryGetCurrentState(resourceName, out ResourceEvent? current))
            {
                string? endpoint = current.Snapshot.Urls.FirstOrDefault(url =>
                    string.Equals(url.Name, endpointName, StringComparison.OrdinalIgnoreCase)
                    && !string.IsNullOrWhiteSpace(url.Url))?.Url;
                if (endpoint is not null)
                {
                    return endpoint;
                }
            }

            await Task.Delay(250, cancellationToken).ConfigureAwait(false);
        }
    }

    /// <summary>Retries individual transient requests only within the retained liveness deadline.</summary>
    internal static async Task WaitForAlivenessAsync(HttpClient client, TimeSpan timeout, CancellationToken cancellationToken)
    {
        using var alive = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        alive.CancelAfter(timeout);
        while (true)
        {
            alive.Token.ThrowIfCancellationRequested();
            try
            {
                using HttpResponseMessage response = await client.GetAsync("/alive", alive.Token).ConfigureAwait(false);
                if (response.StatusCode == HttpStatusCode.OK) return;
            }
            catch (HttpRequestException) { }
            catch (TaskCanceledException) when (!alive.IsCancellationRequested) { }
            await Task.Delay(TimeSpan.FromSeconds(2), alive.Token).ConfigureAwait(false);
        }
    }

    /// <inheritdoc/>
    public ValueTask DisposeAsync() => CleanupAsync(null);

    private async ValueTask CleanupAsync(Exception? original)
    {
        DistributedApplication? application = _application;
        IDistributedApplicationTestingBuilder? builder = _builder;
        FileStream? fixtureLock = _fixtureLock;
        Func<ValueTask>[] actions = [.. _clients.Values.Select<HttpClient, Func<ValueTask>>(client => () =>
            { client.Dispose(); return ValueTask.CompletedTask; }),
            () => application?.DisposeAsync() ?? ValueTask.CompletedTask,
            () => builder?.DisposeAsync() ?? ValueTask.CompletedTask,
            () => { fixtureLock?.Dispose(); return ValueTask.CompletedTask; }];
        _clients.Clear();
        _application = null;
        _builder = null;
        _fixtureLock = null;
        await DisposeOwnedAsync(original, actions).ConfigureAwait(false);
    }

    /// <summary>Attempts every independent disposal while retaining the original failure.</summary>
    internal static async ValueTask DisposeOwnedAsync(Exception? original, params Func<ValueTask>[] actions)
    {
        Exception? first = original;
        foreach (Func<ValueTask> action in actions)
        {
            try { await action().ConfigureAwait(false); }
            catch (Exception failure) { first ??= failure; }
        }
        if (original is null && first is not null) ExceptionDispatchInfo.Capture(first).Throw();
    }
}
