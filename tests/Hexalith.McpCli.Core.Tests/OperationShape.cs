using Hexalith.McpCli.Core.Catalog;
using DeclaredIdentifierKind = Hexalith.McpCli.Abstractions.IdentifierKind;
using DeclaredWireTypeConvention = Hexalith.McpCli.Abstractions.WireTypeConvention;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>
/// The module-scoped Operation Shape: the routing and envelope fields that McpCli's generic translation branches on.
/// Payload role bindings and envelope-filled members are not components; Core executor tests cover them. This is the single
/// source of shape derivation.
/// </summary>
/// <param name="Kind">The operation kind: <c>command</c> or <c>query</c>.</param>
/// <param name="IdentifierKind">The module Identifier Kind: <c>ulid</c> or <c>string</c>.</param>
/// <param name="WireTypeConvention">The module Wire Type convention: <c>explicit</c>, <c>fullTypeName</c> or <c>kebabCase</c>.</param>
/// <param name="TenantSource">The tenant source: <c>platformScope</c>, <c>fixedTenant</c> or <c>public</c>.</param>
/// <param name="AggregateIdSource">The aggregate-identifier source: <c>property</c>, <c>constant</c> or <c>none</c>.</param>
/// <param name="ProjectionSelector">The query projection selector: <c>projectionActorType</c>, <c>projectionType</c> or <c>none</c>.</param>
/// <param name="IdempotencyKey">Whether a caller idempotency key is <c>required</c> or <c>optional</c>.</param>
internal sealed record OperationShape(
    string Kind,
    string IdentifierKind,
    string WireTypeConvention,
    string TenantSource,
    string AggregateIdSource,
    string ProjectionSelector,
    string IdempotencyKey)
{
    /// <summary>Gets the stable, opaque shape key; consumers outside this type compare it only as a string.</summary>
    internal string Key => string.Join(';',
        "kind=" + Kind,
        "identifierKind=" + IdentifierKind,
        "wireTypeConvention=" + WireTypeConvention,
        "tenantSource=" + TenantSource,
        "aggregateIdSource=" + AggregateIdSource,
        "projectionSelector=" + ProjectionSelector,
        "idempotencyKey=" + IdempotencyKey);

    /// <summary>Derives an operation's shape from its Catalog descriptors only.</summary>
    /// <param name="module">The module that declares the operation.</param>
    /// <param name="operation">The cataloged operation.</param>
    /// <returns>The derived shape.</returns>
    internal static OperationShape From(ModuleDescriptor module, OperationDescriptor operation)
    {
        ArgumentNullException.ThrowIfNull(module);
        ArgumentNullException.ThrowIfNull(operation);
        return new(
            operation.Kind switch
            {
                OperationKind.Command => "command",
                OperationKind.Query => "query",
                _ => throw new ArgumentOutOfRangeException(nameof(operation), operation.Kind, "Unknown operation kind."),
            },
            module.IdentifierKind switch
            {
                DeclaredIdentifierKind.Ulid => "ulid",
                DeclaredIdentifierKind.String => "string",
                _ => throw new ArgumentOutOfRangeException(nameof(module), module.IdentifierKind, "Unknown Identifier Kind."),
            },
            module.WireTypeConvention switch
            {
                DeclaredWireTypeConvention.Explicit => "explicit",
                DeclaredWireTypeConvention.FullTypeName => "fullTypeName",
                DeclaredWireTypeConvention.KebabCase => "kebabCase",
                _ => throw new ArgumentOutOfRangeException(nameof(module), module.WireTypeConvention, "Unknown Wire Type convention."),
            },
            operation.PlatformScope is not null ? "platformScope" : module.FixedTenant is not null ? "fixedTenant" : "public",
            operation.AggregateIdAccessor is not null ? "property" : operation.AggregateIdConstant is not null ? "constant" : "none",
            operation.Routing.ProjectionActorType is not null ? "projectionActorType"
                : operation.Routing.ProjectionType is not null ? "projectionType" : "none",
            operation.IdempotencyKeyRequired ? "required" : "optional");
    }
}
