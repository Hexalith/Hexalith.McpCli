using System.IO.Compression;
using System.Security.Cryptography;
using System.Text.Json;

using Hexalith.McpCli.AppHost;

namespace Hexalith.McpCli.Manifest.Tests;

/// <summary>Protects the exact online audit coverage required before an isolated metadata build.</summary>
public sealed class NativeCatalogAuditTests : IDisposable
{
    private readonly string _packageHash;
    private readonly string _root = Path.Combine(Path.GetTempPath(), "mcpcli-reader-audit-" + Guid.NewGuid().ToString("N"));

    /// <summary>Creates only inert reader input files and a credential-free online audit inventory.</summary>
    public NativeCatalogAuditTests()
    {
        string[] inputs = ["global.json", "Directory.Build.props", "Directory.Packages.props",
            "references/Hexalith.Platform/src/Hexalith.Platform.CatalogBuilder/Hexalith.Platform.CatalogBuilder.csproj",
            "references/Hexalith.Platform/src/Hexalith.Platform.CatalogBuilder/Program.cs"];
        var hashes = new Dictionary<string, string>();
        foreach (string input in inputs)
        {
            string path = Path.Combine(_root, input);
            Directory.CreateDirectory(Path.GetDirectoryName(path)!);
            File.WriteAllText(path, input);
            hashes.Add(input, Digest(path));
        }
        string folder = Path.Combine(_root, "packages", "sdk", "4.0.4");
        Directory.CreateDirectory(Path.Combine(folder, "lib"));
        File.Copy(typeof(NativeCatalogAuditTests).Assembly.Location, Path.Combine(folder, "lib", "Fixture.dll"));
        string archive = Path.Combine(folder, "sdk.4.0.4.nupkg");
        using (ZipArchive package = ZipFile.Open(archive, ZipArchiveMode.Create))
            package.CreateEntryFromFile(Path.Combine(folder, "lib", "Fixture.dll"), "lib/Fixture.dll");
        _packageHash = Convert.ToBase64String(SHA512.HashData(File.ReadAllBytes(archive)));
        File.WriteAllText(Path.Combine(_root, "audit.json"), JsonSerializer.Serialize(new
        {
            schemaVersion = 1, result = "audited", sdkVersion = "4.0.4", inputs = hashes,
            packages = new Dictionary<string, string> { ["SDK/4.0.4"] = _packageHash },
            archives = new Dictionary<string, string> { ["SDK/4.0.4"] = _packageHash },
        }));
    }

    /// <summary>Matching exact packages are retained while any uncovered, changed or missing package hash refuses.</summary>
    [Theory]
    [InlineData("matching")]
    [InlineData("uncovered")]
    [InlineData("changed")]
    [InlineData("missing")]
    [InlineData("empty")]
    [InlineData("archive-tampered")]
    [InlineData("asset-tampered")]
    [InlineData("unarchived-asset")]
    public void ReaderGraphRequiresExactAuditedPackageBytes(string kind)
    {
        string proof = Path.Combine(_root, "audit.json");
        using JsonDocument audit = NativeCatalogAudit.Load(_root, proof, Digest(proof), "4.0.4");
        var libraries = new Dictionary<string, object>();
        if (kind != "empty") libraries.Add(kind == "uncovered" ? "Other/1.0.0" : "SDK/4.0.4",
            kind == "missing" ? new { type = "package" } : (object)new { type = "package", sha512 = kind == "changed" ? "different-hash" : _packageHash });
        string folder = Path.Combine(_root, "packages", "sdk", "4.0.4");
        if (kind == "archive-tampered") File.AppendAllText(Path.Combine(folder, "sdk.4.0.4.nupkg"), "tampered");
        if (kind == "asset-tampered") File.AppendAllText(Path.Combine(folder, "lib", "Fixture.dll"), "tampered");
        var target = new Dictionary<string, object> { ["SDK/4.0.4"] = new
        {
            compile = new Dictionary<string, object> { [kind == "unarchived-asset" ? "lib/Unknown.dll" : "lib/Fixture.dll"] = new { } },
        } };
        using JsonDocument assets = JsonDocument.Parse(JsonSerializer.Serialize(new { libraries,
            packageFolders = new Dictionary<string, object> { [Path.Combine(_root, "packages")] = new { } },
            targets = new Dictionary<string, object> { ["net10.0"] = target } }));
        if (kind == "matching") Assert.Equal(_packageHash, NativeCatalogAudit.RequireCoverage(assets.RootElement, audit.RootElement)["SDK/4.0.4"]);
        else Assert.Throws<InvalidDataException>(() => NativeCatalogAudit.RequireCoverage(assets.RootElement, audit.RootElement));
    }

