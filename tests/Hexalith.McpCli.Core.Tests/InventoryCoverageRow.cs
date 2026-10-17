namespace Hexalith.McpCli.Core.Tests;

/// <summary>A legacy surface decision and its normalized target references.</summary>
/// <param name="Id">The stable legacy row identity.</param>
/// <param name="LegacyOperation">The inventoried source surface.</param>
/// <param name="TargetIds">The referenced unique intended targets.</param>
/// <param name="Disposition">The replace, withdraw or defer decision.</param>
/// <param name="Coverage">Whether the target is included or excluded.</param>
/// <param name="Rationale">The reason for the decision.</param>
/// <param name="Approval">The explicit approval evidence.</param>
internal sealed record InventoryCoverageRow(string Id, string LegacyOperation, IReadOnlyList<string> TargetIds,
    string Disposition, string Coverage, string Rationale, InventoryCoverageApproval Approval);
