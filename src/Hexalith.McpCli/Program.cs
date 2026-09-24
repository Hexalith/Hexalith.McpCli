using Hexalith.McpCli.Hosting;

namespace Hexalith.McpCli;

/// <summary>
/// Holds the executable entry point until the CLI and MCP heads are implemented.
/// </summary>
internal static class Program
{
    private static int Main()
    {
        _ = ModuleAssemblyManifest.Entries;
        Console.Error.WriteLine("The Hexalith MCP CLI is not implemented yet.");
        return 2;
    }
}
