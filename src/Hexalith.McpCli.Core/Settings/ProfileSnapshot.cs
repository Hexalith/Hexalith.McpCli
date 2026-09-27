namespace Hexalith.McpCli.Core.Settings;

/// <summary>The versioned profile document in this tool's own settings file.</summary>
/// <param name="Version">The profile schema version.</param>
/// <param name="ActiveProfile">The selected profile name.</param>
/// <param name="Profiles">Named connection profiles.</param>
public sealed record ProfileSnapshot(
    int Version,
    string? ActiveProfile,
    IReadOnlyDictionary<string, ConnectionProfile> Profiles);
