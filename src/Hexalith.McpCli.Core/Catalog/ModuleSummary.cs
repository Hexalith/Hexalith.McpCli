namespace Hexalith.McpCli.Core.Catalog;

/// <summary>A module row in the public discovery document.</summary>
/// <param name="Name">The canonical module name.</param>
/// <param name="Description">The module description.</param>
/// <param name="OperationCount">The number of valid operations.</param>
public sealed record ModuleSummary(string Name, string Description, int OperationCount);
