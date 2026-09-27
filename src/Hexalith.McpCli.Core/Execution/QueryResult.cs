using System.Text.Json;
using System.Text.Json.Serialization;

namespace Hexalith.McpCli.Core.Execution;

/// <summary>The public result of a gateway query.</summary>
/// <param name="Operation">The canonical operation name.</param>
/// <param name="Tenant">The resolved tenant.</param>
/// <param name="Document">The gateway payload, including JSON null when returned.</param>
/// <param name="Paging">Returned paging metadata, when present.</param>
public sealed record QueryResult(
    string Operation,
    string Tenant,
    [property: JsonIgnore(Condition = JsonIgnoreCondition.Never)] JsonElement? Document,
    [property: JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)] QueryPagingDocument? Paging = null);
