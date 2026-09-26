using Hexalith.McpCli.Abstractions;

namespace Catalog.Routing.Contracts;

/// <summary>Exercises a colon, which the Gateway permits in a command wire type.</summary>
/// <param name="ItemId">The aggregate identifier.</param>
[HexalithCommand("Command with a colon in its wire type.", Domain = "routing", WireType = "items:colon",
    AggregateIdProperty = nameof(ItemId))]
public sealed record ColonWireCommand([property: HexalithIdentifier] string ItemId);
