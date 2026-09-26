using System.Text.Json;
using Hexalith.EventStore.Contracts.Commands;
using Hexalith.McpCli.Core.Schema;

namespace Hexalith.McpCli.Core.Catalog;

/// <summary>Compiles readers of finally validated, rebuilt payloads.</summary>
internal static class AggregateIdAccessors
{
    internal static Func<JsonElement, string?>? Create(Type contractType, JsonSerializerOptions options,
        IReadOnlyDictionary<PropertyRole, PropertyBinding> bindings, OperationKind kind)
    {
        if (bindings.TryGetValue(PropertyRole.AggregateId, out PropertyBinding? binding))
        {
            string serializedName = binding.SerializedName;
            return payload => payload.ValueKind == JsonValueKind.Object
                && payload.TryGetProperty(serializedName, out JsonElement value)
                && value.ValueKind == JsonValueKind.String ? value.GetString() : null;
        }

        if (kind == OperationKind.Command && typeof(ICommandContract).IsAssignableFrom(contractType))
        {
            return payload => (JsonSerializer.Deserialize(payload, contractType, options) as ICommandContract)?.AggregateId;
        }

        return null;
    }
}
