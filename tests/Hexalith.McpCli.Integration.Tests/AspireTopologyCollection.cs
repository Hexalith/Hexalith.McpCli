namespace Hexalith.McpCli.Integration.Tests;

/// <summary>Shares one platform fixture and serializes the live topology tests.</summary>
[CollectionDefinition("AspireTopology", DisableParallelization = true)]
public sealed class AspireTopologyCollection : ICollectionFixture<AspireTopologyFixture>;
