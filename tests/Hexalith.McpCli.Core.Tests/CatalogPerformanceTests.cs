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
        string output = Environment.GetEnvironmentVariable("MCPCLI_BENCHMARK_OUTPUT")
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
            start.ArgumentList.Add(typeof(CatalogPerformanceTests).FullName + ".MeasureFirstConstruction");
            start.Environment["MCPCLI_BENCHMARK_PROBE"] = "1";
            start.Environment["MCPCLI_BENCHMARK_OUTPUT"] = output;
            using Process process = Process.Start(start)!;
            Task<string> stdout = process.StandardOutput.ReadToEndAsync(TestContext.Current.CancellationToken);
            Task<string> stderr = process.StandardError.ReadToEndAsync(TestContext.Current.CancellationToken);
            await process.WaitForExitAsync(TestContext.Current.CancellationToken);
            process.ExitCode.ShouldBe(0, await stdout + await stderr + (File.Exists(output) ? File.ReadAllText(output) : "Missing benchmark evidence."));
        }
        catch (Exception exception)
        {
            RetainFailure(output, exception);
            throw;
        }
    }

    /// <summary>Measures one cold Build after loading its assembly population; also retains failures as JSON.</summary>
    [Fact]
    public void MeasureFirstConstruction()
    {
        if (Environment.GetEnvironmentVariable("MCPCLI_BENCHMARK_PROBE") != "1")
        {
            return;
        }

        string output = Environment.GetEnvironmentVariable("MCPCLI_BENCHMARK_OUTPUT")!;
        RunWithFailureEvidence(output, () =>
        {
            Assembly cli = Assembly.Load("Hexalith.McpCli");
            Type manifest = cli.GetType("Hexalith.McpCli.Hosting.ModuleAssemblyManifest", throwOnError: true)!;
            var entries = ((string PackageId, string AssemblyName)[])manifest.GetField("Entries", BindingFlags.NonPublic | BindingFlags.Static)!.GetValue(null)!;
            Assembly sample = typeof(CreateItemCommand).Assembly;
            Assembly[] assemblies = entries.Select(entry => Assembly.Load(entry.AssemblyName)).Append(sample).ToArray();
            sample.GetCustomAttribute<HexalithModuleAttribute>()!.IdentifierKind.ShouldBe(IdentifierKind.Ulid);
            assemblies.Distinct().Count().ShouldBe(entries.Length + 1);
            using JsonDocument scope = JsonDocument.Parse(File.ReadAllText(Path.Combine(AppContext.BaseDirectory, "conformance", "v1-scope.json")));
            string[] required = scope.RootElement.GetProperty("requiredModules").EnumerateArray().Select(value => value.GetString()!).ToArray();
            // No Catalog construction occurs in this process before this measured call.
            var clock = Stopwatch.StartNew();
            CatalogSnapshot catalog = CatalogBuilder.Build(assemblies);
            clock.Stop();
            string[] missing = required.Except(catalog.Modules.Select(module => module.Name), StringComparer.Ordinal).ToArray();
            bool requireV1 = Environment.GetEnvironmentVariable("MCPCLI_BENCHMARK_REQUIRE_V1") == "true";
            string[] failures = [
                .. catalog.Diagnostics.Select(diagnostic => diagnostic.Message),
                .. (LimitViolation(clock.Elapsed.TotalMilliseconds) is { } violation ? new[] { violation } : []),
                .. (requireV1 && missing.Length > 0 ? new[] { "Full-v1 gate: missing required production module(s): " + string.Join(", ", missing) } : []),
            ];
            string evidence = JsonSerializer.Serialize(new
            {
                result = failures.Length == 0 ? (requireV1 ? "passed" : "local-only") : "failed",
                fullV1Accepted = requireV1 && failures.Length == 0,
                elapsedMilliseconds = clock.Elapsed.TotalMilliseconds,
                limitMilliseconds = 500,
                processId = Environment.ProcessId,
                assemblies = assemblies.Select(assembly => assembly.GetName().Name),
                productionPackages = entries.Select(entry => entry.PackageId),
                modules = catalog.Modules.Select(module => new { module.Name, identifierKind = module.IdentifierKind.ToString(), operationCount = module.Operations.Count }),
                missingRequiredModules = missing,
                diagnostics = catalog.Diagnostics,
                failures,
            }, new JsonSerializerOptions { WriteIndented = true });
            Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(output))!);
            File.WriteAllText(output, evidence + Environment.NewLine);
            failures.ShouldBeEmpty(evidence);
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
    [Theory]
    [InlineData("scope")]
    [InlineData("loading")]
    [InlineData("construction")]
    public void EarlyFailureInvalidatesPriorSuccessfulEvidence(string phase)
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
                throw new InvalidOperationException(phase + " failed before measurement");
            }));
            using JsonDocument failed = JsonDocument.Parse(File.ReadAllText(output));
            failed.RootElement.GetProperty("result").GetString().ShouldBe("failed");
            failed.RootElement.GetProperty("fullV1Accepted").GetBoolean().ShouldBeFalse();
            failed.RootElement.GetProperty("failures")[0].GetString().ShouldBe(phase + " failed before measurement");
            failed.RootElement.GetProperty("error").GetString()!.ShouldContain(nameof(InvalidOperationException));
        }
        finally
        {
            File.Delete(output);
        }
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
