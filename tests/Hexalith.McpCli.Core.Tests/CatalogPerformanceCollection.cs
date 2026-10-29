namespace Hexalith.McpCli.Core.Tests;

/// <summary>Runs cold Catalog measurements without concurrent test collections competing for CPU.</summary>
[CollectionDefinition(Name, DisableParallelization = true)]
public sealed class CatalogPerformanceCollection
{
    /// <summary>The collection shared by the cold measurement and its contract tests.</summary>
    public const string Name = "CatalogPerformance";
}
