using System.Text.Json.Serialization;
using Hexalith.EventStore.Contracts.Commands;
using Hexalith.McpCli.Abstractions;

namespace Catalog.Routing.Contracts;

/// <summary>Exercises an attribute domain that repeats the interface value.</summary>
/// <param name="ItemId">The aggregate identifier.</param>
[HexalithCommand("Command whose attribute repeats its interface domain.", Domain = "routing")]
public sealed record RedundantInterfaceCommand(string ItemId) : ICommandContract
{
    /// <summary>Gets the interface command type.</summary>
    public static string CommandType => "redundant-interface-wire";

    /// <summary>Gets the interface domain.</summary>
    public static string Domain => "routing";

    /// <summary>Gets the computed aggregate identifier.</summary>
    [JsonIgnore]
    public string AggregateId => ItemId;
}
