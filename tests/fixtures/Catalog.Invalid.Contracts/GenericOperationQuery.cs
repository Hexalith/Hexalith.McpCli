using Hexalith.McpCli.Abstractions;

namespace Catalog.Invalid.Contracts;

/// <summary>Exercises rejection of a decorated open generic contract.</summary>
/// <typeparam name="T">The unbound payload value type.</typeparam>
/// <param name="Value">The unbound payload value.</param>
[HexalithQuery("Open generic operation query.", Domain = "invalid", ProjectionType = "invalid-items")]
public sealed record GenericOperationQuery<T>(T Value);
