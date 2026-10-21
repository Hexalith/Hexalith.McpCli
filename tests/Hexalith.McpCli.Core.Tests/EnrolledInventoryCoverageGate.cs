using System.Text.Json;
using Hexalith.McpCli.Core.Catalog;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Requires a release inventory for each module in the production manifest.</summary>
internal static class EnrolledInventoryCoverageGate
{
    /// <summary>Checks every unfiltered module; an absent inventory is a blocking finding.</summary>
    internal static IReadOnlyList<string> Check(string directory, ICatalog catalog, CatalogProvider provider)
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

            IReadOnlyList<string> moduleFindings = InventoryCoverageGate.CheckFile(path, catalog, provider);
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
