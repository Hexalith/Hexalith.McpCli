using System.Collections.Frozen;
using System.Collections.ObjectModel;
using Hexalith.McpCli.Core.Execution;

namespace Hexalith.McpCli.Core.Settings;

/// <summary>Resolves one settings snapshot from explicit options, environment, and one profile read.</summary>
public sealed class SettingsResolver(ProfileStore store, IReadOnlyDictionary<string, string?> environment)
{
    /// <summary>Resolves settings without requiring a gateway URL for discovery.</summary>
    /// <param name="input">Explicit global options.</param>
    /// <returns>The immutable settings or a source-specific configuration error.</returns>
    public SettingsResolution Resolve(SettingsInput input)
    {
        ArgumentNullException.ThrowIfNull(input);
        try
        {
            ProfileSnapshot snapshot = store.Read();
            var sources = new Dictionary<string, string>(StringComparer.Ordinal);
            string? profileName = Select(input.Profile, "EVENTSTORE_PROFILE", null, null, "profile", sources);
            ConnectionProfile? profile = null;
            if (profileName is null)
            {
                profileName = snapshot.ActiveProfile;
                sources["profile"] = profileName is null ? "default" : "activeProfile";
            }

            if (profileName is not null && !snapshot.Profiles.TryGetValue(profileName, out profile))
            {
                return Failure("The selected mcpcli profile does not exist.");
            }

            string? urlText = Select(input.Url, "EVENTSTORE_URL", profile?.Url, null, "url", sources);
            Uri? url = null;
            if (urlText is not null && (!Uri.TryCreate(urlText, UriKind.Absolute, out url)
                || url.Scheme is not ("http" or "https") || url.UserInfo.Length > 0
                || url.Query.Length > 0 || url.Fragment.Length > 0))
            {
                return Failure($"Invalid gateway URL from {sources["url"]}.");
            }

            string? token = Select(input.Token, "EVENTSTORE_TOKEN", profile?.Token, null, "token", sources);
            string? tenant = Select(input.Tenant, "EVENTSTORE_TENANT", profile?.Tenant, null, "tenant", sources);
            string? actor = Select(input.Actor, "EVENTSTORE_ACTOR", profile?.Actor, null, "actor", sources);
            string format = Select(input.Format, "EVENTSTORE_FORMAT", profile?.Format, "json", "format", sources)!;
            if (format is not ("json" or "table"))
            {
                return Failure($"Invalid format from {sources["format"]}; expected json or table.");
            }

            if (token is not null && string.IsNullOrWhiteSpace(token)
                || tenant is not null && string.IsNullOrWhiteSpace(tenant)
                || actor is not null && string.IsNullOrWhiteSpace(actor))
            {
                return Failure("A configured token, tenant, or actor is blank.");
            }

            bool? allowOverride = SelectBoolean(input.AllowTenantOverride, "EVENTSTORE_ALLOW_TENANT_OVERRIDE",
                profile?.AllowTenantOverride, "allowTenantOverride", sources);
            bool? readOnly = SelectBoolean(input.ReadOnly, "EVENTSTORE_READ_ONLY", null, "readOnly", sources);
            bool? strict = SelectBoolean(input.Strict, "EVENTSTORE_STRICT", null, "strict", sources);
            string? output = input.Output;
            sources["output"] = output is null ? "default" : "flag";

            var allowed = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach (string extension in profile?.AllowedExtensions ?? [])
            {
                if (extension is null || !allowed.Add(extension))
                {
                    return Failure("The selected profile contains a duplicate or null allowed extension key.");
                }
            }

            if (ExtensionValidator.Validate(allowed.ToDictionary(key => key, _ => string.Empty, StringComparer.Ordinal), allowed).Count > 0)
            {
                return Failure("The selected profile contains an invalid allowed extension key.");
            }

            sources["allowedExtensions"] = profile is null ? "default" : "profile";
            var settings = new ResolvedSettings(url, token, tenant, actor, allowOverride ?? false,
                allowed.ToFrozenSet(StringComparer.OrdinalIgnoreCase), format, output, readOnly ?? false,
                strict ?? false, profileName, new ReadOnlyDictionary<string, string>(sources));
            return new SettingsResolution(settings, null);
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException or InvalidDataException
            or System.Text.Json.JsonException or FormatException)
        {
            return Failure("Invalid mcpcli profile or environment setting: " + exception.Message);
        }
    }

    private string? Select(string? flag, string environmentName, string? profile, string? fallback,
        string field, Dictionary<string, string> sources)
    {
        if (flag is not null)
        {
            sources[field] = "flag";
            return flag;
        }

        if (environment.TryGetValue(environmentName, out string? value) && value is not null)
        {
            sources[field] = environmentName;
            return value;
        }

        sources[field] = profile is null ? "default" : "profile";
        return profile ?? fallback;
    }

    private bool? SelectBoolean(bool? flag, string environmentName, bool? profile,
        string field, Dictionary<string, string> sources)
    {
        if (flag is not null)
        {
            sources[field] = "flag";
            return flag;
        }

        if (environment.TryGetValue(environmentName, out string? raw) && raw is not null)
        {
            sources[field] = environmentName;
            bool parsed;
            if (raw == "1")
            {
                parsed = true;
            }
            else if (raw == "0")
            {
                parsed = false;
            }
            else if (!bool.TryParse(raw, out parsed))
            {
                throw new FormatException($"{environmentName} must be true, false, 1, or 0.");
            }

            return parsed;
        }

        sources[field] = profile is null ? "default" : "profile";
        return profile;
    }

    private static SettingsResolution Failure(string message)
        => new(null, new OperationError("configuration_invalid", Message: message));
}
