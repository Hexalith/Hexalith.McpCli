using System.Diagnostics;
using System.Reflection;
using System.Text.Json;
using System.IO.Compression;
using System.Security.Cryptography;

using Hexalith.McpCli.AppHost;

namespace Hexalith.McpCli.Manifest.Tests;

/// <summary>Exercises actual private reader ownership, diagnostics, SDK policy and disposal without runtime services.</summary>
[Collection("TopologyFixtureEnvironment")]
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

    /// <summary>Actual GenerateAsync must restore and reject unaudited or tampered packages before build or catalog execution.</summary>
    [Theory]
    [InlineData("uncovered")]
    [InlineData("changed")]
    [InlineData("archive")]
    [InlineData("asset")]
    [InlineData("matching")]
    [InlineData("cohort-source-missing")]
    [InlineData("cohort-source-changed")]
    [InlineData("copy-cohort-before-build")]
    [InlineData("source-cohort-after-generation")]
    [InlineData("copy-cohort-after-generation")]
    [InlineData("extra-source-after-generation")]
    [InlineData("matching-generated")]
    [InlineData("copy-before-seal-program")]
    [InlineData("copy-before-seal-cohort")]
    [InlineData("copy-before-seal-project")]
    [InlineData("copy-before-seal-bindings")]
    [InlineData("copy-before-seal-global")]
    [InlineData("catalog-source-missing")]
    [InlineData("catalog-source-changed")]
    [InlineData("catalog-source-after-restore")]
    [InlineData("copy-cohort-after-build")]
    [InlineData("uppercase-source-after-build")]
    public async Task ActualReaderValidatesRestoredBytesBeforeCompilation(string kind)
    {
        string template = Path.Combine(_root, "references", "Hexalith.Platform", "src", "Hexalith.Platform.CatalogBuilder");
        Directory.CreateDirectory(template);
        File.WriteAllText(Path.Combine(template, "Hexalith.Platform.CatalogBuilder.csproj"), "<Project />");
        File.WriteAllText(Path.Combine(template, "Program.cs"), "// inert managed reader template");
        string cohort = Path.Combine(template, "PublishedCatalogArtifactCohort.cs");
        File.WriteAllText(cohort, "// inert managed cohort source");
        foreach (string input in new[] { "global.json", "Directory.Build.props", "Directory.Packages.props" })
            File.WriteAllText(Path.Combine(_root, input), input == "global.json" ? "{}" : "<Project />");
        string catalog = Path.Combine(_root, "references", "Hexalith.Builds", "Props", "Directory.Packages.props");
        Directory.CreateDirectory(Path.GetDirectoryName(catalog)!);
        File.WriteAllText(catalog, "<Project />");
        string fallback = Path.Combine(_root, "sibling-catalog.props");
        File.WriteAllText(fallback, "<Project />");
        string owner = Path.Combine(_root, "managed-owner", "Owner.dll");
        Directory.CreateDirectory(Path.GetDirectoryName(owner)!);
        File.Copy(typeof(NativeCatalogToolTests).Assembly.Location, owner);
        string cache = Path.Combine(_root, "packages");
        string package = Path.Combine(cache, "hexalith.eventstore.client", "4.0.4");
        Directory.CreateDirectory(Path.Combine(package, "lib"));
        string asset = Path.Combine(package, "lib", "Fixture.dll");
        File.Copy(owner, asset);
        string archive = Path.Combine(package, "hexalith.eventstore.client.4.0.4.nupkg");
        using (ZipArchive zip = ZipFile.Open(archive, ZipArchiveMode.Create)) zip.CreateEntryFromFile(asset, "lib/Fixture.dll");
        string digest = Convert.ToBase64String(SHA512.HashData(File.ReadAllBytes(archive)));
        string identity = "Hexalith.EventStore.Client/4.0.4";
        var inputs = new[] { "global.json", "Directory.Build.props", "Directory.Packages.props",
            "references/Hexalith.Builds/Props/Directory.Packages.props",
            "references/Hexalith.Platform/src/Hexalith.Platform.CatalogBuilder/Hexalith.Platform.CatalogBuilder.csproj",
            "references/Hexalith.Platform/src/Hexalith.Platform.CatalogBuilder/Program.cs",
            "references/Hexalith.Platform/src/Hexalith.Platform.CatalogBuilder/PublishedCatalogArtifactCohort.cs" }.ToDictionary(name => name,
                name => Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(Path.Combine(_root, name)))));
        string audit = Path.Combine(_root, "audit.json");
        string auditedIdentity = kind == "uncovered" ? "Other/1.0.0" : identity;
        File.WriteAllText(audit, JsonSerializer.Serialize(new { schemaVersion = 1, result = "audited", sdkVersion = "4.0.4", inputs,
            packages = new Dictionary<string, string> { [auditedIdentity] = digest },
            archives = new Dictionary<string, string> { [auditedIdentity] = digest } }));
        string restored = Path.Combine(_root, "restored.json");
        File.WriteAllText(restored, JsonSerializer.Serialize(new
        {
            libraries = new Dictionary<string, object> { [identity] = new { type = "package", sha512 = kind == "changed" ? "changed-hash" : digest } },
            packageFolders = new Dictionary<string, object> { [cache] = new { } },
            targets = new Dictionary<string, object> { ["net10.0"] = new Dictionary<string, object> { [identity] = new
            { compile = new Dictionary<string, object> { ["lib/Fixture.dll"] = new { } } } } },
        }));
        if (kind == "archive") File.AppendAllText(archive, "changed archive");
        if (kind == "asset") File.AppendAllText(asset, "changed consumed assembly");
        if (kind == "cohort-source-missing") File.Delete(cohort);
        if (kind == "cohort-source-changed") File.AppendAllText(cohort, "changed source");
        if (kind == "catalog-source-missing") File.Delete(catalog);
        if (kind == "catalog-source-changed") File.AppendAllText(catalog, "changed source");
        string bin = Path.Combine(_root, "controlled-dotnet");
        Directory.CreateDirectory(bin);
        string configuration = new DirectoryInfo(AppContext.BaseDirectory).Parent!.Name;
        string stub = Path.Combine(DependencyPolicyTests.FindRepositoryRoot(), "tests", "fixtures", "Topology.DaprStub", "bin", configuration, "net10.0");
        foreach (string file in Directory.EnumerateFiles(stub)) File.Copy(file, Path.Combine(bin, Path.GetFileName(file)));
        File.Move(Path.Combine(bin, OperatingSystem.IsWindows() ? "dapr.exe" : "dapr"), Path.Combine(bin, OperatingSystem.IsWindows() ? "dotnet.exe" : "dotnet"));
        string calls = Path.Combine(_root, "calls.jsonl");
        var environment = new Dictionary<string, string?>
        {
            ["PATH"] = bin + Path.PathSeparator + Environment.GetEnvironmentVariable("PATH"),
            ["MCPCLI_TEST_READER_ASSETS"] = restored, ["MCPCLI_TEST_READER_CALLS"] = calls,
            ["MCPCLI_TEST_READER_BEHAVIOR"] = kind.Contains("-generation", StringComparison.Ordinal)
                || kind.EndsWith("-after-build", StringComparison.Ordinal)
                || kind is "matching-generated" or "copy-cohort-before-build" or "catalog-source-after-restore" ? kind : null,
            ["MCPCLI_TEST_READER_CATALOG_SOURCE"] = catalog,
            ["CustomAfterMicrosoftCommonTargets"] = fallback,
            ["MCPCLI_TEST_READER_COHORT_SOURCE"] = cohort,
            ["MCPCLI_NATIVE_READER_AUDIT_PATH"] = audit,
            ["MCPCLI_NATIVE_READER_AUDIT_SHA256"] = Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(audit))),
        };
        var prior = environment.ToDictionary(pair => pair.Key, pair => Environment.GetEnvironmentVariable(pair.Key));
        string directory = Path.Combine(_root, "actual-reader");
        Action<string>? priorObserver = NativeCatalogTool.InputsCopiedObserver.Value;
        int copyStageCalls = 0;
        NativeCatalogTool.InputsCopiedObserver.Value = reader =>
        {
            copyStageCalls++;
            string? name = kind switch
            {
                "copy-before-seal-program" => "Program.cs",
                "copy-before-seal-cohort" => "PublishedCatalogArtifactCohort.cs",
                "copy-before-seal-project" => "Hexalith.Platform.CatalogBuilder.csproj",
                "copy-before-seal-bindings" => "bindings.props",
                "copy-before-seal-global" => "global.json",
                _ => null,
            };
            if (name is not null) File.AppendAllText(Path.Combine(reader, name), "changed immediately after copying");
        };
        try
        {
            foreach (var pair in environment) Environment.SetEnvironmentVariable(pair.Key, pair.Value);
            Exception? failure = await Record.ExceptionAsync(() => NativeCatalogTool.RunOwnedPreparationAsync(directory, "owner", async () =>
            {
                using JsonDocument unused = await NativeCatalogTool.GenerateAsync(new DirectoryInfo(_root), directory, "instance", "eventstore", "4.0.4",
                    [(owner, owner, "parties")], TestContext.Current.CancellationToken, Path.Combine(bin, OperatingSystem.IsWindows() ? "dotnet.exe" : "dotnet"));
            }));
            string[][] commands = File.Exists(calls) ? File.ReadAllLines(calls).Select(line => JsonSerializer.Deserialize<string[]>(line)!).ToArray() : [];
            if (kind == "matching-generated")
            {
                Assert.Null(failure);
                Assert.Equal(3, commands.Length);
                Assert.Equal(1, copyStageCalls);
                foreach (string[] command in commands.Take(2))
                {
                    Assert.Contains("-p:HexalithBuildPackageVersions1=" + catalog, command);
                    Assert.Contains("-p:HexalithBuildPackageVersions2=", command);
                    Assert.Contains("-p:HexalithBuildPackageVersions3=", command);
                    Assert.Contains("-p:ImportDirectoryBuildProps=false", command);
                    Assert.Contains("-p:ImportDirectoryBuildTargets=false", command);
                    Assert.Contains("-p:ImportDirectoryPackagesProps=false", command);
                    Assert.Contains("-p:CustomAfterMicrosoftCommonTargets=", command);
                }
                string reader = Path.Combine(directory, "reader");
                using JsonDocument prepared = JsonDocument.Parse(File.ReadAllBytes(Path.Combine(reader, "preparation.json")));
                foreach (var (name, original, copy) in new[]
                {
                    ("Program", Path.Combine(template, "Program.cs"), Path.Combine(reader, "Program.cs")),
                    ("Cohort", cohort, Path.Combine(reader, "PublishedCatalogArtifactCohort.cs")),
                })
                {
                    string originalHash = Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(original)));
                    string copiedHash = Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(copy)));
                    Assert.Equal(originalHash, copiedHash);
                    Assert.Equal(originalHash, prepared.RootElement.GetProperty("template" + name + "Sha256").GetString());
                    Assert.Equal(copiedHash, prepared.RootElement.GetProperty("reader" + name + "Sha256").GetString());
                }
                Assert.Equal(Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(catalog))),
                    prepared.RootElement.GetProperty("buildsCatalogSha256").GetString());
                using JsonDocument request = JsonDocument.Parse(File.ReadAllBytes(Path.Combine(reader, "request.json")));
                Assert.False(request.RootElement.TryGetProperty("qualificationCohort", out _));
                Assert.False(request.RootElement.TryGetProperty("currentOwnerArtifacts", out _));
                return; // Controlled process proof only; no live catalog or qualification credit.
            }
            bool beforeProcess = kind is "cohort-source-missing" or "cohort-source-changed" or "catalog-source-missing" or "catalog-source-changed"
                || kind.StartsWith("copy-before-seal-", StringComparison.Ordinal);
            if (kind is "cohort-source-missing" or "catalog-source-missing") Assert.IsType<FileNotFoundException>(failure);
            else Assert.IsType<InvalidDataException>(failure);
            if (kind.StartsWith("copy-before-seal-", StringComparison.Ordinal)) Assert.Equal(1, copyStageCalls);
            if (beforeProcess) Assert.Empty(commands);
            else
            {
                Assert.Equal("restore", commands[0][0]);
                Assert.Contains("-p:Configuration=Release", commands[0]);
            }
            if (kind == "matching")
            {
                Assert.Equal(2, commands.Length);
                Assert.Equal("build", commands[1][0]);
                Assert.Contains("--no-restore", commands[1]);
                Assert.Contains("controlled-reader-build-stop", failure!.Message, StringComparison.Ordinal);
            }
            else if (kind.EndsWith("-generation", StringComparison.Ordinal)) Assert.Equal(3, commands.Length);
            else if (kind.EndsWith("-after-build", StringComparison.Ordinal))
            {
                Assert.Equal(2, commands.Length);
                Assert.Equal("build", commands[1][0]); // No generation invocation may observe build-time drift.
            }
            else if (!beforeProcess) Assert.Single(commands);
            Assert.False(Directory.Exists(directory));
        }
        finally
        {
            NativeCatalogTool.InputsCopiedObserver.Value = priorObserver;
            foreach (var pair in prior) Environment.SetEnvironmentVariable(pair.Key, pair.Value);
        }
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

    /// <summary>Opaque child-process bearer credentials are redacted even without an ambient secret binding.</summary>
    [Theory]
    [InlineData(" ")]
    [InlineData("\t")]
    [InlineData("\n")]
    public void OpaqueBearerDiagnosticsAreRedacted(string separator)
    {
        string diagnostic = "authorization: Bearer" + separator + "opaque-child-credential+/_~.abc==";
        for (int escapes = 0; escapes < 3; escapes++)
        {
            string sanitized = NativeCatalogDiagnostics.Sanitize(diagnostic);
            Assert.DoesNotContain("opaque-child-credential", sanitized, StringComparison.Ordinal);
            Assert.Contains("REDACTED", sanitized, StringComparison.Ordinal);
            diagnostic = JsonSerializer.Serialize(diagnostic);
        }
    }

    /// <summary>An exited parent with inherited open pipes retains process ownership and the preparation directory.</summary>
    [Fact]
    public async Task OpenDescendantPipesRetainOwnedPreparation()
    {
        string path = Path.Combine(_root, "inherited-pipes"), pidFile = Path.Combine(_root, "descendant.pid");
        string configuration = new DirectoryInfo(AppContext.BaseDirectory).Parent!.Name;
        string executable = Path.Combine(DependencyPolicyTests.FindRepositoryRoot(), "tests", "fixtures", "Topology.DaprStub", "bin",
            configuration, "net10.0", OperatingSystem.IsWindows() ? "dapr.exe" : "dapr");
        MethodInfo run = typeof(NativeCatalogTool).GetMethod("RunAsync", BindingFlags.NonPublic | BindingFlags.Static)!;
        try
        {
            TimeoutException failure = await Assert.ThrowsAsync<TimeoutException>(() => NativeCatalogTool.RunOwnedPreparationAsync(path, "owner", async () =>
            {
                await ((Task)run.Invoke(null, [path, "build.log", new[] { "catalog-pipe-parent", pidFile },
                    TestContext.Current.CancellationToken, executable])!);
            }));
            Assert.True(failure.Data.Contains("CatalogOwnedProcessStillRunning"));
            Assert.Equal("owner", File.ReadAllText(Path.Combine(path, ".owner")));
            using Process descendant = Process.GetProcessById(int.Parse(File.ReadAllText(pidFile), System.Globalization.CultureInfo.InvariantCulture));
            Assert.False(descendant.HasExited);
        }
        finally
        {
            if (File.Exists(pidFile))
            {
                using Process descendant = Process.GetProcessById(int.Parse(File.ReadAllText(pidFile), System.Globalization.CultureInfo.InvariantCulture));
                if (!descendant.HasExited) descendant.Kill(entireProcessTree: true);
                using var cleanup = new CancellationTokenSource(TimeSpan.FromSeconds(10));
                await descendant.WaitForExitAsync(cleanup.Token);
            }
        }
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
            readerProjectSha256 = "reader-project-hash", globalJsonSha256 = "sdk-policy-hash",
            templateProgramSha256 = "original-program-hash", readerProgramSha256 = "copied-program-hash", buildsCatalogSha256 = "direct-catalog-hash",
            templateCohortSha256 = "original-cohort-hash", readerCohortSha256 = "copied-cohort-hash", inputHashes = new Dictionary<string, string> { ["adapter.dll"] = "adapter-hash" },
            auditReceiptSha256 = "online-audit-hash", auditedPackageGraph = new Dictionary<string, string> { ["SDK/4.0.4"] = "audited-package-hash" },
            privateKey = "private-reader-value" }));
        var retained = NativeCatalogPreparationEvidence.Capture(tenant, party);
        File.Delete(tenant); File.Delete(party);
        string json = retained.ToJsonString();
        Assert.Contains("sdk-image-hash", json, StringComparison.Ordinal);
        Assert.Contains("reader-project-hash", json, StringComparison.Ordinal);
        Assert.Contains("template-project-hash", json, StringComparison.Ordinal);
        Assert.Contains("original-program-hash", json, StringComparison.Ordinal);
        Assert.Contains("copied-program-hash", json, StringComparison.Ordinal);
        Assert.Contains("original-cohort-hash", json, StringComparison.Ordinal);
        Assert.Contains("copied-cohort-hash", json, StringComparison.Ordinal);
        Assert.Contains("direct-catalog-hash", json, StringComparison.Ordinal);
        Assert.Contains("environment-digest", json, StringComparison.Ordinal);
        Assert.Contains("online-audit-hash", json, StringComparison.Ordinal);
        Assert.Contains("audited-package-hash", json, StringComparison.Ordinal);
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
