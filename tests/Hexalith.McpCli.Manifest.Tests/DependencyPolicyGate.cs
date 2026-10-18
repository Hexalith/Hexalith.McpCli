using System.Xml.Linq;

namespace Hexalith.McpCli.Manifest.Tests;

/// <summary>Checks production restored graphs and the separate test dependency boundary.</summary>
internal static class DependencyPolicyGate
{
    /// <summary>Checks policy integrity, source enrollment, exact stack closure, and every restored node.</summary>
    public static string[] CheckProduction(DependencyPolicy policy, RestoredDependencyGraph graph,
        IReadOnlyDictionary<string, XDocument> projects, string root)
    {
        var failures = new List<string>(graph.LoadFailures);
        string decoration = policy.DecorationPackage.Key;
        Dictionary<string, string> paths = graph.PathsFrom(graph.RootId, decoration, stopAtDecoration: false);
        Dictionary<string, string> closurePaths = graph.PathsFrom(graph.RootId, decoration);
        var direct = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        var enrolled = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        CheckIntegrity(policy, failures);
        foreach ((string project, XDocument document) in projects.OrderBy(item => item.Key, StringComparer.Ordinal))
        {
            if (Path.GetFileNameWithoutExtension(project) == "Hexalith.McpCli.Analyzers")
            {
                continue;
            }

            string projectId = Path.GetFileNameWithoutExtension(project);
            string projectPath = paths.GetValueOrDefault(projectId, $"{graph.RootId} > {projectId}");
            if (!IsProductionProject(root, project))
            {
                failures.Add($"Production source contains non-McpCli project {projectId}: {projectPath}");
            }

            foreach (XElement reference in Declarations(document, "ProjectReference"))
            {
                string include = Include(reference);
                if (include.Contains("$(", StringComparison.Ordinal))
                {
                    failures.Add($"Project {projectId} has an unresolved project reference {include}: {projectPath}");
                    continue;
                }

                string target = ResolveProject(project, include);
                if (IsTestProject(root, target))
                {
                    failures.Add($"Production project {projectId} references test-only project {include}: {projectPath} > {Path.GetFileNameWithoutExtension(target)}");
                }
                else if (!IsProductionProject(root, target))
                {
                    failures.Add($"Project {projectId} references a non-McpCli project {include}: {projectPath} > {Path.GetFileNameWithoutExtension(target)}");
                }
            }

            foreach (XElement reference in Declarations(document, "FrameworkReference"))
            {
                string framework = Include(reference);
                if (framework != "Microsoft.NETCore.App")
                {
                    failures.Add($"Project {projectId} introduces framework reference {framework}: {projectPath}");
                }
            }

            foreach (XElement reference in Items(document, "PackageReference"))
            {
                string id = (string?)reference.Attribute("Include") ?? (string?)reference.Attribute("Update")
                    ?? (string?)reference.Attribute("Remove") ?? string.Empty;
                string path = paths.GetValueOrDefault(id, $"{projectPath} > {graph.Identity(id, Pin(policy, id) ?? "unresolved")}");
                if (reference.Attribute("Version") is not null || reference.Attribute("VersionOverride") is not null
                    || reference.Elements().Any(item => item.Name.LocalName is "Version" or "VersionOverride"))
                {
                    failures.Add($"Project {projectId} pins {id} inline instead of centrally: {path}");
                }

                if (reference.Attribute("Include") is null)
                {
                    continue;
                }

                if (id.Contains("$(", StringComparison.Ordinal))
                {
                    failures.Add($"Project {projectId} has an unresolved package reference {id}: {projectPath}");
                }

                if (IsTestOnly(policy, id))
                {
                    failures.Add($"Production project {projectId} references test-only package {graph.Identity(id, Pin(policy, id) ?? "unresolved")}: {path}");
                    continue;
                }

                bool marked = string.Equals((string?)reference.Attribute("HexalithContracts")
                    ?? reference.Elements().FirstOrDefault(item => item.Name.LocalName == "HexalithContracts")?.Value,
                    "true", StringComparison.OrdinalIgnoreCase);
                if (marked || policy.Modules.ContainsKey(id) || id.EndsWith(".Contracts", StringComparison.OrdinalIgnoreCase)
                    && !id.Equals("Hexalith.EventStore.Contracts", StringComparison.OrdinalIgnoreCase))
                {
                    if (projectId != graph.RootId || !marked || !policy.Modules.ContainsKey(id)
                        || !id.EndsWith(".Contracts", StringComparison.OrdinalIgnoreCase))
                    {
                        failures.Add($"Project {projectId} has an unapproved Contracts root {graph.Identity(id, Pin(policy, id) ?? "unresolved")}: {path}");
                    }
                    else
                    {
                        enrolled.Add(id);
                    }
                }
                else if (!policy.DirectPackages.Contains(id) && !id.Equals(decoration, StringComparison.OrdinalIgnoreCase))
                {
                    failures.Add($"Project {projectId} has an unapproved direct package {graph.Identity(id)}: {path}");
                }
                else if (policy.DirectPackages.Contains(id)
                    && graph.Nodes.TryGetValue(projectId, out RestoredDependencyNode? projectNode)
                    && projectNode.Type == "project" && projectNode.ProjectPath == project
                    && projectNode.Dependencies.ContainsKey(id)
                    && graph.Nodes.TryGetValue(id, out RestoredDependencyNode? packageNode) && packageNode.Type == "package")
                {
                    direct.Add(id);
                }
            }
        }

        foreach (string id in policy.DirectPackages.Except(direct, StringComparer.OrdinalIgnoreCase).Order(StringComparer.Ordinal))
        {
            failures.Add($"Direct package {id}/{Pin(policy, id) ?? "unresolved"} has no production reference: {paths.GetValueOrDefault(id, $"{graph.RootId} > {id}/{Pin(policy, id) ?? "unresolved"}")}");
        }

        foreach ((string id, string version) in policy.Modules.OrderBy(item => item.Key, StringComparer.Ordinal))
        {
            if (!enrolled.Contains(id))
            {
                failures.Add($"Approved module {id}/{version} has no flagged direct reference in the tool: {graph.RootId} > {id}/{version}");
            }
        }

        var stack = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (string id in direct)
        {
            stack.UnionWith(graph.PathsFrom(id, decoration).Keys.Where(key => !key.Equals(decoration, StringComparison.OrdinalIgnoreCase)));
        }

        foreach ((string id, string version) in policy.BaselinePackages.OrderBy(item => item.Key, StringComparer.Ordinal))
        {
            if (!graph.Nodes.ContainsKey(id))
            {
                failures.Add($"Pinned baseline package {id}/{version} is missing from restore: {graph.RootId} > {id}/{version}");
            }
            else if (!stack.Contains(id))
            {
                failures.Add($"Baseline entry {id}/{version} is outside the non-module stack closure: {paths.GetValueOrDefault(id, $"{graph.RootId} > {graph.Identity(id)}")}");
            }
        }

        foreach (string id in stack.Order(StringComparer.Ordinal))
        {
            if (graph.Nodes.TryGetValue(id, out RestoredDependencyNode? node) && node.Type == "package"
                && !policy.BaselinePackages.ContainsKey(id))
            {
                failures.Add($"Stack package {node.Identity} is missing its baseline pin: {paths.GetValueOrDefault(id, $"{graph.RootId} > {node.Identity}")}");
            }
        }

        var moduleDependencies = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach ((string module, string version) in policy.Modules.OrderBy(item => item.Key, StringComparer.Ordinal))
        {
            if (!graph.Nodes.TryGetValue(module, out RestoredDependencyNode? moduleNode) || moduleNode.Type != "package")
            {
                failures.Add($"Pinned module {module}/{version} is missing from restore: {graph.RootId} > {module}/{version}");
                continue;
            }

            foreach ((string id, string path) in graph.PathsFrom(module, decoration))
            {
                moduleDependencies.Add(id);
                if (!graph.Nodes.TryGetValue(id, out RestoredDependencyNode? node))
                {
                    failures.Add($"Module {module} has an unresolved dependency {id}: {path}");
                }
                else if (!id.Equals(module, StringComparison.OrdinalIgnoreCase) && !id.Equals(decoration, StringComparison.OrdinalIgnoreCase)
                    && !stack.Contains(id))
                {
                    failures.Add($"Module {module} adds unapproved package {node.Identity}: {path}");
                }
            }
        }

        foreach ((string id, string path) in closurePaths.OrderBy(item => item.Key, StringComparer.Ordinal))
        {
            if (!graph.Nodes.ContainsKey(id) && !moduleDependencies.Contains(id))
            {
                failures.Add($"Restore has an unresolved dependency {id}: {path}");
            }
        }

        foreach (RestoredDependencyNode node in graph.Nodes.Values.OrderBy(item => item.Id, StringComparer.Ordinal))
        {
            string path = paths.GetValueOrDefault(node.Id, $"{graph.RootId} > {node.Identity}");
            foreach (string framework in node.FrameworkReferences.Order(StringComparer.Ordinal))
            {
                if (framework != "Microsoft.NETCore.App")
                {
                    failures.Add($"{(node.Type == "package" ? "Package" : "Project")} {node.Identity} adds framework reference {framework}: {path}");
                }
            }

            if (IsTestOnly(policy, node.Id) || node.Type == "project" && node.ProjectPath is not null && IsTestProject(root, node.ProjectPath))
            {
                failures.Add($"Production restore contains test-only {node.Type} {node.Identity}: {path}");
            }

            if (node.Type == "project")
            {
                if (node.ProjectPath is null || !IsProductionProject(root, node.ProjectPath))
                {
                    failures.Add($"Production restore contains non-McpCli project {node.Identity}: {path}");
                }

                foreach (string dependency in node.Dependencies.Keys.Order(StringComparer.Ordinal))
                {
                    if (graph.Nodes.TryGetValue(dependency, out RestoredDependencyNode? target) && target.Type == "package"
                        && !policy.DirectPackages.Contains(dependency) && !dependency.Equals(decoration, StringComparison.OrdinalIgnoreCase)
                        && !(node.Id == graph.RootId && policy.Modules.ContainsKey(dependency)))
                    {
                        failures.Add($"Restored project {node.Id} has an unapproved direct package {target.Identity}: {path} > {target.Identity}");
                    }
                }

                continue;
            }

            string? pin = Pin(policy, node.Id);
            if (pin is null && !moduleDependencies.Contains(node.Id))
            {
                failures.Add($"Restored package {node.Identity} is outside the exact dependency policy: {path}");
            }
            else if (pin is not null && !string.Equals(pin, node.Version, StringComparison.OrdinalIgnoreCase))
            {
                failures.Add($"Restored package {node.Identity} differs from pin {node.Id}/{pin}: {path}");
            }
        }

        return failures.Order(StringComparer.Ordinal).ToArray();
    }

