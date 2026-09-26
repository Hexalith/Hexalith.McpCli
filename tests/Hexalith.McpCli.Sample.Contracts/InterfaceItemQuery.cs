using Hexalith.EventStore.Contracts.Queries;
using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Sample.Contracts;

/// <summary>Exercises interface routing precedence over conflicting attribute values.</summary>
/// <param name="ItemId">The item identifier.</param>
[HexalithQuery("Read an item through the query interface.", Domain = "wrong", WireType = "wrong",
    ProjectionType = "wrong", ProjectionActorType = "SampleProjectionActor", AggregateIdProperty = nameof(ItemId))]
public sealed record InterfaceItemQuery([property: HexalithIdentifier] SampleItemId ItemId) : IQueryContract
{
    /// <summary>Gets the interface query type.</summary>
    public static string QueryType => "interface-item-wire";

    /// <summary>Gets the interface domain.</summary>
    public static string Domain => "sample";

    /// <summary>Gets the interface projection type.</summary>
    public static string ProjectionType => "sample-items";
}
