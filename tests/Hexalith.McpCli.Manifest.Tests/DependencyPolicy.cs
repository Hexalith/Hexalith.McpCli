using System.Text.Json;

namespace Hexalith.McpCli.Manifest.Tests;

/// <summary>The reviewed production pins and test-only dependency allowances.</summary>
internal sealed record DependencyPolicy
{
    /// <summary>Gets the policy format version.</summary>
    public int SchemaVersion { get; init; } = 1;

    /// <summary>Gets the allowed non-module production roots.</summary>
    public HashSet<string> DirectPackages { get; init; } = new(StringComparer.OrdinalIgnoreCase);

    /// <summary>Gets the exact non-module package closure.</summary>
    public Dictionary<string, string> BaselinePackages { get; init; } = new(StringComparer.OrdinalIgnoreCase);

    /// <summary>Gets the decoration package identity and pin.</summary>
    public KeyValuePair<string, string> DecorationPackage { get; init; } = new("Hexalith.McpCli.Abstractions", "1.0.0");

    /// <summary>Gets the enrolled module pins.</summary>
    public Dictionary<string, string> Modules { get; init; } = new(StringComparer.OrdinalIgnoreCase);

    /// <summary>Gets packages allowed only as test roots.</summary>
    public HashSet<string> TestPackages { get; init; } = new(StringComparer.OrdinalIgnoreCase);

    /// <summary>Gets the synthetic Contracts fixture identity.</summary>
    public string SampleContracts { get; init; } = "Hexalith.McpCli.Sample.Contracts";

    /// <summary>Reads the version-one policy without depending on a package cache.</summary>
    public static DependencyPolicy Load(string path)
    {
        using JsonDocument document = JsonDocument.Parse(File.ReadAllText(path));
        JsonElement policy = document.RootElement;
        JsonElement decoration = policy.GetProperty("decorationPackage");
        return new DependencyPolicy
        {
            SchemaVersion = policy.GetProperty("schemaVersion").GetInt32(),
            DirectPackages = ReadNames(policy.GetProperty("directPackages")),
            BaselinePackages = ReadVersions(policy.GetProperty("baselinePackages")),
            DecorationPackage = new(decoration.GetProperty("id").GetString()!, decoration.GetProperty("version").GetString()!),
            Modules = ReadVersions(policy.GetProperty("modules")),
            TestPackages = ReadNames(policy.GetProperty("testPackages")),
            SampleContracts = policy.GetProperty("sampleContracts").GetString()!,
        };
    }

    private static HashSet<string> ReadNames(JsonElement array)
        => array.EnumerateArray().Select(item => item.GetString()!).ToHashSet(StringComparer.OrdinalIgnoreCase);

    private static Dictionary<string, string> ReadVersions(JsonElement map)
        => map.EnumerateObject().ToDictionary(item => item.Name, item => item.Value.GetString()!, StringComparer.OrdinalIgnoreCase);
}
