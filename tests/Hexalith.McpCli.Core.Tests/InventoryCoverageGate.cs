using System.Globalization;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using Hexalith.McpCli.Core.Catalog;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Checks approved inventory scope against public discovery and internal descriptors, in tests only.</summary>
internal static class InventoryCoverageGate
{
    /// <summary>Loads an inventory by explicit path, independently of the current working directory.</summary>
    /// <param name="path">The inventory file path.</param>
    /// <param name="catalog">The public, unfiltered discovery service.</param>
    /// <param name="provider">The provider of the independently checked internal snapshot.</param>
    /// <returns>Deterministically ordered, file- and location-qualified findings; empty means coverage matches.</returns>
    internal static IReadOnlyList<string> CheckFile(string path, ICatalog catalog, CatalogProvider provider)
    {
        try
        {
            ReadOnlySpan<byte> bytes = File.ReadAllBytes(path);
            if (bytes.StartsWith<byte>([0xEF, 0xBB, 0xBF]))
            {
                bytes = bytes[3..];
            }

            return Check(new UTF8Encoding(false, true).GetString(bytes), path, catalog, provider);
        }
        catch (DecoderFallbackException)
        {
            return [$"{path}:$: malformed UTF-8 encoding."];
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException)
        {
            return [$"{path}:$: cannot read inventory ({exception.GetType().Name})."];
        }
    }

    /// <summary>Checks one JSON document without loading any inventory into production.</summary>
    /// <param name="json">The versioned inventory JSON.</param>
    /// <param name="file">The stable source label used in every diagnostic.</param>
    /// <param name="catalog">The public, unfiltered discovery service.</param>
    /// <param name="provider">The provider supplying real internal descriptors and declaration diagnostics.</param>
    /// <returns>The exact coverage and validation findings in ordinal order.</returns>
    internal static IReadOnlyList<string> Check(string json, string file, ICatalog catalog, CatalogProvider provider)
    {
        var findings = new List<string>();
        void Add(string location, string message) => findings.Add($"{file}:{location}: {message}");
        JsonDocument parsed;
        try
        {
            parsed = JsonDocument.Parse(json);
        }
        catch (JsonException exception)
        {
            Add("$", string.Create(CultureInfo.InvariantCulture,
                $"invalid JSON at line {exception.LineNumber}, byte {exception.BytePositionInLine}."));
            return findings;
        }

        using (parsed)
        {
            CheckDuplicateKeys(parsed.RootElement, "$", Add);
            InventoryCoverageDocument? inventory = Load(parsed.RootElement, Add);
            if (inventory is not null && findings.Count == 0)
            {
                Validate(inventory, Add);
                if (findings.Count == 0)
                {
                    Compare(inventory, catalog, provider, Add);
                }
            }
        }

        return findings.OrderBy(item => item, StringComparer.Ordinal).ToArray();
    }

    private static InventoryCoverageDocument? Load(JsonElement root, Action<string, string> add)
    {
        if (!Object(root, "$", ["formatVersion", "module", "purpose", "targets", "legacyRows"], add))
        {
            return null;
        }

        if (root.GetProperty("formatVersion").ValueKind != JsonValueKind.Number
            || !root.GetProperty("formatVersion").TryGetInt32(out int version) || version != 1)
        {
            add("$.formatVersion", "expected supported integer formatVersion 1.");
        }

        string module = Text(root.GetProperty("module"), "$.module", add);
        string purpose = Text(root.GetProperty("purpose"), "$.purpose", add);
        var targets = new List<InventoryCoverageTarget>();
        var rows = new List<InventoryCoverageRow>();
        foreach ((JsonElement item, string path) in Items(root.GetProperty("targets"), "$.targets", add))
        {
            if (Object(item, path, ["id", "name", "contractType"], add))
            {
                targets.Add(new(Text(item.GetProperty("id"), path + ".id", add),
                    Text(item.GetProperty("name"), path + ".name", add),
                    Text(item.GetProperty("contractType"), path + ".contractType", add)));
            }
        }

        foreach ((JsonElement item, string path) in Items(root.GetProperty("legacyRows"), "$.legacyRows", add))
        {
            if (!Object(item, path, ["id", "legacyOperation", "targetIds", "disposition", "coverage", "rationale", "approval"], add))
            {
                continue;
            }

            JsonElement approval = item.GetProperty("approval");
            if (!Object(approval, path + ".approval", ["status", "authority", "reference"], add))
            {
                continue;
            }

            rows.Add(new(Text(item.GetProperty("id"), path + ".id", add),
                Text(item.GetProperty("legacyOperation"), path + ".legacyOperation", add),
                Items(item.GetProperty("targetIds"), path + ".targetIds", add)
                    .Select(entry => Text(entry.Item, entry.Path, add)).ToArray(),
                Text(item.GetProperty("disposition"), path + ".disposition", add),
                Text(item.GetProperty("coverage"), path + ".coverage", add),
                Text(item.GetProperty("rationale"), path + ".rationale", add),
                new(Text(approval.GetProperty("status"), path + ".approval.status", add),
                    Text(approval.GetProperty("authority"), path + ".approval.authority", add),
                    Text(approval.GetProperty("reference"), path + ".approval.reference", add))));
        }

        return new(module, purpose, targets, rows);
    }

