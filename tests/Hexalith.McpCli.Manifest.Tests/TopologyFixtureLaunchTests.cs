using System.Diagnostics;

namespace Hexalith.McpCli.Manifest.Tests;

/// <summary>Exercises the actual integration fixture's refusals before infrastructure checks or launch.</summary>
public sealed class TopologyFixtureLaunchTests
{
    /// <summary>Direct execution fails closed, and a missing root source retains its required path.</summary>
    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task UnsafeOrIncompleteFixtureFailsBeforeInfrastructure(bool isolated)
    {
        string root = Path.Combine(Path.GetTempPath(), "mcpcli-fixture-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(Path.Combine(root, "src"));
        string repository = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", ".."));
        string configuration = new DirectoryInfo(AppContext.BaseDirectory).Parent!.Name;
        string source = Path.Combine(repository, "tests", "Hexalith.McpCli.Integration.Tests", "bin", configuration, "net10.0");
        string target = Path.Combine(root, "tests", "Hexalith.McpCli.Integration.Tests", "bin", configuration, "net10.0");
        try
        {
            foreach (string file in Directory.EnumerateFiles(source, "*", SearchOption.AllDirectories))
            {
                string destination = Path.Combine(target, Path.GetRelativePath(source, file));
                Directory.CreateDirectory(Path.GetDirectoryName(destination)!);
                File.Copy(file, destination);
            }
            File.WriteAllText(Path.Combine(root, ".gitmodules"), "[submodule \"Hexalith.EventStore\"]\n path = references/Hexalith.EventStore\n");
            string dotnet = Environment.GetEnvironmentVariable("DOTNET_HOST_PATH")
                ?? Path.GetFullPath(Path.Combine(System.Runtime.InteropServices.RuntimeEnvironment.GetRuntimeDirectory(), "..", "..", "..", OperatingSystem.IsWindows() ? "dotnet.exe" : "dotnet"));
            var start = new ProcessStartInfo(dotnet)
            {
                WorkingDirectory = root, RedirectStandardOutput = true, RedirectStandardError = true,
            };
            start.ArgumentList.Add(Path.Combine(target, "Hexalith.McpCli.Integration.Tests.dll"));
            start.ArgumentList.Add("-method");
            start.ArgumentList.Add("*AuthenticatedQueryReturnsSuccessfulDocument");
            start.Environment["MCPCLI_ISOLATED_TOPOLOGY"] = isolated ? "1" : null;
            start.Environment["PATH"] = Path.Combine(root, "no-infrastructure");
            using Process process = Process.Start(start)!;
            Task<string> stdout = process.StandardOutput.ReadToEndAsync(TestContext.Current.CancellationToken);
            Task<string> stderr = process.StandardError.ReadToEndAsync(TestContext.Current.CancellationToken);
            using var deadline = CancellationTokenSource.CreateLinkedTokenSource(TestContext.Current.CancellationToken);
            deadline.CancelAfter(TimeSpan.FromSeconds(20));
            try { await process.WaitForExitAsync(deadline.Token); }
            finally { if (!process.HasExited) process.Kill(entireProcessTree: true); }
            string output = await stdout;
            Assert.Equal(1, process.ExitCode);
            string error = await stderr;
            string expected = isolated
                ? $"Required root source project '{Path.Combine(root, "references", "Hexalith.EventStore", "src", "Hexalith.EventStore", "Hexalith.EventStore.csproj")}' is missing. Initialize only the declared root checkout 'references/Hexalith.EventStore'."
                : "Live topology tests require tools/live-topology/run-isolated.py; refusing to use host Dapr or Redis.";
            Assert.Equal(string.Empty, error);
            Assert.Contains(expected, output);
            Assert.Contains("Failed: 1, Skipped: 0", output);
            Assert.DoesNotContain("DAPR integration prerequisites are unavailable", output + error);
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }
}
