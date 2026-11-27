using Hexalith.McpCli.Integration.Tests;

namespace Hexalith.McpCli.Manifest.Tests;

/// <summary>Supplies declared resources and an observed readiness operation for offline lifecycle tests.</summary>
internal sealed class LifecycleTestFixture(IReadOnlyList<AspireResource> resources, Func<CancellationToken, Task> readiness)
    : IsolatedTopologyLifecycle<object>
{
    /// <inheritdoc />
    protected override IReadOnlyList<AspireResource> Resources { get; } = resources;

    /// <inheritdoc />
    protected override IReadOnlyList<string> ExtraAppArgs => [];

    /// <inheritdoc />
    protected override Task WaitForReadinessAsync(CancellationToken cancellationToken) => readiness(cancellationToken);
}