    private static void Validate(InventoryCoverageDocument inventory, Action<string, string> add)
    {
        const string canonicalPart = "[a-z0-9]+(?:-[a-z0-9]+)*";
        if (!Regex.IsMatch(inventory.Module, "\\A" + canonicalPart + "\\z", RegexOptions.CultureInvariant))
        {
            add("$.module", $"expected canonical module name; actual '{inventory.Module}'.");
            return;
        }

        if (inventory.Purpose is not ("fixture" or "release"))
        {
            add("$.purpose", "expected 'fixture' or 'release'.");
        }

        var ids = new Dictionary<string, string>(StringComparer.Ordinal);
        var names = new Dictionary<string, string>(StringComparer.Ordinal);
        var types = new Dictionary<string, string>(StringComparer.Ordinal);
        for (int index = 0; index < inventory.Targets.Count; index++)
        {
            InventoryCoverageTarget target = inventory.Targets[index];
            string location = $"target {target.Id}";
            string identityLocation = location + " ($.targets[" + index.ToString(CultureInfo.InvariantCulture) + "].id)";
            Unique(ids, target.Id, identityLocation, "id", add);
            Unique(names, target.Name, location, "name", add);
            Unique(types, target.ContractType, location, "contractType", add);
            if (!Regex.IsMatch(target.Name, "\\A" + Regex.Escape(inventory.Module) + "\\." + canonicalPart + "\\z", RegexOptions.CultureInvariant))
            {
                add(location, $"name must be canonical in module '{inventory.Module}'; actual '{target.Name}'.");
            }
        }

        var rowIds = new Dictionary<string, string>(StringComparer.Ordinal);
        var references = new Dictionary<string, List<InventoryCoverageRow>>(StringComparer.Ordinal);
        for (int index = 0; index < inventory.LegacyRows.Count; index++)
        {
            InventoryCoverageRow row = inventory.LegacyRows[index];
            string location = $"row {row.Id}";
            string identityLocation = location + " ($.legacyRows[" + index.ToString(CultureInfo.InvariantCulture) + "].id)";
            Unique(rowIds, row.Id, identityLocation, "id", add);
            if (row.Coverage is not ("include" or "exclude"))
            {
                add(location, $"coverage must be 'include' or 'exclude'; actual '{row.Coverage}'.");
            }
            else if ((row.Coverage == "include" && row.Disposition != "replace")
                || (row.Coverage == "exclude" && row.Disposition is not ("withdraw" or "defer")))
            {
                add(location, $"invalid disposition/coverage '{row.Disposition}/{row.Coverage}'; include requires replace; exclude requires withdraw or defer.");
            }

            if (row.Approval.Status != "approved")
            {
                add(location, $"approval.status must be 'approved'; actual '{row.Approval.Status}'.");
            }

            if (row.Approval.Authority is not ("owning-maintainer" or "synthetic-fixture"))
            {
                add(location, $"approval.authority must be 'owning-maintainer' or 'synthetic-fixture'; actual '{row.Approval.Authority}'. Scope-only approval cannot establish release readiness.");
            }
            else if (row.Approval.Authority == "synthetic-fixture" && inventory.Purpose == "release")
            {
                add(location, "synthetic-fixture approval certifies fixtures only; purpose must be 'fixture'.");
            }

            var perRow = new HashSet<string>(StringComparer.Ordinal);
            foreach (string id in row.TargetIds)
            {
                if (!perRow.Add(id))
                {
                    add(location, $"duplicate target reference '{id}'.");
                }
                else if (!ids.ContainsKey(id))
                {
                    add(location, $"dangling target reference '{id}'.");
                }
                else
                {
                    if (!references.TryGetValue(id, out List<InventoryCoverageRow>? targetRows))
                    {
                        targetRows = [];
                        references.Add(id, targetRows);
                    }

                    targetRows.Add(row);
                }
            }
        }

        foreach (InventoryCoverageTarget target in inventory.Targets)
        {
            if (!references.TryGetValue(target.Id, out List<InventoryCoverageRow>? targetRows))
            {
                add($"target {target.Id}", "orphan target has no legacy row reference.");
            }
            else if (targetRows.Select(row => row.Coverage).Distinct(StringComparer.Ordinal).Count() > 1)
            {
                add($"target {target.Id}", $"conflicting coverage in rows {string.Join(", ", targetRows.Select(row => row.Id).Order(StringComparer.Ordinal))}.");
            }
        }
    }

