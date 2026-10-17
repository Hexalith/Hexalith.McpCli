namespace Hexalith.McpCli.Core.Tests;

/// <summary>An explicit inventory decision, whose authenticity needs independent owner evidence.</summary>
/// <param name="Status">The recorded approval status.</param>
/// <param name="Authority">The approving role, limited to owner decisions or synthetic fixture certification.</param>
/// <param name="Reference">The evidence reference for the decision.</param>
internal sealed record InventoryCoverageApproval(string Status, string Authority, string Reference);
