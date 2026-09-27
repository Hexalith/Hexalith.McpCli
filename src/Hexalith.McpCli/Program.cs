using System.Reflection;
using Hexalith.McpCli.Cli;

namespace Hexalith.McpCli;

/// <summary>
/// Dispatches the hexalith command line.
/// </summary>
internal static class Program
{
    private static Task<int> Main(string[] args)
    {
        if (args.Length == 1 && args[0] == "--version")
        {
            string version = Assembly.GetExecutingAssembly()
                .GetCustomAttribute<AssemblyInformationalVersionAttribute>()?.InformationalVersion ?? "0.0.0";
            Console.Out.WriteLine(version);
            return Task.FromResult(0);
        }

        return new CliRunner().CreateRoot().Parse(args).InvokeAsync();
    }
}
