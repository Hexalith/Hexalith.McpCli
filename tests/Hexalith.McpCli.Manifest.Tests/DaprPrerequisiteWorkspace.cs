using System.Diagnostics;

namespace Hexalith.McpCli.Manifest.Tests;

/// <summary>Provides one disposable source workspace per prerequisite-test process without real module checkouts.</summary>
public sealed class DaprPrerequisiteWorkspace : IDisposable
{
    /// <summary>Builds declared, Git-initialized stand-ins and copies the integration output into their workspace.</summary>
    public DaprPrerequisiteWorkspace()
    {
        string repository = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", ".."));
        string configuration = new DirectoryInfo(AppContext.BaseDirectory).Parent!.Name;
        string source = Path.Combine(repository, "tests", "Hexalith.McpCli.Integration.Tests", "bin", configuration, "net10.0");
        string target = Path.Combine(Root, "tests", "Hexalith.McpCli.Integration.Tests", "bin", configuration, "net10.0");
        Directory.CreateDirectory(Path.Combine(Root, "src"));
        try
        {
            foreach (string file in Directory.EnumerateFiles(source, "*", SearchOption.AllDirectories))
            {
                string destination = Path.Combine(target, Path.GetRelativePath(source, file));
                Directory.CreateDirectory(Path.GetDirectoryName(destination)!);
                File.Copy(file, destination);
            }

            string[] modules = ["Hexalith.EventStore", "Hexalith.Tenants", "Hexalith.Parties"];
            File.WriteAllText(Path.Combine(Root, ".gitmodules"), string.Join('\n', modules.Select(module =>
                $"[submodule \"{module}\"]\n path = references/{module}")));
            foreach (string module in modules)
            {
                string checkout = Path.Combine(Root, "references", module);
                string directory = Path.Combine(checkout, "src", module);
                Directory.CreateDirectory(directory);
                File.WriteAllText(Path.Combine(directory, module + ".csproj"), "<Project />");
                var start = new ProcessStartInfo("git") { RedirectStandardOutput = true, RedirectStandardError = true };
                foreach (string argument in new[] { "init", "--quiet", checkout }) start.ArgumentList.Add(argument);
                using Process git = Process.Start(start)!;
                if (!git.WaitForExit(10000))
                {
                    git.Kill(entireProcessTree: true);
                    throw new TimeoutException("Preparing the prerequisite workspace exceeded 10 seconds.");
                }

                Assert.Equal(0, git.ExitCode);
            }

            Assembly = Path.Combine(target, "Hexalith.McpCli.Integration.Tests.dll");
        }
        catch
        {
            Directory.Delete(Root, recursive: true);
            throw;
        }
    }

    /// <summary>The independent root used by the real integration fixture in each child process.</summary>
    public string Root { get; } = Path.Combine(Path.GetTempPath(), "mcpcli-prerequisites-" + Guid.NewGuid().ToString("N"));

    /// <summary>The copied integration assembly whose base directory resolves to the independent root.</summary>
    public string Assembly { get; }

    /// <inheritdoc/>
    public void Dispose() => Directory.Delete(Root, recursive: true);
}
