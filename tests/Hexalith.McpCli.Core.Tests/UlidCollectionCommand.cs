using ByteAether.Ulid;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Holds CLR ULID values inside collections and dictionaries.</summary>
public sealed class UlidCollectionCommand
{
    /// <summary>Gets or sets a list of ULIDs.</summary>
    public List<Ulid> Ids { get; init; } = [];

    /// <summary>Gets or sets ULIDs by name.</summary>
    public Dictionary<string, Ulid> ByName { get; init; } = [];

    /// <summary>Gets or sets an array of nullable ULIDs.</summary>
    public Ulid?[] Optional { get; init; } = [];
}
