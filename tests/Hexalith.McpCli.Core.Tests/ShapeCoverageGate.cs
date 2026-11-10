using System.Security.Cryptography;
using System.Text.Json;
using Hexalith.McpCli.Core.Catalog;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Requires an approved vector for every Operation Shape of each enrolled package's module, in tests only.</summary>
internal static class ShapeCoverageGate
{
    /// <summary>Fails each uncovered shape and reports each covered one.</summary>
    /// <param name="modulesDirectory">The directory that holds one approval directory per Contracts package.</param>
    /// <param name="packageIds">The enrolled Contracts package identifiers.</param>
    /// <param name="snapshot">The internal Catalog snapshot that supplies the descriptors.</param>
    /// <param name="reports">Receives one non-failing report per covered shape, when supplied.</param>
    /// <returns>Ordinal-ordered blocking findings; empty means every shape has an approved vector.</returns>
    internal static IReadOnlyList<string> Check(string modulesDirectory, IEnumerable<string> packageIds, CatalogSnapshot snapshot,
        ICollection<string>? reports = null)
    {
        var findings = new List<string>();
        foreach (ShapeCoverage shape in Coverage(modulesDirectory, packageIds, snapshot, findings))
        {
            string operations = string.Join(", ", shape.Operations);
            if (shape.VectorFiles.Count == 0)
            {
                findings.Add($"{shape.Module}: Operation Shape '{shape.Key}' has no approved vector (operations: {operations}).");
            }
            else
            {
                reports?.Add($"{shape.Module}: Operation Shape '{shape.Key}' is covered by approved vector(s) for "
                    + $"{string.Join(", ", shape.VectorOperations)} (operations: {operations}).");
            }
        }

        return findings.Order(StringComparer.Ordinal).ToArray();
    }

    /// <summary>Groups each enrolled module's operations by shape and counts only vectors whose bytes match the approval.</summary>
    /// <param name="modulesDirectory">The directory that holds one approval directory per Contracts package.</param>
    /// <param name="packageIds">The enrolled Contracts package identifiers.</param>
    /// <param name="snapshot">The internal Catalog snapshot that supplies the descriptors.</param>
    /// <param name="findings">Receives package-level findings that prevent shape grouping.</param>
    /// <returns>The shapes in module and key order.</returns>
    internal static IReadOnlyList<ShapeCoverage> Coverage(string modulesDirectory, IEnumerable<string> packageIds, CatalogSnapshot snapshot,
        ICollection<string> findings)
    {
        ArgumentNullException.ThrowIfNull(packageIds);
        ArgumentNullException.ThrowIfNull(snapshot);
        ArgumentNullException.ThrowIfNull(findings);
        var shapes = new List<ShapeCoverage>();
        foreach (string packageId in packageIds)
        {
            string[] directories = Directory.Exists(modulesDirectory)
                ? Directory.GetDirectories(modulesDirectory)
                    .Where(path => string.Equals(Path.GetFileName(path), packageId, StringComparison.OrdinalIgnoreCase)).ToArray()
                : [];
            if (directories.Length != 1)
            {
                findings.Add($"{packageId}: expected one approval directory (package IDs are case-insensitive).");
                continue;
            }

            using JsonDocument approval = JsonDocument.Parse(File.ReadAllBytes(Path.Combine(directories[0], "approval.json")));
            string moduleName = approval.RootElement.GetProperty("module").GetString()!;
            ModuleDescriptor? module = snapshot.Modules.SingleOrDefault(item => string.Equals(item.Name, moduleName, StringComparison.Ordinal));
            if (module is null)
            {
                findings.Add($"{packageId}: approved module '{moduleName}' is absent from the Catalog.");
                continue;
            }

            var vectors = new List<(string Operation, string Path)>();
            foreach (JsonProperty entry in approval.RootElement.GetProperty("vectorFilesSha256").EnumerateObject())
            {
                string path = Path.GetFullPath(Path.Combine(directories[0], entry.Name));
                if (File.Exists(path) && string.Equals(Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(path))),
                    entry.Value.GetString(), StringComparison.Ordinal))
                {
                    using JsonDocument vector = JsonDocument.Parse(File.ReadAllBytes(path));
                    vectors.Add((vector.RootElement.GetProperty("operation").GetString()!, path));
                }
            }

            foreach (IGrouping<string, OperationDescriptor> group in module.Operations
                .GroupBy(operation => OperationShape.From(module, operation).Key, StringComparer.Ordinal)
                .OrderBy(group => group.Key, StringComparer.Ordinal))
            {
                var operations = group.Select(operation => operation.Name).Order(StringComparer.Ordinal).ToArray();
                var covering = vectors.Where(vector => operations.Contains(vector.Operation, StringComparer.Ordinal)).ToArray();
                shapes.Add(new(module.Name, group.Key, operations,
                    covering.Select(vector => vector.Path).Order(StringComparer.Ordinal).ToArray(),
                    covering.Select(vector => vector.Operation).Distinct(StringComparer.Ordinal).Order(StringComparer.Ordinal).ToArray()));
            }
        }

        return shapes;
    }
}
