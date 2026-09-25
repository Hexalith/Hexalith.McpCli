using System.ComponentModel;
using System.Text.Json.Serialization;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Exercises the JSON contract shapes used by command payloads.</summary>
/// <param name="Name">The constructor-bound name.</param>
/// <param name="Nested">The nested object.</param>
/// <param name="Items">A collection of nested objects.</param>
public sealed record MixedCommand(
    [property: Description("The constructor-bound name.")] string Name,
    [property: Description("The nested object.")] NestedValue Nested,
    [property: Description("The nested collection.")] List<NestedValue> Items)
{
    /// <summary>Gets an explicitly required member.</summary>
    public required string Required { get; init; }

    /// <summary>Gets an optional nullable member.</summary>
    public string? Optional { get; init; }

    /// <summary>Gets an enum value.</summary>
    public StatusValue Mode { get; init; }

    /// <summary>Gets the envelope tenant with an escaped JSON name.</summary>
    [JsonPropertyName("tenant/~")]
    public required string Tenant { get; init; }

    /// <summary>Gets the resolved correlation identifier.</summary>
    public string? Correlation { get; init; }

    /// <summary>Gets the caller-supplied idempotency key.</summary>
    public string? IdempotencyKey { get; init; }

    /// <summary>Gets the operator actor.</summary>
    public string? Actor { get; init; }

    /// <summary>Gets an ordinary tenant-like payload member.</summary>
    public string TenantId { get; init; } = string.Empty;

    /// <summary>Gets a computed value that cannot be supplied as input.</summary>
    public string Derived => Name.ToUpperInvariant();
}
