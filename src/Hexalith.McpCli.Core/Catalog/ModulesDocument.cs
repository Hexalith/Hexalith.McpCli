namespace Hexalith.McpCli.Core.Catalog;

/// <summary>The public module-list document.</summary>
/// <param name="Modules">The declared modules in canonical order.</param>
public sealed record ModulesDocument(IReadOnlyList<ModuleSummary> Modules);
