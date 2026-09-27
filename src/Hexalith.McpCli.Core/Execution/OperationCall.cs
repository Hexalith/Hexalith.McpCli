namespace Hexalith.McpCli.Core.Execution;

/// <summary>The common input carried by either operation call.</summary>
/// <param name="Operation">The canonical operation name.</param>
/// <param name="Payload">The raw JSON payload.</param>
/// <param name="Tenant">The optional MCP per-call tenant.</param>
/// <param name="AggregateId">The optional explicit aggregate identifier.</param>
public abstract record OperationCall(string Operation, string Payload, string? Tenant, string? AggregateId);
