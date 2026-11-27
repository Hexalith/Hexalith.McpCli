using Aspire.Hosting;
using Aspire.Hosting.ApplicationModel;
using Hexalith.EventStore.Aspire;

namespace Hexalith.McpCli.AppHost;

/// <summary>Uses the sealed Projects worker that projects authorized Tenant events.</summary>
internal sealed class PreparedProjectsWorkersProject : IProjectMetadata
{
    /// <inheritdoc />
    public string ProjectPath => Path.Combine(
        NativeSourceFixtures.ModuleRoot(RepositoryProjectPaths.GetRepositoryRoot(), "Hexalith.Projects"),
        "src", "Hexalith.Projects.Workers", "Hexalith.Projects.Workers.csproj");

    /// <inheritdoc />
    public bool SuppressBuild => true;
}
