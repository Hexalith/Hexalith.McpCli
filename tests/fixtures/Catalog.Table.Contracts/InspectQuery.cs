using Hexalith.McpCli.Abstractions;

namespace Catalog.Table.Contracts;

/// <summary>Provides an operation description with structural table characters.</summary>
[HexalithQuery("tab\tand\nline\r\\path", Domain = "table-fixture", WireType = "table-wire",
    ProjectionType = "table-fixture")]
public sealed record InspectQuery;
