using System.Security.Cryptography;
using System.Text.Json;

using Hexalith.EventStore.Contracts.Routing;
using Hexalith.McpCli.Integration.Tests;

namespace Hexalith.McpCli.Manifest.Tests;

/// <summary>Rejects invalid SDK readbacks without starting or replacing SDK activation authority.</summary>
public sealed class NativeCatalogEvidenceTests : IDisposable
{
    private readonly string _root = Path.Combine(Path.GetTempPath(), "mcpcli-native-readback-" + Guid.NewGuid().ToString("N"));
    private readonly string[] _hosts = ["eventstore", "parties", "tenants"];

    /// <summary>Creates a synthetic immutable backup and actual SDK-schema coordination documents for verifier controls only.</summary>
    public NativeCatalogEvidenceTests()
    {
        Directory.CreateDirectory(_root);
        string backup = Path.Combine(_root, "initial.rdb");
        File.WriteAllBytes(backup, "REDIS0000"u8.ToArray());
        File.WriteAllText(Receipt, JsonSerializer.Serialize(new { databaseSize = 0, createdBeforeApplications = true, backupFile = backup,
            sha256 = Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(backup))) }));
        File.WriteAllText(Path.Combine(_root, "native-catalog-coordinates.json"), JsonSerializer.Serialize(new
        {
            directory = _root, rootDigest = "actual-root", hosts = _hosts,
            inputs = new { preparations = new { tenantPreparation = new { dependencies = new[] { new { name = "SDK.dll", sha256 = "sdk-hash" } } } } },
        }));
        foreach (string host in _hosts) Write(host, Readback());
    }

    private string Receipt => Path.Combine(_root, "backup.json");
    private string Evidence => Path.Combine(_root, "native-catalog.json");

    /// <summary>Wrong roots, non-serving or incomplete participants, and disagreement cannot leave a successful receipt.</summary>
    [Theory]
    [InlineData("wrong-root")]
    [InlineData("not-serving")]
    [InlineData("incomplete-hosts")]
    [InlineData("missing-owner-executable")]
    [InlineData("disagreeing-readbacks")]
    public async Task InvalidReadbackRefusesWithoutNativeEvidence(string defect)
    {
        RouteCatalogGenerationReadback actual = defect switch
        {
            "wrong-root" => Readback() with { RootDigest = "wrong-root" },
            "not-serving" => Readback() with { Serving = false },
            "incomplete-hosts" => Readback() with { RequiredHosts = Readback().RequiredHosts.Take(2).ToArray() },
            "missing-owner-executable" => Readback() with { RequiredHosts = Readback().RequiredHosts.Select(peer =>
                peer.HostId == "parties" ? peer with { ExecutableDigest = null } : peer).ToArray() },
            _ => Readback() with { Epoch = 2 },
        };
        Write("tenants", actual);
        File.WriteAllText(Evidence, "stale success");
        await Assert.ThrowsAsync<InvalidDataException>(() => NativeCatalogEvidence.RequireAsync(Receipt, TestContext.Current.CancellationToken));
        Assert.False(File.Exists(Evidence));
    }

    /// <summary>Matching SDK-schema readbacks retain their safe inventories without mutating any authority.</summary>
    [Fact]
    public async Task MatchingReadbacksRetainSanitizedInventory()
    {
        await NativeCatalogEvidence.RequireAsync(Receipt, TestContext.Current.CancellationToken);
        using JsonDocument evidence = JsonDocument.Parse(File.ReadAllBytes(Evidence));
        Assert.Equal("passed", evidence.RootElement.GetProperty("result").GetString());
        Assert.Contains("sdk-hash", evidence.RootElement.GetProperty("inputs").GetRawText(), StringComparison.Ordinal);
    }

    private RouteCatalogGenerationReadback Readback() => new(1, 1, "actual-root", "routes", "admission", "Development",
        _hosts.Select(host => new RouteCatalogHostIdentity(host, host, "inventory", "topology", "authentication")
            { ExecutableDigest = host == "eventstore" ? null : "executable" }).ToArray(), true)
        { AttemptId = "attempt", ActivationBindingDigest = "binding" };

    private void Write(string host, RouteCatalogGenerationReadback readback)
        => File.WriteAllText(Path.Combine(_root, host + ".committed.json"), JsonSerializer.Serialize(readback));

    /// <inheritdoc />
    public void Dispose() => Directory.Delete(_root, recursive: true);
}
