using System.Text.Json;

using Hexalith.McpCli.AppHost;

namespace Hexalith.McpCli.Manifest.Tests;

/// <summary>Exercises actual private reader ownership, diagnostics, SDK policy and disposal without runtime services.</summary>
public sealed class NativeCatalogToolTests : IDisposable
{
    private readonly string _root = Path.Combine(Path.GetTempPath(), "mcpcli-native-tool-" + Guid.NewGuid().ToString("N"));

    /// <summary>Creates one task-owned fixture directory.</summary>
    public NativeCatalogToolTests() => Directory.CreateDirectory(_root);

    /// <summary>The exact SDK policy is installed before any private reader build can run.</summary>
    [Fact]
    public void PrivateReaderCopiesExactRootGlobalJson()
    {
        byte[] policy = "{\r\n  \"sdk\": { \"version\": \"10.0.403\", \"rollForward\": \"latestPatch\" }\r\n}\r\n"u8.ToArray();
        File.WriteAllBytes(Path.Combine(_root, "global.json"), policy);
        string build = Path.Combine(_root, "reader");
        NativeCatalogTool.PrepareBuildDirectory(_root, build);
        Assert.Equal(policy, File.ReadAllBytes(Path.Combine(build, "global.json")));
        Assert.Throws<InvalidDataException>(() => NativeCatalogTool.PrepareBuildDirectory(_root, build));
        Assert.Equal(policy, File.ReadAllBytes(Path.Combine(build, "global.json")));
    }

    /// <summary>The actual generation path installs SDK policy before it can reach any dotnet process.</summary>
    [Fact]
    public async Task GenerationInstallsRootPolicyBeforeBuildPreparation()
    {
        byte[] policy = "{ \"sdk\": { \"version\": \"10.0.403\" } }"u8.ToArray();
        File.WriteAllBytes(Path.Combine(_root, "global.json"), policy);
        string template = Path.Combine(_root, "references", "Hexalith.Platform", "src", "Hexalith.Platform.CatalogBuilder");
        Directory.CreateDirectory(template);
        File.WriteAllText(Path.Combine(template, "Hexalith.Platform.CatalogBuilder.csproj"), "<Project />");
        string directory = Owned("generation", "owner");
        string absentOwner = Path.Combine(_root, "absent-owner.dll");
        await Assert.ThrowsAsync<FileNotFoundException>(() => NativeCatalogTool.GenerateAsync(new DirectoryInfo(_root), directory,
            "instance", "eventstore", "4.0.4", [(absentOwner, absentOwner, "parties")], TestContext.Current.CancellationToken));
        Assert.Equal(policy, File.ReadAllBytes(Path.Combine(directory, "reader", "global.json")));
    }

    /// <summary>Failed preparation retains bounded redacted diagnostics and the original failure before removing owned files.</summary>
    [Fact]
    public async Task FailedPreparationPropagatesSanitizedDiagnosticsBeforeCleanup()
    {
        string path = Path.Combine(_root, "preparation");
        var original = new InvalidOperationException("reader failed");
        Exception actual = await Assert.ThrowsAsync<InvalidOperationException>(() => NativeCatalogTool.RunOwnedPreparationAsync(path, "owner", () =>
        {
            Directory.CreateDirectory(Path.Combine(path, "reader"));
            File.WriteAllText(Path.Combine(path, "reader", "build.log"), "compiler error NU1109\nSigningKey=private-key-value\neyJprivate.payload.signature\n-----BEGIN PRIVATE KEY-----\nkey bytes\n-----END PRIVATE KEY-----\n" + new string('x', 40_000));
            return Task.FromException(original);
        }));
        Assert.Same(original, actual);
        string diagnostics = Assert.IsType<string>(actual.Data["NativeCatalogDiagnostics"]);
        Assert.Contains("NU1109", diagnostics, StringComparison.Ordinal);
        Assert.DoesNotContain("private-key-value", diagnostics, StringComparison.Ordinal);
        Assert.DoesNotContain("eyJprivate.payload.signature", diagnostics, StringComparison.Ordinal);
        Assert.DoesNotContain("key bytes", diagnostics, StringComparison.Ordinal);
        Assert.True(diagnostics.Length < 16_500);
        Assert.False(Directory.Exists(path));
    }

