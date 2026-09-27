using System.Reflection;

namespace Hexalith.McpCli.Hosting;

/// <summary>Loads exactly the generated flagged Contracts assembly manifest.</summary>
internal static class ManifestLoader
{
    internal static IReadOnlyList<Assembly> Load()
        => ModuleAssemblyManifest.Entries
            .Select(entry => Assembly.Load(new AssemblyName(entry.AssemblyName)))
            .ToArray();
}
