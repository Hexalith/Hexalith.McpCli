using System.Globalization;
using System.Reflection;
using Microsoft.Extensions.Logging;

namespace Hexalith.McpCli.Core.Catalog;

/// <summary>
/// Builds the Catalog once, on first use, logs each diagnostic once, and applies the empty and strict policies.
/// </summary>
public sealed partial class CatalogProvider
{
    private readonly Lazy<CatalogSnapshot> _catalog;

    /// <summary>Initializes a new instance of the <see cref="CatalogProvider"/> class without touching any assembly.</summary>
    /// <param name="manifest">Supplies the Contracts assembly manifest when the Catalog is first needed.</param>
    /// <param name="logger">Receives each Catalog diagnostic once.</param>
    public CatalogProvider(Func<IReadOnlyList<Assembly>> manifest, ILogger<CatalogProvider> logger)
    {
        ArgumentNullException.ThrowIfNull(manifest);
        ArgumentNullException.ThrowIfNull(logger);
        _catalog = new Lazy<CatalogSnapshot>(() => BuildAndLog(manifest, logger), LazyThreadSafetyMode.ExecutionAndPublication);
    }

    /// <summary>Gets the Catalog for a Catalog-dependent caller, building it on the first call.</summary>
    /// <param name="strict">Whether any diagnostic, warnings included, makes the Catalog unusable.</param>
    /// <returns>The Catalog, or <c>catalog_invalid</c> (checked first) or <c>catalog_empty</c>.</returns>
    public CatalogAccess Get(bool strict)
    {
        CatalogSnapshot catalog = _catalog.Value;
        if (strict && catalog.Diagnostics.Count > 0)
        {
            return new CatalogAccess(null, "catalog_invalid", string.Create(CultureInfo.InvariantCulture,
                $"Strict mode rejects the Catalog because it has {catalog.Diagnostics.Count} diagnostic(s)."));
        }

        if (!catalog.Modules.Any(module => module.Operations.Count > 0))
        {
            return new CatalogAccess(null, "catalog_empty", "The Catalog exposes no valid Operations.");
        }

        return new CatalogAccess(catalog, null, null);
    }

    private static CatalogSnapshot BuildAndLog(Func<IReadOnlyList<Assembly>> manifest, ILogger logger)
    {
        CatalogSnapshot catalog = CatalogBuilder.Build(manifest());
        foreach (CatalogDiagnostic diagnostic in catalog.Diagnostics)
        {
            LogDiagnostic(
                logger,
                string.Equals(diagnostic.Severity, "warning", StringComparison.Ordinal) ? LogLevel.Warning : LogLevel.Error,
                diagnostic.TypeName,
                diagnostic.Category,
                diagnostic.Severity,
                diagnostic.Message);
        }

        return catalog;
    }

    [LoggerMessage(EventId = 1, EventName = "CatalogDiagnostic",
        Message = "Catalog {Severity} {Category} for {TypeName}: {Message}")]
    private static partial void LogDiagnostic(ILogger logger, LogLevel level, string typeName, string category, string severity, string message);
}
