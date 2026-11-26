using System.Diagnostics;
using System.Security.Cryptography;
using System.Text.Json;

using Aspire.Hosting;
using Aspire.Hosting.ApplicationModel;

using Hexalith.EventStore.Aspire;

namespace Hexalith.McpCli.AppHost;

/// <summary>Resolves exact separately built source fixtures without changing their declared root identities.</summary>
internal static class NativeSourceFixtures
{
    /// <summary>The approved native lane always consumes already built resource outputs.</summary>
    internal static bool Enabled => TopologyConfiguration.NativeLaneEnabled;

    /// <summary>Requires a sealed private copy of the exact qualified domain source before selecting its project.</summary>
    internal static string ModuleRoot(string repositoryRoot, string module)
    {
        if (!Enabled) return Path.Combine(repositoryRoot, "references", module);
        if (module is not ("Hexalith.Tenants" or "Hexalith.Parties" or "Hexalith.Projects"))
            throw new InvalidDataException("Only the qualified domain source fixtures may use the private path contract.");
        string receipt = Environment.GetEnvironmentVariable("MCPCLI_NATIVE_SOURCE_FIXTURES")
            ?? throw new InvalidDataException("The native lane requires its private source fixture receipt.");
        string digest = Environment.GetEnvironmentVariable("MCPCLI_NATIVE_SOURCE_FIXTURES_SHA256")
            ?? throw new InvalidDataException("The native lane requires the prepared source fixture hash.");
        return RequireModule(repositoryRoot, module, receipt, digest);
    }

    /// <summary>Authenticates actual source/output bytes and rejects an in-place or linked fixture.</summary>
    internal static string RequireModule(string repositoryRoot, string module, string receipt, string digest)
    {
        byte[] bytes = File.ReadAllBytes(receipt);
        if (Convert.ToHexStringLower(SHA256.HashData(bytes)) != digest)
            throw new InvalidDataException("The private source fixture receipt changed after preparation.");
        using JsonDocument document = JsonDocument.Parse(bytes, new JsonDocumentOptions { AllowDuplicateProperties = false });
        JsonElement proof = document.RootElement;
        if (proof.GetProperty("schemaVersion").GetInt32() != 1 || proof.GetProperty("result").GetString() != "prepared")
            throw new InvalidDataException("The private source fixture preparation is incomplete.");
        JsonElement entry = proof.GetProperty("modules").GetProperty(module);
        string path = entry.GetProperty("path").GetString()!;
        string original = Path.GetFullPath(repositoryRoot) + Path.DirectorySeparatorChar;
        if (!Path.IsPathFullyQualified(path) || Path.GetFullPath(path).StartsWith(original, StringComparison.Ordinal)
            || !Directory.Exists(Path.Combine(path, ".git")) || new DirectoryInfo(path).LinkTarget is not null
            || Directory.Exists(Path.Combine(path, "references", "Hexalith.Builds", ".git"))
            || File.Exists(Path.Combine(path, "references", "Hexalith.Builds", ".git")))
            throw new InvalidDataException("Native source fixtures require private direct Git copies with nested Builds uninitialized.");
        using JsonDocument selection = JsonDocument.Parse(File.ReadAllBytes(Path.Combine(repositoryRoot, "tools", "live-topology", "native-runtime-current.json")));
        string expectedCommit = selection.RootElement.GetProperty("sources").GetProperty(module).GetProperty("commit").GetString()!;
        if (proof.GetProperty("selection").GetProperty(module).GetString() != expectedCommit
            || entry.GetProperty("commit").GetString() != expectedCommit
            || Git(path, "rev-parse", "HEAD") != expectedCommit
            || Git(path, "status", "--porcelain", "--untracked-files=normal", "--ignore-submodules=all") != "")
            throw new InvalidDataException("The private source fixture changed its qualified source identity.");
        for (DirectoryInfo? parent = new(path); parent is not null; parent = parent.Parent)
            if (parent.LinkTarget is not null) throw new InvalidDataException("A native source fixture traverses a directory link.");
        JsonElement files = entry.GetProperty("files");
        if (!files.EnumerateObject().Any()) throw new InvalidDataException("The private source fixture has no sealed files.");
        foreach (JsonProperty file in files.EnumerateObject())
        {
            string selected = Path.GetFullPath(Path.Combine(path, file.Name));
            if (!selected.StartsWith(Path.GetFullPath(path) + Path.DirectorySeparatorChar, StringComparison.Ordinal)
                || new FileInfo(selected).LinkTarget is not null
                || file.Value.GetString() != Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(selected))))
                throw new InvalidDataException("Private source fixture bytes changed: " + file.Name + ".");
        }
        return path;
    }

    private static string Git(string path, params string[] arguments)
    {
        var start = new ProcessStartInfo("git") { RedirectStandardOutput = true, RedirectStandardError = true };
        foreach (string argument in new[] { "-C", path }.Concat(arguments)) start.ArgumentList.Add(argument);
        using Process child = Process.Start(start) ?? throw new InvalidDataException("Cannot verify the private source fixture Git identity.");
        Task<string> output = child.StandardOutput.ReadToEndAsync();
        Task<string> error = child.StandardError.ReadToEndAsync();
        if (!child.WaitForExit(10000))
        {
            child.Kill(entireProcessTree: true);
            child.WaitForExit();
            throw new TimeoutException("Private source fixture Git verification exceeded 10 seconds.");
        }
        string actual = output.GetAwaiter().GetResult().Trim();
        _ = error.GetAwaiter().GetResult();
        return child.ExitCode == 0 ? actual : throw new InvalidDataException("Cannot verify the private source fixture Git identity.");
    }

    internal static string Project(string module) => module == "Hexalith.Projects"
        ? Path.Combine(ModuleRoot(RepositoryProjectPaths.GetRepositoryRoot(), module), "src", "Hexalith.Projects.Server",
            "Hexalith.Projects.Server.csproj")
        : Path.Combine(ModuleRoot(RepositoryProjectPaths.GetRepositoryRoot(), module), "src", module, module + ".csproj");
}

/// <summary>Uses the already built package Gateway from the main module build.</summary>
internal sealed class PreparedGatewayProject : IProjectMetadata
{
    public string ProjectPath => TopologyConfiguration.ResolveGatewayProject(RepositoryProjectPaths.GetRepositoryRoot(), true, false);
    public bool SuppressBuild => true;
}

/// <summary>Uses only the separately built, sealed Tenants fixture.</summary>
internal sealed class PreparedTenantsProject : IProjectMetadata
{
    public string ProjectPath => NativeSourceFixtures.Project("Hexalith.Tenants");
    public bool SuppressBuild => true;
}

/// <summary>Uses only the separately built, sealed Parties fixture.</summary>
internal sealed class PreparedPartiesProject : IProjectMetadata
{
    public string ProjectPath => NativeSourceFixtures.Project("Hexalith.Parties");
    public bool SuppressBuild => true;
}

/// <summary>Uses only the separately built, sealed Projects fixture.</summary>
internal sealed class PreparedProjectsProject : IProjectMetadata
{
    public string ProjectPath => NativeSourceFixtures.Project("Hexalith.Projects");
    public bool SuppressBuild => true;
}
