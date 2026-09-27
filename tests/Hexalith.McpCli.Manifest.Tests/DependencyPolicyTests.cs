using System.Text.Json;
using System.Xml.Linq;

namespace Hexalith.McpCli.Manifest.Tests;

/// <summary>Guards the production tool's restored package and project dependency boundary.</summary>
public sealed class DependencyPolicyTests
{
    /// <summary>Rejects a module dependency on another enrolled module even when both are allowed globally.</summary>
    [Fact]
    public void ModuleClosureCannotImportAnotherModule()
    {
        using JsonDocument first = JsonDocument.Parse("""{"dependencies":{"Other.Contracts":"1.0.0"}}""");
        using JsonDocument second = JsonDocument.Parse("{}");
        var packages = new Dictionary<string, (string Version, JsonElement Details)>(StringComparer.OrdinalIgnoreCase)
        {
            ["First.Contracts"] = ("1.0.0", first.RootElement),
            ["Other.Contracts"] = ("1.0.0", second.RootElement),
        };

        string[] failures = FindUnapprovedModuleDependencies("First.Contracts", packages,
            new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase), "Hexalith.McpCli.Abstractions").ToArray();

        Assert.Contains("First.Contracts adds unapproved transitive package Other.Contracts", failures);
    }

    /// <summary>Rejects unapproved direct roots, package versions, module transitives, and framework references.</summary>
    [Fact]
    public void ProductionContractsStayWithinPinnedDependencyClosure()
    {
        string root = FindRepositoryRoot();
        using JsonDocument policy = JsonDocument.Parse(File.ReadAllText(Path.Combine(root, "tools", "dependency-policy.json")));
        using JsonDocument assets = JsonDocument.Parse(File.ReadAllText(Path.Combine(root,
            "src", "Hexalith.McpCli", "obj", "project.assets.json")));

        JsonElement rules = policy.RootElement;
        Assert.Equal(1, rules.GetProperty("schemaVersion").GetInt32());
        Dictionary<string, string> baseline = ReadVersions(rules.GetProperty("baselinePackages"));
        Dictionary<string, string> modules = ReadVersions(rules.GetProperty("modules"));
        JsonElement decoration = rules.GetProperty("decorationPackage");
        string decorationId = decoration.GetProperty("id").GetString()!;
        string decorationVersion = decoration.GetProperty("version").GetString()!;
        HashSet<string> direct = rules.GetProperty("directPackages").EnumerateArray()
            .Select(item => item.GetString()!).ToHashSet(StringComparer.OrdinalIgnoreCase);
        var failures = new List<string>();

        string sourceRoot = Path.Combine(root, "src");
        string toolProject = Path.Combine(sourceRoot, "Hexalith.McpCli", "Hexalith.McpCli.csproj");
        var enrolled = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (string project in Directory.GetFiles(sourceRoot, "*.csproj", SearchOption.AllDirectories)
            .Where(path => !path.Contains($"{Path.DirectorySeparatorChar}Hexalith.McpCli.Analyzers{Path.DirectorySeparatorChar}", StringComparison.Ordinal)))
        {
            XDocument document = XDocument.Load(project);
            foreach (XElement reference in document.Descendants().Where(item => item.Name.LocalName == "ProjectReference"))
            {
                string include = (string?)reference.Attribute("Include") ?? string.Empty;
                if (include.Contains("$(", StringComparison.Ordinal))
                {
                    failures.Add($"{Path.GetFileName(project)} has an unresolved project reference: {include}");
                    continue;
                }

                string target = Path.GetFullPath(Path.Combine(Path.GetDirectoryName(project)!,
                    include.Replace('\\', Path.DirectorySeparatorChar)));
                if (!target.StartsWith(sourceRoot + Path.DirectorySeparatorChar, StringComparison.Ordinal)
                    || !Path.GetFileName(target).StartsWith("Hexalith.McpCli.", StringComparison.Ordinal))
                {
                    failures.Add($"{Path.GetFileName(project)} references a non-McpCli project: {include}");
                }
            }

            foreach (XElement reference in document.Descendants().Where(item => item.Name.LocalName == "FrameworkReference"))
            {
                string? include = (string?)reference.Attribute("Include");
                if (include != "Microsoft.NETCore.App")
                {
                    failures.Add($"{Path.GetFileName(project)} introduces framework reference {include}");
                }
            }

            foreach (XElement reference in document.Descendants().Where(item => item.Name.LocalName == "PackageReference"))
            {
                string id = (string?)reference.Attribute("Include") ?? string.Empty;
                bool marked = string.Equals((string?)reference.Attribute("HexalithContracts"), "true", StringComparison.OrdinalIgnoreCase);
                if (reference.Attribute("Version") is not null)
                {
                    failures.Add($"{Path.GetFileName(project)} pins {id} inline instead of centrally");
                }

                if (marked || id.EndsWith(".Contracts", StringComparison.OrdinalIgnoreCase)
                    && !id.Equals("Hexalith.EventStore.Contracts", StringComparison.OrdinalIgnoreCase))
                {
                    if (project != toolProject || !marked || !modules.ContainsKey(id))
                    {
                        failures.Add($"{Path.GetFileName(project)} has an unapproved Contracts root: {id}");
                    }
                    else
                    {
                        enrolled.Add(id);
                    }
                }
                else if (!direct.Contains(id) && !id.Equals(decorationId, StringComparison.OrdinalIgnoreCase))
                {
                    failures.Add($"{Path.GetFileName(project)} has an unapproved direct package: {id}");
                }
            }
        }

        foreach (string module in modules.Keys.Except(enrolled, StringComparer.OrdinalIgnoreCase))
        {
            failures.Add($"Approved module {module} has no flagged direct reference in the tool");
        }

        JsonElement targetAssets = assets.RootElement.GetProperty("targets").GetProperty("net10.0");
        var packages = new Dictionary<string, (string Version, JsonElement Details)>(StringComparer.OrdinalIgnoreCase);
        foreach (JsonProperty entry in targetAssets.EnumerateObject())
        {
            if (entry.Value.GetProperty("type").GetString() != "package")
            {
                continue;
            }

            int separator = entry.Name.LastIndexOf('/');
            string id = entry.Name[..separator];
            string version = entry.Name[(separator + 1)..];
            if (!packages.TryAdd(id, (version, entry.Value)))
            {
                failures.Add($"The restore resolved multiple versions of {id}");
            }

            string? expected = baseline.GetValueOrDefault(id) ?? modules.GetValueOrDefault(id);
            if (id.Equals(decorationId, StringComparison.OrdinalIgnoreCase))
            {
                expected = decorationVersion;
            }

            if (expected is null || !string.Equals(expected, version, StringComparison.OrdinalIgnoreCase))
            {
                failures.Add($"Restored package {id}/{version} is outside the exact dependency policy");
            }
        }

        foreach (string id in baseline.Keys.Concat(modules.Keys))
        {
            if (!packages.ContainsKey(id))
            {
                failures.Add($"Pinned package {id} is missing from the tool restore");
            }
        }

        JsonElement frameworks = assets.RootElement.GetProperty("project").GetProperty("frameworks")
            .GetProperty("net10.0").GetProperty("frameworkReferences");
        foreach (JsonProperty framework in frameworks.EnumerateObject())
        {
            if (framework.Name != "Microsoft.NETCore.App")
            {
                failures.Add($"The tool restore adds framework reference {framework.Name}");
            }
        }

        foreach (string module in enrolled)
        {
            if (!packages.TryGetValue(module, out (string Version, JsonElement Details) entry))
            {
                failures.Add($"Enrolled module {module} is missing from the tool restore");
                continue;
            }

            failures.AddRange(FindUnapprovedModuleDependencies(module, packages, baseline, decorationId));

            string? nuspec = FindNuspec(assets.RootElement, module, entry.Version);
            if (nuspec is null)
            {
                failures.Add($"The restored {module} nuspec cannot be inspected");
                continue;
            }

            foreach (XElement reference in XDocument.Load(nuspec).Descendants()
                .Where(item => item.Name.LocalName == "frameworkReference"))
            {
                string? name = (string?)reference.Attribute("name");
                if (name != "Microsoft.NETCore.App")
                {
                    failures.Add($"{module} adds framework reference {name}");
                }
            }
        }

        Assert.True(failures.Count == 0, string.Join(Environment.NewLine, failures));
    }

    private static Dictionary<string, string> ReadVersions(JsonElement map)
        => map.EnumerateObject().ToDictionary(item => item.Name, item => item.Value.GetString()!, StringComparer.OrdinalIgnoreCase);

    private static IEnumerable<string> FindUnapprovedModuleDependencies(string module,
        IReadOnlyDictionary<string, (string Version, JsonElement Details)> packages,
        IReadOnlyDictionary<string, string> baseline, string decorationId)
    {
        var visited = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        var pending = new Queue<string>();
        pending.Enqueue(module);
        while (pending.TryDequeue(out string? id))
        {
            if (!visited.Add(id))
            {
                continue;
            }

            if (!packages.TryGetValue(id, out (string Version, JsonElement Details) package))
            {
                yield return $"{module} has an unresolved transitive package {id}";
                continue;
            }

            if (!id.Equals(module, StringComparison.OrdinalIgnoreCase)
                && !id.Equals(decorationId, StringComparison.OrdinalIgnoreCase)
                && !baseline.ContainsKey(id))
            {
                yield return $"{module} adds unapproved transitive package {id}";
            }

            if (package.Details.TryGetProperty("dependencies", out JsonElement dependencies))
            {
                foreach (JsonProperty dependency in dependencies.EnumerateObject())
                {
                    pending.Enqueue(dependency.Name);
                }
            }
        }
    }

    private static string? FindNuspec(JsonElement assets, string id, string version)
    {
        string key = id + "/" + version;
        if (!assets.GetProperty("libraries").TryGetProperty(key, out JsonElement library))
        {
            return null;
        }

        string packagePath = library.GetProperty("path").GetString()!;
        foreach (JsonProperty folder in assets.GetProperty("packageFolders").EnumerateObject())
        {
            string directory = Path.Combine(folder.Name, packagePath.Replace('/', Path.DirectorySeparatorChar));
            if (Directory.Exists(directory))
            {
                return Directory.EnumerateFiles(directory, "*.nuspec").SingleOrDefault();
            }
        }

        return null;
    }

    private static string FindRepositoryRoot()
    {
        DirectoryInfo? current = new(AppContext.BaseDirectory);
        while (current is not null && !File.Exists(Path.Combine(current.FullName, "Hexalith.McpCli.slnx")))
        {
            current = current.Parent;
        }

        return current?.FullName ?? throw new InvalidOperationException("McpCli repository root was not found.");
    }
}
