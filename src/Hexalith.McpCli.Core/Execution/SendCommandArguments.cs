namespace Hexalith.McpCli.Core.Execution;

/// <summary>Arguments for one gateway command submission.</summary>
/// <param name="Operation">The canonical write operation.</param>
/// <param name="Payload">The raw JSON command payload.</param>
/// <param name="Tenant">The optional MCP per-call tenant.</param>
/// <param name="AggregateId">The optional explicit aggregate identifier; a canonical uppercase ULID in ULID-kind modules.</param>
/// <param name="CorrelationId">The optional caller-supplied canonical uppercase ULID correlation identifier.</param>
/// <param name="IdempotencyKey">The optional caller-supplied canonical uppercase ULID idempotency key.</param>
/// <param name="Extensions">Optional allowlisted extension metadata.</param>
public sealed record SendCommandArguments(
    string Operation,
    string Payload,
    string? Tenant = null,
    string? AggregateId = null,
    string? CorrelationId = null,
    string? IdempotencyKey = null,
    IReadOnlyDictionary<string, string>? Extensions = null)
    : OperationCall(Operation, Payload, Tenant, AggregateId);
