using System.Reflection;
using Hexalith.McpCli.Core.Settings;
using Hexalith.McpCli.Sample.Contracts;

namespace Hexalith.McpCli.StdioHost;

/// <summary>Runs the actual CLI with project-referenced Contracts in an isolated child process.</summary>
internal static class Program
{
    private static async Task<int> Main(string[] args)
    {
        Assembly[] manifest = Environment.GetEnvironmentVariable("MCPCLI_STDIO_CATALOG") switch
        {
            "empty" => [typeof(Manifest.MarkedEmpty.Contracts.Module).Assembly],
            "diagnostic" => [typeof(Catalog.InvalidProvider.Contracts.Module).Assembly],
            _ => [typeof(CreateItemCommand).Assembly],
        };
        Type runnerType = Assembly.Load(new AssemblyName("Hexalith.McpCli"))
            .GetType("Hexalith.McpCli.Cli.CliRunner", throwOnError: true)!;
        ConstructorInfo constructor = runnerType.GetConstructor(BindingFlags.Instance | BindingFlags.NonPublic,
            binder: null, [typeof(ProfileStore), typeof(Func<IReadOnlyList<Assembly>>)], modifiers: null)!;
        string? profilePath = Environment.GetEnvironmentVariable("MCPCLI_STDIO_PROFILE_PATH");
        object runner = constructor.Invoke([new ProfileStore(profilePath), (Func<IReadOnlyList<Assembly>>)(() => manifest)]);
        MethodInfo invoke = runnerType.GetMethod("InvokeAsync", BindingFlags.Instance | BindingFlags.NonPublic,
            binder: null, [typeof(IReadOnlyList<string>), typeof(CancellationToken)], modifiers: null)!;
        return await ((Task<int>)invoke.Invoke(runner, [args, CancellationToken.None])!).ConfigureAwait(false);
    }
}
