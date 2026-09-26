namespace Hexalith.McpCli.Core.Catalog;

/// <summary>Resolved gateway routing values, independent of the public operation name.</summary>
/// <param name="Domain">The gateway domain.</param>
/// <param name="WireType">The gateway command or query type.</param>
/// <param name="ProjectionType">The query projection type, when applicable.</param>
/// <param name="ProjectionActorType">The optional query projection actor type.</param>
public sealed record OperationRouting(string Domain, string WireType, string? ProjectionType, string? ProjectionActorType);
