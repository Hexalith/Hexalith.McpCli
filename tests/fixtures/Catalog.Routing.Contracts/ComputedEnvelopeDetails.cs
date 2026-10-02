namespace Catalog.Routing.Contracts;

/// <summary>An optional nested value in a computed command.</summary>
/// <param name="Note">An optional note that may be null.</param>
public sealed record ComputedEnvelopeDetails(string? Note);
