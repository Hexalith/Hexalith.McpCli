using System.ComponentModel;
using System.Text.Json.Serialization;
using Hexalith.EventStore.Contracts.Commands;
using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Sample.Contracts;

/// <summary>
/// Creates a synthetic item using interface-supplied gateway routing.
/// </summary>
/// <param name="ItemId">The new item's aggregate identifier.</param>
/// <param name="Title">A title for the new item.</param>
[HexalithCommand("Create a synthetic item in the sample module.")]
public sealed record CreateItemCommand(
    [property: HexalithIdentifier]
    [property: Description("The ULID of the new item.")]
    SampleItemId ItemId,
    [property: Description("The title shown for the item.")]
    string Title) : ICommandContract
{
    /// <summary>Gets the gateway's command type.</summary>
    public static string CommandType => "create-item";

    /// <summary>Gets the gateway's domain.</summary>
    public static string Domain => "sample";

    /// <summary>Gets the aggregate identifier through the contract interface.</summary>
    [JsonIgnore]
    public string AggregateId => ItemId.Value;
}
