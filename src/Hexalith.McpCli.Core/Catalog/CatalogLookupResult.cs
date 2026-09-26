using Hexalith.McpCli.Core.Execution;

namespace Hexalith.McpCli.Core.Catalog;

/// <summary>A discovery result containing exactly one success document or error.</summary>
/// <typeparam name="T">The success document type.</typeparam>
/// <param name="Document">The success document.</param>
/// <param name="Error">The error document.</param>
public sealed record CatalogLookupResult<T>(T? Document, OperationError? Error)
    where T : class;