    /// <summary>Allows reviewed testing roots and local fixtures, rejecting external project references.</summary>
    public static string[] CheckTestProjects(DependencyPolicy policy, IReadOnlyDictionary<string, XDocument> projects, string root)
    {
        var failures = new List<string>();
        foreach ((string project, XDocument document) in projects.OrderBy(item => item.Key, StringComparer.Ordinal))
        {
            string name = Path.GetRelativePath(root, project).Replace('\\', '/');
            foreach (XElement reference in Declarations(document, "PackageReference"))
            {
                string id = Include(reference);
                if (!policy.DirectPackages.Contains(id) && !policy.Modules.ContainsKey(id)
                    && !policy.TestPackages.Contains(id) && !id.Equals(policy.SampleContracts, StringComparison.OrdinalIgnoreCase)
                    && !id.Equals(policy.DecorationPackage.Key, StringComparison.OrdinalIgnoreCase))
                {
                    failures.Add($"Test project {name} has an unapproved package {id}");
                }
            }

            foreach (XElement reference in Declarations(document, "ProjectReference"))
            {
                string include = Include(reference);
                if (include.Contains("$(", StringComparison.Ordinal))
                {
                    failures.Add($"Test project {name} has an unresolved project reference {include}");
                    continue;
                }

                string target = ResolveProject(project, include);
                if (!IsTestProject(root, target) && !IsProductionProject(root, target))
                {
                    failures.Add($"Test project {name} references an unapproved project {include}");
                }
            }
        }

        return failures.Order(StringComparer.Ordinal).ToArray();
    }

