using System.Collections.ObjectModel;
using System.Text.Json.Nodes;
using Json.Schema;

namespace Hexalith.McpCli.Core.Schema;

/// <summary>Holds one exported schema, its validator, and resolved property roles.</summary>
public sealed class DerivedSchema
{
    private readonly JsonNode _node;

    /// <summary>Initializes an operation schema snapshot.</summary>
    /// <param name="node">The exported schema document.</param>
    /// <param name="bindings">Resolved operation property roles.</param>
    internal DerivedSchema(JsonNode node, IReadOnlyDictionary<PropertyRole, PropertyBinding> bindings)
    {
        ArgumentNullException.ThrowIfNull(node);
        ArgumentNullException.ThrowIfNull(bindings);
        _node = node.DeepClone();
        Validator = JsonSchema.FromText(_node.ToJsonString());
        Bindings = new ReadOnlyDictionary<PropertyRole, PropertyBinding>(new Dictionary<PropertyRole, PropertyBinding>(bindings));
    }

    /// <summary>Gets a copy of the exported schema document.</summary>
    public JsonNode Node => _node.DeepClone();

    /// <summary>Gets the validator built from the same schema document.</summary>
    public JsonSchema Validator { get; }

    /// <summary>Gets the resolved property roles.</summary>
    public IReadOnlyDictionary<PropertyRole, PropertyBinding> Bindings { get; }
}