    /// <summary>CI-compatible sanitization also covers direct and multiply escaped JSON key diagnostics.</summary>
    [Theory]
    [InlineData("{\"SigningKey\":\"do-not-retain\"}")]
    [InlineData("{\\\"PrivateKey\\\":\\\"do-not-retain\\\"}")]
    [InlineData("{\"SigningKey\":\"do-not-retain")]
    [InlineData("{\\\"PrivateKey\\\":\\\"do-not-retain")]
    public void NamedJsonKeyDiagnosticsAreRedacted(string diagnostic)
    {
        string sanitized = NativeCatalogDiagnostics.Sanitize(diagnostic);
        Assert.DoesNotContain("do-not-retain", sanitized, StringComparison.Ordinal);
        Assert.Contains("REDACTED", sanitized, StringComparison.Ordinal);
    }

    /// <summary>Existing foreign paths and mismatched ownership markers are never removed or overwritten.</summary>
    [Fact]
    public async Task ForeignDirectoryRefusesPreparationAndDeletion()
    {
        string path = Owned("foreign", "someone-else");
        File.WriteAllText(Path.Combine(path, "retained.txt"), "retained");
        bool invoked = false;
        await Assert.ThrowsAsync<InvalidDataException>(() => NativeCatalogTool.RunOwnedPreparationAsync(path, "owner", () => { invoked = true; return Task.CompletedTask; }));
        Assert.False(invoked);
        Assert.Throws<InvalidDataException>(() => NativeCatalogTool.DeleteOwnedDirectory(path, "owner"));
        Assert.Equal("retained", File.ReadAllText(Path.Combine(path, "retained.txt")));
    }

    /// <summary>Kill and exit-confirmation failures cannot release ownership of a potentially running reader.</summary>
    [Fact]
    public async Task KillFailurePreservesUnconfirmedProcessOwnership()
    {
        string path = Path.Combine(_root, "unconfirmed");
        var original = new OperationCanceledException("cancelled");
        Exception actual = await Assert.ThrowsAsync<OperationCanceledException>(() => NativeCatalogTool.RunOwnedPreparationAsync(path, "owner", async () =>
        {
            await NativeCatalogTool.ConfirmTerminationAsync(() => throw new IOException("kill failed"),
                _ => Task.FromException(new TimeoutException("exit unconfirmed")), original);
            throw original;
        }));
        Assert.Same(original, actual);
        Assert.True(actual.Data.Contains("CatalogOwnedProcessStillRunning"));
        Assert.Equal("owner", File.ReadAllText(Path.Combine(path, ".owner")));
    }

    /// <summary>A failed kill remains safe to clean once process exit has independently been confirmed.</summary>
    [Fact]
    public async Task ConfirmedExitClearsUnconfirmedMarkerEvenWhenKillRacesExit()
    {
        var original = new OperationCanceledException("cancelled");
        await NativeCatalogTool.ConfirmTerminationAsync(() => throw new InvalidOperationException("already exited"), _ => Task.CompletedTask, original);
        Assert.False(original.Data.Contains("CatalogOwnedProcessStillRunning"));
        Assert.True(original.Data.Contains("CatalogKillFailure"));
    }

    /// <summary>Actual runtime disposal attempts both SDK disposals and both independent owned directories.</summary>
    [Fact]
    public async Task DisposalFailureDoesNotSkipOtherOwnedCleanup()
    {
        var first = new InvalidOperationException("catalog disposal failed");
        int disposed = 0;
        var catalog = new NativeCatalogTestDisposable(() => { disposed++; throw first; });
        var tenant = new NativeCatalogTestDisposable(() => { disposed++; throw new IOException("metadata disposal failed"); });
        string reader = Owned("reader", "owner"), custody = Owned("custody", "owner");
        var runtime = new NativeCatalogRuntime(tenant, catalog, reader, "owner", custody);
        Exception actual = await Assert.ThrowsAsync<InvalidOperationException>(async () => await runtime.DisposeAsync());
        Assert.Same(first, actual);
        Assert.Equal(2, disposed);
        Assert.False(Directory.Exists(reader));
        Assert.False(Directory.Exists(custody));
    }

