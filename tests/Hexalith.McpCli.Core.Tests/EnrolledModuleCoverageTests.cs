using System.Reflection;
using System.Text.Json.Nodes;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Core.Execution;
using Hexalith.McpCli.Sample.Contracts;
using Shouldly;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Connects generic release coverage and strict discovery to the shipped manifest.</summary>
/// <param name="output">Receives the non-failing inventory and Operation Shape reports.</param>
public sealed class EnrolledModuleCoverageTests(ITestOutputHelper output)
{
    private const string SamplePackage = "Hexalith.McpCli.Sample.Contracts";
    private const string SampleCommandShape = "kind=command;identifierKind=ulid;wireTypeConvention=kebabCase;tenantSource=fixedTenant;"
        + "aggregateIdSource=property;projectionSelector=none;idempotencyKey=optional";
    private const string SampleQueryShape = "kind=query;identifierKind=ulid;wireTypeConvention=kebabCase;tenantSource=fixedTenant;"
        + "aggregateIdSource=property;projectionSelector=projectionType;idempotencyKey=optional";

    private static string ProductionVectors => Path.Combine(AppContext.BaseDirectory, "conformance", "modules");

    /// <summary>Every enrolled Contracts package must have an approved release inventory and lint-clean discovery.</summary>
    [Fact]
    public void EveryProductionModuleHasApprovedExactCoverageAndReviewedDescriptions()
    {
        (string PackageId, string AssemblyName)[] entries = ManifestEntries();
        var provider = new CatalogProvider(() => entries.Select(e => Assembly.Load(e.AssemblyName)).ToArray(), new RecordingLogger<CatalogProvider>());
        // A build with no enrolled packages must still report the generic empty-catalog error.
        if (entries.Length == 0)
        {
            provider.Get(false).ErrorCode.ShouldBe("catalog_empty");
            return;
        }

        ICatalog catalog = new CatalogService(provider, new ExecutionAvailability(false, false), strict: true);
        var reports = new List<string>();
        IReadOnlyList<string> inventoryFindings = EnrolledInventoryCoverageGate.Check(
            Path.Combine(AppContext.BaseDirectory, "inventory-coverage", "v1"), catalog, provider, reports);
        // Reports reach the test output before any assertion, so a failing run still shows them.
        foreach (string report in reports)
        {
            output.WriteLine("reported: " + report);
        }

        inventoryFindings.ShouldBeEmpty();

        CatalogSnapshot snapshot = provider.Get(false).Catalog.ShouldNotBeNull();
        snapshot.Diagnostics.Where(d => d.Severity == "error").ShouldBeEmpty();
        foreach (ModuleDescriptor module in snapshot.Modules)
        {
            var findings = new List<(string Operation, LintFinding Finding)>();
            foreach (OperationDescriptor operation in module.Operations)
            {
                var description = catalog.Describe(operation.Name);
                description.Error.ShouldBeNull();
                findings.AddRange(description.Document.ShouldNotBeNull().LintFindings.Select(f => (operation.Name, f)));
            }
            string acceptedPath = Path.Combine(AppContext.BaseDirectory, "inventory-coverage", "v1", module.Name + "-accepted-lint.json");
            DescriptionLintGate.Check(findings, File.Exists(acceptedPath) ? File.ReadAllText(acceptedPath) : null).ShouldBeEmpty();
        }
    }

    /// <summary>Every Operation Shape of every enrolled module has a hash-approved vector; covered shapes are reported, never pinned by count.</summary>
    [Fact]
    public void EveryProductionOperationShapeHasAnApprovedVector()
    {
        (string PackageId, string AssemblyName)[] entries = ManifestEntries();
        if (entries.Length == 0)
        {
            return;
        }

        CatalogSnapshot snapshot = ProductionSnapshot(entries);
        var reports = new List<string>();
        IReadOnlyList<string> shapeFindings = ShapeCoverageGate.Check(ProductionVectors, entries.Select(entry => entry.PackageId), snapshot, reports);
        // Covered shapes reach the test output before any assertion, so a failing run still shows them.
        foreach (string report in reports)
        {
            output.WriteLine("covered: " + report);
        }

        shapeFindings.ShouldBeEmpty();

        var findings = new List<string>();
        IReadOnlyList<ShapeCoverage> shapes = ShapeCoverageGate.Coverage(ProductionVectors, entries.Select(entry => entry.PackageId), snapshot, findings);
        findings.ShouldBeEmpty();
        reports.Count.ShouldBe(shapes.Count);
        shapes.Select(shape => shape.Module).Distinct(StringComparer.Ordinal).ShouldBe(snapshot.Modules.Select(module => module.Name), ignoreOrder: true);
    }

