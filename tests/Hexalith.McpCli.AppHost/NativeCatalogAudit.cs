using System.IO.Compression;
using System.Security.Cryptography;
using System.Text.Json;

namespace Hexalith.McpCli.AppHost;

/// <summary>Binds an isolated metadata reader to exact package bytes already audited in online preparation.</summary>
internal static class NativeCatalogAudit
{
    /// <summary>Requires the retained online proof and unchanged reader SDK/project/template inputs before disabling refresh.</summary>
    internal static JsonDocument Load(string root, string path, string expectedHash, string sdkVersion)
    {
        byte[] bytes = File.ReadAllBytes(path);
        if (Convert.ToHexStringLower(SHA256.HashData(bytes)) != expectedHash)
            throw new InvalidDataException("The native reader online audit proof differs from preparation.");
        JsonDocument document = JsonDocument.Parse(bytes);
        try
        {
            JsonElement audit = document.RootElement;
            if (audit.GetProperty("schemaVersion").GetInt32() != 1 || audit.GetProperty("result").GetString() != "audited"
                || audit.GetProperty("sdkVersion").GetString() != sdkVersion || !audit.GetProperty("packages").EnumerateObject().Any())
                throw new InvalidDataException("A complete matching online reader audit is required.");
            string[] inputs = ["global.json", "Directory.Build.props", "Directory.Packages.props",
                "references/Hexalith.Builds/Props/Directory.Packages.props",
                "references/Hexalith.Platform/src/Hexalith.Platform.CatalogBuilder/Hexalith.Platform.CatalogBuilder.csproj",
                "references/Hexalith.Platform/src/Hexalith.Platform.CatalogBuilder/Program.cs",
                "references/Hexalith.Platform/src/Hexalith.Platform.CatalogBuilder/PublishedCatalogArtifactCohort.cs"];
            if (audit.GetProperty("packages").EnumerateObject().Any(package =>
                !audit.GetProperty("archives").TryGetProperty(package.Name, out JsonElement archive) || string.IsNullOrEmpty(archive.GetString())))
                throw new InvalidDataException("The online audit must retain actual archive hashes.");
            JsonElement retained = audit.GetProperty("inputs");
            if (retained.EnumerateObject().Count() != inputs.Length || inputs.Any(name =>
                !retained.TryGetProperty(name, out JsonElement digest)
                || digest.GetString() != Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(Path.Combine(root, name))))))
                throw new InvalidDataException("The reader inputs differ from their online audited graph.");
            return document;
        }
        catch { document.Dispose(); throw; }
    }

    /// <summary>Every resolved package must have the exact content hash retained by an online all-dependency audit.</summary>
    internal static Dictionary<string, string> RequireCoverage(JsonElement assets, JsonElement audit)
    {
        JsonElement audited = audit.GetProperty("packages");
        var graph = new Dictionary<string, string>(StringComparer.Ordinal);
        foreach (JsonProperty library in assets.GetProperty("libraries").EnumerateObject())
        {
            if (library.Value.GetProperty("type").GetString() != "package") continue;
            string? hash = library.Value.TryGetProperty("sha512", out JsonElement value) ? value.GetString() : null;
            if (string.IsNullOrWhiteSpace(hash) || !audited.TryGetProperty(library.Name, out JsonElement expected)
                || expected.GetString() != hash)
                throw new InvalidDataException("The isolated reader resolved a package outside its exact online audited graph: " + library.Name + ".");
            VerifyPackageBytes(assets, audit, library.Name, library.Value);
            graph.Add(library.Name, hash);
        }
        if (graph.Count == 0) throw new InvalidDataException("The isolated reader has no audited package graph.");
        return graph;
    }

    private static void VerifyPackageBytes(JsonElement assets, JsonElement audit, string identity, JsonElement library)
    {
        string relative = identity.ToLowerInvariant();
        string filename = relative.Replace('/', '.') + ".nupkg";
        string? folder = assets.GetProperty("packageFolders").EnumerateObject()
            .Select(root => Path.Combine(root.Name, relative)).SingleOrDefault(path => File.Exists(Path.Combine(path, filename)));
        if (folder is null) throw new InvalidDataException("The audited package archive is unavailable: " + identity + ".");
        string archivePath = Path.Combine(folder, filename);
        using (FileStream source = File.OpenRead(archivePath))
            if (Convert.ToBase64String(SHA512.HashData(source)) != audit.GetProperty("archives").GetProperty(identity).GetString())
                throw new InvalidDataException("The cached archive differs from the actual online audited bytes: " + identity + ".");
        using ZipArchive archive = ZipFile.OpenRead(archivePath);
        foreach (ZipArchiveEntry entry in archive.Entries)
        {
            if (entry.FullName.EndsWith('/') || entry.FullName == "[Content_Types].xml" || entry.FullName == "_rels/.rels"
                || entry.FullName.StartsWith("package/services/metadata/core-properties/", StringComparison.Ordinal)
                    && entry.FullName.EndsWith(".psmdcp", StringComparison.Ordinal)) continue;
            string name = entry.FullName.EndsWith(".nuspec", StringComparison.OrdinalIgnoreCase) && !entry.FullName.Contains('/')
                ? entry.FullName.ToLowerInvariant() : entry.FullName;
            RequireEntryBytes(folder, name, entry);
        }
        // Include every consumed target asset, refusing any generated metadata that selects a file absent from its archive.
        string[] groups = ["compile", "runtime", "native", "resource", "build", "buildMultiTargeting", "buildTransitive", "analyzers", "contentFiles", "runtimeTargets"];
        foreach (JsonProperty target in assets.GetProperty("targets").EnumerateObject())
            if (target.Value.TryGetProperty(identity, out JsonElement package))
                foreach (string group in groups)
                    if (package.TryGetProperty(group, out JsonElement files))
                        foreach (JsonProperty file in files.EnumerateObject())
                        {
                            // NuGet records _._ for an empty asset group without extracting a file.
                            if (file.Name.StartsWith(group + "/", StringComparison.Ordinal)
                                && file.Name.EndsWith("/_._", StringComparison.Ordinal)
                                && !file.Name.Contains("../", StringComparison.Ordinal)
                                && !file.Name.Contains('\\')
                                && archive.GetEntry(file.Name) is null
                                && !File.Exists(Path.Combine(folder, file.Name))) continue;
                            RequireEntryBytes(folder, file.Name, archive.GetEntry(file.Name)
                                ?? throw new InvalidDataException("A consumed reader asset is absent from its audited archive: "
                                    + identity + "/" + file.Name + "."));
                        }
    }

    private static void RequireEntryBytes(string folder, string relative, ZipArchiveEntry entry)
    {
        string path = Path.GetFullPath(Path.Combine(folder, relative));
        if (!path.StartsWith(Path.GetFullPath(folder) + Path.DirectorySeparatorChar, StringComparison.Ordinal) || relative.Contains('\\'))
            throw new InvalidDataException("An audited archive asset escapes its package directory.");
        using Stream archived = entry.Open();
        using FileStream consumed = File.OpenRead(path);
        if (!SHA512.HashData(archived).AsSpan().SequenceEqual(SHA512.HashData(consumed)))
            throw new InvalidDataException("A consumed reader asset differs from its audited archive: " + relative + ".");
    }
}
