using Hexalith.McpCli.Abstractions;

namespace Catalog.Invalid.Contracts;

/// <summary>Preserves the former missing-selector case as an accepted computed query regression.</summary>
[HexalithQuery("Computed query without projection selectors.", Domain = "invalid")]
public sealed record MissingProjectionQuery;
