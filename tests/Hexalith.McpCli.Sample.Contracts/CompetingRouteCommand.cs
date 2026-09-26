using System.Text.Json.Serialization;
using Hexalith.EventStore.Contracts.Commands;
using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Sample.Contracts;

/// <summary>Exercises command interface routing precedence over conflicting attributes.</summary>
/// <param name="ItemId">The aggregate identifier.</param>
[HexalithCommand("Command with competing route values.", Domain = "attribute-domain", WireType = "attribute-wire")]
public sealed record CompetingRouteCommand(string ItemId) : ICommandContract
{
    /// <summary>Gets the interface command type.</summary>
    public static string CommandType => "interface-wire";

    /// <summary>Gets the interface domain.</summary>
    public static string Domain => "sample";

    /// <summary>Gets the computed aggregate identifier.</summary>
    [JsonIgnore]
    public string AggregateId => ItemId;
}