    /// <summary>Disposal still attempts independent SDK cleanup while retaining ownership if exit remains unconfirmed.</summary>
    [Fact]
    public async Task UnconfirmedDisposalRetainsReaderAndCustody()
    {
        var original = new InvalidOperationException("exit unconfirmed");
        original.Data["CatalogOwnedProcessStillRunning"] = true;
        int otherDisposed = 0;
        var catalog = new NativeCatalogTestDisposable(() => throw original);
        var tenant = new NativeCatalogTestDisposable(() => { otherDisposed++; return ValueTask.CompletedTask; });
        string reader = Owned("unconfirmed-reader", "owner"), custody = Owned("unconfirmed-custody", "owner");
        var runtime = new NativeCatalogRuntime(tenant, catalog, reader, "owner", custody);
        Exception actual = await Assert.ThrowsAsync<InvalidOperationException>(async () => await runtime.DisposeAsync());
        Assert.Same(original, actual);
        Assert.Equal(1, otherDisposed);
        Assert.True(Directory.Exists(reader));
        Assert.True(Directory.Exists(custody));
    }

    /// <summary>The startup cleanup path retains its original failure even if partial SDK and foreign cleanup also fail.</summary>
    [Fact]
    public async Task PartialStartupCleanupPreservesOriginalAndAttemptsEveryAction()
    {
        var original = new InvalidDataException("startup failed");
        string foreign = Owned("foreign-startup", "foreign"), owned = Owned("owned-startup", "owner");
        int attempted = 0;
        await NativeCatalogCleanup.RunAsync(original,
            () => { attempted++; throw new IOException("partial SDK disposal failed"); },
            () => { attempted++; NativeCatalogTool.DeleteOwnedDirectory(foreign, "owner"); return ValueTask.CompletedTask; },
            () => { attempted++; NativeCatalogTool.DeleteOwnedDirectory(owned, "owner"); return ValueTask.CompletedTask; });
        Assert.Equal(3, attempted);
        Assert.True(original.Data.Contains("CatalogCleanupFailures"));
        Assert.True(Directory.Exists(foreign));
        Assert.False(Directory.Exists(owned));
    }

    /// <summary>Existing credential-free inventories remain readable after private preparation receipts are disposed.</summary>
    [Fact]
    public void PreparationInventoriesSurviveReceiptDeletionWithoutRawEnvironment()
    {
        string tenant = Path.Combine(_root, "tenant.json"), party = Path.Combine(_root, "party.json");
        File.WriteAllText(tenant, JsonSerializer.Serialize(new
        {
            project = "tenants", projectSha256 = "project-hash", buildEnvironmentDigest = "environment-digest",
            buildEnvironment = new { SigningKey = "private-environment-value" }, custody = "private-custody",
            dependencies = new[] { new { name = "SDK.dll", sha256 = "sdk-hash" } },
            loadedSdk = new[] { new { assembly = "SDK", moduleVersionId = "mvid", sha256 = "sdk-image-hash" } },
            declarations = new[] { "owner-route" }, operations = new[] { new { RouteId = "owner-route", Digest = "operation-hash" } },
        }));
        File.WriteAllText(party, JsonSerializer.Serialize(new { templateHash = "program-hash", templateProjectSha256 = "template-project-hash",
            readerProjectSha256 = "reader-project-hash", globalJsonSha256 = "sdk-policy-hash", inputHashes = new Dictionary<string, string> { ["adapter.dll"] = "adapter-hash" },
            privateKey = "private-reader-value" }));
        var retained = NativeCatalogPreparationEvidence.Capture(tenant, party);
        File.Delete(tenant); File.Delete(party);
        string json = retained.ToJsonString();
        Assert.Contains("sdk-image-hash", json, StringComparison.Ordinal);
        Assert.Contains("reader-project-hash", json, StringComparison.Ordinal);
        Assert.Contains("template-project-hash", json, StringComparison.Ordinal);
        Assert.Contains("environment-digest", json, StringComparison.Ordinal);
        Assert.DoesNotContain("private-environment-value", json, StringComparison.Ordinal);
        Assert.DoesNotContain("private-reader-value", json, StringComparison.Ordinal);
        Assert.DoesNotContain("private-custody", json, StringComparison.Ordinal);
    }

    private string Owned(string name, string owner)
    {
        string path = Path.Combine(_root, name);
        NativeCatalogTool.CreatePrivateDirectory(path);
        File.WriteAllText(Path.Combine(path, ".owner"), owner);
        return path;
    }

    /// <inheritdoc />
    public void Dispose() => Directory.Delete(_root, recursive: true);
}
