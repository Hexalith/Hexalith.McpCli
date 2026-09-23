using System.ComponentModel;
using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Sample.Contracts;

/// <summary>
/// Renames a synthetic item using attribute-supplied gateway routing.
/// </summary>
/// <param name="ItemId">The item to rename.</param>
/// <param name="Title">The replacement title.</param>
[HexalithCommand(
    "Rename a synthetic item in the sample module.",
    Domain = "sample",
    AggregateIdProperty = nameof(ItemId))]
public sealed record RenameItemCommand(
    [property: HexalithIdentifier]
    [property: Description("The ULID of the item to rename.")]
    SampleItemId ItemId,
    [property: Description("The replacement title.")]
    string Title);
