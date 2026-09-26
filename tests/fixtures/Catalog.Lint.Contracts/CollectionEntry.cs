using System.ComponentModel;
using Hexalith.McpCli.Abstractions;

namespace Catalog.Lint.Contracts;

/// <summary>Provides a collection element with described and undescribed members.</summary>
/// <param name="Count">An undescribed element count.</param>
/// <param name="MarkedId">A marked identifier-like member.</param>
public sealed record CollectionEntry(
    [property: Description("   ")] int Count,
    [property: HexalithIdentifier]
    [property: Description("The marked entry identifier.")] string MarkedId);
