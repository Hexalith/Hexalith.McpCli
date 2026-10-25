using System.Text.Json;

using Hexalith.EventStore.Aspire;

namespace Hexalith.McpCli.Integration.Tests;

/// <summary>Exposes every approved Operation as a separately selectable live semantic case.</summary>
[Collection("AspireTopology")]
[Trait("Category", "Integration")]
public sealed class LiveVectorTests(AspireTopologyFixture fixture)
{
    /// <summary>Discovers all companion plans without requiring a running topology.</summary>
    public static IEnumerable<TheoryDataRow<string>> Operations()
    {
        string plans = Path.Combine(RepositoryProjectPaths.GetRepositoryRoot(), "tools", "live-topology", "plans");
        foreach (string path in Directory.EnumerateFiles(plans, "*.json").Order(StringComparer.Ordinal))
        {
            using JsonDocument document = JsonDocument.Parse(File.ReadAllText(path));
            string operation = document.RootElement.GetProperty("operation").GetString()!;
            yield return new TheoryDataRow<string>(operation)
            {
                Traits = new Dictionary<string, HashSet<string>> { ["Operation"] = [operation] },
            };
        }
    }

    /// <summary>Submits the selected vector once after proving persisted bootstrap authority.</summary>
    /// <param name="operation">The canonical approved Operation selected by the isolated parent.</param>
    [Theory]
    [MemberData(nameof(Operations))]
    public async Task ApprovedVectorHasPersistentSemantics(string operation)
    {
        LiveVectorSelection.Require(operation, Environment.GetEnvironmentVariable("MCPCLI_LIVE_OPERATION"),
            Environment.GetCommandLineArgs(), typeof(LiveVectorTests).FullName!);
        fixture.SkipIfUnavailable();
        await fixture.RequireAdministratorAuthorityAsync(TestContext.Current.CancellationToken).ConfigureAwait(true);
        await fixture.RequireProjectionWriterAsync(TestContext.Current.CancellationToken).ConfigureAwait(true);
        await LiveVectorProcess.RunAsync(RepositoryProjectPaths.GetRepositoryRoot(), operation,
            RequiredEnvironment("MCPCLI_LIVE_OUTPUT"), RequiredEnvironment("MCPCLI_LIVE_HOST"),
            RequiredEnvironment("MCPCLI_LIVE_BINDING"), fixture.GatewayEndpoint, fixture.CreateLiveIdentity(),
            TestContext.Current.CancellationToken).ConfigureAwait(true);
    }
    private static string RequiredEnvironment(string name)
        => Environment.GetEnvironmentVariable(name)
            ?? throw new InvalidOperationException($"{name} must be supplied by the isolated parent.");
}
