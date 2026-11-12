namespace Hexalith.McpCli.Integration.Tests;

/// <summary>Declares one discovered resource and its bounded fixture liveness probes.</summary>
/// <param name="Name">The exact resource name.</param>
/// <param name="EndpointName">The named endpoint to discover.</param>
/// <param name="ClientTimeout">The per-request client deadline.</param>
/// <param name="ReadinessTimeout">The resource and endpoint discovery deadline.</param>
/// <param name="WaitForAliveness">Whether the fixture must observe a successful liveness response.</param>
/// <param name="AlivenessTimeout">The enclosing liveness deadline.</param>
public sealed record AspireResource(string Name, string EndpointName, TimeSpan ClientTimeout,
    TimeSpan ReadinessTimeout, bool WaitForAliveness, TimeSpan AlivenessTimeout);
