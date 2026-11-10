namespace Hexalith.McpCli.Abstractions;

/// <summary>
/// Declares an agent-facing gateway command on a Contracts class or record.
/// Decorating a type is the owning maintainer's consent to expose it to agents and operators through the Gateway
/// without human confirmation; never decorate UI-only or confirmation-required operations.
/// The Gateway still authorizes every call.
/// </summary>
/// <param name="description">What the command does for a reader unfamiliar with the source.</param>
[AttributeUsage(AttributeTargets.Class, AllowMultiple = false, Inherited = false)]
public sealed class HexalithCommandAttribute(string description) : Attribute
{
    /// <summary>Gets the required command description.</summary>
    public string Description { get; } = description;

    /// <summary>Gets or sets a validating JSON payload example.</summary>
    public string? Example { get; set; }

    /// <summary>Gets or sets the ASCII lowercase kebab-case operation name part, overriding the name derived from the type name.</summary>
    public string? Name { get; set; }

    /// <summary>Gets or sets the exact cataloged platform request scope for this operation.</summary>
    /// <remarks>Use <c>platform:</c> followed by lowercase ASCII letters, digits, and single hyphens,
    /// starting and ending with a letter or digit. Cannot coexist with <see cref="HexalithModuleAttribute.FixedTenant"/>.
    /// The declared scope overrides the session tenant; a per-call tenant must be omitted or match exactly.
    /// A mapped tenant payload property is filled from this scope and must agree when supplied.</remarks>
    public string? PlatformScope { get; set; }

    /// <summary>Gets or sets the gateway domain when no contract interface supplies it.</summary>
    public string? Domain { get; set; }

    /// <summary>Gets or sets the gateway wire type when no contract interface supplies it.</summary>
    public string? WireType { get; set; }

    /// <summary>Gets or sets the exact CLR property containing the aggregate identifier.</summary>
    public string? AggregateIdProperty { get; set; }

    /// <summary>Gets or sets the exact CLR property filled from the envelope tenant.</summary>
    public string? TenantProperty { get; set; }

    /// <summary>Gets or sets the exact CLR property filled from the resolved correlation identifier.</summary>
    public string? CorrelationProperty { get; set; }

    /// <summary>Gets or sets the exact CLR property filled from the envelope idempotency key.</summary>
    public string? IdempotencyKeyProperty { get; set; }

    /// <summary>Gets or sets the exact CLR property filled from the operator's actor.</summary>
    public string? ActorProperty { get; set; }
}
