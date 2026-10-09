using System.CommandLine;
using System.Reflection;
using System.Text.Json;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Core.Settings;

namespace Hexalith.McpCli.Hosting;

/// <summary>Out-of-process adapter around the built CLI and MCP heads with a flagged test Contracts package.</summary>
internal static class Program
{
    private static async Task<int> Main(string[] args)
    {
        if (args is ["--manifest-catalog"])
        {
            object[] packages = ModuleAssemblyManifest.Entries.Select(entry => new
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
        Func<IReadOnlyList<Assembly>> manifest = () => ModuleAssemblyManifest.Entries
            .Select(entry => Assembly.Load(new AssemblyName(entry.AssemblyName)))
            .ToArray();
        string? profilePath = Environment.GetEnvironmentVariable("MCPCLI_CONFORMANCE_PROFILE_PATH");
        object runner = constructor.Invoke([new ProfileStore(profilePath), manifest]);
        MethodInfo invoke = runnerType.GetMethod("InvokeAsync", BindingFlags.Instance | BindingFlags.NonPublic,
            binder: null, [typeof(IReadOnlyList<string>), typeof(CancellationToken)], modifiers: null)!;
        return await ((Task<int>)invoke.Invoke(runner, [args, CancellationToken.None])!).ConfigureAwait(false);
    }
}
