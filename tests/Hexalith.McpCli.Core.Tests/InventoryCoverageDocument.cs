namespace Hexalith.McpCli.Core.Tests;

/// <summary>A validated test-only version-one migration inventory.</summary>
/// <param name="Module">The canonical module under comparison.</param>
/// <param name="Purpose">Whether the evidence is synthetic fixture certification or owner release coverage.</param>
/// <param name="Targets">The unique normalized intended operations.</param>
/// <param name="LegacyRows">The source decisions referring to the targets.</param>
internal sealed record InventoryCoverageDocument(string Module, string Purpose,
    IReadOnlyList<InventoryCoverageTarget> Targets, IReadOnlyList<InventoryCoverageRow> LegacyRows);
