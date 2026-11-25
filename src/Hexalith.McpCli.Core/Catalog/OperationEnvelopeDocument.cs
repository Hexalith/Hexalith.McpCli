using System.Text.Json.Serialization;
using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Core.Catalog;

/// <summary>Describes envelope arguments available to an operation.</summary>
/// <param name="FixedTenant">The module tenant, when fixed.</param>
/// <param name="AggregateIdRequired">Whether the caller must supply an aggregate identifier.</param>
/// <param name="IdempotencyKeyRequired">Whether the caller must supply an idempotency key.</param>
/// <param name="Arguments">The applicable envelope argument names.</param>
/// <param name="IdentifierKind">The module's declared aggregate and marked identifier kind.</param>
/// <param name="PlatformScope">The operation's exact declared platform request scope, when any.</param>
public sealed record OperationEnvelopeDocument(
    [property: JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)] string? FixedTenant,
    bool AggregateIdRequired,
    bool IdempotencyKeyRequired,
    IReadOnlyList<string> Arguments,
    IdentifierKind IdentifierKind,
    [property: JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)] string? PlatformScope = null);
