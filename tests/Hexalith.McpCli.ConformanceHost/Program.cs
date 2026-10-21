using System.Reflection;
using System.Text.Json;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Core.Settings;

namespace Hexalith.McpCli.Hosting;

/// <summary>Out-of-process adapter around the production or explicitly packaged fixture CLI and MCP heads.</summary>
internal static class Program
{
    private static (string PackageId, string AssemblyName)[] ManifestEntries()
    {
#if CONFORMANCE_PRODUCTION
        Type manifest = Assembly.Load("Hexalith.McpCli").GetType("Hexalith.McpCli.Hosting.ModuleAssemblyManifest", throwOnError: true)!;
        return ((string PackageId, string AssemblyName)[])manifest.GetField("Entries", BindingFlags.Static | BindingFlags.NonPublic)!.GetValue(null)!;
#else
        return ModuleAssemblyManifest.Entries;
#endif
    }

    private static IReadOnlyList<Assembly> ManifestAssemblies()
        => ManifestEntries().Select(entry => Assembly.Load(new AssemblyName(entry.AssemblyName))).ToArray();

    private static async Task<int> Main(string[] args)
    {
        if (args is ["--validate-vectors", .. var vectors])
        {
            return await VectorCompatibilityValidator.ValidateAsync(ManifestAssemblies(), vectors).ConfigureAwait(false);
        }

        if (args is ["--full-catalog"])
        {
            CatalogSnapshot snapshot = CatalogBuilder.Build(ManifestAssemblies());
            Console.Out.WriteLine(JsonSerializer.Serialize(snapshot, Hexalith.McpCli.Core.Serialization.McpCliJson.Result));
            return snapshot.Diagnostics.Count == 0 ? 0 : 1;
        }

        if (args is ["--inventory", string inventory])
        {
            var provider = new CatalogProvider(() => ManifestAssemblies(),
                Microsoft.Extensions.Logging.Abstractions.NullLogger<CatalogProvider>.Instance);
            var catalog = new CatalogService(provider, new ExecutionAvailability(false, false), strict: true);
            var findings = Hexalith.McpCli.Core.Tests.InventoryCoverageGate.CheckFile(inventory, catalog, provider);
            Console.Out.WriteLine(JsonSerializer.Serialize(findings));
            return findings.Count == 0 ? 0 : 1;
        }

        if (args is ["--manifest-catalog"])
        {
            object[] packages = ManifestEntries().Select(entry => new
            {
                packageId = entry.PackageId,
                assemblyName = entry.AssemblyName,
                operations = CatalogBuilder.Build([Assembly.Load(new AssemblyName(entry.AssemblyName))])
                    .Modules.SelectMany(module => module.Operations)
                    .Select(operation => new { name = operation.Name, kind = operation.Kind.ToString().ToLowerInvariant() })
                    .ToArray(),
            }).Cast<object>().ToArray();
            Console.Out.WriteLine(JsonSerializer.Serialize(packages));
            return 0;
        }

        Type runnerType = Assembly.Load(new AssemblyName("Hexalith.McpCli"))
            .GetType("Hexalith.McpCli.Cli.CliRunner", throwOnError: true)!;
        ConstructorInfo constructor = runnerType.GetConstructor(BindingFlags.Instance | BindingFlags.NonPublic,
            binder: null, [typeof(ProfileStore), typeof(Func<IReadOnlyList<Assembly>>)], modifiers: null)!;
        Func<IReadOnlyList<Assembly>> manifest = ManifestAssemblies;
        string? profilePath = Environment.GetEnvironmentVariable("MCPCLI_CONFORMANCE_PROFILE_PATH");
        object runner = constructor.Invoke([new ProfileStore(profilePath), manifest]);
        MethodInfo invoke = runnerType.GetMethod("InvokeAsync", BindingFlags.Instance | BindingFlags.NonPublic,
            binder: null, [typeof(IReadOnlyList<string>), typeof(CancellationToken)], modifiers: null)!;
        return await ((Task<int>)invoke.Invoke(runner, [args, CancellationToken.None])!).ConfigureAwait(false);
    }
}
