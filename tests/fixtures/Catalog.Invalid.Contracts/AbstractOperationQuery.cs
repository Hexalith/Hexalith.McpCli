using Hexalith.McpCli.Abstractions;

namespace Catalog.Invalid.Contracts;

/// <summary>Exercises rejection of a decorated abstract contract.</summary>
[HexalithQuery("Abstract operation query.", Domain = "invalid", ProjectionType = "invalid-items")]
public abstract record AbstractOperationQuery;
