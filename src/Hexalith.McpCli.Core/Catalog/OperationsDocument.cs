namespace Hexalith.McpCli.Core.Catalog;

/// <summary>The public operation-list document for one module.</summary>
/// <param name="Module">The canonical module name.</param>
/// <param name="Operations">The selected operations in canonical order.</param>
public sealed record OperationsDocument(string Module, IReadOnlyList<OperationSummary> Operations);