    /// <summary>Removing every vector of the least-covered production shape (today a single-vector shape) fails naming exactly that shape.</summary>
    [Fact]
    public void RemovingTheVectorsOfTheLeastCoveredProductionShapeFailsNamingThatShape()
    {
        (string PackageId, string AssemblyName)[] entries = ManifestEntries();
        if (entries.Length == 0)
        {
            return;
        }

        CatalogSnapshot snapshot = ProductionSnapshot(entries);
        string directory = Path.Combine(Path.GetTempPath(), "shape-removal-" + Path.GetRandomFileName());
        CopyDirectory(ProductionVectors, directory);
        try
        {
            var findings = new List<string>();
            ShapeCoverage target = ShapeCoverageGate.Coverage(directory, entries.Select(entry => entry.PackageId), snapshot, findings)
                .OrderBy(shape => shape.VectorFiles.Count).ThenBy(shape => shape.Module, StringComparer.Ordinal)
                .ThenBy(shape => shape.Key, StringComparer.Ordinal).First();
            findings.ShouldBeEmpty();
            target.VectorFiles.ShouldNotBeEmpty();
            foreach (string vector in target.VectorFiles)
            {
                File.Delete(vector);
            }

            ShapeCoverageGate.Check(directory, entries.Select(entry => entry.PackageId), snapshot).ShouldBe(new[]
            {
                $"{target.Module}: Operation Shape '{target.Key}' has no approved vector (operations: {string.Join(", ", target.Operations)}).",
            });
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Each covered sample shape is reported, and nothing fails while every shape has an approved vector.</summary>
    [Fact]
    public void ApprovedSampleVectorsCoverAndReportEverySampleShape()
    {
        using SampleApproval approval = new();
        var reports = new List<string>();

        ShapeCoverageGate.Check(approval.Modules, [SamplePackage], SampleSnapshot(), reports).ShouldBeEmpty();
        reports.ShouldBe(new[]
        {
            $"sample: Operation Shape '{SampleCommandShape}' is covered by approved vector(s) for sample.create-item, sample.rename-item (operations: sample.create-item, sample.rename-item).",
            $"sample: Operation Shape '{SampleQueryShape}' is covered by approved vector(s) for sample.get-item (operations: sample.get-item).",
        });
    }

    /// <summary>One approved vector covers every operation of its shape, so a shape-mate without its own vector does not fail.</summary>
    [Fact]
    public void OneVectorCoversEveryOperationOfItsSampleShape()
    {
        using SampleApproval approval = new();
        File.Delete(approval.Vector("sample-rename"));
        var reports = new List<string>();

        ShapeCoverageGate.Check(approval.Modules, [SamplePackage], SampleSnapshot(), reports).ShouldBeEmpty();
        reports.ShouldBe(new[]
        {
            $"sample: Operation Shape '{SampleCommandShape}' is covered by approved vector(s) for sample.create-item (operations: sample.create-item, sample.rename-item).",
            $"sample: Operation Shape '{SampleQueryShape}' is covered by approved vector(s) for sample.get-item (operations: sample.get-item).",
        });
    }

    /// <summary>Removing the only vector of a shape fails with that shape and its operations named.</summary>
    [Fact]
    public void RemovingTheOnlyVectorOfASampleShapeFailsNamingThatShape()
    {
        using SampleApproval approval = new();
        File.Delete(approval.Vector("sample-query"));
        var reports = new List<string>();

        ShapeCoverageGate.Check(approval.Modules, [SamplePackage], SampleSnapshot(), reports).ShouldBe(new[]
        {
            $"sample: Operation Shape '{SampleQueryShape}' has no approved vector (operations: sample.get-item).",
        });
        reports.ShouldBe(new[]
        {
            $"sample: Operation Shape '{SampleCommandShape}' is covered by approved vector(s) for sample.create-item, sample.rename-item (operations: sample.create-item, sample.rename-item).",
        });
    }

    /// <summary>A vector whose bytes differ from its approved hash does not count as coverage.</summary>
    [Fact]
    public void ChangedVectorBytesDoNotCoverAShape()
    {
        using SampleApproval approval = new();
        File.AppendAllText(approval.Vector("sample-query"), "\n");

        ShapeCoverageGate.Check(approval.Modules, [SamplePackage], SampleSnapshot()).ShouldBe(new[]
        {
            $"sample: Operation Shape '{SampleQueryShape}' has no approved vector (operations: sample.get-item).",
        });
    }

    /// <summary>The approval directory is matched case-insensitively, and a missing one fails without a shape report.</summary>
    [Fact]
    public void ApprovalDirectoryIsRequiredAndMatchedCaseInsensitively()
    {
        using SampleApproval approval = new();
        var reports = new List<string>();

        ShapeCoverageGate.Check(approval.Modules, [SamplePackage.ToUpperInvariant()], SampleSnapshot()).ShouldBeEmpty();
        ShapeCoverageGate.Check(approval.Modules, ["Other.Contracts"], SampleSnapshot(), reports)
            .ShouldBe(new[] { "Other.Contracts: expected one approval directory (package IDs are case-insensitive)." });
        reports.ShouldBeEmpty();
    }

    /// <summary>A receipt cannot point the shape gate at a module that the Catalog does not contain.</summary>
    [Fact]
    public void ApprovedModuleMustBeInTheCatalog()
    {
        using SampleApproval approval = new("other");
        var reports = new List<string>();

        ShapeCoverageGate.Check(approval.Modules, [SamplePackage], SampleSnapshot(), reports)
            .ShouldBe(new[] { $"{SamplePackage}: approved module 'other' is absent from the Catalog." });
        reports.ShouldBeEmpty();
    }

    /// <summary>Adding an enrolled module without adding its inventory fails independently of dependency policy.</summary>
    [Fact]
    public void MissingInventoryCannotSilentlySkipAnEnrolledModule()
    {
        var provider = new CatalogProvider(() => [typeof(CreateItemCommand).Assembly], new RecordingLogger<CatalogProvider>());
        ICatalog catalog = new CatalogService(provider, new ExecutionAvailability(false, false), strict: false);
        string directory = Path.Combine(Path.GetTempPath(), "missing-inventory-" + Path.GetRandomFileName());
        EnrolledInventoryCoverageGate.Check(directory, catalog, provider)
            .ShouldBe(new[] { $"sample: missing release inventory '{Path.Combine(directory, "sample-approved.json")}'." });
    }

    /// <summary>A fixture document cannot authorize an enrolled production module.</summary>
    [Fact]
    public void SyntheticFixtureCannotAuthorizeProductionEnrollment()
    {
        var provider = new CatalogProvider(() => [typeof(CreateItemCommand).Assembly], new RecordingLogger<CatalogProvider>());
        ICatalog catalog = new CatalogService(provider, new ExecutionAvailability(false, false), strict: false);
        string directory = Path.Combine(AppContext.BaseDirectory, "inventory-coverage", "v1");
        EnrolledInventoryCoverageGate.Check(directory, catalog, provider).ShouldBe(new[] { "sample: enrolled modules require purpose 'release'." });
    }

    /// <summary>A valid inventory for one enrolled module cannot authorize a different enrolled module.</summary>
    [Fact]
    public void AnotherModulesValidReleaseInventoryCannotAuthorizeEnrollment()
    {
        var provider = new CatalogProvider(() => [typeof(CreateItemCommand).Assembly, typeof(global::Catalog.String.Contracts.LookupQuery).Assembly],
            new RecordingLogger<CatalogProvider>());
        ICatalog catalog = new CatalogService(provider, new ExecutionAvailability(false, false), strict: false);
        JsonObject inventory = ReleaseSampleInventory();

        string directory = Path.Combine(Path.GetTempPath(), "mismatched-inventory-" + Path.GetRandomFileName());
        Directory.CreateDirectory(directory);
        try
        {
            string sample = Path.Combine(directory, "sample-approved.json");
            File.WriteAllText(sample, inventory.ToJsonString());
            InventoryCoverageGate.CheckFile(sample, catalog, provider).ShouldBeEmpty();
            File.Copy(sample, Path.Combine(directory, "string-fixture-approved.json"));

            EnrolledInventoryCoverageGate.Check(directory, catalog, provider)
                .ShouldBe(new[] { "string-fixture: inventory declares a different module." });
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Coverage findings in an enrolled module's own inventory fail the enrolled gate.</summary>
    [Fact]
    public void InventoryCoverageFindingsFailEnrollment()
    {
        var provider = new CatalogProvider(() => [typeof(CreateItemCommand).Assembly], new RecordingLogger<CatalogProvider>());
        ICatalog catalog = new CatalogService(provider, new ExecutionAvailability(false, false), strict: false);
        JsonObject inventory = ReleaseSampleInventory();
        inventory["legacyRows"]![0]!["approval"]!["status"] = "pending";

        string directory = Path.Combine(Path.GetTempPath(), "pending-inventory-" + Path.GetRandomFileName());
        Directory.CreateDirectory(directory);
        try
        {
            string sample = Path.Combine(directory, "sample-approved.json");
            File.WriteAllText(sample, inventory.ToJsonString());

            EnrolledInventoryCoverageGate.Check(directory, catalog, provider)
                .ShouldBe(new[] { $"{sample}:row L01: approval.status must be 'approved'; actual 'pending'." });
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>The enrolled gate forwards a module's non-failing inventory reports without adding a finding.</summary>
    [Fact]
    public void EnrolledGateForwardsUnmentionedOperationReports()
    {
        var provider = new CatalogProvider(() => [typeof(CreateItemCommand).Assembly], new RecordingLogger<CatalogProvider>());
        ICatalog catalog = new CatalogService(provider, new ExecutionAvailability(false, false), strict: false);
        JsonObject inventory = ReleaseSampleInventory();
        inventory["targets"]!.AsArray().RemoveAt(2);
        inventory["legacyRows"]![2]!["targetIds"] = new JsonArray("T02");

        string directory = Path.Combine(Path.GetTempPath(), "reported-inventory-" + Path.GetRandomFileName());
        Directory.CreateDirectory(directory);
        try
        {
            string sample = Path.Combine(directory, "sample-approved.json");
            File.WriteAllText(sample, inventory.ToJsonString());
            var reports = new List<string>();

            EnrolledInventoryCoverageGate.Check(directory, catalog, provider, reports).ShouldBeEmpty();
            reports.ShouldBe(new[]
            {
                $"{sample}:internal operation sample.rename-item: reported, not failed; no inventory row mentions this cataloged operation / 'Hexalith.McpCli.Sample.Contracts.RenameItemCommand'.",
                $"{sample}:public operation sample.rename-item: reported, not failed; no inventory row mentions this cataloged operation.",
            });
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    private static (string PackageId, string AssemblyName)[] ManifestEntries()
    {
        Assembly cli = Assembly.Load("Hexalith.McpCli");
        Type manifest = cli.GetType("Hexalith.McpCli.Hosting.ModuleAssemblyManifest", throwOnError: true)!;
        return ((string PackageId, string AssemblyName)[])manifest.GetField("Entries", BindingFlags.NonPublic | BindingFlags.Static)!.GetValue(null)!;
    }

    private static CatalogSnapshot ProductionSnapshot((string PackageId, string AssemblyName)[] entries)
        => new CatalogProvider(() => entries.Select(entry => Assembly.Load(entry.AssemblyName)).ToArray(), new RecordingLogger<CatalogProvider>())
            .Get(false).Catalog.ShouldNotBeNull();

    private static CatalogSnapshot SampleSnapshot()
        => new CatalogProvider(() => [typeof(CreateItemCommand).Assembly], new RecordingLogger<CatalogProvider>()).Get(false).Catalog.ShouldNotBeNull();

    private static void CopyDirectory(string source, string destination)
    {
        foreach (string file in Directory.EnumerateFiles(source, "*", SearchOption.AllDirectories))
        {
            string target = Path.Combine(destination, Path.GetRelativePath(source, file));
            Directory.CreateDirectory(Path.GetDirectoryName(target)!);
            File.Copy(file, target);
        }
    }

    private static JsonObject ReleaseSampleInventory()
    {
        JsonObject inventory = JsonNode.Parse(File.ReadAllText(Path.Combine(AppContext.BaseDirectory, "inventory-coverage", "v1", "sample-approved.json")))!.AsObject();
        inventory["purpose"] = "release";
        foreach (JsonNode? row in inventory["legacyRows"]!.AsArray())
        {
            row!["approval"]!["authority"] = "owning-maintainer";
        }

        return inventory;
    }
}
