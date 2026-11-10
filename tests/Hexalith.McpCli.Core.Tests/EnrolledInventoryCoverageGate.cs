using System.Text.Json;
using Hexalith.McpCli.Core.Catalog;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Requires a release inventory for each module in the production manifest.</summary>
internal static class EnrolledInventoryCoverageGate
{
    /// <summary>Checks every unfiltered module; an absent inventory is a blocking finding.</summary>
    /// <param name="directory">The directory holding each module's release inventory.</param>
    /// <param name="catalog">The public, unfiltered discovery service.</param>
    /// <param name="provider">The provider of the independently checked internal snapshot.</param>
    /// <param name="reports">Receives each module's non-failing inventory reports, when supplied.</param>
    /// <returns>The blocking findings in ordinal order.</returns>
    internal static IReadOnlyList<string> Check(string directory, ICatalog catalog, CatalogProvider provider, ICollection<string>? reports = null)
    {
        var findings = new List<string>();
        CatalogAccess access = provider.Get(false);
        if (access.Catalog is null)
        {
            findings.Add($"catalog: {access.ErrorCode}: {access.Message}");
            return findings;
        }

        foreach (ModuleDescriptor module in access.Catalog.Modules)
        {
            string path = Path.Combine(directory, module.Name + "-approved.json");
            if (!File.Exists(path))
            {
                findings.Add($"{module.Name}: missing release inventory '{path}'.");
                continue;
            }

            IReadOnlyList<string> moduleFindings = InventoryCoverageGate.CheckFile(path, catalog, provider, reports);
            findings.AddRange(moduleFindings);
            if (moduleFindings.Count == 0)
            {
                using JsonDocument document = JsonDocument.Parse(File.ReadAllText(path));
                if (document.RootElement.GetProperty("purpose").GetString() != "release")
                {
                    findings.Add($"{module.Name}: enrolled modules require purpose 'release'.");
                }
                if (document.RootElement.GetProperty("module").GetString() != module.Name)
                {
                    findings.Add($"{module.Name}: inventory declares a different module.");
                }
            }
        }

        return findings.Order(StringComparer.Ordinal).ToArray();
    }
}
