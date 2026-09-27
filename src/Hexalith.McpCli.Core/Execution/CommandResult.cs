using System.Text.Json;
using System.Text.Json.Serialization;

namespace Hexalith.McpCli.Core.Execution;

/// <summary>The public result of an accepted command.</summary>
/// <param name="Operation">The canonical operation name.</param>
/// <param name="MessageId">The gateway's canonical message identifier.</param>
/// <param name="CorrelationId">The gateway correlation identifier.</param>
/// <param name="Tenant">The resolved tenant.</param>
/// <param name="AggregateId">The resolved aggregate identifier.</param>
/// <param name="Status">The accepted status.</param>
/// <param name="IdempotencyKey">The caller-supplied idempotency key, when present.</param>
/// <param name="Result">The optional gateway result payload.</param>
public sealed record CommandResult(
    string Operation,
    string MessageId,
    string CorrelationId,
    string Tenant,
    string AggregateId,
    string Status,
    [property: JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)] string? IdempotencyKey = null,
    [property: JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)] JsonElement? Result = null);
