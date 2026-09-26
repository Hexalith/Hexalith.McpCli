using System.Reflection;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Sample.Contracts;
using Microsoft.Extensions.Logging;
using Shouldly;
using Invalid = global::Catalog.Invalid.Contracts;
using Routing = global::Catalog.Routing.Contracts;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Verifies lazy Catalog construction, one-time diagnostic logging, and the empty and strict policies.</summary>
public sealed class CatalogProviderTests
{
    /// <summary>Constructing the provider touches no assembly; the first call builds and logs once, and later calls do neither.</summary>
    [Fact]
    public void FirstCallBuildsAndLogsEachDiagnosticOnce()
    {
        int manifestReads = 0;
        var logger = new RecordingLogger<CatalogProvider>();
        var provider = new CatalogProvider(() =>
        {
            manifestReads++;
            return [typeof(Invalid.Module).Assembly, typeof(Routing.Module).Assembly];
        }, logger);

        manifestReads.ShouldBe(0);
        logger.Entries.ShouldBeEmpty();

        CatalogAccess first = provider.Get(strict: false);

        manifestReads.ShouldBe(1);
        first.ErrorCode.ShouldBeNull();
        first.Message.ShouldBeNull();
        CatalogSnapshot catalog = first.Catalog.ShouldNotBeNull();
        catalog.Diagnostics.ShouldContain(diagnostic => diagnostic.Severity == "warning");
        catalog.Diagnostics.ShouldContain(diagnostic => diagnostic.Severity == "error");
        logger.Entries.Count.ShouldBe(catalog.Diagnostics.Count);
        for (int index = 0; index < catalog.Diagnostics.Count; index++)
        {
            CatalogDiagnostic diagnostic = catalog.Diagnostics[index];
            LogEntry entry = logger.Entries[index];
            entry.Level.ShouldBe(diagnostic.Severity == "warning" ? LogLevel.Warning : LogLevel.Error);
            entry.EventId.Id.ShouldBe(1);
            entry.Fields["TypeName"].ShouldBe(diagnostic.TypeName);
            entry.Fields["Category"].ShouldBe(diagnostic.Category);
            entry.Fields["Severity"].ShouldBe(diagnostic.Severity);
            entry.Fields["Message"].ShouldBe(diagnostic.Message);
            entry.Text.ShouldContain(diagnostic.Message);
        }

        CatalogAccess second = provider.Get(strict: false);

        manifestReads.ShouldBe(1);
        logger.Entries.Count.ShouldBe(catalog.Diagnostics.Count);
        second.Catalog.ShouldBeSameAs(catalog);
    }

    /// <summary>Concurrent first calls still build the Catalog exactly once.</summary>
    [Fact]
    public void ConcurrentFirstCallsBuildOnce()
    {
        int manifestReads = 0;
        var logger = new RecordingLogger<CatalogProvider>();
        using var barrier = new Barrier(2);
        var provider = new CatalogProvider(() =>
        {
            Interlocked.Increment(ref manifestReads);

            // Hold the first build open so a second concurrent factory entry would meet it here and be counted.
            barrier.SignalAndWait(TimeSpan.FromMilliseconds(500));
            return [typeof(Routing.Module).Assembly];
        }, logger);

        CatalogSnapshot?[] results = new CatalogSnapshot?[8];
        Parallel.For(0, results.Length, index => results[index] = provider.Get(strict: false).Catalog);

        manifestReads.ShouldBe(1);
        results.ShouldAllBe(result => ReferenceEquals(result, results[0]));
        logger.Entries.Count.ShouldBe(results[0]!.Diagnostics.Count);
    }

    /// <summary>A Catalog with no valid Operations is <c>catalog_empty</c>.</summary>
    /// <param name="markedEmpty">Whether the manifest holds a marked empty Module instead of nothing.</param>
    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void CatalogWithoutOperationsIsEmpty(bool markedEmpty)
    {
        Assembly[] manifest = markedEmpty ? [typeof(Manifest.MarkedEmpty.Contracts.Module).Assembly] : [];
        var provider = new CatalogProvider(() => manifest, new RecordingLogger<CatalogProvider>());

        CatalogAccess access = provider.Get(strict: false);

        access.Catalog.ShouldBeNull();
        access.ErrorCode.ShouldBe("catalog_empty");
        access.Message.ShouldNotBeNullOrWhiteSpace();
    }

    /// <summary>Strict mode rejects any diagnostic, warnings included, and is checked before emptiness.</summary>
    [Fact]
    public void StrictModeRejectsAnyDiagnosticBeforeEmptiness()
    {
        var warningsOnly = new CatalogProvider(() => [typeof(Routing.Module).Assembly], new RecordingLogger<CatalogProvider>());
        warningsOnly.Get(strict: true).ShouldSatisfyAllConditions(
            access => access.Catalog.ShouldBeNull(),
            access => access.ErrorCode.ShouldBe("catalog_invalid"),
            access => access.Message.ShouldNotBeNullOrWhiteSpace());
        CatalogAccess normal = warningsOnly.Get(strict: false);
        normal.ErrorCode.ShouldBeNull();
        normal.Catalog.ShouldNotBeNull().Diagnostics.ShouldAllBe(diagnostic => diagnostic.Severity == "warning");

        var emptyWithWarning = new CatalogProvider(() => [typeof(Manifest.MarkedEmpty.Contracts.Module).Assembly],
            new RecordingLogger<CatalogProvider>());
        emptyWithWarning.Get(strict: true).ErrorCode.ShouldBe("catalog_invalid");
        emptyWithWarning.Get(strict: false).ErrorCode.ShouldBe("catalog_empty");
    }

    /// <summary>Strict mode accepts a Catalog without diagnostics.</summary>
    [Fact]
    public void StrictModeAcceptsACleanCatalog()
    {
        var logger = new RecordingLogger<CatalogProvider>();
        var provider = new CatalogProvider(() => [typeof(CreateItemCommand).Assembly], logger);

        CatalogAccess access = provider.Get(strict: true);

        access.ErrorCode.ShouldBeNull();
        access.Catalog.ShouldNotBeNull().Diagnostics.ShouldBeEmpty();
        logger.Entries.ShouldBeEmpty();
    }
}
