namespace Hexalith.McpCli.Core.Catalog;

/// <summary>The outcome of asking for the Catalog: the snapshot, or the error code that Catalog-dependent callers report.</summary>
/// <param name="Catalog">The built Catalog, or <see langword="null"/> when access failed.</param>
/// <param name="ErrorCode"><c>catalog_empty</c> or <c>catalog_invalid</c> when access failed; otherwise <see langword="null"/>.</param>
/// <param name="Message">A human-readable explanation of the failure; otherwise <see langword="null"/>.</param>
public sealed record CatalogAccess(CatalogSnapshot? Catalog, string? ErrorCode, string? Message);
