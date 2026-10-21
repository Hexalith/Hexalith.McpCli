using System.Text.Json;
using Hexalith.McpCli.Core.Catalog;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Allows only exact, explicitly approved operation/code/property lint exceptions.</summary>
internal static class DescriptionLintGate
{
    /// <summary>Checks findings and rejects new or stale exceptions; no file means no accepted findings.</summary>
    internal static IReadOnlyList<string> Check(IEnumerable<(string Operation, LintFinding Finding)> findings, string? acceptedJson)
    {
        var actual = findings.Select(f => JsonSerializer.Serialize(new[] { f.Operation, f.Finding.Code, f.Finding.Property })).ToHashSet(StringComparer.Ordinal);
        var accepted = new HashSet<string>(StringComparer.Ordinal);
        if (acceptedJson is not null)
        {
            try
            {
                using JsonDocument document = JsonDocument.Parse(acceptedJson);
                if (document.RootElement.ValueKind != JsonValueKind.Array)
                {
                    return ["accepted lint: expected array."];
                }
                foreach (JsonElement row in document.RootElement.EnumerateArray())
                {
                    string[] fields = ["operation", "code", "property", "approvalReference"];
                    if (row.ValueKind != JsonValueKind.Object || row.EnumerateObject().Count() != fields.Length
                        || fields.Any(field => !row.TryGetProperty(field, out JsonElement value) || value.ValueKind != JsonValueKind.String || string.IsNullOrWhiteSpace(value.GetString())))
                    {
                        return ["accepted lint: expected operation, code, property and nonempty approvalReference."];
                    }
                    string key = JsonSerializer.Serialize(fields.Take(3).Select(field => row.GetProperty(field).GetString()).ToArray());
                    if (!accepted.Add(key))
                    {
                        return ["accepted lint: duplicate exception " + key + "."];
                    }
                }
            }
            catch (JsonException)
            {
                return ["accepted lint: invalid JSON."];
            }
        }
        return actual.Except(accepted).Select(key => "unapproved lint " + key + ".")
            .Concat(accepted.Except(actual).Select(key => "stale accepted lint " + key + ".")).Order(StringComparer.Ordinal).ToArray();
    }
}