    private static void Compare(InventoryCoverageDocument inventory, ICatalog catalog, CatalogProvider provider, Action<string, string> add)
    {
        CatalogAccess access = provider.Get(false);
        if (access.Catalog is null)
        {
            add("catalog", $"internal Catalog error '{access.ErrorCode}': {access.Message}");
        }
        else
        {
            foreach (CatalogDiagnostic diagnostic in access.Catalog.Diagnostics.Where(item => item.Severity == "error"))
            {
                add($"catalog {diagnostic.TypeName}", $"{diagnostic.Category}: {diagnostic.Message}");
            }
        }

        CatalogLookupResult<OperationsDocument> result = catalog.ListOperations(inventory.Module);
        if (result.Error is not null)
        {
            add("public", $"ListOperations error '{result.Error.Code}': {result.Error.Message ?? "<none>"}");
        }
        else if (result.Document is null)
        {
            add("public", "ListOperations returned no document.");
        }
        else if (result.Document.Module != inventory.Module)
        {
            add("public", $"module expected '{inventory.Module}'; actual '{result.Document.Module}'.");
        }

        if (access.Catalog is null || result.Document is null || result.Error is not null)
        {
            return;
        }

        OperationDescriptor[] descriptors = access.Catalog.Modules
            .Where(module => string.Equals(module.Name, inventory.Module, StringComparison.Ordinal))
            .SelectMany(module => module.Operations).ToArray();
        IReadOnlyList<OperationSummary> operations = result.Document.Operations;
        foreach (IGrouping<string, OperationSummary> group in operations.GroupBy(item => item.Name, StringComparer.Ordinal).Where(group => group.Count() > 1))
        {
            add($"public operation {group.Key}", string.Create(CultureInfo.InvariantCulture,
                $"duplicate public entry; expected once, actual {group.Count()}."));
        }

        var includedNames = new HashSet<string>(StringComparer.Ordinal);
        foreach (InventoryCoverageTarget target in inventory.Targets)
        {
            bool included = inventory.LegacyRows.Any(row => row.Coverage == "include" && row.TargetIds.Contains(target.Id, StringComparer.Ordinal));
            OperationSummary[] matchingPublic = operations.Where(item => string.Equals(item.Name, target.Name, StringComparison.Ordinal)).ToArray();
            OperationDescriptor[] matchingInternal = descriptors.Where(item => string.Equals(item.Name, target.Name, StringComparison.Ordinal)).ToArray();
            if (included)
            {
                includedNames.Add(target.Name);
                if (matchingPublic.Length == 0)
                {
                    add($"target {target.Id}", $"public name expected '{target.Name}' once; actual missing.");
                }

                if (matchingInternal.Length != 1)
                {
                    add($"target {target.Id}", string.Create(CultureInfo.InvariantCulture,
                        $"internal name expected '{target.Name}' once; actual {matchingInternal.Length}."));
                }
                else if (!string.Equals(matchingInternal[0].ContractType.FullName, target.ContractType, StringComparison.Ordinal))
                {
                    add($"target {target.Id}", $"contractType for '{target.Name}' expected '{target.ContractType}'; actual '{matchingInternal[0].ContractType.FullName}'.");
                }
            }
            else
            {
                if (matchingPublic.Length > 0)
                {
                    add($"target {target.Id}", $"excluded name '{target.Name}' is publicly present.");
                }

                foreach (OperationDescriptor descriptor in descriptors.Where(item => item.Name == target.Name || item.ContractType.FullName == target.ContractType))
                {
                    add($"target {target.Id}", $"excluded target is internally present as '{descriptor.Name}' / '{descriptor.ContractType.FullName}'.");
                }
            }
        }

        foreach (string name in operations.Select(item => item.Name).Distinct(StringComparer.Ordinal).Where(name => !includedNames.Contains(name)))
        {
            add($"public operation {name}", "unexpected operation; no approved included target.");
        }

        foreach (OperationDescriptor descriptor in descriptors.Where(item => !includedNames.Contains(item.Name)))
        {
            add($"internal operation {descriptor.Name}", $"unexpected operation / '{descriptor.ContractType.FullName}'; no approved included target.");
        }
    }

