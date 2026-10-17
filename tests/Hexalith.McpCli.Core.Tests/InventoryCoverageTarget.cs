namespace Hexalith.McpCli.Core.Tests;

/// <summary>A unique normalized intended operation, shared by any number of legacy rows.</summary>
/// <param name="Id">The stable inventory target identity.</param>
/// <param name="Name">The canonical public operation name.</param>
/// <param name="ContractType">The exact internal CLR full name.</param>
internal sealed record InventoryCoverageTarget(string Id, string Name, string ContractType);
