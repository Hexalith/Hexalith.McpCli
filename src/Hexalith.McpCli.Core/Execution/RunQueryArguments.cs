namespace Hexalith.McpCli.Core.Execution;

/// <summary>Arguments for one gateway query.</summary>
/// <param name="Operation">The canonical read operation.</param>
/// <param name="Payload">The raw JSON query payload.</param>
/// <param name="Tenant">The optional MCP per-call tenant.</param>
/// <param name="AggregateId">The optional explicit aggregate identifier.</param>
/// <param name="EntityId">The optional entity identifier.</param>
/// <param name="PageSize">The optional requested page size.</param>
/// <param name="Offset">The optional zero-based offset.</param>
/// <param name="Cursor">The optional cursor.</param>
public sealed record RunQueryArguments(
    string Operation,
    string Payload,
    string? Tenant = null,
    string? AggregateId = null,
    string? EntityId = null,
    int? PageSize = null,
    int? Offset = null,
    string? Cursor = null)
    : OperationCall(Operation, Payload, Tenant, AggregateId);
