namespace Hexalith.McpCli.Core.Catalog;

/// <summary>Provides the shared discovery documents used by both heads.</summary>
public interface ICatalog
{
    /// <summary>Lists declared modules.</summary>
    CatalogLookupResult<ModulesDocument> ListModules();

    /// <summary>Lists the operations of one declared module.</summary>
    /// <param name="module">A non-empty module name, checked by the head.</param>
    /// <param name="kind">An optional public kind: <c>read</c> or <c>write</c>.</param>
    CatalogLookupResult<OperationsDocument> ListOperations(string module, string? kind = null);

    /// <summary>Describes one declared operation and its session availability.</summary>
    /// <param name="operation">A non-empty operation name, checked by the head.</param>
    CatalogLookupResult<OperationDescriptionDocument> Describe(string operation);
}