    /// <summary>Authentic published package bytes and the actual restored consumed assets satisfy the same verifier.</summary>
    [Fact]
    public void PublishedArchiveAndConsumedAssetsMatchActualCacheBytes()
    {
        string root = DependencyPolicyTests.FindRepositoryRoot();
        using JsonDocument restored = JsonDocument.Parse(File.ReadAllBytes(Path.Combine(root, "tests", "Hexalith.McpCli.AppHost", "obj", "project.assets.json")));
        const string identity = "Hexalith.EventStore.Client/4.0.4";
        JsonElement library = restored.RootElement.GetProperty("libraries").GetProperty(identity);
        string cache = restored.RootElement.GetProperty("packageFolders").EnumerateObject().Select(item => item.Name)
            .Single(folder => File.Exists(Path.Combine(folder, "hexalith.eventstore.client", "4.0.4", "hexalith.eventstore.client.4.0.4.nupkg")));
        string archive = Path.Combine(cache, "hexalith.eventstore.client", "4.0.4", "hexalith.eventstore.client.4.0.4.nupkg");
        using JsonDocument selection = JsonDocument.Parse(File.ReadAllBytes(Path.Combine(root, "tools", "live-topology", "native-runtime.json")));
        Assert.Equal(selection.RootElement.GetProperty("packages").EnumerateArray().Single(item => item.GetProperty("id").GetString() == "Hexalith.EventStore.Client")
            .GetProperty("sha256").GetString(), Digest(archive));
        string archiveHash = Convert.ToBase64String(SHA512.HashData(File.ReadAllBytes(archive)));
        using JsonDocument audit = JsonDocument.Parse(JsonSerializer.Serialize(new
        {
            packages = new Dictionary<string, string> { [identity] = library.GetProperty("sha512").GetString()! },
            archives = new Dictionary<string, string> { [identity] = archiveHash },
        }));
        using JsonDocument assets = JsonDocument.Parse(JsonSerializer.Serialize(new
        {
            libraries = new Dictionary<string, JsonElement> { [identity] = library },
            packageFolders = new Dictionary<string, object> { [cache] = new { } },
            targets = new Dictionary<string, object> { ["net10.0"] = new Dictionary<string, JsonElement>
                { [identity] = restored.RootElement.GetProperty("targets").GetProperty("net10.0").GetProperty(identity) } },
        }));
        Assert.Equal(library.GetProperty("sha512").GetString(), NativeCatalogAudit.RequireCoverage(assets.RootElement, audit.RootElement)[identity]);
    }

    /// <summary>Changed receipt, SDK version or reader inputs cannot reuse the retained audit.</summary>
    [Theory]
    [InlineData("receipt")]
    [InlineData("sdk")]
    [InlineData("input")]
    public void ChangedAuditInputsRefuseBeforeOfflineBuild(string kind)
    {
        string proof = Path.Combine(_root, "audit.json");
        string hash = Digest(proof);
        if (kind == "receipt") File.AppendAllText(proof, " ");
        if (kind == "input") File.AppendAllText(Path.Combine(_root, "global.json"), "changed");
        Assert.Throws<InvalidDataException>(() => NativeCatalogAudit.Load(_root, proof, hash, kind == "sdk" ? "different" : "4.0.4"));
    }

    private static string Digest(string path) => Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(path)));

    /// <inheritdoc />
    public void Dispose() => Directory.Delete(_root, recursive: true);
}
