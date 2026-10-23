using System.Diagnostics;
using System.Xml.Linq;

namespace Hexalith.McpCli.Manifest.Tests;

/// <summary>Executes missing-helper and forbidden-helper admission failures without a live topology.</summary>
public sealed class AspireHelperDependencyTests
{
    private const string Helper = "Hexalith.Parties.Aspire";

    /// <summary>Missing published artifacts fail by package identity and never fall back to source.</summary>
    [Fact]
    public void MissingHelperHasAnExactDiagnostic()
    {
        var (policy, graph) = Candidate();
        var nodes = new Dictionary<string, RestoredDependencyNode>(graph.Nodes, StringComparer.OrdinalIgnoreCase);
        nodes.Remove(Helper);
        Assert.Equal([$"Required helper {Helper}/1.0.0 is missing from restore."],
            DependencyPolicyGate.CheckAspireHelperClosure(policy, graph with { Nodes = nodes }, [Helper]));
    }

    /// <summary>Unreviewed roots cannot use a helper-shaped name to enter tests.</summary>
    [Fact]
    public void UnreviewedHelperIsRejected()
    {
        var (policy, graph) = Candidate();
        policy.TestPackages.Clear();
        Assert.Equal([$"Helper {Helper} is not approved for tests."], DependencyPolicyGate.CheckAspireHelperClosure(policy, graph, [Helper]));
    }

    /// <summary>A source project cannot substitute for the required published artifact.</summary>
    [Fact]
    public void SourceHelperIsRejected()
    {
        var (policy, graph) = Candidate();
        var nodes = new Dictionary<string, RestoredDependencyNode>(graph.Nodes, StringComparer.OrdinalIgnoreCase);
        nodes[Helper] = nodes[Helper] with { Type = "project", ProjectPath = "/source/helper.csproj" };
        Assert.Equal([$"Required helper {Helper}/1.0.0 must be a published package; source project helpers are forbidden."],
            DependencyPolicyGate.CheckAspireHelperClosure(policy, graph with { Nodes = nodes }, [Helper]));
    }

    /// <summary>Both domain implementations and platform server packages are forbidden in helper closures.</summary>
    [Theory]
    [InlineData("Hexalith.Parties.Server")]
    [InlineData("Hexalith.Parties.Client")]
    [InlineData("Hexalith.Parties.Projections")]
    [InlineData("Hexalith.EventStore.Server")]
    public void HelperWithImplementationDependencyIsRejected(string dependency)
    {
        var (policy, graph) = Candidate();
        var nodes = new Dictionary<string, RestoredDependencyNode>(graph.Nodes, StringComparer.OrdinalIgnoreCase);
        nodes[Helper] = nodes[Helper] with { Dependencies = new Dictionary<string, string> { [dependency] = "2.0.0" } };
        nodes[dependency] = new(dependency, "2.0.0", "package", new Dictionary<string, string>(), []);
        Assert.Equal([$"Helper {Helper}/1.0.0 has a forbidden dependency {dependency}/2.0.0: Topology > {Helper}/1.0.0 > {dependency}/2.0.0"],
            DependencyPolicyGate.CheckAspireHelperClosure(policy, graph with { Nodes = nodes }, [Helper]));
    }

    /// <summary>The actual NuGet client fails closed when the helper artifact is unavailable.</summary>
    [Fact]
    public async Task MissingHelperRestoreCannotFallBackToWorkspaceOrGlobalPackages()
    {
        string root = Path.Combine(Path.GetTempPath(), "mcpcli-missing-helper-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(Path.Combine(root, "empty"));
        try
        {
            File.WriteAllText(Path.Combine(root, "Missing.csproj"), $"<Project Sdk=\"Microsoft.NET.Sdk\"><PropertyGroup><TargetFramework>net10.0</TargetFramework></PropertyGroup><ItemGroup><PackageReference Include=\"{Helper}\" Version=\"0.0.0-missing-fixture\" /></ItemGroup></Project>");
            new XDocument(new XElement("configuration", new XElement("packageSources", new XElement("clear"),
                new XElement("add", new XAttribute("key", "empty"), new XAttribute("value", Path.Combine(root, "empty"))))))
                .Save(Path.Combine(root, "NuGet.Config"));
            var start = new ProcessStartInfo("dotnet")
            {
                WorkingDirectory = root, RedirectStandardOutput = true, RedirectStandardError = true,
            };
            foreach (string argument in new[] { "restore", "Missing.csproj", "--configfile", "NuGet.Config", "--packages", Path.Combine(root, "packages"), "-p:RestoreFallbackFolders=" })
                start.ArgumentList.Add(argument);
            using Process process = Process.Start(start)!;
            using var timeout = CancellationTokenSource.CreateLinkedTokenSource(TestContext.Current.CancellationToken);
            timeout.CancelAfter(TimeSpan.FromSeconds(30));
            Task<string> output = process.StandardOutput.ReadToEndAsync(timeout.Token);
            Task<string> error = process.StandardError.ReadToEndAsync(timeout.Token);
            try { await process.WaitForExitAsync(timeout.Token).ConfigureAwait(true); }
            finally { if (!process.HasExited) process.Kill(entireProcessTree: true); }
            Assert.Equal(1, process.ExitCode);
            Assert.Contains($"error NU1101: Unable to find package {Helper}. No packages exist with this id in source(s): empty", await output.ConfigureAwait(true));
            Assert.Equal(string.Empty, await error.ConfigureAwait(true));
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    private static (DependencyPolicy Policy, RestoredDependencyGraph Graph) Candidate()
    {
        var policy = new DependencyPolicy { TestPackages = new(StringComparer.OrdinalIgnoreCase) { Helper } };
        var nodes = new Dictionary<string, RestoredDependencyNode>(StringComparer.OrdinalIgnoreCase)
        {
            ["Topology"] = new("Topology", "", "project", new Dictionary<string, string> { [Helper] = "1.0.0" }, []),
            [Helper] = new(Helper, "1.0.0", "package", new Dictionary<string, string>(), []),
        };
        return (policy, new("Topology", nodes, []));
    }
}
