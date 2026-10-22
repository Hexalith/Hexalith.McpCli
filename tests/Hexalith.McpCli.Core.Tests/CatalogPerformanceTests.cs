using System.Diagnostics;
using System.Reflection;
using System.Text.Json;
using Hexalith.McpCli.Abstractions;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Sample.Contracts;
using Shouldly;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Measures the first production Catalog build plus exactly one ULID sample in a fresh process.</summary>
public sealed class CatalogPerformanceTests
{
    /// <summary>Runs the measurement in its own process so other tests cannot warm Catalog caches.</summary>
    [Fact]
    public async Task FirstConstructionStaysWithinFiveHundredMilliseconds()
    {
        string? configuredOutput = Environment.GetEnvironmentVariable("MCPCLI_BENCHMARK_OUTPUT");
        string output = configuredOutput
            ?? Path.Combine(Path.GetTempPath(), "mcpcli-catalog-" + Path.GetRandomFileName() + ".json");
        InvalidateOutput(output);
        try
        {
            var start = new ProcessStartInfo("dotnet")
            {
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
            };
            start.ArgumentList.Add(typeof(CatalogPerformanceTests).Assembly.Location);
            start.ArgumentList.Add("-method");
            start.ArgumentList.Add(typeof(CatalogPerformanceTests).FullName + "." + nameof(MeasureFirstConstruction));
            start.Environment["MCPCLI_BENCHMARK_PROBE"] = "1";
            start.Environment["MCPCLI_BENCHMARK_OUTPUT"] = output;
            using Process process = Process.Start(start)!;
            Task<string> stdout = process.StandardOutput.ReadToEndAsync(TestContext.Current.CancellationToken);
            Task<string> stderr = process.StandardError.ReadToEndAsync(TestContext.Current.CancellationToken);
            await process.WaitForExitAsync(TestContext.Current.CancellationToken);
            process.ExitCode.ShouldBe(0, await stdout + await stderr + (File.Exists(output) ? File.ReadAllText(output) : "Missing benchmark evidence."));
            AssertCompletedEvidence(File.ReadAllText(output), Environment.GetEnvironmentVariable("MCPCLI_BENCHMARK_REQUIRE_V1") == "true", Environment.ProcessId);
        }
        catch (Exception exception)
        {
            RetainFailure(output, exception);
            throw;
        }
        finally
        {
            if (configuredOutput is null)
            {
                File.Delete(output);
            }
        }
    }

