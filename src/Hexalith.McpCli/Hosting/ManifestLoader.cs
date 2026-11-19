using System.Reflection;
using Hexalith.McpCli.Core.Catalog;

namespace Hexalith.McpCli.Hosting;

/// <summary>Loads exactly the generated flagged Contracts assembly manifest.</summary>
internal static class ManifestLoader
{
    /// <summary>Loads each enrolled Contracts assembly after binding host Abstractions.</summary>
    /// <returns>The loaded Contracts assemblies in manifest order.</returns>
    internal static IReadOnlyList<Assembly> Load()
    {
        CatalogAbstractionsResolver.Register();
        return ModuleAssemblyManifest.Entries
            .Select(entry => Assembly.Load(new AssemblyName(entry.AssemblyName)))
            .ToArray();
    }
}
