using System.Reflection;
using System.Runtime.Loader;
using Hexalith.McpCli.Abstractions;
using Hexalith.McpCli.Core.Catalog;
using Shouldly;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Pins the host Abstractions binder used when enrolled Contracts request a published assembly version.</summary>
public sealed class CatalogAbstractionsResolverTests
{
    /// <summary>A published Abstractions identity resolves to the host assembly; any other name is ignored.</summary>
    [Fact]
    public void PublishedAbstractionsIdentityBindsTheHostAssembly()
    {
        CatalogAbstractionsResolver.Register();
        Assembly host = typeof(HexalithModuleAttribute).Assembly;
        CatalogAbstractionsResolver.Resolve(
            AssemblyLoadContext.Default,
            new AssemblyName("Hexalith.McpCli.Abstractions, Version=3.0.0.0, Culture=neutral, PublicKeyToken=null"))
            .ShouldBe(host);
        CatalogAbstractionsResolver.Resolve(
            AssemblyLoadContext.Default,
            new AssemblyName("Hexalith.McpCli.Abstractions, Version=99.0.0.0"))
            .ShouldBe(host);
        CatalogAbstractionsResolver.Resolve(AssemblyLoadContext.Default, new AssemblyName("Newtonsoft.Json"))
            .ShouldBeNull();
    }

    /// <summary>Enrolled Parties Contracts can read the host module attribute after the binder is registered.</summary>
    [Fact]
    public void EnrolledPartiesContractsReadTheHostModuleAttribute()
    {
        CatalogAbstractionsResolver.Register();
        Assembly contracts = Assembly.Load("Hexalith.Parties.Contracts");
        HexalithModuleAttribute marker = contracts.GetCustomAttribute<HexalithModuleAttribute>().ShouldNotBeNull();
        marker.Name.ShouldBe("parties");
        CatalogBuilder.Build([contracts]).Modules.Select(module => module.Name).ShouldContain("parties");
    }
}
