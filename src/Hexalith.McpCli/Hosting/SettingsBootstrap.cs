using Hexalith.McpCli.Core.Settings;

namespace Hexalith.McpCli.Hosting;

/// <summary>Captures process environment once and resolves the immutable settings used to build a host.</summary>
/// <param name="profileStore">The private mcpcli profile store.</param>
/// <param name="readEnvironment">The environment reader, or the process environment by default.</param>
internal sealed class SettingsBootstrap(ProfileStore profileStore, Func<string, string?>? readEnvironment = null)
{
    private static readonly string[] EnvironmentNames =
    [
        "EVENTSTORE_PROFILE",
        "EVENTSTORE_URL",
        "EVENTSTORE_TOKEN",
        "EVENTSTORE_TENANT",
        "EVENTSTORE_ACTOR",
        "EVENTSTORE_ALLOW_TENANT_OVERRIDE",
        "EVENTSTORE_FORMAT",
        "EVENTSTORE_READ_ONLY",
        "EVENTSTORE_STRICT",
    ];

    private readonly Func<string, string?> _readEnvironment = readEnvironment ?? Environment.GetEnvironmentVariable;

    /// <summary>Resolves one snapshot before any host or Catalog service is constructed.</summary>
    /// <param name="input">The explicit command-line settings.</param>
    /// <returns>The resolved settings or their canonical configuration error.</returns>
    internal SettingsResolution Resolve(SettingsInput input)
        => new SettingsResolver(profileStore, CaptureEnvironment()).Resolve(input);

    /// <summary>
    /// Resolves presentation settings for profile-management verbs without selecting a profile or reading the store.
    /// </summary>
    /// <remarks>
    /// The <c>--profile</c> flag and <c>EVENTSTORE_PROFILE</c> are ignored so a missing selection cannot block the verb
    /// that repairs it; every other flag and environment value is still validated against an empty snapshot.
    /// </remarks>
    /// <param name="input">The explicit command-line settings.</param>
    /// <returns>The resolved settings or their canonical configuration error.</returns>
    internal SettingsResolution ResolvePresentation(SettingsInput input)
    {
        ArgumentNullException.ThrowIfNull(input);
        Dictionary<string, string?> environment = CaptureEnvironment();
        _ = environment.Remove("EVENTSTORE_PROFILE");
        return new SettingsResolver(EmptySnapshot, environment).Resolve(input with { Profile = null });
    }

    private static ProfileSnapshot EmptySnapshot()
        => new(1, null, new Dictionary<string, ConnectionProfile>(StringComparer.Ordinal));

    private Dictionary<string, string?> CaptureEnvironment()
    {
        var environment = new Dictionary<string, string?>(StringComparer.Ordinal);
        foreach (string name in EnvironmentNames)
        {
            environment[name] = _readEnvironment(name);
        }

        return environment;
    }
}