    private static void CheckIntegrity(DependencyPolicy policy, List<string> failures)
    {
        if (policy.SchemaVersion != 1)
        {
            failures.Add($"Dependency policy schemaVersion {policy.SchemaVersion} is unsupported; expected 1");
        }

        IEnumerable<string> production = policy.DirectPackages.Concat(policy.BaselinePackages.Keys)
            .Concat(policy.Modules.Keys).Append(policy.DecorationPackage.Key);
        foreach (string id in production.Distinct(StringComparer.OrdinalIgnoreCase).Order(StringComparer.Ordinal))
        {
            if (IsTestOnly(policy, id))
            {
                failures.Add($"Policy lists test-only package {id}/{Pin(policy, id) ?? "unresolved"} in production: Hexalith.McpCli > {id}/{Pin(policy, id) ?? "unresolved"}");
            }
        }

        foreach ((string id, string version) in policy.Modules.OrderBy(item => item.Key, StringComparer.Ordinal))
        {
            if (policy.DirectPackages.Contains(id) || policy.BaselinePackages.ContainsKey(id)
                || id.Equals(policy.DecorationPackage.Key, StringComparison.OrdinalIgnoreCase))
            {
                failures.Add($"Policy module {id}/{version} overlaps the non-module production lists: Hexalith.McpCli > {id}/{version}");
            }
        }
    }

