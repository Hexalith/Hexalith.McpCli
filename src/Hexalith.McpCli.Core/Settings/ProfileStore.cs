using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;
using Hexalith.McpCli.Core.Execution;

namespace Hexalith.McpCli.Core.Settings;

/// <summary>Owns this tool's versioned profile file without accessing the admin CLI's store.</summary>
public sealed partial class ProfileStore
{
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web)
    {
        PropertyNameCaseInsensitive = false,
        UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow,
    };

    private readonly string _path;

    /// <summary>Initializes the store at the default path or a test-supplied path.</summary>
    /// <param name="path">The optional exact profile file path.</param>
    public ProfileStore(string? path = null)
    {
        _path = path ?? Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".eventstore", "mcpcli.json");
    }

    /// <summary>Gets the path owned by this tool.</summary>
    public string ProfilePath => _path;

    /// <summary>Reads and validates the version-one profile document once.</summary>
    public ProfileSnapshot Read()
    {
        string directory = Path.GetDirectoryName(_path) ?? throw new InvalidDataException("The profile path has no directory.");
        if (new DirectoryInfo(directory).LinkTarget is not null)
        {
            throw new InvalidDataException("The mcpcli profile directory cannot be a symbolic link.");
        }

        RejectNonRegularPath(_path);
        if (!File.Exists(_path))
        {
            return new ProfileSnapshot(1, null, new Dictionary<string, ConnectionProfile>(StringComparer.Ordinal));
        }

        var information = new FileInfo(_path);
        if (information.Length > 1_048_576)
        {
            throw new InvalidDataException("The mcpcli profile file exceeds the size limit.");
        }

        string json = File.ReadAllText(_path);
        using JsonDocument parsed = JsonDocument.Parse(json, new JsonDocumentOptions { AllowDuplicateProperties = false });

        ProfileSnapshot snapshot = JsonSerializer.Deserialize<ProfileSnapshot>(json, JsonOptions)
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
    {
        ValidateName(name);
        ValidateProfile(profile);
        return Mutate(snapshot =>
        {
            var profiles = new Dictionary<string, ConnectionProfile>(snapshot.Profiles, StringComparer.Ordinal)
            {
                [name] = profile,
            };
            return snapshot with { Profiles = profiles };
        });
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

            ConnectionProfile updated = field switch
            {
                "tenant" => existing with { Tenant = value },
                "actor" => existing with { Actor = value },
                "allowTenantOverride" => existing with { AllowTenantOverride = ParseBoolean(value) },
                "allowedExtensions" => existing with
                {
                    AllowedExtensions = value.Length == 0 ? [] : value.Split(',', StringSplitOptions.None),
                },
                _ => throw new InvalidDataException("Unsupported profile field."),
            };
            ValidateProfile(updated);
            var profiles = new Dictionary<string, ConnectionProfile>(snapshot.Profiles, StringComparer.Ordinal)
            {
                [name] = updated,
            };
            return snapshot with { Profiles = profiles };
        });
    }

    /// <summary>Masks a token for a display document.</summary>
    public static string? MaskToken(string? token)
        => token is null ? null : token[..Math.Min(4, token.Length)] + "***";

    private ProfileSnapshot Mutate(Func<ProfileSnapshot, ProfileSnapshot> update)
        => new ProfileFileTransaction(_path).Apply(Read, update, JsonOptions);

    private static bool ParseBoolean(string value)
        => value switch
        {
            "true" or "1" => true,
            "false" or "0" => false,
            _ => throw new InvalidDataException("allowTenantOverride must be true, false, 1, or 0."),
        };

    private static void ValidateName(string name)
    {
        if (string.IsNullOrWhiteSpace(name) || !ProfileNamePattern().IsMatch(name))
        {
            throw new InvalidDataException("Profile names must contain 1 to 64 ASCII letters, digits, underscores, or hyphens.");
        }
    }

    private static void ValidateProfile(ConnectionProfile profile)
    {
        ArgumentNullException.ThrowIfNull(profile);
        if (profile.Url is not null && (!Uri.TryCreate(profile.Url, UriKind.Absolute, out Uri? uri)
            || uri.Scheme is not ("http" or "https") || uri.UserInfo.Length > 0
            || uri.Query.Length > 0 || uri.Fragment.Length > 0))
        {
            throw new InvalidDataException("A profile URL must be an absolute HTTP(S) gateway URL.");
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

        if (ExtensionValidator.Validate(allowed.ToDictionary(key => key, _ => string.Empty, StringComparer.Ordinal), allowed).Count > 0)
        {
            throw new InvalidDataException("A profile has invalid allowed extension keys.");
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

    [GeneratedRegex("^[a-zA-Z0-9_-]{1,64}$")]
    private static partial Regex ProfileNamePattern();
}
