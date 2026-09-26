using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;
using Hexalith.McpCli.Core.Schema;

namespace Hexalith.McpCli.Core.Catalog;

/// <summary>One resolved operation ready for discovery and execution.</summary>
public sealed class OperationDescriptor
{
    internal OperationDescriptor(string name, OperationKind kind, string description, string? example, DerivedSchema schema,
        OperationRouting routing, Func<JsonElement, string?>? aggregateIdAccessor, string? aggregateIdConstant,
        bool aggregateIdRequired, bool idempotencyKeyRequired, Type contractType)
    {
        Name = name;
        Kind = kind;
        Description = description;
        Example = example;
        Schema = schema;
        Routing = routing;
        AggregateIdAccessor = aggregateIdAccessor;
        AggregateIdConstant = aggregateIdConstant;
        AggregateIdRequired = aggregateIdRequired;
        IdempotencyKeyRequired = idempotencyKeyRequired;
        PropertyBindings = schema.Bindings;
        EnvelopeFilledProperties = Array.AsReadOnly(schema.Bindings.Values
            .Where(binding => binding.Role != PropertyRole.AggregateId)
            .Select(binding => binding.SerializedName).OrderBy(name => name, StringComparer.Ordinal).ToArray());
        ContractType = contractType;
    }

    /// <summary>Gets the canonical module-qualified operation name.</summary>
    public string Name { get; }

    /// <summary>Gets whether the operation is a command or query.</summary>
    public OperationKind Kind { get; }

    /// <summary>Gets the description supplied by the declaration.</summary>
    public string Description { get; }

    /// <summary>Gets the validated sample payload, when declared.</summary>
    public string? Example { get; }

    /// <summary>Gets the reusable derived payload schema and validator.</summary>
    [JsonIgnore]
    public DerivedSchema Schema { get; }

    /// <summary>Gets a defensive copy of the schema document for result serialization.</summary>
    public JsonNode SchemaDocument => Schema.Node;

    /// <summary>Gets the resolved gateway routing fields.</summary>
    public OperationRouting Routing { get; }

    /// <summary>Gets the compiled aggregate identifier reader, when the payload supplies one.</summary>
    [JsonIgnore]
    public Func<JsonElement, string?>? AggregateIdAccessor { get; }

    /// <summary>Gets the query's declared aggregate identifier constant, if any.</summary>
    public string? AggregateIdConstant { get; }

    /// <summary>Gets whether a query needs an explicit aggregate identifier.</summary>
    public bool AggregateIdRequired { get; }

    /// <summary>Gets whether omission of a caller-supplied idempotency key is invalid.</summary>
    public bool IdempotencyKeyRequired { get; }

    /// <summary>Gets serialized members filled from the envelope.</summary>
    public IReadOnlyList<string> EnvelopeFilledProperties { get; }

    /// <summary>Gets exact role-to-serialized-member mappings.</summary>
    [JsonIgnore]
    public IReadOnlyDictionary<PropertyRole, PropertyBinding> PropertyBindings { get; }

    /// <summary>Gets the declared Contracts payload type.</summary>
    [JsonIgnore]
    public Type ContractType { get; }
}
