using Hexalith.McpCli.Abstractions;

namespace Catalog.Explicit.Contracts;

/// <summary>Omits the wire type required by an explicit-convention module.</summary>
[HexalithQuery("Missing explicit wire type query.", Domain = "explicit-fixture", ProjectionType = "explicit-fixture")]
public sealed record MissingWireQuery;
