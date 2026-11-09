using System.Text.RegularExpressions;
using Shouldly;

namespace Hexalith.McpCli.Cli.Tests;

/// <summary>Pins the complete standard-error diagnostics a head may write around Gateway calls.</summary>
internal static partial class HeadDiagnostics
{
    private const string HttpCategory = "System.Net.Http.HttpClient.IEventStoreGatewayClient.";
    private const string McpCategory = "ModelContextProtocol.Server.McpServer";
    private const string CatalogCategory = "Hexalith.McpCli.Core.Catalog.CatalogProvider";

    /// <summary>
    /// Checks that standard error holds only informational console log entries: for each Gateway request the four
    /// client entries, with no exception text, and for the MCP head additionally only MCP server entries.
    /// </summary>
    /// <param name="result">The head result.</param>
    /// <param name="url">The Gateway base URL.</param>
    /// <param name="path">The Gateway request path.</param>
    /// <param name="status">The received status, or <see langword="null" /> when the request failed in transport.</param>
    /// <param name="requests">The number of Gateway requests the invocation made.</param>
    /// <param name="process">Whether to require the real stdio process lifecycle entries.</param>
    internal static void AssertGatewayOnly(HeadResult result, string url, string path, int? status, int requests = 1, bool process = false)
    {
        List<(string Level, string Category, string Id, string Message)> entries = Parse(result.Error);
        entries.ShouldAllBe(entry => entry.Level == "info", result.Error);
        var http = entries.Where(entry => entry.Category.StartsWith(HttpCategory, StringComparison.Ordinal)).ToList();
        entries.Except(http).ShouldAllBe(entry => result.Tool != null && IsMcpEntry(entry, process), result.Error);
        AssertProcessLifecycle(entries, result, process);
        http.Count.ShouldBe(4 * requests, result.Error);
        string target = url.TrimEnd('/') + path;
        for (int index = 0; index < http.Count; index += 4)
        {
            AssertEntry(http[index], "LogicalHandler", "100", "Start processing HTTP request POST " + Regex.Escape(target));
            AssertEntry(http[index + 1], "ClientHandler", "100", "Sending HTTP request POST " + Regex.Escape(target));
            if (status is null)
            {
                AssertEntry(http[index + 2], "ClientHandler", "104", @"HTTP request failed after [0-9.]+ms");
                AssertEntry(http[index + 3], "LogicalHandler", "104", @"HTTP request failed after [0-9.]+ms");
            }
            else
            {
                AssertEntry(http[index + 2], "ClientHandler", "101", @"Received HTTP response headers after [0-9.]+ms - " + status);
                AssertEntry(http[index + 3], "LogicalHandler", "101", @"End processing HTTP request after [0-9.]+ms - " + status);
            }
        }
    }

    /// <summary>
    /// Checks that standard error holds no Gateway client entry: only the expected number of Catalog warnings and, for
    /// the MCP head, informational MCP server entries.
    /// </summary>
    /// <param name="result">The head result.</param>
    /// <param name="catalogWarnings">The number of Catalog diagnostic warnings the manifest produces.</param>
    /// <param name="process">Whether to require the real stdio process lifecycle entries.</param>
    internal static void AssertNoGateway(HeadResult result, int catalogWarnings = 0, bool process = false)
    {
        if (result.Tool is null && catalogWarnings == 0)
        {
            result.Error.ShouldBeEmpty();
            return;
        }

        List<(string Level, string Category, string Id, string Message)> entries = Parse(result.Error);
        entries.Count(entry => entry.Level == "warn" && entry.Category == CatalogCategory).ShouldBe(catalogWarnings, result.Error);
        entries.ShouldAllBe(entry => entry.Level == "warn" && entry.Category == CatalogCategory
            || result.Tool != null && entry.Level == "info" && IsMcpEntry(entry, process), result.Error);
        AssertProcessLifecycle(entries, result, process);
    }

    private static bool IsMcpEntry((string Level, string Category, string Id, string Message) entry, bool process)
        => entry.Category == McpCategory || process && IsLifecycleEntry(entry);

    private static bool IsLifecycleEntry((string Level, string Category, string Id, string Message) entry)
    {
        if (entry.Category == "ModelContextProtocol.Server.StdioServerTransport")
            return (entry.Id, entry.Message) is
                ("857250842", "Server (stream) (hexalith) transport reading messages.")
                or ("1221292038", "Server (stream) (hexalith) transport completed reading messages.")
                or ("1375634372", "Server (stream) (hexalith) shutting down.")
                or ("1256455528", "Server (stream) (hexalith) shut down.");
        return entry.Category == "Microsoft.Hosting.Lifetime" && entry.Id == "0"
            && (entry.Message is "Application started. Press Ctrl+C to shut down." or "Hosting environment: Production"
                or "Application is shutting down..." || entry.Message == "Content root path: " + RepositoryRoot());
    }

    private static void AssertProcessLifecycle(List<(string Level, string Category, string Id, string Message)> entries,
        HeadResult result, bool process)
    {
        if (!process || result.Tool is null) return;
        var lifecycle = entries.Where(IsLifecycleEntry).ToArray();
        lifecycle.Length.ShouldBe(8, result.Error);
        lifecycle.Distinct().Count().ShouldBe(8, result.Error);
    }

    private static string RepositoryRoot()
    {
        for (DirectoryInfo? directory = new(AppContext.BaseDirectory); directory is not null; directory = directory.Parent)
            if (File.Exists(Path.Combine(directory.FullName, "Hexalith.McpCli.slnx"))) return directory.FullName;
        throw new InvalidOperationException("Repository root is missing.");
    }

    private static void AssertEntry((string Level, string Category, string Id, string Message) entry, string handler, string id,
        string message)
    {
        entry.Category.ShouldBe(HttpCategory + handler);
        entry.Id.ShouldBe(id);
        Regex.IsMatch(entry.Message, "^" + message + @"\z").ShouldBeTrue(entry.Message);
    }

    private static List<(string Level, string Category, string Id, string Message)> Parse(string stderr)
    {
        var entries = new List<(string Level, string Category, string Id, string Message)>();
        foreach (string line in stderr.Replace("\r\n", "\n", StringComparison.Ordinal).Split('\n', StringSplitOptions.RemoveEmptyEntries))
        {
            Match header = Header().Match(line);
            if (header.Success)
            {
                entries.Add((header.Groups["level"].Value, header.Groups["category"].Value, header.Groups["id"].Value, string.Empty));
                continue;
            }

            entries.Count.ShouldBeGreaterThan(0, "Standard error has text outside a console log entry: " + line);
            line.ShouldStartWith("      ", customMessage: "Unindented standard error line: " + line);
            (string level, string category, string id, string message) = entries[^1];
            entries[^1] = (level, category, id, message.Length == 0 ? line.Trim() : message + "\n" + line.Trim());
        }

        return entries;
    }

    [GeneratedRegex(@"^(?<level>trce|dbug|info|warn|fail|crit): (?<category>[A-Za-z0-9_.]+)\[(?<id>[0-9]+)\]\z")]
    private static partial Regex Header();
}