    private static string? Pin(DependencyPolicy policy, string id)
        => id.Equals(policy.DecorationPackage.Key, StringComparison.OrdinalIgnoreCase) ? policy.DecorationPackage.Value
            : policy.Modules.GetValueOrDefault(id) ?? policy.BaselinePackages.GetValueOrDefault(id);

    private static bool IsTestOnly(DependencyPolicy policy, string id)
        => policy.TestPackages.Contains(id) || id.Equals(policy.SampleContracts, StringComparison.OrdinalIgnoreCase);

    private static IEnumerable<XElement> Items(XDocument document, string name)
        => document.Descendants().Where(item => item.Name.LocalName == name);

    private static IEnumerable<XElement> Declarations(XDocument document, string name)
        => Items(document, name).Where(item => item.Attribute("Include") is not null);

    private static string Include(XElement item) => (string?)item.Attribute("Include") ?? string.Empty;

    private static string ResolveProject(string project, string include)
        => Path.GetFullPath(Path.Combine(Path.GetDirectoryName(project)!, include.Replace('\\', Path.DirectorySeparatorChar)));

    private static bool IsTestProject(string root, string project)
        => project.StartsWith(Path.Combine(root, "tests") + Path.DirectorySeparatorChar, StringComparison.Ordinal);

    private static bool IsProductionProject(string root, string project)
    {
        string id = Path.GetFileNameWithoutExtension(project);
        return (id == "Hexalith.McpCli" || id.StartsWith("Hexalith.McpCli.", StringComparison.Ordinal))
            && Path.GetDirectoryName(project) == Path.Combine(root, "src", id);
    }
}
