using Hexalith.McpCli.Integration.Tests;

namespace Hexalith.McpCli.Manifest.Tests;

/// <summary>Protects retained Docker health and deadline behavior without connecting to a daemon.</summary>
[Collection("TopologyFixtureEnvironment")]
public sealed class TopologyDockerPrerequisiteTests
{
    /// <summary>A real controlled process proves successful, nonzero and hung probe outcomes.</summary>
    [Theory]
    [InlineData(0, 0, true)]
    [InlineData(7, 0, false)]
    [InlineData(0, 10000, false)]
    public async Task DockerHealthProbeRetainsExitAndDeadlineRefusals(int exit, int delay, bool expected)
    {
        string root = DependencyPolicyTests.FindRepositoryRoot();
        string configuration = new DirectoryInfo(AppContext.BaseDirectory).Parent!.Name;
        string executable = Path.Combine(root, "tests", "fixtures", "Topology.DaprStub", "bin", configuration, "net10.0",
            OperatingSystem.IsWindows() ? "dapr.exe" : "dapr");
        string? priorExit = Environment.GetEnvironmentVariable("MCPCLI_TEST_DAPR_VERSION_EXIT");
        string? priorDelay = Environment.GetEnvironmentVariable("MCPCLI_TEST_DAPR_DELAY_MS");
        try
        {
            Environment.SetEnvironmentVariable("MCPCLI_TEST_DAPR_VERSION_EXIT", exit.ToString(System.Globalization.CultureInfo.InvariantCulture));
            Environment.SetEnvironmentVariable("MCPCLI_TEST_DAPR_DELAY_MS", delay.ToString(System.Globalization.CultureInfo.InvariantCulture));
            Assert.Equal(expected, await TopologyPrerequisites.IsDockerHealthyAsync(executable));
        }
        finally
        {
            Environment.SetEnvironmentVariable("MCPCLI_TEST_DAPR_VERSION_EXIT", priorExit);
            Environment.SetEnvironmentVariable("MCPCLI_TEST_DAPR_DELAY_MS", priorDelay);
        }
    }
}
