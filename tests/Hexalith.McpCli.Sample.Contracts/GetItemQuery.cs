using System.ComponentModel;
using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Sample.Contracts;

/// <summary>
/// Reads a synthetic item through an attribute-routed projection query.
/// </summary>
/// <param name="ItemId">The item to read.</param>
[HexalithQuery(
    "Read one synthetic item from the sample projection.",
    Domain = "sample",
    AggregateIdProperty = nameof(ItemId),
    ProjectionType = "sample-items")]
public sealed record GetItemQuery(
    [property: HexalithIdentifier]
    [property: Description("The ULID of the item to read.")]
    SampleItemId ItemId);
