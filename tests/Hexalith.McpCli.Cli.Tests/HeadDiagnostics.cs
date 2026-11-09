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
    internal static void AssertGatewayOnly(HeadResult result, string url, string path, int? status, int requests = 1)
    {
        List<(string Level, string Category, string Id, string Message)> entries = Parse(result.Error);
        entries.ShouldAllBe(entry => entry.Level == "info", result.Error);
        var http = entries.Where(entry => entry.Category.StartsWith(HttpCategory, StringComparison.Ordinal)).ToList();
        entries.Except(http).ShouldAllBe(entry => result.Tool != null && entry.Category == McpCategory, result.Error);
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
    internal static void AssertNoGateway(HeadResult result, int catalogWarnings = 0)
    {
        if (result.Tool is null && catalogWarnings == 0)
        {
            result.Error.ShouldBeEmpty();
            return;
        }

        List<(string Level, string Category, string Id, string Message)> entries = Parse(result.Error);
        entries.Count(entry => entry.Level == "warn" && entry.Category == CatalogCategory).ShouldBe(catalogWarnings, result.Error);
        entries.ShouldAllBe(entry => entry.Level == "warn" && entry.Category == CatalogCategory
            || result.Tool != null && entry.Level == "info" && entry.Category == McpCategory, result.Error);
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
