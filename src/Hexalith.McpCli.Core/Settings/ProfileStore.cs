using System.Globalization;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Core.Execution;

namespace Hexalith.McpCli.Core.Settings;

/// <summary>Owns this tool's versioned profile file without accessing the admin CLI's store.</summary>
public sealed partial class ProfileStore
{
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web)
    {
        PropertyNameCaseInsensitive = false,
        UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    };

    private readonly Lazy<string> _path;

    /// <summary>Initializes the store at an explicit path, MCPCLI_HOME, or the user profile.</summary>
    /// <param name="path">The optional exact profile file path.</param>
    public ProfileStore(string? path = null)
    {
        string? home = path is null ? Environment.GetEnvironmentVariable("MCPCLI_HOME") : null;
        _path = new Lazy<string>(() => ResolvePath(path, home, Environment.GetFolderPath(Environment.SpecialFolder.UserProfile)));
    }

    /// <summary>Gets the path owned by this tool.</summary>
    public string ProfilePath => _path.Value;

    /// <summary>Resolves the profile location without exposing an invalid environment value.</summary>
    internal static string ResolvePath(string? path, string? home, string userProfile)
    {
        if (path is not null)
        {
            return path;
        }

        if (home is not null)
        {
            if (string.IsNullOrWhiteSpace(home) || home.Any(char.IsControl) || !Path.IsPathFullyQualified(home))
            {
                throw new InvalidDataException("MCPCLI_HOME must be an absolute directory path.");
            }

            try
            {
                home = Path.GetFullPath(home);
                if (File.Exists(home))
                {
                    throw new InvalidDataException("MCPCLI_HOME must be an absolute directory path.");
                }
            }
            catch (ArgumentException)
            {
                throw new InvalidDataException("MCPCLI_HOME must be an absolute directory path.");
            }
        }

        return Path.Combine(home ?? userProfile, ".eventstore", "mcpcli.json");
    }

    /// <summary>Reads and validates the version-one profile document once.</summary>
    public ProfileSnapshot Read()
    {
        string directory = Path.GetDirectoryName(ProfilePath) ?? throw new InvalidDataException("The profile path has no directory.");
        if (new DirectoryInfo(directory).LinkTarget is not null)
        {
            throw new InvalidDataException("The mcpcli profile directory cannot be a symbolic link.");
        }

        RejectNonRegularPath(ProfilePath);
        if (!File.Exists(ProfilePath))
        {
            return new ProfileSnapshot(1, null, new Dictionary<string, ConnectionProfile>(StringComparer.Ordinal));
        }

        var information = new FileInfo(ProfilePath);
        if (information.Length > 1_048_576)
        {
            throw new InvalidDataException("The mcpcli profile file exceeds the size limit.");
        }

        string json = File.ReadAllText(ProfilePath);
        ProfileSnapshot snapshot = Parse(json)
            ?? throw new InvalidDataException("The mcpcli profile document is empty.");
        if (snapshot.Version != 1 || snapshot.Profiles is null)
        {
            throw new InvalidDataException("The mcpcli profile document has an unsupported version or missing profiles.");
        }

        foreach ((string name, ConnectionProfile profile) in snapshot.Profiles)
        {
            if (!ProfileNamePattern().IsMatch(name) || profile is null)
            {
                throw new InvalidDataException("The mcpcli profile document has an invalid profile entry.");
            }

            ValidateProfile(profile);
        }

        if (snapshot.ActiveProfile is not null && !snapshot.Profiles.ContainsKey(snapshot.ActiveProfile))
        {
            throw new InvalidDataException("The active mcpcli profile does not exist.");
        }

        return snapshot;
    }

    /// <summary>Adds or replaces a named profile in one locked transaction.</summary>
    public ProfileSnapshot Add(string name, ConnectionProfile profile)
        => AddWithCancellation(name, profile, CancellationToken.None);

    /// <summary>Adds a profile while observing cancellation until replacement.</summary>
    internal ProfileSnapshot AddWithCancellation(string name, ConnectionProfile profile, CancellationToken cancellationToken)
    {
        ValidateName(name);
        ValidateProfile(profile, forMutation: true);
        ValidateTenant(profile.Tenant);
        return Mutate(snapshot =>
        {
            var profiles = new Dictionary<string, ConnectionProfile>(snapshot.Profiles, StringComparer.Ordinal)
            {
                [name] = profile,
            };
            return snapshot with { Profiles = profiles };
        }, cancellationToken);
    }

    /// <summary>Removes a profile and clears its active selection.</summary>
    public ProfileSnapshot Remove(string name)
    {
        ValidateName(name);
        return Mutate(snapshot =>
        {
            var profiles = new Dictionary<string, ConnectionProfile>(snapshot.Profiles, StringComparer.Ordinal);
            if (!profiles.Remove(name))
            {
                throw new InvalidDataException("The named mcpcli profile does not exist.");
            }

            return snapshot with
            {
                Profiles = profiles,
                ActiveProfile = string.Equals(snapshot.ActiveProfile, name, StringComparison.Ordinal) ? null : snapshot.ActiveProfile,
            };
        });
    }

    /// <summary>Selects an existing profile or clears the active selection.</summary>
    public ProfileSnapshot Use(string? name)
    {
        if (name is not null)
        {
            ValidateName(name);
        }

        return Mutate(snapshot =>
        {
            if (name is not null && !snapshot.Profiles.ContainsKey(name))
            {
                throw new InvalidDataException("The named mcpcli profile does not exist.");
            }

            return snapshot with { ActiveProfile = name };
        });
    }

    /// <summary>Changes one operator setting on an existing profile.</summary>
    public ProfileSnapshot Set(string name, string field, string value)
    {
        ValidateName(name);
        ArgumentNullException.ThrowIfNull(value);
        if (field is not ("tenant" or "actor" or "allowTenantOverride" or "allowedExtensions"))
        {
            throw new InvalidDataException("Only tenant, actor, allowTenantOverride, and allowedExtensions can be set.");
        }

        return Mutate(snapshot =>
        {
            if (!snapshot.Profiles.TryGetValue(name, out ConnectionProfile? existing))
            {
                throw new InvalidDataException("The named mcpcli profile does not exist.");
            }

            ConnectionProfile updated = UpdateProfile(existing, field, value);
            var profiles = new Dictionary<string, ConnectionProfile>(snapshot.Profiles, StringComparer.Ordinal)
            {
                [name] = updated,
            };
            return snapshot with { Profiles = profiles };
        });
    }

    /// <summary>Checks an add or replace without changing the profile file.</summary>
    public void ValidateAdd(string name, ConnectionProfile profile)
        => ValidateAdd(name, profile, tokenInput: false);

    /// <summary>Checks add preconditions before reading a requested token.</summary>
    internal void ValidateAdd(string name, ConnectionProfile profile, bool tokenInput)
    {
        ValidateName(name);
        ValidateProfile(profile, forMutation: true);
        if (tokenInput && profile.Url is not null)
        {
            ValidateTokenEndpoint(new Uri(profile.Url, UriKind.Absolute));
        }

        ValidateTenant(profile.Tenant);
        _ = Read();
    }

    /// <summary>Checks that the named profile can receive a token and returns its current Gateway URL.</summary>
    internal string? ValidateRotation(string name)
    {
        ValidateName(name);
        string? url = GetProfile(Read(), name).Url;
        ValidateTokenEndpoint(url is null ? null : new Uri(url, UriKind.Absolute));
        return url;
    }

    /// <summary>Updates only the token using the latest locked profile snapshot.</summary>
    internal ProfileSnapshot RotateToken(string name, string? gatewayUrl, string token, CancellationToken cancellationToken)
    {
        ValidateName(name);
        return Mutate(snapshot =>
        {
            ConnectionProfile profile = GetProfile(snapshot, name);
            if (!string.Equals(profile.Url, gatewayUrl, StringComparison.Ordinal))
            {
                throw new InvalidDataException("The profile Gateway URL changed during token entry. Rerun token rotation.");
            }

            var profiles = new Dictionary<string, ConnectionProfile>(snapshot.Profiles, StringComparer.Ordinal)
            {
                [name] = WithToken(profile, token),
            };
            return snapshot with { Profiles = profiles };
        }, cancellationToken);
    }

    private static ConnectionProfile GetProfile(ProfileSnapshot snapshot, string name)
        => snapshot.Profiles.TryGetValue(name, out ConnectionProfile? profile)
            ? profile
            : throw new InvalidDataException("The named mcpcli profile does not exist.");

    private static ConnectionProfile WithToken(ConnectionProfile profile, string token)
    {
        ConnectionProfile updated = profile with { Token = token };
        ValidateProfile(updated, forMutation: true);
        return updated;
    }

    /// <summary>Checks a removal without changing the profile file.</summary>
    public void ValidateRemove(string name)
    {
        ValidateName(name);
        if (!Read().Profiles.ContainsKey(name))
        {
            throw new InvalidDataException("The named mcpcli profile does not exist.");
        }
    }

    /// <summary>Checks a selection or clear without changing the profile file.</summary>
    public void ValidateUse(string? name)
    {
        if (name is not null)
        {
            ValidateName(name);
        }

        if (name is not null && !Read().Profiles.ContainsKey(name))
        {
            throw new InvalidDataException("The named mcpcli profile does not exist.");
        }

        if (name is null)
        {
            _ = Read();
        }
    }

    /// <summary>Checks a profile setting and its resulting record without changing the file.</summary>
    public void ValidateSet(string name, string field, string value)
    {
        ValidateName(name);
        ArgumentNullException.ThrowIfNull(value);
        if (field is not ("tenant" or "actor" or "allowTenantOverride" or "allowedExtensions"))
        {
            throw new InvalidDataException("Only tenant, actor, allowTenantOverride, and allowedExtensions can be set.");
        }

        if (!Read().Profiles.TryGetValue(name, out ConnectionProfile? existing))
        {
            throw new InvalidDataException("The named mcpcli profile does not exist.");
        }

        _ = UpdateProfile(existing, field, value);
    }

    /// <summary>Masks a token for a display document.</summary>
    public static string? MaskToken(string? token)
    {
        if (token is null)
        {
            return null;
        }

        int[] textElements = StringInfo.ParseCombiningCharacters(token);
        if (textElements.Length <= 4)
        {
            return FullMask(token);
        }

        string prefix = token[..textElements[4]];
        if (prefix.EnumerateRunes().Any(rune => Rune.GetUnicodeCategory(rune) is
            UnicodeCategory.Control or UnicodeCategory.Format or
            UnicodeCategory.LineSeparator or UnicodeCategory.ParagraphSeparator))
        {
            return FullMask(token);
        }

        string masked = prefix + "***";
        return masked.Contains(token, StringComparison.Ordinal) ? FullMask(token) : masked;
    }

    private ProfileSnapshot Mutate(Func<ProfileSnapshot, ProfileSnapshot> update, CancellationToken cancellationToken = default)
        => new ProfileFileTransaction(ProfilePath).Apply(Read, update, JsonOptions, cancellationToken);

    private static ProfileSnapshot? Parse(string json)
    {
        try
        {
            using JsonDocument parsed = JsonDocument.Parse(json, new JsonDocumentOptions { AllowDuplicateProperties = false });
            return JsonSerializer.Deserialize<ProfileSnapshot>(json, JsonOptions);
        }
        catch (JsonException)
        {
            // The parser message can quote document content, so only a fixed message is surfaced.
            throw new InvalidDataException("The mcpcli profile document is malformed or has unknown or duplicate fields.");
        }
    }

    private static string FullMask(string token)
    {
        if (token.Length > 3)
        {
            return "***";
        }

        foreach (char candidate in "*#~!")
        {
            if (token.IndexOf(candidate) < 0)
            {
                return new string(candidate, 3);
            }
        }

        return "***";
    }

    private static bool ParseBoolean(string value)
        => value switch
        {
            "true" or "1" => true,
            "false" or "0" => false,
            _ => throw new InvalidDataException("allowTenantOverride must be true, false, 1, or 0."),
        };

    private static ConnectionProfile UpdateProfile(ConnectionProfile profile, string field, string value)
    {
        ConnectionProfile updated = field switch
        {
            "tenant" => profile with { Tenant = value },
            "actor" => profile with { Actor = value },
            "allowTenantOverride" => profile with { AllowTenantOverride = ParseBoolean(value) },
            "allowedExtensions" => profile with
            {
                AllowedExtensions = value.Length == 0 ? [] : value.Split(',', StringSplitOptions.None),
            },
            _ => throw new InvalidDataException("Unsupported profile field."),
        };
        ValidateProfile(updated, forMutation: true);
        if (field == "tenant")
        {
            ValidateTenant(updated.Tenant);
        }

        return updated;
    }

    private static void ValidateTenant(string? tenant)
    {
        // The executor lowercases session tenants before applying the Gateway grammar.
        if (tenant is not null && !RoutingResolver.IsTenantDomain(tenant.ToLowerInvariant()))
        {
            throw new InvalidDataException("A lowercased profile tenant must contain 1 to 64 ASCII letters, digits, or hyphens and start and end with a letter or digit.");
        }
    }

    private static void ValidateName(string name)
    {
        if (string.IsNullOrWhiteSpace(name) || !ProfileNamePattern().IsMatch(name))
        {
            throw new InvalidDataException("Profile names must contain 1 to 64 ASCII letters, digits, underscores, or hyphens.");
        }
    }

    private static void ValidateProfile(ConnectionProfile profile, bool forMutation = false)
    {
        ArgumentNullException.ThrowIfNull(profile);
        Uri? uri = null;
        if (profile.Url is not null && (!Uri.TryCreate(profile.Url, UriKind.Absolute, out uri)
            || uri.Scheme is not ("http" or "https") || uri.UserInfo.Length > 0
            || uri.Query.Length > 0 || uri.Fragment.Length > 0))
        {
            throw new InvalidDataException("A profile URL must be an absolute HTTP(S) gateway URL.");
        }

        if (forMutation && profile.Token is not null)
        {
            ValidateTokenEndpoint(uri);
        }

        if (profile.Format is not null && profile.Format is not ("json" or "table"))
        {
            throw new InvalidDataException("A profile format must be json or table.");
        }

        if (profile.Token is not null && string.IsNullOrWhiteSpace(profile.Token)
            || profile.Tenant is not null && string.IsNullOrWhiteSpace(profile.Tenant)
            || profile.Actor is not null && string.IsNullOrWhiteSpace(profile.Actor))
        {
            throw new InvalidDataException("A profile token, tenant, or actor cannot be blank.");
        }

        var allowed = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (string key in profile.AllowedExtensions ?? [])
        {
            if (key is null || !allowed.Add(key))
            {
                throw new InvalidDataException("A profile has duplicate or null allowed extension keys.");
            }
        }

        if (allowed.Any(key => !ExtensionValidator.IsValidKey(key)))
        {
            throw new InvalidDataException("A profile has invalid allowed extension keys.");
        }
    }

    private static void ValidateTokenEndpoint(Uri? uri)
    {
        if (SettingsResolver.RequiresHttps(uri))
        {
            throw new InvalidDataException("A gateway URL with a token must use HTTPS or a loopback IP address.");
        }
    }

    private static void RejectNonRegularPath(string path)
    {
        var file = new FileInfo(path);
        if (file.LinkTarget is not null)
        {
            throw new InvalidDataException("The mcpcli profile path cannot be a symbolic link.");
        }

        if (Directory.Exists(path))
        {
            throw new InvalidDataException("The mcpcli profile path must be a regular file.");
        }
    }

    [GeneratedRegex(@"^[a-zA-Z0-9_-]{1,64}\z")]
    private static partial Regex ProfileNamePattern();
}
