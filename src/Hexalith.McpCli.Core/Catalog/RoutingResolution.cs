namespace Hexalith.McpCli.Core.Catalog;

/// <summary>Resolved routing with the declaration warnings it produced.</summary>
/// <param name="Routing">The resolved gateway routing values.</param>
/// <param name="Warnings">The <c>redundant_value</c> and <c>conflicting_value</c> warnings, in field order.</param>
internal sealed record RoutingResolution(OperationRouting Routing, IReadOnlyList<CatalogDiagnostic> Warnings);
