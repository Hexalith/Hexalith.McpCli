using System.Text.Json.Serialization;

namespace Hexalith.McpCli.Core.Catalog;

/// <summary>A warning about the description quality of one valid operation.</summary>
/// <param name="Code">The stable finding code.</param>
/// <param name="Severity">The warning severity.</param>
/// <param name="Message">An actionable explanation.</param>
/// <param name="Property">The RFC 6901 pointer to a payload schema property, when applicable.</param>
public sealed record LintFinding(
    string Code,
    string Severity,
    string Message,
    [property: JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)] string? Property = null);
