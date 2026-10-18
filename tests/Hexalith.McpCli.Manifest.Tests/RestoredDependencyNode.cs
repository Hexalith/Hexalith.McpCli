namespace Hexalith.McpCli.Manifest.Tests;

/// <summary>A resolved package or project and its outgoing dependency edges.</summary>
/// <param name="Id">The resolved identity.</param>
/// <param name="Version">The resolved version.</param>
/// <param name="Type">The NuGet target type.</param>
/// <param name="Dependencies">The dependency identities and requested versions.</param>
/// <param name="FrameworkReferences">The framework names carried by the target.</param>
/// <param name="ProjectPath">The absolute project path for a project target.</param>
internal sealed record RestoredDependencyNode(
    string Id,
    string Version,
    string Type,
    IReadOnlyDictionary<string, string> Dependencies,
    IReadOnlyList<string> FrameworkReferences,
    string? ProjectPath = null)
{
    /// <summary>Gets the identity used in a diagnostic dependency path.</summary>
    public string Identity => Type == "project" ? Id : $"{Id}/{Version}";
}
