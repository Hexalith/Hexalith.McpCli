namespace Hexalith.McpCli.Core.Catalog;

/// <summary>An immutable snapshot of valid modules and declaration diagnostics.</summary>
public sealed class Catalog
{
    internal Catalog(IReadOnlyList<ModuleDescriptor> modules, IReadOnlyList<CatalogDiagnostic> diagnostics)
    {
        Modules = Array.AsReadOnly(modules.ToArray());
        Diagnostics = Array.AsReadOnly(diagnostics.ToArray());
    }

    /// <summary>Gets modules in ordinal canonical-name order.</summary>
    public IReadOnlyList<ModuleDescriptor> Modules { get; }

    /// <summary>Gets deterministic declaration diagnostics.</summary>
    public IReadOnlyList<CatalogDiagnostic> Diagnostics { get; }
}