    /// <summary>Measures one cold Build after loading its assembly population; also retains failures as JSON.</summary>
    [Fact]
    public void MeasureFirstConstruction()
    {
        Assert.SkipUnless(Environment.GetEnvironmentVariable("MCPCLI_BENCHMARK_PROBE") == "1", "Runs only in the fresh benchmark child process.");

        string output = Environment.GetEnvironmentVariable("MCPCLI_BENCHMARK_OUTPUT")!;
        RunWithFailureEvidence(output, () =>
        {
            Assembly cli = Assembly.Load("Hexalith.McpCli");
            Type manifest = cli.GetType("Hexalith.McpCli.Hosting.ModuleAssemblyManifest", throwOnError: true)!;
            var entries = ((string PackageId, string AssemblyName)[])manifest.GetField("Entries", BindingFlags.NonPublic | BindingFlags.Static)!.GetValue(null)!;
            Assembly sample = typeof(CreateItemCommand).Assembly;
            Assembly[] assemblies = entries.Select(entry => Assembly.Load(entry.AssemblyName)).Append(sample).ToArray();
            assemblies.Distinct().Count().ShouldBe(entries.Length + 1);
            // No Catalog construction occurs in this process before this measured call.
            var clock = Stopwatch.StartNew();
            CatalogSnapshot catalog = CatalogBuilder.Build(assemblies);
            clock.Stop();
            sample.GetCustomAttribute<HexalithModuleAttribute>()!.IdentifierKind.ShouldBe(IdentifierKind.Ulid);
            using JsonDocument scope = JsonDocument.Parse(File.ReadAllText(Path.Combine(AppContext.BaseDirectory, "conformance", "v1-scope.json")));
            string[] required = scope.RootElement.GetProperty("requiredModules").EnumerateArray().Select(value => value.GetString()!).ToArray();
            bool requireV1 = Environment.GetEnvironmentVariable("MCPCLI_BENCHMARK_REQUIRE_V1") == "true";
            var outcome = ConstructionOutcome(catalog.Diagnostics.Select(diagnostic => diagnostic.Message), clock.Elapsed.TotalMilliseconds,
                required, catalog.Modules.Select(module => module.Name), requireV1);
            string evidence = JsonSerializer.Serialize(new
            {
                result = outcome.Result,
                fullV1Accepted = outcome.FullV1Accepted,
                elapsedMilliseconds = clock.Elapsed.TotalMilliseconds,
                limitMilliseconds = 500,
                processId = Environment.ProcessId,
                assemblies = assemblies.Select(assembly => assembly.GetName().Name),
                productionPackages = entries.Select(entry => entry.PackageId),
                modules = catalog.Modules.Select(module => new { module.Name, identifierKind = module.IdentifierKind.ToString(), operationCount = module.Operations.Count }),
                missingRequiredModules = outcome.Missing,
                diagnostics = catalog.Diagnostics,
                failures = outcome.Failures,
            }, new JsonSerializerOptions { WriteIndented = true });
            Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(output))!);
            File.WriteAllText(output, evidence + Environment.NewLine);
            outcome.Failures.ShouldBeEmpty(evidence);
        });
    }

    /// <summary>The limit accepts exactly 500 ms and rejects any greater duration.</summary>
    [Theory]
    [InlineData(500, true)]
    [InlineData(500.0001, false)]
    public void ConstructionLimitIncludesOnlyAtMostFiveHundredMilliseconds(double elapsed, bool accepted)
    {
        LimitViolation(elapsed).ShouldBe(accepted ? null : "First Catalog construction exceeded 500 ms.");
    }

    /// <summary>Early failures replace previous success and retain their actual diagnostics.</summary>
    [Fact]
    public void FailureEvidenceWrapperInvalidatesPriorSuccessAndRetainsTheException()
    {
        string output = Path.Combine(Path.GetTempPath(), "mcpcli-failed-" + Path.GetRandomFileName() + ".json");
        try
        {
            File.WriteAllText(output, "{\"result\":\"passed\",\"fullV1Accepted\":true}");
            Should.Throw<InvalidOperationException>(() => RunWithFailureEvidence(output, () =>
            {
                using JsonDocument pending = JsonDocument.Parse(File.ReadAllText(output));
                pending.RootElement.GetProperty("result").GetString().ShouldBe("pending");
                pending.RootElement.GetProperty("fullV1Accepted").GetBoolean().ShouldBeFalse();
                throw new InvalidOperationException("Failed before measurement");
            }));
            using JsonDocument failed = JsonDocument.Parse(File.ReadAllText(output));
            failed.RootElement.GetProperty("result").GetString().ShouldBe("failed");
            failed.RootElement.GetProperty("fullV1Accepted").GetBoolean().ShouldBeFalse();
            failed.RootElement.GetProperty("failures")[0].GetString().ShouldBe("Failed before measurement");
            failed.RootElement.GetProperty("error").GetString()!.ShouldContain(nameof(InvalidOperationException));
        }
        finally
        {
            File.Delete(output);
        }
    }

    /// <summary>Completion requires actual child measurements with the requested acceptance mode.</summary>
    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void CompletedChildEvidenceRequiresTheRequestedMode(bool requireV1)
    {
        string expected = requireV1 ? "passed" : "local-only";
        string wrong = requireV1 ? "local-only" : "passed";
        AssertCompletedEvidence(JsonSerializer.Serialize(new { result = expected, elapsedMilliseconds = 500, processId = 2 }), requireV1, 1);
        Should.Throw<ShouldAssertException>(() => AssertCompletedEvidence(
            JsonSerializer.Serialize(new { result = wrong, elapsedMilliseconds = 100, processId = 2 }), requireV1, 1));
    }

    /// <summary>Zero-exit no-ops, invalid measurements and parent-process evidence cannot pass.</summary>
    [Theory]
    [InlineData("{\"result\":\"pending\"}")]
    [InlineData("{\"result\":\"passed\",\"processId\":2}")]
    [InlineData("{\"result\":\"passed\",\"elapsedMilliseconds\":null,\"processId\":2}")]
    [InlineData("{\"result\":\"passed\",\"elapsedMilliseconds\":\"100\",\"processId\":2}")]
    [InlineData("{\"result\":\"passed\",\"elapsedMilliseconds\":500.0001,\"processId\":2}")]
    [InlineData("{\"result\":\"passed\",\"elapsedMilliseconds\":100,\"processId\":1}")]
    public void IncompleteChildEvidenceCannotPassAsAMeasurement(string evidence)
    {
        Should.Throw<ShouldAssertException>(() => AssertCompletedEvidence(evidence, true, 1));
    }

    /// <summary>Budget, diagnostics and strict scope violations compose into the recorded acceptance result.</summary>
    [Theory]
    [InlineData(500.0001, true, true, null, "failed", false, "First Catalog construction exceeded 500 ms.")]
    [InlineData(100, true, false, null, "failed", false, "Full-v1 gate: missing required production module(s): tenants")]
    [InlineData(100, false, false, null, "local-only", false, null)]
    [InlineData(500, true, true, null, "passed", true, null)]
    [InlineData(100, false, true, null, "local-only", false, null)]
    [InlineData(100, true, true, "Invalid contract", "failed", false, "Invalid contract")]
    public void ConstructionOutcomeRequiresBudgetScopeAndNoDiagnostics(double elapsed, bool requireV1, bool hasTenants,
        string? diagnostic, string result, bool accepted, string? failure)
    {
        var outcome = ConstructionOutcome(diagnostic is null ? [] : [diagnostic], elapsed,
            ["parties", "tenants"], hasTenants ? ["parties", "tenants", "sample"] : ["parties", "sample"], requireV1);
        outcome.Result.ShouldBe(result);
        outcome.FullV1Accepted.ShouldBe(accepted);
        outcome.Failures.ShouldBe(failure is null ? [] : [failure]);
        outcome.Missing.ShouldBe(hasTenants ? [] : ["tenants"]);
    }

    private static void AssertCompletedEvidence(string evidence, bool requireV1, int parentProcessId)
    {
        using JsonDocument document = JsonDocument.Parse(evidence);
        JsonElement root = document.RootElement;
        root.GetProperty("result").GetString().ShouldBe(requireV1 ? "passed" : "local-only", evidence);
        (root.TryGetProperty("elapsedMilliseconds", out JsonElement elapsed) && elapsed.ValueKind == JsonValueKind.Number
            && elapsed.TryGetDouble(out double milliseconds) && double.IsFinite(milliseconds) && milliseconds >= 0 && milliseconds <= 500).ShouldBeTrue(evidence);
        root.GetProperty("processId").GetInt32().ShouldNotBe(parentProcessId, evidence);
    }

    private static (string[] Failures, string Result, bool FullV1Accepted, string[] Missing) ConstructionOutcome(
        IEnumerable<string> diagnostics, double elapsed, IEnumerable<string> required, IEnumerable<string> discovered, bool requireV1)
    {
        string[] missing = required.Except(discovered, StringComparer.Ordinal).ToArray();
        string[] failures = [
            .. diagnostics,
            .. (LimitViolation(elapsed) is { } violation ? new[] { violation } : []),
            .. (requireV1 && missing.Length > 0 ? new[] { "Full-v1 gate: missing required production module(s): " + string.Join(", ", missing) } : []),
        ];
        return (failures, failures.Length == 0 ? (requireV1 ? "passed" : "local-only") : "failed", requireV1 && failures.Length == 0, missing);
    }

    private static string? LimitViolation(double elapsed)
        => elapsed > 500 ? "First Catalog construction exceeded 500 ms." : null;

    private static void InvalidateOutput(string output)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(output))!);
        File.WriteAllText(output, JsonSerializer.Serialize(new { result = "pending", fullV1Accepted = false }) + Environment.NewLine);
    }

    private static void RunWithFailureEvidence(string output, Action measure)
    {
        InvalidateOutput(output);
        try
        {
            measure();
        }
        catch (Exception exception)
        {
            RetainFailure(output, exception);
            throw;
        }
    }

    private static void RetainFailure(string output, Exception exception)
    {
        // Preserve a measured failure's population and elapsed time when the parent reports it.
        if (File.Exists(output))
        {
            using JsonDocument current = JsonDocument.Parse(File.ReadAllText(output));
            if (current.RootElement.GetProperty("result").GetString() == "failed")
            {
                return;
            }
        }

        File.WriteAllText(output, JsonSerializer.Serialize(new
        {
            result = "failed",
            fullV1Accepted = false,
            elapsedMilliseconds = (double?)null,
            failures = new[] { exception.Message },
            error = exception.ToString(),
        }, new JsonSerializerOptions { WriteIndented = true }) + Environment.NewLine);
    }

}
