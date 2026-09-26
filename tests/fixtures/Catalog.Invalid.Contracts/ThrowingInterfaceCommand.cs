using System.Text.Json.Serialization;
using Hexalith.EventStore.Contracts.Commands;
using Hexalith.McpCli.Abstractions;

namespace Catalog.Invalid.Contracts;

/// <summary>Exercises a contract interface whose static routing member throws.</summary>
/// <param name="ItemId">The aggregate identifier.</param>
[HexalithCommand("Throwing interface command.")]
public sealed record ThrowingInterfaceCommand(string ItemId) : ICommandContract
{
    /// <summary>Gets the interface command type.</summary>
    public static string CommandType => "throwing-interface";

    /// <summary>Gets the interface domain, which cannot be read.</summary>
    public static string Domain => throw new InvalidOperationException("Domain is unavailable.");

    /// <summary>Gets the aggregate identifier.</summary>
    [JsonIgnore]
    public string AggregateId => ItemId;
}
