namespace Hexalith.McpCli.Core.Catalog;

/// <summary>Structured declaration error or warning retained for catalog policy.</summary>
/// <param name="TypeName">The affected contract type or assembly name.</param>
/// <param name="Category">Stable machine-readable diagnostic category.</param>
/// <param name="Severity">Either error or warning.</param>
/// <param name="Message">Human-readable explanation.</param>
public sealed record CatalogDiagnostic(string TypeName, string Category, string Severity, string Message);
