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
    private DistributedApplication? _application;
    private IDistributedApplicationTestingBuilder? _builder;
    private FileStream? _fixtureLock;
    private readonly Dictionary<string, HttpClient> _clients = new(StringComparer.Ordinal);

    /// <summary>The explicitly declared resources.</summary>
    protected abstract IReadOnlyList<AspireResource> Resources { get; }

    /// <summary>Arguments selected by the owning fixture before AppHost evaluation.</summary>
    protected abstract IReadOnlyList<string> ExtraAppArgs { get; }

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
            foreach (AspireResource resource in Resources)
            {
                using var ready = CancellationTokenSource.CreateLinkedTokenSource(startup.Token);
                ready.CancelAfter(resource.ReadinessTimeout);
                await _application.ResourceNotifications.WaitForResourceAsync(resource.Name, KnownResourceStates.Running, ready.Token).ConfigureAwait(false);
                string? endpoint = null;
                while (endpoint is null)
                {
                    if (_application.ResourceNotifications.TryGetCurrentState(resource.Name, out ResourceEvent? current))
                        endpoint = current.Snapshot.Urls.FirstOrDefault(url =>
                            string.Equals(url.Name, resource.EndpointName, StringComparison.OrdinalIgnoreCase)
                            && !string.IsNullOrWhiteSpace(url.Url))?.Url;
                    if (endpoint is null) await Task.Delay(250, ready.Token).ConfigureAwait(false);
                }
                HttpClient client = _application.CreateHttpClient(resource.Name, resource.EndpointName);
                client.BaseAddress ??= new Uri(endpoint);
                client.Timeout = resource.ClientTimeout;
                _clients.Add(resource.Name, client);
            }
            foreach (AspireResource resource in Resources.Where(resource => resource.WaitForAliveness))
            {
                await WaitForAlivenessAsync(Client(resource.Name), resource.AlivenessTimeout, startup.Token).ConfigureAwait(false);
            }
        }
        catch (Exception failure)
        {
            await CleanupAsync(failure).ConfigureAwait(false);
            throw;
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
