using System.Reflection;
using System.Text.Json.Nodes;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Core.Execution;
using Hexalith.McpCli.Sample.Contracts;
using Shouldly;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Connects generic release coverage and strict discovery to the shipped manifest.</summary>
public sealed class EnrolledModuleCoverageTests
{
    /// <summary>Every enrolled Contracts package must have an approved release inventory and lint-clean discovery.</summary>
    [Fact]
    public void EveryProductionModuleHasApprovedExactCoverageAndReviewedDescriptions()
    {
        Assembly cli = Assembly.Load("Hexalith.McpCli");
        Type manifest = cli.GetType("Hexalith.McpCli.Hosting.ModuleAssemblyManifest", throwOnError: true)!;
        var entries = ((string PackageId, string AssemblyName)[])manifest.GetField("Entries", BindingFlags.NonPublic | BindingFlags.Static)!.GetValue(null)!;
        var provider = new CatalogProvider(() => entries.Select(e => Assembly.Load(e.AssemblyName)).ToArray(), new RecordingLogger<CatalogProvider>());
        // A build with no enrolled packages must still report the generic empty-catalog error.
        if (entries.Length == 0)
        {
            provider.Get(false).ErrorCode.ShouldBe("catalog_empty");
            return;
        }

        ICatalog catalog = new CatalogService(provider, new ExecutionAvailability(false, false), strict: true);
        EnrolledInventoryCoverageGate.Check(Path.Combine(AppContext.BaseDirectory, "inventory-coverage", "v1"), catalog, provider).ShouldBeEmpty();
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
