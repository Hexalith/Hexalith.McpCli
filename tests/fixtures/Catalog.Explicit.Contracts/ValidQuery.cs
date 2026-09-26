using Hexalith.McpCli.Abstractions;

namespace Catalog.Explicit.Contracts;

/// <summary>Supplies the wire type required by an explicit-convention module.</summary>
[HexalithQuery("Valid explicit-route query.", Domain = "explicit-fixture", WireType = "explicit-wire",
    ProjectionType = "explicit-fixture")]
public sealed record ValidQuery;
