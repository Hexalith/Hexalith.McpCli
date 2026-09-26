namespace Hexalith.McpCli.Core.Catalog;

/// <summary>An operation row in the public discovery document.</summary>
/// <param name="Name">The canonical operation name.</param>
/// <param name="Kind">The public read or write kind.</param>
/// <param name="Description">The operation description.</param>
public sealed record OperationSummary(string Name, string Kind, string Description);