    private static bool Object(JsonElement item, string path, string[] fields, Action<string, string> add)
    {
        if (item.ValueKind != JsonValueKind.Object)
        {
            add(path, "expected object.");
            return false;
        }

        bool valid = true;
        foreach (JsonProperty property in item.EnumerateObject())
        {
            if (!fields.Contains(property.Name, StringComparer.Ordinal))
            {
                add(path + "." + property.Name, "unknown field.");
                valid = false;
            }
        }

        foreach (string field in fields)
        {
            if (!item.TryGetProperty(field, out _))
            {
                add(path + "." + field, "missing required field.");
                valid = false;
            }
        }

        return valid;
    }

    private static string Text(JsonElement item, string path, Action<string, string> add)
    {
        if (item.ValueKind != JsonValueKind.String || string.IsNullOrWhiteSpace(item.GetString()) || item.GetString() != item.GetString()!.Trim())
        {
            add(path, "expected nonempty string without surrounding whitespace.");
            return string.Empty;
        }

        return item.GetString()!;
    }

    private static IEnumerable<(JsonElement Item, string Path)> Items(JsonElement item, string path, Action<string, string> add)
    {
        if (item.ValueKind != JsonValueKind.Array || item.GetArrayLength() == 0)
        {
            add(path, "expected nonempty array.");
            yield break;
        }

        int index = 0;
        foreach (JsonElement value in item.EnumerateArray())
        {
            yield return (value, path + "[" + index.ToString(CultureInfo.InvariantCulture) + "]");
            index++;
        }
    }

    private static void CheckDuplicateKeys(JsonElement item, string path, Action<string, string> add)
    {
        if (item.ValueKind == JsonValueKind.Object)
        {
            var seen = new HashSet<string>(StringComparer.Ordinal);
            foreach (JsonProperty property in item.EnumerateObject())
            {
                string child = path + "." + property.Name;
                if (!seen.Add(property.Name))
                {
                    add(child, "duplicate JSON key.");
                }

                CheckDuplicateKeys(property.Value, child, add);
            }
        }
        else if (item.ValueKind == JsonValueKind.Array)
        {
            int index = 0;
            foreach (JsonElement value in item.EnumerateArray())
            {
                CheckDuplicateKeys(value, path + "[" + index.ToString(CultureInfo.InvariantCulture) + "]", add);
                index++;
            }
        }
    }

    private static void Unique(Dictionary<string, string> seen, string value, string location, string field, Action<string, string> add)
    {
        if (!seen.TryAdd(value, location))
        {
            add(location, $"duplicate {field} '{value}'; first declared at {seen[value]}.");
        }
    }
}
