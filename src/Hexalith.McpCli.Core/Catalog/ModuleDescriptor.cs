using System.Text.Json;
using System.Text.Json.Serialization;
using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Core.Catalog;

/// <summary>One immutable discoverable Contracts module.</summary>
public sealed class ModuleDescriptor
{
    internal ModuleDescriptor(string name, string description, IdentifierKind identifierKind, string? fixedTenant,
        WireTypeConvention wireTypeConvention, JsonSerializerOptions modulePayloadOptions, IReadOnlyList<OperationDescriptor> operations)
    {
        Name = name;
        Description = description;
        IdentifierKind = identifierKind;
        FixedTenant = fixedTenant;
        WireTypeConvention = wireTypeConvention;
        ModulePayloadOptions = modulePayloadOptions;
        Operations = Array.AsReadOnly(operations.ToArray());
    }

    /// <summary>Gets the canonical module name.</summary>
    public string Name { get; }

    /// <summary>Gets the module description.</summary>
    public string Description { get; }

    /// <summary>Gets the declared identifier kind.</summary>
    public IdentifierKind IdentifierKind { get; }

    /// <summary>Gets the fixed tenant, if any.</summary>
    public string? FixedTenant { get; }

    /// <summary>Gets the wire type fallback convention.</summary>
    public WireTypeConvention WireTypeConvention { get; }

    /// <summary>Gets the cached, read-only payload serializer options.</summary>
    [JsonIgnore]
    public JsonSerializerOptions ModulePayloadOptions { get; }

    /// <summary>Gets operations in ordinal canonical-name order.</summary>
    public IReadOnlyList<OperationDescriptor> Operations { get; }
}
