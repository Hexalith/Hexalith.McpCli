using Aspire.Hosting;
using Aspire.Hosting.ApplicationModel;

using Hexalith.EventStore.Aspire;
using Hexalith.McpCli.AppHost;

namespace Hexalith.McpCli.Manifest.Tests;

/// <summary>Keeps SDK owner preparation off the sealed native launch resource.</summary>
public sealed class NativeCatalogRuntimeTests : IDisposable
{
    private readonly string _root = Path.Combine(Path.GetTempPath(), "mcpcli-catalog-prep-" + Guid.NewGuid().ToString("N"));

    /// <summary>Creates one inert project file used as both launched and preparation identities.</summary>
    public NativeCatalogRuntimeTests()
    {
        Directory.CreateDirectory(_root);
        File.WriteAllText(ProjectPath,
            "<Project Sdk=\"Microsoft.NET.Sdk\"><PropertyGroup><TargetFramework>net11.0</TargetFramework>"
            + "<EnableDefaultItems>false</EnableDefaultItems></PropertyGroup></Project>");
    }

    private string ProjectPath => Path.Combine(_root, "Hexalith.Tenants.csproj");

    /// <summary>A suppressed or argument-overridden launch cannot be the resource passed to PrepareAsync.</summary>
    [Theory]
    [InlineData("suppressed")]
    [InlineData("launch-override")]
    [InlineData("ordinary")]
    public void PreparationSourceUsesBuildCapableCloneOnlyWhenLaunchIsBlocked(string kind)
    {
        IDistributedApplicationBuilder builder = DistributedApplication.CreateBuilder(
            new DistributedApplicationOptions { DisableDashboard = true });
#pragma warning disable ASPIREPROJECTS001
        IResourceBuilder<ProjectResource> launched = builder.AddResource(new ProjectResource("tenants"))
            .WithAnnotation(new SelectedMetadata(ProjectPath, kind == "suppressed"))
            .WithProjectDefaults(new ProjectResourceOptions { ExcludeLaunchProfile = true });
#pragma warning restore ASPIREPROJECTS001
        if (kind == "launch-override") launched.WithAnnotation(new LaunchToolArgsCallbackAnnotation());
        IResourceBuilder<ProjectResource> source = NativeCatalogRuntime.PreparationSource(builder, launched);
        if (kind == "ordinary")
        {
            Assert.Same(launched.Resource, source.Resource);
            Assert.False(NativeCatalogRuntime.PreparationBlocked(launched.Resource));
            return;
        }
        Assert.NotSame(launched.Resource, source.Resource);
        Assert.Equal("tenants-catalog-source", source.Resource.Name);
        Assert.False(source.Resource.GetProjectMetadata().SuppressBuild);
        Assert.Equal(Path.GetFullPath(ProjectPath), Path.GetFullPath(source.Resource.GetProjectMetadata().ProjectPath));
        Assert.Contains(source.Resource.Annotations, annotation => annotation is ExplicitStartupAnnotation);
        Assert.True(NativeCatalogRuntime.PreparationBlocked(launched.Resource));
        Assert.False(NativeCatalogRuntime.PreparationBlocked(source.Resource));
    }

    /// <summary>Catalog composition must keep the launched receiver even when preparation used a clone.</summary>
    [Fact]
    public void BindOwnerKeepsLaunchedReceiverWhenPreparationUsedAClone()
    {
        IDistributedApplicationBuilder builder = DistributedApplication.CreateBuilder(
            new DistributedApplicationOptions { DisableDashboard = true });
#pragma warning disable ASPIREPROJECTS001
        IResourceBuilder<ProjectResource> launched = builder.AddResource(new ProjectResource("tenants"))
            .WithAnnotation(new SelectedMetadata(ProjectPath, true))
            .WithProjectDefaults(new ProjectResourceOptions { ExcludeLaunchProfile = true });
#pragma warning restore ASPIREPROJECTS001
        IResourceBuilder<ProjectResource> source = NativeCatalogRuntime.PreparationSource(builder, launched);
        var prepared = new DevelopmentRouteCatalogOwner(source, typeof(NativeCatalogRuntimeTests).Assembly,
            typeof(NativeCatalogRuntime).Assembly);
        DevelopmentRouteCatalogOwner bound = NativeCatalogRuntime.BindOwner(prepared, launched);
        Assert.Same(launched, bound.Project);
        Assert.Same(prepared.Contracts, bound.Contracts);
        Assert.Same(prepared.Adapters, bound.Adapters);
        var alreadyBound = new DevelopmentRouteCatalogOwner(launched, prepared.Contracts, prepared.Adapters);
        Assert.Same(alreadyBound, NativeCatalogRuntime.BindOwner(alreadyBound, launched));
    }

    /// <inheritdoc />
    public void Dispose() => Directory.Delete(_root, recursive: true);

    private sealed class SelectedMetadata(string path, bool suppressBuild) : IProjectMetadata
    {
        public string ProjectPath { get; } = path;
        public bool SuppressBuild { get; } = suppressBuild;
    }

    private sealed class LaunchToolArgsCallbackAnnotation : IResourceAnnotation;
}
