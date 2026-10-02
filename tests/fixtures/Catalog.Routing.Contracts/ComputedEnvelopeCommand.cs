using System.Text.Json.Serialization;
using Hexalith.EventStore.Contracts.Commands;
using Hexalith.McpCli.Abstractions;

namespace Catalog.Routing.Contracts;

/// <summary>Exercises aggregate access after trusted envelope members have been filled.</summary>
/// <param name="ItemId">The aggregate identifier returned by the computed accessor.</param>
/// <param name="Tenant">The resolved tenant.</param>
/// <param name="Actor">The trusted actor.</param>
/// <param name="Correlation">The resolved correlation identifier.</param>
/// <param name="Idempotency">The optional caller-supplied idempotency identifier.</param>
/// <param name="Details">An optional nested value.</param>
[HexalithCommand("Command with a computed aggregate identifier and envelope members.",
    TenantProperty = nameof(Tenant), ActorProperty = nameof(Actor), CorrelationProperty = nameof(Correlation),
    IdempotencyKeyProperty = nameof(Idempotency))]
public sealed record ComputedEnvelopeCommand(
    string ItemId,
    [property: JsonRequired] string? Tenant = null,
    [property: JsonRequired] string? Actor = null,
    [property: JsonRequired] string? Correlation = null,
    string? Idempotency = null,
    ComputedEnvelopeDetails? Details = null) : ICommandContract
{
    /// <summary>Gets the gateway command type.</summary>
    public static string CommandType => "computed-envelope";

    /// <summary>Gets the gateway domain.</summary>
    public static string Domain => "routing";

    /// <summary>Gets the aggregate identifier only after the trusted envelope is complete.</summary>
    [JsonIgnore]
    public string AggregateId => Tenant is not null && Actor is not null && Correlation is not null
        ? ItemId
        : throw new InvalidOperationException("The trusted envelope is incomplete.");
}
