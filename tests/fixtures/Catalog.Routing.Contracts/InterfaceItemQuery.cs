using Hexalith.EventStore.Contracts.Queries;
using Hexalith.McpCli.Abstractions;

namespace Catalog.Routing.Contracts;

/// <summary>Exercises interface routing precedence over conflicting attribute values.</summary>
/// <param name="ItemId">The item identifier.</param>
[HexalithQuery("Read an item through the query interface.", Domain = "wrong", WireType = "wrong",
    ProjectionType = "wrong", ProjectionActorType = "RoutingProjectionActor", AggregateIdProperty = nameof(ItemId))]
public sealed record InterfaceItemQuery([property: HexalithIdentifier] string ItemId) : IQueryContract
{
    /// <summary>Gets the interface query type.</summary>
    public static string QueryType => "interface-item-wire";

    /// <summary>Gets the interface domain.</summary>
    public static string Domain => "routing";

    /// <summary>Gets the interface projection type.</summary>
    public static string ProjectionType => "routing-items";
}
